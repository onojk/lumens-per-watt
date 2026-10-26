"""Acceptance for p-1 stage 2 by prime-gap stepping (NOTES.md, "p-1 stage 2 by prime-gap stepping: cost model,
completed for the code"; tests written before the code).

  1. Exact check on known primes: p of 16-40 bits, N = p * r with r a 60-bit safe prime (never caught), B in
     {2^7, 2^9, 2^11}, c in {10, 15, 20, 30}: the card's stage-2 catch (lampcore and Python) = the exact predicate
     ord_p(2) | E q for some prime q in (B, B2], ord_p(2) not dividing E. The user's p - 1 form is reported beside it.
  2. Python = Rust per type on that set, and on map numbers in pm1-then-qs pipelines (c in {0, 10, 30}).
  3. The charge formula from the Python trace equals the measured per-type charges.
  4. c absent or 0: every run identical to the pre-change lampcore (LAMPCORE_OLD), all map numbers, pipelines with pm1.
  5. A forced backtrack: N = p q with both caught by stage 2 in the same batch, at different primes.

  LAMPCORE_OLD=<pre-change binary> python3 pm1s2_accept.py -> stdout
"""
import os, json, math, random
import sympy
import partition as P, sizescale as SS, sizescale2 as S2, lamps, optypes
import fastlamps
from fastlamps import run_many

CAP = 1 << 40

def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many(g, nums, CAP, inst=True, types=True)
    finally:
        fastlamps.BIN = b0

def stage1_E(B):
    E = 1
    for p in sympy.primerange(2, B + 1):
        pk = p
        while pk * p <= B:
            pk *= p
        E *= pk
    return E

def ordp2(p):
    return sympy.n_order(2, p)

def predicate(p, B, B2, E):
    o = ordp2(p)
    if E % o == 0:
        return False                      # stage 1 catches it
    r = o // math.gcd(o, E)               # what E misses
    return sympy.isprime(r) and B < r <= B2

def user_form(p, B, B2):
    m = p - 1
    for q in sympy.primerange(2, B + 1):
        pk = q
        while pk * q <= B:
            pk *= q
        g = math.gcd(m, pk)
        m //= g
    return m == 1 or (sympy.isprime(m) and B < m <= B2)

def safe_prime(bits, rng):
    while True:
        q = sympy.randprime(1 << (bits - 2), 1 << (bits - 1))
        if sympy.isprime(2 * q + 1):
            return 2 * q + 1

def py_types(g, N):
    lamps.TYPES = True
    try:
        ops, d = lamps.run(g, N, CAP)
        return ops, d, lamps.LAST.get("types")
    finally:
        lamps.TYPES = False

def formula(tr):
    """Stage-2 charges from the trace: (mul, word, gcd)."""
    if not tr or not tr.get("m"):
        return 0, 0, 0
    m, gmax, q1 = tr["done"], tr["gmax"], tr["q1"]          # primes processed before a factor or the end
    mul = gmax // 2 + (q1.bit_length() - 1) + (bin(q1).count("1") - 1) + 1 + 2 * (m - 1)
    word = 1 + 3 * (m - 1)
    gcd = tr["batches"]
    bt = tr.get("backtrack", 0)            # primes re-stepped in the backtrack
    if bt:
        steps = bt - (1 if tr["bt_first"] else 0)
        mul += steps; word += 2 * steps + bt; gcd += bt
    return mul, word, gcd

if __name__ == "__main__":
    random.seed(2026)                          # sympy.randprime draws from the global RNG: seeded, reproducible
    rng = random.Random(2026)
    r60 = safe_prime(60, rng)
    n1 = b1 = n2 = b2 = n3 = b3 = n4 = b4 = n5 = b5 = 0
    diff_form = caught = 0
    cases = []
    for bits in range(16, 41, 4):
        for _ in range(40):
            cases.append(sympy.randprime(1 << (bits - 1), 1 << bits))
    for B in (2 ** 7, 2 ** 9, 2 ** 11):
        E = stage1_E(B)
        for c in (10, 15, 20, 30):
            g = [{"t": "pm1", "B": B, "b": 0.2, "c": c}]
            nums = [(p * r60, p, r60) for p in cases]
            rs = run(g, nums)
            for (N, p, _), x in zip(nums, rs):
                s1 = E % ordp2(p) == 0
                want = predicate(p, B, c * B, E)
                got = (x[1] is not None) and not s1
                n1 += 1
                b1 += got != want or (x[1] is not None and int(x[1]) != p)
                caught += got
                diff_form += want != (user_form(p, B, c * B) and not s1)
                ops, d, t = py_types(g, N)
                tr = lamps.PM1_TRACE
                n2 += 1
                b2 += not (ops == x[0] and (d is None) == (x[1] is None) and {k: v for k, v in t.items() if v} == {k: v for k, v in x[-1].items() if v})
                if tr and tr.get("m"):
                    mul, word, gcd = formula(tr)
                    n3 += 1
                    b3 += not (t.get("word", 0) == word and t.get("gcd", 0) == 1 + gcd and t.get("mul", 0) == tr["s1_mul"] + mul)
    print(f"1. stage-2 catches = the exact predicate (ord_p(2) | E q): {n1 - b1}/{n1} ({caught} caught by stage 2); "
          f"the user's p - 1 form differs from the predicate on {diff_form} (ord_p(2) a proper divisor of p - 1)")
    print(f"2a. Python = Rust per type (known primes): {n2 - b2}/{n2}")
    print(f"3. charge formula = measured (word, gcd, mul): {n3 - b3}/{n3}")
    pm = lambda B, c: dict(P.PRE["pm1"], B=B, ob=lamps.pm1_ob(B, c), **({"c": c} if c else {}))
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        qsg = dict(SS.qsg(json.load(open("sizescale_k_sealed.json"))["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
        for B in (128, 512, 2048):
            g0 = [dict(P.PRE["pm1"], B=B, ob=2 * B), qsg]
            for a, b in zip(run(g0, nums), run(g0, nums, old=True)):
                n4 += 1
                b4 += a != b
            g0c = [dict(P.PRE["pm1"], B=B, ob=2 * B, c=0), qsg]
            for a, b in zip(run(g0c, nums), run(g0, nums, old=True)):
                n4 += 1
                b4 += a != b
            for c in (10, 30):
                g = [pm(B, c), qsg]
                rs = run(g, nums[::20])
                for (N, p, q), x in zip(nums[::20], rs):
                    ops, d, t = py_types(g, N)
                    n2 += 1
                    b2 += not (ops == x[0] and {k: v for k, v in t.items() if v} == {k: v for k, v in x[-1].items() if v})
        print(f"{bits} bits done", flush=True)
    print(f"4. c absent or 0 = pre-change lampcore: {n4 - b4}/{n4}")
    print(f"2b. Python = Rust per type (all, incl. pipelines): {n2 - b2}/{n2}")
    # 5. forced backtrack: two primes caught by stage 2 at different primes q of one batch
    B, c = 2 ** 9, 30
    E = stage1_E(B)
    found = []
    for p in sympy.primerange(1 << 30, (1 << 30) + 4000000):
        if predicate(p, B, c * B, E):
            o = ordp2(p); q = o // math.gcd(o, E)
            found.append((p, q))
            if len(found) > 400:
                break
    qs_ = sympy.primerange(B + 1, c * B + 1)
    qi = {q: i for i, q in enumerate(qs_)}
    pair = None
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            (p1, q1), (p2, q2) = found[i], found[j]
            if q1 != q2 and qi[q1] // 64 == qi[q2] // 64:
                pair = (p1, p2); break
        if pair:
            break
    g = [{"t": "pm1", "B": B, "b": 0.2, "c": c}]
    N = pair[0] * pair[1]
    x = run(g, [(N, pair[0], pair[1])])[0]
    ops, d, t = py_types(g, N)
    tr = lamps.PM1_TRACE
    n5 = 1
    b5 = not (x[1] is not None and int(x[1]) in pair and tr.get("backtrack", 0) > 0 and ops == x[0]
              and {k: v for k, v in t.items() if v} == {k: v for k, v in x[-1].items() if v} and formula(tr)[1] == t.get("word", 0))
    print(f"5. forced backtrack (N = {pair[0]} x {pair[1]}): factor found through the backtrack, Python = Rust, formula: {n5 - b5}/{n5}")
    assert not (b1 or b2 or b3 or b4 or b5)
