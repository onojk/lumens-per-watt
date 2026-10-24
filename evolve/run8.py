"""Run 8 harness (PLAN.md, Run 8 design): evolution, TPE and random search over one shared
genome space (run8_space.py), plus the fresh-batch evolution arm and the TPE probe warm-
started from allocation A, all through one evaluation function.

Evaluation: a point -> run8_space.to_genome -> lampcore --types on the tuning numbers (cap
2^28) -> fitness (c) = optypes.robust against qs + lc 1.4 alone on the same numbers. A genome
that misses any number scores MISS_FITNESS (worse than any real one). Every fitness request a
method's proposal step makes is one evaluation (TPE trials, random samples, evolution's
children and initial population); evolution's carried-over elites are not re-requested on a
fixed set. Budget per run: BUDGET[arm] evaluations, counted by the evaluator itself.

Populations (oracle-checked): per seed s, a fixed tuning set
  mixed:    12 numbers per band, semiprimes_unbalanced(84, pb, 12, 8000000 + 1000 s + pb)
            (semiprimes_pq for the 42-bit band)
  balanced: semiprimes_pq(84, 18, 8000000 + 1000 s + 99)
sealed: 80 per band, 8500000 + 100 pb + 84 (balanced arm: the 42-bit band's 80).
The fresh-batch arm draws a new tuning set each generation (seed 8200000 + 1000 s + 10 gen).

Arms: sanity (balanced, full space: evolution, TPE, random, evolution-fresh); mixed (the
partition population, full space: the same four); mixed-qs (the qs-gene sub-experiment:
budgets and order fixed at allocation A, only kc, bc, mc, tc, lc searched: evolution, TPE,
random, and the qs-gene probe "tpe-warm", TPE warm-started from A).

Convergence (mixed arms, PLAN.md): A scored on each seed's own tuning set; T2 = evaluations to
reach A's fitness or better; T1 = evaluations to the first improvement whose paired interval
of log2(fitness / A's) over that set (10,000 resamples within each band, random.Random(2026))
does not lie above 0. Computed afterwards by re-scoring the run's improvement sequence (not
counted as evaluations).

  .venv/bin/python run8.py sanity [workers]     -> run8_sanity.json (balanced arm)
  .venv/bin/python run8.py mixed [workers]      -> run8_mixed.json (after review)
  .venv/bin/python run8.py mixed-qs [workers]   -> run8_mixed-qs.json (after review)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random, time
from multiprocessing import Pool
import optypes, oracle
import run8_space as S
from fastlamps import run_many, semiprimes_pq, semiprimes_unbalanced

BANDS = (16, 20, 24, 28, 32, 36, 42)
CAP = 2 ** 28
SEEDS = tuple(range(71, 79))
BUDGET = {"sanity": 340, "mixed": 1360, "mixed-qs": 1360}
REF = [{"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}]
A_POINT = {"order": ("td", "rho", "pm1", "ecm"), "td": 0, "rho": 5793, "pm1": 0, "ecm": 32768,
           "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}
MISS_FITNESS = 1e9
ISLANDS, PER_ISLAND, ELITES, MIGRATE_EVERY, MIGRANTS = 4, 17, 2, 5, 2

# ---- populations --------------------------------------------------------------------------

def population_of(arm):
    return "sanity" if arm == "sanity" else "mixed"

def tuning_set(arm, s, gen=None):
    arm = population_of(arm)
    base = (8200000 + 1000 * s + 10 * gen) if gen is not None else (8000000 + 1000 * s)
    if arm == "sanity":
        return semiprimes_pq(84, 18, base + 99)
    out = []
    for pb in BANDS:
        out += semiprimes_pq(84, 12, base + pb) if pb == 42 else semiprimes_unbalanced(84, pb, 12, base + pb)
    return out

def sealed_set(arm):
    arm = population_of(arm)
    out = {}
    for pb in (BANDS if arm == "mixed" else (42,)):
        seed = 8500000 + 100 * pb + 84
        out[pb] = semiprimes_pq(84, 80, seed) if pb == 42 else semiprimes_unbalanced(84, pb, 80, seed)
    return out

# ---- the one evaluation function ------------------------------------------------------------

class Evaluator:
    """Scores points on one fixed set of numbers and counts every request."""
    def __init__(self, nums, pr=None):
        self.nums, self.pr = nums, pr or optypes.prices()
        self.ref = [r[4] for r in run_many(REF, nums, CAP, types=True)]
        assert all(r is not None for r in self.ref)
        self.count = 0
        self.history = []                      # (evaluation index, fitness, point)

    def per_number(self, pt):
        return run_many(S.to_genome(pt), self.nums, CAP, types=True)

    def fitness_of(self, pt):
        rs = self.per_number(pt)
        if any(r[0] is None for r in rs):
            return MISS_FITNESS
        return optypes.robust([r[4] for r in rs], self.ref, self.pr)[0]

    def __call__(self, pt):
        self.count += 1
        f = self.fitness_of(pt)
        self.history.append((self.count, f, pt))
        return f

def best_of(history):
    i, f, pt = min(history, key=lambda h: h[1])
    return {"fitness": f, "point": pt, "evaluations_to_best": i}

# ---- methods --------------------------------------------------------------------------------

def random_search(ev, budget, rng, qs_only=False):
    while ev.count < budget:
        pt = S.sample(rng)
        ev(S.restrict(pt, A_POINT) if qs_only else pt)
    return best_of(ev.history)

def evolution(ev, budget, rng, fresh=None, qs_only=False):
    """Islands (ISLANDS x PER_ISLAND). Each generation, per island: the ELITES best carry over,
    and children fill the rest (mutation of a parent from the better half, or crossover of
    two then mutation). Every MIGRATE_EVERY generations each island's MIGRANTS best replace
    the next island's worst (ring). On a fixed set, carried members keep their scores and only
    children are evaluated, one at a time, until the budget is used exactly. With fresh (gen ->
    Evaluator on that generation's new batch), every member is scored again each generation
    (ISLANDS x PER_ISLAND evaluations per generation, as Run 6 did)."""
    used = (lambda: fresh.count_total()) if fresh else (lambda: ev.count)
    genes = S.QS_GENES if qs_only else None
    new_point = (lambda: S.restrict(S.sample(rng), A_POINT)) if qs_only else (lambda: S.sample(rng))
    e = fresh(0) if fresh else ev
    isl = []
    for _ in range(ISLANDS):
        pop = []
        for _ in range(PER_ISLAND):
            if used() >= budget:
                break
            p = new_point()
            pop.append((e(p), p))
        isl.append(pop)
    gen = 0
    while used() < budget:
        gen += 1
        for pop in isl:
            pop.sort(key=lambda t: t[0])
        if gen % MIGRATE_EVERY == 0:
            movers = [list(pop[:MIGRANTS]) for pop in isl]
            for i in range(ISLANDS):
                j = (i + 1) % ISLANDS
                isl[j] = sorted(isl[j][:len(isl[j]) - MIGRANTS] + movers[i], key=lambda t: t[0])
        if fresh:
            e = fresh(gen)
        new = []
        for pop in isl:
            elites = pop[:ELITES]
            parents = [p for _, p in pop[:max(ELITES, len(pop) // 2)]]
            members = [p for _, p in elites]
            while len(members) < PER_ISLAND:
                if rng.random() < 0.3 and len(parents) > 1:
                    a, b = rng.sample(parents, 2)
                    kid, _ = S.mutate(S.crossover(a, b, rng), rng, genes)
                else:
                    kid, _ = S.mutate(rng.choice(parents), rng, genes)
                members.append(kid)
            out = []
            for k, p in enumerate(members):
                if k < len(elites) and not fresh:
                    out.append(elites[k])                    # carried: score kept, no evaluation
                    continue
                if used() >= budget:
                    break
                out.append((e(p), p))
            new.append(out)
        isl = new
    if fresh:
        last = [t for pop in isl for t in pop]
        f, p = min(last, key=lambda t: t[0])
        return {"fitness": f, "point": p, "evaluations_to_best": used()}
    return best_of(ev.history)

def tpe_space(trial, qs_only=False):
    """The shared space as Optuna distributions (from run8_space.BOUNDS); with qs_only, only
    the qs genes, the rest fixed at allocation A."""
    import itertools
    if qs_only:
        pt = {g: A_POINT[g] for g in S.BOUNDS if g not in S.QS_GENES}
        pt["kc"] = trial.suggest_int("kc", 1, 32)
        for g in ("bc", "tc", "lc"):
            pt[g] = trial.suggest_float(g, *S.BOUNDS[g][1:])
        pt["mc"] = trial.suggest_float("mc", *S.BOUNDS["mc"][1:], log=True)
        return pt
    pt = {}
    orders = [" ".join(o) for o in itertools.permutations(S.PRE)]
    pt["order"] = tuple(trial.suggest_categorical("order", orders).split())
    for g in ("td", "rho", "ecm"):
        on = trial.suggest_categorical(f"{g}_on", [False, True])
        pt[g] = trial.suggest_int(g, S.BUDGET_LO, S.BUDGET_HI, log=True) if on else 0
    pt["pm1"] = trial.suggest_categorical("pm1", [0, 1])
    pt["kc"] = trial.suggest_int("kc", 1, 32)
    for g in ("bc", "tc", "lc"):
        pt[g] = trial.suggest_float(g, *S.BOUNDS[g][1:])
    pt["mc"] = trial.suggest_float("mc", *S.BOUNDS["mc"][1:], log=True)
    return pt

def point_params(pt, qs_only=False):
    """A point as the Optuna parameters tpe_space would suggest for it (for enqueue_trial)."""
    if qs_only:
        return {g: pt[g] for g in S.QS_GENES}
    p = {"order": " ".join(pt["order"]), "pm1": pt["pm1"], "kc": pt["kc"], "bc": pt["bc"], "mc": pt["mc"],
         "tc": pt["tc"], "lc": pt["lc"]}
    for g in ("td", "rho", "ecm"):
        p[f"{g}_on"] = pt[g] != 0
        if pt[g]:
            p[g] = pt[g]
    return p

def tpe(ev, budget, seed, warm=None, qs_only=False):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    if warm is not None:
        study.enqueue_trial(point_params(warm, qs_only))
    study.optimize(lambda t: ev(tpe_space(t, qs_only)), n_trials=budget)
    return best_of(ev.history)

def convergence(ev, history):
    """T1 and T2 against allocation A on this evaluator's numbers (mixed arms)."""
    import numpy as np
    bands = [i for i in range(len(ev.nums))]
    per_band = {}
    for i, (N, p, q) in enumerate(ev.nums):
        per_band.setdefault(min(p, q).bit_length(), []).append(i)
    groups = [np.array(v) for v in per_band.values()]
    def costs(pt):
        rs = ev.per_number(pt)
        return {P: np.array([optypes.cost(r[4], P, ev.pr) for r in rs]) for P in ("official", "ruint", "montgomery")}
    ref = {P: np.array([optypes.cost(c, P, ev.pr) for c in ev.ref]) for P in ("official", "ruint", "montgomery")}
    cA = costs(A_POINT)
    fit = lambda c, idx: max(c[P][idx].mean() / ref[P][idx].mean() for P in c)
    all_idx = np.arange(len(ev.nums))
    fA = fit(cA, all_idx)
    best, T1, T2 = None, None, None
    for i, f, pt in history:
        if best is not None and f >= best:
            continue
        best = f
        if T2 is None and f <= fA:
            T2 = i
        if T1 is None and f < 1e8:
            c = costs(pt)
            rng = random.Random(2026)
            vals = []
            for _ in range(10000):
                idx = np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups])
                vals.append(math.log2(fit(c, idx) / fit(cA, idx)))
            vals.sort()
            if vals[250] <= 0:
                T1 = i
        if T1 is not None and T2 is not None:
            break
    return {"A_fitness_on_this_set": fA, "T1": T1, "T2": T2}

# ---- one run ----------------------------------------------------------------------------

class FreshBatches:
    def __init__(self, arm, s, pr):
        self.arm, self.s, self.pr, self.evs = arm, s, pr, []
    def __call__(self, gen):
        nums = tuning_set(self.arm, self.s, gen)
        oracle.check(nums)
        ev = Evaluator(nums, self.pr)
        self.evs.append(ev)
        return ev
    def count_total(self):
        return sum(e.count for e in self.evs)

def one_run(args):
    arm, method, s = args
    pr = optypes.prices()
    budget = BUDGET[arm]
    t0 = time.time()
    nums = tuning_set(arm, s)
    oracle.check(nums)
    ev = Evaluator(nums, pr)
    rng = random.Random(1000 * s + {"evolution": 1, "random": 2, "tpe": 3, "evolution-fresh": 4, "tpe-warm": 5}[method])
    qs_only = arm == "mixed-qs"
    if method == "random":
        res = random_search(ev, budget, rng, qs_only)
    elif method == "evolution":
        res = evolution(ev, budget, rng, qs_only=qs_only)
    elif method == "evolution-fresh":
        fb = FreshBatches(arm, s, pr)
        res = evolution(ev, budget, rng, fresh=fb)
        res["tuning_fitness_fixed_set"] = ev.fitness_of(res["point"])   # the same pick on the seed's fixed set
        ev.count = fb.count_total()
    elif method == "tpe":
        res = tpe(ev, budget, s, qs_only=qs_only)
    elif method == "tpe-warm":
        res = tpe(ev, budget, s, warm=A_POINT, qs_only=qs_only)
    if arm != "sanity" and method != "evolution-fresh":
        res["convergence"] = convergence(ev, ev.history)
    res.update(arm=arm, method=method, seed=s, evaluations=ev.count, secs=round(time.time() - t0, 1),
               trace=[(i, f) for i, f, _ in ev.history] if method != "evolution-fresh" else None)
    return res

if __name__ == "__main__":
    arm = ARGS[0]
    workers = int(ARGS[1]) if len(ARGS) > 1 else 8
    methods = ["evolution", "tpe", "random", "tpe-warm"] if arm == "mixed-qs" else ["evolution", "tpe", "random", "evolution-fresh"]
    jobs = [(arm, m, s) for m in methods for s in SEEDS]
    with Pool(workers) as pool:
        results = pool.map(one_run, jobs, chunksize=1)
    json.dump({"arm": arm, "budget": BUDGET[arm], "seeds": SEEDS, "results": results}, open(f"run8_{arm}.json", "w"), indent=1)
    print(f"{arm}: {len(results)} runs written to run8_{arm}.json")
