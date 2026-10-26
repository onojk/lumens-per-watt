"""Information only (user's confounding guard, Oct 25): the full-pass slack sweep priced both ways, current
pricing (Gray-code root updates charged setup_small) and re-typed (those updates at the word-level price,
like sieve_update). The saved slackcheck output kept only ratios, and lampcore's types do not separate the
Gray-code updates from the rest of setup_small, so this reruns the sweep on Python traces (exact update
counts: sum of switches_roots) on 3 balanced and 3 band-24 map numbers per size at 72 / 84 / 96. New
reference genes, corrected card, kset; lc fixed, tc set for slack 1.0 / 1.5 / 2.0 / 2.5 / tuned.
  python3 slackrep.py -> slackrep.json, slackrep.out (stdout)
"""
import json
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
def price(Pn, t):
    return 1.0 if Pn == "official" else PR[Pn][t]
out = {}
for bits in (72, 84, 96):
    g0 = sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
    s0 = round(g0["tc"] + g0["lc"] - 1, 3)
    res = {}
    for s in (1.0, 1.5, 2.0, 2.5, s0):
        g = dict(SS.qsg(dict(g0, tc=s + 1 - g0["lc"])), kset="sf32")
        tot, gray = {}, 0
        for N, _, _ in sample:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            try:
                qs.lamp_qs(N, g, m)
            except lamps.Budget:
                pass
            tr = qs.TRACE; qs.TRACE = None
            for t, v in optypes.qs_counts(tr).items():
                tot[t] = tot.get(t, 0) + v
            gray += sum(sum(a["switches_roots"]) for a in tr["attempts"])
        both = {}
        for Pn in ("official", "ruint", "montgomery"):
            cur = sum(price(Pn, t) * v for t, v in tot.items() if v)
            ret = cur - gray * price(Pn, "setup_small") + gray * price(Pn, "sieve_update")
            both[Pn] = {"current": cur / len(sample), "retyped": ret / len(sample)}
        res[s] = {"types": tot, "gray_updates": gray, "cost_per_number": both}
    out[bits] = {str(k): v for k, v in res.items()}
    print(f"{bits} bits (tuned slack {s0}): cost per number (op-cost units), current / re-typed", flush=True)
    for s, r in res.items():
        print(f"   slack {s:.3f}: " + "  ".join(f"{Pn[:4]} {r['cost_per_number'][Pn]['current']:,.0f} / {r['cost_per_number'][Pn]['retyped']:,.0f}" for Pn in ("official", "ruint", "montgomery"))
              + f"; Gray updates per number {r['gray_updates'] / len(sample):,.0f}", flush=True)
    for Pn in ("official", "ruint", "montgomery"):
        bc = min(res, key=lambda s: res[s]["cost_per_number"][Pn]["current"])
        br = min(res, key=lambda s: res[s]["cost_per_number"][Pn]["retyped"])
        cut = 1 - res[s0]["cost_per_number"][Pn]["retyped"] / res[s0]["cost_per_number"][Pn]["current"]
        print(f"   {Pn}: best slack current {bc}, re-typed {br}; re-typing cuts qs cost at the tuned slack by {cut:.3f}", flush=True)
json.dump(out, open("slackrep.json", "w"), indent=1, default=float)
