"""Stage 7 lc sweep on the tuning seeds (picks lc; never used to judge the card).

Tuned qs (kc 32, bc 1.1, mc 0.25, tc 1.38) with lc in {1.0, 1.2, 1.4, 1.6, 1.8}, on
semiprimes_pq(bits, 40, 1700000 + bits) at 72, 78, 84 bits, cap 2^28, lamps.py (lampcore has
no lc yet). Per cell: log2 mean ops [95% CI] (run6_accept.py's bootstrap), worst, misses;
partials (cofactors below L), combinations, duplicates, pairing yield (combined relations per
partial), share of matrix rows that are combined relations, mean ops per phase; and an exact
check of the lp phase: lp ops = cofactors + 2 * partials + inserts + combinations * (1 + F),
summed over attempts (a partial whose q divides N would skip its lookup; none occurred if
the check holds).

  python3 stage7_lc_sweep.py [workers]  -> stage7_lc_sweep.json
"""
import json, math, sys
from multiprocessing import Pool
import qs
from lamps import run
from fastlamps import semiprimes_pq
from revalidate import bootstrap

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
CAP = 2 ** 28
LC = [1.0, 1.2, 1.4, 1.6, 1.8]
SIZES = [72, 78, 84]
PH = ["mult", "fb", "setup", "sieve", "confirm", "lp", "la", "sqrt"]

def job(args):
    lc, bits, N = args
    g = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": lc}
    qs.TRACE = {}
    ops, d = run([g], N, CAP)
    tr = qs.TRACE
    lp = {k: sum(at["lp"][k] for at in tr["attempts"] if "lp" in at)
          for k in ("cof", "lt", "inserts", "combos", "dup")}
    expect = sum(at["lp"]["cof"] + 2 * at["lp"]["lt"] + at["lp"]["inserts"]
                 + at["lp"]["combos"] * (1 + at["lp"]["F"]) for at in tr["attempts"] if "lp" in at)
    rows = sum(at["rows"] for at in tr["attempts"])
    ys = sum(dp["ys"] for at in tr["attempts"] for dp in at["deps"])
    return lc, bits, {"ops": ops, "factor_ok": ops is None or N % d == 0,
                      "phases": {k: tr["ops"].get(k, 0) for k in PH},
                      "lp": lp, "lp_ok": tr["ops"].get("lp", 0) == expect,
                      "attempts": len(tr["attempts"]), "rows": rows, "ys": ys}

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, 40, 1700000 + b) for b in SIZES}
    jobs = [(lc, b, N) for lc in LC for b in SIZES for N, p, q in nums[b]]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=2)
    out = {"cap_log2": 28, "genes": {"kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38},
           "seed": "1700000 + bits", "count": 40, "cells": {}}
    for lc in LC:
        for b in SIZES:
            rs = [r for l, bb, r in res if l == lc and bb == b]
            ops = [r["ops"] for r in rs if r["ops"] is not None]
            lp = {k: sum(r["lp"][k] for r in rs) for k in rs[0]["lp"]}
            cell = {"mean_log2": math.log2(sum(ops) / len(ops)), "ci95": list(bootstrap(ops)),
                    "worst_log2": math.log2(max(ops)), "misses": len(rs) - len(ops),
                    "lp": lp, "pairing_yield": lp["combos"] / lp["lt"] if lp["lt"] else None,
                    "combined_row_share": (lp["combos"] - lp["dup"]) / sum(r["rows"] for r in rs),
                    "phase_mean_log2": {k: (math.log2(sum(r["phases"][k] for r in rs) / len(rs))
                                            if sum(r["phases"][k] for r in rs) else None) for k in PH},
                    "retries": sum(r["attempts"] - 1 for r in rs),
                    "lp_accounting_ok": all(r["lp_ok"] for r in rs),
                    "factors_ok": all(r["factor_ok"] for r in rs)}
            out["cells"][f"{b} lc={lc}"] = cell
    for b in SIZES:
        print(f"\n{b} bits (40 numbers, seed 1700000 + {b}):")
        print(f"{'lc':5s} {'log2 mean [95% CI]':24s} {'worst':6s} miss  partials  combos  dup  "
              f"yield  comb.rows  confirm  sieve   lp     acct")
        for lc in LC:
            c = out["cells"][f"{b} lc={lc}"]
            pm = c["phase_mean_log2"]
            f = lambda k: f"{pm[k]:.2f}" if pm[k] is not None else "  -  "
            print(f"{lc:<5} {c['mean_log2']:.2f} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]     "
                  f"{c['worst_log2']:.2f}  {c['misses']:3d}  {c['lp']['lt']:8d}  {c['lp']['combos']:6d} "
                  f"{c['lp']['dup']:4d}  " + (f"{c['pairing_yield']:.3f}" if c['pairing_yield'] is not None else "  -  ")
                  + f"  {c['combined_row_share']:.3f}      {f('confirm')}    {f('sieve')}   {f('lp')}  "
                  + ("ok" if c["lp_accounting_ok"] and c["factors_ok"] else "FAIL"))
    json.dump(out, open("stage7_lc_sweep.json", "w"), indent=1)
