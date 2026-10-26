"""Step 3, part 1 (information): the sizes of the card's hash tables at the time of each hash op, from Python
traces (new reference genes, qs alone, re-sieve off; 12 map numbers per size: 2 from each of the first six bands
in map order, or all bands where fewer).
Tables: the large-prime table (lookup at its current size, then an insert on a miss) and the ledger's duplicate
sets (one probe-and-insert per relation offered: |u| set for full relations, the combined set for combined ones).
The op-time sizes follow from the trace's order of events: partial i is looked up at the size reached so far.
  python3 hashsize.py -> hashsize.json, stdout
"""
import json
import numpy as np
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
sealed = json.load(open("sizescale_k_sealed.json"))
out = {}
for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    bands = sorted({r["band"] for r in rows})
    sample = []
    for b in bands:
        sample += [t for t, r in zip(nums, rows) if r["band"] == b][:2]
    sample = sample[:12]
    lp_sizes, dup_sizes, finals = [], [], []
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        qs.lamp_qs(N, g, m)
        tr = qs.TRACE; qs.TRACE = None
        for at in tr["attempts"]:
            if "lp" not in at:
                continue
            lp = at["lp"]
            ins, comb, dup = lp["inserts"], lp["combos"], lp["dup"]
            # every partial: a lookup at the table's size so far; a miss inserts (size grows by one)
            # the order of hits and misses is not traced; sizes at lookup run 0..ins, hits spread over them
            nlook = ins + comb + dup
            lp_sizes += list(np.linspace(0, ins, nlook, endpoint=False)) if nlook else []
            nrel = len(at.get("rels", []))
            full = sum(1 for r in at.get("rels", []) if r[2] == 1)
            dup_sizes += list(range(full)) + list(range(nrel - full))
            finals.append({"lp_table": ins, "full_set": full, "combined_set": nrel - full})
    lp = np.array(lp_sizes); du = np.array(dup_sizes)
    o = {"lp_ops": len(lp), "lp_median": float(np.median(lp)), "lp_p90": float(np.percentile(lp, 90)), "lp_max": float(lp.max()),
         "dup_ops": len(du), "dup_median": float(np.median(du)), "dup_p90": float(np.percentile(du, 90)),
         "final_lp_table_median": float(np.median([f["lp_table"] for f in finals])),
         "final_lp_table_max": int(max(f["lp_table"] for f in finals)), "numbers": len(sample)}
    out[bits] = o
    print(f"{bits} bits ({len(sample)} numbers): large-prime table at lookup: median {o['lp_median']:.0f}, 90th pct {o['lp_p90']:.0f}, "
          f"max {o['lp_max']:.0f} ({o['lp_ops']} lookups); final table median {o['final_lp_table_median']:.0f}, max {o['final_lp_table_max']}; "
          f"ledger duplicate sets at probe: median {o['dup_median']:.0f}, 90th pct {o['dup_p90']:.0f} ({o['dup_ops']} probes)", flush=True)
json.dump(out, open("hashsize.json", "w"), indent=1)
