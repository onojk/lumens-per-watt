"""Acceptance for item 11, re-sieve's prime list by a charged linear merge (NOTES.md, "Cost model: re-sieve
prime list by a charged merge"; tests written before the code), and its report.

  1. Without re-sieve: identical to the pre-change lampcore (LAMPCORE_OLD) per number (all map numbers,
     new / frozen / corrected references).
  2. With re-sieve (p0 30 / 200 / 1000): factor, tests, hits and every type except word identical; word rises
     by sum |plist|, which from the trace is confirm_td - candidates - repeat divisions (Python), and
     Python = Rust per type, 2 numbers per size per genome.
  3. Report: before / after cost per number per pricing, re-sieve-on cells (p0 30), the three references.

  LAMPCORE_OLD=<pre-change binary> python3 merge_accept.py -> merge_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()

def refs(bits):
    return {"new ref": dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32"),
            "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

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

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = n3 = b3 = 0
    out = {}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        out[bits] = {}
        for name, g in refs(bits).items():
            a, b = run(g, nums), run(g, nums, old=True)
            n1 += len(a); b1 += sum(x != y for x, y in zip(a, b))
            for p0 in (30, 200, 1000):
                gr = dict(g, confirm="resieve", p0=p0)
                new, old = run(gr, nums), run(gr, nums, old=True)
                for x, y in zip(new, old):
                    n2 += 1
                    tx = {k: v for k, v in x[4].items() if k != "word"}
                    ty = {k: v for k, v in y[4].items() if k != "word"}
                    dw = x[4]["word"] - y[4]["word"]
                    b2 += not (x[1:4] == y[1:4] and tx == ty and dw >= 0 and x[0] - y[0] == dw)
                if p0 == 30:
                    out[bits][name] = {Pn: {"before": float(np.mean([cost(y[4], Pn) for y in old])),
                                            "after": float(np.mean([cost(x[4], Pn) for x in new]))} for Pn in ("official", "ruint", "montgomery")}
                for N, p, q in nums[::len(nums) // 2][:2]:
                    qs.TRACE = {}
                    m = lamps.Meter(P.QS_CAP)
                    try:
                        qs.lamp_qs(N, gr, m)
                    except lamps.Budget:
                        pass
                    tr = qs.TRACE; qs.TRACE = None
                    c = optypes.qs_counts(tr)
                    ncand = sum(len(at["cands"]) for at in tr["attempts"])
                    rep = sum(at["extra_div"] for at in tr["attempts"])
                    want = c["confirm_td"] - ncand - rep
                    x = run(gr, [(N, p, q)])[0]; y = run(gr, [(N, p, q)], old=True)[0]
                    py = {k: v for k, v in c.items() if v}
                    rt = {k: v for k, v in x[4].items() if v}
                    n3 += 1
                    b3 += not (x[4]["word"] - y[4]["word"] == want and py == rt and m.ops == x[0])
        for name, v in out[bits].items():
            print(f"{bits} bits, {name} + re-sieve (p0 30): cost per number before / after: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.0f} / {v[Pn]['after']:,.0f} (+{(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:.2f}%)" for Pn in v), flush=True)
    print(f"1. without re-sieve: identical to the pre-change lampcore: {n1 - b1}/{n1}")
    print(f"2. with re-sieve: only word (and ops) rise, by the same amount: {n2 - b2}/{n2}")
    print(f"3. word rise = sum |plist| (trace), Python = Rust: {n3 - b3}/{n3}")
    json.dump(out, open("merge_accept.json", "w"), indent=1)
    assert not (b1 or b2 or b3)
