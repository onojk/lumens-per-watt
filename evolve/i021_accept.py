"""Acceptance for I-021, KS scoring by multiplicativity of the Legendre symbol (NOTES.md, "I-021 adopted";
tests written before the Rust code).

  1. Scores bit-identical (Python, ks_eval against the old ks_score) on all map numbers: k in 1..64 (qs's sf32 and
     1..kc lists, cfrac's 1..kc) and sq-style k = mult * j, j <= 200, mult in the deck's {1, 2, 6, 12, 30, 60, 120, 480}.
  2. qs against the pre-change lampcore (LAMPCORE_OLD), all map numbers, new reference (with and without re-sieve),
     frozen and corrected references, and kc 32 without kset: factor, tests, hits and every type except mult,
     word and f64_log identical (so the same rankings); the three changes equal the formula from lamps.ks_rank.
  3. cfrac (kc 16 and 48) on the 54-72 map numbers: same factor, tests and hits; cfrac_ops changes by the formula.
  4. sq "ks" mode on 40-56-bit semiprimes: same factor and k; Python = Rust ops (parity covers it in full).
  5. Python = Rust per type for qs, 2 numbers per size per genome.

  LAMPCORE_OLD=<pre-change binary> python3 i021_accept.py -> stdout
"""
import os, json, random
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
NK = len(lamps.KS_PRIMES)

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    kc = {k: v for k, v in nr.items() if k != "kset"}
    return {"new ref": nr, "new ref + re-sieve": dict(nr, confirm="resieve"), "frozen ref": SS.FROZEN_REF,
            "corrected ref": SS.OLD, "new ref, kc 32": dict(kc, kc=32)}

def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many(g if isinstance(g, list) else [g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0

def cands(g):
    return qs.SF32 if g.get("kset") == "sf32" else list(range(1, max(1, int(g.get("kc", 16))) + 1))

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = n3 = b3 = n4 = b4 = n5 = b5 = 0
    allnums = {bits: S2.map_nums(bits) for bits in SS.SIZES}
    for bits, nums in allnums.items():
        for N, _, _ in nums:
            legn = lamps.ks_prep(N)
            for k in list(range(1, 65)) + [mu * j for mu in (1, 2, 6, 12, 30, 60, 120, 480) for j in range(1, 201)]:
                n1 += 1
                b1 += lamps.ks_eval(k, N, legn)[0] != lamps.ks_score(k, N)
    print(f"1. scores bit-identical: {n1 - b1}/{n1}", flush=True)
    for bits, nums in allnums.items():
        for name, g in genomes(bits).items():
            new, old = run(g, nums), run(g, nums, old=True)
            for (N, p, q), a, b in zip(nums, new, old):
                n2 += 1
                ta = {k: v for k, v in a[4].items() if k not in ("mult", "word", "f64_log")}
                tb = {k: v for k, v in b[4].items() if k not in ("mult", "word", "f64_log")}
                cs = cands(g)
                _, (mu, wo, fl) = lamps.ks_rank(N, cs)
                ok = (a[1:4] == b[1:4] and ta == tb and a[4]["mult"] == b[4]["mult"] - NK * len(cs) + mu
                      and a[4]["word"] == b[4]["word"] + wo and a[4]["f64_log"] == b[4]["f64_log"] + fl
                      and a[0] - b[0] == mu + wo + fl - NK * len(cs))
                b2 += not ok
            for N, p, q in nums[::len(nums) // 2][:2]:
                m = lamps.Meter(P.QS_CAP)
                qs.TRACE = {}
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                r = run(g, [(N, p, q)])[0]
                n5 += 1
                b5 += not (py == {k: v for k, v in r[4].items() if v} and m.ops == r[0])
        print(f"{bits} bits: qs done", flush=True)
    print(f"2. qs vs pre-change lampcore: only mult / word / f64_log change, by the formula: {n2 - b2}/{n2}")
    for bits in (54, 72):
        for kc in (16, 48):
            g = {"t": "cfrac", "kc": kc, "bc": 1.5}
            nums = allnums[bits][:40]
            for (N, p, q), a, b in zip(nums, run(g, nums), run(g, nums, old=True)):
                _, (mu, wo, fl) = lamps.ks_rank(N, range(1, kc + 1))
                n3 += 1
                b3 += not (a[1:4] == b[1:4] and a[4]["cfrac_ops"] - b[4]["cfrac_ops"] == mu + wo + fl - NK * kc)
    print(f"3. cfrac: same results, cfrac_ops by the formula: {n3 - b3}/{n3}")
    rng = random.Random(2026)
    for bits in (40, 48, 56):
        nums = fastlamps.semiprimes_pq(bits, 20, rng.randrange(1 << 30))
        for mult in (1, 6, 60):
            g = {"t": "sq", "mode": "ks", "mult": mult, "k": 0.3, "w": 0.1, "c": 1.0, "ksq": True, "r": 16}
            new, old = run(g, nums), run(g, nums, old=True)
            for (N, p, q), a, b in zip(nums, new, old):
                ops, d = lamps.run([g], N, P.QS_CAP)
                n4 += 1
                b4 += not (a[1] == b[1] and a[0] == ops)
    print(f"4. sq ks: same factor as before, Python = Rust ops: {n4 - b4}/{n4}")
    print(f"5. Python = Rust per type (qs): {n5 - b5}/{n5}")
    assert not (b1 or b2 or b3 or b4 or b5)
