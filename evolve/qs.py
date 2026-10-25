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
          1 op per large prime multiplied into Y, 1 op per Euclid step of gcd(X - Y, N)
  lp      large primes (Stage 7, only when lc > 1): per candidate with cofactor q > 1,
          1 op bound check (q < L); if q < L, 1 op N mod q, 1 op hash lookup, then 1 op
          insert (new q) or 1 op u1*u2 mod N + F ops vector add (combine)

Tests and hits for the luck meter: one test per candidate confirmed (hit = smooth), one
per dependency tried (hit = it splits N).

Genes: kc (multipliers 1..kc ranked by ks score, default 16), bc (B = bc * exp(0.5 sqrt(ln N ln ln N)),
default 1.5),
mc (M = mc * B), tc (threshold = log2(M sqrt(kN/2)) - (tc + lc - 1) * log2(B)),
lc (large-prime bound L = B^lc, 1.0..2.0, default 1.0 = no large primes: today's qs op for op;
NOTES.md, "Stage 7").
Not a gene: "check": 1 turns the ledger's charged relation check on (phase "check"), for the
acceptance test only; mutation never sets it, and absent it is off.
Not a gene: "a_mode": "enumerate" (default: every candidate A formed and charged up front, as
always) or "on_demand" (A's formed one at a time, charged as formed; NOTES.md, "On-demand A
selection"). Set by hand, never mutated. "a_given": a list of A's (prime tuples) used in order
with no selection charge, for the identity test only.

Split (PLAN.md, "Relation economy") into a SOURCE, here: multiplier, polynomials, sieve,
confirmation and large primes (phases 1, 3, 4, 5, 8), and the LEDGER it feeds (ledger.py:
factor base, dedupe, linear algebra, square root; phases 2, 6, 7). One ledger per k.

Set qs.TRACE = {} before a run to record realized counts for the accounting test; with more
than one qs stage in a genome, the counts add up over the run, as lampcore's do.
"""
import math
from itertools import combinations
from ledger import Charger, Ledger, DELTA, _primes

TRACE = None

def lamp_qs(N, g, m):
    tr = TRACE
    if tr is not None:                         # accumulates over every qs stage of the run
        tr.setdefault("ops", {}); tr.setdefault("k_cands", 0); tr.setdefault("attempts", [])
    ch = Charger(m, tr)

    if N % 2 == 0:
        return 2
    if N >= 1 << 100:                          # lampcore's limit (i128 arithmetic), kept here too
        raise ValueError(f"qs supports N < 2^100, got a {N.bit_length()}-bit N")
    from lamps import ks_score, KS_PRIMES

    # 1. multiplier
    kc = max(1, int(g.get("kc", 16)))
    ch.charge("mult", kc * len(KS_PRIMES))
    if tr is not None:
        tr["k_cands"] += kc

    # Multipliers best-first by ks score. An attempt that fails (no dependency splits N, or
    # the polynomials run out) is retried with the next k, paying again for everything:
    # a fresh ledger (2. factor base) for each k.
    ranked = sorted(range(1, kc + 1), key=lambda kk: (-ks_score(kk, N), kk))
    lnN = math.log(N)
    B = max(30, int(g.get("bc", 1.5) * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    for k in ranked:
        at = None
        if tr is not None:
            at = dict(k=k, euler_e=[], ts=[], combos=0, s=0, a_count=0, inv=[], od_cands=0, od_small=0, a_seq=[],
                      n_sieved_setup=0, switches_roots=[], polys=[], cands=[],
                      extra_div=0, F=0, rows=0, deps=[])
            tr["attempts"].append(at)
        led = Ledger(N, k, B, ch, at)
        d = led.build_base() or sieve_source(N, k, g, led, ch, at)
        if d:
            return d
        if led.full:
            d = led.solve()
            if d:
                return d
    return None

def a_on_demand(pool, s, q, target, charge, at):
    """a_mode = on_demand (NOTES.md, "On-demand A selection"): A's formed one at a time, each
    charged when formed. Prefixes are the (s - 1)-combinations of the pool ordered by closeness
    to q; the last prime is the pool prime closest to target / A'. Per candidate: s - 2
    multiplies for A', 1 division, 1 multiply for A, 1 target check (full), one comparison per
    pool prime considered for the last, and, if the check passes, s comparisons per A already
    used (small): a candidate sharing more than s - 2 primes with any used A is rejected (a
    duplicate shares s), since A's that differ in one prime find the same u (NOTES.md, amendment)."""
    by_q = sorted(pool, key=lambda p: (abs(math.log(p / q)), p))
    used = []
    for pre in combinations(by_q, s - 1):
        Ap = math.prod(pre); charge("setup", s - 2)
        tp = target / Ap; charge("setup", 1)
        rest = [p for p in pool if p not in pre]
        last = min(rest, key=lambda p: (abs(math.log(p / tp)), p)); charge("setup", len(rest))
        A = Ap * last; charge("setup", 1)
        charge("setup", 1)                     # target check
        if at is not None:
            at["od_cands"] += 1
            at["od_small"] += len(rest)
        if abs(math.log2(A / target)) > 0.25:
            continue
        key = tuple(sorted(pre + (last,)))
        charge("setup", s * len(used))
        if at is not None:
            at["od_small"] += s * len(used)
        if any(len(set(key) & set(u)) > s - 2 for u in used):
            continue
        used.append(key)
        yield key

def sieve_source(N, k, g, led, ch, at):
    """SIQS relation source on kN: phases 3, 4, 5 and 8 until `led` is full or the polynomials
    run out. Returns a factor if one turns up on the way (a large prime dividing N), else None."""
    import numpy as np
    charge = ch.charge
    kN = k * N
    B, base, roots_t, F, idx = led.B, led.base, led.roots_t, led.F, led.idx
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
    given = g.get("a_given")                   # test hook (acceptance only): a fixed A sequence, no selection charge
    if given is not None:
        combos = [tuple(c) for c in given]
        assert all(len(c) == s for c in combos)
        if at is not None:
            at["combos"], at["s"] = 0, s
    elif g.get("a_mode", "enumerate") == "on_demand" and s >= 2:
        combos = a_on_demand(pool, s, q, target, charge, at)
        if at is not None:
            at["combos"], at["s"] = 0, s
    else:
        combos = list(combinations(pool, s))
        charge("setup", (s - 1) * len(combos))     # multiplies forming each A
        combos.sort(key=lambda c: (abs(math.log(math.prod(c) / target)), c))
        if at is not None:
            at["combos"], at["s"] = len(combos), s
    lc = min(2.0, max(1.0, g.get("lc", 1.0)))
    LP = lc > 1.0                              # lc = 1.0: no large-prime work at all
    L = B ** lc                                # <= B^2, so a cofactor below it is prime
    T = math.log2(M * math.sqrt(kN / 2)) - (g.get("tc", 2.0) + (lc - 1.0)) * math.log2(B)
    width = 2 * M + 1
    chk = bool(g.get("check", 0))              # ledger check: qs's acceptance test only
    partials = {}                              # q -> (u, vec)
    if at is not None:
        at["lp"] = dict(cof=0, lt=0, inserts=0, combos=0, dup=0, F=F)
        at["rels"] = led.rels                  # for the acceptance relation check
    for qs_ in combos:
        A = math.prod(qs_)
        if at is not None:
            at["a_count"] += 1
            at["a_seq"].append(qs_)
        Bl = []
        for ql in qs_:
            Aq = A // ql; charge("setup", 1)
            inv, st = ch.euclid_inv(Aq % ql, ql, "setup")
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
            ainv, st = ch.euclid_inv(A % p, p, "setup")
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
                    ch.m.test(False)
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
                partial = False
                if LP and not smooth:              # 8. large primes
                    charge("lp", 1)                # bound check
                    partial = v < L
                    if at is not None:
                        at["lp"]["cof"] += 1; at["lp"]["lt"] += partial
                ch.m.test(smooth or partial)
                if not (smooth or partial):
                    continue
                u = A * x + Bv
                for ql in qs_:
                    vec[idx[ql]] += 1
                if smooth:
                    if led.add(u, vec, 1, chk):
                        return None
                    continue
                charge("lp", 1)                    # N mod q
                if N % v == 0:
                    return v
                charge("lp", 1)                    # hash lookup
                other = partials.get(v)
                if other is None:
                    charge("lp", 1)                # insert
                    partials[v] = (u, vec)
                    if at is not None:
                        at["lp"]["inserts"] += 1
                    continue
                cu = other[0] * u % N; charge("lp", 1)
                cvec = [a + b for a, b in zip(other[1], vec)]; charge("lp", F)
                if at is not None:
                    at["lp"]["combos"] += 1
                if led.add(cu, cvec, v, chk):
                    return None
    return None
