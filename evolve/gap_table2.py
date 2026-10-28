"""Tables for the second gap run (gap_locate2.json; information only). Common phases as gap_table.py (the same YAFU
function placement); "change" = the card now minus the card in Experiment 1 (gap_locate.json, before alloc-once);
then the confirm + lp split and YAFU's check_sieve_val_tiny by function and callee. M Ir per number, balanced band.
  python3 gap_table2.py -> gap_table2.out (stdout)"""
import json
CARD = {"factor base": ["mult", "fb"], "poly set-up": ["setup", "gray"], "sieve": ["sieve", "resieve"], "scan": ["scan"],
        "confirm + lp": ["confirm", "lp_ledger"], "la + sqrt": ["solve"],
        "unplaced": ["other (in lamp_qs / sieve_source)", "line 0"]}
def yphase(f):                                              # as gap_table.py (copied: that script prints on import)
    if f in ("init_fb_tiny", "find_multiplier_tiny", "legendre_16", "sqrtModP_16", "powm_16"):
        return "factor base"
    if f in ("find_poly_a", "find_first_poly_b", "find_next_poly_b", "modinv_16") or f.startswith("sieve_next_poly"):
        return "poly set-up"
    if f.startswith("fill_sieve_block") or f == "memset":
        return "sieve"
    if f.startswith("mark_sieve_block"):
        return "scan"
    if f == "check_sieve_val_tiny":
        return "confirm + lp"
    if f in ("solve_linear_system_tiny", "find_factors_tiny"):
        return "la + sqrt"
    return "unplaced"
G2, G1 = json.load(open("gap_locate2.json")), json.load(open("gap_locate.json"))
N = 80
m = lambda x: x / N / 1e6
for bits, r in G2["sizes"].items():
    c, y, c1 = r["card"], r["yafu"], G1[bits]["card"]
    yir = {}
    for f, ir in y["Ir"].items():
        yir[yphase(f)] = yir.get(yphase(f), 0) + ir
    gap = m(c["attributed"] - y["attributed"])
    print(f"== {bits} bits, balanced band: M Ir per number (callgrind). Card time shares: "
          + ("see gap_locate2.json" if G2["time_shares_measured"] else "not measured (on battery; conditions not met)"))
    print(f"  {'phase':14s} {'card now':>9s} {'YAFU':>7s} {'card-YAFU':>10s} {'share of gap':>13s} {'card before':>12s} {'change':>8s}")
    for p, regs in CARD.items():
        ci = m(sum(c["Ir"].get(x, 0) for x in regs)); cb = m(sum(c1["Ir"].get(x, 0) for x in regs)); yi = m(yir.get(p, 0))
        print(f"  {p:14s} {ci:9.3f} {yi:7.3f} {ci - yi:10.3f} {100 * (ci - yi) / gap:12.1f}% {cb:12.3f} {ci - cb:+8.3f}")
    print(f"  {'total':14s} {m(c['attributed']):9.3f} {m(y['attributed']):7.3f} {gap:10.3f} {'100.0%':>13s} "
          f"{m(c1['attributed']):12.3f} {m(c['attributed'] - c1['attributed']):+8.3f}")
    print(f"  -- confirm + lp, by sub-step (card; calls into other functions included at their call site):")
    tot_cl = sum(c["Ir"].get(x, 0) for x in ("confirm", "lp_ledger"))
    for s, ir in sorted(c["sub_Ir"].items(), key=lambda kv: -kv[1]):
        top = sorted(c["sub_calls"].get(s, {}).items(), key=lambda kv: -kv[1])[:2]
        print(f"     {s:36s} {m(ir):7.3f} ({100 * ir / tot_cl:5.1f}%)" + (("; calls: " + ", ".join(f"{k[:44]} {m(v):.3f}" for k, v in top)) if top else ""))
    rest = tot_cl - sum(c["sub_Ir"].values())
    print(f"     {'(confirm / lp lines outside the sub-steps)':36s} {m(rest):7.3f} ({100 * rest / tot_cl:5.1f}%)")
    yc = r["yafu_check"]; ytot = sum(yc["own_by_innermost_fn"].values()) + sum(yc["calls_by_callee"].values())
    print(f"  -- YAFU check_sieve_val_tiny, {m(ytot):.3f} M per number:")
    for f, ir in sorted(yc["own_by_innermost_fn"].items(), key=lambda kv: -kv[1]):
        if ir / ytot >= 0.01:
            print(f"     own code, {f:28s} {m(ir):7.3f} ({100 * ir / ytot:5.1f}%)")
    for f, ir in sorted(yc["calls_by_callee"].items(), key=lambda kv: -kv[1]):
        if ir / ytot >= 0.01:
            print(f"     call {f:33s} {m(ir):7.3f} ({100 * ir / ytot:5.1f}%)")
