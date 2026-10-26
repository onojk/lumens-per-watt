"""Information only (user, Oct 25; decides MOVES "Cheaper polynomial setup" candidate (c)). New reference
genes as qs alone (corrected card, kset), Python traces on 3 balanced and 3 band-24 map numbers per size:
A's used per run, distinct pool primes used, pool size P, s, polynomials per A, F; Euclid steps per
inverse of A mod a sieved prime; and the cost of today's per-A inverses against a lazily filled cache
(a pool prime's inverses mod every odd factor-base prime computed the first time it appears in an A,
then s - 1 small modular multiplications per A per sieved prime), per pricing, as a share of qs cost.
  python3 acount.py -> acount.out (stdout)
"""
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
def price(Pn, t):
    return 1.0 if Pn == "official" else PR[Pn][t]
for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
    stat = {"A": [], "distinct": [], "P": [], "s": [], "ppa": [], "F": []}
    steps_all = []
    cost = {Pn: {"today": 0.0, "lazy": 0.0, "qs": 0.0} for Pn in ("official", "ruint", "montgomery")}
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        c = {k: v for k, v in optypes.qs_counts(tr).items() if v}
        for Pn in cost:
            cost[Pn]["qs"] += sum(price(Pn, t) * v for t, v in c.items())
        nA = sum(a["a_count"] for a in tr["attempts"])
        stat["A"].append(nA)
        distinct = set(q for a in tr["attempts"] for A_ in a["a_seq"] for q in A_)
        stat["distinct"].append(len(distinct))
        a0 = tr["attempts"][-1]
        stat["P"].append(a0["P"]); stat["s"].append(a0["s"]); stat["F"].append(a0["F"])
        stat["ppa"].append(sum(len(a["polys"]) for a in tr["attempts"]) / max(1, nA))
        # inverses of A mod each sieved prime: the inv entries after each A's s entries (A's own primes)
        today_steps, n_sieved_total, s_ = 0, 0, a0["s"]
        for a in tr["attempts"]:
            inv = a["inv"]; s = a["s"]; i = 0
            per_A = len(inv) // max(1, a["a_count"])
            for _ in range(a["a_count"]):
                block = inv[i:i + per_A]; i += per_A
                sieved = block[s:]
                today_steps += sum(st for _, _, st in sieved)
                steps_all += [st for _, _, st in sieved]
                n_sieved_total += len(sieved)
        mean_steps = np.mean(steps_all) if steps_all else 0
        n_fb_odd = a0["F"] - 2
        lazy_euclid = len(distinct) * n_fb_odd * mean_steps
        lazy_mults = n_sieved_total * (s_ - 1)
        for Pn in cost:
            cost[Pn]["today"] += today_steps * price(Pn, "setup_euclid")
            cost[Pn]["lazy"] += lazy_euclid * price(Pn, "setup_euclid") + lazy_mults * price(Pn, "setup_small")
    mean = {k: np.mean(v) for k, v in stat.items()}
    print(f"{bits} bits ({len(sample)} numbers): A's per run {mean['A']:.1f} (range {min(stat['A'])}-{max(stat['A'])}); distinct pool primes used {mean['distinct']:.1f}; "
          f"P {mean['P']:.0f}; s {mean['s']:.1f}; polynomials per A {mean['ppa']:.1f}; F {mean['F']:.0f}; Euclid steps per inverse {np.mean(steps_all):.2f}", flush=True)
    print("   per-A inverses today vs lazy cache, share of qs cost (official / ruint / Montgomery): today "
          + " / ".join(f"{cost[Pn]['today'] / cost[Pn]['qs']:.3f}" for Pn in cost) + "; lazy "
          + " / ".join(f"{cost[Pn]['lazy'] / cost[Pn]['qs']:.3f}" for Pn in cost) + "; net saving "
          + " / ".join(f"{(cost[Pn]['today'] - cost[Pn]['lazy']) / cost[Pn]['qs']:+.3f}" for Pn in cost), flush=True)
