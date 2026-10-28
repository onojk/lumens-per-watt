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

## Grok's G-22 to G-26 (01:00 Oct 28 PT; sealed; verbatim)

<!-- verbatim begin -->
G-22 (QS doubling period, 80–96 bits, op-class cost per balanced number, reference card). Prediction: 12 bits. Range: 8–16 bits (arithmetic: measured wall-time growth 1.82× / 2.15× over the two +12-bit steps from the given 0.876 / 1.592 / 3.425 ms figures, converted via log₂, then widened ±33% for op-class vs wall and for the allocate-once differential savings that shrink with size). Base: reference card, balanced semiprimes, op-class v1. Comparison: bits of size increase that double that cost. Confidence: 65%. Falsifier (single condition): measured op-class cost ratio from 80 to 96 exceeds 4× (i.e. doubling period < 8 bits).
G-23 (rho doubling period, balanced semiprimes). Prediction: 4 bits. Range: 3–5.5 bits (arithmetic: leading term √p ∼ 2^{b/4} for balanced p ∼ 2^{b/2} implies exact doubling every 4 bits; ±30%+ widened for lower-order constants and implementation). Base: Pollard's rho, balanced semiprimes. (Theoretical leading term labelled information-only; no direct measured rho costs given.) Confidence: 75%. Falsifier (single condition): measured rho cost ratio over any +8-bit step in the 40–96 range is < 3× (i.e. doubling period > 5.5 bits).
G-24 (bit size of rho vs QS cost-curve cross, balanced, sizes in {40,48,56,64,72,80,88,96}). Prediction: 76 bits. Range: 56–96 bits (arithmetic: theoretical rho doubles every 4 bits while measured QS wall grows every ∼11–14 bits; cross estimated by extrapolating the given QS times against a rho whose 80-bit cost is still higher in the external comparison cited below, then widened heavily for constant factors and the project's SIQS being faster than the cited implementations). Base: project reference-card QS (op-class) vs project rho, balanced numbers. "Cross" = smallest listed size at which QS cost ≤ rho cost. (Information-only external: one student implementation saw rho still faster at 80 bits and QS faster at 100 bits.) Confidence: 55%. Falsifier (single condition): at 72 bits the measured op-class cost of the reference-card QS already undercuts rho on balanced numbers.
G-25 (lowest θ at which QS has best success-per-op-class-cost, 96 bits, θ-bands of 0.02, each lamp alone, today's card & meter). Prediction: 0.36. Range: 0.32–0.40 (arithmetic: given older-card sketch shows QS sole survivor ≥ 0.39 and ECM/QS within 1–2.5× throughout 0.33–0.40; today's card assumed modestly better, centre of the competitive band taken, width covering one full 0.02 band either side). Base: today's reference card, op-class v1, 96-bit, success/cost. "Best" = strictly lowest cost among lamps that achieve positive success in that band under the reference budget. Confidence: 60%. Falsifier (single condition): in the 0.34 band the measured op-class success/cost of QS is worse than that of ECM (or any other single lamp).
G-26 (twilight specialist robust ratio vs reference card, 96-bit held-out, θ 0.33–0.40). Prediction: 0.75. Range: 0.45–1.05 (arithmetic: given ECM/QS already within 1–2.5× in the band ⇒ a gene-only specialist can be expected to capture a 1.3–2× improvement on the reference card; centre 0.75, ±40% widened for evolution variance, robust-ratio (worst of three pricings) conservatism, and sealed-set noise). Below 1 = specialist cheaper. Base: gene-only evolved pipeline trained on 0.33–0.40, validated on sealed held-out 96-bit numbers, robust ratio (worst of op-class / ruint / Montgomery) versus reference card on the same band. Confidence: 50%. Falsifier (single condition): the measured robust ratio on the sealed held-out set is ≥ 1.1.
Information-only: The light-spectrum setup can mislead if the op-class v1 weights (calibrated on the reference card's typical balanced path) systematically mis-price the instruction mix of the other lamps when they are run alone at low θ, so that a lamp whose real retired-instruction count is high appears artificially cheap. A direct check is to re-run the identical spectrum experiment under callgrind (or the existing op-class instrumentation) on every lamp and verify that the charged op-class cost stays within a small factor of actual instructions retired inside each θ band.
<!-- verbatim end -->

**The reviewer's notes:**
- **G-24's falsifier contradicts its range.** The falsifier fires if QS is already cheaper than rho at 72, while the range (56–96) allows a cross at 56–64. Both are recorded as written and scored separately.
- **G-25 redefines "best"** as the lowest cost among lamps with any success. It is scored on the question as asked: success per unit of op-class cost.
- **G-26's reasoning does not follow.** "ECM and QS within 1–2.5×" does not imply a 1.3–2× gain for a specialist. Recorded.
- **G-23's falsifier fires on ANY 8-bit step** below 3×, so noise at small sizes may trigger it. Recorded.
- **External figures** (a student implementation's rho / QS crossover) are labelled information only by Grok.
- **Added to item 1, the light spectrum,** from Grok's information-only point:
  - for each lamp in each θ band, report the total instructions retired (callgrind, attribution-free) beside its op-class cost;
  - flag any band where op-class ÷ instructions differs from that lamp's average by more than 25%.
  - The reason: pooled v1 weights can mis-price a lamp run alone. For example `word` weighs 1.3 in p−1 against 71 in qs.

**All three forecasters are sealed** for this round: the reviewer R-29 to R-33, DeepSeek D-29 to D-33, Grok G-22 to G-26.

**Disclosure (Claude, after filing):** the light spectrum's counts had been started in the background before this file was committed (light_spectrum.py, committed first). When this file was filed, Claude stopped that run **without reading any of its output**. The partial output was moved, unread, to Claude's scratch. The spectrum will be run again from the start through `tools/sealed_run.sh growth-spectrum-twilight`, after this commit, so R-32 and D-32 are scored on a run that began after sealing.
