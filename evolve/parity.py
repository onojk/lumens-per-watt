"""Parity: the Rust lamp core must match lamps.py exactly.

For every genome x number pair, both must agree on ops (or both miss), the factor found,
and the test and hit counts. Genomes: every baseline, every champion of Runs 2-4, and
random fine-deck genomes. Numbers: 28-48 bits.

  python3 parity.py [random_genomes] [numbers_per_size]
"""
import json, os, random, sys
from lamps import run, LAST, rand_genome, use_fine_deck, cap_for
from fastlamps import semiprimes_pq, run_many
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

if __name__ == "__main__":
    sizes = [28, 34, 40, 46]
    nums = {b: semiprimes_pq(b, PER, 90000 + b) for b in sizes}
    checked = mismatches = 0
    for name, g in genomes().items():
        for b in sizes:
            cap = min(cap_for(b), 2 ** 22)
            fast = run_many(g, nums[b], cap)
            for (N, p, q), f in zip(nums[b], fast):
                ops, d = run(g, N, cap)
                slow = (ops, d, LAST["tests"], LAST["hits"])
                checked += 1
                if slow != f:
                    mismatches += 1
                    if mismatches <= 10:
                        print("MISMATCH", name, b, N, "python", slow, "rust", f)
    print(f"checked {checked} genome x number pairs, mismatches {mismatches}")
    sys.exit(1 if mismatches else 0)
