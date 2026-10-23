"""Scaled validation through the Rust lamp core: baselines and every run's champion on
fresh balanced semiprimes at 54-78 bits, cumulative totals and worst cases.

  python3 scale.py [count] [workers] [out]

Writes scale.json (or out). Trial division and Fermat are left out: at these sizes they
need 2^30+ operations per number and only measure the cap.

Coverage rule (Stage 1): a run champion whose stages stop short of sqrt(N) is scored with
its deck's fallback tail (lamps.with_fallback), flagged in the output.
"""
import json, math, sys
from multiprocessing import Pool
from fastlamps import semiprimes_pq, run_many
from evolve import BASELINES
from lamps import with_fallback

COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 40
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
OUT = sys.argv[3] if len(sys.argv) > 3 else "scale.json"
SIZES = [54, 60, 66, 72, 78]
CAP = 2 ** 29

def candidates():
    gs = {k: v for k, v in BASELINES.items() if k not in ("trial division", "fermat")}
    for d, label in (("", "run 2"), ("run3/", "run 3"), ("run4/", "run 4")):
        res = json.load(open(d + "results.json"))
        for key, hist in res["runs"].items():
            gs[f"{label} {key}"] = hist[-1]["champ"]
    return gs

FALLBACK = {}
def with_tails(gs):
    out = {}
    for name, g in gs.items():
        if name in BASELINES:
            out[name] = g
        else:
            out[name], FALLBACK[name] = with_fallback(g, luck=" luck-" in name)
    return out

def job(args):
    name, g, bits = args
    nums = semiprimes_pq(bits, COUNT, 880000 + bits)
    r = run_many(g, nums, CAP)
    ops = [x[0] for x in r if x[0] is not None]
    misses = len(r) - len(ops)
    if not ops:
        return name, bits, None
    ops.sort()
    return name, bits, {
        "mean_log2": math.log2(sum(ops) / len(ops)),
        "median_log2": math.log2(ops[len(ops) // 2]),
        "worst_log2": math.log2(ops[-1]),
        "misses": misses,
        "hit_rate_log2": (math.log2(sum(x[3] for x in r) / sum(x[2] for x in r))
                          if sum(x[3] for x in r) else None),
    }

if __name__ == "__main__":
    gs = with_tails(candidates())
    jobs = [(n, g, b) for n, g in gs.items() for b in SIZES]
    out = {"sizes": SIZES, "count": COUNT, "cap_log2": 29, "results": {}}
    with Pool(WORKERS) as pool:
        for name, bits, r in pool.imap_unordered(job, jobs):
            out["results"].setdefault(name, {})[str(bits)] = r
            print(name, bits, None if r is None else
                  f"mean 2^{r['mean_log2']:.2f} worst 2^{r['worst_log2']:.2f} misses {r['misses']}",
                  flush=True)
    for name, by in out["results"].items():
        pts = [(b, by[str(b)]["mean_log2"]) for b in SIZES if by.get(str(b)) and not by[str(b)]["misses"]]
        if len(pts) >= 2:
            xs, ys = zip(*pts)
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            by["trend"] = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x in xs)
        if name in FALLBACK:
            by["fallback"] = FALLBACK[name]
    json.dump(out, open(OUT, "w"), indent=1)
    print("done")
