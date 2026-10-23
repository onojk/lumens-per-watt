"""Run 6: island-model evolution with the quadratic sieve in the deck, through lampcore.

  python3 evolve_run6.py [GENS] [PER_ISLAND] [WORKERS]       (defaults 20 16 8)

Four runs, one after another: no-luck 51, 52 (td, sq, ps, qs) and luck 53, 54
(td, sq, ps, rho, pm1, qs), fine deck on, coverage rule off. Each run is 4 islands x
PER_ISLAND genomes. Scoring is Run 5's (evolve_scale.measure_fast: cumulative, top two
sizes) on fresh numbers at 66/72/78 bits each generation, 6 per size, cap 2^26, with the
elite-first abort (16x the best elite's top-size cost). Every island's best goes through
the 84-bit gate (12 fixed numbers, cap 2^28); the run champion is the best gate score seen.

Per island, each generation (evolve.py's rules, per island):
- elites: the top two survive by name, plus the island's own gate champion if it fell out;
- diversity reserve: two more survivors, the best-ranked genomes whose card set (the set of
  stage types) differs from every elite's and from each other's, among those that solved
  every training number; fresh random genomes fill any slot left empty;
- migration (ring): after every 5th generation, each island's top two are copied into the
  next island, replacing two of its children;
- children: from the top half, 30% crossover + mutation, 70% mutation.

Outputs in run6/: evolve.log, lineage.jsonl (every genome, every generation, with its
island), results.json (rewritten after every generation, so a crash loses at most one).
Seeds 51-54 belong to this run.
"""
import json, math, os, random, sys, time
GENS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 16
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
sys.argv = sys.argv[:1]          # evolve.py reads its own argv at import
from multiprocessing import Pool
import evolve_scale as es
from evolve import BASELINES
from lamps import use_fine_deck, rand_genome, mutate, crossover, describe
from fastlamps import semiprimes_pq

SIZES = [66, 72, 78]
PER_SIZE = 6
TRAIN_CAP, GATE_CAP = 26, 28
ISLANDS, MIGRATE_EVERY, MIGRANTS, RESERVE = 4, 5, 2, 2
GATE = {84: semiprimes_pq(84, 12, 8484)}
QS_DEFAULT = [{"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}]
DECKS = [("no-luck", ["td", "sq", "ps", "qs"], 51), ("no-luck", ["td", "sq", "ps", "qs"], 52),
         ("luck", ["td", "sq", "ps", "rho", "pm1", "qs"], 53),
         ("luck", ["td", "sq", "ps", "rho", "pm1", "qs"], 54)]
OUT = os.environ.get("RUN6_OUT", "run6/")      # override only for smoke tests

def train_set(seed):
    return {b: semiprimes_pq(b, PER_SIZE, seed * 1000 + b) for b in SIZES}

def score_job(args):
    gen, tests, abort, cap_log2 = args
    es.CAP_LOG2 = cap_log2
    try:
        return es.measure_fast(gen, tests, abort)
    except Exception as e:
        return {"score": 9.0, "cum": {}, "worst": {}, "fails": 99, "luck": None, "err": str(e)}

def cards(ind):
    return frozenset(s["t"] for s in ind["genes"])

def evolve_islands(deck, seed, pool, log, key, lineage, on_gen):
    rng = random.Random(seed)
    tag = ("N" if key.startswith("no-luck") else "L") + str(seed)
    count = 0
    def born(genes, parents, op, gi):
        nonlocal count
        count += 1
        return {"name": f"{tag}-{count:04d}", "parents": parents, "op": op, "born": gi,
                "genes": genes}
    isl = [[born(rand_genome(deck, rng), [], "seed", 0) for _ in range(PER)] for _ in range(ISLANDS)]
    arrived = [{} for _ in range(ISLANDS)]           # name -> island it migrated from, this gen
    isl_champ = [None] * ISLANDS                     # (individual, gate result) per island
    champ, champ_gate, champ_island = None, None, None
    hist = []
    for gi in range(GENS):
        t0 = time.time()
        tests = train_set(seed * 100000 + gi)
        first = pool.map(score_job, [(ind["genes"], tests, None, TRAIN_CAP)
                                     for pop in isl for ind in pop[:2]])
        aborts = []
        for i in range(ISLANDS):
            tops = [r["worst"].get(SIZES[-1]) for r in first[2 * i:2 * i + 2] if not r["fails"]]
            aborts.append((min(tops) + 4) if tops else None)
        rest = pool.map(score_job, [(ind["genes"], tests, aborts[i], TRAIN_CAP)
                                    for i, pop in enumerate(isl) for ind in pop[2:]])
        n = PER - 2
        ranked = [sorted(zip(first[2 * i:2 * i + 2] + rest[n * i:n * i + n], isl[i]),
                         key=lambda t: t[0]["score"]) for i in range(ISLANDS)]
        gates = pool.map(score_job, [(rk[0][1]["genes"], GATE, None, GATE_CAP) for rk in ranked])
        crowned = False
        for i, (rk, gate) in enumerate(zip(ranked, gates)):
            best = rk[0][1]
            if isl_champ[i] is None or gate["score"] < isl_champ[i][1]["score"]:
                isl_champ[i] = (best, gate)
            if champ is None or gate["score"] < champ_gate["score"]:
                champ, champ_gate, champ_island, crowned = best, gate, i, True
        for i, rk in enumerate(ranked):
            for rank, (r, ind) in enumerate(rk):
                lineage.write(json.dumps({
                    "run": key, "gen": gi, "island": i, "rank": rank, "name": ind["name"],
                    "parents": ind["parents"], "op": ind["op"], "born": ind["born"],
                    "migrant_from": arrived[i].get(ind["name"]),
                    "train": round(r["score"], 4),
                    "worst_top": round(r.get("worst", {}).get(SIZES[-1], 0), 2),
                    "hit_rate_log2": (round(r["luck"]["hit_rate_log2"], 2)
                                      if r.get("luck") and r["luck"]["hit_rate_log2"] is not None
                                      else None),
                    "fails": r["fails"],
                    "gate": round(gates[i]["score"], 4) if rank == 0 else None,
                    "champion": ind["name"] == champ["name"],
                    "describe": describe(ind["genes"]), "genes": ind["genes"],
                    **({"err": r["err"]} if "err" in r else {}),
                    }) + "\n")
        lineage.flush()
        hist.append({"gen": gi, "secs": round(time.time() - t0, 1),
                     "islands": [{"best": rk[0][1]["name"], "train": rk[0][0]["score"],
                                  "gate": g["score"], "genome": rk[0][1]["genes"],
                                  "abort_log2": a, "contains_qs": any(s["t"] == "qs" for s in rk[0][1]["genes"])}
                                 for rk, g, a in zip(ranked, gates, aborts)],
                     "train": min(rk[0][0]["score"] for rk in ranked),
                     "gate": min(g["score"] for g in gates),
                     "champ_gate": champ_gate["score"], "champ_name": champ["name"],
                     "champ_island": champ_island, "champ": champ["genes"],
                     "champ_gate_detail": champ_gate})
        log(f"  gen {gi:3d}  {time.time() - t0:5.0f}s  " + "  ".join(
            f"i{i} {rk[0][1]['name']} {rk[0][0]['score']:.3f}/{g['score']:.3f}"
            for i, (rk, g) in enumerate(zip(ranked, gates)))
            + f"{'  NEW CHAMPION' if crowned else ''}  champion {champ['name']} (i{champ_island}) "
              f"N^{champ_gate['score']:.3f}  {describe(champ['genes'])}")
        on_gen(hist)
        if gi == GENS - 1:
            break
        # next generation, island by island
        nxt = []
        for i, rk in enumerate(ranked):
            elite = [ind for _, ind in rk[:max(2, PER // 6)]]
            if isl_champ[i][0] not in elite:
                elite = [isl_champ[i][0]] + elite[:-1]
            seen = {cards(e) for e in elite}
            reserve = []
            for r, ind in rk:
                if len(reserve) == RESERVE:
                    break
                if ind in elite or r["fails"] or cards(ind) in seen:
                    continue
                reserve.append(ind); seen.add(cards(ind))
            while len(reserve) < RESERVE:
                reserve.append(born(rand_genome(deck, rng), [], "reserve-random", gi + 1))
            parents = [ind for _, ind in rk[:PER // 2]]
            pop = elite + reserve
            while len(pop) < PER:
                if rng.random() < 0.3:
                    a, b = rng.choice(parents), rng.choice(parents)
                    genes, op = mutate(crossover(a["genes"], b["genes"], rng), deck, rng)
                    pop.append(born(genes, [a["name"], b["name"]], "cross+" + op, gi + 1))
                else:
                    a = rng.choice(parents)
                    genes, op = mutate(a["genes"], deck, rng)
                    pop.append(born(genes, [a["name"]], op, gi + 1))
            nxt.append(pop)
        arrived = [{} for _ in range(ISLANDS)]
        if (gi + 1) % MIGRATE_EVERY == 0:
            for i, rk in enumerate(ranked):
                j = (i + 1) % ISLANDS
                names = {ind["name"] for ind in nxt[j]}
                movers = [ind for _, ind in rk[:MIGRANTS] if ind["name"] not in names]
                if movers:                           # they replace the last children bred
                    nxt[j] = nxt[j][:PER - len(movers)] + movers
                for ind in movers:
                    arrived[j][ind["name"]] = i
            log(f"  migration after gen {gi}: " + ", ".join(
                f"i{arr[n]}->i{j} {n}" for j, arr in enumerate(arrived) for n in arr))
        isl = nxt
    return hist

if __name__ == "__main__":
    use_fine_deck()
    os.makedirs(OUT, exist_ok=True)
    out = {"mode": "islands-at-scale", "sizes": SIZES, "per_size": PER_SIZE, "gate_bits": 84,
           "gate_seed": 8484, "caps_log2": {"train": TRAIN_CAP, "gate": GATE_CAP},
           "islands": ISLANDS, "per_island": PER, "gens": GENS, "migrate_every": MIGRATE_EVERY,
           "migrants": MIGRANTS, "reserve": RESERVE, "baselines": {}, "runs": {}}
    logf = open(OUT + "evolve.log", "w")
    lineage = open(OUT + "lineage.jsonl", "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    def save():
        tmp = OUT + "results.json.tmp"
        json.dump(out, open(tmp, "w"), indent=1)
        os.replace(tmp, OUT + "results.json")
    log(f"Run 6: {GENS} generations, {ISLANDS} islands x {PER}, workers {WORKERS}, "
        f"train {SIZES} cap 2^{TRAIN_CAP}, gate 84 bits cap 2^{GATE_CAP}")
    hist5 = json.load(open("run5/results.json"))["runs"]["luck-44"]
    assert hist5[-1]["champ_name"] == "L44-0272"
    refs = {"rho": BASELINES["rho"], "hart x480": BASELINES["hart x480"],
            "lehman": BASELINES["lehman"], "qs default": QS_DEFAULT, "L44-0272": hist5[-1]["champ"]}
    with Pool(WORKERS) as pool:
        t0 = time.time()
        bt = train_set(999)
        res = pool.map(score_job, [(g, bt, None, TRAIN_CAP) for g in refs.values()])
        for name, r in zip(refs, res):
            out["baselines"][name] = r
            log(f"baseline {name:11s} N^{r['score']:.3f}  lumens/watt N^{0.5 - r['score']:.3f}  "
                f"misses {r['fails']}")
        save()
        for deck_name, deck, seed in DECKS:
            key = f"{deck_name}-{seed}"
            log(f"run {key}")
            def on_gen(hist, key=key):
                out["runs"][key] = hist
                save()
            evolve_islands(deck, seed, pool, log, key, lineage, on_gen)
        log(f"done in {time.time() - t0:.0f}s")
