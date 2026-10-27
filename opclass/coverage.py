"""Coverage check before counting (procedure, section 4): runs the frozen release binary with --types on every input
and prints each run's op counts by class and the totals. Counts only: no Ir, no prices.
Run from the repo root: python3 opclass/coverage.py > opclass/coverage.out"""
import json, subprocess, sys
sys.path.insert(0, "evolve")
from optypes import TYPE_ORDER
man = json.load(open("opclass/inputs.json"))
tot = dict.fromkeys(TYPE_ORDER, 0)
for r in man["runs"]:
    out = subprocess.run(["opclass/bin/lampcore-release", "--types"], stdin=open(f"opclass/inputs/{r['run']}.in"),
                         capture_output=True, text=True, check=True).stdout
    s = dict.fromkeys(TYPE_ORDER, 0)
    for line in out.splitlines():
        for t, x in zip(TYPE_ORDER, line.split(" T ")[1].split()):
            s[t] += int(x)
    for t in TYPE_ORDER:
        tot[t] += s[t]
    print(r["run"], " ".join(f"{t}={v}" for t, v in s.items() if v))
print("TOTAL", " ".join(f"{t}={v}" for t, v in tot.items()))
print("classes with zero ops:", [t for t in TYPE_ORDER if tot[t] == 0], "(setup_full and confirm_full: charged by no card)")
