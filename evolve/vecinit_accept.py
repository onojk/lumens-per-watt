"""Acceptance for the exponent-vector zero-fill and re-sieve's per-polynomial initialization charges (NOTES.md,
"Meter correction: exponent-vector and per-polynomial initializations", as corrected and accepted; tests
written before the code), and the before / after report.

  1. Against the build before this change (LAMPCORE_OLD), all map numbers, new reference (re-sieve off; on at p0
     30 / 200 / 1000), frozen and corrected references: factor, tests, hits and every type except word identical;
     word rises (and ops by the same amount).
  2. The word rise equals the formula from the Python trace, 2 numbers per size per genome:
     F x candidates processed, plus with re-sieve, per polynomial width + 2F - 1 + |st| + |cand| (the trace's
     per-polynomial candidate count: a ledger that fills mid-polynomial leaves some candidates unprocessed).
  3. Python = Rust per type, the same sample.
  4. Report: cost per number before / after per pricing, per size, for the new reference with and without re-sieve.

  LAMPCORE_OLD=<pre-change binary> python3 vecinit_accept.py -> vecinit_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    out = {"new ref": nr}
    for p0 in (30, 200, 1000):
        out[f"new ref + re-sieve p0 {p0}"] = dict(nr, confirm="resieve", p0=p0)
    out["frozen ref"] = SS.FROZEN_REF
    out["corrected ref"] = SS.OLD
    return out

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

def want(tr, rs):
    w = 0
    for at in tr["attempts"]:
        F, nc = at["F"], len(at["cands"])
        w += F * nc
        if rs:
            w += sum(2 * p["M"] + 1 + 2 * F - 1 + len(p["sieved"]) + p["nc"] for p in at["polys"])
    return w

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = 0
    out = {}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        out[bits] = {}
        for name, g in genomes(bits).items():
            new, old = run(g, nums), run(g, nums, old=True)
            for a, b in zip(new, old):
                n1 += 1
                ta = {k: v for k, v in a[4].items() if k != "word"}
                tb = {k: v for k, v in b[4].items() if k != "word"}
                dw = a[4]["word"] - b[4]["word"]
                b1 += not (a[1:4] == b[1:4] and ta == tb and dw >= 0 and a[0] - b[0] == dw)
            if name in ("new ref", "new ref + re-sieve p0 200"):
                out[bits][name] = {Pn: {"before": float(np.mean([cost(y[4], Pn) for y in old])),
                                        "after": float(np.mean([cost(x[4], Pn) for x in new]))} for Pn in ("official", "ruint", "montgomery")}
            for N, p, q in nums[::len(nums) // 2][:2]:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                x = run(g, [(N, p, q)])[0]; y = run(g, [(N, p, q)], old=True)[0]
                n2 += 1
                b2 += not (x[4]["word"] - y[4]["word"] == want(tr, g.get("confirm") == "resieve")
                           and py == {k: v for k, v in x[4].items() if v} and m.ops == x[0])
        for name, v in out[bits].items():
            print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.0f} / {v[Pn]['after']:,.0f} (+{(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:.2f}%)" for Pn in v), flush=True)
    print(f"1. only word (and ops) rise, by the same amount: {n1 - b1}/{n1}")
    print(f"2-3. word rise = formula (trace), Python = Rust per type: {n2 - b2}/{n2}")
    json.dump(out, open("vecinit_accept.json", "w"), indent=1)
    assert not (b1 or b2)
