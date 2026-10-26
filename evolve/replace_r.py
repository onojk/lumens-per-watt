"""Replacement-rule test for the final Track R genes (NOTES.md, "Replacement-rule test, final Track R
genes": protocol and predictions written before this ran).

Fresh set per size (54 / 72 / 84 / 96): 240 balanced numbers semiprimes_pq(bits, 240, 9600000 + bits)
and a banded population (9430000 + 100 pb + bits, 80 per band). Every genome runs as qs alone.
  (2) as-frozen (the pre-registered rule scores this): the final Track R genes on the corrected card
      (a_mode on_demand, sort_charge 1, kset sf32) against the frozen reference (qs + lc 1.4, enumerate).
  (1) card-matched (reported beside it): the same genes against qs + lc 1.4's genes on the same card.
Rule: at every size no pricing's paired interval above 0 (balanced); no misses; pooled over the four
balanced sets, all three pricings below 1 with intervals excluding 0; and the per-band 1.5x gate on
the banded set (every band, all three pricings): a FAIL fails the rule, a BORDERLINE is reported.
Information: each genome in its (d) pipeline on the banded set against the frozen reference alone.

  python3 replace_r.py -> replace_r.json, stdout
"""
import json, math, random
import numpy as np
import oracle
import partition as P, sizescale as SS, stopping as ST, sizescale3 as K
from fastlamps import semiprimes_pq

PR3 = P.PRICINGS
KSET = {"kset": "sf32"}
sealed = json.load(open("sizescale_k_sealed.json"))
REF = {"(2) as-frozen": SS.FROZEN_REF, "(1) card-matched": dict(SS.OLD, **KSET)}

def idx_sets(groups, n=10000):
    rng = random.Random(2026)
    return [np.concatenate([g[[rng.randrange(len(g)) for _ in range(len(g))]] for g in groups]) for _ in range(n)]

def boot(cA, cB, idxs):
    out = {}
    for Pn in PR3:
        out[Pn] = {"log2": math.log2(cA[Pn].mean() / cB[Pn].mean()),
                   "ci": ST.q([math.log2(cA[Pn][i].mean() / cB[Pn][i].mean()) for i in idxs]),
                   "median_per_number": float(np.median(np.log2(cA[Pn] / cB[Pn])))}
    rob = lambda i: max(cA[Pn][i].mean() / cB[Pn][i].mean() for Pn in PR3)
    out["robust"] = {"ratio": rob(np.arange(len(cA["official"]))), "ci": ST.q([rob(i) for i in idxs])}
    return out

def gate(c, R_, groups):
    ub = lb = 0.0
    for Pn in PR3:
        for gi in groups:
            r2 = random.Random(2026)
            vals = []
            for _ in range(2000):
                i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
            lo, hi = ST.q(vals)
            ub, lb = max(ub, hi), max(lb, lo)
    return ("FAIL" if lb > ST.GATE else ("PASS" if ub <= ST.GATE else "BORDERLINE")), ub, lb

def fmt(b):
    return "  ".join(f"{Pn[:4]} {b[Pn]['log2']:+.3f} [{b[Pn]['ci'][0]:+.3f}, {b[Pn]['ci'][1]:+.3f}]" for Pn in PR3) + \
        f"  robust {b['robust']['ratio']:.3f} [{b['robust']['ci'][0]:.3f}, {b['robust']['ci'][1]:.3f}]"

if __name__ == "__main__":
    out = {"sizes": {}, "rule": {}}
    pool = {"A": {Pn: [] for Pn in PR3}, **{k: {Pn: [] for Pn in PR3} for k in REF}}
    state = {k: {"never_worse": True, "gate_fail": False} for k in REF}
    misses = 0
    IB = []
    for bits in SS.SIZES:
        rec = sealed["sizes"][str(bits)]["tracks"]["R"]
        g = dict(SS.qsg(rec["new_genes"]), **KSET)
        bal = semiprimes_pq(bits, 240, 9600000 + bits)
        oracle.check(bal)
        bp = SS.pop(bits, P.PER_BAND, 9430000)
        mix = [t for v in bp.values() for t in v]
        oracle.check(mix)
        band = np.array([pb for pb, v in bp.items() for _ in v])
        groups = [np.flatnonzero(band == pb) for pb in bp]
        mA, cA = SS.costs([g], bal)
        mM, cM = SS.costs([g], mix)
        misses += mA + mM
        ib = idx_sets([np.arange(len(bal))])
        IB.append(ib)
        _, cPB = SS.costs(K.pipeline(g, *rec["budgets"]["(d) new winner, new budgets"]), bal)   # (d) pipeline, balanced
        row = {"genes": rec["new_genes"], "winner": rec["new_winner"], "misses_balanced": mA, "misses_banded": mM}
        print(f"{bits} bits, {rec['new_winner']} on the corrected card with kset sf32, qs alone (misses: balanced {mA}, banded {mM})", flush=True)
        for k, ref in REF.items():
            mR, cR = SS.costs([ref], bal)
            _, cRM = SS.costs([ref], mix)
            b = boot(cA, cR, ib)
            worse = [Pn for Pn in PR3 if b[Pn]["ci"][0] > 0]
            gt = gate(cM, cRM, groups)
            state[k]["never_worse"] &= not worse
            state[k]["gate_fail"] |= gt[0] == "FAIL"
            for Pn in PR3:
                pool[k][Pn].append(cR[Pn])
            bpb = boot(cPB, cR, ib)
            row[k] = {"balanced": b, "balanced_pipeline": bpb, "clearly_worse": worse, "ref_misses": mR,
                      "banded_gate": {"gate": gt[0], "upper": gt[1], "lower": gt[2]},
                      "banded_ratio": {Pn: float(cM[Pn].mean() / cRM[Pn].mean()) for Pn in PR3}}
            print(f"   {k:17s} balanced: {fmt(b)}" + (f"  CLEARLY WORSE: {worse}" if worse else ""), flush=True)
            print(f"   {'':17s} balanced, (d) pipeline (information): {fmt(bpb)}", flush=True)
            print(f"   {'':17s} banded: " + " / ".join(f"{v:.3f}" for v in row[k]["banded_ratio"].values())
                  + f"; per-band gate {gt[0]} (upper {gt[1]:.3f})", flush=True)
        for Pn in PR3:
            pool["A"][Pn].append(cA[Pn])
        mP, cP = SS.costs(K.pipeline(g, *rec["budgets"]["(d) new winner, new budgets"]), mix)
        _, cPF = SS.costs([SS.FROZEN_REF], mix)
        bP = boot(cP, cPF, idx_sets(groups))
        row["pipeline_vs_frozen_banded"] = bP
        row["pipeline_misses"] = mP
        print(f"   (information) (d) pipeline {rec['budgets']['(d) new winner, new budgets']} on the banded set vs frozen ref alone: {fmt(bP)}; misses {mP}", flush=True)
        out["sizes"][bits] = row
    # pooled as the rule was written: the mean over sizes of the per-size log2 mean-cost ratio, with a
    # bootstrap that resamples each size's numbers (the per-size resamples, replicate by replicate)
    def pooled(k):
        b = {}
        for Pn in PR3:
            per = lambda r: np.mean([math.log2(pool["A"][Pn][s][IB[s][r]].mean() / pool[k][Pn][s][IB[s][r]].mean()) if r is not None
                                     else math.log2(pool["A"][Pn][s].mean() / pool[k][Pn][s].mean()) for s in range(len(SS.SIZES))])
            b[Pn] = {"log2": float(per(None)), "ci": ST.q([per(r) for r in range(len(IB[0]))])}
        b["robust"] = {"ratio": max(2 ** b[Pn]["log2"] for Pn in PR3), "ci": (float("nan"), float("nan"))}
        return b
    for k in REF:
        b = pooled(k)
        pooled_ok = all(b[Pn]["ci"][1] < 0 for Pn in PR3)
        passed = state[k]["never_worse"] and misses == 0 and pooled_ok and not state[k]["gate_fail"]
        out["rule"][k] = {"pooled": b, "never_clearly_worse": state[k]["never_worse"], "misses": misses,
                          "pooled_all_below": pooled_ok, "per_band_gate_failed": state[k]["gate_fail"], "passes": passed}
        print(f"{k} pooled (mean of per-size log2, 960 balanced): " + "  ".join(f"{Pn[:4]} {b[Pn]['log2']:+.3f} [{b[Pn]['ci'][0]:+.3f}, {b[Pn]['ci'][1]:+.3f}]" for Pn in PR3))
        print(f"{k}: never clearly worse {state[k]['never_worse']}; misses {misses}; pooled all three below 1 {pooled_ok}; "
              f"per-band gate failed {state[k]['gate_fail']} -> " + ("PASSES" if passed else "FAILS")
              + ("  [the pre-registered rule scores this comparison]" if k.startswith("(2)") else "  [reported beside it]"))
    json.dump(out, open("replace_r.json", "w"), indent=1, default=float)
