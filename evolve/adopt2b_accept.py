"""Acceptance for the adoption of 2'b as the reference (the user, Oct 27): reference genes = the sealed genes with
kset sf32 (lctest.ref), goff = 1 and confirm = root. All map numbers at 72, 84 and 96 (480 / 560 / 640), lampcore.
  1. The new reference is the 2'b cell of step 3 / 2b-sizes, number by number: per-number ops and all 30 type counts
     identical to dict(ref(bits), goff=1, confirm="root") as those runs built it.
  2. Against the old reference (2'a, goff = 1): the same factor, tests, hits and polynomials (sieve_scan) on every
     number; every type outside confirm_td, root_test, word and setup_small identical.
  3. Relations unchanged: Python traces (relations and candidate values per attempt) identical to 2'a on 4 numbers per size.
  python3 adopt2b_accept.py -> adopt2b_accept.out (stdout); exit 1 on any failure"""
import sys
import partition as P, sizescale2 as S2, qs, lamps, optypes
from fastlamps import run_many
from lctest import ref

def new_reference(bits):
    return dict(ref(bits), goff=1, confirm="root")            # the adopted reference genes (card_params, Oct 27)

def trace(g, N):
    qs.TRACE = {}
    try:
        qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    return [(a.get("rels"), a.get("cands")) for a in tr["attempts"]]

CHANGED = {"confirm_td", "root_test", "word", "setup_small"}
fails = 0
for bits in (72, 84, 96):
    nums = S2.map_nums(bits)
    g_new = new_reference(bits)
    g_2b = dict(dict(ref(bits), goff=1), confirm="root")        # as step3.py / shiftrun.py built 2'b
    g_2a = dict(ref(bits), goff=1)
    r_new, r_2b, r_2a = (run_many([g], nums, P.QS_CAP, types=True) for g in (g_new, g_2b, g_2a))
    same_2b = sum(a[0] == b[0] and a[4] == b[4] for a, b in zip(r_new, r_2b))
    ident = sum(a[1:4] == b[1:4] and a[4]["sieve_scan"] == b[4]["sieve_scan"] for a, b in zip(r_new, r_2a))
    others = sum(all(a[4].get(t, 0) == b[4].get(t, 0) for t in optypes.TYPE_ORDER if t not in CHANGED) for a, b in zip(r_new, r_2a))
    sample = nums[::len(nums) // 4][:4]
    rel = sum(trace(g_new, N) == trace(g_2a, N) for N, _, _ in sample)
    n = len(nums)
    print(f"{bits} bits: (1) identical to the 2'b runs (ops and all 30 types) {same_2b}/{n}; (2) factor, tests, hits and "
          f"polynomials identical to 2'a {ident}/{n}; types outside {sorted(CHANGED)} identical {others}/{n}; "
          f"(3) relations and candidate values identical to 2'a on {rel}/{len(sample)} traced numbers", flush=True)
    fails += (same_2b != n) + (ident != n) + (others != n) + (rel != len(sample))
print("failures:", fails)
sys.exit(1 if fails else 0)
