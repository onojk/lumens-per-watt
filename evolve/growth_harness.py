"""Growth harness v1 (NOTES.md, "Growth-exponent harness: cost note and design", 52c03f4 / 38b3828; the user's next round,
item 2, Oct 28; predictions/growth-v1.md filed first). Each lamp ALONE on 48 fresh balanced semiprimes per size,
semiprimes_pq(bits, 48, 9600000 + bits), at 40, 48, ..., 96 bits, lampcore --types:
  td    partition.PRE genes, cap 2^34, sizes <= 64 only (by design: it needs ~2^(bits/2) divisions)
  rho   partition.PRE genes, cap 2^34 (no budget: alone to success)
  pm1   partition.PRE genes (B from N), cap 2^34
  ecm   partition.PRE genes, cap 2^34
  cfrac accepted genes (kc 32, bc 1.1), cap 2^34
  qs    the reference genes (2'b) at 54 / 72 / 84 / 96; at the other sizes interpolated genes (qs_genes; the user's
        decision, Oct 28, after the first counts run failed on a missing 40-bit reference, 083b916), cap 2^28
Cost per factorisation = total priced cost spent (censored spending included) / successes, per pricing: official, ruint,
Montgomery (optypes.prices, median P-core), op-class v1 (types without a v1 weight make the v1 figure "n/a"). A cell
with < 24 / 48 successes is reported and excluded from fits.
Fits (per lamp, per pricing; bootstrap over numbers within sizes, 10,000 resamples, random.Random(2026)):
  local slope beta(b) = d log2 C / d bits between neighbouring sizes; doubling period = 1 / beta;
  L form ln C = ln A + c (ln N)^a (ln ln N)^(1-a): fixed a in {1/3, 1/2, 1} (c and the residual), and free a by a grid
  (0.20 .. 1.00, step 0.01) with c, ln A by least squares at each a; N = 2^bits per size.
  Crossing: the size where two lamps' interpolated log2 C are equal (R-31: rho and qs).
  python3 growth_harness.py counts -> growth_counts.json (untimed)
  python3 growth_harness.py fit    -> growth_fit.json, stdout (from growth_counts.json)
  python3 growth_harness.py wall   -> growth_wall.json (timed; Run B's conditions; 4 replicates; only when the user says)"""
import sys
ARGV = sys.argv[1:]
import json, math, random, statistics, subprocess, time
import numpy as np
import partition as P, optypes
from fastlamps import BIN, semiprimes_pq
from baseline_msieve import reference, conditions, cool

SIZES = (40, 48, 56, 64, 72, 80, 88, 96)
PER, CAP = 48, 2 ** 34
V1 = {k: v["weight"] for k, v in json.load(open("../opclass/opclass_v1.json"))["classes"].items() if v["weight"]}
PR = optypes.prices()

SEALED_SIZES = (54, 72, 84, 96)

def qs_genes(bits):
    """QS genes for the growth harness (the user's decision, Oct 28: "interpolated genes, growth harness only"; not a
    reference anywhere else): at a sealed size, the reference (2'b) genes; otherwise each numeric gene (kc, bc, mc, tc,
    lc) interpolated linearly in bits between the neighbouring sealed sizes (kc rounded; with kset sf32 the
    multipliers are fixed anyway); below 54, the 54-bit genes held constant. Non-numeric genes are the reference's."""
    if bits in SEALED_SIZES:
        return reference(bits)
    if bits < SEALED_SIZES[0]:
        return dict(reference(SEALED_SIZES[0]), interpolated="held at 54")
    lo = max(b for b in SEALED_SIZES if b < bits); hi = min(b for b in SEALED_SIZES if b > bits)
    a, b, t = reference(lo), reference(hi), (bits - lo) / (hi - lo)
    g = dict(a)
    for k in ("bc", "mc", "tc", "lc"):
        g[k] = a[k] + t * (b[k] - a[k])
    g["kc"] = round(a["kc"] + t * (b["kc"] - a["kc"]))
    g["interpolated"] = f"{lo}-{hi}"
    return g

def lamps(bits):
    L = {"rho": ([dict(P.PRE["rho"])], CAP), "pm1": ([dict(P.PRE["pm1"])], CAP), "ecm": ([dict(P.PRE["ecm"])], CAP),
         "cfrac": ([{"t": "cfrac", "kc": 32, "bc": 1.1}], CAP), "qs": ([qs_genes(bits)], P.QS_CAP)}
    if bits <= 64:
        L = {"td": ([dict(P.PRE["td"])], CAP), **L}
    return L

def run(genome, cap, nums):
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    t0 = time.perf_counter()
    out = subprocess.run(["taskset", "-c", "2", BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout
    dt = time.perf_counter() - t0
    res = []
    for (N, p, q), l in zip(nums, out.splitlines()):
        f = l.split(); i = f.index("T")
        res.append({"ok": f[1] != "miss" and int(f[1]) in (p, q), "types": dict(zip(optypes.TYPE_ORDER, map(int, f[i + 1:])))})
    return res, dt

def costs(ty):
    off = float(sum(ty.values()))
    ru = optypes.cost(ty, "ruint", PR); mo = optypes.cost(ty, "montgomery", PR)
    v1 = None if any(n and t not in V1 for t, n in ty.items()) else sum(V1[t] * n for t, n in ty.items() if n)
    return {"official": off, "ruint": ru, "montgomery": mo, "opclass_v1": v1}

def per_fact(rows, pricing):
    s = sum(r["ok"] for r in rows)
    if s < PER // 2 or any(r["cost"][pricing] is None for r in rows):
        return None
    return sum(r["cost"][pricing] for r in rows) / s

def lfit(bits, logC, a):
    x = np.array([(b * math.log(2)) ** a * math.log(b * math.log(2)) ** (1 - a) for b in bits])
    X = np.vstack([np.ones_like(x), x]).T
    coef, res, *_ = np.linalg.lstsq(X, np.array(logC), rcond=None)
    r = float(np.sum((X @ coef - np.array(logC)) ** 2))
    return float(coef[1]), float(coef[0]), r

def fits(data, lamp, pricing, rng=None):
    sizes = [b for b in SIZES if lamp in data[str(b)]]
    rows = {b: data[str(b)][lamp] for b in sizes}
    if rng:
        rows = {b: [rows[b][rng.randrange(len(rows[b]))] for _ in rows[b]] for b in sizes}
    C = {b: per_fact(rows[b], pricing) for b in sizes}
    ok = [b for b in sizes if C[b]]
    if len(ok) < 3:
        return None
    lg = {b: math.log2(C[b]) for b in ok}
    slopes = {f"{a}-{b}": (lg[b] - lg[a]) / (b - a) for a, b in zip(ok, ok[1:])}
    lnC = [C[b] and math.log(C[b]) for b in ok]
    fixed = {str(a): lfit(ok, lnC, a) for a in (1 / 3, 1 / 2, 1.0)}
    grid = [(lfit(ok, lnC, a / 100)[2], a / 100) for a in range(20, 101)]
    best_a = min(grid)[1]
    c, lnA, r = lfit(ok, lnC, best_a)
    return {"sizes": ok, "log2C": lg, "slopes": slopes, "fixed_a": fixed, "free": {"a": best_a, "c": c, "lnA": lnA, "res": r}}

if __name__ == "__main__":
    mode = ARGV[0] if ARGV else ""
    if mode == "counts":
        out = {}
        for bits in SIZES:
            nums = semiprimes_pq(bits, PER, 9600000 + bits)
            out[str(bits)] = {}
            for name, (g, cap) in lamps(bits).items():
                res, dt = run(g, cap, nums)
                for r in res:
                    r["cost"] = costs(r["types"])
                out[str(bits)][name] = res
                s = sum(r["ok"] for r in res)
                c = per_fact(res, "ruint")
                print(f"{bits} bits {name}: {s}/{PER} succeeded; ruint cost per factorisation {c and round(c):}; ({dt:.1f} s, untimed)", flush=True)
        json.dump(out, open("growth_counts.json", "w"))
    elif mode == "fit":
        data = json.load(open("growth_counts.json"))
        out = {}
        for lamp in ("td", "rho", "pm1", "ecm", "cfrac", "qs"):
            out[lamp] = {}
            for pricing in ("opclass_v1", "ruint", "montgomery", "official"):
                f = fits(data, lamp, pricing)
                if not f:
                    out[lamp][pricing] = None
                    continue
                rng = random.Random(2026)
                boots = [fits(data, lamp, pricing, rng) for _ in range(10000)]
                boots = [b for b in boots if b]
                def ci(get):
                    v = sorted(x for x in (get(b) for b in boots) if x is not None)
                    return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None
                f["slopes_ci"] = {k: ci(lambda b, k=k: b["slopes"].get(k)) for k in f["slopes"]}
                f["free_ci"] = {"a": ci(lambda b: b["free"]["a"]), "c": ci(lambda b: b["free"]["c"])}
                f["c_fixed_half_ci"] = ci(lambda b: b["fixed_a"]["0.5"][0])
                out[lamp][pricing] = f
                print(f"{lamp} [{pricing}]: sizes {f['sizes']}; local slopes " + ", ".join(
                    f"{k} {v:.3f} (doubling {1 / v:.1f} bits) [{f['slopes_ci'][k][0]:.3f}, {f['slopes_ci'][k][1]:.3f}]" for k, v in f["slopes"].items() if v > 0)
                    + f"; L fit a = 1/2: c = {f['fixed_a']['0.5'][0]:.3f} {f['c_fixed_half_ci']}; free a = {f['free']['a']:.2f} {f['free_ci']['a']}, "
                    f"c = {f['free']['c']:.3f} {f['free_ci']['c']}", flush=True)
        json.dump(out, open("growth_fit.json", "w"), indent=1)
    elif mode == "wall":
        bad = conditions()
        if bad:
            print("timing skipped: " + "; ".join(bad)); sys.exit(2)
        out = {}
        for bits in SIZES:
            nums = semiprimes_pq(bits, PER, 9600000 + bits)
            out[str(bits)] = {}
            for name, (g, cap) in lamps(bits).items():
                ts = []
                for r in range(4):
                    cool()
                    res, dt = run(g, cap, nums)
                    ts.append(dt / PER)
                out[str(bits)][name] = {"s_per_number": ts, "succeeded": sum(x["ok"] for x in res)}
                print(f"{bits} bits {name}: {1e3 * statistics.mean(ts):.3f} ms per number (4 replicates)", flush=True)
        json.dump(out, open("growth_wall.json", "w"), indent=1)
    else:
        print(__doc__)
