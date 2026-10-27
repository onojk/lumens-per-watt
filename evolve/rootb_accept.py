"""Acceptance for I-032 option 2'b, root confirm reading the Gray-kept offsets in place (NOTES.md, "I-032 option 2'b:
root confirm reads the kept offsets in place — cost model"). No new gene: goff = 1 with confirm = root.
Genomes: the new reference, + pp 3, + pp 10, the corrected reference; all map numbers 54-96.
  1. goff = 0, confirm = root against the pre-change lampcore (LAMPCORE_OLD, a6d67a2): identical per number and per
     type (root-confirm and root-confirm-2 stay reproducible).
  2. 2'b against 2'a (goff = 1, full pass), every number: the same factor, candidates, hits and polynomials; root_test,
     confirm_td and setup_small change exactly as today's root mode against the full pass (goff = 0); every other
     type except word identical; and word exactly: (2'b - 2'a) = (today's root - full) - (sieved roots summed over
     polynomials) + 2 x (sieved primes summed over A's), the structure counted from a Python trace of each number.
  3. Python traces (2 numbers per size per genome): relations and candidate values identical, 2'b against 2'a and
     against the full pass.
  4. Python = Rust per type for 2'b, 2'a and goff = 0 + root, 2 numbers per size per genome.
  LAMPCORE_OLD=<pre-change binary> python3 rootb_accept.py -> stdout
"""
import qs, lamps, partition as P, sizescale as SS, sizescale2 as S2, optypes
from fastlamps import run_many
from goff_accept import nr, old_run, py_vs_rust

ROOT_TYPES = ("root_test", "confirm_td", "setup_small")

def structure(g, N):
    qs.TRACE = {}
    try:
        qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    roots = sum(len(pl["roots"]) for at in tr["attempts"] for pl in at["polys"])
    primes = sum(at["n_sieved_setup"] for at in tr["attempts"])
    return roots, primes, [(a.get("rels"), a.get("cands")) for a in tr["attempts"]]

if __name__ == "__main__":
    c = {k: [0, 0] for k in (1, 2, 3, 4)}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        g0 = nr(bits)
        for name, g in {"new ref": g0, "new ref + pp 3": dict(g0, pp=3), "new ref + pp 10": dict(g0, pp=10), "corrected ref": SS.OLD}.items():
            rt, a2g, b2g = dict(g, confirm="root"), dict(g, goff=1), dict(g, goff=1, confirm="root")
            full, root, a2, b2 = (run_many([x], nums, P.QS_CAP, types=True) for x in (g, rt, a2g, b2g))
            for x, y in zip(root, old_run(rt, nums)):
                c[1][0] += 1; c[1][1] += not (x[:4] == y[:4] and x[4] == y[4])
            for (N, _, _), f, r, a, b in zip(nums, full, root, a2, b2):
                roots, primes, _ = structure(a2g, N)
                ok = (b[1:4] == a[1:4] and b[4]["sieve_scan"] == a[4]["sieve_scan"]
                      and all(b[4][t] - a[4][t] == r[4][t] - f[4][t] for t in ROOT_TYPES)
                      and all(b[4][t] == a[4][t] for t in optypes.TYPE_ORDER if t not in ROOT_TYPES + ("word",))
                      and b[4]["word"] - a[4]["word"] == (r[4]["word"] - f[4]["word"]) - roots + 2 * primes)
                c[2][0] += 1; c[2][1] += not ok
            for N, p, q in nums[::len(nums) // 2][:2]:
                rb, ra, rf = (structure(x, N)[2] for x in (b2g, a2g, g))
                c[3][0] += 1; c[3][1] += not (rb == ra == rf)
                for x in (b2g, a2g, rt):
                    ok, _, _ = py_vs_rust(x, N, p, q)
                    c[4][0] += 1; c[4][1] += not ok
        print(f"{bits} bits done " + " ".join(f"{k}:{v[0] - v[1]}/{v[0]}" for k, v in c.items()), flush=True)
    names = {1: "goff = 0 + root vs pre-change lampcore, per number and per type",
             2: "2'b vs 2'a: factor, candidates, hits, polynomials; root types as today's root mode; word exact (trace structure)",
             3: "relations and candidate values identical: 2'b, 2'a, full pass (Python traces)",
             4: "Python = Rust per type: 2'b, 2'a, goff = 0 + root"}
    for k, v in c.items():
        print(f"{k}. {names[k]}: {v[0] - v[1]}/{v[0]}")
    assert not any(v[1] for v in c.values())
