"""Stage 9: score race_compare.json against the predictions in NOTES.md (Stage 9 entry),
mechanically, so the verdicts don't come from reading 270 rows.

Rules, as stated before the run:
- Addendum 4 (per pricing, from the pairwise call between the race's two sides alone):
  where one side leads with separated intervals, the race loses to it by at most the
  pricing's bound (official: 2x; calibrated: 1 + pi_other / pi_winner, measured pi) and
  beats the other side; where the sides are tied, the race beats both.
- The judging bar: a failure is a race worse than about 2x the better side, or worse than
  the worse side, under any pricing (race_compare's verdict); the robust verdict is a
  failure under any of the three.
- Addendum 9: unequal against equal slices, per s: at 2^8 little change; at 2^10 and 2^14
  the calibrated cost moves toward the better side and the official cost gets slightly
  worse. Reported as the change in log2 mean, race over the better side.
Also reported: cells where the race beats both sides on the mean, and the race's official
worst case against each side's.

  python3 race_report.py  -> race_report.out (stdout)
"""
import json, statistics

D = json.load(open("race_compare.json"))
CAL = json.load(open("calibrate.json"))
COUNTS = json.load(open("calibrate_counts.json"))
PRICINGS = ("official", "ruint", "montgomery")
ALONE = {pr: (CAL["official"] if pr == "official" else CAL["scores"][pr]) for pr in PRICINGS}

def worst_alone(alg, cell):
    return max(x["ops"] for x in COUNTS[alg][cell] if x["ops"] is not None)

def addendum4(c, a, b, cell, pr):
    A, B = ALONE[pr][a][cell], ALONE[pr][b][cell]
    race = c[pr]["mean_log2"]
    if A["ci95"][1] < B["ci95"][0] or B["ci95"][1] < A["ci95"][0]:
        lead, oth = (A, B) if A["mean_log2"] < B["mean_log2"] else (B, A)
        bound = c["verdict"][pr]["pricing_bound"] if pr != "official" else 2.0
        ok = 2 ** (race - lead["mean_log2"]) <= bound and race < oth["mean_log2"]
        return ok, "lead"
    return race < min(A["mean_log2"], B["mean_log2"]), "tie"

if __name__ == "__main__":
    print("Addendum 4 rule, passes / cells (lead cells, tie cells) per race, setting and pricing:")
    beats_both = []
    for rname, by_label in D["results"].items():
        a, b = rname[5:-1].split(", ")
        print(f"\n{rname}")
        for label, cells in by_label.items():
            row = []
            for pr in PRICINGS:
                res = [addendum4(c, a, b, cell, pr) for cell, c in cells.items()]
                lead = [ok for ok, k in res if k == "lead"]
                tie = [ok for ok, k in res if k == "tie"]
                row.append(f"{pr[:4]} {sum(lead) + sum(tie):2d}/{len(res)} (lead {sum(lead)}/{len(lead)}, tie {sum(tie)}/{len(tie)})")
            fails = {pr: sum(c["verdict"][pr]["fails"] for c in cells.values()) for pr in PRICINGS}
            robust = sum(c["robust_fails"] for c in cells.values())
            print(f"  {label:13s} " + "  ".join(row) + f"   bar failures: " +
                  " ".join(f"{pr[:4]} {fails[pr]}" for pr in PRICINGS) + f"  robust {robust}/{len(cells)}")
            for cell, c in cells.items():
                for pr in PRICINGS:
                    if c[pr]["mean_log2"] < min(ALONE[pr][a][cell]["mean_log2"], ALONE[pr][b][cell]["mean_log2"]):
                        beats_both.append((rname, label, cell, pr))
    print(f"\nRace mean below both sides alone: {len(beats_both)} of {3 * 6 * 15 * 3} (race, setting, cell, pricing) cases")
    for x in beats_both:
        print("  ", *x)
    print("\nAddendum 9: change in log2(race / better side), unequal minus equal (negative = closer); median over cells [min, max]:")
    for rname, by_label in D["results"].items():
        print(f"  {rname}")
        for s in (256, 1024, 16384):
            eq, un = by_label[f"equal {s}"], by_label[f"unequal {s}"]
            parts = []
            for pr in PRICINGS:
                dl = [un[cell][pr]["mean_log2"] - eq[cell][pr]["mean_log2"] for cell in eq]
                parts.append(f"{pr[:4]} {statistics.median(dl):+.2f} [{min(dl):+.2f}, {max(dl):+.2f}]")
            print(f"    s = {s:5d}: " + "  ".join(parts))
    print("\nOfficial worst case (log2): race vs the sides alone, equal slices; cells where the race's worst is below both sides' worst:")
    for rname, by_label in D["results"].items():
        a, b = rname[5:-1].split(", ")
        for s in (256, 1024, 16384):
            cells = by_label[f"equal {s}"]
            better = [cell for cell, c in cells.items()
                      if 2 ** c["official"]["worst_log2"] < min(worst_alone(a, cell), worst_alone(b, cell))]
            print(f"  {rname} s = {s}: {len(better)}/15 {better}")
    print("\nqs-side overshoot per slice, mean over cells (equal slices), and the share of the race's official ops spent by the qs side:")
    for rname, by_label in D["results"].items():
        for s in (256, 1024, 16384):
            cells = by_label[f"equal {s}"]
            ov = statistics.mean(c["overshoot"][1]["mean"] for c in cells.values())
            share = statistics.mean(c["side_ops_mean"][1] / sum(c["side_ops_mean"]) for c in cells.values())
            print(f"  {rname} s = {s:5d}: mean qs overshoot {ov:7.0f} ops ({ov / s:.1f} s), qs share of ops {share:.2f}")
