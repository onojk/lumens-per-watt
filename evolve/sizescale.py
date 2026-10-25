"""qs-gene size-scaling test on the corrected card (NOTES.md, "qs-gene size-scaling test on the
corrected card: design and predictions"; written before this script ran).

Card: final qs with a_mode = on_demand, sort_charge = 1. Pipeline per size: rho at that size's
rho-only robust budget (72: 1,579; 84: 5,793; 96: 12,634 from the corrected re-solve; 54 from
its own map, mode map54), then qs. Fitness (c): robust ratio against qs + lc 1.4's genes alone
under the corrected card, on the same numbers; misses score 1e9.

  python3 sizescale.py map54 [w]  -> sizescale_map54.json   (54-bit map, seeds 9500000 + 100 pb + 54; rho budget)
  python3 sizescale.py tune       -> sizescale_tune.json    (TPE, tpe-tuned settings, seeds 0-3, 200 trials per size;
                                                              tuning numbers 24 per band, seeds 9300000 + 100 pb + bits)
  python3 sizescale.py sealed     -> sizescale_sealed.json  (frozen genomes x sizes, 80 per band, seeds 9400000 + 100 pb + bits)
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

def pipeline(qsg, rho_b):
    return [dict(P.PRE["td"], ob=0), dict(P.PRE["rho"], ob=rho_b), dict(P.PRE["pm1"], ob=0), dict(P.PRE["ecm"], ob=0), qsg]

def costs(genome, nums):
    rs = run_many(genome, nums, P.QS_CAP, types=True)
    miss = sum(1 for x, (N, _, _) in zip(rs, nums) if not (x[1] is not None and 1 < int(x[1]) < N))
    return miss, {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3}

def qsg(pt):
    return dict({"t": "qs", "kc": int(pt["kc"]), "bc": pt["bc"], "mc": pt["mc"], "tc": pt["tc"], "lc": pt["lc"]}, **CARD)

def rho_budget(bits):
    return RHO_B[bits] if bits in RHO_B else json.load(open("sizescale_map54.json"))["rho_budget"]

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

    if mode == "tune":
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        out = {}
        for bits in SIZES:
            bp = pop(bits, 24, 9300000)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            rb = rho_budget(bits)
            _, ref = costs([OLD], nums)
            def fit(pt):
                miss, c = costs(pipeline(qsg(pt), rb), nums)
                return 1e9 if miss else max(c[Pn].mean() / ref[Pn].mean() for Pn in PR3)
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
            out[bits] = {"rho_budget": rb, "n_tuning": len(nums), "baselines": base, "runs": runs, "frozen": best["best"],
                         "frozen_seed": best["seed"], "frozen_fitness": best["fitness"]}
            print(f"{bits} bits (rho {rb}, {len(nums)} tuning numbers): old genes {base['old genes']:.4f}, new genes {base['new genes']:.4f}")
            for r in runs:
                b = r["best"]
                print(f"   seed {r['seed']}: {r['fitness']:.4f}  kc {b['kc']}, bc {b['bc']:.3f}, mc {b['mc']:.3f}, tc {b['tc']:.3f}, lc {b['lc']:.3f}")
            print(f"   frozen: seed {best['seed']}")
        json.dump(out, open("sizescale_tune.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "sealed":
        tune = json.load(open("sizescale_tune.json"))
        G = {f"tuned@{b}": qsg(tune[str(b)]["frozen"]) for b in SIZES}
        G["old genes"], G["new genes"] = OLD, NEW
        out = {}
        for bits in SIZES:
            bp = pop(bits, P.PER_BAND, 9400000)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            band = np.array([pb for pb, v in bp.items() for _ in v])
            groups = [np.flatnonzero(band == pb) for pb in bp]
            rb = rho_budget(bits)
            refs = {"corrected": costs([OLD], nums)[1], "frozen": costs([FROZEN_REF], nums)[1]}
            C = {g: costs(pipeline(q_, rb), nums) for g, q_ in G.items()}
            rng = random.Random(2026)
            idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(B)]
            allx = np.arange(len(nums))
            row = {"rho_budget": rb, "n": len(nums), "genomes": {}, "pairs": {}}
            for rname, R_ in refs.items():
                sc = lambda c, i, Pn: c[Pn][i].mean() / R_[Pn][i].mean()
                for g, (miss, c) in C.items():
                    bands = {Pn: {} for Pn in PR3}
                    for Pn in PR3:
                        for pb, gi in zip(bp, groups):
                            r2 = random.Random(2026)
                            vals = []
                            for _ in range(2000):
                                i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                                vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
                            bands[Pn][pb] = {"ratio": float(sc(c, gi, Pn)), "ci": ST.q(vals)}
                    ub = max(v["ci"][1] for Pn in PR3 for v in bands[Pn].values())
                    lb = max(v["ci"][0] for Pn in PR3 for v in bands[Pn].values())
                    gate = "FAIL" if (lb > ST.GATE or miss) else ("PASS" if ub <= ST.GATE else "BORDERLINE")
                    scores = {Pn: float(sc(c, allx, Pn)) for Pn in PR3}
                    fvals = [max(sc(c, i, Pn) for Pn in PR3) for i in idxs]
                    row["genomes"][f"{g} | ref {rname}"] = {"fitness": max(scores.values()), "ci": ST.q(fvals), "scores": scores,
                                                            "binding": max(scores, key=scores.get), "misses": miss, "gate": gate,
                                                            "gate_worst_upper": ub, "gate_worst_lower": lb}
            R_ = refs["corrected"]
            sc = lambda c, i, Pn: c[Pn][i].mean() / R_[Pn][i].mean()
            for g in G:
                if g == "old genes":
                    continue
                ca, cb = C[g][1], C["old genes"][1]
                pp = {}
                for Pn in PR3:
                    vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs]
                    pp[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": ST.q(vals)}
                rv = [math.log2(max(sc(ca, i, Pn) for Pn in PR3) / max(sc(cb, i, Pn) for Pn in PR3)) for i in idxs]
                pp["robust"] = {"log2": math.log2(max(sc(ca, allx, Pn) for Pn in PR3) / max(sc(cb, allx, Pn) for Pn in PR3)), "ci": ST.q(rv)}
                lo = all(pp[Pn]["ci"][1] < 0 for Pn in PR3); hi = all(pp[Pn]["ci"][0] > 0 for Pn in PR3)
                pp["call"] = g if lo else ("old genes" if hi else "undecided")
                row["pairs"][f"{g} vs old genes"] = pp
            out[bits] = row
            print(f"\n{bits} bits ({len(nums)} sealed numbers; rho {rb}; final qs corrected)")
            for k, x in row["genomes"].items():
                print(f"  {k:32s} fitness {x['fitness']:.4f} [{x['ci'][0]:.4f}, {x['ci'][1]:.4f}] (" + " / ".join(f"{v:.3f}" for v in x["scores"].values())
                      + f"; binds {x['binding'][:4]})  misses {x['misses']}  gate {x['gate']} (upper {x['gate_worst_upper']:.3f}, lower {x['gate_worst_lower']:.3f})")
            for k, pp in row["pairs"].items():
                print(f"  {k:24s} robust {pp['robust']['log2']:+.3f} [{pp['robust']['ci'][0]:+.3f}, {pp['robust']['ci'][1]:+.3f}]  "
                      + "  ".join(f"{Pn[:4]} {pp[Pn]['log2']:+.3f} [{pp[Pn]['ci'][0]:+.3f},{pp[Pn]['ci'][1]:+.3f}]" for Pn in PR3) + f"  call {pp['call']}")
        # trend: per gene, the four seeds' best values per size
        trend = {}
        for gname in ("kc", "bc", "mc", "tc", "lc"):
            vals = {b: [r["best"][gname] for r in tune[str(b)]["runs"]] for b in SIZES}
            med = [statistics.median(vals[b]) for b in SIZES]
            mono_up = all(a < b for a, b in zip(med, med[1:])); mono_dn = all(a > b for a, b in zip(med, med[1:]))
            sep = max(vals[96]) < min(vals[54]) or min(vals[96]) > max(vals[54])
            pts = [(b, v) for b in SIZES for v in vals[b]]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            rk = lambda a: [sorted(a).index(v) for v in a]
            rho_s = float(np.corrcoef(rk(xs), rk(ys))[0, 1])
            trend[gname] = {"per_size": vals, "medians": med, "monotone": "up" if mono_up else ("down" if mono_dn else "no"),
                            "ends_separated": sep, "spearman": rho_s}
            print(f"trend {gname}: medians " + ", ".join(f"{b}: {m:.3f}" for b, m in zip(SIZES, med))
                  + f"; monotone {trend[gname]['monotone']}; 54 vs 96 seed ranges separated {sep}; Spearman {rho_s:+.2f}")
        out["trend"] = trend
        json.dump(out, open("sizescale_sealed.json", "w"), indent=1, default=float)
