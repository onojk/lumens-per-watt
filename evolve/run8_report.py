"""Run 8 report (PLAN.md, Run 8 design): per method, best-of-8 and median-of-8 fitness on the
tuning sets, evaluations-to-best, the winners split into budgets/order and qs genes, and each
seed's best re-scored on the sealed numbers, with the tuning-vs-sealed gap beside the two
reference gaps (qs + lc 1.4 alone, never selected; allocation A, selected on the map).

  .venv/bin/python run8_report.py ARM  -> run8_ARM_report.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math, statistics
import run8 as R

arm = ARGS[0]
data = json.load(open(f"run8_{arm}.json"))
sealed = [t for v in R.sealed_set(arm).values() for t in v]
R.oracle.check(sealed)
ev_sealed = R.Evaluator(sealed)
QSA = {"order": ("td", "rho", "pm1", "ecm"), "td": 0, "rho": 0, "pm1": 0, "ecm": 0,
       "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}           # qs + lc 1.4 alone
gaps_ref = {}
for name, pt in (("qs + lc 1.4 alone", QSA), ("allocation A", R.A_POINT)):
    tun = [R.Evaluator(R.tuning_set(arm, s)).fitness_of(pt) for s in data["seeds"]]
    sea = ev_sealed.fitness_of(pt)
    gaps_ref[name] = {"tuning_median": statistics.median(tun), "sealed": sea,
                      "gap_median_log2": statistics.median(math.log2(sea / t) for t in tun)}
out = {"arm": arm, "reference_gaps": gaps_ref, "methods": {}}
by = {}
for r in data["results"]:
    by.setdefault(r["method"], []).append(r)
fmt = lambda p: (f"order {'>'.join(x[:3] for x in p['order'])}  td {p['td']}  rho {p['rho']}  pm1 {'full' if p['pm1'] else 0}  ecm {p['ecm']}",
                 f"kc {p['kc']}  bc {p['bc']:.2f}  mc {p['mc']:.3f}  tc {p['tc']:.2f}  lc {p['lc']:.2f}")
print(f"{arm}: budget {data['budget']} evaluations per run, seeds {data['seeds'][0]}-{data['seeds'][-1]}\n")
print("reference gaps (log2 sealed / tuning, median over the seeds' tuning sets):")
for k, v in gaps_ref.items():
    print(f"  {k:20s} tuning {v['tuning_median']:.3f}  sealed {v['sealed']:.3f}  gap {v['gap_median_log2']:+.3f}")
for m, rs in by.items():
    rs.sort(key=lambda r: r["seed"])
    tun = [r["fitness"] for r in rs]
    sea = [ev_sealed.fitness_of(r["point"]) for r in rs]
    gaps = [math.log2(s / t) for s, t in zip(sea, tun)]
    best = min(range(len(rs)), key=lambda i: tun[i])
    out["methods"][m] = {"tuning": tun, "sealed": sea, "gaps_log2": gaps, "evaluations": [r["evaluations"] for r in rs],
                         "evaluations_to_best": [r["evaluations_to_best"] for r in rs], "points": [r["point"] for r in rs],
                         "best_of_8": tun[best], "median_of_8": statistics.median(tun)}
    print(f"\n{m}: best-of-8 {tun[best]:.3f} (seed {rs[best]['seed']}), median-of-8 {statistics.median(tun):.3f}, "
          f"evaluations-to-best median {statistics.median(r['evaluations_to_best'] for r in rs):.0f}, "
          f"evaluations {sorted(set(r['evaluations'] for r in rs))}, secs median {statistics.median(r['secs'] for r in rs):.0f}")
    print(f"  sealed: best seed's genome {sea[best]:.3f}; median over seeds {statistics.median(sea):.3f}; "
          f"tuning-vs-sealed gap median {statistics.median(gaps):+.3f} (range {min(gaps):+.3f} to {max(gaps):+.3f})")
    for r, t, s in zip(rs, tun, sea):
        a, b = fmt(r["point"])
        print(f"    seed {r['seed']}: tuning {t:.3f}  sealed {s:.3f} | {a} | {b}")
json.dump(out, open(f"run8_{arm}_report.json", "w"), indent=1)
