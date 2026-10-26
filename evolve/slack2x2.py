"""The scored 2x2 slack retune (NOTES.md, "The scored 2x2 slack retune: protocol"; written before this script ran).

Genome: each size's new reference qs genes (Track R final genes, qs alone, kset sf32), lc fixed, tc = s + 1 - lc for
slack s on the 0.1 grid 1.6-2.8. Re-sieve off (13 configs) and on at p0 in {30, 60, 100, 200, 400, 700, 1000, 1500}
(104 configs). Every run's per-type counts are priced three ways (axes) under each pricing:
  fc    the current card's prices (fully corrected);
  gray  pre-Gray type prices with only the Gray-code update re-typed to word (the scoring axis of G-slack2x2);
  old   pre-Gray type prices.
Pre-Gray type prices on today's counts: word and sieve_update at the old word price (calibrated sieve_update),
setup_gray at setup_small ("old") or the old word price ("gray"), hash at lp_small, sort_cmp and f64_log at
setup_small, f64_div at setup_full (a full multiply). Today's counts include later meter corrections, so "old" is
"pre-Gray prices on today's counts", not the historical card.

  python3 slack2x2.py map     -> slack2x2_map.json   (all map numbers; best cells, shift intervals, p0, winner)
  python3 slack2x2.py alpha   -> slack2x2_alpha.json (alpha_filed per slack, Python traces, 3 top-band map numbers)
  python3 slack2x2.py sealed  -> slack2x2_sealed.json (winner vs the current reference on fresh numbers
                                                       9440000 + 100 pb + bits, 80 per band; gate; paired bootstrap)
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, oracle
from fastlamps import run_many

PR3 = ("official", "ruint", "montgomery")
SLACKS = [round(1.6 + 0.1 * i, 1) for i in range(13)]
P0S = (30, 60, 100, 200, 400, 700, 1000, 1500)
AXES = ("old", "gray", "fc")
sealed = json.load(open("sizescale_k_sealed.json"))
cal = json.load(open("calibrate.json"))
NB = 10000

def med(ref, t):
    return sorted(cal["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1]

def axis_prices():
    fc = optypes.prices()
    out = {"fc": fc}
    for ax in ("old", "gray"):
        pr = {"official": None}
        for ref in ("ruint", "montgomery"):
            d = dict(fc[ref])
            ow = med(ref, "sieve_update")
            d["word"] = d["sieve_update"] = ow
            d["setup_gray"] = med(ref, "setup_small") if ax == "old" else ow
            d["hash"] = med(ref, "lp_small")
            d["sort_cmp"] = d["f64_log"] = med(ref, "setup_small")
            d["f64_div"] = med(ref, "setup_full")
            pr[ref] = d
        out[ax] = pr
    return out
AXP = axis_prices()

def ref_genes(bits):
    return dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")

def configs(bits):
    g0 = ref_genes(bits)
    out = []
    for s in SLACKS:
        g = dict(g0, tc=s + 1 - g0["lc"])
        out.append(("off", s, None, g))
        for p0 in P0S:
            out.append(("on", s, p0, dict(g, confirm="resieve", p0=p0)))
    return out

def price(t, ax, Pn):
    t = {k: v for k, v in t.items() if v}
    return float(sum(t.values())) if Pn == "official" else float(sum(AXP[ax][Pn][k] * v for k, v in t.items()))

def run_cost(g, nums):
    rs = run_many([g], nums, P.QS_CAP, types=True)
    assert all(r[1] is not None for r in rs), "a miss"
    return {(ax, Pn): np.array([price(r[4], ax, Pn) for r in rs]) for ax in AXES for Pn in PR3}

def band_weights(band, rng, nb=NB):
    """Within-band resampling weights: (nb, n) counts."""
    band = np.asarray(band)
    W = np.zeros((nb, len(band)))
    for b in np.unique(band):
        idx = np.where(band == b)[0]
        draw = rng.integers(0, len(idx), size=(nb, len(idx)))
        for j in range(len(idx)):
            np.add.at(W, (np.arange(nb), idx[draw[:, j]]), 1)
    return W

def ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]

def map_mode():
    out = {}
    rng = np.random.default_rng(2026)
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        band = [r["band"] for r in SS.corrected_map_rows(bits)]
        cf = configs(bits)
        costs = [run_cost(g, nums) for (_, _, _, g) in cf]
        C = {k: np.stack([c[k] for c in costs], axis=1) for k in costs[0]}           # n x configs
        ref = run_cost(ref_genes(bits), nums)
        isoff = np.array([c[0] == "off" for c in cf])
        sl = np.array([c[1] for c in cf]); p0 = np.array([c[2] or 0 for c in cf])
        W = band_weights(band, rng)
        Wn = W / W.sum(axis=1, keepdims=True)
        o = {"n": len(nums), "cells": {}, "p0": {}, "configs": [[c[0], c[1], c[2]] for c in cf]}
        mean = {k: v.mean(axis=0) for k, v in C.items()}
        boot = {k: Wn @ v for k, v in C.items()}                                    # nb x configs
        for ax in AXES:
            for Pn in PR3:
                k = (ax, Pn)
                cell = {}
                for side, mask in (("off", isoff), ("on", ~isoff)):
                    idx = np.where(mask)[0]
                    j = idx[np.argmin(mean[k][idx])]
                    jb = idx[np.argmin(boot[k][:, idx], axis=1)]
                    cell[side] = {"slack": float(sl[j]), "p0": int(p0[j]) or None, "cost": float(mean[k][j]),
                                  "slack_boot": sl[jb]}
                # shifts against the off cell of the "old" axis (off/no) under the same pricing
                k0 = ("old", Pn)
                idx = np.where(isoff)[0]
                s00 = sl[idx[np.argmin(boot[k0][:, idx], axis=1)]]
                for side in ("off", "on"):
                    sh = cell[side]["slack_boot"] - s00
                    cell[side]["shift_vs_offno"] = float(cell[side]["slack"] - sl[idx[np.argmin(mean[k0][idx])]])
                    cell[side]["shift_ci"] = ci(sh)
                    sh2 = cell[side]["slack_boot"] - cell["off"]["slack_boot"]
                    cell[side]["shift_vs_off_same_axis_ci"] = ci(sh2)
                    del cell[side]["slack_boot"]
                cell["resieve_saving"] = 1 - cell["on"]["cost"] / cell["off"]["cost"]
                o["cells"][f"{ax} {Pn}"] = cell
        # Track R (worst of three, fc prices) and Track M, against the current reference
        rmean = {Pn: ref[("fc", Pn)].mean() for Pn in PR3}
        trR = np.max([mean[("fc", Pn)] / rmean[Pn] for Pn in PR3], axis=0)
        trM = mean[("fc", "montgomery")] / rmean["montgomery"]
        for name, f in (("R", trR), ("M", trM)):
            for side, mask in (("off", isoff), ("on", ~isoff)):
                idx = np.where(mask)[0]
                j = idx[np.argmin(f[idx])]
                o["cells"][f"track {name} {side}"] = {"slack": float(sl[j]), "p0": int(p0[j]) or None, "fitness": float(f[j])}
            o["cells"][f"track {name}"] = {"resieve_saving": 1 - o["cells"][f"track {name} on"]["fitness"] / o["cells"][f"track {name} off"]["fitness"]}
        # p0 at the best on-slack, per criterion (fc)
        for name, f in (("ruint", mean[("fc", "ruint")]), ("montgomery", mean[("fc", "montgomery")]),
                        ("official", mean[("fc", "official")]), ("track R", trR), ("track M", trM)):
            idx = np.where(~isoff)[0]
            j = idx[np.argmin(f[idx])]
            at = np.where((~isoff) & (sl == sl[j]))[0]
            o["p0"][name] = {"best_slack": float(sl[j]), "best_p0": int(p0[j]),
                             "by_p0": {int(p0[i]): float(f[i]) for i in at}}
        o["means"] = {f"{ax} {Pn}": mean[(ax, Pn)].tolist() for ax in AXES for Pn in PR3}
        o["means"]["track R"] = trR.tolist(); o["means"]["track M"] = trM.tolist()
        jw = int(np.argmin(trR))
        o["winner"] = {"side": cf[jw][0], "slack": cf[jw][1], "p0": cf[jw][2], "track_R_fitness_map": float(trR[jw]),
                       "genes": cf[jw][3]}
        o["reference_slack"] = round(ref_genes(bits)["tc"] + ref_genes(bits)["lc"] - 1, 3)
        o["reference_cost"] = {f"{ax} {Pn}": float(ref[(ax, Pn)].mean()) for ax in AXES for Pn in PR3}
        out[bits] = o
        print(f"{bits} bits: winner {o['winner']['side']} slack {o['winner']['slack']} p0 {o['winner']['p0']} "
              f"Track R {o['winner']['track_R_fitness_map']:.4f} (map)", flush=True)
        for key, c in o["cells"].items():
            print(f"   {key}: {json.dumps(c, default=float)}", flush=True)
        for key, c in o["p0"].items():
            print(f"   p0 {key}: best slack {c['best_slack']} best p0 {c['best_p0']}; " +
                  " ".join(f"{k}:{v:.5g}" for k, v in c["by_p0"].items()), flush=True)
    json.dump(out, open("slack2x2_map.json", "w"), indent=1, default=float)

def alpha_mode():
    import qs, lamps
    from ledger import Charger, Ledger
    from scipy.optimize import minimize_scalar
    out = {}
    for bits in SS.SIZES:
        g0 = ref_genes(bits)
        rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
        top = max(r["band"] for r in rows)
        sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3]
        out[bits] = {}
        for s in SLACKS:
            g = dict(g0, tc=s + 1 - g0["lc"])
            ys, ws = [], []
            for N, _, _ in sample:
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                tr = qs.TRACE; qs.TRACE = None
                lnN = math.log(N); B = max(30, int(g0["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
                L = B ** g0["lc"]
                for at in tr["attempts"]:
                    led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
                    led.build_base()
                    for v in at["cands"]:
                        v = abs(v)
                        if v == 0:
                            continue
                        for p in led.base[1:]:
                            while v % p == 0:
                                v //= p
                        if 1 < v < L:
                            x = math.log(v) / math.log(B)
                            a = 1.0 + 0.2 * math.floor((x - 1.0) / 0.2)
                            b = min(a + 0.2, g0["lc"])
                            ys.append((math.log(v) - a * math.log(B), (b - a) * math.log(B)))
            # within a bin, ln q - ln B^a = y in [0, w), density ~ q^(1 - alpha) dq/q... in y: ~ e^{(1 - alpha) y}
            ys = np.array(ys)
            def nll(alpha):
                t = 1.0 - alpha
                if abs(t) < 1e-9:
                    return float(np.sum(np.log(ys[:, 1])))
                return -float(np.sum(t * ys[:, 0] - np.log((np.exp(t * ys[:, 1]) - 1) / t)))
            r = minimize_scalar(nll, bounds=(-3, 6), method="bounded")
            out[bits][s] = {"alpha_filed": float(r.x), "filed": len(ys)}
            print(f"{bits} bits slack {s}: alpha_filed {r.x:.3f} ({len(ys)} filed q, 3 numbers)", flush=True)
    json.dump(out, open("slack2x2_alpha.json", "w"), indent=1)

def sealed_mode():
    mp = json.load(open("slack2x2_map.json"))
    out = {}
    rng = np.random.default_rng(2026)
    for bits in SS.SIZES:
        w = mp[str(bits)]["winner"]
        pop = SS.pop(bits, 80, 9440000)
        nums, band = [], []
        for pb, ns in pop.items():
            nums += ns; band += [pb] * len(ns)
        A = run_cost(w["genes"], nums); R = run_cost(ref_genes(bits), nums)
        W = band_weights(band, rng)
        Wn = W / W.sum(axis=1, keepdims=True)
        o = {"winner": {k: w[k] for k in ("side", "slack", "p0")}, "n": len(nums)}
        lr = {}
        for Pn in PR3:
            a, r = A[("fc", Pn)], R[("fc", Pn)]
            o[Pn] = {"winner": float(a.mean()), "reference": float(r.mean()), "ratio": float(a.mean() / r.mean()),
                     "ci": ci((Wn @ a) / (Wn @ r))}
            lr[Pn] = (Wn @ a) / (Wn @ r)
        rob = np.max([lr[Pn] for Pn in PR3], axis=0)
        o["robust"] = {"ratio": max(o[Pn]["ratio"] for Pn in PR3), "ci": ci(rob)}
        # gate: per band and pricing, 95% interval of mean cost / mean reference cost (resampled within band)
        bandarr = np.array(band); gate = "PASS"; worst = 0
        o["bands"] = {}
        for pb in sorted(set(band)):
            idx = np.where(bandarr == pb)[0]
            draw = rng.integers(0, len(idx), size=(NB, len(idx)))
            o["bands"][pb] = {}
            for Pn in PR3:
                a, r = A[("fc", Pn)][idx], R[("fc", Pn)][idx]
                bb = a[draw].mean(axis=1) / r[draw].mean(axis=1)
                lo, hi = ci(bb)
                o["bands"][pb][Pn] = {"ratio": float(a.mean() / r.mean()), "ci": [lo, hi]}
                worst = max(worst, a.mean() / r.mean())
                if lo > 1.5:
                    gate = "FAIL"
                elif hi > 1.5 and gate == "PASS":
                    gate = "BORDERLINE"
        o["gate"] = gate; o["worst_band_point"] = float(worst)
        o["adopt"] = bool(gate == "PASS" and o["robust"]["ci"][1] < 1.0)
        out[bits] = o
        print(f"{bits} bits: winner {o['winner']}; robust {o['robust']['ratio']:.4f} {o['robust']['ci']}; " +
              "; ".join(f"{Pn} {o[Pn]['ratio']:.4f} [{o[Pn]['ci'][0]:.4f}, {o[Pn]['ci'][1]:.4f}]" for Pn in PR3) +
              f"; gate {gate} (worst band point {worst:.3f}); adopt {o['adopt']}", flush=True)
        for pb, v in o["bands"].items():
            print(f"   band {pb}: " + "  ".join(f"{Pn[:4]} {v[Pn]['ratio']:.3f} [{v[Pn]['ci'][0]:.3f}, {v[Pn]['ci'][1]:.3f}]" for Pn in PR3), flush=True)
    json.dump(out, open("slack2x2_sealed.json", "w"), indent=1, default=float)

if __name__ == "__main__":
    {"map": map_mode, "alpha": alpha_mode, "sealed": sealed_mode}[ARGS[0]]()
