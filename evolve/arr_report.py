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
G-37 (Grok's forecast, sealed in predictions/arrangement-v1.md; computed here, after the search, never by the judge):
  - the ranking: the search record's evaluated genomes with a defined training G_rho (op-class v1, the forecast's
    pricing; a genome the search dropped, by the cost guard or for too few successes, has none), excluding any
    invalidated by the early-exit audit; the 10 highest, ties broken on the genome's sorted JSON (the smaller first;
    the user's ruling, Oct 30: never on evaluation order; arrangement-v1's G-37 had no tie at its boundary);
  - the numbers: the held-out 48-bit balanced validation numbers, semiprimes_pq(48, 48, 9930048) (the harness's
    draw), run here for each ranked genome and for rho alone (cap arr_price.CAP); a genome whose runs here hit an
    error or abort is excluded and listed (the denominator printed is the count actually measured);
  - the split: Fermat-easy = Fermat steps <= sqrt(p) (as above); its size is printed beside the result;
  - "cost vs rho on a subset" = the MEAN op-class v1 cost per number of the genome on that subset (total spent,
    censored runs included, / numbers) divided by rho's mean on the same numbers; the aggregate is the mean, and
    nothing else (the user's pre-run note);
  - a genome counts when (cost vs rho, easy) <= 0.5 x (cost vs rho, rest); G-37's value = count / genomes measured.
D-44 (DeepSeek's forecast, sealed; computed here, never by the judge):
  - the genome: rank 1 by training G_rho among valid genomes = the search record's "best" (the search's own ranking:
    worst-of G_rho under the cost guard); if the op-class-only rank 1 differs, it is printed beside (not scored);
  - the numbers: the held-out balanced validation numbers at 64 and 80 bits, semiprimes_pq(bits, 48, 9930000 + bits)
    (the harness's draw), the genome and rho alone (arr_price.RHO) each run here (cap arr_price.CAP); an error or abort
    in either arm makes D-44 INVALID (the early-exit audit);
  - the ratio: C_cand / C_rho at each size, op-class v1, C = total cost over successes (arr_price.per_fact); the band
    average = the geometric mean of the two; interval: paired bootstrap over both sizes (one index list per size,
    shared by both arms), 10,000 resamples, random.Random(2026), 2.5-97.5%;
  - the outcome: "falsified" if the band average is < 0.69 or > 1.27, otherwise "not falsified".
The search record is proposer output, read like a genome file: O_NOFOLLOW, a regular file, at most 64 MiB, strict
UTF-8, no NaN / Infinity or duplicate keys; every genome taken from it must pass the harness's own genome checks
(arr_validate._parse) or is refused.
  python3 arr_report.py SEARCH_JSON [--test-seed S]   (--test-seed: G-37 on semiprimes_pq(48, 48, S), for code checks;
                                                        never a held-out seed; D-44 then on S + 16 and S + 32)"""
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

def read_record(path):
    """The search record, read as untrusted input (see the module doc)."""
    import os, stat
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > (64 << 20):
            raise SystemExit(f"REFUSED: {path} is not a regular file of at most 64 MiB")
        data = b""
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            data += chunk
    finally:
        os.close(fd)
    def no_const(c):
        raise ValueError(f"constant {c}")
    def no_dupes(pairs):
        if len({k for k, _ in pairs}) != len(pairs):
            raise ValueError("duplicate keys")
        return dict(pairs)
    try:
        return json.loads(data.decode("utf-8"), parse_constant=no_const, object_pairs_hook=no_dupes)
    except (UnicodeDecodeError, ValueError, RecursionError) as e:
        raise SystemExit(f"REFUSED: {path}: {str(e)[:80]}")

def gkey(g):
    """The tie-break key (the user's ruling, Oct 30): the genome's sorted JSON."""
    return json.dumps(g, sort_keys=True)

def checked(genome):
    """A genome from the record, through the harness's own checks (one arr stage, valid genes) or refused."""
    import arr_validate as AV
    return AV._parse("record", json.dumps(genome).encode())[1]

def main(path):
    d = read_record(path)
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
    if "evaluated" in d:
        out["_g37"] = g37(d, TEST_SEED or 9930048)
        out["_d44"] = d44(d, TEST_SEED)
    else:
        print("\nG-37: not computed (this search record keeps no evaluated-genome list)")
    print("\nREPORT " + json.dumps(out, default=str))

def g37(d, seed=9930000 + 48):
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import arr_price as AP
    from fastlamps import semiprimes_pq
    ranked = [dict(e, genome=checked(e["genome"])) for e in d["evaluated"]
              if not e.get("invalid") and (e.get("g_rho") or {}).get("opclass_v1") is not None]
    ranked = sorted(ranked, key=lambda e: (-e["g_rho"]["opclass_v1"], gkey(e["genome"])))[:10]
    nums = semiprimes_pq(48, 48, seed)
    easy = [fermat_easy(*x) for x in nums]
    rho = AP.run(AP.RHO, AP.CAP, nums, 48)
    if any(r["term"] in AP.BAD_TERMS for r in rho):
        print("\nG-37: NOT COMPUTED: rho's run on the held-out 48-bit numbers hit an error or abort")
        return {"error": "rho"}
    mean = lambda rs, m: sum(r["cost"]["opclass_v1"] for r, k in zip(rs, m) if k) / sum(m)
    rest = [not x for x in easy]
    rows, excluded = [], []
    for e in ranked:
        rs = AP.run(e["genome"], AP.CAP, nums, 48)
        if any(r["term"] in AP.BAD_TERMS for r in rs):
            excluded.append(e["genome"])
            continue
        re_, rr = mean(rs, easy) / mean(rho, easy), mean(rs, rest) / mean(rho, rest)
        rows.append({"genome": e["genome"], "g_rho_train_opclass": e["g_rho"]["opclass_v1"], "vs_rho_easy": re_,
                     "vs_rho_rest": rr, "counts": re_ <= 0.5 * rr})
    k = sum(r["counts"] for r in rows)
    print(f"\nG-37 ({'held-out' if seed == 9930048 else 'TEST (not held-out)'} 48-bit numbers, seed {seed}, 48; Fermat-easy subset {sum(easy)} of {len(easy)}; aggregate: mean op-class v1 "
          f"cost per number vs rho's on the same numbers):")
    for r in rows:
        print(f"   {json.dumps(r['genome'])}: training G_rho (op-class) {r['g_rho_train_opclass']:.4f}; vs rho easy "
              f"{r['vs_rho_easy']:.4f}, rest {r['vs_rho_rest']:.4f}" + ("; counts (easy <= 0.5 x rest)" if r["counts"] else ""))
    for g in excluded:
        print(f"   EXCLUDED (early-exit audit on the held-out runs): {json.dumps(g)}")
    print(f"G-37 value: {k} / {len(rows)} = {k / len(rows):.2f}" if rows else "G-37 value: no genome measured")
    return {"easy": sum(easy), "n": len(easy), "rows": rows, "excluded": excluded, "count": k, "measured": len(rows),
            "value": k / len(rows) if rows else None}

def d44(d, test=None):
    import random
    import arr_price as AP
    from fastlamps import semiprimes_pq
    from concurrent.futures import ThreadPoolExecutor
    best = checked(d["pairs"][d["best"]]["genome"])
    ranked = [e for e in d["evaluated"] if not e.get("invalid") and (e.get("g_rho") or {}).get("opclass_v1") is not None]
    top_op = min(ranked, key=lambda e: (-e["g_rho"]["opclass_v1"], gkey(e["genome"])))["genome"] if ranked else None
    seeds = {64: test + 16, 80: test + 32} if test else {64: 9930064, 80: 9930080}
    nums = {b: semiprimes_pq(b, 48, seeds[b]) for b in (64, 80)}
    jobs = [(g, b) for g in ("cand", "rho") for b in (64, 80)]
    with ThreadPoolExecutor(2) as ex:
        res = dict(zip(jobs, ex.map(lambda j: AP.run(best if j[0] == "cand" else AP.RHO, AP.CAP, nums[j[1]], j[1]), jobs)))
    bad = [j for j in jobs if any(r["term"] in AP.BAD_TERMS for r in res[j])]
    label = "held-out" if not test else "TEST (not held-out)"
    print(f"\nD-44 ({label} balanced numbers at 64 and 80 bits, seeds {seeds}, 48 each; op-class v1; band average = geometric "
          f"mean of C_cand / C_rho at 64 and 80):")
    print(f"   genome (rank 1, the search's ranking): {json.dumps(best)}")
    if top_op is not None and json.dumps(top_op, sort_keys=True) != json.dumps(best, sort_keys=True):
        print(f"   (rank 1 by op-class-only training G_rho differs, not scored: {json.dumps(top_op)})")
    if bad:
        print(f"   D-44 INVALID (early-exit audit): an error or abort in {bad}")
        return {"invalid": bad}
    def band(ix):
        r = []
        for b in (64, 80):
            c, h = AP.per_fact(res[("cand", b)], "opclass_v1", ix and ix[b]), AP.per_fact(res[("rho", b)], "opclass_v1", ix and ix[b])
            if not c or not h:
                return None
            r.append(c / h)
        return math.sqrt(r[0] * r[1])
    per = {b: (lambda c, h: c / h if c and h else None)(AP.per_fact(res[("cand", b)], "opclass_v1"),
                                                         AP.per_fact(res[("rho", b)], "opclass_v1")) for b in (64, 80)}
    rng, bs = random.Random(2026), []
    for _ in range(10000):
        ix = {b: [rng.randrange(48) for _ in range(48)] for b in (64, 80)}
        v = band(ix)
        if v is not None:
            bs.append(v)
    bs.sort()
    v = band(None)
    ci = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if bs else (None, None)
    succ = {k: sum(r["ok"] for r in rs) for k, rs in res.items()}
    out = "not defined" if v is None else ("falsified" if v < 0.69 or v > 1.27 else "not falsified")
    print(f"   successes {succ}; C_cand / C_rho: 64 {f(per[64], 4)}, 80 {f(per[80], 4)}")
    print(f"   D-44 band average {f(v, 4)} [{f(ci[0], 4)}, {f(ci[1], 4)}] ({len(bs)} resamples defined); forecast 0.98, range "
          f"0.69-1.27: {out}")
    return {"genome": best, "ratios": per, "band": v, "ci": ci, "outcome": out, "successes": {f"{a} {b}": n for (a, b), n in succ.items()}}

TEST_SEED = None

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--test-seed" in a:                       # code checks only: G-37 on numbers that are not held out
        i = a.index("--test-seed")
        TEST_SEED = int(a[i + 1])
        HELD_OUT = {9930000 + b for b in (48, 64, 80, 84, 96)} | {9935000 + b for b in (64, 80)}
        assert not {TEST_SEED, TEST_SEED + 16, TEST_SEED + 32} & HELD_OUT, "a test seed must not be a held-out seed"
        a = a[:i] + a[i + 2:]
    if len(a) != 1:
        sys.exit(__doc__)
    import os
    main(os.path.abspath(a[0]))
