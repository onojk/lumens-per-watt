"""Acceptance for charging ECM's modular additions at the word-level price (NOTES.md, "Cost model:
ECM modular additions"; tests written before the code).

  1. Every non-word per-type count is unchanged against the pre-change lampcore (LAMPCORE_OLD), per
     number, ECM alone at cap 2^28, on the map numbers (54-96 bits).
  2. The word count equals the formula, per number (Python trace: curves and how each ended):
     5 per curve; per curve reaching stage 1, sum over prime powers q of 4 + 10 (bit_length(q) - 1);
     per curve reaching stage 2, 4 + 6 + 50*6 + ladder(W) + ladder(j0) + 96 per giant j + 6 per
     giant step + 1 per pair (j, b) with jW +- b prime in (B1, B2]; ladder(k) = 4 + 10 (bit_length(k) - 1).
  3. Python = Rust per type (word included) on a sample.

  LAMPCORE_OLD=<old binary> python3 ecmword_accept.py -> stdout
"""
import os, sys, json, subprocess
import partition as P, sizescale2 as S2, ecm, lamps, optypes
from ledger import _primes
from fastlamps import run_many
import fastlamps

def run_with(binary, genome, nums, pre_change=False):
    """pre_change: the old binary prints the 23 types before "word"."""
    old, order = fastlamps.BIN, optypes.TYPE_ORDER
    fastlamps.BIN = binary
    if pre_change:
        optypes.TYPE_ORDER = [t for t in order if t != "word"]
    try:
        rs = run_many(genome, nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN, optypes.TYPE_ORDER = old, order
    return [r[:4] + ((dict(r[4], word=0)),) if pre_change else r for r in rs]

def lad(k):
    return 4 + 10 * (k.bit_length() - 1)

def formula(N, g, curves):
    B1, B2 = ecm.bounds(N, g)
    primes = _primes(max(B1, B2))
    s1 = 0
    for p in primes:
        if p > B1:
            break
        q = p
        while q * p <= B1:
            q *= p
        s1 += lad(q)
    W = ecm.W
    j0, jmax = max(1, B1 // W), -(-B2 // W)
    isp = set(p for p in primes if B1 < p <= B2)
    pairs = sum(1 for j in range(j0, jmax + 1) for b in ecm.BABY if (j * W + b) in isp or (j * W - b) in isp)
    s2 = 4 + 6 + 50 * 6 + lad(W) + lad(j0) + 96 * (jmax - j0 + 1) + 6 * (jmax - j0) + pairs
    w = 0
    for cv in curves:
        w += 5
        if cv["end"] in ("setup factor", "degenerate"):
            continue
        w += s1
        if cv["end"] in ("s1 factor", "s1 both") or B2 <= B1:
            continue
        w += s2
    return w

if __name__ == "__main__":
    g = dict(P.PRE["ecm"])
    bad1 = bad2 = bad3 = n1 = n2 = n3 = 0
    for bits in (54, 72, 84, 96):
        nums = S2.map_nums(bits)
        new = run_with(fastlamps.BIN, [g], nums)
        old = run_with(os.environ["LAMPCORE_OLD"], [g], nums, pre_change=True)
        for a, b in zip(new, old):
            n1 += 1
            ta = {k: v for k, v in a[4].items() if k != "word"}
            tb = {k: v for k, v in b[4].items() if k != "word"}
            bad1 += not (ta == tb and a[1] == b[1] and a[0] - a[4]["word"] == b[0])
        for t, r in list(zip(nums, new))[::20]:
            N = t[0]
            ecm.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                ecm.lamp_ecm(N, g, m)
            except lamps.Budget:
                pass
            tr = ecm.TRACE; ecm.TRACE = None
            w = tr["ops"].get("word", 0)
            n2 += 1
            bad2 += w != formula(N, g, tr["curves"])
            pt = {k: v for k, v in optypes.ecm_counts(tr, N).items() if v}
            rt = {k: v for k, v in r[4].items() if v}
            n3 += 1
            bad3 += pt != rt or m.ops != r[0]
    print(f"1. non-word types, factor and multiply-side ops unchanged vs pre-change lampcore: {n1 - bad1}/{n1}")
    print(f"2. word count = formula (Python trace): {n2 - bad2}/{n2}")
    print(f"3. Python = Rust per type (word included) and total ops: {n3 - bad3}/{n3}")
    assert not (bad1 or bad2 or bad3)
