"""Checks opclass/linemap.tsv: its ranges tile every line of every lampcore/src/*.rs exactly once, and every class is
a TYPE_ORDER type or one of the named buckets. Run from the repo root: python3 opclass/check_map.py"""
import glob, sys
sys.path.insert(0, "evolve")
from optypes import TYPE_ORDER
OK = set(TYPE_ORDER) | {"meter", "uncharged:card", "uncharged:harness", "@caller", "decl"}
rows = [l.rstrip("\n").split("\t") for l in open("opclass/linemap.tsv") if l.strip() and not l.startswith("#")]
bad = 0
for f in sorted(glob.glob("lampcore/src/*.rs")):
    n = sum(1 for _ in open(f))
    cover = [0] * (n + 1)
    for r in rows:
        if r[0] == f:
            a, b = int(r[1]), int(r[2])
            for i in range(a, b + 1):
                if 1 <= i <= n:
                    cover[i] += 1
                else:
                    print(f"{f}: range {a}-{b} past the end ({n})"); bad += 1
    gaps = [i for i in range(1, n + 1) if cover[i] == 0]
    over = [i for i in range(1, n + 1) if cover[i] > 1]
    print(f"{f}: {n} lines, uncovered {len(gaps)}, covered twice {len(over)}" + (f" (first {gaps[:5]} {over[:5]})" if gaps or over else ""))
    bad += len(gaps) + len(over)
cls = {r[3] for r in rows}
print("classes used:", sorted(cls))
print("unknown classes:", sorted(cls - OK) or "none")
print("TYPE_ORDER types with no line:", [t for t in TYPE_ORDER if t not in cls])
bad += len(cls - OK)
print("OK" if bad == 0 else f"FAIL ({bad})")
sys.exit(1 if bad else 0)
