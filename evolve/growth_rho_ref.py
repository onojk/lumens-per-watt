"""G_rho's reference for freezing (the user's ruling, Oct 29): rho alone (partition.PRE["rho"] genes) over the 48-80
chord, from the committed growth_counts.json (sealed run 68250b3; 48 balanced semiprimes per size, seeds 9600000 + bits).
Doubling period = (b - a) / log2(C(b) / C(a)), C = total priced cost / successes (growth_harness.per_fact), under
op-class v1, ruint, Montgomery, official and op-class v1 with the size-scaled gcd price (gcdscale.py, uniform-k curve:
rho's gcd is of a product of differences mod N). Bootstrap: 10,000 resamples within each size, random.Random(2026),
2.5-97.5% (growth_gref.py's convention). No new run.
  python3 growth_rho_ref.py -> growth_rho_ref.json, stdout"""
import sys
sys.argv = sys.argv[:1]
import json, math, random
import gcdscale

A, B = 48, 80
PRICINGS = ("opclass_v1", "ruint", "montgomery", "official", "opclass_v1_gcdscaled")
data = json.load(open("growth_counts.json"))
rows = {}
for b in (A, B):
    rs = []
    for r in data[str(b)]["rho"]:
        c = dict(r["cost"]); c["opclass_v1_gcdscaled"] = gcdscale.cost(r["types"], b, "uniform")
        rs.append({"ok": r["ok"], "cost": c, "gcd": r["types"].get("gcd", 0), "mul": r["types"].get("mul", 0)})
    rows[b] = rs

def per_fact(rs, pr):
    s = sum(r["ok"] for r in rs)
    return sum(r["cost"][pr] for r in rs) / s if s >= len(rs) // 2 else None

def period(rw, pr):
    ca, cb = per_fact(rw[A], pr), per_fact(rw[B], pr)
    return (B - A) / math.log2(cb / ca) if ca and cb else None

out = {"window": [A, B], "lamp": "rho alone, partition.PRE['rho']", "source": "growth_counts.json (sealed 68250b3)",
       "success": {b: sum(r["ok"] for r in rows[b]) for b in (A, B)},
       "gcd_share_opclass": {b: sum(r["gcd"] for r in rows[b]) * gcdscale.V1["gcd"] / sum(r["cost"]["opclass_v1"] for r in rows[b]) for b in (A, B)},
       "gcd_units_scaled": {b: gcdscale.gcd_units(b, "uniform") for b in (A, B)}, "periods": {}}
rng = random.Random(2026)
for pr in PRICINGS:
    p = period(rows, pr)
    bs = sorted(x for x in (period({b: [rows[b][rng.randrange(len(rows[b]))] for _ in rows[b]] for b in (A, B)}, pr)
                            for _ in range(10000)) if x)
    ci = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1])
    out["periods"][pr] = {"period": p, "ci": ci}
    print(f"rho doubling period {A}-{B} [{pr}]: {p:.3f} bits [{ci[0]:.3f}, {ci[1]:.3f}]")
print(f"successes {out['success']}; rho's gcd share of op-class cost {', '.join(f'{b}: {v:.4f}' for b, v in out['gcd_share_opclass'].items())}; "
      f"scaled gcd units {', '.join(f'{b}: {v:.1f}' for b, v in out['gcd_units_scaled'].items())} (flat 1401.7)")
json.dump(out, open("growth_rho_ref.json", "w"), indent=1)
