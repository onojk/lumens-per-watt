"""Why is map(c = 2, d = 2, x0 = 5) + Brent(512) dearer than rho on the Fermat-easy subset (1.09-1.84 x in G-37's
table, 6c6edfc)? The user's request, Oct 30: exploratory, untimed, not scored, no deck, not in any sealed run; plain
Python with counters, no op meter (each run's op total is checked against lampcore's metered count, so the counters
describe the metered runs exactly).

The hypothesis and prediction (the user's, written before this ran): close p and q make both cycles close in the
same batch, so the batch gcd is N and Brent backtracks. Prediction: more gcd = N events on the easy subset,
shrinking as b drops.

Numbers: the held-out 48-bit balanced validation numbers, semiprimes_pq(48, 48, 9930048) (the set G-37 used; scoring
is done, 6c6edfc). Fermat-easy = Fermat steps <= sqrt(p) (explore/close_factors.py's count).
Runs: map(c = 2, d = 2, x0 = 5) + Brent(b) for b = 512, 64, 16, 1; and rho's genes, map(c = 1, d = 2, x0 = 2) +
Brent(64) (= lampcore rho), for reference. Per number: the batch gcds that returned N (0 or 1: Brent stops at the
first gcd != 1), the backtrack's map steps and gcds, the op-class cost (mul 554.9 per map step and per batched
product, gcd 1,401.7: arr's charges, NOTES "Cost model: the arrangement lamp") and the share of it spent in the
backtrack. Per subset (easy, rest): means, and the cost against rho's on the same numbers.
  python3 brent_backtrack.py > brent_backtrack.out"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evolve"))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evolve"))
from fastlamps import semiprimes_pq
import arr_price as AP

MUL, GCD = AP.V1["mul"], AP.V1["gcd"]                    # op-class v1, exact (rounded: 554.9, 1,401.7)

def brent(N, c, x0, b):
    """arr.py's Brent rule on the d = 2 map, with counters (the same steps and gcds, in the same order)."""
    f = lambda v: (v * v + c) % N
    st = {"steps": 0, "prods": 0, "gcds": 0, "gcdN": 0, "bt_steps": 0, "bt_gcds": 0}
    y, r, q, G = x0 % N, 1, 1, 1
    while True:
        x = y
        for _ in range(r):
            y = f(y); st["steps"] += 1
        k = 0
        while k < r and G == 1:
            ys = y
            for _ in range(min(b, r - k)):
                y = f(y); st["steps"] += 1; st["prods"] += 1
                q = q * abs(x - y) % N
            G = math.gcd(q, N); st["gcds"] += 1
            k += b
        r *= 2
        if G != 1:
            break
    if G == N:
        st["gcdN"] += 1
        while True:
            ys = f(ys); st["bt_steps"] += 1
            G = math.gcd(abs(x - ys), N); st["bt_gcds"] += 1
            if G > 1:
                break
    st["ok"] = 1 < G < N
    st["cost"] = MUL * (st["steps"] + st["prods"] + st["bt_steps"]) + GCD * (st["gcds"] + st["bt_gcds"])
    st["bt_cost"] = MUL * st["bt_steps"] + GCD * st["bt_gcds"]
    return st

def fermat_easy(N, p, q):
    r = math.isqrt(N)
    c = r if r * r == N else r + 1
    return (p + q) // 2 - c + 1 <= math.isqrt(p)

nums = semiprimes_pq(48, 48, 9930048)
easy = [fermat_easy(*x) for x in nums]
ARMS = [("rho genes: map(1, 2, 2) + Brent(64)", 1, 2, 64)] + [(f"map(2, 2, 5) + Brent({b})", 2, 5, b) for b in (512, 64, 16, 1)]
res = {}
for name, c, x0, b in ARMS:
    rs = [brent(N, c, x0, b) for N, _, _ in nums]
    g = [{"t": "arr", "layout": {"kind": "map", "c": c, "d": 2, "x0": x0}, "detect": {"kind": "brent", "b": b}}]
    metered = AP.run(g, AP.CAP, nums, 48)
    bad = [i for i, (u, m) in enumerate(zip(rs, metered)) if abs(u["cost"] - m["cost"]["opclass_v1"]) > 1e-6 * m["cost"]["opclass_v1"]]
    res[name] = rs
    print(f"{name}: parity with lampcore's metered op-class cost: {48 - len(bad)}/48" + (f" (mismatch at {bad[:3]})" if bad else ""))
rho = res[ARMS[0][0]]
print(f"\nheld-out 48-bit numbers: {sum(easy)} Fermat-easy of {len(easy)}")
for name, *_ in ARMS:
    rs = res[name]
    print(f"\n{name}")
    for label, m in (("easy", easy), ("rest", [not e for e in easy])):
        sub = [r for r, k in zip(rs, m) if k]
        rsub = [r for r, k in zip(rho, m) if k]
        mean = lambda xs, key: sum(x[key] for x in xs) / len(xs)
        print(f"  {label:4s} (n = {len(sub):2d}): gcd = N events {sum(r['gcdN'] for r in sub)} ({mean(sub, 'gcdN'):.3f} per number); "
              f"backtrack ops per number {mean(sub, 'bt_steps') + mean(sub, 'bt_gcds'):,.1f} (steps {mean(sub, 'bt_steps'):,.1f}, "
              f"gcds {mean(sub, 'bt_gcds'):,.1f}); backtrack share of cost {sum(r['bt_cost'] for r in sub) / sum(r['cost'] for r in sub):.3f}; "
              f"mean op-class cost {mean(sub, 'cost'):,.0f} = {mean(sub, 'cost') / mean(rsub, 'cost'):.3f} x rho's; "
              f"map steps per number {mean(sub, 'steps'):,.0f} (rho {mean(rsub, 'steps'):,.0f})")
print("\nper easy number, map(2, 2, 5) + Brent(512) against rho's genes (map steps, gcd = N, backtrack ops, cost ratio):")
for i, (k, (N, p, q)) in enumerate(zip(easy, nums)):
    if k:
        a, r = res[ARMS[1][0]][i], rho[i]
        print(f"  #{i:2d} p {p} q {q}: steps {a['steps']:,} vs {r['steps']:,}; gcd = N {a['gcdN']} vs {r['gcdN']}; backtrack ops "
              f"{a['bt_steps'] + a['bt_gcds']:,} vs {r['bt_steps'] + r['bt_gcds']:,}; cost ratio {a['cost'] / r['cost']:.3f}")
