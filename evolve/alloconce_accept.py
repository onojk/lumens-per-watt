"""Acceptance for allocate once per attempt (NOTES.md, "Cost note (before code): allocate once per attempt"). All map
numbers at 72, 84 and 96 (480 / 560 / 640): lampcore before (the release build with the A-prime fix, from f988aab, lampcore unchanged through 566f9a8: sha256
ef345913..., kept in Claude's scratch) against after (the release build of this commit): stdout byte-identical, with
and without --types (factor, ops, tests, hits, stage, k, all 30 type counts per number), for 2'a (goff = 1), 2'b (the
reference), the reference pipeline, and to cover the other changed paths: 2'b with a_mode = enumerate (no OnDemand),
2'b + pp 3 (the power-entry arrays), and confirm = resieve. Python is unchanged (no Python file in this commit).
  python3 alloconce_accept.py -> alloconce_accept.out (stdout); exit 1 on any failure"""
import json, subprocess, sys
import partition as P, sizescale2 as S2
from fastlamps import BIN
from lctest import ref
from baseline_msieve import pipeline

BEFORE = "/tmp/claude-1000/-home-onojk123-lumens-per-watt/ddfe4e3f-7fea-48e0-ba4d-4e65f4fd682d/scratchpad/lampcore_fix_ef3459"

def raw(binary, genome, nums, types):
    text = json.dumps(genome) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    return subprocess.run([binary] + (["--types"] if types else []), input=text, capture_output=True, text=True, check=True).stdout

fails = 0
for bits in (72, 84, 96):
    nums = S2.map_nums(bits)
    r2b = dict(ref(bits), goff=1, confirm="root")
    enum = {k: v for k, v in r2b.items() if k != "a_mode"}
    cells = {"2'a": [dict(ref(bits), goff=1)], "2'b": [r2b], "pipeline": pipeline(bits), "2'b enumerate": [enum],
             "2'b + pp 3": [dict(r2b, pp=3)], "resieve": [dict(ref(bits), goff=1, confirm="resieve")]}
    line = []
    for name, g in cells.items():
        same = all(raw(BEFORE, g, nums, t) == raw(BIN, g, nums, t) for t in (False, True))
        line.append(f"{name} {'identical' if same else 'DIFFERENT'}")
        fails += not same
    print(f"{bits} bits ({len(nums)} numbers): lampcore before/after, stdout with and without --types: " + "; ".join(line), flush=True)
print("failures:", fails)
sys.exit(1 if fails else 0)
