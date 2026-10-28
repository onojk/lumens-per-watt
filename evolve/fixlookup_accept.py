"""Acceptance for the A-prime lookup fix (NOTES.md, "Cost note (before code): the A-prime lookup fix"; the user's
decision, Oct 27). All map numbers at 72, 84 and 96 (480 / 560 / 640).
  1. lampcore before (opclass/bin/lampcore-release, sha256 1505efbf..., built from 735fd67) against after (the
     release build of this commit): stdout byte-identical, with and without --types (factor, ops, tests, hits, stage,
     k, all 30 type counts per number), for 2'a (goff = 1), 2'b (the reference) and the reference pipeline.
  2. Python before (qs.py at 9164007, from git) against after: factor, ops, tests, hits, per-type counts and the whole
     trace (relations, candidate values, the A sequence, ... per attempt) identical, 2'a and 2'b, on 4 numbers per size.
  (Python = Rust: the parity suite, separately.)
  python3 fixlookup_accept.py -> fixlookup_accept.out (stdout); exit 1 on any failure"""
import importlib.util, json, os, subprocess, sys, tempfile
import partition as P, sizescale2 as S2, qs, lamps, optypes
from fastlamps import BIN
from lctest import ref
from baseline_msieve import pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
BEFORE = os.path.join(HERE, "..", "opclass", "bin", "lampcore-release")

def raw(binary, genome, nums, types):
    text = json.dumps(genome) + "\n" + str(P.QS_CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    return subprocess.run([binary] + (["--types"] if types else []), input=text, capture_output=True, text=True, check=True).stdout

def old_qs():
    src = subprocess.run(["git", "show", "9164007:evolve/qs.py"], capture_output=True, text=True, check=True, cwd=HERE).stdout
    path = os.path.join(tempfile.mkdtemp(), "qs_before.py"); open(path, "w").write(src)
    spec = importlib.util.spec_from_file_location("qs_before", path); mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, HERE); spec.loader.exec_module(mod)
    return mod

def trace(mod, g, N):
    mod.TRACE = {}
    m = lamps.Meter(P.QS_CAP)
    try:
        f = mod.lamp_qs(N, g, m)
    except lamps.Budget:
        f = "budget"
    tr = mod.TRACE; mod.TRACE = None
    return f, m.ops, m.tests, m.hits, optypes.qs_counts(tr), tr    # the whole trace: relations, candidates, A sequence, ...

qs0 = old_qs()
fails = 0
for bits in (72, 84, 96):
    nums = S2.map_nums(bits)
    cells = {"2'a": [dict(ref(bits), goff=1)], "2'b": [dict(ref(bits), goff=1, confirm="root")], "pipeline": pipeline(bits)}
    line = []
    for name, g in cells.items():
        same = all(raw(BEFORE, g, nums, t) == raw(BIN, g, nums, t) for t in (False, True))
        line.append(f"{name} {'identical' if same else 'DIFFERENT'}")
        fails += not same
    sample = nums[::len(nums) // 4][:4]
    py = 0
    for g in (cells["2'a"][0], cells["2'b"][0]):
        for N, _, _ in sample:
            py += trace(qs0, g, N) == trace(qs, g, N)
    fails += py != 2 * len(sample)
    print(f"{bits} bits ({len(nums)} numbers): lampcore before/after, stdout with and without --types: " + "; ".join(line)
          + f". Python before/after (factor, ops, tests, hits, types, the whole trace), 2'a and 2'b: {py}/{2 * len(sample)}", flush=True)
print("failures:", fails)
sys.exit(1 if fails else 0)
