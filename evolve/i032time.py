"""I-032 option 2', the sealed priced and timed run (predictions/i032-2prime.md; run through tools/sealed_run.sh
i032-2prime). 96 bits, all 640 map numbers, re-sieve off, the reference genes of root-confirm-2.
Cells: REF (goff off, full pass); 2'a (goff on, full pass); 2'b (goff on, root confirm); 2'b+pp3 (goff on, root, pp 3,
threshold +0 bits).
  0. Identity first (stops with an error if it fails): on all 640 numbers (lampcore), 2'a against REF and 2'b against
     2'a give the same factor, candidates and hits; on 2 numbers (Python traces), the same relations and candidate
     values.
  1. Priced (official / ruint / Montgomery): mean per number per cell; ratios with paired 95% bootstrap intervals
     (10,000, random.Random(2026)) for 2'a vs REF, 2'b vs 2'a and 2'b+pp3 vs 2'a; every cell vs REF for information.
  2. Wall-clock: 8 replicates, each in its own random cell order (timing.shuffled, seed 2027), lampcore --phasetime on
     core 2; wall, sieve and confirm per cell (mean, sd, min, max); ratios on the same bases with 95% t intervals over
     the 8 replicate pairs; core 2's MHz per cell (flagged if the median is > 10% off REF's); the machine state
     before each replicate.
  python3 i032time.py -> i032time.json, stdout
"""
import json, math, random, statistics, sys
import numpy as np
import partition as P, sizescale2 as S2, qs, lamps
from fastlamps import run_many
from lctest import ref, cost, PT
from timing import shuffled

R, REPS, SEED, T7 = 10000, 8, 2027, 2.3646
g0 = ref(96)
cells = {"REF": g0, "2'a": dict(g0, goff=1), "2'b": dict(g0, goff=1, confirm="root"),
         "2'b+pp3": dict(g0, goff=1, confirm="root", pp=3)}
BASES = (("2'a", "REF"), ("2'b", "2'a"), ("2'b+pp3", "2'a"))
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
for a, b in (("2'a", "REF"), ("2'b", "2'a")):
    bad = sum(x[1:4] != y[1:4] or x[4]["sieve_scan"] != y[4]["sieve_scan"] for x, y in zip(runs[a], runs[b]))
    rel = all(trace(cells[a], N) == trace(cells[b], N) for N, _, _ in nums[::len(nums) // 2][:2])
    print(f"identity {a} vs {b}: factor, candidates, hits and polynomials identical on {len(nums) - bad}/{len(nums)} numbers; "
          f"relations and candidate values identical on 2 traced numbers: {'yes' if rel else 'NO'}", flush=True)
    if bad or not rel:
        sys.exit(f"STOP: identity failed for {a} vs {b}")
assert all(r[1] is not None for rs in runs.values() for r in rs)

# 1. priced
c = {n: {Pn: [cost(r[4], Pn) for r in rs] for Pn in PT} for n, rs in runs.items()}
out = {"priced": {}, "timing": {}}
for n in cells:
    out["priced"][n] = {"mean": {Pn: float(np.mean(c[n][Pn])) for Pn in PT}}
    print(f"priced {n}: " + " ".join(f"{Pn} {np.mean(c[n][Pn]):,.1f}" for Pn in PT), flush=True)
for a, b in BASES + tuple((n, "REF") for n in ("2'b", "2'b+pp3")):
    pr = {Pn: paired(c[a][Pn], c[b][Pn]) for Pn in PT}
    info = "" if (a, b) in BASES else " (information)"
    out["priced"][f"{a} vs {b}"] = {Pn: {"ratio": v[0], "ci95": v[1]} for Pn, v in pr.items()}
    print(f"priced {a} vs {b}{info}: " + " ".join(f"{Pn} {v[0]:.4f} [{v[1][0]:.4f}, {v[1][1]:.4f}]" for Pn, v in pr.items())
          + f"; robust {max(v[0] for v in pr.values()):.4f}", flush=True)

# 2. wall-clock
res, order, states, clock = shuffled(cells, nums, reps=REPS, seed=SEED)
def series(n, part):
    if part == "wall":
        return [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in res[n]]
    return [w[part]["ns"] / 1e3 for w in res[n]]
for n in cells:
    rec = {"mhz": clock[n]}
    line = f"timing {n}:"
    for part in ("wall", "sieve", "confirm"):
        x = series(n, part)
        rec[part] = {"mean": statistics.mean(x), "sd": statistics.stdev(x), "min": min(x), "max": max(x), "per_replicate": x}
        line += f" {part} {rec[part]['mean']:,.1f} us (sd {rec[part]['sd']:.1f}, {rec[part]['min']:,.1f}-{rec[part]['max']:,.1f});"
    m = clock[n]
    line += (f" core 2 MHz {m['min']:.0f}-{m['max']:.0f}, median {m['median']:.0f} (n {m['n']})" + (" FLAGGED (>10% off REF)" if m["flag"] else "")
             if m["n"] else " core 2 MHz: no samples")
    out["timing"][n] = rec
    print(line, flush=True)
for a, b in BASES + tuple((n, "REF") for n in ("2'b", "2'b+pp3")):
    info = "" if (a, b) in BASES else " (information)"
    line = f"timing {a} vs {b}{info}:"
    out["timing"][f"{a} vs {b}"] = {}
    for part in ("wall", "sieve", "confirm"):
        q = [x / y for x, y in zip(series(a, part), series(b, part))]
        mq, h = statistics.mean(q), T7 * statistics.stdev(q) / math.sqrt(len(q))
        out["timing"][f"{a} vs {b}"][part] = {"mean": mq, "ci95": [mq - h, mq + h], "half_width": h, "per_replicate": q}
        line += f" {part} {mq:.4f} [{mq - h:.4f}, {mq + h:.4f}] ({100 * (mq - 1):+.1f}%, +-{100 * h:.1f} points);"
    print(line, flush=True)
print(f"replicate orders (random.Random({SEED})):")
for r in range(1, REPS + 1):
    print(f"  r{r}: " + ", ".join(n for rr, n in order if rr == r))
for i, s in enumerate(states):
    print(f"## machine state before replicate {i + 1}\n{s}", end="")
out.update(order=order, states=states, seed=SEED)
json.dump(out, open("i032time.json", "w"), indent=1)
