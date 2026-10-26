"""Information only (user / DeepSeek, Oct 25; no card change): is the tuned slack ~2.0 an optimum or a
plateau? New reference genes (final Track R genes, corrected card, kset sf32) at 72 / 84 / 96, qs alone on
all map numbers; slack s = tc + lc - 1 fixed at 1.0 / 1.5 / 2.0 / 2.5 / tuned by setting tc = s + 1 - lc
with lc as tuned. Per pricing: mean cost relative to the tuned genome, and the cost split.
  LAMPCORE=<committed build> python3 slackcheck.py -> slackcheck.out (stdout)
"""
import json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes
from fastlamps import run_many
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
GROUPS = {"setup": ("mult", "fb", "setup_full", "setup_euclid", "setup_small"), "sieve": ("sieve_update", "sieve_scan"),
          "confirm": ("confirm_full", "confirm_td"), "lp": ("lp_full", "lp_small"), "la+sqrt": ("la", "sqrt_mul", "sqrt_gcd"),
          "other": ("check", "word")}
def cost(t, Pn):
    return float(sum(t.values())) if Pn == "official" else P.cost_of(t, PR[Pn])
for bits in (72, 84, 96):
    g0 = sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]
    nums = S2.map_nums(bits)
    s0 = g0["tc"] + g0["lc"] - 1
    res = {}
    for s in (1.0, 1.5, 2.0, 2.5, round(s0, 3)):
        g = dict(SS.qsg(dict(g0, tc=s + 1 - g0["lc"])), kset="sf32")
        rs = run_many([g], nums, P.QS_CAP, types=True)
        miss = sum(x[1] is None for x in rs)
        tot = {t: sum(x[4][t] for x in rs) for t in optypes.TYPE_ORDER}
        tot = {t: v for t, v in tot.items() if v}
        res[s] = (miss, tot)
    base = res[round(s0, 3)][1]
    print(f"{bits} bits (tuned slack {s0:.3f}: tc {g0['tc']:.3f}, lc {g0['lc']:.3f})", flush=True)
    for s, (miss, tot) in res.items():
        rel = " / ".join(f"{cost(tot, Pn) / cost(base, Pn):.3f}" for Pn in ("official", "ruint", "montgomery"))
        split = []
        for Pn in ("official", "ruint"):
            c = cost(tot, Pn)
            split.append(Pn[:4] + " " + ", ".join(f"{k} {cost({t: tot.get(t, 0) for t in ts if tot.get(t, 0)}, Pn) / c:.2f}" for k, ts in GROUPS.items()))
        print(f"   slack {s:.3f}: cost vs tuned {rel} (official / ruint / Montgomery); misses {miss}; split: " + " | ".join(split), flush=True)
