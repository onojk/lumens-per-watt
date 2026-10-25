"""The new qs genes on balanced numbers: should they replace qs + lc 1.4 as the reference?
(NOTES.md, "After Run 8: ... (2)"; design, power, replacement rule and predictions there first.)

Fresh balanced numbers semiprimes_pq(bits, 240, 8700000 + bits), bits 54..84 step 6, all
through oracle.check. Each genome alone, lampcore --types, cap 2^28: the new qs, qs + lc 1.4,
N51-0917's qs (information only). Per size: log2(mean cost new / mean cost qs + lc 1.4) per
pricing with a paired bootstrap (10,000, random.Random(2026)), the robust ratio (c), the (e)
call (new / old / undecided), the median per-number log2 ratio, misses. Pooled: the mean over
the six sizes of the per-size log2 ratio, numbers resampled within each size.

  python3 newqs_balanced.py  -> newqs_balanced.json, stdout
"""
import sys
sys.argv[1:] = []
import json, math, random, statistics
import numpy as np
import optypes, oracle
import partition as P
from fastlamps import semiprimes_pq, run_many

SIZES = (54, 60, 66, 72, 78, 84)
PER = 240
CAP = 2 ** 28
B = 10000
PR = ("official", "ruint", "montgomery")
NEW_QS = {"t": "qs", "kc": 4, "bc": 0.8993889783377338, "mc": 0.7340990893362095,
          "tc": 1.1044621542694246, "lc": 1.6612269841697611}
G = {"new qs": [NEW_QS], "qs + lc 1.4": [P.QS_VARIANTS["qs + lc 1.4"]], "N51-0917's qs": [P.QS_VARIANTS["N51-0917's qs"]]}
pr = optypes.prices()

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

C, miss = {}, {}
for bits in SIZES:
    nums = semiprimes_pq(bits, PER, 8700000 + bits)
    oracle.check(nums)
    for name, g in G.items():
        rs = run_many(g, nums, CAP, types=True)
        ok = [r[1] is not None and 1 < int(r[1]) < N for r, (N, _, _) in zip(rs, nums)]
        miss[(name, bits)] = ok.count(False)
        C[(name, bits)] = {Pn: np.array([optypes.cost(r[4], Pn, pr) for r in rs]) for Pn in PR}

rng = random.Random(2026)
IDX = {bits: [np.array([rng.randrange(PER) for _ in range(PER)]) for _ in range(B)] for bits in SIZES}
out = {"sizes": SIZES, "per_size": PER, "seeds": "8700000 + bits", "misses": {f"{k[0]} | {k[1]}": v for k, v in miss.items()}, "cmp": {}}

def compare(a, b):
    res, boots = {}, {Pn: [] for Pn in PR}
    for bits in SIZES:
        ca, cb = C[(a, bits)], C[(b, bits)]
        row = {}
        for Pn in PR:
            vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in IDX[bits]]
            boots[Pn].append(vals)
            row[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": q(vals),
                       "median_per_number_log2": statistics.median(np.log2(ca[Pn] / cb[Pn]))}
        row["robust"] = max(2 ** row[Pn]["log2"] for Pn in PR)
        lo_all = all(row[Pn]["ci"][1] < 0 for Pn in PR)
        hi_all = all(row[Pn]["ci"][0] > 0 for Pn in PR)
        row["call"] = a if lo_all else (b if hi_all else "undecided")
        row["any_pricing_above_0"] = any(row[Pn]["ci"][0] > 0 for Pn in PR)
        res[bits] = row
    pooled = {}
    for Pn in PR:
        pts = statistics.mean(res[bits][Pn]["log2"] for bits in SIZES)
        vals = [statistics.mean(boots[Pn][k][j] for k in range(len(SIZES))) for j in range(B)]
        pooled[Pn] = {"log2": pts, "ci": q(vals)}
    return res, pooled

for a, b in (("new qs", "qs + lc 1.4"), ("N51-0917's qs", "qs + lc 1.4"), ("new qs", "N51-0917's qs")):
    res, pooled = compare(a, b)
    out["cmp"][f"{a} / {b}"] = {"per_size": res, "pooled": pooled}
    print(f"\n{a} / {b}: log2 mean-cost ratio [paired 95%]; ratio; median per-number log2")
    for bits in SIZES:
        r = res[bits]
        print(f"  {bits}: " + "  ".join(f"{Pn[:4]} {r[Pn]['log2']:+.3f} [{r[Pn]['ci'][0]:+.3f},{r[Pn]['ci'][1]:+.3f}] x{2 ** r[Pn]['log2']:.3f} (med {r[Pn]['median_per_number_log2']:+.3f})" for Pn in PR)
              + f"  | robust {r['robust']:.3f}  call: {r['call']}")
    print("  pooled (mean of per-size log2): " + "  ".join(f"{Pn[:4]} {pooled[Pn]['log2']:+.3f} [{pooled[Pn]['ci'][0]:+.3f},{pooled[Pn]['ci'][1]:+.3f}] x{2 ** pooled[Pn]['log2']:.3f}" for Pn in PR))
print("\nmisses: " + ", ".join(f"{k[0]} {k[1]}: {v}" for k, v in miss.items() if v) if any(miss.values()) else "\nmisses: none")
nm = out["cmp"]["new qs / qs + lc 1.4"]
rule = {"never_clearly_worse": not any(nm["per_size"][b]["any_pricing_above_0"] for b in SIZES),
        "no_misses": not any(v for (n, _), v in miss.items() if n == "new qs"),
        "pooled_all_below_0": all(nm["pooled"][Pn]["ci"][1] < 0 for Pn in PR)}
rule["replace"] = all(rule.values())
out["replacement_rule"] = rule
print(f"replacement rule: {rule}")
json.dump(out, open("newqs_balanced.json", "w"), indent=1, default=float)
