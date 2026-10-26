"""I-021 before / after: qs cost per number per pricing on all map numbers, new reference with and without
re-sieve (p0 200). LAMPCORE_OLD=<pre-change binary> python3 i021_cost.py -> stdout"""
import os, json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2
import fastlamps
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json")); PR = P.prices()
def cost(t, Pn):
    t = {k: v for k, v in t.items() if v}
    return float(sum(t.values())) if Pn == "official" else float(sum(PR[Pn][k] * v for k, v in t.items()))
for bits in SS.SIZES:
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    nums = S2.map_nums(bits)
    for name, g in (("new ref", nr), ("new ref + re-sieve p0 200", dict(nr, confirm="resieve", p0=200))):
        new = run_many([g], nums, P.QS_CAP, types=True)
        b0 = fastlamps.BIN; fastlamps.BIN = os.environ["LAMPCORE_OLD"]
        old = run_many([g], nums, P.QS_CAP, types=True); fastlamps.BIN = b0
        print(f"{bits} bits, {name}: " + "  ".join(
            f"{Pn[:4]} {np.mean([cost(y[4], Pn) for y in old]):,.1f} -> {np.mean([cost(x[4], Pn) for x in new]):,.1f} "
            f"({np.mean([cost(x[4], Pn) for x in new]) - np.mean([cost(y[4], Pn) for y in old]):+,.1f}, "
            f"{(np.mean([cost(x[4], Pn) for x in new]) / np.mean([cost(y[4], Pn) for y in old]) - 1) * 100:+.2f}%)"
            for Pn in ("official", "ruint", "montgomery")), flush=True)
