"""Acceptance for the Gray-code root update without a reduction (NOTES.md, "Gray-code root update without a
reduction"; card code change, op counts and results identical).

  1. Against the pre-change lampcore (LAMPCORE_OLD), per number on all map numbers (54-96): every field and
     every type identical, for the new reference (with and without re-sieve), the frozen and the corrected
     reference.
  2. Python = Rust per type, 2 numbers per size per genome.

  LAMPCORE_OLD=<pre-change binary> python3 gray_a_accept.py -> stdout
"""
import os, json
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    return {"new ref": nr, "new ref + re-sieve": dict(nr, confirm="resieve"), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = 0
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        for name, g in genomes(bits).items():
            for a, b in zip(run(g, nums), run(g, nums, old=True)):
                n1 += 1
                b1 += a != b
            for N, p, q in nums[::len(nums) // 2][:2]:
                m = lamps.Meter(P.QS_CAP)
                qs.TRACE = {}
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                r = run(g, [(N, p, q)])[0]
                n2 += 1
                b2 += not (py == {k: v for k, v in r[4].items() if v} and m.ops == r[0])
        print(f"{bits} bits done", flush=True)
    print(f"1. vs pre-change lampcore: identical per number and per type: {n1 - b1}/{n1}")
    print(f"2. Python = Rust per type: {n2 - b2}/{n2}")
    assert not (b1 or b2)
