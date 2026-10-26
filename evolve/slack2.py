"""Information only (user, Oct 25): per slack (tc + lc - 1 = 1.0 / 1.5 / 2.0 / 2.5 / tuned; tc adjusted, lc
fixed), new reference genes as qs alone (corrected card, kset), Python traces on 3 balanced map numbers
per size at 72 / 84 / 96: candidates per relation kept, and partial-pairing yield (combined relations per
partial filed). Plus the threshold reference against each position's own |Q(x)|.
  python3 slack2.py -> slack2.out (stdout)
"""
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
sealed = json.load(open("sizescale_k_sealed.json"))
u = np.linspace(0, 1, 2000001)[1:-1]
sh = -np.log2(np.abs(2 * u * u - 1))
sh = sh[np.isfinite(sh)]
print(f"threshold reference vs |Q(x)| = M sqrt(kN/2) |2u^2 - 1| (u = x/M uniform): mean shortfall {sh.mean():.3f} bits, "
      f"median {np.median(sh):.3f} bits, 90th pct {np.percentile(sh, 90):.3f} bits", flush=True)
for bits in (72, 84, 96):
    g0 = sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3]
    s0 = round(g0["tc"] + g0["lc"] - 1, 3)
    lnN = math.log(sample[0][0]); B = max(30, int(g0["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    print(f"{bits} bits: log2 B ~ {math.log2(B):.2f}, so 1 slack unit ~ {math.log2(B):.1f} bits; mean shortfall {sh.mean():.2f} bits = {sh.mean() / math.log2(B):.3f} slack units", flush=True)
    for s in (1.0, 1.5, 2.0, 2.5, s0):
        g = dict(SS.qsg(dict(g0, tc=s + 1 - g0["lc"])), kset="sf32")
        C = R = Rc = ins = 0
        for N, _, _ in sample:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                qs.lamp_qs(N, g, m)
            except lamps.Budget:
                pass
            tr = qs.TRACE; qs.TRACE = None
            for at in tr["attempts"]:
                C += len(at["cands"]); R += len(at.get("rels", [])); Rc += at["lp"]["combos"]; ins += at["lp"]["inserts"]
        print(f"   slack {s:.3f}: candidates per relation {C / R:.2f}; relations {R / len(sample):.0f} per number, of which combined from partials {Rc / R:.2f}; "
              f"pairing yield {Rc / ins if ins else 0:.3f} combined per partial filed ({ins / len(sample):.0f} partials per number)", flush=True)
