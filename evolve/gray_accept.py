"""Acceptance for the Gray-code root-update re-typing (NOTES.md, "Gray-code root update re-typed to
word-level"; tests written before the code), and the formal before / after.

  1. Against the pre-change lampcore (LAMPCORE_OLD), per number on all map numbers (54-96), for the new
     reference genes, the frozen reference and the corrected reference, with and without re-sieve: total
     ops, factor and every type identical except setup_small and setup_gray, and
     old setup_small = new setup_small + new setup_gray.
  2. setup_gray = the trace's update count (sum of switches_roots), Python, 2 numbers per size per genome.
  3. Python = Rust per type, the same sample.
  4. Formal before / after (op counts unchanged; prices only): absolute cost per number per pricing with
     setup_gray priced as setup_small (before) and as word (after), on all map numbers.

  LAMPCORE_OLD=<pre-change binary> python3 gray_accept.py -> gray_accept.json, stdout
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
    return {"new ref": nr, "new ref + re-sieve": dict(nr, confirm="resieve"), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

def run(g, nums, old=False):
    b0, o0 = fastlamps.BIN, optypes.TYPE_ORDER
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
        optypes.TYPE_ORDER = [t for t in o0 if t != "setup_gray"]
    try:
        rs = run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN, optypes.TYPE_ORDER = b0, o0
    return [r[:4] + (dict(r[4], setup_gray=0),) if old else r for r in rs]

def cost(t, Pn, before):
    t = {k: v for k, v in t.items() if v}
    if Pn == "official":
        return float(sum(t.values()))
    pr = dict(PR[Pn])
    if before:
        pr["setup_gray"] = pr["setup_small"]
    return float(sum(pr[k] * v for k, v in t.items()))

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
                ta = {k: v for k, v in a[4].items() if k not in ("setup_small", "setup_gray")}
                tb = {k: v for k, v in b[4].items() if k not in ("setup_small", "setup_gray")}
                b1 += not (a[:4] == b[:4] and ta == tb and b[4]["setup_small"] == a[4]["setup_small"] + a[4]["setup_gray"])
            ba = {Pn: {"before": float(np.mean([cost(x[4], Pn, True) for x in new])),
                       "after": float(np.mean([cost(x[4], Pn, False) for x in new]))} for Pn in ("official", "ruint", "montgomery")}
            out[bits][name] = ba
            for N, p, q in nums[::len(nums) // 2][:2]:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                upd = sum(sum(a["switches_roots"]) for a in tr["attempts"])
                r = run(g, [(N, p, q)])[0]
                rt = {k: v for k, v in r[4].items() if v}
                n2 += 1
                b2 += not (py == rt and py.get("setup_gray", 0) == upd and m.ops == r[0])
            print(f"{bits} bits, {name}: cost per number before / after (cut): " + "  ".join(
                f"{Pn[:4]} {v['before']:,.0f} / {v['after']:,.0f} ({1 - v['after'] / v['before']:.3f})" for Pn, v in ba.items()), flush=True)
    print(f"1. vs pre-change lampcore: identical except setup_small -> setup_gray, which moves exactly: {n1 - b1}/{n1}")
    print(f"2-3. setup_gray = trace update count, and Python = Rust per type: {n2 - b2}/{n2}")
    json.dump(out, open("gray_accept.json", "w"), indent=1)
    assert not (b1 or b2)
