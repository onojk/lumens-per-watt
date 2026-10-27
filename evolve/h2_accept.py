"""Acceptance for stage H's scan fix (NOTES.md, "Stage H, scan fix"): every pp cell identical per number and per type
to b2bade2's lampcore (LAMPCORE_OLD) on all map numbers (54-96): pp 10 at tc 1.0353 / 0.7623 / 0.5713 and pp 3 at
+1 / +2 / +3 bits (the stage H and H2 tc values, applied at every size), and the reference with pp absent.
  LAMPCORE_OLD=<b2bade2 binary> python3 h2_accept.py -> stdout
"""
import math, os
import partition as P, sizescale as SS, sizescale2 as S2
import fastlamps
from fastlamps import run_many
from lctest import ref

LB = math.log2(1752.0)

def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0

n = b = 0
g96 = ref(96)
for bits in SS.SIZES:
    g0 = ref(bits)
    cells = {"reference": g0, "pp 10 tc 1.0353": dict(g0, pp=10, tc=g96["tc"]), "pp 10 tc 0.7623": dict(g0, pp=10, tc=0.7623),
             "pp 10 tc 0.5713": dict(g0, pp=10, tc=g96["tc"] - 5 / LB)}
    for d in (1, 2, 3):
        cells[f"pp 3 +{d} bits"] = dict(g0, pp=3, tc=g96["tc"] - d / LB)
    nums = S2.map_nums(bits)
    for name, g in cells.items():
        bad = sum(x != y for x, y in zip(run(g, nums), run(g, nums, old=True)))
        n += len(nums); b += bad
        if bad:
            print(f"  {bits} bits {name}: {bad} differ", flush=True)
    print(f"{bits} bits done", flush=True)
print(f"pp cells and the reference against b2bade2: identical per number and per type: {n - b}/{n}")
assert not b
