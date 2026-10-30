"""Close-factor check of arrangement-v1's number generators (the user's request, Oct 29, before the balanced-map search):
exploratory, untimed, not scored, no deck, not in any sealed run; plain Python, no op meter. A property check of the
test sets, not a cost.

Generators (design docs/planning/arrangement_lamps.md §8, with the 84-bit addendum; the scorer's draws):
  balanced train  fastlamps.semiprimes_pq(bits, n, 9920000 + bits)
  balanced valid  fastlamps.semiprimes_pq(bits, n, 9930000 + bits)
  theta train     theta 0.20-0.30 (twilight2_search.numbers' draw, band changed; arr_validate.theta_numbers), 9925000 + bits
  theta valid     the same, 9935000 + bits
at 48, 64 and 80 bits (theta: 64 and 80 only, as design §8 draws it). The draws are sequential, so the first 48
(balanced) or 96 (theta) of the n = 200 drawn here are exactly the sets the search and the scorer see.

1. Per generator and size, on the actual set (48 or 96): a histogram of |q - p| / sqrt(N), and the fraction with
   |q - p| < N^(1/4).
2. On 200 per size: the steps of three exact searches, counted as candidates tested (closed forms, no loops):
     trial division down from isqrt(N): d = isqrt(N), isqrt(N) - 1, ... until d | N   -> isqrt(N) - p + 1
     trial division up from 2:          d = 2, 3, ... until d | N                      -> p - 1
     Fermat: a = ceil(sqrt N), +1, ... until a^2 - N is a square; for N = pq (odd primes) the first such a is
             (p + q) / 2                                                                -> (p + q)/2 - ceil(sqrt N) + 1
   with rho's scale sqrt(p) beside them (Pollard rho needs about sqrt(pi p / 2) iterations). Medians per size, and the
   doubling period over the 48-80 chord, (80 - 48) / log2(median(80) / median(48)).
3. The stop rule, written before the first run: the test set is "too easy" (stop and report before any search) if, for
   any generator and size, (a) more than 1% of the actual set has |q - p| < N^(1/4), or (b) more than 5% of the 200
   have Fermat steps <= sqrt(p) (Fermat at or below rho's scale), or (c) the median Fermat steps are below 100 x the
   median sqrt(p).
  python3 close_factors.py > close_factors.out"""
import math, os, random, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evolve"))
from fastlamps import semiprimes_pq
from lamps import rand_prime

N_DRAW = 200
BINS = (0, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, math.inf)

def theta_numbers(bits, seed, n, lo=0.20, hi=0.30):
    """twilight2_search.numbers' draw, band [lo, hi) (the same as arr_validate.theta_numbers)."""
    rng, out = random.Random(seed), []
    while len(out) < n:
        pb = round(rng.uniform(lo, hi) * bits)
        p, q = rand_prime(pb, rng), rand_prime(bits - pb + 1, rng)
        N = p * q
        if N.bit_length() != bits:
            continue
        p, q = min(p, q), max(p, q)
        if lo <= math.log2(p) / math.log2(N) < hi:
            out.append((N, p, q))
    return out

GENS = {
    "balanced train": ((48, 64, 80), 48, lambda b, n: semiprimes_pq(b, n, 9920000 + b)),
    "balanced valid": ((48, 64, 80), 48, lambda b, n: semiprimes_pq(b, n, 9930000 + b)),
    "theta train": ((64, 80), 48, lambda b, n: theta_numbers(b, 9925000 + b, n)),
    "theta valid": ((64, 80), 96, lambda b, n: theta_numbers(b, 9935000 + b, n)),
}

def steps(N, p, q):
    r = math.isqrt(N)
    c = r if r * r == N else r + 1
    return {"td_down": r - p + 1, "td_up": p - 1, "fermat": (p + q) // 2 - c + 1, "rho_scale": math.sqrt(p)}

def fourth_root_gap(N, p, q):
    return (q - p) ** 4 < N                    # |q - p| < N^(1/4), exactly

too_easy = []
for gname, (sizes, actual, draw) in GENS.items():
    print(f"== {gname} (actual set: {actual} per size)")
    med = {}
    for b in sizes:
        nums = draw(b, N_DRAW)
        act = nums[:actual]
        ratios = [(q - p) / math.sqrt(N) for N, p, q in act]
        hist = [sum(lo <= x < hi for x in ratios) for lo, hi in zip(BINS, BINS[1:])]
        close = sum(fourth_root_gap(*x) for x in act) / len(act)
        st = [steps(*x) for x in nums]
        m = {k: statistics.median(s[k] for s in st) for k in st[0]}
        med[b] = m
        fe = sum(s["fermat"] <= s["rho_scale"] for s in st) / len(st)
        print(f"  {b} bits: |q-p|/sqrt(N) histogram " + ", ".join(
            f"[{lo:g},{hi:g}): {h}" for lo, hi, h in zip(BINS, BINS[1:], hist) if h) +
              f"; min {min(ratios):.4f}, median {statistics.median(ratios):.4f}")
        print(f"     fraction |q-p| < N^(1/4): {close:.4f} ({round(close * len(act))}/{len(act)})")
        print(f"     {N_DRAW} numbers, median steps: td down {m['td_down']:.4g}, td up {m['td_up']:.4g}, "
              f"Fermat {m['fermat']:.4g}, rho scale sqrt(p) {m['rho_scale']:.4g}; Fermat / sqrt(p) "
              f"{m['fermat'] / m['rho_scale']:.4g}; fraction Fermat <= sqrt(p): {fe:.4f}")
        if close > 0.01:
            too_easy.append(f"{gname} {b}: {close:.2%} have |q-p| < N^(1/4)")
        if fe > 0.05:
            too_easy.append(f"{gname} {b}: {fe:.2%} have Fermat steps <= sqrt(p)")
        if m["fermat"] < 100 * m["rho_scale"]:
            too_easy.append(f"{gname} {b}: median Fermat {m['fermat']:.4g} < 100 x median sqrt(p) {m['rho_scale']:.4g}")
    if 48 in med and 80 in med:
        print("  doubling period 48-80 (bits per doubling of the median): " + ", ".join(
            f"{k} {32 / math.log2(med[80][k] / med[48][k]):.3f}" for k in ("td_down", "td_up", "fermat", "rho_scale")))
    elif 64 in med and 80 in med:
        print("  doubling period 64-80 (theta; no 48-bit draw): " + ", ".join(
            f"{k} {16 / math.log2(med[80][k] / med[64][k]):.3f}" for k in ("td_down", "td_up", "fermat", "rho_scale")))
print("\nstop rule (3): " + ("TOO EASY: " + "; ".join(too_easy) if too_easy else
                             "not triggered: no generator gives Fermat a large advantage"))
