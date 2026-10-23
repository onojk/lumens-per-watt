"""Run 6 ablation (a measurement, not a scored run).

Each Run 6 champion three ways, on the ACCEPT numbers (72/78 Stage 2 sets, 84-bit 1300084),
lampcore, cap 2^28, same bootstrap as run6_accept.py:
  full       the champion as evolved
  qs only    every non-qs stage removed (all qs stages kept, in order)
  first qs   only its first qs stage
Per cell: log2 mean [95% CI], worst [95% CI], misses; for the full genome, which stage won
each number; for each ablation, the paired per-number comparison with the full genome.

  python3 run6_ablation.py [workers]      -> run6_ablation.json
"""
import json, math, sys
from multiprocessing import Pool
from fastlamps import semiprimes_pq, run_many
from revalidate import bootstrap
from run6_accept import bootstrap_worst, SETS, CAP

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4

def job(args):
    champ, variant, g, bits = args
    count, seed = SETS[bits]
    r = run_many(g, semiprimes_pq(bits, count, seed), CAP, inst=True)
    all_ops = [x[0] for x in r]
    ops = [x for x in all_ops if x is not None]
    capped = [CAP if x is None else x for x in all_ops]
    return champ, variant, bits, {
        "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
        "ci95": list(bootstrap(ops)) if ops else None,
        "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
        "misses": len(all_ops) - len(ops), "ops": all_ops, "stage": [x[4] for x in r]}

if __name__ == "__main__":
    acc = json.load(open("run6/accept.json"))
    jobs = []
    for name, c in acc["champions"].items():
        g = c["genes"]
        qs = [s for s in g if s["t"] == "qs"]
        for variant, gg in (("full", g), ("qs only", qs), ("first qs", qs[:1])):
            jobs += [(name, variant, gg, b) for b in SETS]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs)
    out = {"cap_log2": 28, "results": {}}
    for champ, variant, b, cell in res:
        out["results"].setdefault(champ, {}).setdefault(variant, {})[str(b)] = cell
    # the full rows must reproduce accept.json
    for champ, by in out["results"].items():
        for b in SETS:
            a, s = by["full"][str(b)], acc["results"][champ][str(b)]
            assert all(a[k] == s[k] for k in ("mean_log2", "ci95", "worst_log2", "worst_ci95", "misses")), (champ, b)
    print("full rows reproduce run6/accept.json\n")
    for champ, by in out["results"].items():
        genes = acc["champions"][champ]["genes"]
        print(f"{champ}: " + " -> ".join(s["t"] for s in genes))
        for b in SETS:
            full = by["full"][str(b)]
            wins = {}
            for st in full["stage"]:
                key = "miss" if st is None else f"{st}:{genes[st]['t']}"
                wins[key] = wins.get(key, 0) + 1
            print(f"  {b} bits  winning stage (full): {wins}")
            for variant in ("full", "qs only", "first qs"):
                c = by[variant][str(b)]
                line = (f"    {variant:9s} {c['mean_log2']:.3f} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]"
                        f"  worst {c['worst_log2']:.2f} [{c['worst_ci95'][0]:.2f}, {c['worst_ci95'][1]:.2f}]"
                        f"  misses {c['misses']}")
                if variant != "full":
                    pairs = [(f, a) for f, a in zip(full["ops"], c["ops"]) if f is not None and a is not None]
                    cheaper = sum(a < f for f, a in pairs); dearer = sum(a > f for f, a in pairs)
                    same = sum(a == f for f, a in pairs)
                    ratio = sum(a for f, a in pairs) / sum(f for f, a in pairs)
                    line += (f"  | vs full: total ops x{ratio:.3f}, per number cheaper {cheaper} / "
                             f"same {same} / dearer {dearer}")
                print(line)
        print()
    json.dump(out, open("run6_ablation.json", "w"))
