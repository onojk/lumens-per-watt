"""Run 8 sanity-arm summary with paired intervals (PLAN.md reporting rules): for each method's
best-of-8 genome and its median genomes (ranks 4 and 5 of 8 by tuning fitness), fitness against
qs + lc 1.4 alone on the seed's tuning set and on the sealed set, with a paired bootstrap of
log2(fitness) over resampled numbers (fitness is already a ratio to qs alone on the same
numbers; 10,000 resamples, random.Random(2026)). Pass: the median genomes' sealed intervals
do not lie above 0 (not worse than qs alone beyond noise). Also: Optuna's own time per trial
on a free objective (340 and 1,360 trials), for the time estimate.

  .venv/bin/python run8_paired.py sanity  -> run8_sanity_paired.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, statistics, time
import numpy as np
import optypes
import run8 as R

arm = ARGS[0]
data = json.load(open(f"run8_{arm}.json"))
pr = optypes.prices()
PR = ("official", "ruint", "montgomery")

def per_number(ev, pt):
    rs = ev.per_number(pt)
    return {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}

def paired(ev, pt):
    c = per_number(ev, pt)
    ref = {P: np.array([optypes.cost(x, P, pr) for x in ev.ref]) for P in PR}
    fit = lambda idx: max(c[P][idx].mean() / ref[P][idx].mean() for P in PR)
    n = len(ev.nums)
    rng = random.Random(2026)
    vals = sorted(math.log2(fit(np.array([rng.randrange(n) for _ in range(n)]))) for _ in range(10000))
    return fit(np.arange(n)), (vals[250], vals[9749])

sealed = R.Evaluator([t for v in R.sealed_set(arm).values() for t in v], pr)
out = {}
by = {}
for r in data["results"]:
    by.setdefault(r["method"], []).append(r)
for m, rs in by.items():
    rs = sorted(rs, key=lambda r: r["fitness"])
    picks = {"best-of-8": rs[0], "median rank 4": rs[3], "median rank 5": rs[4]}
    out[m] = {"median_of_8_tuning": statistics.median(r["fitness"] for r in rs)}
    for label, r in picks.items():
        tun_ev = R.Evaluator(R.tuning_set(arm, r["seed"]), pr)
        ft, ct = paired(tun_ev, r["point"])
        fs, cs = paired(sealed, r["point"])
        out[m][label] = {"seed": r["seed"], "tuning": ft, "tuning_ci_log2": ct, "sealed": fs, "sealed_ci_log2": cs}
    med_sealed_above = all(out[m][k]["sealed_ci_log2"][0] > 0 for k in ("median rank 4", "median rank 5"))
    out[m]["passed"] = not med_sealed_above
# Optuna overhead per trial (free objective)
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
over = {}
for n in (340, 1360):
    study = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=0))
    t = time.perf_counter()
    study.optimize(lambda tr: sum(v if isinstance(v, (int, float)) else 0 for v in R.tpe_space(tr).values() if not isinstance(v, tuple)) * 0.0, n_trials=n)
    over[n] = (time.perf_counter() - t) / n
out["optuna_seconds_per_trial_free_objective"] = over
out["secs_per_run"] = {m: sorted(r["secs"] for r in rs) for m, rs in by.items()}
json.dump(out, open(f"run8_{arm}_paired.json", "w"), indent=1)
for m in by:
    o = out[m]
    print(f"{m}: median-of-8 tuning {o['median_of_8_tuning']:.3f}; {'PASSED' if o['passed'] else 'FAILED'}")
    for k in ("best-of-8", "median rank 4", "median rank 5"):
        v = o[k]
        print(f"  {k:14s} (seed {v['seed']}): tuning {v['tuning']:.3f} [{2 ** v['tuning_ci_log2'][0]:.3f}, {2 ** v['tuning_ci_log2'][1]:.3f}]   "
              f"sealed {v['sealed']:.3f} [{2 ** v['sealed_ci_log2'][0]:.3f}, {2 ** v['sealed_ci_log2'][1]:.3f}]")
print("\nOptuna's own time per trial (free objective):", {k: f"{v * 1000:.1f} ms" for k, v in over.items()})
for m, s in out["secs_per_run"].items():
    print(f"secs per run, {m}: median {statistics.median(s):.0f} (min {min(s):.0f}, max {max(s):.0f}); per evaluation {statistics.median(s) / data['budget']:.3f} s")
