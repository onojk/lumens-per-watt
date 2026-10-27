"""Stage G (NOTES.md, "Stage G"; G-1..G-5 sealed before this ran): a threshold scan at 96 bits, gene change only.
The reference genes, and the threshold lowered by 2, 4 and 6 bits through tc alone (tc += d / log2 B, B the size's
mean 1,752; lc unchanged, so L unchanged). All 640 map numbers per cell: candidates per number (confirm-region calls),
polynomials, combinations (lp:comb calls, LAMPCORE_LPBREAK=1), priced (ruint, Montgomery, official: mean, median, mean
of the slowest decile), wall-clock (two replicates, region breakdown). Capture: stage B's funnel (step9.run_size with
the cell's genes) on stage B's 8-number subset.
  python3 stageg.py -> stageg.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref, bnd, cost, phasetime, PT
import step9

BMEAN = 1752.0
g0 = ref(96)
cells = {f"{'reference' if d == 0 else f'-{d} bits'}": dict(g0, tc=g0["tc"] + d / math.log2(BMEAN)) for d in (0, 2, 4, 6)}
nums = S2.map_nums(96)
out = {}
for name, g in cells.items():
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(r[1] is not None for r in rs)
    width = [2 * max(64, int(g["mc"] * bnd(N, g))) + 1 for N, _, _ in nums]
    polys = np.array([r[4]["sieve_scan"] / w for r, w in zip(rs, width)])
    c = {Pn: np.array([cost(r[4], Pn) for r in rs]) for Pn in PT}
    lpb = phasetime(g, nums, True)
    walls = [phasetime(g, nums, False) for _ in range(2)]
    regs = ("setup", "gray", "sieve", "scan", "confirm", "lp_ledger", "solve")
    recs, npol, _, _, _ = step9.run_size(96, g)
    capture = {cls: {"true_per_poly": len(recs[cls]) / npol, "passed": step9.frac(recs[cls], "passed"), "end_to_end": step9.frac(recs[cls], "filed")}
               for cls in ("full", "part")}
    rec = {"tc": g["tc"], "candidates": walls[0]["confirm"]["calls"], "polys": float(polys.mean()), "polys_median": float(np.median(polys)),
           "combinations": lpb["lp:comb"]["calls"], "partials_looked_up": lpb["lp:hash"]["calls"],
           "priced": {Pn: {"mean": float(v.mean()), "median": float(np.median(v)), "slowest_decile_mean": float(np.sort(v)[-len(v) // 10:].mean())} for Pn, v in c.items()},
           "wall_us": [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in walls],
           "wall_regions_us": {k: float(np.mean([w[k]["ns"] for w in walls])) / 1e3 for k in regs if k in walls[0]},
           "capture_subset": capture, "subset_polys": npol}
    out[name] = rec
    pr = rec["priced"]
    print(f"{name} (tc {g['tc']:.4f}): candidates {rec['candidates']:,.0f}; polynomials {rec['polys']:.1f} (median {rec['polys_median']:.1f}); "
          f"combinations {rec['combinations']:.1f}; capture (subset, {npol} polys) partials passed {capture['part']['passed']:.3f} end {capture['part']['end_to_end']:.3f}, "
          f"fulls passed {capture['full']['passed']:.3f}; ruint mean {pr['ruint']['mean']:,.0f} median {pr['ruint']['median']:,.0f} slowest decile "
          f"{pr['ruint']['slowest_decile_mean']:,.0f}; official {pr['official']['mean']:,.0f}; Montgomery {pr['montgomery']['mean']:,.0f}; wall "
          f"{np.mean(rec['wall_us']):,.1f} us ({rec['wall_us'][0]:,.1f} / {rec['wall_us'][1]:,.1f}): " + " ".join(f"{k} {v:,.1f}" for k, v in rec["wall_regions_us"].items()), flush=True)
json.dump(out, open("stageg.json", "w"), indent=1)
