"""Price mappings for the partition study's lamps (NOTES.md, partition study, prerequisite):
every op type td, rho, pm1, ECM and qs charge has a calibrated price, and the per-type
splits are exact.

On 84-bit numbers with the study's smaller-factor bands (16-42 bits), each lamp alone (the
study's stage genes; cap 2^21, qs to 2^28):
  - optypes.per_type sums to the run's ops (asserted inside per_type);
  - td: td_mod = ops = tests (one N mod d, one test, per divisor), or tests + 1 for a run
    stopped by the cap (its crossing charge is applied, its test is not);
  - pm1: its multiplies (ops - tests) equal an independent recount, the sum of
    max(1, bit_length(p^e)) over the prime powers p^e <= B; its gcds = tests (1 when the
    run reached its gcd);
  - every type emitted has a price in calibrate.prices under ruint and Montgomery, for
    every benchmark run (P1-P3, E1);
  - mutation: dropping td_mod's price (or pm1's gcd price) must be caught.

  python3 price_accept.py  -> price_accept.json
"""
import json, math, sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import optypes, qs, ecm, calibrate
from lamps import Meter, Budget, LAMPS, primes_upto
from fastlamps import semiprimes_pq, semiprimes_unbalanced

TD = {"t": "td", "a": 0.5}
RHO = {"t": "rho", "c": 1, "b": 64}
PM1 = {"t": "pm1", "b": 0.19911571277067214}
ECM = {"t": "ecm", "b1": 1.0, "b2": 50}
QS = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}
B = "calibrate_bench"
RUNS = {r: calibrate.load_bench(f"{B}/opbench_{r.lower()}.jsonl") for r in ("P1", "P2", "P3", "E1")}
FAIL = []

def check(cond, *what):
    if not cond:
        FAIL.append(what)
        print("FAIL", *what)
    return cond

def alone(stage, N, cap):
    mod = {"qs": qs, "ecm": ecm}.get(stage["t"])
    tr = {} if mod else None
    if mod:
        mod.TRACE = tr
    m = Meter(cap)
    try:
        LAMPS[stage["t"]](N, stage, m)
    except Budget:
        pass
    if mod:
        mod.TRACE = None
    return m, tr

def pm1_recount(N, g):
    Bd = max(10, int(N ** g["b"]))
    total = 0
    for p in primes_upto(Bd):
        pk = p
        while pk * p <= Bd:
            pk *= p
        total += max(1, pk.bit_length())
    return total

def priced(types, drop=None):
    for ref in ("ruint", "montgomery"):
        for r, b in RUNS.items():
            pr = calibrate.prices(b, ref)
            if drop:
                pr.pop(drop, None)
            if not set(types) <= set(pr):
                return False
    return True

if __name__ == "__main__":
    nums = []
    for pb in (16, 24, 32):
        nums += semiprimes_unbalanced(84, pb, 2, 6600000 + pb)
    nums += semiprimes_pq(84, 2, 6600042)
    types, n = set(), 0
    for N, p, q in nums:
        for st, cap in ((TD, 2 ** 21), (RHO, 2 ** 21), (PM1, 2 ** 21), (ECM, 2 ** 21), (QS, 2 ** 28)):
            m, tr = alone(st, N, cap)
            c = optypes.per_type(st, tr, m.ops, m.tests, N)
            types |= set(c)
            if st["t"] == "td":
                # a run stopped by the cap applied its crossing charge but not that test
                check(c["td_mod"] == m.ops == m.tests + (m.ops > cap), "td split", N)
            if st["t"] == "pm1" and m.tests == 1:
                check(c["mul"] == pm1_recount(N, st) and c["gcd"] == 1, "pm1 recount", N, c, pm1_recount(N, st))
            n += 1
    check(priced(types), "every type priced", sorted(types))
    mut = {d: not priced(types, drop=d) for d in ("td_mod", "gcd")}
    check(all(mut.values()), "mutation missed", mut)
    out = {"runs": n, "types": sorted(types), "mutation_caught": mut, "failures": len(FAIL)}
    print(out)
    json.dump(out, open("price_accept.json", "w"), indent=1)
    sys.exit(1 if FAIL else 0)
