"""Dark regions, a first sketch of the light spectrum (Phase 3; the user, Oct 28; information only, existing data, no new
runs). For each size (72 and 96: size_map.json; 84: partition_map.json; 80 numbers per band) and each smaller-factor band
(theta = smaller factor bits / N bits), each lamp ALONE: td, rho, p-1 (its fixed B), ECM (the maps' genes, Python, cap 2^21
ops), and the maps' qs ("qs + lc 1.4", an older card under an older meter: it lacks today's word-level types, so its
cost is understated against today's card, and it always succeeds within 2^28).
  light(lamp, band) = successes / total priced cost spent on the band's numbers (successes per million price units),
  under ruint (median P-core prices, optypes.prices) and official (ops).
A band is dark where the BEST lamp's light is lowest; the spectrum is the table of light per lamp per theta.
  python3 dark_regions.py -> dark_regions.json, stdout"""
import json
import optypes

LAMPS = ["td", "rho", "pm1", "ecm", "qs + lc 1.4"]
PR = optypes.prices()

def price(per_type, pricing):
    if pricing == "official":
        return float(sum(per_type.values()))
    return float(sum(PR["ruint"].get(t, 0.0) * n for t, n in per_type.items()))

def unpriced(per_type):
    return sorted(t for t, n in per_type.items() if n and t not in PR["ruint"])

if __name__ == "__main__":
    maps = {72: json.load(open("size_map.json"))["maps"]["72"]["rows"],
            84: json.load(open("partition_map.json"))["rows"],
            96: json.load(open("size_map.json"))["maps"]["96"]["rows"]}
    out, missing = {}, set()
    for bits, rows in maps.items():
        bands = sorted({r["band"] for r in rows})
        out[bits] = {}
        print(f"== {bits} bits: light = successes per million price units (ruint; official in brackets), 80 numbers per band")
        print(f"  {'band (theta)':16s}" + "".join(f"{l:>20s}" for l in LAMPS) + "   best lamp")
        for b in bands:
            rs = [r for r in rows if r["band"] == b]
            row = {}
            for l in LAMPS:
                succ = sum(r[l]["T"] is not None for r in rs)
                for r in rs:
                    missing.update(unpriced(r[l]["per_type"]))
                c_r = sum(price(r[l]["per_type"], "ruint") for r in rs)
                c_o = sum(price(r[l]["per_type"], "official") for r in rs)
                row[l] = {"success": succ, "n": len(rs), "light_ruint": 1e6 * succ / c_r if c_r else None,
                          "light_official": 1e6 * succ / c_o if c_o else None}
            best = max(LAMPS, key=lambda l: row[l]["light_ruint"] or 0)
            row["best"] = best
            out[bits][b] = row
            print(f"  {b:3d} ({b / bits:.2f})     " + "".join(
                f"{row[l]['light_ruint']:9.3f} [{row[l]['light_official']:7.3f}]" if row[l]['light_ruint'] else f"{'0 (' + str(row[l]['success']) + '/80)':>20s}"
                for l in LAMPS) + f"   {best}")
        dark = min(out[bits], key=lambda b: out[bits][b][out[bits][b]["best"]]["light_ruint"])
        print(f"  darkest band at {bits} bits: smaller factor {dark} bits (theta {dark / bits:.2f}); "
              f"best lamp there {out[bits][dark]['best']}, light {out[bits][dark][out[bits][dark]['best']]['light_ruint']:.3f}")
    if missing:
        print("types without a ruint price (counted as 0 under ruint):", sorted(missing))
    json.dump({str(k): {str(b): v for b, v in d.items()} for k, d in out.items()}, open("dark_regions.json", "w"), indent=1)
