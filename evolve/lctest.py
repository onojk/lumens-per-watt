"""Step 7 (NOTES.md, "Step 7 added"; protocol and design point written before this ran): the L test, a gene test with
no code change.

  7b  X3 on the card: the share of single large-prime partials never combined by completion (their q seen once),
      from Python traces (the card's cofactors recomputed from the traced candidates, as in lpdist), new reference
      genes, 84 and 96 bits, 12 map numbers per size (two per band).
  7c  card runs on all map numbers (the step-5 sets), per size: the reference against
        (a) lc changed only (L / B = 12; at 96 also 8) - the test as specified, scored;
        (b) the same lc with tc raised so the slack tc + lc - 1 is unchanged - information (L only).
      Per configuration: polynomials to completion (sieve_scan / width), stored partials and combinations per
      number (lampcore --phasetime with LAMPCORE_LPBREAK=1: lp:hash calls are partials looked up, lp:comb calls
      combinations, stored = their difference; counts are identical with the timers on or off), priced qs per
      number (mean, median, mean of the slowest decile; official / ruint / Montgomery), wall-clock ns per number
      (a run without the sub-timers; total and lp_ledger and confirm), and the per-partial price in sieve
      positions: lp_ledger's priced (and wall) cost per stored-or-combined partial over the sieve region's priced
      (and wall) cost per sieve position.
  python3 lctest.py -> lctest.json, stdout
"""
import json, math, os, subprocess
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many
from ledger import Charger, Ledger

sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
PT = ("official", "ruint", "montgomery")

def ref(bits):
    return dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")

def bnd(N, g):
    lnN = math.log(N)
    return max(30, int(g["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))

def configs(bits):
    g = ref(bits)
    nums = S2.map_nums(bits)
    B = bnd(nums[0][0], g)                     # the card's B at this size (map numbers share the bit length)
    out = {"reference": g}
    for r in ((12, 8) if bits == 96 else (12,)):
        lc = 1 + math.log(r) / math.log(B)
        out[f"(a) L/B {r}"] = dict(g, lc=lc)
        out[f"(b) L/B {r}, slack kept"] = dict(g, lc=lc, tc=g["tc"] + (g["lc"] - lc))
    return out, B

def cost(t, Pn):
    t = {k: v for k, v in t.items() if v}
    return float(sum(t.values())) if Pn == "official" else float(sum(PR[Pn][k] * v for k, v in t.items()))

def phasetime(g, nums, lpb, svb=False):
    """lampcore --phasetime on core 2, means per number per region: ns (less the per-region overhead), ruint, calls.
    lpb: the lp_ledger sub-regions (LAMPCORE_LPBREAK=1); svb: the sieve sub-regions (LAMPCORE_SIEVEBREAK=1), each
    with "units", the sieve_update and word ops it would carry (the sieve region charges them once at its end)."""
    text = json.dumps([g]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    env = {k: v for k, v in os.environ.items() if k not in ("LAMPCORE_LPBREAK", "LAMPCORE_SIEVEBREAK")}
    if lpb:
        env["LAMPCORE_LPBREAK"] = "1"
    if svb:
        env["LAMPCORE_SIEVEBREAK"] = "1"
    res = subprocess.run(["taskset", "-c", "2", fastlamps.BIN, "--phasetime"], input=text, capture_output=True, text=True, check=True, env=env)
    lines = [json.loads(l) for l in res.stderr.splitlines() if l.startswith("{")]
    over = lines[0]["overhead_ns_per_region"]
    recs = lines[1:]
    names = recs[0]["regions"]
    ns = np.sum([r["ns"] for r in recs], axis=0).astype(float)
    calls = np.sum([r["calls"] for r in recs], axis=0).astype(float)
    types = np.sum([r["types"] for r in recs], axis=0)
    ns_c = ns - calls * over
    pr = np.array([sum(PR["ruint"].get(t, 0) * types[i][j] for j, t in enumerate(optypes.TYPE_ORDER) if types[i][j]) for i in range(len(names))])
    n = len(nums)
    out = {nm: {"ns": ns_c[i] / n, "priced": pr[i] / n, "calls": calls[i] / n} for i, nm in enumerate(names)}
    if svb:
        su = np.sum([r["sv_units"] for r in recs], axis=0)
        for i, nm in enumerate(("sv:zero", "sv:free2", "sv:prime", "sv:power", "sv:tail")):
            out[nm]["units"] = su[i] / n
    return out

def x3(bits, g, sample):
    """Share of partials whose q is seen once by completion, and partials / stored per number (Python traces)."""
    single = parts = 0
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        qs.lamp_qs(N, g, m)
        tr = qs.TRACE; qs.TRACE = None
        B = bnd(N, g)
        L = B ** min(3.0, max(1.0, g["lc"]))
        for at in tr["attempts"]:
            if "lp" not in at:
                continue
            led = Ledger(N, at["k"], B, Charger(lamps.Meter(1 << 60), None), None)
            led.build_base()
            cnt = {}
            for v in at["cands"]:
                v = abs(v)
                if v == 0:
                    continue
                for p in led.base[1:]:
                    while v % p == 0:
                        v //= p
                if 1 < v < L:
                    cnt[v] = cnt.get(v, 0) + 1
            parts += sum(cnt.values())
            single += sum(1 for c in cnt.values() if c == 1)
    return single / parts if parts else None, parts / len(sample)

if __name__ == "__main__":
    out = {}
    for bits in (84, 96):
        nums = S2.map_nums(bits)
        rows = SS.corrected_map_rows(bits)
        sample = []
        for b in sorted({r["band"] for r in rows}):
            sample += [t for t, r in zip(nums, rows) if r["band"] == b][:2]
        cf, B = configs(bits)
        out[bits] = {"B": B, "configs": {}}
        for name, g in cf.items():
            rs = run_many([g], nums, P.QS_CAP, types=True)
            assert all(r[1] is not None for r in rs), "a miss"
            width = [2 * max(64, int(g["mc"] * bnd(N, g))) + 1 for N, _, _ in nums]
            polys = np.array([r[4]["sieve_scan"] / w for r, w in zip(rs, width)])
            c = {Pn: np.array([cost(r[4], Pn) for r in rs]) for Pn in PT}
            lpb = phasetime(g, nums, True)
            wall = phasetime(g, nums, False)
            looked, comb = lpb["lp:hash"]["calls"], lpb["lp:comb"]["calls"]
            pos = float(np.mean([p * w for p, w in zip(polys, width)]))      # sieve positions per number
            tot_ns = sum(v["ns"] for k, v in wall.items() if not k.startswith("lp:"))
            tot_pr = sum(v["priced"] for k, v in wall.items() if not k.startswith("lp:"))
            rec = {"lc": g["lc"], "tc": g["tc"], "polys_mean": float(polys.mean()), "polys_median": float(np.median(polys)),
                   "partials_looked_up": looked, "stored_partials": looked - comb, "combinations": comb,
                   "priced": {Pn: {"mean": float(v.mean()), "median": float(np.median(v)),
                                   "slowest_decile_mean": float(np.sort(v)[-max(1, len(v) // 10):].mean())} for Pn, v in c.items()},
                   "wall_ns": {"total": tot_ns, "lp_ledger": wall["lp_ledger"]["ns"], "confirm": wall["confirm"]["ns"], "sieve": wall["sieve"]["ns"]},
                   "weighted_ns_per_priced_unit": tot_ns / tot_pr,
                   "per_partial_price_sieve_positions": {
                       "priced": (wall["lp_ledger"]["priced"] / looked) / (wall["sieve"]["priced"] / pos) if looked else None,
                       "wall": (wall["lp_ledger"]["ns"] / looked) / (wall["sieve"]["ns"] / pos) if looked else None}}
            if name in ("reference", "(a) L/B 12"):
                rec["x3_never_combined"], rec["partials_per_number_subset"] = x3(bits, g, sample)
                rec["x3_subset"] = len(sample)
            out[bits]["configs"][name] = rec
            pp = rec["per_partial_price_sieve_positions"]
            print(f"{bits} bits, {name} (lc {g['lc']:.4f}, tc {g['tc']:.4f}): polynomials {rec['polys_mean']:.2f} (median {rec['polys_median']:.1f}); "
                  f"partials looked up {looked:.0f}, stored {looked - comb:.0f}, combinations {comb:.1f}; ruint mean {rec['priced']['ruint']['mean']:,.0f}, "
                  f"median {rec['priced']['ruint']['median']:,.0f}, slowest decile {rec['priced']['ruint']['slowest_decile_mean']:,.0f}; "
                  f"official {rec['priced']['official']['mean']:,.0f}, Montgomery {rec['priced']['montgomery']['mean']:,.0f}; wall {tot_ns / 1e3:,.1f} us "
                  f"(lp_ledger {wall['lp_ledger']['ns'] / 1e3:,.1f}, confirm {wall['confirm']['ns'] / 1e3:,.1f}); per-partial price "
                  f"{pp['priced']:.1f} (priced) / {pp['wall']:.1f} (wall) sieve positions"
                  + (f"; X3 never-combined {rec['x3_never_combined']:.3f} ({rec['x3_subset']} numbers, {rec['partials_per_number_subset']:.0f} partials per number)" if "x3_never_combined" in rec else ""), flush=True)
    json.dump(out, open("lctest.json", "w"), indent=1)
