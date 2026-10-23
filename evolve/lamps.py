"""Lamp parts, genomes, and op-counted fitness for evolving factoring algorithms.

Watts = operations (one modular multiply, square test, or gcd = 1 op).
Lumens = candidate stations for p ruled out, about sqrt(N) for a balanced semiprime.
Efficacy exponent = 1/2 - work exponent, where work ~ N^e (worst case over test N).
"""
import math, random

class Budget(Exception):
    pass

class Meter:
    def __init__(self, cap):
        self.ops = 0
        self.cap = cap
    def tick(self, k=1):
        self.ops += k
        if self.ops > self.cap:
            raise Budget()

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
        if N % d == 0:
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

def lamp_sq(N, g, m):
    """Square search on kN: Fermat (k=1, wide window), Lehman (windows ~N^(1/6)/sqrt k),
    Hart (window 1). Every test of x^2 - kN is one op."""
    K = max(1, int(N ** g["k"]))
    for k in multipliers(g["mode"], K, g.get("mult", 1)):
        kN = k * N
        if g["ksq"]:
            kN *= 4
        x0 = math.isqrt(kN)
        if x0 * x0 < kN:
            x0 += 1
        W = max(1, int(g["c"] * (N ** g["w"]) / math.sqrt(k)))
        for x in range(x0, x0 + W):
            m.tick()
            ok, y = is_square(x * x - kN)
            if ok:
                d = math.gcd(x - y, N)
                if 1 < d < N:
                    return d
    return None

def lamp_rho(N, g, m):
    """Brent rho, x -> x^2 + c, gcds batched every b steps."""
    c = g["c"]
    b = max(1, g["b"])
    y, r, q, G = 2, 1, 1, 1
    while True:
        x = y
        for _ in range(r):
            y = (y * y + c) % N; m.tick()
        k = 0
        while k < r and G == 1:
            ys = y
            for _ in range(min(b, r - k)):
                y = (y * y + c) % N
                q = q * abs(x - y) % N
                m.tick(2)
            G = math.gcd(q, N); m.tick()
            k += b
        r *= 2
        if G != 1:
            break
    if G == N:
        while True:
            ys = (ys * ys + c) % N; m.tick()
            G = math.gcd(abs(x - ys), N); m.tick()
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

def lamp_pm1(N, g, m):
    """Pollard p-1 with bound N^b."""
    B = max(10, int(N ** g["b"]))
    a = 2
    for p in primes_upto(B):
        pk = p
        while pk * p <= B:
            pk *= p
        a = pow(a, pk, N); m.tick(max(1, pk.bit_length()))
    d = math.gcd(a - 1, N); m.tick()
    return d if 1 < d < N else None

from blockflash import lamp_ps

LAMPS = {"td": lamp_td, "sq": lamp_sq, "rho": lamp_rho, "pm1": lamp_pm1, "ps": lamp_ps}

# ---- genomes ----------------------------------------------------------------

def rand_stage(kind, rng):
    if kind == "td":
        return {"t": "td", "a": rng.uniform(0.05, 0.5)}
    if kind == "sq":
        return {"t": "sq", "mode": rng.choice(["one", "seq", "seqm", "smooth"]),
                "mult": rng.choice([1, 2, 6, 12, 30, 60, 120, 480]),
                "k": rng.uniform(0.0, 0.5), "w": rng.uniform(0.0, 0.5),
                "c": rng.uniform(0.1, 4.0), "ksq": rng.random() < 0.5}
    if kind == "rho":
        return {"t": "rho", "c": rng.randint(1, 9), "b": rng.choice([1, 4, 16, 64, 128])}
    if kind == "ps":
        return {"t": "ps", "a": rng.uniform(0.3, 0.55), "s": rng.uniform(0.1, 0.4),
                "c": rng.uniform(0.25, 4.0)}
    return {"t": "pm1", "b": rng.uniform(0.05, 0.4)}

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
            if isinstance(v, bool):
                s[key] = not v
            elif isinstance(v, float):
                lo, hi = (0.1, 6.0) if key == "c" else (0.0, 0.55)
                s[key] = min(hi, max(lo, v + rng.gauss(0, 0.05 if key != "c" else 0.4)))
            elif key == "mode":
                s[key] = rng.choice(["one", "seq", "seqm", "smooth"])
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

def crossover(a, b, rng):
    child = a[:rng.randint(0, len(a))] + b[rng.randint(0, len(b)):]
    return [dict(s) for s in (child or a)][:4]

def run(gen, N, cap):
    m = Meter(cap)
    try:
        for s in gen:
            d = LAMPS[s["t"]](N, s, m)
            if d:
                return m.ops, d
    except Budget:
        pass
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
            kk = {"one": "k=1", "seq": "k=1..", "seqm": f"k={s['mult']}i", "smooth": "smooth k"}[s["mode"]]
            parts.append(f"square search [{kk} up to N^{s['k']:.2f}, window {s['c']:.2f}·N^{s['w']:.2f}/√k{', 4kN' if s['ksq'] else ''}]")
        elif s["t"] == "rho":
            parts.append(f"rho [c={s['c']}, gcd every {s['b']}]")
        elif s["t"] == "ps":
            parts.append(f"block flash [to N^{s['a']:.2f}, blocks {s['c']:.2f}·N^{s['s']:.2f}]")
        else:
            parts.append(f"p−1 [B=N^{s['b']:.2f}]")
    return " → ".join(parts)
