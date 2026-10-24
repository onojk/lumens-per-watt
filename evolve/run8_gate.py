"""Run 8 supplements to run8_final_report.py (written after the mixed arms ran; no new
selection, only checks of what was pre-registered):

- ACCEPT gate (PLAN.md, written before Run 8): no band worse than 1.5x qs + lc 1.4 alone under
  any pricing, on the sealed numbers (80 per band). The final report prints per-band ratios for
  each method's best-of-8 genome only; this checks every run's genome and allocation A.
- Clause (a) scored as literally written in PLAN ("evolution's best-of-4 final fitness"; the
  wording predates the move to 8 seeds): best-of-4 over seeds 71-74, both methods'
  trajectories over those seeds. The final report scores the best-of-8 reading.
- mixed-qs: the warm-started probe's own best-of-8 genome against A on the sealed numbers
  (the final report's A_check uses the best method overall), same paired bootstrap.

  .venv/bin/python run8_gate.py ARM  -> run8_ARM_gate.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, random
import numpy as np
import optypes
import run8 as R

PR = ("official", "ruint", "montgomery")
GATE = 1.5
B = 10000
arm = ARGS[0]
data = json.load(open(f"run8_{arm}.json"))
pr = optypes.prices()

def band_of(t):
    return min(t[1], t[2]).bit_length()

sealed = [t for v in R.sealed_set(arm).values() for t in v]
R.oracle.check(sealed)
ev = R.Evaluator(sealed, pr)
bands = sorted({band_of(t) for t in sealed})
idx = {b: np.array([i for i, t in enumerate(sealed) if band_of(t) == b]) for b in bands}
ref = {P: np.array([optypes.cost(x, P, pr) for x in ev.ref]) for P in PR}

def costs(pt):
    rs = ev.per_number(pt)
    return any(r[0] is None for r in rs), {P: np.array([optypes.cost(r[4], P, pr) for r in rs]) for P in PR}

def gate(c):
    ratios = {P: {b: float(c[P][idx[b]].mean() / ref[P][idx[b]].mean()) for b in bands} for P in PR}
    worst = max((v, P, b) for P in PR for b, v in ratios[P].items())
    return ratios, worst

out = {"arm": arm, "gate": GATE, "genomes": []}
cache = {}
for name, pt, seed in [("allocation A", R.A_POINT, None)] + [(r["method"], r["point"], r["seed"]) for r in data["results"]]:
    miss, c = costs(pt)
    cache[(name, seed)] = c
    ratios, (wv, wP, wb) = gate(c)
    ok = not miss and wv <= GATE
    out["genomes"].append({"method": name, "seed": seed, "miss": miss, "worst": wv, "worst_pricing": wP, "worst_band": wb,
                           "passes": ok, "ratios": ratios})
print(f"{arm}: ACCEPT gate (no band > {GATE}x qs + lc 1.4 alone, any pricing), sealed numbers, {len(sealed)} ({len(sealed) // len(bands)} per band)")
for m in dict.fromkeys(g["method"] for g in out["genomes"]):
    gs = [g for g in out["genomes"] if g["method"] == m]
    fails = [g for g in gs if not g["passes"]]
    w = max(gs, key=lambda g: g["worst"])
    print(f"  {m:15s} passes {len(gs) - len(fails)}/{len(gs)}; worst band ratio {w['worst']:.3f} (seed {w['seed']}, band {w['worst_band']}, {w['worst_pricing']})"
          + (f"; FAIL: " + ", ".join(f"seed {g['seed']} {g['worst']:.3f} band {g['worst_band']} {g['worst_pricing']}" + (" (miss)" if g["miss"] else "") for g in fails) if fails else ""))

def traj(rs):
    cur, best = [math.inf] * len(rs), []
    for i in range(max(len(r["trace"]) for r in rs)):
        for k, r in enumerate(rs):
            if i < len(r["trace"]):
                cur[k] = min(cur[k], r["trace"][i][1])
        best.append(min(cur))
    return best

by = {}
for r in data["results"]:
    by.setdefault(r["method"], []).append(r)
four = (71, 72, 73, 74)
E4 = [r for r in by["evolution"] if r["seed"] in four]
T4 = [r for r in by["tpe"] if r["seed"] in four]
target = min(r["fitness"] for r in E4)
ie = next((i + 1 for i, f in enumerate(traj(E4)) if f <= target), None)
it_ = next((i + 1 for i, f in enumerate(traj(T4)) if f <= target), None)
out["clause_a_best_of_4"] = {"seeds": four, "target": target, "evolution_evaluations": ie, "tpe_evaluations": it_,
                             "holds": ie is not None and it_ is not None and it_ < ie}
print(f"\nclause (a), best-of-4 over seeds 71-74 (literal wording): {out['clause_a_best_of_4']}")

if arm == "mixed-qs":
    W = min(by["tpe-warm"], key=lambda r: r["fitness"])
    cw, cA = cache[("tpe-warm", W["seed"])], cache[("allocation A", None)]
    groups = list(idx.values())
    fit = lambda c, i: max(c[P][i].mean() / ref[P][i].mean() for P in PR)
    rng = random.Random(2026)
    vals = []
    for _ in range(B):
        i = np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups])
        vals.append(math.log2(fit(cw, i) / fit(cA, i)))
    vals.sort()
    lo, hi = vals[int(0.025 * B)], vals[int(0.975 * B) - 1]
    allx = np.arange(len(sealed))
    fw, fA = fit(cw, allx), fit(cA, allx)
    out["probe_vs_A"] = {"probe_seed": W["seed"], "probe_sealed": fw, "A_sealed": fA, "log2": math.log2(fw / fA), "ci": [lo, hi],
                         "verdict": "A near-optimal" if hi >= 0 else f"partition study under-explored by {fA / fw:.3f}x"}
    print(f"\nprobe (tpe-warm best-of-8) vs A, sealed: {out['probe_vs_A']}")
json.dump(out, open(f"run8_{arm}_gate.json", "w"), indent=1)
