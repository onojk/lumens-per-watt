"""Cumulative lumens vs cumulative watts, by planting secrets.

A station s goes dark once the algorithm would have caught p if p = s. We measure that
directly: run each algorithm on many balanced semiprimes whose p values are spread across
the stations, and record the cumulative watts (ops) each one took. Sorting those gives
the curve: the fraction of possible secrets darkened as watts accumulate.

  python3 curves.py [run3] [bits] [count] [workers]

Writes curves.json (or run3/curves.json): per algorithm, the sorted darkening watts and
the cumulative totals.
"""
import json, math, sys
from multiprocessing import Pool
from lamps import run, semiprimes, describe
from evolve import BASELINES

RUN = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].isdigit() else ""
nums = [a for a in sys.argv[1:] if a.isdigit()]
BITS = int(nums[0]) if len(nums) > 0 else 40
COUNT = int(nums[1]) if len(nums) > 1 else 120
WORKERS = int(nums[2]) if len(nums) > 2 else 2
DIR = RUN + "/" if RUN else ""

def job(args):
    gen, N = args
    ops, d = run(gen, N, 10 ** 15)
    return ops

def curve(gen, Ns, pool):
    ops = sorted(pool.map(job, [(gen, N) for N in Ns]))
    total = sum(ops)
    stations = 2 ** (BITS / 2)                 # candidates for p, about sqrt(N)
    return {
        "darkening_watts": ops,
        "cumulative_watts": total,
        "cumulative_lumens": stations * len(ops),
        "lumens_per_watt_log2": math.log2(stations * len(ops) / total),
        "median_log2": math.log2(ops[len(ops) // 2]),
        "mean_log2": math.log2(total / len(ops)),
        "worst_log2": math.log2(ops[-1]),
    }

if __name__ == "__main__":
    Ns = semiprimes(BITS, COUNT, 515000 + BITS)
    cands = dict(BASELINES)
    try:
        res = json.load(open(DIR + "results.json"))
        for key, hist in res["runs"].items():
            cands[f"champion {key}"] = hist[-1]["champ"]
    except FileNotFoundError:
        pass
    out = {"bits": BITS, "count": COUNT, "curves": {}}
    with Pool(WORKERS) as pool:
        for name, g in cands.items():
            c = curve(g, Ns, pool)
            c["genome"] = g
            out["curves"][name] = c
            print(f"{name:22s} mean 2^{c['mean_log2']:.1f}  median 2^{c['median_log2']:.1f}  "
                  f"worst 2^{c['worst_log2']:.1f}  lumens/watt 2^{c['lumens_per_watt_log2']:.1f}",
                  flush=True)
    json.dump(out, open(DIR + "curves.json", "w"), indent=1)
