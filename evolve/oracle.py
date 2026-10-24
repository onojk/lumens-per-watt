"""Population oracle (NOTES.md, "Library references and oracles"): an independent check that
every (N, p, q) a study generates is what it claims. Harness only, never in a charged path.

check(nums) asserts, for each (N, p, q): p * q = N, p and q prime (sympy.isprime), and
sympy.factorint(N) == {p: 1, q: 1}. The sympy version is pinned (SYMPY_VERSION) so that a
silent upgrade is noticed. New populations are passed through check() when generated.

  python3 oracle.py [workers]   checks every population the committed studies use
"""
import sys
import sympy

SYMPY_VERSION = "1.14.0"

def _one(t):
    N, p, q = t
    return N == p * q and sympy.isprime(p) and sympy.isprime(q) and sympy.factorint(N) == ({p: 1, q: 1} if p != q else {p: 2})

def check(nums, workers=1):
    assert sympy.__version__ == SYMPY_VERSION, f"sympy {sympy.__version__}, pinned {SYMPY_VERSION}"
    if workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            ok = pool.map(_one, nums, chunksize=4)
    else:
        ok = [_one(t) for t in nums]
    bad = [t for t, o in zip(nums, ok) if not o]
    assert not bad, f"oracle rejects {len(bad)} numbers, e.g. {bad[:2]}"
    return len(nums)

if __name__ == "__main__":
    ARGS, sys.argv[1:] = sys.argv[1:], []
    workers = int(ARGS[0]) if ARGS else 8
    import calibrate, partition as P
    pops = {}
    for k, v in calibrate.pops().items():
        pops[f"Stage 8 {k}"] = v
    for name, base in (("partition tuning", P.TUNING), ("partition sealed", P.SEALED)):
        for pb, v in P.population(base).items():
            pops[f"{name} {pb}"] = v
    total = 0
    for name, nums in pops.items():
        total += check(nums, workers)
    print(f"oracle (sympy {sympy.__version__}): {total} numbers in {len(pops)} populations, all N = p q with p, q prime and factorint agreeing")
