"""Acceptance for step 2, audit items 14 and 15 (NOTES.md, "Step 2: audit items 14 and 15", with its amendment;
tests written before the run), and the before / after report.

  1. Against the pre-step build (LAMPCORE_OLD), all map numbers, new reference off and on at p0 30 / 200 / 1000,
     frozen and corrected references: factor, tests, hits and every type but word identical.
  2. The word change equals the formula from the Python trace, 2 numbers per size per genome:
       per solve (rows, cw = ceil(F/64), rw = ceil(rows/64)): 2 rows cw + rows rw + pivots (cw + rw) + deps rw,
       plus per dependency tried: rows + F + its members' entries + F - 1;
       per kept candidate: s (the A-prime adds).
  3. Python = Rust per type, the same sample.
  4. Report: cost per number before / after per pricing, per size, new reference off and on at p0 200.

  LAMPCORE_OLD=<pre-step binary> python3 s2_accept.py -> s2_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes
from s1_accept import genomes, run, cost, trace

def want(tr):
    w = 0
    for at in tr["attempts"]:
        if "s1" not in at:
            continue
        w += at["s1"]["kept"] * at["s"]
        if at.get("rows"):
            F, rows = at["F"], at["rows"]
            cw, rw = -(-F // 64), -(-rows // 64)
            w += 2 * rows * cw + rows * rw + at["pivots"] * (cw + rw) + at["ndeps"] * rw
            for d in at["deps"]:
                w += rows + F + sum(len(at["rels"][i][1]) for i in d["idx"]) + F - 1
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
                b1 += not (a[1:4] == b[1:4] and ta == tb and a[0] - b[0] == a[4]["word"] - b[4]["word"])
            if name in ("new ref", "new ref + re-sieve p0 200"):
                out[bits][name] = {Pn: {"before": float(np.mean([cost(y[4], Pn) for y in old])),
                                        "after": float(np.mean([cost(x[4], Pn) for x in new]))} for Pn in ("official", "ruint", "montgomery")}
            for N, p, q in nums[::len(nums) // 2][:2]:
                tr, m = trace(N, g)
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                x = run(g, [(N, p, q)])[0]; y = run(g, [(N, p, q)], old=True)[0]
                n2 += 1
                ok = (x[4]["word"] - y[4]["word"] == want(tr) and py == {k: v for k, v in x[4].items() if v} and m.ops == x[0])
                b2 += not ok
                if not ok:
                    print(f"   MISMATCH {bits} {name}: dw {x[4]['word'] - y[4]['word']} want {want(tr)}", flush=True)
        for name, v in out[bits].items():
            print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.1f} / {v[Pn]['after']:,.1f} ({(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:+.3f}%)" for Pn in v), flush=True)
    print(f"1. only word (and ops) change, by the same amount: {n1 - b1}/{n1}")
    print(f"2-3. word change = formula (trace), Python = Rust per type: {n2 - b2}/{n2}")
    json.dump(out, open("s2_accept.json", "w"), indent=1)
    assert not (b1 or b2)
