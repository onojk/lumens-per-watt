"""Acceptance test for the ledger's charged relation check (NOTES.md, "Ledger: the charged
relation check").

1. qs with the check on ("check": 1) vs off, on semiprimes_pq(bits, 40, 770000 + bits) at
   40-60 bits, cap 2^29, for default qs, tuned qs and tuned qs + lc 1.4. Every relation
   submitted to a ledger is logged by the harness (a wrapper around Ledger.add, not
   charged) and:
   - the measured "check" phase equals the formula recomputed here from the submitted
     relations alone, over a factor base rebuilt here (tolerance 0);
   - the relations rejected are exactly those the harness finds invalid or trivial
     (all even and u = +-Y mod N);
   - on a run with nothing rejected, everything else (ops minus check, factor, tests,
     hits, every other phase, the kept relations) equals the check-off run.
   Runs with rejections are counted and reported.
2. Injected relations (a ledger built directly, harness only): a valid full relation (kept),
   the same with u + 1 (invalid: rejected), a trivial all-even relation (rejected), and a
   nontrivial all-even one built by CRT from the known factors (kept; solve() alone on it
   splits N). Each is charged exactly the formula; with the check off all four are kept.
3. Mutation test (python3 ledger_accept.py WORKERS mutate): each check charge in ledger.py
   in turn gets one extra op; part 1's formula comparison must fail for every one.

  python3 ledger_accept.py [workers] [mutate]  -> ledger_accept.json (not in mutate mode)
"""
import json, math, sys, types
from multiprocessing import Pool
import qs, ledger, lamps
from lamps import run, LAST, Meter
from fastlamps import semiprimes_pq

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
MUTATE = len(sys.argv) > 2 and sys.argv[2] == "mutate"
SIZES = [40, 44, 48, 52, 56, 60]
COUNT = 40
CAP = 2 ** 29
QS = {"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}
TUNED = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}
GENOMES = {"default": QS, "tuned": TUNED, "tuned lc 1.4": dict(TUNED, lc=1.4)}

def pw(e):
    """Square-and-multiply ops for exponent e, as charged: bit_length + popcount - 1."""
    return e.bit_length() + bin(e).count("1") - 1

def base_of(N, k, bc):
    lnN = math.log(N)
    B = max(30, int(bc * math.exp(0.5 * math.sqrt(lnN * math.log(lnN)))))
    kN = k * N
    return [-1, 2] + [p for p in ledger._primes(B)[1:]
                      if kN % p == 0 or pow(kN % p, (p - 1) // 2, p) == 1]

def formula(N, base, u, vec, y):
    """(ops, verdict) of the check on one relation: verdict 'ok', 'invalid' or 'trivial'."""
    F = len(base)
    facs = [(base[j], vec[j]) for j in range(1, F) if vec[j]] + ([(y, 2)] if y != 1 else [])
    ops = 2 + sum(pw(e) for _, e in facs) + max(0, len(facs) - 1)
    ops += vec[0] & 1                              # sign
    ops += 1                                       # compare
    rhs = math.prod(pow(b, e, N) for b, e in facs) % N * (-1) ** (vec[0] & 1) % N
    if u * u % N != rhs:
        return ops, "invalid"
    ops += -(-F // 64)                             # parity scan
    if any(e & 1 for e in vec):
        return ops, "ok"
    half = [(b, e // 2) for b, e in facs]
    ops += sum(pw(e) for _, e in half) + max(0, len(half) - 1) + 2
    Y = math.prod(pow(b, e, N) for b, e in half) % N
    return ops, ("trivial" if u % N in (Y, (N - Y) % N) else "ok")

LOG = None

def logged_add(orig):
    def add(self, u, vec, y=1, check=False):
        if LOG is not None:
            LOG.append((self.k, u, list(vec), y, check))
        return orig(self, u, vec, y, check)
    return add

def one(mod, g, N):
    """Run genome g with module `mod` as qs; returns result, phases, kept relations, log."""
    global LOG
    lamps.LAMPS["qs"] = mod.lamp_qs
    LOG = []
    mod.TRACE = {}
    ops, d = run([g], N, CAP)
    tr = mod.TRACE
    out = dict(res=(ops, d, LAST["tests"], LAST["hits"]), ph=dict(tr["ops"]),
               rels=[r for at in tr["attempts"] for r in at.get("rels", [])],
               rejected=sum(at.get("rejected", 0) for at in tr["attempts"]), log=LOG)
    LOG = None
    return out

def compare(N, g, mod=qs):
    off = one(mod, g, N)
    on = one(mod, dict(g, check=1), N)
    bases = {}
    want, verdicts = 0, {"ok": 0, "invalid": 0, "trivial": 0}
    for k, u, vec, y, chk in on["log"]:
        assert chk
        if k not in bases:
            bases[k] = base_of(N, k, g["bc"])
        assert len(bases[k]) == len(vec), "factor base rebuilt differently"
        n, v = formula(N, bases[k], u, vec, y)
        want += n
        verdicts[v] += 1
    measured = on["ph"].get("check", 0)
    r = dict(N=str(N), check_ops=measured, formula=want, exact=measured == want,
             rejected=on["rejected"], harness_rejects=verdicts["invalid"] + verdicts["trivial"],
             verdicts=verdicts, submitted=len(on["log"]), off_check=off["ph"].get("check", 0))
    r["rejects_agree"] = r["rejected"] == r["harness_rejects"]
    if on["rejected"] == 0:
        ph_on = {k: v for k, v in on["ph"].items() if k != "check"}
        r["identity"] = (on["res"][0] - measured == off["res"][0] and on["res"][1:] == off["res"][1:]
                         and ph_on == off["ph"] and on["rels"] == off["rels"]
                         and [x[:4] for x in on["log"]] == [x[:4] for x in off["log"]])
    else:
        r["identity"] = None
    r["solved"] = on["res"][1] is not None and N % on["res"][1] == 0 and 1 < on["res"][1] < N
    return r

def job(args):
    ledger.Ledger.add = logged_add(ORIG_ADD)
    name, bits, (N, p, q) = args
    r = compare(N, GENOMES[name])
    r.update(genome=name, bits=bits)
    return r

ORIG_ADD = ledger.Ledger.add

def injected():
    """Part 2: hand-built relations into a ledger at 48 bits (k = 1, tuned bc)."""
    N, p, q = semiprimes_pq(48, 1, 4242)[0]
    out = {}
    for chk in (True, False):
        m = Meter(CAP)
        tr = {"ops": {}}
        led = ledger.Ledger(N, 1, int(1.1 * math.exp(0.5 * math.sqrt(math.log(N) * math.log(math.log(N))))),
                            ledger.Charger(m, tr))
        if led.build_base():
            raise SystemExit("factor base found a factor; pick another seed")
        base, F = led.base, led.F
        def vec_of(v):
            vec = [0] * F
            if v < 0:
                vec[0], v = 1, -v
            for j in range(1, F):
                while v % base[j] == 0:
                    v //= base[j]; vec[j] += 1
            return vec if v == 1 else None
        t = math.isqrt(N) + 1
        while True:                                # a smooth u^2 - N: a valid full relation
            vec = vec_of(t * t - N)
            if vec and any(e & 1 for e in vec):
                break
            t += 1
        p1, p2 = base[2], base[3]
        triv = [0] * F; triv[2] = 2; triv[3] = 2
        Y = p1 * p2 % N
        u_nt = (Y * q * pow(q, -1, p) - Y * p * pow(p, -1, q)) % N   # = Y mod p, -Y mod q
        cases = [("valid", t, vec), ("invalid", t + 1, vec), ("trivial all-even", p1 * p2, triv),
                 ("nontrivial all-even", u_nt, triv)]
        res = {}
        for name, u, v in cases:
            before = tr["ops"].get("check", 0)
            n_rels = len(led.rels)
            led.add(u, list(v), 1, chk)
            ops = tr["ops"].get("check", 0) - before
            fo, verdict = formula(N, base, u, v, 1)
            res[name] = dict(kept=len(led.rels) > n_rels, ops=ops,
                             formula=fo if chk else 0, verdict=verdict)
        if chk:                                    # solve() on the nontrivial all-even relation alone
            led.rels[:] = [r for r in led.rels if r[0] == u_nt]
            d = led.solve()
            res["nontrivial all-even"]["splits"] = d in (p, q)
        out["check on" if chk else "check off"] = res
    on, off = out["check on"], out["check off"]
    ok = (all(r["ops"] == r["formula"] for r in on.values())
          and [on[c]["kept"] for c in on] == [True, False, False, True]
          and on["nontrivial all-even"]["splits"]
          and all(r["kept"] and r["ops"] == 0 for r in off.values()))
    return out, ok

CHECK_CHARGES = [                                  # (name, exact source line in ledger.py, mutated)
    ("u^2", 'lhs, _ = ch.cpow(u, 2, N, "check")', 'lhs, _ = ch.cpow(u, 2, N, "check"); ch.charge("check", 1)'),
    ("factor power", 'v, _ = ch.cpow(b, e, N, "check")', 'v, _ = ch.cpow(b, e, N, "check"); ch.charge("check", 1)'),
    ("join", 'r = r * v % N; ch.charge("check", 1)', 'r = r * v % N; ch.charge("check", 2)'),
    ("sign", 'rhs = (N - rhs) % N; ch.charge("check", 1)', 'rhs = (N - rhs) % N; ch.charge("check", 2)'),
    ("compare", 'ch.charge("check", 1)                      # compare', 'ch.charge("check", 2)'),
    ("parity scan", 'ch.charge("check", -(-self.F // 64))', 'ch.charge("check", -(-self.F // 64) + 1)'),
    ("trivial compares", 'ch.charge("check", 2)                      # u = Y', 'ch.charge("check", 3)  # u = Y'),
]

def mutate_job(args):
    name, line, new = args
    src = open(ledger.__file__).read()
    assert src.count(line) == 1, line
    led = types.ModuleType("ledger")
    exec(compile(src.replace(line, new), ledger.__file__, "exec"), led.__dict__)
    sys.modules["ledger"] = led
    led.Ledger.add = logged_add(led.Ledger.add)
    mod = types.ModuleType("qs_mutant")
    exec(compile(open(qs.__file__).read(), qs.__file__, "exec"), mod.__dict__)
    caught = runs = 0
    # the trivial test runs only on all-even relations: tuned lc 1.4 at 40 bits produces them
    # (12 of 40 runs), and semiprimes_pq(52, 2, 11)[1] is a known case
    cases = [(GENOMES[g], N) for g in ("tuned", "tuned lc 1.4") for bits in (48, 56)
             for N, p, q in semiprimes_pq(bits, 3, 770000 + bits)]
    cases += [(GENOMES["tuned lc 1.4"], N) for N, p, q in semiprimes_pq(40, 10, 770040)]
    cases += [(GENOMES["tuned lc 1.4"], semiprimes_pq(52, 2, 11)[1][0])]
    for g, N in cases:
        r = compare(N, g, mod)
        runs += 1
        caught += not r["exact"]
    return name, runs, caught

if __name__ == "__main__":
    if MUTATE:
        with Pool(WORKERS) as pool:
            res = pool.map(mutate_job, CHECK_CHARGES)
        ok = True
        for name, runs, caught in res:
            print(f"mutated {name:16s}: check formula failed on {caught}/{runs} runs "
                  f"({'caught' if caught else 'MISSED'})")
            ok &= caught > 0
        print("MUTATION TEST", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    inj, inj_ok = injected()
    for mode, res in inj.items():
        for name, r in res.items():
            print(f"injected ({mode}) {name:20s}: kept {r['kept']}, check ops {r['ops']} "
                  f"(formula {r['formula']}, {r['verdict']})" + (f", splits N {r['splits']}" if "splits" in r else ""))
    print("injected relations:", "PASS" if inj_ok else "FAIL")
    jobs = [(name, b, x) for name in GENOMES for b in SIZES for x in semiprimes_pq(b, COUNT, 770000 + b)]
    with Pool(WORKERS) as pool:
        res = pool.map(job, jobs, chunksize=4)
    out = {"cap_log2": 29, "seed": "770000 + bits", "count": COUNT, "genomes": GENOMES,
           "injected": inj, "injected_pass": inj_ok, "results": {}}
    all_ok = inj_ok
    for name in GENOMES:
        out["results"][name] = {}
        for b in SIZES:
            r = [x for x in res if x["genome"] == name and x["bits"] == b]
            exact = sum(x["exact"] for x in r)
            agree = sum(x["rejects_agree"] for x in r)
            rej_runs = [x for x in r if x["rejected"]]
            ident = sum(1 for x in r if x["identity"])
            solved = sum(x["solved"] for x in r)
            ok = (exact == len(r) and agree == len(r) and ident == len(r) - len(rej_runs)
                  and solved == len(r) and all(x["off_check"] == 0 for x in r))
            all_ok &= ok
            s = dict(n=len(r), solved=solved, exact=exact, rejects_agree=agree,
                     identity_runs=ident, runs_with_rejections=len(rej_runs),
                     rejected=sum(x["rejected"] for x in r),
                     invalid=sum(x["verdicts"]["invalid"] for x in r),
                     trivial=sum(x["verdicts"]["trivial"] for x in r),
                     submitted=sum(x["submitted"] for x in r),
                     check_ops=sum(x["check_ops"] for x in r), pass_=ok)
            out["results"][name][b] = s
            print(f"{name:13s} {b} bits: solved {solved}/{len(r)}, check exact {exact}/{len(r)}, "
                  f"rejections agree {agree}/{len(r)}, identity {ident}/{len(r) - len(rej_runs)} "
                  f"(runs with rejections {len(rej_runs)}: {s['trivial']} trivial, {s['invalid']} invalid), "
                  f"submitted {s['submitted']}, check ops {s['check_ops']}  {'PASS' if ok else 'FAIL'}",
                  flush=True)
    out["pass"] = all_ok
    json.dump(out, open("ledger_accept.json", "w"), indent=1)
    print("ACCEPTANCE", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)
