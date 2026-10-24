"""Coverage test for Run 8's shared genome space (run8_space.py): evolution's operators reach
the whole space TPE and random search use, and nothing leaves it.

  1. sample(): 20,000 points, all in bounds; all 24 card orders, pm1 on and off, every budget
     at 0 and near both ends, every qs gene near both ends of its range.
  2. mutation alone, from one fixed start, 50,000 steps: always in bounds; every gene changed;
     all 24 orders visited; pm1 both ways; every budget reaches 0, 2^8 and 2^20; every qs gene
     reaches within 5% of both bounds (log scale for mc).
  3. crossover: every gene of the child comes from one parent; the order is a parent's whole.
  4. to_genome: valid (lamps.validate_genome), runs through lamps.run on a 48-bit number, and
     an off budget skips its stage (ob = 0), pm1 on is ob = 2^40.
  5. The test itself: a broken operator (order changes limited to swapping the first two
     stages; pm1 never flipped) must make the coverage check fail.

  python3 run8_space_test.py  -> exit 0 on success
"""
import math, random, sys
import run8_space as S
from lamps import validate_genome, run
from fastlamps import semiprimes_pq

FAIL = []
def check(cond, *what):
    if not cond:
        FAIL.append(what)
        print("FAIL", *what)

def near(v, lo, hi, end, log=False):
    f = (lambda x: math.log(x)) if log else (lambda x: x)
    span = f(hi) - f(lo)
    return abs(f(v) - f(end)) <= 0.05 * span

def coverage(points, label):
    orders = {p["order"] for p in points}
    check(len(orders) == 24, label, "orders", len(orders))
    check({p["pm1"] for p in points} == {0, 1}, label, "pm1")
    for g in ("td", "rho", "ecm"):
        vals = [p[g] for p in points]
        check(0 in vals, label, g, "never 0")
        nz = [v for v in vals if v]
        check(near(min(nz), S.BUDGET_LO, S.BUDGET_HI, S.BUDGET_LO, True) and near(max(nz), S.BUDGET_LO, S.BUDGET_HI, S.BUDGET_HI, True),
              label, g, "range", min(nz), max(nz))
    for g in ("kc", "bc", "mc", "tc", "lc"):
        kind, lo, hi = S.BOUNDS[g]
        vals = [p[g] for p in points]
        log = kind == "logfloat"
        check(near(min(vals), lo, hi, lo, log) and near(max(vals), lo, hi, hi, log), label, g, "range", min(vals), max(vals))

if __name__ == "__main__":
    rng = random.Random(8)
    pts = [S.sample(rng) for _ in range(20000)]
    check(all(S.in_bounds(p) for p in pts), "sample out of bounds")
    coverage(pts, "sample")

    p = {"order": S.PRE, "td": 0, "rho": 5793, "ecm": 32768, "pm1": 0, "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}
    walk, changed = [p], set()
    for _ in range(50000):
        p, genes = S.mutate(p, rng)
        changed.update(genes)
        check(S.in_bounds(p), "mutation left the space", p)
        walk.append(p)
    check(changed == set(S.BOUNDS), "genes never mutated", set(S.BOUNDS) - changed)
    coverage(walk, "mutation walk")
    for g in ("td", "rho", "ecm"):
        vals = {q[g] for q in walk}
        check(S.BUDGET_LO in vals and S.BUDGET_HI in vals, "mutation", g, "does not reach both budget bounds exactly")

    for _ in range(2000):
        a, b = S.sample(rng), S.sample(rng)
        c = S.crossover(a, b, rng)
        check(all(c[g] in (a[g], b[g]) for g in S.BOUNDS) and S.in_bounds(c), "crossover", a, b, c)

    N = semiprimes_pq(48, 1, 48048)[0][0]
    for q in pts[:30]:
        g = S.to_genome(q)
        validate_genome(g)
        check([s["t"] for s in g[:4]] == list(q["order"]) and g[4]["t"] == "qs", "genome order", q)
        check(all(s["ob"] == (q[s["t"]] if s["t"] != "pm1" else (S.PM1_FULL if q["pm1"] else 0)) for s in g[:4]), "genome budgets", q)
        ops, d = run(g, N, 2 ** 28)
        check(d is None or N % d == 0, "genome run", q, ops, d)
    # the test catches a broken operator: order limited to swapping the first two stages, and
    # pm1 never flipped; each must make the walk's coverage check fail
    real = S._mutate_gene
    for label, broken in (("order: first two only", lambda pt, g, r: pt.__setitem__("order", (pt["order"][1], pt["order"][0]) + tuple(pt["order"][2:])) if g == "order" else real(pt, g, r)),
                          ("pm1 never flipped", lambda pt, g, r: None if g == "pm1" else real(pt, g, r))):
        S._mutate_gene = broken
        before = len(FAIL)
        q, w = dict(walk[0]), [dict(walk[0])]
        for _ in range(20000):
            q, _ = S.mutate(q, rng)
            w.append(q)
        coverage(w, "broken")
        caught = len(FAIL) > before
        del FAIL[before:]
        S._mutate_gene = real
        check(caught, "the coverage test missed a broken operator:", label)
        print(f"broken operator ({label}): {'caught' if caught else 'MISSED'}")
    print(f"run8 space: {len(FAIL)} failures (sample 20,000; mutation walk 50,000; crossover 2,000; genomes 30)")
    sys.exit(1 if FAIL else 0)
