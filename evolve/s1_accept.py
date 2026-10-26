"""Acceptance for step 1, deleting the fills (NOTES.md, "Step 1: delete the fills (cost model, before code)";
tests written before the run), the before / after report, and the addendum's statistics.

  1. Against the pre-step build (LAMPCORE_OLD), all map numbers, new reference off and on at p0 30 / 200 / 1000,
     frozen and corrected references: factor, tests, hits and every type but word identical.
  2. The word change equals the formula from the Python trace, 2 numbers per size per genome:
       per attempt: + s1.attempt (F, plus width + F with re-sieve)
       per re-sieve polynomial: + |cand| - width - F
       per candidate: + its step-1 charge (sets, copy, clear), - F (the old zero-fill)
       per combination: + |a| + |b| + 2|out|, - F (the old vector add)
       per solve: + the entries of the GF(2) row build
  3. Python = Rust per type, the same sample.
  4. Report: cost per number before / after per pricing, per size, new reference off and on at p0 200; the
     touched entries per candidate, per kept relation and per full relation; |cand| / width per polynomial
     (median, 90th percentile); u = log|Q| / log p_max (median over candidates).

  LAMPCORE_OLD=<pre-step binary> python3 s1_accept.py -> s1_accept.json, stdout
"""
import os, json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from ledger import Charger, Ledger
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

def trace(N, g):
    qs.TRACE = {}
    m = lamps.Meter(P.QS_CAP)
    try:
        qs.lamp_qs(N, g, m)
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    return tr, m

def want(tr, rs):
    w = 0
    for at in tr["attempts"]:
        if "s1" not in at:
            continue
        F, s1 = at["F"], at["s1"]
        w += s1["attempt"] + s1["cand"] - F * len(at["cands"]) + s1["comb"] - F * at["lp"]["combos"] + at.get("s1_bits", 0)
        if rs:
            w += sum(p["nc"] - (2 * p["M"] + 1) - F for p in at["polys"])
    return w

if __name__ == "__main__":
    n1 = b1 = n2 = b2 = 0
    out = {}
    stats = {}
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
                ok = (x[4]["word"] - y[4]["word"] == want(tr, g.get("confirm") == "resieve")
                      and py == {k: v for k, v in x[4].items() if v} and m.ops == x[0])
                b2 += not ok
                if not ok:
                    print(f"   MISMATCH {bits} {name}: dw {x[4]['word'] - y[4]['word']} want {want(tr, g.get('confirm') == 'resieve')}", flush=True)
        # addendum statistics: new reference, 6 numbers per size (3 balanced from the top band, 3 from band 24)
        rows = SS.corrected_map_rows(bits)
        top = max(r["band"] for r in rows)
        sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
        T = Tk = kept = Tf = nf = nc = 0
        dens, us = [], []
        for N, _, _ in sample:
            tr, _ = trace(N, genomes(bits)["new ref"])
            for at in tr["attempts"]:
                if "s1" not in at:
                    continue
                s1 = at["s1"]
                T += s1["T"]; Tk += s1["Tk"]; kept += s1["kept"]; Tf += s1.get("Tf", 0); nf += s1.get("nf", 0); nc += len(at["cands"])
                dens += [p["nc"] / (2 * p["M"] + 1) for p in at["polys"]]
            lnN = math.log(N)
            g0 = genomes(bits)["new ref"]
            B = max(30, int(g0["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
            for at in tr["attempts"]:
                led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
                led.build_base()
                pmax = led.base[-1]                # the largest factor-base prime
                us += [math.log(abs(v)) / math.log(pmax) for v in at["cands"] if v]
        st = {"touched_per_candidate": T / nc, "touched_per_kept": Tk / kept, "touched_per_full": Tf / nf if nf else None,
              "cand_per_width_median": float(np.median(dens)), "cand_per_width_p90": float(np.percentile(dens, 90)),
              "u_median": float(np.median(us)), "numbers": len(sample)}
        st["flag_outside_4_10"] = not (4 <= st["touched_per_candidate"] <= 10 and 4 <= st["touched_per_kept"] <= 10)
        stats[bits] = st
        for name, v in out[bits].items():
            print(f"{bits} bits, {name}: cost per number before / after: " + "  ".join(
                f"{Pn[:4]} {v[Pn]['before']:,.1f} / {v[Pn]['after']:,.1f} ({(v[Pn]['after'] / v[Pn]['before'] - 1) * 100:+.2f}%)" for Pn in v), flush=True)
        print(f"{bits} bits, new reference ({len(sample)} numbers): touched per candidate {st['touched_per_candidate']:.2f}, per kept relation "
              f"{st['touched_per_kept']:.2f}, per full relation {st['touched_per_full']:.2f}; |cand| / width median {st['cand_per_width_median'] * 100:.2f}%, "
              f"90th pct {st['cand_per_width_p90'] * 100:.2f}%; u median {st['u_median']:.2f}" + ("  FLAG (outside 4-10)" if st["flag_outside_4_10"] else ""), flush=True)
    print(f"1. only word (and ops) change, by the same amount: {n1 - b1}/{n1}")
    print(f"2-3. word change = formula (trace), Python = Rust per type: {n2 - b2}/{n2}")
    json.dump({"cost": out, "stats": stats}, open("s1_accept.json", "w"), indent=1)
    assert not (b1 or b2)
