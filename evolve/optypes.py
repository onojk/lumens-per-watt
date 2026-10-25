"""Per-type op counts (NOTES.md, "Op-price calibration"): the split of a run's official ops
into the types calibrate.py prices. Shared by calibrate.py and race.py.

  rho:  mul = ops - tests, gcd = tests (one luck-meter test per gcd)
  pm1:  the same split: its charges are bit_length(p^e) multiplies per prime power and one
        gcd at the end (one test); its prime generation is not charged
  td:   td_mod = ops, one N mod d per divisor (its divisor stepping is not charged)
  ecm:  setup_mul, setup_euclid_N (each curve's Euclid steps, recomputed from its sigma),
        mul (stage 1 + stage 2), gcd
  qs:   the trace split of qs_counts below
  other lamps (sq, ps, cfrac): one unpriced type, "<lamp>_ops" (no price mapping yet)

Every split sums to the run's ops exactly. For a run stopped mid-way (a race side torn down
when the other side wins), the split is exact for every finished unit; for qs, the unit in
progress (one A's 2s full-price setup ops, or one candidate's 2 confirm ops) can be
attributed to the small type instead of the full one; for rho, a gcd charged just before
the stop but not yet tested counts as a multiply (1 op). The sum is still exact.
"""

def qs_counts(tr):
    o = tr["ops"]
    ats = tr["attempts"]
    setup_full = sum((a["s"] - 1) * a["combos"] + (a["s"] + 1) * a.get("od_cands", 0) + 2 * a["s"] * a["a_count"] for a in ats)
    setup_euc = sum(st for a in ats for _, _, st in a["inv"])
    scans = sum(2 * p["M"] + 1 for a in ats for p in a["polys"])
    confirm_full = sum(2 * len(a["cands"]) for a in ats)
    sqrt_gcd = sum(d["gcd_steps"] for a in ats for d in a["deps"])
    lp_full = sum(a["lp"]["combos"] for a in ats if "lp" in a)
    return {"mult": o.get("mult", 0), "fb": o.get("fb", 0),
            "setup_full": setup_full, "setup_euclid": setup_euc,
            "setup_small": o.get("setup", 0) - setup_full - setup_euc,
            "sieve_update": o.get("sieve", 0) - scans, "sieve_scan": scans,
            "confirm_full": confirm_full, "confirm_td": o.get("confirm", 0) - confirm_full,
            "la": o.get("la", 0), "sqrt_mul": o.get("sqrt", 0) - sqrt_gcd, "sqrt_gcd": sqrt_gcd,
            "lp_full": lp_full, "lp_small": o.get("lp", 0) - lp_full, "check": o.get("check", 0)}

def ecm_setup_steps(N, sigma):
    """(Euclid steps of den^-1 mod N, whether den is invertible) for a Suyama curve."""
    u, v = (sigma * sigma - 5) % N, 4 * sigma % N
    den = 16 * u ** 3 * v % N
    r0, r1, steps = N, den, 0
    while r1:
        r0, r1 = r1, r0 % r1
        steps += 1
    return steps, r0 == 1

def ecm_counts(tr, N):
    """A finished curve's setup is 10 multiplies, its Euclid steps (one charge), and one
    more multiply when den is invertible. For a curve still in setup (a side torn down),
    its steps count only if that charge was made: the rest of the setup phase shows it."""
    o = tr["ops"]
    setup = o.get("ecm_setup", 0)
    steps = done = 0
    for cv in tr["curves"]:
        st, inv = ecm_setup_steps(N, cv["sigma"])
        if cv["end"] is not None:
            steps += st
            done += 10 + st + (inv and cv["end"] not in ("setup factor", "degenerate"))
        elif setup - done >= 10 + st:
            steps += st
    return {"setup_mul": setup - steps, "setup_euclid_N": steps,
            "mul": o.get("ecm_s1", 0) + o.get("ecm_s2", 0), "gcd": o.get("ecm_gcd", 0)}

def rho_counts(ops, tests):
    return {"mul": ops - tests, "gcd": tests}

# The fixed type order of lampcore's --types output (lampcore/src/main.rs, TYPE_NAMES).
TYPE_ORDER = ["mult", "fb", "setup_full", "setup_euclid", "setup_small", "sieve_update", "sieve_scan",
              "confirm_full", "confirm_td", "la", "sqrt_mul", "sqrt_gcd", "lp_full", "lp_small", "check",
              "setup_mul", "setup_euclid_N", "mul", "gcd", "td_mod", "sq_ops", "ps_ops", "cfrac_ops"]

def prices(path="calibrate.json"):
    """Per pricing, the price of each type: official 1 for every op; ruint and Montgomery from
    calibrate.json, the median of the three P-core runs (the price table lives there only)."""
    import json
    cal = json.load(open(path))
    out = {"official": None}
    for ref in ("ruint", "montgomery"):
        names = cal["prices"][f"{ref} P1"]
        out[ref] = {t: sorted(cal["prices"][f"{ref} {r}"][t] for r in ("P1", "P2", "P3"))[1] for t in names}
    return out

def cost(counts, pricing, pr):
    """Cost of one run's per-type counts under a pricing; raises on an unpriced type."""
    if pricing == "official":
        return float(sum(counts.values()))
    missing = [t for t, n in counts.items() if n and t not in pr[pricing]]
    if missing:
        raise KeyError(f"unpriced op types under {pricing}: {missing}")
    return float(sum(pr[pricing][t] * n for t, n in counts.items() if n))

def robust(runs, ref_runs, pr=None):
    """(c) fitness: per pricing, the mean cost of `runs` over the mean cost of `ref_runs` (the
    reference genome on the same numbers); the fitness is the max over the three pricings.
    runs, ref_runs: lists of per-type count dicts. Returns (fitness, {pricing: ratio})."""
    pr = pr or prices()
    ratios = {P: (sum(cost(c, P, pr) for c in runs) / len(runs)) / (sum(cost(c, P, pr) for c in ref_runs) / len(ref_runs))
              for P in ("official", "ruint", "montgomery")}
    return max(ratios.values()), ratios

def per_type(stage, tr, ops, tests, N):
    t = stage["t"]
    if t == "qs":
        c = qs_counts(tr)
    elif t == "ecm":
        c = ecm_counts(tr, N)
    elif t in ("rho", "pm1"):
        c = rho_counts(ops, tests)
    elif t == "td":
        c = {"td_mod": ops}
    else:
        c = {f"{t}_ops": ops}
    assert sum(c.values()) == ops, ("per-type split does not add up", t, c, ops)
    return c
