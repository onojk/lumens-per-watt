"""Partition study, per band and per pricing (map only, tuning numbers; information): each
plan's mean cost as a ratio to qs + lc 1.4 alone, under official / ruint / Montgomery.

  official-only best: the allocation that minimizes the official score alone (same grid
                      and refinement as partition.py's optimize)
  robust best (A):    partition.py's chosen allocation for qs + lc 1.4 (fitness (c))
  difference:         robust / official-only best (above 1: A costs more there)
  primefac:           primefac's default plan (partition_primefac.py)
Also: rho alone and ECM alone against qs alone per band and pricing (where they finish every
number of the band within their cap), for the hypothesis that rho stays cheaper than qs at
20-28 bits under every pricing.

  python3 partition_bands.py  -> partition_bands.out (stdout)
"""
import sys
sys.argv[1:] = []
import json
import numpy as np
import partition as P
import partition_primefac as PF

M, PR = PF.M, PF.PR
A = PF.A

def optimize_official(M):
    fit = lambda v: M.costs(v, "official").mean() / M.qs["official"].mean()
    best = min(((bt, br, bp, be) for bt in P.COARSE for br in P.COARSE for bp in P.PM1_OPTS for be in P.COARSE), key=fit)
    vec = list(best)
    while True:
        moved = False
        for i, opts in enumerate((P.FINE, P.FINE, P.PM1_OPTS, P.FINE)):
            for o in opts:
                trial = vec.copy(); trial[i] = o
                if fit(tuple(trial)) < fit(tuple(vec)) - 1e-12:
                    vec, moved = trial, True
        if not moved:
            return tuple(vec)

O = optimize_official(M)
print(f"official-only best: td {O[0]}, rho {O[1]}, pm1 {'full' if O[2] else 0}, ecm {O[3]}")
print(f"robust best (A):    td {A[0]}, rho {A[1]}, pm1 {'full' if A[2] else 0}, ecm {A[3]}")
for Pn in P.PRICINGS:
    q = M.qs[Pn]
    co, ca, cp = M.costs(O, Pn), M.costs(A, Pn), PF.primefac_costs(Pn)
    print(f"\n{Pn}: ratio to qs + lc 1.4 alone (band mean cost / qs mean cost)")
    print(f"  {'band':>5s} {'off-only':>9s} {'robust A':>9s} {'diff':>6s} {'primefac':>9s} {'rho alone':>10s} {'ecm alone':>10s}")
    for pb in list(P.BANDS) + ["all"]:
        sel = M.band == pb if pb != "all" else np.ones(M.n, dtype=bool)
        r = lambda c: c[sel].mean() / q[sel].mean()
        alone = {}
        for s in ("rho", "ecm"):
            alone[s] = f"{M.full[s][Pn][sel].mean() / q[sel].mean():10.3f}" if pb != "all" and np.isfinite(M.T[s][sel]).all() else f"{'-':>10s}"
        print(f"  {str(pb):>5s} {r(co):9.3f} {r(ca):9.3f} {r(ca) / r(co):6.2f} {r(cp):9.3f} {alone['rho']} {alone['ecm']}")
    print(f"  robust ratio: off-only {max(M.costs(O, x).mean() / M.qs[x].mean() for x in P.PRICINGS):.3f}, "
          f"A {max(M.costs(A, x).mean() / M.qs[x].mean() for x in P.PRICINGS):.3f}" if Pn == "montgomery" else "")
# the between-band trade: where does the official-only plan's extra cost under ruint come from?
print("\nruint, extra cost of the official-only plan over A, by band (share of the total difference):")
d = M.costs(O, "ruint") - M.costs(A, "ruint")
tot = d.sum()
print("  " + "  ".join(f"{pb}: {d[M.band == pb].sum() / tot:+.2f}" for pb in P.BANDS) + f"   (total {tot / M.n:+.0f} per number)")
