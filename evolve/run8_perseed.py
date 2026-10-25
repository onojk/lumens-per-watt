"""Run 8 per-seed paired comparison on the sealed numbers (added after the run; design, power
estimate and predictions in NOTES.md first). PLAN reporting rule: each seed, method X's best
against method Y's best from the same seed; a sign test over seeds plus the paired bootstrap.

Pairs: TPE vs evolution, TPE vs random. d_s = log2(fit TPE / fit other) on the sealed numbers.
Per-seed interval: numbers resampled within bands. Aggregate: mean of d_s over seeds,
(i) numbers resampled, seeds fixed; (ii) seeds and numbers resampled. Sealed misses count as a
loss in the sign test and are left out of the means.

  .venv/bin/python run8_perseed.py ARM  -> run8_ARM_perseed.json, stdout
  .venv/bin/python run8_perseed.py ARM X:Y [X:Y ...]  -> other pairs (d = log2(fit X / fit Y)),
      run8_ARM_perseed_posthoc.json
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

sealed = [t for v in R.sealed_set(arm).values() for t in v]
R.oracle.check(sealed)
ev = R.Evaluator(sealed, pr)
ref = {P: np.array([optypes.cost(x, P, pr) for x in ev.ref]) for P in PR}
groups = {}
for i, t in enumerate(sealed):
    groups.setdefault(band_of(t), []).append(i)
groups = [np.array(v) for v in groups.values()]

def costs(pt):
    rs = ev.per_number(pt)
    return any(r[0] is None for r in rs), {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}

def fit(c, i):
    return max(c[P][i].mean() / ref[P][i].mean() for P in PR)

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

def sign_p(k, n):
    """Two-sided exact binomial (p = 1/2)."""
    tail = sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)

by = {}
for r in data["results"]:
    by.setdefault(r["method"], {})[r["seed"]] = r
seeds = sorted(by["tpe"])
PAIRS = [tuple(a.split(":")) for a in ARGS[1:]] or [("tpe", "evolution"), ("tpe", "random")]
C = {(m, s): costs(by[m][s]["point"]) for m in {x for p in PAIRS for x in p} for s in seeds}
rng = random.Random(2026)
idxs = [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(B)]
allx = np.arange(len(sealed))
out = {"arm": arm, "pairs": {}}
print(f"{arm}: per-seed paired comparison, sealed {len(sealed)} numbers; d = log2(fit X / fit Y), < 0 = X better")
for X, other in PAIRS:
    rows, boot = [], {}
    for s in seeds:
        (mt, ct), (mo, co) = C[(X, s)], C[(other, s)]
        if mt or mo:
            d = math.inf if mt and not mo else (-math.inf if mo and not mt else float("nan"))
            rows.append({"seed": s, "d": d, "ci": None, "miss": {X: mt, other: mo}})
            continue
        vals = [math.log2(fit(ct, i) / fit(co, i)) for i in idxs]
        boot[s] = vals
        rows.append({"seed": s, "d": math.log2(fit(ct, allx) / fit(co, allx)), "ci": q(vals), "miss": None})
    n = sum(1 for r in rows if not math.isnan(r["d"]))
    k = sum(1 for r in rows if r["d"] < 0)
    clear = sum(1 for r in rows if r["ci"] is not None and r["ci"][1] < 0) + sum(1 for r in rows if r["d"] == -math.inf)
    clear_lose = sum(1 for r in rows if r["ci"] is not None and r["ci"][0] > 0) + sum(1 for r in rows if r["d"] == math.inf)
    fin = sorted(boot)
    mean_d = statistics.mean(r["d"] for r in rows if r["seed"] in boot)
    med_d = statistics.median(r["d"] for r in rows if r["seed"] in boot)
    agg_i = q([statistics.mean(boot[s][b] for s in fin) for b in range(B)])
    r2 = random.Random(2027)
    agg_ii = q([statistics.mean(boot[s][b] for s in (r2.choice(fin) for _ in fin)) for b in range(B)])
    out["pairs"][f"{X}_vs_{other}"] = {"rows": rows, "tpe_better_seeds": k, "of": n, "sign_p": sign_p(k, n),
                                       "clearly_better": clear, "clearly_worse": clear_lose, "seeds_in_means": fin,
                                       "mean_d": mean_d, "median_d": med_d, "ci_numbers": agg_i, "ci_seeds_and_numbers": agg_ii}
    print(f"\n{X} vs {other}: {X} better on {k}/{n} seeds (sign test p = {sign_p(k, n):.4f}); interval below 0 on {clear}, above 0 on {clear_lose}")
    print(f"  mean d over {len(fin)} seeds {mean_d:+.3f} (median {med_d:+.3f}); (i) numbers resampled [{agg_i[0]:+.3f}, {agg_i[1]:+.3f}]; "
          f"(ii) seeds and numbers [{agg_ii[0]:+.3f}, {agg_ii[1]:+.3f}]")
    for r in rows:
        ci = f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]" if r["ci"] else f"(sealed miss: {r['miss']})"
        print(f"    seed {r['seed']}: d {r['d']:+.3f} {ci}")
json.dump(out, open(f"run8_{arm}_perseed" + ("_posthoc" if ARGS[1:] else "") + ".json", "w"), indent=1)
