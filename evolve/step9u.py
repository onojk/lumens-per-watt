"""Step 9b addition (read-only): where the sieve's under-count comes from, at true fulls and true partials (new
reference, KS on, 3 map numbers per size from step 9's sample): per position, the true log2 of the smooth part split
into what the sieve adds (round(log2 p) once per odd sieved prime hit) and what it misses: (1) the prime 2's part,
(2) A's primes dividing g, (3) prime powers (exponents beyond the first) of the sieved primes, (4) rounding
(log2 p - round(log2 p), summed over the sieved primes hit).
  python3 step9u.py -> step9u.json, stdout
"""
import json, math
import numpy as np
import partition as P, qs, lamps
from ledger import Charger, Ledger
from lctest import ref, bnd
from step9 import sample
out = {}
for bits in (84, 96):
    g = ref(bits)
    qs.TRACE_ARR = True
    comp = {"full": [], "part": []}
    for N, _, _ in sample(bits)[:3]:
        qs.TRACE = {}
        qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
        tr = qs.TRACE; qs.TRACE = None
        B = bnd(N, g); L = B ** g["lc"]
        for at in tr["attempts"]:
            if "s1" not in at:
                continue
            led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None); led.build_base()
            for po in at["polys"]:
                if "A" not in po:
                    continue
                A, Bv, C, arr, M = po["A"], po["B"], po["C"], po["arr"], po["Mw"]
                aprimes = {p for p in led.base[2:] if A % p == 0}
                for i0 in range(2 * M + 1):
                    x = i0 - M
                    v = abs((A * x + 2 * Bv) * x + C)
                    if v == 0:
                        continue
                    two = apr = powr = rnd = 0.0
                    w = v
                    while w % 2 == 0:
                        w //= 2; two += 1
                    for p in led.base[2:]:
                        e = 0
                        while w % p == 0:
                            w //= p; e += 1
                        if e:
                            lp = math.log2(p)
                            if p in aprimes:
                                apr += e * lp
                            else:
                                powr += (e - 1) * lp
                                rnd += lp - max(1, round(lp))
                    cls = "full" if w == 1 else ("part" if w < L else None)
                    if cls:
                        comp[cls].append((two, apr, powr, rnd, two + apr + powr + rnd))
    qs.TRACE_ARR = False
    out[bits] = {}
    for cls, rows in comp.items():
        a = np.array(rows)
        out[bits][cls] = {"n": len(rows), **{nm: {"mean": float(a[:, i].mean()), "median": float(np.median(a[:, i]))}
                                            for i, nm in enumerate(("two", "a_primes", "powers", "rounding", "total"))}}
        o = out[bits][cls]
        print(f"{bits} bits, true {cls} (n {o['n']}): under-count mean / median, bits: prime 2 {o['two']['mean']:.2f} / {o['two']['median']:.2f}; "
              f"A-primes {o['a_primes']['mean']:.2f} / {o['a_primes']['median']:.2f}; prime powers {o['powers']['mean']:.2f} / {o['powers']['median']:.2f}; "
              f"rounding {o['rounding']['mean']:+.2f} / {o['rounding']['median']:+.2f}; total {o['total']['mean']:.2f} / {o['total']['median']:.2f}", flush=True)
json.dump(out, open("step9u.json", "w"), indent=1)
