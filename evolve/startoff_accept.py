"""Acceptance for the start-offset meter correction (item 10; NOTES.md, "Meter correction: the sieve's
start offsets"; tests written before the code), and its report.

  1. Against the pre-change lampcore (LAMPCORE_OLD), all map numbers, new / frozen / corrected references,
     with and without re-sieve (p0 30): factor, tests, hits, sieve updates and scans, candidates (confirm
     counts) identical; only setup_small and word (and ops) rise.
  2. From Python traces: the word rise = roots sieved (sum over polynomials) + roots walked under re-sieve,
     and the setup_small rise = (F - 2) per attempt that reaches polynomial setup; Python = Rust per type.
  3. Report, cost per number, absolute: before (pre-change, sieve_update at 0.0340 / 0.1254); after the meter
     correction at that sieve_update price; and after with sieve_update at the clean price.

  LAMPCORE_OLD=<pre-change binary> python3 startoff_accept.py -> startoff_accept.json, stdout
"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
OLD_SU = {"ruint": 0.0340, "montgomery": 0.1254}

def genomes(bits):
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    return {"new ref": nr, "new ref + re-sieve": dict(nr, confirm="resieve", p0=30), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}

def run(g, nums, old=False):
    b0 = fastlamps.BIN
    if old:
        fastlamps.BIN = os.environ["LAMPCORE_OLD"]
    try:
        return run_many([g], nums, P.QS_CAP, types=True)
    finally:
        fastlamps.BIN = b0

def cost(t, Pn, su):
    t = {k: v for k, v in t.items() if v}
    if Pn == "official":
        return float(sum(t.values()))
    pr = dict(PR[Pn]); pr["sieve_update"] = su
    return float(sum(pr[k] * v for k, v in t.items()))

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = 0
    out = {}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        out[bits] = {}
        for name, g in genomes(bits).items():
            new, old = run(g, nums), run(g, nums, old=True)
            for x, y in zip(new, old):
                n1 += 1
                fixed = ("sieve_update", "sieve_scan", "confirm_full", "confirm_td", "lp_full", "lp_small", "la", "mult", "fb")
                b1 += not (x[1:4] == y[1:4] and all(x[4][t] == y[4][t] for t in fixed)
                           and x[4]["setup_small"] >= y[4]["setup_small"] and x[4]["word"] >= y[4]["word"]
                           and x[0] - y[0] == (x[4]["setup_small"] - y[4]["setup_small"]) + (x[4]["word"] - y[4]["word"]))
            out[bits][name] = {Pn: {"before": float(np.mean([cost(y[4], Pn, OLD_SU.get(Pn)) for y in old])),
                                    "after_meter": float(np.mean([cost(x[4], Pn, OLD_SU.get(Pn)) for x in new])),
                                    "after_clean_su": float(np.mean([cost(x[4], Pn, PR[Pn]["sieve_update"] if Pn != "official" else None) for x in new]))}
                               for Pn in ("official", "ruint", "montgomery")}
            for N, p, q in nums[::len(nums) // 2][:2]:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                roots = sum(len(pl["roots"]) for at in tr["attempts"] for pl in at["polys"])
                p0 = g.get("p0", 30)
                walked = sum(1 for at in tr["attempts"] for pl in at["polys"] for (pp, r) in pl["roots"] if pp >= p0) if g.get("confirm") == "resieve" else 0
                setups = sum(at["F"] - 2 for at in tr["attempts"] if "P" in at)
                x = run(g, [(N, p, q)])[0]; y = run(g, [(N, p, q)], old=True)[0]
                c = {k: v for k, v in optypes.qs_counts(tr).items() if v}
                rt = {k: v for k, v in x[4].items() if v}
                n2 += 1
                ok = (x[4]["word"] - y[4]["word"] == roots + walked and x[4]["setup_small"] - y[4]["setup_small"] == setups and c == rt and m.ops == x[0])
                b2 += not ok
                if not ok:
                    print("   check 2 mismatch", bits, name, N, x[4]["word"] - y[4]["word"], roots + walked, x[4]["setup_small"] - y[4]["setup_small"], setups, c == rt, m.ops == x[0])
            v = out[bits][name]
            print(f"{bits} bits, {name}: cost per number before / after meter / after clean sieve_update: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.0f} / {v[Pn]['after_meter']:,.0f} (+{(v[Pn]['after_meter'] / v[Pn]['before'] - 1) * 100:.2f}%) / {v[Pn]['after_clean_su']:,.0f} ({(v[Pn]['after_clean_su'] / v[Pn]['before'] - 1) * 100:+.2f}%)" for Pn in v), flush=True)
    print(f"1. only setup_small and word (and ops) rise; everything else identical: {n1 - b1}/{n1}")
    print(f"2. word rise = roots (+ walked), setup_small rise = (F - 2) per attempt, Python = Rust: {n2 - b2}/{n2}")
    json.dump(out, open("startoff_accept.json", "w"), indent=1)
    assert not (b1 or b2)
