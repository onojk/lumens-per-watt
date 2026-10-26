"""Stage F (step 6, read-only): the yield model (yieldmodel.py) against the card's own polynomials at 84 and 96.
The same 8 map numbers per size as stage B (step9.sample); new reference genes, KS on; each polynomial's residues
|g(x)| over its whole interval, its base and root counts (A's primes and p | k one-root), the large-prime bound L.
Capture is a measured input, not a fit: stage B's threshold-pass rates for fulls and for partials by log2(q/B) band
(step9.json). Reported, model against card, per size (means over the 8 numbers):
  true fulls and partials per polynomial (the card's from stage B's exact factoring);
  captured fulls and partials per polynomial;
  combinations at the card's own polynomial count, and the never-combined share (Poisson per q, lambda_q from the
  model, times capture);
  polynomials to completion (model: solve P x fulls_cap + combos(P) = F + 10) against the card's;
  the L/B 12 effects (slack kept: capture by band unchanged, L = 12 B): polynomials, stored partials, combinations.
  python3 stagef.py -> stagef.json, stdout
"""
import json, math
import numpy as np
import partition as P, qs, lamps
from ledger import Charger, Ledger
from lctest import ref, bnd, x3
from step9 import sample
from yieldmodel import Model

S9 = json.load(open("step9.json"))
BANDS = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 99)]

def cap_q(bits, qb):
    tab = S9[str(bits)]["part"]["by_qb"]
    for lo, hi in BANDS:
        if lo <= qb < hi:
            v = tab[f"{lo}-{hi}"]["passed"]
            return v if v == v else 0.0            # nan (no partials in band) -> 0
    return 0.0

def number(bits, N, g):
    qs.TRACE_ARR = True
    qs.TRACE = {}
    qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    tr = qs.TRACE; qs.TRACE = None; qs.TRACE_ARR = False
    B = bnd(N, g); L = B ** g["lc"]
    fcap = S9[str(bits)]["full"]["passed"]
    res = None
    for at in tr["attempts"]:
        if "s1" not in at:
            continue
        k = at["k"]; kN = k * N
        led = Ledger(N, k, B, Charger(lamps.Meter(1 << 60), None), None); led.build_base()
        odd = led.base[2:]
        pmax = odd[-1]
        lnp, lnL = math.log(pmax), math.log(L)
        ts = np.arange(lnp, lnL, 0.05)               # t = ln q grid over (pmax, L]
        models = {}
        tf = tp = 0.0
        lam_true = np.zeros(len(ts))                  # sum over polynomials of lambda_q(t) (true, uncaptured)
        npolys = 0
        for po in at["polys"]:
            if "A" not in po:
                continue
            A = po["A"]
            if A not in models:
                ap = {p for p in odd if A % p == 0}
                c = [1.0 if (p in ap or k % p == 0) else 2.0 for p in odd]
                mdl = Model(odd, c, kN, pmax)
                ss, lg = mdl.grid(48.0, 0.1)
                models[A] = (ss, lg)
            ss, lg = models[A]
            M, Bv, C = po["Mw"], po["B"], po["C"]
            sv = np.array([math.log(abs((A * x + 2 * Bv) * x + C)) for x in range(-M, M + 1) if (A * x + 2 * Bv) * x + C != 0])
            pf = np.exp(np.interp(sv, ss, lg))
            tf += pf.sum()
            # partials density over t: per position exp(logP(s - t)) / t; lambda_q(t) = (2 / q) sum_x exp(logP(s_x - t))
            sm = np.exp(np.interp(sv[None, :] - ts[:, None], ss, lg, left=0.0))
            tp += float((sm.sum(axis=1) / ts).sum() * 0.05)
            lam_true += 2 * np.exp(-ts) * sm.sum(axis=1)
            npolys += 1
        cap = np.array([cap_q(bits, (t - math.log(B)) / math.log(2)) for t in ts])
        dens = np.exp(ts) / (2 * ts) * 0.05          # eligible primes per t step (half the primes have roots)
        F = led.F
        def combos(x):
            return float((dens * (x - 1 + np.exp(-x))).sum())
        x_card = lam_true * cap                        # summed over the card's own polynomials
        lam1 = lam_true / npolys * cap                  # per polynomial, captured
        full1 = tf / npolys * fcap
        def need(Pp, lim=None):
            lm = lam1 if lim is None else lam1 * (ts <= lim)
            return Pp * full1 + combos(Pp * lm) - (F + 10)
        def solveP(lim=None):
            lo, hi = 0.0, 1e6
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if need(mid, lim) > 0:
                    hi = mid
                else:
                    lo = mid
            return 0.5 * (lo + hi)
        P0 = solveP()
        P12 = solveP(math.log(12 * B))
        def stored(Pp, lim=None):
            lm = lam1 if lim is None else lam1 * (ts <= lim)
            return float((dens * (1 - np.exp(-Pp * lm))).sum())
        res = {"polys_card": npolys, "true_fulls_per_poly": tf / npolys, "true_parts_per_poly": tp / npolys,
               "cap_fulls_per_poly": full1, "cap_parts_per_poly": float((dens * lam1).sum()),
               "combos_at_card_P": combos(x_card), "looked_up_at_card_P": float((dens * x_card).sum()),
               "never_combined": float((dens * x_card * np.exp(-x_card)).sum() / (dens * x_card).sum()),
               "polys_model": P0, "polys_model_L12": P12, "stored_model": stored(P0), "stored_model_L12": stored(P12, math.log(12 * B)),
               "combos_model": combos(P0 * lam1), "combos_model_L12": combos(P12 * lam1 * (ts <= math.log(12 * B))),
               "card_combos": at["lp"]["combos"], "card_inserts": at["lp"]["inserts"]}
    return res

if __name__ == "__main__":
    out = {}
    for bits in (84, 96):
        g = ref(bits)
        rows = [number(bits, N, g) for N, _, _ in sample(bits)]
        rows = [r for r in rows if r]
        mean = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
        nc_card, _ = x3(bits, g, sample(bits))
        mean["never_combined_card"] = nc_card
        out[bits] = {"mean": mean, "rows": rows}
        m = mean
        s9 = S9[str(bits)]
        print(f"\n{bits} bits ({len(rows)} numbers):", flush=True)
        print(f"  true per polynomial: fulls model {m['true_fulls_per_poly']:.3f} / card {s9['full']['true_per_poly']:.3f}; partials model "
              f"{m['true_parts_per_poly']:.2f} / card {s9['part']['true_per_poly']:.2f}", flush=True)
        print(f"  captured per polynomial: fulls model {m['cap_fulls_per_poly']:.3f} / card {s9['full']['true_per_poly'] * s9['full']['end_to_end']:.3f}; "
              f"partials model {m['cap_parts_per_poly']:.2f} / card {s9['part']['true_per_poly'] * s9['part']['end_to_end']:.2f}", flush=True)
        print(f"  at the card's own polynomials: combinations model {m['combos_at_card_P']:.1f} / card {m['card_combos']:.1f}; partials looked up model "
              f"{m['looked_up_at_card_P']:.0f}; never-combined model {m['never_combined']:.3f} / card {m['never_combined_card']:.3f}", flush=True)
        print(f"  polynomials to completion: model {m['polys_model']:.1f} / card {m['polys_card']:.1f}; L/B 12 (slack kept): model polynomials "
              f"{(m['polys_model_L12'] / m['polys_model'] - 1) * 100:+.1f}%, stored partials {(m['stored_model_L12'] / m['stored_model'] - 1) * 100:+.1f}%, "
              f"combinations {(m['combos_model_L12'] / m['combos_model'] - 1) * 100:+.1f}%", flush=True)
    json.dump(out, open("stagef.json", "w"), indent=1)
