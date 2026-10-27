"""2'b+pp3 threshold shifts, follow-ups to pp3-gap-and-shift (same design as i032shift.py, which stays as committed).
  python3 shiftrun.py A -> shiftrun_A.json, stdout   (predictions/shift-past-2.md; tools/sealed_run.sh shift-past-2)
      96 bits, 640 map numbers. Cells: 2'a (base), 2'b, 2'b+pp3 at +1, +2 and +3 bits (+2 added before the run, at the reviewer's request) (tc -= d / log2 1,752, as
      i032shift.py). Region excess over own-rate price against 2'b (and 2'a for information).
  python3 shiftrun.py B -> shiftrun_B.json, stdout   (predictions/shift-72-84.md; tools/sealed_run.sh shift-72-84)
      72 and 84 bits, all map numbers (480, 560). Cells per size: 2'a (base), 2'b+pp3 at +0, +1, +2 bits
      (tc -= d / log2 B, B the mean of the card's B over the size's map numbers, lctest.bnd: 588.5 at 72, 1,094.5 at 84).
Re-sieve off; the reference genes (lctest.ref) with goff = 1 (the reference since Oct 26).
  0. Identity first (stops with an error if it fails): 2'b against 2'a (A): the same factor, candidates, hits and
     polynomials on every number, relations and candidate values on 2 traced numbers; each 2'b+pp3 cell against the
     same genes with goff off, likewise.
  1. Priced (official / ruint / Montgomery): mean per number per cell; ratios with paired 95% bootstrap intervals
     (10,000, random.Random(2026)); robust ratio and (e) call. Bases: every cell against 2'a; in A also the 2'b+pp3
     cells against 2'b (information).
  2. Wall-clock: 8 replicates per size, each in its own random cell order (timing.shuffled, seed 2029 for A, 2030 + size
     for B), lampcore --phasetime on core 2; every region per replicate with its own ruint and calls; ratios with 95% t
     intervals over the 8 replicate pairs (t7 2.3646) for wall and every region; core 2's MHz per cell; the machine
     state before each replicate.
  3. Region excess over own-rate price: for each region, (wall ratio - ruint ratio) x the base's region mean, per
     replicate, mean and 95% t. scan has no ops of its own (sieve_scan is charged in the sieve region): its expected
     ratio is the ratio of its calls (polynomials scanned). Bases: 2'b (A, the scored base for R2-16) and 2'a.
  4. One LAMPCORE_LPBREAK=1 pass per cell (information; sub-timers add overhead).
"""
import json, math, random, statistics, sys
MODE = sys.argv[1] if len(sys.argv) > 1 else ""   # before the imports: partition and sizescale clear sys.argv
import numpy as np
import partition as P, sizescale2 as S2, qs, lamps
from fastlamps import run_many
from lctest import ref, cost, PT, phasetime, bnd
from timing import shuffled

R, REPS, T7 = 10000, 8, 2.3646
REGIONS = ("setup", "gray", "sieve", "scan", "confirm", "lp_ledger", "solve", "mult", "fb", "resieve")
EXCESS = ("setup", "gray", "scan", "lp_ledger", "solve", "mult", "fb", "sieve", "confirm")

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

def identity(a, ga, gb, ra, rb, nums):
    bad = sum(x[1:4] != y[1:4] or x[4]["sieve_scan"] != y[4]["sieve_scan"] for x, y in zip(ra, rb))
    rel = all(trace(ga, N) == trace(gb, N) for N, _, _ in nums[::len(nums) // 2][:2])
    print(f"identity {a}: factor, candidates, hits and polynomials identical on {len(nums) - bad}/{len(nums)} numbers; "
          f"relations and candidate values identical on 2 traced numbers: {'yes' if rel else 'NO'}", flush=True)
    if bad or not rel:
        sys.exit(f"STOP: identity failed for {a}")

def size_run(bits, cells, pbases, tbases, xbases, seed, tag):
    nums = S2.map_nums(bits)
    out = {"bits": bits, "priced": {}, "timing": {}, "excess": {}}
    # 0. identity
    runs = {n: run_many([g], nums, P.QS_CAP, types=True) for n, g in cells.items()}
    if "2'b" in cells:
        identity(f"{tag}2'b vs 2'a", cells["2'b"], cells["2'a"], runs["2'b"], runs["2'a"], nums)
    for n, g in cells.items():
        if "pp3" in n:
            off = dict(g); off.pop("goff")
            identity(f"{tag}{n} vs the same genes with goff off", g, off, runs[n], run_many([off], nums, P.QS_CAP, types=True), nums)
    assert all(r[1] is not None for rs in runs.values() for r in rs)
    # 1. priced
    c = {n: {Pn: [cost(r[4], Pn) for r in rs] for Pn in PT} for n, rs in runs.items()}
    for n in cells:
        out["priced"][n] = {"mean": {Pn: float(np.mean(c[n][Pn])) for Pn in PT}}
        print(f"priced {tag}{n}: " + " ".join(f"{Pn} {np.mean(c[n][Pn]):,.1f}" for Pn in PT), flush=True)
    for a, b in pbases:
        pr = {Pn: paired(c[a][Pn], c[b][Pn]) for Pn in PT}
        info = "" if b == "2'a" else " (information)"
        out["priced"][f"{a} vs {b}"] = {Pn: {"ratio": v[0], "ci95": v[1]} for Pn, v in pr.items()}
        print(f"priced {tag}{a} vs {b}{info}: " + " ".join(f"{Pn} {v[0]:.4f} [{v[1][0]:.4f}, {v[1][1]:.4f}]" for Pn, v in pr.items())
              + f"; robust {max(v[0] for v in pr.values()):.4f}; (e) "
              + ("better" if all(v[1][1] < 1 for v in pr.values()) else "worse" if all(v[1][0] > 1 for v in pr.values()) else "undecided"), flush=True)
    # 2. wall-clock
    res, order, states, clock = shuffled(cells, nums, reps=REPS, seed=seed)
    def series(n, part):
        if part == "wall":
            return [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in res[n]]
        return [w[part]["ns"] / 1e3 for w in res[n]]
    for n in cells:
        rec = {"mhz": clock[n]}
        line = f"timing {tag}{n}:"
        for part in ("wall",) + tuple(k for k in REGIONS if k in res[n][0]):
            x = series(n, part)
            rec[part] = {"mean": statistics.mean(x), "sd": statistics.stdev(x), "min": min(x), "max": max(x), "per_replicate": x}
            if part != "wall":   # the region's priced counts (ruint) and calls, deterministic
                rec[part]["ruint"] = float(res[n][0][part]["priced"])
                rec[part]["calls"] = float(res[n][0][part]["calls"])
            line += (f" {part} {rec[part]['mean']:,.1f} us (sd {rec[part]['sd']:.1f}, {rec[part]['min']:,.1f}-{rec[part]['max']:,.1f})"
                     + (f" ruint {rec[part]['ruint']:,.1f}" if part != "wall" else "") + ";")
        m = clock[n]
        line += (f" core 2 MHz {m['min']:.0f}-{m['max']:.0f}, median {m['median']:.0f} (n {m['n']})" + (" FLAGGED (>10% off 2'a)" if m["flag"] else "")
                 if m["n"] else " core 2 MHz: no samples")
        out["timing"][n] = rec
        print(line, flush=True)
    for a, b in tbases:
        info = "" if b == "2'a" else " (information)"
        line = f"timing {tag}{a} vs {b}{info}:"
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
    # 3. region excess over own-rate price
    T = out["timing"]
    for a, b in xbases:
        line = f"excess {tag}{a} vs {b} (wall above own-rate price, us per number [95%]):"
        rec = {}
        for k in EXCESS:
            if k not in T[b] or not T[b][k]["mean"]:
                continue
            key = "calls" if k == "scan" else "ruint"
            if not T[b][k][key]:
                continue
            pr = T[a][k][key] / T[b][k][key]
            ex = [(x / y - pr) * T[b][k]["mean"] for x, y in zip(T[a][k]["per_replicate"], T[b][k]["per_replicate"])]
            m, h = statistics.mean(ex), T7 * statistics.stdev(ex) / math.sqrt(len(ex))
            rec[k] = {"price_ratio": pr, "basis": key, "excess_us": m, "ci95": [m - h, m + h]}
            line += f" {k} {m:+.1f} [{m - h:+.1f}, {m + h:+.1f}]" + (" (calls)" if key == "calls" else "") + ";"
        out["excess"][f"{a} vs {b}"] = rec
        print(line, flush=True)
    # 4. LPBREAK
    out["lpbreak"] = {}
    for n, g in cells.items():
        lp = phasetime(g, nums, True)
        out["lpbreak"][n] = {k: v for k, v in lp.items() if k.startswith("lp:") or k == "lp_ledger"}
        print(f"lp break {tag}{n} (information; sub-timers on): " + " ".join(f"{k} {v['ns'] / 1e3:,.1f} us / {v['calls']:,.1f} calls" for k, v in out["lpbreak"][n].items()), flush=True)
    print(f"replicate orders {tag}(random.Random({seed})):")
    for r in range(1, REPS + 1):
        print(f"  r{r}: " + ", ".join(n for rr, n in order if rr == r))
    for i, s in enumerate(states):
        print(f"## {tag}machine state before replicate {i + 1}\n{s}", end="")
    out.update(order=order, states=states, seed=seed)
    return out

def shift_cells(bits, ds, lb, with_2b):
    g0 = dict(ref(bits), goff=1)
    cells = {"2'a": g0}
    if with_2b:
        cells["2'b"] = dict(g0, confirm="root")
    for d in ds:
        cells[f"2'b+pp3 +{d}"] = dict(g0, confirm="root", pp=3, tc=g0["tc"] - d / lb)
    return cells

if MODE == "A":
    cells = shift_cells(96, (1, 2, 3), math.log2(1752.0), True)
    pp = [n for n in cells if "pp3" in n]
    out = size_run(96, cells, [(n, "2'a") for n in cells if n != "2'a"] + [(n, "2'b") for n in pp],
                   [(n, "2'a") for n in cells if n != "2'a"] + [(n, "2'b") for n in pp],
                   [(n, "2'b") for n in pp] + [(n, "2'a") for n in pp], 2029, "")
    json.dump(out, open("shiftrun_A.json", "w"), indent=1)
elif MODE == "B":
    out = {}
    for bits in (72, 84):
        B = statistics.mean(bnd(N, ref(bits)) for N, _, _ in S2.map_nums(bits))
        print(f"{bits} bits: mean B over the map numbers {B:.1f}; shift d bits = tc - d / {math.log2(B):.4f}", flush=True)
        cells = shift_cells(bits, (0, 1, 2), math.log2(B), False)
        base = [(n, "2'a") for n in cells if n != "2'a"]
        out[str(bits)] = size_run(bits, cells, base, base, base, 2030 + bits, f"{bits}: ")
        out[str(bits)]["mean_B"] = B
    json.dump(out, open("shiftrun_B.json", "w"), indent=1)
else:
    sys.exit("usage: shiftrun.py A|B")
