"""Scoring harness for arrangement-v1 (design docs/planning/arrangement_lamps.md §8 step 4; predictions
predictions/arrangement-v1.md; fitness G_rho, reviews/growth_fitness_rho.md, frozen 77ff2ee, with G,
reviews/growth_fitness.md, frozen c86ef35). A judge file: pinned in the predictions, run only through tools/sealed_run.sh.

Input: genome files written by the search (tools/search_sandbox.sh -> search_out/), each a JSON genome (a list of
stages) or {"name": ..., "genome": [...]}. Every genome must hold an arr stage and pass lamps.validate_genome.

Maps (design §8; numbers never seen by the search):
  balanced  48 per size at 48, 64, 80 and 96 bits, semiprimes_pq(bits, 48, 9930000 + bits)
  theta     96 per size at 64 and 80 bits, theta = log2 p / log2 N uniform in [0.20, 0.30), seeds 9935000 + bits
            (twilight2_search.numbers' draw with the band changed; Q5's map: cost against rho only, no growth)
Arms, each on the same numbers (the paired bootstrap): the candidate; rho alone (partition.PRE["rho"], G_rho's
reference genes); on the balanced map at 80 and 96 bits, the reference card's QS (growth_harness.qs_genes: the
sealed 2'b genes at 96, interpolated at 80, as G's reference). Untimed counts, lampcore --types; 2 lampcore processes
at a time (the user's instruction: the laptop runs hot). Caps: CAP = 2^34 for the candidate and rho (the growth
harness's cap, as G_rho's reference); partition.QS_CAP for QS.

Pricing per run (growth_harness.costs): official, ruint, Montgomery, op-class v1, and op-class v1 with the size-scaled
gcd price (gcdscale.py; per gcd, the small-k curve for the arr gcds whose other argument was < 2^64, lampcore's " A n"
column, and the uniform-k curve for every other gcd). C(s) = total priced cost, censored spending included, divided
by successes (growth_harness.per_fact). A success is a factor equal to p or q.

Reported per genome (balanced map):
  - the op-count growth slope 48-80: least squares of log2(median official ops per number, censored runs at the ops
    they spent) over 48, 64, 80 bits (origin_dots.py's slope; Q1's and Q4's slope), beside rho's on the same numbers;
  - G_rho = period_cand / period_rho over 48-80, period = 32 / log2(C(80) / C(48)), under the five pricings; worst-of
    = min over op-class v1, ruint, Montgomery, scaled gcd (official reported, no veto); "not defined" below 24 / 48
    successes at 48 or 80 for either arm; paired bootstrap, 10,000 resamples, random.Random(2026), 2.5-97.5%;
    "slower growth" / "faster growth" only when the whole interval is on one side of 1;
  - a pricing artifact flag: G_rho > 1 under op-class v1 but not under the scaled gcd price (rule 1);
  - G = period_cand / period_QS over 80-96, under the four pricings (and the scaled gcd price, for information);
    worst-of = min over op-class v1, ruint, Montgomery; not defined below 24 / 48 at 80 or 96 for either arm. The
    84-96 gene check needs 84-bit numbers, which design §8 does not draw: reported as not run, flagged for the user;
  - cost ratio C_cand / C_rho at 64 and 80 bits, per pricing, paired bootstrap; robust = max over the worst-of set;
  - the user's flag (Oct 29): a genome with a bin-compare rule whose cost grows faster than rho's (its op-count slope
    or its op-class C(80)/C(48) above rho's on the same numbers), even if it does well at 48 bits;
  - the class (rule 5): "rediscovered known lamp" for the exponent layout or the map layout with Floyd or Brent;
  - the Q fields: layout, rule, map degree d (Q6), rho-shaped (Q1: map + Floyd/Brent and slope in [0.20, 0.30]).
Theta map: per genome, the cost ratio against rho at 64 and 80 bits and the op-count slope 64-80.
A JSON line "RESULT {...}" closes the output with every number above.

  python3 arr_validate.py balanced|theta GENOME_FILE [...]
  python3 arr_validate.py selftest       the code paths on small numbers (20/24/28/32 bits, seeds 9939000 + bits),
                                         never on a scored map; prints counts, no verdicts"""
import os, sys
ARGV = sys.argv[1:]
sys.argv = sys.argv[:1]
os.chdir(os.path.dirname(os.path.abspath(__file__)))     # the price and gene files are read relative to evolve/
sys.path.insert(0, ".")
import json, math, random, statistics, subprocess
from concurrent.futures import ThreadPoolExecutor
import lamps, optypes, gcdscale
import partition as P
from fastlamps import BIN, semiprimes_pq
from lamps import rand_prime
from growth_harness import qs_genes, costs

CAP = 2 ** 34
WORKERS = 2
B_RESAMPLES, SEED = 10000, 2026
PRICINGS = ("opclass_v1", "ruint", "montgomery", "official", "opclass_v1_gcdscaled")
WORST_G_RHO = ("opclass_v1", "ruint", "montgomery", "opclass_v1_gcdscaled")
WORST_G = ("opclass_v1", "ruint", "montgomery")
RHO = [dict(P.PRE["rho"])]

def theta_numbers(bits, seed, n, lo=0.20, hi=0.30):
    """twilight2_search.numbers' draw, band [lo, hi)."""
    rng, out = random.Random(seed), []
    while len(out) < n:
        pb = round(rng.uniform(lo, hi) * bits)
        p, q = rand_prime(pb, rng), rand_prime(bits - pb + 1, rng)
        N = p * q
        if N.bit_length() != bits:
            continue
        p, q = min(p, q), max(p, q)
        if lo <= math.log2(p) / math.log2(N) < hi:
            out.append((N, p, q))
    return out

def run(genome, cap, nums, bits):
    """One lampcore --types call; per number: success, official ops, priced costs."""
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    assert len(out) == len(nums), ("lampcore output lines", len(out), len(nums))
    res = []
    for (N, p, q), l in zip(nums, out):
        f = l.split()
        i = f.index("T")
        ty = {t: n for t, n in zip(optypes.TYPE_ORDER, map(int, f[i + 1:])) if n}
        small = int(f[f.index("A") + 1]) if "A" in f[:i] else 0
        c = costs(ty)
        sc = gcdscale.cost({t: n for t, n in ty.items() if t != "gcd"}, bits) if ty else 0.0
        if sc is not None:
            g = ty.get("gcd", 0)
            assert 0 <= small <= g, ("gcd_small exceeds the gcds", small, g)
            sc += small * gcdscale.gcd_units(bits, "small") + (g - small) * gcdscale.gcd_units(bits, "uniform")
        c["opclass_v1_gcdscaled"] = sc
        res.append({"ok": f[1] != "miss" and int(f[1]) in (p, q), "ops": sum(ty.values()), "cost": c,
                    "gcd": ty.get("gcd", 0), "gcd_small": small})
    return res

def per_fact(rs, pr, idx=None):
    idx = range(len(rs)) if idx is None else idx
    s = sum(rs[i]["ok"] for i in idx)
    if s < len(rs) // 2 or any(rs[i]["cost"][pr] is None for i in idx):
        return None
    return sum(rs[i]["cost"][pr] for i in idx) / s

def period(R, a, b, pr, ix=None):
    ca, cb = per_fact(R[a], pr, ix and ix[a]), per_fact(R[b], pr, ix and ix[b])
    return (b - a) / math.log2(cb / ca) if ca and cb and cb != ca else None

def ls_slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def ops_slope(R, sizes):
    return ls_slope(list(sizes), [math.log2(max(1, statistics.median(r["ops"] for r in R[b]))) for b in sizes])

def paired(stat, sizes, n, rng):
    """Point estimate is stat(None); interval from B_RESAMPLES paired resamples (one index list per size, shared by
    every arm). Resamples where the statistic is not defined are dropped (growth_rho_ref.py's convention)."""
    bs = []
    for _ in range(B_RESAMPLES):
        ix = {b: [rng.randrange(n[b]) for _ in range(n[b])] for b in sizes}
        v = stat(ix)
        if v is not None:
            bs.append(v)
    bs.sort()
    ci = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if bs else (None, None)
    return {"value": stat(None), "ci": ci, "resamples_defined": len(bs)}

def side(v):
    lo, hi = v["ci"]
    if v["value"] is None or lo is None:
        return "not defined"
    return "slower growth" if lo > 1 else "faster growth" if hi < 1 else "not separable from 1"

def classify(genome):
    a = [s for s in genome if s["t"] == "arr"]
    if not a:
        raise ValueError("a genome without an arr stage")
    s = a[0]
    lay, rule = s["layout"]["kind"], s["detect"]["kind"]
    known = lay == "exponent" or (lay == "map" and rule in ("floyd", "brent"))
    return {"layout": lay, "rule": rule, "d": s["layout"].get("d", 2) if lay == "map" else None,
            "arr_stages": len(a), "class": "rediscovered known lamp" if known else "candidate",
            "bin_compare": any(x["detect"]["kind"] == "bins" for x in a)}

def load(paths):
    out = []
    for p in paths:
        g = json.load(open(p))
        name, gen = (g.get("name", p), g["genome"]) if isinstance(g, dict) else (p, g)
        lamps.validate_genome(gen)
        classify(gen)
        out.append((name, gen))
    return out

def arms_run(jobs):
    """jobs: {key: (genome, cap, nums, bits)} -> {key: results}, WORKERS lampcore processes at a time."""
    with ThreadPoolExecutor(WORKERS) as ex:
        fut = {k: ex.submit(run, *v) for k, v in jobs.items()}
        return {k: f.result() for k, f in fut.items()}

def fmt(v, nd=3):
    if v["value"] is None:
        return "not defined"
    lo, hi = v["ci"]
    return f"{v['value']:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]" if lo is not None else f"{v['value']:.{nd}f}"

def score_balanced(genomes, sizes=(48, 64, 80, 96), chord=(48, 80), gchord=(80, 96), ratio_at=(64, 80), per=48,
                   seed0=9930000, qs=True):
    nums = {b: semiprimes_pq(b, per, seed0 + b) for b in sizes}
    n = {b: len(nums[b]) for b in sizes}
    jobs = {("rho", b): (RHO, CAP, nums[b], b) for b in sizes}
    if qs:
        jobs.update({("qs", b): ([qs_genes(b)], P.QS_CAP, nums[b], b) for b in gchord})
    for i, (_, g) in enumerate(genomes):
        jobs.update({(i, b): (g, CAP, nums[b], b) for b in sizes})
    R = arms_run(jobs)
    arm = lambda k: {b: R[(k, b)] for b in sizes if (k, b) in R}
    rho = arm("rho")
    a, b = chord
    out = {"map": "balanced", "sizes": list(sizes), "per_size": per, "seeds": f"{seed0} + bits", "cap": CAP,
           "rho": {"successes": {s: sum(r["ok"] for r in rho[s]) for s in sizes},
                   "ops_slope": ops_slope(rho, (a, ratio_at[0], b)),
                   "period": {pr: period(rho, a, b, pr) for pr in PRICINGS}},
           "gene_check_84_96": "not run: design §8 draws no 84-bit validation numbers (flagged for the user)",
           "genomes": []}
    if qs:
        q = arm("qs")
        out["qs"] = {"successes": {s: sum(r["ok"] for r in q[s]) for s in gchord},
                     "period": {pr: period(q, *gchord, pr) for pr in PRICINGS}}
    for i, (name, g) in enumerate(genomes):
        rng = random.Random(SEED)
        C = arm(i)
        info = classify(g)
        slope = ops_slope(C, (a, ratio_at[0], b))
        e = {"name": name, "genome": g, **info,
             "successes": {s: sum(r["ok"] for r in C[s]) for s in sizes},
             "gcd_small": {s: sum(r["gcd_small"] for r in C[s]) for s in sizes},
             "gcd": {s: sum(r["gcd"] for r in C[s]) for s in sizes},
             "ops_slope": slope, "ops_slope_rho": out["rho"]["ops_slope"],
             "rho_shaped": info["layout"] == "map" and info["rule"] in ("floyd", "brent") and 0.20 <= slope <= 0.30}
        e["g_rho"] = {pr: paired(lambda ix, pr=pr: (lambda pc, pq: pc / pq if pc and pq else None)(
                          period(C, a, b, pr, ix), period(rho, a, b, pr, ix)), (a, b), n, rng) for pr in PRICINGS}
        e["g_rho_worst"] = paired(lambda ix: (lambda v: min(v) if None not in v else None)(
            [(lambda pc, pq: pc / pq if pc and pq else None)(period(C, a, b, pr, ix), period(rho, a, b, pr, ix))
             for pr in WORST_G_RHO]), (a, b), n, rng)
        e["g_rho_verdict"] = side(e["g_rho_worst"])
        go, gs = e["g_rho"]["opclass_v1"]["value"], e["g_rho"]["opclass_v1_gcdscaled"]["value"]
        e["pricing_artifact"] = bool(go and go > 1 and not (gs and gs > 1))
        if qs:
            q = arm("qs")
            e["g"] = {pr: paired(lambda ix, pr=pr: (lambda pc, pq: pc / pq if pc and pq else None)(
                          period(C, *gchord, pr, ix), period(q, *gchord, pr, ix)), gchord, n, rng) for pr in PRICINGS}
            e["g_worst"] = paired(lambda ix: (lambda v: min(v) if None not in v else None)(
                [(lambda pc, pq: pc / pq if pc and pq else None)(period(C, *gchord, pr, ix), period(q, *gchord, pr, ix))
                 for pr in WORST_G]), gchord, n, rng)
        e["ratio"] = {}
        for s in ratio_at:
            r1 = lambda ix, pr, s=s: (lambda x, y: x / y if x and y else None)(per_fact(C[s], pr, ix and ix[s]),
                                                                            per_fact(rho[s], pr, ix and ix[s]))
            e["ratio"][s] = {pr: paired(lambda ix, pr=pr: r1(ix, pr), (s,), n, rng) for pr in PRICINGS}
            e["ratio"][s]["robust"] = paired(lambda ix: (lambda v: max(v) if None not in v else None)(
                [r1(ix, pr) for pr in WORST_G_RHO]), (s,), n, rng)
        grow_c = period(C, a, b, "opclass_v1")
        grow_r = out["rho"]["period"]["opclass_v1"]
        faster = slope > out["rho"]["ops_slope"] or (grow_c is not None and grow_r is not None and grow_c < grow_r)
        e["flag_bin_compare_faster_than_rho"] = bool(info["bin_compare"] and faster)
        out["genomes"].append(e)
    return out

def score_theta(genomes, sizes=(64, 80), per=96, seed0=9935000):
    nums = {b: theta_numbers(b, seed0 + b, per) for b in sizes}
    n = {b: per for b in sizes}
    jobs = {("rho", b): (RHO, CAP, nums[b], b) for b in sizes}
    for i, (_, g) in enumerate(genomes):
        jobs.update({(i, b): (g, CAP, nums[b], b) for b in sizes})
    R = arms_run(jobs)
    rho = {b: R[("rho", b)] for b in sizes}
    out = {"map": "theta 0.20-0.30", "sizes": list(sizes), "per_size": per, "seeds": f"{seed0} + bits", "cap": CAP,
           "rho": {"successes": {s: sum(r["ok"] for r in rho[s]) for s in sizes}, "ops_slope": ops_slope(rho, sizes)},
           "genomes": []}
    for i, (name, g) in enumerate(genomes):
        rng = random.Random(SEED)
        C = {b: R[(i, b)] for b in sizes}
        e = {"name": name, "genome": g, **classify(g), "successes": {s: sum(r["ok"] for r in C[s]) for s in sizes},
             "ops_slope": ops_slope(C, sizes), "ratio": {}}
        for s in sizes:
            r1 = lambda ix, pr, s=s: (lambda x, y: x / y if x and y else None)(per_fact(C[s], pr, ix and ix[s]),
                                                                            per_fact(rho[s], pr, ix and ix[s]))
            e["ratio"][s] = {pr: paired(lambda ix, pr=pr: r1(ix, pr), (s,), n, rng) for pr in PRICINGS}
            e["ratio"][s]["robust"] = paired(lambda ix: (lambda v: max(v) if None not in v else None)(
                [r1(ix, pr) for pr in WORST_G_RHO]), (s,), n, rng)
        out["genomes"].append(e)
    return out

def report(out):
    print(f"map {out['map']}: sizes {out['sizes']}, {out['per_size']} per size, seeds {out['seeds']}, cap {out['cap']}")
    print(f"rho alone: successes {out['rho']['successes']}; op-count slope {out['rho']['ops_slope']:.3f} per bit")
    if "period" in out["rho"]:
        print("rho doubling period (same numbers): " + ", ".join(
            f"{pr} {v:.3f}" if v else f"{pr} n/a" for pr, v in out["rho"]["period"].items()))
    if "qs" in out:
        print(f"QS (reference genes): successes {out['qs']['successes']}; doubling period " + ", ".join(
            f"{pr} {v:.3f}" if v else f"{pr} n/a" for pr, v in out["qs"]["period"].items()))
        print(f"G gene check 84-96: {out['gene_check_84_96']}")
    for e in out["genomes"]:
        print(f"\n== {e['name']}: {e['layout']} + {e['rule']}" + (f", d = {e['d']}" if e["d"] else "")
              + f"; {e['class']}" + ("; rho-shaped (Q1)" if e.get("rho_shaped") else ""))
        print(f"   successes {e['successes']}")
        print(f"   op-count slope {e['ops_slope']:.3f} per bit (rho {out['rho']['ops_slope']:.3f})")
        if "g_rho" in e:
            print(f"   G_rho 48-80: " + "; ".join(f"{pr} {fmt(v)}" for pr, v in e["g_rho"].items()))
            print(f"   G_rho worst-of (op-class, ruint, Montgomery, scaled gcd): {fmt(e['g_rho_worst'])}: {e['g_rho_verdict']}"
                  + ("; PRICING ARTIFACT (G_rho > 1 flat, not scaled)" if e["pricing_artifact"] else ""))
            print(f"   gcds whose other argument < 2^64: " + ", ".join(f"{s}: {e['gcd_small'][s]}/{e['gcd'][s]}" for s in e["gcd"]))
        if "g" in e:
            print(f"   G 80-96: " + "; ".join(f"{pr} {fmt(v)}" for pr, v in e["g"].items())
                  + f"; worst-of {fmt(e['g_worst'])}: {side(e['g_worst'])}")
        for s, rr in e["ratio"].items():
            print(f"   cost / rho at {s}: " + "; ".join(f"{pr} {fmt(v, 4)}" for pr, v in rr.items()))
        if e.get("flag_bin_compare_faster_than_rho"):
            print("   FLAG: bin-compare genome whose cost grows faster than rho's (the user's flag)")
    print("\nRESULT " + json.dumps(out, default=str))

if __name__ == "__main__":
    if not ARGV or ARGV[0] not in ("balanced", "theta", "selftest") or (ARGV[0] != "selftest" and len(ARGV) < 2):
        sys.exit(__doc__)
    if ARGV[0] == "selftest":
        G = [("rho-shaped", [{"t": "arr", "layout": {"kind": "map", "c": 1, "d": 2, "x0": 2}, "detect": {"kind": "brent", "b": 64}}]),
             ("bins", [{"t": "arr", "layout": {"kind": "bins", "m": 3, "B": 1}, "detect": {"kind": "bins"}, "ob": 400000}]),
             ("stride", [{"t": "arr", "layout": {"kind": "stride", "a": 2, "s": 1}, "detect": {"kind": "batch", "b": 64}}])]
        for g in G:
            lamps.validate_genome(g[1])
        report(score_balanced(G, sizes=(20, 24, 28, 32), chord=(20, 28), gchord=(28, 32), ratio_at=(24, 28), per=16,
                              seed0=9939000, qs=False))
        report(score_theta(G[:1], sizes=(28, 32), per=16, seed0=9939500))
        sys.exit(0)
    G = load(ARGV[1:])
    report(score_balanced(G) if ARGV[0] == "balanced" else score_theta(G))
