"""Information only (user, Oct 25; no card change): from qs traces, per size (new reference genes, qs alone,
corrected card, kset; 3 balanced map numbers per size):
  (a) the distribution of filed large primes q relative to B: log_B q for every partial filed (1 < q < B^lc);
  (b) candidates whose cofactor after trial division is composite with both prime factors in (B, B^lc),
      i.e. in [B^2, B^(2 lc)] and qualifying as two-large-prime relations (sympy, harness only).
Candidates are those that passed the card's current threshold, so (b) is a floor: a 2LP card would loosen it.
  python3 lpdist.py -> lpdist.out (stdout)
"""
import json, math
import numpy as np
import sympy
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
from ledger import Charger, Ledger
sealed = json.load(open("sizescale_k_sealed.json"))
for bits in (54, 72, 84, 96):
    g0 = sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]
    g = dict(SS.qsg(g0), kset="sf32")
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3]
    lc = g0["lc"]
    logq, n_cand, n_2lp, n_2lp_any, n_part, n_full = [], 0, 0, 0, 0, 0
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        lnN = math.log(N); B = max(30, int(g0["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
        L = B ** lc
        for at in tr["attempts"]:
            led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
            led.build_base()
            for v in at["cands"]:
                v = abs(v)
                if v == 0:
                    continue
                n_cand += 1
                for p in led.base[1:]:
                    while v % p == 0:
                        v //= p
                if v == 1:
                    n_full += 1
                elif v < L:
                    n_part += 1
                    logq.append(math.log(v) / math.log(B))
                elif B * B <= v <= B ** (2 * lc) and not sympy.isprime(v):
                    f = sympy.factorint(v)
                    ps = [p for p, e in f.items() for _ in range(e)]
                    n_2lp_any += 1
                    if len(ps) == 2 and all(B < p < L for p in ps):
                        n_2lp += 1
    lq = np.array(logq)
    hist = np.histogram(lq, bins=[1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5])[0] / max(1, len(lq))
    print(f"{bits} bits (lc {lc:.3f}): candidates {n_cand / 3:.0f} per number; full {n_full / 3:.0f}, partials filed {n_part / 3:.0f}; "
          f"log_B q of partials: median {np.median(lq):.3f}, mean {lq.mean():.3f}; share in [1,1.2) [1.2,1.4) [1.4,1.6) [1.6,1.8) [1.8,2) [2,2.5): "
          + " ".join(f"{h:.2f}" for h in hist), flush=True)
    print(f"   2LP-qualifying cofactors (two primes in (B, B^lc)): {n_2lp / 3:.1f} per number = {n_2lp / max(1, n_part):.3f} per partial; "
          f"composite cofactors in [B^2, B^(2lc)] of any shape {n_2lp_any / 3:.1f} per number", flush=True)
