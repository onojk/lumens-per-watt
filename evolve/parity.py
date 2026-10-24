"""Parity: the Rust lamp core must match lamps.py exactly.

For every genome x number pair, both must agree on ops (or both miss), the factor found,
the test and hit counts, the winning stage, and a square-search win's k. Genomes: every
baseline, every champion of Runs 2-4, and random fine-deck genomes. Numbers: 28-48 bits.

Quadratic sieve (qs_pairs): the same fields plus qs's per-phase op breakdown, on the
acceptance numbers (40-60 bits), the Stage 2 numbers at 66/72/78 bits, numbers that make qs
retry with its next multiplier (asserted), gene variants, qs after another stage, a low
cap that stops it partway through a phase, random genomes drawn from a deck with qs in it, and
random genomes drawn from the wide qs ranges for runs after Run 6
(lamps.use_wide_qs_ranges: mc 0.05-12 log scale, bc 0.7-3.0), small sieve intervals
(mc 0.05-0.5 at 48-84 bits), where a factor-base prime wider than the
interval can start past its end and must not step (asserted for mc <= 0.25: lampcore's sieve
count wrapped there until it was guarded). Large primes (Stage 7, lc gene): lc = 1.0 identity
pairs, lc 1.2-2.0 variants at 40-84 bits, numbers that make an lc > 1 run retry (asserted),
td then qs with lc, and random genomes with a
random lc in every qs stage; the per-phase check includes lp. Caps chosen per number so the
run stops on its 10th lp charge (asserted: a miss whose last charge is lp).
Edge: both cores refuse qs on N >= 2^100 with an error, never a silent wrap.

Guards (guard_pairs): block flash whose two product trees can't fit in the budget, and p-1
whose bound is past 2^32 at 84 bits, both stopping before allocating (asserted on the Python
side; lampcore must finish them within a 256 MB address space), plus p-1 past 2^32 that runs to the cap through the
u128 prime-power loop and Python's segmented sieve, and caps on either side of the block-flash
threshold at 40 bits.

  python3 parity.py [random_genomes] [numbers_per_size]
"""
import json, math, os, random, sys
import qs
import lamps, blockflash
import subprocess
from lamps import run, LAST, rand_genome, rand_stage, use_fine_deck, cap_for, Meter, LAMPS
from fastlamps import semiprimes_pq, run_many, PHASES, BIN
from evolve import BASELINES

R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 4

def genomes():
    gs = dict(BASELINES)
    for d in ("", "run3/", "run4/"):
        try:
            res = json.load(open(d + "results.json"))
        except FileNotFoundError:
            continue
        for key, hist in res["runs"].items():
            gs[f"{d}champion {key}"] = hist[-1]["champ"]
    use_fine_deck()
    rng = random.Random(2026)
    deck = ["td", "sq", "ps", "rho", "pm1"]
    for i in range(R):
        gs[f"random {i}"] = rand_genome(deck, rng)
    return gs

QS = {"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}
# (seed, bits, index) of numbers on which the default qs retries (tuning seeds)
RETRY = [(550040, 40, i) for i in (116, 286, 294, 397, 472, 581, 604, 929, 986, 987, 1120, 1249)]

def qs_pairs():
    """Yields (label, genome, [(N, p, q)], cap, must_retry)."""
    for b in (40, 44, 48, 52, 56, 60):
        yield "qs acceptance", [QS], semiprimes_pq(b, 40, 770000 + b), 2 ** 29, False
    for b in (66, 72, 78):
        yield "qs stage 2", [QS], semiprimes_pq(b, 80, 990000 + b), 2 ** 29, False
    for seed, b, i in RETRY:
        yield "qs retry", [QS], semiprimes_pq(b, i + 1, seed)[i:], 2 ** 29, True
    variants = {"qs kc1 small base": [dict(QS, kc=1, bc=1.0, mc=2.0, tc=1.5)],
                "qs kc8 big base": [dict(QS, kc=8, bc=2.0, mc=6.0, tc=2.5)],
                "td then qs": [{"t": "td", "a": 0.1}, QS]}
    for b in (40, 48, 56, 60, 66, 72, 78):
        nums = semiprimes_pq(b, 8, 330000 + b)
        for name, g in variants.items():
            if b <= 60 or name != "qs kc1 small base":
                yield name, g, nums, 2 ** 29, False
        yield "qs low cap", [QS], nums, 2 ** 14, False
    for b in (48, 54, 60, 66, 72, 78, 84):
        nums = semiprimes_pq(b, 4, 1500000 + b)
        for mc in SMALL_MC:
            yield f"qs small mc {mc}", [dict(QS, kc=32, bc=1.1, mc=mc, tc=1.38)], nums, 2 ** 29, False
            yield f"qs small mc {mc} default genes", [dict(QS, mc=mc)], nums, 2 ** 29, False
        yield "qs wide corner bc 0.7 mc 0.05", [dict(QS, kc=32, bc=0.7, mc=0.05, tc=1.38)], nums, 2 ** 29, False
    for i, g in enumerate(random_qs_genomes()):
        for b in (28, 34, 40, 46, 54, 60):
            yield f"random qs {i}", g, semiprimes_pq(b, 2, 440000 + b), min(cap_for(b), 2 ** 22), False
    for i, g in enumerate(random_qs_genomes(30, wide=True)):
        for b in (34, 46, 60, 72, 84):
            yield f"random wide qs {i}", g, semiprimes_pq(b, 2, 1600000 + b), min(cap_for(b), 2 ** 24), False
    yield from lp_pairs()

TUNED = dict(QS, kc=32, bc=1.1, mc=0.25, tc=1.38)
# (genes, seed, bits, index) of numbers on which an lc > 1 run retries (searched, seed 550040)
LP_RETRY = [(dict(QS, lc=1.4), 550040, 40, i) for i in (38, 162, 515, 1445)] + \
           [(dict(TUNED, lc=1.4), 550040, 40, i) for i in (58, 62, 82, 108, 167, 169)] + \
           [(dict(QS, kc=8, bc=1.0, mc=2.0, tc=1.5, lc=1.8), 550040, 40, i) for i in (12, 30, 43, 52)]

class ChargeLog(dict):
    """qs.TRACE["ops"] that also remembers each charge: (phase, ops charged before it)."""
    def __init__(self):
        super().__init__(); self.log = []; self.total = 0
    def __setitem__(self, phase, value):
        n = value - self.get(phase, 0)
        self.log.append((phase, self.total)); self.total += n
        super().__setitem__(phase, value)

def lp_stop_caps(g, nums, nth=10):
    """Per number, the cap at which a qs-only genome stops on its nth lp charge (the total
    charged before that charge), so the run misses inside the lp phase."""
    out = []
    for N, p, q in nums:
        qs.TRACE = {"ops": ChargeLog()}
        run(g, N, 2 ** 29)
        lps = [before for phase, before in qs.TRACE["ops"].log if phase == "lp"]
        if len(lps) >= nth:
            out.append((N, p, q, lps[nth - 1]))
    qs.TRACE = None
    return out

def lp_pairs():
    """Stage 7: the lc gene (single large prime)."""
    for b in (48, 60, 72, 84):
        nums = semiprimes_pq(b, 6, 1800000 + b)
        yield "lc 1.0 identity default", [dict(QS, lc=1.0)], nums, 2 ** 29, False
        yield "lc 1.0 identity tuned", [dict(TUNED, lc=1.0)], nums, 2 ** 29, False
    for b in (40, 48, 56, 60, 66, 72, 78, 84):
        nums = semiprimes_pq(b, 6, 1800000 + b)
        for lc in (1.2, 1.4, 1.6, 2.0):
            yield f"lc {lc} tuned", [dict(TUNED, lc=lc)], nums, 2 ** 29, False
        yield "lc 1.4 default", [dict(QS, lc=1.4)], nums, 2 ** 29, False
        yield "td then qs lc 1.4", [{"t": "td", "a": 0.1}, dict(TUNED, lc=1.4)], nums, 2 ** 29, False
    for b in (48, 56, 60, 72):
        g = [dict(TUNED, lc=1.4)]
        for N, p, q, cap in lp_stop_caps(g, semiprimes_pq(b, 6, 1800000 + b)):
            yield "lc cap inside lp", g, [(N, p, q)], cap, False
    for g, seed, b, i in LP_RETRY:
        yield "lc retry", [g], semiprimes_pq(b, i + 1, seed)[i:], 2 ** 29, True
    rng = random.Random(2029)
    for i, g in enumerate(random_qs_genomes(30, wide=True)):
        g = [dict(st, lc=rng.uniform(1.0, 2.0)) if st["t"] == "qs" else st for st in g]
        for b in (34, 46, 60, 72, 84):
            yield f"random lc qs {i}", g, semiprimes_pq(b, 2, 1900000 + b), min(cap_for(b), 2 ** 24), False

SMALL_MC = (0.05, 0.1, 0.25, 0.5)

def non_stepping(trace):
    """Sieve roots, over every polynomial of the run, whose start lies past the interval."""
    return sum(1 for at in trace["attempts"] for poly in at["polys"]
               for p, r in poly["roots"] if (r + poly["M"]) % p >= 2 * poly["M"] + 1)

def random_qs_genomes(n=60, wide=False):
    """Random genomes from the full deck plus qs, each with at least one qs stage. wide: qs
    genes from the post-Run 6 ranges (restored afterwards, so other pairs are unchanged)."""
    use_fine_deck()
    rng = random.Random(2028 if wide else 2027)
    saved = (dict(lamps.QS_RANGES), dict(lamps.QS_SIGMA), set(lamps.QS_LOG))
    if wide:
        lamps.use_wide_qs_ranges()
    deck = ["td", "sq", "ps", "rho", "pm1", "qs"]
    out = []
    while len(out) < n:
        g = rand_genome(deck, rng)
        if not any(st["t"] == "qs" for st in g):
            g.insert(rng.randint(0, len(g)), rand_stage("qs", rng))
        out.append(g[:4])
    lamps.QS_RANGES.clear(); lamps.QS_RANGES.update(saved[0])
    lamps.QS_SIGMA.clear(); lamps.QS_SIGMA.update(saved[1])
    lamps.QS_LOG.clear(); lamps.QS_LOG.update(saved[2])
    return out

PS84 = {"t": "ps", "a": 0.5, "s": 0.4, "c": 4.0}
PS40 = {"t": "ps", "a": 0.45, "s": 0.3, "c": 1.0}
TD = {"t": "td", "a": 0.1}

def ops_before(g, N):
    """Ops charged by every stage of g but the last (they must all miss)."""
    m = Meter(2 ** 40)
    for st in g[:-1]:
        assert not LAMPS[st["t"]](N, st, m)
    return m.ops

def ps_threshold(g, N):
    """The smallest cap at which the block-flash guard lets g's last stage (ps) through."""
    st = g[-1]
    L = int(N ** st["a"]) + 1
    B = max(2, int(st["c"] * N ** st["s"]))
    return ops_before(g, N) + (B - 1) + ((L + B - 1) // B - 1)

def pm1_bound(st, N):
    return max(10, int(N ** st["b"]))

def guard_pairs():
    """Yields (label, genome, [(N, p, q)], cap, spy, allocates): spy is the Python function
    that does the big allocation, and allocates says whether the run must reach it."""
    n84 = semiprimes_pq(84, 4, 840084)
    for g in ([PS84], [TD, dict(PS84, s=0.35, c=2.0)]):
        for cap in (2 ** 26, 2 ** 28):
            for N, p, q in n84:
                assert ps_threshold(g, N) > cap
            yield "ps guard 84", g, n84, cap, "product_tree", False
    for N, p, q in semiprimes_pq(40, 4, 840040):
        g = [TD, PS40]
        t = ps_threshold(g, N)
        for cap, through in ((t - 1, False), (t, True), (t + 1, True), (2 ** 22, True)):
            yield "ps threshold 40", g, [(N, p, q)], cap, "product_tree", through
    for g in ([{"t": "pm1", "b": 0.39}], [{"t": "pm1", "b": 0.4}],
              [TD, {"t": "pm1", "b": 0.395}]):
        for N, p, q in n84:
            assert pm1_bound(g[-1], N) > 2 ** 32
        yield "pm1 guard 84", g, n84, 2 ** 26, "primes_segmented", False
    g = [{"t": "pm1", "b": 0.39}]
    cap = int(2 ** 28.5)
    for N, p, q in n84[:2]:
        B = pm1_bound(g[0], N)
        assert B > 2 ** 32 and B / math.log(B) < cap
    yield "pm1 past 2^32 84", g, n84[:2], cap, "primes_segmented", True

LIMIT_MB = 256

def rust_within(g, nums, cap):
    """True if lampcore finishes the batch with its address space limited to LIMIT_MB (a
    stage that allocated what the guard should have skipped would fail instead)."""
    import resource
    def limit():
        resource.setrlimit(resource.RLIMIT_AS, (LIMIT_MB << 20, LIMIT_MB << 20))
    text = json.dumps(g) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    r = subprocess.run([BIN], input=text, capture_output=True, text=True, preexec_fn=limit)
    return r.returncode == 0 and len(r.stdout.split("\n")) == len(nums) + 1

def check_guards():
    checked = mismatches = 0
    bounded = True
    for label, g, nums, cap, spy, allocates in guard_pairs():
        fast = run_many(g, nums, cap, inst=True)
        if not allocates:
            bounded &= rust_within(g, nums, cap)
        mod = blockflash if spy == "product_tree" else lamps
        orig = getattr(mod, spy)
        for (N, p, q), f in zip(nums, fast):
            calls = []
            setattr(mod, spy, lambda *a, **k: (calls.append(1), orig(*a, **k))[1])
            try:
                ops, d = run(g, N, cap)
            finally:
                setattr(mod, spy, orig)
            assert bool(calls) == allocates, (label, N, cap, "python reached", spy, bool(calls))
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"])
            checked += 1
            if slow != f:
                mismatches += 1
                if mismatches <= 10:
                    print("MISMATCH", label, N, cap, "python", slow, "rust", f)
    return checked, mismatches, bounded

def check_qs_limit():
    """N >= 2^100: lampcore exits with an error, lamps.py raises; neither returns a result."""
    N = (1 << 100) + 277
    text = json.dumps([QS]) + "\n100000\n" + f"{N} 3 5\n"
    r = subprocess.run([BIN], input=text, capture_output=True, text=True)
    rust_ok = r.returncode != 0 and "N < 2^100" in r.stderr and r.stdout == ""
    try:
        run([QS], N, 100000)
        py_ok = False
    except ValueError as e:
        py_ok = "N < 2^100" in str(e)
    return rust_ok and py_ok

def check_qs():
    checked = mismatches = 0
    wide = {}                                    # mc -> (pairs, non-stepping roots)
    for label, g, nums, cap, must_retry in qs_pairs():
        fast = run_many(g, nums, cap, inst=True, phases=True)
        for (N, p, q), f in zip(nums, fast):
            qs.TRACE = {"ops": ChargeLog()}
            ops, d = run(g, N, cap)
            ph = {k: qs.TRACE.get("ops", {}).get(k, 0) for k in PHASES}
            last_phase = qs.TRACE["ops"].log[-1][0] if qs.TRACE["ops"].log else None
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"], ph)
            if must_retry:
                assert len(qs.TRACE["attempts"]) > 1, ("expected a retry", N)
            if label == "lc cap inside lp":
                assert ops is None and last_phase == "lp", ("expected a miss inside lp", N, last_phase)
            if label.startswith("qs small mc"):
                mc, ns = g[0]["mc"], non_stepping(qs.TRACE)
                if mc <= 0.25:
                    assert ns > 0, ("expected a prime wider than the interval", label, N)
                pairs, total = wide.get(mc, (0, 0))
                wide[mc] = (pairs + 1, total + ns)
            checked += 1
            if slow != f:
                mismatches += 1
                if mismatches <= 10:
                    print("MISMATCH", label, N, "python", slow, "rust", f)
    print("qs small mc: " + ", ".join(f"mc {mc}: {pr} pairs, {ns} non-stepping roots"
                                       for mc, (pr, ns) in sorted(wide.items())))
    return checked, mismatches

if __name__ == "__main__":
    sizes = [28, 34, 40, 46]
    nums = {b: semiprimes_pq(b, PER, 90000 + b) for b in sizes}
    checked = mismatches = 0
    for name, g in genomes().items():
        for b in sizes:
            cap = min(cap_for(b), 2 ** 22)
            fast = run_many(g, nums[b], cap, inst=True)
            for (N, p, q), f in zip(nums[b], fast):
                ops, d = run(g, N, cap)
                slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"])
                checked += 1
                if slow != f:
                    mismatches += 1
                    if mismatches <= 10:
                        print("MISMATCH", name, b, N, "python", slow, "rust", f)
    print(f"checked {checked} genome x number pairs, mismatches {mismatches}")
    qc, qm = check_qs()
    print(f"qs: checked {qc} genome x number pairs (ops, factor, tests, hits, stage, k, "
          f"per-phase ops), mismatches {qm}")
    gc, gm, bounded = check_guards()
    print(f"guards: checked {gc} genome x number pairs (block flash and p-1 past 2^32 at 84 bits), "
          f"mismatches {gm}; lampcore runs the stop-before-allocating pairs within "
          f"{LIMIT_MB} MB: {'yes' if bounded else 'NO'}")
    limit = check_qs_limit()
    print(f"qs on N >= 2^100: both cores refuse with an error: {'yes' if limit else 'NO'}")
    sys.exit(1 if mismatches or qm or gm or not bounded or not limit else 0)
