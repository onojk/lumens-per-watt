"""Re-sieve against full-pass confirmation (user's decision 2, Oct 25): qs alone on all map numbers, per size,
for the new reference genes (final Track R genes, corrected card, kset) and both old references, with
confirm absent and confirm = resieve (p0 30), at the genes' tuned slack. Absolute cost per number per
pricing, and the ratio. Current pricing (the Gray-code re-typing is not applied here; it is reported separately).
  python3 resieve_measure.py -> resieve_measure.json, resieve_measure.out (stdout)
"""
import json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
out = {}
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    G = {"new ref": dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32"),
         "frozen ref (old)": SS.FROZEN_REF, "corrected ref (old genes)": SS.OLD}
    out[bits] = {}
    for name, g in G.items():
        r = {}
        for lab, gg in (("full pass", g), ("re-sieve", dict(g, confirm="resieve", p0=30))):
            rs = run_many([gg], nums, P.QS_CAP, types=True)
            assert all(x[1] is not None for x in rs)
            c = {Pn: float(np.mean([optypes.cost({k: v for k, v in x[4].items() if v}, Pn, PR) for x in rs])) for Pn in ("official", "ruint", "montgomery")}
            r[lab] = c
        out[bits][name] = r
        print(f"{bits} bits, {name}: cost per number full pass / re-sieve (ratio): " + "  ".join(
            f"{Pn[:4]} {r['full pass'][Pn]:,.0f} / {r['re-sieve'][Pn]:,.0f} ({r['re-sieve'][Pn] / r['full pass'][Pn]:.3f})" for Pn in r["full pass"]), flush=True)
json.dump(out, open("resieve_measure.json", "w"), indent=1)
