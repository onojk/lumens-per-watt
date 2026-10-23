"""Evolve factoring algorithms, scored by lumens per watt.

  python3 evolve.py GENS POP WORKERS [cumulative|worst] [fine]
  cumulative (default, Run 3): score = cumulative total watts over every test number;
                               outputs go to run3/
  cumulative fine (Run 4):     same score, plus the luck-by-design cards and the hit-rate
                               meter; outputs go to run4/
  worst (Run 2):               score = worst case; outputs go to this folder

Meter (v2):
- Fresh training semiprimes every generation, so nothing can memorize them.
- Score = effective exponent at the top two training sizes, log2(worst ops)/bits.
  Lumens per watt at that size is N^(1/2 - score).
- Validation gate: each generation's training winner is re-run on a fixed held-out set
  of bigger numbers. Only a genome that wins there becomes the champion.
"""
import json, math, random, sys, time
from multiprocessing import Pool
from lamps import *

SIZES = [32, 38, 44]
PER_SIZE = 8
GATE = {48: semiprimes(48, 12, 4848)}

def train_set(seed):
    return {b: semiprimes(b, PER_SIZE, seed * 1000 + b) for b in SIZES}

MODE = sys.argv[4] if len(sys.argv) > 4 else "cumulative"     # "cumulative" (Run 3+) or "worst" (Run 2)
FINE = len(sys.argv) > 5 and sys.argv[5] == "fine"             # Run 4: luck-by-design cards
if FINE:
    use_fine_deck()
METER = measure_cumulative if MODE == "cumulative" else measure
WORST_KEY = "worst" if MODE == "cumulative" else "ys"

def score_job(args):
    gen, tests, abort = args
    try:
        return METER(gen, tests, abort)
    except Exception:
        return {"score": 9.0, "trend": None, "ys": {}, "worst": {}, "fails": 99}

BASELINES = {
    "trial division": [{"t": "td", "a": 0.5}],
    "fermat": [{"t": "sq", "mode": "one", "mult": 1, "k": 0.0, "w": 0.5, "c": 1.0, "ksq": False}],
    "lehman": [{"t": "td", "a": 1/3},
               {"t": "sq", "mode": "seq", "mult": 1, "k": 1/3, "w": 1/6, "c": 0.25, "ksq": True}],
    "hart x480": [{"t": "sq", "mode": "seqm", "mult": 480, "k": 0.40, "w": 0.0, "c": 1.0, "ksq": False}],
    "pollard-strassen": [{"t": "ps", "a": 0.5, "s": 0.25, "c": 1.0}],
    "rho": [{"t": "rho", "c": 1, "b": 64}],
}

def evolve(deck, gens, pop_n, seed, pool, log, key, lineage):
    """Every genome is a named individual with parents, the mutation that made it,
    and its birth generation. Each generation, every individual is written to the
    lineage log with its scores, so any champion can be traced back to its ancestors."""
    rng = random.Random(seed)
    tag = ("N" if key.startswith("no-luck") else "L") + str(seed)
    count = 0
    def born(genes, parents, op, gi):
        nonlocal count
        count += 1
        return {"name": f"{tag}-{count:04d}", "parents": parents, "op": op, "born": gi,
                "genes": genes}
    pop = [born(rand_genome(deck, rng), [], "seed", 0) for _ in range(pop_n)]
    champ, champ_gate = None, None
    hist = []
    for gi in range(gens):
        tests = train_set(seed * 100000 + gi)
        results = pool.map(score_job, [(ind["genes"], tests, None) for ind in pop[:2]])
        tops = [r[WORST_KEY].get(SIZES[-1]) for r in results if not r["fails"]]
        abort = (min(tops) + 4) if tops else None          # 16x the elite's top-size cost
        results += pool.map(score_job, [(ind["genes"], tests, abort) for ind in pop[2:]])
        ranked = sorted(zip(results, pop), key=lambda t: t[0]["score"])
        best_r, best = ranked[0]
        gate = METER(best["genes"], GATE)
        crowned = champ is None or gate["score"] < champ_gate["score"]
        if crowned:
            champ, champ_gate = best, gate
        for rank, (r, ind) in enumerate(ranked):
            lineage.write(json.dumps({
                "run": key, "gen": gi, "rank": rank, "name": ind["name"],
                "parents": ind["parents"], "op": ind["op"], "born": ind["born"],
                "train": round(r["score"], 4),
                "worst_top": round(r.get(WORST_KEY, {}).get(SIZES[-1], 0), 2),
                "hit_rate_log2": (round(r["luck"]["hit_rate_log2"], 2)
                                  if r.get("luck") and r["luck"]["hit_rate_log2"] is not None else None),
                "gate": round(gate["score"], 4) if rank == 0 else None,
                "champion": ind["name"] == champ["name"],
                "describe": describe(ind["genes"]), "genes": ind["genes"]}) + "\n")
        lineage.flush()
        hist.append({"gen": gi, "train": best_r["score"], "gate": gate["score"],
                     "champ_gate": champ_gate["score"], "best": best["name"],
                     "champ_name": champ["name"], "genome": best["genes"], "champ": champ["genes"]})
        log(f"  gen {gi:3d}  {best['name']} train N^{best_r['score']:.3f}  gate N^{gate['score']:.3f}"
            f"{'  NEW CHAMPION' if crowned else ''}  champion {champ['name']} N^{champ_gate['score']:.3f}"
            f"  {describe(best['genes'])}")
        elite = [ind for _, ind in ranked[: max(2, pop_n // 6)]]
        if champ not in elite:
            elite = [champ] + elite[:-1]
        parents = [ind for _, ind in ranked[: pop_n // 2]]
        nxt = list(elite)                                   # survivors keep their names
        while len(nxt) < pop_n:
            if rng.random() < 0.3:
                a, b = rng.choice(parents), rng.choice(parents)
                genes = crossover(a["genes"], b["genes"], rng)
                genes, op = mutate(genes, deck, rng)
                nxt.append(born(genes, [a["name"], b["name"]], "cross+" + op, gi + 1))
            else:
                a = rng.choice(parents)
                genes, op = mutate(a["genes"], deck, rng)
                nxt.append(born(genes, [a["name"]], op, gi + 1))
        pop = nxt
    return hist

SEEDS = (31, 32, 33, 34) if FINE else (21, 22, 23, 24) if MODE == "cumulative" else (11, 12, 13, 14)
DECKS = [("no-luck", ["td", "sq", "ps"], SEEDS[0]), ("no-luck", ["td", "sq", "ps"], SEEDS[1]),
         ("luck", ["td", "sq", "ps", "rho", "pm1"], SEEDS[2]),
         ("luck", ["td", "sq", "ps", "rho", "pm1"], SEEDS[3])]
OUT = "run4/" if FINE else "run3/" if MODE == "cumulative" else ""

if __name__ == "__main__":
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    pop_n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    out = {"mode": MODE, "baselines": {}, "runs": {}}
    import os
    if OUT:
        os.makedirs(OUT, exist_ok=True)
    logf = open(OUT + "evolve.log", "w")
    lineage = open(OUT + "lineage.jsonl", "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    with Pool(workers) as pool:
        t0 = time.time()
        bt = train_set(999)
        for name, g in BASELINES.items():
            r = METER(g, bt)
            out["baselines"][name] = r
            log(f"baseline {name:17s} N^{r['score']:.3f}  lumens/watt N^{0.5-r['score']:.3f}  "
                f"misses {r['fails']}")
        for deck_name, deck, seed in DECKS:
            key = f"{deck_name}-{seed}"
            log(f"run {key}")
            out["runs"][key] = evolve(deck, gens, pop_n, seed, pool, log, key, lineage)
            json.dump(out, open(OUT + "results.json", "w"), indent=1)
        log(f"done in {time.time()-t0:.0f}s")
