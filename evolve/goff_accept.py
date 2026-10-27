"""Acceptance for I-032 option 2'a, start offsets kept by the Gray code (NOTES.md, "I-032 option 2'a: start offsets
kept by the Gray code — cost model"). Gene goff, off by default.
  1. goff off against the pre-change lampcore (LAMPCORE_OLD): identical per number and per type on all map numbers
     54-96, for the new reference, + re-sieve, + root, + pp 3, + pp 10, the frozen and the corrected reference.
  2. goff on against goff off, all map numbers 54-96, same genomes: the same factor, candidates, hits and every type
     except word; word changes by exactly -setup_gray (the per-polynomial start offsets of every root, roots x
     (polynomials - 1) per A, less the per-A conversion), and under re-sieve by a further -(roots walked) (< 0).
  3. Relations identical (Python traces, 2 numbers per size): the ledger's relations, every candidate value and the
     traced x-roots per polynomial, on against off; and Python's word change equals -setup_gray - roots walked exactly.
  4. Python = Rust per type, goff on and off, 2 numbers per size per genome.
  LAMPCORE_OLD=<pre-change binary> python3 goff_accept.py -> stdout
"""
import json, os, subprocess
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
P0 = 30

def nr(bits):
    return dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")

def old_run(g, nums):
    text = json.dumps([g]) + "\n" + str(int(P.QS_CAP)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    res = subprocess.run([os.environ["LAMPCORE_OLD"], "--types"], input=text, capture_output=True, text=True, check=True)
    out = []
    for line in res.stdout.split("\n"):
        if not line:
            continue
        f = line.split()
        i = f.index("T")
        t = dict(zip(optypes.TYPE_ORDER, map(int, f[i + 1:])))
        assert len(f) - i - 1 == len(optypes.TYPE_ORDER)
        f = f[:i]
        out.append(((None, None, int(f[1]), int(f[2])) if f[0] == "miss" else (int(f[0]), int(f[1]), int(f[2]), int(f[3]))) + (t,))
    return out

def py(g, N):
    m = lamps.Meter(P.QS_CAP)
    qs.TRACE = {}
    try:
        qs.lamp_qs(N, g, m)
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    return {k: v for k, v in optypes.qs_counts(tr).items() if v}, m.ops, tr

def py_vs_rust(g, N, p, q):
    t, ops, tr = py(g, N)
    r = run_many([g], [(N, p, q)], P.QS_CAP, types=True)[0]
    return t == {k: v for k, v in r[4].items() if v} and ops == r[0], t, tr

def walked(g, tr):
    if g.get("confirm") != "resieve":
        return 0
    p0 = g.get("p0", P0)
    return sum(1 for at in tr["attempts"] for pl in at["polys"] for (pp, _) in pl["roots"] if pp >= p0)

if __name__ == "__main__":
    c = {k: [0, 0] for k in (1, 2, 3, 4)}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        g0 = nr(bits)
        gens = {"new ref": g0, "new ref + re-sieve": dict(g0, confirm="resieve"), "new ref + root": dict(g0, confirm="root"),
                "new ref + pp 3": dict(g0, pp=3), "new ref + pp 10": dict(g0, pp=10), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}
        for name, g in gens.items():
            off = run_many([g], nums, P.QS_CAP, types=True)
            for a, b in zip(off, old_run(g, nums)):
                c[1][0] += 1; c[1][1] += not (a[:4] == b[:4] and a[4] == b[4])
            on = run_many([dict(g, goff=1)], nums, P.QS_CAP, types=True)
            for a, b in zip(off, on):
                same = a[1:4] == b[1:4] and all(a[4][t] == b[4][t] for t in optypes.TYPE_ORDER if t != "word")
                dw = b[4]["word"] - a[4]["word"]
                okw = dw == -a[4]["setup_gray"] if g.get("confirm") != "resieve" else dw < -a[4]["setup_gray"] or a[4]["setup_gray"] == 0
                c[2][0] += 1; c[2][1] += not (same and okw)
            for N, p, q in nums[::len(nums) // 2][:2]:
                okf, tf, trf = py_vs_rust(g, N, p, q)
                okn, tn, trn = py_vs_rust(dict(g, goff=1), N, p, q)
                rels = lambda tr: [(a.get("rels"), a.get("cands"), [pl["roots"] for pl in a["polys"]]) for a in tr["attempts"]]
                dw = tn.get("word", 0) - tf.get("word", 0)
                c[3][0] += 1; c[3][1] += not (rels(trf) == rels(trn) and dw == -tf.get("setup_gray", 0) - walked(g, trf))
                c[4][0] += 2; c[4][1] += (not okf) + (not okn)
        print(f"{bits} bits done " + " ".join(f"{k}:{v[0] - v[1]}/{v[0]}" for k, v in c.items()), flush=True)
    names = {1: "goff off vs pre-change lampcore, per number and per type",
             2: "goff on vs off: factor, candidates, hits, every type but word; word -setup_gray (re-sieve: less)",
             3: "relations, candidate values and traced x-roots identical; Python word change exact (Python traces)",
             4: "Python = Rust per type, goff on and off"}
    for k, v in c.items():
        print(f"{k}. {names[k]}: {v[0] - v[1]}/{v[0]}")
    assert not any(v[1] for v in c.values())
