"""Acceptance for sort_charge (NOTES.md, "The sort_charge option": tests written before the code).

  1. sort_charge = 0 is today's card: lampcore with "sort_charge": 0 equals the run without the
     key, per type and per number, on all 2,880 map numbers, both a_modes, three genomes.
  2. Identity (Python): sort_charge 1 against 0 on sample numbers (both modes, qs + lc 1.4's and
     the new genes): every phase equal except mult and setup, which differ by exactly the formula
     from the trace (kc; per attempt len(pool_all), P, C, and the keys formed).
  3. Python = Rust with sort_charge 1: per-type counts and factor on map samples (2 per band per
     size, three genomes, on_demand; 1 per band, enumerate, qs + lc 1.4's genes).

  python3 sortcharge_accept.py [workers]  -> sortcharge_accept.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json
from multiprocessing import Pool
import qs, optypes
import partition as P
import typemix as TM
import ondemand_accept as OA
from qs import sort_cost
from fastlamps import run_many

GEN = {"old": OA.OLD, "new": OA.NEW, "n51": OA.N51}
PHASES = OA.PHASES

def identity_job(args):
    N, gname, mode = args
    g = dict(GEN[gname], a_mode=mode)
    d0, ops0, tr0 = OA.py_run(N, dict(g, sort_charge=0))
    d1, ops1, tr1 = OA.py_run(N, dict(g, sort_charge=1))
    ph0 = {k: tr0["ops"].get(k, 0) for k in PHASES}
    ph1 = {k: tr1["ops"].get(k, 0) for k in PHASES}
    want_mult = sort_cost(int(g["kc"]))
    want_setup = 0
    for at in tr1["attempts"]:
        want_setup += at["n_pool_all"] + sort_cost(at["n_pool_all"]) + sort_cost(at["P"])
        if mode == "enumerate":
            want_setup += at["combos"] + sort_cost(at["combos"])
        else:
            want_setup += sort_cost(at["s"]) * at.get("od_keys", 0)
    ok = (d0 == d1 and all(ph0[k] == ph1[k] for k in PHASES if k not in ("mult", "setup"))
          and ph1["mult"] - ph0["mult"] == want_mult and ph1["setup"] - ph0["setup"] == want_setup
          and len(tr0["attempts"]) == len(tr1["attempts"]))
    return {"N": N, "genome": gname, "mode": mode, "attempts": len(tr1["attempts"]), "mult_extra": want_mult,
            "setup_extra": want_setup, "ok": bool(ok)}

def parity_job(args):
    N, gname, mode = args
    g = dict(GEN[gname], a_mode=mode, sort_charge=1)
    d, ops, tr = OA.py_run(N, g)
    return N, gname, mode, d, ops, {k: v for k, v in optypes.qs_counts(tr).items() if v}

if __name__ == "__main__":
    workers = int(ARGS[0]) if ARGS else 8
    out = {}
    samples = {bits: TM.load(bits)[0] for bits in (72, 78, 84, 90, 96)}
    # 1
    n1 = 0
    for bits, nums in samples.items():
        for gname in GEN:
            for mode in ("enumerate", "on_demand"):
                a = run_many([dict(GEN[gname], a_mode=mode)], nums, P.QS_CAP, types=True)
                b = run_many([dict(GEN[gname], a_mode=mode, sort_charge=0)], nums, P.QS_CAP, types=True)
                assert a == b, (bits, gname, mode)
                n1 += len(nums)
    print(f"1. sort_charge 0 = absent: {n1} runs identical (2,880 numbers x 3 genomes x 2 modes)")
    out["off_unchanged"] = n1
    bands = {}
    for bits in samples:
        src = json.load(open(TM.SRC[bits][0]))
        bands[bits] = [r["band"] for r in (src if bits == 84 else src["maps"][str(bits)])["rows"]]
    def pick(bits, per):
        seen, outl = {}, []
        for t, b in zip(samples[bits], bands[bits]):
            if seen.get(b, 0) < per:
                seen[b] = seen.get(b, 0) + 1
                outl.append(t)
        return outl
    with Pool(workers) as pool:
        jobs = [(t[0], gname, mode) for bits in samples for t in pick(bits, 1)[-3:] for gname in ("old", "new")
                for mode in ("enumerate", "on_demand")]
        res = pool.map(identity_job, jobs, chunksize=1)
        bad = [r for r in res if not r["ok"]]
        print(f"2. identity (sort_charge 1 vs 0): {len(res) - len(bad)}/{len(res)} runs equal outside mult and setup, "
              f"which differ by exactly the formula")
        for r in res:
            print(f"   {r['N'].bit_length()} bits {r['genome']} {r['mode']:9s} attempts {r['attempts']} mult +{r['mult_extra']} setup +{r['setup_extra']}"
                  + ("" if r["ok"] else "  FAIL"))
        out["identity"] = res
        jobs = [(t[0], gname, "on_demand") for bits in samples for gname, per in (("old", 2), ("new", 2), ("n51", 1)) for t in pick(bits, per)]
        jobs += [(t[0], "old", "enumerate") for bits in samples for t in pick(bits, 1)]
        py = pool.map(parity_job, jobs, chunksize=1)
    mism = 0
    for gname in GEN:
        for mode in ("enumerate", "on_demand"):
            rows = [x for x in py if x[1] == gname and x[2] == mode]
            if not rows:
                continue
            nums = [next(t for b in samples for t in samples[b] if t[0] == x[0]) for x in rows]
            rs = run_many([dict(GEN[gname], a_mode=mode, sort_charge=1)], nums, P.QS_CAP, types=True)
            for (N, _, _, d, ops, pt), r in zip(rows, rs):
                rt = {k: v for k, v in r[4].items() if v}
                same_factor = (r[1] is None and d is None) or (r[1] is not None and d is not None and int(r[1]) == d)
                if not (same_factor and (r[0] == ops or (r[0] is None and d is None)) and rt == pt):
                    mism += 1
                    if mism <= 5:
                        print("   MISMATCH", gname, mode, N, {k: (pt.get(k), rt.get(k)) for k in set(pt) | set(rt) if pt.get(k) != rt.get(k)})
    print(f"3. Python = Rust with sort_charge 1: {len(py) - mism}/{len(py)} runs agree (per type, factor)")
    out["parity"] = {"runs": len(py), "mismatches": mism}
    json.dump(out, open("sortcharge_accept.json", "w"), indent=1)
    assert not bad and not mism
