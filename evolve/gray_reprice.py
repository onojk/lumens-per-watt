"""Gray-code before / after restated under the clean word price (re-pricing only; op counts unchanged).
qs alone on all map numbers, current lampcore (Gray re-typed, ledger charged), three references. Columns:
before (setup_gray at setup_small), after at the old word price (0.0340 / 0.1254), after at the clean price.
The 'word' type (the ledger check) is priced at the clean word price in every column.
  python3 gray_reprice.py -> gray_reprice.json, stdout
"""
import json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
OLD_WORD = {"ruint": 0.0340, "montgomery": 0.1254}
def cost(t, Pn, gray):
    t = {k: v for k, v in t.items() if v}
    if Pn == "official":
        return float(sum(t.values()))
    pr = dict(PR[Pn]); pr["setup_gray"] = gray
    return float(sum(pr[k] * v for k, v in t.items()))
out = {}
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    out[bits] = {}
    G = {"new ref": dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32"),
         "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}
    for name, g in G.items():
        rs = run_many([g], nums, P.QS_CAP, types=True)
        r = {}
        for Pn in ("ruint", "montgomery"):
            b = np.mean([cost(x[4], Pn, PR[Pn]["setup_small"]) for x in rs])
            ao = np.mean([cost(x[4], Pn, OLD_WORD[Pn]) for x in rs])
            an = np.mean([cost(x[4], Pn, PR[Pn]["word"]) for x in rs])
            r[Pn] = {"before": b, "after_old_word": ao, "after_clean_word": an,
                     "cut_old_word": 1 - ao / b, "cut_clean_word": 1 - an / b}
        out[bits][name] = r
        print(f"{bits} bits, {name}: " + "  ".join(
            f"{Pn[:4]} {v['before']:,.0f} -> {v['after_old_word']:,.0f} ({v['cut_old_word'] * 100:.2f}%) | clean {v['after_clean_word']:,.0f} ({v['cut_clean_word'] * 100:.2f}%)"
            for Pn, v in r.items()), flush=True)
json.dump(out, open("gray_reprice.json", "w"), indent=1, default=float)
