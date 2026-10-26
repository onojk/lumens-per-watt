"""Information only (user's decision 3, Oct 25; no card change): what qs's setup consists of and each
part's share of total qs cost. New reference genes as qs alone (corrected card, kset), Python traces on
3 balanced and 3 band-24 map numbers per size. Every charge is attributed to its call site by wrapping
Charger.charge (instrumentation; counts unchanged), then priced by its type.
  python3 setupshare.py -> setupshare.out (stdout)
"""
import json, inspect, collections
import partition as P, sizescale as SS, sizescale2 as S2, optypes, qs, lamps, ledger
sealed = json.load(open("sizescale_k_sealed.json"))
PR = P.prices()
ATTR = collections.Counter()
_orig = ledger.Charger.charge
def charge(self, phase, n):
    if phase in ("mult", "fb", "setup"):
        st = inspect.stack()
        fn = st[1].function; line = st[1].lineno
        if fn == "euclid_inv" or (len(st) > 2 and st[2].function == "euclid_inv"):
            caller = st[2] if fn == "euclid_inv" else st[3]
            cat = "inverse of A mod each sieved prime" if "for p in sieved" in (caller.code_context or [""])[0] or caller.lineno > 238 else "inverses for B_l (A's primes)"
            cat = "euclid|" + cat
        elif phase == "mult":
            cat = "small|multiplier scoring (KS) and ranking"
        elif phase == "fb":
            cat = "small|factor base (Legendre and Tonelli-Shanks)"
        elif fn in ("a_on_demand", "_a_pass") or 120 <= line <= 210:
            cat = "asel|A selection (on-demand search, pool sort, forming A)"
        elif 225 <= line <= 237:
            cat = "small|B_l per A (A/q, gamma)"
        elif 240 <= line <= 252:
            cat = "small|per-A roots (r1, r2, 2 B_l A^-1 per sieved prime)"
        elif 255 <= line <= 268:
            cat = "small|Gray-code switching (root updates per polynomial)"
        else:
            cat = f"small|other setup (line {line})"
        ATTR[cat] += n
    return _orig(self, phase, n)
ledger.Charger.charge = charge
for bits in SS.SIZES:
    g = dict(SS.qsg(sealed["sizes"][str(bits)]["tracks"]["R"]["new_genes"]), kset="sf32")
    rows = SS.corrected_map_rows(bits); nums = S2.map_nums(bits)
    top = max(r["band"] for r in rows)
    sample = [t for t, r in zip(nums, rows) if r["band"] == top][:3] + [t for t, r in zip(nums, rows) if r["band"] == 24][:3]
    ATTR.clear(); tot = collections.Counter(); sf = 0
    for N, _, _ in sample:
        qs.TRACE = {}
        m = lamps.Meter(P.QS_CAP)
        try:
            qs.lamp_qs(N, g, m)
        except lamps.Budget:
            pass
        tr = qs.TRACE; qs.TRACE = None
        c = optypes.qs_counts(tr)
        tot.update(c); sf += c["setup_full"]
    out = []
    for Pn in ("official", "ruint", "montgomery"):
        price = (lambda t: 1.0) if Pn == "official" else (lambda t: PR[Pn][t])
        total = sum(price(t) * v for t, v in tot.items() if v)
        parts = {}
        for cat, n in ATTR.items():
            kind, name = cat.split("|", 1)
            if kind == "euclid":
                parts[name] = parts.get(name, 0) + n * price("setup_euclid")
            elif kind == "asel":
                parts[name] = parts.get(name, 0) + sf * price("setup_full") + (n - sf) * price("setup_small")
            elif name.startswith("multiplier"):
                parts[name] = parts.get(name, 0) + n * price("mult")
            elif name.startswith("factor base"):
                parts[name] = parts.get(name, 0) + n * price("fb")
            else:
                parts[name] = parts.get(name, 0) + n * price("setup_small")
        out.append((Pn, total, parts))
    print(f"{bits} bits ({len(sample)} numbers): share of total qs cost (official / ruint / Montgomery)", flush=True)
    names = sorted(out[1][2], key=lambda k: -out[1][2][k])
    for nm in names:
        print(f"   {nm:58s} " + " / ".join(f"{o[2].get(nm, 0) / o[1]:.3f}" for o in out), flush=True)
    print(f"   {'setup, all parts':58s} " + " / ".join(f"{sum(o[2].values()) / o[1]:.3f}" for o in out), flush=True)
