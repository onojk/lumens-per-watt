"""Per-stage budgets by size from a stopping rule (NOTES.md, "Per-stage budgets by size from a
stopping rule: cost model and predictions"; written before this script).

Rule, per pre-stage in order (rho, then ECM; td and pm1 off), on the numbers still unsolved:
hazard h(t) per window of the map's grid, value h * Q_P(bits), cost c_{s,P} (the stage's price per
official op over the alive numbers); budget_P = upper edge of the last window with value >= cost
(0 = off); budget = min over pricings. Q_P = frozen dedicated curve (official) x r_P (qs's price
per official op on the map). Primary windows: 1/8 octave (partition.FINE); SENSITIVITY: half octave.

  python3 stopping.py derive     -> stopping_derive.json   (the rule on the 72/84/96 maps vs hindsight)
  python3 stopping.py map [w]    -> stopping_map.json      (fresh 78/90-bit maps, seeds 9200000 + 100 pb + bits)
  python3 stopping.py derive2    -> stopping_derive2.json  (addendum: exhaustive robust optimum + backward induction, 72/84/96)
  python3 stopping.py test       -> stopping_test.json     (addendum genomes at 78/90; per-band gate intervals; two references)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random
from multiprocessing import Pool
import numpy as np
import optypes, oracle
import partition as P
import size_budgets as SB
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many

PR3 = P.PRICINGS
QS = SB.QS
A_B = SB.A_B
B = 10000
GATE = 1.5
TEST = {78: (16, 20, 24, 28, 32, 36, 39), 90: (16, 20, 24, 28, 32, 36, 42, 45)}
NEIGH = {78: (72, 84), 90: (84, 96)}
EDGES = {"eighth": [0] + [b for b in P.FINE if b > 0], "half": [0] + [b for b in P.FINE if b > 0][::4]}
PRc = P.prices()
cur = json.load(open("size_curve.json"))["coef"]
Q = lambda bits: 2 ** (cur[0] + cur[1] * bits + cur[2] * bits * bits)
Lf = lambda b: math.sqrt(b * math.log(2) * math.log(b * math.log(2)))

def load_maps():
    M = {84: P.Map(json.load(open("partition_map.json"))["rows"], "qs + lc 1.4", PRc)}
    for bits, v in json.load(open("size_map.json"))["maps"].items():
        M[int(bits)] = P.Map(v["rows"], "qs + lc 1.4", PRc)
    return M

def r_P(M):
    return {Pn: M.qs[Pn].mean() / M.qs["official"].mean() for Pn in PR3}

def hazard(M, s, alive0, edges):
    """Per window k: h_k (per op), and c_{k,P} (mean price per official op over the alive numbers)."""
    T = M.T[s]
    h, c = [], {Pn: [] for Pn in PR3}
    for a, b in zip(edges[:-1], edges[1:]):
        alive = alive0 & (T > a)
        n = int(alive.sum())
        h.append(0.0 if n == 0 else float((alive & (T <= b)).sum()) / n / (b - a))
        for Pn in PR3:
            c[Pn].append(float(M.pib[s][Pn][alive].mean()) if n else 1.0)
    return np.array(h), {Pn: np.array(v) for Pn, v in c.items()}

def budget_from(h, c, QP, edges):
    per = {}
    for Pn in PR3:
        ok = np.flatnonzero(h * QP[Pn] >= c[Pn])
        per[Pn] = int(edges[ok[-1] + 1]) if len(ok) else 0
    return min(per.values()), per

def derive(maps, bits, edges):
    """maps: one map (derivation at its own size) or two neighbours (hazards averaged). Returns
    budgets {rho, ecm} and the per-pricing detail."""
    rr = [r_P(M) for M in maps]
    if len(maps) == 1:
        rP = rr[0]
    else:
        (b0, b1) = NEIGH[bits]
        w = (bits - b0) / (b1 - b0)
        rP = {Pn: (1 - w) * rr[0][Pn] + w * rr[1][Pn] for Pn in PR3}
    QP = {Pn: Q(bits) * rP[Pn] for Pn in PR3}
    alive = [np.ones(M.n, dtype=bool) for M in maps]
    out, detail = {}, {}
    for s in ("rho", "ecm"):
        hs = [hazard(M, s, a, edges) for M, a in zip(maps, alive)]
        h = np.mean([x[0] for x in hs], axis=0)
        c = {Pn: np.mean([x[1][Pn] for x in hs], axis=0) for Pn in PR3}
        b, per = budget_from(h, c, QP, edges)
        out[s], detail[s] = b, per
        alive = [a & ~(M.T[s] <= b) for M, a in zip(maps, alive)] if b else alive
    return out, {"per_pricing": detail, "Q_P": QP, "r_P": rP}

def hindsight(M):
    fM = lambda r_, e_: M.fitness((0, r_, 0, e_))[0]
    _, hr, he = min(((fM(r_, e_), r_, e_) for r_ in P.COARSE for e_ in P.COARSE))
    while True:
        moved = False
        for i in (0, 1):
            for o in P.FINE:
                t = (o, he) if i == 0 else (hr, o)
                if fM(*t) < fM(hr, he) - 1e-12:
                    (hr, he), moved = t, True
        if not moved:
            return {"rho": hr, "ecm": he}, fM(hr, he)

def steps(a, b):
    """Distance in 1/8-octave grid steps (None if exactly one of them is 0)."""
    if a == 0 or b == 0:
        return 0 if a == b else None
    return round(8 * abs(math.log2(a) - math.log2(b)))

def pop(bits):
    out = {}
    for pb in TEST[bits]:
        seed = 9200000 + 100 * pb + bits
        out[pb] = semiprimes_pq(bits, P.PER_BAND, seed) if 2 * pb >= bits else semiprimes_unbalanced(bits, pb, P.PER_BAND, seed)
    return out

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]


# ---- addendum: exhaustive robust optimum and backward induction (exact composition) ----
NEW_QS = {"t": "qs", "kc": 4, "bc": 0.8993889783377338, "mc": 0.7340990893362095,
          "tc": 1.1044621542694246, "lc": 1.6612269841697611}
GRID = P.FINE

def mats(objs):
    """objs: [(Map, {P: per-number qs scale})]. Returns S[P][r, e] = summed composed cost of
    (rho at GRID[r], ECM at GRID[e], qs) over all numbers, and the summed qs cost per pricing."""
    S, qsum = {}, {}
    for Pn in PR3:
        tot, qt = 0.0, 0.0
        for M, scale in objs:
            qsv = M.qs[Pn] * scale[Pn]
            qt += qsv.sum()
            rc, al, ec, un = [], [], [], []
            for b in GRID:
                t = M.stage_terms("rho", b, Pn)
                rc.append(0.0 if t is None else float(t[1].sum()))
                al.append(np.ones(M.n) if t is None else (~t[0]).astype(float))
                t = M.stage_terms("ecm", b, Pn)
                ec.append(np.zeros(M.n) if t is None else t[1])
                un.append(qsv if t is None else np.where(t[0], 0.0, qsv))
            A, E, U = np.array(al), np.array(ec), np.array(un)
            tot = tot + np.array(rc)[:, None] + A @ E.T + A @ U.T
        S[Pn], qsum[Pn] = tot, qt
    return S, qsum

def robust_opt(S, qsum):
    F = np.max([S[Pn] / qsum[Pn] for Pn in PR3], axis=0)
    r, e = np.unravel_index(np.argmin(F), F.shape)
    return {"rho": GRID[r], "ecm": GRID[e]}, float(F[r, e]), F

def backward(S, qsum, F):
    per = {}
    for Pn in PR3:
        eP = np.argmin(S[Pn], axis=1)                      # e_P(r), last stage first
        rP = int(np.argmin(S[Pn][np.arange(len(GRID)), eP]))
        per[Pn] = {"rho": GRID[rP], "ecm": GRID[eP[rP]]}
    rc = min(GRID.index(v["rho"]) for v in per.values())
    ec = min(int(np.argmin(S[Pn][rc])) for Pn in PR3)
    cons = {"rho": GRID[rc], "ecm": GRID[ec]}
    return per, cons, float(F[rc, ec])

def transferred(maps, bits):
    b0, b1 = NEIGH[bits]
    w = (bits - b0) / (b1 - b0)
    r0, r1 = r_P(maps[b0]), r_P(maps[b1])
    rt = {Pn: (1 - w) * r0[Pn] + w * r1[Pn] for Pn in PR3}
    objs = []
    for src, rs in ((b0, r0), (b1, r1)):
        objs.append((maps[src], {Pn: Q(bits) * rt[Pn] / (Q(src) * rs[Pn]) for Pn in PR3}))
    return objs

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "derive":
        maps = load_maps()
        out = {}
        for bits in (72, 84, 96):
            hb, hf = hindsight(maps[bits])
            row = {"hindsight": hb, "hindsight_map_fitness": hf}
            for wname, edges in EDGES.items():
                b, d = derive([maps[bits]], bits, edges)
                row[wname] = {"budgets": b, "detail": d, "map_fitness": maps[bits].fitness((0, b["rho"], 0, b["ecm"]))[0],
                              "steps_from_hindsight": {s: steps(b[s], hb[s]) for s in b}}
            out[bits] = row
            print(f"{bits} bits: Q {Q(bits):.0f}; hindsight rho {hb['rho']}, ecm {hb['ecm']} (map fitness {hf:.4f})")
            for wname in EDGES:
                x = row[wname]
                print(f"  {wname:6s} windows: rho {x['budgets']['rho']}, ecm {x['budgets']['ecm']} (map fitness {x['map_fitness']:.4f}); "
                      f"steps from hindsight {x['steps_from_hindsight']}; per pricing " +
                      "; ".join(f"{s}: " + ", ".join(f"{Pn[:4]} {v}" for Pn, v in x['detail']['per_pricing'][s].items()) for s in ("rho", "ecm")))
        json.dump(out, open("stopping_derive.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "derive2":
        maps = load_maps()
        out = {}
        one = lambda M: {Pn: 1.0 for Pn in PR3}
        for bits in (72, 84, 96):
            M = maps[bits]
            S, qsum = mats([(M, one(M))])
            ro, rf, F = robust_opt(S, qsum)
            per, cons, cf = backward(S, qsum, F)
            v4 = P.optimize(M, np.ones(M.n, dtype=bool))
            f4 = M.fitness(v4)[0]
            out[bits] = {"robust": ro, "robust_fitness": rf, "bi_per_pricing": per, "bi_conservative": cons, "bi_fitness": cf,
                         "steps": {st: steps(cons[st], ro[st]) for st in ro},
                         "four_stage": {"vec": v4, "fitness": f4}}
            print(f"{bits} bits: robust grid optimum rho {ro['rho']}, ecm {ro['ecm']} (fitness {rf:.4f}); "
                  f"BI conservative rho {cons['rho']}, ecm {cons['ecm']} (fitness {cf:.4f}); steps {out[bits]['steps']}")
            print("   BI per pricing: " + "; ".join(f"{Pn}: rho {v['rho']}, ecm {v['ecm']}" for Pn, v in per.items()))
            print(f"   (info) 4-stage robust optimum (td, rho, pm1, ecm) {v4}, fitness {f4:.4f}")
        json.dump(out, open("stopping_derive2.json", "w"), indent=1, default=float)
        sys.exit(0)

    if mode == "map":
        workers = int(ARGS[1]) if len(ARGS) > 1 else 8
        out = {"fine": P.FINE, "seeds": "9200000 + 100 pb + bits", "maps": {}}
        with Pool(workers) as pool:
            for bits in (78, 90):
                bp = pop(bits)
                nums = [t for v in bp.values() for t in v]
                oracle.check(nums)
                rows = pool.map(SB.pre_job, [(bits, pb, N) for pb, v in bp.items() for N, _, _ in v], chunksize=2)
                rs = run_many([QS], nums, P.QS_CAP, types=True)
                for r, x, (N, _, _) in zip(rows, rs, nums):
                    assert x[1] is not None and 1 < int(x[1]) < N, ("qs alone missed", bits, N)
                    r["qs + lc 1.4"] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
                sample = [v[i][0] for v in bp.values() for i in range(4)]
                py = pool.map(SB.py_qs_job, sample)
                lc = {r["N"]: r["qs + lc 1.4"] for r in rows}
                bad = [N for N, (ops, pt) in zip(sample, py) if ops != lc[str(N)]["ops"] or pt != lc[str(N)]["per_type"]]
                print(f"{bits}: parity (Python qs per-type vs lampcore --types) {len(sample) - len(bad)}/{len(sample)}")
                if bad:
                    sys.exit(f"parity failure at {bits} bits: blocker")
                out["maps"][bits] = {"bands": list(bp), "rows": rows}
                for pb in bp:
                    rr = [r for r in rows if r["band"] == pb]
                    print(f"  {pb}", {s: f"{sum(1 for r in rr if r[s]['T'] is not None)}/{len(rr)}" for s in P.PRE},
                          f"qs log2 mean {math.log2(np.mean([r['qs + lc 1.4']['ops'] for r in rr])):.2f}")
        json.dump(out, open("stopping_map.json", "w"))
        sys.exit(0)

    # ---- test ----
    pr = optypes.prices()
    maps = load_maps()
    tmaps = json.load(open("stopping_map.json"))["maps"]
    res = {}
    for bits in (78, 90):
        b0, b1 = NEIGH[bits]
        rule, det = derive([maps[b0], maps[b1]], bits, EDGES["eighth"])
        rule_half, _ = derive([maps[b0], maps[b1]], bits, EDGES["half"])
        lr = math.exp(Lf(bits) - Lf(84))
        St, qt = mats(transferred(maps, bits))
        tro, trf, Ft = robust_opt(St, qt)
        tper, tcons, tcf = backward(St, qt, Ft)
        G = {"TRANSFER": (tro["rho"], tro["ecm"]), "BI-conservative": (tcons["rho"], tcons["ecm"]),
             "Q-RULE": (rule["rho"], rule["ecm"]), "A": (A_B["rho"], A_B["ecm"]),
             "theory": (SB.snap(A_B["rho"] * lr), SB.snap(A_B["ecm"] * lr)),
             "Q-RULE half-octave (info)": (rule_half["rho"], rule_half["ecm"])}
        bp = pop(bits)
        nums = [t for v in bp.values() for t in v]
        oracle.check(nums)
        rows = tmaps[str(bits)]["rows"]
        assert [r_["N"] for r_ in rows] == [str(t[0]) for t in nums]
        M = P.Map(rows, "qs + lc 1.4", PRc)
        groups = [np.flatnonzero(M.band == pb) for pb in bp]
        REFS = {}
        for rname, rg in (("qs + lc 1.4", QS), ("new qs", NEW_QS)):
            rr_ = run_many([rg], nums, P.QS_CAP, types=True)
            assert all(x[1] is not None and 1 < int(x[1]) < N for x, (N, _, _) in zip(rr_, nums)), rname
            REFS[rname] = {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rr_]) for Pn in PR3}
        rng = random.Random(2026)
        idxs = [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(B)]
        C, xcheck = {}, {}
        for g, (rb, eb) in G.items():
            rs = run_many(SB.genome(rb, eb), nums, P.QS_CAP, types=True)
            miss = sum(1 for x, (N, _, _) in zip(rs, nums) if not (x[1] is not None and 1 < int(x[1]) < N))
            composed = M.costs((0, rb, 0, eb), "official")
            xcheck[g] = int(sum(1 for x, cpd in zip(rs, composed) if x[0] is not None and abs(x[0] - cpd) < 0.5))
            C[g] = (miss, {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3})
        allx = np.arange(len(nums))
        row = {"budgets": G, "rule_detail": det, "theory_ratio": lr, "xcheck": xcheck, "genomes": {}, "pairs": {},
               "transfer": {"robust": tro, "robust_fitness_transferred": trf, "bi_per_pricing": tper, "bi_conservative": tcons,
                            "steps": {st: steps(tcons[st], tro[st]) for st in tro}},
               "secondary": {}}
        def evaluate(ref):
            sc = lambda c, i, Pn: c[Pn][i].mean() / ref[Pn][i].mean()
            fit = lambda c, i: max(sc(c, i, Pn) for Pn in PR3)
            gs = {}
            for g in G:
                miss, c = C[g]
                bands = {}
                for Pn in PR3:
                    bands[Pn] = {}
                    for pb, gi in zip(bp, groups):
                        r2 = random.Random(2026)
                        vals = []
                        for _ in range(B):
                            i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                            vals.append(c[Pn][i].mean() / ref[Pn][i].mean())
                        bands[Pn][pb] = {"point": float(sc(c, gi, Pn)), "ci": q(vals)}
                cells = [(v["point"], v["ci"], Pn, pb) for Pn in PR3 for pb, v in bands[Pn].items()]
                if miss or any(ci[0] > GATE for _, ci, _, _ in cells):
                    gate = "FAIL"
                elif all(ci[1] <= GATE for _, ci, _, _ in cells):
                    gate = "PASS"
                else:
                    gate = "BORDERLINE"
                gs[g] = {"fitness": fit(c, allx), "scores": {Pn: sc(c, allx, Pn) for Pn in PR3}, "misses": miss,
                         "bands": bands, "gate": gate, "worst": max(cells, key=lambda x: x[0]),
                         "worst_upper": max(cells, key=lambda x: x[1][1])}
            pairs = {}
            for a_, b_ in (("TRANSFER", "A"), ("TRANSFER", "theory"), ("TRANSFER", "BI-conservative"),
                           ("Q-RULE", "A"), ("Q-RULE", "theory"), ("theory", "A")):
                ca, cb = C[a_][1], C[b_][1]
                pairs[f"{a_} / {b_}"] = {
                    "ratio": fit(ca, allx) / fit(cb, allx), "log2": math.log2(fit(ca, allx) / fit(cb, allx)),
                    "ci": q([math.log2(fit(ca, i) / fit(cb, i)) for i in idxs]),
                    "by_pricing": {Pn: {"log2": math.log2(sc(ca, allx, Pn) / sc(cb, allx, Pn)),
                                        "ci": q([math.log2(sc(ca, i, Pn) / sc(cb, i, Pn)) for i in idxs])} for Pn in PR3}}
            return gs, pairs
        row["genomes"], row["pairs"] = evaluate(REFS["qs + lc 1.4"])
        row["secondary"], row["pairs_secondary"] = evaluate(REFS["new qs"])
        hb, hf = hindsight(M)
        row["hindsight"] = {"budgets": hb, "map_fitness": hf, "map_fitness_by_genome": {g: M.fitness((0, G[g][0], 0, G[g][1]))[0] for g in G}}
        res[bits] = row
        print(f"\n{bits} bits: {len(nums)} numbers, bands {list(bp)}; Q {Q(bits):.0f}; L ratio {lr:.4f}")
        print("  budgets (rho, ecm): " + "  ".join(f"{g} {v}" for g, v in G.items()))
        print("  rule per pricing: " + "; ".join(f"{s}: " + ", ".join(f"{Pn[:4]} {v}" for Pn, v in det['per_pricing'][s].items()) for s in ("rho", "ecm")))
        print("  map cross-check (composed official = direct): " + "  ".join(f"{g} {v}/{len(nums)}" for g, v in xcheck.items()))
        print(f"  transferred maps: robust optimum rho {tro['rho']}, ecm {tro['ecm']} (fitness {trf:.4f}); BI conservative {tcons}; steps {row['transfer']['steps']}; "
              "BI per pricing " + "; ".join(f"{Pn[:4]} {v['rho']}/{v['ecm']}" for Pn, v in tper.items()))
        for g in G:
            x, y = row["genomes"][g], row["secondary"][g]
            w, wu = x["worst"], x["worst_upper"]
            print(f"  {g:26s}: fitness {x['fitness']:.3f} (" + ", ".join(f"{Pn[:4]} {v:.3f}" for Pn, v in x["scores"].items())
                  + f"); misses {x['misses']}; gate {x['gate']} (worst point {w[0]:.3f} [{w[1][0]:.3f}, {w[1][1]:.3f}] band {w[3]} {w[2]}; "
                  f"highest upper {wu[1][1]:.3f} band {wu[3]} {wu[2]}) | vs new qs: fitness {y['fitness']:.3f} ("
                  + ", ".join(f"{Pn[:4]} {v:.3f}" for Pn, v in y["scores"].items()) + f"), gate {y['gate']}")
            for Pn in PR3:
                print(f"     {Pn:10s} " + "  ".join(f"{pb}: {v['point']:.3f}" for pb, v in x["bands"][Pn].items()))
        for k, o in row["pairs"].items():
            o2 = row["pairs_secondary"][k]
            print(f"  {k:26s} robust x{o['ratio']:.3f}, log2 {o['log2']:+.3f} [{o['ci'][0]:+.3f}, {o['ci'][1]:+.3f}];  "
                  + "  ".join(f"{Pn[:4]} {v['log2']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}]" for Pn, v in o["by_pricing"].items())
                  + f" | vs new qs: log2 {o2['log2']:+.3f} [{o2['ci'][0]:+.3f}, {o2['ci'][1]:+.3f}]")
        h = row["hindsight"]
        print(f"  (info) hindsight on own map: rho {hb['rho']}, ecm {hb['ecm']}, map fitness {hf:.3f}; map fitness: "
              + "  ".join(f"{g} {v:.3f}" for g, v in h["map_fitness_by_genome"].items()))
    json.dump(res, open("stopping_test.json", "w"), indent=1, default=float)
