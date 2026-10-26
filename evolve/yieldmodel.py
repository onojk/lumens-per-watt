"""I-023, the tilted saddle-point yield model ("light meter"), ported for step 6 (NOTES.md, "Step 6 added", the
2026-10-26 morning entry A.3; read-only, no card change).

Per residue size |Q| (natural log s = ln |Q|), with the base's primes p (root count c_p: 2, or 1 for p | k and for
A's primes, where g(x) = Q(x)/A is linear mod p) and the prime 2's law by kN mod 8:
  untilted P(v_p >= j) = c_p / p^j; tilt the valuation by p^(j (1 - alpha)); local factor
  Z_p = 1 - c/p + c (p - 1)/p * r / (1 - r), r = p^-alpha; alpha solved (bisection) so that
  sum_p E_alpha[v_p] ln p = s; then
  log P(smooth) = sum log Z_p + log Z_2 + sum_{p <= pmax} -log(1 - 1/p) - (1 - alpha) s - 1/2 log(2 pi V), capped at 0,
  V = sum_p Var_alpha[v_p ln p].
2-adic law of t^2 - kN: kN = 3 mod 4: P(v = 1) = 1/2; 5 mod 8: P(v = 2) = 1/2; 1 mod 8: P(v = j) = 2^(1-j), j >= 3;
the rest at v = 0.
Partials (one large prime q in (pmax, L]): P_part(s) = int_{ln pmax}^{ln L} exp(log P(s - t)) / t dt; per eligible prime
q the expected count per polynomial is lambda_q = (2 / q) * sum_x P_smooth(ln |g(x)| - ln q).
"""
import math
import numpy as np

def primes_upto(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(n) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]

def two_adic(kN):
    """(values j, probabilities) of v_2 for t^2 - kN, t uniform."""
    js = np.arange(0, 64)
    pr = np.zeros(64)
    if kN % 4 == 3:
        pr[0], pr[1] = 0.5, 0.5
    elif kN % 8 == 5:
        pr[0], pr[2] = 0.5, 0.5
    elif kN % 8 == 1:
        pr[0] = 0.5
        pr[3:] = 2.0 ** (1 - js[3:])
    else:                                    # kN even (k even): treat as no 2-adic help
        pr[0] = 1.0
    return js, pr

class Model:
    def __init__(self, base_odd, c, kN, pmax):
        self.p = np.array(base_odd, dtype=float)
        self.c = np.array(c, dtype=float)
        self.lp = np.log(self.p)
        self.j2, self.pr2 = two_adic(kN)
        self.norm = float(sum(-math.log(1 - 1 / q) for q in primes_upto(int(pmax))))
        self.lnpmax = math.log(pmax)

    def _stats(self, a):
        r = self.p ** (-a)
        cp = self.c * (self.p - 1) / self.p
        Z = 1 - self.c / self.p + cp * r / (1 - r)
        e = cp * r / (1 - r) ** 2 / Z
        e2 = cp * r * (1 + r) / (1 - r) ** 3 / Z
        w2 = self.pr2 * 2.0 ** (self.j2 * (1 - a))
        Z2 = w2.sum()
        e_2 = (w2 * self.j2).sum() / Z2
        v_2 = (w2 * self.j2 ** 2).sum() / Z2 - e_2 ** 2
        mean = (e * self.lp).sum() + e_2 * math.log(2)
        var = ((e2 - e ** 2) * self.lp ** 2).sum() + v_2 * math.log(2) ** 2
        return np.log(Z).sum() + math.log(Z2), mean, var

    def logP(self, s):
        """log of the smooth probability at ln|Q| = s."""
        if s <= 0:
            return 0.0
        lo, hi = 1e-6, 1.0 - 1e-9
        if self._stats(hi)[1] >= s:            # small s: alpha near 1, the residue is almost surely smooth
            return 0.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if self._stats(mid)[1] > s:
                lo = mid
            else:
                hi = mid
        a = 0.5 * (lo + hi)
        lz, _, var = self._stats(a)
        return min(0.0, lz + self.norm - (1 - a) * s - 0.5 * math.log(2 * math.pi * var))

    def grid(self, smax, step=0.25):
        ss = np.arange(0.0, smax + step, step)
        return ss, np.array([self.logP(s) for s in ss])
