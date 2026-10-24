"""Stage 8 tuning: fix ECM's b1 and b2 on the tuning seeds before any comparison (NOTES.md,
"Stage 8"). Numbers: semiprimes_pq(bits, 40, 3000000 + bits) at 72, 78, 84 bits, used for
nothing else. Grid: b1 in {0.25, 0.5, 1, 2, 4} x b2 in {0, 25, 50, 100, 200} (b2 = 0: no
stage 2); curves and s0 at their defaults. Cap 2^29.

Rule, fixed before running: the frozen cell is the one with the lowest average over the
three sizes of log2(mean ops). Reported beside it: each cell's per-size means and 95%
bootstrap intervals, and the mean curves per number.

  python3 ecm_tune.py [workers]  -> ecm_tune.json
"""
import json, math, sys
from multiprocessing import Pool
import ecm
from lamps import Meter, Budget
from fastlamps import semiprimes_pq
from revalidate import bootstrap

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SIZES = (72, 78, 84)
B1S = (0.25, 0.5, 1.0, 2.0, 4.0)
B2S = (0, 25, 50, 100, 200)
CAP = 2 ** 29

def job(args):
    b1, b2, bits, N = args
    m = Meter(CAP)
    ecm.TRACE = {}
    try:
        d = ecm.lamp_ecm(N, {"b1": b1, "b2": b2}, m)
    except Budget:
        d = None
    return b1, b2, bits, (m.ops if d else None), len(ecm.TRACE["curves"])

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, 40, 3000000 + b) for b in SIZES}
    jobs = [(b1, b2, b, N) for b1 in B1S for b2 in B2S for b in SIZES for N, p, q in nums[b]]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=4)
    cells = {}
    for b1 in B1S:
        for b2 in B2S:
            c = {}
            for b in SIZES:
                r = [x for x in res if x[0] == b1 and x[1] == b2 and x[2] == b]
                ops = [x[3] for x in r if x[3] is not None]
                c[b] = dict(mean_log2=math.log2(sum(ops) / len(ops)), ci95=list(bootstrap(ops)),
                            misses=len(r) - len(ops), curves=sum(x[4] for x in r) / len(r))
            c["score"] = sum(c[b]["mean_log2"] for b in SIZES) / len(SIZES)
            cells[f"{b1}/{b2}"] = c
    best = min(cells, key=lambda k: cells[k]["score"])
    print("b1/b2       score   " + "   ".join(f"{b}: mean [95% CI] curves" for b in SIZES))
    for k, c in sorted(cells.items(), key=lambda kv: kv[1]["score"]):
        print(f"{k:10s}  {c['score']:.3f}  " + "  ".join(
            f"{c[b]['mean_log2']:.2f} [{c[b]['ci95'][0]:.2f}, {c[b]['ci95'][1]:.2f}] {c[b]['curves']:.1f}"
            + ("*" if c[b]["misses"] else "") for b in SIZES))
    b1, b2 = map(float, best.split("/"))
    print(f"\nfrozen: b1 = {b1}, b2 = {b2:g}")
    json.dump({"seeds": "3000000 + bits", "sizes": SIZES, "cap_log2": 29, "rule":
               "lowest average over sizes of log2(mean ops)", "cells": cells,
               "frozen": {"b1": b1, "b2": b2}}, open("ecm_tune.json", "w"), indent=1)
