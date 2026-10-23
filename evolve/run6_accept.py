"""Run 6 ACCEPT, written before any Run 6 result exists.

The champions of the four Run 6 runs (run6/results.json: the last generation's "champ" per
run) against qs-default, Run 5's L44-0272, and rho, through lampcore at cap 2^28 on:
- 72 and 78 bits: the Stage 2 numbers, semiprimes_pq(bits, 80, 990000 + bits);
- 84 bits: 80 fresh numbers, semiprimes_pq(84, 80, 1300084) (seed 1300000 + bits, used by
  no earlier stage; the gate's 8484 and the cap check's 1100084 are different sets).

Per size: log2(mean ops) with revalidate.py's 95% bootstrap interval (random.Random(2026) per
cell, 10,000 resamples, tails at index 250 and 9749; misses left out of the mean and starred,
as in Stage 2), and the worst case with the same bootstrap on the max of each resample (its own
fresh random.Random(2026); a miss counts as the cap there, so a starred worst is a lower bound).
For each champion: whether it contains qs, and with what genes.

Check: at 72 and 78 bits the reference rows (qs-default, L44-0272, rho) must reproduce
qs_stage2.json exactly when they have no misses (that file is cap 2^29), or this stops.

  python3 run6_accept.py [workers]

Writes run6/accept.json.
"""
import json, math, os, random, sys
from multiprocessing import Pool
from fastlamps import semiprimes_pq, run_many
from evolve import BASELINES
from revalidate import bootstrap, R

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
CAP = 2 ** 28
SETS = {72: (80, 990072), 78: (80, 990078), 84: (80, 1300084)}
OUT = os.environ.get("RUN6_OUT", "run6/")      # override only for smoke tests
QS_DEFAULT = [{"t": "qs", "kc": 16, "bc": 1.5, "mc": 4.0, "tc": 2.0}]

def bootstrap_worst(ops):
    rng = random.Random(2026)
    n = len(ops)
    vals = sorted(math.log2(max(rng.choice(ops) for _ in range(n))) for _ in range(R))
    return vals[int(0.025 * R)], vals[int(0.975 * R) - 1]

def job(args):
    name, g, bits = args
    count, seed = SETS[bits]
    r = run_many(g, semiprimes_pq(bits, count, seed), CAP)
    all_ops = [x[0] for x in r]
    ops = [x for x in all_ops if x is not None]
    capped = [CAP if x is None else x for x in all_ops]
    return name, bits, {
        "mean_log2": math.log2(sum(ops) / len(ops)) if ops else None,
        "ci95": list(bootstrap(ops)) if ops else None,
        "worst_log2": math.log2(max(capped)), "worst_ci95": list(bootstrap_worst(capped)),
        "misses": len(all_ops) - len(ops)}

def qs_genes(g):
    return [{k: v for k, v in s.items() if k != "t"} for s in g if s["t"] == "qs"]

if __name__ == "__main__":
    runs = json.load(open(OUT + "results.json"))["runs"]
    assert len(runs) == 4, f"expected four finished runs, found {list(runs)}"
    hist5 = json.load(open("run5/results.json"))["runs"]["luck-44"]
    assert hist5[-1]["champ_name"] == "L44-0272"
    genomes, champs = {}, {}
    for key, hist in runs.items():
        last = hist[-1]
        genomes[last["champ_name"]] = last["champ"]
        champs[last["champ_name"]] = {"run": key, "gens": len(hist), "gate_84": last["champ_gate"],
                                      "contains_qs": bool(qs_genes(last["champ"])),
                                      "qs_genes": qs_genes(last["champ"]), "genes": last["champ"]}
    genomes.update({"qs default": QS_DEFAULT, "L44-0272": hist5[-1]["champ"], "rho": BASELINES["rho"]})
    with Pool(WORKERS) as pool:
        res = pool.map(job, [(name, g, b) for name, g in genomes.items() for b in SETS])
    out = {"cap_log2": 28, "sets": {str(b): {"count": c, "seed": s} for b, (c, s) in SETS.items()},
           "champions": champs, "genomes": genomes, "results": {}}
    for name, b, cell in res:
        out["results"].setdefault(name, {})[str(b)] = cell
    stage2 = json.load(open("qs_stage2.json"))["results"]
    for name, ref in (("qs default", "qs"), ("L44-0272", "L44-0272"), ("rho", "rho")):
        for b in (72, 78):
            a, s = out["results"][name][str(b)], stage2[ref][str(b)]
            if s["misses"] == 0 and not all(a[k] == s[k] for k in ("mean_log2", "ci95", "worst_log2", "misses")):
                sys.exit(f"STOP: {name} at {b} bits does not reproduce qs_stage2.json: {a} vs {s}")
    print("qs default, L44-0272 and rho reproduce their qs_stage2.json rows at 72 and 78 bits")
    star = lambda c: "*" if c["misses"] else ""
    print(f"{'':12s}" + "".join(f"{b} bits: mean [95% CI]   worst [95% CI]".ljust(50) for b in SETS))
    for name, by in out["results"].items():
        print(f"{name:12s}" + "".join(
            (f"{c['mean_log2']:.2f}{star(c)} [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}]"
             if c["mean_log2"] is not None else "all missed*").ljust(24)
            + f"{c['worst_log2']:.2f}{star(c)} [{c['worst_ci95'][0]:.2f}, {c['worst_ci95'][1]:.2f}]".ljust(26)
            for c in (by[str(b)] for b in SETS)))
    for name, c in champs.items():
        print(f"{name} ({c['run']}): gate N^{c['gate_84']:.3f}; "
              + (f"contains qs, genes {c['qs_genes']}" if c["contains_qs"] else "no qs"))
    json.dump(out, open(OUT + "accept.json", "w"), indent=1)
