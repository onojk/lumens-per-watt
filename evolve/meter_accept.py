"""Acceptance for the meter correction charging the ledger's duplicate check and the sq card's tried-multiplier
set (NOTES.md, "Meter correction: the ledger's duplicate check"; tests written before the code), and the report.

  1. qs, all map numbers (54-96), new reference (with and without re-sieve), frozen and corrected references,
     against the pre-change lampcore (LAMPCORE_OLD): factor, tests and hits identical; every type except
     word identical; ops and word both rise by the same amount (zero when no relation reaches the ledger).
  2. That amount = 2 x (full relations offered) + 3 x (combined relations offered), from Python traces
     (smooth candidates; lp combinations), and Python = Rust per type, on 2 numbers per size per genome.
  3. cfrac and sq: same factor as before and ops rise (their types are single lumps); exact parity is in parity.py.
  4. Report: before / after cost per number per pricing (absolute), per size, for the three references.

  LAMPCORE_OLD=<pre-change binary> python3 meter_accept.py -> meter_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many
from ledger import Charger, Ledger

sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    return {"new ref": nr, "new ref + re-sieve": dict(nr, confirm="resieve"), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

def run(g, nums, old=False, cap=P.QS_CAP):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many(g if isinstance(g, list) else [g], nums, cap, types=True)
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
        for name, g in genomes(bits).items():
            new, old = run(g, nums), run(g, nums, old=True)
            for a, b in zip(new, old):
                n1 += 1
                ta = {k: v for k, v in a[4].items() if k != "word"}
                tb = {k: v for k, v in b[4].items() if k != "word"}
                dw = a[4]["word"] - b[4]["word"]
                b1 += not (a[1:4] == b[1:4] and ta == tb and dw >= 0 and a[0] - b[0] == dw)   # dw = 0 when qs finds the factor before any relation (e.g. N mod q)
            if name != "new ref + re-sieve":
                out[bits][name] = {Pn: {"before": float(np.mean([cost(x[4], Pn) for x in old])),
                                        "after": float(np.mean([cost(x[4], Pn) for x in new]))} for Pn in ("official", "ruint", "montgomery")}
                out[bits][name]["relations_charged_ops_per_run"] = float(np.mean([a[4]["word"] - b[4]["word"] for a, b in zip(new, old)]))
            for N, p, q in nums[::len(nums) // 2][:2]:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                full = comb = 0
                lnN = __import__("math").log(N)
                for at in tr["attempts"]:
                    comb += at["lp"]["combos"]
                    B = max(30, int(g["bc"] * __import__("math").exp(0.5 * __import__("math").sqrt(lnN * __import__("math").log(lnN)))))
                    led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
                    led.build_base()
                    for v in at["cands"]:
                        v = abs(v)
                        if v == 0:
                            continue
                        for pp in led.base[1:]:
                            while v % pp == 0:
                                v //= pp
                        full += v == 1
                r = run(g, [(N, p, q)])[0]
                ro = run(g, [(N, p, q)], old=True)[0]
                py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                rt = {k: v for k, v in r[4].items() if v}
                n2 += 1
                b2 += not (r[4]["word"] - ro[4]["word"] == 2 * full + 3 * comb and py == rt and m.ops == r[0])
        for gname, gg in (("cfrac", [{"t": "cfrac"}]), ("sq smooth", [{"t": "sq", "k": 0.34, "mode": "smooth", "c": 1.0, "w": 0.17, "ksq": False}])):
            sub = nums[:40] if bits <= 54 else []
            if not sub:
                continue
            new, old = run(gg, sub, cap=2 ** 26), run(gg, sub, old=True, cap=2 ** 26)
            for a, b in zip(new, old):
                if a[1] is None or b[1] is None:
                    continue
                n3 += 1
                b3 += not (a[1] == b[1] and a[0] >= b[0])
        for name, v in out[bits].items():
            print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.1f} / {v[Pn]['after']:,.1f} (+{(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:.3f}%)" for Pn in ("official", "ruint", "montgomery"))
                + f"; charged ops per run {v['relations_charged_ops_per_run']:.0f}", flush=True)
    print(f"1. qs vs pre-change lampcore: only word (and ops) rise, by the same amount: {n1 - b1}/{n1}")
    print(f"2. word rise = 2 x full offered + 3 x combined offered (trace), and Python = Rust: {n2 - b2}/{n2}")
    print(f"3. cfrac / sq smooth at 54 bits: same factor, ops not lower: {n3 - b3}/{n3}")
    json.dump(out, open("meter_accept.json", "w"), indent=1)
    assert not (b1 or b2 or b3)
