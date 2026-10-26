"""Acceptance for kset = sf32 (NOTES.md, "kc becomes a constant"; tests written before the code).

  1. Identity: with kset absent, lampcore equals the pre-kset lampcore (LAMPCORE=<old binary>) per
     type and per number on the map numbers (54-96 bits), for qs + lc 1.4 (enumerate, the frozen
     reference), the corrected-card qs + lc 1.4, and the kc/lc round's R@96 and M@84 genomes.
  2. With kset = sf32: lampcore's "mult" count equals the kc = 20 run's on every map number, and
     Python's selected k (trace) equals the top squarefree KS pick, on 2 numbers per band at 54-72.

  LAMPCORE=<old> python3 kset_accept.py dump old.json; python3 kset_accept.py dump new.json;
  python3 kset_accept.py check old.json new.json
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json
import partition as P
import sizescale as SS
import sizescale2 as S2
from fastlamps import run_many

def genomes():
    kb = json.load(open("sizescale_k_budgets.json"))["genes"]
    return {"frozen ref": SS.FROZEN_REF, "corrected ref": SS.OLD,
            "R-k@96": SS.qsg(kb["96"]["R"]), "M-k@84": SS.qsg(kb["84"]["M"])}

if __name__ == "__main__":
    if ARGS[0] == "dump":
        out = {}
        for bits in SS.SIZES:
            nums = S2.map_nums(bits)
            for name, g in genomes().items():
                out[f"{bits} {name}"] = [list(r[:2]) + [r[4]] for r in run_many([g], nums, P.QS_CAP, types=True)]
        json.dump(out, open(ARGS[1], "w"), default=str)
        sys.exit(0)
    old, new = json.load(open(ARGS[1])), json.load(open(ARGS[2]))
    n = sum(len(v) for v in old.values())
    bad = sum(a != b for k in old for a, b in zip(old[k], new[k]))
    print(f"1. kset absent = pre-kset lampcore: {n - bad}/{n} runs identical (per type, factor, ops)")
    import qs, lamps
    m_bad = m_n = 0
    for bits in SS.SIZES:
        nums = S2.map_nums(bits)
        for name, g in genomes().items():
            a = run_many([dict(g, kset="sf32")], nums, P.QS_CAP, types=True)
            b = run_many([dict(g, kc=20)], nums, P.QS_CAP, types=True)
            for x, y in zip(a, b):
                m_n += 1
                m_bad += x[4]["mult"] != y[4]["mult"]
    print(f"2a. kset sf32 'mult' count = kc 20's: {m_n - m_bad}/{m_n}")
    k_bad = k_n = 0
    for bits in (54, 72):
        bp = SS.pop(bits, 2, 9500000)
        for N, _, _ in [t for v in bp.values() for t in v]:
            for name in ("corrected ref", "R-k@96"):
                g = dict(genomes()[name], kset="sf32")
                qs.TRACE = {}
                m = lamps.Meter(P.QS_CAP)
                try:
                    qs.lamp_qs(N, g, m)
                except lamps.Budget:
                    pass
                k = qs.TRACE["attempts"][0]["k"]
                qs.TRACE = None
                want = max(qs.SF32, key=lambda kk: (lamps.ks_score(kk, N), -kk))
                k_n += 1
                k_bad += k != want
    print(f"2b. Python's selected k = top squarefree KS pick: {k_n - k_bad}/{k_n}")
    assert not bad and not m_bad and not k_bad
