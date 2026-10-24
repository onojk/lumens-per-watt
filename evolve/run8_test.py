"""Run 8 harness tests (PLAN.md, Run 8 design), run before any arm:

  1. The same genome scores identically through every method's path: Evaluator.fitness_of,
     the counted call (evolution's and random search's path), a second Evaluator on the same
     numbers, and TPE's path (point -> Optuna parameters -> tpe_space on a FixedTrial ->
     point: the same point, the same fitness).
  2. TPE's and random search's samples stay inside the shared bounds (run8_space.in_bounds):
     10,000 random samples; 400 TPE trials on a cheap stub objective.
  3. Evaluations are counted the same way for every method: with a stub evaluator, random,
     evolution, the fresh-batch arm, TPE and the warm-started probe each use exactly the
     budget (340 and 1,360); the probe's first trial is allocation A.
  4. The qs-gene sub-experiment: every point random search, evolution and TPE propose keeps
     A's budgets and order; TPE's qs-only round trip is exact; the counts are exact.

  .venv/bin/python run8_test.py  -> exit 0 only if everything ran and passed
"""
import sys
sys.argv[1:] = []
import random
import run8 as R
import run8_space as S

FAIL, PENDING = [], []
def check(cond, *what):
    if not cond:
        FAIL.append(what)
        print("FAIL", *what)

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    optuna = None
    PENDING.append("optuna not installed: TPE parts of tests 1-3 not run")

class Stub:
    """A cheap evaluator with the same counting as Evaluator."""
    def __init__(self):
        self.count, self.history = 0, []
    def fitness_of(self, pt):
        return (pt["kc"] - 20) ** 2 + abs(pt["bc"] - 1.1) + (pt["rho"] % 997) / 997.0
    def __call__(self, pt):
        self.count += 1
        f = self.fitness_of(pt)
        self.history.append((self.count, f, pt))
        return f

class StubFresh:
    def __init__(self):
        self.evs = []
    def __call__(self, gen):
        self.evs.append(Stub())
        return self.evs[-1]
    def count_total(self):
        return sum(e.count for e in self.evs)

if __name__ == "__main__":
    # 1. identical scoring through every path (small real set: 6 balanced 84-bit numbers)
    nums = R.semiprimes_pq(84, 6, 8099099)
    ev = R.Evaluator(nums)
    ev2 = R.Evaluator(nums)
    rng = random.Random(1)
    pts = [R.A_POINT] + [S.sample(rng) for _ in range(5)]
    for pt in pts:
        f0 = ev.fitness_of(pt)
        check(ev(pt) == f0 == ev2.fitness_of(pt), "scores differ across paths", pt)
        if optuna:
            back = R.tpe_space(optuna.trial.FixedTrial(R.point_params(pt)))
            check(back == pt and ev.fitness_of(back) == f0, "TPE round trip changes the point", pt, back)
    # 2. bounds
    check(all(S.in_bounds(S.sample(rng)) for _ in range(10000)), "random sample out of bounds")
    if optuna:
        study = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=0))
        seen = []
        study.optimize(lambda t: (seen.append(R.tpe_space(t)), Stub().fitness_of(seen[-1]))[1], n_trials=400)
        check(all(S.in_bounds(p) for p in seen), "TPE sample out of bounds")
        check(len({p["order"] for p in seen}) == 24, "TPE never proposed some orders", len({p["order"] for p in seen}))
    # 3. counting
    for budget in (340, 1360):
        st = Stub(); R.random_search(st, budget, random.Random(2)); check(st.count == budget, "random count", budget, st.count)
        st = Stub(); R.evolution(st, budget, random.Random(3)); check(st.count == budget, "evolution count", budget, st.count)
        fb = StubFresh(); R.evolution(Stub(), budget, random.Random(4), fresh=fb)
        check(fb.count_total() == budget, "fresh-batch count", budget, fb.count_total())
        check(len(fb.evs) == budget // (R.ISLANDS * R.PER_ISLAND), "fresh-batch generations", budget, len(fb.evs))
        if optuna:
            st = Stub(); R.tpe(st, budget, 5); check(st.count == budget, "TPE count", budget, st.count)
            st = Stub(); R.tpe(st, budget, 6, warm=R.A_POINT)
            check(st.count == budget and st.history[0][2] == R.A_POINT, "warm-start count or first trial", budget, st.count)
    # 4. qs-gene sub-experiment
    fixed = lambda p: all(p[g] == R.A_POINT[g] for g in S.BOUNDS if g not in S.QS_GENES)
    for name, fn in (("random", lambda st: R.random_search(st, 1360, random.Random(7), qs_only=True)),
                     ("evolution", lambda st: R.evolution(st, 1360, random.Random(8), qs_only=True))):
        st = Stub(); fn(st)
        check(st.count == 1360 and all(fixed(p) for _, _, p in st.history), f"qs-only {name}")
    if optuna:
        for warm in (None, R.A_POINT):
            st = Stub(); R.tpe(st, 1360, 9, warm=warm, qs_only=True)
            check(st.count == 1360 and all(fixed(p) for _, _, p in st.history), "qs-only TPE", warm is not None)
        back = R.tpe_space(optuna.trial.FixedTrial(R.point_params(R.A_POINT, True)), True)
        check(back == R.A_POINT, "qs-only TPE round trip", back)
    print(f"run8 harness tests: {len(FAIL)} failures" + (f"; PENDING: {PENDING}" if PENDING else ""))
    sys.exit(1 if FAIL else (2 if PENDING else 0))
