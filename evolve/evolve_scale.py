"""Run 5: evolution scored at scale, through the Rust lamp core.

Small sizes reward constants; big sizes reward exponents (see NOTES.md). This runs the
same evolution as evolve.py (cumulative scoreboard, fine deck, lineage, gate) but measures
every genome with lampcore at 52, 58, and 64 bits, with the gate at 68 bits.

  python3 evolve_scale.py GENS POP WORKERS

Outputs go to run5/. Needs lampcore built and parity.py passing.
Seeds 41-44 belong to this run; later runs use fresh seeds.
"""
import math, sys
import evolve as ev
from lamps import use_fine_deck
from fastlamps import semiprimes_pq, run_many

SIZES = [52, 58, 64]
PER_SIZE = 6
CAP_LOG2 = 23          # 2^23: about 8x the best bulbs' worst case at 64 bits

def train_set(seed):
    return {b: semiprimes_pq(b, PER_SIZE, seed * 1000 + b) for b in SIZES}

def measure_fast(gen, tests, abort_log2=None):
    """Same scoring as lamps.measure_cumulative, computed by lampcore."""
    sizes = sorted(tests, reverse=True)
    cum, worst, fails = {}, {}, 0
    t_all = h_all = solved = 0
    for i, bits in enumerate(sizes):
        cap = 2 ** CAP_LOG2
        if i == 0 and abort_log2 is not None:
            cap = min(cap, int(2 ** abort_log2))
        res = run_many(gen, tests[bits], cap)
        total, w = 0, 0
        for ops, d, t, h in res:
            t_all += t; h_all += h
            if ops is None:
                fails += 1
                if i == 0:
                    return {"score": 0.5 + 0.02 * fails, "cum": cum, "worst": worst,
                            "fails": fails, "luck": None}
                ops = 2 ** CAP_LOG2
            else:
                solved += 1
            total += ops; w = max(w, ops)
        cum[bits] = math.log2(total / len(res))
        worst[bits] = math.log2(max(w, 1))
    top = sizes[:2]
    score = sum(cum[b] / b for b in top) / len(top)
    if fails:
        score = max(score, 0.5) + 0.02 * fails
    luck = {"tests": t_all, "hits": h_all,
            "hit_rate_log2": math.log2(h_all / t_all) if h_all and t_all else None,
            "useful_share": solved / h_all if h_all else None}
    return {"score": score, "cum": cum, "worst": worst, "fails": fails, "luck": luck}

if __name__ == "__main__":
    use_fine_deck()
    ev.SIZES = SIZES
    ev.train_set = train_set
    ev.GATE = {68: semiprimes_pq(68, 12, 6868)}
    ev.METER = measure_fast
    ev.WORST_KEY = "worst"
    ev.MODE = "cumulative"
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    pop_n = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    import json, os, time
    from multiprocessing import Pool
    os.makedirs("run5", exist_ok=True)
    out = {"mode": "cumulative-at-scale", "sizes": SIZES, "gate_bits": 68,
           "baselines": {}, "runs": {}}
    logf = open("run5/evolve.log", "w")
    lineage = open("run5/lineage.jsonl", "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    decks = [("no-luck", ["td", "sq", "ps"], 41), ("no-luck", ["td", "sq", "ps"], 42),
             ("luck", ["td", "sq", "ps", "rho", "pm1"], 43),
             ("luck", ["td", "sq", "ps", "rho", "pm1"], 44)]
    with Pool(workers) as pool:
        t0 = time.time()
        bt = train_set(999)
        for name, g in ev.BASELINES.items():
            if name in ("trial division", "fermat"):
                continue
            r = measure_fast(g, bt)
            out["baselines"][name] = r
            log(f"baseline {name:17s} N^{r['score']:.3f}  lumens/watt N^{0.5-r['score']:.3f}  "
                f"misses {r['fails']}")
        for deck_name, deck, seed in decks:
            key = f"{deck_name}-{seed}"
            log(f"run {key}")
            out["runs"][key] = ev.evolve(deck, gens, pop_n, seed, pool, log, key, lineage)
            json.dump(out, open("run5/results.json", "w"), indent=1)
        log(f"done in {time.time()-t0:.0f}s")
