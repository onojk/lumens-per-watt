"""Report of an arrangement-v1 search (the search record $LPW_SEARCH_OUT/arr_search_<map>.json, from arr_search.py).
Not a judge file and not a verdict: it reads the search's own training-map records (no lampcore runs, no new numbers)
and prints what the user asked to see beside each genome. Verdicts come only from the sealed harness, arr_validate.py.

Per reported genome (every layout x rule pair's best; the overall best marked):
  - the search fitness (worst-of G_rho on the training numbers, the cost guard) or why it was dropped;
  - G_rho per pricing on the training numbers (point values) and the robust cost ratio against rho per size;
  - the op-count growth slope over the chord (least squares of log2 median official ops at 48, 64, 80, the
    harness's definition; and over all five sizes), beside rho's on the same numbers (the user's request, Oct 29);
  - FLAG, bin compare (the user's, Oct 29): a bin-compare genome whose cost grows faster than rho's (its op-count
    slope, or its op-class C(80) / C(48), above rho's), even if it does well at the bottom of the range;
  - the Fermat split at the chord's bottom size (the user's ruling, Oct 30): the numbers where Fermat needs no more
    steps than sqrt(p) ("Fermat-easy": (p + q)/2 - ceil(sqrt N) + 1 <= sqrt p, explore/close_factors.py's count)
    and the rest; on each, the candidate's and rho's op-class cost per factorisation (total spent / successes) and
    mean spent per number;
  - FLAG, Fermat (the user's, Oct 30): the genome has an advantage over rho at that size, adv = 1 - C_cand / C_rho
    (op-class cost per factorisation over all the size's numbers) > 0, and it is mostly on the Fermat-easy subset:
    on the rest alone, adv_rest = 1 - C_cand,rest / C_rho,rest is below adv / 2 (removing the easy numbers takes away
    more than half of the advantage). Not computed when C_cand is not defined (fewer than half factored);
  - the class: "rediscovered known lamp" (exponent, or map with Floyd / Brent), rho-shaped (Q1: map + Floyd / Brent,
    slope 0.20-0.30), the map degree d (Q6).
  python3 arr_report.py SEARCH_JSON"""
import json, math, statistics, sys

WORST = ("opclass_v1", "ruint", "montgomery", "opclass_v1_gcdscaled")

def per_fact(rs, pr):
    s = sum(r["ok"] for r in rs)
    if not rs or s < len(rs) // 2 or any(r["cost"][pr] is None for r in rs):
        return None
    return sum(r["cost"][pr] for r in rs) / s

def period(R, a, b, pr):
    if a not in R or b not in R:
        return None
    ca, cb = per_fact(R[a], pr), per_fact(R[b], pr)
    return (b - a) / math.log2(cb / ca) if ca and cb and cb > ca else None

def slope(R, sizes):
    if any(s not in R or not R[s] for s in sizes):
        return None
    xs, ys = list(sizes), [math.log2(max(1, statistics.median(r["ops"] for r in R[s]))) for s in sizes]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

def fermat_easy(N, p, q):
    r = math.isqrt(N)
    c = r if r * r == N else r + 1
    return (p + q) // 2 - c + 1 <= math.isqrt(p)

def split_cost(rs, mask):
    sub = [r for r, m in zip(rs, mask) if m]
    s = sum(r["ok"] for r in sub)
    tot = sum(r["cost"]["opclass_v1"] for r in sub)
    return {"n": len(sub), "ok": s, "per_fact": tot / s if s else None, "mean_spent": tot / len(sub) if sub else None,
            "total": tot}

def f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}" if isinstance(x, float) else str(x)

def main(path):
    d = json.load(open(path))
    sizes = list(d["sizes"])
    a, b = d["chord"]
    mid = d["screen"]
    key = lambda R: {int(k): v for k, v in R.items()}
    rho = key(d["rho"]["records"])
    nums = {int(k): [tuple(map(int, x)) for x in v] for k, v in d["numbers"].items()}
    easy = [fermat_easy(*x) for x in nums[a]]
    rho_slope, rho_slope5 = slope(rho, (a, mid, b)), slope(rho, sizes)
    print(f"search {path}: map {d['map']}, sizes {sizes}, {d['per']} per size, seeds {d['seeds']}, "
          f"{d['evaluations']} evaluations; budget {d['budget']['x_rho_max']} x rho's max per number")
    print(f"rho alone: successes " + str({s: sum(r['ok'] for r in rho[s]) for s in sizes})
          + f"; op-count slope {f(rho_slope)} per bit ({a}/{mid}/{b}), {f(rho_slope5)} (all sizes); op-class period "
          + f(period(rho, a, b, "opclass_v1")))
    rs_e, rs_r = split_cost(rho[a], easy), split_cost(rho[a], [not e for e in easy])
    print(f"Fermat split at {a} bits: {sum(easy)} of {len(easy)} training numbers Fermat-easy (Fermat steps <= sqrt p); "
          f"rho op-class per factorisation: easy {f(rs_e['per_fact'], 0)}, rest {f(rs_r['per_fact'], 0)}")
    out = {}
    order = sorted(d["pairs"], key=lambda n: (d["pairs"][n]["fitness"] is None, -(d["pairs"][n]["fitness"] or 0)))
    for name in order:
        e = d["pairs"][name]
        R = key(e["records"])
        st = e["genome"][0]
        lay, rule = st["layout"]["kind"], st["detect"]["kind"]
        known = lay == "exponent" or (lay == "map" and rule in ("floyd", "brent"))
        sl, sl5 = slope(R, (a, mid, b)), slope(R, sizes)
        rec = {"genome": e["genome"], "fitness": e["fitness"], "slope": sl, "slope_all": sl5}
        print(f"\n== {name}{'  (BEST OVERALL)' if name == d['best'] else ''}: {json.dumps(e['genome'])}")
        print(f"   class: {'rediscovered known lamp' if known else 'candidate'}"
              + (f"; d = {st['layout'].get('d', 2)}" if lay == "map" else "")
              + ("; rho-shaped (Q1)" if known and lay == "map" and sl is not None and 0.20 <= sl <= 0.30 else ""))
        s = e["search"]
        print(f"   search fitness (worst-of G_rho {a}-{b}, cost guard): {f(e['fitness'])}"
              + (f"; dropped at {s['dropped_at']} bits: {s.get('why', '')}" if s.get("dropped_at") else ""))
        print(f"   successes " + str({k: sum(r['ok'] for r in v) for k, v in sorted(R.items())}))
        print(f"   op-count slope {f(sl)} per bit ({a}/{mid}/{b}; rho {f(rho_slope)}), {f(sl5)} over all sizes (rho {f(rho_slope5)})")
        g = {p: (lambda pc, pr: pc / pr if pc and pr else None)(period(R, a, b, p), period(rho, a, b, p))
             for p in ("opclass_v1", "ruint", "montgomery", "official", "opclass_v1_gcdscaled")}
        rec["g_rho"] = g
        print(f"   G_rho {a}-{b} (training, point): " + "; ".join(f"{p} {f(v)}" for p, v in g.items())
              + f"; worst-of {f(None if None in [g[p] for p in WORST] else min(g[p] for p in WORST))}")
        rr = {}
        for k in sorted(R):
            v = [(lambda x, y: x / y if x and y else None)(per_fact(R[k], p), per_fact(rho[k], p)) for p in WORST]
            rr[k] = None if None in v else max(v)
        rec["ratio"] = rr
        print(f"   robust cost ratio vs rho: " + ", ".join(f"{k}: {f(v)}" for k, v in rr.items()))
        if a in R and len(R[a]) == len(easy):
            ce, cr = split_cost(R[a], easy), split_cost(R[a], [not x for x in easy])
            c_all, r_all = per_fact(R[a], "opclass_v1"), per_fact(rho[a], "opclass_v1")
            adv = 1 - c_all / r_all if c_all and r_all else None
            adv_rest = 1 - cr["per_fact"] / rs_r["per_fact"] if cr["per_fact"] and rs_r["per_fact"] else None
            flag = adv is not None and adv > 0 and (adv_rest is None or adv_rest < adv / 2)
            rec["fermat"] = {"easy": ce, "rest": cr, "adv": adv, "adv_rest": adv_rest, "flag": flag}
            print(f"   Fermat split at {a}: op-class per factorisation easy {f(ce['per_fact'], 0)} (rho {f(rs_e['per_fact'], 0)}), "
                  f"rest {f(cr['per_fact'], 0)} (rho {f(rs_r['per_fact'], 0)}); advantage over rho {f(adv)} overall, "
                  f"{f(adv_rest)} without the easy subset" + ("; FLAG: advantage mostly on the Fermat-easy subset" if flag else ""))
        else:
            print(f"   Fermat split at {a}: not available (the genome was not run on all {a}-bit numbers)")
        if rule == "bins":
            pc, pr = period(R, a, b, "opclass_v1"), period(rho, a, b, "opclass_v1")
            faster = (sl is not None and rho_slope is not None and sl > rho_slope) or (pc is not None and pr is not None and pc < pr)
            undefined = sl is None and pc is None
            rec["flag_bins"] = faster
            print("   FLAG: bin-compare genome whose cost grows faster than rho's" if faster else
                  f"   bin compare: growth {'not measurable over the chord (dropped)' if undefined else 'not faster than rho'}")
        out[name] = rec
    print("\nREPORT " + json.dumps(out, default=str))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
