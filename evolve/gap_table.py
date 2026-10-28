"""The common-phase table for Experiment 1 (from gap_locate.json; information only). The card's --phasetime regions and
YAFU's tinysiqs functions grouped into the same phases, by each function's own source comment (cofactorize_siqs.c):
  factor base       card mult, fb             YAFU init_fb_tiny, find_multiplier_tiny, legendre_16, sqrtModP_16, powm_16
  poly set-up       card setup, gray          YAFU find_poly_a, find_first_poly_b, find_next_poly_b, modinv_16, sieve_next_poly*
  sieve             card sieve, resieve       YAFU fill_sieve_block*, memset (the block clear)
  scan              card scan                 YAFU mark_sieve_block* ("find the offsets corresponding to relations")
  confirm + lp      card confirm, lp_ledger   YAFU check_sieve_val_tiny
  la + sqrt         card solve                YAFU solve_linear_system_tiny, find_factors_tiny ("MPQS square root phase")
  unplaced          card "other", "line 0"    YAFU anything else
  Then the card's library Ir by region (gap_library.json, from gap_locate.card_library_by_region on the same callgrind files).
  python3 gap_table.py -> gap_table.out (stdout)"""
import json
G = json.load(open("gap_locate.json"))
CARD = {"factor base": ["mult", "fb"], "poly set-up": ["setup", "gray"], "sieve": ["sieve", "resieve"], "scan": ["scan"],
        "confirm + lp": ["confirm", "lp_ledger"], "la + sqrt": ["solve"],
        "unplaced": ["other (in lamp_qs / sieve_source)", "line 0"]}
def yphase(f):
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
N = 80
for bits, r in G.items():
    c, y, ns = r["card"], r["yafu"], r["card_phasetime_ns"]
    tns = sum(ns.values())
    yir = {}
    yset = {}
    for f, ir in y["Ir"].items():
        p = yphase(f); yir[p] = yir.get(p, 0) + ir; yset.setdefault(p, []).append(f)
    print(f"== {bits} bits, balanced band: M Ir per number (callgrind); card time share (--phasetime)")
    print(f"  {'phase':14s} {'card':>8s} {'YAFU':>8s} {'card-YAFU':>10s} {'share of gap':>13s} {'card time share':>16s}")
    ctot, ytot = c["attributed"] / N / 1e6, y["attributed"] / N / 1e6
    gap = ctot - ytot
    for p, regs in CARD.items():
        ci = sum(c["Ir"].get(x, 0) for x in regs) / N / 1e6
        yi = yir.get(p, 0) / N / 1e6
        ts = sum(ns.get(x, 0) for x in regs) / tns * 100
        print(f"  {p:14s} {ci:8.3f} {yi:8.3f} {ci - yi:10.3f} {100 * (ci - yi) / gap:12.1f}% {ts:15.1f}%")
    print(f"  {'total':14s} {ctot:8.3f} {ytot:8.3f} {gap:10.3f} {'100.0%':>13s}")
    unpl = [f for f in yset.get("unplaced", [])]
    if unpl:
        print(f"  YAFU unplaced functions: {', '.join(sorted(unpl))}")
    # SIMD totals over each side's own main-object instructions
    for side, d in (("card", c["simd_own"]), ("YAFU", y["simd_own"])):
        t = {}
        for v in d.values():
            for k, x in v.items():
                t[k] = t.get(k, 0) + x
        if side == "card":
            for k, x in c["simd_callees_all"].items():
                t[k] = t.get(k, 0) + x
        tt = sum(t.values())
        print(f"  {side} own main-object Ir: {tt / N / 1e6:.3f} M per number; 256-bit {100 * t.get('256-bit', 0) / tt:.2f}%, "
              f"128-bit packed {100 * t.get('128-bit packed', 0) / tt:.2f}%, scalar FP in xmm {100 * t.get('scalar FP in xmm', 0) / tt:.2f}%"
              + (f"; library (GMP, libc; not classified) {sum(y['library_Ir'].values()) / N / 1e6:.3f} M per number" if side == "YAFU" else ""))
L = json.load(open("gap_library.json"))
print("== the card's library Ir by region (M per number; allocation split by callee-wide fractions)")
for bits, r in L.items():
    kinds = sorted({k for v in r.values() for k in v})
    print(f"  {bits} bits: totals " + ", ".join(f"{k} {sum(v.get(k, 0) for v in r.values()) / N / 1e6:.3f}" for k in kinds))
    for reg, v in sorted(r.items(), key=lambda kv: -sum(kv[1].values())):
        if sum(v.values()) / N / 1e6 >= 0.02:
            print(f"    {reg:16s} " + ", ".join(f"{k} {x / N / 1e6:.3f}" for k, x in sorted(v.items(), key=lambda kv: -kv[1])))
