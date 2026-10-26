"""Word-price calibration and audit-op prices (NOTES.md, "Word-price calibration and the audit ops"):
from three `opbench --audit` runs on a P-core (taskset -c 2), the median per op of ns per op, its price
as a ratio to the 84-bit multiply (ruint chain; Montgomery chain), and its ratio to the clean and the old
sieve update. Also the roots-per-update ratio: the benchmark's prime set against the card's per size
(slackrep traces: Gray-code updates are one per root per switch; sieve updates from qs_counts).
  python3 audit_price.py R1 R2 R3 -> stdout, audit_price.json
"""
import sys, json, statistics
runs = [[json.loads(l) for l in open(p)] for p in sys.argv[1:]]
names = [d["name"] for d in runs[0] if "ns_median" in d]
ns = {nm: statistics.median(next(d["ns_median"] for d in r if d.get("name") == nm) for r in runs) for nm in names}
geo = next(d for d in runs[0] if d.get("name") == "sieve update")
cal = json.load(open("calibrate.json"))
def cur(ref, t):
    return sorted(cal["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1]
out = {"ns": ns, "prices": {}}
print(f"benchmark geometry: B {geo['B']}, M {geo['M']}, width {geo['width']}, F {geo['F']}, roots per update {geo['roots_per_update']:.4f}")
for ref in ("ruint", "montgomery"):
    t = ns[f"mulmod {ref} chain"]
    out["prices"][ref] = {nm: ns[nm] / t for nm in names}
    print(f"{ref}: 84-bit multiply {t:.3f} ns; current sieve_update price {cur(ref, 'sieve_update'):.4f}")
    for nm in names:
        print(f"   {nm:52s} {ns[nm]:8.3f} ns  price {ns[nm] / t:.4f}  x clean sieve update {ns[nm] / ns['sieve update clean']:.2f}")
d = json.load(open("slackrep.json"))
print("card's roots per update (one Gray-code root update per root per switch / sieve updates), tuned slack:")
for b, v in d.items():
    k = [s for s in v if s not in ("1.0", "1.5", "2.0", "2.5")][0]
    r = v[k]
    print(f"   {b}: {r['gray_updates'] / r['types']['sieve_update']:.4f}")
json.dump(out, open("audit_price.json", "w"), indent=1)
