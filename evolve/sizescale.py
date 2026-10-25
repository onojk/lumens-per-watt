"""qs-gene size-scaling test on the corrected card (NOTES.md, "qs-gene size-scaling test on the
corrected card: design and predictions"; written before this script ran).

Card: final qs with a_mode = on_demand, sort_charge = 1. Pipeline per size: rho at that size's
rho-only robust budget (72: 1,579; 84: 5,793; 96: 12,634 from the corrected re-solve; 54 from
its own map, mode map54), then qs. Fitness (c): robust ratio against qs + lc 1.4's genes alone
under the corrected card, on the same numbers; misses score 1e9.

  python3 sizescale.py map54 [w]  -> sizescale_map54.json   (54-bit map, seeds 9500000 + 100 pb + 54; rho budget)
  python3 sizescale.py msolve [w] -> sizescale_tracks.json  (two tracks, user's decision Oct 25: per-size pipeline
                                                              budgets for Track R (robust = ruint; rho-only) and Track M
                                                              (Montgomery alone; rho + ECM); per-pricing optima at
                                                              54-96 with the ECM grid widened to 2^22 where an optimum
                                                              sits at the 2^20 edge)
  python3 sizescale.py tune       -> sizescale_tune.json    (per track: TPE, tpe-tuned settings, seeds 0-3, 200 trials
                                                              per size; tuning numbers 24 per band, seeds 9300000 + 100 pb + bits)
  python3 sizescale.py sealed     -> sizescale_sealed.json  (both tracks' frozen genomes plus the two baselines, in both
                                                              tracks' pipelines at every size; 80 per band, seeds 9400000 + 100 pb + bits)

Track R fitness: max over the three pricings (robust). Track M fitness: the Montgomery ratio.
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, statistics
from multiprocessing import Pool
import numpy as np
import optypes, oracle
import partition as P
import stopping as ST
import run8_space as S
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many

PR3 = P.PRICINGS
pr = optypes.prices()
SIZES = (54, 72, 84, 96)
BANDS = {54: (16, 20, 24, 27), 72: (16, 20, 24, 28, 32, 36), 84: (16, 20, 24, 28, 32, 36, 42),
         96: (16, 20, 24, 28, 32, 36, 42, 48)}
RHO_B = {72: 1579, 84: 5793, 96: 12634}               # corrected re-solve (resolve.out); 54: map54
CARD = {"a_mode": "on_demand", "sort_charge": 1}
OLD = dict(P.QS_VARIANTS["qs + lc 1.4"], **CARD)
NEW = dict({"t": "qs", "kc": 4, "bc": 0.8993889783377338, "mc": 0.7340990893362095,
            "tc": 1.1044621542694246, "lc": 1.6612269841697611}, **CARD)
FROZEN_REF = dict(P.QS_VARIANTS["qs + lc 1.4"])        # the frozen reference (enumerate, no sort charge)
TRIALS, SEEDS = 200, (0, 1, 2, 3)
B = 10000

def pop(bits, per, base):
    out = {}
    for pb in BANDS[bits]:
        seed = base + 100 * pb + bits
        out[pb] = semiprimes_pq(bits, per, seed) if 2 * pb >= bits else semiprimes_unbalanced(bits, pb, per, seed)
    return out

def pipeline(qsg, rho_b, ecm_b=0):
    return [dict(P.PRE["td"], ob=0), dict(P.PRE["rho"], ob=rho_b), dict(P.PRE["pm1"], ob=0), dict(P.PRE["ecm"], ob=ecm_b), qsg]

TRACKS = ("R", "M")
def track_fit(c, ref, track):
    if track == "R":
        return max(c[Pn].mean() / ref[Pn].mean() for Pn in PR3)
    return c["montgomery"].mean() / ref["montgomery"].mean()

def track_budgets(bits, track):
    t = json.load(open("sizescale_tracks.json"))
    b = t["pipelines"][str(bits)][track]
    return b["rho"], b["ecm"]

EXT = [b for b in P.FINE if b > 0] + [round(2 ** (20 + i / 8)) for i in range(1, 17)]   # ECM grid to 2^22

def corrected_map_rows(bits):
    if bits == 54:
        return json.load(open("sizescale_map54.json"))["rows"]
    import resolve as RS
    import typemix as TM
    nums, _ = TM.load(bits)
    rows = RS.rows_of(bits)
    RS.add_qs(rows, nums, OLD, "qs corrected")
    return rows

def ecm_ext_job(N):
    r = P.run_alone(P.PRE["ecm"], N, 2 ** 22, [b for b in EXT if b > 2 ** 20])
    return r

def ext_matrix(M, rows, ext_rec, Pn):
    """Summed composed cost over (rho in GRID) x (ECM in [0] + EXT), qs as the map's qs column."""
    qsv = M.qs[Pn]
    rc, al = [], []
    for b in ST.GRID:
        t = M.stage_terms("rho", b, Pn)
        rc.append(0.0 if t is None else float(t[1].sum()))
        al.append(np.ones(M.n) if t is None else (~t[0]).astype(float))
    T = M.T["ecm"].copy()
    full = M.full["ecm"][Pn].copy()
    PRP = {"official": None, "ruint": P.prices()["ruint"], "montgomery": P.prices()["montgomery"]}
    for i, r in ext_rec.items():
        T[i] = r["T"] if r["T"] is not None else np.inf
        full[i] = float(sum(r["per_type"].values())) if Pn == "official" else P.cost_of(r["per_type"], PRP[Pn])
    ec, un = [np.zeros(M.n)], [qsv]
    for e in EXT:
        succ = T <= e
        if e <= 2 ** 20:
            sp = M.spent["ecm"][P.FINE.index(e)]
        else:
            sp = np.array([ext_rec[i]["spent"].get(str(e), ext_rec[i]["ops"]) if i in ext_rec else 0.0 for i in range(M.n)])
        ec.append(np.where(succ, full, sp * M.pib["ecm"][Pn]))
        un.append(np.where(succ, 0.0, qsv))
    A, E, U = np.array(al), np.array(ec), np.array(un)
    return np.array(rc)[:, None] + A @ E.T + A @ U.T, qsv.sum()

def costs(genome, nums):
    rs = run_many(genome, nums, P.QS_CAP, types=True)
    miss = sum(1 for x, (N, _, _) in zip(rs, nums) if not (x[1] is not None and 1 < int(x[1]) < N))
    return miss, {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3}

def qsg(pt):
    return dict({"t": "qs", "kc": int(pt["kc"]), "bc": pt["bc"], "mc": pt["mc"], "tc": pt["tc"], "lc": pt["lc"]}, **CARD)

def rho_budget(bits):
    return RHO_B[bits] if bits in RHO_B else json.load(open("sizescale_map54.json"))["rho_budget"]

def msolve(workers):
    out = {"pipelines": {}, "per_pricing": {}}
    for bits in (54, 72, 78, 84, 90, 96):
        rows = corrected_map_rows(bits)
        M = P.Map(rows, "qs corrected", P.prices())
        S_, qsum = ST.mats([(M, {Pn: 1.0 for Pn in PR3})])
        res = {}
        for Pn in PR3:
            r, e = np.unravel_index(np.argmin(S_[Pn]), S_[Pn].shape)
            res[Pn] = {"rho": ST.GRID[r], "ecm": ST.GRID[e], "fitness": float(S_[Pn][r, e] / qsum[Pn]), "edge": ST.GRID[e] == ST.GRID[-1]}
        if any(v["edge"] for v in res.values()):
            need = [i for i, rr in enumerate(rows) if rr["ecm"]["T"] is None or rr["ecm"]["T"] > 2 ** 20]
            with Pool(workers) as pool:
                recs = pool.map(ecm_ext_job, [int(rows[i]["N"]) for i in need], chunksize=1)
            ext_rec = dict(zip(need, recs))
            for Pn in PR3:
                if res[Pn]["edge"]:
                    Mx, qs_ = ext_matrix(M, rows, ext_rec, Pn)
                    r, e = np.unravel_index(np.argmin(Mx), Mx.shape)
                    eb = ([0] + EXT)[e]
                    res[Pn]["widened"] = {"rho": ST.GRID[r], "ecm": eb, "fitness": float(Mx[r, e] / qs_),
                                          "edge_again": eb == EXT[-1], "rows_rerun": len(need)}
        ro, rf, F = ST.robust_opt(S_, qsum)
        res["robust"] = {"rho": ro["rho"], "ecm": ro["ecm"], "fitness": rf}
        out["per_pricing"][bits] = res
        if bits in SIZES:
            out["pipelines"][bits] = {"R": {"rho": ro["rho"], "ecm": ro["ecm"]},
                                      "M": {"rho": res["montgomery"]["rho"], "ecm": res["montgomery"]["ecm"]}}
        print(f"{bits}: " + "; ".join(f"{k}: rho {v['rho']}, ecm {v['ecm']} ({v['fitness']:.3f})" + (" [edge]" if v.get("edge") else "")
                                       + (f" -> widened to 2^22: rho {v['widened']['rho']}, ecm {v['widened']['ecm']} ({v['widened']['fitness']:.3f})"
                                          + (" [edge again]" if v["widened"]["edge_again"] else "") if "widened" in v else "")
                                       for k, v in res.items()))
    json.dump(out, open("sizescale_tracks.json", "w"), indent=1, default=float)

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "map54":
        workers = int(ARGS[1]) if len(ARGS) > 1 else 8
        bp = pop(54, P.PER_BAND, 9500000)
        nums = [t for v in bp.values() for t in v]
        oracle.check(nums)
        with Pool(workers) as pool:
            rows = pool.map(P.map_job, [(pb, N) for pb, v in bp.items() for N, _, _ in v], chunksize=2)
        rs = run_many([OLD], nums, P.QS_CAP, types=True)
        for r, x in zip(rows, rs):
            r["qs corrected"] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
        M = P.Map(rows, "qs corrected", P.prices())
        S_, qsum = ST.mats([(M, {Pn: 1.0 for Pn in PR3})])
        F = np.max([S_[Pn] / qsum[Pn] for Pn in PR3], axis=0)
        r_only = F[:, 0]                                   # ECM off (index 0 = budget 0)
        j = int(np.argmin(r_only))
        ro, rf, _ = ST.robust_opt(S_, qsum)
        out = {"rho_budget": ST.GRID[j], "rho_only_fitness": float(r_only[j]), "two_stage_robust": ro, "two_stage_fitness": rf,
               "rows": rows}
        json.dump(out, open("sizescale_map54.json", "w"))
        print(f"54-bit map ({len(nums)} numbers): rho-only robust optimum rho {ST.GRID[j]} (fitness {r_only[j]:.4f}); "
              f"two-stage robust optimum {ro} (fitness {rf:.4f})")
        sys.exit(0)

    if mode == "msolve":
        msolve(int(ARGS[1]) if len(ARGS) > 1 else 8)
        sys.exit(0)

    if mode == "tune":
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        out = {}
        for track in TRACKS:
            out[track] = {}
            for bits in SIZES:
                bp = pop(bits, 24, 9300000)
                nums = [t for v in bp.values() for t in v]
                oracle.check(nums)
                rb, eb = track_budgets(bits, track)
                _, ref = costs([OLD], nums)
                def fit(pt):
                    miss, c = costs(pipeline(qsg(pt), rb, eb), nums)
                    return 1e9 if miss else track_fit(c, ref, track)
                base = {"old genes": fit(OLD), "new genes": fit(NEW)}
                runs = []
                for seed in SEEDS:
                    sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=TRIALS // 10, multivariate=True)
                    study = optuna.create_study(sampler=sampler)
                    def objective(t):
                        pt = {"kc": t.suggest_int("kc", 1, 32), "bc": t.suggest_float("bc", 0.7, 3.0),
                              "mc": t.suggest_float("mc", 0.05, 12.0, log=True), "tc": t.suggest_float("tc", 1.0, 3.5),
                              "lc": t.suggest_float("lc", 1.0, 2.0)}
                        return fit(pt)
                    study.optimize(objective, n_trials=TRIALS)
                    runs.append({"seed": seed, "best": study.best_params, "fitness": study.best_value,
                                 "top5": sorted(([t.value, t.params] for t in study.trials), key=lambda x: x[0])[:5]})
                best = min(runs, key=lambda r: r["fitness"])
                out[track][bits] = {"budgets": [rb, eb], "n_tuning": len(nums), "baselines": base, "runs": runs,
                                    "frozen": best["best"], "frozen_seed": best["seed"], "frozen_fitness": best["fitness"]}
                print(f"Track {track}, {bits} bits (rho {rb}, ECM {eb}; {len(nums)} tuning numbers): old genes {base['old genes']:.4f}, "
                      f"new genes {base['new genes']:.4f}", flush=True)
                for r in runs:
                    b = r["best"]
                    print(f"   seed {r['seed']}: {r['fitness']:.4f}  kc {b['kc']}, bc {b['bc']:.3f}, mc {b['mc']:.3f}, tc {b['tc']:.3f}, lc {b['lc']:.3f}", flush=True)
                print(f"   frozen: seed {best['seed']}", flush=True)
        json.dump(out, open("sizescale_tune.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "sealed":
        tune = json.load(open("sizescale_tune.json"))
        G = {f"{tr}-tuned@{b}": qsg(tune[tr][str(b)]["frozen"]) for tr in TRACKS for b in SIZES}
        G["old genes"], G["new genes"] = OLD, NEW
        out = {"cells": {}, "winners": {}, "trend": {}, "cross_size": {}}
        for bits in SIZES:
            bp = pop(bits, P.PER_BAND, 9400000)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            band = np.array([pb for pb, v in bp.items() for _ in v])
            groups = [np.flatnonzero(band == pb) for pb in bp]
            refs = {"corrected": costs([OLD], nums)[1], "frozen": costs([FROZEN_REF], nums)[1]}
            rng = random.Random(2026)
            idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(B)]
            allx = np.arange(len(nums))
            cell = {}
            C = {}
            for track in TRACKS:
                rb, eb = track_budgets(bits, track)
                for g, q_ in G.items():
                    C[(track, g)] = costs(pipeline(q_, rb, eb), nums)
            def band_gate(c, R_, prs):
                bands = {}
                for Pn in prs:
                    bands[Pn] = {}
                    for pb, gi in zip(bp, groups):
                        r2 = random.Random(2026)
                        vals = []
                        for _ in range(2000):
                            i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                            vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
                        bands[Pn][pb] = ST.q(vals)
                ub = max(v[1] for Pn in prs for v in bands[Pn].values())
                lb = max(v[0] for Pn in prs for v in bands[Pn].values())
                return ("FAIL" if lb > ST.GATE else ("PASS" if ub <= ST.GATE else "BORDERLINE")), ub, lb
            for (track, g), (miss, c) in C.items():
                for rname, R_ in refs.items():
                    scores = {Pn: float(c[Pn].mean() / R_[Pn].mean()) for Pn in PR3}
                    fv = [track_fit({Pn: c[Pn][i] for Pn in PR3}, {Pn: R_[Pn][i] for Pn in PR3}, track) for i in idxs]
                    gate_prs = PR3 if track == "R" else ("montgomery",)
                    gate, ub, lb = band_gate(c, R_, gate_prs)
                    if miss:
                        gate = "FAIL"
                    rec = {"track_fitness": track_fit(c, R_, track), "ci": ST.q(fv), "scores": scores,
                           "robust": max(scores.values()), "binding": max(scores, key=scores.get), "misses": miss,
                           "gate": gate, "gate_worst_upper": ub, "gate_worst_lower": lb}
                    if track == "M":
                        rg, rub, rlb = band_gate(c, R_, ("ruint",))
                        rec["ruint_gate_info"] = {"gate": rg, "upper": rub, "lower": rlb}
                    cell[f"{track} pipeline | {g} | ref {rname}"] = rec
            # winners per track (own candidates, own pipeline, corrected reference)
            R_ = refs["corrected"]
            win = {}
            for track in TRACKS:
                cands = [g for g in G if g.startswith(f"{track}-tuned") or g in ("old genes", "new genes")]
                wg = min(cands, key=lambda g: track_fit(C[(track, g)][1], R_, track))
                c = C[(track, wg)][1]
                win[track] = {"genome": wg, "genes": G[wg], "budgets": track_budgets(bits, track),
                              "scores": {Pn: float(c[Pn].mean() / R_[Pn].mean()) for Pn in PR3}}
            cR, cM = C[("R", win["R"]["genome"])][1], C[("M", win["M"]["genome"])][1]
            pdm = float(cR["montgomery"].mean() / cM["montgomery"].mean())
            pdr = float(cM["ruint"].mean() / cR["ruint"].mean())
            pdm_ci = ST.q([cR["montgomery"][i].mean() / cM["montgomery"][i].mean() for i in idxs])
            pdr_ci = ST.q([cM["ruint"][i].mean() / cR["ruint"][i].mean() for i in idxs])
            win["PD_M"], win["PD_M_ci"], win["PD_R"], win["PD_R_ci"] = pdm, pdm_ci, pdr, pdr_ci
            win["official_M_over_R"] = float(cM["official"].mean() / cR["official"].mean())
            # paired: tuned (own size) vs old genes, per track
            pairs = {}
            for track in TRACKS:
                ca, cb = C[(track, f"{track}-tuned@{bits}")][1], C[(track, "old genes")][1]
                pp = {}
                for Pn in PR3:
                    vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs]
                    pp[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": ST.q(vals)}
                tv = [math.log2(track_fit({Pn: ca[Pn][i] for Pn in PR3}, {Pn: R_[Pn][i] for Pn in PR3}, track) /
                                track_fit({Pn: cb[Pn][i] for Pn in PR3}, {Pn: R_[Pn][i] for Pn in PR3}, track)) for i in idxs]
                pp["track"] = {"log2": math.log2(track_fit(ca, R_, track) / track_fit(cb, R_, track)), "ci": ST.q(tv)}
                pairs[track] = pp
            out["cells"][bits] = cell
            out["winners"][bits] = {"winners": win, "tuned_vs_old": pairs}
            out["cross_size"][bits] = {track: {f"{track}-tuned@{b}": track_fit(C[(track, f'{track}-tuned@{b}')][1], R_, track) for b in SIZES}
                                       for track in TRACKS}
            print(f"\n{bits} bits ({len(nums)} sealed numbers; final qs corrected; reference qs + lc 1.4 corrected alone)")
            for track in TRACKS:
                w = win[track]
                rec = cell[f"{track} pipeline | {w['genome']} | ref corrected"]
                fr = cell[f"{track} pipeline | {w['genome']} | ref frozen"]
                extra = f"; ruint gate (info) {rec['ruint_gate_info']['gate']}" if track == "M" else ""
                print(f"  Track {track} winner: {w['genome']} in rho {w['budgets'][0]}, ECM {w['budgets'][1]}: track fitness {rec['track_fitness']:.4f} "
                      f"[{rec['ci'][0]:.4f}, {rec['ci'][1]:.4f}] (" + " / ".join(f"{v:.3f}" for v in rec["scores"].values())
                      + f"; binds {rec['binding'][:4]}); gate {rec['gate']}{extra}; vs frozen ref " + " / ".join(f"{v:.3f}" for v in fr["scores"].values()))
            print(f"  cross-pricing: PD_M (Montgomery: R winner / M winner) {pdm:.3f} [{pdm_ci[0]:.3f}, {pdm_ci[1]:.3f}]; "
                  f"PD_R (ruint: M winner / R winner) {pdr:.3f} [{pdr_ci[0]:.3f}, {pdr_ci[1]:.3f}]; official M / R {win['official_M_over_R']:.3f}")
            for track in TRACKS:
                pp = pairs[track]
                print(f"  Track {track}: tuned@{bits} vs old genes, track metric {pp['track']['log2']:+.3f} [{pp['track']['ci'][0]:+.3f}, {pp['track']['ci'][1]:+.3f}]  "
                      + "  ".join(f"{Pn[:4]} {pp[Pn]['log2']:+.3f} [{pp[Pn]['ci'][0]:+.3f},{pp[Pn]['ci'][1]:+.3f}]" for Pn in PR3))
                print(f"     cross-size (track fitness of each size's tuned genome here): " + ", ".join(f"{k}: {v:.4f}" for k, v in out["cross_size"][bits][track].items()))
        for track in TRACKS:
            out["trend"][track] = {}
            for gname in ("kc", "bc", "mc", "tc", "lc"):
                vals = {b: [r["best"][gname] for r in tune[track][str(b)]["runs"]] for b in SIZES}
                med = [statistics.median(vals[b]) for b in SIZES]
                mono_up = all(a < b for a, b in zip(med, med[1:])); mono_dn = all(a > b for a, b in zip(med, med[1:]))
                sep = max(vals[96]) < min(vals[54]) or min(vals[96]) > max(vals[54])
                xs = [b for b in SIZES for _ in vals[b]]; ys = [v for b in SIZES for v in vals[b]]
                rk = lambda a: [sorted(a).index(v) for v in a]
                rho_s = float(np.corrcoef(rk(xs), rk(ys))[0, 1])
                out["trend"][track][gname] = {"per_size": vals, "medians": med, "monotone": "up" if mono_up else ("down" if mono_dn else "no"),
                                              "ends_separated": sep, "spearman": rho_s}
                print(f"Track {track} trend {gname}: medians " + ", ".join(f"{b}: {m:.3f}" for b, m in zip(SIZES, med))
                      + f"; monotone {out['trend'][track][gname]['monotone']}; 54 vs 96 separated {sep}; Spearman {rho_s:+.2f}")
        json.dump(out, open("sizescale_sealed.json", "w"), indent=1, default=float)
