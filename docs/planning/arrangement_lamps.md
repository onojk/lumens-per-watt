# Arrangement lamps: "arrangement + detection rule" (DRAFT; the user's "Seven of Nine" card, stage 3)

**Status: DRAFT for the user. Nothing is built or run.** No code until the user has seen this design. No scored run until predictions are sealed (`predictions/<id>.md`, `tools/sealed_run.sh`).

Novelty Plan: phase 4 (program search: a building-block family, metered by construction, the proposer locked out, scored on growth). Phase 2's "judge locked away" item is a precondition (§6).

## 1. The idea

Tower N's dots are placed in some order (the **arrangement**), and a **detection rule** notices a hidden collision: two dots that agree mod p but not mod N. gcd with N reveals p. The value-line lens (stage 1) shows the collisions; the vl lamp (stage 2) is the slowest arrangement, placing k = 2, 3, … with a gcd per dot, and costs p − 1 gcds. Rho is the arrangement x → x² + c mod N with cycle detection, needing about √(πp/2) steps.

**The question this family can answer:** does evolution, given building blocks and an honest meter, rediscover rho-shaped layouts (a pseudo-random map plus cycle detection, about p^(1/2) steps)?

**What it cannot answer:** anything sub-exponential. Every collision-only arrangement over a random-looking map is bounded below by the birthday limit, about p^(1/2) steps (§5). Gains past rho need structure (smoothness, relations: p−1, ECM, QS), which this family does not contain except through the optional exponent arrangement (§2).

## 2. The genome

A genome is one stage, `{"t": "arr", "layout": {...}, "detect": {...}, "ob": budget}`. It can be placed in a pipeline like any pre-stage.

**Layouts** (the order dots are placed; each produces x_i mod N):

| layout | genes | x_i | charge per dot |
|---|---|---|---|
| stride | start a, stride s | a + s·i | one `word` (an add) |
| fold | width w, stride s | the stride walk in blocks of w, with the block's product accumulated mod N | one `mul` per dot |
| map | c, degree d (even, 2–8), x0 | x_{i+1} = x_i^d + c mod N | rho's step cost: (log2 d + popcount d − 1) × `mul` |
| squares bins | multiplier m, bins B | x_i = (m·i)² mod N, placed into B bins by low bits | one `mul` and one `hash` per dot |
| exponent (optional) | base a, bound B | x_k = a^(k!) mod N (p−1's arrangement) | `mul` per modular multiply, as p−1 |

**Detection rules** (when to test for a collision):

| rule | genes | test | charge |
|---|---|---|---|
| per dot | – | gcd(x_i − t, N), t = a fixed target (0 for stride: the vl lamp) | one `gcd` per dot |
| batched | b | product of b differences mod N, then one gcd | one `mul` per difference, one `gcd` per batch |
| Floyd | – | gcd(x_i − x_2i, N): the map run twice | the second walk's steps plus one `gcd` (or batched) |
| Brent | b | as lampcore's rho (power-of-two checkpoints) | as rho |
| bin compare | – | within a bin, gcd(x − y, N) for each pair | one `sort_cmp` per compare, one `gcd` per pair |

**Not evolved:** N, the meter, prices, the harness, the numbers. Genes are bounded: d ≤ 8, b ≤ 4,096, w ≤ 4,096, B ≤ 2^16, ob ≤ the pipeline's budget.

## 3. Charging (the meter is sacred)

- **Every placed dot and every gcd is charged,** using existing op types only (`word`, `mul`, `gcd`, `hash`, `sort_cmp`), at op-class v1's frozen weights.
- A new op type, if one is needed, gets its cost model in NOTES before code, and the user's decision before it is priced.
- **Parity:** Python and lampcore, identical ops, tests, factor and per-type counts. The vl lamp (stage 2) is the template, and stride + per-dot must reproduce vl exactly (a built-in check).
- **The gcd cost-growth finding** (NOTES, "gcd cost against N's size"; `bench/gcdbench`): op-class v1 prices every gcd flat (1,401.7 units). Measured instructions per gcd grow with N's size:
  - against a small k (the vl dots), about 325 instructions while N fits one 64-bit limb, and about 590 at 96–128 bits;
  - against a uniform k (rho, p−1, ECM), about 440 → 845 over 24–64 bits (about 10 per bit), 1,590 at 96 and 2,135 at 128.
  
  So op-class v1 overcharges gcds below about 80 bits and undercharges above about 96. In this family gcds can dominate (per-dot detection), so the cost is reported two ways:
  1. **op-class v1** (frozen; primary; the verdict);
  2. **op-class v1 with a size-scaled gcd price beside it, for information only:** gcd units = 1,401.7 × (measured instructions per gcd at N's size, small or uniform k as the rule uses) ÷ (the instructions the flat price stands for, 1,401.7 × 0.909). The 0.909 is QS's instructions per op-class unit from the twilight meter-health check.
  
  A verdict that changes between the two is flagged. Whether the scaled price ever becomes primary is the user's pricing decision. It is not made here, and op-class v1's weights are not changed.

## 4. Fitness

- **G, frozen** (`reviews/growth_fitness.md`, c86ef35): candidate doubling period ÷ the reference card's (QS) over 80–96 bits, all four pricings, op-class primary, paired bootstrap, at least 24 / 48 successes per end.
  - Every arrangement lamp is expected to grow far faster than QS: rho's G is about 0.44 (4.05 ÷ 9.29).
  - At 80–96 bits, p ~ 2^40–2^48. A p^(1/2) arrangement needs about 2^20–2^24 steps, which is feasible in lampcore. A walk (p steps) is not, and is censored by its budget, so G is "not defined" for it under the minimum-successes rule.
- **Proposed, not frozen: G_rho.** The same definition and machinery as G, with **rho (the reference card's rho genes, alone)** as the reference and the **40–64 chord** as the window. Here walks, maps and bins all succeed, so the family can be ranked against its natural baseline.
  - G_rho must be frozen by the user, before anything is scored with it, the same way G was frozen.
  - Until then, only G (frozen) is scored, and G_rho is reported for information.
- Cost at a fixed size (the robust ratio c against rho alone, at 48 and 64 bits) is reported beside growth, never alone (G's rule 5).

## 5. The baseline and the expected best

- **Baseline: rho** (Brent, x² + 1, lampcore's genes), measured on the same numbers.
- **The birthday limit:** for any layout whose x_i mod p behave like random draws, the first collision mod p comes after about √(πp/2) dots. No detection rule can see a collision before it exists. So for the map, fold and bins layouts the best possible growth is about p^(1/2), a log2-steps slope of about 0.25 per bit of N. That is rho's, and "rediscovers rho" is the expected best outcome.
- **Structured layouts:**
  - stride walks find p at the first multiple, about p steps (slope 0.5);
  - squares bins compare values mod N, so a collision mod p is visible only through pairwise gcds (quadratic in the dots per bin) or products. They should not beat the birthday limit, and with bin-compare detection they pay √p² compares;
  - the exponent arrangement is p−1, erratic, depending on p−1's smoothness. With it allowed, the family can "rediscover p−1" on smooth-p numbers. It is optional, and the user decides whether it is in the gene pool.
- **The origin-dots shape check** (`explore/origin_dots.py`, unmetered) already shows walk 0.503, rho 0.254 and p−1 0.253 (erratic) per bit at 20–40 bits.

## 6. The guard: the proposer cannot touch the judge

- **What the proposer is allowed to touch:** the search operates only on genome JSON (the genes in §2). It never edits code. A candidate's only output is a genome file.
- **Pinned judge files:** the judge (lampcore binary sha256, `evolve/optypes.py`, `opclass/opclass_v1.json`, `evolve/calibrate.json`, the harness script, `predictions/<id>.md`) is pinned by hash in the predictions file before the run.
- **Checked twice:** the harness checks every pinned hash at the start of the run and again before writing results. A mismatch stops the run as a failure, committed as a result.
- **Separate processes:**
  - the search runs in a separate process with the repo checked out read-only (a git worktree, with the judge files' paths not writable);
  - scoring runs only through `tools/sealed_run.sh`, which refuses if `predictions/<id>.md` is not committed and clean.
- **This is Novelty Plan phase 2's "judge locked away" item.** If phase 2 is not done when this runs, this design's guard is the minimum, and the user decides whether that suffices.

## 7. Questions to seal (forecasters, before any scored run)

1. **Does evolution rediscover a rho-shaped layout?** Defined as: the best genome uses the map layout (any c, d) with a cycle-detection rule (Floyd or Brent, batched or not), and its log2-steps slope over 40–64 bits is within 0.20–0.30 per bit. Yes or no, with a probability.
2. The best genome's G (frozen, 80–96, op-class), or "not defined".
3. The best genome's cost ratio against rho alone at 64 bits, op-class v1, with a range; and the same under the size-scaled gcd price.
4. Does any non-map layout (stride, fold, bins) beat a slope of 0.45 per bit? Yes or no.
5. Optional, if the exponent arrangement is in the pool: does the search select it on θ < 0.3 numbers?

## 8. Run plan (only after the user's approval and sealing)

1. Cost model in NOTES for each layout and rule (charges per §3), then code in Python and lampcore. Parity, including stride + per-dot = vl exactly.
2. The training map at 40, 48, 56 and 64 bits (untimed counts), and the search (a coordinate search over the genes, as the twilight search). STOP to report the genome.
3. Validation on held-out numbers: G (frozen) at 80–96 where defined, G_rho if frozen by then, cost against rho; both gcd pricings.
4. A wall arm only if a prediction names it.

## 9. Decisions for the user

- Approve or amend the design.
- Freeze G_rho (or not) before scoring.
- Whether the exponent arrangement is in the pool.
- The gcd pricing question (§3): stay flat (op-class v1) with the scaled view as information, or define a size-scaled gcd price as a new pricing (a prospective change, v2).
