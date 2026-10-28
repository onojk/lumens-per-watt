# Growth fitness G

**Status: FROZEN, 2026-10-28** (the user's ruling, Oct 28; frozen in the commit that renamed this file from `growth_fitness_DRAFT.md`). It is the Novelty Plan phase 3 gate: "growth fitness frozen before anything is scored with it". **Nothing was scored with G before this commit.** Any change from here is a new version (G v2), made prospectively by the user's decision. This version's verdicts stand.

The draft (5fb0668) had G = reference ÷ candidate, while its label said "G > 1 = slower growth"; the user's ruling fixes the ratio (§1). The earlier NOTES design line, "a card's local slope ÷ the reference's at 88–96", is superseded.

## 1. Definition

**G = (the candidate's doubling period) ÷ (the reference card's doubling period)**, both under the same pricing. Op-class v1 is primary.

- **G > 1 means slower growth,** which is better: the candidate's cost takes more bits of N to double.
- **Doubling period over a chord a–b:** (b − a) ÷ log2(C(b) ÷ C(a)). C(s) is the mean cost per factorisation at s bits: total priced cost over all numbers, censored spending included, ÷ successes (`growth_harness.py per_fact`).
- **Primary window: the 80–96 chord.**
- **Gene check: the 84–96 chord,** reported beside it. Both its ends run on sealed reference genes, while 80 runs on interpolated ones. If the 80–96 and 84–96 intervals do not overlap, under the candidate or the reference, the report flags it, and the verdict rests on neither window until the user rules.

## 2. The reference

The reference card's QS, 48 balanced semiprimes per size, `semiprimes_pq(bits, 48, 9600000 + bits)`.
- **The 80–96 chord** comes from sealed counts run 68250b3 (`evolve/growth_counts.json`).
- **The 84-bit end of the 84–96 chord** comes from `evolve/growth_gref.py` (7709517), untimed, 48 / 48 succeeded.
- **The interval:** 10,000 bootstrap resamples within each size, `random.Random(2026)`, 2.5–97.5%.

| pricing | doubling period 80–96 (primary) | 95% interval | doubling period 84–96 (gene check) | 95% interval | intervals overlap |
|---|---|---|---|---|---|
| **op-class v1 (primary)** | **9.29 bits** | 8.75 – 9.89 | 9.17 bits | 8.43 – 10.06 | yes |
| ruint | 8.80 | 8.26 – 9.39 | 8.69 | 7.96 – 9.56 | yes |
| Montgomery | 8.69 | 8.17 – 9.25 | 8.61 | 7.89 – 9.46 | yes |
| official | 7.63 | 7.16 – 8.16 | 7.56 | 6.93 – 8.35 | yes |

**The interval's lower bound,** 8.75 here against 8.74 in the draft and the ruling, differs only by the quantile index (`bs[250]` in the committed script against `bs[249]` in the draft's check). The committed script's value stands.

**The interpolated genes at 80** don't move the reference's growth beyond noise: the 84–96 chord, on sealed genes only, gives 9.17 against 9.29.

## 3. Rules

1. **G is reported under all four pricings,** each pricing's candidate period over the reference's period under that pricing. Op-class v1 is primary. A verdict follows robust rule (b): the worst of op-class, ruint and Montgomery, with official reported but not a veto.
2. **The interval:** a paired bootstrap of G.
   - Candidate and reference run on the same numbers at each size, resampled together (10,000 resamples, seeded).
   - "Slower growth" or "faster growth" needs the whole interval on one side of 1.
3. **Minimum successes:** at least 24 of 48 at each chord end (80, 84 and 96), for the candidate and for the reference. Otherwise G is "not defined" for that window.
4. **Genes:** a candidate is compared with the reference as defined here, including the interpolated 80-bit genes, and every G report states it. If the reference's genes at 80 are later sealed or retuned, the reference is re-measured, and that is a new version.
5. **Pricing disagreement:**
   - the rho / QS crossing moves from below 40 bits (op-class, ruint) to 40–48 (Montgomery) and 56–64 (official);
   - G covers growth over 80–96 only;
   - cost at a given size stays the robust cost ratio (c), and G is always reported beside the robust cost ratio at 96, never alone.
6. **Wall clock:** when the growth wall step runs (held for the load condition), a wall-clock doubling period is added as a fifth column, for information. It doesn't enter a verdict unless the user decides it should.

## 4. What G does not measure

- **Absolute cost.** A card can have G > 1 and still cost more at every size.
- **Growth outside 80–96.** Above 96 bits is lampcore's ceiling; below 80, the interpolated genes and small-size overheads dominate.
- **Resolution:**
  - the reference's own interval is about ±6% on 80–96, so a G within about 0.94–1.06 is not separable from 1 at 48 numbers per size;
  - the paired bootstrap narrows this for candidates that share the reference's numbers;
  - more numbers per size would narrow it further.

## 5. Sanity points (from the committed counts; not verdicts)

- **Rho:** 4.05 ÷ 9.29 ≈ 0.44 on the 40–96 local slopes. That is much faster growth, as theory expects.
- **Reference against itself** on fresh numbers: the interval should contain 1. This is not yet run; it is the first G report's control arm.
