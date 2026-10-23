"""Pollard–Strassen block flash: rule out a whole block of stations per evaluation.

f(x) = (x+1)(x+2)...(x+B) mod N.  f(iB) is the product of block i, stations iB+1..iB+B.
All block products come from one multipoint evaluation (product tree + remainder tree),
so m blocks of B stations cost about M(B) log B + M(m) log m instead of m*B.

Cost model: a polynomial product with n output coefficients over Z/N is charged as
FFT arithmetic, 3*(n/2)*log2(n) + n ring multiplies (next power of two n).
The Python computes the same products exactly with Kronecker substitution on big
integers, for speed; the charge is the FFT count, not CPython's Karatsuba work.
Additions and subtractions are not charged, matching the other lamps.
"""
import math

def fft_cost(n_out):
    n = 1
    while n < n_out:
        n *= 2
    return 3 * (n // 2) * max(1, n.bit_length() - 1) + n

def pmul(a, b, N, m):
    """Multiply coefficient lists (low to high) mod N."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return []
    m.tick(fft_cost(la + lb - 1))
    if la < 8 or lb < 8:                      # tiny products: schoolbook, same answer
        out = [0] * (la + lb - 1)
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    out[i + j] += x * y
        return [c % N for c in out]
    slot = 2 * N.bit_length() + min(la, lb).bit_length() + 1
    slot = (slot + 7) // 8 * 8
    nb = slot // 8
    A = int.from_bytes(b"".join(x.to_bytes(nb, "little") for x in a), "little")
    Bv = int.from_bytes(b"".join(y.to_bytes(nb, "little") for y in b), "little")
    raw = (A * Bv).to_bytes((la + lb) * nb, "little")
    return [int.from_bytes(raw[i * nb:(i + 1) * nb], "little") % N for i in range(la + lb - 1)]

def inv_series(g, k, N, m):
    """h with g*h = 1 mod x^k, g[0] = 1 (Newton iteration)."""
    h = [1]
    prec = 1
    while prec < k:
        prec = min(2 * prec, k)
        gh = pmul(g[:prec], h, N, m)[:prec]
        two_minus = [(-c) % N for c in gh]
        two_minus[0] = (two_minus[0] + 2) % N
        h = pmul(h, two_minus, N, m)[:prec]
    return h

def pmod(a, b, N, m):
    """a mod b for monic b."""
    da, db = len(a) - 1, len(b) - 1
    if da < db:
        return a
    k = da - db + 1
    ra, rb = a[::-1], b[::-1]
    q_rev = pmul(ra[:k], inv_series(rb, k, N, m), N, m)[:k]
    q = q_rev[::-1]
    bq = pmul(b, q, N, m)
    r = [(a[i] - bq[i]) % N for i in range(db)]
    return r

def product_tree(leaves, N, m):
    tree = [leaves]
    while len(tree[-1]) > 1:
        lvl = tree[-1]
        nxt = [pmul(lvl[i], lvl[i + 1], N, m) if i + 1 < len(lvl) else lvl[i]
               for i in range(0, len(lvl), 2)]
        tree.append(nxt)
    return tree

def multipoint(f, pts, N, m):
    tree = product_tree([[(-x) % N, 1] for x in pts], N, m)
    rems = [pmod(f, tree[-1][0], N, m)]
    for lvl in range(len(tree) - 2, -1, -1):
        nxt = []
        for i, node in enumerate(tree[lvl]):
            nxt.append(pmod(rems[i // 2], node, N, m))
        rems = nxt
    return [r[0] if r else 0 for r in rems]

def lamp_ps(N, g, m):
    """Block flash covering stations 1..N^a in blocks of B = c*N^s."""
    L = int(N ** g["a"]) + 1
    B = max(2, int(g["c"] * N ** g["s"]))
    nblocks = (L + B - 1) // B
    f = product_tree([[j % N, 1] for j in range(1, B + 1)], N, m)[-1][0]
    vals = multipoint(f, [i * B for i in range(nblocks)], N, m)
    for i, v in enumerate(vals):
        d = math.gcd(v, N); m.tick()
        if d == 1:
            continue
        if d < N:
            return d
        for st in range(i * B + 1, i * B + B + 1):        # block holds both p and q: scan it
            m.tick()
            if st > 1 and N % st == 0:
                return st
    return None
