"""Stage 9 first comparison (NOTES.md, "Stage 9: race combinator", First comparison and
addenda 4-9; predictions fixed there before this ran).

Races: race(ECM, qs + lc 1.4), race(rho, qs + lc 1.4), race(ECM, N51-0917's qs); side a (the
non-qs side) starts. Populations: the Stage 8 numbers (ecm_compare.py: balanced 54-84,
unbalanced 72/78/84 x 24/28/32), cap 2^28. Slice settings: sa = sb = s for s in 2^8, 2^10,
2^14, and the unequal setting of addendum 9: sa = s, sb = round(s * pi_a / pi_qs), with pi the
card's ruint-calibrated price per official op on that cell from the Stage 8 traces
(calibrate_counts.json, calibrate.json), never from race results.

Per race, setting and cell:
- official ops from lampcore, with Python's ops required to agree on every number (and the
  per-side ops), log2 mean and worst with the usual bootstrap, misses, switches;
- calibrated cost under ruint and Montgomery (median P-core prices) from each side's per-type
  counts (Python traces), log2 mean with its interval;
- the two sides alone under all three pricings (calibrate.json, the same numbers);
- ratio race / better side and race / worse side per pricing, the failure test per pricing
  (worse than 2x the better side, or worse than the worse side) and the robust verdict (a
  failure under any pricing), with each pricing's measured pi_a / pi_b and the bound
  1 + pi_other / pi_winner it implies;
- the (e) call: among {race, side a alone, side b alone}, the leader when all three pricings
  name the same leader with no tie, else "undecided";
- overshoot per side (mean and max ops past the slice size, share of slices that overshot),
  and the largest single charge per side.

  python3 race_compare.py [workers]  -> race_compare.json
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []      # ecm_compare and revalidate read sys.argv on import
import json, math, statistics
from multiprocessing import Pool
import race
from lamps import run
from fastlamps import run_many
from revalidate import bootstrap
from run6_accept import bootstrap_worst
from ecm_compare import BAL, UNB, balanced, unbalanced, ECM, QS, RHO, CAP

WORKERS = int(ARGS[0]) if ARGS else 8
N51_QS = json.load(open("run6/accept.json"))["genomes"]["N51-0917"][0]
assert N51_QS["t"] == "qs" and "lc" not in N51_QS
SIDES = {"ecm": ECM[0], "qs + lc 1.4": QS[0], "rho": RHO[0], "N51-0917": N51_QS}
RACES = [("ecm", "qs + lc 1.4"), ("rho", "qs + lc 1.4"), ("ecm", "N51-0917")]
SLICES = (256, 1024, 16384)
PRICINGS = ("official", "ruint", "montgomery")

CAL = json.load(open("calibrate.json"))
COUNTS = json.load(open("calibrate_counts.json"))
PRICE = {ref: {t: sorted(CAL["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1]
               for t in CAL["prices"][f"{ref} P1"]} for ref in ("ruint", "montgomery")}

def pops():
    p = {str(b): balanced(b) for b in BAL}
    p.update({f"{b}/{pb}": unbalanced(b, pb) for b, pb in UNB})
    return p

def pi_stage8(alg, cell):
    rows = [x for x in COUNTS[alg][cell] if x["ops"] is not None]
    return sum(PRICE["ruint"][t] * n for x in rows for t, n in x["counts"].items()) / sum(x["ops"] for x in rows)

def notes_ratios():
    """The addendum 9 table as committed in NOTES.md: cell -> ratio per race (2 decimals)."""
    lines = open("../NOTES.md").read().split("9. **A fourth slice setting", 1)[1].split("\n")
    rows = {}
    for ln in lines:
        f = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(f) == 4 and f[0] and f[0][0].isdigit() and f[1][0].isdigit():
            rows[f[0]] = dict(zip(RACES, map(float, f[1:])))
        elif rows and not ln.strip().startswith("|"):
            break
    return rows

NOTES_RATIOS = notes_ratios()

def settings(a, b, cell):
    out = [(f"equal {s}", s, s) for s in SLICES]
    ratio = pi_stage8(a, cell) / pi_stage8(b, cell)
    assert round(ratio, 2) == NOTES_RATIOS[cell][(a, b)], ("ratio drifted from NOTES addendum 9", a, b, cell, ratio)
    out += [(f"unequal {s}", s, round(s * ratio)) for s in SLICES]
    return out

def check_sides_alone(P):
    """The sides alone come from calibrate.json / calibrate_counts.json: same genomes, same
    cells, same numbers in the same order. N51-0917's qs stage stands in for the whole
    genome only because its sq stages never run: its ops alone must equal the genome's on
    every number."""
    import calibrate
    for name, st in SIDES.items():
        want = calibrate.ALGS[name]
        assert (want == [st]) if name != "N51-0917" else (want[0] == st), ("genome differs", name)
    for alg in SIDES:
        assert set(COUNTS[alg]) == set(P), ("cells differ", alg)
        for cell, nums in P.items():
            assert [x["N"] for x in COUNTS[alg][cell]] == [str(N) for N, p, q in nums], ("numbers differ", alg, cell)
    for cell, nums in P.items():
        stage_alone = [r[0] for r in run_many([N51_QS], nums, CAP)]
        assert stage_alone == [x["ops"] for x in COUNTS["N51-0917"][cell]], ("N51-0917's sq stages ran", cell)

def job(args):
    a, b, label, sa, sb, cell, N = args
    race.TRACE = {}
    race.RECORD_CHARGES = True
    ops, d = run([{"t": "race", "a": SIDES[a], "b": SIDES[b], "sa": sa, "sb": sb}], N, CAP)
    tr = race.TRACE
    sides = [{"ops": s["ops"], "per_type": s["per_type"], "slices": s["slices"], "size": s["size"],
              "end": s["end"], "max_charge": max(s["charges"]) if s["charges"] else 0} for s in tr["sides"]]
    return (a, b, label, cell, N), ops, sides, tr["switches"]

def price_of(sides, ref):
    return sum(PRICE[ref][t] * n for s in sides for t, n in s["per_type"].items())

def cell_stats(vals, capped=None):
    out = {"mean_log2": math.log2(sum(vals) / len(vals)), "ci95": list(bootstrap(vals))}
    if capped is not None:
        out["worst_log2"] = math.log2(max(capped))
        out["worst_ci95"] = list(bootstrap_worst(capped))
    return out

def leader(cells):
    best = min(cells, key=lambda k: cells[k]["mean_log2"])
    ties = [k for k in cells if k != best and cells[k]["ci95"][0] <= cells[best]["ci95"][1]]
    return best, ties

if __name__ == "__main__":
    P = pops()
    check_sides_alone(P)
    assert set(NOTES_RATIOS) == set(P), "addendum 9 table does not cover every cell"
    jobs, setting_of = [], {}
    for a, b in RACES:
        for cell, nums in P.items():
            for label, sa, sb in settings(a, b, cell):
                setting_of[(a, b, label, cell)] = (sa, sb)
                jobs += [(a, b, label, sa, sb, cell, N) for N, p, q in nums]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=4)
    by = {}
    for key, ops, sides, sw in res:
        by.setdefault(key[:4], {})[key[4]] = (ops, sides, sw)
    out = {"cap_log2": 28, "sides": SIDES, "races": [list(r) for r in RACES], "results": {}}
    alone = {pr: (CAL["official"] if pr == "official" else CAL["scores"][pr]) for pr in PRICINGS}
    for (a, b, label, cell), (sa, sb) in setting_of.items():
        nums = P[cell]
        rows = by[(a, b, label, cell)]
        g = [{"t": "race", "a": SIDES[a], "b": SIDES[b], "sa": sa, "sb": sb}]
        rust = run_many(g, nums, CAP, race=True)
        for (N, p, q), r in zip(nums, rust):
            ops, sides, sw = rows[N]
            assert r[0] == ops and r[4] == (sides[0]["ops"], sides[1]["ops"], sw), ("cores disagree", a, b, label, cell, N)
        solved = [rows[N] for N, p, q in nums if rows[N][0] is not None]
        misses = len(nums) - len(solved)
        capped = [CAP if rows[N][0] is None else rows[N][0] for N, p, q in nums]
        c = {"sa": sa, "sb": sb, "misses": misses}
        c["official"] = cell_stats([x[0] for x in solved], capped)
        for ref in ("ruint", "montgomery"):
            c[ref] = cell_stats([price_of(x[1], ref) for x in solved])
        # pi per side, per pricing (aggregate over the cell's solved numbers)
        c["pi"] = {}
        for ref in PRICINGS:
            pis = []
            for i in (0, 1):
                off = sum(x[1][i]["ops"] for x in solved)
                cost = off if ref == "official" else sum(PRICE[ref][t] * n for x in solved for t, n in x[1][i]["per_type"].items())
                pis.append(cost / off if off else None)
            c["pi"][ref] = pis
        c["verdict"] = {}
        for ref in PRICINGS:
            A, B = alone[ref][a][cell], alone[ref][b][cell]
            better, worse = (A, B) if A["mean_log2"] <= B["mean_log2"] else (B, A)
            r_better = 2 ** (c[ref]["mean_log2"] - better["mean_log2"])
            r_worse = 2 ** (c[ref]["mean_log2"] - worse["mean_log2"])
            pa, pb = c["pi"][ref]
            win = 0 if A["mean_log2"] <= B["mean_log2"] else 1
            pw, po = (pa, pb) if win == 0 else (pb, pa)
            bound = 1 + po / pw if pw and po else None
            fail = r_better > 2.0 or r_worse > 1.0
            c["verdict"][ref] = {"race_over_better": r_better, "race_over_worse": r_worse,
                                 "fails": fail, "pi_ratio_other_over_winner": (po / pw) if pw and po else None,
                                 "pricing_bound": bound, "beyond_bound": bool(bound and r_better > bound)}
        c["robust_fails"] = any(v["fails"] for v in c["verdict"].values())
        L = {ref: leader({"race": c[ref], a: alone[ref][a][cell], b: alone[ref][b][cell]}) for ref in PRICINGS}
        c["leaders"] = {ref: [l[0], l[1]] for ref, l in L.items()}
        same = len({L[ref][0] for ref in PRICINGS}) == 1 and not any(L[ref][1] for ref in PRICINGS)
        c["call_e"] = L["official"][0] if same else "undecided"
        sw = [x[2] for x in solved]
        c["switches"] = {"mean": sum(sw) / len(sw), "median": statistics.median(sw), "max": max(sw)}
        c["side_ops_mean"] = [sum(x[1][i]["ops"] for x in solved) / len(solved) for i in (0, 1)]
        c["overshoot"] = []
        for i in (0, 1):
            ov = [L_ - x[1][i]["size"] for x in solved for L_ in x[1][i]["slices"]]
            c["overshoot"].append({"mean": sum(ov) / len(ov) if ov else 0, "max": max(ov) if ov else 0,
                                   "share_over": sum(o > 0 for o in ov) / len(ov) if ov else 0,
                                   "max_single_charge": max(x[1][i]["max_charge"] for x in solved)})
        out["results"].setdefault(f"race({a}, {b})", {}).setdefault(label, {})[cell] = c
    for rname, by_label in out["results"].items():
        a, b = rname[5:-1].split(", ")
        print(f"\n{rname}")
        for label, cells in by_label.items():
            print(f"  {label}:")
            for cell, c in cells.items():
                v = c["verdict"]
                print(f"    {cell:6s} sb {c['sb']:6d}  "
                      + "  ".join(f"{ref[:4]} {c[ref]['mean_log2']:.2f} (x{v[ref]['race_over_better']:.2f} best"
                                  f"{' FAIL' if v[ref]['fails'] else ''}{' >bound' if v[ref]['beyond_bound'] else ''})" for ref in PRICINGS)
                      + f"  (e) {c['call_e']}  sw {c['switches']['mean']:.0f}"
                      + f"  ov {c['overshoot'][0]['mean']:.0f}/{c['overshoot'][1]['mean']:.0f}"
                      + f"  c {c['overshoot'][0]['max_single_charge']}/{c['overshoot'][1]['max_single_charge']}"
                      + f"  pi_r {c['pi']['ruint'][0]:.3f}/{c['pi']['ruint'][1]:.3f}"
                      + (f"  misses {c['misses']}" if c["misses"] else ""))
    json.dump(out, open("race_compare.json", "w"), indent=1)
