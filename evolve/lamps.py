"""Lamp parts, genomes, and op-counted fitness for evolving factoring algorithms.

Watts = operations (one modular multiply, square test, or gcd = 1 op).
Lumens = candidate stations for p ruled out, about sqrt(N) for a balanced semiprime.
Efficacy exponent = 1/2 - work exponent, where work ~ N^e (worst case over test N).
"""
import math, random, sys

class Budget(Exception):
    pass

class Meter:
    """Counts watts (ops), plus tests and hits for the luck meter.

    A test is one check against the method's invariant event (does this station divide N,
    is this x^2 - kN a square, does this gcd exceed 1). A hit is the event firing, useful
    or not. Hit rate = hits / tests: how lucky each test is, apart from how cheap it is.
    """
    def __init__(self, cap):
        self.ops = 0
        self.cap = cap
        self.tests = 0
        self.hits = 0
        self.k = None           # instrumentation: the k a square-search win came from
    def tick(self, k=1):
        self.ops += k
        if self.ops > self.cap:
            raise Budget()
    def test(self, hit):
        self.tests += 1
        if hit:
            self.hits += 1

def is_square(n):
    if n < 0:
        return False, 0
    r = math.isqrt(n)
    return r * r == n, r

# ---- lamp parts -------------------------------------------------------------

def lamp_td(N, g, m):
    """Trial division up to N^a."""
    lim = int(N ** g["a"]) + 1
    if N % 2 == 0:
        return 2
    d = 3
    while d <= lim:
        m.tick()
        hit = N % d == 0
        m.test(hit)
        if hit:
            return d
        d += 2
    return None

SMOOTH_K = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 18, 20, 24, 30, 36, 40, 45, 48, 60,
            72, 80, 90, 120, 144, 180, 210, 240, 360, 420, 480, 720, 840, 1260, 1680,
            2520, 5040, 7560, 10080, 15120, 20160, 25200, 27720, 45360, 50400, 55440]

def multipliers(mode, K, mult):
    if mode == "one":
        yield 1
    elif mode == "seq":
        for k in range(1, K + 1):
            yield k
    elif mode == "seqm":            # k = mult * i, a fixed smooth stride
        for i in range(1, K + 1):
            yield mult * i
    else:                           # "smooth": highly divisible k first, then the rest
        seen = set()
        for k in SMOOTH_K:
            if k > K:
                break
            seen.add(k)
            yield k
        for k in range(1, K + 1):
            if k not in seen:
                yield k

KS_PRIMES = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
def ks_score(k, N):
    """Knuth–Schroeppel-style score: how square-friendly kN is mod small primes."""
    kN = k * N
    r8 = kN % 8
    s = (2.0 if r8 == 1 else 1.0 if r8 == 5 else 0.5) * math.log(2) - 0.5 * math.log(k)
    for p in KS_PRIMES:
        if k % p == 0:
            s += math.log(p) / p
        elif pow(kN % p, (p - 1) // 2, p) == 1:
            s += 2 * math.log(p) / (p - 1)
    return s

def ks_order(N, K, mult, chunk, m):
    """Luck by design: multipliers mult*i, i <= K, taken in chunks of `chunk`.

    Each chunk is scored (one op per small prime per candidate, charged when the chunk
    is reached) and tried best-first, so ranking cost is only paid as it's used.
    """
    i = 1
    while i <= K:
        block = [mult * j for j in range(i, min(K, i + chunk - 1) + 1)]
        m.tick(len(block) * len(KS_PRIMES))
        block.sort(key=lambda k: -ks_score(k, N))
        yield from block
        i += chunk

def lamp_sq(N, g, m):
    """Square search on kN: Fermat (k=1, wide window), Lehman (windows ~N^(1/6)/sqrt k),
    Hart (window 1). Every test of x^2 - kN is one op."""
    K = max(1, int(N ** g["k"]))
    ks = ks_order(N, K, g.get("mult", 1), g.get("r", 16), m) if g["mode"] == "ks" else None
    for k in (ks if ks is not None else multipliers(g["mode"], K, g.get("mult", 1))):
        kN = k * N
        if g["ksq"]:
            kN *= 4
        # Window ends at sqrt(kN) + width, with sqrt(kN) ~ s + f taken from the exact
        # isqrt (a float sqrt of kN itself loses ~10 bits past 60-bit N).
        s = math.isqrt(kN)
        x0 = s if s * s == kN else s + 1
        f = float(kN - s * s) / float(2 * s)
        width = g["c"] * (N ** g["w"]) / math.sqrt(k)
        W = max(1, s + math.floor(f + width) - x0 + 1)
        for x in range(x0, x0 + W):
            m.tick()
            ok, y = is_square(x * x - kN)
            m.test(ok)
            if ok:
                d = math.gcd(x - y, N)
                if 1 < d < N:
                    m.k = k
                    return d
    return None

def lamp_rho(N, g, m):
    """Brent rho, x -> x^d + c (d = 2 by default), gcds batched every b steps.

    Luck-by-design genes: degree d (even) and start x0. x^d costs about
    log2(d) + popcount(d) - 1 multiplies per step instead of 1.
    """
    c = g["c"]
    b = max(1, g["b"])
    d = g.get("d", 2)
    step_cost = max(1, d.bit_length() - 1 + bin(d).count("1") - 1)
    if d == 2:
        f = lambda v: (v * v + c) % N
    else:
        f = lambda v: (pow(v, d, N) + c) % N
    y, r, q, G = g.get("x0", 2), 1, 1, 1
    while True:
        x = y
        for _ in range(r):
            y = f(y); m.tick(step_cost)
        k = 0
        while k < r and G == 1:
            ys = y
            for _ in range(min(b, r - k)):
                y = f(y)
                q = q * abs(x - y) % N
                m.tick(step_cost + 1)
            G = math.gcd(q, N); m.tick()
            m.test(G != 1)
            k += b
        r *= 2
        if G != 1:
            break
    if G == N:
        while True:
            ys = f(ys); m.tick(step_cost)
            G = math.gcd(abs(x - ys), N); m.tick()
            m.test(G != 1)
            if G > 1:
                break
    return G if 1 < G < N else None

_PR = None
def primes_upto(n):
    global _PR
    if _PR is None or _PR[0] < n:
        s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
        for i in range(2, math.isqrt(n) + 1):
            if s[i]:
                s[i * i::i] = bytearray(len(s[i * i::i]))
        _PR = (n, [i for i in range(n + 1) if s[i]])
    return [p for p in _PR[1] if p <= n]

def primes_segmented(n, seg=1 << 22):
    """Primes up to n in order, sieved a segment at a time (for bounds too big to sieve whole)."""
    small = primes_upto(math.isqrt(n))
    lo = 2
    while lo <= n:
        hi = min(lo + seg - 1, n)
        s = bytearray([1]) * (hi - lo + 1)
        for p in small:
            if p * p > hi:
                break
            start = max(p * p, (lo + p - 1) // p * p)
            s[start - lo::p] = bytearray(len(s[start - lo::p]))
        for i, v in enumerate(s):
            if v:
                yield lo + i
        lo = hi + 1

def lamp_pm1(N, g, m):
    """Pollard p-1 with bound N^b."""
    B = max(10, int(N ** g["b"]))
    # Same guard as lampcore: each prime ticks at least once, so if a lower bound on pi(B)
    # can't fit in the budget the run would miss anyway; stop before sieving a huge range.
    if B > (1 << 26) and m.ops + B / math.log(B) > m.cap:
        raise Budget()
    a = 2
    for p in (primes_upto(B) if B <= (1 << 26) else primes_segmented(B)):
        pk = p
        while pk * p <= B:
            pk *= p
        a = pow(a, pk, N); m.tick(max(1, pk.bit_length()))
    d = math.gcd(a - 1, N); m.tick()
    m.test(d != 1)
    return d if 1 < d < N else None

from blockflash import lamp_ps
from qs import lamp_qs
from cfrac import lamp_cfrac                              # in no deck: tests and comparisons only
from ecm import lamp_ecm                                  # in no deck until Run 8
from race import lamp_race, validate as race_validate     # Stage 9; in no deck until Run 8

LAMPS = {"td": lamp_td, "sq": lamp_sq, "rho": lamp_rho, "pm1": lamp_pm1, "ps": lamp_ps,
         "qs": lamp_qs, "cfrac": lamp_cfrac, "ecm": lamp_ecm, "race": lamp_race}

# ---- genomes ----------------------------------------------------------------

def rand_stage(kind, rng):
    if kind == "td":
        return {"t": "td", "a": rng.uniform(0.05, 0.5)}
    if kind == "sq":
        return {"t": "sq", "mode": rng.choice(SQ_MODES),
                "mult": rng.choice([1, 2, 6, 12, 30, 60, 120, 480]),
                "k": rng.uniform(0.0, 0.5), "w": rng.uniform(0.0, 0.5),
                "c": rng.uniform(0.1, 4.0), "ksq": rng.random() < 0.5,
                **({"r": rng.choice([4, 8, 16, 32, 64])} if FINE_DECK else {})}
    if kind == "rho":
        st = {"t": "rho", "c": rng.randint(1, 9), "b": rng.choice([1, 4, 16, 64, 128])}
        if FINE_DECK:
            st["d"] = rng.choice([2, 2, 4, 6, 8])
            st["x0"] = rng.randint(2, 9)
        return st
    if kind == "qs":
        return {"t": "qs", "kc": rng.randint(*QS_RANGES["kc"]),
                **{key: (math.exp(rng.uniform(*map(math.log, QS_RANGES[key]))) if key in QS_LOG
                         else rng.uniform(*QS_RANGES[key])) for key in ("bc", "mc", "tc")}}
    if kind == "ps":
        return {"t": "ps", "a": rng.uniform(0.3, 0.55), "s": rng.uniform(0.1, 0.4),
                "c": rng.uniform(0.25, 4.0)}
    return {"t": "pm1", "b": rng.uniform(0.05, 0.4)}

FINE_DECK = False          # Run 4 turns on the luck-by-design cards
QS_RANGES = {"kc": (1, 32), "bc": (0.8, 3.0), "mc": (1.0, 12.0), "tc": (1.0, 3.5)}
QS_SIGMA = {"bc": 0.15, "mc": 0.75, "tc": 0.15}
QS_LOG = set()             # genes sampled and mutated on a log scale (sigma in log units)
SQ_MODES = ["one", "seq", "seqm", "smooth"]

def use_fine_deck():
    global FINE_DECK
    FINE_DECK = True
    SQ_MODES.append("ks")

def use_wide_qs_ranges():
    """For runs after Run 6: mc 0.05..12 on a log scale, bc 0.7..3.0 (both sweeps found the
    optimum below Run 6's mc floor of 1.0). Opt-in, so replays of Run 6 are unchanged."""
    QS_RANGES.update(mc=(0.05, 12.0), bc=(0.7, 3.0))
    QS_SIGMA.update(mc=0.3)
    QS_LOG.add("mc")

def rand_genome(deck, rng):
    return [rand_stage(rng.choice(deck), rng) for _ in range(rng.randint(1, 3))]

def mutate(gen, deck, rng):
    """Return (child genome, name of the mutation that made it)."""
    g = [dict(s) for s in gen]
    r = rng.random()
    if r < 0.55 and g:
        op = "tune"
        s = rng.choice(g)
        for key in list(s):
            if key == "t" or rng.random() > 0.5:
                continue
            v = s[key]
            if s["t"] == "qs":                 # its own ranges; other stages untouched
                lo, hi = QS_RANGES[key]
                if key == "kc":
                    s[key] = min(hi, max(lo, v + rng.choice([-1, 1]) * max(1, v // 4)))
                elif key in QS_LOG:
                    s[key] = min(hi, max(lo, v * math.exp(rng.gauss(0, QS_SIGMA[key]))))
                else:
                    s[key] = min(hi, max(lo, v + rng.gauss(0, QS_SIGMA[key])))
            elif isinstance(v, bool):
                s[key] = not v
            elif isinstance(v, float):
                lo, hi = (0.1, 6.0) if key == "c" else (0.0, 0.55)
                s[key] = min(hi, max(lo, v + rng.gauss(0, 0.05 if key != "c" else 0.4)))
            elif key == "mode":
                s[key] = rng.choice(SQ_MODES)
            elif key == "d":
                s[key] = rng.choice([2, 4, 6, 8])
            elif key == "mult":
                s[key] = rng.choice([1, 2, 4, 6, 12, 24, 30, 60, 120, 240, 480, 720])
            elif isinstance(v, int):
                s[key] = max(1, v + rng.choice([-1, 1]) * max(1, v // 2))
    elif r < 0.7 and len(g) < 4:
        op = "insert"
        g.insert(rng.randint(0, len(g)), rand_stage(rng.choice(deck), rng))
    elif r < 0.8 and len(g) > 1:
        op = "delete"
        g.pop(rng.randrange(len(g)))
    elif r < 0.9 and len(g) > 1:
        op = "swap"
        i, j = rng.sample(range(len(g)), 2); g[i], g[j] = g[j], g[i]
    else:
        op = "replace"
        g[rng.randrange(len(g))] = rand_stage(rng.choice(deck), rng)
    return g, op

COVERAGE = False           # Stage 1 coverage rule; off for replays of Runs 2-5

def use_coverage_rule():
    global COVERAGE
    COVERAGE = True

def covered(gen):
    """True if some stage provably finds a factor of any balanced semiprime: trial
    division to sqrt(N), or Lehman (trial to N^(1/3), then 4kN for every k up to N^(1/3)
    with window at least N^(1/6)/(4 sqrt k))."""
    td_third = False
    for s in gen:
        if s["t"] == "td":
            if s["a"] >= 0.5:
                return True
            td_third = td_third or s["a"] >= 1 / 3
        elif (s["t"] == "sq" and td_third and s["mode"] == "seq" and s["ksq"]
              and s["k"] >= 1 / 3 and s["w"] >= 1 / 6 and s["c"] >= 0.25):
            return True
    return False

def with_fallback(gen, luck):
    """Coverage rule: a genome whose stages stop short of sqrt(N) gets a fallback tail,
    charged like any stage. No-luck deck: trial division to sqrt(N), complete but it can
    exceed the cap. Luck deck: rho with a c no rho stage already uses, heuristic.
    Returns (genome to score, whether the tail was added)."""
    if covered(gen):
        return gen, False
    if not luck:
        return gen + [{"t": "td", "a": 0.5}], True
    used = {s["c"] for s in gen if s["t"] == "rho"}
    return gen + [{"t": "rho", "c": min(c for c in range(1, 10) if c not in used), "b": 64}], True

def crossover(a, b, rng):
    child = a[:rng.randint(0, len(a))] + b[rng.randint(0, len(b)):]
    return [dict(s) for s in (child or a)][:4]

LAST = {"tests": 0, "hits": 0, "stage": None, "k": None, "ob": []}

class StageBudget(Exception):
    """A stage's own op budget ("ob") is spent: the stage ends without a factor."""

OB_MUTATE = 0    # mutation hook for ob_accept.py: 1 = never end, 2 = end one charge early

class StageMeter:
    """What a stage with an op budget sees (NOTES.md, "Per-stage op budget"): every charge
    goes to the shared meter whole; the charge that takes the stage's own spending past
    ob is applied, then the stage ends. ops, cap and k are the shared meter's."""
    def __init__(self, m, ob):
        self._m, self.ob, self.spent = m, ob, 0
        self.tests = self.hits = 0                # this stage's own (read-only instrumentation)
    def tick(self, k=1):
        if OB_MUTATE == 2 and self.spent + k > self.ob:
            raise StageBudget()
        self.spent += k                       # counted before the cap check, as Meter.tick does
        self._m.tick(k)                       # may raise Budget: the whole run misses
        if self.spent > self.ob and OB_MUTATE != 1:
            raise StageBudget()
    def test(self, hit):
        self._m.test(hit)
        self.tests += 1
        self.hits += bool(hit)
    @property
    def ops(self):
        return self._m.ops
    @property
    def cap(self):
        """What the ps / pm1 prechecks compare against: the shared cap or the meter total at
        which this stage's budget runs out, whichever is lower."""
        return min(self._m.cap, self._m.ops - self.spent + self.ob)
    @property
    def k(self):
        return self._m.k
    @k.setter
    def k(self, v):
        self._m.k = v

def validate_genome(gen):
    """Raises ValueError for a genome that may not be built: a bad ob, an ob on a race or
    on a race's side, or an invalid race (race.validate)."""
    for s in gen:
        if "ob" in s and (not isinstance(s["ob"], int) or isinstance(s["ob"], bool) or s["ob"] < 0):
            raise ValueError("ob must be a non-negative integer")
        if s["t"] == "race":
            if "ob" in s or "ob" in s.get("a", {}) or "ob" in s.get("b", {}):
                raise ValueError("ob is not allowed on a race or its sides")
            race_validate(s)

TYPES = False    # True: LAST["types"] gets the run's per-type op counts (optypes.py), per stage
NO_BUDGET = 1 << 200

def _stage_types(s, tr, spent, tests, N):
    import optypes
    if s["t"] == "race":
        out = {}
        for sd in tr.get("sides", []):
            for t, n in sd["per_type"].items():
                out[t] = out.get(t, 0) + n
        return out
    return optypes.per_type(s, tr, spent, tests, N)

def run(gen, N, cap):
    """Returns (ops, factor), or (None, None) on a miss. Test and hit counts of the
    latest run are left in LAST for the luck meter, with the winning stage's index and,
    for a square-search win, its k (read-only instrumentation; None on a miss). LAST["ob"]
    lists, per stage with an op budget that ran, (index, ob, spent, ended by its budget,
    its own tests, its own hits). With TYPES on, LAST["types"] holds the run's per-type op
    counts, taken per stage (each stage on its own counting meter and with its own traces;
    read-only, no op changes)."""
    validate_genome(gen)
    m = Meter(cap)
    obs = []
    types = {}
    try:
        for i, s in enumerate(gen):
            ob = s.get("ob")
            if ob == 0:
                continue                          # skipped: no lamp code runs
            if ob is None and not TYPES:
                d = LAMPS[s["t"]](N, s, m)
            else:
                budget = ob if ob is not None else NO_BUDGET
                sm = StageMeter(m, budget)
                start = m.ops
                mod = sys.modules.get(s["t"]) if TYPES and s["t"] in ("qs", "ecm", "cfrac", "race") else None
                if mod is not None:
                    saved, tr = mod.TRACE, {}
                    mod.TRACE = tr
                try:
                    d = LAMPS[s["t"]](N, s, sm)
                    if ob is not None:
                        obs.append((i, ob, sm.spent, False, sm.tests, sm.hits))
                except StageBudget:
                    obs.append((i, ob, sm.spent, True, sm.tests, sm.hits))
                    d = None
                except Budget:
                    # a precheck (no charge crossed the cap) that the stage's budget made
                    # binding ends the stage, not the run
                    if m.ops <= m.cap and start + budget < m.cap:
                        obs.append((i, ob, sm.spent, True, sm.tests, sm.hits))
                        d = None
                    else:
                        if ob is not None:
                            obs.append((i, ob, sm.spent, False, sm.tests, sm.hits))
                        raise
                finally:
                    if TYPES:
                        if mod is not None:
                            mod.TRACE = saved
                        for t, n in _stage_types(s, tr if mod is not None else None, sm.spent, sm.tests, N).items():
                            types[t] = types.get(t, 0) + n
            if d:
                LAST.update(tests=m.tests, hits=m.hits, stage=i, k=m.k, ob=obs, types=types)
                return m.ops, d
    except Budget:
        pass
    LAST.update(tests=m.tests, hits=m.hits, stage=None, k=None, ob=obs, types=types)
    return None, None

# ---- test semiprimes ---------------------------------------------------------

def rand_prime(bits, rng):
    while True:
        p = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if all(pow(a, p - 1, p) == 1 for a in (2, 3, 5, 7, 11, 13)):
            return p

def semiprimes(bits, count, seed):
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        p, q = rand_prime(bits // 2, rng), rand_prime(bits - bits // 2, rng)
        if p != q:
            out.append(p * q)
    return out

def cap_for(bits):
    return int(2 ** (0.5 * bits + 6))        # 64x trial division: slow is scored, not a miss

def slope(xs, ys):
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def measure_cumulative(gen, tests, abort_log2=None):
    """Cumulative scoring (Run 3). tests = {bits: [N...]}, largest size first.

    Watts are summed over every test number at a size: the cumulative total to darken
    all of their secrets. Score (lower is better) = log2(cumulative watts / count) / bits,
    averaged over the top two sizes, so lumens per watt is N^(1/2 - score).
    Worst cases are kept alongside. Missing any number counts as not finished.
    """
    sizes = sorted(tests, reverse=True)
    cum, worst, per_n, fails = {}, {}, {}, 0
    t_all, h_all, solved = 0, 0, 0
    for i, bits in enumerate(sizes):
        cap = cap_for(bits)
        if i == 0 and abort_log2 is not None:
            cap = min(cap, int(2 ** abort_log2))
        total, w, opsl = 0, 0, []
        for N in tests[bits]:
            ops, d = run(gen, N, cap)
            t_all += LAST["tests"]; h_all += LAST["hits"]
            if ops is None:
                fails += 1
                if i == 0:
                    return {"score": 0.5 + 0.02 * fails, "cum": cum, "worst": worst,
                            "per_n": per_n, "fails": fails, "luck": None}
                ops = cap_for(bits)
            else:
                solved += 1
            total += ops; w = max(w, ops); opsl.append(ops)
        cum[bits] = math.log2(total / len(tests[bits]))
        worst[bits] = math.log2(max(w, 1))
        per_n[bits] = opsl
    top = sizes[:2]
    score = sum(cum[b] / b for b in top) / len(top)
    if fails:
        score = max(score, 0.5) + 0.02 * fails
    luck = {"tests": t_all, "hits": h_all,
            "hit_rate_log2": math.log2(h_all / t_all) if h_all and t_all else None,
            "useful_share": solved / h_all if h_all else None}
    return {"score": score, "cum": cum, "worst": worst, "per_n": per_n, "fails": fails,
            "luck": luck}

def measure(gen, tests, abort_log2=None):
    """Worst case over tests = {bits: [N...]}, largest size first.

    Score (lower is better) is the effective exponent at the top two sizes:
    log2(worst ops) / bits, averaged. It prices the bulb at the sizes actually run, so
    being slow on small N can't lower it. The fitted slope is reported as the trend.
    abort_log2: give up early if the top size already costs more than 2^abort_log2.
    """
    sizes = sorted(tests, reverse=True)
    ys, fails = {}, 0
    for i, bits in enumerate(sizes):
        cap = cap_for(bits)
        if i == 0 and abort_log2 is not None:
            cap = min(cap, int(2 ** abort_log2))
        worst = 0
        for N in tests[bits]:
            ops, d = run(gen, N, cap)
            if ops is None:
                fails += 1
                ops = cap_for(bits)
                if i == 0:                  # missed at the top size: stop measuring
                    ys[bits] = math.log2(ops)
                    return {"score": 0.5 + 0.02 * fails, "trend": None, "ys": ys, "fails": fails}
            worst = max(worst, ops)
        ys[bits] = math.log2(max(worst, 1))
    top = sizes[:2]
    score = sum(ys[b] / b for b in top) / len(top)
    if fails:
        score = max(score, 0.5) + 0.02 * fails  # worst luck: missing any N means not done
    asc = sorted(ys)
    return {"score": score, "trend": slope(asc, [ys[b] for b in asc]), "ys": ys, "fails": fails}

def describe(gen):
    parts = []
    for s in gen:
        if s["t"] == "td":
            parts.append(f"trial to N^{s['a']:.2f}")
        elif s["t"] == "sq":
            kk = {"one": "k=1", "seq": "k=1..", "seqm": f"k={s['mult']}i", "smooth": "smooth k",
                  "ks": f"k={s['mult']}i ranked by {s.get('r', 16)}s"}[s["mode"]]
            parts.append(f"square search [{kk} up to N^{s['k']:.2f}, window {s['c']:.2f}·N^{s['w']:.2f}/√k{', 4kN' if s['ksq'] else ''}]")
        elif s["t"] == "rho":
            extra = (f", x^{s['d']}" if s.get("d", 2) != 2 else "") + \
                    (f", start {s['x0']}" if s.get("x0", 2) != 2 else "")
            parts.append(f"rho [c={s['c']}, gcd every {s['b']}{extra}]")
        elif s["t"] == "qs":
            parts.append(f"quadratic sieve [k from 1..{s.get('kc', 16)}, B {s.get('bc', 1.5):.2f}·L^½, "
                         f"M {s.get('mc', 4.0):.1f}·B, slack {s.get('tc', 2.0):.2f}·log B]")
        elif s["t"] == "ps":
            parts.append(f"block flash [to N^{s['a']:.2f}, blocks {s['c']:.2f}·N^{s['s']:.2f}]")
        else:
            parts.append(f"p−1 [B=N^{s['b']:.2f}]")
    return " → ".join(parts)
