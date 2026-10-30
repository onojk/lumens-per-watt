"""Family (1), change the group: the pre-check (the user's ruling, Oct 30; cost model NOTES 3cf6d3e, written first).
Exploratory: not scored, no deck, no search; lampcore runs for p - 1, ECM and rho are untimed counts (exact charges).

Numbers (fresh training-like, guarded against every held-out and training seed): balanced semiprimes_pq(bits, 96,
9948000 + bits) and theta 0.20-0.30 (arr_validate's draw) theta_numbers(bits, 9949000 + bits, 96), at 48, 64, 80 bits.
Arms, each against rho alone (partition.PRE["rho"]) on the same numbers:
  pm1(B1, c)   the pm1 lamp, B = B1 in {2^8, 2^10, ..., 2^18}, stage 2 c in {0, 50} (B2 = c B1), lampcore --types
  ecm(b1)      the ecm lamp, b1 in {0.5, 1.0, 2.0}, b2 50 (B1 from sqrt N, as the lamp sizes it)
  pp1(B1)      p + 1 by the cost model (no lamp): B2 = 50 B1, 2 seeds; seed s finds the factor r if the order
               r - (D_s / r) is B1/B2-smooth (all prime powers <= B1 but one prime <= B2); (D_s / r) = +-1 with even
               odds, drawn once per (number, seed, factor) from random.Random(number index, seed); a seed that finds
               both factors is a failure (gcd = N); every seed's stage is charged (mul, word, gcd per NOTES), and the
               second seed runs only if the first failed
Per arm, map and size: the success fraction f; C = total spent / successes per pricing (defined only at f >= 1/2);
the cost ratio against rho per pricing; the worst-of ratio (max over op-class v1, ruint, Montgomery, scaled gcd) with a
paired bootstrap interval (2,000 resamples, random.Random(2026), 2.5-97.5%); and G_rho (48-80, worst-of point) where
defined at 48 and 80. The win rules (docs/planning/next_family_template.md): a LEVEL win needs the worst-of interval
entirely below 1 at every size; a SLOPE win (G_rho > 1) needs no size with the interval entirely above 1.
  python3 group_precheck.py > group_precheck.out"""
import math, os, random, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "evolve"))
os.chdir(os.path.join(HERE, "..", "evolve"))
import arr_price as AP
from fastlamps import semiprimes_pq
from lamps import rand_prime

SIZES, PER = (48, 64, 80), 96
SEEDS = {"balanced": 9948000, "theta": 9949000}
FORBIDDEN = {base + b for base in (9920000, 9925000, 9930000, 9935000) for b in range(40, 129)}
assert not {s + b for s in SEEDS.values() for b in SIZES} & FORBIDDEN, "a held-out or training seed"
WORST = ("opclass_v1", "ruint", "montgomery", "opclass_v1_gcdscaled")
PRS = ("official",) + WORST
B1S = [2 ** k for k in range(8, 19, 2)]

def theta_numbers(bits, seed, n, lo=0.20, hi=0.30):
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

def primes_upto(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]

PRIMES = primes_upto(1 << 21)          # trial division of p +- 1 up to 2^21 (p < 2^42 at 80 bits, theta or balanced)

from functools import lru_cache

@lru_cache(maxsize=None)
def factor(m):
    f = {}
    for q in PRIMES:
        if q * q > m:
            break
        while m % q == 0:
            f[q] = f.get(q, 0) + 1
            m //= q
    if m > 1:
        f[m] = f.get(m, 0) + 1
    return f

def smooth(m, B1, B2):
    """All prime powers <= B1, except at most one prime (exponent 1) in (B1, B2]."""
    big = [(q, e) for q, e in factor(m).items() if q ** e > B1]          # factor() is cached: each m is factored once
    return not big or (len(big) == 1 and big[0][1] == 1 and big[0][0] <= B2)

def s1_bits(B1):
    return sum(max(1, (q ** int(math.log(B1, q))).bit_length()) for q in PRIMES if q <= B1)

def pi(x):
    import bisect
    return bisect.bisect_right(PRIMES, x) if x <= PRIMES[-1] else int(x / math.log(x) * (1 + 1 / math.log(x)))

def pp1_records(nums, bits, B1):
    B2 = 50 * B1
    sb, n2 = s1_bits(B1), pi(B2) - pi(B1)
    ty = {"mul": 2 * sb + 2 * n2, "word": 2 * sb + 3 * n2, "gcd": 1 + math.ceil(n2 / 64) + 1}
    one = AP.costs(ty, bits, 0)
    out = []
    for i, (N, p, q) in enumerate(nums):
        found, seeds = None, 0
        for s in range(2):
            seeds += 1
            rng = random.Random(i * 1000 + s)
            hit = [smooth(r - (1 if rng.random() < 0.5 else -1) * (-1), B1, B2) for r in (p, q)]
            # (D/r) = -1 -> order r + 1; +1 -> order r - 1 (the coin above picks the sign)
            if hit[0] != hit[1]:
                found = True
                break
        c = {pr: (v * seeds if v is not None else None) for pr, v in one.items()}
        out.append({"ok": bool(found), "cost": c, "ops": sum(ty.values()) * seeds})
    return out

def ratio_ci(C, R, rng):
    n = len(C)
    def worst(ix):
        v = []
        for pr in WORST:
            c, r = AP.per_fact(C, pr, ix), AP.per_fact(R, pr, ix)
            if not c or not r:
                return None
            v.append(c / r)
        return max(v)
    bs = sorted(x for x in (worst([rng.randrange(n) for _ in range(n)]) for _ in range(2000)) if x is not None)
    return worst(None), ((bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if len(bs) > 100 else (None, None))

def main():
    arms = [(f"pm1(B1=2^{int(math.log2(B))}, c={c})", {"t": "pm1", "B": B, **({"c": c} if c else {})}) for B in B1S for c in (0, 50)]
    arms += [(f"ecm(b1={b1})", {"t": "ecm", "b1": b1, "b2": 50}) for b1 in (0.5, 1.0, 2.0)]
    arms += [(f"pp1(B1=2^{int(math.log2(B))}, B2=50 B1, 2 seeds)", B) for B in B1S]
    for mp, seed0 in SEEDS.items():
        nums = {b: (semiprimes_pq(b, PER, seed0 + b) if mp == "balanced" else theta_numbers(b, seed0 + b, PER)) for b in SIZES}
        jobs = [("rho", b) for b in SIZES] + [(name, b) for name, g in arms if not isinstance(g, int) for b in SIZES]
        gmap = dict(arms)
        with ThreadPoolExecutor(2) as ex:
            res = dict(zip(jobs, ex.map(lambda j: AP.run(AP.RHO if j[0] == "rho" else [gmap[j[0]]], AP.CAP, nums[j[1]], j[1]), jobs)))
        for name, g in arms:
            if isinstance(g, int):
                for b in SIZES:
                    res[(name, b)] = pp1_records(nums[b], b, g)
        bad = [k for k, rs in res.items() if any(r.get("term") in AP.BAD_TERMS for r in rs)]
        print(f"\n===== {mp} map: {PER} per size at {SIZES}, seeds {seed0} + bits" + (f"; ERRORS in {bad}" if bad else ""))
        print("rho: successes " + str({b: sum(r['ok'] for r in res[('rho', b)]) for b in SIZES}))
        for name, _ in arms:
            line, cis, defined = [], {}, True
            for b in SIZES:
                C, R = res[(name, b)], res[("rho", b)]
                f = sum(r["ok"] for r in C) / len(C)
                w, ci = ratio_ci(C, R, random.Random(2026))
                cis[b] = (w, ci)
                defined &= w is not None
                line.append(f"{b}: f {f:.2f}, worst-of {('%.3f' % w) if w else 'n/a'}"
                            + (f" [{ci[0]:.3f}, {ci[1]:.3f}]" if w and ci[0] else ""))
            gr = None
            if all(cis[b][0] for b in (48, 80)):
                v = []
                for pr in WORST:
                    pc = AP.period({48: res[(name, 48)], 80: res[(name, 80)]}, 48, 80, pr)
                    pr_ = AP.period({48: res[("rho", 48)], 80: res[("rho", 80)]}, 48, 80, pr)
                    v.append(pc / pr_ if pc and pr_ else None)
                gr = min(v) if None not in v else None
            level = defined and all(cis[b][1][1] is not None and cis[b][1][1] < 1 for b in SIZES)
            slope = (gr is not None and gr > 1 and defined
                     and not any(cis[b][1][0] is not None and cis[b][1][0] > 1 for b in SIZES))
            print(f"  {name:34s} " + "; ".join(line) + f"; G_rho {('%.3f' % gr) if gr else 'n/a'}"
                  + ("; LEVEL WIN" if level else "") + ("; SLOPE WIN" if slope else ""))

if __name__ == "__main__":
    main()
