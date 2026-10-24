"""Partition study (NOTES.md, "Partition study: cost model and predictions", with its
amendments): sequential op budgets td(ob1) -> rho(ob2) -> pm1(ob3) -> ecm(ob4) -> final qs.

  python3 partition.py map [workers]  -> partition_map.json   (tuning seeds only)
  python3 partition.py optimize       -> partition_alloc.json (from the map; prints the report)

The sealed run is a separate mode, written and run only after the allocations are reviewed.

map: on every tuning number (mixed: 84-bit N, smaller factor 16/20/24/28/32/36/42 bits, 80
per band; seeds 4000000 + 100 pb + 84), each pre-stage alone (Python, cap 2^21) records its
ops-to-success T (None if it did not succeed within the cap), the exact spending at every
candidate budget b (the meter total right after the first charge past b: the "past ob"
rule), and its per-type counts at the end; each final qs alone (cap 2^28) its ops and
per-type counts. pm1 (one gcd, at the end) needs only its full-length cost.

optimize: the cost of a budget vector on a number is composed exactly from these records
(per-number composition: lamps compute on N alone, so no independence assumption): a stage
with T <= ob finds the factor at T and costs its exact per-type price; otherwise it spends
its recorded prefix (calibrated: that prefix times the stage's price per official op on
that band) and the next stage runs; after the last pre-stage, qs alone. Fitness (c):
score_P = mean cost under pricing P / qs alone's mean under P, on the same numbers;
fitness = max over official, ruint, Montgomery (median P-core prices). Search: ob in
{0, 2^8, ..., 2^20} for td, rho and ECM and {0, full} for pm1, then coordinate refinement
over the 1/8-octave grid 2^(k/8), k = 64..160 (spending is recorded exactly only at these
candidates, so refinement scans them rather than a continuous minimizer). Done for both
final-qs variants, on the mixed population and on the balanced control.

Reported per allocation: budgets, fitness and score per pricing, ratio per band and the
worst band (per pricing), the map's prediction for the sealed numbers with 95% bootstrap
intervals (10,000 resamples, random.Random(2026) per cell; overall resampled within each
band), the best single lamp per band (hindsight, information only), and, if pm1 is on, its
per-band savings where it succeeds and added cost where it fails.
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, statistics
from multiprocessing import Pool
import numpy as np
import optypes, qs, ecm
from lamps import Meter, Budget, LAMPS
from fastlamps import semiprimes_pq, semiprimes_unbalanced

BANDS = (16, 20, 24, 28, 32, 36, 42)
PER_BAND = 80
TUNING, SEALED = 4000000, 5000000
TD = {"t": "td", "a": 0.5}
RHO = {"t": "rho", "c": 1, "b": 64}
PM1 = {"t": "pm1", "b": 0.19911571277067214}
ECM = {"t": "ecm", "b1": 1.0, "b2": 50}
N51_QS = json.load(open("run6/accept.json"))["genomes"]["N51-0917"][0]
QS_VARIANTS = {"qs + lc 1.4": {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4},
               "N51-0917's qs": N51_QS}
PRE = {"td": TD, "rho": RHO, "pm1": PM1, "ecm": ECM}
PRE_CAP, QS_CAP = 2 ** 21, 2 ** 28
FINE = [0] + sorted({int(round(2 ** (k / 8))) for k in range(64, 161)})   # 0 and 2^8 .. 2^20
COARSE = [0] + [2 ** e for e in range(8, 21)]
PM1_OPTS = (0, 1)                                                      # off, full length
PRICINGS = ("official", "ruint", "montgomery")
R = 10000

def population(base):
    pop = {}
    for pb in BANDS:
        seed = base + 100 * pb + 84
        pop[pb] = semiprimes_pq(84, PER_BAND, seed) if pb == 42 else semiprimes_unbalanced(84, pb, PER_BAND, seed)
    return pop

def prices():
    cal = json.load(open("calibrate.json"))
    out = {}
    for ref in ("ruint", "montgomery"):
        names = cal["prices"][f"{ref} P1"]
        out[ref] = {t: sorted(cal["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1] for t in names}
    return out

class SpentMeter(Meter):
    """Records, for each candidate budget b (sorted), the meter total right after the first
    charge that takes it past b."""
    def __init__(self, cap, cands):
        super().__init__(cap)
        self.cands, self.ptr, self.spent = cands, 0, {}
    def tick(self, k=1):
        self.ops += k
        while self.ptr < len(self.cands) and self.ops > self.cands[self.ptr]:
            self.spent[self.cands[self.ptr]] = self.ops
            self.ptr += 1
        if self.ops > self.cap:
            raise Budget()

def run_alone(stage, N, cap, cands):
    mod = {"qs": qs, "ecm": ecm}.get(stage["t"])
    tr = {} if mod else None
    if mod:
        mod.TRACE = tr
    m = SpentMeter(cap, cands)
    try:
        d = LAMPS[stage["t"]](N, stage, m)
    except Budget:
        d = None
    if mod:
        mod.TRACE = None
    ok = bool(d) and 1 < d < N
    return {"T": m.ops if ok else None, "ops": m.ops, "spent": {str(b): s for b, s in m.spent.items()},
            "per_type": optypes.per_type(stage, tr, m.ops, m.tests, N)}

def map_job(args):
    pb, N = args
    out = {"N": str(N), "band": pb}
    for name, st in PRE.items():
        out[name] = run_alone(st, N, PRE_CAP, [b for b in FINE if b > 0] if name != "pm1" else [])
    for name, st in QS_VARIANTS.items():
        r = run_alone(st, N, QS_CAP, [])
        out[name] = {"T": r["T"], "ops": r["ops"], "per_type": r["per_type"]}
    return out

# ---- optimize -------------------------------------------------------------------------

def cost_of(per_type, pr):
    return float(sum(pr[t] * n for t, n in per_type.items()))

class Map:
    def __init__(self, rows, qs_name, PR):
        self.rows, self.n = rows, len(rows)
        self.band = np.array([r["band"] for r in rows])
        PRP = {"official": None, "ruint": PR["ruint"], "montgomery": PR["montgomery"]}
        price = lambda pt, P: float(sum(pt.values())) if P == "official" else cost_of(pt, PRP[P])
        # price per official op of each pre-stage, per band and pricing (from its alone runs)
        pi = {s: {P: {} for P in PRICINGS} for s in PRE}
        for s in PRE:
            for P in PRICINGS:
                for pb in sorted(set(self.band.tolist())):
                    rr = [r[s] for r in rows if r["band"] == pb]
                    pi[s][P][pb] = sum(price(x["per_type"], P) for x in rr) / sum(x["ops"] for x in rr)
        self.pi = pi
        self.qs = {P: np.array([price(r[qs_name]["per_type"], P) for r in rows]) for P in PRICINGS}
        assert all(r[qs_name]["T"] for r in rows), "qs alone missed on a tuning number"
        # per stage and budget index: success mask, and cost (success: exact; else: spent)
        self.T = {s: np.array([r[s]["T"] if r[s]["T"] is not None else np.inf for r in rows], dtype=float) for s in PRE}
        self.full = {s: {P: np.array([price(r[s]["per_type"], P) for r in rows]) for P in PRICINGS} for s in PRE}
        self.spent = {}
        for s in ("td", "rho", "ecm"):
            arr = np.zeros((len(FINE), self.n))
            for j, b in enumerate(FINE):
                if b == 0:
                    continue
                for i, r in enumerate(rows):
                    v = r[s]["spent"].get(str(b))
                    arr[j, i] = v if v is not None else r[s]["ops"]   # finished before passing b
            self.spent[s] = arr
        self.pib = {s: {P: np.array([pi[s][P][pb] for pb in self.band]) for P in PRICINGS} for s in PRE}

    def stage_terms(self, s, b, P):
        """(success mask, cost vector) of stage s at budget b (FINE value; pm1: 0/1)."""
        if s == "pm1":
            if b == 0:
                return None
            succ = np.isfinite(self.T["pm1"])
            return succ, self.full["pm1"][P]                       # success or not: full length
        if b == 0:
            return None
        succ = self.T[s] <= b
        j = FINE.index(b)
        spent = self.spent[s][j] * self.pib[s][P]
        return succ, np.where(succ, self.full[s][P], spent)

    def costs(self, vec, P):
        total = np.zeros(self.n)
        alive = np.ones(self.n, dtype=bool)
        for s, b in zip(("td", "rho", "pm1", "ecm"), vec):
            t = self.stage_terms(s, b, P)
            if t is None:
                continue
            succ, c = t
            total += np.where(alive, c, 0.0)
            alive &= ~succ
        total += np.where(alive, self.qs[P], 0.0)
        return total

    def fitness(self, vec, mask=None):
        mask = np.ones(self.n, dtype=bool) if mask is None else mask
        scores = {P: self.costs(vec, P)[mask].mean() / self.qs[P][mask].mean() for P in PRICINGS}
        return max(scores.values()), scores

def optimize(M, mask):
    best = None
    for bt in COARSE:
        for br in COARSE:
            for bp in PM1_OPTS:
                for be in COARSE:
                    f = M.fitness((bt, br, bp, be), mask)[0]
                    if best is None or f < best[0]:
                        best = (f, (bt, br, bp, be))
    vec = list(best[1])
    while True:
        moved = False
        for i, opts in enumerate((FINE, FINE, PM1_OPTS, FINE)):
            cur = M.fitness(tuple(vec), mask)[0]
            for o in opts:
                trial = vec.copy(); trial[i] = o
                f = M.fitness(tuple(trial), mask)[0]
                if f < cur - 1e-12:
                    cur, vec, moved = f, trial, True
        if not moved:
            return tuple(vec)

def boot_band(vals):
    rng = random.Random(2026)
    n = len(vals)
    s = sorted(math.log2(sum(rng.choice(vals) for _ in range(n)) / n) for _ in range(R))
    return s[int(0.025 * R)], s[int(0.975 * R) - 1]

def boot_overall(by_band):
    rng = random.Random(2026)
    tot = sum(len(v) for v in by_band.values())
    s = sorted(math.log2(sum(sum(rng.choice(v) for _ in range(len(v))) for v in by_band.values()) / tot) for _ in range(R))
    return s[int(0.025 * R)], s[int(0.975 * R) - 1]

def report(M, vec, mask, label):
    f, scores = M.fitness(vec, mask)
    bands = sorted(set(M.band[mask]))
    out = {"budgets": {"td": vec[0], "rho": vec[1], "pm1": "full" if vec[2] else 0, "ecm": vec[3]},
           "fitness": f, "score": scores, "band_ratio": {}, "worst_band": {}, "prediction": {}}
    for P in PRICINGS:
        c = M.costs(vec, P)
        out["band_ratio"][P] = {int(pb): c[M.band == pb].mean() / M.qs[P][M.band == pb].mean() for pb in bands}
        wb = max(out["band_ratio"][P], key=out["band_ratio"][P].get)
        out["worst_band"][P] = [wb, out["band_ratio"][P][wb]]
        by_band = {int(pb): list(c[M.band == pb]) for pb in bands}
        out["prediction"][P] = {"mean_log2": math.log2(c[mask].mean()), "ci95": boot_overall(by_band),
                                "bands": {pb: {"mean_log2": math.log2(sum(v) / len(v)), "ci95": boot_band(v)} for pb, v in by_band.items()},
                                "qs_mean_log2": math.log2(M.qs[P][mask].mean())}
    # best single lamp per band (hindsight; a pre-stage counts only if it finished every
    # number of the band within its cap)
    out["best_single_per_band"] = {}
    for P in PRICINGS:
        row = {}
        for pb in bands:
            sel = M.band == pb
            cand = {"qs": M.qs[P][sel].mean()}
            for s in PRE:
                if np.isfinite(M.T[s][sel]).all():
                    cand[s] = M.full[s][P][sel].mean()
            best = min(cand, key=cand.get)
            alloc = M.costs(vec, P)[sel].mean()
            row[int(pb)] = {"lamp": best, "alloc_over_best": alloc / cand[best]}
        out["best_single_per_band"][P] = row
    if vec[2]:
        off = (vec[0], vec[1], 0, vec[3])
        out["pm1_effect"] = {}
        for P in PRICINGS:
            con, coff = M.costs(vec, P), M.costs(off, P)
            reach = np.ones(M.n, dtype=bool)
            for s, b in zip(("td", "rho"), vec[:2]):
                if b:
                    reach &= ~(M.T[s] <= b)
            succ = reach & np.isfinite(M.T["pm1"])
            fail = reach & ~np.isfinite(M.T["pm1"])
            out["pm1_effect"][P] = {int(pb): {"saved_where_it_succeeds": float((coff - con)[succ & (M.band == pb)].sum() / max(1, (M.band == pb).sum())),
                                              "added_where_it_fails": float((con - coff)[fail & (M.band == pb)].sum() / max(1, (M.band == pb).sum())),
                                              "succeeds": int((succ & (M.band == pb)).sum()), "fails": int((fail & (M.band == pb)).sum())}
                                    for pb in bands}
    return out

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "map":
        workers = int(ARGS[1]) if len(ARGS) > 1 else 8
        pop = population(TUNING)
        jobs = [(pb, N) for pb in BANDS for N, p, q in pop[pb]]
        with Pool(workers) as pool:
            rows = pool.map(map_job, jobs, chunksize=2)
        json.dump({"bands": BANDS, "per_band": PER_BAND, "seeds": "4000000 + 100 pb + 84", "fine": FINE,
                   "rows": rows}, open("partition_map.json", "w"))
        for pb in BANDS:
            rr = [r for r in rows if r["band"] == pb]
            print(pb, {s: f"{sum(1 for r in rr if r[s]['T'] is not None)}/{len(rr)}" for s in PRE},
                  {q: round(math.log2(statistics.mean(r[q]["ops"] for r in rr)), 2) for q in QS_VARIANTS})
        sys.exit(0)
    data = json.load(open("partition_map.json"))
    assert data["fine"] == FINE
    rows = data["rows"]
    PR = prices()
    out = {}
    for qname in QS_VARIANTS:
        M = Map(rows, qname, PR)
        for pop_name, mask in (("mixed", np.ones(M.n, dtype=bool)), ("balanced control", M.band == 42)):
            vec = optimize(M, mask)
            out[f"{qname} | {pop_name}"] = r = report(M, vec, mask, pop_name)
            print(f"\n{qname} | {pop_name}: budgets {r['budgets']}  fitness {r['fitness']:.3f}  "
                  + "  ".join(f"{P[:4]} x{1 / r['score'][P]:.2f}" for P in PRICINGS) + "  (speed-up over qs alone)")
            for P in PRICINGS:
                pr = r["prediction"][P]
                print(f"  {P:10s} predicted log2 mean {pr['mean_log2']:.2f} [{pr['ci95'][0]:.2f}, {pr['ci95'][1]:.2f}]  qs alone {pr['qs_mean_log2']:.2f}"
                      f"  worst band {r['worst_band'][P][0]} (ratio {r['worst_band'][P][1]:.2f})")
                print("     bands: " + "  ".join(f"{pb}: {v['mean_log2']:.2f} [{v['ci95'][0]:.2f},{v['ci95'][1]:.2f}] r{r['band_ratio'][P][pb]:.2f}"
                                               for pb, v in pr["bands"].items()))
                print("     best single per band (hindsight): " + "  ".join(f"{pb}: {v['lamp']} x{v['alloc_over_best']:.2f}"
                                                                         for pb, v in r["best_single_per_band"][P].items()))
            if "pm1_effect" in r:
                for P in PRICINGS:
                    print(f"  pm1 {P}: " + "  ".join(f"{pb}: +{v['saved_where_it_succeeds']:.0f}/-{v['added_where_it_fails']:.0f} ({v['succeeds']}/{v['fails']})"
                                                     for pb, v in r["pm1_effect"][P].items()))
    json.dump({"allocations": out}, open("partition_alloc.json", "w"), indent=1)
