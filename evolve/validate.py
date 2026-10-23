"""Re-test baselines and each run's final winner on fresh, larger semiprimes."""
import json, math, sys
from lamps import run, semiprimes, describe
from evolve import BASELINES

VSIZES = [36, 42, 48, 54]
TESTS = {b: semiprimes(b, 12, 777000 + b) for b in VSIZES}

def measure(gen):
    worst, fails = [], 0
    for b, Ns in TESTS.items():
        w = 0
        for N in Ns:
            ops, d = run(gen, N, int(4 * 2 ** (0.45 * b)))
            if ops is None:
                fails += 1
                ops = int(4 * 2 ** (0.45 * b))
            else:
                assert N % d == 0 and 1 < d < N
            w = max(w, ops)
        worst.append(math.log2(w))
    xs = VSIZES; mx = sum(xs) / len(xs); my = sum(worst) / len(worst)
    e = sum((x - mx) * (y - my) for x, y in zip(xs, worst)) / sum((x - mx) ** 2 for x in xs)
    return e, worst, fails

if __name__ == "__main__":
    res = json.load(open("results.json"))
    cands = dict(BASELINES)
    for key, hist in res["runs"].items():
        cands[f"evolved {key}"] = hist[-1]["genome"]
    out = {}
    for name, g in cands.items():
        e, worst, fails = measure(g)
        out[name] = {"e": e, "eff": 0.5 - e, "worst_log2": worst, "fails": fails, "genome": g}
        print(f"{name:20s} work N^{e:.3f}  lumens/watt N^{0.5-e:.3f}  fails {fails:2d}  "
              f"worst log2 ops {[round(w,1) for w in worst]}", flush=True)
        if name.startswith("evolved"):
            print(f"{'':20s} {describe(g)}", flush=True)
    json.dump(out, open("validation.json", "w"), indent=1)
