"""A re-reading of the sealed light spectrum's committed outputs (evolve/light_spectrum.json, from sealed run 721af65,
committed unchanged in 68be1a9); no new runs (the reviewer's brief, Oct 28). Prints:
  1. per size and theta band: every lamp's light under op-class v1 and ruint, and the best lamp under each (CFRAC's ruint
     light is 0 by the runner's defect: its lumped type has no ruint price);
  2. per size: the lowest band whose op-class best is QS, and the lowest band from which QS stays best in every band above;
     the same under ruint; and the op-class line with td's and p-1's light multiplied by their pooled instruction-check
     ratio (op-class / instructions, the run's own per-size values), "instruction-corrected, information only";
  3. at 96 bits, bands 0.20-0.28 (theta 0.20-0.30): per lamp, successes, op-class and ruint cost per success, and the ratio
     of the best non-QS lamp's op-class light to QS's.
  python3 spectrum_opclass_view.py > ../results/growth-spectrum-twilight_opclass_view.out"""
import json

d = json.load(open("light_spectrum.json"))
L = ["td", "rho", "pm1", "ecm", "cfrac", "qs"]

def pooled(bits, lamp):
    cells = [d[bits][b][lamp] for b in d[bits]]
    return sum(c["check_opclass_v1"] for c in cells) / sum(c["check_instructions"] for c in cells)

def lines(bits, key, corr=None):
    bands = sorted(d[bits], key=float)
    best = {}
    for b in bands:
        v = {l: d[bits][b][l][key] * (corr.get(l, 1.0) if corr else 1.0) for l in L}
        best[b] = "qs" if v["qs"] > max(v[l] for l in L if l != "qs") else max((l for l in L if l != "qs"), key=lambda l: v[l])
    first = next((b for b in bands if best[b] == "qs"), None)
    stays = next((b for i, b in enumerate(bands) if all(best[x] == "qs" for x in bands[i:])), None)
    return best, first, stays

print("Re-reading of sealed run 721af65's committed outputs (light_spectrum.json, 68be1a9). No new runs.")
print("light = successes per million price units; QS 'best' = strictly brighter than every other lamp.\n")
summary = []
for bits in ("72", "84", "96"):
    bo, fo, so = lines(bits, "light_v1")
    br, fr, sr = lines(bits, "light_ruint")
    corr = {"td": pooled(bits, "td"), "pm1": pooled(bits, "pm1")}
    bc, fc, sc = lines(bits, "light_v1", corr)
    print(f"== {bits} bits: per band, light under op-class v1 / ruint, and the best lamp under each")
    for b in sorted(d[bits], key=float):
        c = d[bits][b]
        print(f"  {b}: " + "  ".join(f"{l} {c[l]['light_v1']:.3f}/{c[l]['light_ruint']:.3f}" for l in L)
              + f"   best op-class {bo[b]}, ruint {br[b]}" + ("" if bo[b] == br[b] else "   (differ)"))
    summary.append((bits, fo, so, fr, sr, fc, sc, corr))
    print()
print("== the crossover (lower edges of theta bands)")
for bits, fo, so, fr, sr, fc, sc, corr in summary:
    print(f"  {bits} bits: op-class: lowest band with QS best {fo}, QS best in every band from {so}; "
          f"ruint: lowest {fr}, from {sr}; {'the same' if (fo, so) == (fr, sr) else 'they differ'}")
for bits, fo, so, fr, sr, fc, sc, corr in summary:
    print(f"  {bits} bits, instruction-corrected, information only (td light x {corr['td']:.3f}, p-1 light x {corr['pm1']:.3f}): "
          f"lowest band with QS best {fc}, QS best in every band from {sc}")
print("\n== 96 bits, theta 0.20-0.30: per lamp, successes / 40, op-class and ruint cost per success (millions; '-' = no success)")
for b in ("0.20", "0.22", "0.24", "0.26", "0.28"):
    c = d["96"][b]
    parts = []
    for l in L:
        s = c[l]["success"]
        oc = f"{c[l]['opclass_v1'] / s / 1e6:.2f}" if s else "-"
        rc = f"{c[l]['ruint'] / s / 1e6:.3f}" if s and c[l]["ruint"] else ("-" if not s else "n/a")
        parts.append(f"{l} {s}/40 {oc} / {rc}")
    bn = max((l for l in L if l != "qs"), key=lambda l: c[l]["light_v1"])
    r = c[bn]["light_v1"] / c["qs"]["light_v1"]
    print(f"  {b}-{float(b) + 0.02:.2f}: " + "; ".join(parts) + f"   best non-QS {bn}: op-class light ratio to QS {r:.2f}")
