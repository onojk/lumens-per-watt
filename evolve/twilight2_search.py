"""Twilight specialist on theta 0.28-0.34, the p-1 to QS hand-off (predictions/twilight-028-034.md, sealed first;
run only through tools/sealed_run.sh twilight-028-034). Gene search only; no code mutation. 96 bits primary, 84 secondary.
  train   : 160 fresh numbers per size (seeds 9810000 + bits), each pre-stage ALONE in lampcore --types at every budget
            (twilight_search's map: td, rho and ECM on partition.COARSE, ob = the budget, rho also at the reference
            pipeline's own budget; p-1 at B in {0, 256, ..., 8192}, ob = 2B), and the reference QS alone. A pipeline's
            cost is composed exactly from these records (stage order td, rho, p-1, ECM, then QS).
            Search: the coarse grid exhaustively, then a coordinate search; then the p-1 refinement pass: B in steps of
            2^(1/4) strictly between the coarse best's grid neighbours (the best B = 0: 128 * 2^(k/4), k = 0..3; the best
            B = 8,192, the top of the grid: between 4,096 and 8,192 only), each mapped alone as above, and a coordinate
            search again over all genes with the refined B's added. Fitness = rule (b): the worst of op-class v1, ruint
            and Montgomery of mean pipeline cost / mean QS-alone cost; official reported. The composition of the selected
            genome must equal a direct lampcore run on every training number (else a blocker: exit 3).
            -> twilight2_search.json. STOP here (the design, section 6): the selected genome is reported first.
  validate: 400 held-out numbers per size (seeds 9820000 + bits), drawn here. Direct lampcore --types runs of the
            specialist, (i) QS alone (the reference card) and (ii) the reference pipeline. Every arm must factor every
            number (else a blocker: exit 3). Ratios of mean cost (specialist / baseline) per pricing, paired bootstrap
            (10,000 resamples, numpy default_rng(2026), 2.5-97.5%), rule (b) per resample. If the specialist's genome is
            the reference card alone, arm (i) is 1.000 by construction and is not run (the user's Oct 28 rule).
            Meter-health check: callgrind instructions (minus the arm's start-up) per op-class v1 unit on the first 8
            held-out numbers per arm, and each arm's ratio to QS alone's. -> twilight2_validate.json
  wall    : the three arms on the same held-out numbers, batch, pinned to core 2, 4 replicates, the order rotating;
            baseline_msieve.conditions() at the start (AC, cap, TCPU, no Wolfram kernel, the load check) and cool() (the
            load check, the 90 C pause) before every replicate. Specialist / baseline per replicate, mean and 95% t
            interval (3 df, 3.1824). -> twilight2_wall.json
  python3 twilight2_search.py train | validate | wall"""
import sys
MODE = sys.argv[1] if len(sys.argv) > 1 else ""
sys.argv = sys.argv[:1]                                        # partition and sizescale read sys.argv
import json, math, os, random, re, statistics, subprocess, tempfile, time
from multiprocessing import Pool
import numpy as np
import optypes
import partition as P
from lamps import rand_prime
from fastlamps import BIN
from baseline_msieve import reference, conditions, cool
from timing import machine_state, timed_with_clock
from twilight_search import GRID, PM1_B, PRICINGS, price, stage_genome, genome

SIZES = (96, 84)
LO, HI = 0.28, 0.34
PER, VAL, SUB, BOOT, REPS, T3 = 160, 400, 8, 10000, 4, 3.1824
STAGES = ("td", "rho", "pm1", "ecm")
SCR = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad"
RULE_B = ("opclass_v1", "ruint", "montgomery")

def numbers(bits, seed, n):
    rng, out = random.Random(seed), []
    while len(out) < n:
        pb = round(rng.uniform(LO, HI) * bits)
        p, q = rand_prime(pb, rng), rand_prime(bits - pb + 1, rng)
        N = p * q
        if N.bit_length() != bits:
            continue
        p, q = min(p, q), max(p, q)
        if LO <= math.log2(p) / math.log2(N) < HI:
            out.append((N, p, q))
    return out

def run(genome_, cap, nums):
    text = json.dumps(genome_) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout
    res = []
    for (N, p, q), l in zip(nums, out.splitlines()):
        f = l.split(); i = f.index("T")
        ty = dict(zip(optypes.TYPE_ORDER, map(int, f[i + 1:])))
        res.append((f[1] != "miss" and int(f[1]) in (p, q), ty))
    return res

def ref_budgets(bits):
    return json.load(open("sizescale_k_sealed.json"))["sizes"][str(bits)]["tracks"]["R"]["budgets"]["(d) new winner, new budgets"]

class TMap:
    """Each stage alone at each budget, and QS alone, on the training numbers; pipelines composed from the records."""
    def __init__(self, bits, nums, opts):
        self.n, self.nums, self.rec = len(nums), nums, {}
        for s, o in zip(STAGES, opts):
            for b in o:
                self.add(s, b)
        r = run([reference(bits)], P.QS_CAP, nums)
        assert all(ok for ok, _ in r), "QS alone missed a training number"
        self.qs = {pr: np.array([price(ty, pr) for _, ty in r]) for pr in PRICINGS}
        self.qs_ty = [ty for _, ty in r]

    def add(self, s, b):
        if b == 0 or (s, b) in self.rec:
            return
        r = run([stage_genome(s, b)], P.QS_CAP, self.nums)
        self.rec[(s, b)] = (np.array([ok for ok, _ in r]), {pr: np.array([price(ty, pr) for _, ty in r]) for pr in PRICINGS},
                            [ty for _, ty in r])

    def costs(self, vec, pr):
        total, alive = np.zeros(self.n), np.ones(self.n, dtype=bool)
        for s, b in zip(STAGES, vec):
            if b == 0:
                continue
            succ, c, _ = self.rec[(s, b)]
            total += np.where(alive, c[pr], 0.0)
            alive &= ~succ
        return total + np.where(alive, self.qs[pr], 0.0)

    def composed_types(self, vec, i):
        tot, alive = {}, True
        for s, b in zip(STAGES, vec):
            if b == 0 or not alive:
                continue
            succ, _, tys = self.rec[(s, b)]
            for t, n in tys[i].items():
                tot[t] = tot.get(t, 0) + n
            alive = not succ[i]
        if alive:
            for t, n in self.qs_ty[i].items():
                tot[t] = tot.get(t, 0) + n
        return {t: n for t, n in tot.items() if n}

    def fitness(self, vec):
        sc = {pr: self.costs(vec, pr).mean() / self.qs[pr].mean() for pr in PRICINGS}
        return max(sc[p] for p in RULE_B), sc

def coordinate(M, vec, opts):
    vec = list(vec)
    while True:
        moved = False
        for i, o in enumerate(opts):
            cur = M.fitness(tuple(vec))[0]
            for x in o:
                trial = vec.copy(); trial[i] = x
                f = M.fitness(tuple(trial))[0]
                if f < cur - 1e-12:
                    cur, vec, moved = f, trial, True
        if not moved:
            return tuple(vec)

def refined(b):
    """p-1 B's in steps of 2^(1/4) strictly between the coarse best's grid neighbours (not on the coarse grid)."""
    if b == 0:
        vals = [128 * 2 ** (k / 4) for k in range(4)]
    else:
        i = PM1_B.index(b)
        lo, hi = PM1_B[i - 1] or 128, (PM1_B[i + 1] if i + 1 < len(PM1_B) else b)
        vals = [lo * 2 ** (k / 4) for k in range(1, 4 * round(math.log2(hi / lo)))]
    return sorted({round(v) for v in vals} - set(PM1_B))

def train():
    out = {}
    for bits in SIZES:
        t0 = time.time()
        nums = numbers(bits, 9810000 + bits, PER)
        bud = ref_budgets(bits)
        rho_opts = sorted(set(GRID) | {bud[0]})
        opts = [GRID, rho_opts, list(PM1_B), GRID]
        M = TMap(bits, nums, opts)
        coarse = min((M.fitness(v)[0], v) for v in ((t, r, p, e) for t in GRID for r in rho_opts for p in PM1_B for e in GRID))[1]
        coarse = coordinate(M, coarse, opts)
        cf, csc = M.fitness(coarse)
        ref = refined(coarse[2])
        for b in ref:
            M.add("pm1", b)
        opts[2] = sorted(set(PM1_B) | set(ref))
        vec = coordinate(M, coarse, opts)
        f, sc = M.fitness(vec)
        ref_vec = (0, bud[0], bud[1], bud[2])
        rf, rsc = M.fitness(ref_vec)
        direct = run(genome(vec, bits), P.QS_CAP, nums)
        same = sum(M.composed_types(vec, i) == {t: n for t, n in ty.items() if n} for i, (_, ty) in enumerate(direct))
        pm1_curve = {b: M.fitness((vec[0], vec[1], b, vec[3]))[1] for b in opts[2]}   # p-1 B scan at the selected other genes
        out[str(bits)] = {"best": vec, "fitness": f, "scores": sc, "coarse_best": coarse, "coarse_fitness": cf,
                          "coarse_scores": csc, "pm1_refined": ref, "reference_pipeline_grid": ref_vec,
                          "reference_fitness": rf, "reference_scores": rsc, "composition_matches_direct": same, "n": PER,
                          "pm1_success": {b: int(M.rec[("pm1", b)][0].sum()) for b in opts[2] if b},
                          "pm1_scan": {str(b): s for b, s in pm1_curve.items()}, "genome": genome(vec, bits)}
        print(f"{bits} bits (theta {LO}-{HI}, {PER} training numbers, {time.time() - t0:.0f} s): coarse best {coarse} "
              f"rule (b) {cf:.4f}; p-1 refinement {ref}; best (td, rho, p-1 B, ECM) = {vec}: rule (b) {f:.4f} "
              f"(op-class {sc['opclass_v1']:.4f}, ruint {sc['ruint']:.4f}, Montgomery {sc['montgomery']:.4f}, official "
              f"{sc['official']:.4f}) against QS alone; the reference pipeline {ref_vec}: rule (b) {rf:.4f} (op-class "
              f"{rsc['opclass_v1']:.4f}); composition = direct run on {same}/{PER}", flush=True)
        print(f"  p-1 B scan at the selected other genes (op-class / rule (b)): "
              + ", ".join(f"{b} {s['opclass_v1']:.4f}/{max(s[p] for p in RULE_B):.4f}" for b, s in pm1_curve.items()), flush=True)
        if same != PER:
            json.dump(out, open("twilight2_search.json", "w"), indent=1)
            print("BLOCKER: the composition differs from the direct run"); sys.exit(3)
    json.dump(out, open("twilight2_search.json", "w"), indent=1)

def arms(bits):
    tr = json.load(open("twilight2_search.json"))[str(bits)]
    bud = ref_budgets(bits)
    spec = tr["genome"]
    return {"specialist": spec, "qs": [reference(bits)], "reference_pipeline": genome((0, bud[0], bud[1], bud[2]), bits)}

def qs_only(a):
    return a["specialist"] == a["qs"]

def instructions(args):
    genome_, nums = args
    text = json.dumps(genome_) + "\n" + str(int(P.QS_CAP)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = os.path.join(tempfile.mkdtemp(dir=SCR, prefix="tw2_"), "cg.out")
    subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=no", "--dump-line=no", f"--callgrind-out-file={out}", BIN],
                   input=text, capture_output=True, text=True, check=True)
    return int(re.search(r"^summary: (\d+)", open(out).read(), re.M).group(1))

def validate():
    out, rng = {}, np.random.default_rng(2026)
    for bits in SIZES:
        nums = numbers(bits, 9820000 + bits, VAL)
        A = arms(bits)
        skip = qs_only(A)
        cost, okc = {}, {}
        for name, g in A.items():
            if name == "specialist" and skip:
                continue
            r = run(g, P.QS_CAP, nums)
            okc[name] = sum(ok for ok, _ in r)
            cost[name] = {pr: np.array([price(ty, pr) for _, ty in r]) for pr in PRICINGS}
        if skip:
            cost["specialist"], okc["specialist"] = cost["qs"], okc["qs"]
        rec = {"n": VAL, "arms": A, "success": okc, "specialist_is_qs_alone": skip,
               "mean_cost": {a: {pr: float(c[pr].mean()) for pr in PRICINGS} for a, c in cost.items()}, "vs": {}}
        idx = rng.integers(0, VAL, size=(BOOT, VAL))
        for base in ("qs", "reference_pipeline"):
            v = {}
            for pr in PRICINGS:
                pt = cost["specialist"][pr].mean() / cost[base][pr].mean()
                bs = cost["specialist"][pr][idx].mean(axis=1) / cost[base][pr][idx].mean(axis=1)
                v[pr] = {"ratio": float(pt), "ci95": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))], "_bs": bs}
            rb = np.max([v[p]["_bs"] for p in RULE_B], axis=0)
            v["rule_b"] = {"ratio": max(v[p]["ratio"] for p in RULE_B),
                           "ci95": [float(np.quantile(rb, 0.025)), float(np.quantile(rb, 0.975))]}
            for pr in PRICINGS:
                del v[pr]["_bs"]
            v["by_construction"] = skip and base == "qs"
            v["cells_agree"] = (all(v[p]["ci95"][1] < 1 for p in RULE_B) and "cheaper") or \
                               (all(v[p]["ci95"][0] > 1 for p in RULE_B) and "dearer") or "not called"
            rec["vs"][base] = v
            print(f"{bits} bits, specialist / {base}" + (" (1.000 by construction; not run)" if v["by_construction"] else "")
                  + ": " + ", ".join(f"{pr} {v[pr]['ratio']:.4f} [{v[pr]['ci95'][0]:.4f}, {v[pr]['ci95'][1]:.4f}]" for pr in PRICINGS)
                  + f"; rule (b) {v['rule_b']['ratio']:.4f} [{v['rule_b']['ci95'][0]:.4f}, {v['rule_b']['ci95'][1]:.4f}]; "
                  f"three pricings: {v['cells_agree']}", flush=True)
        print(f"{bits} bits: successes " + ", ".join(f"{a} {k}/{VAL}" for a, k in okc.items()), flush=True)
        if any(k != VAL for k in okc.values()):
            out[str(bits)] = rec
            json.dump(out, open("twilight2_validate.json", "w"), indent=1)
            print("BLOCKER: an arm missed a held-out number"); sys.exit(3)
        # meter-health: instructions per op-class unit on the first SUB numbers per arm, start-up subtracted
        names = [a for a in A if not (a == "specialist" and skip)]
        jobs = [(A[a], []) for a in names] + [(A[a], nums[:SUB]) for a in names]
        with Pool(3) as pool:
            irs = pool.map(instructions, jobs, chunksize=1)
        mh = {}
        for k, a in enumerate(names):
            ir = irs[len(names) + k] - irs[k]
            v1 = sum(price(ty, "opclass_v1") for _, ty in run(A[a], P.QS_CAP, nums[:SUB]))
            mh[a] = {"instructions": ir, "opclass_v1": v1, "ir_per_unit": ir / v1}
        for a in mh:
            mh[a]["vs_qs"] = mh[a]["ir_per_unit"] / mh["qs"]["ir_per_unit"]
        rec["meter_health"] = mh
        print(f"{bits} bits meter-health (instructions per op-class unit, first {SUB} held-out numbers): "
              + ", ".join(f"{a} {m['ir_per_unit']:.3f} ({m['vs_qs']:.3f} x QS)" for a, m in mh.items()), flush=True)
        out[str(bits)] = rec
    json.dump(out, open("twilight2_validate.json", "w"), indent=1)

def run_wall(genome_, nums):
    text = json.dumps(genome_) + "\n" + str(int(P.QS_CAP)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    subprocess.run(["taskset", "-c", "2", BIN], input=text, capture_output=True, text=True, check=True)
    return time.perf_counter() - t0

def wall():
    bad = conditions()
    state0 = machine_state()
    if bad:
        print("timing skipped: " + "; ".join(bad)); print(state0); sys.exit(2)
    out = {"replicates": REPS, "state_start": state0, "sizes": {}}
    for bits in SIZES:
        nums = numbers(bits, 9820000 + bits, VAL)
        A = arms(bits)
        names = [a for a in A if not (a == "specialist" and qs_only(A))]   # QS alone: the specialist's clock is QS's
        rec = {"n": VAL, "s": {a: [] for a in A}, "mhz": {a: [] for a in A}, "order": [], "states": [],
               "specialist_is_qs_alone": qs_only(A)}
        for r in range(REPS):
            cool()
            rec["states"].append(machine_state())
            order = names[r % len(names):] + names[:r % len(names)]
            rec["order"].append(order)
            for a in order:
                dt, mhz = timed_with_clock(lambda: run_wall(A[a], nums), period=0.05, skip_launch=True)
                rec["s"][a].append(dt); rec["mhz"][a] += mhz
        if qs_only(A):
            rec["s"]["specialist"] = rec["s"]["qs"]
        rec["ms_per_number"] = {a: 1e3 * statistics.mean(v) / VAL for a, v in rec["s"].items()}
        rec["vs"] = {}
        for base in ("qs", "reference_pipeline"):
            rs = [s / b for s, b in zip(rec["s"]["specialist"], rec["s"][base])]
            m, h = statistics.mean(rs), T3 * statistics.stdev(rs) / math.sqrt(REPS)
            rec["vs"][base] = {"per_replicate": rs, "mean": m, "ci95": [m - h, m + h]}
        rec["mhz_median"] = {a: (statistics.median(v) if v else None) for a, v in rec["mhz"].items()}
        print(f"{bits} bits wall ({VAL} numbers, {REPS} replicates): ms per number "
              + ", ".join(f"{a} {v:.3f}" for a, v in rec["ms_per_number"].items())
              + "; " + "; ".join(f"specialist / {b} {v['mean']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]" for b, v in rec["vs"].items())
              + "; core 2 median MHz " + ", ".join(f"{a} {v}" for a, v in rec["mhz_median"].items()), flush=True)
        out["sizes"][str(bits)] = rec
    out["state_end"] = machine_state()
    json.dump(out, open("twilight2_wall.json", "w"), indent=1)

if __name__ == "__main__":
    {"train": train, "validate": validate, "wall": wall}[MODE]()
