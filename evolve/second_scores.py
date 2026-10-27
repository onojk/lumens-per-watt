"""Second scores under the free-2-corrected meter (NOTES.md, "Second scores under the corrected meter"; the adopted
rule: the original score is kept, a second score under the corrected meter is reported beside it). Counts only, no
timing. Every affected comparison is priced twice: with the uncorrected binary (LAMPCORE_UNCORRECTED, built at
d269cc8, before 6031239; it must reproduce the recorded originals) and with the corrected binary (6031239).
Ratios: mean per number, paired 95% bootstrap (10,000; random.Random(2026), the runners' exact resamples); robust
ratio = max over pricings; (e) better / worse / undecided.
  LAMPCORE_UNCORRECTED=<binary> python3 second_scores.py -> second_scores.json, stdout
"""
import json, math, os, random, statistics
import numpy as np
import partition as P, sizescale2 as S2, fastlamps
from fastlamps import run_many
from lctest import ref, cost, PT, bnd

R = 10000
OLD, NEW = os.environ["LAMPCORE_UNCORRECTED"], fastlamps.BIN

_idx = {}
def idx(n):
    if n not in _idx:
        rng = random.Random(2026)   # the runners reseed per comparison, so the resamples are the same for every pair
        _idx[n] = np.array([[rng.randrange(n) for _ in range(n)] for _ in range(R)])
    return _idx[n]

def paired(a, b):
    a, b = np.array(a), np.array(b)
    I = idx(len(a))
    vals = np.sort(np.log2(a[I].sum(1) / b[I].sum(1)))
    return a.sum() / b.sum(), [2 ** vals[int(0.025 * R)], 2 ** vals[int(0.975 * R) - 1]]

def priced(g, nums, binary):
    fastlamps.BIN = binary
    rs = run_many([g], nums, P.QS_CAP, types=True)
    fastlamps.BIN = NEW
    assert all(r[1] is not None for r in rs)
    return {Pn: [cost(r[4], Pn) for r in rs] for Pn in PT}

cache = {}
def cell(bits, name, g, nums):
    key = (bits, name)
    if key not in cache:
        cache[key] = {"old": priced(g, nums, OLD), "new": priced(g, nums, NEW)}
    return cache[key]

def compare(bits, a, b):
    out = {}
    for m in ("old", "new"):
        pr = {Pn: paired(a[m][Pn], b[m][Pn]) for Pn in PT}
        e = ("better" if all(v[1][1] < 1 for v in pr.values()) else "worse" if all(v[1][0] > 1 for v in pr.values()) else "undecided")
        out[m] = {"ratio": {Pn: v[0] for Pn, v in pr.items()}, "ci95": {Pn: v[1] for Pn, v in pr.items()},
                  "robust": max(v[0] for v in pr.values()), "e": e}
    return out

LB96 = math.log2(1752.0)
runs = []
# (run, bits, cell name, genes, base name, base genes)
def plan():
    p = []
    g = ref(96); ga = dict(g, goff=1); gb = dict(ga, confirm="root"); rt = dict(g, confirm="root")
    for d, nm in ((5, "(iii) pp 10, +5 bits"),):
        p.append(("stage H2", 96, nm, dict(g, pp=10, tc=g["tc"] - d / LB96), "reference", g))
    for d in (3, 1, 2):
        p.append(("stage H2", 96, f"pp 3, +{d} bit(s)" + (" (iv)" if d == 3 else ""), dict(g, pp=3, tc=g["tc"] - d / LB96), "reference", g))
    for d in range(5):
        p.append(("root-confirm", 96, f"root + pp 3, +{d}", dict(rt, pp=3, tc=g["tc"] - d / LB96), "reference", g))
    p.append(("i032-2prime", 96, "2'b+pp3", dict(gb, pp=3), "2'a", ga))
    p.append(("i032-2prime", 96, "2'b+pp3", dict(gb, pp=3), "REF (information)", g))
    for d in range(3):
        p.append(("pp3-gap-and-shift", 96, f"2'b+pp3 +{d}", dict(gb, pp=3, tc=g["tc"] - d / LB96), "2'a", ga))
    for d in (1, 2, 3):
        p.append(("shift-past-2 (A)", 96, f"2'b+pp3 +{d}", dict(gb, pp=3, tc=g["tc"] - d / LB96), "2'a", ga))
        p.append(("shift-past-2 (A)", 96, f"2'b+pp3 +{d}", dict(gb, pp=3, tc=g["tc"] - d / LB96), "2'b (information)", gb))
    for bits in (72, 84):
        h = ref(bits); ha = dict(h, goff=1); hb = dict(ha, confirm="root")
        lb = math.log2(statistics.mean(bnd(N, h) for N, _, _ in S2.map_nums(bits)))
        for d in range(3):
            p.append(("shift-72-84 (B)", bits, f"2'b+pp3 +{d}", dict(hb, pp=3, tc=h["tc"] - d / lb), "2'a", ha))
    p.append(("2b-sizes", 96, "2'b+pp3 +0", dict(gb, pp=3), "2'b", gb))
    return p

out = []
for run, bits, nm, gc, bn, gbase in plan():
    nums = S2.map_nums(bits)
    a = cell(bits, json.dumps(gc, sort_keys=True), gc, nums)
    b = cell(bits, json.dumps(gbase, sort_keys=True), gbase, nums)
    c = compare(bits, a, b)
    out.append({"run": run, "bits": bits, "cell": nm, "base": bn, **c})
    f = lambda m: (" / ".join(f"{c[m]['ratio'][Pn]:.4f}" for Pn in PT) + f"; robust {c[m]['robust']:.4f}; {c[m]['e']}")
    print(f"{run} | {bits} | {nm} vs {bn} | original {f('old')} | corrected {f('new')}", flush=True)
json.dump(out, open("second_scores.json", "w"), indent=1)
