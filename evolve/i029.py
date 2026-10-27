"""I-029 microbenchmark driver (NOTES.md, "I-029 microbenchmark: design note"; predictions/i029.md, cbc2220).
1. Capture: Python traces (qs.TRACE_ARR) of the reference card at 96 bits on stage B's 8-number subset. Every
   polynomial's base and, per odd base prime, its roots in sieve-index coordinates (two for p not dividing kA; one
   for p | k; one for A's primes, where g is linear mod p); every candidate confirm processed (i0, v = g(x)).
   A Python check confirms, for every candidate, that the root hits are exactly the odd base primes dividing v.
2. lampcore's i029bench (Rust release) on the capture, pinned to core 2, twice (two replicates).
3. The implied wall-clock change for the reference card at 96, all else equal: 1,013 candidates per number x
   (t_root - t_full), against H2's reference (2,100.1 us per number, confirm 576.4 us; stageh2.json).
  python3 i029.py -> i029.json, stdout (the capture is written to the scratch file i029_cands.txt, not committed)
"""
import json, subprocess
import partition as P, qs, lamps
from ledger import Charger, Ledger
from lctest import ref, bnd
from step9 import sample

BIN = "../lampcore/target/release/i029bench"
g = ref(96)
lines = []
ncand = 0
qs.TRACE_ARR = True
for N, _, _ in sample(96):
    qs.TRACE = {}
    qs.lamp_qs(N, g, lamps.Meter(P.QS_CAP))
    tr = qs.TRACE; qs.TRACE = None
    B = bnd(N, g)
    for at in tr["attempts"]:
        if "s1" not in at:
            continue
        k = at["k"]; kN = k * N
        led = Ledger(N, k, B, Charger(lamps.Meter(1 << 60), None), None); led.build_base()
        base, rt = led.base, led.roots_t
        lines.append("base " + " ".join(map(str, base)))
        ps = at["polys"]; ntot = len(at["cands"])
        for pi, po in enumerate(ps):
            if "A" not in po:
                continue
            A, Bv, C, M = po["A"], po["B"], po["C"], po["Mw"]
            c1 = ps[pi + 1]["c0"] if pi + 1 < len(ps) and "c0" in ps[pi + 1] else ntot
            proc = po["cand_pos"][:max(0, c1 - po["c0"])]
            roots = []
            for p in base[2:]:
                if A % p == 0:
                    x = -C * pow(2 * Bv, -1, p) % p
                    rs = [(x + M) % p] * 2
                elif rt[p] == 0:
                    x = -Bv * pow(A, -1, p) % p
                    rs = [(x + M) % p] * 2
                else:
                    ai = pow(A, -1, p)
                    rs = [((rt[p] - Bv) * ai + M) % p, ((-rt[p] - Bv) * ai + M) % p]
                roots += rs
            cs = []
            for i0 in proc:
                x = i0 - M
                v = (A * x + 2 * Bv) * x + C
                hit = {p for j, p in enumerate(base[2:]) if i0 % p in (roots[2 * j], roots[2 * j + 1])}
                div = {p for p in base[2:] if v % p == 0}
                assert hit == div, (N, A, i0)
                cs.append(f"{i0} {v}")
            lines.append(f"poly {len(cs)}")
            lines.append(" ".join(map(str, roots)))
            lines += cs
            ncand += len(cs)
qs.TRACE_ARR = False
open("i029_cands.txt", "w").write("\n".join(lines) + "\n")
print(f"captured {ncand} candidates (root hits = dividing odd primes, checked in Python)", flush=True)
reps = []
for rep in (1, 2):
    r = subprocess.run(["taskset", "-c", "2", BIN], stdin=open("i029_cands.txt"), capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    reps.append(d)
    print(f"replicate {rep}: " + r.stdout.strip(), flush=True)
h2 = json.load(open("stageh2.json"))["reference"]
wall, conf, cands = sum(h2["wall_us"]) / 2, h2["wall_regions_us"]["confirm"], h2["candidates"]
out = {"replicates": reps, "h2_reference": {"wall_us": wall, "confirm_us": conf, "candidates": cands}, "summary": {}}
for ver in ("full", "root", "root_bf"):
    med = sum(d[ver]["ns_per_cand_median"] for d in reps) / 2
    mean = sum(d[ver]["ns_per_cand_mean"] for d in reps) / 2
    pmed = sum(d[ver]["ns_per_prime_median"] for d in reps) / 2
    out["summary"][ver] = {"ns_per_cand_median": med, "ns_per_cand_mean": mean, "ns_per_prime_median": pmed}
full = out["summary"]["full"]["ns_per_cand_median"]
for ver in ("root", "root_bf"):
    s = out["summary"][ver]
    d_us = cands * (s["ns_per_cand_median"] - full) / 1e3
    s["implied_delta_us"] = d_us
    s["implied_wall_change_pct"] = d_us / wall * 100
print(f"\nmeans of the two replicates (median over passes): full {full:.1f} ns per candidate "
      f"({out['summary']['full']['ns_per_prime_median']:.3f} ns per prime); " +
      "; ".join(f"{v} {out['summary'][v]['ns_per_cand_median']:.1f} ns per candidate ({out['summary'][v]['ns_per_prime_median']:.3f} ns per prime tested), "
                f"implied {out['summary'][v]['implied_delta_us']:+.1f} us per number = {out['summary'][v]['implied_wall_change_pct']:+.1f}% of H2's reference "
                f"{wall:,.1f} us (confirm {conf:.1f} us, {cands:,.0f} candidates)" for v in ("root", "root_bf")), flush=True)
json.dump(out, open("i029.json", "w"), indent=1)
