"""Op-class v1, step 3 (the user's word, Oct 27; ruling 0b012d3): 2'b against 2'a under the frozen op-class v1 pricing
(opclass/opclass_v1.json, df5a0e3) at 72, 84 and 96 bits, all map numbers, lampcore --types (the frozen release
binary, sha256 1505efbf...). Report only: nothing adopted.
  (a) the break-even sieve_update weight (2'b's op-class ratio = 1, other weights fixed);
  (b) the op-class ratio, paired bootstrap 95% interval (10,000 resamples, random.Random(2026), ratio of sums);
  (c) the robust ratio under the adopted rule (option (b): worst of op-class, ruint, Montgomery) and the (e) call;
  (d) official, for the record (no veto).
  Information: the root_test weight at which the op-class ratio = 1, and 2'b+pp3 (+0, corrected meter) against 2'a.
  python3 step3_sizes.py [bits ...] -> step3_<bits>.json, stdout (step3.py generalised to other sizes, Oct 27; same
  computation; reference genes and map numbers exist only at 54, 72, 84 and 96)"""
import hashlib, json, math, random, sys
ARGV = sys.argv[1:]   # before the imports: partition clears sys.argv
import numpy as np
import partition as P, sizescale2 as S2, optypes
from fastlamps import run_many, BIN
from lctest import ref
R = 10000

def paired(a, b):
    """As shiftrun.paired (copied: importing shiftrun runs its command line): ratio of sums, paired bootstrap 95%."""
    rng = random.Random(2026)
    n = len(a)
    vals = sorted(math.log2(sum(a[i] for i in idx) / sum(b[i] for i in idx))
                  for idx in ([rng.randrange(n) for _ in range(n)] for _ in range(R)))
    return 2 ** math.log2(sum(a) / sum(b)), [2 ** vals[int(0.025 * R)], 2 ** vals[int(0.975 * R) - 1]]

assert hashlib.sha256(open(BIN, "rb").read()).hexdigest().startswith("1505efbffb20002326753d23a668d1c15f77a53d2b5577825a631330ca855a79"[:16])
V1 = json.load(open("../opclass/opclass_v1.json"))
W = {t: (c["weight"] if c["ops"] else 0.0) for t, c in V1["classes"].items()}
PR = optypes.prices()
RULE = ("opclass", "ruint", "montgomery")
ALL = ("opclass", "ruint", "montgomery", "official")

def cost(t, Pn):
    if Pn == "official":
        return float(sum(t.values()))
    if Pn == "opclass":
        return float(sum(W[k] * v for k, v in t.items() if v))
    return float(sum(PR[Pn][k] * v for k, v in t.items() if v))

def call(pr):
    if all(pr[Pn][1][1] < 1 for Pn in RULE):
        return "better"
    if all(pr[Pn][1][0] > 1 for Pn in RULE):
        return "worse"
    return "undecided"

out = {"v1": "df5a0e3", "rule": "robust = worst of op-class, ruint, Montgomery (option (b)); official reported, no veto", "sizes": {}}
SIZES = tuple(int(b) for b in ARGV) or (72, 84, 96)
for bits in SIZES:
    nums = S2.map_nums(bits)
    g0 = dict(ref(bits), goff=1)
    cells = {"2'a": g0, "2'b": dict(g0, confirm="root"), "2'b+pp3": dict(g0, confirm="root", pp=3)}
    runs = {n: run_many([g], nums, P.QS_CAP, types=True) for n, g in cells.items()}
    assert all(r[1] is not None for rs in runs.values() for r in rs)
    c = {n: {Pn: [cost(r[4], Pn) for r in rs] for Pn in ALL} for n, rs in runs.items()}
    tot = {n: {t: sum(r[4].get(t, 0) for r in rs) for t in optypes.TYPE_ORDER} for n, rs in runs.items()}
    rec = {}
    for cell in ("2'b", "2'b+pp3"):
        pr = {Pn: paired(c[cell][Pn], c["2'a"][Pn]) for Pn in ALL}
        robust = max(pr[Pn][0] for Pn in RULE)
        # (a) break-even sieve_update weight: rest_b + w U_b = rest_a + w U_a
        Ua, Ub = tot["2'a"]["sieve_update"], tot[cell]["sieve_update"]
        rest = {n: sum(W[t] * tot[n][t] for t in optypes.TYPE_ORDER if t != "sieve_update") for n in ("2'a", cell)}
        be_su = None if Ua == Ub else (rest[cell] - rest["2'a"]) / (Ua - Ub)
        # information: break-even root_test weight
        Ra, Rb = tot["2'a"]["root_test"], tot[cell]["root_test"]
        rest_r = {n: sum(W[t] * tot[n][t] for t in optypes.TYPE_ORDER if t != "root_test") for n in ("2'a", cell)}
        be_rt = None if Ra == Rb else (rest_r["2'a"] - rest_r[cell]) / (Rb - Ra)
        rec[cell] = {"ratios": {Pn: {"ratio": v[0], "ci95": v[1]} for Pn, v in pr.items()}, "robust": robust, "call": call(pr),
                     "breakeven_sieve_update_weight": be_su, "sieve_update_ops": [Ua, Ub],
                     "breakeven_root_test_weight": be_rt, "root_test_weight_v1": W["root_test"]}
        print(f"{bits} {cell} vs 2'a: " + " ".join(f"{Pn} {v[0]:.4f} [{v[1][0]:.4f}, {v[1][1]:.4f}]" for Pn, v in pr.items())
              + f"; robust (op-class, ruint, Montgomery) {robust:.4f}; (e) {call(pr)}", flush=True)
        print(f"     (a) sieve_update ops 2'a {Ua:,} / {cell} {Ub:,}: break-even sieve_update weight "
              + ("none (equal counts: the weight cancels)" if be_su is None else f"{be_su:.3f} (v1 {W['sieve_update']:.3f})")
              + f"; information: break-even root_test weight " + ("none" if be_rt is None else f"{be_rt:.2f} (v1 {W['root_test']:.2f}, x{be_rt / W['root_test']:.2f})"), flush=True)
    out["sizes"][str(bits)] = rec
json.dump(out, open("step3.json" if SIZES == (72, 84, 96) else f"step3_{"_".join(map(str, SIZES))}.json", "w"), indent=1)
