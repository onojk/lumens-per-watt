"""Stage 7 comparison: tuned qs with the pre-registered lc = 1.4 against tuned qs (lc = 1.0).

Genes: kc 32, bc 1.1, mc 0.25, tc 1.38 for both (qs_boundary_sweep.py's best cell); lc 1.4
was fixed on the tuning seeds (stage7_lc_sweep.py) before this ran.
Numbers: the Run 6 ACCEPT sets (run6_accept.SETS): the Stage 2 numbers at 72 and 78 bits and
semiprimes_pq(84, 80, 1300084). Cap 2^28. Ops and the per-phase breakdown come from lampcore;
the large-prime counts (partials, combinations, pairing yield) from lamps.py's trace, and the
two cores must agree on every number's ops.

Per size: log2(mean ops) and the worst case, each with run6_accept.py's 95% bootstrap
(index 250/9749; the worst-case interval's upper end is the observed worst by construction),
retries, mean ops per phase, pairing yield; growth per bit from 72 to 84 (least squares on
log2 mean). Verdict (NOTES, Stage 7): a win only where lc 1.4's interval sits below lc 1.0's.
Supplementary: the paired log2 ratio of total ops on the same numbers, bootstrapped over
numbers (fresh random.Random(2026) per size, same indices) -- not the verdict rule.

  python3 stage7_compare.py [workers]  -> stage7_compare.json
"""
import json, math, random, sys
from multiprocessing import Pool
import qs
from lamps import run
from fastlamps import semiprimes_pq, run_many, PHASES
from revalidate import bootstrap, R
from run6_accept import bootstrap_worst, SETS, CAP

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
TUNED = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}
GENOMES = {"lc 1.0 (tuned qs)": [dict(TUNED)], "lc 1.4": [dict(TUNED, lc=1.4)]}

def py_job(args):
    name, bits, N = args
    qs.TRACE = {}
    ops, d = run(GENOMES[name], N, CAP)
    ats = qs.TRACE["attempts"]
    lp = {k: sum(at["lp"][k] for at in ats) for k in ("cof", "lt", "inserts", "combos", "dup")}
    return name, bits, N, ops, lp, len(ats), sum(at["rows"] for at in ats)

def paired(a, b):
    """log2(sum a / sum b) with a percentile bootstrap over numbers."""
    rng = random.Random(2026)
    n = len(a)
    vals = []
    for _ in range(R):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx)))
    vals.sort()
    return math.log2(sum(a) / sum(b)), [vals[int(0.025 * R)], vals[int(0.975 * R) - 1]]

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, c, s) for b, (c, s) in SETS.items()}
    with Pool(WORKERS) as pool:
        py = pool.map(py_job, [(name, b, N) for name in GENOMES for b in nums for N, p, q in nums[b]],
                      chunksize=4)
    out = {"cap_log2": 28, "sets": {str(b): {"count": c, "seed": s} for b, (c, s) in SETS.items()},
           "genomes": GENOMES, "results": {}, "paired_log2_ratio": {}}
    ops_by = {}
    for name, g in GENOMES.items():
        out["results"][name] = {}
        for b in nums:
            rust = run_many(g, nums[b], CAP, phases=True)
            pyr = [x for x in py if x[0] == name and x[1] == b]
            for (N, p, q), r, x in zip(nums[b], rust, pyr):
                assert x[2] == N and x[3] == r[0], ("cores disagree", name, b, N, x[3], r[0])
            all_ops = [r[0] for r in rust]
            ops = [o for o in all_ops if o is not None]
            capped = [CAP if o is None else o for o in all_ops]
            ops_by[name, b] = capped
            lp = {k: sum(x[4][k] for x in pyr) for k in pyr[0][4]}
            out["results"][name][str(b)] = {
                "mean_log2": math.log2(sum(ops) / len(ops)), "ci95": list(bootstrap(ops)),
                "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
                "misses": len(all_ops) - len(ops),
                "retries": sum(x[5] - 1 for x in pyr),
                "phase_mean": {ph: sum(r[4][ph] for r in rust) / len(rust) for ph in PHASES},
                "lp": lp, "pairing_yield": lp["combos"] / lp["lt"] if lp["lt"] else None,
                "combined_row_share": (lp["combos"] - lp["dup"]) / sum(x[6] for x in pyr)}
        xs = list(nums)
        ys = [out["results"][name][str(b)]["mean_log2"] for b in xs]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        out["results"][name]["per_bit"] = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                                           / sum((x - mx) ** 2 for x in xs))
    for b in nums:
        out["paired_log2_ratio"][str(b)] = paired(ops_by["lc 1.4", b], ops_by["lc 1.0 (tuned qs)", b])
    star = lambda c: "*" if c["misses"] else ""
    for name in GENOMES:
        print(f"\n{name}  (growth {out['results'][name]['per_bit']:.3f} log2-ops per bit, 72->84)")
        for b in nums:
            c = out["results"][name][str(b)]
            print(f"  {b} bits: mean {c['mean_log2']:.2f}{star(c)} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]"
                  f"  worst {c['worst_log2']:.2f} [{c['worst_ci95'][0]:.2f}, {c['worst_ci95'][1]:.2f}]"
                  f"  retries {c['retries']}"
                  + (f"  partials {c['lp']['lt']} yield {c['pairing_yield']:.3f}"
                     f" combined rows {c['combined_row_share']:.3f}" if c["pairing_yield"] is not None else ""))
            print("           phases (log2 mean): " + "  ".join(
                f"{ph} {math.log2(v):.2f}" for ph, v in c["phase_mean"].items() if v))
    print("\npaired log2(total ops lc 1.4 / total ops lc 1.0) [95% CI], same numbers (supplementary):")
    for b in nums:
        v, ci = out["paired_log2_ratio"][str(b)]
        print(f"  {b} bits: {v:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]  ({2 ** -v:.2f}x)")
    json.dump(out, open("stage7_compare.json", "w"), indent=1)
