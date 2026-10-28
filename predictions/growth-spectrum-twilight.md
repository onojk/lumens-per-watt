# growth-spectrum-twilight: the growth harness v1, the light spectrum v1 and the twilight specialist: sealed predictions, filed before any run in this round

**The runs** (none has started):
- **The growth harness v1** (`evolve/growth_harness.py`, ec6ea78);
- **The light spectrum v1** (`evolve/light_spectrum.py`, committed before running). Its counts were running in the background when this file was filed, and no output had been read.
- **The twilight specialist** (`evolve/twilight_search.py`, 5835507; its validation run not yet written).

The reviewer's R-29 to R-31 for the growth harness are in `predictions/growth-v1.md` (c8b589d).

## DeepSeek's D-29 to D-33 (00:57 Oct 28 PT; sealed; verbatim)

<!-- verbatim begin -->
SEALED — no revisions. All ranges inclusive. "Bits" = binary bits. "Op-class" = op-class v1 unless named. "Balanced" = theta 0.5. "Cheaper" = lower cost. "QS-best" = strictly highest success per op-class cost; exact ties do not count as QS-best.
D-29: prediction 11 bits; range 7.5–15.5 bits. QS reference card alone, balanced semiprimes, op-class v1 cost per number, doubling period between 80 and 96 bits. Chat gives wall, not absolute op-class cost; proxy from after-allocate-once wall 84/96 ratio ≈2.29 gives ≈10.1 bits, 72/84 gives ≈11.6. Assumption: op-class cost per wall-ms roughly constant across 84–96; transfer across sizes, so widened. Confidence 25%. Falsifier: measured doubling period outside 7.5–15.5 bits.
D-30: chat-only: missing. Sealed fallback, outside prior labelled information only: prediction 4 bits; range 2.5–6.5 bits. Balanced rho expected cost ~N^1/4, ~4-bit doubling period; not chat-derived. Confidence 15%. Falsifier: outside 2.5–6.5 bits.
D-31: prediction 80 bits; range 56–96 bits (nominal ±30% band 56–104, censored at the 96-bit run limit). Rho cost curve missing in chat. Cross = lowest size in {40, 48, …, 96} where rho op-class cost per balanced number exceeds QS reference-card op-class cost per number; no cross by 96 = ">96". Outside prior information only for the rho side. Confidence 15%. Falsifier: crossover ≤56 or >96 / no cross.
D-32: prediction 0.36 theta; range 0.25–0.40 theta (nominal ±30% censored upward at 0.40 because the older sketch says only QS succeeds at 0.39+). Today's card/meter, 96 bits, theta bands of 0.02, each lamp alone with reference budget, op-class v1. "Lowest theta" = lower edge of the first band where QS is strictly QS-best. Sketch is older card/meter; transfer widened. Confidence 30%. Falsifier: outside 0.25–0.40.
D-33: robust ratio range 0.60–1.40 (below 1 = specialist cheaper). Gene-only evolved pipeline trained on theta 0.33–0.40, validated on sealed held-out 96-bit numbers vs reference card; robust = worst (max) of op-class v1, ruint, Montgomery. No training results in chat; wide. Confidence 20%. Falsifier: outside 0.60–1.40.
Information only: prioritise a per-candidate, per-op trace in the 0.33–0.40 band at 96 bits recording, at matched theta, the marginal cost and success probability of one extra QS partial relation versus one extra ECM curve under the same op meter, to locate which sub-cost (sieve, root test, large prime, confirm) a new method must beat.
<!-- verbatim end -->

**The reviewer's notes:**
- **D-29's arithmetic checks:** the post-allocate-once wall goes from 1.338 ms at 84 bits to 3.058 ms at 96, a ratio of 2.29, which is a doubling period of about 10.1 bits.
- **A confidence inconsistency.** The ranges are set wide, but the confidences are 15–30%: DeepSeek expects to miss 70–85% of the time, against its own 80–85% coverage target. A low stated confidence also lowers its Brier penalty on a miss. **Recorded as filed.** The ranges are scored with the interval score, each read as an 80% interval, as for every forecaster.
- **D-30 and D-31 rest partly on an outside theoretical prior,** labelled by DeepSeek. Recorded.
- **Its information-only suggestion is added to the Novelty Plan:** measure the twilight band's exchange rate. That is the marginal op-class cost and success gain of one extra QS partial relation against one extra ECM curve, at matched θ.

## The reviewer's R-32 / R-33 (Oct 28; sealed; verbatim)

      R-32 Light spectrum v1, 96 bits: lowest theta band where QS is strictly best by success per op-class
           cost: 0.34 to 0.42. 65%.
      R-33 Twilight specialist vs reference on theta 0.33-0.40 at 96 bits, robust ratio: 0.80 to 1.02
           (a modest gain or none). 60%.

**Notes on scope** (the ranges are unchanged):
- **D-32 and R-32's "reference budget":** in the reference pipeline td and ECM have budget 0 and CFRAC is absent. The runner states the stand-ins: td and ECM at the earlier maps' 2^21 cap; CFRAC with its accepted genes at the QS cap.
- **"The reference" in D-33 and R-33:** the validation reports both the reference card (QS alone) and the reference pipeline. D-33 names the card. R-33 says "reference" without saying which, so it is scored against the reference card, the same comparison as D-33, unless the user rules otherwise before the validation run.

## Grok's

Pending (the user decides whether to relay).

**Disclosure (Claude, after filing):** the light spectrum's counts had been started in the background before this file was committed (light_spectrum.py, committed first). When this file was filed, Claude stopped that run **without reading any of its output**. The partial output was moved, unread, to Claude's scratch. The spectrum will be run again from the start through `tools/sealed_run.sh growth-spectrum-twilight`, after this commit, so R-32 and D-32 are scored on a run that began after sealing.
