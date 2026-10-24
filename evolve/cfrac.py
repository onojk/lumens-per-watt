"""Continued-fraction card ("cfrac"): Morrison-Brillhart CFRAC on kN, a second relation
source into the same ledger as qs (ledger.py: one k, one factor base).

Cost model: NOTES.md, "CFRAC as a second relation source", written before this code:

  mult     14 ops per candidate multiplier (ks scoring, as qs)
  fb       the ledger's (as qs phase 2)
  cf_step  bit_length(kN) for g = isqrt(kN), then 4 per step: a_(i+1), P_(i+1), Q_(i+1),
           A_i mod N
  cf_td    every residue Q_i: F ops (1 per base entry tried, -1 included) + 1 per extra
           division; the sign entry is free
  la, sqrt the ledger's

Expansion: P_0 = 0, Q_0 = 1, a_0 = g, Q_-1 = kN; P_(i+1) = a_i Q_i - P_i,
Q_(i+1) = Q_(i-1) + a_i (P_i - P_(i+1)), a_(i+1) = (g + P_(i+1)) // Q_(i+1), and
A_(i+1) = a_(i+1) A_i + A_(i-1) mod N, A_-1 = 1, A_0 = g. Relation after step i:
A_i^2 = (-1)^(i+1) Q_(i+1) (mod N). The source stops when the ledger is full, or when
Q_(i+1) = 1 (the end of the period; that step is paid, its residue is not divided).

Tests and hits for the luck meter: one test per residue divided (hit = smooth), and the
ledger's one per dependency tried.

Genes: kc and bc, read exactly as qs reads them. Not a gene: "check": 1 turns the ledger's
relation check on (tests only). Set cfrac.TRACE = {} before a run to record realized counts.
"""
import math
from ledger import Charger, Ledger

TRACE = None

def lamp_cfrac(N, g, m):
    tr = TRACE
    if tr is not None:                         # accumulates over every cfrac stage of the run
        tr.setdefault("ops", {}); tr.setdefault("k_cands", 0); tr.setdefault("attempts", [])
    ch = Charger(m, tr)

    if N % 2 == 0:
        return 2
    if N >= 1 << 100:                          # lampcore's limit (i128 arithmetic), kept here too
        raise ValueError(f"cfrac supports N < 2^100, got a {N.bit_length()}-bit N")
    from lamps import ks_score, KS_PRIMES

    # 1. multiplier
    kc = max(1, int(g.get("kc", 16)))
    ch.charge("mult", kc * len(KS_PRIMES))
    if tr is not None:
        tr["k_cands"] += kc

    ranked = sorted(range(1, kc + 1), key=lambda kk: (-ks_score(kk, N), kk))
    lnN = math.log(N)
    B = max(30, int(g.get("bc", 1.5) * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    for k in ranked:
        at = None
        if tr is not None:
            at = dict(k=k, euler_e=[], ts=[], F=0, rows=0, deps=[], steps=0, residues=[],
                      period_end=False)
            tr["attempts"].append(at)
        led = Ledger(N, k, B, ch, at)
        d = led.build_base() or cf_source(N, k, g, led, ch, at)
        if d:
            return d
        if led.full:
            d = led.solve()
            if d:
                return d
    return None

def cf_source(N, k, g, led, ch, at, until=None):
    """CFRAC relation source on kN until `led` is full (or holds `until` relations, for a
    fixed split with another source) or the period ends. Always None: it never finds a
    factor on its own."""
    if until is not None and len(led.rels) >= until:
        return None                            # nothing to add: no op charged
    charge = ch.charge
    kN = k * N
    base, F = led.base, led.F
    chk = bool(g.get("check", 0))
    if at is not None:
        at["rels"] = led.rels                  # for the acceptance relation check
    charge("cf_step", kN.bit_length())         # g = isqrt(kN)
    g0 = math.isqrt(kN)
    if g0 * g0 == kN:                          # Q_1 = 0: no expansion (never for k < N, N squarefree)
        return None
    P, Q, Qp, a = 0, 1, kN, g0
    A, Ap = g0 % N, 1
    i = 0
    while True:
        charge("cf_step", 4)
        P1 = a * Q - P
        Q1 = Qp + a * (P - P1)
        a1 = (g0 + P1) // Q1
        An = (a1 * A + Ap) % N
        if at is not None:
            at["steps"] += 1
        if Q1 == 1:                            # end of the period: the relations repeat
            if at is not None:
                at["period_end"] = True
            return None
        # residue: A^2 = (-1)^(i+1) Q1 (mod N)
        charge("cf_td", F)
        if at is not None:
            at["residues"].append(Q1)
        vec = [0] * F
        vec[0] = (i + 1) & 1
        v = Q1
        for j in range(1, F):
            p = base[j]
            if v % p == 0:
                v //= p; vec[j] += 1
                while v % p == 0:
                    v //= p; vec[j] += 1; charge("cf_td", 1)
        ch.m.test(v == 1)
        if v == 1 and (led.add(A, vec, 1, chk) or (until is not None and len(led.rels) >= until)):
            return None
        P, Qp, Q, a = P1, Q, Q1, a1
        Ap, A = A, An
        i += 1
