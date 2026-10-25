"""Re-solve on the existing maps with the corrected card (NOTES.md, "Re-solve on the existing maps
with the corrected card: plan and predictions"; written before this script ran).

Corrected card: qs + lc 1.4's genes (and N51-0917's at 84) with a_mode = on_demand, sort_charge = 1,
run alone (lampcore --types, cap 2^28) on every map's numbers; pre-stage records unchanged.
Every ratio uses the same card in numerator and denominator. The enumerate column recomputes the
recorded figures from the maps' own qs + lc 1.4 records, as a check.

  python3 resolve.py map     -> resolve.json, stdout   (map-only: per-size optima, BI, A vs B, transfer)
  python3 resolve.py sealed  -> resolve_sealed.json     (only if an optimum moved > 1 grid step:
                                                          stopping.py test's genome runs at 78/90, corrected)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random
import numpy as np
import optypes, oracle
import partition as P
import stopping as ST
import typemix as TM
import size_budgets as SB
from fastlamps import run_many

PR3 = P.PRICINGS
PRc = P.prices()
OLD = dict(P.QS_VARIANTS["qs + lc 1.4"])
N51 = dict(P.QS_VARIANTS["N51-0917's qs"])
CORR = lambda g: dict(g, a_mode="on_demand", sort_charge=1)
SIZES = (72, 78, 84, 90, 96)
A_VEC = (0, 5793, 0, 32768)
one = {Pn: 1.0 for Pn in PR3}

def rows_of(bits):
    src = json.load(open(TM.SRC[bits][0]))
    return (src if bits == 84 else src["maps"][str(bits)])["rows"]

def add_qs(rows, nums, g, name):
    rs = run_many([g], nums, P.QS_CAP, types=True)
    for r, x, (N, _, _) in zip(rows, rs, nums):
        assert x[1] is not None and 1 < int(x[1]) < N, (name, N)
        r[name] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}

def two_stage(objs):
    S, qsum = ST.mats(objs)
    ro, rf, F = ST.robust_opt(S, qsum)
    per, cons, cf = ST.backward(S, qsum, F)
    return {"robust": ro, "robust_fitness": rf, "bi_per_pricing": per, "bi_conservative": cons, "bi_fitness": cf}

def stage_steps(a, b):
    return {s: ST.steps(a[s], b[s]) for s in ("rho", "ecm")}

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "map":
        rows, maps = {}, {"enumerate": {}, "corrected": {}}
        for bits in SIZES:
            nums, _ = TM.load(bits)
            oracle.check(nums)
            rows[bits] = rows_of(bits)
            add_qs(rows[bits], nums, CORR(OLD), "qs corrected")
            if bits == 84:
                add_qs(rows[bits], nums, CORR(N51), "N51 corrected")
            maps["enumerate"][bits] = P.Map(rows[bits], "qs + lc 1.4", PRc)
            maps["corrected"][bits] = P.Map(rows[bits], "qs corrected", PRc)
        out = {"per_size": {}, "allocations": {}, "transfer": {}}
        # 1. per-size two-stage robust optima and backward induction
        print("1. robust grid optimum (rho, ECM; td, pm1 off), fitness against the same card's qs alone")
        for bits in SIZES:
            row = {card: two_stage([(maps[card][bits], one)]) for card in ("enumerate", "corrected")}
            row["steps_corrected_vs_enumerate"] = stage_steps(row["corrected"]["robust"], row["enumerate"]["robust"])
            row["A_budgets_fitness"] = {card: maps[card][bits].fitness(A_VEC)[0] for card in ("enumerate", "corrected")}
            row["A_budgets_scores"] = {card: maps[card][bits].fitness(A_VEC)[1] for card in ("enumerate", "corrected")}
            row["corrected_qs_over_enumerate_qs"] = {Pn: float(maps["corrected"][bits].qs[Pn].mean() / maps["enumerate"][bits].qs[Pn].mean()) for Pn in PR3}
            for card in ("enumerate", "corrected"):
                x, M = row[card], maps[card][bits]
                vo = (0, x["robust"]["rho"], 0, x["robust"]["ecm"])
                so = M.fitness(vo)[1]
                x["binding_optimum"] = max(so, key=so.get)
                sa = row["A_budgets_scores"][card]
                x["binding_A"] = max(sa, key=sa.get)
                x["opt_over_A"] = x["robust_fitness"] / row["A_budgets_fitness"][card]
                bp = x["bi_per_pricing"][x["binding_optimum"]]
                x["bi_binding_equals_robust"] = bp == x["robust"]
            out["per_size"][bits] = row
            for card in ("enumerate", "corrected"):
                x = row[card]
                print(f"  {bits} {card:9s}: rho {x['robust']['rho']:>7}, ecm {x['robust']['ecm']:>7}  fitness {x['robust_fitness']:.4f}; "
                      f"BI ruint rho {x['bi_per_pricing']['ruint']['rho']}, ecm {x['bi_per_pricing']['ruint']['ecm']}; "
                      f"BI conservative rho {x['bi_conservative']['rho']}, ecm {x['bi_conservative']['ecm']} ({x['bi_fitness']:.4f}); "
                      f"A's budgets {row['A_budgets_fitness'][card]:.4f}; optimum / A {x['opt_over_A']:.4f}; binding: optimum {x['binding_optimum']}, A {x['binding_A']}; "
                      f"BI under the binding pricing = robust optimum: {x['bi_binding_equals_robust']}")
            print(f"     steps corrected vs enumerate: {row['steps_corrected_vs_enumerate']}; qs corrected / enumerate: "
                  + " / ".join(f"{v:.3f}" for v in row["corrected_qs_over_enumerate_qs"].values()))
        # 2. allocations A and B at 84 (four-stage optimizer), cross-comparison
        print("\n2. allocations at 84 bits (four-stage optimizer td, rho, pm1, ECM; mixed tuning numbers)")
        r84 = rows[84]
        Ms = {"enumerate": {"A": P.Map(r84, "qs + lc 1.4", PRc), "B": P.Map(r84, "N51-0917's qs", PRc)},
              "corrected": {"A": P.Map(r84, "qs corrected", PRc), "B": P.Map(r84, "N51 corrected", PRc)}}
        allm = np.ones(len(r84), dtype=bool)
        for card, mm in Ms.items():
            res = {}
            for name, M in mm.items():
                vec = P.optimize(M, allm)
                f, sc = M.fitness(vec)
                res[name] = {"budgets": dict(zip(("td", "rho", "pm1", "ecm"), vec)), "fitness_own_ref": f, "scores_own_ref": sc}
            ref = mm["A"].qs
            cross = {}
            for name, M in mm.items():
                vec = tuple(res[name]["budgets"][s] for s in ("td", "rho", "pm1", "ecm"))
                sc = {Pn: float(M.costs(vec, Pn).mean() / ref[Pn].mean()) for Pn in PR3}
                cross[name] = {"scores": sc, "robust": max(sc.values())}
            res["cross_single_reference"] = cross
            res["B_over_A_cross"] = cross["B"]["robust"] / cross["A"]["robust"]
            out["allocations"][card] = res
            bA = max(res['A']['scores_own_ref'], key=res['A']['scores_own_ref'].get); bB = max(res['B']['scores_own_ref'], key=res['B']['scores_own_ref'].get)
            print(f"  {card:9s}: A {res['A']['budgets']} fitness {res['A']['fitness_own_ref']:.4f} (binds {bA});  B {res['B']['budgets']} fitness {res['B']['fitness_own_ref']:.4f} (binds {bB})")
            print(f"             cross (single reference qs + lc 1.4 alone, same card): A {cross['A']['robust']:.4f} ("
                  + " / ".join(f"{v:.3f}" for v in cross["A"]["scores"].values()) + f"), B {cross['B']['robust']:.4f} ("
                  + " / ".join(f"{v:.3f}" for v in cross["B"]["scores"].values()) + f"); B / A {res['B_over_A_cross']:.3f}")
        # 3. transfer test at 78 / 90, map-only
        print("\n3. transfer (neighbouring maps, Q-curve rescaled), scored on the 78 / 90 maps")
        rec = json.load(open("stopping_test.json"))
        for bits in (78, 90):
            res = {}
            for card in ("enumerate", "corrected"):
                tr = two_stage(ST.transferred(maps[card], bits))
                M = maps[card][bits]
                local = out["per_size"][bits][card]["robust"]
                th = rec[str(bits)]["budgets"]["theory"]
                cands = {"TRANSFER": (tr["robust"]["rho"], tr["robust"]["ecm"]), "A": (5793, 32768), "theory": tuple(th),
                         "local optimum": (local["rho"], local["ecm"])}
                scored = {k: {"budgets": v, "fitness": M.fitness((0, v[0], 0, v[1]))[0], "scores": M.fitness((0, v[0], 0, v[1]))[1]} for k, v in cands.items()}
                for k, v in scored.items():
                    v["binding"] = max(v["scores"], key=v["scores"].get)
                    v["over_A"] = v["fitness"] / scored["A"]["fitness"]
                res[card] = {"transfer": tr["robust"], "scored": scored,
                             "transfer_steps_from_local": stage_steps(tr["robust"], local)}
                print(f"  {bits} {card:9s}: TRANSFER rho {tr['robust']['rho']}, ecm {tr['robust']['ecm']} (steps from local {res[card]['transfer_steps_from_local']}); "
                      + "; ".join(f"{k} {v['budgets']} {v['fitness']:.4f} (/A {v['over_A']:.3f}, binds {v['binding'][:4]})" for k, v in scored.items()))
            out["transfer"][bits] = res
        moved = {bits: out["per_size"][bits]["steps_corrected_vs_enumerate"] for bits in SIZES}
        far = {b: s for b, s in moved.items() if any(v is None or v > 1 for v in s.values())}
        out["sealed_rerun_needed"] = bool(far)
        out["moved_more_than_one_step"] = far
        print(f"\nsealed rerun needed (an optimum moved > 1 grid step): {bool(far)} {far}")
        json.dump(out, open("resolve.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "sealed":
        # stopping.py test's design on the 78/90 populations, final qs corrected; references:
        # qs + lc 1.4 corrected alone (primary) and the frozen reference (enumerate) beside it
        res_map = json.load(open("resolve.json"))
        out = {}
        for bits in (78, 90):
            bp = ST.pop(bits)
            nums = [t for v in bp.values() for t in v]
            oracle.check(nums)
            band = np.array([pb for pb, v in bp.items() for _ in v])
            groups = [np.flatnonzero(band == pb) for pb in bp]
            pr = optypes.prices()
            ref = {}
            for rname, g in (("corrected", CORR(OLD)), ("frozen", OLD)):
                rs = run_many([g], nums, P.QS_CAP, types=True)
                ref[rname] = {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3}
            T = res_map["transfer"][str(bits)]
            G = {"TRANSFER corrected": tuple(T["corrected"]["scored"]["TRANSFER"]["budgets"]),
                 "TRANSFER enumerate": tuple(T["enumerate"]["scored"]["TRANSFER"]["budgets"]),
                 "A": (5793, 32768), "theory": tuple(T["corrected"]["scored"]["theory"]["budgets"])}
            C = {}
            for gname, (rb, eb) in G.items():
                genome = SB.genome(rb, eb)[:-1] + [CORR(OLD)]
                rs = run_many(genome, nums, P.QS_CAP, types=True)
                miss = sum(1 for x, (N, _, _) in zip(rs, nums) if not (x[1] is not None and 1 < int(x[1]) < N))
                C[gname] = (miss, {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3})
            rng = random.Random(2026)
            idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(ST.B)]
            allx = np.arange(len(nums))
            row = {"budgets": G, "genomes": {}, "pairs": {}}
            for rname in ("corrected", "frozen"):
                R_ = ref[rname]
                sc = lambda c, i, Pn: c[Pn][i].mean() / R_[Pn][i].mean()
                for gname, (miss, c) in C.items():
                    bands = {Pn: {} for Pn in PR3}
                    for Pn in PR3:
                        for pb, gi in zip(bp, groups):
                            r2 = random.Random(2026)
                            vals = []                  # paired per-band interval
                            for _ in range(2000):
                                i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                                vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
                            bands[Pn][pb] = {"ratio": float(sc(c, gi, Pn)), "ci": ST.q(vals)}
                    ub = max(v["ci"][1] for Pn in PR3 for v in bands[Pn].values())
                    lb = max(v["ci"][0] for Pn in PR3 for v in bands[Pn].values())
                    gate = "FAIL" if (lb > ST.GATE or miss) else ("PASS" if ub <= ST.GATE else "BORDERLINE")
                    fit = max(sc(c, allx, Pn) for Pn in PR3)
                    fvals = [max(sc(c, i, Pn) for Pn in PR3) for i in idxs]
                    row["genomes"][f"{gname} | ref {rname}"] = {"fitness": fit, "ci": ST.q(fvals), "scores": {Pn: float(sc(c, allx, Pn)) for Pn in PR3},
                                                                "misses": miss, "gate": gate, "gate_worst_upper": ub, "gate_worst_lower": lb}
            R_ = ref["corrected"]
            sc = lambda c, i, Pn: c[Pn][i].mean() / R_[Pn][i].mean()
            for a in ("TRANSFER corrected", "TRANSFER enumerate", "theory"):
                ca, cb = C[a][1], C["A"][1]
                pp = {}
                for Pn in PR3:
                    vals = [math.log2(ca[Pn][i].mean() / cb[Pn][i].mean()) for i in idxs]
                    pp[Pn] = {"log2": math.log2(ca[Pn].mean() / cb[Pn].mean()), "ci": ST.q(vals)}
                rv = [math.log2(max(sc(ca, i, Pn) for Pn in PR3) / max(sc(cb, i, Pn) for Pn in PR3)) for i in idxs]
                pp["robust"] = {"log2": math.log2(max(sc(ca, allx, Pn) for Pn in PR3) / max(sc(cb, allx, Pn) for Pn in PR3)), "ci": ST.q(rv)}
                lo = all(pp[Pn]["ci"][1] < 0 for Pn in PR3); hi = all(pp[Pn]["ci"][0] > 0 for Pn in PR3)
                pp["call"] = a if lo else ("A" if hi else "undecided")
                row["pairs"][f"{a} vs A"] = pp
            out[bits] = row
            print(f"\n{bits} bits ({len(nums)} numbers), final qs corrected")
            for k, x in row["genomes"].items():
                print(f"  {k:36s} fitness {x['fitness']:.4f} [{x['ci'][0]:.4f}, {x['ci'][1]:.4f}] (" + " / ".join(f"{v:.3f}" for v in x["scores"].values())
                      + f")  misses {x['misses']}  gate {x['gate']} (upper {x['gate_worst_upper']:.3f}, lower {x['gate_worst_lower']:.3f})")
            for k, pp in row["pairs"].items():
                print(f"  {k:24s} robust {pp['robust']['log2']:+.3f} [{pp['robust']['ci'][0]:+.3f}, {pp['robust']['ci'][1]:+.3f}]  "
                      + "  ".join(f"{Pn[:4]} {pp[Pn]['log2']:+.3f} [{pp[Pn]['ci'][0]:+.3f},{pp[Pn]['ci'][1]:+.3f}]" for Pn in PR3) + f"  call {pp['call']}")
        json.dump(out, open("resolve_sealed.json", "w"), indent=1, default=float)
