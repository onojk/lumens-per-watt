"""Acceptance test for the ECM card (NOTES.md, "Stage 8: elliptic-curve card"), default genes.

1. Completeness, cap 2^29: every one of
   - balanced: semiprimes_pq(bits, 40, 2700000 + bits) at 40, 44, ..., 84 bits;
   - unbalanced: semiprimes_unbalanced(bits, pbits, 40, 2800000 + 100 pbits + bits) at
     72/78/84 bits with a 24-, 28- and 32-bit smaller factor.
2. Exact accounting, every run, tolerance 0. Each phase is recomputed here from N, the genes
   and how each curve ended (the trace's per-curve end state), never from the lamp's counts:
   - setup: 10 multiplies + Euclid steps of 16 u^3 v mod N, recomputed from sigma + 1 for the
     numerator times the inverse when it exists;
   - stage 1: the independent ladder recount, 5 + 11 (bit_length(q) - 1) per prime power
     q <= B1, from this file's own prime sieve and B1;
   - stage 2: 5 (2Q) + 51 * 6 (baby steps) + the ladders for 210 Q and j0 W + 6 per giant step
     + 3 per (j, b) pair, the pairs counted here;
   - gcd: 1 after stage 1, 1 after stage 2.
3. Group-order check (harness only): on semiprimes with both factors below 2^20
   (semiprimes_pq(bits, 150, 3100000 + bits) at 36, 38, 40 bits), genes b1 = 4 (GO_GENES,
   B1 ~ 220), every curve's end state
   is predicted from brute force: the group order of the curve (or its twist) mod p and mod q
   by point counting, the order of the starting point, and from those whether stage 1
   (order | prod of prime powers <= B1) or stage 2 (the stage-1 point's order divides jw + b or
   jw - b for some pair the card evaluates) catches p, q, both or neither. The prediction
   must equal what the card did, curve by curve. Skipped and counted: curves singular mod p
   or q, and curves where an x-only differential addition of the card would be degenerate
   mod p or q (a difference point with X = 0 or Z = 0 mod p: a stage-1 base landing on the
   2-torsion point (0, 0), or a baby/giant-step difference that is O). There x-only
   arithmetic leaves the group law, so the card may find p where group theory says it
   cannot, or miss it; any gcd it takes is still a true divisor.
4. Mutation test (python3 ecm_accept.py WORKERS mutate): each charge line in ecm.py in turn
   gets one extra op; the accounting must fail for every one.

  python3 ecm_accept.py [workers] [mutate]  -> ecm_accept.json (not in mutate mode)
"""
import json, math, sys, types
from multiprocessing import Pool
import numpy as np
import ecm
from lamps import Meter, Budget
from fastlamps import semiprimes_pq, semiprimes_unbalanced

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
MUTATE = len(sys.argv) > 2 and sys.argv[2] == "mutate"
CAP = 2 ** 29
G = {"t": "ecm"}                                   # default genes
BALANCED = list(range(40, 85, 4))
UNBALANCED = [(b, pb) for b in (72, 78, 84) for pb in (24, 28, 32)]
PHASES = ["ecm_setup", "ecm_s1", "ecm_s2", "ecm_gcd"]
GO_SIZES = (36, 38, 40)                            # group-order check: both factors < 2^20
# b1 = 4 (B1 ~ 220) for the group-order check: at default B1 (~55 here) the stage-1 point's
# order often keeps a factor 2 or 3 beyond the prime powers, which makes giant-step differences
# O and leaves the group law (x-only); at real sizes B1 is 500-1100 and that is rare.
GO_GENES = {"t": "ecm", "b1": 4.0, "b2": 50}
W = 210

def sieve(n):
    s = [True] * (n + 1)
    s[0] = s[1] = False
    for i in range(2, math.isqrt(n) + 1):
        if s[i]:
            for j in range(i * i, n + 1, i):
                s[j] = False
    return s

def bounds(N, g=G):
    s = math.isqrt(N)
    ls = math.log(s)
    B1 = max(10, int(g.get("b1", 1.0) * math.exp(math.sqrt(ls * math.log(ls)) / math.sqrt(2))))
    return B1, int(g.get("b2", 50) * B1)

def ladder_ops(k):
    return 5 + 11 * (k.bit_length() - 1)

class Plan:
    """Everything about a run that depends only on N and the genes."""
    def __init__(self, N, g=G):
        self.N = N
        self.B1, self.B2 = bounds(N, g)
        pr = sieve(max(self.B1, self.B2))
        self.isprime = pr
        self.pp = []
        for p in range(2, self.B1 + 1):
            if pr[p]:
                q = p
                while q * p <= self.B1:
                    q *= p
                self.pp.append(q)
        self.K = math.prod(self.pp)
        self.s1 = sum(ladder_ops(q) for q in self.pp)
        self.j0, self.jmax = max(1, self.B1 // W), -(-self.B2 // W)
        baby = [b for b in range(1, W // 2, 2) if math.gcd(b, W) == 1]
        self.pairs = [(j, b) for j in range(self.j0, self.jmax + 1) for b in baby
                      if any(self.B1 < x <= self.B2 and pr[x] for x in (j * W + b, j * W - b))]
        self.s2 = (5 + 51 * 6 + ladder_ops(W) + ladder_ops(self.j0) + 6 * (self.jmax - self.j0)
                   + 3 * len(self.pairs))

def setup_parts(N, sigma):
    u, v = (sigma * sigma - 5) % N, 4 * sigma % N
    den = 16 * u ** 3 * v % N
    num = pow(v - u, 3, N) * (3 * u + v) % N
    r0, r1, steps = N, den, 0
    while r1:
        r0, r1 = r1, r0 % r1
        steps += 1
    return u, v, num, den, steps, r0                # r0 = gcd(den, N)

def formula(plan, curves):
    f = dict.fromkeys(PHASES, 0)
    for cv in curves:
        *_, steps, gcd = setup_parts(plan.N, cv["sigma"])
        f["ecm_setup"] += 10 + steps + (gcd == 1)
        if cv["end"] in ("setup factor", "degenerate"):
            continue
        f["ecm_s1"] += plan.s1
        f["ecm_gcd"] += 1
        if cv["end"] in ("s1 factor", "s1 both") or plan.B2 <= plan.B1:
            continue
        f["ecm_s2"] += plan.s2
        f["ecm_gcd"] += 1
    return f

def run_one(mod, N, g=G):
    m = Meter(CAP)
    mod.TRACE = {}
    try:
        d = mod.lamp_ecm(N, g, m)
    except Budget:
        d = None
    tr = mod.TRACE
    mod.TRACE = None
    return m, d, tr

def check(N, m, tr, plan=None):
    plan = plan or Plan(N)
    f = formula(plan, tr["curves"])
    meas = {ph: tr["ops"].get(ph, 0) for ph in PHASES}
    return f, meas, meas == f and sum(meas.values()) == m.ops

def job(args):
    kind, bits, pbits, (N, p, q) = args
    m, d, tr = run_one(ecm, N)
    f, meas, exact = check(N, m, tr)
    return dict(kind=kind, bits=bits, pbits=pbits, N=str(N), ops=m.ops, solved=d in (p, q),
                curves=len(tr["curves"]), exact=exact, measured=meas, formula=f,
                ends=[cv["end"] for cv in tr["curves"]])

# ---- group-order check ------------------------------------------------------------------

def count_points(A, p):
    """#E(F_p) for y^2 = x^3 + A x^2 + x, by summing Legendre symbols over every x."""
    x = np.arange(p, dtype=np.int64)
    f = (x * x % p * x + A * (x * x % p) + x) % p
    e, r, b = (p - 1) // 2, np.ones(p, dtype=np.int64), f.copy()
    while e:
        if e & 1:
            r = r * b % p
        b = b * b % p
        e >>= 1
    leg = np.where(f == 0, 0, np.where(r == 1, 1, -1))
    return p + 1 + int(leg.sum())

def mul_x(k, X, Z, a24, p):
    """x-only kP mod p (Montgomery ladder, no charges); returns (X : Z)."""
    def dbl(X, Z):
        t1, t2 = (X + Z) ** 2 % p, (X - Z) ** 2 % p
        t3 = t1 - t2
        return t1 * t2 % p, t3 * (t2 + a24 * t3) % p
    def add(XP, ZP, XQ, ZQ, XD, ZD):
        u, v = (XP - ZP) * (XQ + ZQ) % p, (XP + ZP) * (XQ - ZQ) % p
        return ZD * (u + v) ** 2 % p, XD * (u - v) ** 2 % p
    if k == 0:
        return (1, 0)
    R0, R1 = (X, Z), dbl(X, Z)
    for bit in bin(k)[3:]:
        if bit == "1":
            R0 = add(*R0, *R1, X, Z); R1 = dbl(*R1)
        else:
            R1 = add(*R0, *R1, X, Z); R0 = dbl(*R0)
    return R0

def factorize(n):
    out, d = [], 2
    while d * d <= n:
        while n % d == 0:
            out.append(d); n //= d
        d += 1
    if n > 1:
        out.append(n)
    return sorted(set(out))

def caught_mod(p, plan, u, v, num, den):
    """('setup' | 's1' | 's2' | None, or 'singular') for one prime factor p."""
    if den % p == 0:
        return "setup"
    a24 = num * pow(den, -1, p) % p
    if a24 in (0, 1):
        return "singular"
    A = (4 * a24 - 2) % p
    X0, Z0 = pow(u, 3, p), pow(v, 3, p)
    bad = lambda pt: pt[0] % p == 0 or pt[1] % p == 0
    pre = 1
    for qq in plan.pp:                              # stage-1 ladders: difference = the base
        base = mul_x(pre, X0, Z0, a24, p)
        if base[1] % p == 0:
            break                                   # already O: caught, consistently
        if base[0] % p == 0:
            return "x-only degenerate"
        pre *= qq
    x = X0 * pow(Z0, -1, p) % p
    rhs = (x * x * x + A * x * x + x) % p
    n = count_points(A, p)
    if rhs and pow(rhs, (p - 1) // 2, p) != 1:
        n = 2 * (p + 1) - n                         # the point lies on the twist
    order = n
    for r in factorize(n):
        while order % r == 0 and mul_x(order // r, X0, Z0, a24, p)[1] == 0:
            order //= r
    if plan.K % order == 0:
        return "s1"
    o1 = order // math.gcd(order, plan.K)           # order of the stage-1 point
    if plan.B2 <= plan.B1:
        return None
    K = plan.K                                      # stage-2 differences: Q, bQ (b odd <= 99), W, S_j
    diffs = [K] + [K * b for b in range(1, 100, 2)] + [K * W] + \
            [K * W * j for j in range(plan.j0, plan.jmax)]
    if any(bad(mul_x(k, X0, Z0, a24, p)) for k in diffs):
        return "x-only degenerate"
    if any((j * W + b) % o1 == 0 or (j * W - b) % o1 == 0 for j, b in plan.pairs):
        return "s2"
    return None

def predict(N, p, q, plan, sigma):
    u, v, num, den, steps, gcd = setup_parts(N, sigma)
    cp, cq = caught_mod(p, plan, u, v, num, den), caught_mod(q, plan, u, v, num, den)
    for skip in ("singular", "x-only degenerate"):
        if skip in (cp, cq):
            return skip
    if cp == "setup" or cq == "setup":
        return "degenerate" if cp == cq == "setup" else "setup factor"
    for st in ("s1", "s2"):
        hp, hq = cp == st, cq == st
        if hp and hq:
            return f"{st} both"
        if hp or hq:
            return f"{st} factor"
    return "none"

def order_job(args):
    bits, (N, p, q) = args
    m, d, tr = run_one(ecm, N, GO_GENES)
    plan = Plan(N, GO_GENES)
    agree = skipped = xdeg = 0
    bad = []
    for cv in tr["curves"]:
        want = predict(N, p, q, plan, cv["sigma"])
        if want == "singular":
            skipped += 1
        elif want == "x-only degenerate":
            xdeg += 1
        elif want == cv["end"]:
            agree += 1
        else:
            bad.append((cv["sigma"], want, cv["end"]))
    ends = {}
    for cv in tr["curves"]:
        ends[cv["end"]] = ends.get(cv["end"], 0) + 1
    return dict(bits=bits, N=str(N), curves=len(tr["curves"]), agree=agree, skipped=skipped,
                xdeg=xdeg, bad=bad, ends=ends, exact=check(N, m, tr, plan)[2])

# ---- mutation test ------------------------------------------------------------------------

def charge_lines():
    """Every source line of ecm.py that charges, with its one-op mutation."""
    out = []
    for line in open(ecm.__file__).read().split("\n"):
        s = line.strip()
        if 'c("ecm_' not in s and "c(ph, 1)" not in s:
            continue
        if s.startswith("c = ") or s.startswith("#"):
            continue
        if s.endswith('c("ecm_setup", steps)'):
            out.append((s, s.replace('c("ecm_setup", steps)', 'c("ecm_setup", steps + 1)')))
        else:
            k = s.rindex(", 1)")
            out.append((s, s[:k] + ", 2)" + s[k + 4:]))
    return out

def mutate_job(args):
    line, new = args
    src = open(ecm.__file__).read()
    assert src.count(line) == 1, line
    mod = types.ModuleType("ecm_mutant")
    exec(compile(src.replace(line, new), ecm.__file__, "exec"), mod.__dict__)
    caught = runs = 0
    nums = semiprimes_pq(40, 3, 2700040) + semiprimes_pq(60, 3, 2700060)
    nums += semiprimes_pq(28, 6, 3100028)                       # small: setup factors, both at once
    for N, p, q in nums:
        m, d, tr = run_one(mod, N)
        runs += 1
        caught += not check(N, m, tr)[2]
    return line, runs, caught

if __name__ == "__main__":
    if MUTATE:
        lines = charge_lines()
        with Pool(WORKERS) as pool:
            res = pool.map(mutate_job, lines)
        ok = True
        for line, runs, caught in res:
            print(f"{'caught' if caught else 'MISSED'} {caught:2d}/{runs}: {line}")
            ok &= caught > 0
        print(f"MUTATION TEST ({len(lines)} charge lines)", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    jobs = [("balanced", b, None, x) for b in BALANCED for x in semiprimes_pq(b, 40, 2700000 + b)]
    jobs += [("unbalanced", b, pb, x) for b, pb in UNBALANCED
             for x in semiprimes_unbalanced(b, pb, 40, 2800000 + 100 * pb + b)]
    ojobs = [(b, x) for b in GO_SIZES for x in semiprimes_pq(b, 150, 3100000 + b)]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=2)
        ores = pool.map(order_job, ojobs, chunksize=4)
    out = {"genes": G, "group_order_genes": GO_GENES, "cap_log2": 29, "balanced": {},
           "unbalanced": {}, "group_order": {}}
    all_ok = True
    for kind, keys in (("balanced", [(b, None) for b in BALANCED]), ("unbalanced", UNBALANCED)):
        for b, pb in keys:
            r = [x for x in res if x["kind"] == kind and x["bits"] == b and x["pbits"] == pb]
            solved, exact = sum(x["solved"] for x in r), sum(x["exact"] for x in r)
            ok = solved == len(r) == exact
            all_ok &= ok
            ends = {}
            for x in r:
                for e in x["ends"]:
                    ends[e] = ends.get(e, 0) + 1
            s = dict(n=len(r), solved=solved, exact=exact, curves=sum(x["curves"] for x in r),
                     mean_log2=math.log2(sum(x["ops"] for x in r) / len(r)), ends=ends,
                     measured={ph: sum(x["measured"][ph] for x in r) for ph in PHASES},
                     formula={ph: sum(x["formula"][ph] for x in r) for ph in PHASES}, pass_=ok)
            key = str(b) if pb is None else f"{b}/{pb}"
            out[kind][key] = s
            print(f"{kind:10s} {key:6s}: solved {solved}/{len(r)}, exact {exact}/{len(r)}, curves "
                  f"{s['curves']}, ends {ends}, mean 2^{s['mean_log2']:.2f}  {'PASS' if ok else 'FAIL'}",
                  flush=True)
    for b in GO_SIZES:
        r = [x for x in ores if x["bits"] == b]
        curves, agree = sum(x["curves"] for x in r), sum(x["agree"] for x in r)
        skipped, bad = sum(x["skipped"] for x in r), [y for x in r for y in x["bad"]]
        xdeg = sum(x["xdeg"] for x in r)
        ends = {}
        for x in r:
            for e, n in x["ends"].items():
                ends[e] = ends.get(e, 0) + n
        ok = not bad and agree + skipped + xdeg == curves and all(x["exact"] for x in r)
        all_ok &= ok
        out["group_order"][b] = dict(numbers=len(r), curves=curves, agree=agree, skipped=skipped,
                                     x_only_degenerate=xdeg, mismatches=bad[:20], ends=ends, pass_=ok)
        print(f"group order {b} bits: {len(r)} numbers, {curves} curves, prediction agrees on "
              f"{agree}, skipped: singular {skipped}, x-only degenerate {xdeg}; mismatches "
              f"{len(bad)}; ends {ends}  {'PASS' if ok else 'FAIL'}", flush=True)
        for y in bad[:5]:
            print("   MISMATCH sigma, predicted, card:", y)
    out["pass"] = all_ok
    json.dump(out, open("ecm_accept.json", "w"), indent=1)
    print("ACCEPTANCE", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)
