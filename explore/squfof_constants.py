"""SQUFOF's step constants for family (2)'s cost model (the user's ruling, Oct 30): exploratory, untimed, not scored, no
deck, no meter; plain Python. Ported from the published description (Shanks's square forms; Gower and Wagstaff, "Square
form factorization", Math. Comp. 2008), not from any implementation.

Numbers: training-like balanced semiprimes, fastlamps.semiprimes_pq(bits, n, SEED0 + bits), SEED0 = 9946000, at 48, 64
and 80 bits. The seeds are checked not to be any held-out seed (9930000 + b, 9935000 + b) nor arrangement-v1's training
seeds (9920000 + b, 9925000 + b).

One form step = one (P, Q) update: b = (P0 + P) // Q, P' = b Q - P, Q' = Qprev + b (P - P'), the cost model's step (a word
division and six word ops). Forward steps run until Q is a square on an even step; then the reverse cycle from the
square root runs until P repeats, and gcd(N, P) is taken. A trivial gcd (an improper square) costs its reverse steps,
and the forward cycle continues from where it was (the queue-free variant: every square is tried).
  alpha = forward steps / N^(1/4);  beta = reverse steps (all attempts) / forward steps;  A = (forward + reverse) / N^(1/4)
  (normalised by N^(1/4), not (k N)^(1/4), so A compares directly with rho's 2.1 ops per N^(1/4); NOTES)
Strategies:
  S1    k = 1 alone, forward cap 64 N^(1/4) (generous: the natural distribution); a number over the cap is a failure
  S2    multipliers in Gower-Wagstaff order 1, 3, 5, 7, 11, 15, 21, 33, 35, 55, 77, 105, 165, ... each with the standard
        forward bound 3 L, L = 2 sqrt(2 sqrt(k N)); on a failure, the next k; every step of every k counted
  per-k k in {1, 3, 5, 7, 11} each alone (cap 64 (kN)^(1/4)), at 48 and 64 bits only (Python time)
Per size and strategy: mean A with a 95% bootstrap interval (10,000 resamples, random.Random(2026)), median, the mean
alpha and beta, failures, multipliers tried, reverse attempts (= gcds), square tests (= forward steps / 2).
  python3 squfof_constants.py > squfof_constants.out"""
import math, os, random, statistics, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evolve"))
from fastlamps import semiprimes_pq

SEED0 = 9946000
SIZES = {48: 400, 64: 400, 80: 160}
FORBIDDEN = {base + b for base in (9920000, 9925000, 9930000, 9935000) for b in range(40, 129)}
assert not {SEED0 + b for b in SIZES} & FORBIDDEN, "a held-out or training seed"
KSEQ = [1, 3, 5, 7, 11, 15, 21, 33, 35, 55, 77, 105, 165, 231, 385, 1155]

def squfof_k(N, k, cap):
    """One multiplier. Returns (factor or None, forward steps, reverse steps, reverse attempts)."""
    kN = k * N
    P0 = math.isqrt(kN)
    if P0 * P0 == kN:
        g = math.gcd(N, P0)
        return (g if 1 < g < N else None), 0, 0, 0
    Pprev, P, Qprev, Q = P0, P0, 1, kN - P0 * P0
    fwd = rev = att = 0
    i = 1
    while fwd < cap:
        b = (P0 + P) // Q
        Pn = b * Q - P
        Qn = Qprev + b * (P - Pn)
        Qprev, Q, Pprev, P = Q, Qn, P, Pn
        fwd += 1
        i += 1
        if i % 2 == 0:
            r = math.isqrt(Q)
            if r * r == Q:
                att += 1                                  # the reverse cycle from this square
                b2 = (P0 - P) // r
                RP = b2 * r + P
                RQprev, RQ = r, (kN - RP * RP) // r
                while True:
                    bb = (P0 + RP) // RQ
                    RPn = bb * RQ - RP
                    RQn = RQprev + bb * (RP - RPn)
                    RQprev, RQ = RQ, RQn
                    rev += 1
                    if RPn == RP:
                        break
                    RP = RPn
                g = math.gcd(N, RP)
                if 1 < g < N:
                    return g, fwd, rev, att
    return None, fwd, rev, att

def one(args):
    N, p, q, strategy, k = args
    q4 = N ** 0.25
    if strategy == "S1" or strategy == "perk":
        kk = 1 if strategy == "S1" else k
        g, f, r, a = squfof_k(N, kk, int(64 * (kk * N) ** 0.25) + 10)
        return {"ok": g in (p, q), "f": f, "r": r, "att": a, "ks": 1, "q4": q4}
    F = R = A = 0
    for j, kk in enumerate(KSEQ):
        L = 2 * math.isqrt(2 * math.isqrt(kk * N))
        g, f, r, a = squfof_k(N, kk, 3 * L)
        F, R, A = F + f, R + r, A + a
        if g in (p, q):
            return {"ok": True, "f": F, "r": R, "att": A, "ks": j + 1, "q4": q4}
    return {"ok": False, "f": F, "r": R, "att": A, "ks": len(KSEQ), "q4": q4}

def summary(rs):
    A = [(x["f"] + x["r"]) / x["q4"] for x in rs]
    m = sum(A) / len(A)
    rng, bs = random.Random(2026), []
    for _ in range(10000):
        s = [A[rng.randrange(len(A))] for _ in A]
        bs.append(sum(s) / len(s))
    bs.sort()
    F, R = sum(x["f"] for x in rs), sum(x["r"] for x in rs)
    return (f"A mean {m:.3f} [{bs[250]:.3f}, {bs[9749]:.3f}], median {statistics.median(A):.3f}; alpha mean "
            f"{F / sum(x['q4'] for x in rs):.3f}, beta {R / F:.3f}; failures {sum(not x['ok'] for x in rs)}/{len(rs)}; "
            f"multipliers per number {sum(x['ks'] for x in rs) / len(rs):.2f}; reverse attempts (gcds) per number "
            f"{sum(x['att'] for x in rs) / len(rs):.2f}"), {"A_mean": m, "A_ci": (bs[250], bs[9749])}

if __name__ == "__main__":
    out = {}
    with Pool(2) as pool:
        for bits, n in SIZES.items():
            nums = semiprimes_pq(bits, n, SEED0 + bits)
            print(f"== {bits} bits: {n} numbers, seed {SEED0 + bits}", flush=True)
            for strat in ("S1", "S2"):
                rs = pool.map(one, [(N, p, q, strat, 1) for N, p, q in nums])
                line, s = summary(rs)
                out[(bits, strat)] = s
                print(f"  {strat}: {line}", flush=True)
            if bits <= 64:
                for k in (1, 3, 5, 7, 11):
                    rs = pool.map(one, [(N, p, q, "perk", k) for N, p, q in nums])
                    print(f"  k = {k:2d} alone: {summary(rs)[0]}", flush=True)
