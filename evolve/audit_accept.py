"""Acceptance for the audit re-typing, items 0-8 (NOTES.md, "Audit re-typing, items 0-8: cost model";
tests written before the code), and its report. A pricing correction: op counts unchanged.

  1. Against the pre-change lampcore (LAMPCORE_OLD), all map numbers, new reference (with and without
     re-sieve), corrected and frozen references: total ops, factor, tests and hits identical; the types the
     re-typing does not touch (fb, setup_euclid, sieve_update, sieve_scan, la, sqrt_mul, sqrt_gcd, lp_full,
     check, setup_gray) identical; setup_full and confirm_full now zero; the sum over types equal to ops.
  2. Python = Rust per type, 2 numbers per size per genome.
  3. Report: cost per number per pricing, absolute, before / after, with bases stated.

  LAMPCORE_OLD=<pre-change binary> python3 audit_accept.py -> audit_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
NEW = ["hash", "sort_cmp", "f64_log", "f64_div"]
FIXED = ["fb", "setup_euclid", "sieve_update", "sieve_scan", "la", "sqrt_mul", "sqrt_gcd", "lp_full", "check", "setup_gray"]
def run(g, nums, old=False):
    b0, o0 = fastlamps.BIN, optypes.TYPE_ORDER
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
        optypes.TYPE_ORDER = [t for t in o0 if t not in NEW]
    try:
        rs = run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN, optypes.TYPE_ORDER = b0, o0
    return [r[:4] + (dict(r[4], **{t: 0 for t in NEW}),) for r in rs] if old else rs
def cost(t, Pn):
    t = {k: v for k, v in t.items() if v}
    return float(sum(t.values())) if Pn == "official" else float(sum(PR[Pn][k] * v for k, v in t.items()))
n1 = b1 = n2 = b2 = 0
out = {}
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    out[bits] = {}
    for name, g in (("new ref", nr), ("new ref + re-sieve", dict(nr, confirm="resieve")), ("corrected ref", SS.OLD), ("frozen ref", SS.FROZEN_REF)):
        a, b = run(g, nums), run(g, nums, old=True)
        for x, y in zip(a, b):
            n1 += 1
            ok = (x[:4] == y[:4] and all(x[4][t] == y[4][t] for t in FIXED) and x[4]["setup_full"] == 0 and x[4]["confirm_full"] == 0
                  and sum(x[4].values()) == x[0] and sum(y[4].values()) == y[0])
            b1 += not ok
        out[bits][name] = {Pn: {"before": float(np.mean([cost(y[4], Pn) for y in b])), "after": float(np.mean([cost(x[4], Pn) for x in a]))} for Pn in ("official", "ruint", "montgomery")}
        for N, p, q in nums[::len(nums) // 2][:2]:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                qs.lamp_qs(N, g, m)
            except lamps.Budget:
                pass
            tr = qs.TRACE; qs.TRACE = None
            r = run(g, [(N, p, q)])[0]
            n2 += 1
            b2 += not ({k: v for k, v in optypes.qs_counts(tr).items() if v} == {k: v for k, v in r[4].items() if v} and m.ops == r[0])
        v = out[bits][name]
        print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(f"{Pn[:4]} {v[Pn]['before']:,.0f} / {v[Pn]['after']:,.0f} ({(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:+.2f}%)" for Pn in v), flush=True)
print(f"1. ops, factor, tests, hits and the untouched types identical; setup_full and confirm_full zero: {n1 - b1}/{n1}")
print(f"2. Python = Rust per type: {n2 - b2}/{n2}")
json.dump(out, open("audit_accept.json", "w"), indent=1)
assert not (b1 or b2)
