"""Acceptance for the pm1 absolute bound (NOTES.md, "(A1)"; tests written before the code).

  1. Python: the B-card (B = 2^k) equals the b-card entries of pm1check_map.json (ops, success,
     per-type counts) on all 2,000 map numbers, k = 8 .. 15.
  2. Rust = Python: lampcore with the B-card alone, per-type counts and factor, on the 54- and
     84-bit map numbers at k = 8, 11 and 14.

  python3 bround_accept.py [workers]  -> stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json
from multiprocessing import Pool
import partition as P
import sizescale2 as S2
from fastlamps import run_many

def job(args):
    N, k = args
    r = P.run_alone({"t": "pm1", "b": 0.2, "B": 2 ** k}, N, P.PRE_CAP, [])
    return {"T": r["T"], "ops": r["ops"], "per_type": r["per_type"]}

if __name__ == "__main__":
    workers = int(ARGS[0]) if ARGS else 8
    pmap = json.load(open("pm1check_map.json"))
    bad = n = 0
    with Pool(workers) as pool:
        for bits, d in pmap.items():
            Ns = [int(x) for x in d["N"]]
            for k in range(8, 16):
                res = pool.map(job, [(N, k) for N in Ns], chunksize=16)
                for a, b in zip(res, d[str(k)]):
                    n += 1
                    bad += a != b
    print(f"1. B-card = b-card map entries: {n - bad}/{n} equal")
    mism = m = 0
    for bits in ("54", "84"):
        nums = S2.map_nums(int(bits))
        for k in (8, 11, 14):
            rs = run_many([{"t": "pm1", "b": 0.2, "B": 2 ** k}], nums, P.QS_CAP, types=True)
            for x, (N, _, _) in zip(rs, nums):
                py = job((N, k))
                m += 1
                rt = {t: v for t, v in x[4].items() if v}
                pt = {t: v for t, v in py["per_type"].items() if v}
                ok = rt == pt and ((x[1] is None) == (py["T"] is None)) and (py["T"] is None or x[0] == py["T"])
                mism += not ok
    print(f"2. Rust = Python (B-card alone): {m - mism}/{m} agree")
    assert not bad and not mism
