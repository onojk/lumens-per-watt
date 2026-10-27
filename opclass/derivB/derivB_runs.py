#!/usr/bin/env python3
"""derivB: run every inputs.json run of lampcore-debug1 --types under callgrind (after hash checks)."""
import hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

REPO = "/home/onojk123/lumens-per-watt"
D = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(D, "raw")
os.makedirs(RAW, exist_ok=True)
BIN_SHA = {"lampcore-debug1": "b5b8dc6aad3d24a7a9f55b60bec9cca033852392c3ce781622ae02c3e202f332",
           "lampcore-release": "1505efbffb20002326753d23a668d1c15f77a53d2b5577825a631330ca855a79"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


for b, h in BIN_SHA.items():
    assert sha(f"{REPO}/opclass/bin/{b}") == h, b
runs = json.load(open(f"{REPO}/opclass/inputs.json"))["runs"]
for r in runs:
    assert sha(f"{REPO}/opclass/inputs/{r['run']}.in") == r["sha256"], r["run"]
print("hashes ok", flush=True)


def one(r):
    name = r["run"]
    out = os.path.join(RAW, name)
    if os.path.exists(out + ".done"):
        return name, "cached"
    with open(f"{REPO}/opclass/inputs/{name}.in", "rb") as fin, open(out + ".stdout", "wb") as fo, \
            open(out + ".vg", "wb") as fe:
        rc = subprocess.call(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no",
                              "--compress-pos=no", f"--callgrind-out-file={out}.cg",
                              f"{REPO}/opclass/bin/lampcore-debug1", "--types"], stdin=fin, stdout=fo, stderr=fe)
    if rc == 0:
        open(out + ".done", "w").write("ok\n")
    return name, rc


par = int(sys.argv[1]) if len(sys.argv) > 1 else 3
order = sorted(runs, key=lambda r: -os.path.getsize(f"{REPO}/opclass/inputs/{r['run']}.in") - (10**6 if r["run"] == "C_sq" else 0))
with ThreadPoolExecutor(par) as ex:
    for name, rc in ex.map(one, order):
        print(name, rc, flush=True)
print("all done", flush=True)
