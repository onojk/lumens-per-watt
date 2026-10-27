"""Root confirm, the sealed timed run (NOTES.md, "Root confirm (I-029) as a card option"; predictions/root-confirm.md;
run through tools/sealed_run.sh root-confirm). 96 bits, all 640 map numbers, re-sieve off. Cells, against the
reference (full pass, pp absent): root alone; root + pp 3 ("2 free") at threshold shifts 0, +1, +2, +3, +4 bits
(tc -= d / log2 1,752; L unchanged).
Per cell: candidates per number (confirm-region calls); polynomials (sieve_scan / width); priced official / ruint /
Montgomery (mean; log2 mean-cost ratio against the reference with a paired 95% bootstrap, 10,000, random.Random(2026);
the robust ratio (c) = max over pricings; the (e) call); wall-clock, two replicates, interleaved and counterbalanced
(timing.counterbalanced), per region, with core 2's MHz per cell. Information only: ruint with root_test at the
within-benchmark ratio price 0.0430 (NOTES, "Meter note on the root_test price").
  python3 rootconfirm.py -> rootconfirm.json, stdout
"""
import json, math, random
import numpy as np
import partition as P, sizescale2 as S2
from fastlamps import run_many
from lctest import ref, bnd, cost, PT, PR
from timing import counterbalanced

LB = math.log2(1752.0)
R = 10000
RATIO_PRICE = 0.0430

g0 = ref(96)
rt = dict(g0, confirm="root")
cells = {"reference": g0, "root": rt}
for d in range(5):
    cells[f"root + pp 3, +{d} bits"] = dict(rt, pp=3, tc=g0["tc"] - d / LB)
nums = S2.map_nums(96)

def paired(a, b):
    rng = random.Random(2026)
    n = len(a)
    vals = sorted(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx))
                  for idx in ([rng.randrange(n) for _ in range(n)] for _ in range(R)))
    return math.log2(sum(a) / sum(b)), [vals[int(0.025 * R)], vals[int(0.975 * R) - 1]]

def ruint_ratio_price(t):
    return float(sum((RATIO_PRICE if k == "root_test" else PR["ruint"][k]) * v for k, v in t.items() if v))

types, out = {}, {}
for name, g in cells.items():
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(r[1] is not None for r in rs), name
    types[name] = rs
res, order, states, clock = counterbalanced(cells, nums, reps=2)
regs = ("setup", "gray", "sieve", "scan", "confirm", "lp_ledger", "solve")
ref_c = {Pn: [cost(r[4], Pn) for r in types["reference"]] for Pn in PT}
ref_ri = [ruint_ratio_price(r[4]) for r in types["reference"]]
ref_wall = None
for name, g in cells.items():
    rs = types[name]
    width = [2 * max(64, int(g["mc"] * bnd(N, g))) + 1 for N, _, _ in nums]
    polys = float(np.mean([r[4]["sieve_scan"] / w for r, w in zip(rs, width)]))
    c = {Pn: [cost(r[4], Pn) for r in rs] for Pn in PT}
    walls = res[name]
    wall = [sum(v["ns"] for k, v in w.items() if not k.startswith("lp:")) / 1e3 for w in walls]
    if ref_wall is None:
        ref_wall = wall
    rec = {"tc": g["tc"], "pp": g.get("pp", 0), "confirm": g.get("confirm", "full"),
           "candidates": walls[0]["confirm"]["calls"], "polys": polys,
           "priced_mean": {Pn: float(np.mean(v)) for Pn, v in c.items()},
           "wall_us": wall, "wall_regions_us": {k: float(np.mean([w[k]["ns"] for w in walls])) / 1e3 for k in regs},
           "wall_vs_ref": float(np.mean(wall) / np.mean(ref_wall) - 1),
           "wall_vs_ref_per_replicate": [w / rw - 1 for w, rw in zip(wall, ref_wall)],
           "mhz": clock[name]}
    line = (f"{name} (pp {rec['pp']}, tc {g['tc']:.4f}, confirm {rec['confirm']}): candidates {rec['candidates']:,.1f} per number; "
            f"polynomials {polys:.1f}; priced mean " + " ".join(f"{Pn} {rec['priced_mean'][Pn]:,.0f}" for Pn in PT)
            + f"; wall {np.mean(wall):,.1f} us ({wall[0]:,.1f} / {wall[1]:,.1f}), {100 * rec['wall_vs_ref']:+.1f}% vs reference "
            f"(replicates {' / '.join(f'{100 * x:+.1f}%' for x in rec['wall_vs_ref_per_replicate'])}): "
            + " ".join(f"{k} {v:,.1f}" for k, v in rec["wall_regions_us"].items())
            + f"; core 2 MHz " + (f"{clock[name]['min']:.0f}-{clock[name]['max']:.0f}, median {clock[name]['median']:.0f} (n {clock[name]['n']})"
                                  + (" FLAGGED (>10% off the reference)" if clock[name]["flag"] else "") if clock[name]["n"] else "no samples"))
    if name != "reference":
        pr = {Pn: paired(c[Pn], ref_c[Pn]) for Pn in PT}
        ratios = {Pn: 2 ** pr[Pn][0] for Pn in PT}
        robust = max(ratios.values())
        signs = {Pn: (-1 if pr[Pn][1][1] < 0 else 1 if pr[Pn][1][0] > 0 else 0) for Pn in PT}
        call = ("better" if all(s < 0 for s in signs.values()) else "worse" if all(s > 0 for s in signs.values()) else "undecided")
        ri = paired([ruint_ratio_price(r[4]) for r in rs], ref_ri)
        rec.update(paired={Pn: {"log2": pr[Pn][0], "ci95": pr[Pn][1], "ratio": ratios[Pn]} for Pn in PT},
                   robust_ratio=robust, e_call=call, ruint_at_ratio_price={"ratio": 2 ** ri[0], "ci95_ratio": [2 ** x for x in ri[1]]})
        line += ("; vs reference " + " ".join(f"{Pn} {ratios[Pn]:.4f} [{2 ** pr[Pn][1][0]:.4f}, {2 ** pr[Pn][1][1]:.4f}]" for Pn in PT)
                 + f"; robust ratio (c) {robust:.4f}; (e) {call}; information only: ruint at root_test {RATIO_PRICE} {2 ** ri[0]:.4f} "
                 f"[{2 ** ri[1][0]:.4f}, {2 ** ri[1][1]:.4f}]")
    out[name] = rec
    print(line, flush=True)
print("order timed:", ", ".join(f"r{r} {n}" for r, n in order))
for i, s in enumerate(states):
    print(f"## machine state before replicate {i + 1}\n{s}", end="")
json.dump({"cells": out, "order": order, "states": states}, open("rootconfirm.json", "w"), indent=1)
