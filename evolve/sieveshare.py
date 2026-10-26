"""Information only (user's item 2, Oct 25; no card change): the share of qs's charged ops that are
sieve updates, and the share of sieve updates from primes below 30, per size, for each track's
kc/lc-round (d) winner run as qs alone.
  - sieve_update share: lampcore --types on all map numbers (official ops, and cost share under
    ruint and Montgomery).
  - small-prime share: exact per-polynomial update counts from Python's trace ((width-1-start)//p + 1
    per root, as the card charges) on 2 balanced-band and 2 band-24 map numbers per size.
  python3 sieveshare.py -> sieveshare.out (stdout)
"""
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    rows = SS.corrected_map_rows(bits)
    bands = [r["band"] for r in rows]
    for tr in SS.TRACKS:
        g = SS.qsg(sealed["sizes"][str(bits)]["tracks"][tr]["new_genes"])
        rs = run_many([g], nums, P.QS_CAP, types=True)
        tot = {t: sum(x[4][t] for x in rs) for t in optypes.TYPE_ORDER}
        tot = {t: v for t, v in tot.items() if v}
        off = sum(tot.values())
        sh = {"official": tot["sieve_update"] / off}
        for Pn in ("ruint", "montgomery"):
            sh[Pn] = PR[Pn]["sieve_update"] * tot["sieve_update"] / P.cost_of(tot, PR[Pn])
        sample = []
        for want in (max(bands), 24):
            sample += [t for t, b in zip(nums, bands) if b == want][:2]
        small = allu = 0
        for N, _, _ in sample:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                qs.lamp_qs(N, g, m)
            except lamps.Budget:
                pass
            for at in qs.TRACE["attempts"]:
                for poly in at["polys"]:
                    M = poly["M"]; width = 2 * M + 1
                    for p, r in poly["roots"]:
                        u = (width - 1 - (r + M) % p) // p + 1
                        allu += u
                        small += u if p < 30 else 0
                    assert sum((width - 1 - (r + M) % p) // p + 1 for p, r in poly["roots"]) == poly["upd"]
            qs.TRACE = None
        print(f"{bits} Track {tr} ({sealed['sizes'][str(bits)]['tracks'][tr]['new_winner']}): sieve updates are "
              + " / ".join(f"{sh[Pn]:.3f}" for Pn in sh) + " of qs cost (official ops / ruint / Montgomery); "
              f"primes < 30 give {small / allu:.3f} of sieve updates (exact, {len(sample)} numbers)", flush=True)
