"""Before / after wall-clock comparison of phasetime runs (overnight stage A): the mean of replicate jsons per side,
per size and variant, for every region: ns per number before -> after, the change, and the after anchor-C ratio
(ns per priced ruint unit / 27.3).
  python3 wallcmp.py BEFORE1.json[,BEFORE2.json] AFTER1.json[,AFTER2.json] -> stdout
"""
import sys, json
import numpy as np
def load(arg):
    ds = [json.load(open(f)) for f in arg.split(",")]
    out = {}
    for b in ds[0]:
        for v in ds[0][b]:
            for r, x in ds[0][b][v]["regions"].items():
                if r.startswith("lp:") or x.get("ns_per_priced_unit") is None:
                    continue
                ns = float(np.mean([d[b][v]["regions"][r]["ns_per_number"] for d in ds]))
                out[(b, v, r)] = (ns, x["priced_ruint_per_number"])
    return out
bef, aft = load(sys.argv[1]), load(sys.argv[2])
for (b, v, r), (ns1, pr) in aft.items():
    ns0 = bef[(b, v, r)][0]
    print(f"{b} {v:20s} {r:10s} {ns0 / 1e3:9.1f} -> {ns1 / 1e3:9.1f} us ({(ns1 / ns0 - 1) * 100:+6.1f}%)  C after {ns1 / pr / 27.3:5.2f}")
