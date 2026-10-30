"""The arrangement lamp "arr" (arrangement-v1; design docs/planning/arrangement_lamps.md, 70d374a; cost model NOTES,
"Cost model: the arrangement lamp", 6062320, and the stride ruling 77e898e, written before this code). In no deck.

A stage is {"t": "arr", "layout": {"kind": ..., genes}, "detect": {"kind": ..., genes}, "ob": budget}.
  layouts: stride (a, s), fold (w, a, s), map (c, d, x0), bins (m, B), exponent (a, K)
  rules:   dot (t), batch (b, t), floyd (b), brent (b), bins (bin compare; bins layout only)
Charges (op-class types): stride 1 word per step (dot 0 free); fold w word + w mul per dot; map rho's step cost in mul
(dot 0 free); bins word + mul + hash per dot; exponent max(1, bitlen(k)) mul per k. dot: 1 gcd per dot; batch: 1 mul
per dot + 1 gcd per batch; floyd: 3 layout steps + 1 mul per iteration, 1 gcd per b iterations; brent: lampcore rho's
loop exactly; bin compare: 1 sort_cmp + 1 gcd per pair. A batched gcd of N backtracks dot by dot (charged).
Ops = mul + word + hash + sort_cmp + gcd, gcd = tests. lampcore/src/main.rs (lamp_arr) is the twin: same charges, same
order of charges, same tests.

Read-only instrumentation: with TRACE a dict, the stage's word / hash / sort_cmp / mul / gcd charges; SMALL counts the
gcds whose non-N argument was < 2^64 at the call (the size-scaled gcd price's small-k curve; information only).
MUTATE (parity's mutation check): a charge site's name; that site charges one op more than the cost model."""
import math

TRACE = None
SMALL = 0
MUTATE = None

LAYOUTS = ("stride", "fold", "map", "bins", "exponent")
RULES = ("dot", "batch", "floyd", "brent", "bins")
SITES = ("stride", "fold_word", "fold_mul", "map", "bins_word", "bins_mul", "bins_hash", "exponent",
         "dot_gcd", "batch_mul", "batch_gcd", "bt_gcd", "floyd_mul", "floyd_gcd", "brent_mul", "brent_gcd",
         "cmp_sort", "cmp_gcd")

def _int(g, k, lo, hi=None, default=None):
    v = g.get(k, default)
    if not isinstance(v, int) or isinstance(v, bool) or v < lo or (hi is not None and v > hi):
        raise ValueError(f"arr: gene {k} = {v!r} out of range")
    return v

def validate(s):
    """Raises ValueError for a stage that may not be built (bad genes, or a rule the layout cannot take)."""
    L, D = s.get("layout"), s.get("detect")
    if not isinstance(L, dict) or not isinstance(D, dict) or L.get("kind") not in LAYOUTS or D.get("kind") not in RULES:
        raise ValueError("arr: layout and detect must name a known kind")
    k = L["kind"]
    if k == "stride":
        _int(L, "a", 0); _int(L, "s", 1)
    elif k == "fold":
        _int(L, "w", 2, 4096); _int(L, "a", 0); _int(L, "s", 1)
    elif k == "map":
        _int(L, "c", 0, default=1); _int(L, "x0", 0, default=2)
        if L.get("d", 2) not in (2, 4, 6, 8) or isinstance(L.get("d", 2), bool):
            raise ValueError("arr: map degree d must be 2, 4, 6 or 8")
    elif k == "bins":
        _int(L, "m", 1); B = _int(L, "B", 1, 1 << 16)
        if B & (B - 1):
            raise ValueError("arr: B must be a power of 2")
    else:
        _int(L, "a", 0); _int(L, "K", 1)
    r = D["kind"]
    if r in ("dot", "batch"):
        _int(D, "t", 0, default=0)
    if r in ("batch", "floyd", "brent"):
        _int(D, "b", 1, 4096)
    if r in ("floyd", "brent") and k not in ("map", "stride"):
        raise ValueError("arr: floyd and brent need a map or stride layout")
    if r == "bins" and k != "bins":
        raise ValueError("arr: bin compare needs the bins layout")

class Layout:
    """The dots x_0, x_1, ... mod N. dot() places the next one (charged per the layout); f(v, extra) is the step of a
    map or stride layout as a function, charged with `extra` more mul in the same charge (rho's batched step)."""
    def __init__(self, g, N, ch):
        self.k, self.N, self.ch, self.started = g["kind"], N, ch, False
        if self.k == "stride":
            self.x, self.s = g["a"] % N, g["s"] % N
        elif self.k == "map":
            self.c, self.d, self.x = g.get("c", 1) % N, g.get("d", 2), g.get("x0", 2) % N
            self.step = max(1, self.d.bit_length() - 1 + bin(self.d).count("1") - 1)
        elif self.k == "fold":
            self.w, self.v, self.s = g["w"], g["a"] % N, g["s"] % N
        elif self.k == "bins":
            self.m, self.y = g["m"] % N, 0
        else:
            self.x, self.kk, self.K = g["a"] % N, 0, g["K"]

    def copy(self):
        c = Layout.__new__(Layout)
        c.__dict__.update(self.__dict__)
        return c

    def f(self, v, extra=0):
        N = self.N
        if self.k == "stride":
            self.ch({"word": 1, "mul": extra}, "stride")
            return (v + self.s) % N
        self.ch({"mul": self.step + extra}, "map")
        return ((v * v if self.d == 2 else pow(v, self.d, N)) + self.c) % N

    def dot(self):
        """The next dot, or None when the layout is finished (exponent past K)."""
        N, ch = self.N, self.ch
        if self.k in ("stride", "map"):
            if self.started:
                self.x = self.f(self.x)
            self.started = True
            return self.x
        if self.k == "fold":
            p = 1
            for _ in range(self.w):
                ch({"word": 1}, "fold_word")
                v, self.v = self.v, (self.v + self.s) % N
                ch({"mul": 1}, "fold_mul")
                p = p * v % N
            return p
        if self.k == "bins":
            ch({"word": 1}, "bins_word")
            self.y = (self.y + self.m) % N
            ch({"mul": 1}, "bins_mul")
            x = self.y * self.y % N
            ch({"hash": 1}, "bins_hash")
            return x
        self.kk += 1
        if self.kk > self.K:
            return None
        ch({"mul": max(1, self.kk.bit_length())}, "exponent")
        self.x = pow(self.x, self.kk, N)
        return self.x

def lamp_arr(N, g, m):
    global SMALL
    validate(g)
    tr = TRACE

    def ch(parts, site):
        n = 0
        for t, k in parts.items():
            if k:
                if tr is not None:
                    tr[t] = tr.get(t, 0) + k
                n += k
        if MUTATE == site:
            n += 1
            if tr is not None:
                tr["mutated"] = tr.get("mutated", 0) + 1
        m.tick(n)

    def gt(v, site):
        """One charged gcd of v with N, one luck-meter test (hit: the gcd is not 1)."""
        global SMALL
        ch({"gcd": 1}, site)
        if v.bit_length() <= 64:
            SMALL += 1
        G = math.gcd(v, N)
        m.test(G != 1)
        return G

    L = Layout(g["layout"], N, ch)
    D = g["detect"]
    r = D["kind"]

    if r == "dot":
        t = D.get("t", 0)
        x = L.dot()
        while x is not None:
            G = gt((x - t) % N, "dot_gcd")
            if 1 < G < N:
                return G
            x = L.dot()
        return None

    if r == "batch":
        t, b = D.get("t", 0), D["b"]
        st, q, n = L.copy(), 1, 0
        while True:
            x = L.dot()
            if x is not None:
                ch({"mul": 1}, "batch_mul")
                q = q * ((x - t) % N) % N
                n += 1
            if n and (n == b or x is None):
                G = gt(q, "batch_gcd")
                if G == N:
                    for _ in range(n):            # the backtrack: re-place the batch's dots, one gcd each
                        y = st.dot()
                        G = gt((y - t) % N, "bt_gcd")
                        if G != 1:
                            return G if G < N else None
                    return None
                if G != 1:
                    return G
                st, n = L.copy(), 0
            if x is None:
                return None

    if r == "floyd":
        b = D["b"]
        x = y = L.dot()
        q, n, sx, sy = 1, 0, x, y
        while True:
            x = L.f(x)
            y = L.f(L.f(y))
            ch({"mul": 1}, "floyd_mul")
            q = q * abs(x - y) % N
            n += 1
            if n == b:
                G = gt(q, "floyd_gcd")
                if G == N:
                    x, y = sx, sy
                    for _ in range(n):
                        x = L.f(x)
                        y = L.f(L.f(y))
                        G = gt(abs(x - y), "bt_gcd")
                        if G != 1:
                            return G if G < N else None
                    return None
                if G != 1:
                    return G
                n, sx, sy = 0, x, y

    if r == "brent":                              # lamps.lamp_rho's loop, with the layout's step
        b = D["b"]
        y, rr, q, G = L.dot(), 1, 1, 1
        while True:
            x = y
            for _ in range(rr):
                y = L.f(y)
            k = 0
            while k < rr and G == 1:
                ys = y
                for _ in range(min(b, rr - k)):
                    y = L.f(y, 1 + (MUTATE == "brent_mul"))
                    q = q * abs(x - y) % N
                G = gt(q, "brent_gcd")
                k += b
            rr *= 2
            if G != 1:
                break
        if G == N:
            while True:
                ys = L.f(ys)
                G = gt(abs(x - ys), "bt_gcd")
                if G > 1:
                    break
        return G if 1 < G < N else None

    B = g["layout"]["B"]                          # bin compare
    bins = {}
    while True:
        x = L.dot()
        lst = bins.setdefault(x & (B - 1), [])
        for y in lst:
            ch({"sort_cmp": 1}, "cmp_sort")
            G = gt(abs(x - y), "cmp_gcd")
            if 1 < G < N:
                return G
        lst.append(x)

def counts(tr, ops, tests):
    """The stage's per-type split (optypes.per_type): word, hash and sort_cmp from the trace, gcd = tests (rho's
    convention), mul the rest. The trace's own mul + gcd must equal that remainder."""
    tr = tr or {}
    w, h, s = tr.get("word", 0), tr.get("hash", 0), tr.get("sort_cmp", 0)
    c = {"mul": ops - tests - w - h - s, "gcd": tests}
    for t, n in (("word", w), ("hash", h), ("sort_cmp", s)):
        if n:
            c[t] = n
    if TRACE is not None or tr:
        assert tr.get("mul", 0) + tr.get("gcd", 0) + tr.get("mutated", 0) == ops - w - h - s, ("arr trace", tr, ops)
    return c
