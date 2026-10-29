"""The value-line lamp's sanity arm (the user's "Seven of Nine" card, stage 2; NOTES, "Cost model: the value-line
lamp", d033b40, written before this code). Untimed counts; not scored; vl is in no deck.
  1. parity: lamps.run (Python) against lampcore --types on vl and td, a = 0.5, on 12 balanced semiprimes at
     20 and 24 bits (seeds 9900020, 9900024): ops, factor, tests, hits and per-type counts must be equal.
  2. counts: td {"t": "td", "a": 0.5} and vl {"t": "vl", "a": 0.5} on the same balanced semiprimes, 24 per size at
     24, 32, 40, 48 bits (seeds 9900000 + bits), lampcore --types. Per size: successes, mean ops, vl / td of mean
     cost per number under op-class v1, ruint, Montgomery and official, and the expectation 2 x price(gcd) /
     price(td_mod) (official: 2.000 exactly per number is checked number by number).
     A ratio <= 1 under any pricing, or official != 2 (p - 1)/(p - 1) per number, is reported as a METER BUG.
  python3 vl_sanity.py -> vl_sanity.json, stdout"""
import sys
sys.argv = sys.argv[:1]
import json, random, subprocess
import lamps, optypes
from lamps import rand_prime
from fastlamps import BIN

PR = optypes.prices()
V1 = {k: v["weight"] for k, v in json.load(open("../opclass/opclass_v1.json"))["classes"].items() if v["weight"]}
PRICINGS = ("opclass_v1", "ruint", "montgomery", "official")
GEN = {"td": [{"t": "td", "a": 0.5}], "vl": [{"t": "vl", "a": 0.5}]}
CAP = 10 ** 12

def price(ty, pr):
    if pr == "official":
        return float(sum(ty.values()))
    if pr == "opclass_v1":
        return float(sum(V1.get(t, 0.0) * n for t, n in ty.items()))
    return optypes.cost(ty, pr, PR)

def unit(t, pr):
    return price({t: 1}, pr)

def semiprimes(bits, n, seed):
    rng, out = random.Random(seed), []
    while len(out) < n:
        p, q = rand_prime(bits // 2, rng), rand_prime(bits - bits // 2, rng)
        if p != q and (p * q).bit_length() == bits:
            out.append((p * q, min(p, q), max(p, q)))
    return out

def core(gen, nums):
    text = json.dumps(gen) + "\n" + str(CAP) + "\n" + "".join(f"{N} {p} {q}\n" for N, p, q in nums)
    out = subprocess.run([BIN, "--types"], input=text, capture_output=True, text=True, check=True).stdout
    res = []
    for l in out.splitlines():
        f = l.split(); i = f.index("T")
        ty = {t: n for t, n in zip(optypes.TYPE_ORDER, map(int, f[i + 1:])) if n}
        res.append({"ops": int(f[0]), "factor": None if f[1] == "miss" else int(f[1]), "tests": int(f[2]),
                    "hits": int(f[3]), "types": ty})
    return res

def py(gen, N):
    lamps.TYPES = True
    ops, d = lamps.run(gen, N, CAP)
    L = lamps.LAST
    return {"ops": ops, "factor": d, "tests": L["tests"], "hits": L["hits"],
            "types": {t: n for t, n in (L.get("types") or {}).items() if n}}

if __name__ == "__main__":
    out = {"parity": {}, "sizes": {}}
    bad = 0
    for bits in (20, 24):
        nums = semiprimes(bits, 12, 9900000 + bits)
        for name, g in GEN.items():
            c = core(g, nums)
            mism = [(N, r, py(g, N)) for (N, _, _), r in zip(nums, c) if py(g, N) != r]
            bad += len(mism)
            out["parity"][f"{bits} {name}"] = len(mism)
            print(f"parity {bits} bits {name}: {len(nums) - len(mism)}/{len(nums)} identical"
                  + (f"; first mismatch {mism[0]}" if mism else ""), flush=True)
    if bad:
        json.dump(out, open("vl_sanity.json", "w"), indent=1)
        print("BLOCKER: parity failed"); sys.exit(3)
    exp = {pr: 2 * unit("gcd", pr) / unit("td_mod", pr) for pr in PRICINGS}
    print("expected vl / td (2 x gcd / td_mod): " + ", ".join(f"{pr} {v:.2f}" for pr, v in exp.items()), flush=True)
    bug = False
    for bits in (24, 32, 40, 48):
        nums = semiprimes(bits, 24, 9900000 + bits)
        r = {name: core(g, nums) for name, g in GEN.items()}
        ok = {name: sum(x["factor"] == p for x, (_, p, _) in zip(rs, nums)) for name, rs in r.items()}
        steps_ok = all(v["ops"] == p - 1 and t["ops"] == (p - 1) // 2 for v, t, (_, p, _) in zip(r["vl"], r["td"], nums))
        ratio = {pr: sum(price(x["types"], pr) for x in r["vl"]) / sum(price(x["types"], pr) for x in r["td"]) for pr in PRICINGS}
        per_num_official = all(v["ops"] == 2 * t["ops"] for v, t in zip(r["vl"], r["td"]))
        flag = any(ratio[pr] <= 1 for pr in PRICINGS) or not per_num_official or not steps_ok
        bug |= flag
        out["sizes"][str(bits)] = {"n": len(nums), "success": ok, "steps_vl_p_minus_1_td_half": steps_ok,
                                   "official_2x_every_number": per_num_official, "ratio": ratio, "expected": exp,
                                   "ratio_over_expected": {pr: ratio[pr] / exp[pr] for pr in PRICINGS},
                                   "mean_ops": {k: sum(x["ops"] for x in v) / len(v) for k, v in r.items()},
                                   "types_vl": sorted({t for x in r["vl"] for t in x["types"]}),
                                   "types_td": sorted({t for x in r["td"] for t in x["types"]})}
        print(f"{bits} bits ({len(nums)} numbers): success td {ok['td']}, vl {ok['vl']}; steps vl = p - 1 and td = (p - 1)/2 on "
              f"every number: {steps_ok}; vl / td " + ", ".join(f"{pr} {ratio[pr]:.3f} (x{ratio[pr] / exp[pr]:.4f} of expected)" for pr in PRICINGS)
              + ("; METER BUG FLAG" if flag else ""), flush=True)
    out["meter_bug"] = bug
    print("meter bug flag: " + ("YES, investigate before anything else" if bug else "none (vl dearer than td under every pricing, official exactly 2x)"))
    json.dump(out, open("vl_sanity.json", "w"), indent=1)
