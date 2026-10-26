"""Acceptance for item 13 (NOTES.md, "Cost models: items 12 and 13"): the on-demand selection's rest-list
building (P word ops per prefix) and its removal (1 per pick) are charged. Against the pre-change lampcore
(LAMPCORE_OLD), all map numbers: only word (and ops) rise; everything else identical; the enumerate frozen
reference is unchanged. From Python traces: the word rise = P x prefixes + picks (od_prefixes x P + od_cands);
Python = Rust per type. Report: before / after cost per number per pricing.
  LAMPCORE_OLD=<binary> python3 item13_accept.py -> item13_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0
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
            tx = {k: v for k, v in x[4].items() if k != "word"}; ty = {k: v for k, v in y[4].items() if k != "word"}
            dw = x[4]["word"] - y[4]["word"]
            ok = x[1:4] == y[1:4] and tx == ty and dw >= 0 and x[0] - y[0] == dw
            if name == "frozen ref":
                ok = ok and dw == 0
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
            want = sum(at.get("od_prefixes", 0) * at["P"] + at.get("od_cands", 0) for at in tr["attempts"] if "P" in at)
            x = run(g, [(N, p, q)])[0]; y = run(g, [(N, p, q)], old=True)[0]
            n2 += 1
            b2 += not (x[4]["word"] - y[4]["word"] == want and {k: v for k, v in optypes.qs_counts(tr).items() if v} == {k: v for k, v in x[4].items() if v} and m.ops == x[0])
        v = out[bits][name]
        print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(f"{Pn[:4]} {v[Pn]['before']:,.0f} / {v[Pn]['after']:,.0f} (+{(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:.2f}%)" for Pn in v), flush=True)
print(f"1. only word (and ops) rise; frozen (enumerate) unchanged: {n1 - b1}/{n1}")
print(f"2. word rise = P x prefixes + picks (trace), Python = Rust: {n2 - b2}/{n2}")
json.dump(out, open("item13_accept.json", "w"), indent=1)
assert not (b1 or b2)
