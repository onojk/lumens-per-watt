"""Stage H, step 3 (NOTES.md, "Stage H"): find tc for cell (ii), option on (pp 10) with candidates per number
matching the reference. 32 map numbers at 96 (every 20th); candidates per number by the luck meter's tests (one per
processed candidate; within 0.3% of the confirm-region calls on all 640 for the reference). Bisection on tc, every
run reported. No comparison quantities are computed here.
  python3 hsearch.py -> hsearch.json, stdout
"""
import json
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref

g0 = ref(96)
nums = S2.map_nums(96)[::20]
def cands(g):
    rs = run_many([g], nums, P.QS_CAP)
    assert all(r[1] is not None for r in rs)
    return float(np.mean([r[2] for r in rs]))
target = cands(g0)
runs = [{"cell": "reference", "tc": g0["tc"], "cands": target}]
print(f"reference (tc {g0['tc']:.4f}): {target:.1f} candidates per number (32 numbers)", flush=True)
c = cands(dict(g0, pp=10))
runs.append({"cell": "pp 10", "tc": g0["tc"], "cands": c})
print(f"pp 10, reference tc: {c:.1f} ({(c / target - 1) * 100:+.1f}%)", flush=True)
lo, hi = g0["tc"] - 0.6, g0["tc"]                # tc lower = threshold higher
for _ in range(12):
    mid = 0.5 * (lo + hi)
    c = cands(dict(g0, pp=10, tc=mid))
    runs.append({"cell": "pp 10", "tc": mid, "cands": c})
    print(f"pp 10, tc {mid:.4f} (threshold +{(g0['tc'] - mid) * 10.775:.2f} bits): {c:.1f} ({(c / target - 1) * 100:+.1f}%)", flush=True)
    if c > target:
        hi = mid
    else:
        lo = mid
    if abs(c / target - 1) < 0.003:
        break
best = min(runs[2:], key=lambda r: abs(r["cands"] / target - 1))
print(f"chosen tc {best['tc']:.4f}: {best['cands']:.1f} against {target:.1f}", flush=True)
json.dump({"target": target, "runs": runs, "chosen_tc": best["tc"]}, open("hsearch.json", "w"), indent=1)
