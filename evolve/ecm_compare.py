"""Stage 8 comparison (NOTES.md, "Stage 8: elliptic-curve card"; PLAN.md, Stage 8).

ECM with the frozen genes (b1 1.0, b2 50: ecm_tune.py) against our best qs (tuned qs + lc 1.4:
kc 32, bc 1.1, mc 0.25, tc 1.38, lc 1.4) and rho, cap 2^28, on two populations:
- balanced: the Stage 2 numbers at 54, 60, 66, 72, 78 bits (semiprimes_pq(bits, 80,
  990000 + bits)) and semiprimes_pq(84, 80, 1300084) (the Run 6 ACCEPT numbers at 72-84);
- unbalanced: semiprimes_unbalanced(bits, pbits, 80, 2900000 + 100 pbits + bits) for bits in
  {72, 78, 84} x pbits in {24, 28, 32}.
Per cell: log2(mean ops) and the worst case with the index-250/9749 bootstrap, misses, mean
ops per phase, ECM's mean curves per number; growth per bit (balanced 54->84 and 72->84;
unbalanced: per bit of p at fixed N, per bit of N at fixed p); the paired log2 ratio ECM / qs
(supplementary). Ops and phases come from lampcore; curves (ECM) and the small-number split
(qs) from lamps.py's traces, and the two cores must agree on every number's ops.

Pricing sensitivity (NOTES.md, "Pricing sensitivity", stated before running): qs re-priced
with its small-number ops at r = 1/8 and 1/32; ECM and rho unchanged. Reported beside the
official numbers, never in place of them.

  python3 ecm_compare.py [workers]  -> ecm_compare.json
"""
import json, math, random, sys
from multiprocessing import Pool
import qs, ecm
from lamps import run
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many, PHASES
from revalidate import bootstrap, R
from run6_accept import bootstrap_worst
from evolve import BASELINES

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
CAP = 2 ** 28
ECM = [{"t": "ecm", "b1": 1.0, "b2": 50}]
QS = [{"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}]
RHO = BASELINES["rho"]
ALGS = {"ecm": ECM, "qs + lc 1.4": QS, "rho": RHO}
BAL = [54, 60, 66, 72, 78, 84]
UNB = [(b, pb) for b in (72, 78, 84) for pb in (24, 28, 32)]
RATES = (1 / 8, 1 / 32)

def balanced(b):
    return semiprimes_pq(b, 80, 1300084 if b == 84 else 990000 + b)

def unbalanced(b, pb):
    return semiprimes_unbalanced(b, pb, 80, 2900000 + 100 * pb + b)

def qs_split(tr):
    """(full-price ops, small-number ops) of one qs run, from its trace (NOTES.md, pricing)."""
    ops = tr["ops"]
    ats = tr["attempts"]
    setup_full = sum((at["s"] - 1) * at["combos"] + 2 * at["s"] * at["a_count"] for at in ats)
    confirm_full = sum(2 * len(at["cands"]) for at in ats)
    lp_full = sum(at["lp"]["combos"] for at in ats if "lp" in at)
    full = ops.get("mult", 0) + ops.get("sqrt", 0) + setup_full + confirm_full + lp_full
    small = sum(ops.values()) - full
    return full, small

def py_job(args):
    alg, key, N = args
    if alg == "ecm":
        ecm.TRACE = {}
        ops, d = run(ECM, N, CAP)
        return alg, key, N, ops, len(ecm.TRACE["curves"]), None
    qs.TRACE = {}
    ops, d = run(QS, N, CAP)
    return alg, key, N, ops, None, qs_split(qs.TRACE)

def cell(all_ops):
    ops = [o for o in all_ops if o is not None]
    capped = [CAP if o is None else o for o in all_ops]
    return {"mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
            "ci95": list(bootstrap(ops)) if ops else None,
            "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
            "misses": len(all_ops) - len(ops)}

def paired(a, b):
    rng = random.Random(2026)
    n = len(a)
    vals = sorted(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx))
                  for idx in ([rng.randrange(n) for _ in range(n)] for _ in range(R)))
    return math.log2(sum(a) / sum(b)), [vals[int(0.025 * R)], vals[int(0.975 * R) - 1]]

def slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

if __name__ == "__main__":
    pops = {str(b): balanced(b) for b in BAL}
    pops.update({f"{b}/{pb}": unbalanced(b, pb) for b, pb in UNB})
    with Pool(WORKERS) as pool:
        py = pool.map(py_job, [(a, k, N) for a in ("ecm", "qs + lc 1.4") for k, nums in pops.items()
                               for N, p, q in nums], chunksize=2)
    pyd = {(a, k, N): (o, c, s) for a, k, N, o, c, s in py}
    out = {"cap_log2": 28, "genomes": ALGS, "results": {}, "paired_ecm_over_qs": {}, "repriced_qs": {}}
    capped = {}
    for alg, g in ALGS.items():
        out["results"][alg] = {}
        for k, nums in pops.items():
            r = run_many(g, nums, CAP, phases=alg != "rho")
            ops = [x[0] for x in r]
            if alg != "rho":
                for (N, p, q), o in zip(nums, ops):
                    assert pyd[alg, k, N][0] == o, ("cores disagree", alg, k, N)
            c = cell(ops)
            if alg != "rho":
                c["phase_mean"] = {ph: sum(x[4][ph] for x in r) / len(r) for ph in PHASES if any(x[4][ph] for x in r)}
            if alg == "ecm":
                c["curves_mean"] = sum(pyd[alg, k, N][1] for N, p, q in nums) / len(nums)
            out["results"][alg][k] = c
            capped[alg, k] = [CAP if o is None else o for o in ops]
    for k in pops:
        out["paired_ecm_over_qs"][k] = paired(capped["ecm", k], capped["qs + lc 1.4", k])
        out["repriced_qs"][k] = {}
        for rate in RATES:
            vals = []
            for N, p, q in pops[k]:
                o, _, (full, small) = pyd["qs + lc 1.4", k, N]
                vals.append(full + rate * small if o is not None else None)
            c = cell(vals)
            c["ecm_leads"] = out["results"]["ecm"][k]["ci95"][1] < c["ci95"][0]
            c["qs_leads"] = c["ci95"][1] < out["results"]["ecm"][k]["ci95"][0]
            out["repriced_qs"][k][f"1/{round(1 / rate)}"] = c
    growth = {}
    for alg in ALGS:
        ys = [out["results"][alg][str(b)]["mean_log2"] for b in BAL]
        growth[alg] = {"balanced 54-84": slope(BAL, ys), "balanced 72-84": slope(BAL[3:], ys[3:])}
        for b in (72, 78, 84):
            growth[alg][f"per p bit at {b}"] = slope([24, 28, 32], [out["results"][alg][f"{b}/{pb}"]["mean_log2"] for pb in (24, 28, 32)])
        for pb in (24, 28, 32):
            growth[alg][f"per N bit at p{pb}"] = slope([72, 78, 84], [out["results"][alg][f"{b}/{pb}"]["mean_log2"] for b in (72, 78, 84)])
    out["growth"] = growth
    for k in pops:
        print(f"\n{k}:")
        for alg in ALGS:
            c = out["results"][alg][k]
            extra = f"  curves {c['curves_mean']:.1f}" if "curves_mean" in c else ""
            print(f"  {alg:12s} mean {c['mean_log2']:.2f} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]  worst "
                  f"{c['worst_log2']:.2f} [{c['worst_ci95'][0]:.2f}, {c['worst_ci95'][1]:.2f}]  misses {c['misses']}{extra}")
        v, ci = out["paired_ecm_over_qs"][k]
        print(f"  paired ecm/qs: {v:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}] ({2 ** -v:.2f}x {'fewer' if v < 0 else 'more'} ops for ecm)")
        for rk, c in out["repriced_qs"][k].items():
            print(f"  qs re-priced at {rk}: mean {c['mean_log2']:.2f} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]  "
                  f"ecm leads: {c['ecm_leads']}, qs leads: {c['qs_leads']}")
    print("\ngrowth (log2-ops per bit):")
    for alg, gr in growth.items():
        print(f"  {alg:12s} " + "  ".join(f"{k} {v:.3f}" for k, v in gr.items()))
    json.dump(out, open("ecm_compare.json", "w"), indent=1)
