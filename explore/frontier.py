"""The frontier (the user's ruling, Oct 30): per size, the minimum cost over all known lamps under the worst-of pricing
set, the reference for future families. Measurement only: existing lamps with exact lampcore charges (untimed counts),
no search, no predictions.

Numbers (fresh, guarded against every held-out and training seed): balanced semiprimes_pq(bits, 96, 9950000 + bits) and
theta 0.20-0.30 (arr_validate's draw) theta_numbers(bits, 9951000 + bits, 96), at 48, 56, 64, 72, 80, 88, 96 bits.

THE BOUND RULE, fixed before measuring (recorded in NOTES with this script's commit; nothing chosen post hoc):
  rho     partition.PRE["rho"] (c 1, b 64), cap arr_price.CAP
  td      partition.PRE["td"] (a 0.5), cap arr_price.CAP; run only where its walk (about p/2 divisions) fits in time:
          balanced at 48 and 56 bits, theta at every size (p <= 29 bits)
  pm1     partition.PRE["pm1"] (B = N^0.199, no stage 2), and the same with stage 2 c = 50 (B2 = 50 B), the analogue of
          ECM's frozen b2 = 50; cap arr_price.CAP. (Disclosed: the family (1) pre-check, dac84be, saw p-1 with stage 2
          near N^0.2 do well on other numbers; the frozen b = 0.199 predates it.)
  ecm     partition.PRE["ecm"] (b1 1.0: B1 from sqrt N; b2 50; up to 10,000 curves), cap arr_price.CAP
  qs      growth_harness.qs_genes(bits): the sealed reference (2'b) genes at 54 / 72 / 84 / 96, interpolated between, held
          at the 54-bit genes below 54; cap partition.QS_CAP
  cfrac   kc 32, bc 1.1 (the accepted genes), cap arr_price.CAP; its lumped cfrac_ops has no ruint or Montgomery price, so
          it is reported under official and op-class only and cannot hold a worst-of frontier
  not run sq, ps (lumped op types with no ruint / Montgomery price: they cannot be on a worst-of frontier either); vl (a
          walk like td); race and arr (composites / families, not reference lamps: arr's known genomes are rho)
Per lamp, map, size and pricing: C = total spent / successes (defined at >= half factored), with a bootstrap interval
(2,000 resamples, random.Random(2026), 2.5-97.5%). Frontier per pricing: the minimum C over the lamps priced under it.
The robust holder at a size: the lamp with the smallest worst-of ratio to the per-pricing frontier, max over
{op-class v1, ruint, Montgomery, scaled gcd} of C_lamp / frontier; it holds the frontier robustly when that is 1.0.
Crossovers: between neighbouring sizes where the robust holder changes, the bits where the two lamps' op-class log2 C
lines cross (linear interpolation).
  python3 frontier.py -> results/frontier.json, stdout"""
import json, math, os, random, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "evolve"))
os.chdir(os.path.join(HERE, "..", "evolve"))
import arr_price as AP
import partition as P
from fastlamps import semiprimes_pq
from growth_harness import qs_genes
from lamps import rand_prime

SIZES, PER = (48, 56, 64, 72, 80, 88, 96), 96
SEEDS = {"balanced": 9950000, "theta": 9951000}
FORBIDDEN = {base + b for base in (9920000, 9925000, 9930000, 9935000, 9946000, 9948000, 9949000) for b in range(40, 129)}
assert not {s + b for s in SEEDS.values() for b in SIZES} & FORBIDDEN, "a held-out, training or reused seed"
WORST = ("opclass_v1", "ruint", "montgomery", "opclass_v1_gcdscaled")
PRS = ("official",) + WORST

def theta_numbers(bits, seed, n, lo=0.20, hi=0.30):
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

def lamps(mp, bits):
    L = {"rho": ([dict(P.PRE["rho"])], AP.CAP),
         "pm1": ([dict(P.PRE["pm1"])], AP.CAP),
         "pm1+s2": ([dict(P.PRE["pm1"], c=50)], AP.CAP),
         "ecm": ([dict(P.PRE["ecm"])], AP.CAP),
         "qs": ([qs_genes(bits)], P.QS_CAP),
         "cfrac": ([{"t": "cfrac", "kc": 32, "bc": 1.1}], AP.CAP)}
    if mp == "theta" or bits <= 56:
        L["td"] = ([dict(P.PRE["td"])], AP.CAP)
    return L

def boot(rs, pr):
    c = AP.per_fact(rs, pr)
    if c is None:
        return None, (None, None)
    rng, n, bs = random.Random(2026), len(rs), []
    for _ in range(2000):
        v = AP.per_fact(rs, pr, [rng.randrange(n) for _ in range(n)])
        if v is not None:
            bs.append(v)
    bs.sort()
    return c, (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if len(bs) > 100 else (None, None)

def main():
    out = {"rule": __doc__.split("THE BOUND RULE")[1].split("Per lamp")[0].strip(), "maps": {}}
    for mp, seed0 in SEEDS.items():
        nums = {b: (semiprimes_pq(b, PER, seed0 + b) if mp == "balanced" else theta_numbers(b, seed0 + b, PER)) for b in SIZES}
        jobs = [(name, b) for b in SIZES for name in lamps(mp, b)]
        with ThreadPoolExecutor(2) as ex:
            res = dict(zip(jobs, ex.map(lambda j: AP.run(*lamps(mp, j[1])[j[0]], nums[j[1]], j[1]), jobs)))
        M = out["maps"][mp] = {"seeds": f"{seed0} + bits", "sizes": {}}
        print(f"\n===== {mp}: {PER} per size, seeds {seed0} + bits", flush=True)
        for b in SIZES:
            row = {}
            for name in lamps(mp, b):
                rs = res[(name, b)]
                bad = sum(r["term"] in AP.BAD_TERMS for r in rs)
                row[name] = {"f": sum(r["ok"] for r in rs) / len(rs), "errors": bad,
                             "C": {pr: boot(rs, pr) for pr in PRS}}
            front = {}
            for pr in PRS:
                cands = {n: v["C"][pr][0] for n, v in row.items() if v["C"][pr][0] and not v["errors"]}
                front[pr] = min(cands.items(), key=lambda kv: kv[1]) if cands else (None, None)
            ratio = {}
            for n, v in row.items():
                r = [v["C"][pr][0] / front[pr][1] if v["C"][pr][0] and front[pr][1] else None for pr in WORST]
                ratio[n] = max(r) if None not in r and not v["errors"] else None
            holder = min((n for n in ratio if ratio[n] is not None), key=lambda n: ratio[n])
            M["sizes"][b] = {"lamps": row, "frontier": front, "worst_of_ratio_to_frontier": ratio, "robust_holder": holder}
            print(f"  {b} bits: frontier holder per pricing " + ", ".join(f"{pr} {front[pr][0]}" for pr in PRS)
                  + f"; robust holder {holder} (worst-of ratio {ratio[holder]:.3f})", flush=True)
            for n, v in row.items():
                c = v["C"]["opclass_v1"]
                print(f"     {n:7s} f {v['f']:.2f}" + (f" ERRORS {v['errors']}" if v["errors"] else "")
                      + (f"; op-class C 2^{math.log2(c[0]):.2f} [2^{math.log2(c[1][0]):.2f}, 2^{math.log2(c[1][1]):.2f}]" if c[0] and c[1][0] else "; op-class C n/a")
                      + f"; worst-of ratio to frontier {('%.3f' % ratio[n]) if ratio[n] else 'n/a'}", flush=True)
        hs = [M["sizes"][b]["robust_holder"] for b in SIZES]
        cross = []
        for (b0, h0), (b1, h1) in zip(zip(SIZES, hs), zip(SIZES[1:], hs[1:])):
            if h0 != h1:
                L = lambda n, b: math.log2(M["sizes"][b]["lamps"][n]["C"]["opclass_v1"][0])
                try:
                    d0, d1 = L(h0, b0) - L(h1, b0), L(h0, b1) - L(h1, b1)
                    x = b0 + (b1 - b0) * d0 / (d0 - d1) if d0 != d1 else None
                except (TypeError, ValueError, KeyError):
                    x = None
                cross.append({"from": h0, "to": h1, "between": [b0, b1], "op_class_crossing_bits": x})
        M["crossovers"] = cross
        print("  robust holders: " + ", ".join(f"{b}: {h}" for b, h in zip(SIZES, hs)))
        print("  crossovers: " + ("; ".join(f"{c['from']} -> {c['to']} between {c['between']}"
                                            + (f", op-class lines cross at ~{c['op_class_crossing_bits']:.1f} bits" if c["op_class_crossing_bits"] else "")
                                            for c in cross) or "none"))
    os.makedirs(os.path.join(HERE, "..", "results"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "..", "results", "frontier.json"), "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
