"""The arrangement-v1 search on the balanced training map (design docs/planning/arrangement_lamps.md §8 step 3; the
proposer: not a judge file, run only inside tools/search_sandbox.sh, through tools/sealed_run.sh). Gene search only;
no code is mutated. Its only output is what it writes to $LPW_SEARCH_OUT (genome files and the search record).

Training map: 48 balanced semiprimes per size at 48, 56, 64, 72 and 80 bits, semiprimes_pq(bits, 48, 9920000 + bits)
(design §8). No held-out number or seed is drawn, read or mounted here (tools/search_sandbox.sh mounts an
allow-list of files, checked for the held-out seeds).

Fitness: G_rho on the training numbers (reviews/growth_fitness_rho.md, v2): the candidate's doubling period over
48-80 / rho's (partition.PRE["rho"], alone, on the same numbers), worst of op-class v1, ruint, Montgomery and the
size-scaled gcd price (point values; the pricing and the period are arr_price.run / .period, the judge's own).
"Not defined" (fewer than 24 / 48 successes at a size) ranks below every defined value.
The cost guard (the user's ruling, Oct 30, after the selftest showed G_rho alone selecting padded genomes, costly at
the small end and so flat): a genome's fitness is defined only if its robust cost ratio against rho (the worst of the
same four pricings, C_candidate / C_rho) is at most 1.25 at every training size, 48 to 80; above it, the genome is
dropped at that size, as "not defined".

The search's budget (its own, not the judge's): per number, 16 x rho's largest op count on that size's training
numbers. A genome above it is censored there (its spent ops still count). Sizes are run in the order 48, 64, 80, 56,
72, in chunks of 8 numbers; a genome is dropped as "not defined" as soon as 25 of a size's 48 numbers have failed, or
at the first size where it fails the cost guard (64 is a screen: a genome dropped there is not run at 80).

Gene grid (design §2's genes; bounded as there; ob is not searched: the stage runs alone):
  stride   a {0, 1, 2, 3, 7}, s {1, 2, 3, 6, 30}
  fold     w {2, 4, 16, 64, 256, 1024, 4096}, a {1, 2, 3}, s {1, 2, 3}
  map      c {1, 2, 3, 5, 7, 11}, d {2, 4, 6, 8}, x0 {2, 3, 5, 7}
  bins     m {1, 2, 3, 7}, B {1, 16, 256, 4096, 65536}
  exponent a {2, 3, 5, 7}, K {2^8, 2^10, ..., 2^20}
  dot t {1, 0}; batch b {1, 8, 64, 512, 4096}, t {1, 0} (1 first: a sweep cannot leave an all-undefined start, and
           the exponent layout needs t = 1); floyd, brent b {1, 8, 64, 128, 512, 4096}; bin compare none
Search: for each of the 15 valid layout x rule pairs, a coordinate search from the first grid value of every gene:
sweep the genes in order, evaluate every grid value of the gene (2 lampcore processes at a time), keep the best
(ties keep the incumbent), until a sweep changes nothing (at most 4 sweeps). The best genome overall is the pair best
with the highest fitness. Every pair's best is then run on all five sizes, and its per-number records are kept for
the report (evolve/arr_report.py).
Theta mode (Q5, design §8: the theta 0.20-0.30 sub-map; its genome answers Q5 and nothing else): training 48 per size
at 64 and 80 bits, theta = log2 p / log2 N uniform in [0.20, 0.30), seeds 9925000 + bits (twilight2_search.numbers'
draw with the band changed, as the harness's theta map). The design gives no separate ranking for it, so the
balanced map's rule is used on the sizes it has: worst-of G_rho over the 64-80 chord against rho on the same numbers,
under the same cost guard (robust cost ratio <= 1.25 at 64 and 80), the same budget (16 x rho's max per size), grid,
start points and early drop.
If no pair has a defined fitness, the record's "best" is null (no genome selected).
  python3 arr_search.py balanced          -> $LPW_SEARCH_OUT/arr_search_balanced.json, genome_<layout>_<rule>.json
  python3 arr_search.py theta             -> $LPW_SEARCH_OUT/arr_search_theta.json, genome_<layout>_<rule>.json
  python3 arr_search.py selftest          the same on 20-32 bits, 16 per size, seeds 9929000 + bits (no training map)"""
import os, sys
ARGV = sys.argv[1:]
sys.argv = sys.argv[:1]
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
import json, math, random, time
from concurrent.futures import ThreadPoolExecutor
import lamps
import arr_price as V
from fastlamps import semiprimes_pq
from lamps import rand_prime

def theta_numbers(bits, seed, n, lo=0.20, hi=0.30):
    """twilight2_search.numbers' draw, band [lo, hi) (the harness's theta draw; training seeds only here)."""
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

WORKERS = 2
CAP_X = 16
GUARD = 1.25
CHUNK = 8
LAYOUT_GRID = {
    "stride": {"a": [0, 1, 2, 3, 7], "s": [1, 2, 3, 6, 30]},
    "fold": {"w": [2, 4, 16, 64, 256, 1024, 4096], "a": [1, 2, 3], "s": [1, 2, 3]},
    "map": {"c": [1, 2, 3, 5, 7, 11], "d": [2, 4, 6, 8], "x0": [2, 3, 5, 7]},
    "bins": {"m": [1, 2, 3, 7], "B": [1, 16, 256, 4096, 65536]},
    "exponent": {"a": [2, 3, 5, 7], "K": [2 ** k for k in range(8, 21, 2)]},
}
RULE_GRID = {
    "dot": {"t": [1, 0]},                       # t = 1 first: the exponent layout (p-1) only works with t = 1
    "batch": {"b": [1, 8, 64, 512, 4096], "t": [1, 0]},
    "floyd": {"b": [1, 8, 64, 128, 512, 4096]},
    "brent": {"b": [1, 8, 64, 128, 512, 4096]},
    "bins": {},
}
PAIRS = [(l, r) for l in LAYOUT_GRID for r in RULE_GRID
         if not (r in ("floyd", "brent") and l not in ("map", "stride")) and not (r == "bins" and l != "bins")]

class Invalid(Exception):
    """An error or aborted number (the early-exit audit): the genome is invalid and is never ranked."""

class Search:
    def __init__(self, sizes, per, seed0, chord, screen, draw=semiprimes_pq):
        self.sizes, self.per, self.chord, self.screen = sizes, per, chord, screen
        self.nums = {b: draw(b, per, seed0 + b) for b in sizes}
        self.rho = {b: V.run(V.RHO, V.CAP, self.nums[b], b) for b in sizes}
        assert all(sum(r["ok"] for r in self.rho[b]) >= per // 2 for b in sizes), "rho fails the training map"
        self.cap = {b: CAP_X * max(r["ops"] for r in self.rho[b]) for b in sizes}
        self.memo, self.evals = {}, 0

    def records(self, g, sizes, partial=False):
        """Per-number records at `sizes`, in order, in chunks of CHUNK numbers. At the first size where more than
        per/2 numbers have failed: (None, that size), or with partial, (the records so far, that size), the dropped
        size holding the chunks run before the drop."""
        out = {}
        for b in sizes:
            rs, fail = [], 0
            for i in range(0, self.per, CHUNK):
                part = V.run(g, self.cap[b], self.nums[b][i:i + CHUNK], b)
                rs += part
                if any(r["term"] in V.BAD_TERMS for r in part):
                    raise Invalid(f"{b} bits: " + next(r.get("why", r["term"]) for r in part if r["term"] in V.BAD_TERMS))
                fail += sum(not r["ok"] for r in part)
                if fail > self.per - self.per // 2:
                    if partial:
                        out[b] = rs
                        return out, b
                    return None, b
            out[b] = rs
        return out, None

    def ratio(self, rs, b):
        """Robust cost ratio against rho at size b: the worst (max) over op-class v1, ruint, Montgomery and the
        scaled gcd price of C_candidate / C_rho (None if either is not defined)."""
        v = [(lambda x, y: x / y if x and y else None)(V.per_fact(rs, p), V.per_fact(self.rho[b], p))
             for p in V.WORST_G_RHO]
        return None if None in v else max(v)

    def fitness(self, g):
        key = json.dumps(g, sort_keys=True)
        if key not in self.memo:
            self.evals += 1
            a, b = self.chord
            order = tuple(dict.fromkeys((a, self.screen, b) + tuple(self.sizes)))      # each size once
            R, ratios = {}, {}
            for s in order:
                try:
                    rs, dropped = self.records(g, (s,))
                except Invalid as e:
                    self.memo[key] = {"fit": None, "dropped_at": s, "why": f"INVALID (early-exit audit): {e}",
                                      "invalid": True, "ratio": ratios}
                    break
                if rs is None:
                    self.memo[key] = {"fit": None, "dropped_at": s, "why": "fewer than half factored", "ratio": ratios}
                    break
                R[s] = rs[s]
                ratios[s] = self.ratio(R[s], s)
                if ratios[s] is None or ratios[s] > GUARD:
                    self.memo[key] = {"fit": None, "dropped_at": s, "why": f"cost guard: robust ratio {ratios[s]}",
                                      "ratio": ratios}
                    break
            else:
                v = [(lambda pc, pr: pc / pr if pc and pr else None)(V.period(R, a, b, p), V.period(self.rho, a, b, p))
                     for p in V.WORST_G_RHO]
                self.memo[key] = {"fit": None if None in v else min(v), "dropped_at": None,
                                  "g_rho": dict(zip(V.WORST_G_RHO, v)), "ratio": ratios}
        return self.memo[key]

def better(x, y):
    """x strictly better than y (None = not defined, below everything)."""
    return x is not None and (y is None or x > y)

def genome(pair, genes):
    lay, rule = pair
    L = {"kind": lay, **{k: genes[("layout", k)] for k in LAYOUT_GRID[lay]}}
    D = {"kind": rule, **{k: genes[("detect", k)] for k in RULE_GRID[rule]}}
    return [{"t": "arr", "layout": L, "detect": D}]

def coordinate(S, pair, log):
    lay, rule = pair
    axes = [(("layout", k), v) for k, v in LAYOUT_GRID[lay].items()] + [(("detect", k), v) for k, v in RULE_GRID[rule].items()]
    genes = {k: v[0] for k, v in axes}
    best = S.fitness(genome(pair, genes))["fit"]
    with ThreadPoolExecutor(WORKERS) as ex:
        for sweep in range(4):
            changed = False
            for k, vals in axes:
                cands = [{**genes, k: v} for v in vals]
                fits = list(ex.map(lambda c: S.fitness(genome(pair, c))["fit"], cands))
                for c, f in zip(cands, fits):
                    if better(f, best):
                        genes, best, changed = c, f, True
            log(f"  {lay} x {rule}: sweep {sweep + 1}: best {best if best is None else round(best, 4)} at "
                + json.dumps({k[1]: v for k, v in genes.items()}) + f" ({S.evals} evaluations so far)")
            if not changed:
                break
    return genome(pair, genes), best

def main(sizes, per, seed0, chord, screen, out_dir, tag, draw=semiprimes_pq):
    t0 = time.time()
    log = lambda s: print(f"[{time.time() - t0:7.0f}s] {s}", flush=True)
    S = Search(sizes, per, seed0, chord, screen, draw)
    log(f"map {tag}: sizes {sizes}, {per} per size, seeds {seed0} + bits; rho successes "
        + str({b: sum(r['ok'] for r in S.rho[b]) for b in sizes}) + f"; budget per number {CAP_X} x rho's max: {S.cap}")
    res = {}
    for pair in PAIRS:
        g, f = coordinate(S, pair, log)
        lamps.validate_genome(g)
        res[pair] = (g, f)
    best = max((p for p in PAIRS), key=lambda p: (res[p][1] is not None, res[p][1] or 0))
    if res[best][1] is None:
        best = None
        log(f"best overall: none (no pair has a defined fitness); {S.evals} evaluations")
    else:
        log(f"best overall: {best[0]} x {best[1]}, fitness {res[best][1]}; {S.evals} evaluations")
    out = {"map": tag, "sizes": sizes, "per": per, "seeds": f"{seed0} + bits", "chord": chord, "screen": screen,
           "budget": {"x_rho_max": CAP_X, "per_size": S.cap}, "evaluations": S.evals,
           "numbers": {b: [[str(N), str(p), str(q)] for N, p, q in S.nums[b]] for b in sizes},
           "rho": {"genome": V.RHO, "records": S.rho}, "best": f"{best[0]}_{best[1]}" if best else None, "pairs": {},
           "evaluated": [{"genome": json.loads(k), **v} for k, v in S.memo.items()]}
    def final(pair):                      # every size in order, stopping where the genome is dropped (as the search)
        g = res[pair][0]
        try:
            return pair, S.records(g, sizes, partial=True)
        except Invalid as e:
            return pair, ({}, f"INVALID: {e}")
    with ThreadPoolExecutor(WORKERS) as ex:
        finals = dict(ex.map(final, PAIRS))
    for pair in PAIRS:
        g, f = res[pair]
        R, dropped = finals[pair]
        name = f"{pair[0]}_{pair[1]}"
        out["pairs"][name] = {"genome": g, "fitness": f, "search": S.memo[json.dumps(g, sort_keys=True)],
                              "records": R, "dropped_at": dropped}
        json.dump({"name": name, "genome": g}, open(os.path.join(out_dir, f"genome_{name}.json"), "w"))
        log(f"  {name}: fitness {f}; successes " + str({b: sum(r['ok'] for r in R[b]) for b in R})
            + (f"; dropped at {dropped} bits" if dropped else ""))
    path = os.path.join(out_dir, f"arr_search_{tag}.json")
    json.dump(out, open(path, "w"))
    log(f"wrote {path}")

if __name__ == "__main__":
    if not ARGV or ARGV[0] not in ("balanced", "theta", "selftest"):
        sys.exit(__doc__)
    out_dir = os.environ.get("LPW_SEARCH_OUT")
    if ARGV[0] == "selftest":
        out_dir = out_dir or os.environ.get("TMPDIR", "/tmp")
        main((20, 24, 28, 32), 16, 9929000, (20, 32), 28, out_dir, "selftest")
    else:
        if not out_dir:
            sys.exit("LPW_SEARCH_OUT is not set: the search runs only inside tools/search_sandbox.sh")
        if ARGV[0] == "balanced":
            main((48, 56, 64, 72, 80), 48, 9920000, (48, 80), 64, out_dir, "balanced")
        else:
            main((64, 80), 48, 9925000, (64, 80), 64, out_dir, "theta",
                 lambda bits, n, seed: theta_numbers(bits, seed, n))     # Search draws (bits, count, seed)
