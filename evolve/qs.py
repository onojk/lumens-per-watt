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
lc (large-prime bound L = B^lc, 1.0..3.0, default 1.0 = no large primes: today's qs op for op;
NOTES.md, "Stage 7").
Not a gene: "check": 1 turns the ledger's charged relation check on (phase "check"), for the
acceptance test only; mutation never sets it, and absent it is off.
Not a gene: "a_mode": "enumerate" (default: every candidate A formed and charged up front, as
always) or "on_demand" (A's formed one at a time, charged as formed; NOTES.md, "On-demand A
selection"). Set by hand, never mutated. "kset": "sf32" scores only the squarefree k <= 32 (kc ignored; NOTES.md, "kc becomes a
constant"). "confirm": "resieve" confirms each candidate by re-sieving: primes >= "p0" (default 30) are
matched by walking their roots over a candidate bitmap (word-level ops), and v is divided only by the
matched primes and the primes below p0 or not sieved (NOTES.md, "Root-matched candidate confirmation").
"sort_charge": 1 charges every sort in the card (NOTES.md,
"The sort_charge option"); 0 or absent: today's counts. "a_given": a list of A's (prime tuples) used in order
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
TRACE_ARR = False    # trace only (step 9): also keep each polynomial's A, B, C, sieve array and threshold
# Work trace (IDEAS I-044; read-only, default off; no charge or count depends on it): set
# WORKTRACE = {"target": n, "meter": "corrected" or "uncorrected"} and the n-th polynomial of the run (0-based, over
# all attempts) records its work as WORKTRACE["events"]: (x, op type, charged) per op, in the order the card does it.
# x is the sieve position (0 .. width - 1) the op touches, or the candidate's position for per-candidate work.
# "meter": "uncorrected" marks the free 2's writes uncharged, as before the free-2 correction (6031239).
WORKTRACE = None

def _wt(wt, x, typ, n=1, charged=True):
    for _ in range(n):
        wt["events"].append((x, typ, charged))

def _sieve_sums(arr, par, w2):
    """Trace only: the sieve array without the free 2 (stage H), as step9.py and pp_accept.py read it."""
    a = arr.copy()
    if par is not None:
        a[par::2] -= w2
    return a

def lamp_qs(N, g, m):
    tr = TRACE
    if tr is not None:                         # accumulates over every qs stage of the run
        tr.setdefault("ops", {}); tr.setdefault("k_cands", 0); tr.setdefault("attempts", [])
    ch = Charger(m, tr)

    if N % 2 == 0:
        return 2
    if N >= 1 << 100:                          # lampcore's limit (i128 arithmetic), kept here too
        raise ValueError(f"qs supports N < 2^100, got a {N.bit_length()}-bit N")
    from lamps import ks_rank

    # 1. multiplier
    # kset "sf32" (NOTES.md, "kc becomes a constant"): the squarefree k <= 32; absent: 1..kc
    cands = SF32 if g.get("kset") == "sf32" else list(range(1, max(1, int(g.get("kc", 16))) + 1))
    kc = len(cands)
    sc, (mu, wo, fl) = ks_rank(N, cands)      # I-021 (NOTES.md, "I-021 adopted"): symbols, charged by the work
    ch.charge("mult", mu); ch.charge("word", wo); ch.charge("flog", fl)
    if tr is not None:
        tr["k_cands"] += kc

    # Multipliers best-first by ks score. An attempt that fails (no dependency splits N, or
    # the polynomials run out) is retried with the next k, paying again for everything:
    # a fresh ledger (2. factor base) for each k.
    ranked = sorted(cands, key=lambda kk: (-sc[kk], kk))
    SC = bool(g.get("sort_charge", 0))
    if SC:                                     # sort_charge: the multiplier ranking (keys already charged)
        ch.charge("sortc", sort_cost(kc))     # comparisons (audit item 2: sort_cmp)
    lnN = math.log(N)
    B = max(30, int(g.get("bc", 1.5) * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    for k in ranked:
        at = None
        if tr is not None:
            at = dict(k=k, euler_e=[], ts=[], combos=0, s=0, a_count=0, inv=[], od_prefixes=0, od_cands=0, od_small=0, a_seq=[],
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

SF32 = [1, 2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31]   # squarefree k <= 32

def merge_asc(a, b):
    """Linear merge of two ascending lists of distinct ints (re-sieve's prime list; NOTES.md, item 11)."""
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:]); out.extend(b[j:])
    return out

def sort_cost(n):
    """sort_charge (NOTES.md, "The sort_charge option"): n ceil(log2 n) comparisons for n >= 2."""
    return n * (n - 1).bit_length() if n >= 2 else 0

def a_on_demand(pool, s, q, target, charge, at, sc=False, by_q=None):
    """a_mode = on_demand (NOTES.md, "On-demand A selection", second amendment): A's formed one at
    a time, each charged when formed. Prefixes are the (s - 1)-combinations of the pool ordered
    by closeness to q. A prefix lying within a used A is skipped ((s - 1) small ops per used A).
    Otherwise A' (s - 2 multiplies) and t' = target / A' (1 op), then last primes are tried in
    order of closeness to t' (a scan of the remaining pool primes, small; 1 multiply and 1 target
    check, full): the first try failing the target check ends the prefix; a try passing it is
    compared with every used A (s small ops each) and accepted if it shares at most s - 2 primes
    with each (A's differing in one prime find the same u). If that pass runs out of prefixes,
    pass 2 walks them again (third amendment), paying again, with no prefix check, and accepts
    any A not already used."""
    # the pool in closeness order, as the pool selection already produced it (item 12: no re-sort)
    by_q = list(by_q)
    used = []
    for limit in (s - 2, s - 1):
        if limit == s - 1 and at is not None:
            at["od_pass2"] = 1
        yield from _a_pass(by_q, pool, s, target, charge, at, used, limit, sc)

def _a_pass(by_q, pool, s, target, charge, at, used, limit, sc):
    for pre in combinations(by_q, s - 1):
        if limit == s - 2:
            charge("word", (s - 1) * len(used))    # prefix-overlap check (audit item 1)
            if at is not None:
                at["od_small"] += (s - 1) * len(used)
            if any(all(p in u for p in pre) for u in used):
                continue
        Ap = math.prod(pre); charge("word", s - 2)      # word multiplies (audit item 3)
        tp = target / Ap; charge("fdiv", 1)             # a double divide (audit item 1)
        if at is not None:
            at["od_prefixes"] += 1
        rest = [p for p in pool if p not in pre]
        charge("word", len(pool))              # building rest: one word op per pool prime (item 13)
        while rest:
            last = min(rest, key=lambda p: (abs(math.log(p / tp)), p)); charge("flog", len(rest))   # a log per scanned prime (item 1)
            if at is not None:
                at["od_small"] += len(rest)
            rest.remove(last); charge("word", 1)    # the removal (item 13)
            A = Ap * last; charge("word", 1)    # a word multiply (audit item 3)
            charge("flog", 1)                  # target check: a log (audit item 1)
            if at is not None:
                at["od_cands"] += 1
            if abs(math.log2(A / target)) > 0.25:
                break
            key = tuple(sorted(pre + (last,)))
            if sc:                             # sort_charge: the key's s primes
                charge("sortc", sort_cost(s))
            if at is not None:
                at["od_keys"] = at.get("od_keys", 0) + 1
            charge("word", s * len(used))          # overlap compare (audit item 1)
            if at is not None:
                at["od_small"] += s * len(used)
            if any(len(set(key) & set(u)) > limit for u in used):
                continue
            used.append(key)
            yield key
            break

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
    # M mod p once per attempt (NOTES.md, "Meter correction: the sieve's start offsets"): one small-modulus
    # op per odd factor-base prime; each start is then r + m_p (- p), one word op per root
    mp = {p: M % p for p in base[2:]}; charge("setup", len(base) - 2)
    s = 1
    while target ** (1 / s) > pool_all[-1] and s < 8:
        s += 1
    while s > 1 and target ** (1 / s) < pool_all[min(len(pool_all) - 1, 2)]:
        s -= 1
    q = target ** (1 / s)
    P = min(len(pool_all), 40 if s == 1 else 16 + 4 * s)
    closeness = sorted(pool_all, key=lambda p: (abs(math.log(p / q)), p))[:P]
    pool = sorted(closeness)
    sc = bool(g.get("sort_charge", 0))
    if sc:                                     # sort_charge: pool selection (n keys + comparisons), then ascending
        charge("flog", len(pool_all))          # the keys: a log each (audit item 2)
        charge("sortc", sort_cost(len(pool_all)) + sort_cost(P))
    if at is not None:
        at["n_pool_all"], at["P"] = len(pool_all), P
    given = g.get("a_given")                   # test hook (acceptance only): a fixed A sequence, no selection charge
    if given is not None:
        combos = [tuple(c) for c in given]
        assert all(len(c) == s for c in combos)
        if at is not None:
            at["combos"], at["s"] = 0, s
    elif g.get("a_mode", "enumerate") == "on_demand" and s >= 2:
        combos = a_on_demand(pool, s, q, target, charge, at, sc, by_q=closeness)
        if at is not None:
            at["combos"], at["s"] = 0, s
    else:
        combos = list(combinations(pool, s))
        charge("word", (s - 1) * len(combos))      # word multiplies forming each A (audit item 3)
        combos.sort(key=lambda c: (abs(math.log(math.prod(c) / target)), c))
        if sc:                                 # sort_charge: the candidate sort (C keys + comparisons)
            charge("flog", len(combos)); charge("sortc", sort_cost(len(combos)))
        if at is not None:
            at["combos"], at["s"] = len(combos), s
    lc = min(3.0, max(1.0, g.get("lc", 1.0)))    # clamp 3.0 (NOTES.md, "(A2)"): above 2.0 a cofactor may be composite
    LP = lc > 1.0                              # lc = 1.0: no large-prime work at all
    L = B ** lc                                # lc <= 2: a cofactor below L is prime; above, filed the same way
    T = math.log2(M * math.sqrt(kN / 2)) - (g.get("tc", 2.0) + (lc - 1.0)) * math.log2(B)
    width = 2 * M + 1
    # stage H (NOTES.md, "Stage H: sieve 2 and small prime powers"): gene pp, prime powers q = p^j < 2^pp walked
    # like base primes (odd p with two roots, p not dividing k; 2^j, 4 <= j, only when kN = 1 mod 8), and the
    # prime 2's fixed part w2 added on one parity class by a second threshold at the scan; pp absent or 0: off
    PPB = int(g.get("pp", 0))
    ppe = []                                   # per power entry: [q, p, the roots of t^2 = kN mod q, log value, M mod q]
    w2 = 0
    if PPB:
        for p in base[2:]:
            t = roots_t[p]
            if k % p == 0 or p * p >= 1 << PPB:
                continue
            inv, st = ch.euclid_inv(2 * t % p, p, "setup")     # (2t)^-1 mod p, for the Hensel lifts
            if at is not None:
                at["inv"].append((2 * t % p, p, st))
            q, tq = p, t
            while q * p < 1 << PPB:
                d = (tq * tq - kN) % (q * p)       # a multiple of q
                tq += q * (-(d // q) * inv % p)
                q *= p
                charge("setup", 3)                 # kN mod q with the square, times the inverse, the update
                ppe.append([q, p, [tq, q - tq], logp[p], M % q]); charge("setup", 1)    # M mod q
        if kN % 8 == 1:
            s2, j = 1, 4
            while 1 << j < 1 << PPB:
                q = 1 << j
                if (s2 * s2 - kN) % q:
                    s2 += 1 << (j - 2)
                charge("setup", 1)                 # the square and compare
                ppe.append([q, 2, [s2, q - s2, (s2 + q // 2) % q, (q - s2 + q // 2) % q], 1, M % q]); charge("setup", 1)
                j += 1
        w2 = 1 if kN % 4 in (2, 3) else (2 if kN % 8 == 5 else 3)
        charge("word", 2)                          # M mod 2, w2 from kN mod 8
    chk = bool(g.get("check", 0))              # ledger check: qs's acceptance test only
    RS = g.get("confirm") == "resieve"         # root-matched confirmation by re-sieving; P0: below it, divide directly
    RT = g.get("confirm") == "root"            # I-029 root confirm (NOTES.md, "Root confirm (I-029) as a card option")
    GOFF = g.get("goff", 0) != 0               # I-032 2'a: start offsets kept by the Gray code (NOTES.md, "I-032 option 2'a")
    P0 = int(g.get("p0", 30))
    partials = {}                              # q -> (u, sparse exponent list)
    # step 1 (NOTES.md, "Step 1: delete the fills"): one exponent vector per attempt, reused (F word); with
    # re-sieve, the slot array (width) and the generation stamps (F) once per attempt
    ev = [0] * F
    charge("word", F + (width + F if RS else 0))
    if RT:
        charge("setup", F - 2)                 # root confirm: each odd base prime's reciprocal (a 64-bit divide)
    if at is not None:
        at["s1"] = dict(attempt=F + (width + F if RS else 0), cand=0, comb=0, T=0, Tk=0, kept=0)
    if at is not None:
        at["lp"] = dict(cof=0, lt=0, inserts=0, combos=0, dup=0, F=F)
        at["rels"] = led.rels                  # for the acceptance relation check
    for qs_ in combos:
        A = math.prod(qs_)
        qj = [idx[ql] for ql in qs_]           # A's primes' base indices, once per A (NOTES.md, "Cost note (before code): the A-prime lookup fix"); uncharged
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
            Bl.append(Aq * gam); charge("word", 1)    # a word multiply (audit item 4); A/q above stays small-modulus
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
        qe = []                                # stage H: per power entry [q, roots, 2 B_l A^-1 mod q, log value, M mod q]
        par = None
        if PPB:
            for q, p, ts, lv, mq in ppe:
                if A % p == 0:
                    continue
                ar = A % q; charge("setup", 1)
                ainv, st = ch.euclid_inv(ar, q, "setup")
                if at is not None:
                    at["inv"].append((ar, q, st))
                rs = [ainv * ((t - Bv) % q) % q for t in ts]; charge("setup", len(ts))
                bainv = []
                for b in Bl:
                    bainv.append(2 * b * ainv % q); charge("setup", 1)
                qe.append([q, rs, bainv, lv, mq])
            par = (Bv + M + kN % 2) % 2; charge("word", 1)    # the parity class whose threshold is T - w2
        if GOFF:                               # 2'a: each root to its start offset r + M mod p (- p), once per A, one word op per root
            for ent in st_:
                p = ent[0]
                ent[1] = [r + mp[p] - p if r + mp[p] >= p else r + mp[p] for r in ent[1]]
            for ent in qe:
                q, mq = ent[0], ent[4]
                ent[1] = [r + mq - q if r + mq >= q else r + mq for r in ent[1]]
            charge("word", sum(len(e[1]) for e in st_) + sum(len(e[1]) for e in qe))
            if RT:                             # 2'b (NOTES.md, "I-032 option 2'b"): per sieved prime its base index and its
                rtab = [(idx[ent[0]], ent) for ent in st_]   # live entry (offsets read in place); first-root index and reciprocal, 2 word
                charge("word", 2 * len(rtab))
                aj = sorted(idx[ql] for ql in qs_)
        signs = [1] * s
        for i in range(1 << (s - 1)):
            wt = None
            if WORKTRACE is not None:          # work trace (read-only): is this the traced polynomial?
                n_ = WORKTRACE.setdefault("n", 0)
                WORKTRACE["n"] = n_ + 1
                if n_ == WORKTRACE["target"]:
                    wt = WORKTRACE
                    wt.update(events=[], width=width, M=M, F=F, goff=GOFF, rt=RT, pp=PPB, i=i)
            if i:                              # Gray code: flip one B_l, update every root
                v = (i & -i).bit_length()      # flips B_v, v in 1..s-1
                d = signs[v]
                signs[v] = -d
                Bv -= 2 * d * Bl[v]
                n_roots = 0
                for ent in st_:
                    p, rs, bainv = ent
                    bi = bainv[v]              # r, bi in [0, p): add or subtract, one conditional correction
                    ent[1] = [r + bi - p if r + bi >= p else r + bi for r in rs] if d > 0 else \
                             [r - bi + p if r < bi else r - bi for r in rs]
                    n_roots += len(rs)
                for ent in qe:
                    q, rs, bainv = ent[0], ent[1], ent[2]
                    bi = bainv[v]
                    ent[1] = [r + bi - q if r + bi >= q else r + bi for r in rs] if d > 0 else \
                             [r - bi + q if r < bi else r - bi for r in rs]
                    n_roots += len(rs)
                charge("gray", n_roots)            # word-level type setup_gray (NOTES.md, "Gray-code root update re-typed")
                if wt is not None:
                    for ent in st_ + qe:
                        for r in ent[1]:
                            _wt(wt, r if GOFF else (r + mp.get(ent[0], 0)) % width, "setup_gray")
                if at is not None:
                    at["switches_roots"].append(n_roots)
            C = (Bv * Bv - kN) // A
            # 4. sieve
            arr = np.zeros(width, dtype=np.int32)
            if wt is not None:
                for x_ in range(width):
                    _wt(wt, x_, "sieve_scan")      # the clear (paid by the width charge)
            if par is not None:                # stage H: the free 2 by initialisation (the scan fix); its writes charged below
                arr[par::2] = w2
                if wt is not None:
                    for x_ in range(par, width, 2):
                        _wt(wt, x_, "sieve_scan:free2", charged=wt["meter"] == "corrected")
            upd = 0
            hits = []
            nr = 0
            for p, rs, _ in st_:
                for r in rs:
                    if GOFF:                       # 2'a: the kept offset; the trace keeps the x-root (trace only, uncharged)
                        start = r
                        r = (r - mp[p]) % p
                    else:
                        start = r + mp[p]
                        if start >= p:
                            start -= p
                        nr += 1
                    arr[start::p] += logp[p]
                    upd += (width - 1 - start) // p + 1
                    hits.append((p, r))
                    if wt is not None:
                        if not GOFF:
                            _wt(wt, start, "word")    # the start offset
                        for x_ in range(start, width, p):
                            _wt(wt, x_, "sieve_update")
            for q, rs, _, lv, mq in qe:
                for r in rs:
                    if GOFF:
                        start = r
                    else:
                        start = r + mq
                        if start >= q:
                            start -= q
                        nr += 1
                    arr[start::q] += lv
                    upd += (width - 1 - start) // q + 1
                    if wt is not None:
                        if not GOFF:
                            _wt(wt, start, "word")
                        for x_ in range(start, width, q):
                            _wt(wt, x_, "sieve_update")
            charge("word", nr)                     # start offsets, one word op per root
            charge("sieve", upd)
            charge("sieve", width)
            f2 = (width - par + 1) // 2 if par is not None else 0   # meter correction: the free 2's writes, one sieve_scan
            if f2:                                                   # per cell written (NOTES.md, "Meter correction ... free-2")
                charge("sieve", f2)
            if RT and not GOFF:                    # root confirm: the sieved roots' start offsets stored, one word per root
                rtab = []                          # per sieved base prime, ascending: (base index, p, its start offsets)
                for p, rs, _ in st_:
                    st0 = [(r + mp[p]) - p if r + mp[p] >= p else r + mp[p] for r in rs]
                    rtab.append((idx[p], p, st0))
                charge("word", sum(len(e[2]) for e in rtab))
                aj = sorted(idx[ql] for ql in qs_)
            if at is not None:
                at["polys"].append({"M": M, "roots": hits, "upd": upd, "f2": f2, "par": par,
                                    "sieved": [p for p, _, _ in st_],
                                    "rp": {p: len(rs) for p, rs, _ in st_}})
            cand = np.nonzero(arr >= T)[0].tolist()
            if wt is not None:
                for x_ in range(width):
                    _wt(wt, x_, "sieve_scan")      # the scan (paid by the width charge)
                wt["cand"] = list(cand)
            if at is not None:
                at["polys"][-1]["nc"] = len(cand)   # trace only: candidates of this polynomial (all, processed or not)
            if RS:                                 # re-sieve (NOTES.md, "Root-matched candidate confirmation")
                rec = {i0: [] for i0 in cand}
                walk = nhit = 0
                for p, rs, _ in st_:
                    if p < P0:
                        continue
                    for r in rs:
                        if GOFF:
                            start = r                      # 2'a: the kept offset, no add
                        else:
                            start = r + mp[p]
                            if start >= p:
                                start -= p
                            walk += 1                      # the start offset, one word op per root walked
                        if start >= width:
                            continue
                        walk += 2 * ((width - 1 - start) // p + 1)   # index step + bitmap test per position
                        for i0 in range(start, width, p):
                            if i0 in rec:
                                rec[i0].append(idx[p]); nhit += 1
                charge("word", len(cand) + walk + nhit)     # bitmap set per candidate, the walk, one per hit
                sieved_j = {idx[p] for p, _, _ in st_}
                direct = [j for j in range(1, F) if base[j] < P0 or j not in sieved_j]
                # per polynomial, counted as lampcore does it: the slots cleared after the walk (|cand|), the
                # generation stamps written (|st|), the direct list's pass (F - 1), the record lists (|cand|)
                charge("word", 2 * len(cand) + len(st_) + F - 1)
            if at is not None and TRACE_ARR:      # step 9 (read-only): the polynomial, its sieve array, where confirm starts
                at["polys"][-1].update(A=A, B=Bv, C=C, arr=_sieve_sums(arr, par, w2), T=T, par=par, w2=w2, Mw=M, c0=len(at["cands"]), cand_pos=list(cand))
            # 5. confirm
            for i0 in cand:
                x = i0 - M
                v = (A * x + 2 * Bv) * x + C; charge("word", 2)   # two word multiply-adds (audit item 5)
                if wt is not None:
                    _wt(wt, i0, "word", 3)                        # v, and the sign check below
                    if RT:
                        _wt(wt, i0, "root_test", len(rtab))
                if RS:                             # merge two ascending lists, |plist| word ops (NOTES.md, item 11)
                    plist = merge_asc(direct, rec[i0]); charge("word", len(plist))
                else:
                    plist = range(1, F)
                charge("word", 1)                  # the sign check (audit item 8)
                if RT:
                    charge("root", len(rtab))      # the root test, one per sieved base prime
                else:
                    charge("confirm", len(plist) if RS else F - 1)
                if at is not None:
                    at["cands"].append(v)
                TT = []                             # entries touched in the reused vector (step 1)
                if v < 0:
                    ev[0] = 1; TT.append(0); v = -v
                if v == 0:
                    s1w = 2 * len(TT); charge("word", s1w)      # sets + clear
                    for j in TT:
                        ev[j] = 0
                    if at is not None:
                        at["s1"]["cand"] += s1w; at["s1"]["T"] += len(TT)
                    ch.m.test(False)
                    continue
                if RT:                             # root confirm: hits, the prime 2 by the low bit, A's primes by v mod p
                    rh = ([j for j, ent in rtab if i0 % ent[0] in ent[1]] if GOFF else
                          [j for j, p, st0 in rtab if i0 % p in st0])
                    charge("word", 1)
                    dl = [1] if v % 2 == 0 else []
                    for j in aj:
                        charge("confirm", 1)
                        if v % base[j] == 0:
                            dl.append(j)
                    charge("confirm", len(rh) + (v % 2 == 0))   # the first division by each hit and an even v
                    plist = merge_asc(dl, rh); charge("word", len(plist))
                    if wt is not None:
                        _wt(wt, i0, "word", 1 + len(plist))
                        _wt(wt, i0, "confirm_td", len(aj) + len(rh) + (v % 2 == 0))
                elif wt is not None:
                    _wt(wt, i0, "confirm_td", F - 1)
                for j in plist:
                    p = base[j]
                    if v % p == 0:
                        v //= p; ev[j] += 1; TT.append(j)
                        if wt is not None:
                            _wt(wt, i0, "word")    # the set
                        while v % p == 0:
                            v //= p; ev[j] += 1; charge("confirm", 1)
                            if wt is not None:
                                _wt(wt, i0, "confirm_td")
                            if at is not None:
                                at["extra_div"] += 1
                smooth = v == 1
                partial = False
                if LP and not smooth:              # 8. large primes
                    charge("word", 1)              # bound check (audit item 6)
                    partial = v < L
                    if wt is not None:
                        _wt(wt, i0, "word")
                    if at is not None:
                        at["lp"]["cof"] += 1; at["lp"]["lt"] += partial
                ch.m.test(smooth or partial)
                if not (smooth or partial):
                    s1w = 2 * len(TT); charge("word", s1w)      # sets + clear
                    for j in TT:
                        ev[j] = 0
                    if at is not None:
                        at["s1"]["cand"] += s1w; at["s1"]["T"] += len(TT)
                    if wt is not None:
                        _wt(wt, i0, "word", len(TT))           # the clear
                    continue
                u = A * x + Bv
                Tk = list(TT)
                for j in qj:                       # the A-primes (uncharged until item 15); indices from qj
                    if ev[j] == 0:
                        Tk.append(j)
                    ev[j] += 1
                vec = [(j, ev[j]) for j in Tk]     # the sparse relation
                s1w = len(TT) + 2 * len(Tk); charge("word", s1w + len(qs_))   # sets, the sparse copy, the clear; item 15: the A-prime adds
                if wt is not None:
                    _wt(wt, i0, "word", 2 * len(Tk) + len(qs_))   # the sparse copy, the clear, the A-prime adds
                for j in Tk:
                    ev[j] = 0
                if at is not None:
                    at["s1"]["cand"] += s1w; at["s1"]["T"] += len(TT); at["s1"]["Tk"] += len(Tk); at["s1"]["kept"] += 1
                    if smooth:
                        at["s1"]["Tf"] = at["s1"].get("Tf", 0) + len(Tk); at["s1"]["nf"] = at["s1"].get("nf", 0) + 1
                if smooth:
                    if wt is not None:
                        _wt(wt, i0, "hash"); _wt(wt, i0, "word")   # the ledger's dedupe probe and its word
                    if led.add(u, vec, 1, chk):
                        return None
                    continue
                charge("lp", 1)                    # N mod q
                if wt is not None:
                    _wt(wt, i0, "lp_small"); _wt(wt, i0, "hash")
                if N % v == 0:
                    return v
                charge("hash", 1)                  # hash lookup (audit item 6)
                other = partials.get(v)
                if other is None:
                    charge("hash", 1)              # insert (audit item 6)
                    if wt is not None:
                        _wt(wt, i0, "hash")
                    partials[v] = (u, vec)
                    if at is not None:
                        at["lp"]["inserts"] += 1
                    continue
                cu = other[0] * u % N; charge("lp", 1)
                out = []                           # sparse combination through the clean vector (step 1)
                for j, e in other[1] + vec:
                    if ev[j] == 0:
                        out.append(j)
                    ev[j] += e
                cvec = [(j, ev[j]) for j in out]
                for j in out:
                    ev[j] = 0
                s1c = len(other[1]) + len(vec) + 2 * len(out); charge("word", s1c)
                if wt is not None:
                    _wt(wt, i0, "lp_full"); _wt(wt, i0, "word", s1c); _wt(wt, i0, "hash"); _wt(wt, i0, "word", 2)
                if at is not None:
                    at["s1"]["comb"] += s1c
                if at is not None:
                    at["lp"]["combos"] += 1
                if led.add(cu, cvec, v, chk):
                    return None
    return None
