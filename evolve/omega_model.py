"""Optional cross-check after step 1 (user, Oct 26; no meter or card change): the tilted-valuation saddle-point
model of distinct base primes per full relation, against the card's traced relations with KS on.

Model (the user's Wolfram model, nothing fitted): per base prime p with r_p roots of kN (2 for odd p not dividing
kN, 1 for p | kN), untilted P(v_p >= k) = r_p / p^k; the valuation is tilted by p^(k (1 - alpha)); alpha is solved
per relation by bisection so that sum_p E_alpha[v_p] log p = log |Q|; predicted omega = sum_p P_alpha(v_p >= 1).
The prime 2 takes r_2 = 1 (its behaviour mod 8 is not modelled).

Measured: for each full relation (a candidate whose |v| is smooth over the base, re-sieve off), the distinct base
primes dividing |v|, and the sign. |Q| here is |v| = |Q(x)| / A, the value the card trial-divides; the A-primes
(s per relation) and the sign are reported separately and added for the touched-entry comparison.
New reference genes, qs alone, 6 map numbers per size (3 top-band, 3 band-24).
  python3 omega_model.py -> omega_model.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
from ledger import Charger, Ledger
sealed = json.load(open("sizescale_k_sealed.json"))

def model_omega(lnQ, ps, rs, kmax=40):
    lp = np.log(ps)
    ks = np.arange(0, kmax + 1)
    # untilted P(v = k): k = 0: 1 - r/p; k >= 1: r/p^k - r/p^(k+1)
    pk = np.power.outer(ps, -ks.astype(float))
    pv = np.where(ks[None, :] == 0, 1 - rs[:, None] / ps[:, None], rs[:, None] * (pk - pk / ps[:, None]))
    pv = np.clip(pv, 0, None)
    def stats(alpha):
        w = pv * np.exp(np.outer(lp, ks) * (1 - alpha))
        w /= w.sum(axis=1, keepdims=True)
        ev = (w * ks[None, :]).sum(axis=1)
        return float((ev * lp).sum()), float((1 - w[:, 0]).sum())
    lo, hi = -2.0, 1.0
    if stats(hi)[0] > lnQ:
        return stats(hi)[1], hi
    for _ in range(60):
        mid = (lo + hi) / 2
        if stats(mid)[0] > lnQ:
            lo = mid
        else:
            hi = mid
    return stats((lo + hi) / 2)[1], (lo + hi) / 2

if __name__ == "__main__":
    out = {}
    for bits in SS.SIZES:
        g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
        rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
        top = max(r["band"] for r in rows)
        sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
        meas, pred, alphas, signs, svals = [], [], [], [], []
        for N, _, _ in sample:
            qs.TRACE = {}
            m = lamps.Meter(P.QS_CAP)
            qs.lamp_qs(N, g, m)
            tr = qs.TRACE; qs.TRACE = None
            lnN = math.log(N)
            B = max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
            for at in tr["attempts"]:
                if "s1" not in at:
                    continue
                led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
                led.build_base()
                kN = at["k"] * N
                base = led.base[1:]                                  # primes (2 and up)
                ps = np.array(base, dtype=float)
                rs = np.array([1.0 if (p == 2 or kN % p == 0) else 2.0 for p in base])
                for v in at["cands"]:
                    if v == 0:
                        continue
                    w, om = abs(v), 0
                    for p in base:
                        if w % p == 0:
                            om += 1
                            while w % p == 0:
                                w //= p
                    if w != 1:
                        continue                                     # full relations only
                    o, a = model_omega(math.log(abs(v)), ps, rs)
                    meas.append(om); pred.append(o); alphas.append(a); signs.append(v < 0); svals.append(at["s"])
        meas, pred = np.array(meas), np.array(pred)
        sl, ic = np.polyfit(pred, meas, 1)
        r2 = 1 - ((meas - (ic + sl * pred)) ** 2).sum() / ((meas - meas.mean()) ** 2).sum()
        o = {"full_relations": len(meas), "measured_omega_mean": float(meas.mean()), "model_omega_mean": float(pred.mean()),
             "mean_miss": float((meas - pred).mean()), "fit": [float(ic), float(sl)], "r2": float(r2),
             "alpha_median": float(np.median(alphas)), "sign_share": float(np.mean(signs)), "s_mean": float(np.mean(svals)),
             "touched_measured": float(meas.mean() + np.mean(signs) + np.mean(svals)),
             "touched_model": float(pred.mean() + np.mean(signs) + np.mean(svals))}
        out[bits] = o
        print(f"{bits} bits ({o['full_relations']} full relations, 6 numbers): distinct base primes of |v| measured {o['measured_omega_mean']:.2f}, "
              f"model {o['model_omega_mean']:.2f} (miss {o['mean_miss']:+.2f}; measured = {ic:.2f} + {sl:.2f} x model, R^2 {r2:.2f}; alpha median "
              f"{o['alpha_median']:.2f}); + sign {o['sign_share']:.2f} + A-primes {o['s_mean']:.2f}: touched entries per full relation measured "
              f"{o['touched_measured']:.2f}, model {o['touched_model']:.2f}", flush=True)
    json.dump(out, open("omega_model.json", "w"), indent=1)
