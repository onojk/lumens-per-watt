"""Type mix of the two qs references by size (NOTES.md, "Type mix of the two qs references";
information only, no fitness). On the existing map numbers at 72/96 (size_map, seeds 9000000
+ 100 pb + bits), 78/90 (stopping_map, 9200000 + ...) and 84 (partition_map, 4000000 + ...):

  1. qs + lc 1.4 per-type counts from the maps; the new qs alone rerun here (lampcore --types,
     cap 2^28; it was run in stopping.py test but its counts were not saved). Mean ops per
     type, each type's share of ruint and Montgomery cost, new/old per pricing, and each type's
     contribution to the new - old difference (as a share of old's total) per pricing.
  2. One-gene swaps (lampcore, same numbers): old genes with one gene set to the new value, and
     new genes with one gene set back to the old value; new/old per pricing.
  3. Operand-size dependence of the prices: optypes.prices() is one table; the opbench 60/84/100-bit
     mulmod timings (P-core repeats) beside it.

  python3 typemix.py  -> typemix.json, stdout
"""
import sys
sys.argv[1:] = []
import json, statistics
import numpy as np
import optypes
import partition as P
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many

PR3 = ("official", "ruint", "montgomery")
pr = optypes.prices()
OLD = dict(P.QS_VARIANTS["qs + lc 1.4"])
NEW = {"t": "qs", "kc": 4, "bc": 0.8993889783377338, "mc": 0.7340990893362095,
       "tc": 1.1044621542694246, "lc": 1.6612269841697611}
GENES = ("kc", "bc", "mc", "tc", "lc")
SRC = {72: ("size_map.json", 9000000), 78: ("stopping_map.json", 9200000), 84: ("partition_map.json", 4000000),
       90: ("stopping_map.json", 9200000), 96: ("size_map.json", 9000000)}

def load(bits):
    f, base = SRC[bits]
    d = json.load(open(f))
    m = d if bits == 84 else d["maps"][str(bits)]
    nums = []
    for pb in m["bands"]:
        seed = base + 100 * pb + bits
        nums += semiprimes_pq(bits, P.PER_BAND, seed) if 2 * pb >= bits else semiprimes_unbalanced(bits, pb, P.PER_BAND, seed)
    assert [r["N"] for r in m["rows"]] == [str(t[0]) for t in nums]
    return nums, [{k: v for k, v in r["qs + lc 1.4"]["per_type"].items() if v} for r in m["rows"]]   # 84: zeros stored

def run(g, nums):
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(x[1] is not None and 1 < int(x[1]) < N for x, (N, _, _) in zip(rs, nums))
    return [{k: v for k, v in x[4].items() if v} for x in rs]

def mean_cost(pts, Pn):
    return float(np.mean([optypes.cost(c, Pn, pr) for c in pts]))

def price(t, Pn):
    return 1.0 if Pn == "official" else pr[Pn][t]

out = {"sizes": {}}
for bits in (72, 78, 84, 90, 96):
    nums, old = load(bits)
    chk = run(OLD, nums)
    assert chk == old, "map counts for qs + lc 1.4 do not reproduce"
    new = run(NEW, nums)
    types = [t for t in optypes.TYPE_ORDER if any(t in c for c in old + new)]
    mt = {g: {t: float(np.mean([c.get(t, 0) for c in pts])) for t in types} for g, pts in (("old", old), ("new", new))}
    tot = {g: {Pn: sum(price(t, Pn) * mt[g][t] for t in types) for Pn in PR3} for g in mt}
    share = {g: {Pn: {t: price(t, Pn) * mt[g][t] / tot[g][Pn] for t in types} for Pn in ("ruint", "montgomery")} for g in mt}
    ratio = {Pn: tot["new"][Pn] / tot["old"][Pn] for Pn in PR3}
    # s (primes per A) from setup_full: all C(16 + 4s, s) combinations are formed up front, (s - 1) each,
    # i.e. 2 C(28, 3) = 6,552 at s = 3 and 3 C(32, 4) = 107,880 at s = 4; a run at s = 4 has setup_full > 50,000
    s4 = {g: float(np.mean([c.get("setup_full", 0) > 50000 for c in pts])) for g, pts in (("old", old), ("new", new))}
    contrib = {Pn: {t: price(t, Pn) * (mt["new"][t] - mt["old"][t]) / tot["old"][Pn] for t in types} for Pn in PR3}
    swaps = {}
    for gname in GENES:
        o1 = dict(OLD, **{gname: NEW[gname]})
        n1 = dict(NEW, **{gname: OLD[gname]})
        a, b = run(o1, nums), run(n1, nums)
        swaps[gname] = {"old_with_new": {Pn: mean_cost(a, Pn) / tot["old"][Pn] for Pn in PR3},
                        "new_with_old": {Pn: mean_cost(b, Pn) / tot["old"][Pn] for Pn in PR3}}
    out["sizes"][bits] = {"n": len(nums), "mean_per_type": mt, "totals": tot, "shares": share, "new_over_old": ratio,
                          "contrib": contrib, "swaps": swaps, "s4_fraction": s4}
    print(f"\n{bits} bits, {len(nums)} numbers: new qs alone / qs + lc 1.4 alone: " + ", ".join(f"{Pn} {ratio[Pn]:.3f}" for Pn in PR3))
    print(f"  share of numbers at s = 4 (setup_full > 50,000): old {s4['old']:.3f}, new {s4['new']:.3f}")
    print(f"  {'type':13s} {'old mean':>11s} {'new mean':>11s}  price r / m   old share r / m   new share r / m   contrib to new-old: off / r / m")
    for t in types:
        print(f"  {t:13s} {mt['old'][t]:11.0f} {mt['new'][t]:11.0f}  {price(t, 'ruint'):5.3f} / {price(t, 'montgomery'):5.3f}"
              f"   {share['old']['ruint'][t]:5.3f} / {share['old']['montgomery'][t]:5.3f}   {share['new']['ruint'][t]:5.3f} / {share['new']['montgomery'][t]:5.3f}"
              f"   {contrib['official'][t]:+.3f} / {contrib['ruint'][t]:+.3f} / {contrib['montgomery'][t]:+.3f}")
    print("  one-gene swaps, new/old ratio (off / ruint / mont):")
    for gname, s in swaps.items():
        print(f"    old genes, {gname} -> new {NEW[gname]:.4g}: " + " / ".join(f"{s['old_with_new'][Pn]:.3f}" for Pn in PR3)
              + f"    new genes, {gname} -> old {OLD[gname]:.4g}: " + " / ".join(f"{s['new_with_old'][Pn]:.3f}" for Pn in PR3))

# 3. prices and operand size
bench = {}
for rep in ("p1", "p2", "p3"):
    for line in open(f"calibrate_bench/opbench_{rep}.jsonl"):
        x = json.loads(line)
        if x["name"].startswith("mulmod") and "bits" in x:
            bench.setdefault((x["name"], x["bits"]), []).append(x["ns_median"])
med = {f"{k[0]} @{k[1]}": statistics.median(v) for k, v in sorted(bench.items())}
out["mulmod_ns_by_bits"] = med
print("\nprices: optypes.prices() is one table per pricing (no size argument). opbench mulmod, median of P1-P3 (ns):")
for k, v in med.items():
    print(f"  {k}: {v:.2f}")
json.dump(out, open("typemix.json", "w"), indent=1)
