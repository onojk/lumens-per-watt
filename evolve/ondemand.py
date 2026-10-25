"""On-demand A selection: measurement (NOTES.md, "On-demand A: measurement plan and predictions";
rule version 3, accepted by ondemand_accept.py). Information plus the gate; lampcore --types,
cap 2^28; the frozen reference is qs + lc 1.4 with a_mode = enumerate.

  R1  map numbers 72/78/84/90/96 (typemix.load), reported on all numbers and on the numbers
      outside the acceptance sample (the first 2 per band, 72 numbers, on which the rule's three
      amendments were shaped): qs + lc 1.4's genes ("old"), the new genes
      ("new") and N51-0917's qs ("n51"), each alone under enumerate and on_demand. Per size and
      pricing: X / frozen reference, X on_demand / X enumerate, new / old and n51 / old with both
      on_demand (log2 with the paired bootstrap, numbers resampled within bands, 10,000,
      random.Random(2026)); setup_full per run and its ruint share; polynomials per run
      (sieve_scan / (2M + 1)); official ops excluding setup_full; misses; the gate per genome
      against the frozen reference with per-band intervals (PASS: every band's upper bound
      <= 1.5 under every pricing and no misses; FAIL: a band's lower bound > 1.5 or a miss;
      else BORDERLINE).
  R2  the replacement rule as pre-registered and as coded in newqs_balanced.py: balanced
      semiprimes_pq(bits, 240, 8700000 + bits), 54-84 step 6, new / old with both on_demand.
  R3  balanced control: the partition optimizer on band 42 of partition_map.json with the
      final qs's costs = qs + lc 1.4 on_demand (pre-stage records unchanged).

  python3 ondemand.py  -> ondemand.json, stdout
"""
import sys
sys.argv[1:] = []
import json, math, random, statistics
import numpy as np
import optypes, oracle
import partition as P
import typemix as TM
from fastlamps import semiprimes_pq, run_many

PR3 = ("official", "ruint", "montgomery")
B = 10000
pr = optypes.prices()
G = {"old": dict(P.QS_VARIANTS["qs + lc 1.4"]), "new": dict(TM.NEW), "n51": dict(P.QS_VARIANTS["N51-0917's qs"])}
MODES = ("enumerate", "on_demand")

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

def runs(g, nums):
    rs = run_many([g], nums, P.QS_CAP, types=True)
    miss = sum(1 for r, (N, _, _) in zip(rs, nums) if not (r[1] is not None and 1 < int(r[1]) < N))
    pts = [{k: v for k, v in r[4].items() if v} for r in rs]
    return miss, pts, {Pn: np.array([optypes.cost(c, Pn, pr) for c in pts]) for Pn in PR3}

def m_of(N, g):
    lnN = math.log(N)
    Bf = max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    return max(64, int(g.get("mc", 4.0) * Bf))

out = {"R1": {}, "R2": {}, "R3": {}}
# ---------------- R1
def r1_summary(R_all, nums, band, keep):
    """R1 statistics on the numbers selected by `keep` (misses counted on those numbers only)."""
    ki = np.flatnonzero(keep)
    nk = [nums[i] for i in ki]
    bk = band[ki]
    R = {}
    for key, (okv, pts, c) in R_all.items():
        R[key] = (int((~okv[ki]).sum()), [pts[i] for i in ki], {Pn: c[Pn][ki] for Pn in PR3})
    bands_k = sorted(set(bk.tolist()))
    groups = [np.flatnonzero(bk == b) for b in bands_k]
    rng = random.Random(2026)
    idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(B)]
    ref = R[("old", "enumerate")][2]
    res = {"n": len(nk), "genomes": {}, "pairs": {}}
    for (gn, mo), (miss, pts, c) in R.items():
        sf = np.array([x.get("setup_full", 0) for x in pts])
        M_ = np.array([m_of(N, G[gn]) for N, _, _ in nk])
        polys = np.array([x.get("sieve_scan", 0) for x in pts]) / (2 * M_ + 1)
        off_ex = np.array([sum(x.values()) - x.get("setup_full", 0) for x in pts])
        per_band = {}
        for Pn in PR3:
            per_band[Pn] = {}
            for b, gi in zip(bands_k, groups):
                r2 = random.Random(2026)
                vals = []
                for _ in range(2000):
                    i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                    vals.append(c[Pn][i].mean() / ref[Pn][i].mean())
                per_band[Pn][int(b)] = {"ratio": float(c[Pn][gi].mean() / ref[Pn][gi].mean()), "ci": q(vals)}
        ub = max(v["ci"][1] for Pn in PR3 for v in per_band[Pn].values())
        lb = max(v["ci"][0] for Pn in PR3 for v in per_band[Pn].values())
        gate = "FAIL" if (lb > 1.5 or miss) else ("PASS" if ub <= 1.5 else "BORDERLINE")
        res["genomes"][f"{gn} {mo}"] = {
            "misses": miss, "vs_frozen": {Pn: float(c[Pn].mean() / ref[Pn].mean()) for Pn in PR3},
            "setup_full_mean": float(sf.mean()), "setup_full_ruint_share": float(sf.sum() / c["ruint"].sum()),
            "setup_full_montgomery_share": float(sf.sum() / c["montgomery"].sum()),
            "polys_mean": float(polys.mean()), "official_ex_setup_full_mean": float(off_ex.mean()),
            "per_band": per_band, "gate": gate, "gate_worst_upper": ub, "gate_worst_lower": lb}
    def pair(a, b):
        ca, cb = R[a][2], R[b][2]
        row = {}
        for Pn in PR3:
            vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs]
            row[Pn] = {"ratio": float(ca[Pn].mean() / cb[Pn].mean()), "log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": q(vals)}
        rv = [max(ca[Pn][i].mean() / cb[Pn][i].mean() for Pn in PR3) for i in idxs]
        row["robust"] = {"ratio": max(row[Pn]["ratio"] for Pn in PR3), "ci": q(rv)}
        lo = all(row[Pn]["ci"][1] < 0 for Pn in PR3); hi = all(row[Pn]["ci"][0] > 0 for Pn in PR3)
        row["call"] = "first" if lo else ("second" if hi else "undecided")
        return row
    for name, a, b in (("old od / old enum", ("old", "on_demand"), ("old", "enumerate")),
                       ("new od / new enum", ("new", "on_demand"), ("new", "enumerate")),
                       ("n51 od / n51 enum", ("n51", "on_demand"), ("n51", "enumerate")),
                       ("new / old, both enum", ("new", "enumerate"), ("old", "enumerate")),
                       ("new / old, both od", ("new", "on_demand"), ("old", "on_demand")),
                       ("n51 / old, both enum", ("n51", "enumerate"), ("old", "enumerate")),
                       ("n51 / old, both od", ("n51", "on_demand"), ("old", "on_demand"))):
        res["pairs"][name] = pair(a, b)
    return res

def runs_ok(g, nums):
    rs = run_many([g], nums, P.QS_CAP, types=True)
    ok = np.array([r[1] is not None and 1 < int(r[1]) < N for r, (N, _, _) in zip(rs, nums)])
    pts = [{k: v for k, v in r[4].items() if v} for r in rs]
    return ok, pts, {Pn: np.array([optypes.cost(c, Pn, pr) for c in pts]) for Pn in PR3}

print("R1: map numbers; ratios official / ruint / Montgomery")
for bits in (72, 78, 84, 90, 96):
    nums, _ = TM.load(bits)
    oracle.check(nums)
    src = json.load(open(TM.SRC[bits][0]))
    band = np.array([r["band"] for r in (src if bits == 84 else src["maps"][str(bits)])["rows"]])
    R_all = {(gn, mo): runs_ok(dict(G[gn], a_mode=mo), nums) for gn in G for mo in MODES}
    accept, ct = np.zeros(len(nums), dtype=bool), {}
    for i, b in enumerate(band.tolist()):        # the acceptance sample (ondemand_accept.py): first 2 per band
        if ct.get(b, 0) < 2:
            ct[b] = ct.get(b, 0) + 1
            accept[i] = True
    out["R1"][bits] = {}
    for subset, keep in (("all", np.ones(len(nums), dtype=bool)), ("unseen", ~accept)):
        res = r1_summary(R_all, nums, band, keep)
        out["R1"][bits][subset] = res
        print(f"\n{bits} bits, {subset} ({res['n']} numbers)")
        for k, x in res["genomes"].items():
            print(f"  {k:14s} vs frozen ref " + " / ".join(f"{x['vs_frozen'][Pn]:.3f}" for Pn in PR3)
                  + f"  setup_full {x['setup_full_mean']:9.0f} (ruint share {x['setup_full_ruint_share']:.3f}, mont {x['setup_full_montgomery_share']:.3f})"
                  + f"  polys {x['polys_mean']:6.1f}  official ex setup_full {x['official_ex_setup_full_mean']:9.0f}  misses {x['misses']}"
                  + f"  gate {x['gate']} (worst band upper {x['gate_worst_upper']:.3f}, lower {x['gate_worst_lower']:.3f})")
        for k, r in res["pairs"].items():
            print(f"  {k:22s} " + "  ".join(f"{Pn[:4]} x{r[Pn]['ratio']:.3f} [{r[Pn]['ci'][0]:+.3f},{r[Pn]['ci'][1]:+.3f}]" for Pn in PR3)
                  + f"  robust x{r['robust']['ratio']:.3f} [{r['robust']['ci'][0]:.3f},{r['robust']['ci'][1]:.3f}]  call {r['call']}")
# ---------------- R2
SIZES, PER = (54, 60, 66, 72, 78, 84), 240
C, miss = {}, {}
for bits in SIZES:
    nums = semiprimes_pq(bits, PER, 8700000 + bits)
    oracle.check(nums)
    for gn in ("new", "old"):
        mi, _, c = runs(dict(G[gn], a_mode="on_demand"), nums)
        C[(gn, bits)], miss[(gn, bits)] = c, mi
rng = random.Random(2026)
IDX = {bits: [np.array([rng.randrange(PER) for _ in range(PER)]) for _ in range(B)] for bits in SIZES}
res, boots = {}, {Pn: [] for Pn in PR3}
for bits in SIZES:
    ca, cb = C[("new", bits)], C[("old", bits)]
    row = {}
    for Pn in PR3:
        vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in IDX[bits]]
        boots[Pn].append(vals)
        row[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": q(vals)}
    row["any_pricing_above_0"] = any(row[Pn]["ci"][0] > 0 for Pn in PR3)
    res[bits] = row
pooled = {Pn: {"log2": statistics.mean(res[b][Pn]["log2"] for b in SIZES),
               "ci": q([statistics.mean(boots[Pn][k][j] for k in range(len(SIZES))) for j in range(B)])} for Pn in PR3}
rule = {"never_clearly_worse": not any(res[b]["any_pricing_above_0"] for b in SIZES),
        "no_misses": not any(v for (n, _), v in miss.items() if n == "new"),
        "pooled_all_below_0": all(pooled[Pn]["ci"][1] < 0 for Pn in PR3)}
rule["replace"] = all(rule.values())
out["R2"] = {"per_size": res, "pooled": pooled, "misses": {f"{k[0]} {k[1]}": v for k, v in miss.items()}, "rule": rule}
print("\nR2: replacement rule (new / old, both on_demand; balanced 54-84, 240 per size)")
for bits in SIZES:
    print(f"  {bits}: " + "  ".join(f"{Pn[:4]} {res[bits][Pn]['log2']:+.3f} [{res[bits][Pn]['ci'][0]:+.3f},{res[bits][Pn]['ci'][1]:+.3f}]" for Pn in PR3))
print("  pooled: " + "  ".join(f"{Pn[:4]} {pooled[Pn]['log2']:+.3f} [{pooled[Pn]['ci'][0]:+.3f},{pooled[Pn]['ci'][1]:+.3f}]" for Pn in PR3))
print(f"  misses: {out['R2']['misses']}\n  rule: {rule}")
# ---------------- R3
data = json.load(open("partition_map.json"))
rows = data["rows"]
nums84, _ = TM.load(84)
rs = run_many([dict(G["old"], a_mode="on_demand")], nums84, P.QS_CAP, types=True)
pts = [{k: v for k, v in x[4].items() if v} for x in rs]
for r, x, pt in zip(rows, rs, pts):
    r["qs + lc 1.4 on_demand"] = {"T": x[0], "ops": x[0], "per_type": pt}
PRc = P.prices()
for qname in ("qs + lc 1.4", "qs + lc 1.4 on_demand"):
    M = P.Map(rows, qname, PRc)
    for pop_name, mask in (("balanced control", M.band == 42),):
        vec = P.optimize(M, mask)
        rep = P.report(M, vec, mask, pop_name)
        out["R3"][f"{qname} | {pop_name}"] = {"budgets": rep["budgets"], "fitness": rep["fitness"], "score": rep["score"]}
        print(f"R3: {qname} | {pop_name}: budgets {rep['budgets']}  fitness {rep['fitness']:.3f}")
json.dump(out, open("ondemand.json", "w"), indent=1, default=float)
