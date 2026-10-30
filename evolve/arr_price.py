"""Pricing and per-number records for arrangement-v1, shared by the scoring harness (arr_validate.py) and the search
(arr_search.py). A judge file: pinned. It holds no number generator and no seed, so the search sandbox can mount it
without exposing held-out data (DeepSeek's item 2, Oct 30).

run(genome, cap, nums, bits) -> one record per number:
  ok      the printed factor is p or q
  ops     official ops spent (the sum of the per-type counts)
  cost    official, ruint, Montgomery, op-class v1 (growth_harness.costs' rules) and op-class v1 with the size-scaled
          gcd price (gcdscale; the small-k curve for the gcd_small count, lampcore's " A n", uniform otherwise)
  term    the termination (Grok's b1 early-exit audit, Oct 30):
            "factor"   a factor equal to p or q
            "budget"   no factor, the run cap spent (ops >= cap)
            "ended"    no factor, under the cap: the stage ended by itself (a layout that finished, a gcd of N, an ob)
            "error"    anything else: lampcore exited non-zero, a missing or unparsable line, a factor that is not p
                       or q, an inconsistent count
            "aborted"  the lampcore call was cut short (a timeout); every number of that call
  An "error" or "aborted" record makes a genome's score invalid (arr_validate). Records of an aborted or failed
  call carry no costs (None), so no statistic can use them silently.
Per-fact cost and the doubling period are G's and G_rho's definitions (growth_harness.per_fact)."""
import json, math, os, subprocess
import optypes, gcdscale
from fastlamps import BIN

CAP = 2 ** 34
RHO = [{"t": "rho", "c": 1, "b": 64}]           # partition.PRE["rho"] (G_rho's reference genes); the harness asserts it
PRICINGS = ("opclass_v1", "ruint", "montgomery", "official", "opclass_v1_gcdscaled")
WORST_G_RHO = ("opclass_v1", "ruint", "montgomery", "opclass_v1_gcdscaled")
WORST_G = ("opclass_v1", "ruint", "montgomery")
HERE = os.path.dirname(os.path.abspath(__file__))
V1 = {k: v["weight"] for k, v in json.load(open(os.path.join(HERE, "..", "opclass", "opclass_v1.json")))["classes"].items()
      if v["weight"]}
PR = optypes.prices(os.path.join(HERE, "calibrate.json"))
TERMS = ("factor", "budget", "ended", "error", "aborted")
BAD_TERMS = ("error", "aborted")

def costs(ty, bits, small):
    """The five pricings of one run's per-type counts (growth_harness.costs, plus the scaled gcd price)."""
    priced = lambda pr: None if any(n and t not in PR[pr] for t, n in ty.items()) else optypes.cost(ty, pr, PR)
    c = {"official": float(sum(ty.values())), "ruint": priced("ruint"), "montgomery": priced("montgomery"),
         "opclass_v1": None if any(n and t not in V1 for t, n in ty.items()) else sum(V1[t] * n for t, n in ty.items() if n)}
    sc = gcdscale.cost({t: n for t, n in ty.items() if t != "gcd"}, bits) if ty else 0.0
    if sc is not None:
        g = ty.get("gcd", 0)
        sc += small * gcdscale.gcd_units(bits, "small") + (g - small) * gcdscale.gcd_units(bits, "uniform")
    c["opclass_v1_gcdscaled"] = sc
    return c

def _bad(term, why, n):
    return [{"ok": False, "ops": 0, "cost": {p: None for p in PRICINGS}, "gcd": 0, "gcd_small": 0, "term": term,
             "why": why} for _ in range(n)]

def run(genome, cap, nums, bits, timeout=None):
    """One lampcore --types call over nums; one record per number (see the module doc). Never raises for a lampcore
    failure: the failure is recorded per number."""
    text = json.dumps(genome) + "\n" + str(int(cap)) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    try:
        r = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _bad("aborted", f"timeout after {timeout} s", len(nums))
    if r.returncode != 0:
        return _bad("error", f"lampcore exit {r.returncode}: {r.stderr.strip()[-200:]}", len(nums))
    lines = r.stdout.splitlines()
    res = []
    for k, (N, p, q) in enumerate(nums):
        try:
            f = lines[k].split()
            i = f.index("T")
            counts = list(map(int, f[i + 1:]))
            if len(counts) != len(optypes.TYPE_ORDER) or any(n < 0 for n in counts):
                raise ValueError("per-type counts")
            ty = {t: n for t, n in zip(optypes.TYPE_ORDER, counts) if n}
            small = int(f[f.index("A") + 1]) if "A" in f[:i] else 0
            if not 0 <= small <= ty.get("gcd", 0):
                raise ValueError("gcd_small exceeds the gcds")
            ops = sum(ty.values())
            if f[0] == "miss":
                term, ok = ("budget" if ops >= cap else "ended"), False
            else:
                if int(f[1]) not in (p, q) or int(f[0]) != ops:
                    raise ValueError("a factor that is not p or q, or ops that do not match the counts")
                term, ok = "factor", True
            res.append({"ok": ok, "ops": ops, "cost": costs(ty, bits, small), "gcd": ty.get("gcd", 0),
                        "gcd_small": small, "term": term})
        except (IndexError, ValueError) as e:
            res.append(_bad("error", f"line {k}: {e}", 1)[0])
    if len(lines) != len(nums):
        for x in res:
            if x["term"] not in BAD_TERMS:
                x.update(_bad("error", f"lampcore printed {len(lines)} lines for {len(nums)} numbers", 1)[0])
    return res

def per_fact(rs, pr, idx=None):
    """Total priced cost / successes; None below half successes or when a cost is unpriced."""
    idx = range(len(rs)) if idx is None else idx
    s = sum(rs[i]["ok"] for i in idx)
    if s < len(rs) // 2 or any(rs[i]["cost"][pr] is None for i in idx):
        return None
    return sum(rs[i]["cost"][pr] for i in idx) / s

def period(R, a, b, pr, ix=None):
    """Doubling period over a-b; None when not defined: too few successes, an unpriced type, or a cost that does not
    grow over the chord (C(b) <= C(a): no doubling, so no period; a negative "period" would read as fast growth)."""
    ca, cb = per_fact(R[a], pr, ix and ix[a]), per_fact(R[b], pr, ix and ix[b])
    return (b - a) / math.log2(cb / ca) if ca and cb and cb > ca else None
