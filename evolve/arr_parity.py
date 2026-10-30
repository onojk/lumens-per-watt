"""Parity for the arrangement lamp arr (arrangement-v1; NOTES, "Cost model: the arrangement lamp", 6062320, and the stride
ruling 77e898e). Untimed counts; not scored; no training run.
  1. map(c = 1, d = 2, x0 = 2) + brent(b) = lampcore rho {"c": 1, "b": b} exactly (ops, factor, tests, hits, stage, k,
     per-type counts), lampcore against lampcore and Python against lampcore; also d = 4, 6, 8 and other c, x0.
  2. stride(a = 2, s = 1) + dot(t = 0) against vl {"a": 0.5}: factor, tests, hits and gcds identical; ops = vl ops +
     exactly one word per step (dots - 1); per-type = vl's gcd plus word = dots - 1.
  3. Python (lamps.run, TYPES on) against lampcore --types on every valid layout x rule pair, several gene sets each,
     alone, under an ob, and in a pipeline after an ob-limited arr stage: the whole output line, including the
     per-type counts and gcd_small (" A ..."), must be identical. Caps are small, so censored runs are included.
  4. Refusals: invalid genomes are refused by both cores.
  5. Mutation check: each charge site in arr.SITES, charged one op more in Python (arr.MUTATE), must be caught by (3);
     each type arr uses, dropped and doubled in lampcore's output (LAMPCORE_TYPES_MUTATE), must be caught.
  6. gcd_small's threshold (< 2^32, G_rho v2, 9e89a4e) at 36-56 bits, where gcd arguments fall between 2^32 and 2^64
     (the 20-28-bit numbers of (3) cannot tell 2^32 from 2^64): Python = lampcore on the whole line; some gcds counted
     small and some not; and the v1 threshold (Python with arr.MUTATE = "small64") must differ.
  python3 arr_parity.py > arr_parity.out; exit 3 on any failure"""
import sys
sys.argv = sys.argv[:1]
import json, os, random, subprocess
import lamps, optypes, arr
from lamps import rand_prime
from fastlamps import BIN

def semiprimes(bits, n, seed, lo_frac=0.5):
    rng, out = random.Random(seed), []
    while len(out) < n:
        a = max(2, int(bits * lo_frac))
        p, q = rand_prime(a, rng), rand_prime(bits - a, rng)
        if p != q and (p * q).bit_length() == bits:
            out.append((p * q, min(p, q), max(p, q)))
    return out

def core(gen, nums, cap, env=None):
    text = json.dumps(gen) + "\n" + str(cap) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    r = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, env=env)
    if r.returncode:
        return None
    return r.stdout.splitlines()

def py(gen, N, cap):
    lamps.TYPES = True
    ops, d = lamps.run(gen, N, cap)
    L = lamps.LAST
    head = f"{ops} {d} {L['tests']} {L['hits']} {L['stage']} -" if d else f"miss {L['tests']} {L['hits']}"
    tail = (f" A {L['arr_small']}" if any(s["t"] == "arr" for s in gen) else "")
    ty = L.get("types") or {}
    return head + tail + " T" + "".join(f" {ty.get(t, 0)}" for t in optypes.TYPE_ORDER)

def fields(line):
    f = line.split()
    i = f.index("T")
    return f, {t: int(n) for t, n in zip(optypes.TYPE_ORDER, f[i + 1:]) if int(n)}

def A(layout, detect, **kw):
    return {"t": "arr", "layout": layout, "detect": detect, **kw}

LAYOUTS = {
    "stride": [{"kind": "stride", "a": 2, "s": 1}, {"kind": "stride", "a": 5, "s": 3}, {"kind": "stride", "a": 0, "s": 7}],
    "fold": [{"kind": "fold", "w": 2, "a": 2, "s": 1}, {"kind": "fold", "w": 16, "a": 3, "s": 2}],
    "map": [{"kind": "map", "c": 1, "d": 2, "x0": 2}, {"kind": "map", "c": 3, "d": 4, "x0": 5},
            {"kind": "map", "c": 7, "d": 6, "x0": 11}, {"kind": "map", "c": 1, "d": 8, "x0": 2}],
    "bins": [{"kind": "bins", "m": 1, "B": 1}, {"kind": "bins", "m": 3, "B": 16}, {"kind": "bins", "m": 7, "B": 256}],
    "exponent": [{"kind": "exponent", "a": 2, "K": 400}, {"kind": "exponent", "a": 3, "K": 5000}],
}
RULES = {
    "dot": [{"kind": "dot"}, {"kind": "dot", "t": 1}],
    "batch": [{"kind": "batch", "b": 1, "t": 1}, {"kind": "batch", "b": 7}, {"kind": "batch", "b": 64, "t": 1}],
    "floyd": [{"kind": "floyd", "b": 1}, {"kind": "floyd", "b": 10}],
    "brent": [{"kind": "brent", "b": 1}, {"kind": "brent", "b": 7}, {"kind": "brent", "b": 128}],
    "bins": [{"kind": "bins"}],
}
VALID = [(l, r) for l in LAYOUTS for r in RULES
         if not (r in ("floyd", "brent") and l not in ("map", "stride")) and not (r == "bins" and l != "bins")]
CAP = 400_000

def pair_genomes():
    out = []
    for l, r in VALID:
        for i, lg in enumerate(LAYOUTS[l]):
            for j, dg in enumerate(RULES[r]):
                if (i + j) % 2 and len(LAYOUTS[l]) * len(RULES[r]) > 4:
                    continue                      # a spread of gene combinations, not the full product
                out.append(((l, r), [A(lg, dg)]))
        lg, dg = LAYOUTS[l][0], RULES[r][-1]
        out.append(((l, r), [A(lg, dg, ob=3000)]))
        out.append(((l, r), [A(lg, dg, ob=2000), {"t": "rho", "c": 1, "b": 16}]))
    return out

def numbers():
    nums = []
    for bits in (20, 24, 28):
        nums += semiprimes(bits, 5, 9940000 + bits)
        nums += semiprimes(bits, 3, 9945000 + bits, lo_frac=0.3)
    return nums

if __name__ == "__main__":
    fail = 0
    nums = numbers()
    # 1. map + brent = rho
    bad = tot = 0
    for b in (1, 2, 7, 64, 256):
        for extra in ({}, {"d": 4, "c": 3, "x0": 5}, {"d": 8, "c": 1, "x0": 2}, {"d": 6, "c": 9, "x0": 3}):
            rg = {"t": "rho", "c": extra.get("c", 1), "b": b, **({"d": extra["d"], "x0": extra["x0"]} if extra else {})}
            ag = A({"kind": "map", "c": extra.get("c", 1), "d": extra.get("d", 2), "x0": extra.get("x0", 2)}, {"kind": "brent", "b": b})
            for cap in (10 ** 12, 3000):
                rc, ac = core([rg], nums, cap), core([ag], nums, cap)
                for (N, _, _), x, y in zip(nums, rc, ac):
                    tot += 1
                    yr = y.split(" A ")[0] + " T" + y.split(" T", 1)[1]     # arr's line carries " A n" in addition
                    ok = x == yr and py([ag], N, cap) == y
                    bad += not ok
                    if not ok and bad < 4:
                        print("  mismatch", N, rg, x, y, py([ag], N, cap))
    print(f"1. map(c, d, x0) + brent(b) = lampcore rho exactly (ops, factor, tests, hits, stage, k, per-type), and Python = "
          f"lampcore: {tot - bad}/{tot} identical")
    fail += bad
    # 2. stride + dot against vl
    bad = tot = 0
    vnums = [x for bits in (20, 24, 28, 32) for x in semiprimes(bits, 8, 9950000 + bits)]
    vc = core([{"t": "vl", "a": 0.5}], vnums, 10 ** 12)
    sg = [A({"kind": "stride", "a": 2, "s": 1}, {"kind": "dot", "t": 0})]
    sc = core(sg, vnums, 10 ** 12)
    for (N, p, _), v, s in zip(vnums, vc, sc):
        tot += 1
        (vf, vt), (sf, st) = fields(v), fields(s)
        dots = int(sf[2])
        ok = (sf[1:4] == vf[1:4] and int(sf[0]) == int(vf[0]) + dots - 1 and sf[1] == str(p)
              and st == ({**vt, "word": dots - 1} if dots > 1 else vt) and py(sg, N, 10 ** 12) == s)
        bad += not ok
        if not ok and bad < 4:
            print("  mismatch", N, v, s)
    print(f"2. stride(2, 1) + dot(0) against vl(0.5), 32 numbers at 20-32 bits: factor, tests, hits and gcds identical, "
          f"ops = vl + exactly (dots - 1) word, Python = lampcore: {tot - bad}/{tot}")
    fail += bad
    # 3. every layout x rule pair
    gens = pair_genomes()
    lines = {}
    bad = tot = 0
    seen = {}
    for (l, r), g in gens:
        c = core(g, nums, CAP)
        lines[json.dumps(g)] = c
        for (N, _, _), x in zip(nums, c):
            tot += 1
            ok = py(g, N, CAP) == x
            bad += not ok
            k = f"{l} x {r}"
            seen.setdefault(k, [0, 0, 0])
            seen[k][0] += 1
            seen[k][1] += not x.startswith("miss")
            seen[k][2] += not ok
            if not ok and bad < 4:
                print("  mismatch", N, g, x, py(g, N, CAP))
    for k, (n, hit, b) in seen.items():
        print(f"   {k:20s} {n:4d} runs, {hit:4d} factored, {b} mismatches")
    used = sorted({t for c in lines.values() for x in c for t in fields(x)[1]})
    print(f"3. every valid layout x rule pair ({len(VALID)} pairs, {len(gens)} genomes, {len(nums)} numbers at 20/24/28 bits, "
          f"cap {CAP}, alone, under ob, and before rho): {tot - bad}/{tot} identical lines; types in use {used}")
    fail += bad
    # 4. refusals
    BADG = [A({"kind": "fold", "w": 4, "a": 2, "s": 1}, {"kind": "brent", "b": 4}),
            A({"kind": "exponent", "a": 2, "K": 9}, {"kind": "floyd", "b": 1}),
            A({"kind": "bins", "m": 1, "B": 16}, {"kind": "floyd", "b": 1}),
            A({"kind": "map", "c": 1, "d": 2, "x0": 2}, {"kind": "bins"}),
            A({"kind": "map", "c": 1, "d": 3, "x0": 2}, {"kind": "dot"}),
            A({"kind": "map", "c": 1, "d": 10, "x0": 2}, {"kind": "dot"}),
            A({"kind": "bins", "m": 1, "B": 24}, {"kind": "bins"}),
            A({"kind": "bins", "m": 1, "B": 1 << 17}, {"kind": "bins"}),
            A({"kind": "stride", "a": 2, "s": 0}, {"kind": "dot"}),
            A({"kind": "fold", "w": 1, "a": 2, "s": 1}, {"kind": "dot"}),
            A({"kind": "stride", "a": 2, "s": 1}, {"kind": "batch", "b": 0}),
            A({"kind": "stride", "a": 2, "s": 1}, {"kind": "batch", "b": 5000}),
            A({"kind": "spiral", "a": 2}, {"kind": "dot"}),
            A({"kind": "stride", "a": 2, "s": 1}, {"kind": "guess"}),
            A({"kind": "stride", "a": 1 << 64, "s": 1}, {"kind": "dot"}),          # genes >= 2^64 (lampcore's u64)
            A({"kind": "map", "c": 1 << 64, "d": 2, "x0": 2}, {"kind": "brent", "b": 4}),
            A({"kind": "exponent", "a": 2, "K": 400}, {"kind": "dot", "t": 1 << 70}),
            A({"kind": "bins", "m": (1 << 64) + 1, "B": 16}, {"kind": "bins"})]
    ref = 0
    for g in BADG:
        try:
            lamps.run([g], nums[0][0], CAP)
            pr = False
        except ValueError:
            pr = True
        rr = core([g], nums[:1], CAP) is None
        ref += pr and rr
        if not (pr and rr):
            print("  not refused by both", g, pr, rr)
    print(f"4. refusals: {ref}/{len(BADG)} invalid genomes refused by both cores")
    fail += len(BADG) - ref
    # 5. mutation check
    caught = {}
    for site in arr.SITES:
        arr.MUTATE = site
        hit = False
        for g_json, c in lines.items():
            g = json.loads(g_json)
            if any(py(g, N, CAP) != x for (N, _, _), x in zip(nums, c)):
                hit = True
                break
        arr.MUTATE = None
        caught[f"charge {site} +1"] = hit
    for t in used:
        for how in ("drop", "double"):
            env = {**os.environ, "LAMPCORE_TYPES_MUTATE": f"{t}:{how}"}
            hit = any(core(json.loads(gj), nums, CAP, env) != c for gj, c in lines.items())
            caught[f"lampcore {t} {how}"] = hit
    miss = [k for k, v in caught.items() if not v]
    print(f"5. mutations caught: {len(caught) - len(miss)}/{len(caught)}" + (f"; NOT caught: {miss}" if miss else ""))
    fail += len(miss)
    # 6. gcd_small's threshold
    tn = [x for bits in (36, 44, 56) for x in semiprimes(bits, 3, 9960000 + bits)]
    TG = [[A({"kind": "map", "c": 1, "d": 2, "x0": 2}, {"kind": "brent", "b": 16})],
          [A({"kind": "stride", "a": 2, "s": 1}, {"kind": "dot"}, ob=20000)],
          [A({"kind": "stride", "a": 1 << 40, "s": 1}, {"kind": "dot"}, ob=20000)],
          [A({"kind": "bins", "m": 1, "B": 1}, {"kind": "bins"}, ob=20000)]]
    bad = tot = 0
    small = gcds = 0
    caught = False
    for g in TG:
        c = core(g, tn, 200_000)
        for (N, _, _), x in zip(tn, c):
            tot += 1
            ok = py(g, N, 200_000) == x
            bad += not ok
            f, ty = fields(x)
            small += int(f[f.index("A") + 1]); gcds += ty.get("gcd", 0)
            arr.MUTATE = "small64"
            caught |= py(g, N, 200_000) != x
            arr.MUTATE = None
    mixed = 0 < small < gcds
    print(f"6. gcd_small < 2^32 at 36/44/56 bits ({len(TG)} genomes x {len(tn)} numbers): {tot - bad}/{tot} identical lines; "
          f"{small} of {gcds} gcds small (both kinds present: {mixed}); the v1 threshold (< 2^64) caught: {caught}")
    fail += bad + (not mixed) + (not caught)
    print(f"exit {3 if fail else 0}")
    sys.exit(3 if fail else 0)
