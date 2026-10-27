"""Acceptance for stage H's option on (NOTES.md, "Stage H: sieve 2 and small prime powers", 3caf8df). The option
off is checked by gray_a_accept.py against the pre-change lampcore.

  1. Python = Rust per type and in total ops, 2 numbers per size (54-96), for: the new reference + pp 10, + pp 10
     with re-sieve, + pp 6, + pp 3 ("2 free"), + pp 12, the corrected reference + pp 10.
  2. The sieve value is exact (Python traces, qs.TRACE_ARR; 2 numbers at 54 and 72, every polynomial): at every
     position, arr[x] + w2 (on the parity class) equals the sum over the base of round(log2 p) x the valuation
     capped as designed: for odd p with two roots, not dividing A, min(v_p, e_max) with p^e_max < 2^pp the largest
     power; for p | k, min(v_p, 1); for A's primes 0; for 2, v2 when kN = 3 mod 4 or 5 mod 8 or kN even, and
     min(v2, max(3, pp - 1)) when kN = 1 mod 8 (pp <= 4: the parity add's 3 alone).
  python3 pp_accept.py -> stdout
"""
import json, math
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
from fastlamps import run_many
from ledger import Charger, Ledger
from lctest import bnd

sealed = json.load(open("sizescale_k_sealed.json"))

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    return {"new ref pp 10": dict(nr, pp=10), "new ref pp 10 + re-sieve": dict(nr, pp=10, confirm="resieve"),
            "new ref pp 6": dict(nr, pp=6), "new ref pp 3 (2 free)": dict(nr, pp=3), "new ref pp 12": dict(nr, pp=12), "corrected ref pp 10": dict(SS.OLD, pp=10)}

def val(v, p):
    e = 0
    while v % p == 0:
        v //= p; e += 1
    return e

def exact_check(bits, N, g):
    qs.TRACE_ARR = True
    qs.TRACE = {}
    qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    tr = qs.TRACE; qs.TRACE = None; qs.TRACE_ARR = False
    B = bnd(N, g); pp = g["pp"]
    npos = bad = 0
    for at in tr["attempts"]:
        if "s1" not in at:
            continue
        k = at["k"]; kN = k * N
        led = Ledger(N, k, B, Charger(lamps.Meter(1 << 60), None), None); led.build_base()
        logp = {p: max(1, round(math.log2(p))) for p in led.base[2:]}
        for po in at["polys"]:
            if "A" not in po:
                continue
            A, Bv, C, arr, M, par, w2 = po["A"], po["B"], po["C"], po["arr"], po["Mw"], po["par"], po["w2"]
            for i0 in range(2 * M + 1):
                x = i0 - M
                v = abs((A * x + 2 * Bv) * x + C)
                if v == 0:
                    continue
                want = 0
                for p in led.base[2:]:
                    if A % p == 0:
                        continue
                    e = val(v, p)
                    if not e:
                        continue
                    if k % p == 0:
                        cap = 1
                    else:
                        cap = 1
                        while p ** (cap + 1) < 1 << pp:
                            cap += 1
                    want += logp[p] * min(e, cap)
                e2 = val(v, 2)
                want += min(e2, max(3, pp - 1)) if kN % 8 == 1 else e2
                got = int(arr[i0]) + (w2 if i0 % 2 == par else 0)
                npos += 1
                bad += got != want
    return npos, bad

if __name__ == "__main__":
    n1 = b1 = 0
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        for name, g in genomes(bits).items():
            for N, p, q in nums[::len(nums) // 2][:2]:
                m = lamps.Meter(P.QS_CAP)
                qs.TRACE = {}
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                r = run_many([g], [(N, p, q)], P.QS_CAP, types=True)[0]
                n1 += 1
                ok = py == {k: v for k, v in r[4].items() if v} and m.ops == r[0]
                b1 += not ok
                if not ok:
                    print("  mismatch", bits, name, N, flush=True)
        print(f"{bits} bits done", flush=True)
    print(f"1. Python = Rust per type, option on: {n1 - b1}/{n1}", flush=True)
    tot = tb = 0
    for bits in (54, 72):
        nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
        for N, _, _ in S2.map_nums(bits)[:2]:
            for ppv in (10, 6, 3):
                n, b = exact_check(bits, N, dict(nr, pp=ppv))
                tot += n; tb += b
    print(f"2. sieve value exact at every position: {tot - tb}/{tot}")
    assert not (b1 or tb)
