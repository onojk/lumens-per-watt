"""Generalization tests for the new qs genes (NOTES.md, "Run 8 wrap-up addendum ...
Generalization tests"; predictions there first). Budgets and order held at allocation A
(td 0, rho 5793, pm1 0, ECM 32768); final qs = the new genes (kc 4, bc 0.8994, mc 0.7341,
tc 1.1045, lc 1.6612) against qs + lc 1.4's genes. Fitness (c) against qs + lc 1.4 alone on the
same numbers; all three pricings; lampcore --types, cap 2^28.

Populations, fixed here before the run (fresh seeds 8800000 + 100 pb + bits, unused so far; all
through oracle.check):
  (a) mixed 72-bit: smaller factor 16, 20, 24, 28, 32 bits (unbalanced) and 36 (balanced), 80 each
      mixed 96-bit: 16, 20, 24, 28, 32, 36, 42 (unbalanced) and 48 (balanced), 80 each
  (b) balanced 84-bit: 240 numbers (the power of NOTES (2): an official effect of about 0.07
      log2 needs a few hundred numbers), seed 8800000 + 100 * 42 + 84

Reported per population: each genome's fitness and per-pricing scores, log2(fit new / fit old)
with the paired bootstrap resampling numbers within bands (10,000, random.Random(2026)), the
same per pricing, per-band ratios, the ACCEPT gate (no band > 1.5x qs + lc 1.4 alone under any
pricing) and misses.

  python3 newqs_general.py  -> newqs_general.json, stdout
"""
import sys
sys.argv[1:] = []
import json, math, random
import numpy as np
import optypes, oracle
import run8 as R
import run8_space as S
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many

PR = ("official", "ruint", "montgomery")
B = 10000
NEW = dict(R.A_POINT, kc=4, bc=0.8993889783377338, mc=0.7340990893362095, tc=1.1044621542694246, lc=1.6612269841697611)
OLD = dict(R.A_POINT, kc=32, bc=1.1, mc=0.25, tc=1.38, lc=1.4)
pr = optypes.prices()

def pop(bits, bands, per):
    out = {}
    for pb in bands:
        seed = 8800000 + 100 * pb + bits
        out[pb] = semiprimes_pq(bits, per, seed) if 2 * pb >= bits else semiprimes_unbalanced(bits, pb, per, seed)
    return out

POPS = {"(a) mixed 72": pop(72, (16, 20, 24, 28, 32, 36), 80),
        "(a) mixed 96": pop(96, (16, 20, 24, 28, 32, 36, 42, 48), 80),
        "(b) balanced 84": pop(84, (42,), 240)}

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

out = {}
for name, bypb in POPS.items():
    nums = [t for v in bypb.values() for t in v]
    oracle.check(nums)
    band = np.array([pb for pb, v in bypb.items() for _ in v])
    groups = [np.flatnonzero(band == pb) for pb in bypb]
    ref = {P: np.array([optypes.cost(x[4], P, pr) for x in run_many(R.REF, nums, R.CAP, types=True)]) for P in PR}
    G = {}
    for g, pt in (("new", NEW), ("old", OLD)):
        rs = run_many(S.to_genome(pt), nums, R.CAP, types=True)
        miss = sum(1 for r, (N, _, _) in zip(rs, nums) if not (r[1] is not None and 1 < int(r[1]) < N))
        G[g] = {"miss": miss, "c": {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}}
    sc = lambda c, i, P: c[P][i].mean() / ref[P][i].mean()
    fit = lambda c, i: max(sc(c, i, P) for P in PR)
    allx = np.arange(len(nums))
    rng = random.Random(2026)
    idxs = [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(B)]
    cn, co = G["new"]["c"], G["old"]["c"]
    res = {"n": len(nums), "bands": list(bypb), "genomes": {}}
    for g in ("new", "old"):
        c = G[g]["c"]
        per_band = {P: {pb: float(sc(c, gi, P)) for pb, gi in zip(bypb, groups)} for P in PR}
        worst = max((v, P, pb) for P in PR for pb, v in per_band[P].items())
        res["genomes"][g] = {"fitness": fit(c, allx), "scores": {P: sc(c, allx, P) for P in PR}, "per_band": per_band,
                             "misses": G[g]["miss"], "gate_worst": worst, "gate_pass": worst[0] <= 1.5 and not G[g]["miss"]}
    vals = [math.log2(fit(cn, i) / fit(co, i)) for i in idxs]
    res["new_over_old"] = {"ratio": fit(cn, allx) / fit(co, allx), "log2": math.log2(fit(cn, allx) / fit(co, allx)), "ci": q(vals)}
    res["new_over_old_by_pricing"] = {P: {"log2": math.log2(sc(cn, allx, P) / sc(co, allx, P)),
                                          "ci": q([math.log2(sc(cn, i, P) / sc(co, i, P)) for i in idxs])} for P in PR}
    out[name] = res
    print(f"\n{name}: {len(nums)} numbers, bands {list(bypb)}")
    for g in ("new", "old"):
        x = res["genomes"][g]
        print(f"  {g} qs genes (A's budgets): fitness {x['fitness']:.3f} (" + ", ".join(f"{P} {v:.3f}" for P, v in x["scores"].items())
              + f"); misses {x['misses']}; gate {'PASS' if x['gate_pass'] else 'FAIL'} (worst {x['gate_worst'][0]:.3f}, band {x['gate_worst'][2]}, {x['gate_worst'][1]})")
        for P in PR:
            print(f"     {P:10s} per band: " + "  ".join(f"{pb}: {v:.3f}" for pb, v in x["per_band"][P].items()))
    r = res["new_over_old"]
    print(f"  new / old robust: x{r['ratio']:.3f}, log2 {r['log2']:+.3f} [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
    print("  by pricing: " + "  ".join(f"{P} {v['log2']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}]" for P, v in res["new_over_old_by_pricing"].items()))
json.dump(out, open("newqs_general.json", "w"), indent=1, default=float)
