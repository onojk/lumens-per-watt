# arrangement-v1: the sealed forecasts, scored as written (Oct 30; no compute)

**Sources:**
- Measured values are held-out unless marked: sealed harness run f527a0a and report 6c6edfc, balanced map, 48 per size, seeds 9930000 + bits.
- The best genome is the re-run search's rank 1 (96bb064): map(c = 2, d = 2, x0 = 5) + Brent(512).
- **Scoring rule:** each forecast is scored on its own falsifier, or, where it gives no falsifier, on its stated value and range, using point values. Intervals are shown for reference only.

**Measured values used:**

| quantity | measured |
|---|---|
| best genome | map + Brent (cycle detection), d = 2: rho-shaped, a rediscovered known lamp |
| op-count slope 48–80 (log2 median ops, least squares at 48/64/80) | **0.2631** held-out (rho 0.2497); 0.249 training |
| G_rho 48–80, op-class v1 | **0.96796** [0.9117, 1.0281] |
| G_rho 48–80, scaled gcd | 0.96832 [0.9119, 1.0261] |
| G_rho 48–80, worst-of (op-class, ruint, Montgomery, scaled gcd) | 0.96796 [0.9126, 1.0275] |
| G 80–96, op-class v1 / worst-of | **0.4474** [0.4072, 0.4948] / 0.4474 [0.4070, 0.4941]; defined |
| cost / rho, op-class v1 | 64: **0.9896**; 80: **0.9872** |
| cost / rho, scaled gcd | 64: 0.9928; 80: 0.9876 |
| non-map layouts (stride, fold, bins) | none measured: every non-map pair dropped at 48 bits within the search's budget (0 / 48 factored; bin compare 0 / 48), so no non-map slope exists |
| map degree d | 2 |
| D-44 band average | 0.9884 [0.8611, 1.1331] |
| G-37 | 0 / 10 = 0.00 (Fermat-easy subset 6 of 48) |

## The scores

| ID | Q | forecast (as written) | range | measured | falsified | note |
|---|---|---|---|---|---|---|
| R-38 | Q1 | rho-shaped: yes, 80% | yes/no | yes (map + Brent, slope 0.263) | **no** | |
| R-39 | Q2 | G_rho 1.00, holds under worst-of incl. scaled gcd; G defined, 0.43 | G_rho 0.88–1.12; G 0.36–0.52; 65% / 60% | G_rho 0.968 (worst-of 0.968); G 0.447 | **no** | both within range |
| R-40 | Q3 | 0.95 at 64 and 80, op-class; scaled within ±0.03 of op-class | 0.82–1.08; 60% | 0.990 / 0.987; scaled shift +0.003 / +0.000 | **no** | |
| R-41 | Q4 | a non-map layout beats 0.45: no, 85% | yes/no | no non-map slope measured (all dropped at 48 bits) | **no** | not falsified by default: no non-map genome was measurable, so none beat 0.45 within this budget |
| R-42 | Q5 | exponent selected on θ < 0.3: no, 60% | yes/no | — | **cannot be scored** | the θ sub-map search has not run |
| R-43 | Q6 | d = 2: yes, 70% | yes/no | d = 2 | **no** | |
| D-38 | Q1 | yes, rho-shaped | slope 0.20–0.30; 0.85 | yes, slope 0.263 | **no** | |
| D-39 | Q2 | G_rho ≈ 1.00 op-class; worst-of ≈ 0.99 [0.96, 1.03], no strict win; G ≈ 1.00 or "not defined" | op-class [0.97, 1.04]; 0.65 | G_rho op-class **0.96796**; worst-of 0.968, no strict win; G 0.447, defined | **yes** | The falsifier's first condition holds: 0.96796 < 0.97, on the point value. The interval [0.912, 1.028] overlaps the range, and the gap is inside G_rho's stated ±4% resolution, but the forecast is scored as written. The G statement (≈ 1.00 or undefined) is also wrong (0.447, defined), as the reviewer's note anticipated; it is not in the falsifier. |
| D-40 | Q3 | op-class 64 ≈ 0.99, 80 ≈ 1.00; scaled 64 ≈ 1.00, 80 ≈ 1.01 | [0.95, 1.04], [0.96, 1.05]; scaled [0.96, 1.05], [0.97, 1.06]; 0.60 | 0.9896, 0.9872; scaled 0.9928, 0.9876; scaled shift ≤ 0.4% | **no** | all four inside; the measured intervals (±17–23%) are far wider than the ranges |
| D-41 | Q4 | no non-map layout beats 0.45 | 0.85 | none measured | **no** | not falsified by default, as R-41 |
| D-42 | Q5 | exponent not selected on θ 0.20–0.30 | 0.60 | — | **cannot be scored** | the θ sub-map search has not run |
| D-43 | Q6 | d = 2 | 0.75 | d = 2 | **no** | |
| G-31 | Q1 | yes, rho-shaped | categorical; 70% | yes, slope 0.263 | **no** | |
| G-32 | Q2 | G_rho 1.05, holds under worst-of; G not defined | G_rho 0.70–1.40; 50% | G_rho 0.968 (worst-of 0.968); G 0.447, defined | **no** | Not falsified, since the falsifier needs G_rho ≥ 1.50 or a non-rho genome. The G statement ("not defined") is wrong (0.447, defined), as the reviewer's note anticipated; it is not in the falsifier. |
| G-33 | Q3 | 0.95 at both sizes, op-class and scaled gcd | 0.65–1.25; 55% | 0.990 / 0.987; scaled 0.993 / 0.988 | **no** | falsifier: op-class at 80 ≥ 1.40 (0.987) |
| G-34 | Q4 | no | categorical; 65% | no non-map genome selected; none measurable | **no** | not falsified by default, as R-41 |
| G-35 | Q5 | yes, exponent selected | categorical; 55% | — | **cannot be scored** | the θ sub-map search has not run |
| G-36 | Q6 | d = 2 | categorical; 60% | d = 2 | **no** | |
| D-44 | (sealed Oct 30) | 0.98, band average of held-out op-class cost / rho at 64–80 | 0.69–1.27; 25% | 0.988 [0.861, 1.133] | **no** | already scored (6c6edfc) |
| G-37 | (sealed Oct 30) | 0.02 | 0.00–0.08; 60% | 0 / 10 = 0.00 | **no** | already scored (6c6edfc) |

**Totals over the 20 forecasts:**
- 16 not falsified;
- 1 falsified (D-39, by 0.002 on the point value);
- 3 cannot be scored (R-42, D-42, G-35: Q5, the θ sub-map, has not run).

Of the 16, 3 are not falsified only by default (R-41, D-41, G-34: no non-map slope could be measured within the search's budget).

Two statements outside their falsifiers were wrong: D-39's and G-32's "G not defined / ≈ 1.00". The measured G is 0.447, defined, as the reviewer's notes said.

## Q5, scored after the θ sub-map search (Oct 30)

**Sources:**
- θ search: sealed 0f16ffe; its same-seed rerun, 32773cc, has identical content (post-hoc set comparison; order differs, NOTES).
- θ scoring: sealed d8321a8.

**Selected genome on the θ 0.20–0.30 sub-map:** map(c = 5, d = 2, x0 = 2) + Brent(512), training fitness (worst-of G_rho, 64–80, cost guard) 1.133. **Not the exponent layout.**
- The exponent layout was evaluated across its grid: K = 256 factored fewer than half the training numbers at 64 bits; K ≥ 1,024 factored at least half but cost 27–50 × rho (robust) at 64 bits, far over the 1.25 cost guard.
- Both exponent pairs were dropped at 64 bits.

| ID | Q | forecast (as written) | measured | falsified | note |
|---|---|---|---|---|---|
| R-42 | Q5 | exponent selected on θ < 0.3: no, 60% | not selected (map + Brent) | **no** | |
| D-42 | Q5 | no; selects a map/rho-shaped genome; 0.60 | map + Brent selected | **no** | |
| G-35 | Q5 | yes, exponent selected; 55% | map + Brent selected | **yes** | the falsifier holds: the selected genome is not the exponent layout |

**Totals over all 20 forecasts:**
- 15 genuine passes;
- 3 not falsified by default (R-41, D-41, G-34);
- 2 falsified: D-39, by 0.002 on the point value; G-35.

**Held-out θ scoring of the selected genome** (information; not a Q5 condition; 96 per size, seeds 9935000 + bits; audit clean, 192 / 192 factors in both arms):
- Robust cost against rho: **1.267 [1.077, 1.491] at 64 bits**, dearer than rho with the interval above 1.
- 0.990 [0.804, 1.227] at 80 bits.
- On held-out numbers the pick exceeds the search's 1.25 guard at 64 bits. Its training fitness (G_rho 1.133) came from a flatter cost curve, not from being cheaper.
