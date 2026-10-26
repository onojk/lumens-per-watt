"""Stage E (overnight queue; R-G1 / R-G2 sealed before it ran): the re-sieve x F 2x2 at 96 bits. Cells: re-sieve off /
on (p0 200) x reference F / F x 1.3 (step 8's mapping, threshold-held variant: bc x 1.3, mc / 1.3, lc' for L/B held,
tc for the threshold in bits held). All 640 map numbers: priced (ruint, Montgomery, official: mean, median, mean of
the slowest decile), polynomials, solve share (priced), wall-clock (two replicates, region breakdown).
  python3 e2x2.py -> e2x2.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref, bnd, cost, phasetime, PT

BMEAN = 1752.0
g0 = ref(96)
lc2 = 1 + (g0["lc"] - 1) * math.log(BMEAN) / math.log(1.3 * BMEAN)
sl = g0["tc"] + g0["lc"] - 1
gF = dict(g0, bc=g0["bc"] * 1.3, mc=g0["mc"] / 1.3, lc=lc2, tc=sl * math.log2(BMEAN) / math.log2(1.3 * BMEAN) - (lc2 - 1))
cells = {"off, ref F": g0, "off, F x1.3": gF,
         "on p0 200, ref F": dict(g0, confirm="resieve", p0=200), "on p0 200, F x1.3": dict(gF, confirm="resieve", p0=200)}
nums = S2.map_nums(96)
out = {}
for name, g in cells.items():
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(r[1] is not None for r in rs)
    width = [2 * max(64, int(g["mc"] * bnd(N, g))) + 1 for N, _, _ in nums]
    polys = np.array([r[4]["sieve_scan"] / w for r, w in zip(rs, width)])
    c = {Pn: np.array([cost(r[4], Pn) for r in rs]) for Pn in PT}
    walls = [phasetime(g, nums, False) for _ in range(2)]
    regs = ("setup", "gray", "sieve", "resieve", "confirm", "lp_ledger", "solve")
    rec = {"polys": float(polys.mean()),
           "solve_share_priced": walls[0]["solve"]["priced"] / sum(v["priced"] for k, v in walls[0].items() if not k.startswith("lp:")),
           "priced": {Pn: {"mean": float(v.mean()), "median": float(np.median(v)), "slowest_decile_mean": float(np.sort(v)[-len(v) // 10:].mean())} for Pn, v in c.items()},
           "wall_us": float(np.mean([sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) for w in walls])) / 1e3,
           "wall_regions_us": {k: float(np.mean([w[k]["ns"] for w in walls])) / 1e3 for k in regs if k in walls[0]}}
    out[name] = rec
    print(f"{name}: polynomials {rec['polys']:.1f}; solve share {rec['solve_share_priced'] * 100:.2f}%; ruint mean {rec['priced']['ruint']['mean']:,.0f} "
          f"median {rec['priced']['ruint']['median']:,.0f} slowest decile {rec['priced']['ruint']['slowest_decile_mean']:,.0f}; official {rec['priced']['official']['mean']:,.0f}; "
          f"Montgomery {rec['priced']['montgomery']['mean']:,.0f}; wall {rec['wall_us']:,.1f} us: " + " ".join(f"{k} {v:,.1f}" for k, v in rec["wall_regions_us"].items()), flush=True)
json.dump(out, open("e2x2.json", "w"), indent=1)
