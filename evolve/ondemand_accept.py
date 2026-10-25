"""Acceptance for a_mode = on_demand (NOTES.md, "On-demand A selection": identity and parity
tests, written before the code). Run before any measurement.

  1. enumerate unchanged: lampcore reproduces qs + lc 1.4's per-type counts in every map
     (72/78/84/90/96), number for number.
  2. Identity (Python): on sample numbers per size, for both genomes and both modes, the run with
     "a_given" = the run's own A sequence charges every phase identically, except setup, which
     differs by exactly the selection charge: (s - 1) C(P, s) for enumerate; (s + 1) od_cands
     (s - 1) od_prefixes + 2 od_cands full + od_small small for on_demand.
  3. Python = Rust: on_demand on map samples (2 per band per size for qs + lc 1.4's genes and
     the new genes, 1 per band for N51-0917's qs), Python's qs_counts against lampcore --types on
     every type, and the same factor.

  python3 ondemand_accept.py [workers]  -> ondemand_accept.json, stdout
"""
import sys
ARGS, sys.argv[1:] = sys.argv[1:], []
import json, math
from multiprocessing import Pool
from math import comb
import qs, lamps, optypes
import partition as P
import typemix as TM
from fastlamps import run_many

OLD = dict(P.QS_VARIANTS["qs + lc 1.4"])
NEW = dict(TM.NEW)
N51 = dict(P.QS_VARIANTS["N51-0917's qs"])
PHASES = ("mult", "fb", "setup", "sieve", "confirm", "la", "sqrt", "lp", "check")

def py_run(N, g):
    qs.TRACE = {}
    m = lamps.Meter(P.QS_CAP)
    d = qs.lamp_qs(N, g, m)
    return d, m.ops, qs.TRACE

def identity_job(args):
    N, gname, mode = args
    g = dict({"old": OLD, "new": NEW}[gname], a_mode=mode)
    d, ops, tr = py_run(N, g)
    ats = tr["attempts"]
    given = [c for at in ats for c in at["a_seq"]]
    if len(ats) > 1:                           # a retry (next multiplier): reported, not tested here
        return {"N": N, "genome": gname, "mode": mode, "skip": f"{len(ats)} attempts", "ok": True}
    at = ats[0]
    d2, ops2, tr2 = py_run(N, dict(g, a_given=given))
    ph1 = {k: tr["ops"].get(k, 0) for k in PHASES}
    ph2 = {k: tr2["ops"].get(k, 0) for k in PHASES}
    s = at["s"]
    sel = (s - 1) * at["combos"] if mode == "enumerate" else (s - 1) * at["od_prefixes"] + 2 * at["od_cands"] + at["od_small"]
    if mode == "enumerate":
        P_ = 40 if s == 1 else 16 + 4 * s
        assert at["combos"] == comb(P_, s)
    ok = d == d2 and all(ph1[k] == ph2[k] for k in PHASES if k != "setup") and ph1["setup"] - ph2["setup"] == sel \
        and tr2["attempts"][0]["a_seq"] == given
    return {"N": N, "genome": gname, "mode": mode, "s": s, "a_count": at["a_count"], "od_cands": at["od_cands"],
            "selection": sel, "ok": bool(ok)}

def parity_job(args):
    N, gname = args
    g = dict({"old": OLD, "new": NEW, "n51": N51}[gname], a_mode="on_demand")
    d, ops, tr = py_run(N, g)
    return N, gname, d, ops, {k: v for k, v in optypes.qs_counts(tr).items() if v}, len(tr["attempts"])

if __name__ == "__main__":
    workers = int(ARGS[0]) if ARGS else 8
    out = {}
    # 1
    for bits in (72, 78, 84, 90, 96):
        nums, old = TM.load(bits)
        assert TM.run(OLD, nums) == old
    print("1. enumerate unchanged: lampcore reproduces qs + lc 1.4's per-type counts in all five maps (2,880 numbers)")
    out["enumerate_unchanged"] = 2880
    samples = {bits: TM.load(bits)[0] for bits in (72, 78, 84, 90, 96)}
    bands = {bits: [r["band"] for r in (json.load(open(TM.SRC[bits][0])) if bits == 84 else
                                        json.load(open(TM.SRC[bits][0]))["maps"][str(bits)])["rows"]] for bits in samples}
    def pick(bits, per):
        seen, outl = {}, []
        for t, b in zip(samples[bits], bands[bits]):
            if seen.get(b, 0) < per:
                seen[b] = seen.get(b, 0) + 1
                outl.append(t)
        return outl
    with Pool(workers) as pool:
        # 2
        jobs = [(t[0], gname, mode) for bits in samples for t in pick(bits, 1)[-3:] for gname in ("old", "new")
                for mode in ("enumerate", "on_demand")]
        res = pool.map(identity_job, jobs, chunksize=1)
        bad = [r for r in res if not r["ok"]]
        skipped = [r for r in res if "skip" in r]
        res = [r for r in res if "skip" not in r]
        print(f"   retries skipped: {[(r['N'].bit_length(), r['genome'], r['mode'], r['skip']) for r in skipped]}")
        print(f"2. identity (a_given = the run's own A sequence): {len(res) - len(bad)}/{len(res)} runs identical outside setup,"
              f" setup differing by exactly the selection charge")
        for r in res:
            print(f"   {r['N'].bit_length()} bits {r['genome']} {r['mode']:9s} s {r['s']} A's {r['a_count']} candidates {r['od_cands']}"
                  f" selection charge {r['selection']}" + ("" if r["ok"] else "  FAIL"))
        out["identity"] = res
        # 3
        jobs = [(t[0], gname) for bits in samples for gname, per in (("old", 2), ("new", 2), ("n51", 1)) for t in pick(bits, per)]
        py = pool.map(parity_job, jobs, chunksize=1)
    mism = 0
    for gname in ("old", "new", "n51"):
        g = dict({"old": OLD, "new": NEW, "n51": N51}[gname], a_mode="on_demand")
        rows = [x for x in py if x[1] == gname]
        nums = [next(t for b in samples for t in samples[b] if t[0] == x[0]) for x in rows]
        rs = run_many([g], nums, P.QS_CAP, types=True)
        for (N, _, d, ops, pt, _), r in zip(rows, rs):
            rt = {k: v for k, v in r[4].items() if v}
            same_factor = (r[1] is None and d is None) or (r[1] is not None and d is not None and int(r[1]) == d)
            if not (same_factor and (r[0] == ops or (r[0] is None and d is None)) and rt == pt):
                mism += 1
                if mism <= 5:
                    print("   MISMATCH", gname, N, ops, r[0], {k: (pt.get(k), rt.get(k)) for k in set(pt) | set(rt) if pt.get(k) != rt.get(k)})
    print(f"3. Python = Rust, on_demand, per-type counts and factor: {len(py) - mism}/{len(py)} runs agree")
    out["parity"] = {"runs": len(py), "mismatches": mism, "python_misses": sum(1 for x in py if x[2] is None)}
    out["parity"]["python_retries"] = sum(1 for x in py if x[5] > 1)
    print(f"   Python misses among them: {out['parity']['python_misses']}; runs needing more than one multiplier: {out['parity']['python_retries']}")
    # 4. misses and multiplier retries on all map numbers, both modes, three genomes (lampcore)
    out["retries"] = {}
    print("4. misses on the 2,880 map numbers (lampcore), both modes, three genomes")
    for gname in ("old", "new", "n51"):
        for mode in ("enumerate", "on_demand"):
            g = dict({"old": OLD, "new": NEW, "n51": N51}[gname], a_mode=mode)
            miss = tot = 0
            ks = {}
            for bits in samples:
                rs = run_many([g], samples[bits], P.QS_CAP)
                for r, (N, _, _) in zip(rs, samples[bits]):
                    tot += 1
                    miss += not (r[1] is not None and 1 < int(r[1]) < N)
            out["retries"][f"{gname} {mode}"] = {"runs": tot, "misses": miss}
            print(f"   {gname:3s} {mode:9s}: misses {miss}/{tot}")
    json.dump(out, open("ondemand_accept.json", "w"), indent=1)
    assert not bad and not mism
