"""Primes and gaps (NOTES.md, "Primes and gaps as the reference line"; predictions written
there first): does any lamp's cost on the partition tuning numbers depend on p's arithmetic
beyond its size? Map only, no new runs; never fitness.

Per lamp, a response (td, rho, ECM: log2 ops-to-success on the numbers it solved within its
cap; p-1: success; qs + lc 1.4: log2 ops) against features of the smaller factor p (gaps before
and after p over ln p, twin flag, log LPF(p - 1) / log p, log LPF(p + 1) / log p, p mod 4,
p mod 3, log p within the band). Pooled Spearman over within-band ranks; permutation test
permuting responses within bands (10,000, random.Random(2026)); Holm over every pair tested.

  python3 primes_gaps.py  -> primes_gaps.json, stdout
"""
import sys
sys.argv[1:] = []
import json, math, random
import numpy as np
import sympy
import partition as P
import oracle

R = 10000
rows = json.load(open("partition_map.json"))["rows"]
pop = P.population(P.TUNING)
small = {str(N): min(p, q) for pb in P.BANDS for N, p, q in pop[pb]}
oracle.check([t for pb in P.BANDS for t in pop[pb]])

def lpf_ratio(n, p):
    return math.log(max(sympy.factorint(n))) / math.log(p)

feats = {"gap before / ln p": [], "gap after / ln p": [], "twin": [], "LPF(p-1)": [], "LPF(p+1)": [],
         "p mod 4": [], "p mod 3": [], "log p": []}
for r in rows:
    p = small[r["N"]]
    lp = math.log(p)
    feats["gap before / ln p"].append((p - sympy.prevprime(p)) / lp)
    feats["gap after / ln p"].append((sympy.nextprime(p) - p) / lp)
    feats["twin"].append(float(sympy.isprime(p - 2) or sympy.isprime(p + 2)))
    feats["LPF(p-1)"].append(lpf_ratio(p - 1, p))
    feats["LPF(p+1)"].append(lpf_ratio(p + 1, p))
    feats["p mod 4"].append(p % 4)
    feats["p mod 3"].append(p % 3)
    feats["log p"].append(lp)
band = np.array([r["band"] for r in rows])
resp = {}
for lamp in ("td", "rho", "ecm"):
    resp[lamp] = np.array([math.log2(r[lamp]["T"]) if r[lamp]["T"] is not None else np.nan for r in rows])
resp["pm1"] = np.array([1.0 if r["pm1"]["T"] is not None else 0.0 for r in rows])
resp["qs + lc 1.4"] = np.array([math.log2(r["qs + lc 1.4"]["ops"]) for r in rows])

def within_band_ranks(x, mask):
    out = np.full(len(x), np.nan)
    for pb in P.BANDS:
        idx = np.flatnonzero((band == pb) & mask)
        if len(idx) < 3:
            continue
        v = np.asarray(x)[idx]
        order = np.argsort(np.argsort(v, kind="stable"), kind="stable").astype(float)
        # average ties
        for val in np.unique(v):
            t = v == val
            order[t] = order[t].mean()
        out[idx] = (order - order.mean()) / (order.std() or 1.0)
    return out

results = []
rng = random.Random(2026)
for lamp, y in resp.items():
    mask = ~np.isnan(y)
    for name, x in feats.items():
        x = np.asarray(x, dtype=float)
        rx, ry = within_band_ranks(x, mask), within_band_ranks(y, mask)
        use = ~np.isnan(rx) & ~np.isnan(ry)
        if use.sum() < 10 or np.nanstd(rx[use]) == 0 or np.nanstd(ry[use]) == 0:
            continue
        rho_obs = float(np.mean(rx[use] * ry[use]))
        groups = [np.flatnonzero(use & (band == pb)) for pb in P.BANDS]
        groups = [g for g in groups if len(g)]
        perm_ry = ry.copy()
        count = 0
        for _ in range(R):
            for g in groups:
                vals = list(ry[g]); rng.shuffle(vals); perm_ry[g] = vals
            if abs(np.mean(rx[use] * perm_ry[use])) >= abs(rho_obs) - 1e-12:
                count += 1
        results.append({"lamp": lamp, "feature": name, "n": int(use.sum()), "bands": int(len(groups)),
                        "rank_corr": rho_obs, "p": (count + 1) / (R + 1)})
# Holm
m = len(results)
order = sorted(range(m), key=lambda i: results[i]["p"])
prev = 0.0
for rank, i in enumerate(order):
    adj = min(1.0, max(prev, (m - rank) * results[i]["p"]))
    results[i]["p_holm"] = adj
    prev = adj
print(f"{m} (lamp, feature) tests; Holm-adjusted p < 0.05 marked *")
for lamp in resp:
    print(f"\n{lamp}:")
    for r in results:
        if r["lamp"] == lamp:
            print(f"  {r['feature']:18s} n {r['n']:3d} ({r['bands']} bands)  rank corr {r['rank_corr']:+.3f}  p {r['p']:.4f}  Holm {r['p_holm']:.4f}{'  *' if r['p_holm'] < 0.05 else ''}")
json.dump({"tests": m, "results": results}, open("primes_gaps.json", "w"), indent=1)
