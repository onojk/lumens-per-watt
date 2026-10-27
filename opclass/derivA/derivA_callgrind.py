#!/usr/bin/env python3
"""derivA: verify hashes, then run every input of opclass/inputs.json under callgrind (lampcore-debug1 --types)."""
import hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
REPO = "/home/onojk123/lumens-per-watt"
D = os.path.dirname(os.path.abspath(__file__))
BIN_SHA = {"opclass/bin/lampcore-release": "1505efbffb20002326753d23a668d1c15f77a53d2b5577825a631330ca855a79",
           "opclass/bin/lampcore-debug1": "b5b8dc6aad3d24a7a9f55b60bec9cca033852392c3ce781622ae02c3e202f332"}
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
for p, h in BIN_SHA.items():
    assert sha(os.path.join(REPO, p)) == h, p
runs = json.load(open(os.path.join(REPO, "opclass/inputs.json")))["runs"]
for r in runs:
    assert sha(os.path.join(REPO, "opclass/inputs", r["run"] + ".in")) == r["sha256"], r["run"]
print("hashes ok: 2 binaries,", len(runs), "inputs", flush=True)
def go(r):
    name = r["run"]
    cg = os.path.join(D, "raw", name + ".cg")
    if os.path.exists(cg) and os.path.exists(os.path.join(D, "raw", name + ".done")):
        return name, "cached"
    with open(os.path.join(REPO, "opclass/inputs", name + ".in")) as fi, \
         open(os.path.join(D, "raw", name + ".stdout"), "w") as fo, open(os.path.join(D, "raw", name + ".vglog"), "w") as fe:
        rc = subprocess.run(["valgrind", "--tool=callgrind", "--dump-instr=yes", "--compress-strings=no",
                             "--compress-pos=no", "--callgrind-out-file=" + cg,
                             os.path.join(REPO, "opclass/bin/lampcore-debug1"), "--types"],
                            stdin=fi, stdout=fo, stderr=fe).returncode
    assert rc == 0, (name, rc)
    open(os.path.join(D, "raw", name + ".done"), "w").write("ok\n")
    return name, "ok"
order = sorted(runs, key=lambda r: -(10**6 if r["run"] == "C_sq" else 0) - os.path.getsize(os.path.join(REPO, "opclass/inputs", r["run"] + ".in")))
with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as ex:
    for name, st in ex.map(go, order):
        print(name, st, flush=True)
