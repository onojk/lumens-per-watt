"""Stage 3 microbenchmark driver (cost note only; information): bench/copybench (a standalone crate, lampcore untouched)
pinned to core 2 under the standing conditions (cap 2,400 MHz, AC; checked first), 5 replicates per size.
Inputs per size from Python traces of the reference (2'b), 6 map numbers per size: kept relations per number
296 / 462 / 927, mean list length 10.78 / 11.53 / 11.74, F 58 / 91.7 / 136.5, the A-primes' mean base index
21.6 / 38.7 / 79.5 (estimated 2 + pi(p)/2), s = 4; widths 463 / 1,121 / 2,113. 100-128 bits: each input extrapolated
log-linearly in bits from the three (a model).
  python3 copybench_run.py -> copybench_run.json, stdout"""
import json, math, statistics, subprocess, sys
import numpy as np
from baseline_msieve import conditions
from timing import machine_state
BIN = "../bench/copybench/target/release/copybench"
MEAS = {72: (296, 10.78, 58.0, 21.6, 463), 84: (462, 11.53, 91.7, 38.7, 1121), 96: (927, 11.74, 136.5, 79.5, 2113)}
bad = conditions()
if bad:
    sys.exit("timing skipped: " + "; ".join(bad))
xs = np.array(sorted(MEAS))
fit = [np.polyfit(xs, np.log([MEAS[b][i] for b in xs]), 1) for i in range(5)]
sizes = {b: MEAS[b] for b in MEAS}
for b in (100, 108, 116, 128):
    sizes[b] = tuple(float(math.exp(np.polyval(f, b))) for f in fit)
out = {"state": machine_state(), "sizes": {}}
for b, (rels, ln, F, idx, w) in sorted(sizes.items()):
    rels_i, ln_i, F_i, idx_i, w_i = int(round(rels)), int(round(ln)), int(round(F)), int(round(idx)), int(round(w))
    reps = max(3, int(400000 / rels_i))
    rows = []
    for _ in range(5):
        res = subprocess.run(["taskset", "-c", "2", BIN, str(ln_i), str(rels_i), str(w_i), str(reps), str(F_i), str(idx_i), "4"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
        rows.append({**json.loads(res[0]), **json.loads(res[1])})
    med = {k: statistics.median(r[k] for r in rows) for k in ("ns_per_relation_lookups", "ns_per_copy_alone", "ns_per_copy_under_pressure")}
    out["sizes"][b] = {"model": b not in MEAS, "kept_per_number": rels, "list_len": ln, "F": F, "a_index": idx, "width": w,
                       "replicates": rows, "median": med}
    print(f"{b} bits{' (model inputs)' if b not in MEAS else ''}: kept {rels:,.0f}/number, list {ln:.1f}, F {F:.0f}, A-prime index {idx:.0f}: "
          f"ns per kept relation: A-prime lookups {med['ns_per_relation_lookups']:.1f}, copy alone {med['ns_per_copy_alone']:.1f}, "
          f"copy under sieve-sweep pressure {med['ns_per_copy_under_pressure']:.1f} (information; see the caveat)", flush=True)
json.dump(out, open("copybench_run.json", "w"), indent=1)
