"""Step 8 (NOTES.md, "Step 8: the F test — protocol"; written before this ran): the card at 96 bits, B x 1.3
(bc x 1.3) with M held (mc / 1.3) and L/B held (lc' = 1 + (lc - 1) ln B / ln 1.3B, B the size's mean 1,752);
(a) tc held (scored), (b) tc set so the threshold in bits is unchanged (information). All 640 map numbers.
  python3 ftest.py -> ftest.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref, bnd, cost, phasetime, PT

BITS, BMEAN = 96, 1752.0
g0 = ref(BITS)
lc2 = 1 + (g0["lc"] - 1) * math.log(BMEAN) / math.log(1.3 * BMEAN)
sl = g0["tc"] + g0["lc"] - 1
cf = {"reference": g0,
      "(a) B x 1.3, tc held": dict(g0, bc=g0["bc"] * 1.3, mc=g0["mc"] / 1.3, lc=lc2),
      "(b) B x 1.3, threshold held": dict(g0, bc=g0["bc"] * 1.3, mc=g0["mc"] / 1.3, lc=lc2,
                                          tc=sl * math.log2(BMEAN) / math.log2(1.3 * BMEAN) - (lc2 - 1))}
nums = S2.map_nums(BITS)
out = {}
for name, g in cf.items():
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(r[1] is not None for r in rs), "a miss"
    width = [2 * max(64, int(g["mc"] * bnd(N, g))) + 1 for N, _, _ in nums]
    polys = np.array([r[4]["sieve_scan"] / w for r, w in zip(rs, width)])
    c = {Pn: np.array([cost(r[4], Pn) for r in rs]) for Pn in PT}
    walls = [phasetime(g, nums, False) for _ in range(2)]
    tot = float(np.mean([sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) for w in walls]))
    w0 = walls[0]
    pr_tot = sum(v["priced"] for k, v in w0.items() if not k.startswith("lp:"))
    rec = {"genes": {k: g[k] for k in ("bc", "mc", "tc", "lc")}, "F_mean": None, "polys_mean": float(polys.mean()),
           "solve_share_priced": w0["solve"]["priced"] / pr_tot,
           "priced": {Pn: {"mean": float(v.mean()), "median": float(np.median(v)),
                           "slowest_decile_mean": float(np.sort(v)[-len(v) // 10:].mean())} for Pn, v in c.items()},
           "wall_us": tot / 1e3, "wall_regions_us": {k: float(np.mean([w[k]["ns"] for w in walls])) / 1e3 for k in ("setup", "sieve", "confirm", "lp_ledger", "solve")}}
    out[name] = rec
    print(f"{name} {rec['genes']}: polynomials {rec['polys_mean']:.1f}; solve share (priced) {rec['solve_share_priced'] * 100:.2f}%; ruint mean "
          f"{rec['priced']['ruint']['mean']:,.0f} median {rec['priced']['ruint']['median']:,.0f} slowest decile {rec['priced']['ruint']['slowest_decile_mean']:,.0f}; "
          f"official {rec['priced']['official']['mean']:,.0f}; Montgomery {rec['priced']['montgomery']['mean']:,.0f}; wall {rec['wall_us']:,.1f} us "
          + " ".join(f"{k} {v:,.1f}" for k, v in rec["wall_regions_us"].items()), flush=True)
json.dump(out, open("ftest.json", "w"), indent=1)
