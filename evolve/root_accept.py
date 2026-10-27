"""Acceptance for root confirm (NOTES.md, "Root confirm (I-029) as a card option").
  1. Option off against the pre-change lampcore (LAMPCORE_OLD, 29 type columns; the new root_test column must be 0):
     identical per number and per type on all map numbers 54-96 for the new reference (with and without re-sieve),
     the frozen and the corrected reference.
  2. Python = Rust per type, option off, 2 numbers per size per genome.
  3. Option on against the full pass, all map numbers 54-96, genomes: the new reference, + pp 3, + pp 10: the same
     factor, candidates (tests), hits, polynomials (sieve_scan) and every type outside confirm (all types equal except
     confirm_td, word, setup_small and root_test).
  4. Relations identical (Python traces, 2 numbers per size): the ledger's relations (u, sparse vector, y) and every
     candidate value, root against full.
  5. Python = Rust per type, option on, 2 numbers per size, for the same genomes and the corrected reference + root.
  LAMPCORE_OLD=<373261d binary> python3 root_accept.py -> stdout
"""
import json, os, subprocess
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps
import fastlamps
from fastlamps import run_many

sealed = json.load(open("sizescale_k_sealed.json"))
OLD_ORDER = optypes.TYPE_ORDER[:-1]
assert optypes.TYPE_ORDER[-1] == "root_test"
CONFIRM_TYPES = {"confirm_td", "word", "setup_small", "root_test"}

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
        t = dict(zip(OLD_ORDER, map(int, f[i + 1:])))
        assert len(f) - i - 1 == len(OLD_ORDER)
        f = f[:i]
        out.append(((None, None, int(f[1]), int(f[2])) if f[0] == "miss" else (int(f[0]), int(f[1]), int(f[2]), int(f[3]))) + (t,))
    return out

def py_vs_rust(g, N, p, q):
    m = lamps.Meter(P.QS_CAP)
    qs.TRACE = {}
    try:
        qs.lamp_qs(N, g, m)
    except lamps.Budget:
        pass
    tr = qs.TRACE; qs.TRACE = None
    py = {k: v for k, v in optypes.qs_counts(tr).items() if v}
    r = run_many([g], [(N, p, q)], P.QS_CAP, types=True)[0]
    return py == {k: v for k, v in r[4].items() if v} and m.ops == r[0], tr

if __name__ == "__main__":
    c = {k: [0, 0] for k in (1, 2, 3, 4, 5)}
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        g0 = nr(bits)
        off = {"new ref": g0, "new ref + re-sieve": dict(g0, confirm="resieve"), "frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD}
        for name, g in off.items():
            for a, b in zip(run_many([g], nums, P.QS_CAP, types=True), old_run(g, nums)):
                ta = dict(a[4]); z = ta.pop("root_test")
                c[1][0] += 1; c[1][1] += not (z == 0 and a[:4] == b[:4] and ta == b[4])
            for N, p, q in nums[::len(nums) // 2][:2]:
                ok, _ = py_vs_rust(g, N, p, q)
                c[2][0] += 1; c[2][1] += not ok
        for name, g in {"new ref": g0, "new ref + pp 3": dict(g0, pp=3), "new ref + pp 10": dict(g0, pp=10)}.items():
            full = run_many([g], nums, P.QS_CAP, types=True)
            root = run_many([dict(g, confirm="root")], nums, P.QS_CAP, types=True)
            for a, b in zip(full, root):
                same = a[1:4] == b[1:4] and all(a[4][t] == b[4][t] for t in optypes.TYPE_ORDER if t not in CONFIRM_TYPES)
                c[3][0] += 1; c[3][1] += not same
            for N, p, q in nums[::len(nums) // 2][:2]:
                okf, trf = py_vs_rust(g, N, p, q)
                okr, trr = py_vs_rust(dict(g, confirm="root"), N, p, q)
                rels = lambda tr: [(a.get("rels"), a.get("cands")) for a in tr["attempts"]]
                c[4][0] += 1; c[4][1] += not (rels(trf) == rels(trr))
                c[5][0] += 1; c[5][1] += not okr
        for N, p, q in nums[::len(nums) // 2][:2]:
            ok, _ = py_vs_rust(dict(SS.OLD, confirm="root"), N, p, q)
            c[5][0] += 1; c[5][1] += not ok
        print(f"{bits} bits done " + " ".join(f"{k}:{v[0] - v[1]}/{v[0]}" for k, v in c.items()), flush=True)
    names = {1: "option off vs pre-change lampcore, per number and per type", 2: "Python = Rust per type, option off",
             3: "option on vs full pass: factor, candidates, hits and every non-confirm type", 4: "relations and candidate values identical (Python traces)",
             5: "Python = Rust per type, option on"}
    for k, v in c.items():
        print(f"{k}. {names[k]}: {v[0] - v[1]}/{v[0]}")
    assert not any(v[1] for v in c.values())
