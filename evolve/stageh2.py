"""Stage H2, the re-time after the scan fix (NOTES.md, "Stage H, scan fix"; predictions/stage-h2.md; run through
tools/sealed_run.sh stage-h2). Same measurements as stageh.py. 96 bits, all 640 map numbers, re-sieve off. Cells: the
reference; (iii) pp 10, threshold +5 bits; (iv) pp 3 ("2 free"), +3 bits; pp 3 at +1 and +2 bits (tc -= d / log2
1,752; L unchanged).
Per cell: candidates per number (confirm-region calls) and per polynomial; polynomials (sieve_scan / width);
combinations and partials looked up (lp:comb, lp:hash calls, LAMPCORE_LPBREAK=1); priced ruint / Montgomery /
official (mean, median, slowest-decile mean); wall-clock, two replicates (taskset core 2), regions, sieve per
polynomial; on stage B's 8-number subset (Python traces): partial and full capture (passed threshold, end to end)
and the under-count at true partials and fulls (step9.run_size), and the never-combined share (lctest.x3).
  python3 stageh2.py -> stageh2.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref, bnd, cost, phasetime, PT, x3
import step9

LB = math.log2(1752.0)
g0 = ref(96)
cells = {"reference": g0,
         "(iii) pp 10, +5 bits": dict(g0, pp=10, tc=g0["tc"] - 5 / LB),
         "(iv) pp 3 (2 free), +3 bits": dict(g0, pp=3, tc=g0["tc"] - 3 / LB),
         "pp 3 (2 free), +1 bit": dict(g0, pp=3, tc=g0["tc"] - 1 / LB),
         "pp 3 (2 free), +2 bits": dict(g0, pp=3, tc=g0["tc"] - 2 / LB)}
nums = S2.map_nums(96)
sub = step9.sample(96)
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
    cap = {cls: {"true_per_poly": len(recs[cls]) / npol, "passed": step9.frac(recs[cls], "passed"),
                 "end_to_end": step9.frac(recs[cls], "filed"),
                 "under_median": float(np.median([r["under"] for r in recs[cls]])),
                 "under_mean": float(np.mean([r["under"] for r in recs[cls]])),
                 "under_p90": float(np.percentile([r["under"] for r in recs[cls]], 90))} for cls in ("full", "part")}
    nc, _ = x3(96, g, sub)
    pm = float(polys.mean())
    wr = {k: float(np.mean([w[k]["ns"] for w in walls])) / 1e3 for k in regs}
    rec = {"tc": g["tc"], "pp": g.get("pp", 0), "candidates": walls[0]["confirm"]["calls"],
           "candidates_per_poly": walls[0]["confirm"]["calls"] / pm, "polys": pm, "polys_median": float(np.median(polys)),
           "combinations": lpb["lp:comb"]["calls"], "partials_looked_up": lpb["lp:hash"]["calls"],
           "priced": {Pn: {"mean": float(v.mean()), "median": float(np.median(v)), "slowest_decile_mean": float(np.sort(v)[-len(v) // 10:].mean())} for Pn, v in c.items()},
           "wall_us": [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in walls],
           "wall_regions_us": wr, "sieve_us_per_poly": wr["sieve"] / pm,
           "sieve_update_per_poly": float(np.mean([r[4]["sieve_update"] for r in rs])) / pm,
           "capture_subset": cap, "subset_polys": npol, "never_combined_subset": nc}
    out[name] = rec
    pr = rec["priced"]
    print(f"{name} (pp {rec['pp']}, tc {g['tc']:.4f}): candidates {rec['candidates']:,.0f} per number, {rec['candidates_per_poly']:.2f} per polynomial; "
          f"polynomials {pm:.1f} (median {rec['polys_median']:.1f}); combinations {rec['combinations']:.1f}; looked up {rec['partials_looked_up']:.0f}; "
          f"subset ({npol} polys): partials passed {cap['part']['passed']:.3f} end {cap['part']['end_to_end']:.3f}, fulls passed {cap['full']['passed']:.3f} "
          f"end {cap['full']['end_to_end']:.3f}; under-count at partials median {cap['part']['under_median']:.2f} mean {cap['part']['under_mean']:.2f} "
          f"p90 {cap['part']['under_p90']:.2f}, at fulls median {cap['full']['under_median']:.2f}; never-combined {nc:.3f}; ruint mean {pr['ruint']['mean']:,.0f} "
          f"median {pr['ruint']['median']:,.0f} slowest decile {pr['ruint']['slowest_decile_mean']:,.0f}; official {pr['official']['mean']:,.0f}; Montgomery "
          f"{pr['montgomery']['mean']:,.0f}; wall {np.mean(rec['wall_us']):,.1f} us ({rec['wall_us'][0]:,.1f} / {rec['wall_us'][1]:,.1f}): "
          + " ".join(f"{k} {v:,.1f}" for k, v in wr.items()) + f"; sieve {rec['sieve_us_per_poly']:.3f} us / polynomial, {rec['sieve_update_per_poly']:,.0f} updates / polynomial", flush=True)
json.dump(out, open("stageh2.json", "w"), indent=1)
