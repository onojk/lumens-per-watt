"""Acceptance test for Stage 7's large-prime variation (NOTES.md, "Stage 7").

Genome: the pre-registered one, tuned qs with lc 1.4 (kc 32, bc 1.1, mc 0.25, tc 1.38).

1. Completeness: cap 2^29, factors every one of semiprimes_pq(bits, 40, 770000 + bits) at
   40, 44, 48, 52, 56, 60 bits.
2. Exact accounting: every phase, lp included, equals its formula recomputed from the run's
   raw inputs (qs_accept.formulas for phases 1-7; here, the lp phase and the large primes
   multiplied into Y). The lp formula never reads the lamp's own counters: it re-derives
   each candidate's cofactor by trial division over the independently rebuilt factor base,
   recomputes L = B^lc, and replays the hash table over the cofactors in order:
   1 per cofactor > 1, 2 per cofactor below L (N mod q, lookup), 1 per first occurrence of
   q (insert), 1 + F per repeat (combine). Tolerance 0.
3. Relation check (harness only, not charged): every relation kept satisfies
   u^2 = y^2 prod p^e (mod N) (y = q for a combined relation, 1 for a full one), and every
   dependency tried satisfies X^2 = Y^2 (mod N).
4. Mutation test (python3 stage7_accept.py WORKERS mutate): each lp charge in qs.py in turn
   gets one extra op; the accounting must fail on the mutated card for every one of them.

  python3 stage7_accept.py [workers] [mutate]

Writes stage7_accept.json (not in mutate mode).
"""
import json, math, re, sys, types
from multiprocessing import Pool
import qs
import lamps
from lamps import run
from fastlamps import semiprimes_pq
from qs_accept import formulas, PHASES as QS_PHASES

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
MUTATE = len(sys.argv) > 2 and sys.argv[2] == "mutate"
SIZES = [40, 44, 48, 52, 56, 60]
COUNT = 40
CAP = 2 ** 29
GENOME = [{"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}]
PHASES = QS_PHASES[:5] + ["lp"] + QS_PHASES[5:]

def B_of(N):
    lnN = math.log(N)
    return max(30, int(GENOME[0]["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))

def base_of(N, at):
    """The attempt's factor base, rebuilt from N, k and B independently of the lamp."""
    kN = at["k"] * N
    out = [-1, 2]
    for p in qs._primes(B_of(N))[1:]:
        if kN % p == 0 or pow(kN % p, (p - 1) // 2, p) == 1:
            out.append(p)
    assert len(out) == at["F"], (len(out), at["F"])
    return out

def lp_formula(N, at, base):
    L = B_of(N) ** GENOME[0]["lc"]
    F = len(base)
    ops, seen_q = 0, set()
    for v in at["cands"]:
        v = abs(v)
        if not v:
            continue
        for p in base[1:]:
            while v % p == 0:
                v //= p
        if v == 1:
            continue
        ops += 1                                   # bound check
        if not v < L:
            continue
        ops += 1                                   # N mod q
        if N % v == 0:
            break                                  # qs returns q
        ops += 1                                   # lookup
        if v in seen_q:
            ops += 1 + F                           # combine
        else:
            seen_q.add(v); ops += 1                # insert
    return ops

def relation_check(N, at, base):
    bad_rel = bad_dep = 0
    for u, vec, y in at["rels"]:
        rhs = y * y % N
        for j, e in enumerate(vec):
            if e:
                rhs = rhs * pow(base[j] % N, e, N) % N
        bad_rel += u * u % N != rhs
    for d in at["deps"]:
        bad_dep += d["X"] * d["X"] % N != d["Y"] * d["Y"] % N
    return len(at["rels"]), bad_rel, len(at["deps"]), bad_dep

def check(N, d, ops, tr):
    for at in tr["attempts"]:
        for dd in at["deps"]:
            dd["N"] = N
    bases = {id(at): base_of(N, at) for at in tr["attempts"]}
    f, model = formulas(tr, lambda at: bases[id(at)])
    f["lp"] = sum(lp_formula(N, at, bases[id(at)]) for at in tr["attempts"])
    f["sqrt"] += sum(1 for at in tr["attempts"] for dd in at["deps"]
                     for i in dd["idx"] if at["rels"][i][2] != 1)
    measured = {ph: tr["ops"].get(ph, 0) for ph in PHASES}
    rc = [relation_check(N, at, bases[id(at)]) for at in tr["attempts"]]
    lp = {k: sum(at["lp"][k] for at in tr["attempts"]) for k in ("cof", "lt", "inserts", "combos", "dup")}
    return {"measured": measured, "formula": {ph: f[ph] for ph in PHASES},
            "exact": measured == {ph: f[ph] for ph in PHASES}
                     and (ops is None or sum(measured.values()) == ops),
            "rels": sum(x[0] for x in rc), "bad_rels": sum(x[1] for x in rc),
            "combined": sum(1 for at in tr["attempts"] for r in at["rels"] if r[2] != 1),
            "deps": sum(x[2] for x in rc), "bad_deps": sum(x[3] for x in rc), "lp": lp,
            "model": model}

def job(args):
    bits, (N, p, q) = args
    qs.TRACE = {}
    ops, d = run(GENOME, N, CAP)
    r = check(N, d, ops, qs.TRACE)
    r.update(bits=bits, N=str(N), ops=ops, attempts=len(qs.TRACE["attempts"]),
             factor_ok=d is not None and 1 < d < N and N % d == 0)
    return r

LP_CHARGES = [                                     # (name, exact source line) of each lp charge
    ("bound check", 'charge("lp", 1)                # bound check'),
    ("N mod q", 'charge("lp", 1)                # N mod q'),
    ("lookup", 'charge("lp", 1)                # hash lookup'),
    ("insert", 'charge("lp", 1)            # insert'),
    ("combine u1*u2", 'cu = other[0] * u % N; charge("lp", 1)'),
    ("combine F", 'charge("lp", F)'),
    ("y into Y", 'Y = Y * rels[i][2] % N; charge("sqrt", 1)'),
]

def mutant(line):
    """qs.py with one charge on `line` raised by one op, as a fresh module."""
    src = open(qs.__file__).read()
    assert src.count(line) == 1, line
    new = re.sub(r'charge\("(\w+)", (\w+)\)', r'charge("\1", \2 + 1)', line)
    mod = types.ModuleType("qs_mutant")
    exec(compile(src.replace(line, new), qs.__file__, "exec"), mod.__dict__)
    return mod

def mutate_job(args):
    name, line = args
    mod = mutant(line)
    lamps.LAMPS["qs"] = mod.lamp_qs                # run() dispatches through LAMPS
    caught = runs = 0
    for bits in (48, 56, 60):
        for N, p, q in semiprimes_pq(bits, 4, 770000 + bits):
            mod.TRACE = {}
            ops, d = run(GENOME, N, CAP)
            r = check(N, d, ops, mod.TRACE)
            runs += 1
            caught += not r["exact"]
    return name, runs, caught

if __name__ == "__main__":
    if MUTATE:
        with Pool(WORKERS) as pool:
            res = pool.map(mutate_job, LP_CHARGES)
        ok = True
        for name, runs, caught in res:
            print(f"mutated {name:14s}: accounting failed on {caught}/{runs} runs "
                  f"({'caught' if caught else 'MISSED'})")
            ok &= caught > 0
        print("MUTATION TEST", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    jobs = [(b, x) for b in SIZES for x in semiprimes_pq(b, COUNT, 770000 + b)]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs)
    out = {"genome": GENOME, "cap_log2": 29, "seed": "770000 + bits", "count": COUNT, "sizes": {}}
    all_ok = True
    for b in SIZES:
        r = [x for x in res if x["bits"] == b]
        solved = sum(x["factor_ok"] for x in r)
        exact = sum(x["exact"] for x in r)
        bad = sum(x["bad_rels"] + x["bad_deps"] for x in r)
        ok = solved == len(r) and exact == len(r) and bad == 0
        all_ok &= ok
        ops = [x["ops"] for x in r if x["ops"]]
        lp = {k: sum(x["lp"][k] for x in r) for k in r[0]["lp"]}
        out["sizes"][b] = {"solved": solved, "exact_runs": exact, "n": len(r),
                           "retries": sum(x["attempts"] - 1 for x in r),
                           "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
                           "measured": {ph: sum(x["measured"][ph] for x in r) for ph in PHASES},
                           "formula": {ph: sum(x["formula"][ph] for x in r) for ph in PHASES},
                           "relations": sum(x["rels"] for x in r),
                           "combined": sum(x["combined"] for x in r),
                           "bad_relations": sum(x["bad_rels"] for x in r),
                           "dependencies": sum(x["deps"] for x in r),
                           "bad_dependencies": sum(x["bad_deps"] for x in r),
                           "lp": lp, "pass": ok}
        s = out["sizes"][b]
        print(f"{b} bits: solved {solved}/{len(r)}, exact {exact}/{len(r)}, relations "
              f"{s['relations']} ({s['combined']} combined), bad {s['bad_relations']}, "
              f"dependencies {s['dependencies']}, bad {s['bad_dependencies']}, partials {lp['lt']}, "
              f"retries {s['retries']}, mean 2^{s['mean_log2']:.2f}  {'PASS' if ok else 'FAIL'}",
              flush=True)
        for ph in PHASES:
            print(f"    {ph:8s} measured {s['measured'][ph]:>12d}  formula {s['formula'][ph]:>12d}")
    out["pass"] = all_ok
    json.dump(out, open("stage7_accept.json", "w"), indent=1)
    print("ACCEPTANCE", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)
