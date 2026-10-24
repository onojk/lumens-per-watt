"""Stage 9 acceptance, Python side (NOTES.md, "Stage 9: race combinator", acceptance and
addenda 2, 5): run before the Rust port and before any comparison.

  1. Genome checks: a nested race, sa = sb = 0, and a missing or negative slice are
     rejected before any op is charged.
  2. Disabled-side identity, every lamp: race(X, B, sa, 0) equals X alone and
     race(A, X, 0, sb) equals X alone, op for op (ops, factor, tests, hits, k, and the
     per-phase trace for the traced cards).
  3. One-switch identity, every lamp as the resumed side (addendum 2): race(X, E) with E =
     td a = 0.05, which ends without a factor inside its first slice, at three switch
     points (early, mid-run, at X's largest charge; plus mid-stage-2 for ECM and the end of
     the first polynomial for qs). Total ops = X alone + E alone; factor = X's; tests and
     hits = the sums; one switch; and the race's charge sequence is X's with E's whole
     sequence inserted at the switch.
  4. Random races (pairs of lamps, slices 2^4-2^14, 40-60 bits), each checked for:
     - per-side sums: side ops add up to the race's ops, tests and hits to the meter's,
       each side's per-type counts to its ops;
     - interleaving: each side's charge sequence is a prefix of its alone sequence (all
       of it for the winner); every finished slice is at least its size and below its size
       plus that side's largest charge;
     - the race bound, corrected (NOTES, Stage 9, correction): the measured check, when
       both sides finish alone, race <= 2 min(T_A, T_B) + s + O_other (O_other the other
       side's total overshoot); and the a-priori form, race <= T_w + (ceil(T_w/s) + 1) *
       (s + c_other) for the winner w, c_other the other side's largest single charge
       (reported per side).
  5. Caps that stop mid-slice and mid-chunk: a race whose cap falls inside a slice misses,
     and its meter shows the crossing charge.
  6. Mutation test: charging a switch (race.SWITCH_COST = 1) must fail check 3.

  python3 race_accept.py  -> race_accept.json
"""
import json, random, sys
import lamps, race, qs, ecm, cfrac
from lamps import Meter, Budget, LAMPS, LAST, run
from fastlamps import semiprimes_pq

CAP = 2 ** 28
E = {"t": "td", "a": 0.05}
LAMP_CASES = {   # stage, bit sizes: each lamp at sizes where it finishes within the cap
    "td": ({"t": "td", "a": 0.5}, (24, 28)),
    "sq": ({"t": "sq", "mode": "seqm", "mult": 60, "k": 0.3, "w": 0.25, "c": 1.2, "ksq": False, "r": 64}, (36, 40)),
    "ps": ({"t": "ps", "a": 0.5, "s": 0.25, "c": 1.0}, (32, 36)),
    "rho": ({"t": "rho", "c": 1, "b": 64}, (40, 48)),
    "pm1": ({"t": "pm1", "b": 0.3}, (40, 48)),
    "qs": ({"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38}, (40, 60, 84)),
    "qs lc 1.4": ({"t": "qs", "kc": 32, "bc": 1.1, "mc": 0.25, "tc": 1.38, "lc": 1.4}, (40, 60, 84)),
    "cfrac": ({"t": "cfrac", "kc": 32, "bc": 1.1}, (40, 52)),
    "ecm": ({"t": "ecm", "b1": 1.0, "b2": 50}, (40, 60, 84)),
}

class RecMeter(Meter):
    def __init__(self, cap):
        super().__init__(cap)
        self.charges = []
    def tick(self, k=1):
        self.charges.append(k)
        super().tick(k)

def alone(stage, N, cap=CAP):
    """Runs one stage on a recording meter: (result dict, charge sequence, phase trace)."""
    mod = race.TRACED.get(stage["t"])
    tr = {} if mod else None
    if mod:
        mod.TRACE = tr
    m = RecMeter(cap)
    try:
        d = LAMPS[stage["t"]](N, stage, m)
    except Budget:
        d = None
    if mod:
        mod.TRACE = None
    return dict(ops=m.ops if d else None, d=d, tests=m.tests, hits=m.hits, k=m.k), m.charges, tr

def raced(s, N, cap=CAP, record=True):
    race.TRACE = {}
    race.RECORD_CHARGES = record
    m = RecMeter(cap)
    try:
        d = race.lamp_race(N, s, m)
    except Budget:
        d = None
    tr, race.TRACE, race.RECORD_CHARGES = race.TRACE, None, False
    return dict(ops=m.ops if d else None, d=d, tests=m.tests, hits=m.hits, k=m.k), m.charges, tr

def nums(bits, n=2, seed=0):
    return semiprimes_pq(bits, n, 9900000 + 100 * seed + bits)

FAIL = []
def check(cond, *what):
    if not cond:
        FAIL.append(what)
        print("FAIL", *what)
    return cond

def test_validation():
    S = LAMP_CASES["rho"][0]
    bad = [{"t": "race", "a": {"t": "race", "a": S, "b": S, "sa": 1, "sb": 1}, "b": S, "sa": 1, "sb": 1},
           {"t": "race", "a": S, "b": S, "sa": 0, "sb": 0},
           {"t": "race", "a": S, "b": S, "sa": -1, "sb": 4},
           {"t": "race", "a": S, "sa": 4, "sb": 4},
           {"t": "race", "a": S, "b": S, "sa": 4}]
    n = 0
    for s in bad:
        m = Meter(CAP)
        try:
            race.lamp_race(1000003 * 999983, s, m)
            check(False, "validation accepted", s)
        except ValueError:
            check(m.ops == 0, "validation charged ops", s)
            n += 1
        try:
            race.validate_genome([s]); check(False, "validate_genome accepted", s)
        except ValueError:
            pass
    return n

def test_disabled(name, stage, bits):
    n = 0
    for N, p, q in nums(bits, 2, 1):
        a, ach, atr = alone(stage, N)
        for s, side in (({"t": "race", "a": stage, "b": E, "sa": 64, "sb": 0}, 0),
                        ({"t": "race", "a": E, "b": stage, "sa": 0, "sb": 64}, 1)):
            r, rch, rtr = raced(s, N)
            check(r == a and rch == ach, "disabled identity", name, bits, N, side, a, r)
            st, other = rtr["sides"][side], rtr["sides"][1 - side]
            check(atr is None or st["phases"] == atr["ops"], "disabled per-phase", name, bits, N, side)
            check(rtr["switches"] == 0 and other["end"] == "not run" and other["ops"] == 0,
                  "disabled side ran", name, N)
            n += 1
    return n

def one_switch_points(name, stage, N, a, ach, atr):
    T = a["ops"]
    big = max(range(len(ach)), key=lambda i: ach[i])
    pts = {"early": 1, "mid": T // 2, "largest charge": sum(ach[:big]) + 1}
    if name == "ecm" and atr["curves"] and atr["curves"][0]["end"] == "s2 factor" and len(atr["curves"]) == 1:
        o = atr["ops"]
        pts["mid stage 2"] = o["ecm_setup"] + o["ecm_s1"] + o["ecm_s2"] // 2
    if name.startswith("qs") and atr["attempts"] and atr["attempts"][0]["polys"]:
        p0 = atr["attempts"][0]["polys"][0]
        for i in range(len(ach) - 1):
            if ach[i] == p0["upd"] and ach[i + 1] == 2 * p0["M"] + 1:
                pts["end of first polynomial"] = sum(ach[:i + 2])
                break
    return {k: v for k, v in pts.items() if 1 <= v < T}

def test_one_switch(name, stage, bits, mutate=False):
    """On the first two of up to 16 numbers where X finds a factor alone and E does not."""
    n = used = 0
    for N, p, q in nums(bits, 16, 2):
        if used == 2:
            break
        a, ach, atr = alone(stage, N)
        e, ech, _ = alone(E, N)
        if a["d"] is None or e["d"] is not None:
            continue
        used += 1
        for where, sa in one_switch_points(name, stage, N, a, ach, atr).items():
            try:
                r, rch, rtr = raced({"t": "race", "a": stage, "b": E, "sa": sa, "sb": 1 << 20}, N)
            except AssertionError:
                if mutate:
                    return "caught (per-type sum)"
                raise
            # X's charge sequence with E's inserted at the switch: the slice ends at the
            # first charge that brings X's counter to >= sa
            c, i = 0, 0
            while c < sa:
                c += ach[i]; i += 1
            want = ach[:i] + ech + ach[i:]
            ok = r["ops"] == a["ops"] + sum(ech) and r["d"] == a["d"] \
                 and r["tests"] == a["tests"] + e["tests"] and r["hits"] == a["hits"] + e["hits"] \
                 and rtr["switches"] == 1 and rch == want
            if mutate:
                if not ok:
                    return "caught (one-switch identity)"
                continue
            check(ok, "one-switch identity", name, bits, N, where, sa, a["ops"], sum(ech), r["ops"], rtr["switches"])
            n += 1
    if not mutate:
        check(used == 2, "one-switch: fewer than 2 usable numbers", name, bits, used)
    return "missed" if mutate else n

def test_random(count=120, seed=7):
    rng = random.Random(seed)
    pool = ["rho", "pm1", "qs", "qs lc 1.4", "cfrac", "ecm", "sq", "td"]
    n = bound_checked = 0
    worst_bound = worst_apriori = 0.0
    max_charge = {}
    for _ in range(count):
        x, y = rng.choice(pool), rng.choice(pool)
        bits = rng.choice((40, 44, 48)) if {"sq", "td"} & {x, y} else rng.choice((40, 48, 56, 60))
        A, B = LAMP_CASES[x][0], LAMP_CASES[y][0]
        if x == "td" or y == "td":
            bits = 28
        sa = sb = 1 << rng.randint(4, 14)
        N = nums(bits, 1, rng.randint(10, 10 ** 6))[0][0]
        r, rch, tr = raced({"t": "race", "a": A, "b": B, "sa": sa, "sb": sb}, N)
        sides = tr["sides"]
        tot = sum(s["ops"] for s in sides)
        check(r["ops"] is None or tot == r["ops"], "side ops sum", x, y, N, tot, r["ops"])
        check(sum(s["tests"] for s in sides) == r["tests"] and sum(s["hits"] for s in sides) == r["hits"],
              "tests/hits sum", x, y, N)
        for s in sides:
            if s["per_type"]:
                check(sum(s["per_type"].values()) == s["ops"], "per-type sum", x, y, N, s["t"])
        # interleaving: each side's charges are a prefix of its alone sequence
        alone_res = []
        for st, s in zip((A, B), sides):
            a, ach, _ = alone(st, N)
            alone_res.append(a)
            if s["charges"]:
                check(ach[:len(s["charges"])] == s["charges"], "prefix", x, y, N, st["t"])
            if s["end"] == "found":
                check(s["charges"] == ach, "winner's sequence is complete", x, y, N, st["t"])
            mx = max(ach) if ach else 0
            max_charge[st["t"]] = max(max_charge.get(st["t"], 0), mx)
            for L in s["slices"]:
                check(s["size"] <= L < s["size"] + mx, "slice length", x, y, N, st["t"], L, s["size"], mx)
        # corrected race bound, when both finish alone
        if r["ops"] is not None and all(a["d"] for a in alone_res):
            TA, TB = alone_res[0]["ops"], alone_res[1]["ops"]
            m = 0 if TA <= TB else 1
            other = sides[1 - m]
            O = sum(L - other["size"] for L in other["slices"])
            bound = 2 * min(TA, TB) + sa + O
            check(r["ops"] <= bound, "race bound", x, y, N, sa, TA, TB, r["ops"], bound)
            worst_bound = max(worst_bound, r["ops"] / bound)
            bound_checked += 1
        w = next((i for i, s in enumerate(sides) if s["end"] == "found"), None)
        if w is not None:
            Tw = alone_res[w]["ops"]
            _, och, _ = alone((A, B)[1 - w], N)
            co = max(och) if och else 0
            apriori = Tw + (-(-Tw // sa) + 1) * (sa + co)
            check(r["ops"] <= apriori, "a-priori bound", x, y, N, sa, Tw, co, r["ops"], apriori)
            worst_apriori = max(worst_apriori, r["ops"] / apriori)
        n += 1
    return n, bound_checked, worst_bound, worst_apriori, max_charge

def test_caps():
    n = 0
    A, B = LAMP_CASES["ecm"][0], LAMP_CASES["qs"][0]
    for N, p, q in nums(60, 2, 3):
        full, ch, tr = raced({"t": "race", "a": A, "b": B, "sa": 256, "sb": 256}, N)
        for frac in (0.3, 0.6, 0.9):
            cap = int(full["ops"] * frac)
            r, rch, _ = raced({"t": "race", "a": A, "b": B, "sa": 256, "sb": 256}, N, cap)
            check(r["d"] is None and sum(rch) > cap and sum(rch[:-1]) <= cap and rch == ch[:len(rch)],
                  "cap mid-slice", N, cap)
            n += 1
        # a cap inside qs's largest chunk
        big = max(range(len(ch)), key=lambda i: ch[i])
        cap = sum(ch[:big]) + ch[big] // 2
        r, rch, _ = raced({"t": "race", "a": A, "b": B, "sa": 256, "sb": 256}, N, cap)
        check(r["d"] is None and len(rch) == big + 1, "cap mid-chunk", N, cap)
        n += 1
    return n

if __name__ == "__main__":
    out = {}
    out["validation"] = test_validation()
    out["disabled"] = {}
    out["one_switch"] = {}
    for name, (stage, sizes) in LAMP_CASES.items():
        for bits in sizes:
            out["disabled"][f"{name} {bits}"] = test_disabled(name, stage, bits)
            out["one_switch"][f"{name} {bits}"] = test_one_switch(name, stage, bits)
        print(name, "disabled", [out["disabled"][f"{name} {b}"] for b in sizes],
              "one-switch", [out["one_switch"][f"{name} {b}"] for b in sizes], flush=True)
    out["random"] = dict(zip(("races", "bound_checked", "worst_ratio_to_measured_bound",
                              "worst_ratio_to_apriori_bound", "max_single_charge_per_lamp"), test_random()))
    print("random", out["random"], flush=True)
    out["caps"] = test_caps()
    race.SWITCH_COST = 1
    out["mutation"] = {f"{name} {sizes[0]}": test_one_switch(name, stage, sizes[0], mutate=True)
                       for name, (stage, sizes) in LAMP_CASES.items()}
    race.SWITCH_COST = 0
    print("mutation (switch charged 1 op):", out["mutation"])
    check(all(v.startswith("caught") for v in out["mutation"].values()), "mutation missed")
    out["failures"] = len(FAIL)
    print("failures:", len(FAIL))
    json.dump(out, open("race_accept.json", "w"), indent=1)
    sys.exit(1 if FAIL else 0)
