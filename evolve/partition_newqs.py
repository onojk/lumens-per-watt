"""Partition map re-run with the new qs genes (NOTES.md, "After Run 8: (1) partition map with
the new qs genes"; predictions written there first). Map only, tuning numbers.

The map's pre-stage records do not depend on the final qs, so partition_map.json is reused.
New: the new qs alone (kc 4, bc 0.8994, mc 0.7341, tc 1.1045, lc 1.6612; Run 8 mixed-qs TPE,
seed 77) on the same 560 tuning numbers, cap 2^28, per-type counts from lampcore --types.
Parity first: lampcore's per-type counts for qs + lc 1.4 must equal the map's stored Python
counts on every number (a mismatch stops the script).

Then, as partition_orders.py does for qs + lc 1.4, with the new qs as the final stage: for
each of the 24 orders, the exact optimum over the map's budget grid and its 1/8-octave
refinement, under fitness (c) against qs + lc 1.4 alone (the Run 8 reference); every order
against the best by the paired stratified bootstrap (10,000, random.Random(2026)). Reported
beside: A's budgets with the new qs (the comparison point), the best against it (paired),
fitness against the new qs alone, per-band ratios.

  python3 partition_newqs.py  -> partition_newqs.json, stdout
"""
import sys
sys.argv[1:] = []
import itertools, json, math, random
import numpy as np
import partition as P
import oracle
from fastlamps import run_many

NEW_QS = {"t": "qs", "kc": 4, "bc": 0.8993889783377338, "mc": 0.7340990893362095,
          "tc": 1.1044621542694246, "lc": 1.6612269841697611}
NAMES = ("td", "rho", "pm1", "ecm")
A_B = {"td": 0, "rho": 5793, "pm1": 0, "ecm": 32768}

data = json.load(open("partition_map.json"))
assert data["fine"] == P.FINE
rows = data["rows"]
pop = P.population(P.TUNING)
byN = {str(N): (N, p, q) for pb in P.BANDS for N, p, q in pop[pb]}
nums = [byN[r["N"]] for r in rows]
oracle.check(nums)

# parity: lampcore --types vs the map's Python per-type counts, qs + lc 1.4
old = run_many([P.QS_VARIANTS["qs + lc 1.4"]], nums, P.QS_CAP, types=True)
bad = 0
for r, x in zip(rows, old):
    py = r["qs + lc 1.4"]
    lc = {k: v for k, v in x[4].items() if v}
    if x[0] != py["ops"] or lc != {k: v for k, v in py["per_type"].items() if v}:
        bad += 1
print(f"parity (lampcore --types vs map's Python counts, qs + lc 1.4): {len(rows) - bad}/{len(rows)} identical")
if bad:
    sys.exit("parity failure: blocker")

new = run_many([NEW_QS], nums, P.QS_CAP, types=True)
misses = 0
for r, x in zip(rows, new):
    ok = x[1] is not None and 1 < int(x[1]) < int(r["N"])
    misses += not ok
    r["new qs"] = {"T": x[0] if ok else None, "ops": x[0], "per_type": {k: v for k, v in x[4].items() if v}}
print(f"new qs alone: {misses} misses of {len(rows)}")
if misses:
    sys.exit("new qs missed on a tuning number: the map cannot compose its cost")

PR = P.prices()
MN = P.Map(rows, "new qs", PR)          # stage terms and the new qs's final-stage costs
MO = P.Map(rows, "qs + lc 1.4", PR)     # the reference: qs + lc 1.4 alone
BANDS_IDX = [np.flatnonzero(MN.band == pb) for pb in P.BANDS]

def costs(order, b, Pn):
    total = np.zeros(MN.n)
    alive = np.ones(MN.n, dtype=bool)
    for s in order:
        t = MN.stage_terms(s, b[s], Pn)
        if t is None:
            continue
        succ, c = t
        total += np.where(alive, c, 0.0)
        alive &= ~succ
    return total + np.where(alive, MN.qs[Pn], 0.0)

def scores(order, b, ref, idx=slice(None)):
    return {Pn: costs(order, b, Pn)[idx].mean() / ref.qs[Pn][idx].mean() for Pn in P.PRICINGS}

def fitness(order, b, ref=MO):
    return max(scores(order, b, ref).values())

def optimize(order):
    best = None
    for bt in P.COARSE:
        for br in P.COARSE:
            for bp in P.PM1_OPTS:
                for be in P.COARSE:
                    b = {"td": bt, "rho": br, "pm1": bp, "ecm": be}
                    f = fitness(order, b)
                    if best is None or f < best[0]:
                        best = (f, b)
    grid_best = best
    b = dict(best[1])
    while True:
        moved = False
        for s in NAMES:
            for o in (P.PM1_OPTS if s == "pm1" else P.FINE):
                t = dict(b); t[s] = o
                if fitness(order, t) < fitness(order, b) - 1e-12:
                    b, moved = t, True
        if not moved:
            return fitness(order, b), b, grid_best

def boot(order_b, b_b, order_a, b_a):
    """95% interval of log2(fitness b / fitness a), numbers resampled within bands."""
    ca = {Pn: costs(order_a, b_a, Pn) for Pn in P.PRICINGS}
    cb = {Pn: costs(order_b, b_b, Pn) for Pn in P.PRICINGS}
    rng = random.Random(2026)
    vals = []
    for _ in range(10000):
        idx = np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in BANDS_IDX])
        f = lambda c: max(c[Pn][idx].mean() / MO.qs[Pn][idx].mean() for Pn in P.PRICINGS)
        vals.append(math.log2(f(cb) / f(ca)))
    vals.sort()
    return vals[250], vals[9749]

if __name__ == "__main__":
    fmt = lambda b: f"td {b['td']:>7}  rho {b['rho']:>7}  pm1 {'full' if b['pm1'] else 0:>4}  ecm {b['ecm']:>7}"
    fA = fitness(NAMES, A_B)
    fA_old = max({Pn: MO.costs((0, 5793, 0, 32768), Pn).mean() / MO.qs[Pn].mean() for Pn in P.PRICINGS}.values())
    newalone = {Pn: MN.qs[Pn].mean() / MO.qs[Pn].mean() for Pn in P.PRICINGS}
    print(f"\nfitness (c) against qs + lc 1.4 alone, map (560 tuning numbers):")
    print(f"  A with qs + lc 1.4 (partition study): {fA_old:.4f}")
    print(f"  new qs alone: {max(newalone.values()):.4f} ({', '.join(f'{k} {v:.3f}' for k, v in newalone.items())})")
    sA = scores(NAMES, A_B, MO)
    print(f"  A's budgets with the new qs: {fA:.4f} ({', '.join(f'{k} {v:.3f}' for k, v in sA.items())})")
    res = {}
    for order in itertools.permutations(NAMES):
        f, b, (gf, gb) = optimize(order)
        res[" -> ".join(order)] = {"fitness": f, "budgets": b, "grid_fitness": gf, "grid_budgets": gb}
    ranked = sorted(res.items(), key=lambda kv: kv[1]["fitness"])
    best_k, best_v = ranked[0]
    best_o = tuple(best_k.split(" -> "))
    print("\nall 24 orders, new qs final: grid optimum | refined | refined vs best, log2 [paired 95%]")
    for k, v in ranked:
        o = tuple(k.split(" -> "))
        lo, hi = (0.0, 0.0) if k == best_k else boot(o, v["budgets"], best_o, best_v["budgets"])
        v["vs_best_log2"] = math.log2(v["fitness"] / best_v["fitness"]); v["vs_best_ci95"] = [lo, hi]
        print(f"  {k:28s} grid {v['grid_fitness']:.4f} ({fmt(v['grid_budgets'])}) | refined {v['fitness']:.4f} ({fmt(v['budgets'])}) | "
              f"{v['vs_best_log2']:+.4f} [{lo:+.4f}, {hi:+.4f}]")
    matters = [k for k, v in res.items() if v["vs_best_ci95"][0] > 0]
    print(f"\ncard order: {'MATTERS' if matters else 'does not matter'} ({len(matters)} of 24 orders have an interval above 0)")
    fixed = res[" -> ".join(NAMES)]
    out = {"new_qs": NEW_QS, "misses": misses, "A_old_fitness": fA_old, "new_qs_alone": newalone, "A_budgets_new_qs": {"fitness": fA, "scores": sA},
           "orders": res, "best": best_k, "card_order_matters": bool(matters)}
    for label, o, v in (("fixed order td -> rho -> pm1 -> ecm", NAMES, fixed), (f"best order {best_k}", best_o, best_v)):
        lo, hi = boot(o, v["budgets"], NAMES, A_B)
        s = scores(o, v["budgets"], MO)
        own = max(scores(o, v["budgets"], MN).values())
        bands = {Pn: {pb: float(costs(o, v["budgets"], Pn)[g].mean() / MO.qs[Pn][g].mean()) for pb, g in zip(P.BANDS, BANDS_IDX)} for Pn in P.PRICINGS}
        print(f"\n{label}: {fmt(v['budgets'])}  fitness {v['fitness']:.4f} ({', '.join(f'{k} {x:.3f}' for k, x in s.items())}); against the new qs alone {own:.4f}")
        print(f"  vs A's budgets with the new qs: log2 {math.log2(v['fitness'] / fA):+.4f} [{lo:+.4f}, {hi:+.4f}]")
        for Pn in P.PRICINGS:
            print(f"  per band, {Pn}: " + "  ".join(f"{pb}: {x:.3f}" for pb, x in bands[Pn].items()))
        out[label] = {"budgets": v["budgets"], "fitness": v["fitness"], "scores": s, "vs_new_qs_alone": own,
                      "vs_A_budgets_log2": math.log2(v["fitness"] / fA), "vs_A_budgets_ci95": [lo, hi], "per_band": bands}
    json.dump(out, open("partition_newqs.json", "w"), indent=1)
