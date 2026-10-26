"""Before/after measurement for charging ECM's additions (NOTES.md, "Cost model: ECM modular additions").

  1. ECM alone on every map number (54-96 bits): the new ECM map column (success ops, spent at each grid
     budget, per type) from the current card; mean cost new / old per pricing (old = the stored maps).
  2. Re-solves with the new column, Track M (and Track R, information):
     (a) the final pipelines without p-1 (sizescale2.solve_track, final genes) against the round-3 budgets;
     (b) the p-1-inclusive joint optimum (pm1check.solve, the kc/lc round's (d) genes) against the (d) budgets.
     Steps moved per budget.

  python3 ecmword_measure.py [workers] -> ecmword_measure.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math
from multiprocessing import Pool
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, sizescale3 as K, pm1check as C

PR3 = P.PRICINGS
PRP = {"official": None, "ruint": P.prices()["ruint"], "montgomery": P.prices()["montgomery"]}

def ecm_job(N):
    return P.run_alone(P.PRE["ecm"], N, P.PRE_CAP, [b for b in P.FINE if b > 0])

def price(pt, Pn):
    return float(sum(pt.values())) if Pn == "official" else P.cost_of(pt, PRP[Pn])

if __name__ == "__main__":
    workers = int(ARGS[0]) if ARGS else 8
    sealed2 = json.load(open("sizescale_r2_sealed.json"))
    kb = json.load(open("sizescale_k_budgets.json"))
    pmapall = json.load(open("pm1check_map.json"))
    out = {}
    for bits in SS.SIZES:
        rows = SS.corrected_map_rows(bits)
        nums = S2.map_nums(bits)
        with Pool(workers) as pool:
            new = pool.map(ecm_job, [int(r["N"]) for r in rows], chunksize=4)
        ratio = {}
        for Pn in PR3:
            o = [price(r["ecm"]["per_type"], Pn) for r in rows]
            n = [price(x["per_type"], Pn) for x in new]
            ratio[Pn] = float(np.mean(n) / np.mean(o))
        same_T = sum((r["ecm"]["T"] is None) == (x["T"] is None) for r, x in zip(rows, new))
        for r, x in zip(rows, new):
            r["ecm"] = x
        rec = {"ecm_alone_new_over_old": ratio, "same_success": same_T, "n": len(rows), "tracks": {}}
        print(f"{bits} bits: ECM alone new/old mean cost " + " / ".join(f"{Pn[:4]} {v:.3f}" for Pn, v in ratio.items())
              + f"; same success/failure on {same_T}/{len(rows)}", flush=True)
        for track in SS.TRACKS:
            fc = sealed2["sizes"][str(bits)]["tracks"][track]
            g = SS.qsg(fc["final_genes"])
            a = S2.solve_track([dict(r) for r in rows], nums, g, track, workers)
            prev_a = tuple(fc["budgets_final"])
            st_a = {"rho": S2.steps(a["rho"], prev_a[0]), "ecm": S2.steps(a["ecm"], prev_a[1])}
            gk = SS.qsg(kb["genes"][str(bits)][track])
            b = C.solve([dict(r) for r in rows], nums, gk, pmapall[str(bits)], workers, K.OBJ[track])
            b.pop("_F"), b.pop("_egrid")
            j = b["joint"]
            prev_b = tuple(kb["pipelines"][str(bits)][track])
            st_b, mv_b = K.moved((j["rho"], j["pm1_B"], j["ecm"]), prev_b)
            rec["tracks"][track] = {"no_p1": {"budgets": [a["rho"], a["ecm"]], "previous": list(prev_a), "steps": st_a, "fitness": a["fitness"]},
                                    "with_p1": {"budgets": [j["rho"], j["pm1_B"], j["ecm"]], "previous": list(prev_b), "steps": st_b,
                                                "moved_more_than_one": mv_b, "fitness": j["fitness"]}}
            print(f"   Track {track}: no p-1 ({a['rho']}, {a['ecm']}) vs final {prev_a}, steps {st_a}; "
                  f"with p-1 ({j['rho']}, {j['pm1_B']}, {j['ecm']}) vs (d) {prev_b}, steps {st_b}" + ("  MOVED > 1 STEP" if mv_b else ""), flush=True)
        out[bits] = rec
    json.dump(out, open("ecmword_measure.json", "w"), indent=1, default=float)
