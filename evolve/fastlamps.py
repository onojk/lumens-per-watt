"""Run genomes through the Rust lamp core (../lampcore) for big numbers.

The Rust core counts operations exactly as lamps.py does; parity.py checks that on
hundreds of shared cases before any big-number result is trusted.

  from fastlamps import semiprimes_pq, run_many
  nums = semiprimes_pq(72, 40, seed)            # [(N, p, q), ...]
  results = run_many(genome, nums, cap)         # [(ops or None, factor, tests, hits), ...]
  run_many(genome, nums, cap, inst=True)        # adds (winning stage, square-search k)
  run_many(genome, nums, cap, phases=True)      # adds per-phase ops (genomes with qs or cfrac)
"""
import json, os, random, subprocess
from lamps import rand_prime

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.environ.get("LAMPCORE",
                     os.path.join(HERE, "..", "lampcore", "target", "release", "lampcore"))

PHASES = ["mult", "fb", "setup", "sieve", "confirm", "la", "sqrt", "lp", "check",
          "cf_step", "cf_td"]           # qs's and cfrac's, in lampcore's order

def semiprimes_pq(bits, count, seed):
    """Same numbers as lamps.semiprimes(bits, count, seed), with their factors."""
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        p, q = rand_prime(bits // 2, rng), rand_prime(bits - bits // 2, rng)
        if p != q:
            out.append((p * q, min(p, q), max(p, q)))
    return out

def semiprimes_unbalanced(bits, pbits, count, seed):
    """Semiprimes N = p q with p a random pbits-bit prime and q a random (bits - pbits)-bit
    prime (Stage 8's unbalanced population), as (N, smaller, larger)."""
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        p, q = rand_prime(pbits, rng), rand_prime(bits - pbits, rng)
        if p != q:
            out.append((p * q, min(p, q), max(p, q)))
    return out

def run_many(genome, nums, cap, inst=False, phases=False):
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + \
        "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    res = subprocess.run([BIN], input=text, capture_output=True, text=True, check=True)
    out = []
    for line in res.stdout.split("\n"):
        if not line:
            continue
        f = line.split()
        if f[0] == "miss":
            r = (None, None, int(f[1]), int(f[2]), None, None)
        else:
            r = (int(f[0]), int(f[1]), int(f[2]), int(f[3]), int(f[4]),
                 None if f[5] == "-" else int(f[5]))
        r = r if inst else r[:4]
        if phases:
            ph = [int(x) for x in (f[3:] if f[0] == "miss" else f[6:])]
            assert len(ph) == len(PHASES), line
            r = r + (dict(zip(PHASES, ph)),)
        out.append(r)
    return out
