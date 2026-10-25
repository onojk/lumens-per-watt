"""Size-relative op budgets (NOTES.md, "Size-relative op budgets: cost model and predictions";
written before this script). Pre-stage budgets become shares of the expected qs cost at N's
bit length: ob_s(N) = snap(s_s * Q(bits(N))), snap = nearest 1/8-octave grid point
(partition.FINE). td and pm1 stay at A's 0; the final qs is qs + lc 1.4 (A's genes).

  python3 size_budgets.py curve      -> size_curve.json     (Q(bits) from fresh balanced tuning numbers)
  python3 size_budgets.py map [w]    -> size_map.json       (pre-stage + qs maps at 72 and 96 bits, fresh seeds)
  python3 size_budgets.py eval       -> size_budgets.json   (tuning on the 84-bit map, verdict at 72 / 96, identity at 84)

curve: semiprimes_pq(bits, 60, 9100000 + bits), bits 60..100 step 4; qs + lc 1.4 alone, lampcore,
cap 2^28; least squares log2(mean official ops) = a + b bits + c bits^2.
map: seeds 9000000 + 100 pb + bits; 72: bands 16-32 unbalanced, 36 balanced; 96: 16-42 unbalanced,
48 balanced; 80 per band. Pre-stages alone in Python with spending records (partition.run_alone,
cap 2^21); qs + lc 1.4 alone in lampcore --types; parity: Python qs per-type counts = lampcore's on
4 numbers per band.
eval: three rules (NOTES addendum): primary (dedicated curve), sensitivity (calibration-run curve, 54-84
quadratic), theory (L(N) ratio); (1) best (s_rho, s_ECM) on the 84-bit partition map (grid + 1/8-octave refinement, fitness
(c)); (2) at 72 and 96: share genome vs A's absolute budgets, both run directly in lampcore
--types on the map's numbers; the map's composed official cost must equal the direct run's on
every number; paired bootstrap (numbers within bands, 10,000, random.Random(2026)); ACCEPT gate;
(3) identity at 84 on fresh numbers (seeds 9000000 + 100 pb + 84): share genome = A op for op;
(4) information only: each size's hindsight best budgets on its own map.
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random
from multiprocessing import Pool
import numpy as np
import optypes, oracle
import partition as P
from fastlamps import semiprimes_pq, semiprimes_unbalanced, run_many

PR3 = P.PRICINGS
QS = P.QS_VARIANTS["qs + lc 1.4"]
A_B = {"rho": 5793, "ecm": 32768}
SIZES = {72: (16, 20, 24, 28, 32, 36), 96: (16, 20, 24, 28, 32, 36, 42, 48), 84: P.BANDS}
B = 10000
GATE = 1.5

def pop(bits, base=9000000):
    out = {}
    for pb in SIZES[bits]:
        seed = base + 100 * pb + bits
        out[pb] = semiprimes_pq(bits, P.PER_BAND, seed) if 2 * pb >= bits else semiprimes_unbalanced(bits, pb, P.PER_BAND, seed)
    return out

def snap(x):
    g = [b for b in P.FINE if b > 0]
    return min(g, key=lambda b: abs(math.log2(b) - math.log2(x)))

def genome(rho, ecm):
    return [dict(P.PRE["td"], ob=0), dict(P.PRE["rho"], ob=rho), dict(P.PRE["pm1"], ob=0), dict(P.PRE["ecm"], ob=ecm), QS]

def q(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]

def pre_job(args):
    bits, pb, N = args
    out = {"N": str(N), "band": pb}
    for name, st in P.PRE.items():
        out[name] = P.run_alone(st, N, P.PRE_CAP, [b for b in P.FINE if b > 0] if name != "pm1" else [])
    return out

def py_qs_job(N):
    r = P.run_alone(QS, N, P.QS_CAP, [])
    return r["ops"], {k: v for k, v in r["per_type"].items() if v}

if __name__ == "__main__":
    mode = ARGS[0]
    if mode == "curve":
        rows = {}
        for bits in range(60, 101, 4):
            nums = semiprimes_pq(bits, 60, 9100000 + bits)
            oracle.check(nums)
            rs = run_many([QS], nums, P.QS_CAP)
            assert all(r[0] is not None for r in rs), bits
            rows[bits] = float(np.mean([r[0] for r in rs]))
        x = np.array(sorted(rows), dtype=float)
        y = np.log2([rows[int(b)] for b in x])
        c2, c1, c0 = np.polyfit(x, y, 2)
        fit = {int(b): float(c0 + c1 * b + c2 * b * b) for b in x}
        json.dump({"mean_ops": rows, "coef": [c0, c1, c2], "fit_log2": fit}, open("size_curve.json", "w"), indent=1)
        print("bits  log2 mean qs ops  fit  resid")
        for b in sorted(rows):
            print(f"  {b}: {math.log2(rows[b]):.3f}  {fit[b]:.3f}  {math.log2(rows[b]) - fit[b]:+.3f}")
        print(f"coef a {c0:.4f} b {c1:.5f} c {c2:.7f}")
        sys.exit(0)

    if mode == "map":
        workers = int(ARGS[1]) if len(ARGS) > 1 else 8
        out = {"fine": P.FINE, "seeds": "9000000 + 100 pb + bits", "maps": {}}
        with Pool(workers) as pool:
            for bits in (72, 96):
                bp = pop(bits)
                nums = [t for v in bp.values() for t in v]
                oracle.check(nums)
                rows = pool.map(pre_job, [(bits, pb, N) for pb, v in bp.items() for N, _, _ in v], chunksize=2)
                rs = run_many([QS], nums, P.QS_CAP, types=True)
                for r, x, (N, _, _) in zip(rows, rs, nums):
                    ok = x[1] is not None and 1 < int(x[1]) < N
                    assert ok, ("qs alone missed", bits, N)
                    r["qs + lc 1.4"] = {"T": x[0], "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
                sample = [v[i][0] for v in bp.values() for i in range(4)]
                py = pool.map(py_qs_job, sample)
                lc = {str(N): r["qs + lc 1.4"] for N, r in zip([t[0] for t in nums], rows)}
                bad = [N for N, (ops, pt) in zip(sample, py) if ops != lc[str(N)]["ops"] or pt != lc[str(N)]["per_type"]]
                print(f"{bits}: parity (Python qs per-type vs lampcore --types) {len(sample) - len(bad)}/{len(sample)}")
                if bad:
                    sys.exit(f"parity failure at {bits} bits: blocker")
                out["maps"][bits] = {"bands": list(bp), "rows": rows}
                for pb in bp:
                    rr = [r for r in rows if r["band"] == pb]
                    print(f"  {pb}", {s: f"{sum(1 for r in rr if r[s]['T'] is not None)}/{len(rr)}" for s in P.PRE},
                          f"qs log2 mean {math.log2(np.mean([r['qs + lc 1.4']['ops'] for r in rr])):.2f}")
        json.dump(out, open("size_map.json", "w"))
        sys.exit(0)

    # ---- eval ----
    PRc = P.prices()
    pr = optypes.prices()
    cur = json.load(open("size_curve.json"))
    c0, c1, c2 = cur["coef"]
    cal = json.load(open("calibrate_counts.json"))["qs + lc 1.4"]
    xs = [54, 60, 66, 72, 78, 84]
    e2, e1, e0 = np.polyfit(xs, [math.log2(np.mean([r["ops"] for r in cal[str(b)]])) for b in xs], 2)
    Lf = lambda b: math.sqrt(b * math.log(2) * math.log(b * math.log(2)))
    RULES = {"primary": lambda b: 2 ** (c1 * (b - 84) + c2 * (b * b - 84 * 84)),
             "sensitivity": lambda b: 2 ** (e1 * (b - 84) + e2 * (b * b - 84 * 84)),
             "theory": lambda b: math.exp(Lf(b) - Lf(84))}
    res = {"curve_primary": [c0, c1, c2], "curve_sensitivity": [e0, e1, e2],
           "ratios": {k: {b: f(b) for b in (72, 96)} for k, f in RULES.items()}}

    # (1) tuning on the 84-bit partition map: td 0, pm1 0, fixed order
    M84 = P.Map(json.load(open("partition_map.json"))["rows"], "qs + lc 1.4", PRc)
    f84 = lambda r, e: M84.fitness((0, r, 0, e))[0]
    best = min(((f84(r, e), r, e) for r in P.COARSE for e in P.COARSE))
    _, r, e = best
    while True:
        moved = False
        for i in (0, 1):
            for o in P.FINE:
                t = (o, e) if i == 0 else (r, o)
                if f84(*t) < f84(r, e) - 1e-12:
                    (r, e), moved = t, True
        if not moved:
            break
    tuned = {"rho": r, "ecm": e}
    res["tuned_84"] = {"budgets": tuned, "fitness": f84(r, e), "fitness_A": f84(A_B["rho"], A_B["ecm"])}
    print("ratios: " + "  ".join(f"{k} 72/84 {f(72):.4f} 96/84 {f(96):.4f}" for k, f in RULES.items()))
    print(f"(1) best on the 84-bit map: rho {r}, ecm {e}, fitness {f84(r, e):.4f} (A {f84(A_B['rho'], A_B['ecm']):.4f})")
    ob = lambda rule, bits: {s_: (0 if tuned[s_] == 0 else snap(tuned[s_] * RULES[rule](bits))) for s_ in tuned}

    def run_costs(gen, nums):
        rs = run_many(gen, nums, P.QS_CAP, types=True)
        miss = sum(1 for x, (N, _, _) in zip(rs, nums) if not (x[1] is not None and 1 < int(x[1]) < N))
        return miss, [x[0] for x in rs], {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in rs]) for Pn in PR3}

    # (3) identity at 84, fresh numbers
    bp84 = pop(84)
    n84 = [t for v in bp84.values() for t in v]
    oracle.check(n84)
    rsA = run_many(genome(A_B["rho"], A_B["ecm"]), n84, P.QS_CAP, types=True)
    res["identity_84"] = {}
    for rule in RULES:
        s84 = ob(rule, 84)
        rsS = run_many(genome(s84["rho"], s84["ecm"]), n84, P.QS_CAP, types=True)
        same = sum(1 for a, b in zip(rsA, rsS) if a[0] == b[0] and a[4] == b[4])
        res["identity_84"][rule] = {"budgets": s84, "identical": same, "of": len(n84)}
        print(f"(3) identity at 84 bits, {rule}: budgets {s84}; per-number counts identical to A on {same}/{len(n84)}")

    # (2) verdict at 72 and 96
    maps = json.load(open("size_map.json"))["maps"]
    res["sizes"] = {}
    for bits in (72, 96):
        bp = pop(bits)
        nums = [t for v in bp.values() for t in v]
        oracle.check(nums)
        rows = maps[str(bits)]["rows"]
        assert [r_["N"] for r_ in rows] == [str(t[0]) for t in nums]
        M = P.Map(rows, "qs + lc 1.4", PRc)
        groups = [np.flatnonzero(M.band == pb) for pb in bp]
        ref_l = {Pn: np.array([optypes.cost(x[4], Pn, pr) for x in run_many([QS], nums, P.QS_CAP, types=True)]) for Pn in PR3}
        G = {"A": (A_B["rho"], A_B["ecm"])}
        G.update({rule: (ob(rule, bits)["rho"], ob(rule, bits)["ecm"]) for rule in RULES})
        C, xcheck = {}, {}
        for g, (rb, eb) in G.items():
            miss, ops, c = run_costs(genome(rb, eb), nums)
            composed = M.costs((0, rb, 0, eb), "official")
            xcheck[g] = int(sum(1 for a, b in zip(ops, composed) if a is not None and abs(a - b) < 0.5))
            C[g] = (miss, c)
        allx = np.arange(len(nums))
        sc = lambda c, i, Pn: c[Pn][i].mean() / ref_l[Pn][i].mean()
        fit = lambda c, i: max(sc(c, i, Pn) for Pn in PR3)
        rng = random.Random(2026)
        idxs = [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(B)]
        row = {"budgets": G, "map_xcheck_official_identical": xcheck, "n": len(nums),
               "qs_map_vs_lampcore_ref_identical": bool(all(np.allclose(M.qs[Pn], ref_l[Pn]) for Pn in PR3)), "genomes": {}, "pairs": {}}
        for g in G:
            miss, c = C[g]
            per_band = {Pn: {pb: float(sc(c, gi, Pn)) for pb, gi in zip(bp, groups)} for Pn in PR3}
            worst = max((v, Pn, pb) for Pn in PR3 for pb, v in per_band[Pn].items())
            row["genomes"][g] = {"fitness": fit(c, allx), "scores": {Pn: sc(c, allx, Pn) for Pn in PR3}, "per_band": per_band,
                                 "misses": miss, "gate_worst": worst, "gate_pass": worst[0] <= GATE and not miss}
        for a, b in (("primary", "A"), ("theory", "A"), ("sensitivity", "A"), ("theory", "primary"), ("sensitivity", "primary")):
            ca, cb = C[a][1], C[b][1]
            row["pairs"][f"{a} / {b}"] = {
                "ratio": fit(ca, allx) / fit(cb, allx), "log2": math.log2(fit(ca, allx) / fit(cb, allx)),
                "ci": q([math.log2(fit(ca, i) / fit(cb, i)) for i in idxs]),
                "by_pricing": {Pn: {"log2": math.log2(sc(ca, allx, Pn) / sc(cb, allx, Pn)),
                                    "ci": q([math.log2(sc(ca, i, Pn) / sc(cb, i, Pn)) for i in idxs])} for Pn in PR3}}
        # (4) hindsight: best budgets on this size's own map (information only)
        fM = lambda r_, e_: M.fitness((0, r_, 0, e_))[0]
        hb = min(((fM(r_, e_), r_, e_) for r_ in P.COARSE for e_ in P.COARSE))
        _, hr, he = hb
        while True:
            moved = False
            for i in (0, 1):
                for o in P.FINE:
                    t = (o, he) if i == 0 else (hr, o)
                    if fM(*t) < fM(hr, he) - 1e-12:
                        (hr, he), moved = t, True
            if not moved:
                break
        row["hindsight"] = {"budgets": {"rho": hr, "ecm": he}, "map_fitness": fM(hr, he),
                            "map_fitness_by_genome": {g: fM(*G[g]) for g in G}}
        res["sizes"][bits] = row
        print(f"\n{bits} bits: {len(nums)} numbers, bands {list(bp)}; budgets (rho, ecm): " + "  ".join(f"{g} {v}" for g, v in G.items()))
        print("  map cross-check (composed official = direct lampcore): " + "  ".join(f"{g} {v}/{len(nums)}" for g, v in xcheck.items())
              + f"; map qs = lampcore qs: {row['qs_map_vs_lampcore_ref_identical']}")
        for g in G:
            x = row["genomes"][g]
            print(f"  {g:11s}: fitness {x['fitness']:.3f} (" + ", ".join(f"{Pn} {v:.3f}" for Pn, v in x["scores"].items())
                  + f"); misses {x['misses']}; gate {'PASS' if x['gate_pass'] else 'FAIL'} (worst {x['gate_worst'][0]:.3f}, band {x['gate_worst'][2]}, {x['gate_worst'][1]})")
            for Pn in PR3:
                print(f"     {Pn:10s} per band: " + "  ".join(f"{pb}: {v:.3f}" for pb, v in x["per_band"][Pn].items()))
        for k, o in row["pairs"].items():
            print(f"  {k:22s} robust x{o['ratio']:.3f}, log2 {o['log2']:+.3f} [{o['ci'][0]:+.3f}, {o['ci'][1]:+.3f}];  "
                  + "  ".join(f"{Pn[:4]} {v['log2']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}]" for Pn, v in o["by_pricing"].items()))
        h = row["hindsight"]
        print(f"  (info) hindsight best on own map: rho {hr}, ecm {he}, map fitness {h['map_fitness']:.3f}; map fitness by genome: "
              + "  ".join(f"{g} {v:.3f}" for g, v in h["map_fitness_by_genome"].items()))
    json.dump(res, open("size_budgets.json", "w"), indent=1, default=float)
