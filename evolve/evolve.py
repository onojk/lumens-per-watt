import json, math, random, sys, time
from multiprocessing import Pool
from lamps import *

TRAIN = {b: semiprimes(b, 10, 1000 + b) for b in SIZES}

def score(gen):
    try:
        e, top, ys = fitness(gen, TRAIN)
    except Exception as ex:
        return (9.0, 99.0, [])
    return (e, top, ys)

BASELINES = {
    "trial division": [{"t": "td", "a": 0.5}],
    "fermat": [{"t": "sq", "mode": "one", "mult": 1, "k": 0.0, "w": 0.5, "c": 1.0, "ksq": False}],
    "lehman": [{"t": "td", "a": 1/3},
               {"t": "sq", "mode": "seq", "mult": 1, "k": 1/3, "w": 1/6, "c": 0.25, "ksq": True}],
    "hart": [{"t": "sq", "mode": "seq", "mult": 1, "k": 1/3, "w": 0.0, "c": 1.0, "ksq": False}],
    "rho": [{"t": "rho", "c": 1, "b": 64}],
}

def evolve(deck, gens, pop_n, seed, pool, log):
    rng = random.Random(seed)
    pop = [rand_genome(deck, rng) for _ in range(pop_n)]
    best_hist = []
    for gen_i in range(gens):
        scores = pool.map(score, pop)
        ranked = sorted(zip(scores, pop), key=lambda t: (round(t[0][0], 3), t[0][1]))
        (e, top, ys), best = ranked[0]
        best_hist.append({"gen": gen_i, "e": e, "eff": 0.5 - e, "top": top, "genome": best})
        log(f"  gen {gen_i:3d}  best work N^{e:.3f}  lumens/watt N^{0.5-e:.3f}  "
            f"worst@44b 2^{top:.1f}  {describe(best)}")
        elite = [g for _, g in ranked[: max(2, pop_n // 6)]]
        parents = [g for _, g in ranked[: pop_n // 2]]
        nxt = [list(g) for g in elite]
        while len(nxt) < pop_n:
            if rng.random() < 0.3:
                child = crossover(rng.choice(parents), rng.choice(parents), rng)
            else:
                child = rng.choice(parents)
            nxt.append(mutate(child, deck, rng))
        pop = nxt
    return best_hist

if __name__ == "__main__":
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    pop_n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    out = {"baselines": {}, "runs": {}}
    logf = open("evolve.log", "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    with Pool(2) as pool:
        t0 = time.time()
        for name, g in BASELINES.items():
            e, top, ys = score(g)
            out["baselines"][name] = {"e": e, "eff": 0.5 - e, "top": top, "ys": ys}
            log(f"baseline {name:15s} work N^{e:.3f}  lumens/watt N^{0.5-e:.3f}")
        for deck_name, deck, seed in [("no-luck", ["td", "sq"], 1), ("no-luck", ["td", "sq"], 2),
                                      ("luck", ["td", "sq", "rho", "pm1"], 3),
                                      ("luck", ["td", "sq", "rho", "pm1"], 4)]:
            key = f"{deck_name}-{seed}"
            log(f"run {key}")
            out["runs"][key] = evolve(deck, gens, pop_n, seed, pool, log)
            json.dump(out, open("results.json", "w"), indent=1)
        log(f"done in {time.time()-t0:.0f}s")
