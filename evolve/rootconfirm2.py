"""Root confirm, the retime (predictions/root-confirm-2.md; run through tools/sealed_run.sh root-confirm-2). 96 bits,
all 640 map numbers, re-sieve off, card e13603a. Cells: the reference (full pass, pp absent); root alone; root + pp 3
("2 free") at threshold shifts 0, +1, +2, +3 bits (tc -= d / log2 1,752; L unchanged). Counts and priced totals are
those of root-confirm (574f356); only the wall-clock is new.
Wall-clock: 8 replicates, each timing every cell once in its own seeded random order (timing.shuffled, seed 2026;
the orders are recorded), core 2's MHz sampled every second per cell, the machine state read before each replicate.
Per cell: total wall, sieve and confirm regions, per replicate; mean, sd, min and max over the 8; the ratio to the
reference within each replicate, its mean and a 95% t interval over the 8 replicate pairs (t 0.975, 7 df = 2.3646).
  python3 rootconfirm2.py -> rootconfirm2.json, stdout
"""
import json, math, statistics
import sizescale2 as S2
from lctest import ref
from timing import shuffled

LB = math.log2(1752.0)
REPS, SEED, T7 = 8, 2026, 2.3646

g0 = ref(96)
rt = dict(g0, confirm="root")
cells = {"reference": g0, "root": rt}
for d in range(4):
    cells[f"root + pp 3, +{d} bits"] = dict(rt, pp=3, tc=g0["tc"] - d / LB)
nums = S2.map_nums(96)

res, order, states, clock = shuffled(cells, nums, reps=REPS, seed=SEED)

def series(name, part):
    if part == "wall":
        return [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in res[name]]
    return [w[part]["ns"] / 1e3 for w in res[name]]

def summary(x):
    return {"mean": statistics.mean(x), "sd": statistics.stdev(x), "min": min(x), "max": max(x), "per_replicate": x}

def ratio(x, y):
    q = [a / b for a, b in zip(x, y)]
    m, h = statistics.mean(q), T7 * statistics.stdev(q) / math.sqrt(len(q))
    return {"mean": m, "ci95": [m - h, m + h], "half_width": h, "per_replicate": q}

out = {}
for name, g in cells.items():
    rec = {"tc": g["tc"], "pp": g.get("pp", 0), "confirm": g.get("confirm", "full"),
           "candidates": res[name][0]["confirm"]["calls"], "mhz": clock[name]}
    line = f"{name} (pp {rec['pp']}, tc {g['tc']:.4f}, confirm {rec['confirm']}): candidates {rec['candidates']:,.1f} per number"
    for part in ("wall", "sieve", "confirm"):
        x = series(name, part)
        rec[part] = summary(x)
        line += f"; {part} {rec[part]['mean']:,.1f} us (sd {rec[part]['sd']:.1f}, {rec[part]['min']:,.1f}-{rec[part]['max']:,.1f})"
        if name != "reference":
            rec[part + "_ratio"] = r = ratio(x, series("reference", part))
            line += f" ratio {r['mean']:.4f} [{r['ci95'][0]:.4f}, {r['ci95'][1]:.4f}] ({100 * (r['mean'] - 1):+.1f}%, +-{100 * r['half_width']:.1f} points)"
    c = clock[name]
    line += "; core 2 MHz " + (f"{c['min']:.0f}-{c['max']:.0f}, median {c['median']:.0f} (n {c['n']})"
                               + (" FLAGGED (>10% off the reference)" if c["flag"] else "") if c["n"] else "no samples")
    out[name] = rec
    print(line, flush=True)
print(f"replicate orders (random.Random({SEED})):")
for r in range(1, REPS + 1):
    print(f"  r{r}: " + ", ".join(n for rr, n in order if rr == r))
for i, s in enumerate(states):
    print(f"## machine state before replicate {i + 1}\n{s}", end="")
json.dump({"cells": out, "order": order, "states": states, "seed": SEED}, open("rootconfirm2.json", "w"), indent=1)
