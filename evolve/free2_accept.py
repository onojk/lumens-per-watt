"""Acceptance for the free-2 meter correction (NOTES.md, "Meter correction (proposed; ...): pp's free-2 initialisation
is uncharged"; the user's decision, APPLY, Oct 27): with pp on, each polynomial charges one sieve_scan per cell the
free-2 initialisation writes, ceil((width - par) / 2).
Genomes: without pp: the reference, + goff, + goff + root, + root; with pp: + goff + root + pp 3, + goff + root + pp 3
at +2 bits, + pp 3, + pp 10, + root + pp 10, + goff + pp 10. All map numbers 54-96.
  1. Without pp: every number identical to the pre-change lampcore (LAMPCORE_OLD), per number and per type.
  2. With pp: factor, tests and hits identical; every type identical except sieve_scan; the sieve_scan increase equals
     the total-ops increase and is positive on every number.
  3. With pp, 2 numbers per size per genome (Python traces): the increase equals the cells written, counted
     independently as len(range(par, 2M + 1, 2)) summed over the traced polynomials; Python = Rust per type and in ops.
  LAMPCORE_OLD=<pre-change binary> python3 free2_accept.py -> stdout
"""
import math
import partition as P, sizescale as SS, sizescale2 as S2, qs, lamps
from fastlamps import run_many
from goff_accept import nr, old_run, py_vs_rust

if __name__ == "__main__":
    c = {k: [0, 0] for k in (1, 2, 3)}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        g0 = nr(bits)
        lb = math.log2(1752.0)
        nopp = [g0, dict(g0, goff=1), dict(g0, goff=1, confirm="root"), dict(g0, confirm="root")]
        withpp = [dict(g0, goff=1, confirm="root", pp=3), dict(g0, goff=1, confirm="root", pp=3, tc=g0["tc"] - 2 / lb),
                  dict(g0, pp=3), dict(g0, pp=10), dict(g0, confirm="root", pp=10), dict(g0, goff=1, pp=10)]
        for g in nopp:
            for x, y in zip(run_many([g], nums, P.QS_CAP, types=True), old_run(g, nums)):
                c[1][0] += 1; c[1][1] += not (x[:4] == y[:4] and x[4] == y[4])
        for g in withpp:
            new = run_many([g], nums, P.QS_CAP, types=True)
            dd = {}
            for (N, _, _), x, y in zip(nums, new, old_run(g, nums)):
                d = x[4]["sieve_scan"] - y[4]["sieve_scan"]
                ok = (x[1:4] == y[1:4] and d > 0 and x[0] - y[0] == d
                      and all(x[4].get(t, 0) == y[4].get(t, 0) for t in set(x[4]) | set(y[4]) if t != "sieve_scan"))
                c[2][0] += 1; c[2][1] += not ok
                dd[N] = d
            for N, p, q in nums[::len(nums) // 2][:2]:
                ok, _, tr = py_vs_rust(g, N, p, q)
                cells = sum(len(range(pl["par"], 2 * pl["M"] + 1, 2)) for at in tr["attempts"] for pl in at["polys"])
                c[3][0] += 1; c[3][1] += not (ok and cells == dd[N])
        print(f"{bits} bits done " + " ".join(f"{k}:{v[0] - v[1]}/{v[0]}" for k, v in c.items()), flush=True)
    names = {1: "without pp: identical to the pre-change lampcore, per number and per type",
             2: "with pp: only sieve_scan and total ops change, by the same positive amount",
             3: "with pp: the increase = cells written, len(range(par, 2M+1, 2)) over traced polynomials; Python = Rust"}
    for k, v in c.items():
        print(f"{k}. {names[k]}: {v[0] - v[1]}/{v[0]}")
    assert not any(v[1] for v in c.values())
