"""Per-track p-1 map check (NOTES.md, "Per-track p-1 map check": protocol and predictions written
before this script ran). Map-only, corrected card, each track's final genes as the final qs.

  python3 pm1check.py [workers]  -> pm1check_map.json (pm1 at B = 2^8 .. 2^15 on the map numbers),
                                    pm1check.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, os
from multiprocessing import Pool
import numpy as np
import partition as P
import sizescale as SS
import sizescale2 as S2

PR3 = P.PRICINGS
KS = list(range(8, 16))
PRP = {"official": None, "ruint": P.prices()["ruint"], "montgomery": P.prices()["montgomery"]}

def b_of(N, k):
    return math.log2(2 ** k + 0.5) / math.log2(N)

def pm1_job(args):
    N, k = args
    g = dict(P.PRE["pm1"], b=b_of(N, k))
    assert max(10, int(N ** g["b"])) == 2 ** k
    r = P.run_alone(g, N, P.PRE_CAP, [])
    return {"T": r["T"], "ops": r["ops"], "per_type": r["per_type"]}

def price(pt, Pn):
    return float(sum(pt.values())) if Pn == "official" else P.cost_of(pt, PRP[Pn])

def composed3(M, ext_rec, top, Pn, pm):
    """Summed cost over rho (GRID) x p-1 ([off] + KS) x ECM ([0] + grid to `top`), final qs = M's qs."""
    grid = S2.grid_ext(top) if top > 2 ** 20 else [b for b in P.FINE if b > 0]
    qsv = M.qs[Pn]
    rc, al = [], []
    for b in P_GRID():
        t = M.stage_terms("rho", b, Pn)
        rc.append(0.0 if t is None else float(t[1].sum()))
        al.append(np.ones(M.n) if t is None else (~t[0]).astype(float))
    A = np.array(al)
    T = M.T["ecm"].copy()
    full = M.full["ecm"][Pn].copy()
    for i, r in ext_rec.items():
        T[i] = r["T"] if r["T"] is not None else np.inf
        full[i] = price(r["per_type"], Pn)
    ec, un = [np.zeros(M.n)], [qsv]
    for e in grid:
        succ = T <= e
        if e <= 2 ** 20:
            sp = M.spent["ecm"][P.FINE.index(e)]
        else:
            sp = np.array([ext_rec[i]["spent"].get(str(e), ext_rec[i]["ops"]) if i in ext_rec else 0.0 for i in range(M.n)])
        ec.append(np.where(succ, full, sp * M.pib["ecm"][Pn]))
        un.append(np.where(succ, 0.0, qsv))
    E, U = np.array(ec), np.array(un)
    out = []
    for j in [None] + KS:
        if j is None:
            pc, alive = np.zeros(M.n), np.ones(M.n)
        else:
            recs = pm[str(j)]
            pc = np.array([price(r["per_type"], Pn) for r in recs])
            alive = np.array([0.0 if r["T"] is not None else 1.0 for r in recs])
        Aj = A * alive[None, :]
        out.append(np.array(rc)[:, None] + (A @ pc)[:, None] + Aj @ E.T + Aj @ U.T)
    return np.stack(out, axis=1), [0] + grid

def P_GRID():
    import stopping as ST
    return ST.GRID

def solve(rows, nums, genome, pm, workers, objective):
    """objective: 'R' (robust), or a pricing name (that pricing alone)."""
    rs = S2.run_many([genome], nums, P.QS_CAP, types=True)
    for r, x, (N, _, _) in zip(rows, rs, nums):
        assert x[1] is not None and 1 < int(x[1]) < N
        r["track qs"] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
    M = P.Map(rows, "track qs", P.prices())
    Mref = P.Map(rows, "qs corrected", P.prices())
    refsum = {Pn: Mref.qs[Pn].sum() for Pn in PR3}
    top, ext_rec = 2 ** 20, {}
    while True:
        mats = {Pn: composed3(M, ext_rec, top, Pn, pm) for Pn in PR3}
        egrid = mats["official"][1]
        S = {Pn: mats[Pn][0] / refsum[Pn] for Pn in PR3}
        F = np.max([S[Pn] for Pn in PR3], axis=0) if objective == "R" else S[objective]
        r, j, e = np.unravel_index(np.argmin(F), F.shape)
        r0, e0 = np.unravel_index(np.argmin(F[:, 0, :]), F[:, 0, :].shape)
        at_edge = egrid[-1] in (egrid[e], egrid[e0])
        if not at_edge or top == S2.EDGES[-1]:
            break
        top = next(x for x in S2.EDGES if x > top)
        need = [i for i, rr in enumerate(rows) if rr["ecm"]["T"] is None or rr["ecm"]["T"] > 2 ** 20]
        with Pool(workers) as pool:
            ext_rec = dict(zip(need, pool.map(S2.ext_job, [(int(rows[i]["N"]), top) for i in need], chunksize=1)))
    G = P_GRID()
    def at(ri, ji, ei):
        return {"rho": G[ri], "pm1_B": 0 if ji == 0 else 2 ** KS[ji - 1], "ecm": egrid[ei], "fitness": float(F[ri, ji, ei]),
                "scores": {Pn: float(S[Pn][ri, ji, ei]) for Pn in PR3}}
    # best per B (rho, ECM re-optimized), for the profile
    prof = {}
    for ji in range(F.shape[1]):
        ri, ei = np.unravel_index(np.argmin(F[:, ji, :]), F[:, ji, :].shape)
        prof[0 if ji == 0 else 2 ** KS[ji - 1]] = at(ri, ji, ei)
    return {"joint": at(r, j, e), "no_pm1": at(r0, 0, e0), "profile": prof, "grid_top": top, "at_edge": bool(at_edge),
            "_F": F, "_egrid": egrid}

if __name__ == "__main__":
    workers = int(ARGS[0]) if ARGS else 8
    sealed = json.load(open("sizescale_r2_sealed.json"))
    if os.path.exists("pm1check_map.json"):
        pmap = json.load(open("pm1check_map.json"))
    else:
        pmap = {}
        with Pool(workers) as pool:
            for bits in SS.SIZES:
                nums = S2.map_nums(bits)
                res = pool.map(pm1_job, [(int(t[0]), k) for k in KS for t in nums], chunksize=8)
                n = len(nums)
                pmap[str(bits)] = {"N": [str(t[0]) for t in nums], **{str(k): res[i * n:(i + 1) * n] for i, k in enumerate(KS)}}
                print(f"{bits} bits: {n} numbers; p-1 solves " + ", ".join(
                    f"2^{k} {sum(r['T'] is not None for r in pmap[str(bits)][str(k)]) / n:.3f} ({pmap[str(bits)][str(k)][0]['ops']} ops)" for k in KS), flush=True)
        json.dump(pmap, open("pm1check_map.json", "w"))
    out = {}
    for bits in SS.SIZES:
        rows = SS.corrected_map_rows(bits)
        nums = S2.map_nums(bits)
        assert [r["N"] for r in rows] == [str(t[0]) for t in nums] == pmap[str(bits)]["N"]
        out[bits] = {}
        for track in SS.TRACKS:
            rec = sealed["sizes"][str(bits)]["tracks"][track]
            g = rec["final_genes"]
            fr, fe = rec["budgets_final"]
            res = {}
            for obj in (track, "official", "ruint", "montgomery") if track == "R" else ("montgomery", "official", "ruint"):
                d = solve([dict(r) for r in rows], nums, g, pmap[str(bits)], workers, obj)
                F, eg = d.pop("_F"), d.pop("_egrid")
                if obj == track or (track == "M" and obj == "montgomery"):
                    fin = float(F[P_GRID().index(fr), 0, eg.index(fe)])
                    d["final_pipeline_fitness"] = fin
                    d["log2_joint_vs_final"] = math.log2(d["joint"]["fitness"] / fin)
                    d["no_pm1_reproduces_final"] = (d["no_pm1"]["rho"], d["no_pm1"]["ecm"]) == (fr, fe)
                res[obj] = d
            out[bits][track] = res
            main = res[track if track == "R" else "montgomery"]
            j, n0 = main["joint"], main["no_pm1"]
            print(f"\n{bits} Track {track} (final pipeline rho {fr}, ECM {fe}; no-p-1 optimum ({n0['rho']}, {n0['ecm']})"
                  f"{'' if main['no_pm1_reproduces_final'] else ' DIFFERS'}; ECM grid to 2^{int(math.log2(main['grid_top']))}{', AT EDGE' if main['at_edge'] else ''})")
            print(f"   joint optimum: rho {j['rho']}, p-1 B {j['pm1_B'] or 'off'}, ECM {j['ecm']}: fitness {j['fitness']:.4f} vs final {main['final_pipeline_fitness']:.4f} "
                  f"(log2 {main['log2_joint_vs_final']:+.4f}); " + " / ".join(f"{v:.3f}" for v in j["scores"].values())
                  + f"; p-1 {'ON' if j['pm1_B'] else 'off'}")
            print("   best per B: " + "  ".join(f"{('off' if B == 0 else '2^%d' % int(math.log2(B)))} {v['fitness']:.4f} ({v['rho']},{v['ecm']})" for B, v in main["profile"].items()))
            for obj, d in res.items():
                if d is main:
                    continue
                jj = d["joint"]
                print(f"   {obj}-alone optimum: rho {jj['rho']}, p-1 B {jj['pm1_B'] or 'off'}, ECM {jj['ecm']} ({jj['fitness']:.4f}; no p-1 "
                      f"({d['no_pm1']['rho']}, {d['no_pm1']['ecm']}) {d['no_pm1']['fitness']:.4f}; log2 {math.log2(jj['fitness'] / d['no_pm1']['fitness']):+.4f})")
    json.dump(out, open("pm1check.json", "w"), indent=1, default=float)
