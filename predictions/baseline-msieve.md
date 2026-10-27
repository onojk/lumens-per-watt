# baseline-msieve: the adopted reference (2′b) against msieve on the map numbers (I-038; information only): predictions

**Run:** `evolve/baseline_msieve.py` (not yet written). msieve 1.53 built from source in `~/opt`; it runs in batch mode, one process over a file of numbers, so start-up is paid once.
- **Numbers:** the 96-, 72- and 84-bit map numbers.
- **Machine:** pinned to core 2, cap 2.4 GHz, AC online. Machine state is recorded; timing is skipped if the conditions are not met.
- **Measured:** wall per number for msieve and for the reference (2′b) on the same numbers, under the same conditions, 4 replicates each. msieve's factors are checked against ours on every number.
- **Information only:** msieve has no op meter, so it never enters fitness.

**Status:** sealed. Filed before msieve is built and before any timing. The msieve source download was denied by the permission prompt at filing time, so nothing about msieve has been measured on this machine.

## The reviewer's (Oct 27, sealed; verbatim)

      Reviewer (Oct 27, sealed): at 96 bits, capped 2.4 GHz, batch mode, the new reference card's wall
      per number divided by msieve's is between 0.7 and 6 (central 2): msieve faster, but by less than
      10x. Confidence 65% that the ratio is inside 0.7-6. At 72 bits the ratio is closer to 1 than at
      96 (msieve's fixed per-number setup weighs more on small numbers), 60%.

## DeepSeek's D-18 / D-19 (received 07:58 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
### D-18 — 96 bits
Definition: (card wall per number) / (msieve wall per number), both on the same 96-bit map numbers, single core, 2.4 GHz cap, AC, batch mode for msieve. Base: card = 2'b (adopted reference). msieve = its default QS/SIQS path in batch mode. Ratio < 1 means the card is faster. Units: dimensionless ratio; wall in µs per number.
Sealed range 0.35–1.05 (central 0.60); confidence 60% that the true value is inside. Falsifier: falsified if the ratio is >1.15 or <0.20.
Working: card 2'b at 96 bits ≈ 3,850 × 0.89 = 3,426.5 µs. Missing input: msieve's per-number wall on this machine at 96 bits does not exist. External anchor (information only): a published single-core msieve run on a Xeon E5-2680 v3 at 2.50 GHz factored a 79-digit number in 150 s (1 min 49 s on a laptop, 1 min 24 s on an i7-11700K). QS heuristic quoted for msieve, exp(0.22n − 10.7) s: n = 24 gives 0.0044 s and n = 29 gives 0.0133 s, judged "far below any plausible 96-bit time" and not used. Scaling the 79-digit/150 s anchor to 96 bits gives a factor ~1.6–2.5×, so msieve ≈ 240–375 s per number; card/msieve = 0.0091–0.0143, far below the sealed range. The wide range 0.35–1.05 reflects the opposite possibility (batch start-up, msieve's own parameters, anchor not comparable); central 0.60 deliberately does not extrapolate the ~1% figure. Width rule: arithmetic too uncertain to set the width, so the range is set by the spread of plausible msieve models and is very wide, stated explicitly.
### D-19 — is the ratio closer to 1 at 72 than at 96?
Definition: "closer to 1" = |r72 − 1| < |r96 − 1|, r_b the D-18 ratio at size b; same comparison and conditions, card = 2'b at both sizes.
Sealed answer: Yes, confidence 75%. Falsifier: |r72 − 1| ≥ |r96 − 1|.
Reasoning: the card's wall grows sub-exponentially while msieve's QS wall grows super-polynomially; if msieve is slower at 96 the gap widens with size (e.g. r96 ≈ 0.1, r72 ≈ 0.33 → 0.67 < 0.90). The 25% residual covers msieve being faster at both sizes. Missing input: msieve's 72-bit wall on this machine is also missing; D-19 is an ordering claim about two unmeasured quantities.
<!-- verbatim end -->

**The reviewer's annotations** (the ranges are unchanged):
- **A units error.** The external anchor is a 79-**digit** number (about 262 bits). D-18 read it as 79 bits and scaled it **up** to 96 bits, so the resulting 240–375 s per 96-bit number is off by orders of magnitude: 96 bits is 29 digits.
  - The heuristic D-18 rejected, exp(0.22n − 10.7) s, about 13 ms at 29 digits, is the plausible order.
  - At about 3.4 ms for the card, that would give a ratio near 0.26: below D-18's range, though the falsifier at 0.20 is not reached.
- **The guard:** external numbers were used despite it. They are labelled information only.
- **D-19:** both tools are QS-class with the same growth form; the ordering claim stands as sealed.
- **The same uncertainty affects the reviewer's prediction** (0.7–6, msieve faster): neither forecaster knew msieve's small-number path.

## Grok's G-11 / G-12 (received 08:00 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
**Sealed predictions (Grok, 27 Oct 2026 ~08:05 PT)**
Using only the numbers supplied. Absolute msieve wall times on this machine are missing.

### G-11 — At 96 bits: (card wall per number) / (msieve wall per number)
**Range:** 0.6–2.5 (confidence 60 % that the true value falls inside).
Below 1 = card faster.

(Information only, not used for the range: public literature quotes for msieve SIQS on ~30-decimal-digit numbers are typically several milliseconds on modern CPUs; the card's ~3.4 ms for 2'b at 2.4 GHz is in the same order of magnitude, but machine, pinning, and batch overhead differ. Those figures are in decimal digits, not bits.)

**Falsifier:** the measured ratio lies outside 0.6–2.5.

### G-12 — At 72 bits vs 96: is the ratio closer to 1 at 72?
**Definition of "closer to 1":** the absolute value |ratio − 1| is smaller at 72 bits than at 96 bits.
**Answer:** yes (confidence 55 %).

**Falsifier:** |ratio_72 − 1| ≥ |ratio_96 − 1|.
<!-- verbatim end -->

**The reviewer's note:** units handled correctly (decimal digits against bits); single-condition falsifiers.
