"""qs boundary sweep, second grid: below the edge of qs_boundary_sweep.py's.

qs alone with N51-0917's kc 32 and tc 1.38, on the 78- and 84-bit ACCEPT sets, cap 2^28,
grid mc in {0.03, 0.06, 0.12, 0.25} x bc in {0.9, 1.0, 1.1, 1.2}. Per cell: log2 mean [95% CI]
(run6_accept.py's bootstrap), worst, misses. Question: where below mc = 0.25 (the first grid's
best cell, on its edge) does the optimum sit?

Every cell runs in BOTH cores, after the qs.rs fix for primes wider than the sieve interval;
the cell's numbers come from lamps.py and the per-cell count of lampcore disagreements (ops,
factor, tests, hits) is reported beside it. It must be 0 everywhere (it is: no lampcore
disagreements in any cell).

  python3 qs_boundary_sweep2.py [workers]  -> qs_boundary_sweep2.json, .out by redirect
"""
import json, math, sys
from multiprocessing import Pool
from lamps import run, LAST
from fastlamps import semiprimes_pq, run_many
from revalidate import bootstrap
from run6_accept import bootstrap_worst, SETS, CAP

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MC = [0.03, 0.06, 0.12, 0.25]
BC = [0.9, 1.0, 1.1, 1.2]
SIZES = [78, 84]
gene = lambda mc, bc: [{"t": "qs", "kc": 32, "bc": bc, "mc": mc, "tc": 1.38}]

def job(args):
    mc, bc, bits = args
    count, seed = SETS[bits]
    nums = semiprimes_pq(bits, count, seed)
    fast = run_many(gene(mc, bc), nums, CAP)
    r = []
    for N, p, q in nums:
        ops, d = run(gene(mc, bc), N, CAP)
        r.append((ops, d, LAST["tests"], LAST["hits"]))
    rust_mismatch = sum(a != b for a, b in zip(r, fast))
    all_ops = [x[0] for x in r]
    ops = [x for x in all_ops if x is not None]
    capped = [CAP if x is None else x for x in all_ops]
    return mc, bc, bits, {
        "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
        "ci95": list(bootstrap(ops)) if ops else None,
        "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
        "misses": len(all_ops) - len(ops), "rust_mismatch": rust_mismatch}

if __name__ == "__main__":
    with Pool(WORKERS) as pool:
        res = pool.map(job, [(mc, bc, b) for b in SIZES for mc in MC for bc in BC])
    out = {"cap_log2": 28, "kc": 32, "tc": 1.38, "mc": MC, "bc": BC, "cells": {}}
    for mc, bc, b, cell in res:
        out["cells"][f"{b} mc={mc} bc={bc}"] = cell
    for b in SIZES:
        print(f"\n{b} bits: log2 mean [95% CI] (misses starred); rows mc, columns bc")
        print("mc \\ bc " + "".join(f"{bc:<22}" for bc in BC))
        best = min((c["mean_log2"], k) for k, c in out["cells"].items() if k.startswith(f"{b} ") and c["mean_log2"])
        for mc in MC:
            row = ""
            for bc in BC:
                c = out["cells"][f"{b} mc={mc} bc={bc}"]
                mark = "<" if f"{b} mc={mc} bc={bc}" == best[1] else ("*" if c["misses"] else " ")
                row += (f"{c['mean_log2']:.2f}{mark}[{c['ci95'][0]:.2f},{c['ci95'][1]:.2f}]" if c["mean_log2"] else "all missed").ljust(22)
            print(f"{mc:<8}" + row)
        print(f"best: {best[1]} at {best[0]:.3f}")
        print("lampcore disagreements per cell (of 80): " + (", ".join(
            f"mc={mc} bc={bc}: {out['cells'][f'{b} mc={mc} bc={bc}']['rust_mismatch']}"
            for mc in MC for bc in BC if out['cells'][f'{b} mc={mc} bc={bc}']['rust_mismatch']) or "none"))
    json.dump(out, open("qs_boundary_sweep2.json", "w"), indent=1)
