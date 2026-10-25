"""Outside check (information only, not the meter): textbook pipeline model for a p-1 stage.
Official pricing (every op = 1). 84-bit N, smaller factor p in bands 16..42 bits, equally likely.
Pipeline: rho (budget r) -> p-1 stage 1 bound B (cost ceil(log2 lcm(1..B))) -> ECM (budget e,
stage-1 model: group order 12m, m B1-powersmooth, 11 ops per bit of lcm(1..B1)) -> qs cost Q.
rho catch: Rayleigh law on tail+cycle, Brent detection 1.57x, 1.56 ops per Brent step.
Part 1: rho 5793 and ECM 32768 fixed (rates given), p-1 bound swept.
Part 2: rho, B, ECM, B1 jointly optimized. Known failure: never reproduces allocation A.
(Written and first run by the user in their own workspace; saved here verbatim, Oct 25.)"""
import math, random
import numpy as np
from sympy import factorint, randprime, primerange
random.seed(2026)
BANDS = [16, 20, 24, 28, 32, 36, 42]
N = 1000
def lcmbits(b):
    return math.ceil(sum(math.floor(math.log(b) / math.log(p) + 1e-12) * math.log2(p) for p in primerange(2, b + 1)))
def rhoc(r, k):
    if r == 0: return 0.0
    ps = np.exp(np.linspace(math.log(2 ** (k - 1)), math.log(2 ** k), 400)); w = ps / np.log(ps)
    t = r / (1.56 * 1.57); return float(((1 - np.exp(-t * t / (2 * ps))) * w).sum() / w.sum())
psm = lambda f, b: all(p ** e <= b for p, e in f.items())
PF = [[factorint(randprime(2 ** (k - 1), 2 ** k) - 1) for _ in range(N)] for k in BANDS]
MF = [[factorint(random.randint(2 ** (k - 1) // 12 + 1, 2 ** k // 12)) for _ in range(N)] for k in BANDS]
_c = {}
def rate(F, b, key):
    if (key, b) not in _c: _c[(key, b)] = [sum(psm(f, b) for f in F[i]) / N for i in range(7)]
    return _c[(key, b)]
_lb = {}
def lb(b):
    if b not in _lb: _lb[b] = lcmbits(b)
    return _lb[b]
RHO_FIXED = [1.00, 0.97, 0.21, 0.014, 0.001, 0, 0]
ECM_FIXED = [0.88, 0.88, 0.56, 0.22, 0.12, 0.04, 0.01]
def cost_fixed(Q, B):
    tot = 0
    for i in range(7):
        al = 1 - RHO_FIXED[i]; c = RHO_FIXED[i] * 5793 / 2 + al * 5793
        if B: c += al * lb(B); al *= 1 - rate(PF, B, "p")[i]
        e = ECM_FIXED[i]; c += al * (e * 32768 / 2 + (1 - e) * 32768); al *= 1 - e
        tot += c + al * Q
    return tot / 7
print("Part 1: rho 5793, ECM 32768 fixed; cost with p-1 / cost without")
for Q in (300000, 550000, 1000000):
    base = cost_fixed(Q, 0)
    print(f" qs={Q}: " + "  ".join(f"2^{e}:{cost_fixed(Q, 2 ** e) / base:.3f}" for e in range(8, 17)))
rs = [0] + [round(2 ** x) for x in np.arange(10, 15.01, 0.5)]
bs = [0] + [2 ** x for x in range(8, 17)]
es = [0] + [round(2 ** x) for x in np.arange(12, 18.01, 0.5)]
b1s = [100, 200, 400, 800, 1600]
RC = {(r, i): rhoc(r, BANDS[i]) for r in rs for i in range(7)}
def cost_joint(Q, r, B, e, b1):
    tot = 0
    for i in range(7):
        pr = RC[(r, i)]; c = (pr * r / 2 + (1 - pr) * r) if r else 0; al = 1 - pr
        if B: c += al * lb(B); al *= 1 - rate(PF, B, "p")[i]
        if e:
            pe = 1 - (1 - rate(MF, b1, "m")[i]) ** (e // (11 * lb(b1)))
            c += al * (pe * e / 2 + (1 - pe) * e); al *= 1 - pe
        tot += c + al * Q
    return tot / 7
print("Part 2: joint optimum (rho, B, ECM, B1); cost / qs alone")
for Q in (100000, 300000, 550000, 1000000):
    for use in (False, True):
        b = min((cost_joint(Q, r, B, e, b1), r, B, e, b1) for r in rs for B in (bs if use else [0]) for e in es for b1 in b1s)
        print(f" qs={Q} {'p-1' if use else 'no p-1'}: {b[0] / Q:.3f}  rho {b[1]}  B {b[2]}  ECM {b[3]}  B1 {b[4]}")
