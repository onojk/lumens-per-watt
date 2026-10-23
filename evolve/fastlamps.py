"""Run genomes through the Rust lamp core (../lampcore) for big numbers.

The Rust core counts operations exactly as lamps.py does; parity.py checks that on
hundreds of shared cases before any big-number result is trusted.

  from fastlamps import semiprimes_pq, run_many
  nums = semiprimes_pq(72, 40, seed)            # [(N, p, q), ...]
  results = run_many(genome, nums, cap)         # [(ops or None, factor, tests, hits), ...]
"""
import json, os, random, subprocess
from lamps import rand_prime

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.environ.get("LAMPCORE",
                     os.path.join(HERE, "..", "lampcore", "target", "release", "lampcore"))

def semiprimes_pq(bits, count, seed):
    """Same numbers as lamps.semiprimes(bits, count, seed), with their factors."""
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        p, q = rand_prime(bits // 2, rng), rand_prime(bits - bits // 2, rng)
        if p != q:
            out.append((p * q, min(p, q), max(p, q)))
    return out

def run_many(genome, nums, cap):
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + \
        "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    res = subprocess.run([BIN], input=text, capture_output=True, text=True, check=True)
    out = []
    for line in res.stdout.split("\n"):
        if not line:
            continue
        f = line.split()
        if f[0] == "miss":
            out.append((None, None, int(f[1]), int(f[2])))
        else:
            out.append((int(f[0]), int(f[1]), int(f[2]), int(f[3])))
    return out
