"""Outside baseline for the partition study, map only (NOTES.md, "Library references and
oracles"; prediction written there before this ran): primefac 2.0.12's default plan encoded
as td(ob 499) -> rho(ob 168,000) -> qs + lc 1.4, evaluated from partition_map.json on the
tuning numbers under all three pricings, beside allocation A. Information only.

Composition per number (exact up to 1 op): td's ob 499 covers divisors 3..999 and no tuning
number has p < 1000, so td spends exactly 500 ops (all td_mod); rho succeeds iff its ops-to-
success T <= 168,000, else it spends 168,001 (rho charges 1-2 ops at a time, so the true
value is 168,001 or 168,002) priced at rho's price per official op on that band; then qs.

  python3 partition_primefac.py  -> partition_primefac.out (stdout)
"""
import sys
sys.argv[1:] = []
import json, math
import numpy as np
import partition as P

rows = json.load(open("partition_map.json"))["rows"]
PR = P.prices()
M = P.Map(rows, "qs + lc 1.4", PR)
assert all(r["td"]["T"] is None or r["td"]["T"] > 499 for r in rows)
A = (0, 5793, 0, 32768)
RHO_OB = 168000

def primefac_costs(Pn):
    td = 500.0 if Pn == "official" else 500.0 * PR[Pn]["td_mod"]
    succ = M.T["rho"] <= RHO_OB
    rho = np.where(succ, M.full["rho"][Pn], (RHO_OB + 1) * M.pib["rho"][Pn])
    return td + rho + np.where(succ, 0.0, M.qs[Pn])

print("primefac default plan (td to 1000 -> 42,000 Floyd rounds = 168,000 ops -> qs + lc 1.4) vs allocation A, tuning map:")
for Pn in P.PRICINGS:
    pf, a, q = primefac_costs(Pn), M.costs(A, Pn), M.qs[Pn]
    print(f"  {Pn:10s} primefac / qs alone {pf.mean() / q.mean():.3f}   A / qs alone {a.mean() / q.mean():.3f}   "
          f"primefac / A = {pf.mean() / a.mean():.2f}x")
    print("     per band, primefac / A: " + "  ".join(f"{pb}: {pf[M.band == pb].mean() / a[M.band == pb].mean():.2f}" for pb in P.BANDS))
pf_rob = max(primefac_costs(Pn).mean() / M.qs[Pn].mean() for Pn in P.PRICINGS)
a_rob = max(M.costs(A, Pn).mean() / M.qs[Pn].mean() for Pn in P.PRICINGS)
print(f"  robust ratio vs qs + lc 1.4 alone: primefac {pf_rob:.3f}, A {a_rob:.3f}; primefac / A {pf_rob / a_rob:.2f}x")
succ = M.T["rho"] <= RHO_OB
print("  rho within 168,000 ops, successes per band: " + "  ".join(f"{pb}: {int(succ[M.band == pb].sum())}/80" for pb in P.BANDS))
