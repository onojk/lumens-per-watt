"""Elliptic-curve card ("ecm"): Lenstra's ECM on Montgomery curves, x-only, Suyama's
parametrization, stage 1 by Montgomery ladder and a baby-step giant-step stage 2.

Cost model: NOTES.md, "Stage 8: elliptic-curve card", written before this code. 1 op per
modular multiply or squaring, every one charged where it is performed (additions free):

  ecm_setup  per curve: sigma^2, u^2, u^3, v^2, v^3, (v-u)^2, (v-u)^3, *(3u+v), u^3*v, *16,
             1 op per Euclid step of the one inverse, numerator * inverse
  ecm_s1     ladder per prime power q <= B1: 5 + 11 (bit_length(q) - 1)
             (xDBL 3M + 2S = 5, xADD 4M + 2S = 6)
  ecm_s2     2Q (5), baby steps 3Q..103Q (51 xADDs), ladders for W = 210 Q and j0 W,
             6 per giant step, 3 per (j, b) pair with jw + b or jw - b prime in (B1, B2]
  ecm_gcd    1 per gcd (after stage 1, after stage 2)
  word       (NOTES.md, "ECM modular additions"): 4 per xDBL, 6 per xADD, 5 per curve setup (sigma^2 - 5,
             4 sigma, v - u, 3u, 3u + v), and in stage 2 4 per (j, b) candidate (two indices, two
             prime-table tests) and 1 per accumulated pair (p1 - p2); priced like sieve_update

Genes: b1 (B1 = max(10, int(b1 exp(sqrt(ln s ln ln s) / sqrt 2))), s = isqrt(N), default 1.0),
b2 (B2 = int(b2 B1), 0 = no stage 2, default 50), curves (default 10000), s0 (first sigma,
default 6; curve i uses s0 + i).

Tests and hits for the luck meter: one test per curve; hit = the curve found a factor.
Set ecm.TRACE = {} before a run to record each curve's sigma and how it ended.
"""
import math
from ledger import Charger, _primes

TRACE = None
W = 210
BABY = [b for b in range(1, W // 2, 2) if math.gcd(b, W) == 1]   # 24 values

def bounds(N, g):
    ls = math.log(math.isqrt(N))
    B1 = max(10, int(g.get("b1", 1.0) * math.exp(math.sqrt(ls * math.log(ls)) / math.sqrt(2))))
    return B1, int(g.get("b2", 50) * B1)

def lamp_ecm(N, g, m):
    tr = TRACE
    if tr is not None:
        tr.setdefault("ops", {}); tr.setdefault("curves", [])
    ch = Charger(m, tr)
    c = ch.charge
    if N % 2 == 0:
        return 2
    if N >= 1 << 100:                          # lampcore's limit, kept here too
        raise ValueError(f"ecm supports N < 2^100, got a {N.bit_length()}-bit N")
    B1, B2 = bounds(N, g)
    primes = _primes(max(B1, B2))
    pp = []                                    # prime powers q = p^e <= B1
    for p in primes:
        if p > B1:
            break
        q = p
        while q * p <= B1:
            q *= p
        pp.append(q)
    stage2 = B2 > B1
    isprime = bytearray(B2 + 1) if stage2 else None
    if stage2:
        for p in primes:
            isprime[p] = 1
    a24 = 0

    def xdbl(X, Z, ph):
        c("word", 4)                           # X + Z, X - Z, t1 - t2, t2 + e (NOTES.md, "ECM modular additions")
        t1 = (X + Z) * (X + Z) % N; c(ph, 1)
        t2 = (X - Z) * (X - Z) % N; c(ph, 1)
        X2 = t1 * t2 % N; c(ph, 1)
        t3 = t1 - t2
        e = a24 * t3 % N; c(ph, 1)
        Z2 = t3 * (t2 + e) % N; c(ph, 1)
        return X2, Z2

    def xadd(XP, ZP, XQ, ZQ, XD, ZD, ph):
        c("word", 6)                           # XP - ZP, XQ + ZQ, XP + ZP, XQ - ZQ, uu + vv, uu - vv
        uu = (XP - ZP) * (XQ + ZQ) % N; c(ph, 1)
        vv = (XP + ZP) * (XQ - ZQ) % N; c(ph, 1)
        sa = (uu + vv) * (uu + vv) % N; c(ph, 1)
        sb = (uu - vv) * (uu - vv) % N; c(ph, 1)
        X3 = ZD * sa % N; c(ph, 1)
        Z3 = XD * sb % N; c(ph, 1)
        return X3, Z3

    def ladder(k, X, Z, ph):
        """(kP, (k+1)P) for k >= 1: R0 = P, R1 = 2P, then xADD + xDBL per bit below the top."""
        R0, R1 = (X, Z), xdbl(X, Z, ph)
        for bit in bin(k)[3:]:
            if bit == "1":
                R0 = xadd(*R0, *R1, X, Z, ph); R1 = xdbl(*R1, ph)
            else:
                R1 = xadd(*R0, *R1, X, Z, ph); R0 = xdbl(*R0, ph)
        return R0, R1

    for i in range(max(1, int(g.get("curves", 10000)))):
        sigma = int(g.get("s0", 6)) + i
        cur = None
        if tr is not None:
            cur = {"sigma": sigma, "end": None}
            tr["curves"].append(cur)
        def end(how, hit):
            if cur is not None:
                cur["end"] = how
            m.test(hit)

        # setup: Suyama, u = sigma^2 - 5, v = 4 sigma, P = (u^3 : v^3), a24 = (v-u)^3 (3u+v) / (16 u^3 v)
        s_sq = sigma * sigma % N; c("ecm_setup", 1)
        u = (s_sq - 5) % N; c("word", 1)
        v = 4 * sigma % N; c("word", 1)
        u2 = u * u % N; c("ecm_setup", 1)
        u3 = u2 * u % N; c("ecm_setup", 1)
        v2 = v * v % N; c("ecm_setup", 1)
        v3 = v2 * v % N; c("ecm_setup", 1)
        t = (v - u) % N; c("word", 1)
        t2 = t * t % N; c("ecm_setup", 1)
        t3 = t2 * t % N; c("ecm_setup", 1)
        c("word", 2)                           # 3u, 3u + v
        num = t3 * ((3 * u + v) % N) % N; c("ecm_setup", 1)
        den = u3 * v % N; c("ecm_setup", 1)
        den = 16 * den % N; c("ecm_setup", 1)
        r0, r1, s0_, s1_, steps = N, den, 0, 1, 0  # extended Euclid for den^-1 mod N
        while r1:
            qq = r0 // r1
            r0, r1, s0_, s1_ = r1, r0 - qq * r1, s1_, s0_ - qq * s1_
            steps += 1
        c("ecm_setup", steps)
        if r0 != 1:                            # den not invertible: r0 = gcd(den, N)
            if r0 < N:
                end("setup factor", True)
                return r0
            end("degenerate", False)
            continue
        a24 = num * (s0_ % N) % N; c("ecm_setup", 1)

        # stage 1
        X, Z = u3, v3
        for q in pp:
            (X, Z), _ = ladder(q, X, Z, "ecm_s1")
        d = math.gcd(Z, N); c("ecm_gcd", 1)
        if 1 < d < N:
            end("s1 factor", True)
            return d
        if d == N:
            end("s1 both", False)
            continue
        if not stage2:
            end("none", False)
            continue

        # stage 2: baby steps bQ (odd b < w/2), giant steps j W, j0 = max(1, B1 // w)
        Q = (X, Z)
        D2 = xdbl(X, Z, "ecm_s2")
        bq = {1: Q, 3: xadd(*Q, *D2, *Q, "ecm_s2")}
        for b in range(5, W // 2, 2):
            bq[b] = xadd(*bq[b - 2], *D2, *bq[b - 4], "ecm_s2")
        Wp, _ = ladder(W, X, Z, "ecm_s2")
        j0, jmax = max(1, B1 // W), -(-B2 // W)
        S, S1 = ladder(j0, *Wp, "ecm_s2")
        acc = 1
        for j in range(j0, jmax + 1):
            for b in BABY:
                q1, q2 = j * W + b, j * W - b; c("word", 2)            # the two indices
                c("word", 2)                                           # the two prime-table tests
                if (B1 < q1 <= B2 and isprime[q1]) or (B1 < q2 <= B2 and isprime[q2]):
                    Xb, Zb = bq[b]
                    p1 = S[0] * Zb % N; c("ecm_s2", 1)
                    p2 = Xb * S[1] % N; c("ecm_s2", 1)
                    c("word", 1)                                       # p1 - p2
                    acc = acc * (p1 - p2) % N; c("ecm_s2", 1)
            if j < jmax:
                S, S1 = S1, xadd(*S1, *Wp, *S, "ecm_s2")
        d = math.gcd(acc, N); c("ecm_gcd", 1)
        if 1 < d < N:
            end("s2 factor", True)
            return d
        end("s2 both" if d == N else "none", False)
    return None
