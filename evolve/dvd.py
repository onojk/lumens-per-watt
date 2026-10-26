"""Demand-vs-drift comparison, information only (PLAN bound-hit rule, adopted Oct 25 for future
rounds; reported for the kc/lc round as information). For each bound-hit gene of a (d) winner: the
winner against the same genome with that gene set to the median of the round's interior values (all
32 seed bests, excluding values within the bound-hit rule), on the 9420000 sealed numbers, track metric.
"""
import json, math, random, statistics
import numpy as np
import partition as P, sizescale as SS, stopping as ST, sizescale3 as K
tune = json.load(open("sizescale_k_tune.json"))
sealed = json.load(open("sizescale_k_sealed.json"))
kb = json.load(open("sizescale_k_budgets.json"))
allpts = [r["best"] for t in tune.values() for c in t.values() for r in c["runs"]]
def interior(g):
    lo, hi = K.BOUNDS[g]
    return statistics.median(p[g] for p in allpts if not (p[g] <= lo * 1.1 or p[g] >= hi * 0.9))
for bits in SS.SIZES:
    for tr in SS.TRACKS:
        rec = sealed["sizes"][str(bits)]["tracks"][tr]
        g = rec["new_genes"]
        hits = [x.split()[0] for x in K.bound_hits(g)]
        if not hits:
            continue
        bp = SS.pop(bits, P.PER_BAND, 9420000); nums = [t for v in bp.values() for t in v]
        band = np.array([pb for pb, v in bp.items() for _ in v]); groups = [np.flatnonzero(band == pb) for pb in bp]
        _, R_ = SS.costs([SS.OLD], nums)
        bud = rec["budgets"]["(d) new winner, new budgets"]
        _, c0 = SS.costs(K.pipeline(SS.qsg(g), *bud), nums)
        rng = random.Random(2026)
        idxs = [np.concatenate([g_[[rng.randrange(len(g_)) for _ in range(len(g_))]] for g_ in groups]) for _ in range(10000)]
        tf = lambda c, i: SS.track_fit({Pn: c[Pn][i] for Pn in P.PRICINGS}, {Pn: R_[Pn][i] for Pn in P.PRICINGS}, tr)
        for h in hits:
            v = interior(h)
            g2 = dict(g, **{h: (round(v) if h == "kc" else v)})
            _, c1 = SS.costs(K.pipeline(SS.qsg(g2), *bud), nums)
            full = np.arange(len(nums))
            d = math.log2(tf(c0, full) / tf(c1, full))
            lo, hi = ST.q([math.log2(tf(c0, i) / tf(c1, i)) for i in idxs])
            verdict = "DEMAND" if hi < 0 else "drift"
            print(f"{bits} Track {tr} winner {rec['new_winner']}: {h} {g[h]:.4g} vs interior median {g2[h]:.4g}: "
                  f"log2 winner/interior {d:+.4f} [{lo:+.4f}, {hi:+.4f}] -> {verdict}", flush=True)
