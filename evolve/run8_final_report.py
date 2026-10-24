"""Run 8 report for the mixed arms (PLAN.md, Run 8 design; written and committed before the
mixed arm ran). Reads run8_ARM.json.

Per method (8 seeds):
- best-of-8 and median-of-8 fitness on the tuning sets; each seed's best re-scored on the
  sealed numbers (80 per band);
- T1 / T2 per seed (from the run): median, IQR, and how many seeds reached each;
- the winning genomes split into budgets / order and qs genes;
- OVERFIT bracket per run: the tuning-to-sealed gap g = log2(sealed / tuning) of the run's best
  genome, by a paired bootstrap that resamples the tuning numbers and the sealed numbers
  within bands (10,000, random.Random(2026)), the same resampled numbers for the genome and
  for allocation A. Against qs + lc 1.4 alone's gap (0 by construction: fitness is a ratio to
  it), "overfit at all" if g's interval lies above 0; against A's gap, OVERFIT if the interval
  of g - g_A lies above 0 (the primary bar).
- per-band sealed ratios to qs + lc 1.4 alone for each method's best-of-8 genome, all pricings.
Prediction clauses (primary TPE against evolution, as written in PLAN):
- (a) TPE reaches a fitness at least as good as evolution's best-of-8 final fitness within
  fewer evaluations: the evaluation at which TPE's best-of-8 trajectory (the best over the 8
  seeds of each seed's best so far, by evaluation index) first reaches evolution's best-of-8
  final fitness, against the evaluation at which evolution's best-of-8 reached it;
- (b) at the full budget TPE's best ties or beats evolution's best: the paired bootstrap of
  log2(fitness of TPE's best-of-8 genome / evolution's) on the same sealed numbers (resampled
  within bands); TIE if the interval includes 0.
Random search is predicted clearly worst. tpe-tuned and evolution-fresh are reported
separately. For mixed-qs: the qs-gene probe (warm-started TPE) against cold TPE, and the
probe's best against A on the sealed numbers: "A near-optimal" if the paired interval
includes 0 or lies above it, else "partition study under-explored by Z" (Z = A / best).

  .venv/bin/python run8_final_report.py ARM  -> run8_ARM_final.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, statistics
import numpy as np
import optypes
import run8 as R

PR = ("official", "ruint", "montgomery")
B = 10000
arm = ARGS[0]
data = json.load(open(f"run8_{arm}.json"))
pr = optypes.prices()

def band_of(t):
    return min(t[1], t[2]).bit_length()

class Costs:
    """Per-number costs of a point and of the reference on one set, for paired resampling."""
    def __init__(self, ev, pt):
        rs = ev.per_number(pt)
        self.miss = any(r[0] is None for r in rs)
        self.c = {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}
        self.ref = {P: np.array([optypes.cost(x, P, pr) for x in ev.ref]) for P in PR}
    def fit(self, idx):
        return max(self.c[P][idx].mean() / self.ref[P][idx].mean() for P in PR)

def groups_of(nums):
    g = {}
    for i, t in enumerate(nums):
        g.setdefault(band_of(t), []).append(i)
    return [np.array(v) for v in g.values()]

def resample(groups, rng):
    return np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups])

def q(vals):
    vals = sorted(vals)
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]

sealed_nums = [t for v in R.sealed_set(arm).values() for t in v]
R.oracle.check(sealed_nums)
ev_sealed = R.Evaluator(sealed_nums, pr)
g_sealed = groups_of(sealed_nums)
cA_sealed = Costs(ev_sealed, R.A_POINT)

by = {}
for r in data["results"]:
    by.setdefault(r["method"], []).append(r)
out = {"arm": arm, "methods": {}}
best_costs = {}
for m, rs in by.items():
    rs = sorted(rs, key=lambda r: r["seed"])
    rows = []
    for r in rs:
        tun_nums = R.tuning_set(arm, r["seed"])
        ev_t = R.Evaluator(tun_nums, pr)
        g_t = groups_of(tun_nums)
        cg_t, cA_t = Costs(ev_t, r["point"]), Costs(ev_t, R.A_POINT)
        cg_s = Costs(ev_sealed, r["point"])
        rng = random.Random(2026)
        gaps, diffs = [], []
        for _ in range(B):
            it, is_ = resample(g_t, rng), resample(g_sealed, rng)
            gg = math.log2(cg_s.fit(is_) / cg_t.fit(it))
            ga = math.log2(cA_sealed.fit(is_) / cA_t.fit(it))
            gaps.append(gg); diffs.append(gg - ga)
        all_t, all_s = np.arange(len(tun_nums)), np.arange(len(sealed_nums))
        row = {"seed": r["seed"], "tuning": cg_t.fit(all_t), "sealed": cg_s.fit(all_s), "point": r["point"],
               "evaluations": r["evaluations"], "evaluations_to_best": r["evaluations_to_best"],
               "gap": math.log2(cg_s.fit(all_s) / cg_t.fit(all_t)), "gap_ci": q(gaps),
               "gap_minus_A": math.log2(cg_s.fit(all_s) / cg_t.fit(all_t)) - math.log2(cA_sealed.fit(all_s) / cA_t.fit(all_t)),
               "gap_minus_A_ci": q(diffs), "convergence": r.get("convergence"), "trace": r.get("trace")}
        row["sealed_miss"] = cg_s.miss          # a sealed number not factored within the cap
        if cg_s.miss:                           # scored as Evaluator scores a miss (added after the run)
            row["sealed"], row["gap"], row["gap_minus_A"] = R.MISS_FITNESS, math.inf, math.inf
        row["overfit_at_all"] = row["gap_ci"][0] > 0 or cg_s.miss
        row["OVERFIT"] = row["gap_minus_A_ci"][0] > 0 or cg_s.miss
        rows.append(row)
        best_costs.setdefault(m, {})[r["seed"]] = cg_s
    tun = [x["tuning"] for x in rows]
    bi = min(range(len(rows)), key=lambda i: tun[i])
    conv = [x["convergence"] for x in rows if x["convergence"]]
    def agg(key):
        v = [c[key] for c in conv if c[key] is not None]
        if not v:
            return {"reached": 0, "of": len(conv)}
        qs_ = np.percentile(v, [25, 50, 75])
        return {"reached": len(v), "of": len(conv), "median": float(qs_[1]), "iqr": [float(qs_[0]), float(qs_[2])]}
    best = rows[bi]
    cb = best_costs[m][best["seed"]]
    per_band = {P: {} for P in PR}
    for P in PR:
        for pb, idx in zip(sorted({band_of(t) for t in sealed_nums}), [np.array([i for i, t in enumerate(sealed_nums) if band_of(t) == b]) for b in sorted({band_of(t) for t in sealed_nums})]):
            per_band[P][pb] = float(cb.c[P][idx].mean() / cb.ref[P][idx].mean())
    out["methods"][m] = {"rows": [{k: v for k, v in x.items() if k != "trace"} for x in rows],
                         "best_of_8": {"seed": best["seed"], "tuning": best["tuning"], "sealed": best["sealed"], "point": best["point"]},
                         "median_of_8_tuning": statistics.median(tun), "median_of_8_sealed": statistics.median(x["sealed"] for x in rows),
                         "T1": agg("T1"), "T2": agg("T2"), "overfit_runs": sum(x["OVERFIT"] for x in rows),
                         "overfit_at_all_runs": sum(x["overfit_at_all"] for x in rows), "per_band_sealed_best": per_band}

def best_traj(m):
    """Best-of-8 trajectory: at each evaluation index, the best over seeds of each seed's best so far."""
    rows = out["methods"][m]["rows"]
    traces = [r["trace"] for r in by[m]]
    n = max(len(t) for t in traces)
    cur = [math.inf] * len(traces)
    traj = []
    for i in range(n):
        for k, t in enumerate(traces):
            if i < len(t):
                cur[k] = min(cur[k], t[i][1])
        traj.append(min(cur))
    return traj

if "evolution" in out["methods"] and "tpe" in out["methods"] and by["tpe"][0].get("trace"):
    E, T = out["methods"]["evolution"], out["methods"]["tpe"]
    target = E["best_of_8"]["tuning"]
    te, tt = best_traj("evolution"), best_traj("tpe")
    tol = target * (1 + 1e-12)         # the recomputed target can differ from the traced value in the last ulp
    ie = next((i + 1 for i, f in enumerate(te) if f <= tol), None)
    it_ = next((i + 1 for i, f in enumerate(tt) if f <= tol), None)
    out["clause_a"] = {"target": target, "evolution_evaluations": ie, "tpe_evaluations": it_,
                       "holds": it_ is not None and ie is not None and it_ < ie}
    ce, ct = best_costs["evolution"][E["best_of_8"]["seed"]], best_costs["tpe"][T["best_of_8"]["seed"]]
    rng = random.Random(2026)
    vals = [math.log2(ct.fit(idx) / ce.fit(idx)) for idx in (resample(g_sealed, rng) for _ in range(B))]
    lo, hi = q(vals)
    pt = math.log2(ct.fit(np.arange(len(sealed_nums))) / ce.fit(np.arange(len(sealed_nums))))
    out["clause_b"] = {"log2_tpe_over_evolution": pt, "ci": [lo, hi], "tie": lo <= 0 <= hi, "tpe_better": hi < 0,
                       "holds": lo <= 0}
    out["random_clearly_worst"] = all(out["methods"]["random"]["best_of_8"]["sealed"] > out["methods"][m]["best_of_8"]["sealed"]
                                      for m in ("evolution", "tpe"))
if arm == "mixed-qs":
    W, T = out["methods"]["tpe-warm"], out["methods"]["tpe"]
    cw, ct = best_costs["tpe-warm"][W["best_of_8"]["seed"]], best_costs["tpe"][T["best_of_8"]["seed"]]
    rng = random.Random(2026)
    idxs = [resample(g_sealed, rng) for _ in range(B)]
    lo, hi = q([math.log2(cw.fit(i) / ct.fit(i)) for i in idxs])
    out["probe_vs_cold_tpe"] = {"log2_warm_over_cold": math.log2(W["best_of_8"]["sealed"] / T["best_of_8"]["sealed"]), "ci": [lo, hi]}
    best_m = min(out["methods"], key=lambda m: out["methods"][m]["best_of_8"]["sealed"])
    cbm = best_costs[best_m][out["methods"][best_m]["best_of_8"]["seed"]]
    lo, hi = q([math.log2(cbm.fit(i) / cA_sealed.fit(i)) for i in idxs])
    fA = cA_sealed.fit(np.arange(len(sealed_nums)))
    fb = out["methods"][best_m]["best_of_8"]["sealed"]
    out["A_check"] = {"best_method": best_m, "best_sealed": fb, "A_sealed": fA, "log2_best_over_A": math.log2(fb / fA), "ci": [lo, hi],
                      "verdict": "A near-optimal" if hi >= 0 else f"partition study under-explored by {fA / fb:.3f}x"}
json.dump(out, open(f"run8_{arm}_final.json", "w"), indent=1)

fmt = lambda p: (f"order {'>'.join(x[:3] for x in p['order'])} td {p['td']} rho {p['rho']} pm1 {'full' if p['pm1'] else 0} ecm {p['ecm']}",
                 f"kc {p['kc']} bc {p['bc']:.2f} mc {p['mc']:.3f} tc {p['tc']:.2f} lc {p['lc']:.2f}")
print(f"{arm}: {data['budget']} evaluations per run, seeds {data['seeds'][0]}-{data['seeds'][-1]}; fitness = robust ratio to qs + lc 1.4 alone\n")
for m, o in out["methods"].items():
    b = o["best_of_8"]
    print(f"{m}: best-of-8 tuning {b['tuning']:.3f} (seed {b['seed']}), sealed {b['sealed']:.3f}; median-of-8 tuning {o['median_of_8_tuning']:.3f}, sealed {o['median_of_8_sealed']:.3f}")
    for k in ("T1", "T2"):
        a = o[k]
        print(f"  {k}: reached {a['reached']}/{a['of']}" + (f", median {a['median']:.0f}, IQR [{a['iqr'][0]:.0f}, {a['iqr'][1]:.0f}]" if a.get("median") is not None else ""))
    print(f"  OVERFIT (gap above A's): {o['overfit_runs']}/8 runs; overfit at all (gap above 0): {o['overfit_at_all_runs']}/8")
    a, bq = fmt(b["point"])
    print(f"  winner: {a} | {bq}")
    for P in PR:
        print(f"  sealed per band, {P}: " + "  ".join(f"{pb}: {v:.3f}" for pb, v in o["per_band_sealed_best"][P].items()))
    for x in o["rows"]:
        a, bq = fmt(x["point"])
        print(f"    seed {x['seed']}: tuning {x['tuning']:.3f} sealed {'MISS' if x['sealed_miss'] else format(x['sealed'], '.3f')} gap {x['gap']:+.3f} [{x['gap_ci'][0]:+.3f},{x['gap_ci'][1]:+.3f}]"
              f" minus A {x['gap_minus_A']:+.3f} [{x['gap_minus_A_ci'][0]:+.3f},{x['gap_minus_A_ci'][1]:+.3f}]{' OVERFIT' if x['OVERFIT'] else ''} | {a} | {bq}")
for k in ("clause_a", "clause_b", "random_clearly_worst", "probe_vs_cold_tpe", "A_check"):
    if k in out:
        print(f"\n{k}: {out[k]}")
