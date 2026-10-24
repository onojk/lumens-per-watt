"""Per-stage op budget ("ob") acceptance (NOTES.md, "Per-stage op budget"), Python side.

For every lamp X (race_accept.LAMP_CASES), on two numbers per size, in the genome [X, Y]
(Y = rho below 40 bits, tuned qs from 40 bits), each expectation composed from X and Y run
alone on a recording meter:
  - ob absent: X finds -> X alone; X ends -> X alone's ops plus Y alone's;
  - ob = 0: Y alone, winning stage index 1, X runs no code;
  - ob = T, T + 1, 2T (T = X's natural total): the same as ob absent, op for op,
    including the per-phase ops;
  - ob = b below T (b = 1, T // 3, T - 1): the charge sequence is X's prefix up to and
    including the first charge that takes it past b, then Y's whole sequence; ops = that
    prefix + Y alone's; overshoot 1 <= spent - b <= the passing charge (so at most X's
    largest single charge: NOTES, correction); the stage is recorded as ended by its budget.
    Except where the stage's precheck reads the budget (ps: its product trees' minimum
    charge (B - 1) + (blocks - 1) exceeds b; pm1 past 2^26): it then ends before any charge,
    with 0 spent, and the genome equals Y alone.
Plus: a ps stage with a large block (product trees of many GB) and ob = 1000, and a pm1
stage with a bound past 2^32 and ob = 1000, under a cap of 2^40: the precheck reads the
budget, so each ends before allocating (asserted with a spy), with 0 ops spent, and the
genome equals qs alone. A cap inside a budgeted stage is a miss (the cap wins); bad genomes (negative or
non-integer ob, ob on a race or its side) are rejected before any op; and the mutation test:
an ob that never ends the stage (lamps.OB_MUTATE = 1) and one that ends it one charge early
(OB_MUTATE = 2) must each be caught.

  python3 ob_accept.py  -> ob_accept.json
"""
import json, sys
import lamps, qs, cfrac, ecm
from lamps import run, LAST, Meter
from fastlamps import semiprimes_pq
from race_accept import LAMP_CASES, RecMeter, alone

CAP = 2 ** 28
RHO = {"t": "rho", "c": 1, "b": 64}
QS = {"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}
FAIL = []

def check(cond, *what):
    if not cond:
        FAIL.append(what)
        print("FAIL", *what)
    return cond

def recorded(gen, N, cap=CAP):
    """run() on a recording meter, with one trace shared by the traced cards."""
    tr = {}
    qs.TRACE = cfrac.TRACE = ecm.TRACE = tr
    saved, lamps.Meter = lamps.Meter, RecMeter
    holder = {}
    orig_init = RecMeter.__init__
    def init(self, cap):
        orig_init(self, cap)
        holder["m"] = self
    RecMeter.__init__ = init
    try:
        ops, d = run(gen, N, cap)
    finally:
        RecMeter.__init__ = orig_init
        lamps.Meter = saved
        qs.TRACE = cfrac.TRACE = ecm.TRACE = None
    m = holder["m"]
    return dict(ops=ops, d=d, tests=LAST["tests"], hits=LAST["hits"], stage=LAST["stage"], k=LAST["k"],
                ob=list(LAST["ob"]), phases=tr.get("ops", {})), m.charges

def compare_key(r):
    return {k: r[k] for k in ("ops", "d", "tests", "hits", "stage", "k", "phases")}

def precheck_min(X, N):
    """The ops a stage's precheck says it must charge before any test, as the first stage
    (0 where it has no precheck or the precheck does not apply)."""
    if X["t"] == "ps":
        L = int(N ** X["a"]) + 1
        B = max(2, int(X["c"] * N ** X["s"]))
        return (B - 1) + ((L + B - 1) // B - 1)
    if X["t"] == "pm1":
        B = max(10, int(N ** X["b"]))
        return B / __import__("math").log(B) if B > (1 << 26) else 0
    return 0

def lamp_case(name, X, bits, mutate=False):
    n = 0
    Y = RHO if bits < 40 else QS
    for N, p, q in semiprimes_pq(bits, 2, 7700000 + bits):
        x, xch, _ = alone(X, N)
        y, ych, _ = alone(Y, N)
        T = sum(xch)
        base, bch = recorded([X, Y], N)
        if not mutate:
            want_ops = x["ops"] if x["d"] else (T + y["ops"] if y["d"] else None)
            check(base["ops"] == want_ops and bch == (xch if x["d"] else xch + ych), "ob absent", name, bits, N)
            z, zch = recorded([dict(X, ob=0), Y], N)
            check(z["ops"] == y["ops"] and z["d"] == y["d"] and z["stage"] == (1 if y["d"] else None)
                  and zch == ych and z["tests"] == y["tests"], "ob = 0", name, bits, N)
            for ob in (T, T + 1, 2 * T):
                if ob == 0:
                    continue
                r, rch = recorded([dict(X, ob=ob), Y], N)
                check(compare_key(r) == compare_key(base) and rch == bch, "ob at or past natural end", name, bits, N, ob)
                n += 1
            n += 2
        for b in sorted({1, T // 3, T - 1}):
            if not 1 <= b < T:
                continue
            r, rch = recorded([dict(X, ob=b), Y], N)
            if precheck_min(X, N) > b:
                ok = rch == ych and r["ops"] == y["ops"] and r["d"] == y["d"] and r["ob"] == [(0, b, 0, True)]
            else:
                c, j = 0, 0
                while c <= b:
                    c += xch[j]; j += 1
                want = xch[:j] + ych
                ok = rch == want and r["ops"] == (c + y["ops"] if y["d"] else None) and r["d"] == y["d"] \
                     and r["ob"] and r["ob"][0][3] and r["ob"][0][2] == c and 1 <= c - b <= xch[j - 1] <= max(xch)
            if mutate:
                if not ok:
                    return "caught"
                continue
            check(ok, "ob below natural end", name, bits, N, b, r["ob"])
            n += 1
    return "missed" if mutate else n

def precheck_cases():
    import blockflash
    n = 0
    for label, st, mod, spy in (("ps large block", {"t": "ps", "a": 0.5, "s": 0.4, "c": 4.0, "ob": 1000}, blockflash, "product_tree"),
                                ("pm1 past 2^32", {"t": "pm1", "b": 0.39, "ob": 1000}, lamps, "primes_segmented")):
        for N, p, q in semiprimes_pq(84, 2, 7700084):
            calls = []
            orig = getattr(mod, spy)
            setattr(mod, spy, lambda *a, **k: (calls.append(1), orig(*a, **k))[1])
            try:
                ops, d = run([st, QS], N, 2 ** 40)
                rec = list(LAST["ob"]); stage = LAST["stage"]
            finally:
                setattr(mod, spy, orig)
            q_ops, q_d = run([QS], N, 2 ** 40)
            check(not calls and rec == [(0, 1000, 0, True)] and stage == 1 and (ops, d) == (q_ops, q_d),
                  "precheck reads the budget", label, N, calls, rec)
            n += 1
    return n

def caps_and_validation():
    n = 0
    N = semiprimes_pq(48, 1, 7700048)[0][0]
    x, xch, _ = alone(RHO, N)
    T = sum(xch)
    r, _ = recorded([dict(RHO, ob=T // 2), QS], N, cap=T // 4)
    check(r["ops"] is None and r["ob"] and not r["ob"][0][3], "cap inside a budgeted stage")
    n += 1
    race = {"t": "race", "a": RHO, "b": QS, "sa": 64, "sb": 64}
    for g in ([dict(RHO, ob=-1)], [dict(RHO, ob="5")], [dict(RHO, ob=True)], [dict(RHO, ob=2.5)],
              [dict(race, ob=10)], [dict(race, a=dict(RHO, ob=10))], [dict(race, b=dict(QS, ob=10))]):
        m = Meter(CAP)
        try:
            run(g, N, CAP)
            check(False, "accepted", g)
        except ValueError:
            n += 1
    return n

if __name__ == "__main__":
    out = {"cases": {}}
    for name, (X, sizes) in LAMP_CASES.items():
        out["cases"][name] = {b: lamp_case(name, X, b) for b in sizes}
        print(name, out["cases"][name], flush=True)
    out["precheck_cases"] = precheck_cases()
    print("precheck cases:", out["precheck_cases"])
    out["caps_and_validation"] = caps_and_validation()
    out["mutation"] = {}
    for mode, label in ((1, "never ends"), (2, "ends one charge early")):
        lamps.OB_MUTATE = mode
        out["mutation"][label] = {name: lamp_case(name, X, sizes[0], mutate=True) for name, (X, sizes) in LAMP_CASES.items()}
        lamps.OB_MUTATE = 0
        print("mutation:", label, out["mutation"][label])
        check(all(v == "caught" for v in out["mutation"][label].values()), "mutation missed", label)
    out["failures"] = len(FAIL)
    print("failures:", len(FAIL))
    json.dump(out, open("ob_accept.json", "w"), indent=1)
    sys.exit(1 if FAIL else 0)
