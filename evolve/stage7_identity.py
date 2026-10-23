"""Stage 7 identity: qs with lc = 1.0 (and with no lc gene) equals today's qs op for op.

Today's qs is lampcore's (parity-equal to lamps.py at b3e062b on every qs pair). Fields:
ops, factor, tests, hits, stage, k, and every phase; the lp phase must be 0.
Numbers: the qs acceptance set semiprimes_pq(bits, 40, 770000 + bits) at 40-60 bits and the
Stage 2 numbers semiprimes_pq(bits, 80, 990000 + bits) at 66/72/78; cap 2^29.
Genes: qs-default and tuned qs (kc 32, bc 1.1, mc 0.25, tc 1.38).

  python3 stage7_identity.py [workers]
"""
import sys
from multiprocessing import Pool
import qs
from lamps import run, LAST
from fastlamps import semiprimes_pq, run_many, PHASES

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
CAP = 2 ** 29
GENES = {"default": {"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0},
         "tuned": {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}}
SETS = [(b, 40, 770000 + b) for b in (40, 44, 48, 52, 56, 60)] + \
       [(b, 80, 990000 + b) for b in (66, 72, 78)]

def job(args):
    name, lc, bits, N = args
    g = dict(GENES[name])
    if lc is not None:
        g["lc"] = lc
    qs.TRACE = {}
    ops, d = run([g], N, CAP)
    ph = {k: qs.TRACE.get("ops", {}).get(k, 0) for k in PHASES}
    lp = qs.TRACE.get("ops", {}).get("lp", 0)
    return name, lc, bits, N, (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"], ph), lp

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, c, s) for b, c, s in SETS}
    ref = {}
    for name, g in GENES.items():
        for b in nums:
            for (N, p, q), f in zip(nums[b], run_many([g], nums[b], CAP, inst=True, phases=True)):
                ref[name, N] = f
    jobs = [(name, lc, b, N) for name in GENES for lc in (1.0, None) for b in nums
            for N, p, q in nums[b]]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=4)
    bad = [(name, lc, b, N, slow, ref[name, N]) for name, lc, b, N, slow, lp in res
           if slow != ref[name, N] or lp]
    misses = sum(1 for *_, slow, lp in res if slow[0] is None)
    print(f"identity: {len(res)} runs (2 gene sets x lc 1.0 / absent x {sum(len(v) for v in nums.values())} "
          f"numbers), mismatches vs today's qs {len(bad)}, lp ops nonzero "
          f"{sum(1 for *_, lp in res if lp)}, misses {misses}")
    for x in bad[:5]:
        print("MISMATCH", x)
    sys.exit(1 if bad else 0)
