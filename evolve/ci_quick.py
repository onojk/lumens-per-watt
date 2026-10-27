"""Quick parity and acceptance subset for CI (.github/workflows/parity.yml; CONTRIBUTING.md). Not a replacement for
parity.py or the per-change acceptance scripts, which a maintainer runs before adopting anything.
  1. Lamps (parity.py's first check, small): every baseline genome, Python against Rust on ops, factor, tests, hits,
     stage and k, 2 numbers per size at 28 and 34 bits.
  2. qs per type: Python = Rust (per-type counts and total ops) for the reference genes and the card options
     (re-sieve, root confirm, pp 3, goff, goff + root), the frozen and the corrected reference, 2 map numbers at 54, 72, 84.
  3. Identity (lampcore): root confirm against the full pass, and goff on against off, on 12 map numbers at 54-96:
     the same factor, candidates and hits, the same types outside the changed ones, and goff's word change exactly
     -setup_gray.
  python3 ci_quick.py -> stdout; exit 1 on any failure
"""
import sys, time
import partition as P, sizescale as SS, sizescale2 as S2, optypes
from fastlamps import run_many
from lamps import run, LAST, cap_for
from parity import genomes
from goff_accept import nr, py_vs_rust

t0 = time.time()
fails = []
n = {1: 0, 2: 0, 3: 0}
from fastlamps import semiprimes_pq
for name, g in genomes().items():
    for b in (28, 34):
        nums = semiprimes_pq(b, 2, 90000 + b)
        cap = min(cap_for(b), 2 ** 22)
        for (N, p, q), f in zip(nums, run_many(g, nums, cap, inst=True)):
            ops, d = run(g, N, cap)
            n[1] += 1
            if (ops, d, LAST["tests"], LAST["hits"], LAST["stage"], LAST["k"]) != f:
                fails.append(f"1 lamps {name} {b} {N}")
print(f"1. lamps: done ({time.time() - t0:.0f} s)", flush=True)

CONFIRM_TYPES = {"confirm_td", "word", "setup_small", "root_test"}
for bits in (54, 72, 84, 96):
    nums = S2.map_nums(bits)
    g0 = nr(bits)
    gens = {"ref": g0, "resieve": dict(g0, confirm="resieve"), "root": dict(g0, confirm="root"), "pp 3": dict(g0, pp=3),
            "goff": dict(g0, goff=1), "goff + root": dict(g0, goff=1, confirm="root"), "frozen": SS.FROZEN_REF, "corrected": SS.OLD}
    for name, g in (gens.items() if bits <= 84 else ()):
        for N, p, q in nums[::len(nums) // 2][:2]:
            ok, _, _ = py_vs_rust(g, N, p, q)
            n[2] += 1
            if not ok:
                fails.append(f"2 types {bits} {name} {N}")
    sub = nums[::max(1, len(nums) // 12)][:12]
    full = run_many([g0], sub, P.QS_CAP, types=True)
    for other, changed in ((dict(g0, confirm="root"), CONFIRM_TYPES), (dict(g0, goff=1), {"word"})):
        for a, b in zip(full, run_many([other], sub, P.QS_CAP, types=True)):
            n[3] += 1
            same = a[1:4] == b[1:4] and all(a[4][t] == b[4][t] for t in optypes.TYPE_ORDER if t not in changed)
            if "goff" in other:
                same = same and b[4]["word"] - a[4]["word"] == -a[4]["setup_gray"]
            if not same:
                fails.append(f"3 identity {bits} {other.get('confirm', '')}{' goff' if 'goff' in other else ''} {a[0]}")
    print(f"{bits} bits: done ({time.time() - t0:.0f} s)", flush=True)
print(f"checks: lamps {n[1]}, qs per type {n[2]}, identity {n[3]}; failures: {len(fails)}" + ("".join(f"\n  {f}" for f in fails[:20])))
print(f"elapsed {time.time() - t0:.0f} s")
sys.exit(1 if fails else 0)
