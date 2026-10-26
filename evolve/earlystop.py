"""Information only (user, Oct 25; no card change): at the qs card's stop (F + DELTA relations, DELTA =
10), F, the active primes (odd exponent in >= 1 and in >= 2 relations), the GF(2) rank and null-space
dimension; and, replaying the relations in arrival order, the earliest point with >= 5 and >= 10
dependencies, how many relations before F + 10 that is, and the share of the run's sieve ops spent
after it. Final Track R genes (the new reference) as qs alone, corrected card with kset sf32, on
balanced map numbers. Instrumentation wraps Ledger.add to note the sieve ops at each kept relation;
nothing is charged differently.
  python3 earlystop.py -> earlystop.out (stdout)
"""
import json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps, ledger

sealed = json.load(open("sizescale_k_sealed.json"))
marks = []
_orig_add = ledger.Ledger.add
def add(self, u, vec, y=1, check=False):
    n0 = len(self.rels)
    r = _orig_add(self, u, vec, y, check)
    if len(self.rels) > n0 and self.at is not None:
        marks.append((id(self), qs.TRACE["ops"].get("sieve", 0)))
    return r
ledger.Ledger.add = add

def rank_curve(masks):
    basis = {}
    out = []
    r = 0
    for m in masks:
        while m:
            h = m.bit_length() - 1
            if h in basis:
                m ^= basis[h]
            else:
                basis[h] = m; r += 1
                break
        out.append(r)
    return out

for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    rows = SS.corrected_map_rows(bits)
    nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:4]
    for N, _, _ in sample:
        marks.clear()
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        at = tr["attempts"][-1]
        rels = at["rels"]
        F = at["F"] if "F" in at else len(rels) - 10
        led_marks = [s for lid, s in marks][-len(rels):]
        masks = [sum(1 << j for j, e in vec if e & 1) for _, vec, _ in rels]   # sparse relations (step 1)
        rk = rank_curve(masks)
        n = len(rels)
        cnt = np.zeros(max(F, 1), dtype=int)
        for _, vec, _ in rels:
            for j, e in vec:
                if e & 1:
                    cnt[j] += 1
        act1, act2 = int((cnt >= 1).sum()), int((cnt >= 2).sum())
        null = [i + 1 - rk[i] for i in range(n)]
        sieve_total = tr["ops"].get("sieve", 0)
        line = f"{bits} bits N {N}: F {len(rels[0][1])}, relations {n}, active primes >=1 {act1}, >=2 {act2}, rank {rk[-1]}, null {null[-1]}"
        for want in (5, 10):
            i = next((i for i in range(n) if null[i] >= want), None)
            if i is None:
                line += f"; >= {want} deps: not reached"
            else:
                after = sieve_total - led_marks[i] if i < len(led_marks) else 0
                line += f"; >= {want} deps at relation {i + 1} ({n - (i + 1)} before the stop; sieve ops after it {after / sieve_total:.3f})"
        print(line, flush=True)
