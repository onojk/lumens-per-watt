"""lampcore per-type counters against existing results (NOTES.md, "lampcore per-type op
counters", checks): calibrate.json's per-number counts and scores, and the partition study's
sealed per-number counts and costs, recomputed from lampcore --types, must equal the
Python-trace values exactly.

  python3 types_check.py [workers]  -> types_check.json
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json
from multiprocessing import Pool
from fastlamps import run_many
import calibrate
import partition as P

WORKERS = int(ARGS[0]) if ARGS else 8

def same_order(lc, like):
    """lampcore's counts in the Python dict's key order (types it lacks must be zero)."""
    assert all(n == 0 for t, n in lc.items() if t not in like), (lc, like)
    return {t: lc[t] for t in like}

def check_calibrate():
    counts = json.load(open("calibrate_counts.json"))
    pops = calibrate.pops()
    rebuilt, compared = {}, 0
    for alg, g in calibrate.ALGS.items():
        rebuilt[alg] = {}
        for k, nums in pops.items():
            rs = run_many(g, nums, calibrate.CAP, types=True)
            rows = []
            for (N, p, q), r, x in zip(nums, rs, counts[alg][k]):
                assert x["N"] == str(N) and x["ops"] == r[0], (alg, k, N)
                c = same_order(r[4], x["counts"]) if r[0] is not None else x["counts"]
                if r[0] is not None:
                    assert c == x["counts"], ("counts differ", alg, k, N, c, x["counts"])
                    compared += 1
                rows.append({"N": x["N"], "ops": r[0], "counts": c})
            rebuilt[alg][k] = rows
    cal = json.load(open("calibrate.json"))
    for ref in ("ruint", "montgomery"):
        names = list(cal["prices"][f"{ref} P1"])
        pr = {t: sorted(cal["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1] for t in names}
        assert calibrate.price_all(rebuilt, pr) == cal["scores"][ref], ("scores differ", ref)
    return compared

def check_partition():
    out = json.load(open("partition_sealed.json"))
    pop = P.population(P.SEALED)
    jobs = [(gname, g, pb, N) for gname, g in out["genomes"].items() for pb in P.BANDS for N, p, q in pop[pb]]
    with Pool(WORKERS) as pool:
        py = pool.map(P.sealed_job, jobs, chunksize=2)
    pyd = {(r[0], r[2]): r for r in py}
    PR = P.prices()
    price = lambda c, Pn: float(sum(c.values())) if Pn == "official" else P.cost_of(c, PR[Pn])
    compared = 0
    for gname, g in out["genomes"].items():
        cost = {Pn: {} for Pn in P.PRICINGS}
        for pb in P.BANDS:
            rs = run_many(g, pop[pb], P.QS_CAP, types=True)
            for Pn in P.PRICINGS:
                cost[Pn][pb] = []
            for (N, p, q), r in zip(pop[pb], rs):
                _, _, _, ops, c_py = pyd[(gname, str(N))]
                c = same_order(r[4], c_py)
                assert r[0] == ops and c == c_py, ("sealed counts differ", gname, N, c, c_py)
                compared += 1
                for Pn in P.PRICINGS:
                    cost[Pn][pb].append(price(c, Pn))
        import math
        for Pn in P.PRICINGS:
            allv = [v for pb in P.BANDS for v in cost[Pn][pb]]
            assert math.log2(sum(allv) / len(allv)) == out["cells"][gname][Pn]["mean_log2"], ("cell differs", gname, Pn)
            for pb in P.BANDS:
                v = cost[Pn][pb]
                assert math.log2(sum(v) / len(v)) == out["cells"][gname][Pn]["bands"][str(pb)]["mean_log2"], (gname, Pn, pb)
    return compared

if __name__ == "__main__":
    a = check_calibrate()
    print(f"calibrate: {a} per-number count sets equal to calibrate_counts.json; scores equal to calibrate.json exactly")
    b = check_partition()
    print(f"partition sealed: {b} per-number count sets equal to the Python per-stage split; every cell's log2 mean equal to partition_sealed.json exactly")
    json.dump({"calibrate_runs": a, "partition_sealed_runs": b, "exact": True}, open("types_check.json", "w"), indent=1)
