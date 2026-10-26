"""Relation ledger (PLAN.md, "Relation economy"): the half of a relation card that every
relation source shares.

A ledger is built for one N and one multiplier k (one k per ledger, so one factor base).
It owns qs's phases 2, 6 and 7 and the dedupe between them:

  fb      the factor base: -1, 2, primes dividing k, odd primes p <= B with (kN | p) = 1;
          Euler's criterion per prime and Tonelli-Shanks roots, charged as NOTES.md's
          "Quadratic-sieve card" lists
  dedupe  free: a full relation is dropped if |u| was seen, a combined one (y > 1) if u was
          seen up to sign
  la      ceil(rows * cols * rows / 64), dense GF(2) elimination
  sqrt    per dependency: multiplies forming X and Y, 1 op per large prime multiplied into
          Y, 1 op per Euclid step of gcd(X - Y, N)
  check   opt-in per source, off by default (NOTES.md, "Ledger: the charged relation
          check"): per relation submitted, u^2 and the right-hand side by square-and-
          multiply, 1 per sign flip, 1 compare, ceil(F/64) parity scan; an all-even
          relation also pays the test for u = +-Y. Invalid or trivial relations are rejected.

A source (qs.py's sieve, later CFRAC) finds relations (u, vec, y) with
u^2 = y^2 prod p^vec (mod N) and hands them to add(); solve() runs once the ledger is full.
With the check off the ledger trusts its relations, and every charge is made at the same
point and in the same chunk as before the split, so qs is op for op unchanged
(relation_economy_identity.py). qs turns the check on only for its acceptance test
(genome key "check": 1, never mutated).
"""
import math

DELTA = 10                 # surplus relations: rows = F + DELTA

def _primes(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(n) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]

class Charger:
    """The meter plus the per-phase trace: every charge of a relation card goes through here."""
    def __init__(self, m, tr):
        self.m, self.tr = m, tr

    def charge(self, phase, n):
        if self.tr is not None:
            self.tr["ops"][phase] = self.tr["ops"].get(phase, 0) + n
        self.m.tick(n)

    def cpow(self, b, e, mod, phase):
        """Square-and-multiply, 1 op per modular multiply, the base reduction counted as
        the first: bit_length(e) + popcount(e) - 1 in all."""
        r = b % mod; self.charge(phase, 1); n = 1
        for bit in bin(e)[3:]:
            r = r * r % mod; self.charge(phase, 1); n += 1
            if bit == "1":
                r = r * b % mod; self.charge(phase, 1); n += 1
        return r, n

    def euclid_inv(self, a, mod, phase):
        """Inverse of a mod `mod` by extended Euclid, 1 op per division step."""
        r0, r1, s0, s1, steps = mod, a % mod, 0, 1, 0
        while r1:
            q = r0 // r1
            r0, r1, s0, s1 = r1, r0 - q * r1, s1, s0 - q * s1
            steps += 1
        self.charge(phase, steps)
        return s0 % mod, steps

class Ledger:
    def __init__(self, N, k, B, ch, at=None):
        self.N, self.k, self.kN, self.B = N, k, k * N, B
        self.ch, self.at = ch, at
        self.rels = []                             # (u, sparse [(j, e)], y): u^2 = y^2 prod p_j^e (mod N)
        self.seen, self.seen_c = set(), set()      # full |u|'s; combined u's up to sign

    def build_base(self):
        """Phase 2. Returns a prime dividing N if one turns up, else None."""
        ch, at, kN, k = self.ch, self.at, self.kN, self.k
        base = [-1, 2]
        roots_t = {}                               # p -> sqrt(kN) mod p
        for p in _primes(self.B)[1:]:
            e = (p - 1) // 2
            leg, n = ch.cpow(kN, e, p, "fb")
            if at is not None:
                at["euler_e"].append(e)
            if kN % p == 0:
                if k % p:
                    return p                       # p divides N
                base.append(p); roots_t[p] = 0
                continue
            if leg != 1:
                continue
            t, n = _tonelli(kN % p, p, ch.cpow, ch.charge)
            if at is not None:
                at["ts"].append((kN % p, p, n))
            base.append(p); roots_t[p] = t
        self.base, self.roots_t, self.F = base, roots_t, len(base)
        self.idx = {p: i for i, p in enumerate(base)}
        self.need = self.F + DELTA
        if at is not None:
            at["F"] = self.F
        return None

    @property
    def full(self):
        return len(self.rels) >= self.need

    def _product(self, vec, y, half):
        """y^(1 or 2) * prod p^(e_p or e_p/2) mod N over entries p >= 2, charged to "check":
        square-and-multiply per factor, 1 op per multiply joining it after the first."""
        ch, N, base = self.ch, self.N, self.base
        r = None
        factors = [(base[j], e // 2 if half else e) for j, e in vec if j >= 1]
        if y != 1:
            factors.append((y, 1 if half else 2))
        for b, e in factors:
            v, _ = ch.cpow(b, e, N, "check")
            if r is None:
                r = v
            else:
                r = r * v % N; ch.charge("check", 1)
        return 1 if r is None else r

    def check(self, u, vec, y):
        """Phase 9: is u^2 = y^2 prod p^e (mod N), and not a trivial all-even relation?"""
        ch, N = self.ch, self.N
        lhs, _ = ch.cpow(u, 2, N, "check")
        rhs = self._product(vec, y, False)
        if any(j == 0 and e & 1 for j, e in vec):
            rhs = (N - rhs) % N; ch.charge("check", 1)
        ch.charge("check", 1)                      # compare
        if lhs != rhs:
            return False
        ch.charge("check", -(-self.F // 64))       # parity scan
        if any(e & 1 for _, e in vec):
            return True
        Y = self._product(vec, y, True)            # all even: a one-row dependency
        ch.charge("check", 2)                      # u = Y, u = N - Y
        return u % N not in (Y, (N - Y) % N)

    def add(self, u, vec, y=1, check=False):
        """Keep the relation unless it fails the check (when on) or repeats one already kept.
        Returns True once full."""
        if check and not self.check(u, vec, y):
            if self.at is not None:
                self.at["rejected"] = self.at.get("rejected", 0) + 1
            return False
        # the duplicate check (NOTES.md, "Meter correction: the ledger's duplicate check"): a hash
        # lookup-and-insert of the two-word key, 2 word ops; a combined key also forms min(cu, N - cu), 3
        if y == 1:
            self.ch.charge("hash", 1); self.ch.charge("word", 1)    # audit item 0: the probe-and-insert is a hash op
            if abs(u) in self.seen:
                return False
            self.seen.add(abs(u))
        else:
            self.ch.charge("hash", 1); self.ch.charge("word", 2)
            key = min(u, self.N - u)
            if key in self.seen_c:
                if self.at is not None:
                    self.at["lp"]["dup"] += 1
                return False
            self.seen_c.add(key)
        self.rels.append((u, vec, y))
        return self.full

    def solve(self):
        """Phases 6 and 7 on a full ledger. Returns a factor, or None if no dependency splits N."""
        ch, at, N, F, rels, base = self.ch, self.at, self.N, self.F, self.rels, self.base

        # 6. linear algebra: dense GF(2) elimination
        rows = len(rels)
        ch.charge("la", -(-rows * F * rows // 64))
        if at is not None:
            at["rows"] = rows
        # GF(2) rows (bit-packed) built from the sparse relations, 1 word per entry (step 1)
        nnz = sum(len(vec) for _, vec, _ in rels); ch.charge("word", nnz)
        if at is not None:
            at["s1_bits"] = at.get("s1_bits", 0) + nnz
        mat = [sum(1 << j for j, e in vec if e & 1) for _, vec, _ in rels]
        # item 14 (NOTES.md, "Step 2"), counted as lampcore lays it out: cw = ceil(F/64) words per bit row,
        # rw = ceil(rows/64) per combination row
        cw, rw = -(-F // 64), -(-rows // 64)
        ch.charge("word", rows * cw + rows * rw)   # the rows' and the combination matrix's initialization
        comb = [1 << i for i in range(rows)]
        used = [False] * rows
        pivots = 0
        for col in range(F):
            piv = next((r for r in range(rows) if not used[r] and mat[r] >> col & 1), None)
            if piv is None:
                continue
            used[piv] = True
            pivots += 1
            for r in range(rows):
                if r != piv and mat[r] >> col & 1:
                    mat[r] ^= mat[piv]; comb[r] ^= comb[piv]
        ch.charge("word", pivots * (cw + rw))      # the per-pivot row clones
        deps = [comb[r] for r in range(rows) if mat[r] == 0]
        ch.charge("word", rows * cw + len(deps) * rw)   # the zero-row scan, the copies
        if at is not None:
            at["pivots"] = pivots; at["ndeps"] = len(deps)

        # 7. square root, dependency by dependency
        for dep in deps:
            members = [i for i in range(rows) if dep >> i & 1]
            # the member scan (rows), ex[] (F), the member sums (their entries), the Y scan (F - 1)
            ch.charge("word", rows + F + sum(len(rels[i][1]) for i in members) + F - 1)
            mults = 0
            X = 1
            for j, i in enumerate(members):
                if j:
                    X = X * rels[i][0] % N; ch.charge("sqrt", 1); mults += 1
                else:
                    X = rels[i][0] % N
            ex = [0] * F
            for i in members:
                for j, e in rels[i][1]:
                    ex[j] += e
            Y, hs = None, []
            for j in range(1, F):
                if ex[j]:
                    y, n = ch.cpow(base[j], ex[j] // 2, N, "sqrt"); mults += n
                    hs.append(ex[j] // 2)
                    if Y is None:
                        Y = y
                    else:
                        Y = Y * y % N; ch.charge("sqrt", 1); mults += 1
            Y = 1 if Y is None else Y
            ys = 0
            for i in members:                      # large primes, squared in each combined relation
                if rels[i][2] != 1:
                    Y = Y * rels[i][2] % N; ch.charge("sqrt", 1); mults += 1; ys += 1
            a, b, steps = (X - Y) % N, N, 0
            while b:
                a, b = b, a % b
                steps += 1
            ch.charge("sqrt", steps)
            if at is not None:
                at["deps"].append({"mults": mults, "gcd_steps": steps, "members": len(members),
                                   "h": hs, "xy": (X - Y) % N, "ys": ys,
                                   "idx": members, "X": X, "Y": Y})
            ch.m.test(1 < a < N)
            if 1 < a < N:
                return a
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
