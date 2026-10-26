"""Reference change check (NOTES.md, DeepSeek's "Reference change, recorded precisely"; user's
decision 1, Oct 25): on the kc/lc round's sealed numbers (9420000), re-run winner selection and the
gates with the new reference (each size's final Track R genes as qs alone on the corrected card with
kset sf32) in place of qs + lc 1.4 corrected. Candidates, budgets and numbers are the round's own.
Run on the lampcore build before the ECM-addition change (LAMPCORE=<saved binary>).

  LAMPCORE=<binary> python3 reselect.py -> reselect.json, stdout
"""
import json, random
import numpy as np
import partition as P, sizescale as SS, stopping as ST, sizescale3 as K

PR3 = P.PRICINGS
sealed = json.load(open("sizescale_k_sealed.json"))
kb = json.load(open("sizescale_k_budgets.json"))

def gate(c, R_, groups, prs):
    ub = lb = 0.0
    for Pn in prs:
        for gi in groups:
            r2 = random.Random(2026)
            vals = []
            for _ in range(2000):
                i = gi[[r2.randrange(len(gi)) for _ in range(len(gi))]]
                vals.append(c[Pn][i].mean() / R_[Pn][i].mean())
            lo, hi = ST.q(vals)
            ub, lb = max(ub, hi), max(lb, lo)
    return ("FAIL" if lb > ST.GATE else ("PASS" if ub <= ST.GATE else "BORDERLINE")), round(ub, 3)

if __name__ == "__main__":
    out = {}
    new = {tr: {f"{tr}-k@{b}": SS.qsg(kb["genes"][str(b)][tr]) for b in SS.SIZES} for tr in SS.TRACKS}
    for bits in SS.SIZES:
        bp = SS.pop(bits, P.PER_BAND, 9420000)
        nums = [t for v in bp.values() for t in v]
        band = np.array([pb for pb, v in bp.items() for _ in v])
        groups = [np.flatnonzero(band == pb) for pb in bp]
        refR = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
        refs = {"old (qs + lc 1.4 corrected)": SS.costs([SS.OLD], nums)[1], "new (final Track R genes)": SS.costs([refR], nums)[1]}
        out[bits] = {}
        for track in SS.TRACKS:
            rec = sealed["sizes"][str(bits)]["tracks"][track]
            fc = K.final_cell(bits, track)
            bd = tuple(kb["pipelines"][str(bits)][track])
            cands = dict(new[track]); cands["current final"] = fc["final_genes"]; cands["old genes"], cands["new genes"] = SS.OLD, SS.NEW
            Cd = {g: SS.costs(K.pipeline(q_, *bd), nums) for g, q_ in cands.items()}
            res = {}
            for rn, R_ in refs.items():
                fit = {g: (None if Cd[g][0] else SS.track_fit(Cd[g][1], R_, track)) for g in Cd}
                wg = min((g for g in fit if fit[g] is not None), key=fit.get)
                c = Cd[wg][1]
                gt = gate(c, R_, groups, PR3 if track == "R" else ("montgomery",))
                res[rn] = {"winner": wg, "fitness": fit[wg], "scores": {Pn: float(c[Pn].mean() / R_[Pn].mean()) for Pn in PR3},
                           "gate": gt, "candidates": fit}
            changed = res["old (qs + lc 1.4 corrected)"]["winner"] != res["new (final Track R genes)"]["winner"]
            out[bits][track] = {"recorded_winner": rec["new_winner"], "by_reference": res, "winner_changed": changed}
            o, n = res["old (qs + lc 1.4 corrected)"], res["new (final Track R genes)"]
            print(f"{bits} Track {track}: winner old ref {o['winner']} ({o['fitness']:.4f}; gate {o['gate'][0]} {o['gate'][1]}) | "
                  f"new ref {n['winner']} ({n['fitness']:.4f}; " + " / ".join(f"{v:.3f}" for v in n["scores"].values())
                  + f"; gate {n['gate'][0]} {n['gate'][1]})" + ("  WINNER CHANGED" if changed else "  unchanged"), flush=True)
    json.dump(out, open("reselect.json", "w"), indent=1, default=float)
