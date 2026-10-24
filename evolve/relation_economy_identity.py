"""Identity check for the relation-economy refactor (PLAN.md, "Relation economy"): qs split
into a SOURCE (qs.py) and a LEDGER (ledger.py) must equal today's qs op for op.

Reference: qs.py as of commit 78b2dae (before the split), loaded from git, and a lampcore
binary built from the same commit (path given as the first argument).
Pairs: every qs pair parity.py checks (parity.qs_pairs: lc 1.0 and lc 1.2-2.0, retries,
caps that stop mid-phase and inside lp, qs after another stage, random genomes with random
lc), plus tuned qs at lc 1.0 and lc 1.4 on the Run 6 ACCEPT numbers (cap 2^28).

Python: the refactored and reference cards must agree on ops (or both miss), factor, tests,
hits, winning stage, the whole trace (every realized count the accounting tests read), and
the charge sequence itself: every charge's phase and size, in order.
Rust: the refactored and reference binaries must print identical lines (ops, factor, tests,
hits, stage, k, all eight phases).

  python3 relation_economy_identity.py REF_LAMPCORE [workers]
"""
import subprocess, sys, types
from multiprocessing import Pool

REF_BIN = sys.argv[1] if len(sys.argv) > 1 else None
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
sys.argv[1:] = []                                  # parity.py reads its own arguments on import

import qs, lamps
from lamps import run, LAST
from fastlamps import semiprimes_pq, run_many
import fastlamps
from parity import qs_pairs, TUNED
from run6_accept import SETS, CAP
REF_COMMIT = "78b2dae"

class ChargeSeq(dict):
    """TRACE["ops"] that records every charge as (phase, size), in order."""
    def __init__(self):
        super().__init__(); self.seq = []
    def __setitem__(self, phase, value):
        self.seq.append((phase, value - self.get(phase, 0)))
        super().__setitem__(phase, value)

def ref_module():
    src = subprocess.run(["git", "show", f"{REF_COMMIT}:evolve/qs.py"], capture_output=True,
                         text=True, check=True).stdout
    mod = types.ModuleType("qs_ref")
    exec(compile(src, "qs_ref.py", "exec"), mod.__dict__)
    return mod

REF = None

def one(mod, g, N, cap):
    lamps.LAMPS["qs"] = mod.lamp_qs                # run() dispatches through LAMPS
    mod.TRACE = {"ops": ChargeSeq()}
    ops, d = run(g, N, cap)
    tr = mod.TRACE
    mod.TRACE = None
    return (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"]), tr["ops"].seq, tr

def job(args):
    global REF
    if REF is None:
        REF = ref_module()
    label, g, N, cap = args
    a = one(REF, g, N, cap)
    b = one(qs, g, N, cap)
    lamps.LAMPS["qs"] = qs.lamp_qs
    lp = sum(n for ph, n in b[1] if ph == "lp")
    return label, N, a[0] == b[0], a[1] == b[1], a[2] == b[2], lp, len(b[1])

def pairs():
    for label, g, nums, cap, must_retry in qs_pairs():
        yield label, g, nums, cap
    for lc in (1.0, 1.4):
        for b, (c, s) in SETS.items():
            yield f"ACCEPT lc {lc}", [dict(TUNED, lc=lc)], semiprimes_pq(b, c, s), CAP

if __name__ == "__main__":
    groups = list(pairs())
    jobs = [(label, g, N, cap) for label, g, nums, cap in groups for N, p, q in nums]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=2)
    bad = [r for r in res if not all(r[2:5])]
    lp_runs = sum(1 for r in res if r[5])
    print(f"python: {len(res)} runs, {sum(r[6] for r in res)} charges compared; "
          f"result mismatches {sum(not r[2] for r in res)}, charge-sequence mismatches "
          f"{sum(not r[3] for r in res)}, trace mismatches {sum(not r[4] for r in res)}; "
          f"{lp_runs} runs with lp charges")
    for r in bad[:10]:
        print("  MISMATCH", r)
    rust_bad = rust_n = 0
    if REF_BIN:
        for label, g, nums, cap in groups:
            new = run_many(g, nums, cap, inst=True, phases=True)
            fastlamps.BIN, keep = REF_BIN, fastlamps.BIN
            try:
                old = run_many(g, nums, cap, inst=True, phases=True)
            finally:
                fastlamps.BIN = keep
            rust_n += len(nums)
            for (N, p, q), x, y in zip(nums, new, old):
                if x != y:
                    rust_bad += 1
                    if rust_bad <= 10:
                        print("  RUST MISMATCH", label, N, "new", x, "ref", y)
        print(f"rust: {rust_n} runs (ops, factor, tests, hits, stage, k, 8 phases), "
              f"mismatches {rust_bad}")
    else:
        print("rust: skipped (no reference binary given)")
    ok = not bad and not rust_bad and REF_BIN
    print("IDENTITY", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
