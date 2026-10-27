"""The 2'b+pp3 threshold-shift test (predictions/pp3-gap-and-shift.md; run through tools/sealed_run.sh pp3-gap-and-shift).
96 bits, all 640 map numbers, re-sieve off, the reference genes of root-confirm-2 / i032-2prime, card 5f0007a or later.
Cells: 2'a (goff on, full pass; the base); 2'b+pp3 at threshold shifts +0, +1, +2 bits (goff on, root, pp 3;
tc -= d / log2 1,752; L unchanged).
  0. Identity first (stops with an error if it fails): 2'b+pp3 at +0 against 2'b (goff on, root, no pp) is not
     relation-identical (pp changes candidates), so identity is checked only where it must hold: each 2'b+pp3 cell
     against the same genes with goff off (the same factor, candidates, hits and polynomials on all 640 numbers;
     relations on 2 traced numbers).
  1. Priced (official / ruint / Montgomery): mean per number per cell; ratios to 2'a with paired 95% bootstrap
     intervals (10,000, random.Random(2026)); robust ratio and (e) call.
  2. Wall-clock: 8 replicates, each in its own random cell order (timing.shuffled, seed 2028), lampcore --phasetime on
     core 2. Per cell, EVERY region per replicate is saved (setup, gray, sieve, scan, confirm, lp_ledger, solve, ...),
     mean / sd / min / max; ratios to 2'a with 95% t intervals over the 8 replicate pairs for wall and each region;
     core 2's MHz per cell (flagged if the median is > 10% off 2'a's); the machine state before each replicate (the
     frequency limits included).
  3. After the timed replicates, one LAMPCORE_LPBREAK=1 pass per cell (information: lp:copy, lp:hash, lp:comb and
     lp:add ns and calls; the sub-timers add overhead, so these ns are not compared with the timed regions).
  python3 i032shift.py -> i032shift.json, stdout
"""
import json, math, random, statistics, sys
import numpy as np
import partition as P, sizescale2 as S2, qs, lamps
from fastlamps import run_many
from lctest import ref, cost, PT, phasetime
from timing import shuffled

R, REPS, SEED, T7 = 10000, 8, 2028, 2.3646
LB = math.log2(1752.0)
g0 = ref(96)
cells = {"2'a": dict(g0, goff=1)}
for d in range(3):
    cells[f"2'b+pp3 +{d}"] = dict(g0, goff=1, confirm="root", pp=3, tc=g0["tc"] - d / LB)
BASES = tuple((n, "2'a") for n in cells if n != "2'a")
REGIONS = ("setup", "gray", "sieve", "scan", "confirm", "lp_ledger", "solve", "mult", "fb", "resieve")
nums = S2.map_nums(96)

def paired(a, b):
    rng = random.Random(2026)
    n = len(a)
    vals = sorted(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx))
                  for idx in ([rng.randrange(n) for _ in range(n)] for _ in range(R)))
    return 2 ** math.log2(sum(a) / sum(b)), [2 ** vals[int(0.025 * R)], 2 ** vals[int(0.975 * R) - 1]]

def trace(g, N):
    qs.TRACE = {}
    try:
        qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    return [(a.get("rels"), a.get("cands")) for a in tr["attempts"]]

# 0. identity
runs = {n: run_many([g], nums, P.QS_CAP, types=True) for n, g in cells.items()}
for n, g in cells.items():
    if n == "2'a":
        continue
    off = dict(g); off.pop("goff")
    ro = run_many([off], nums, P.QS_CAP, types=True)
    bad = sum(x[1:4] != y[1:4] or x[4]["sieve_scan"] != y[4]["sieve_scan"] for x, y in zip(runs[n], ro))
    rel = all(trace(g, N) == trace(off, N) for N, _, _ in nums[::len(nums) // 2][:2])
    print(f"identity {n} vs the same genes with goff off: factor, candidates, hits and polynomials identical on "
          f"{len(nums) - bad}/{len(nums)} numbers; relations and candidate values identical on 2 traced numbers: {'yes' if rel else 'NO'}", flush=True)
    if bad or not rel:
        sys.exit(f"STOP: identity failed for {n}")
assert all(r[1] is not None for rs in runs.values() for r in rs)

# 1. priced
c = {n: {Pn: [cost(r[4], Pn) for r in rs] for Pn in PT} for n, rs in runs.items()}
out = {"priced": {}, "timing": {}}
for n in cells:
    out["priced"][n] = {"mean": {Pn: float(np.mean(c[n][Pn])) for Pn in PT}}
    print(f"priced {n}: " + " ".join(f"{Pn} {np.mean(c[n][Pn]):,.1f}" for Pn in PT), flush=True)
for a, b in BASES:
    pr = {Pn: paired(c[a][Pn], c[b][Pn]) for Pn in PT}
    info = ""
    out["priced"][f"{a} vs {b}"] = {Pn: {"ratio": v[0], "ci95": v[1]} for Pn, v in pr.items()}
    print(f"priced {a} vs {b}{info}: " + " ".join(f"{Pn} {v[0]:.4f} [{v[1][0]:.4f}, {v[1][1]:.4f}]" for Pn, v in pr.items())
          + f"; robust {max(v[0] for v in pr.values()):.4f}; (e) "
          + ("better" if all(v[1][1] < 1 for v in pr.values()) else "worse" if all(v[1][0] > 1 for v in pr.values()) else "undecided"), flush=True)

# 2. wall-clock
res, order, states, clock = shuffled(cells, nums, reps=REPS, seed=SEED)
def series(n, part):
    if part == "wall":
        return [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in res[n]]
    return [w[part]["ns"] / 1e3 for w in res[n]]
for n in cells:
    rec = {"mhz": clock[n]}
    line = f"timing {n}:"
    for part in ("wall",) + tuple(k for k in REGIONS if k in res[n][0]):
        x = series(n, part)
        rec[part] = {"mean": statistics.mean(x), "sd": statistics.stdev(x), "min": min(x), "max": max(x), "per_replicate": x}
        line += f" {part} {rec[part]['mean']:,.1f} us (sd {rec[part]['sd']:.1f}, {rec[part]['min']:,.1f}-{rec[part]['max']:,.1f});"
    m = clock[n]
    line += (f" core 2 MHz {m['min']:.0f}-{m['max']:.0f}, median {m['median']:.0f} (n {m['n']})" + (" FLAGGED (>10% off 2'a)" if m["flag"] else "")
             if m["n"] else " core 2 MHz: no samples")
    out["timing"][n] = rec
    print(line, flush=True)
for a, b in BASES:
    line = f"timing {a} vs {b}:"
    out["timing"][f"{a} vs {b}"] = {}
    for part in ("wall",) + tuple(k for k in REGIONS if k in res[a][0]):
        ya = series(b, part)
        if not all(ya):
            continue
        q = [x / y for x, y in zip(series(a, part), ya)]
        mq, h = statistics.mean(q), T7 * statistics.stdev(q) / math.sqrt(len(q))
        out["timing"][f"{a} vs {b}"][part] = {"mean": mq, "ci95": [mq - h, mq + h], "half_width": h, "per_replicate": q}
        line += f" {part} {mq:.4f} [{mq - h:.4f}, {mq + h:.4f}] ({100 * (mq - 1):+.1f}%, +-{100 * h:.1f} points);"
    print(line, flush=True)
out["lpbreak"] = {}
for n, g in cells.items():
    lp = phasetime(g, nums, True)
    out["lpbreak"][n] = {k: v for k, v in lp.items() if k.startswith("lp:") or k == "lp_ledger"}
    print(f"lp break {n} (information; sub-timers on): " + " ".join(f"{k} {v['ns'] / 1e3:,.1f} us / {v['calls']:,.1f} calls" for k, v in out["lpbreak"][n].items()), flush=True)
print(f"replicate orders (random.Random({SEED})):")
for r in range(1, REPS + 1):
    print(f"  r{r}: " + ", ".join(n for rr, n in order if rr == r))
for i, s in enumerate(states):
    print(f"## machine state before replicate {i + 1}\n{s}", end="")
out.update(order=order, states=states, seed=SEED)
json.dump(out, open("i032shift.json", "w"), indent=1)
