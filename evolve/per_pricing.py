"""Per-pricing grid optima (rho, ECM; td, pm1 off) beside the robust optimum, both cards, 72-96 bits
(NOTES.md, "Per-pricing optima under the corrected card"). Reads resolve.json (each pricing's
optimum = backward induction under that pricing, exact composition) and re-scores every optimum
on the maps under each pricing.

  python3 per_pricing.py  -> per_pricing.json, stdout
"""
import sys
sys.argv[1:] = []
import json
import partition as P
import resolve as RS
import typemix as TM

d = json.load(open("resolve.json"))
out = {}
maps = {}
for bits in RS.SIZES:
    nums, _ = TM.load(bits)
    rows = RS.rows_of(bits)
    RS.add_qs(rows, nums, RS.CORR(RS.OLD), "qs corrected")
    maps[bits] = {"enumerate": P.Map(rows, "qs + lc 1.4", RS.PRc), "corrected": P.Map(rows, "qs corrected", RS.PRc)}
for bits in RS.SIZES:
    out[bits] = {}
    for card in ("enumerate", "corrected"):
        x = d["per_size"][str(bits)][card]
        M = maps[bits][card]
        cands = {f"{Pn} alone": x["bi_per_pricing"][Pn] for Pn in RS.PR3}
        cands["robust"] = x["robust"]
        res = {}
        for name, b in cands.items():
            f, sc = M.fitness((0, b["rho"], 0, b["ecm"]))
            res[name] = {"rho": b["rho"], "ecm": b["ecm"], "scores": sc, "robust": f}
        out[bits][card] = res
        print(f"{bits} {card:9s}: " + "; ".join(f"{k}: rho {v['rho']}, ecm {v['ecm']} (" + " / ".join(f"{s:.3f}" for s in v["scores"].values())
                                                  + f"; robust {v['robust']:.3f})" for k, v in res.items()))
json.dump(out, open("per_pricing.json", "w"), indent=1, default=float)
