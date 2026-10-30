# Growth fitness G_rho (the arrangement family's growth fitness)

**Status: FROZEN, 2026-10-29** (the user's ruling, Oct 29: G_rho approved, with the window changed to 48–80 bits). It is frozen in the commit that adds this file. **Nothing was scored with G_rho before this commit.** Any change from here is a new version (G_rho v2), made prospectively by the user's decision.

It is the companion of G (`reviews/growth_fitness.md`, frozen c86ef35), which it does not replace. G compares against the reference card's QS over 80–96 bits. G_rho compares against rho, the arrangement family's natural baseline, over 48–80 bits, where walks, maps and bins can all succeed.

## 1. Definition

**G_rho = (the candidate's doubling period) ÷ (rho's doubling period)** over the **48–80 chord**, both under the same pricing.

- **G_rho > 1 means slower growth,** which is better.
- **Doubling period over a chord a–b:** (b − a) ÷ log2(C(b) ÷ C(a)). C(s) is the mean cost per factorisation at s bits: total priced cost over all numbers, censored spending included, ÷ successes. This is G's definition (`growth_harness.py per_fact`).
- **Why 48–80** (the user's reason): 40–64 sits inside one 64-bit limb and misses the step where N needs a second 64-bit word. That step shows in the gcd cost (`bench/gcdbench`, dd2db46) and in the twilight wall arm's rho stage (92802f6). 48–80 crosses it.

## 2. The reference

**Rho alone,** `partition.PRE["rho"]` genes, on 48 balanced semiprimes per size, `semiprimes_pq(bits, 48, 9600000 + bits)`, from sealed counts run 68250b3 (`evolve/growth_counts.json`). Computed by `evolve/growth_rho_ref.py` (9ebeabc), with no new run. 48 / 48 succeeded at both ends. The interval comes from 10,000 bootstrap resamples within each size, `random.Random(2026)`, 2.5–97.5%.

| pricing | rho doubling period 48–80 | 95% interval |
|---|---|---|
| **op-class v1 (primary)** | **3.936 bits** | 3.790 – 4.098 |
| ruint | 3.938 | 3.788 – 4.094 |
| Montgomery | 3.947 | 3.801 – 4.108 |
| official | 3.935 | 3.788 – 4.093 |
| op-class v1, size-scaled gcd (`evolve/gcdscale.py`, uniform-k) | 3.932 | 3.786 – 4.088 |

Rho's gcds are 1.3% (48 bits) and 1.1% (80 bits) of its op-class cost, so the gcd scaling barely moves the reference. It can move a candidate whose cost is mostly gcds.

## 3. Rules

1. **Pricings:** G_rho is reported under op-class v1 (primary), ruint, Montgomery, official, and op-class v1 with the size-scaled gcd price.
   - **For the arrangement family, the worst-of set is op-class v1, ruint, Montgomery and the size-scaled gcd price** (the user's ruling, Oct 29). Official is reported, not a veto.
   - **A win under the flat gcd price that does not hold under the scaled price is a pricing artifact.** It is flagged and not adopted.
   - The scaled price uses the small-k curve where the gcd's other argument fits one 64-bit word, and the uniform-k curve elsewhere. Each candidate's report states which curve each of its gcds used.
2. **The interval:** a paired bootstrap of G_rho. Candidate and rho run on the same numbers at each size, resampled together (10,000 resamples, seeded). "Slower growth" or "faster growth" needs the whole interval on one side of 1.
3. **Minimum successes:** at least 24 of 48 at 48 and at 80 bits, for the candidate and for rho. Otherwise G_rho is "not defined".
4. **Beside, never alone:** G_rho is always reported beside the cost ratio against rho at 64 and 80 bits (robust, the same worst-of set), and beside G (frozen) where G is defined.
5. **Rediscoveries:** a candidate whose genome is a p−1 or rho arrangement (the exponent layout, or the map layout with cycle detection) is reported as **"rediscovered known lamp"**, never as novelty, whatever its G_rho.
6. **Reference genes:** rho's genes are `partition.PRE["rho"]`, as in the growth counts. If they change, rho is re-measured, and that is a new version.

## 4. What G_rho does not measure

- **Absolute cost.** A candidate can grow more slowly and still cost more at every size.
- **Growth outside 48–80,** including the QS range (that is G's job).
- **Resolution:** rho's own interval is about ±4% (3.79–4.10), so a G_rho within about 0.96–1.04 is not separable from 1 at 48 numbers per size, before pairing.

## v2 (the user's ruling, Oct 29; before anything was scored with v1 or v2)

§3 rule 1's "the gcd's other argument fits one 64-bit word" becomes **"the gcd's other argument is < 2^32"** (the small-k curve; the uniform-k curve elsewhere). The reason: at 48–64 bits every residue mod N fits one word, so the v1 wording put differences mod N on the small-k curve. That contradicts the ruling 558b18f, which puts differences mod N on the uniform curve, and the gcd bench's small-k definition (k = 2, 3, …). It also priced an algorithm identical to rho differently from rho. Everything else in v1 stands. NOTES, "Ruling: the scaled gcd price's small-k label".
