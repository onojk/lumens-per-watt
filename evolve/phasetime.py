"""Phase-level wall-clock check (NOTES.md, "Phase-level wall-clock check"): lampcore --phasetime on all map
numbers per size, new reference genes as qs alone, with and without re-sieve, pinned to one P-core.
Per region: overhead-corrected ns, priced ruint cost, ns per priced unit, and its ratio to three anchors (NOTES.md,
"Step 5"): (A) the median region; (B) the time-weighted mean, total ns / total priced units (the materiality rule's
anchor since the stage-1 stop: a region flagged at ratio_B > 1.5 stops a run only if time share x (ratio_B - 1) >= 1%);
(C) the calibrated clean multiply, 27.3 ns per ruint unit (information).
  python3 phasetime.py [lpbreak] -> phasetime.json (phasetime_lpbreak.json), stdout
With lpbreak, LAMPCORE_LPBREAK=1 also times four sub-regions inside lp_ledger ("lp:copy", "lp:hash", "lp:comb",
"lp:add"); they are excluded from the anchors and shares and reported as a breakdown of lp_ledger.
"""
import json, os, subprocess, sys
LPB = len(sys.argv) > 1 and sys.argv[1] == "lpbreak"
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, optypes
import fastlamps
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()["ruint"]
out = {}
for bits in SS.SIZES:
    nums = S2.map_nums(bits)
    nr = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    out[bits] = {}
    for name, g in (("new ref", nr), ("new ref + re-sieve", dict(nr, confirm="resieve"))):
        text = json.dumps([g]) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
        env = dict(os.environ, LAMPCORE_LPBREAK="1") if LPB else os.environ
        res = subprocess.run(["taskset", "-c", "2", fastlamps.BIN, "--phasetime"], input=text, capture_output=True, text=True, check=True, env=env)
        lines = [json.loads(l) for l in res.stderr.splitlines() if l.startswith("{")]
        over = lines[0]["overhead_ns_per_region"]
        recs = lines[1:]
        names = recs[0]["regions"]
        ns = np.sum([r["ns"] for r in recs], axis=0).astype(float)
        calls = np.sum([r["calls"] for r in recs], axis=0).astype(float)
        types = np.sum([r["types"] for r in recs], axis=0)
        ns_c = ns - calls * over
        priced = np.array([sum(PR.get(t, 0) * types[i][j] for j, t in enumerate(optypes.TYPE_ORDER) if types[i][j]) for i in range(len(names))])
        per = np.where(priced > 0, ns_c / np.maximum(priced, 1e-9), np.nan)
        live = [i for i in range(len(names)) if priced[i] > 0 and calls[i] > 0 and not names[i].startswith("lp:")]
        subs = [i for i in range(len(names)) if names[i].startswith("lp:") and calls[i] > 0]
        med = float(np.median(per[live]))
        wmean = float(ns_c[live].sum() / priced[live].sum())
        CAL = 27.3
        rows = {}
        for i in range(len(names)):
            sh = float(ns_c[i] / ns_c[live].sum()) if i in live else 0.0
            rb = float(per[i] / wmean) if i in live else None
            rows[names[i]] = {"ns_per_number": ns_c[i] / len(nums), "priced_ruint_per_number": priced[i] / len(nums),
                              "ns_per_priced_unit": float(per[i]) if i in live else None, "ratio_to_median": float(per[i] / med) if i in live else None,
                              "ratio_B": rb, "ratio_C": float(per[i] / CAL) if i in live else None, "time_share": sh,
                              "materiality_B": sh * (rb - 1) if rb is not None else None}
        lpi = names.index("lp_ledger")
        for i in subs:
            rows[names[i]].update({"ns_per_priced_unit": float(ns_c[i] / priced[i]) if priced[i] > 0 else None,
                                   "share_of_lp_ledger": float(ns_c[i] / ns_c[lpi]), "calls_per_number": calls[i] / len(nums)})
        out[bits][name] = {"overhead_ns_per_region": over, "median_ns_per_priced_unit": med, "weighted_ns_per_priced_unit": wmean, "regions": rows}
        print(f"{bits} bits, {name}: overhead {over:.1f} ns/region; anchors: (A) median {med:.1f}, (B) time-weighted {wmean:.1f}, "
              f"(C) calibrated multiply {CAL} ns per priced ruint unit", flush=True)
        for i in live:
            r = rows[names[i]]
            flag = ""
            if r["ratio_B"] > 1.5:
                flag = f"  FLAG B ({r['materiality_B'] * 100:.2f}%{' STOP' if r['materiality_B'] >= 0.01 else ', under 1%'})"
            print(f"   {names[i]:10s} {r['ns_per_number']:12,.0f} ns/number  priced {r['priced_ruint_per_number']:10,.1f}  {r['ns_per_priced_unit']:7.1f} ns/unit  "
                  f"A x{r['ratio_to_median']:.2f}  B x{r['ratio_B']:.2f}  C x{r['ratio_C']:.2f}  time share {r['time_share']:.3f}{flag}", flush=True)
        for i in subs:
            r = rows[names[i]]
            print(f"      {names[i]:9s} {r['ns_per_number']:12,.0f} ns/number  priced {r['priced_ruint_per_number']:10,.1f}  "
                  + (f"{r['ns_per_priced_unit']:7.1f} ns/unit  " if r["ns_per_priced_unit"] else "  (unpriced)  ")
                  + f"{r['share_of_lp_ledger'] * 100:5.1f}% of lp_ledger  ({r['calls_per_number']:.0f} calls/number)", flush=True)
json.dump(out, open("phasetime_lpbreak.json" if LPB else "phasetime.json", "w"), indent=1)
