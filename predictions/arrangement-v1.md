# arrangement-v1: the arrangement lamp family ("arrangement + detection rule"), predictions

**Status: the reviewer's sealed; DeepSeek and Grok pending. Nothing is built or run.** The design is `docs/planning/arrangement_lamps.md` as of 70d374a: approved in principle by the user (Oct 29), with the reviewer's amendments. The fitness is G_rho (`reviews/growth_fitness_rho.md`, frozen 77ff2ee), with G (`reviews/growth_fitness.md`, frozen c86ef35) beside it.

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

## Grok's

Pending (the user decides whether to relay).
