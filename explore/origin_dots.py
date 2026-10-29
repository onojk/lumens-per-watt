"""Origin dots, "k of n" (the user's exploratory idea, Oct 28): exploratory, untimed, not scored, no predictions; plain
Python, no op meter. A shape check, not a cost.
Tower N's dots k/N collide with a smaller tower exactly when gcd(k, N) > 1. For balanced semiprimes N = pq at
20, 24, ..., 40 bits (40 numbers per size, random.Random(7000 + bits)), count the STEPS TO THE FIRST HIDDEN COLLISION
(a step = one dot placed and one gcd / compare test) for four arrangements of the dots:
  walk    : k = 2, 3, 4, ...; collision when gcd(k, N) > 1 (trial division)
  rho     : x -> x^2 + 1 mod N, x0 = 2, Floyd; step i tests gcd(x_i - x_2i, N) > 1. If the first collision is
            gcd = N (no factor), it is counted as found and flagged; the steps stop there.
  p-1     : a = 2, x_k = a^(k!) mod N, k = 1, 2, ...; collision when gcd(x_k - 1, N) > 1 (gcd = N flagged as above)
  value   : place k/N reduced (fractions.Fraction), k = 1, 2, ...; collision when it lands on a smaller tower
            (its denominator < N). Must equal walk step for step: k = 1 lands on tower 1 by construction (1/N is
            already reduced; it does not land) and walk starts at k = 2, so value's step count is walk's + 1.
Per size: median steps per arrangement, and the slope of log2(median steps) against bits (least squares).
  python3 origin_dots.py > origin_dots.out"""
import math, random, statistics
from fractions import Fraction

SIZES, PER = (20, 24, 28, 32, 36, 40), 40

def is_prime(n):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True

def rand_prime(bits, rng):
    while True:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(n):
            return n

def semiprimes(bits, n, seed):
    rng, out = random.Random(seed), []
    while len(out) < n:
        p, q = rand_prime(bits // 2, rng), rand_prime(bits - bits // 2, rng)
        if p != q and (p * q).bit_length() == bits:
            out.append((p * q, min(p, q)))
    return out

def walk(N):
    k = 2
    while math.gcd(k, N) == 1:
        k += 1
    return k - 1, False

def rho(N):
    x = y = 2
    i = 0
    while True:
        x = (x * x + 1) % N
        y = (y * y + 1) % N; y = (y * y + 1) % N
        i += 1
        g = math.gcd(x - y, N)
        if g > 1:
            return i, g == N

def pm1(N):
    x, k = 2, 0
    while True:
        k += 1
        x = pow(x, k, N)
        g = math.gcd(x - 1, N)
        if g > 1:
            return k, g == N

def value(N):
    k = 1
    while Fraction(k, N).denominator == N:
        k += 1
    return k, False

ARR = (("walk", walk), ("rho", rho), ("p-1", pm1), ("value", value))

def slope(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

if __name__ == "__main__":
    med = {a: [] for a, _ in ARR}
    print(f"balanced semiprimes, {PER} per size, seeds 7000 + bits; steps to the first hidden collision")
    for bits in SIZES:
        nums = semiprimes(bits, PER, 7000 + bits)
        steps, flags = {}, {}
        for a, f in ARR:
            r = [f(N) for N, _ in nums]
            steps[a], flags[a] = [s for s, _ in r], sum(b for _, b in r)
            med[a].append(statistics.median(steps[a]))
        same = all(v == w + 1 for v, w in zip(steps["value"], steps["walk"]))
        walk_is_p = all(s + 1 == p for s, (_, p) in zip(steps["walk"], nums))
        print(f"{bits} bits: median steps " + ", ".join(f"{a} {statistics.median(steps[a]):,.1f}" for a, _ in ARR)
              + f"; max p-1 {max(steps['p-1']):,}; gcd = N (no factor): rho {flags['rho']}, p-1 {flags['p-1']}"
              + f"; value = walk + 1 on every number: {same}; walk ends at the smaller prime: {walk_is_p}", flush=True)
    print("slope of log2(median steps) per bit, 20-40: "
          + ", ".join(f"{a} {slope(SIZES, [math.log2(m) for m in med[a]]):.3f}" for a, _ in ARR))
    for a, _ in ARR:
        ls = [math.log2(m) for m in med[a]]
        print(f"  {a}: log2(median) " + " ".join(f"{x:.2f}" for x in ls)
              + "; per-step slopes " + " ".join(f"{(ls[i + 1] - ls[i]) / 4:.3f}" for i in range(len(ls) - 1)))
