"""qs vs rho on the Stage 2 numbers: a measurement, not a scored run.

qs alone (the acceptance genome), rho, Run 5's champion L44-0272, and Hart x480 on
semiprimes_pq(bits, 80, 990000 + bits) at 54-78 bits, cap 2^29, coverage rule off.
Statistic and bootstrap are revalidate.py's: log2(mean ops) with a 95% percentile interval
(random.Random(2026) per cell, 10,000 resamples, tails at index 250 and 9749).

qs runs in Python (no Rust port yet); the others run through lampcore, as in Stage 2.
Rho and Hart x480 must reproduce their Stage 2 rows exactly, or this stops.

  python3 qs_stage2.py [workers]

Writes qs_stage2.json.
"""
import json, math, sys
from multiprocessing import Pool
from lamps import run
from fastlamps import semiprimes_pq, run_many
from evolve import BASELINES
from revalidate import bootstrap, SIZES, COUNT, CAP

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
QS = [{"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}]

def l44_0272():
    hist = json.load(open("run5/results.json"))["runs"]["luck-44"]
    assert hist[-1]["champ_name"] == "L44-0272"
    return hist[-1]["champ"]

def qs_job(args):
    bits, N = args
    return bits, run(QS, N, CAP)[0]

def cell(ops_all):
    ops = [x for x in ops_all if x is not None]
    lo, hi = bootstrap(ops)
    return {"mean_log2": math.log2(sum(ops) / len(ops)), "ci95": [lo, hi],
            "worst_log2": math.log2(max(ops)), "misses": len(ops_all) - len(ops)}

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, COUNT, 990000 + b) for b in SIZES}
    out = {"sizes": SIZES, "count": COUNT, "seed": "990000 + bits", "cap_log2": 29,
           "genomes": {"qs": QS, "rho": BASELINES["rho"], "L44-0272": l44_0272(),
                       "hart x480": BASELINES["hart x480"]}, "results": {}}
    with Pool(WORKERS) as pool:
        qres = pool.map(qs_job, [(b, N) for b in SIZES for N, p, q in nums[b]])
    out["results"]["qs"] = {str(b): cell([o for bb, o in qres if bb == b]) for b in SIZES}
    for name in ("rho", "L44-0272", "hart x480"):
        g = out["genomes"][name]
        out["results"][name] = {str(b): cell([x[0] for x in run_many(g, nums[b], CAP)])
                                for b in SIZES}
    stage2 = json.load(open("revalidation.json"))["results"]
    for name in ("rho", "hart x480"):
        for b in SIZES:
            a, r = out["results"][name][str(b)], stage2[name][str(b)]
            same = all(a[k] == r[k] for k in ("mean_log2", "ci95", "worst_log2", "misses"))
            if not same:
                sys.exit(f"STOP: {name} at {b} bits does not reproduce Stage 2: {a} vs {r}")
    print("rho and Hart x480 reproduce their Stage 2 rows exactly")
    for name, by in out["results"].items():
        print(f"{name:10s}", "  ".join(
            f"{by[str(b)]['mean_log2']:.2f}{'*' if by[str(b)]['misses'] else ''} "
            f"[{by[str(b)]['ci95'][0]:.2f}, {by[str(b)]['ci95'][1]:.2f}] w{by[str(b)]['worst_log2']:.2f}"
            for b in SIZES))
    for name, by in out["results"].items():
        xs = [b for b in SIZES if not by[str(b)]["misses"]]
        ys = [by[str(b)]["mean_log2"] for b in xs]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        by["per_bit"] = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        print(f"{name:10s} growth {by['per_bit']:.3f} log2-ops per bit")
    json.dump(out, open("qs_stage2.json", "w"), indent=1)
