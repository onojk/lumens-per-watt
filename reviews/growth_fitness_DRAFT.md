# Growth fitness G (DRAFT)

**Status: DRAFT. Not frozen; nothing is scored with it.** Written at the reviewer's request (Oct 28) as the Novelty Plan phase 3 gate: "growth fitness frozen before anything is scored with it". Freezing it is the user's decision. Until then, the earlier design line in NOTES ("a card's local slope ÷ the reference's at 88–96") is superseded only by the user's choice between the two (§6, point 1).

## 1. Definition

**G = (the reference card's doubling period, 80–96 bits) ÷ (the candidate's doubling period, 80–96 bits)**, op-class v1 primary.

- **Doubling period** = 16 ÷ log2(C(96) ÷ C(80)), where C(b) is the mean cost per factorisation at b bits (total cost over all numbers ÷ successes, as `growth_harness.py per_fact` defines it). It is the chord over 80–96, not a fitted slope.
- **G > 1 means the candidate's cost grows faster.** Its cost doubles in fewer bits than the reference's, so it scales worse.

  > **Direction to confirm.** The brief says "G > 1 = slower growth". With the reference's period in the numerator, G > 1 means the candidate's period is **shorter**, which is **faster** growth. Either the ratio is inverted (G = candidate ÷ reference, so G > 1 means slower growth and is better) or the label is. This draft does not choose; the user does, before freezing (§6, point 2). The numbers below are stated as periods so they hold either way.

- **The reference value** (op-class v1, sealed counts run 68250b3, 48 balanced numbers per size): **9.29 bits**.

## 2. The reference under all four pricings

Bootstrap: 10,000 resamples of the 48 numbers within each size, `random.Random(2026)`, 2.5–97.5% interval. It is computed from the committed `evolve/growth_counts.json`, untimed.

| pricing | QS doubling period 80–96 (bits) | 95% interval |
|---|---|---|
| **op-class v1 (primary)** | **9.29** | 8.74 – 9.89 |
| ruint | 8.80 | 8.26 – 9.39 |
| Montgomery | 8.69 | 8.17 – 9.25 |
| official | 7.63 | 7.16 – 8.16 |

The pricings disagree on QS's growth by about 20% (7.6 to 9.3 bits). Official counts a sieve update and a big multiply alike, so the work that grows fastest weighs relatively more under it.

## 3. Rules

1. **G is reported under all four pricings,** each candidate period over the reference's period under the **same** pricing. Op-class v1 is primary. Robust rule (b) applies to any verdict: the worst of op-class, ruint and Montgomery, with official reported but not a veto.
2. **The interval:** a paired bootstrap of G. Candidate and reference run on the same numbers at each size, resampled together (10,000 resamples, seeded). A verdict needs the whole interval on one side of 1.
3. **Minimum successes:** at least 24 of 48 at both 80 and 96 bits for that lamp or card, or G is "not defined". This is the harness's rule; p−1 at its reference B fails it everywhere.
4. **Interpolated genes:** the reference QS at 80 and 88 runs on genes interpolated between the sealed sizes ("interpolated genes, growth harness only", daf0986); 80 is an endpoint of G's chord. A candidate is compared with the reference **as defined, including the interpolation**, and every G report states it. If the reference's genes at 80 are retuned or sealed later, the reference period is re-measured and G's reference value changes prospectively.
5. **Pricing disagreement on the crossing:**
   - the rho / QS crossing moves from below 40 bits (op-class, ruint) to 40–48 (Montgomery) and 56–64 (official);
   - a candidate whose growth gain depends on a pricing's view of the small sizes can win under one pricing and lose under another;
   - G is a growth ratio over 80–96 only. It says nothing about which lamp is cheaper at a given size; cost at size stays the robust ratio (c).
6. **Wall clock:** when the growth wall step runs (held for the load condition), a wall-clock doubling period is added as a fifth column, for information. It does not enter the verdict until the user decides.

## 4. What G does not measure

- **Absolute cost.** A card can have G favourable and still cost more at every size in 40–96. G is reported beside the robust cost ratio at 96, never alone.
- **Growth outside 80–96.** Above 96 is lampcore's ceiling; below 80, the interpolated genes and small-size overheads dominate.
- **Noise from the chord's endpoints.** The interval is about ±6% on the reference (§2), so a G inside about 0.94–1.06 is not separable from the reference with 48 numbers per size.

## 5. Checks before freezing

1. **Reference against itself:** run the reference on a fresh number set (new seeds); its G against the committed reference must contain 1 in its interval.
2. **A known-worse candidate:** for example, QS on the 54-bit genes held at every size. It must give a G on the "worse" side, with its interval excluding 1.
3. **Rho as a sanity point:** rho's period (4.05 bits) against QS's (9.29) gives a strongly unfavourable G, about 2.3× the reference's growth rate.

## 6. Open points for the user

1. **The window:** the 80–96 chord (this draft) or the 88–96 local slope (the earlier NOTES design line). The chord has less noise; the local slope is closer to the asymptote.
2. **G's direction** (§1): reference ÷ candidate, or candidate ÷ reference, so that "G > 1" means what the label says.
3. **Numbers per size:** 48 (the harness) or more at 80 and 96 to narrow the interval.
4. **Whether the wall-clock period** ever enters the verdict.
