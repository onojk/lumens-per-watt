"""Free exhaustive baseline before Run 8 (PLAN.md, Run 8 design; prediction written there
first): with the final qs fixed at qs + lc 1.4, the best budgets for each of the 24 orders of
the four pre-stages, from partition_map.json (tuning numbers), by the partition study's grid
and refinement under fitness (c). The per-number composition runs the stages in the given
order: every lamp computes on N alone (pm1's precheck does not apply at B ~ 2^16.7), so the
order changes only which stage gets each number first.

Reported:
- per order, the exact optimum over the map's budget grid ({0, 2^8..2^20} for td, rho and
  ECM, pm1 {0, full}: 14 x 14 x 14 x 2 = 5,488 combinations, all evaluated), and the value
  after coordinate refinement on the finer 1/8-octave grid (a local search, not exhaustive);
- every order's refined optimum against the best, by the paired stratified bootstrap
  (10,000 resamples within each band, random.Random(2026)) of log2(fitness / best's);
  card order "doesn't matter" only if every order's interval includes 0;
- the landscape: robust fitness over all 24 x 5,488 = 131,712 grid combinations; the share
  at or below the upper end of the best grid point's own 95% bootstrap interval, and the
  spread of budgets among those combinations (a plateau, or an isolated minimum).

  python3 partition_orders.py  -> partition_orders.json, partition_orders.out (stdout)
"""
import sys
sys.argv[1:] = []
import itertools, json, math, random
import numpy as np
import partition as P

rows = json.load(open("partition_map.json"))["rows"]
PR = P.prices()
M = P.Map(rows, "qs + lc 1.4", PR)
NAMES = ("td", "rho", "pm1", "ecm")

def costs(order, b, Pn):
    total = np.zeros(M.n)
    alive = np.ones(M.n, dtype=bool)
    for s in order:
        t = M.stage_terms(s, b[s], Pn)
        if t is None:
            continue
        succ, c = t
        total += np.where(alive, c, 0.0)
        alive &= ~succ
    return total + np.where(alive, M.qs[Pn], 0.0)

def fitness(order, b):
    return max(costs(order, b, Pn).mean() / M.qs[Pn].mean() for Pn in P.PRICINGS)

GRID = []                       # (order, budgets, fitness) for every grid combination

def optimize(order):
    best = None
    for bt in P.COARSE:
        for br in P.COARSE:
            for bp in P.PM1_OPTS:
                for be in P.COARSE:
                    b = {"td": bt, "rho": br, "pm1": bp, "ecm": be}
                    f = fitness(order, b)
                    GRID.append((order, b, f))
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

def boot_self(order, b):
    """95% interval of log2(fitness) for one plan, resampling numbers within each band."""
    c = {Pn: costs(order, b, Pn) for Pn in P.PRICINGS}
    rng = random.Random(2026)
    bands = [np.flatnonzero(M.band == pb) for pb in P.BANDS]
    vals = []
    for _ in range(10000):
        idx = np.concatenate([bb[[rng.randrange(len(bb)) for _ in range(len(bb))]] for bb in bands])
        vals.append(math.log2(max(c[Pn][idx].mean() / M.qs[Pn][idx].mean() for Pn in P.PRICINGS)))
    vals.sort()
    return vals[250], vals[9749]

def boot(order_b, b_b, order_a, b_a):
    ca = {Pn: costs(order_a, b_a, Pn) for Pn in P.PRICINGS}
    cb = {Pn: costs(order_b, b_b, Pn) for Pn in P.PRICINGS}
    rng = random.Random(2026)
    bands = [np.flatnonzero(M.band == pb) for pb in P.BANDS]
    vals = []
    for _ in range(10000):
        idx = np.concatenate([b[[rng.randrange(len(b)) for _ in range(len(b))]] for b in bands])
        f = lambda c: max(c[Pn][idx].mean() / M.qs[Pn][idx].mean() for Pn in P.PRICINGS)
        vals.append(math.log2(f(cb) / f(ca)))
    vals.sort()
    return vals[250], vals[9749]

if __name__ == "__main__":
    fmt = lambda b: f"td {b['td']:>7}  rho {b['rho']:>7}  pm1 {'full' if b['pm1'] else 0:>4}  ecm {b['ecm']:>7}"
    res = {}
    for order in itertools.permutations(NAMES):
        f, b, (gf, gb) = optimize(order)
        res[" -> ".join(order)] = {"fitness": f, "budgets": b, "grid_fitness": gf, "grid_budgets": gb}
    ranked = sorted(res.items(), key=lambda kv: kv[1]["fitness"])
    A_order, A_b = NAMES, {"td": 0, "rho": 5793, "pm1": 0, "ecm": 32768}
    fA = fitness(A_order, A_b)
    best_k, best_v = ranked[0]
    best_o = tuple(best_k.split(" -> "))
    print(f"A (td -> rho -> pm1 -> ecm; rho 5793, ecm 32768): fitness {fA:.4f}\n")
    print("all 24 orders: exact optimum over the map's budget grid | after 1/8-octave refinement | refined vs best, log2 [paired 95%]")
    for k, v in ranked:
        o = tuple(k.split(" -> "))
        lo, hi = (0.0, 0.0) if k == best_k else boot(o, v["budgets"], best_o, best_v["budgets"])
        v["vs_best_log2"] = math.log2(v["fitness"] / best_v["fitness"]); v["vs_best_ci95"] = [lo, hi]
        print(f"  {k:28s} grid {v['grid_fitness']:.4f} ({fmt(v['grid_budgets'])}) | refined {v['fitness']:.4f} ({fmt(v['budgets'])}) | "
              f"{v['vs_best_log2']:+.4f} [{lo:+.4f}, {hi:+.4f}]")
    matters = [k for k, v in res.items() if v["vs_best_ci95"][0] > 0]
    print(f"\ncard order: {'MATTERS' if matters else 'does not matter'} ({len(matters)} of 24 orders have an interval above 0)")
    lo, hi = boot(best_o, best_v["budgets"], A_order, A_b)
    print(f"overall best: {best_k}, refined fitness {best_v['fitness']:.4f}; log2(best / A) = {math.log2(best_v['fitness'] / fA):+.4f} [{lo:+.4f}, {hi:+.4f}]")
    # landscape over the grid
    gbest = min(GRID, key=lambda t: t[2])
    slo, shi = boot_self(gbest[0], gbest[1])
    thr = 2 ** shi
    fs = np.array([t[2] for t in GRID])
    near = [t for t in GRID if t[2] <= thr]
    print(f"\nlandscape: {len(GRID)} grid combinations; best grid point {gbest[2]:.4f} ({' -> '.join(gbest[0])}; {fmt(gbest[1])}), "
          f"its own 95% interval of log2 fitness [{slo:.4f}, {shi:.4f}] -> fitness up to {thr:.4f}")
    print(f"  within that interval: {len(near)} combinations ({100 * len(near) / len(GRID):.2f}%)")
    for s in NAMES:
        vals = sorted({t[1][s] for t in near})
        print(f"    {s}: {vals}")
    print(f"    rho before ecm in {sum(1 for t in near if t[0].index('rho') < t[0].index('ecm') or t[1]['rho'] == 0)}/{len(near)}")
    qs_ = np.quantile(fs, [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 1.0])
    print("  fitness quantiles (min, 1%, 5%, 25%, median, 75%, max): " + ", ".join(f"{x:.3f}" for x in qs_))
    json.dump({"A_fitness": fA, "orders": res, "best": best_k, "best_vs_A_log2_ci95": [lo, hi], "card_order_matters": bool(matters),
               "landscape": {"n": len(GRID), "best_grid_fitness": gbest[2], "best_self_ci95_log2": [slo, shi],
                             "within_interval": len(near), "quantiles": qs_.tolist()}}, open("partition_orders.json", "w"), indent=1)
