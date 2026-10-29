# arrangement-v1: the arrangement lamp family ("arrangement + detection rule"), predictions

**Status: the reviewer's and Grok's sealed; DeepSeek's text not yet received (two relay messages ended in the paste placeholder). Nothing is built or run.** The design is `docs/planning/arrangement_lamps.md` as of 70d374a: approved in principle by the user (Oct 29), with the reviewer's amendments. The fitness is G_rho (`reviews/growth_fitness_rho.md`, frozen 77ff2ee), with G (`reviews/growth_fitness.md`, frozen c86ef35) beside it.

Novelty Plan: phase 4 (program search, the building-block family). Q1 is phase 4's test drive on a family with a known answer.

## The questions (design §7)

1. **Q1:** Is the best genome rho-shaped? That means the map layout with cycle detection (Floyd or Brent, batched or not), with a log2-steps slope of 0.20–0.30 per bit over 48–80 bits. Yes or no. A yes is reported as "rediscovered known lamp"; it validates the search, meter and guard.
2. **Q2:** The best genome's G_rho (48–80, op-class, plus its worst-of value including the scaled gcd price), or "not defined". Its G (80–96), or "not defined".
3. **Q3:** The best genome ÷ rho alone at 64 and 80 bits, op-class v1, with a range; and the same under the size-scaled gcd price.
4. **Q4:** Does any non-map layout (stride, fold, bins) beat a slope of 0.45 per bit? Yes or no.
5. **Q5:** Does the search select the exponent layout (rediscovered p−1) on θ < 0.3 numbers? It is scored on the θ 0.20–0.30 sub-map only (design §8).
6. **Q6:** The best genome's map degree d: d = 2, or higher?

**Number distributions** (design §8):
- **Balanced main map:**
  - training: 48 per size at 48–80 bits, seeds 9920000 + bits;
  - validation: 48 per size at 48, 64, 80 and 96 bits, seeds 9930000 + bits, with rho alone on the same numbers.
- **θ sub-map:** θ uniform 0.20–0.30; training 48 per size at 64 and 80 bits (seeds 9925000 + bits); validation 96 per size (seeds 9935000 + bits).

## The reviewer's R-38 to R-43 (Oct 29; sealed; verbatim; filed before any run)

<!-- verbatim begin -->
  R-38 (Q1) Best genome rho-shaped (map + cycle detection, slope 0.20-0.30 per
       bit, 48-80): yes, 80%.
  R-39 (Q2) Best genome G_rho (48-80, op-class): 1.00, range 0.88-1.12, 65%;
       holds under the worst-of set incl. scaled gcd price. G (80-96) defined:
       0.43, range 0.36-0.52, 60%.
  R-40 (Q3) Best genome / rho alone at 64 and 80 bits, op-class: 0.95, range
       0.82-1.08, 60%; under the scaled gcd price within +/-0.03 of op-class.
  R-41 (Q4) A non-map layout beats 0.45 per bit: no, 85%.
  R-42 (Q5, if kept) Search selects the exponent layout on theta < 0.3: no, 60%.
  R-43 (Q6) Best map degree d = 2: yes, 70%.
  Calibration note: ranges widened and confidences lowered from R-38 on, per the
  scorecard (stated 61-65%, hit 47-50%).
<!-- verbatim end -->

**Scope note** (the prediction is unchanged): Q5 is kept, with its own sub-map (design §8), so R-42 is scored.

## DeepSeek's

Pending (the user decides whether to relay).

## Grok's G-31 to G-36 (Oct 29; sealed; verbatim, as relayed by the user; filed before any build or run)

<!-- verbatim begin -->
G-31 (best genome is rho-shaped: map + Floyd/Brent, slope 0.20–0.30 / bit over
48–80). Prediction: yes. Range: categorical {yes, no}. Arithmetic: measured
unmetered slopes (20–40 bits) are 0.254 for rho (x²+1, Floyd) and 0.253 for p-1
versus 0.503 for walk/value-line; map + cycle detection is explicitly in the gene
pool while non-map layouts are linear (stride/fold/bins). Base: best genome under
G_rho fitness on the main balanced map (training 48 per size at 48/56/64/72/80).
"Rho-shaped" defined exactly as map layout + Floyd or Brent detection (batched or
not) with fitted slope in [0.20, 0.30]. Confidence: 70%. Falsifier (single
condition): the selected genome uses a non-map layout or a fitted slope outside
[0.20, 0.30].

G-32 (best genome's G_rho 48–80 op-class; holds under worst-of incl. scaled gcd?;
its G 80–96). Prediction: G_rho = 1.05; holds under worst-of; G = not defined.
Range: G_rho 0.70–1.40 (±33% around 1.05). Arithmetic: rho alone measured at
3.936 bits [3.790, 4.098]; a rediscovered or mildly tuned map+cycle genome is
expected near 1.0 relative to that baseline, centre lifted to 1.05 for possible
Brent/batched or degree effects, then widened for search variance and the
1.1–1.3% gcd share. Scaled-gcd price changes gcd by a size-dependent factor but
gcd is only ~1% of cost, so worst-of is not expected to reverse a near-1 result.
G (vs QS 9.29 bits) is undefined if the genome is rho-shaped (cannot run the
80–96 QS comparison on a pure rho). Base: op-class v1, G_rho = (candidate
doubling period) / 3.936 over 48–80, worst-of = {op-class v1, ruint, Montgomery,
scaled gcd}. Confidence: 50%. Falsifier (single condition): measured G_rho
(op-class) ≥ 1.50 or the genome is reported as non-rho-shaped.

G-33 (best genome / rho alone at 64 and 80 bits, op-class; same under scaled
gcd). Prediction: 0.95 at both sizes (op-class and scaled-gcd). Range: 0.65–1.25
at each size (±32%). Arithmetic: if the genome is a close rho variant, cost ratio
near 1; centre 0.95 allows a small implementation edge (batched detection or
degree), width covers the possibility of a modestly worse constant or of a
non-rho genome that is still competitive at these sizes. Scaled-gcd adjustment is
small (gcd 1.1–1.3% of rho cost) so the two pricings stay close. Base: mean cost
per factorisation, op-class v1 and size-scaled gcd price, versus rho alone on the
same 48 held-out numbers per size. Confidence: 55%. Falsifier (single condition):
measured op-class ratio at 80 bits ≥ 1.40.

G-34 (any non-map layout beats 0.45 per bit). Prediction: no. Range: categorical
{yes, no}. Arithmetic: measured walk/value-line slopes are 0.503; non-map layouts
(stride, fold, bins) are linear arrangements whose collision time is expected to
track that slope; "beat 0.45" would require a sub-linear improvement not observed
in the unmetered shapes. Base: fitted slope of log2(median steps) per bit, 48–80,
any stride/fold/squares-bins genome. Confidence: 65%. Falsifier (single
condition): a non-map genome is selected with fitted slope ≤ 0.45.

G-35 (search selects exponent layout on the θ 0.20–0.30 sub-map). Prediction:
yes. Range: categorical {yes, no}. Arithmetic: exponent layout is exactly p-1's
arrangement; on the low-θ band (smaller factors) the earlier twilight results
showed p-1 delivering useful successes at low op-class cost, and the gene pool
includes it. Base: selected genome on the θ-uniform 0.20–0.30 sub-map (training
48 at 64 and 80). Confidence: 55%. Falsifier (single condition): the selected
genome on that sub-map is not the exponent layout.

G-36 (best genome's map degree: d = 2 or higher). Prediction: d = 2. Range:
categorical {d=2, d>2}. Arithmetic: measured rho baseline uses x²+1; higher even
d (4,6,8) costs (log2 d + popcount(d) − 1) muls per step (charge 554.9 each)
while the Brent/Pollard (1981) cycle-shortening benefit is conditional on
p ≡ 1 mod 2k and is not guaranteed to offset the extra multiplies under the
frozen op-class weights. Base: map-layout degree of the best G_rho genome on the
main balanced map. Confidence: 60%. Falsifier (single condition): the selected
genome has map degree d ≥ 4.
<!-- verbatim end -->

**The reviewer's notes on G-31..G-36** (Oct 29; annotations only; no prediction changes):

<!-- verbatim begin -->
- G-32's "G undefined for a pure rho (cannot run the 80-96 QS comparison)" shares
  D-39's reading: G compares the candidate's own 80-96 doubling period with QS's
  9.29 bits; the design states a p^(1/2) arrangement is feasible at 80-96 and
  validation includes 96, so G should be defined (~0.43) unless the stage budget
  censors rho at 96. If the budget censors it, state so in the results.
- G-32's falsifier has two conditions (the second duplicates G-31); recorded as
  written.
- G-35's support cites twilight evidence where p-1 was compared with QS at 96
  bits; on the 0.20-0.30 sub-map at 64/80 bits p-1 competes with rho at
  p ~ 2^13-2^24. Recorded as given.
<!-- verbatim end -->
