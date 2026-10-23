"""Stage 2: statistical re-validation through the Rust lamp core.

Rho, Hart x480, and the final champion of each Run 3 and Run 4 run, on 80 fresh balanced
semiprimes per size (semiprimes_pq(bits, 80, 990000 + bits)), cap 2^29, coverage rule off.

Statistic per (algorithm, size) cell: log2(mean ops), the total-work scoreboard of every
scale table. Misses are left out of the cell's mean and interval and counted beside it.
95% interval by bootstrap over numbers: a fresh random.Random(2026) per cell, 10,000
resamples of n draws each (rng.choice over the cell's ops in number-generation order,
misses removed), percentile method with symmetric tails: sorted resampled values at index
int(0.025 * R) and int(0.975 * R) - 1, so exactly 250 resamples sit outside each end.

Verdict for each champion against rho and Hart x480 at each size: "better" if its interval
lies entirely below the other's, "worse" if entirely above, otherwise "within noise".

  python3 revalidate.py [workers]

Writes revalidation.json.
"""
import json, math, random, sys
from multiprocessing import Pool
from fastlamps import semiprimes_pq, run_many
from evolve import BASELINES

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
SIZES = [54, 60, 66, 72, 78]
COUNT = 80
CAP = 2 ** 29
R = 10000

def candidates():
    gs = {"rho": BASELINES["rho"], "hart x480": BASELINES["hart x480"]}
    for d, label in (("run3/", "run 3"), ("run4/", "run 4")):
        res = json.load(open(d + "results.json"))
        for key, hist in res["runs"].items():
            gs[f"{label} {key}"] = hist[-1]["champ"]
    return gs

def bootstrap(ops):
    rng = random.Random(2026)
    n = len(ops)
    vals = sorted(math.log2(sum(rng.choice(ops) for _ in range(n)) / n) for _ in range(R))
    return vals[int(0.025 * R)], vals[int(0.975 * R) - 1]

def job(args):
    name, g, bits = args
    nums = semiprimes_pq(bits, COUNT, 990000 + bits)
    r = run_many(g, nums, CAP, inst=True)
    ops = [x[0] for x in r if x[0] is not None]
    lo, hi = bootstrap(ops)
    return name, bits, {
        "mean_log2": math.log2(sum(ops) / len(ops)), "ci95": [lo, hi],
        "worst_log2": math.log2(max(ops)), "misses": len(r) - len(ops),
        "per_n": [{"N": str(N), "ops": x[0], "stage": x[4], "k": x[5]}
                  for (N, p, q), x in zip(nums, r)],
    }

def verdict(a, b):
    if a["ci95"][1] < b["ci95"][0]:
        return "better"
    if a["ci95"][0] > b["ci95"][1]:
        return "worse"
    return "within noise"

if __name__ == "__main__":
    gs = candidates()
    jobs = [(n, g, b) for n, g in gs.items() for b in SIZES]
    out = {"sizes": SIZES, "count": COUNT, "seed": "990000 + bits", "cap_log2": 29,
           "resamples": R, "rng": "random.Random(2026) per cell", "coverage_rule": False,
           "results": {}, "verdicts": {}}
    with Pool(WORKERS) as pool:
        for name, bits, r in pool.imap_unordered(job, jobs):
            out["results"].setdefault(name, {})[str(bits)] = r
            print(f"{name:18s} {bits}  2^{r['mean_log2']:.2f} [{r['ci95'][0]:.2f}, {r['ci95'][1]:.2f}]"
                  f"{'  misses %d' % r['misses'] if r['misses'] else ''}", flush=True)
    res = out["results"]
    for name in gs:
        if name in ("rho", "hart x480"):
            continue
        out["verdicts"][name] = {ref: {str(b): verdict(res[name][str(b)], res[ref][str(b)])
                                       for b in SIZES} for ref in ("rho", "hart x480")}
    json.dump(out, open("revalidation.json", "w"), indent=1)
    print("done")
