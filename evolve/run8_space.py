"""Run 8's shared genome space (PLAN.md, Run 8 design): one definition of the genes and their
bounds, used by evolution's operators, random search's sampler and TPE's distributions, so
all three methods search exactly the same space.

A point is a dict:
  order  a permutation of the four pre-stages ("td", "rho", "pm1", "ecm"): 24 orders
  td, rho, ecm   op budgets: 0, or an integer in [2^8, 2^20] (log scale)
  pm1    0 (off) or 1 (full length: pm1 takes one gcd at the end, so partial budgets buy
         nothing; NOTES.md, partition study)
  kc     final qs: integer 1..32
  bc     0.7..3.0     mc  0.05..12 (log)     tc  1.0..3.5     lc  1.0..2.0
Stage genes are fixed at the partition study's values (STAGES).

  to_genome(point)   the lamp genome: the pre-stages in order, each with its ob, then qs
  sample(rng)        uniform over the space (budgets: 0 with probability P_ZERO, else
                     log-uniform; mc log-uniform)
  mutate(point, rng) evolution's mutation: one or two genes changed, every gene reachable
  crossover(a, b, rng)  uniform per gene (the order as a whole from one parent)
  BOUNDS             the table TPE's distributions are built from
"""
import math, random

PRE = ("td", "rho", "pm1", "ecm")
STAGES = {"td": {"t": "td", "a": 0.5}, "rho": {"t": "rho", "c": 1, "b": 64},
          "pm1": {"t": "pm1", "b": 0.19911571277067214}, "ecm": {"t": "ecm", "b1": 1.0, "b2": 50}}
BUDGET_LO, BUDGET_HI = 2 ** 8, 2 ** 20
PM1_FULL = 2 ** 40                 # "full length": at or past pm1's natural total (the ob identity)
P_ZERO = 0.25                      # chance a sampled budget is 0 (the stage off)
BOUNDS = {
    "td": ("budget", BUDGET_LO, BUDGET_HI), "rho": ("budget", BUDGET_LO, BUDGET_HI),
    "ecm": ("budget", BUDGET_LO, BUDGET_HI), "pm1": ("choice", (0, 1)),
    "order": ("perm", PRE),
    "kc": ("int", 1, 32), "bc": ("float", 0.7, 3.0), "mc": ("logfloat", 0.05, 12.0),
    "tc": ("float", 1.0, 3.5), "lc": ("float", 1.0, 2.0),
}
SIGMA = {"bc": 0.15, "tc": 0.15, "lc": 0.1, "mc": 0.3, "budget": 0.75}   # mutation steps (log2 units for budgets)

def in_bounds(pt):
    for g, spec in BOUNDS.items():
        v, kind = pt[g], spec[0]
        if kind == "budget" and not (v == 0 or (isinstance(v, int) and spec[1] <= v <= spec[2])):
            return False
        if kind == "choice" and v not in spec[1]:
            return False
        if kind == "perm" and sorted(v) != sorted(spec[1]):
            return False
        if kind == "int" and not (isinstance(v, int) and spec[1] <= v <= spec[2]):
            return False
        if kind in ("float", "logfloat") and not (spec[1] <= v <= spec[2]):
            return False
    return True

def _budget(rng):
    return 0 if rng.random() < P_ZERO else int(round(2 ** rng.uniform(8, 20)))

def sample(rng):
    order = list(PRE)
    rng.shuffle(order)
    return {"order": tuple(order), "td": _budget(rng), "rho": _budget(rng), "ecm": _budget(rng),
            "pm1": rng.choice((0, 1)), "kc": rng.randint(1, 32), "bc": rng.uniform(0.7, 3.0),
            "mc": math.exp(rng.uniform(math.log(0.05), math.log(12.0))), "tc": rng.uniform(1.0, 3.5),
            "lc": rng.uniform(1.0, 2.0)}

def _clip(v, lo, hi):
    return min(hi, max(lo, v))

def _mutate_gene(pt, g, rng):
    kind = BOUNDS[g][0]
    if kind == "budget":
        v = pt[g]
        if v == 0 or rng.random() < 0.15:             # switch the stage on (log-uniform) or off
            pt[g] = int(round(2 ** rng.uniform(8, 20))) if v == 0 else 0
        else:
            pt[g] = int(round(_clip(2 ** (math.log2(v) + rng.gauss(0, SIGMA["budget"])), BUDGET_LO, BUDGET_HI)))
    elif kind == "choice":
        pt[g] = 1 - pt[g]
    elif kind == "perm":
        o = list(pt[g])
        i, j = rng.sample(range(len(o)), 2)           # a random transposition: reaches all 24
        o[i], o[j] = o[j], o[i]
        pt[g] = tuple(o)
    elif g == "kc":
        v = pt[g]
        pt[g] = int(_clip(v + rng.choice((-1, 1)) * max(1, v // 4), 1, 32))
    elif kind == "logfloat":
        lo, hi = BOUNDS[g][1:]
        pt[g] = _clip(pt[g] * math.exp(rng.gauss(0, SIGMA[g])), lo, hi)
    else:
        lo, hi = BOUNDS[g][1:]
        pt[g] = _clip(pt[g] + rng.gauss(0, SIGMA[g]), lo, hi)

def mutate(pt, rng):
    """Return (child, the genes changed): one gene, or two with probability 1/3."""
    child = dict(pt)
    genes = rng.sample(list(BOUNDS), 2 if rng.random() < 1 / 3 else 1)
    for g in genes:
        _mutate_gene(child, g, rng)
    return child, genes

def crossover(a, b, rng):
    return {g: (a if rng.random() < 0.5 else b)[g] for g in BOUNDS}

def to_genome(pt):
    gen = []
    for name in pt["order"]:
        b = pt[name]
        ob = (PM1_FULL if b else 0) if name == "pm1" else b
        gen.append(dict(STAGES[name], ob=ob))
    return gen + [{"t": "qs", "kc": pt["kc"], "bc": pt["bc"], "mc": pt["mc"], "tc": pt["tc"], "lc": pt["lc"]}]
