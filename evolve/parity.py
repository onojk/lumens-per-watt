"""Parity: the Rust lamp core must match lamps.py exactly.

For every genome x number pair, both must agree on ops (or both miss), the factor found,
the test and hit counts, the winning stage, and a square-search win's k. Genomes: every
baseline, every champion of Runs 2-4, and random fine-deck genomes. Numbers: 28-48 bits.

Quadratic sieve (qs_pairs): the same fields plus qs's per-phase op breakdown, on the
acceptance numbers (40-60 bits), the Stage 2 numbers at 66/72/78 bits, numbers that make qs
retry with its next multiplier (asserted), gene variants, qs after another stage, and a low
cap that stops it partway through a phase.

  python3 parity.py [random_genomes] [numbers_per_size]
"""
import json, os, random, sys
import qs
from lamps import run, LAST, rand_genome, use_fine_deck, cap_for
from fastlamps import semiprimes_pq, run_many, PHASES
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

def check_qs():
    checked = mismatches = 0
    for label, g, nums, cap, must_retry in qs_pairs():
        fast = run_many(g, nums, cap, inst=True, phases=True)
        for (N, p, q), f in zip(nums, fast):
            qs.TRACE = {}
            ops, d = run(g, N, cap)
            ph = {k: qs.TRACE.get("ops", {}).get(k, 0) for k in PHASES}
            slow = (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"], ph)
            if must_retry:
                assert len(qs.TRACE["attempts"]) > 1, ("expected a retry", N)
            checked += 1
            if slow != f:
                mismatches += 1
                if mismatches <= 10:
                    print("MISMATCH", label, N, "python", slow, "rust", f)
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
    sys.exit(1 if mismatches or qm else 0)
