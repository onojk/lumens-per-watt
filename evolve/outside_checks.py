"""Repo-side checks of the user's outside figures (Wolfram Language 15, Oct 24; NOTES.md,
"Outside checks"). Information only: no fitness, no charged path, no new population.

  1. rho charging on the partition map's band-16 numbers (rho c 1, b 64, d 2, x0 2): the
     card re-run with counters (f evaluations, product accumulations, gcds), asserted equal to
     the map's ops; beside them Brent detection steps (b = 1) and tail + cycle (mu + lambda of
     x -> x^2 + 1 mod p, from x0 = 2).
  2. pm1 per band on the partition map (B = int(N^0.1991...)): the map's solve fraction, the
     exact prediction (ord_p(2) or ord_q(2) divides the exponent, not both), and p - 1
     B-powersmooth, beside the user's random-prime rates.
  3. Random-prime B-powersmooth rates (2000 primes per size, random.Random(2026)) at
     B = 2^16.7 and B = 2^10: the user's two tables recomputed.

  python3 outside_checks.py  -> outside_checks.json, stdout
"""
import json, math, random
from sympy import factorint, isprime, primerange
import partition as PT
from fastlamps import semiprimes_pq, semiprimes_unbalanced

out = {}
mp = json.load(open("partition_map.json"))
pop = {pb: (semiprimes_pq(84, 80, 4000000 + 100 * pb + 84) if pb == 42 else
            semiprimes_unbalanced(84, pb, 80, 4000000 + 100 * pb + 84)) for pb in mp["bands"]}
rows = {pb: [r for r in mp["rows"] if r["band"] == pb] for pb in mp["bands"]}
for pb in mp["bands"]:
    assert [int(r["N"]) for r in rows[pb]] == [t[0] for t in pop[pb]]

# 1. rho: the card's loop (lamps.lamp_rho with d 2), counted by kind
def rho_counts(N, c=1, b=64, x0=2):
    f = lambda v: (v * v + c) % N
    fe = pr = gc = 0
    y, r, q, G = x0, 1, 1, 1
    while True:
        x = y
        for _ in range(r):
            y = f(y); fe += 1
        k = 0
        while k < r and G == 1:
            ys = y
            for _ in range(min(b, r - k)):
                y = f(y); q = q * abs(x - y) % N; fe += 1; pr += 1
            G = math.gcd(q, N); gc += 1
            k += b
        r *= 2
        if G != 1:
            break
    if G == N:
        while True:
            ys = f(ys); fe += 1
            G = math.gcd(abs(x - ys), N); gc += 1
            if G > 1:
                break
    return fe, pr, gc

def mu_lambda(p, c=1, x0=2):
    seen, x, i = {}, x0 % p, 0
    while x not in seen:
        seen[x] = i; x = (x * x + c) % p; i += 1
    return i                                                   # mu + lambda

R = []
for r, (N, p, q) in zip(rows[16], pop[16]):
    fe, pr, gc = rho_counts(N)
    assert fe + pr + gc == r["rho"]["T"], (N, fe + pr + gc, r["rho"]["T"])
    det = sum(rho_counts(N, b=1)[:1])                          # f evaluations to detection, b = 1
    R.append({"p": min(p, q), "ops": fe + pr + gc, "f": fe, "prod": pr, "gcd": gc, "brent_f_b1": det,
              "mu_lambda": mu_lambda(min(p, q))})
mean = lambda k: sum(x[k] for x in R) / len(R)
sq = sum(math.sqrt(math.pi * x["p"] / 2) for x in R) / len(R)
out["rho_band16"] = {k: mean(k) for k in ("ops", "f", "prod", "gcd", "brent_f_b1", "mu_lambda")}
out["rho_band16"]["sqrt_pi_p_over_2"] = sq
o = out["rho_band16"]
print(f"1. rho, band 16 (80 numbers, ops asserted equal to the map): mean ops {o['ops']:.1f} = f evals {o['f']:.1f}"
      f" + products {o['prod']:.1f} + gcds {o['gcd']:.1f}")
print(f"   sqrt(pi p/2) {sq:.1f}; mu + lambda {o['mu_lambda']:.1f} ({o['mu_lambda'] / sq:.3f}x);"
      f" Brent f evals to detection (b = 1) {o['brent_f_b1']:.1f} ({o['brent_f_b1'] / sq:.3f}x)")
print(f"   ops per Brent detection step {o['ops'] / o['brent_f_b1']:.3f}; per sqrt(pi p/2) {o['ops'] / sq:.3f};"
      f" card f evals / detection steps {o['f'] / o['brent_f_b1']:.3f}")

# 2. pm1 per band
def powersmooth(n, B):
    return all(pp ** e <= B for pp, e in factorint(n).items())
def exponent_hits(p, B):
    """ord_p(2) divides prod over primes l <= B of the largest l^k <= B."""
    o = p - 1
    for l, e in factorint(p - 1).items():
        for _ in range(e):
            if pow(2, o // l, p) == 1:
                o //= l
            else:
                break
    return all(l ** e <= B for l, e in factorint(o).items())
USER_167 = {16: 1.00, 20: 0.886, 24: 0.700, 28: 0.531, 32: 0.404, 36: 0.276, 39: 0.195, 42: 0.143}
out["pm1"] = {}
print("\n2. pm1 on the partition map (B = int(N^b), b 0.1991): solve fraction per band")
print("   band  map    exact-pred  p-1 smooth  user rate  map - user  2 SE (n 80 + n 2000)")
for pb in mp["bands"]:
    sm = pr_ = ps = 0
    comp = {"small only": 0, "large only": 0, "both (gcd N)": 0}
    for r, (N, p, q) in zip(rows[pb], pop[pb]):
        B = max(10, int(N ** PT.PM1["b"]))
        a, b_ = min(p, q), max(p, q)
        hp, hq = exponent_hits(a, B), exponent_hits(b_, B)
        pr_ += hp != hq
        if hp and hq: comp["both (gcd N)"] += 1
        elif hp: comp["small only"] += 1
        elif hq: comp["large only"] += 1
        sm += r["pm1"]["T"] is not None
        ps += powersmooth(a - 1, B)
    u = USER_167[pb]
    se = 2 * math.sqrt(u * (1 - u) / 80 + u * (1 - u) / 2000)
    out["pm1"][pb] = {"map": sm / 80, "exact_pred": pr_ / 80, "p_minus_1_powersmooth": ps / 80, "user": u, "two_se": se, "hits": comp}
    print(f"   {pb:4d}  {sm / 80:.3f}  {pr_ / 80:.3f}       {ps / 80:.3f}       {u:.3f}      {sm / 80 - u:+.3f}      {se:.3f}"
          + ("  OFF" if abs(sm / 80 - u) > se else "") + f"   {comp}")

# 3. random-prime powersmooth rates
rng = random.Random(2026)
def rand_prime(bits):
    while True:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if isprime(n):
            return n
out["random_primes"] = {}
for lab, B, sizes in (("2^16.7", int(2 ** 16.7), (16, 20, 24, 28, 32, 36, 39, 42)), ("2^10", 2 ** 10, (20, 24, 28, 32))):
    rates = {s: sum(powersmooth(rand_prime(s) - 1, B) for _ in range(2000)) / 2000 for s in sizes}
    out["random_primes"][lab] = rates
    print(f"\n3. random primes, B = {lab} ({B}), 2000 per size: " + "  ".join(f"{s}: {v:.3f}" for s, v in rates.items()))
cost = 1558
print("   B = 2^10 meter charge 1,558 ops / rate: " + "  ".join(f"{s}: {cost / v:,.0f}" for s, v in out["random_primes"]["2^10"].items()))
json.dump(out, open("outside_checks.json", "w"), indent=1)
