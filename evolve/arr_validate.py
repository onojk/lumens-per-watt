"""Scoring harness for arrangement-v1 (design docs/planning/arrangement_lamps.md §8 step 4; predictions
predictions/arrangement-v1.md; fitness G_rho, reviews/growth_fitness_rho.md, frozen 77ff2ee, with G,
reviews/growth_fitness.md, frozen c86ef35). A judge file: pinned in the predictions, run only through tools/sealed_run.sh.

Input: the search's output directory (tools/search_sandbox.sh -> search_out/) and the genome file names to score.
  The allow-list (Grok's b2, Oct 30): only names matching genome_<layout>_<rule>.json are read. The search record
  arr_search_<map>.json is skipped (logged, not read); every other entry of the directory is REFUSED and logged; the
  run continues on the allowed files only.
  The reader (DeepSeek's b3, Oct 30) is total: each file either parses into a genome or is refused with a reason.
  It opens the name inside the directory (no "/" in a name, so no traversal; the directory path itself must not
  pass through a symlink) with O_NOFOLLOW | O_NONBLOCK; refuses a symlink, a FIFO, a device, a directory, anything
  that is not a regular file, more than 64 KiB, bytes that are not UTF-8, JSON that does not parse (NaN / Infinity,
  duplicate keys and nesting too deep included), and any shape but {"name": <short name>, "genome": [<one arr
  stage>]} or [<one arr stage>]: exactly one stage, t = "arr" (design §2; a non-arr stage, e.g. sq, is refused:
  NOTES 7fd6290), keys t / layout / detect / ob only, then lamps.validate_genome.
The early-exit audit (Grok's b1, Oct 30): every record carries its termination (arr_price.run: factor, budget, ended,
error, aborted). Any error or aborted number makes that genome's score INVALID (flagged; no verdict); an error or
abort in rho's or QS's arm makes the whole run INVALID.

Maps (design §8 with its 84-bit addendum; numbers never seen by the search):
  balanced  48 per size at 48, 64, 80, 84 and 96 bits, semiprimes_pq(bits, 48, 9930000 + bits); 84 runs the
            candidate and QS only (G's 84-96 gene check)
  theta     96 per size at 64 and 80 bits, theta = log2 p / log2 N uniform in [0.20, 0.30), seeds 9935000 + bits
            (twilight2_search.numbers' draw with the band changed; Q5's map: cost against rho only, no growth)
Arms, each on the same numbers (the paired bootstrap): the candidate; rho alone (partition.PRE["rho"], G_rho's
reference genes); on the balanced map at 80, 84 and 96 bits, the reference card's QS (growth_harness.qs_genes: the
sealed 2'b genes at 84 and 96, interpolated at 80, as G's reference). Untimed counts, lampcore --types; 2 lampcore processes
at a time (the user's instruction: the laptop runs hot). Caps: CAP = 2^34 for the candidate and rho (the growth
harness's cap, as G_rho's reference); partition.QS_CAP for QS.

Pricing per run (growth_harness.costs): official, ruint, Montgomery, op-class v1, and op-class v1 with the size-scaled
gcd price (gcdscale.py; per gcd, the small-k curve for the arr gcds whose other argument was < 2^32 (G_rho v2), lampcore's " A n"
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
    worst-of = min over op-class v1, ruint, Montgomery; not defined below 24 / 48 at 80 or 96 for either arm; the
    84-96 gene check beside it, flagged when the two windows' op-class period intervals do not overlap for the
    candidate or for the reference QS (G rule 1);
  - cost ratio C_cand / C_rho at 64 and 80 bits, per pricing, paired bootstrap; robust = max over the worst-of set;
  - the user's flag (Oct 29): a genome with a bin-compare rule whose cost grows faster than rho's (its op-count slope
    or its op-class C(80)/C(48) above rho's on the same numbers), even if it does well at 48 bits;
  - the class (rule 5): "rediscovered known lamp" for the exponent layout or the map layout with Floyd or Brent;
  - the Q fields: layout, rule, map degree d (Q6), rho-shaped (Q1: map + Floyd/Brent and slope in [0.20, 0.30]).
Theta map: per genome, the cost ratio against rho at 64 and 80 bits and the op-count slope 64-80.
A JSON line "RESULT {...}" closes the output with every number above.

  python3 arr_validate.py balanced|theta SEARCH_OUT_DIR GENOME_NAME [...]
  python3 arr_validate.py selftest       the code paths on small numbers (20-44 bits, seeds 9939000 / 9939500 /
                                         9939700 + bits, never a scored map), QS and the gene check included;
                                         and the reader, allow-list and early-exit cases (exit 3 on a failure)"""
import os, sys
ARGV = sys.argv[1:]
sys.argv = sys.argv[:1]
os.chdir(os.path.dirname(os.path.abspath(__file__)))     # the price and gene files are read relative to evolve/
sys.path.insert(0, ".")
import json, math, random, re, stat, statistics
from concurrent.futures import ThreadPoolExecutor
import lamps
import partition as P
from fastlamps import semiprimes_pq
from lamps import rand_prime
from growth_harness import qs_genes
from arr_price import CAP, RHO, PRICINGS, WORST_G_RHO, WORST_G, BAD_TERMS, TERMS, run, per_fact, period

WORKERS = 2
B_RESAMPLES, SEED = 10000, 2026
assert RHO == [dict(P.PRE["rho"])], "arr_price.RHO is not partition.PRE['rho']"
GENOME_NAME = re.compile(r"genome_[a-z]+_[a-z]+\.json")
RECORD_NAME = re.compile(r"arr_search_[a-z]+\.json")
MAX_BYTES = 1 << 16
STAGE_KEYS = {"t", "layout", "detect", "ob"}

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

class Refused(Exception):
    pass

def _no_constants(c):
    raise Refused(f"JSON constant {c} is not allowed")

def _no_dupes(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Refused("duplicate JSON keys")
    return dict(pairs)

def _parse(name, data):
    if len(data) > MAX_BYTES:
        raise Refused(f"larger than {MAX_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("not UTF-8")
    try:
        obj = json.loads(text, parse_constant=_no_constants, object_pairs_hook=_no_dupes)
    except RecursionError:
        raise Refused("JSON nested too deep")
    except ValueError as e:
        raise Refused(f"not JSON ({str(e)[:60]})")
    if isinstance(obj, dict):
        if set(obj) != {"name", "genome"}:
            raise Refused("an object must have exactly the keys name and genome")
        label, gen = obj["name"], obj["genome"]
        if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", label):
            raise Refused("name must be 1-64 characters of [A-Za-z0-9_.-]")
    else:
        label, gen = name, obj
    if not isinstance(gen, list) or len(gen) != 1 or not isinstance(gen[0], dict):
        raise Refused("a genome is a list of exactly one stage (design §2)")
    st = gen[0]
    if st.get("t") != "arr" or not set(st) <= STAGE_KEYS:
        raise Refused(f"the stage must be an arr stage with keys from {sorted(STAGE_KEYS)}")
    for part in ("layout", "detect"):
        if not isinstance(st.get(part), dict) or any(not isinstance(k, str) for k in st[part]):
            raise Refused(f"{part} must be an object")
        if any(not ((isinstance(v, int) and not isinstance(v, bool)) or (k == "kind" and isinstance(v, str)))
               for k, v in st[part].items()):
            raise Refused(f"{part}: every gene must be an integer (kind a string)")
    try:
        lamps.validate_genome(gen)
    except Exception as e:
        raise Refused(f"invalid genome: {str(e)[:80]}")
    return label, gen

def read_genome(dir_path, name):
    """One genome file, read totally: (label, genome) or Refused (see the module doc)."""
    try:
        if not isinstance(name, str) or not GENOME_NAME.fullmatch(name):
            raise Refused("name not on the allow-list (genome_<layout>_<rule>.json)")
        absd = os.path.abspath(dir_path)
        if os.path.realpath(absd) != absd:
            raise Refused("the directory path passes through a symlink")
        dfd = os.open(absd, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
            except OSError as e:
                raise Refused(f"cannot open without following links ({e.strerror})")
            try:
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode):
                    raise Refused("not a regular file")
                if st.st_size > MAX_BYTES:
                    raise Refused(f"larger than {MAX_BYTES} bytes")
                data = b""
                while len(data) <= MAX_BYTES:
                    chunk = os.read(fd, MAX_BYTES + 1 - len(data))
                    if not chunk:
                        break
                    data += chunk
            finally:
                os.close(fd)
        finally:
            os.close(dfd)
        return _parse(name, data)
    except Refused:
        raise
    except Exception as e:                        # totality: anything unexpected is a refusal, never a crash
        raise Refused(f"unexpected {type(e).__name__}")

def load(dir_path, names, log=print):
    """The allow-listed genomes of a search's output directory; every other entry refused and logged."""
    try:
        entries = sorted(os.listdir(dir_path))
    except OSError as e:
        log(f"REFUSED: cannot list {dir_path} ({e.strerror})")
        entries = []
    for e in entries:
        if RECORD_NAME.fullmatch(e):
            log(f"skipped: {e} (the search record, not a genome)")
        elif not GENOME_NAME.fullmatch(e):
            log(f"REFUSED: {e} (not on the allow-list; not read)")
        elif e not in names:
            log(f"skipped: {e} (allowed, not requested)")
    out = []
    for nm in names:
        try:
            label, gen = read_genome(dir_path, nm)
            classify(gen)
            out.append((label, gen))
            log(f"read: {nm} -> {label}")
        except Refused as r:
            log(f"REFUSED: {nm}: {r}")
    return out

def arms_run(jobs, abort=()):
    """jobs: {key: (genome, cap, nums, bits)} -> {key: results}, WORKERS lampcore processes at a time. Keys whose
    first element is in `abort` run with a timeout too short to finish (the selftest's forced abort)."""
    with ThreadPoolExecutor(WORKERS) as ex:
        fut = {k: ex.submit(run, *v, timeout=1e-4 if k[0] in abort else None) for k, v in jobs.items()}
        return {k: f.result() for k, f in fut.items()}

def terms(R):
    t = {x: 0 for x in TERMS}
    for rs in R.values():
        for r in rs:
            t[r["term"]] += 1
    return t

def fmt(v, nd=3):
    if v["value"] is None:
        return "not defined"
    lo, hi = v["ci"]
    return f"{v['value']:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]" if lo is not None else f"{v['value']:.{nd}f}"

def score_balanced(genomes, sizes=(48, 64, 80, 84, 96), chord=(48, 80), gchord=(80, 96), gene=(84, 96), ratio_at=(64, 80),
                   per=48, seed0=9930000, qs=True, abort=()):
    nums = {b: semiprimes_pq(b, per, seed0 + b) for b in sizes}
    n = {b: len(nums[b]) for b in sizes}
    rho_sizes = tuple(b for b in sizes if not (qs and b == gene[0]))    # 84 is for G's gene check only (QS, candidate)
    jobs = {("rho", b): (RHO, CAP, nums[b], b) for b in rho_sizes}
    if qs:
        jobs.update({("qs", b): ([qs_genes(b)], P.QS_CAP, nums[b], b) for b in sorted(set(gchord) | set(gene))})
    for i, (_, g) in enumerate(genomes):
        jobs.update({(i, b): (g, CAP, nums[b], b) for b in sizes})
    R = arms_run(jobs, abort)
    arm = lambda k: {b: R[(k, b)] for b in sizes if (k, b) in R}
    rho = arm("rho")
    a, b = chord
    out = {"map": "balanced", "sizes": list(sizes), "per_size": per, "seeds": f"{seed0} + bits", "cap": CAP,
           "rho": {"successes": {s: sum(r["ok"] for r in rho[s]) for s in rho_sizes},
                   "ops_slope": ops_slope(rho, (a, ratio_at[0], b)),
                   "period": {pr: period(rho, a, b, pr) for pr in PRICINGS}},
           "chords": {"g_rho": chord, "g": gchord, "gene_check": gene}, "genomes": []}
    out["reference_terms"] = {"rho": terms(rho), **({"qs": terms(arm("qs"))} if qs else {})}
    out["run_invalid"] = any(t[x] for t in out["reference_terms"].values() for x in BAD_TERMS)
    if qs:
        q = arm("qs")
        out["qs"] = {"genes": {s: qs_genes(s) for s in sorted(set(gchord) | set(gene))},
                     "successes": {s: sum(r["ok"] for r in q[s]) for s in sorted(set(gchord) | set(gene))},
                     "period": {pr: period(q, *gchord, pr) for pr in PRICINGS},
                     "period_gene_check": {pr: period(q, *gene, pr) for pr in PRICINGS}}
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
             "rho_shaped": info["layout"] == "map" and info["rule"] in ("floyd", "brent") and 0.20 <= slope <= 0.30,
             "terms": terms(C)}
        e["invalid"] = out["run_invalid"] or any(e["terms"][x] for x in BAD_TERMS)
        e["g_rho"] = {pr: paired(lambda ix, pr=pr: (lambda pc, pq: pc / pq if pc and pq else None)(
                          period(C, a, b, pr, ix), period(rho, a, b, pr, ix)), (a, b), n, rng) for pr in PRICINGS}
        e["g_rho_worst"] = paired(lambda ix: (lambda v: min(v) if None not in v else None)(
            [(lambda pc, pq: pc / pq if pc and pq else None)(period(C, a, b, pr, ix), period(rho, a, b, pr, ix))
             for pr in WORST_G_RHO]), (a, b), n, rng)
        e["g_rho_verdict"] = "INVALID (early-exit audit)" if e["invalid"] else side(e["g_rho_worst"])
        go, gs = e["g_rho"]["opclass_v1"]["value"], e["g_rho"]["opclass_v1_gcdscaled"]["value"]
        e["pricing_artifact"] = bool(go and go > 1 and not (gs and gs > 1))
        if qs:
            q = arm("qs")
            e["g"] = {pr: paired(lambda ix, pr=pr: (lambda pc, pq: pc / pq if pc and pq else None)(
                          period(C, *gchord, pr, ix), period(q, *gchord, pr, ix)), gchord, n, rng) for pr in PRICINGS}
            e["g_worst"] = paired(lambda ix: (lambda v: min(v) if None not in v else None)(
                [(lambda pc, pq: pc / pq if pc and pq else None)(period(C, *gchord, pr, ix), period(q, *gchord, pr, ix))
                 for pr in WORST_G]), gchord, n, rng)
            # G's gene check (rule 1): the 84-96 chord beside 80-96; flag when the two windows' period intervals do not
            # overlap, for the candidate or for the reference QS (op-class v1, the primary pricing)
            e["g_gene_check"] = {pr: paired(lambda ix, pr=pr: (lambda pc, pq: pc / pq if pc and pq else None)(
                period(C, *gene, pr, ix), period(q, *gene, pr, ix)), gene, n, rng) for pr in PRICINGS}
            win = {}
            for who, X in (("candidate", C), ("reference QS", q)):
                for w in (gchord, gene):
                    v = paired(lambda ix, X=X, w=w: period(X, *w, "opclass_v1", ix), w, n, rng)
                    win[(who, w)] = v["ci"] if v["value"] is not None else (None, None)   # undefined point: no interval
            e["gene_check_flag"] = [who for who in ("candidate", "reference QS")
                                    if None in win[(who, gchord)] + win[(who, gene)]
                                    or win[(who, gchord)][1] < win[(who, gene)][0]
                                    or win[(who, gene)][1] < win[(who, gchord)][0]]
            e["gene_check_windows"] = {f"{who} {w[0]}-{w[1]}": ci for (who, w), ci in win.items()}
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

def score_theta(genomes, sizes=(64, 80), per=96, seed0=9935000, abort=()):
    nums = {b: theta_numbers(b, seed0 + b, per) for b in sizes}
    n = {b: per for b in sizes}
    jobs = {("rho", b): (RHO, CAP, nums[b], b) for b in sizes}
    for i, (_, g) in enumerate(genomes):
        jobs.update({(i, b): (g, CAP, nums[b], b) for b in sizes})
    R = arms_run(jobs, abort)
    rho = {b: R[("rho", b)] for b in sizes}
    out = {"map": "theta 0.20-0.30", "sizes": list(sizes), "per_size": per, "seeds": f"{seed0} + bits", "cap": CAP,
           "rho": {"successes": {s: sum(r["ok"] for r in rho[s]) for s in sizes}, "ops_slope": ops_slope(rho, sizes)},
           "genomes": []}
    out["reference_terms"] = {"rho": terms(rho)}
    out["run_invalid"] = any(out["reference_terms"]["rho"][x] for x in BAD_TERMS)
    for i, (name, g) in enumerate(genomes):
        rng = random.Random(SEED)
        C = {b: R[(i, b)] for b in sizes}
        e = {"name": name, "genome": g, **classify(g), "successes": {s: sum(r["ok"] for r in C[s]) for s in sizes},
             "ops_slope": ops_slope(C, sizes), "ratio": {}, "terms": terms(C)}
        e["invalid"] = out["run_invalid"] or any(e["terms"][x] for x in BAD_TERMS)
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
    print(f"reference terminations: {out['reference_terms']}"
          + ("; RUN INVALID: an error or abort in a reference arm (early-exit audit)" if out["run_invalid"] else ""))
    if "period" in out["rho"]:
        print("rho doubling period (same numbers): " + ", ".join(
            f"{pr} {v:.3f}" if v else f"{pr} n/a" for pr, v in out["rho"]["period"].items()))
    if "qs" in out:
        print(f"QS (reference genes): successes {out['qs']['successes']}; doubling period " + ", ".join(
            f"{pr} {v:.3f}" if v else f"{pr} n/a" for pr, v in out["qs"]["period"].items()))
        print(f"QS gene-check period {out['chords']['gene_check'][0]}-{out['chords']['gene_check'][1]}: " + ", ".join(
            f"{pr} {v:.3f}" if v else f"{pr} n/a" for pr, v in out["qs"]["period_gene_check"].items()))
    for e in out["genomes"]:
        print(f"\n== {e['name']}: {e['layout']} + {e['rule']}" + (f", d = {e['d']}" if e["d"] else "")
              + f"; {e['class']}" + ("; rho-shaped (Q1)" if e.get("rho_shaped") else ""))
        print(f"   successes {e['successes']}; terminations {e['terms']}")
        if e["invalid"]:
            print("   INVALID (early-exit audit): an error or aborted number in this genome's runs"
                  + (" or a reference arm's" if out["run_invalid"] else "") + "; no verdict from this score")
        print(f"   op-count slope {e['ops_slope']:.3f} per bit (rho {out['rho']['ops_slope']:.3f})")
        if "g_rho" in e:
            ca, cb = out["chords"]["g_rho"]
            print(f"   G_rho {ca}-{cb}: " + "; ".join(f"{pr} {fmt(v)}" for pr, v in e["g_rho"].items()))
            print(f"   G_rho worst-of (op-class, ruint, Montgomery, scaled gcd): {fmt(e['g_rho_worst'])}: {e['g_rho_verdict']}"
                  + ("; PRICING ARTIFACT (G_rho > 1 flat, not scaled)" if e["pricing_artifact"] else ""))
            print(f"   gcds whose other argument < 2^32: " + ", ".join(f"{s}: {e['gcd_small'][s]}/{e['gcd'][s]}" for s in e["gcd"]))
        if "g" in e:
            ga, gb = out["chords"]["g"]
            print(f"   G {ga}-{gb}: " + "; ".join(f"{pr} {fmt(v)}" for pr, v in e["g"].items())
                  + f"; worst-of {fmt(e['g_worst'])}: {side(e['g_worst'])}")
            ka, kb = out["chords"]["gene_check"]
            print(f"   G {ka}-{kb} (gene check): " + "; ".join(f"{pr} {fmt(v)}" for pr, v in e["g_gene_check"].items()))
            if e["gene_check_flag"]:
                print(f"   FLAG (G rule 1): the {ga}-{gb} and {ka}-{kb} period intervals do not overlap (or are not defined) for "
                      f"{', '.join(e['gene_check_flag'])}; the verdict rests on neither window until the user rules")
        for s, rr in e["ratio"].items():
            print(f"   cost / rho at {s}: " + "; ".join(f"{pr} {fmt(v, 4)}" for pr, v in rr.items()))
        if e.get("flag_bin_compare_faster_than_rho"):
            print("   FLAG: bin-compare genome whose cost grows faster than rho's (the user's flag)")
    print("\nRESULT " + json.dumps(out, default=str))

def selftest_guards():
    """The reader, the allow-list and the early-exit audit (DeepSeek b3, Grok b1 and b2): every case must come out as
    expected; returns 3 on any failure."""
    import tempfile
    bad = []
    good = [{"t": "arr", "layout": {"kind": "map", "c": 1, "d": 2, "x0": 2}, "detect": {"kind": "brent", "b": 64}}]
    with tempfile.TemporaryDirectory() as d:
        w = lambda n, data: open(os.path.join(d, n), "wb").write(data if isinstance(data, bytes) else data.encode())
        w("genome_map_brent.json", json.dumps({"name": "good", "genome": good}))
        w("notes.txt", "a stray file")                                        # the allow-list: refused, logged
        w("arr_search_balanced.json", "{}")                                   # the search record: skipped
        os.symlink(os.path.join(d, "genome_map_brent.json"), os.path.join(d, "genome_map_floyd.json"))
        os.mkfifo(os.path.join(d, "genome_map_dot.json"))
        os.mkdir(os.path.join(d, "genome_map_batch.json"))
        w("genome_bins_dot.json", " " * (MAX_BYTES + 1) + json.dumps(good))
        w("genome_bins_batch.json", b"\xff\xfe[1]")
        w("genome_bins_bins.json", '[{"t": "arr", "layout": {"kind": "map", "c": NaN, "d": 2, "x0": 2}, "detect": {"kind": "brent", "b": 64}}]')
        w("genome_fold_dot.json", '[{"t": "arr", "t": "arr", "layout": {"kind": "map"}, "detect": {"kind": "brent", "b": 64}}]')
        w("genome_fold_batch.json", "[" * 30000 + "]" * 30000)                  # deep nesting, under the size cap
        w("genome_stride_dot.json", json.dumps([{"t": "sq", "k": 0.1, "mode": "fermat", "ksq": False}]))
        w("genome_stride_batch.json", json.dumps(good + [{"t": "rho", "c": 1, "b": 64}]))
        w("genome_stride_floyd.json", json.dumps([{"t": "arr", "layout": {"kind": "stride", "a": True, "s": 1}, "detect": {"kind": "dot"}}]))
        w("genome_stride_brent.json", json.dumps([{"t": "arr", "layout": {"kind": "stride", "a": 2, "s": 0}, "detect": {"kind": "dot"}}]))
        w("genome_exponent_dot.json", json.dumps({"name": "x", "genome": good, "extra": 1}))
        w("genome_exponent_batch.json", json.dumps({"name": "../../etc", "genome": good}))
        asked = ["genome_map_brent.json", "genome_map_floyd.json", "genome_map_dot.json", "genome_map_batch.json",
                 "genome_bins_dot.json", "genome_bins_batch.json", "genome_bins_bins.json", "genome_fold_dot.json",
                 "genome_fold_batch.json", "genome_stride_dot.json", "genome_stride_batch.json", "genome_stride_floyd.json",
                 "genome_stride_brent.json", "genome_exponent_dot.json", "genome_exponent_batch.json",
                 "../genome_map_brent.json", "genome_map_brent.json/x", "genome_none_none.json", "notes.txt"]
        logs = []
        got = load(d, asked, log=logs.append)
        n_first = len(logs)
        os.symlink(d, d + "-link")
        got_link = load(d + "-link", ["genome_map_brent.json"], log=logs.append)
        os.unlink(d + "-link")
    for l in logs:
        print("   reader:", l)
    refused = [l for l in logs[:n_first] if l.startswith("REFUSED: genome_") or l.startswith("REFUSED: ../")
               or l.startswith("REFUSED: notes.txt:")]
    if [x[0] for x in got] != ["good"]:
        bad.append(f"the reader loaded {[x[0] for x in got]}, expected only 'good'")
    if len(refused) != len(asked) - 1:
        bad.append(f"{len(refused)} requested files refused, expected {len(asked) - 1}")
    if not any(l == "REFUSED: notes.txt (not on the allow-list; not read)" for l in logs):
        bad.append("the stray file was not refused and logged")
    if got_link:
        bad.append("a directory path through a symlink was read")
    # the early-exit audit: a forced abort of a genome's runs, and of rho's
    g2 = [("forced-abort", good), ("clean", good)]
    o = score_balanced(g2, sizes=(20, 24, 28), chord=(20, 28), gchord=(24, 28), ratio_at=(24, 28), per=8,
                       seed0=9939000, qs=False, abort=(0,))
    e0, e1 = o["genomes"]
    print(f"   abort case: forced-abort terms {e0['terms']}, invalid {e0['invalid']}, verdict {e0['g_rho_verdict']}; "
          f"clean terms {e1['terms']}, invalid {e1['invalid']}")
    if not (e0["invalid"] and e0["g_rho_verdict"].startswith("INVALID") and e0["terms"]["aborted"] == 24
            and not e1["invalid"] and not o["run_invalid"]):
        bad.append("the forced genome abort was not caught, or caught the clean genome")
    o = score_balanced(g2[1:], sizes=(20, 24, 28), chord=(20, 28), gchord=(24, 28), ratio_at=(24, 28), per=8,
                       seed0=9939000, qs=False, abort=("rho",))
    print(f"   abort case (rho's arm): run invalid {o['run_invalid']}, genome invalid {o['genomes'][0]['invalid']}")
    if not (o["run_invalid"] and o["genomes"][0]["invalid"]):
        bad.append("a forced abort of rho's arm did not invalidate the run")
    # an error: a lampcore that exits non-zero (a genome lampcore refuses, run past the reader)
    rs = run([{"t": "arr", "layout": {"kind": "stride", "a": 2, "s": 0}, "detect": {"kind": "dot"}}], 1000,
             semiprimes_pq(20, 2, 1), 20)
    print(f"   error case: terms {[r['term'] for r in rs]}")
    if [r["term"] for r in rs] != ["error", "error"]:
        bad.append("a lampcore error was not recorded as error")
    for x in bad:
        print("SELFTEST FAILED:", x)
    print("selftest guards: " + ("ok" if not bad else f"{len(bad)} failed"))
    return 3 if bad else 0

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
        # the G and gene-check paths, with QS on small numbers (qs_genes holds the 54-bit genes below 54)
        report(score_balanced(G[:1], sizes=(24, 32, 36, 40, 44), chord=(24, 36), gchord=(36, 44), gene=(40, 44),
                              ratio_at=(32, 36), per=16, seed0=9939700, qs=True))
        sys.exit(selftest_guards())
    if len(ARGV) < 3:
        sys.exit(__doc__)
    G = load(ARGV[1], ARGV[2:])
    if not G:
        print("no genome to score: every requested file was refused")
        sys.exit(3)
    report(score_balanced(G) if ARGV[0] == "balanced" else score_theta(G))
