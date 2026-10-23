"""Quadratic sieve card ("qs"): self-initializing multiple-polynomial QS on kN.

Cost model: NOTES.md, "Quadratic-sieve card", written before this code. Every charge
goes through charge(phase, n), so each phase's ops can be checked against its formula.
The charges are exactly the ones listed there:

  mult    14 ops per candidate multiplier (ks scoring)
  fb      Euler's criterion per prime (square-and-multiply, bit_length + popcount - 1),
          Tonelli-Shanks modular multiplies, counted as performed
  setup   per A: multiplies building A (s - 1 per combination formed), B_l (1 to form
          A/q_l, Euclid steps of its inverse, 2 multiplies), per sieved prime the
          Euclid steps of A^-1 mod p, 2 root multiplies, s multiplies for 2 B_l A^-1;
          per Gray-code switch to the next B: 1 op per root updated
  sieve   1 op per sieve-array update, 1 op per cell scanned
  confirm 2 ops to form g(x), 1 per factor-base entry tried, 1 per extra division
  la      ceil(rows * cols * rows / 64), dense GF(2) elimination
  sqrt    per dependency: multiplies forming X and Y (powers by square-and-multiply),
          1 op per Euclid step of gcd(X - Y, N)

Tests and hits for the luck meter: one test per candidate confirmed (hit = smooth), one
per dependency tried (hit = it splits N).

Genes: kc (multipliers 1..kc ranked by ks score), bc (B = bc * exp(0.5 sqrt(ln N ln ln N)),
default 1.5),
mc (M = mc * B), tc (threshold = log2(M sqrt(kN/2)) - tc * log2(B)).

Set qs.TRACE = {} before a run to record realized counts for the accounting test.
"""
import math
from itertools import combinations

TRACE = None
DELTA = 10                 # surplus relations: rows = F + DELTA

def _primes(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(n) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]

def lamp_qs(N, g, m):
    import numpy as np
    from lamps import ks_score, KS_PRIMES
    tr = TRACE
    if tr is not None:
        tr.clear()
        tr.update(ops={}, k_cands=0, attempts=[])
    def charge(phase, n):
        if tr is not None:
            tr["ops"][phase] = tr["ops"].get(phase, 0) + n
        m.tick(n)

    def cpow(b, e, mod, phase):
        """Square-and-multiply, 1 op per modular multiply, the base reduction counted as
        the first: bit_length(e) + popcount(e) - 1 in all."""
        r = b % mod; charge(phase, 1); n = 1
        for bit in bin(e)[3:]:
            r = r * r % mod; charge(phase, 1); n += 1
            if bit == "1":
                r = r * b % mod; charge(phase, 1); n += 1
        return r, n

    def euclid_inv(a, mod, phase):
        """Inverse of a mod `mod` by extended Euclid, 1 op per division step."""
        r0, r1, s0, s1, steps = mod, a % mod, 0, 1, 0
        while r1:
            q = r0 // r1
            r0, r1, s0, s1 = r1, r0 - q * r1, s1, s0 - q * s1
            steps += 1
        charge(phase, steps)
        return s0 % mod, steps

    if N % 2 == 0:
        return 2

    # 1. multiplier
    kc = max(1, int(g.get("kc", 1)))
    charge("mult", kc * len(KS_PRIMES))
    if tr is not None:
        tr["k_cands"] = kc
    def attempt(k, at):
        kN = k * N

        # 2. factor base: -1, 2, primes dividing k, odd primes with (kN | p) = 1
        lnN = math.log(N)
        B = max(30, int(g.get("bc", 1.5) * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
        base = [-1, 2]
        roots_t = {}                               # p -> sqrt(kN) mod p
        for p in _primes(B)[1:]:
            e = (p - 1) // 2
            leg, n = cpow(kN, e, p, "fb")
            if at is not None:
                at["euler_e"].append(e)
            if kN % p == 0:
                if k % p:
                    return p                       # p divides N
                base.append(p); roots_t[p] = 0
                continue
            if leg != 1:
                continue
            t, n = _tonelli(kN % p, p, cpow, charge)
            if at is not None:
                at["ts"].append((kN % p, p, n))
            base.append(p); roots_t[p] = t
        F = len(base)
        if at is not None:
            at["F"] = F
        idx = {p: i for i, p in enumerate(base)}
        logp = {p: max(1, round(math.log2(p))) for p in base[2:]}

        # 3. polynomials: A = product of s primes near (sqrt(2kN)/M)^(1/s)
        M = max(64, int(g.get("mc", 4.0) * B))
        target = math.isqrt(2 * kN) / M
        pool_all = [p for p in base[2:] if k % p and p > 2]
        if not pool_all:
            return None
        s = 1
        while target ** (1 / s) > pool_all[-1] and s < 8:
            s += 1
        while s > 1 and target ** (1 / s) < pool_all[min(len(pool_all) - 1, 2)]:
            s -= 1
        q = target ** (1 / s)
        P = min(len(pool_all), 40 if s == 1 else 16 + 4 * s)
        pool = sorted(sorted(pool_all, key=lambda p: (abs(math.log(p / q)), p))[:P])
        combos = list(combinations(pool, s))
        charge("setup", (s - 1) * len(combos))     # multiplies forming each A
        combos.sort(key=lambda c: (abs(math.log(math.prod(c) / target)), c))
        if at is not None:
            at["combos"], at["s"] = len(combos), s
        T = math.log2(M * math.sqrt(kN / 2)) - g.get("tc", 2.0) * math.log2(B)
        width = 2 * M + 1
        need = F + DELTA
        rels, seen = [], set()
        for qs_ in combos:
            A = math.prod(qs_)
            if at is not None:
                at["a_count"] += 1
            Bl = []
            for ql in qs_:
                Aq = A // ql; charge("setup", 1)
                inv, st = euclid_inv(Aq % ql, ql, "setup")
                if at is not None:
                    at["inv"].append((Aq % ql, ql, st))
                gam = roots_t[ql] * inv % ql; charge("setup", 1)
                if gam > ql // 2:
                    gam = ql - gam
                Bl.append(Aq * gam); charge("setup", 1)
            sieved = [p for p in base[2:] if A % p]
            sieved = [p for p in sieved if p != 2]
            st_ = []                               # per sieved prime: [p, roots, 2 B_l A^-1]
            Bv = sum(Bl)
            for p in sieved:
                ainv, st = euclid_inv(A % p, p, "setup")
                if at is not None:
                    at["inv"].append((A % p, p, st))
                t = roots_t[p]
                r1 = ainv * ((t - Bv) % p) % p; charge("setup", 1)
                r2 = ainv * ((-t - Bv) % p) % p; charge("setup", 1)
                bainv = []
                for b in Bl:
                    bainv.append(2 * b * ainv % p); charge("setup", 1)
                st_.append([p, [r1] if t == 0 else [r1, r2], bainv])
            if at is not None:
                at["n_sieved_setup"] += len(sieved)
            signs = [1] * s
            for i in range(1 << (s - 1)):
                if i:                              # Gray code: flip one B_l, update every root
                    v = (i & -i).bit_length()      # flips B_v, v in 1..s-1
                    d = signs[v]
                    signs[v] = -d
                    Bv -= 2 * d * Bl[v]
                    n_roots = 0
                    for ent in st_:
                        p, rs, bainv = ent
                        ent[1] = [(r + d * bainv[v]) % p for r in rs]
                        n_roots += len(rs)
                    charge("setup", n_roots)
                    if at is not None:
                        at["switches_roots"].append(n_roots)
                C = (Bv * Bv - kN) // A
                # 4. sieve
                arr = np.zeros(width, dtype=np.int32)
                upd = 0
                hits = []
                for p, rs, _ in st_:
                    for r in rs:
                        start = (r + M) % p
                        arr[start::p] += logp[p]
                        upd += (width - 1 - start) // p + 1
                        hits.append((p, r))
                charge("sieve", upd)
                charge("sieve", width)
                if at is not None:
                    at["polys"].append({"M": M, "roots": hits, "upd": upd,
                                        "sieved": [p for p, _, _ in st_],
                                        "rp": {p: len(rs) for p, rs, _ in st_}})
                # 5. confirm
                for i0 in np.nonzero(arr >= T)[0].tolist():
                    x = i0 - M
                    v = (A * x + 2 * Bv) * x + C; charge("confirm", 2)
                    charge("confirm", F)
                    if at is not None:
                        at["cands"].append(v)
                    vec = [0] * F
                    if v < 0:
                        vec[0] = 1; v = -v
                    if v == 0:
                        m.test(False)
                        continue
                    for j in range(1, F):
                        p = base[j]
                        if v % p == 0:
                            v //= p; vec[j] += 1
                            while v % p == 0:
                                v //= p; vec[j] += 1; charge("confirm", 1)
                                if at is not None:
                                    at["extra_div"] += 1
                    smooth = v == 1
                    m.test(smooth)
                    if not smooth:
                        continue
                    u = A * x + Bv
                    if abs(u) in seen:
                        continue
                    seen.add(abs(u))
                    for ql in qs_:
                        vec[idx[ql]] += 1
                    rels.append((u, vec))
                    if len(rels) >= need:
                        break
                if len(rels) >= need:
                    break
            if len(rels) >= need:
                break
        if len(rels) < need:
            return None

        # 6. linear algebra: dense GF(2) elimination
        rows = len(rels)
        charge("la", -(-rows * F * rows // 64))
        if at is not None:
            at["rows"] = rows
        mat = [sum(1 << j for j in range(F) if vec[j] & 1) for _, vec in rels]
        comb = [1 << i for i in range(rows)]
        used = [False] * rows
        for col in range(F):
            piv = next((r for r in range(rows) if not used[r] and mat[r] >> col & 1), None)
            if piv is None:
                continue
            used[piv] = True
            for r in range(rows):
                if r != piv and mat[r] >> col & 1:
                    mat[r] ^= mat[piv]; comb[r] ^= comb[piv]
        deps = [comb[r] for r in range(rows) if mat[r] == 0]

        # 7. square root, dependency by dependency
        for dep in deps:
            members = [i for i in range(rows) if dep >> i & 1]
            mults = 0
            X = 1
            for j, i in enumerate(members):
                if j:
                    X = X * rels[i][0] % N; charge("sqrt", 1); mults += 1
                else:
                    X = rels[i][0] % N
            ex = [0] * F
            for i in members:
                for j, e in enumerate(rels[i][1]):
                    ex[j] += e
            Y, hs = None, []
            for j in range(1, F):
                if ex[j]:
                    y, n = cpow(base[j], ex[j] // 2, N, "sqrt"); mults += n
                    hs.append(ex[j] // 2)
                    if Y is None:
                        Y = y
                    else:
                        Y = Y * y % N; charge("sqrt", 1); mults += 1
            Y = 1 if Y is None else Y
            a, b, steps = (X - Y) % N, N, 0
            while b:
                a, b = b, a % b
                steps += 1
            charge("sqrt", steps)
            if at is not None:
                at["deps"].append({"mults": mults, "gcd_steps": steps, "members": len(members),
                                   "h": hs, "xy": (X - Y) % N})
            m.test(1 < a < N)
            if 1 < a < N:
                return a
        return None

    # Multipliers best-first by ks score. An attempt that fails (no dependency splits N, or
    # the polynomials run out) is retried with the next k, paying again for everything.
    ranked = sorted(range(1, kc + 1), key=lambda kk: (-ks_score(kk, N), kk))
    for k in ranked:
        at = None
        if tr is not None:
            at = dict(k=k, euler_e=[], ts=[], combos=0, s=0, a_count=0, inv=[],
                      n_sieved_setup=0, switches_roots=[], polys=[], cands=[],
                      extra_div=0, F=0, rows=0, deps=[])
            tr["attempts"].append(at)
        d = attempt(k, at)
        if d:
            return d
    return None

def _tonelli(n, p, cpow, charge):
    """sqrt(n) mod p (n a nonzero residue), charged 1 op per modular multiply."""
    if p % 4 == 3:
        return cpow(n, (p + 1) // 4, p, "fb")
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2; s += 1
    total = 0
    z = 2
    while True:                                # Euler's criterion on each z tried
        t, c = cpow(z, (p - 1) // 2, p, "fb"); total += c
        if t == p - 1:
            break
        z += 1
    cz, c = cpow(z, q, p, "fb"); total += c
    t, c = cpow(n, q, p, "fb"); total += c
    r, c = cpow(n, (q + 1) // 2, p, "fb"); total += c
    mm = s
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p; i += 1
        b = cz
        for _ in range(mm - i - 1):
            b = b * b % p
        r = r * b % p; cz = b * b % p; t = t * cz % p
        n_mul = i + (mm - i - 1) + 3
        charge("fb", n_mul); total += n_mul
        mm = i
    return r, total
