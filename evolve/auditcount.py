"""Information only (user, Oct 26; no re-typing): ops per run and share of qs cost per pricing, at today's
types, for audit items 1-8. New reference genes as qs alone (corrected card, kset sf32), Python traces on
3 balanced and 3 band-24 map numbers per size. Counts from trace fields and the card's charge formulas.
  python3 auditcount.py -> auditcount.out (stdout)
"""
import json
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
from qs import sort_cost
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
def pr(Pn, t):
    return 1.0 if Pn == "official" else PR[Pn][t]
for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
    items = {k: {} for k in range(1, 9)}     # item -> {type: count}
    total = {}
    def add(i, t, n):
        items[i][t] = items[i].get(t, 0) + n
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        for t, v in optypes.qs_counts(tr).items():
            total[t] = total.get(t, 0) + v
        add(2, "mult", sort_cost(20))                       # multiplier ranking sort (kset: 20 candidates)
        for a in tr["attempts"]:
            s, F = a["s"], a["F"]
            # 1: on-demand search small ops (overlap checks, closeness scan), t' per prefix, the target check (typed full)
            add(1, "setup_small", a["od_small"] + a["od_prefixes"])
            add(1, "setup_full", a["od_cands"])
            # 2: sorts: pool selection and its ascending sort per attempt; the A-key sort per accepted A
            add(2, "setup_small", a["n_pool_all"] + sort_cost(a["n_pool_all"]) + sort_cost(a["P"]) + sort_cost(s) * a.get("od_keys", 0))
            # 3: forming A: the prefix products (s - 2 each, setup_small) and A = A' * last (typed full)
            add(3, "setup_small", (s - 2) * a["od_prefixes"])
            add(3, "setup_full", a["od_cands"] + (s - 1) * a["od_prefixes"])
            # 4: B_l = (A/q) * gamma, s per A (typed full); A/q itself divides by q (small-modulus, not a candidate)
            add(4, "setup_full", s * a["a_count"])
            nc = len(a["cands"])
            add(5, "confirm_full", 2 * nc)                    # v evaluation
            lp = a.get("lp", {})
            add(6, "lp_small", lp.get("cof", 0) + 2 * lp.get("lt", 0) - lp.get("combos", 0))   # bound check per cofactor; lookup per partial; insert per new q
            add(7, "lp_small", lp.get("combos", 0) * F)       # exponent-vector add per combination
            add(8, "confirm_td", nc)                          # the sign check inside the F-pass
    tot = {Pn: sum(pr(Pn, t) * v for t, v in total.items() if v) for Pn in ("official", "ruint", "montgomery")}
    print(f"{bits} bits ({len(sample)} numbers): ops per run, and share of qs cost (official / ruint / Montgomery) at today's types", flush=True)
    for i in range(1, 9):
        ops = sum(items[i].values()) / len(sample)
        sh = [sum(pr(Pn, t) * v for t, v in items[i].items()) / tot[Pn] for Pn in tot]
        print(f"   item {i}: {ops:,.0f} ops per run ({', '.join(f'{t} {v / len(sample):,.0f}' for t, v in items[i].items())}); share " + " / ".join(f"{x:.4f}" for x in sh), flush=True)
