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
count wrapped there until it was guarded). On-demand A selection (a_mode = on_demand): the
reference, new, N51-0917 and default genes at 48-90 bits, a low cap, the retry numbers and
random wide genomes. sort_charge = 1: both a_modes, a retry, a low cap, random wide genomes. Large primes (Stage 7, lc gene): lc = 1.0 identity
pairs, lc 1.2-2.0 variants at 40-84 bits, numbers that make an lc > 1 run retry (asserted),
td then qs with lc, and random genomes with a
random lc in every qs stage; the per-phase check includes lp. Caps chosen per number so the
run stops on its 10th lp charge (asserted: a miss whose last charge is lp). Ledger relation
check ("check": 1, check_pairs): default, tuned and tuned + lc 1.4 qs at 40-72 bits, a number
on which the check rejects a trivial combined relation (asserted), caps that stop inside the
check phase (asserted), and random genomes with the check on; the per-phase check includes it.
CFRAC (cfrac_pairs): the cfrac acceptance numbers (40-60 bits), 66/72 bits, numbers that make
it retry (asserted), period ends at 20-28 bits (asserted, with kc 1 a miss and with kc 4 the
next k), caps that stop inside cf_step and inside cf_td (asserted), td then cfrac, cfrac with
the check on, and random kc/bc genomes; the per-phase check includes cf_step and cf_td.
ECM (ecm_pairs): the ecm acceptance numbers, balanced (40-84 bits) and unbalanced (24-32-bit
factor at 72-84), a setup factor (s0 = p: asserted), a degenerate first curve (s0 = N:
asserted), curves that find both factors at once in stage 1 and in stage 2 (asserted), no
stage 2 (b2 = 0), a curve limit that ends in a miss, caps inside each of ecm_setup, ecm_s1,
ecm_s2 and ecm_gcd (asserted), td then ecm, and random b1/b2/s0 genomes; the per-phase check
includes the four ecm phases.
Edge: both cores refuse qs on N >= 2^100 with an error, never a silent wrap.

Per-type counts (check_types): on every pair above (general, qs, guards, race, ob), lampcore
--types equals Python's per-stage split (lamps.TYPES), and on every solved run the counts sum
to its ops. Mutation: for each type in use, lampcore's output with that type dropped or
doubled (LAMPCORE_TYPES_MUTATE) must be caught.

Race (race_pairs, Stage 9): every ordered pair of lamp types (td, sq, ps, rho, pm1, qs, qs lc
1.4, cfrac, ecm) at 32-40 bits under three slice settings; the Stage 9 comparison races
(race(ECM, qs + lc 1.4), race(rho, qs + lc 1.4), race(ECM, N51-0917's qs)) at 54-84 bits and
on unbalanced numbers, at 2^8 / 2^10 / 2^14 and unequal slices; a disabled side (sa or sb = 0);
a side that ends without a factor (the other runs alone, asserted); both sides ending, so the
next stage runs (asserted); a race after another stage; caps that stop mid-race (asserted
misses); and random races of random stages and slices. Fields: the usual ones, per-phase ops
summed over both sides, and per-side ops and switches. Both cores refuse a nested race and
sa = sb = 0 with an error.

Op budget (ob_pairs): [X with ob, then rho or qs] for every lamp X at 28-84 bits, with ob = 0, 1,
7, 100, 1,000, 10^4, 10^5 and 2^40 (skipped, below and past each stage's natural length);
budgets on two stages in a row; ob on a final qs; a cap inside a budgeted stage (asserted
miss); and random budgeted genomes. Fields: the usual ones and per-phase ops. Both cores
refuse a negative or non-integer ob and an ob on a race or its side with an error.

Guards (guard_pairs): block flash whose two product trees can't fit in the budget (the cap,
or a stage op budget far below a cap of 2^40, which ends only that stage), and p-1
whose bound is past 2^32 at 84 bits, both stopping before allocating (asserted on the Python
side; lampcore must finish them within a 256 MB address space), plus p-1 past 2^32 that runs to the cap through the
u128 prime-power loop and Python's segmented sieve, and caps on either side of the block-flash
threshold at 40 bits.

  python3 parity.py [random_genomes] [numbers_per_size]
"""
import json, math, os, random, sys
import qs, cfrac, ecm
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
    # the pm1 absolute bound (NOTES.md, "(A1)"), alone and after rho with a budget
    for B in (256, 2048, 32768):
        gs[f"pm1 B {B}"] = [{"t": "pm1", "b": 0.2, "B": B}]
        gs[f"rho then pm1 B {B}"] = [{"t": "rho", "c": 1, "b": 64, "ob": 300}, {"t": "pm1", "b": 0.2, "B": B}]
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
    # a_mode = on_demand (NOTES.md, "On-demand A selection"): the reference genes, the new genes,
    # N51-0917's qs and the default genes at 48-90 bits, a low cap, the retry numbers, and random
    # wide genomes with on_demand in every qs stage
    new_genes = dict(QS, kc=4, bc=0.8993889783377338, mc=0.7340990893362095, tc=1.1044621542694246, lc=1.6612269841697611)
    for b in (48, 60, 66, 72, 78, 84, 90):
        nums = semiprimes_pq(b, 6, 2100000 + b)
        for name, g0 in (("tuned lc 1.4", dict(TUNED, lc=1.4)), ("new genes", new_genes), ("N51", N51_QS), ("default", QS)):
            yield f"qs on_demand {name}", [dict(g0, a_mode="on_demand")], nums, 2 ** 29, False
        yield "qs on_demand low cap", [dict(TUNED, lc=1.4, a_mode="on_demand")], nums, 2 ** 14, False
    for seed, b, i in RETRY:
        yield "qs on_demand retry", [dict(QS, a_mode="on_demand")], semiprimes_pq(b, i + 1, seed)[i:], 2 ** 29, False
    for i, g in enumerate(random_qs_genomes(15, wide=True)):
        g = [dict(st, a_mode="on_demand") if st["t"] == "qs" else st for st in g]
        for b in (46, 60, 72, 84):
            yield f"random wide qs on_demand {i}", g, semiprimes_pq(b, 2, 2200000 + b), min(cap_for(b), 2 ** 24), False
    # sort_charge = 1 (NOTES.md, "The sort_charge option"): both a_modes, reference and new genes,
    # a retry (the multiplier sort once, the pool sorts per attempt), a low cap, random wide genomes
    for b in (48, 60, 72, 84):
        nums = semiprimes_pq(b, 4, 2300000 + b)
        for mode in ("enumerate", "on_demand"):
            yield f"qs sort_charge {mode}", [dict(TUNED, lc=1.4, a_mode=mode, sort_charge=1)], nums, 2 ** 29, False
            yield f"qs sort_charge {mode} new genes", [dict(new_genes, a_mode=mode, sort_charge=1)], nums, 2 ** 29, False
        yield "qs sort_charge low cap", [dict(TUNED, lc=1.4, a_mode="on_demand", sort_charge=1)], nums, 2 ** 13, False
    for seed, b, i in RETRY[:4]:
        yield "qs sort_charge retry", [dict(QS, a_mode="on_demand", sort_charge=1)], semiprimes_pq(b, i + 1, seed)[i:], 2 ** 29, False
    for i, g in enumerate(random_qs_genomes(10, wide=True)):
        g = [dict(st, a_mode="on_demand", sort_charge=1) if st["t"] == "qs" else st for st in g]
        for b in (46, 60, 72):
            yield f"random wide qs sort_charge {i}", g, semiprimes_pq(b, 2, 2400000 + b), min(cap_for(b), 2 ** 24), False
    yield from lp_pairs()
    yield from check_pairs()
    yield from cfrac_pairs()
    yield from ecm_pairs()

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

def lp_stop_caps(g, nums, nth=10, phase="lp"):
    """Per number, the cap at which a qs-only genome stops on its nth charge to `phase` (the
    total charged before that charge), so the run misses inside that phase."""
    out = []
    for N, p, q in nums:
        tr = new_trace()
        run(g, N, 2 ** 29)
        lps = [before for ph, before in tr["ops"].log if ph == phase]
        if len(lps) >= nth:
            out.append((N, p, q, lps[nth - 1]))
    qs.TRACE = cfrac.TRACE = ecm.TRACE = None
    return out

def new_trace():
    """One trace shared by qs and cfrac, so a genome with both adds up as lampcore does."""
    tr = {"ops": ChargeLog()}
    qs.TRACE = cfrac.TRACE = ecm.TRACE = tr
    return tr

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
    # lc above 2.0 (NOTES.md, "(A2)": clamp 3.0, composite cofactors filed like primes), and the
    # pm1 absolute bound "B" ("(A1)") alone and in a corrected-card pipeline
    card = {"a_mode": "on_demand", "sort_charge": 1}
    for b in (48, 60, 72, 84, 96):
        nums = semiprimes_pq(b, 4, 2500000 + b)
        for lc in (2.3, 2.5, 3.0):
            yield f"lc {lc} tuned", [dict(TUNED, lc=lc)], nums, 2 ** 29, False
            yield f"lc {lc} tuned corrected card", [dict(TUNED, lc=lc, kc=48, **card)], nums, 2 ** 29, False
        yield "lc 2.5 low cap", [dict(TUNED, lc=2.5, **card)], nums, 2 ** 14, False
        yield "rho pm1 B ecm qs pipeline", [{"t": "td", "a": 0.5, "ob": 0}, {"t": "rho", "c": 1, "b": 64, "ob": 1448},
                                             {"t": "pm1", "b": 0.2, "B": 2048, "ob": 4096},
                                             {"t": "ecm", "b1": 1.0, "b2": 50, "ob": 17867}, dict(TUNED, lc=2.2, kc=40, **card)], nums, 2 ** 29, False
    rng = random.Random(2031)
    for i, g in enumerate(random_qs_genomes(15, wide=True)):
        g = [dict(st, lc=rng.uniform(2.0, 3.0), kc=rng.randint(1, 64)) if st["t"] == "qs" else st for st in g]
        for b in (46, 60, 72, 84):
            yield f"random lc>2 qs {i}", g, semiprimes_pq(b, 2, 2600000 + b), min(cap_for(b), 2 ** 24), False

def check_pairs():
    """The ledger's charged relation check (opt-in, "check": 1)."""
    for b in (40, 48, 56, 60, 66, 72):
        nums = semiprimes_pq(b, 6, 2000000 + b)
        for name, g in (("default", QS), ("tuned", TUNED), ("tuned lc 1.4", dict(TUNED, lc=1.4))):
            yield f"check on {name}", [dict(g, check=1)], nums, 2 ** 29, False
    yield "check trivial reject", [dict(TUNED, lc=1.4, check=1)], semiprimes_pq(52, 2, 11)[1:], 2 ** 29, False
    for b in (48, 60):
        g = [dict(TUNED, lc=1.4, check=1)]
        for N, p, q, cap in lp_stop_caps(g, semiprimes_pq(b, 4, 2000000 + b), 25, "check"):
            yield "check cap inside check", g, [(N, p, q)], cap, False
    rng = random.Random(2030)
    for i, g in enumerate(random_qs_genomes(20, wide=True)):
        g = [dict(st, lc=rng.uniform(1.0, 2.0), check=1) if st["t"] == "qs" else st for st in g]
        for b in (34, 46, 60, 72):
            yield f"random check qs {i}", g, semiprimes_pq(b, 2, 2100000 + b), min(cap_for(b), 2 ** 24), False

CF = {"t": "cfrac", "kc": 32, "bc": 1.1}
CF_RETRY = (6, 8, 10, 17, 20, 21)                # indices into semiprimes_pq(40, ., 550040)
CF_PERIOD = {20: (39, 45, 48), 24: (27, 31, 54), 28: (132, 136, 178)}   # seed 560000 + bits, kc 1
CF_PERIOD_NEXT = {20: (43, 64, 81), 24: (27, 133, 154), 28: (132, 352, 467)}  # kc 4: period end, then next k

def cfrac_pairs():
    """The CFRAC card (cfrac.py): a second relation source into the ledger."""
    for b in (40, 44, 48, 52, 56, 60):
        nums = semiprimes_pq(b, 8, 770000 + b)
        yield "cfrac acceptance", [CF], nums, 2 ** 29, False
        yield "cfrac default genes", [{"t": "cfrac"}], nums[:4], 2 ** 29, False
    for b in (66, 72):
        yield "cfrac large", [CF], semiprimes_pq(b, 4, 2200000 + b), 2 ** 29, False
    for i in CF_RETRY:
        yield "cfrac retry", [CF], semiprimes_pq(40, i + 1, 550040)[i:], 2 ** 29, True
    for b, idx in CF_PERIOD.items():
        all_n = semiprimes_pq(b, max(idx) + 1, 560000 + b)
        for i in idx:
            yield "cfrac period end", [dict(CF, kc=1, bc=3.0)], all_n[i:i + 1], 2 ** 29, False
    for b, idx in CF_PERIOD_NEXT.items():
        all_n = semiprimes_pq(b, max(idx) + 1, 560000 + b)
        for i in idx:
            yield "cfrac period end kc 4", [dict(CF, kc=4, bc=3.0)], all_n[i:i + 1], 2 ** 29, False
    for b in (48, 60):
        for phase, nth in (("cf_step", 200), ("cf_td", 200)):
            for N, p, q, cap in lp_stop_caps([CF], semiprimes_pq(b, 3, 2300000 + b), nth, phase):
                yield f"cfrac cap inside {phase}", [CF], [(N, p, q)], cap, False
    for b in (40, 52, 60):
        nums = semiprimes_pq(b, 4, 2400000 + b)
        yield "td then cfrac", [{"t": "td", "a": 0.1}, CF], nums, 2 ** 29, False
        yield "cfrac check on", [dict(CF, check=1)], nums, 2 ** 29, False
    rng = random.Random(2031)
    for i in range(20):
        g = [{"t": "cfrac", "kc": rng.randint(1, 32), "bc": round(rng.uniform(0.7, 3.0), 3)}]
        for b in (34, 46, 60):
            yield f"random cfrac {i}", g, semiprimes_pq(b, 2, 2500000 + b), min(cap_for(b), 2 ** 24), False

ECM_BOTH = {"s1": (36, (27, 73, 94)), "s2": (40, (3, 6, 9))}   # semiprimes_pq(bits, ., 3200000 + bits)

def ecm_pairs():
    """The ECM card (ecm.py)."""
    from fastlamps import semiprimes_unbalanced
    E = {"t": "ecm"}
    for b in range(40, 85, 4):
        yield "ecm balanced", [E], semiprimes_pq(b, 6, 2700000 + b), 2 ** 29, False
    for b in (72, 84):
        for pb in (24, 32):
            yield "ecm unbalanced", [E], semiprimes_unbalanced(b, pb, 4, 2800000 + 100 * pb + b), 2 ** 29, False
    for b in (40, 56, 72):
        for N, p, q in semiprimes_pq(b, 2, 3300000 + b):
            yield "ecm setup factor", [dict(E, s0=p)], [(N, p, q)], 2 ** 29, False
        for N, p, q in semiprimes_pq(40, 2, 3300040 + b):
            yield "ecm degenerate", [dict(E, s0=N)], [(N, p, q)], 2 ** 29, False
    for st, (b, idx) in ECM_BOTH.items():
        all_n = semiprimes_pq(b, max(idx) + 1, 3200000 + b)
        for i in idx:
            yield f"ecm both {st}", [E], all_n[i:i + 1], 2 ** 29, False
    for b in (48, 72):
        nums = semiprimes_pq(b, 4, 3400000 + b)
        yield "ecm no stage 2", [dict(E, b2=0)], nums, 2 ** 29, False
        yield "ecm curve limit", [dict(E, b1=0.1, b2=0, curves=2)], nums, 2 ** 29, False
        yield "td then ecm", [{"t": "td", "a": 0.1}, E], nums, 2 ** 29, False
    for b in (48, 72):
        for phase, nth in (("ecm_setup", 25), ("ecm_s1", 5000), ("ecm_s2", 3000), ("ecm_gcd", 3)):
            for N, p, q, cap in lp_stop_caps([E], semiprimes_pq(b, 3, 3500000 + b), nth, phase):
                yield f"ecm cap inside {phase}", [E], [(N, p, q)], cap, False
    rng = random.Random(2032)
    for i in range(20):
        g = [{"t": "ecm", "b1": round(rng.uniform(0.25, 4.0), 3), "b2": rng.choice([0, 10, 25, 50, 100, 200]),
              "s0": rng.randint(6, 1000)}]
        for b in (34, 52, 72):
            yield f"random ecm {i}", g, semiprimes_pq(b, 2, 3600000 + b), min(cap_for(b), 2 ** 24), False

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
    # a small op budget makes the precheck binding although the cap is far above it
    QS84 = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}
    yield "ps ob guard 84", [dict(PS84, ob=1000), QS84], n84, 2 ** 40, "product_tree", False
    yield "pm1 ob guard 84", [{"t": "pm1", "b": 0.39, "ob": 1000}, QS84], n84, 2 ** 40, "primes_segmented", False

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
            if "ob guard" in label:
                assert LAST["stage"] == 1 and [x[:4] for x in LAST["ob"]] == [(0, 1000, 0, True)], (label, N, LAST["ob"])
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
            tr = new_trace()
            ops, d = run(g, N, cap)
            ph = {k: tr["ops"].get(k, 0) for k in PHASES}
            last_phase = tr["ops"].log[-1][0] if tr["ops"].log else None
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"], ph)
            if must_retry:
                assert len(qs.TRACE["attempts"]) > 1, ("expected a retry", N)
            if label == "lc cap inside lp":
                assert ops is None and last_phase == "lp", ("expected a miss inside lp", N, last_phase)
            if label.startswith("cfrac cap inside "):
                want = label.rsplit(" ", 1)[1]
                assert ops is None and last_phase == want, ("expected a miss inside " + want, N, last_phase)
            if label.startswith("cfrac period end"):
                assert any(at.get("period_end") for at in tr["attempts"]), ("expected a period end", N)
                if label == "cfrac period end kc 4":
                    assert len(tr["attempts"]) > 1 and tr["attempts"][0]["period_end"], \
                        ("expected the next k after a period end", N)
            if label.startswith("ecm cap inside "):
                want = label.rsplit(" ", 1)[1]
                assert ops is None and last_phase == want, ("expected a miss inside " + want, N, last_phase)
            ends = [cv["end"] for cv in tr.get("curves", [])]
            if label == "ecm setup factor":
                assert ends == ["setup factor"], ("expected a setup factor", N, ends)
            if label == "ecm degenerate":
                assert ends[0] == "degenerate", ("expected a degenerate first curve", N, ends)
            if label.startswith("ecm both "):
                assert label[-2:] + " both" in ends, ("expected both factors at once", N, ends)
            if label == "ecm curve limit":
                assert ops is None and len(ends) == 2, ("expected a miss after 2 curves", N, ends)
            if label == "check cap inside check":
                assert ops is None and last_phase == "check", ("expected a miss inside check", N, last_phase)
            if label == "check trivial reject":
                assert sum(at.get("rejected", 0) for at in qs.TRACE["attempts"]) > 0, ("expected a rejection", N)
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

import race
N51_QS = {"t": "qs", "kc": 32, "bc": 1.1275106842116758, "mc": 1.0028451156262428, "tc": 1.378994531313155}
RACE_STAGES = {
    "td": {"t": "td", "a": 0.5},
    "sq": {"t": "sq", "mode": "seqm", "mult": 60, "k": 0.3, "w": 0.25, "c": 1.2, "ksq": False, "r": 64},
    "ps": {"t": "ps", "a": 0.5, "s": 0.25, "c": 1.0},
    "rho": {"t": "rho", "c": 1, "b": 64},
    "pm1": {"t": "pm1", "b": 0.3},
    "qs": {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38},
    "qs lc 1.4": {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4},
    "cfrac": {"t": "cfrac", "kc": 32, "bc": 1.1},
    "ecm": {"t": "ecm", "b1": 1.0, "b2": 50},
}
TD_END = {"t": "td", "a": 0.05}          # ends without a factor in a few ops

def R_(a, b, sa, sb):
    return {"t": "race", "a": a, "b": b, "sa": sa, "sb": sb}

def race_pairs():
    """(label, genome, numbers, cap, assertion on the Python run or None)."""
    nums = {b: semiprimes_pq(b, 2, 2600000 + b) for b in (32, 36, 40)}
    for i, (x, A) in enumerate(RACE_STAGES.items()):
        for j, (y, B) in enumerate(RACE_STAGES.items()):
            b = (32, 36, 40)[(i + j) % 3]
            for sa, sb in ((16, 16), (256, 1024), (4096, 256)):
                yield f"pair {x}/{y}", [R_(A, B, sa, sb)], nums[b], 2 ** 26, None
    E, Q, RH = RACE_STAGES["ecm"], RACE_STAGES["qs lc 1.4"], RACE_STAGES["rho"]
    for b in (54, 72, 84):
        ns = semiprimes_pq(b, 2, 2700000 + b)
        for s in (256, 1024, 16384):
            for A, B in ((E, Q), (RH, Q), (E, N51_QS)):
                yield f"stage 9 {b} {s}", [R_(A, B, s, s)], ns, 2 ** 28, None
            yield f"stage 9 unequal {b} {s}", [R_(E, Q, s, 6 * s)], ns, 2 ** 28, None
    from fastlamps import semiprimes_unbalanced
    ns = semiprimes_unbalanced(84, 24, 2, 2800084)
    for s in (256, 16384):
        yield "stage 9 84/24", [R_(E, Q, s, s)], ns, 2 ** 28, None
        yield "stage 9 84/24 rho", [R_(RH, Q, s, s)], ns, 2 ** 28, None
    n48 = semiprimes_pq(48, 3, 2900048)
    yield "disabled sb", [R_(E, Q, 64, 0)], n48, 2 ** 28, None
    yield "disabled sa", [R_(E, Q, 0, 64)], n48, 2 ** 28, None
    yield "side ends, other alone", [R_(TD_END, E, 64, 64)], n48, 2 ** 28, "ends"
    yield "side ends mid-race", [R_(E, {"t": "pm1", "b": 0.05}, 32, 32)], n48, 2 ** 28, None
    yield "both end, next stage", [R_(TD_END, {"t": "td", "a": 0.06}, 4, 4), RH], n48, 2 ** 28, "next"
    yield "race after a stage", [TD_END, R_(RH, Q, 512, 512)], n48, 2 ** 28, None
    for N, p, q in n48:
        full = run([R_(E, Q, 256, 256)], N, 2 ** 28)[0]
        for frac in (0.25, 0.5, 0.9):
            yield "cap mid-race", [R_(E, Q, 256, 256)], [(N, p, q)], int(full * frac), "miss"
    rng = random.Random(909)
    kinds = ["td", "sq", "rho", "pm1", "ps", "qs", "cfrac", "ecm"]
    for _ in range(60):
        A, B = (rand_stage(k, rng) if k in ("td", "sq", "rho", "pm1", "ps") else dict(RACE_STAGES[k])
                for k in (rng.choice(kinds), rng.choice(kinds)))
        sa, sb = (rng.choice((0, 1, 4, 64, 1000, 4096, 1 << 14)) for _ in range(2))
        if sa == sb == 0:
            sa = 64
        b = rng.choice((32, 36, 40))
        yield "random race", [R_(A, B, sa, sb)], semiprimes_pq(b, 1, rng.randint(1, 10 ** 6)), 2 ** 24, None

OBS = (0, 1, 7, 100, 1000, 10 ** 4, 10 ** 5, 2 ** 40)

def ob_pairs():
    """(label, genome, numbers, cap, expectation or None)."""
    small = {"td": 28, "sq": 36, "ps": 32}
    for x, X in RACE_STAGES.items():
        for b in ((small[x],) if x in small else (40, 60, 84) if x in ("qs", "qs lc 1.4", "ecm") else (40, 48)):
            ns = semiprimes_pq(b, 2, 3100000 + b)
            Y = RACE_STAGES["rho"] if b < 40 else RACE_STAGES["qs"]
            for ob in OBS:
                yield f"ob {x} {ob}", [dict(X, ob=ob), Y], ns, 2 ** 28, None
    ns = semiprimes_pq(56, 3, 3200056)
    E, Q, RH, P = RACE_STAGES["ecm"], RACE_STAGES["qs lc 1.4"], RACE_STAGES["rho"], RACE_STAGES["pm1"]
    for o1, o2 in ((100, 1000), (5000, 0), (0, 5000), (2 ** 40, 300)):
        yield "ob two stages", [dict(P, ob=o1), dict(E, ob=o2), Q], ns, 2 ** 28, None
    yield "ob on final qs", [dict(RH, ob=500), dict(Q, ob=2 ** 40)], ns, 2 ** 28, None
    yield "ob on final qs, too small", [dict(RH, ob=500), dict(Q, ob=1000)], ns, 2 ** 28, None
    for N, p, q in ns:
        yield "cap inside a budgeted stage", [dict(RH, ob=10 ** 6), Q], [(N, p, q)], 300, "miss"
    rng = random.Random(4242)
    kinds = ["td", "sq", "rho", "pm1", "ps"]
    for _ in range(60):
        g = [dict(rand_stage(rng.choice(kinds), rng), ob=rng.choice(OBS)) for _ in range(rng.randint(1, 3))]
        g.append(dict(RACE_STAGES["qs"]))
        b = rng.choice((32, 36, 40, 44))
        yield "random ob", g, semiprimes_pq(b, 1, rng.randint(1, 10 ** 6)), 2 ** 24, None

def check_ob():
    checked = mismatches = 0
    phased = lambda st: st["t"] in ("qs", "cfrac", "ecm")
    for label, g, nums, cap, expect in ob_pairs():
        has_ph = any(phased(st) for st in g)
        fast = run_many(g, nums, cap, inst=True, phases=has_ph)
        for (N, p, q), f in zip(nums, fast):
            tr = new_trace()
            ops, d = run(g, N, cap)
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"])
            if has_ph:
                slow += ({k: tr["ops"].get(k, 0) for k in PHASES},)
            if expect == "miss":
                assert ops is None and LAST["ob"] and not LAST["ob"][-1][3], (label, N, LAST["ob"])
            checked += 1
            if slow != f:
                mismatches += 1
                if mismatches <= 10:
                    print("MISMATCH", label, N, "python", slow, "rust", f)
    qs.TRACE = cfrac.TRACE = ecm.TRACE = None
    return checked, mismatches

def check_ob_refusals():
    RH, Q = RACE_STAGES["rho"], RACE_STAGES["qs"]
    race_ = R_(RH, Q, 64, 64)
    ok = True
    for g in ([dict(RH, ob=-1)], [dict(RH, ob=2.5)], [dict(RH, ob="5")], [dict(RH, ob=True)],
              [dict(race_, ob=10)], [dict(race_, a=dict(RH, ob=10))], [dict(race_, b=dict(Q, ob=10))]):
        r = subprocess.run([BIN], input=json.dumps(g) + "\n1000\n1000036000099 1000003 1000033\n",
                           capture_output=True, text=True)
        rust_ok = r.returncode != 0 and "ob" in r.stderr and r.stdout == ""
        try:
            run(g, 1000036000099, 1000)
            py_ok = False
        except ValueError:
            py_ok = True
        ok = ok and rust_ok and py_ok
    return ok

def check_race_refusals():
    S = RACE_STAGES["rho"]
    ok = True
    for g in ([R_(R_(S, S, 1, 1), S, 1, 1)], [R_(S, S, 0, 0)]):
        r = subprocess.run([BIN], input=json.dumps(g) + "\n1000\n1000036000099 1000003 1000033\n",
                           capture_output=True, text=True)
        rust_ok = r.returncode != 0 and "race:" in r.stderr and r.stdout == ""
        try:
            run(g, 1000036000099, 1000)
            py_ok = False
        except ValueError:
            py_ok = True
        ok = ok and rust_ok and py_ok
    return ok

def check_race():
    checked = mismatches = 0
    phased = lambda st: st["t"] in ("qs", "cfrac", "ecm") or (st["t"] == "race" and {st["a"]["t"], st["b"]["t"]} & {"qs", "cfrac", "ecm"})
    for label, g, nums, cap, expect in race_pairs():
        has_ph = any(phased(st) for st in g)
        fast = run_many(g, nums, cap, inst=True, phases=has_ph, race=True)
        for (N, p, q), f in zip(nums, fast):
            tr = new_trace()
            race.TRACE = rt = {}
            ops, d = run(g, N, cap)
            ph = {k: tr["ops"].get(k, 0) for k in PHASES}
            for sd in rt.get("sides", []):
                for k, v in (sd["phases"] or {}).items():
                    ph[k] += v
            rinfo = (rt["sides"][0]["ops"], rt["sides"][1]["ops"], rt["switches"]) if rt else (0, 0, 0)
            if not has_ph:
                ph = None
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"]) + ((ph,) if ph is not None else ()) + (rinfo,)
            if expect == "ends":
                assert rt["sides"][0]["end"] == "none" and rt["sides"][1]["end"] == "found", (label, N, rt["sides"])
            if expect == "next":
                assert LAST["stage"] == 1 and all(sd["end"] == "none" for sd in rt["sides"]), (label, N)
            if expect == "miss":
                assert ops is None, (label, N)
            race.TRACE = None
            checked += 1
            if slow != f:
                mismatches += 1
                if mismatches <= 10:
                    print("MISMATCH", label, N, "python", slow, "rust", f)
    qs.TRACE = cfrac.TRACE = ecm.TRACE = None
    return checked, mismatches

def all_pairs():
    """(label, genome, numbers, cap) for every pair the sections above check."""
    sizes = [28, 34, 40, 46]
    nums = {b: semiprimes_pq(b, PER, 90000 + b) for b in sizes}
    for name, g in genomes().items():
        for b in sizes:
            yield "general " + name, g, nums[b], min(cap_for(b), 2 ** 22)
    for label, g, ns, cap, _ in qs_pairs():
        yield label, g, ns, cap
    for label, g, ns, cap, _, _ in guard_pairs():
        yield label, g, ns, cap
    for label, g, ns, cap, _ in race_pairs():
        yield label, g, ns, cap
    for label, g, ns, cap, _ in ob_pairs():
        yield label, g, ns, cap

def check_types(mutation_sample=40):
    from optypes import TYPE_ORDER
    checked = mismatches = identity = 0
    sample, in_use = [], set()
    for label, g, ns, cap in all_pairs():
        fast = run_many(g, ns, cap, types=True)
        for (N, p, q), f in zip(ns, fast):
            lamps.TYPES = True
            try:
                ops, d = run(g, N, cap)
                py = {t: LAST["types"].get(t, 0) for t in TYPE_ORDER}
            finally:
                lamps.TYPES = False
            checked += 1
            if f[0] is not None and sum(f[4].values()) != f[0]:
                identity += 1
            if py != f[4] or ops != f[0]:
                mismatches += 1
                if mismatches <= 10:
                    print("TYPES MISMATCH", label, N, {t: (py[t], f[4][t]) for t in TYPE_ORDER if py[t] != f[4][t]})
            used = {t for t, n in py.items() if n}
            if used - in_use or len(sample) < mutation_sample:
                sample.append((g, (N, p, q), cap, py, ops))
                in_use |= used
    # mutation: each type in use, dropped and doubled in lampcore's output, must be caught
    caught = {}
    for t in sorted(in_use):
        for how in ("drop", "double"):
            os.environ["LAMPCORE_TYPES_MUTATE"] = f"{t}:{how}"
            try:
                hit = False
                for g, num, cap, py, ops in sample:
                    if not py[t]:
                        continue
                    f = run_many(g, [num], cap, types=True)[0]
                    if f[4] != py or (f[0] is not None and sum(f[4].values()) != f[0]):
                        hit = True
                        break
                caught[f"{t}:{how}"] = hit
            finally:
                del os.environ["LAMPCORE_TYPES_MUTATE"]
    qs.TRACE = cfrac.TRACE = ecm.TRACE = None
    return checked, mismatches, identity, caught

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
    rc, rm = check_race()
    print(f"race: checked {rc} genome x number pairs (ops, factor, tests, hits, stage, k, "
          f"per-phase ops, per-side ops and switches), mismatches {rm}")
    refuse = check_race_refusals()
    print(f"race: both cores refuse a nested race and sa = sb = 0 with an error: {'yes' if refuse else 'NO'}")
    oc, om = check_ob()
    print(f"ob: checked {oc} genome x number pairs (ops, factor, tests, hits, stage, k, per-phase ops), mismatches {om}")
    obref = check_ob_refusals()
    print(f"ob: both cores refuse bad ob values and ob on a race or its side with an error: {'yes' if obref else 'NO'}")
    tc, tm, tid, tmut = check_types()
    print(f"types: checked {tc} genome x number pairs (lampcore --types vs Python's per-stage split), "
          f"mismatches {tm}, sum-identity failures {tid}; mutations caught {sum(tmut.values())}/{len(tmut)}"
          + ("" if all(tmut.values()) else f" (missed: {[k for k, v in tmut.items() if not v]})"))
    sys.exit(1 if mismatches or qm or gm or not bounded or not limit or rm or not refuse or om or not obref
             or tm or tid or not all(tmut.values()) else 0)
