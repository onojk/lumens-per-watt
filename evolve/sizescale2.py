"""qs-gene size-scaling test, rounds 2-3, two tracks (NOTES.md, "Size-scaling test, round 2 (two
tracks): protocol and predictions"; written before this script ran).

  python3 sizescale2.py tune 2     -> sizescale_r2_tune.json    (widened bounds; round-1 budgets per track)
  python3 sizescale2.py resolve 2  -> sizescale_r2_budgets.json (budgets re-solved with round-2 frozen genomes;
                                                                  steps against round 1; round-3 trigger)
  python3 sizescale2.py tune 3     -> sizescale_r3_tune.json    (only if triggered; round-2 re-solved budgets)
  python3 sizescale2.py resolve 3  -> sizescale_r3_budgets.json (final budgets after round 3; settled or not)
  python3 sizescale2.py sealed     -> sizescale_r2_sealed.json  (fresh numbers 9410000 + 100 pb + bits; ablation
                                                                  rows (a) (b) (c); winners; PD_M, PD_R)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, os
from multiprocessing import Pool
import numpy as np
import optypes, oracle
import partition as P
import stopping as ST
import sizescale as SS
from fastlamps import run_many

PR3 = P.PRICINGS
SIZES, TRACKS = SS.SIZES, SS.TRACKS
BOUNDS = {"kc": (1, 32), "bc": (0.3, 3.0), "mc": (0.01, 12.0), "tc": (1.0, 3.5), "lc": (1.0, 2.0)}
B = 10000
EDGES = (2 ** 22, 2 ** 24)

def bound_hits(pt):
    hits = []
    for g, (lo, hi) in BOUNDS.items():
        v = pt[g]
        if v <= lo * 1.1 or v >= hi * 0.9:
            hits.append(f"{g} {v:.4g} (bounds {lo}-{hi})")
    return hits

def budgets_file(rnd):
    return "sizescale_tracks.json" if rnd == 1 else f"sizescale_r{rnd}_budgets.json"

def budgets(rnd, bits, track):
    t = json.load(open(budgets_file(rnd)))
    b = t["pipelines"][str(bits)][track]
    return b["rho"], b["ecm"]

def tune_file(rnd):
    return "sizescale_tune.json" if rnd == 1 else f"sizescale_r{rnd}_tune.json"

def frozen(rnd, track, bits):
    return json.load(open(tune_file(rnd)))[track][str(bits)]["frozen"]

def map_nums(bits):
    if bits == 54:
        bp = SS.pop(54, P.PER_BAND, 9500000)
        return [t for v in bp.values() for t in v]
    import typemix as TM
    return TM.load(bits)[0]

def grid_ext(top):
    g = [b for b in P.FINE if b > 0]
    k = 1
    while g[-1] < top:
        g.append(round(2 ** (20 + k / 8)))
        k += 1
    return g

def ext_job(args):
    N, top = args
    return P.run_alone(P.PRE["ecm"], N, top, [b for b in grid_ext(top) if b > 2 ** 20])

def composed(M, ext_rec, top, Pn):
    """Summed composed cost over rho (GRID) x ECM ([0] + grid to `top`), final qs = M's qs column."""
    grid = grid_ext(top) if top > 2 ** 20 else [b for b in P.FINE if b > 0]
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
    for e in grid:
        succ = T <= e
        if e <= 2 ** 20:
            sp = M.spent["ecm"][P.FINE.index(e)]
        else:
            sp = np.array([ext_rec[i]["spent"].get(str(e), ext_rec[i]["ops"]) if i in ext_rec else 0.0 for i in range(M.n)])
        ec.append(np.where(succ, full, sp * M.pib["ecm"][Pn]))
        un.append(np.where(succ, 0.0, qsv))
    A, E, U = np.array(al), np.array(ec), np.array(un)
    return np.array(rc)[:, None] + A @ E.T + A @ U.T, [0] + grid

def solve_track(rows, nums, genome, track, workers):
    rs = run_many([genome], nums, P.QS_CAP, types=True)
    for r, x, (N, _, _) in zip(rows, rs, nums):
        assert x[1] is not None and 1 < int(x[1]) < N
        r["track qs"] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
    M = P.Map(rows, "track qs", P.prices())
    Mref = P.Map(rows, "qs corrected", P.prices())
    refsum = {Pn: Mref.qs[Pn].sum() for Pn in PR3}
    top, ext_rec = 2 ** 20, {}
    while True:
        mats = {Pn: composed(M, ext_rec, top, Pn) for Pn in PR3}
        egrid = mats["official"][1]
        F = (np.max([mats[Pn][0] / refsum[Pn] for Pn in PR3], axis=0) if track == "R"
             else mats["montgomery"][0] / refsum["montgomery"])
        r, e = np.unravel_index(np.argmin(F), F.shape)
        at_edge = egrid[e] == egrid[-1]
        if not at_edge or top == EDGES[-1]:
            break
        top = next(x for x in EDGES if x > top)
        need = [i for i, rr in enumerate(rows) if rr["ecm"]["T"] is None or rr["ecm"]["T"] > 2 ** 20]
        with Pool(workers) as pool:
            ext_rec = dict(zip(need, pool.map(ext_job, [(int(rows[i]["N"]), top) for i in need], chunksize=1)))
    scores = {Pn: float(mats[Pn][0][r, e] / refsum[Pn]) for Pn in PR3}
    return {"rho": ST.GRID[r], "ecm": egrid[e], "fitness": float(F[r, e]), "scores": scores, "grid_top": top,
            "at_edge": bool(at_edge)}

def steps(a, b):
    """Grid steps between budgets a and b (None: one is 0 and the other is not)."""
    if a == 0 or b == 0:
        return 0 if a == b else None
    return round(8 * abs(math.log2(a) - math.log2(b)))

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "tune":
        rnd = int(ARGS[1])
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        out = {}
        for track in TRACKS:
            out[track] = {}
            for bits in SIZES:
                bp = SS.pop(bits, 24, 9300000)
                nums = [t for v in bp.values() for t in v]
                oracle.check(nums)
                rb, eb = budgets(rnd - 1, bits, track)
                _, ref = SS.costs([SS.OLD], nums)
                def fit(pt):
                    miss, c = SS.costs(SS.pipeline(SS.qsg(pt), rb, eb), nums)
                    return 1e9 if miss else SS.track_fit(c, ref, track)
                prev = frozen(rnd - 1, track, bits)
                base = {"old genes": fit(SS.OLD), f"round {rnd - 1} frozen": fit(prev)}
                runs = []
                for seed in SS.SEEDS:
                    sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=SS.TRIALS // 10, multivariate=True)
                    study = optuna.create_study(sampler=sampler)
                    def objective(t):
                        pt = {"kc": t.suggest_int("kc", 1, 32), "bc": t.suggest_float("bc", 0.3, 3.0),
                              "mc": t.suggest_float("mc", 0.01, 12.0, log=True), "tc": t.suggest_float("tc", 1.0, 3.5),
                              "lc": t.suggest_float("lc", 1.0, 2.0)}
                        return fit(pt)
                    study.optimize(objective, n_trials=SS.TRIALS)
                    runs.append({"seed": seed, "best": study.best_params, "fitness": study.best_value, "bound_hits": bound_hits(study.best_params)})
                best = min(runs, key=lambda r: r["fitness"])
                out[track][bits] = {"budgets": [rb, eb], "baselines": base, "runs": runs, "frozen": best["best"],
                                    "frozen_seed": best["seed"], "frozen_fitness": best["fitness"], "frozen_bound_hits": bound_hits(best["best"])}
                print(f"Round {rnd}, Track {track}, {bits} bits (rho {rb}, ECM {eb}): old genes {base['old genes']:.4f}, "
                      f"round {rnd - 1} frozen {base[f'round {rnd - 1} frozen']:.4f}", flush=True)
                for r in runs:
                    b = r["best"]
                    print(f"   seed {r['seed']}: {r['fitness']:.4f}  kc {b['kc']}, bc {b['bc']:.3f}, mc {b['mc']:.4f}, tc {b['tc']:.3f}, lc {b['lc']:.3f}"
                          + (f"  BOUND: {'; '.join(r['bound_hits'])}" if r["bound_hits"] else ""), flush=True)
                print(f"   frozen: seed {best['seed']}", flush=True)
        json.dump(out, open(tune_file(rnd), "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "resolve":
        rnd = int(ARGS[1])
        workers = int(ARGS[2]) if len(ARGS) > 2 else 8
        out = {"pipelines": {}, "detail": {}, "steps_from_previous": {}}
        moved = False
        for bits in SIZES:
            rows = SS.corrected_map_rows(bits)
            nums = map_nums(bits)
            assert [r["N"] for r in rows] == [str(t[0]) for t in nums]
            out["pipelines"][bits], out["detail"][bits], out["steps_from_previous"][bits] = {}, {}, {}
            for track in TRACKS:
                g = SS.qsg(frozen(rnd, track, bits))
                d = solve_track([dict(r) for r in rows], nums, g, track, workers)
                pr_, pe = budgets(rnd - 1, bits, track)
                st = {"rho": steps(d["rho"], pr_), "ecm": steps(d["ecm"], pe)}
                mv = any(v is None or v > 1 for v in st.values())
                moved |= mv
                out["pipelines"][bits][track] = {"rho": d["rho"], "ecm": d["ecm"]}
                out["detail"][bits][track] = d
                out["steps_from_previous"][bits][track] = {"steps": st, "moved_more_than_one": mv, "previous": [pr_, pe]}
                print(f"{bits} Track {track}: rho {d['rho']}, ECM {d['ecm']} (fitness {d['fitness']:.4f}; " + " / ".join(f"{v:.3f}" for v in d["scores"].values())
                      + f"; ECM grid to 2^{int(math.log2(d['grid_top']))}{', AT EDGE' if d['at_edge'] else ''}); previous ({pr_}, {pe}); steps {st}"
                      + ("  MOVED > 1 STEP" if mv else ""), flush=True)
        out["moved_more_than_one_step"] = moved
        print(f"any budget moved more than one step (or off <-> on): {moved}")
        json.dump(out, open(budgets_file(rnd), "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "sealed":
        final_round = 3 if os.path.exists("sizescale_r3_tune.json") else 2
        final_budget_round = 3 if os.path.exists("sizescale_r3_budgets.json") else 2
        r1 = json.load(open("sizescale_sealed.json"))
        cand_final = {tr: {f"{tr}-final@{b}": SS.qsg(frozen(final_round, tr, b)) for b in SIZES} for tr in TRACKS}
        out = {"final_round": final_round, "final_budget_round": final_budget_round, "sizes": {}}
        for bits in SIZES:
            bp = SS.pop(bits, P.PER_BAND, 9410000)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            band = np.array([pb for pb, v in bp.items() for _ in v])
            groups = [np.flatnonzero(band == pb) for pb in bp]
            refs = {"corrected": SS.costs([SS.OLD], nums)[1], "frozen": SS.costs([SS.FROZEN_REF], nums)[1]}
            R_ = refs["corrected"]
            rng = random.Random(2026)
            idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(B)]
            def tf(c, i=None):
                if i is None:
                    return SS.track_fit(c, R_, track)
                return SS.track_fit({Pn: c[Pn][i] for Pn in PR3}, {Pn: R_[Pn][i] for Pn in PR3}, track)
            def gate(c, prs):
                ub = lb = 0.0
                for Pn in prs:
                    for gi in groups:
                        r2 = random.Random(2026)
                        vals = []
                        for _ in range(2000):
                            i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                            vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
                        lo, hi = ST.q(vals)
                        ub, lb = max(ub, hi), max(lb, lo)
                return ("FAIL" if lb > ST.GATE else ("PASS" if ub <= ST.GATE else "BORDERLINE")), ub, lb
            row = {}
            for track in TRACKS:
                b1 = budgets(1, bits, track)
                bf = budgets(final_budget_round, bits, track)
                # final winner: best by track fitness in the final pipeline among final-round tuned + baselines
                cands = dict(cand_final[track]); cands["old genes"], cands["new genes"] = SS.OLD, SS.NEW
                Cf = {g: SS.costs(SS.pipeline(q_, *bf), nums) for g, q_ in cands.items()}
                wg = min(Cf, key=lambda g: 1e9 if Cf[g][0] else SS.track_fit(Cf[g][1], R_, track))
                w1 = r1["winners"][str(bits)]["winners"][track]
                rows = {"(a) round-1 winner, round-1 budgets": (w1["genes"], b1),
                        "(b) final genes, round-1 budgets": (cands[wg], b1),
                        "(c) final genes, final budgets": (cands[wg], bf)}
                rec = {"final_winner": wg, "final_genes": cands[wg], "round1_winner": w1["genome"], "budgets_round1": b1,
                       "budgets_final": bf, "rows": {}}
                C = {}
                for name, (g, bud) in rows.items():
                    miss, c = (Cf[wg] if name.startswith("(c)") else SS.costs(SS.pipeline(g, *bud), nums))
                    C[name] = c
                    gt = gate(c, PR3 if track == "R" else ("montgomery",))
                    r = {"track_fitness": tf(c), "ci": ST.q([tf(c, i) for i in idxs]),
                         "scores": {Pn: float(c[Pn].mean() / R_[Pn].mean()) for Pn in PR3},
                         "scores_frozen_ref": {Pn: float(c[Pn].mean() / refs["frozen"][Pn].mean()) for Pn in PR3},
                         "misses": miss, "gate": "FAIL" if miss else gt[0], "gate_upper": gt[1], "gate_lower": gt[2]}
                    r["binding"] = max(r["scores"], key=r["scores"].get)
                    if track == "M":
                        rg = gate(c, ("ruint",))
                        r["ruint_gate_info"] = {"gate": rg[0], "upper": rg[1], "lower": rg[2]}
                    rec["rows"][name] = r
                ks = list(rows)
                pairs = {}
                for a, b in ((ks[1], ks[0]), (ks[2], ks[1]), (ks[2], ks[0])):
                    ca, cb = C[a], C[b]
                    pp = {"track": {"log2": math.log2(tf(ca) / tf(cb)), "ci": ST.q([math.log2(tf(ca, i) / tf(cb, i)) for i in idxs])}}
                    for Pn in PR3:
                        pp[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()),
                                  "ci": ST.q([math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs])}
                    pairs[f"{a[:3]} vs {b[:3]}"] = pp
                rec["pairs"] = pairs
                rec["_C"] = C
                row[track] = rec
            pdc = {}
            for lab, rn in (("round 1 (a rows)", "(a) round-1 winner, round-1 budgets"), ("final (c rows)", "(c) final genes, final budgets")):
                cR, cM = row["R"]["_C"][rn], row["M"]["_C"][rn]
                pdc[lab] = {"PD_M": float(cR["montgomery"].mean() / cM["montgomery"].mean()),
                            "PD_M_ci": ST.q([cR["montgomery"][i].mean() / cM["montgomery"][i].mean() for i in idxs]),
                            "PD_R": float(cM["ruint"].mean() / cR["ruint"].mean()),
                            "PD_R_ci": ST.q([cM["ruint"][i].mean() / cR["ruint"][i].mean() for i in idxs]),
                            "official_M_over_R": float(cM["official"].mean() / cR["official"].mean())}
            for track in TRACKS:
                del row[track]["_C"]
            out["sizes"][bits] = {"tracks": row, "cross_pricing": pdc,
                                  "round1_sealed_9400000": {k: r1["winners"][str(bits)]["winners"][k] for k in ("PD_M", "PD_R")}}
            print(f"\n{bits} bits ({len(nums)} fresh sealed numbers)")
            for track in TRACKS:
                rec = row[track]
                print(f"  Track {track}: final winner {rec['final_winner']} {({k: round(v, 3) if isinstance(v, float) else v for k, v in rec['final_genes'].items() if k in ('kc','bc','mc','tc','lc')})}; "
                      f"budgets round 1 {rec['budgets_round1']} -> final {rec['budgets_final']}")
                for name, r in rec["rows"].items():
                    extra = f"; ruint gate (info) {r['ruint_gate_info']['gate']}" if track == "M" else ""
                    print(f"    {name:38s} {r['track_fitness']:.4f} [{r['ci'][0]:.4f}, {r['ci'][1]:.4f}] (" + " / ".join(f"{v:.3f}" for v in r["scores"].values())
                          + f"; binds {r['binding'][:4]}) gate {r['gate']}{extra}")
                for k, pp in rec["pairs"].items():
                    print(f"    {k}: track {pp['track']['log2']:+.3f} [{pp['track']['ci'][0]:+.3f}, {pp['track']['ci'][1]:+.3f}]  "
                          + "  ".join(f"{Pn[:4]} {pp[Pn]['log2']:+.3f}" for Pn in PR3))
            for lab, v in pdc.items():
                print(f"  {lab}: PD_M {v['PD_M']:.3f} [{v['PD_M_ci'][0]:.3f}, {v['PD_M_ci'][1]:.3f}]  PD_R {v['PD_R']:.3f} [{v['PD_R_ci'][0]:.3f}, {v['PD_R_ci'][1]:.3f}]  official M/R {v['official_M_over_R']:.3f}")
            r1p = out["sizes"][bits]["round1_sealed_9400000"]
            print(f"  round 1 as recorded (9400000 numbers): PD_M {r1p['PD_M']:.3f}  PD_R {r1p['PD_R']:.3f}")
        json.dump(out, open("sizescale_r2_sealed.json", "w"), indent=1, default=float)
