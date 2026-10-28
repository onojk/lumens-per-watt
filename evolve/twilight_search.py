"""Twilight specialist, gene search only (the user's next round, item 3, Oct 28; Phase 3; no code mutation).
Band: theta 0.33-0.40 (smaller prime = 0.33-0.40 of N's bits), at 84 and 96 bits.
  train : 160 fresh numbers per size (seeds 9800000 + bits), each pre-stage ALONE in lampcore --types at every budget of
          the coarse grid (partition.COARSE, 0 .. 2^20; rho also at the reference's own budget) for td, rho and ECM (partition.PRE genes, ob = the budget), p-1 at
          B in {0, 256, ..., 8192} (ob = 2B), and the reference QS (2'b) alone; per number: success and per-type counts.
          A pipeline's cost on a number is composed EXACTLY from these records (lamps compute on N alone; a stage that
          succeeds within its budget stops the pipeline; else its budget's spending, then the next stage; QS last).
  search: coordinate search over (td, rho, p-1 B, ECM) from the coarse grid's best; fitness = rule (b): the worst of
          op-class v1, ruint and Montgomery of (mean pipeline cost / mean QS-alone cost) on the training numbers;
          official reported. The reference pipeline (sizescale_k_sealed "(d)": td 0, rho, p-1 B, ECM 0) is scored the
          same way, for information. The composition is checked against a direct lampcore run of the best genome on
          every training number (per-type counts must be equal).
  Validation (not here): fresh sealed held-out numbers, the best genome against the reference card and the reference
  pipeline, priced three ways + wall, meter-health check; predictions filed first (STOP at that point).
  python3 twilight_search.py -> twilight_search.json, stdout"""
import json, math, random, subprocess
import numpy as np
import partition as P, optypes
from lamps import rand_prime
from fastlamps import BIN
from baseline_msieve import reference

SIZES, PER = (84, 96), 160
GRID = list(P.COARSE)
PM1_B = [0, 256, 512, 1024, 2048, 4096, 8192]
V1 = {k: v["weight"] for k, v in json.load(open("../opclass/opclass_v1.json"))["classes"].items() if v["weight"]}
PR = optypes.prices()
PRICINGS = ("opclass_v1", "ruint", "montgomery", "official")

def price(ty, pr):
    if pr == "official":
        return float(sum(ty.values()))
    if pr == "opclass_v1":
        return float(sum(V1.get(t, 0.0) * n for t, n in ty.items()))
    return optypes.cost(ty, pr, PR)

def numbers(bits, seed, n):
    rng, out = random.Random(seed), []
    while len(out) < n:
        pb = round(rng.uniform(0.33, 0.40) * bits)
        p, q = rand_prime(pb, rng), rand_prime(bits - pb + 1, rng)
        N = p * q
        if N.bit_length() != bits:
            continue
        p, q = min(p, q), max(p, q)
        if 0.33 <= math.log2(p) / math.log2(N) < 0.40:
            out.append((N, p, q))
    return out

def run(genome, cap, nums):
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout
    res = []
    for (N, p, q), l in zip(nums, out.splitlines()):
        f = l.split(); i = f.index("T")
        ty = dict(zip(optypes.TYPE_ORDER, map(int, f[i + 1:])))
        res.append((f[1] != "miss" and int(f[1]) in (p, q), ty))
    return res

def stage_genome(s, b):
    if s == "pm1":
        return dict(P.PRE["pm1"], B=b, ob=2 * b)
    return dict(P.PRE[s], ob=b)

class TMap:
    def __init__(self, bits, nums, rho_opts):
        self.n = len(nums)
        self.rec = {}
        for s, opts in (("td", GRID), ("rho", rho_opts), ("pm1", PM1_B), ("ecm", GRID)):
            for b in opts:
                if b == 0:
                    continue
                r = run([stage_genome(s, b)], P.QS_CAP, nums)
                self.rec[(s, b)] = (np.array([ok for ok, _ in r]), {pr: np.array([price(ty, pr) for _, ty in r]) for pr in PRICINGS},
                                    [ty for _, ty in r])
        r = run([reference(bits)], P.QS_CAP, nums)
        assert all(ok for ok, _ in r), "QS alone missed a training number"
        self.qs = {pr: np.array([price(ty, pr) for _, ty in r]) for pr in PRICINGS}
        self.qs_ty = [ty for _, ty in r]

    def costs(self, vec, pr):
        total, alive = np.zeros(self.n), np.ones(self.n, dtype=bool)
        for s, b in zip(("td", "rho", "pm1", "ecm"), vec):
            if b == 0:
                continue
            succ, c, _ = self.rec[(s, b)]
            total += np.where(alive, c[pr], 0.0)
            alive &= ~succ
        return total + np.where(alive, self.qs[pr], 0.0)

    def composed_types(self, vec, i):
        tot, alive = {}, True
        for s, b in zip(("td", "rho", "pm1", "ecm"), vec):
            if b == 0 or not alive:
                continue
            succ, _, tys = self.rec[(s, b)]
            for t, n in tys[i].items():
                tot[t] = tot.get(t, 0) + n
            alive = not succ[i]
        if alive:
            for t, n in self.qs_ty[i].items():
                tot[t] = tot.get(t, 0) + n
        return tot

    def fitness(self, vec):
        sc = {pr: self.costs(vec, pr).mean() / self.qs[pr].mean() for pr in PRICINGS}
        return max(sc[p] for p in ("opclass_v1", "ruint", "montgomery")), sc

def search(M, rho_opts):
    best = min(((M.fitness(v)[0], v) for v in ((t, r, p, e) for t in GRID for r in rho_opts for p in PM1_B for e in GRID)))
    vec = list(best[1])
    while True:
        moved = False
        for i, opts in enumerate((GRID, rho_opts, PM1_B, GRID)):
            cur = M.fitness(tuple(vec))[0]
            for o in opts:
                trial = vec.copy(); trial[i] = o
                f = M.fitness(tuple(trial))[0]
                if f < cur - 1e-12:
                    cur, vec, moved = f, trial, True
        if not moved:
            return tuple(vec)

def genome(vec, bits):
    g = [stage_genome(s, b) for s, b in zip(("td", "rho", "pm1", "ecm"), vec) if b]
    return g + [reference(bits)]

if __name__ == "__main__":
    out = {}
    for bits in SIZES:
        nums = numbers(bits, 9800000 + bits, PER)
        bud = json.load(open("sizescale_k_sealed.json"))["sizes"][str(bits)]["tracks"]["R"]["budgets"]["(d) new winner, new budgets"]
        rho_opts = sorted(set(GRID) | {bud[0]})               # the coarse grid plus the reference's own rho budget
        M = TMap(bits, nums, rho_opts)
        vec = search(M, rho_opts)
        f, sc = M.fitness(vec)
        ref_vec = (0, bud[0], bud[1], bud[2])                  # the reference pipeline: td off, rho, p-1 B, ECM off
        rf, rsc = M.fitness(ref_vec)
        # the composition against a direct run of the best genome, every training number
        direct = run(genome(vec, bits), P.QS_CAP, nums)
        same = sum(M.composed_types(vec, i) == {t: n for t, n in ty.items() if n} or
                   {t: n for t, n in M.composed_types(vec, i).items() if n} == {t: n for t, n in ty.items() if n}
                   for i, (_, ty) in enumerate(direct))
        out[bits] = {"best": vec, "fitness": f, "scores": sc, "reference_pipeline_grid": ref_vec, "reference_fitness": rf,
                     "reference_scores": rsc, "composition_matches_direct": same, "n": PER, "genome": genome(vec, bits)}
        print(f"{bits} bits (theta 0.33-0.40, {PER} training numbers): best (td, rho, p-1 B, ECM) = {vec}: rule (b) {f:.4f} "
              f"(op-class {sc['opclass_v1']:.4f}, ruint {sc['ruint']:.4f}, Montgomery {sc['montgomery']:.4f}, official {sc['official']:.4f}) "
              f"against QS alone; the reference pipeline {ref_vec} {rf:.4f}; composition = direct run on {same}/{PER}", flush=True)
    json.dump({str(k): v for k, v in out.items()}, open("twilight_search.json", "w"), indent=1)
