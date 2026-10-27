"""Step 9b (NOTES.md, "Step 9" and its amendment; predictions S9-1..S9-9 sealed before this ran): the capture funnel
on the card's own polynomials. Python traces with qs.TRACE_ARR (each polynomial's A, B, C, sieve array and threshold;
trace only), new reference genes, KS on, 8 map numbers per size at 84 and 96 (one per band, then the top band again).

At every sieve position x (|x| <= M) the residue g(x) = (A x + 2B) x + C is factored exactly over the whole base
(including 2 and A's primes; numpy int64, |g| < 2^62 asserted): a true full (cofactor 1) or a true 1LP partial
(cofactor q, 1 < q < L, L = B^lc < B^2, so q is prime). The funnel per class:
  true -> passed the sieve threshold (arr[x] >= T) -> processed by confirm (not cut off when the ledger filled; confirm
  is the exact full pass, so a processed candidate is classified exactly) -> filed: a partial is looked up in the
  large-prime table; a full is offered to the ledger, and rejected there only if |u| (u = A x + B) repeats.
Also: partials by log2(q/B) band; capture against log2(Qmax / |g(x)|) (Qmax = M sqrt(kN/2)); the sieve's under-count
(true log2 of the smooth part minus the sieve's accumulated value); per-A capture spread; realized A against the
target sqrt(2kN)/M; realized max |g| over Qmax; true fulls and partials per polynomial.
  python3 step9.py -> step9.json, stdout
"""
import json, math
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
from ledger import Charger, Ledger
from lctest import ref, bnd

QB = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 99)]

def sample(bits):
    nums = S2.map_nums(bits); rows = SS.corrected_map_rows(bits)
    bands = sorted({r["band"] for r in rows})
    out = [next(t for t, r in zip(nums, rows) if r["band"] == b) for b in bands]
    top = [t for t, r in zip(nums, rows) if r["band"] == bands[-1]]
    i = 1
    while len(out) < 8:
        out.append(top[i]); i += 1
    return out[:8]

def run_size(bits, g=None):
    g = g or ref(bits)
    qs.TRACE_ARR = True
    recs = {"full": [], "part": []}       # per true relation: dict of fields
    polys = 0
    a_ratio, gmax_ratio, by_a = [], [], []
    for N, p_, q_ in sample(bits):
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        qs.lamp_qs(N, g, m)
        tr = qs.TRACE; qs.TRACE = None
        B = bnd(N, g)
        L = B ** g["lc"]
        for at in tr["attempts"]:
            if "s1" not in at:
                continue
            k = at["k"]; kN = k * N
            led = Ledger(N, k, B, Charger(lamps.Meter(1 << 60), None), None); led.build_base()
            base = led.base[1:]
            ncand_total = len(at["cands"])
            ps = at["polys"]
            seen_u = set()
            for pi, po in enumerate(ps):
                if "A" not in po:
                    continue
                polys += 1
                A, Bv, C, arr, T, M = po["A"], po["B"], po["C"], po["arr"], po["T"], po["Mw"]
                c0 = po["c0"]
                c1 = ps[pi + 1]["c0"] if pi + 1 < len(ps) and "c0" in ps[pi + 1] else ncand_total
                processed = set(po["cand_pos"][:max(0, c1 - c0)])
                target = math.isqrt(2 * kN) / M
                Qmax = M * math.sqrt(kN / 2)
                a_ratio.append(math.log2(A / target))
                gv = [(A * int(x) + 2 * Bv) * int(x) + C for x in range(-M, M + 1)]
                assert max(abs(v) for v in gv) < (1 << 62)
                gmax_ratio.append(math.log2(max(abs(v) for v in gv) / Qmax))
                w = np.array([abs(v) for v in gv], dtype=np.int64)
                logs = np.zeros(len(w))
                for p in base:
                    while True:
                        mk = (w != 0) & (w % p == 0)
                        if not mk.any():
                            break
                        w[mk] //= p
                        logs[mk] += math.log2(p)
                n_ok = n_cap = 0
                for i0 in range(len(w)):
                    v = gv[i0]
                    if v == 0:
                        continue
                    cof = int(w[i0])
                    if cof == 1:
                        cls = "full"
                    elif cof < L:
                        cls = "part"
                    else:
                        continue
                    passed = float(arr[i0]) >= T
                    proc = passed and i0 in processed
                    u = A * (i0 - M) + Bv
                    filed = proc
                    if cls == "full" and proc:
                        if abs(u) in seen_u:
                            filed = False
                        seen_u.add(abs(u))
                    r = {"passed": passed, "proc": proc, "filed": filed,
                         "under": logs[i0] - float(arr[i0]), "uq": math.log2(Qmax / abs(v))}
                    if cls == "part":
                        r["qb"] = math.log2(cof / B)
                        n_ok += 1; n_cap += filed
                    recs[cls].append(r)
                if n_ok:
                    by_a.append(n_cap / n_ok)
    qs.TRACE_ARR = False
    return recs, polys, a_ratio, gmax_ratio, by_a

def frac(rs, key):
    return sum(r[key] for r in rs) / len(rs) if rs else float("nan")

if __name__ == "__main__":
    out = {}
    for bits in (84, 96):
        recs, polys, a_ratio, gmax_ratio, by_a = run_size(bits)
        o = {"polys": polys}
        for cls in ("full", "part"):
            rs = recs[cls]
            o[cls] = {"true": len(rs), "true_per_poly": len(rs) / polys, "passed": frac(rs, "passed"),
                      "processed_given_passed": (sum(r["proc"] for r in rs) / max(1, sum(r["passed"] for r in rs))),
                      "filed_given_processed": (sum(r["filed"] for r in rs) / max(1, sum(r["proc"] for r in rs))),
                      "end_to_end": frac(rs, "filed"),
                      "under_count": {"mean": float(np.mean([r["under"] for r in rs])), "median": float(np.median([r["under"] for r in rs])),
                                      "p90": float(np.percentile([r["under"] for r in rs], 90))},
                      "by_uq": {}}
            for lo in range(0, 12):
                sel = [r for r in rs if lo <= r["uq"] < lo + 1]
                if len(sel) >= 10:
                    o[cls]["by_uq"][lo] = {"n": len(sel), "passed": frac(sel, "passed"), "end_to_end": frac(sel, "filed")}
        o["part"]["by_qb"] = {}
        for lo, hi in QB:
            sel = [r for r in recs["part"] if lo <= r["qb"] < hi]
            o["part"]["by_qb"][f"{lo}-{hi}"] = {"n": len(sel), "passed": frac(sel, "passed"), "end_to_end": frac(sel, "filed")}
        sel = [r for r in recs["part"] if r["qb"] < 3]
        o["part"]["qb_lt_3"] = {"n": len(sel), "passed": frac(sel, "passed"), "end_to_end": frac(sel, "filed")}
        sel = [r for r in recs["part"] if r["qb"] < 4]
        o["part"]["qb_lt_4"] = {"n": len(sel), "passed": frac(sel, "passed"), "end_to_end": frac(sel, "filed")}
        o["a_vs_target_log2"] = {"mean": float(np.mean(a_ratio)), "sd": float(np.std(a_ratio)), "min": float(min(a_ratio)), "max": float(max(a_ratio))}
        o["gmax_over_qmax_log2"] = {"mean": float(np.mean(gmax_ratio)), "max": float(max(gmax_ratio))}
        o["per_A_partial_capture"] = {"n": len(by_a), "p10": float(np.percentile(by_a, 10)), "median": float(np.median(by_a)), "p90": float(np.percentile(by_a, 90))}
        out[bits] = o
        print(f"\n{bits} bits: {polys} polynomials", flush=True)
        for cls in ("full", "part"):
            c = o[cls]
            print(f"  {cls}: true {c['true']} ({c['true_per_poly']:.2f} per polynomial); passed threshold {c['passed']:.3f}; processed | passed "
                  f"{c['processed_given_passed']:.3f}; filed | processed {c['filed_given_processed']:.3f}; end to end {c['end_to_end']:.3f}; "
                  f"under-count mean {c['under_count']['mean']:.2f}, median {c['under_count']['median']:.2f}, p90 {c['under_count']['p90']:.2f} bits", flush=True)
            print("     by log2(Qmax/|g|): " + "  ".join(f"{k}: {v['passed']:.2f}/{v['end_to_end']:.2f} (n {v['n']})" for k, v in c["by_uq"].items()), flush=True)
        print("  partials by log2(q/B): " + "  ".join(f"{k}: passed {v['passed']:.3f}, end {v['end_to_end']:.3f} (n {v['n']})" for k, v in o["part"]["by_qb"].items()), flush=True)
        print(f"  partials log2(q/B) < 3: end to end {o['part']['qb_lt_3']['end_to_end']:.3f} (n {o['part']['qb_lt_3']['n']}); < 4: {o['part']['qb_lt_4']['end_to_end']:.3f}", flush=True)
        print(f"  A vs target, log2: mean {o['a_vs_target_log2']['mean']:+.3f}, sd {o['a_vs_target_log2']['sd']:.3f}, range {o['a_vs_target_log2']['min']:+.3f}..{o['a_vs_target_log2']['max']:+.3f}; "
              f"max |g| / Qmax, log2: mean {o['gmax_over_qmax_log2']['mean']:+.3f}, max {o['gmax_over_qmax_log2']['max']:+.3f}; per-A partial capture p10 / median / p90 "
              f"{o['per_A_partial_capture']['p10']:.2f} / {o['per_A_partial_capture']['median']:.2f} / {o['per_A_partial_capture']['p90']:.2f} ({o['per_A_partial_capture']['n']} polynomials)", flush=True)
    json.dump(out, open("step9.json", "w"), indent=1)
