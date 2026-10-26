"""Acceptance for root-matched confirmation by re-sieving (NOTES.md, "Root-matched candidate confirmation:
cost model"; tests written before the code).

  1. confirm absent = the committed lampcore (LAMPCORE_OLD), per type and per number, on the map numbers
     (54-96 bits), for the new reference genes per size and qs + lc 1.4 (frozen and corrected).
  2. confirm = resieve finds the same relations: per number, the same factor, ops-independent fields
     (tests, hits) and every per-type count except confirm_td and word, against confirm absent; confirm_td
     falls and word appears. Also p0 = 2 (re-sieve every prime) and p0 = 1000 (no prime re-sieved, so
     confirm_td = 1 + |direct| per candidate, still the same relations).
  3. Python = Rust per type with confirm = resieve, on 2 numbers per size per genome.

  LAMPCORE_OLD=<committed binary> python3 resieve_accept.py -> stdout
"""
import os, json
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))

def genomes(bits):
    return {"new ref": dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32"),
            "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

def run(g, nums, binary=None):
    b0 = fastlamps.BIN
    if binary:
        fastlamps.BIN = binary
    try:
        return run_many([g], nums, P.QS_CAP, inst=False, types=True)
    finally:
        fastlamps.BIN = b0

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = n3 = b3 = 0
    drop = {}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        for name, g in genomes(bits).items():
            cur = run(g, nums)
            old = run(g, nums, os.environ["LAMPCORE_OLD"])
            for a, b in zip(cur, old):
                n1 += 1
                b1 += a != b
            for p0 in (30, 2, 1000):
                rs = run(dict(g, confirm="resieve", p0=p0), nums)
                ctd = [0, 0]
                for a, b in zip(rs, cur):
                    n2 += 1
                    ta = {k: v for k, v in a[4].items() if k not in ("confirm_td", "word")}
                    tb = {k: v for k, v in b[4].items() if k not in ("confirm_td", "word")}
                    same = (a[1] == b[1] and a[2:4] == b[2:4] and ta == tb and a[4]["confirm_td"] <= b[4]["confirm_td"]
                            and (a[4]["word"] > 0 or p0 == 1000))
                    b2 += not same
                    ctd[0] += a[4]["confirm_td"]; ctd[1] += b[4]["confirm_td"]
                drop[(bits, name, p0)] = ctd[0] / ctd[1]
            g2 = dict(g, confirm="resieve")
            for N, p, q in nums[::len(nums) // 2][:2]:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    d = qs.lamp_qs(N, g2, m)
                except lamps.Budget:
                    d = None
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                r = run(g2, [(N, p, q)])[0]
                rt = {k: v for k, v in r[4].items() if v}
                n3 += 1
                b3 += not (py == rt and m.ops == r[0] and ((d is None and r[1] is None) or (d is not None and r[1] is not None and int(r[1]) == d)))
    print(f"1. confirm absent = committed lampcore: {n1 - b1}/{n1} runs identical")
    print(f"2. confirm = resieve (p0 30 / 2 / 1000): same relations and every other type: {n2 - b2}/{n2}")
    for bits in SS.SIZES:
        print(f"   {bits} bits confirm_td new/old, p0 30 / 2 / 1000: " + "; ".join(
            f"{name} " + " / ".join(f"{drop[(bits, name, p0)]:.3f}" for p0 in (30, 2, 1000)) for name in genomes(bits)))
    print(f"3. Python = Rust per type with confirm = resieve: {n3 - b3}/{n3}")
    assert not (b1 or b2 or b3)
