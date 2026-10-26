"""Acceptance test for the CFRAC card (NOTES.md, "CFRAC as a second relation source").

Genome: cfrac with tuned qs's kc 32 and bc 1.1 (the genes NOTES's prediction assumes).

1. Completeness: cap 2^29, factors every one of semiprimes_pq(bits, 40, 770000 + bits) at
   40, 44, 48, 52, 56, 60 bits.
2. Exact accounting: every phase equals its formula, tolerance 0. cf_step and cf_td are
   recomputed from an independent replay of the expansion of sqrt(kN) for each attempt's k
   (the harness's own recurrence, trial division over a factor base rebuilt here, dedupe,
   and the stop rule: ledger full at F + 10 relations, or Q = 1); the replay's residues
   must also equal the lamp's. mult, fb, la and sqrt use qs_accept's formulas.
3. Relation check (harness only): every relation kept satisfies u^2 = prod p^e (mod N), and
   every dependency tried satisfies X^2 = Y^2 (mod N).
4. Mutation test (python3 cfrac_accept.py WORKERS mutate): each cfrac charge in turn gets
   one extra op; the accounting must fail for every one.

  python3 cfrac_accept.py [workers] [mutate]  -> cfrac_accept.json (not in mutate mode)
"""
import json, math, sys, types
from multiprocessing import Pool
import cfrac, ledger, lamps
import lamps
from lamps import Meter, Budget, KS_PRIMES
from fastlamps import semiprimes_pq
from qs_accept import sqm, ts_count, euclid_steps

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
MUTATE = len(sys.argv) > 2 and sys.argv[2] == "mutate"
SIZES = [40, 44, 48, 52, 56, 60]
COUNT = 40
CAP = 2 ** 29
GENE = {"t": "cfrac", "kc": 32, "bc": 1.1}
PHASES = ["mult", "fb", "cf_step", "cf_td", "la", "sqrt", "hash", "word"]   # hash, word: the ledger's duplicate check

def base_of(N, k):
    lnN = math.log(N)
    B = max(30, int(GENE["bc"] * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    kN = k * N
    return [-1, 2] + [p for p in ledger._primes(B)[1:]
                      if kN % p == 0 or pow(kN % p, (p - 1) // 2, p) == 1]

def replay(N, k, base):
    """(cf_step ops, cf_td ops, residues, rows, smooth relations offered to the ledger) for one attempt."""
    kN, F = k * N, len(base)
    g = math.isqrt(kN)
    step, td, residues, seen, rows, offers, tsum = kN.bit_length(), 0, [], set(), 0, 0, 0
    if g * g == kN:
        return step, td, residues, rows, (offers, tsum)
    # the convergent recurrence written out again: x_i = (sqrt(kN) + P_i) / Q_i
    Ps, Qs, As = [0], [1], [g % N]
    Qm1, Am1 = kN, 1
    while True:
        i = len(Ps) - 1
        a = (g + Ps[i]) // Qs[i]
        P = a * Qs[i] - Ps[i]
        Q = (kN - P * P) // Qs[i]                  # the long form, not the lamp's
        assert Q == (Qs[i - 1] if i else Qm1) + a * (Ps[i] - P)
        step += 4
        if Q == 1:
            return step, td, residues, rows, (offers, tsum)
        residues.append(Q)
        td += F
        v, smooth = Q, True
        touched = (i + 1) & 1                      # the sign entry, then each dividing prime (step 1)
        for p in base[1:]:
            e = 0
            while v % p == 0:
                v //= p; e += 1
            td += max(0, e - 1)
            touched += e > 0
        u = As[i]
        offers += v == 1                           # each smooth residue: 1 hash + 1 word (duplicate check)
        tsum += (v == 1) * touched                 # and |T| word for its sparse copy (step 1)
        if v == 1 and u not in seen:
            seen.add(u); rows += 1
            if rows >= F + ledger.DELTA:
                return step, td, residues, rows, (offers, tsum)
        a1 = (g + P) // Q
        As.append((a1 * As[i] + (As[i - 1] if i else Am1)) % N)
        Ps.append(P); Qs.append(Q)

def check(N, tr):
    f = dict.fromkeys(PHASES, 0)
    _, (mu, wo, fl) = lamps.ks_rank(N, range(1, tr["k_cands"] + 1))   # I-021: one lump (cfrac is untyped)
    f["mult"] = mu + wo + fl
    rels = bad_rel = deps = bad_dep = 0
    residues_ok = True
    for at in tr["attempts"]:
        f["fb"] += sum(sqm(e) for e in at["euler_e"]) + sum(ts_count(n, p) for n, p, _ in at["ts"])
        if "rels" not in at:                       # factor base found a factor
            continue
        base = base_of(N, at["k"])
        assert len(base) == at["F"], "factor base rebuilt differently"
        s, t, res, rows, offers = replay(N, at["k"], base)
        f["cf_step"] += s; f["cf_td"] += t; f["hash"] += offers[0]; f["word"] += offers[0] + offers[1]
        if at["rows"]:
            f["word"] += sum(len(vec) for _, vec, _ in at["rels"])   # GF(2) rows built from the sparse relations
        residues_ok &= res == at["residues"]
        if at["rows"]:
            f["la"] += -(-at["rows"] * at["F"] * at["rows"] // 64)
        for d in at["deps"]:
            f["sqrt"] += (d["members"] - 1) + sum(sqm(h) for h in d["h"]) + max(0, len(d["h"]) - 1)
            f["sqrt"] += euclid_steps(d["xy"], N)
            deps += 1
            bad_dep += d["X"] * d["X"] % N != d["Y"] * d["Y"] % N
        for u, vec, y in at["rels"]:
            rels += 1
            rhs = y * y % N
            for j, e in vec:                       # sparse (step 1)
                rhs = rhs * pow(base[j] % N, e, N) % N
            bad_rel += u * u % N != rhs
    measured = {ph: tr["ops"].get(ph, 0) for ph in PHASES}
    return dict(measured=measured, formula=f, exact=measured == f and residues_ok,
                residues_ok=residues_ok, rels=rels, bad_rels=bad_rel, deps=deps, bad_deps=bad_dep)

def run_one(mod, N):
    m = Meter(CAP)
    mod.TRACE = {}
    try:
        d = mod.lamp_cfrac(N, GENE, m)
    except Budget:
        d = None
    tr = mod.TRACE
    mod.TRACE = None
    return m.ops, d, tr

def job(args):
    bits, (N, p, q) = args
    ops, d, tr = run_one(cfrac, N)
    r = check(N, tr)
    r.update(bits=bits, N=str(N), ops=ops, attempts=len(tr["attempts"]),
             solved=d is not None and 1 < d < N and N % d == 0,
             period_ends=sum(at.get("period_end", False) for at in tr["attempts"]),
             residues=sum(len(at.get("residues", [])) for at in tr["attempts"]),
             smooth=sum(len(at.get("rels", [])) for at in tr["attempts"]))
    r["exact"] &= sum(r["measured"].values()) == ops
    return r

CHARGES = [                                        # (name, exact source line in cfrac.py, mutated)
    ("isqrt", 'charge("cf_step", kN.bit_length())', 'charge("cf_step", kN.bit_length() + 1)'),
    ("step", 'charge("cf_step", 4)', 'charge("cf_step", 5)'),
    ("trial division", 'charge("cf_td", F)', 'charge("cf_td", F + 1)'),
    ("extra division", 'v //= p; vec[j] += 1; charge("cf_td", 1)', 'v //= p; vec[j] += 1; charge("cf_td", 2)'),
]

def mutate_job(args):
    name, line, new = args
    src = open(cfrac.__file__).read()
    assert src.count(line) == 1, line
    mod = types.ModuleType("cfrac_mutant")
    exec(compile(src.replace(line, new), cfrac.__file__, "exec"), mod.__dict__)
    caught = runs = 0
    for bits in (48, 56, 60):
        for N, p, q in semiprimes_pq(bits, 4, 770000 + bits):
            ops, d, tr = run_one(mod, N)
            r = check(N, tr)
            runs += 1
            caught += not (r["exact"] and sum(r["measured"].values()) == ops)
    return name, runs, caught

if __name__ == "__main__":
    if MUTATE:
        with Pool(WORKERS) as pool:
            res = pool.map(mutate_job, CHARGES)
        ok = True
        for name, runs, caught in res:
            print(f"mutated {name:15s}: accounting failed on {caught}/{runs} runs "
                  f"({'caught' if caught else 'MISSED'})")
            ok &= caught > 0
        print("MUTATION TEST", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    jobs = [(b, x) for b in SIZES for x in semiprimes_pq(b, COUNT, 770000 + b)]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs)
    out = {"genome": GENE, "cap_log2": 29, "seed": "770000 + bits", "count": COUNT, "sizes": {}}
    all_ok = True
    for b in SIZES:
        r = [x for x in res if x["bits"] == b]
        solved = sum(x["solved"] for x in r)
        exact = sum(x["exact"] for x in r)
        bad = sum(x["bad_rels"] + x["bad_deps"] for x in r)
        ok = solved == len(r) and exact == len(r) and bad == 0
        all_ok &= ok
        ops = [x["ops"] for x in r if x["solved"]]
        s = {"n": len(r), "solved": solved, "exact_runs": exact,
             "retries": sum(x["attempts"] - 1 for x in r),
             "period_ends": sum(x["period_ends"] for x in r),
             "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
             "measured": {ph: sum(x["measured"][ph] for x in r) for ph in PHASES},
             "formula": {ph: sum(x["formula"][ph] for x in r) for ph in PHASES},
             "residues": sum(x["residues"] for x in r), "smooth": sum(x["smooth"] for x in r),
             "relations": sum(x["rels"] for x in r), "bad_relations": sum(x["bad_rels"] for x in r),
             "dependencies": sum(x["deps"] for x in r), "bad_dependencies": sum(x["bad_deps"] for x in r),
             "pass": ok}
        out["sizes"][b] = s
        print(f"{b} bits: solved {solved}/{len(r)}, exact {exact}/{len(r)}, relations "
              f"{s['relations']}, bad {s['bad_relations']}, dependencies {s['dependencies']}, "
              f"bad {s['bad_dependencies']}, residues {s['residues']} (smooth rate "
              f"{s['smooth'] / max(1, s['residues']):.4f}), retries {s['retries']}, period ends "
              f"{s['period_ends']}, mean 2^{s['mean_log2']:.2f}  {'PASS' if ok else 'FAIL'}", flush=True)
        for ph in PHASES:
            print(f"    {ph:8s} measured {s['measured'][ph]:>12d}  formula {s['formula'][ph]:>12d}")
    out["pass"] = all_ok
    json.dump(out, open("cfrac_accept.json", "w"), indent=1)
    print("ACCEPTANCE", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)
