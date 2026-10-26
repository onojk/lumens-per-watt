"""Acceptance for item 12 (NOTES.md, "Cost models: items 12 and 13"): on-demand selection takes the pool's
closeness order from the pool selection instead of re-sorting it. Nothing is charged differently, so every
run must be identical to the pre-change lampcore (LAMPCORE_OLD), per number and per type, on all map
numbers, for the new reference (with and without re-sieve), the corrected reference (on_demand) and the
frozen reference (enumerate); and Python = Rust per type on a sample.
  LAMPCORE_OLD=<binary> python3 item12_accept.py -> stdout
"""
import os, json
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0
n1 = b1 = n2 = b2 = 0
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    for g in (nr, dict(nr, confirm="resieve"), SS.OLD, SS.FROZEN_REF):
        a, b = run(g, nums), run(g, nums, old=True)
        n1 += len(a); b1 += sum(x != y for x, y in zip(a, b))
        for N, p, q in nums[::len(nums) // 2][:2]:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                qs.lamp_qs(N, g, m)
            except lamps.Budget:
                pass
            tr = qs.TRACE; qs.TRACE = None
            r = run(g, [(N, p, q)])[0]
            n2 += 1
            b2 += not ({k: v for k, v in optypes.qs_counts(tr).items() if v} == {k: v for k, v in r[4].items() if v} and m.ops == r[0])
print(f"1. identical to the pre-change lampcore, per number and per type: {n1 - b1}/{n1}")
print(f"2. Python = Rust per type: {n2 - b2}/{n2}")
assert not (b1 or b2)
