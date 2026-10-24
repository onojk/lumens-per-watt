"""Calibrated re-score (NOTES.md, "Op-price calibration on this laptop"): measurement only.

Prices come from lampcore's opbench (lampcore/src/bin/opbench.rs) as ratios to one 84-bit
modular multiply, under two references: ruint's U256::mul_mod and a two-limb Montgomery
multiply (each timed as a dependent chain). Neither is "the" price: the ratios depend on
implementation quality, so both are reported.

Algorithms: ECM (b1 1.0, b2 50), tuned qs + lc 1.4, rho, N51-0917, on the Stage 8 populations
(ecm_compare.py: balanced 54-84, unbalanced 72/78/84 x 24/28/32), cap 2^28. Per number, the
counts each price applies to (NOTES.md, the phase mapping) come from lampcore and lamps.py's
traces, exactly:
  rho:  multiplies = ops - gcds, gcds = luck-meter tests
  ecm:  setup multiplies, setup Euclid steps (recomputed from each curve's sigma), s1 + s2
        multiplies, gcds
  qs:   mult, fb (small mulmod); setup full (1), setup Euclid steps (small), other setup
        (small mulmod); sieve updates and scans; confirm full (1) and trial divisions; la (xor);
        sqrt multiplies (1) and gcd steps (U256 Euclid step); lp full (1) and the rest
        (trial-division price)
A gcd mod N for rho and ECM is priced at one measured U256::gcd call. The official model
charges it 1 op: the model finding, reported, not corrected anywhere official.

  python3 calibrate.py counts [workers]           -> calibrate_counts.json (slow: traces)
  python3 calibrate.py price P1 P2 P3 E1          -> calibrate.json (opbench outputs)
  python3 calibrate.py extra P1 P2 P3 E1          (prints only) leaders under each single
        run's prices, the gcd share of rho and ECM, and the break-even multiplier on qs's
        small-number prices at which qs and ECM are level
"""
import json, math, random, sys
ARGS, sys.argv[1:] = sys.argv[1:], []  # revalidate and ecm_compare read sys.argv on import
from multiprocessing import Pool
import qs, ecm
from lamps import run
from fastlamps import run_many
from revalidate import bootstrap, R
from ecm_compare import BAL, UNB, balanced, unbalanced, ECM, QS, RHO, CAP
from optypes import qs_counts, ecm_counts

N51 = json.load(open("run6/accept.json"))["genomes"]["N51-0917"]
ALGS = {"ecm": ECM, "qs + lc 1.4": QS, "rho": RHO, "N51-0917": N51}

def pops():
    p = {str(b): balanced(b) for b in BAL}
    p.update({f"{b}/{pb}": unbalanced(b, pb) for b, pb in UNB})
    return p

def count_job(args):
    alg, key, N = args
    if alg == "ecm":
        ecm.TRACE = {}
        ops, d = run(ECM, N, CAP)
        return alg, key, N, ops, ecm_counts(ecm.TRACE, N)
    qs.TRACE = {}
    ops, d = run(ALGS[alg], N, CAP)
    c = qs_counts(qs.TRACE)
    assert ops is None or sum(c.values()) == ops, ("split does not add up", alg, N)
    return alg, key, N, ops, c

def gather(workers):
    P = pops()
    jobs = [(a, k, N) for a in ("ecm", "qs + lc 1.4", "N51-0917") for k, nums in P.items() for N, p, q in nums]
    with Pool(workers) as pool:
        res = pool.map(count_job, jobs, chunksize=2)
    out = {a: {k: [] for k in P} for a in ALGS}
    for a, k, N, ops, c in res:
        out[a][k].append({"N": str(N), "ops": ops, "counts": c})
    for k, nums in P.items():                        # rho: lampcore (ops, tests = gcds)
        for (N, p, q), r in zip(nums, run_many(RHO, nums, CAP)):
            out["rho"][k].append({"N": str(N), "ops": r[0], "counts": {"mul": (r[0] or CAP) - r[2], "gcd": r[2]}})
        for a in ("ecm", "qs + lc 1.4", "N51-0917"):  # the cores agree on ops
            rust = run_many(ALGS[a], nums, CAP)
            assert [x["ops"] for x in out[a][k]] == [x[0] for x in rust], ("cores disagree", a, k)
    json.dump(out, open("calibrate_counts.json", "w"))

def load_bench(path):
    b = {}
    for line in open(path):
        d = json.loads(line)
        if "ns_median" in d:
            b[(d["name"], d.get("bits"))] = d["ns_median"]
    return b

def prices(b, ref):
    """Price of each count type, as a ratio to the reference 84-bit multiply."""
    t = b[(f"mulmod {ref} chain", 84)]
    r = lambda name, bits=None: b[(name, bits)] / t
    sm, td = r("small mulmod u64 chain"), r("trial division i128 ~2^50 by p")
    return {"mul": 1.0, "gcd": r("gcd U256::gcd per call", 84),
            "setup_mul": 1.0, "setup_euclid_N": r("ext euclid i128 per step", 84),
            "mult": sm, "fb": sm, "setup_full": 1.0, "setup_euclid": r("ext euclid small per step"),
            "setup_small": sm, "sieve_update": r("sieve update"), "sieve_scan": r("cell scan"),
            "confirm_full": 1.0, "confirm_td": td, "la": r("xor word"), "sqrt_mul": 1.0,
            "sqrt_gcd": r("gcd U256 Euclid per step", 84), "lp_full": 1.0, "lp_small": td}

def cell(vals):
    return {"mean_log2": math.log2(sum(vals) / len(vals)), "ci95": list(bootstrap(vals))}

def leader(cells):
    """(leader, tied-with list): the lowest mean; ties are algorithms whose interval overlaps it."""
    best = min(cells, key=lambda a: cells[a]["mean_log2"])
    ties = [a for a in cells if a != best and cells[a]["ci95"][0] <= cells[best]["ci95"][1]]
    return best, ties

def price_all(counts, pr):
    out = {}
    for a, by in counts.items():
        out[a] = {}
        for k, rows in by.items():
            vals = [sum(pr[t] * n for t, n in x["counts"].items()) for x in rows if x["ops"] is not None]
            out[a][k] = cell(vals)
    return out

def qs_mean_scaled(rows, pr, kf):
    """log2 mean cost with every price other than a full multiply (1.0) scaled by kf."""
    v = [sum((pr[t] if pr[t] == 1.0 else kf * pr[t]) * n for t, n in x["counts"].items())
         for x in rows if x["ops"] is not None]
    return math.log2(sum(v) / len(v))

def extra(runs, counts):
    keys = list(counts["ecm"])
    for a in ("ecm", "rho"):
        for k in keys:
            rows = [x for x in counts[a][k] if x["ops"] is not None]
            g = sum(x["counts"]["gcd"] for x in rows) / len(rows)
            tot = sum(x["ops"] for x in rows) / len(rows)
            print(f"{a} {k}: gcds/number {g:.1f}  ops/number {tot:.0f}  gcd share {100 * g / tot:.3f}%")
    fmt = lambda l: l[0] + (f" (tie {', '.join(l[1])})" if l[1] else "")
    for ref in ("ruint", "montgomery"):
        for r, b in runs.items():
            sc = price_all(counts, prices(b, ref))
            print(f"\nleaders, {ref} {r}: " + "; ".join(f"{k} {fmt(leader({a: sc[a][k] for a in ALGS}))}" for k in keys))
    for ref in ("ruint", "montgomery"):
        names = list(prices(runs["P1"], ref))
        pr = {t: sorted(prices(runs[r], ref)[t] for r in ("P1", "P2", "P3"))[1] for t in names}
        ecm_mean = price_all({"ecm": counts["ecm"]}, pr)["ecm"]
        print(f"\nbreak-even multiplier on small-number prices, {ref} (above 1: qs leads ECM with that margin; "
              f"'none': qs's full-multiply part alone exceeds ECM):")
        for k in keys:
            row = []
            for alg in ("qs + lc 1.4", "N51-0917"):
                e = ecm_mean[k]["mean_log2"]
                if qs_mean_scaled(counts[alg][k], pr, 0.0) >= e:
                    row.append(f"{alg} none")
                    continue
                lo, hi = 1e-3, 1e3
                for _ in range(60):
                    m = math.sqrt(lo * hi)
                    lo, hi = (m, hi) if qs_mean_scaled(counts[alg][k], pr, m) < e else (lo, m)
                row.append(f"{alg} x{m:.2f}")
            print(f"  {k:6s} " + "  ".join(row))

if __name__ == "__main__":
    if ARGS[0] == "counts":
        gather(int(ARGS[1]) if len(ARGS) > 1 else 8)
        sys.exit(0)
    if ARGS[0] == "extra":
        extra(dict(zip(("P1", "P2", "P3", "E1"), (load_bench(p) for p in ARGS[1:5]))),
              json.load(open("calibrate_counts.json")))
        sys.exit(0)
    runs = dict(zip(("P1", "P2", "P3", "E1"), (load_bench(p) for p in ARGS[1:5])))
    counts = json.load(open("calibrate_counts.json"))
    keys = list(counts["ecm"])
    official = {a: {k: cell([x["ops"] for x in rows if x["ops"] is not None]) for k, rows in by.items()}
                for a, by in counts.items()}
    out = {"prices": {}, "scores": {}, "leaders": {}, "official": official}
    for ref in ("ruint", "montgomery"):
        for run_id, b in runs.items():
            out["prices"][f"{ref} {run_id}"] = prices(b, ref)
    print("price spread (ratio to the reference 84-bit multiply; runs P1 P2 P3 on cpu 2, E1 on cpu 5):")
    names = list(out["prices"]["ruint P1"])
    for t in names:
        print(f"  {t:15s} " + "  ".join(f"{ref[:4]} " + " ".join(f"{out['prices'][f'{ref} {r}'][t]:.4f}" for r in runs)
                                         for ref in ("ruint", "montgomery")))
    for ref in ("ruint", "montgomery"):
        pr = {t: sorted(out["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1] for t in names}  # median of P-core repeats
        out["scores"][ref] = price_all(counts, pr)
        out["leaders"][ref] = {k: leader({a: out["scores"][ref][a][k] for a in ALGS}) for k in keys}
    out["leaders"]["official"] = {k: leader({a: official[a][k] for a in ALGS}) for k in keys}
    print("\ncell        official            ruint                     montgomery                agree")
    for k in keys:
        lo, lr, lm = (out["leaders"][x][k] for x in ("official", "ruint", "montgomery"))
        fmt = lambda l: l[0] + (f" (tie {', '.join(l[1])})" if l[1] else "")
        print(f"  {k:7s} {fmt(lo):26s} {fmt(lr):26s} {fmt(lm):26s} {'yes' if (lr[0], set(lr[1])) == (lm[0], set(lm[1])) else 'NO'}")
    print("\ncalibrated log2(mean cost, in reference multiplies) [95% CI]:")
    for k in keys:
        print(f"  {k}:")
        for a in ALGS:
            o, r_, m = official[a][k], out["scores"]["ruint"][a][k], out["scores"]["montgomery"][a][k]
            print(f"    {a:12s} official {o['mean_log2']:.2f}   ruint {r_['mean_log2']:.2f} [{r_['ci95'][0]:.2f}, {r_['ci95'][1]:.2f}]"
                  f"   montgomery {m['mean_log2']:.2f} [{m['ci95'][0]:.2f}, {m['ci95'][1]:.2f}]")
    json.dump(out, open("calibrate.json", "w"), indent=1)
