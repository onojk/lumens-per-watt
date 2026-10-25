"""Budget/order freedom beyond A (NOTES.md, "Budget/order freedom beyond A: design and
predictions"; written before this script). Per seed: the mixed arm's best (budgets, order and qs
genes searched) against the mixed-qs arm's best (qs genes only, budgets and order at A), same
method and seed; both arms share the tuning set per seed and the sealed set.

d_s = log2(fit mixed / fit mixed-qs) on the sealed numbers, < 0 = the freedom pays. Per-seed
interval: numbers resampled within bands. Aggregate: mean of d_s over seeds, (i) numbers
resampled, seeds fixed; (ii) seeds and numbers resampled. Sealed misses count in the sign test
and are left out of the means. Same machinery as run8_perseed.py.

  .venv/bin/python run8_freedom.py  -> run8_freedom.json, stdout
"""
import sys
sys.argv[1:] = []
import json, math, random, statistics
import numpy as np
import optypes
import run8 as R

PR = ("official", "ruint", "montgomery")
B = 10000
PAIRS = [("evolution", "evolution"), ("tpe", "tpe"), ("random", "random"), ("tpe-tuned", "tpe-warm")]
pr = optypes.prices()

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

def sign_p(k, n):
    """Two-sided exact binomial (p = 1/2)."""
    tail = sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)
sealed = [t for v in R.sealed_set("mixed").values() for t in v]
assert sealed == [t for v in R.sealed_set("mixed-qs").values() for t in v]
R.oracle.check(sealed)
ev = R.Evaluator(sealed, pr)
ref = {P: np.array([optypes.cost(x, P, pr) for x in ev.ref]) for P in PR}
groups = {}
for i, t in enumerate(sealed):
    groups.setdefault(min(t[1], t[2]).bit_length(), []).append(i)
groups = [np.array(v) for v in groups.values()]
by = {}
for arm in ("mixed", "mixed-qs"):
    for r in json.load(open(f"run8_{arm}.json"))["results"]:
        by[(arm, r["method"], r["seed"])] = r

def costs(pt):
    rs = ev.per_number(pt)
    return any(r[0] is None for r in rs), {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}

fit = lambda c, i: max(c[P][i].mean() / ref[P][i].mean() for P in PR)
rng = random.Random(2026)
idxs = [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(B)]
allx = np.arange(len(sealed))
seeds = R.SEEDS
out = {"pairs": {}}
print(f"budget/order freedom: d = log2(fit mixed X / fit mixed-qs Y), same seed, sealed {len(sealed)} numbers; < 0 = freedom pays")
for X, Y in PAIRS:
    rows, boot = [], {}
    for s in seeds:
        (mm, cm), (mq, cq) = costs(by[("mixed", X, s)]["point"]), costs(by[("mixed-qs", Y, s)]["point"])
        if mm or mq:
            d = math.inf if mm and not mq else (-math.inf if mq and not mm else float("nan"))
            rows.append({"seed": s, "d": d, "ci": None, "miss": {"mixed": mm, "mixed-qs": mq}})
            continue
        vals = [math.log2(fit(cm, i) / fit(cq, i)) for i in idxs]
        boot[s] = vals
        rows.append({"seed": s, "d": math.log2(fit(cm, allx) / fit(cq, allx)), "ci": q(vals), "miss": None,
                     "sealed": [fit(cm, allx), fit(cq, allx)]})
    n = sum(1 for r in rows if not math.isnan(r["d"]))
    k = sum(1 for r in rows if r["d"] < 0)
    below = sum(1 for r in rows if (r["ci"] and r["ci"][1] < 0) or r["d"] == -math.inf)
    above = sum(1 for r in rows if (r["ci"] and r["ci"][0] > 0) or r["d"] == math.inf)
    fin = sorted(boot)
    mean_d = statistics.mean(boot_d := [r["d"] for r in rows if r["seed"] in boot])
    med_d = statistics.median(boot_d)
    agg_i = q([statistics.mean(boot[s][b] for s in fin) for b in range(B)])
    r2 = random.Random(2027)
    agg_ii = q([statistics.mean(boot[s][b] for s in (r2.choice(fin) for _ in fin)) for b in range(B)])
    key = f"mixed {X} vs mixed-qs {Y}"
    out["pairs"][key] = {"rows": rows, "mixed_better_seeds": k, "of": n, "sign_p": sign_p(k, n), "below": below, "above": above,
                         "seeds_in_means": fin, "mean_d": mean_d, "median_d": med_d, "ci_numbers": agg_i, "ci_seeds_and_numbers": agg_ii}
    print(f"\n{key}: mixed better on {k}/{n} seeds (sign p = {sign_p(k, n):.4f}); interval below 0 on {below}, above 0 on {above}")
    print(f"  mean d over {len(fin)} seeds {mean_d:+.3f} (median {med_d:+.3f}); (i) [{agg_i[0]:+.3f}, {agg_i[1]:+.3f}]; (ii) [{agg_ii[0]:+.3f}, {agg_ii[1]:+.3f}]")
    for r in rows:
        extra = f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]  sealed {r['sealed'][0]:.3f} / {r['sealed'][1]:.3f}" if r["ci"] else f"(sealed miss: {r['miss']})"
        print(f"    seed {r['seed']}: d {r['d']:+.3f} {extra}")
json.dump(out, open("run8_freedom.json", "w"), indent=1)
