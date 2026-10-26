"""kc / lc bound round, both tracks, p-1-inclusive budgets (NOTES.md, "kc / lc bound round";
protocol and predictions written before this script ran).

  python3 sizescale3.py tune        -> sizescale_k_tune.json    (kc 1-64, lc 1.0-2.5; step-1 joint budgets)
  python3 sizescale3.py resolve     -> sizescale_k_budgets.json (every cell re-solved once with its new frozen
                                                                  genome; Track M at 72 retuned and re-solved,
                                                                  at most two re-solves in all)
  python3 sizescale3.py sealed      -> sizescale_k_sealed.json  (fresh numbers 9420000 + 100 pb + bits; rows
                                                                  (c), (c+p), (d); PD_M, PD_R)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random
import numpy as np
import oracle
import partition as P
import stopping as ST
import sizescale as SS
import sizescale2 as S2
import pm1check as C

PR3 = P.PRICINGS
SIZES, TRACKS = SS.SIZES, SS.TRACKS
BOUNDS = {"kc": (1, 64), "bc": (0.3, 3.0), "mc": (0.01, 12.0), "tc": (1.0, 3.5), "lc": (1.0, 2.5)}
B = 10000
OBJ = {"R": "R", "M": "montgomery"}

def bound_hits(pt):
    return [f"{g} {pt[g]:.4g} (bounds {lo}-{hi})" for g, (lo, hi) in BOUNDS.items() if pt[g] <= lo * 1.1 or pt[g] >= hi * 0.9]

def pipeline(qsg, rho_b, pm1_B, ecm_b):
    pm = dict(P.PRE["pm1"], B=int(pm1_B), ob=2 * int(pm1_B)) if pm1_B else dict(P.PRE["pm1"], ob=0)
    return [dict(P.PRE["td"], ob=0), dict(P.PRE["rho"], ob=rho_b), pm, dict(P.PRE["ecm"], ob=ecm_b), qsg]

def step1_budgets(bits, track):
    j = json.load(open("pm1check.json"))[str(bits)][track][OBJ[track]]["joint"]
    return j["rho"], j["pm1_B"], j["ecm"]

def steps(a, b, octave=False):
    if a == 0 or b == 0:
        return 0 if a == b else None
    return round((1 if octave else 8) * abs(math.log2(a) - math.log2(b)))

def moved(new, old):
    st = {"rho": steps(new[0], old[0]), "pm1_B": steps(new[1], old[1], True), "ecm": steps(new[2], old[2])}
    return st, any(v is None or v > 1 for v in st.values())

def final_cell(bits, track):
    return json.load(open("sizescale_r2_sealed.json"))["sizes"][str(bits)]["tracks"][track]

STAGES = ("td", "rho", "pm1", "ecm", "qs")

def catches(genome, nums, band):
    """Per band, how many numbers each stage solved (lampcore's winning-stage index)."""
    rs = S2.run_many(genome, nums, P.QS_CAP, inst=True)
    out = {}
    for x, pb in zip(rs, band):
        st = STAGES[x[4]] if x[1] is not None else "miss"
        out.setdefault(int(pb), {}).setdefault(st, 0)
        out[int(pb)][st] += 1
    return out

def tune_cell(bits, track, bud, prev_genes):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    bp = SS.pop(bits, 24, 9300000)
    nums = [t for v in bp.values() for t in v]
    oracle.check(nums)
    _, ref = SS.costs([SS.OLD], nums)
    def fit(pt):
        miss, c = SS.costs(pipeline(SS.qsg(pt), *bud), nums)
        return 1e9 if miss else SS.track_fit(c, ref, track)
    base = {"old genes": fit(SS.OLD), "current final": fit(prev_genes)}
    runs = []
    for seed in SS.SEEDS:
        sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=SS.TRIALS // 10, multivariate=True)
        study = optuna.create_study(sampler=sampler)
        def objective(t):
            pt = {"kc": t.suggest_int("kc", 1, 64), "bc": t.suggest_float("bc", 0.3, 3.0),
                  "mc": t.suggest_float("mc", 0.01, 12.0, log=True), "tc": t.suggest_float("tc", 1.0, 3.5),
                  "lc": t.suggest_float("lc", 1.0, 2.5)}
            return fit(pt)
        study.optimize(objective, n_trials=SS.TRIALS)
        runs.append({"seed": seed, "best": study.best_params, "fitness": study.best_value, "bound_hits": bound_hits(study.best_params)})
    best = min(runs, key=lambda r: r["fitness"])
    rec = {"budgets": list(bud), "baselines": base, "runs": runs, "frozen": best["best"], "frozen_seed": best["seed"],
           "frozen_fitness": best["fitness"], "frozen_bound_hits": bound_hits(best["best"])}
    print(f"Track {track}, {bits} bits (rho {bud[0]}, p-1 B {bud[1]}, ECM {bud[2]}): old genes {base['old genes']:.4f}, "
          f"current final {base['current final']:.4f}", flush=True)
    for r in runs:
        b = r["best"]
        print(f"   seed {r['seed']}: {r['fitness']:.4f}  kc {b['kc']}, bc {b['bc']:.3f}, mc {b['mc']:.4f}, tc {b['tc']:.3f}, lc {b['lc']:.3f}"
              + (f"  BOUND: {'; '.join(r['bound_hits'])}" if r["bound_hits"] else ""), flush=True)
    print(f"   frozen: seed {best['seed']}", flush=True)
    return rec

def resolve_cell(bits, track, genes, workers):
    rows = SS.corrected_map_rows(bits)
    nums = S2.map_nums(bits)
    pmap = json.load(open("pm1check_map.json"))[str(bits)]
    assert [r["N"] for r in rows] == [str(t[0]) for t in nums] == pmap["N"]
    d = C.solve([dict(r) for r in rows], nums, SS.qsg(genes), pmap, workers, OBJ[track])
    d.pop("_F"), d.pop("_egrid")
    j = d["joint"]
    return (j["rho"], j["pm1_B"], j["ecm"]), d

if __name__ == "__main__":
    mode = ARGS[0]
    workers = int(ARGS[1]) if len(ARGS) > 1 else 8
    if mode == "tune":
        out = {}
        for track in TRACKS:
            out[track] = {}
            for bits in SIZES:
                out[track][bits] = tune_cell(bits, track, step1_budgets(bits, track), final_cell(bits, track)["final_genes"])
        json.dump(out, open("sizescale_k_tune.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "resolve":
        tune = json.load(open("sizescale_k_tune.json"))
        out = {"pipelines": {}, "genes": {}, "detail": {}, "moves": {}, "m72": {}}
        for bits in SIZES:
            for k in out:
                if k != "m72":
                    out[k][bits] = {}
            for track in TRACKS:
                g = tune[track][str(bits)]["frozen"]
                prev = tuple(tune[track][str(bits)]["budgets"])
                bud, d = resolve_cell(bits, track, g, workers)
                st, mv = moved(bud, prev)
                out["pipelines"][bits][track], out["genes"][bits][track], out["detail"][bits][track] = list(bud), g, d
                out["moves"][bits][track] = {"steps": st, "moved_more_than_one": mv, "previous": list(prev)}
                print(f"{bits} Track {track}: re-solve 1 (rho {bud[0]}, p-1 B {bud[1]}, ECM {bud[2]}) fitness {d['joint']['fitness']:.4f}; "
                      f"tuning budgets {prev}; steps {st}" + ("  MOVED > 1 STEP" if mv else "  settled"), flush=True)
        # Track M at 72: retune and re-solve while unsettled, at most two re-solves in all
        bud, prev, g = tuple(out["pipelines"][72]["M"]), tuple(tune["M"]["72"]["budgets"]), out["genes"][72]["M"]
        hist = [{"resolve": 1, "budgets": list(bud), "genes": g, "steps": out["moves"][72]["M"]["steps"]}]
        settled = not out["moves"][72]["M"]["moved_more_than_one"]
        if not settled:
            print("\nTrack M at 72: retune in re-solve 1's budgets", flush=True)
            rec = tune_cell(72, "M", bud, g)
            g2 = rec["frozen"]
            bud2, d2 = resolve_cell(72, "M", g2, workers)
            st, mv = moved(bud2, bud)
            hist.append({"resolve": 2, "retune": rec, "budgets": list(bud2), "genes": g2, "steps": st, "detail": d2})
            settled = not mv
            out["pipelines"][72]["M"], out["genes"][72]["M"] = list(bud2), g2
            print(f"72 Track M: re-solve 2 (rho {bud2[0]}, p-1 B {bud2[1]}, ECM {bud2[2]}) fitness {d2['joint']['fitness']:.4f}; "
                  f"steps from re-solve 1 {st}" + ("  MOVED > 1 STEP (limit reached)" if mv else "  settled"), flush=True)
        out["m72"] = {"history": hist, "settled": settled, "resolves": len(hist)}
        print(f"Track M at 72: {'settled' if settled else 'NOT settled at the limit'} after {len(hist)} re-solve(s)")
        json.dump(out, open("sizescale_k_budgets.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "sealed":
        kb = json.load(open("sizescale_k_budgets.json"))
        new = {tr: {f"{tr}-k@{b}": SS.qsg(kb["genes"][str(b)][tr]) for b in SIZES} for tr in TRACKS}
        r2 = json.load(open("sizescale_r2_sealed.json"))
        out = {"sizes": {}}
        for bits in SIZES:
            bp = SS.pop(bits, P.PER_BAND, 9420000)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            band = np.array([pb for pb, v in bp.items() for _ in v])
            groups = [np.flatnonzero(band == pb) for pb in bp]
            refs = {"corrected": SS.costs([SS.OLD], nums)[1], "frozen": SS.costs([SS.FROZEN_REF], nums)[1]}
            R_ = refs["corrected"]
            rng = random.Random(2026)
            idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(B)]
            def tf(c, track, i=None):
                if i is None:
                    return SS.track_fit(c, R_, track)
                return SS.track_fit({Pn: c[Pn][i] for Pn in PR3}, {Pn: R_[Pn][i] for Pn in PR3}, track)
            def gate(c, prs):
                ub = lb = 0.0
                for Pn in prs:
                    for gi in groups:
                        r2_ = random.Random(2026)
                        vals = []
                        for _ in range(2000):
                            i = gi[[r2_.randrange(len(gi)) for _ in range(len(gi))]]
                            vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
                        lo, hi = ST.q(vals)
                        ub, lb = max(ub, hi), max(lb, lo)
                return ("FAIL" if lb > ST.GATE else ("PASS" if ub <= ST.GATE else "BORDERLINE")), ub, lb
            row, Cs = {}, {}
            for track in TRACKS:
                fc = final_cell(bits, track)
                fg, (fr, fe) = fc["final_genes"], fc["budgets_final"]
                bd = tuple(kb["pipelines"][str(bits)][track])
                cands = dict(new[track]); cands["current final"] = fg; cands["old genes"], cands["new genes"] = SS.OLD, SS.NEW
                Cd = {g: SS.costs(pipeline(q_, *bd), nums) for g, q_ in cands.items()}
                wg = min(Cd, key=lambda g: 1e9 if Cd[g][0] else tf(Cd[g][1], track))
                rows = {"(c) current final, final pipeline": (fg, (fr, 0, fe)),
                        "(c+p) current final, step-1 p-1 budgets": (fg, step1_budgets(bits, track)),
                        "(d) new winner, new budgets": (cands[wg], bd)}
                rec = {"new_winner": wg, "new_genes": cands[wg], "budgets": {k: list(v[1]) for k, v in rows.items()},
                       "candidates": {g: (None if Cd[g][0] else tf(Cd[g][1], track)) for g in Cd}, "rows": {}}
                C_ = {}
                for name, (g, bud) in rows.items():
                    miss, c = Cd[wg] if name.startswith("(d)") else SS.costs(pipeline(g, *bud), nums)
                    C_[name] = c
                    gt = gate(c, PR3 if track == "R" else ("montgomery",))
                    r = {"track_fitness": tf(c, track), "ci": ST.q([tf(c, track, i) for i in idxs]),
                         "scores": {Pn: float(c[Pn].mean() / R_[Pn].mean()) for Pn in PR3},
                         "scores_frozen_ref": {Pn: float(c[Pn].mean() / refs["frozen"][Pn].mean()) for Pn in PR3},
                         "misses": miss, "gate": "FAIL" if miss else gt[0], "gate_upper": gt[1], "gate_lower": gt[2]}
                    r["binding"] = max(r["scores"], key=r["scores"].get)
                    r["catches_per_band"] = catches(pipeline(g, *bud), nums, band)
                    if track == "M":
                        rg = gate(c, ("ruint",))
                        r["ruint_gate_info"] = {"gate": rg[0], "upper": rg[1], "lower": rg[2]}
                    rec["rows"][name] = r
                ks = list(rows)
                pairs = {}
                for a, b in ((ks[1], ks[0]), (ks[2], ks[1]), (ks[2], ks[0])):
                    ca, cb = C_[a], C_[b]
                    pp = {"track": {"log2": math.log2(tf(ca, track) / tf(cb, track)),
                                    "ci": ST.q([math.log2(tf(ca, track, i) / tf(cb, track, i)) for i in idxs])}}
                    for Pn in PR3:
                        pp[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()),
                                  "ci": ST.q([math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs])}
                    pairs[f"{a.split()[0]} vs {b.split()[0]}"] = pp
                rec["pairs"] = pairs
                row[track], Cs[track] = rec, C_
            pdc = {}
            for lab, rn in (("(c)", ks[0]), ("(c+p)", ks[1]), ("(d)", ks[2])):
                cR, cM = Cs["R"][rn], Cs["M"][rn]
                pdc[lab] = {"PD_M": float(cR["montgomery"].mean() / cM["montgomery"].mean()),
                            "PD_M_ci": ST.q([cR["montgomery"][i].mean() / cM["montgomery"][i].mean() for i in idxs]),
                            "PD_R": float(cM["ruint"].mean() / cR["ruint"].mean()),
                            "PD_R_ci": ST.q([cM["ruint"][i].mean() / cR["ruint"][i].mean() for i in idxs]),
                            "official_M_over_R": float(cM["official"].mean() / cR["official"].mean())}
            fr9410 = r2["sizes"][str(bits)]["cross_pricing"]["final (c rows)"]
            out["sizes"][bits] = {"tracks": row, "cross_pricing": pdc, "final_round_9410000": {k: fr9410[k] for k in ("PD_M", "PD_R")}}
            print(f"\n{bits} bits ({len(nums)} fresh sealed numbers)")
            for track in TRACKS:
                rec = row[track]
                print(f"  Track {track}: new winner {rec['new_winner']} {({k: round(v, 3) if isinstance(v, float) else v for k, v in rec['new_genes'].items() if k in ('kc','bc','mc','tc','lc')})}")
                print("    candidates: " + ", ".join(f"{g} {v:.4f}" if v is not None else f"{g} MISS" for g, v in rec["candidates"].items()))
                for name, r in rec["rows"].items():
                    extra = f"; ruint gate (info) {r['ruint_gate_info']['gate']}" if track == "M" else ""
                    print(f"    {name:42s} {rec['budgets'][name]} {r['track_fitness']:.4f} [{r['ci'][0]:.4f}, {r['ci'][1]:.4f}] ("
                          + " / ".join(f"{v:.3f}" for v in r["scores"].values()) + f"; binds {r['binding'][:4]}) gate {r['gate']}{extra}"
                          + (f" MISSES {r['misses']}" if r["misses"] else ""))
                for name, r in rec["rows"].items():
                    print(f"    catches {name.split()[0]:6s} " + "  ".join(f"{pb}: " + ",".join(f"{st} {n}" for st, n in sorted(v.items()))
                                                                 for pb, v in sorted(r["catches_per_band"].items())))
                for k, pp in rec["pairs"].items():
                    print(f"    {k}: track {pp['track']['log2']:+.4f} [{pp['track']['ci'][0]:+.4f}, {pp['track']['ci'][1]:+.4f}]  "
                          + "  ".join(f"{Pn[:4]} {pp[Pn]['log2']:+.4f} [{pp[Pn]['ci'][0]:+.3f}, {pp[Pn]['ci'][1]:+.3f}]" for Pn in PR3))
            for lab, v in pdc.items():
                print(f"  {lab}: PD_M {v['PD_M']:.3f} [{v['PD_M_ci'][0]:.3f}, {v['PD_M_ci'][1]:.3f}]  PD_R {v['PD_R']:.3f} "
                      f"[{v['PD_R_ci'][0]:.3f}, {v['PD_R_ci'][1]:.3f}]  official M/R {v['official_M_over_R']:.3f}")
            f9 = out["sizes"][bits]["final_round_9410000"]
            print(f"  final round as recorded (9410000 numbers): PD_M {f9['PD_M']:.3f}  PD_R {f9['PD_R']:.3f}")
        json.dump(out, open("sizescale_k_sealed.json", "w"), indent=1, default=float)
