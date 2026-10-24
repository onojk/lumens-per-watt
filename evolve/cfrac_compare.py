"""CFRAC comparison (NOTES.md, "CFRAC as a second relation source"; PLAN.md, "Relation
economy"): CFRAC alone, tuned qs, and qs + CFRAC into one ledger, on the Run 6 ACCEPT numbers
(run6_accept.SETS: the Stage 2 numbers at 72 and 78 bits, semiprimes_pq(84, 80, 1300084)),
cap 2^28.

Genomes: tuned qs (kc 32, bc 1.1, mc 0.25, tc 1.38); CFRAC alone with tuned qs's kc and bc
(the genes the prediction assumes); qs + CFRAC with the same genes, one k and one ledger per
attempt, as a fixed split (Stage 9's race element does not exist yet): CFRAC fills the first
cs * (F + 10) relations, then the qs sieve fills the rest. cs in {0.1, 0.25, 0.5}, fixed
before measurement and all reported, none tuned. Identity check first: at cs = 0 the split
card skips CFRAC entirely and must equal tuned qs (lampcore) on every ACCEPT number: ops,
factor, tests, hits, every phase. The ledger check is off for all of them
(both sources are correct by construction; NOTES.md, ledger entry).

Ops and phases: lampcore for tuned qs and CFRAC alone; lamps.py for the split (Python
only: it is a harness composition of two accepted sources, not a card).

Per size: log2(mean ops) and the worst case with run6_accept.py's bootstrap (index
250/9749), misses, mean ops per phase, growth per bit 72 -> 84 (least squares on log2 mean),
and the paired log2 ratio of total ops against tuned qs on the same numbers (supplementary).
Prediction, stated before measurement: CFRAC alone loses by ~6x at 72 bits and ~10x at 84
(uncertain by 2-3x either way), with steeper growth; qs + CFRAC no better than qs alone.

  python3 cfrac_compare.py [workers]  -> cfrac_compare.json
"""
import json, math, random, sys
from multiprocessing import Pool
import cfrac, qs
from ledger import Charger, Ledger
from lamps import Meter, Budget, KS_PRIMES, ks_score
from fastlamps import semiprimes_pq, run_many, PHASES
from revalidate import bootstrap, R
from run6_accept import bootstrap_worst, SETS, CAP

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
TUNED = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}
CF = {"t": "cfrac", "kc": 32, "bc": 1.1}
SPLITS = (0.1, 0.25, 0.5)
IDENTITY = 0.0                                     # the split card at cs = 0 must be tuned qs

def lamp_split(N, g, cs, m, tr):
    """qs + CFRAC into one ledger per k: CFRAC first, to cs * need relations, then qs.
    Charges exactly those of the two sources and the ledger (no new charges)."""
    ch = Charger(m, tr)
    if N % 2 == 0:
        return 2
    kc = max(1, int(g["kc"]))
    ch.charge("mult", kc * len(KS_PRIMES))
    ranked = sorted(range(1, kc + 1), key=lambda kk: (-ks_score(kk, N), kk))
    lnN = math.log(N)
    B = max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    for k in ranked:
        led = Ledger(N, k, B, ch, None)
        d = led.build_base()
        if d:
            return d
        if cs > 0:                             # cs = 0: tuned qs, op for op (checked below)
            cfrac.cf_source(N, k, g, led, ch, None, until=math.ceil(cs * led.need))
        if not led.full:
            d = qs.sieve_source(N, k, g, led, ch, None)
            if d:
                return d
        if led.full:
            d = led.solve()
            if d:
                return d
    return None

def split_job(args):
    cs, bits, N = args
    m = Meter(CAP)
    tr = {"ops": {}}
    try:
        d = lamp_split(N, TUNED, cs, m, tr)
        ops = m.ops if d else None
    except Budget:
        d = ops = None
    return cs, bits, N, ops, {ph: tr["ops"].get(ph, 0) for ph in PHASES}, (d, m.tests, m.hits)

def paired(a, b):
    rng = random.Random(2026)
    n = len(a)
    vals = []
    for _ in range(R):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx)))
    vals.sort()
    return math.log2(sum(a) / sum(b)), [vals[int(0.025 * R)], vals[int(0.975 * R) - 1]]

def cell(all_ops, phases):
    ops = [o for o in all_ops if o is not None]
    capped = [CAP if o is None else o for o in all_ops]
    return {"mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
            "ci95": list(bootstrap(ops)) if ops else None,
            "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
            "misses": len(all_ops) - len(ops),
            "phase_mean": {ph: sum(p[ph] for p in phases) / len(phases) for ph in PHASES}}, capped

if __name__ == "__main__":
    nums = {b: semiprimes_pq(b, c, s) for b, (c, s) in SETS.items()}
    names = ["tuned qs", "cfrac alone"] + [f"qs + cfrac, cs {cs}" for cs in SPLITS]
    out = {"cap_log2": 28, "sets": {str(b): {"count": c, "seed": s} for b, (c, s) in SETS.items()},
           "genomes": {"tuned qs": [TUNED], "cfrac alone": [CF], "splits": SPLITS},
           "results": {n: {} for n in names}, "paired_log2_ratio_vs_tuned_qs": {n: {} for n in names[1:]}}
    with Pool(WORKERS) as pool:
        split = pool.map(split_job, [(cs, b, N) for cs in (IDENTITY,) + SPLITS for b in nums
                                     for N, p, q in nums[b]], chunksize=2)
    ident = bad = 0
    for b in nums:
        rust = run_many([TUNED], nums[b], CAP, phases=True)
        rows = [x for x in split if x[0] == IDENTITY and x[1] == b]
        for r, x in zip(rust, rows):
            ident += 1
            if (r[0], r[1], r[2], r[3], r[4]) != (x[3], x[5][0], x[5][1], x[5][2], x[4]):
                bad += 1
                print("IDENTITY MISMATCH", b, x[2], r, x)
    print(f"split card at cs = 0 vs tuned qs: {ident} numbers (ops, factor, tests, hits, every phase), "
          f"mismatches {bad}")
    assert bad == 0
    out["identity_cs0"] = {"numbers": ident, "mismatches": bad}
    capped = {}
    for b in nums:
        for name, g in (("tuned qs", [TUNED]), ("cfrac alone", [CF])):
            r = run_many(g, nums[b], CAP, phases=True)
            out["results"][name][str(b)], capped[name, b] = cell([x[0] for x in r], [x[4] for x in r])
        for cs in SPLITS:
            rows = [x for x in split if x[0] == cs and x[1] == b]
            assert [x[2] for x in rows] == [N for N, p, q in nums[b]]
            name = f"qs + cfrac, cs {cs}"
            out["results"][name][str(b)], capped[name, b] = cell([x[3] for x in rows], [x[4] for x in rows])
        for name in names[1:]:
            out["paired_log2_ratio_vs_tuned_qs"][name][str(b)] = paired(capped[name, b], capped["tuned qs", b])
    xs = list(nums)
    for name in names:
        ys = [out["results"][name][str(b)]["mean_log2"] for b in xs]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        out["results"][name]["per_bit"] = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                                           / sum((x - mx) ** 2 for x in xs))
        print(f"\n{name}  (growth {out['results'][name]['per_bit']:.3f} log2-ops per bit, 72->84)")
        for b in xs:
            c = out["results"][name][str(b)]
            print(f"  {b} bits: mean {c['mean_log2']:.2f} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]"
                  f"  worst {c['worst_log2']:.2f} [{c['worst_ci95'][0]:.2f}, {c['worst_ci95'][1]:.2f}]"
                  f"  misses {c['misses']}")
            print("           phases (log2 mean): " + "  ".join(
                f"{ph} {math.log2(v):.2f}" for ph, v in c["phase_mean"].items() if v))
    print("\npaired log2(total ops / tuned qs's) [95% CI], same numbers (supplementary):")
    for name in names[1:]:
        for b in xs:
            v, ci = out["paired_log2_ratio_vs_tuned_qs"][name][str(b)]
            print(f"  {name:20s} {b} bits: {v:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]  ({2 ** v:.2f}x tuned qs's ops)")
    json.dump(out, open("cfrac_compare.json", "w"), indent=1)
