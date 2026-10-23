"""Acceptance test for the quadratic-sieve card (NOTES.md, "Quadratic-sieve card").

1. Completeness: qs alone, cap 2^29, factors every one of semiprimes_pq(bits, 40,
   770000 + bits) at 40, 44, 48, 52, 56, 60 bits.
2. Exact accounting: on every run, each phase's measured ops equal its written formula,
   recomputed here from the run's raw inputs (exponents, Tonelli-Shanks inputs, inverse
   arguments, sieve roots, candidate values, dependency data). Tolerance 0.
3. Model agreement: per size, total sieve updates within 5% of
   sum over polynomials of (2M + 1) * sum_{sieved p} r_p / p, and root switches equal
   to sum of r_p per new B.

  python3 qs_accept.py [workers]

Writes qs_accept.json.
"""
import json, math, sys
from multiprocessing import Pool
import qs
from lamps import run, LAST, KS_PRIMES
from fastlamps import semiprimes_pq

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
SIZES = [40, 44, 48, 52, 56, 60]
COUNT = 40
CAP = 2 ** 29
GENOME = [{"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}]
PHASES = ["mult", "fb", "setup", "sieve", "confirm", "la", "sqrt"]

def sqm(e):
    """Square-and-multiply charge for exponent e."""
    return e.bit_length() + bin(e).count("1") - 1

def euclid_steps(a, b):
    steps = 0
    while b:
        a, b = b, a % b
        steps += 1
    return steps

def ts_count(n, p):
    """Tonelli-Shanks modular multiplies, recounted independently."""
    if p % 4 == 3:
        return sqm((p + 1) // 4)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2; s += 1
    c, z = 0, 2
    while True:
        c += sqm((p - 1) // 2)
        if pow(z, (p - 1) // 2, p) == p - 1:
            break
        z += 1
    c += sqm(q) + sqm(q) + sqm((q + 1) // 2)
    cz, t, mm = pow(z, q, p), pow(n, q, p), s
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p; i += 1
        b = pow(cz, 1 << (mm - i - 1), p)
        c += i + (mm - i - 1) + 3
        cz = b * b % p; t = t * cz % p; mm = i
    return c

def hits_in(r, p, M):
    """How many x in [-M, M] have x = r (mod p)."""
    return (M - r) // p - (-M - 1 - r) // p

def formulas(tr, base_of):
    f = dict.fromkeys(PHASES, 0)
    f["mult"] = tr["k_cands"] * len(KS_PRIMES)
    model = {"upd": 0, "upd_expected": 0.0, "switch": 0, "switch_expected": 0}
    for at in tr["attempts"]:
        f["fb"] += sum(sqm(e) for e in at["euler_e"])
        f["fb"] += sum(ts_count(n, p) for n, p, _ in at["ts"])
        s = at["s"]
        f["setup"] += (s - 1) * at["combos"]
        f["setup"] += sum(euclid_steps(mod, a % mod) for a, mod, _ in at["inv"])
        f["setup"] += at["a_count"] * s * 3                      # A/q_l, gamma, B_l per l
        f["setup"] += at["n_sieved_setup"] * (2 + s)             # 2 roots, s values 2 B_l A^-1
        polys = at["polys"]
        for i, pl in enumerate(polys):
            M = pl["M"]
            f["sieve"] += sum(hits_in(r, p, M) for p, r in pl["roots"]) + 2 * M + 1
            model["upd"] += pl["upd"]
            model["upd_expected"] += (2 * M + 1) * sum(pl["rp"][p] / p for p in pl["sieved"])
        f["setup"] += sum(at["switches_roots"])
        model["switch"] += sum(at["switches_roots"])
        # every switch updates every root of every sieved prime of its A
        sw_exp = 0
        per_a = 1 << (s - 1) if s else 1
        for a_i in range(0, len(polys), per_a):
            roots = sum(polys[a_i]["rp"].values())
            sw_exp += roots * (min(per_a, len(polys) - a_i) - 1)
        model["switch_expected"] += sw_exp
        F = at["F"]
        base = base_of(at)
        for v in at["cands"]:
            f["confirm"] += 2 + F
            v = abs(v)
            if v:
                for p in base[1:]:
                    e = 0
                    while v % p == 0:
                        v //= p; e += 1
                    f["confirm"] += max(0, e - 1)
        rows = at["rows"]
        if rows:
            f["la"] += -(-rows * F * rows // 64)
        for d in at["deps"]:
            f["sqrt"] += (d["members"] - 1) + sum(sqm(h) for h in d["h"]) + max(0, len(d["h"]) - 1)
            f["sqrt"] += euclid_steps(d["xy"], d["N"])
    return f, model

def job(args):
    bits, (N, p, q) = args
    qs.TRACE = {}
    ops, d = run(GENOME, N, CAP)
    tr = qs.TRACE
    for at in tr["attempts"]:
        for dd in at["deps"]:
            dd["N"] = N
    def base_of(at):
        # rebuild the attempt's factor base from N, k, and B, independently of the lamp
        k = at["k"]; kN = k * N
        lnN = math.log(N)
        B = max(30, int(GENOME[0]["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
        out = [-1, 2]
        for pp in qs._primes(B)[1:]:
            if kN % pp == 0 or pow(kN % pp, (pp - 1) // 2, pp) == 1:
                out.append(pp)
        assert len(out) == at["F"], (len(out), at["F"])
        return out
    f, model = formulas(tr, base_of)
    measured = {ph: tr["ops"].get(ph, 0) for ph in PHASES}
    return {"bits": bits, "N": str(N), "ops": ops, "factor_ok": d is not None and N % d == 0 and 1 < d < N,
            "attempts": len(tr["attempts"]), "measured": measured, "formula": f,
            "total_ok": ops is None or sum(measured.values()) == ops, "model": model}

if __name__ == "__main__":
    jobs = [(b, x) for b in SIZES for x in semiprimes_pq(b, COUNT, 770000 + b)]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs)
    out = {"genome": GENOME, "cap_log2": 29, "seed": "770000 + bits", "count": COUNT, "sizes": {}}
    all_ok = True
    for b in SIZES:
        r = [x for x in res if x["bits"] == b]
        solved = sum(1 for x in r if x["factor_ok"])
        exact = sum(1 for x in r if x["measured"] == x["formula"] and x["total_ok"])
        meas = {ph: sum(x["measured"][ph] for x in r) for ph in PHASES}
        form = {ph: sum(x["formula"][ph] for x in r) for ph in PHASES}
        upd = sum(x["model"]["upd"] for x in r); upd_e = sum(x["model"]["upd_expected"] for x in r)
        sw = sum(x["model"]["switch"] for x in r); sw_e = sum(x["model"]["switch_expected"] for x in r)
        ok = solved == len(r) and exact == len(r) and abs(upd / upd_e - 1) <= 0.05 and sw == sw_e
        all_ok &= ok
        ops = [x["ops"] for x in r if x["ops"]]
        out["sizes"][b] = {"solved": solved, "exact_runs": exact, "n": len(r),
                           "retries": sum(x["attempts"] - 1 for x in r),
                           "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
                           "measured": meas, "formula": form,
                           "sieve_updates": upd, "sieve_updates_expected": upd_e,
                           "root_switches": sw, "root_switches_expected": sw_e, "pass": ok}
        print(f"{b} bits: solved {solved}/{len(r)}, exact {exact}/{len(r)}, "
              f"sieve updates {upd} vs {upd_e:.0f} ({100 * (upd / upd_e - 1):+.2f}%), "
              f"switches {sw} vs {sw_e}, mean 2^{out['sizes'][b]['mean_log2']:.2f}  "
              f"{'PASS' if ok else 'FAIL'}", flush=True)
        for ph in PHASES:
            print(f"    {ph:8s} measured {meas[ph]:>12d}  formula {form[ph]:>12d}")
    out["pass"] = all_ok
    json.dump(out, open("qs_accept.json", "w"), indent=1)
    print("ACCEPTANCE", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)
