# Arrangement lamps: "arrangement + detection rule" (the user's "Seven of Nine" card, stage 3)

**Status: APPROVED IN PRINCIPLE (the user, Oct 29), with rulings 1–3 folded in (§3, §4, §2, §9). Nothing is built or run.** The reviewer reads this after the push, before predictions are sealed. No code and no scored run until then (`predictions/<id>.md`, `tools/sealed_run.sh`).

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
| squares bins | multiplier m, bins B | x_i = (m·i)² mod N, placed into B bins by low bits | one `mul` and one `hash` per dot (see §5: the bins carry no information about x mod p) |
| exponent (in the pool, the user's ruling) | base a, bound B | x_k = a^(k!) mod N (p−1's arrangement) | `mul` per modular multiply, as p−1 |

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
  
  So op-class v1 overcharges gcds below about 80 bits and undercharges above about 96. In this family gcds can dominate (per-dot detection).
- **The ruling (the user's, Oct 29, option (a); NOTES 558b18f).** Op-class v1 stays frozen and primary. Beside it goes **op-class v1 with a size-scaled gcd price** (`evolve/gcdscale.py`): gcd units = measured instructions per gcd at N's size ÷ 0.909.
  - The instructions come from `bench/gcdbench/gcd_ir.json`, interpolated linearly in bits.
  - The small-k curve applies where the gcd's other argument fits one 64-bit word, and the uniform-k curve elsewhere.
  - **For this family the scaled price joins the worst-of set:** an advantage must hold under op-class v1, ruint, Montgomery and the scaled price. A win only under the flat price is flagged as a **pricing artifact** and not adopted.

## 4. Fitness

- **G, frozen** (`reviews/growth_fitness.md`, c86ef35): candidate doubling period ÷ the reference card's (QS) over 80–96 bits, all four pricings, op-class primary, paired bootstrap, at least 24 / 48 successes per end.
  - Every arrangement lamp is expected to grow far faster than QS: rho's G is about 0.44 (4.05 ÷ 9.29).
  - At 80–96 bits, p ~ 2^40–2^48. A p^(1/2) arrangement needs about 2^20–2^24 steps, which is feasible in lampcore. A walk (p steps) is not, and is censored by its budget, so G is "not defined" for it under the minimum-successes rule.
- **G_rho, FROZEN 2026-10-29** (`reviews/growth_fitness_rho.md`, 77ff2ee; the user's ruling). Candidate doubling period ÷ rho's (`partition.PRE["rho"]`, alone) over the **48–80 chord**.
  - The window crosses the one-word to two-word step, which 40–64 would miss.
  - Rho's reference: 3.936 bits op-class [3.790, 4.098], from sealed counts 68250b3.
  - The worst-of set is op-class v1, ruint, Montgomery and the size-scaled gcd price. At least 24 / 48 successes at 48 and 80.
  - **G_rho is this family's primary growth fitness.** G (80–96) is reported beside it where defined.
- Cost at a fixed size (the robust ratio c against rho alone, at 48 and 64 bits) is reported beside growth, never alone (G's rule 5).

## 5. The baseline and the expected best

- **Baseline: rho** (Brent, x² + 1, lampcore's genes), measured on the same numbers.
- **The birthday limit:** for any layout whose x_i mod p behave like random draws, the first collision mod p comes after about √(πp/2) dots. No detection rule can see a collision before it exists. So for the map and fold layouts the best possible growth is about p^(1/2), a log2-steps slope of about 0.25 per bit of N. That is rho's, and "rediscovers rho" is the expected best outcome.
- **Structured layouts:**
  - stride walks find p at the first multiple, about p steps (slope 0.5);
  - **squares bins (the reviewer's amendment, Oct 29):**
    - binning by the low bits of x mod N carries no information about x mod p, so dots that agree mod p land in bins at random, and the bins cannot expose mod-p collisions;
    - bin compare detects only exact equality mod N (x² ≡ y² mod N, a Fermat-type square congruence), a different and rarer event;
    - a mod-p collision is reachable only through gcds of differences across bins, which the bins do not organise;
    - **so the expected result for bins is worse than the birthday limit, not equal to it;**
  - the exponent arrangement is p−1, erratic, depending on p−1's smoothness. **It is in the gene pool** (the user's ruling), so the family can rediscover p−1 on smooth-p numbers.
- **Rediscoveries** of p−1 (the exponent layout) or rho (the map layout with cycle detection) are reported separately, as **"rediscovered known lamp"**, never as novelty (the user's ruling; G_rho's rule 5).
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

1. **Does evolution rediscover a rho-shaped layout?** Defined as: the best genome uses the map layout (any c, d) with a cycle-detection rule (Floyd or Brent, batched or not), and its log2-steps slope over 48–80 bits is within 0.20–0.30 per bit. Yes or no, with a probability. (A yes is reported as "rediscovered known lamp".)
   - **Its meaning (the reviewer's amendment):** "map + cycle detection" is in the gene pool, so a yes mainly validates the search, the meter and the guard on a family with a known answer. It is phase 4's test drive and is reported as such, not as discovery.
2. The best genome's G_rho (frozen, 48–80, op-class; and its worst-of value including the scaled gcd price), or "not defined". Its G (80–96), or "not defined".
3. The best genome's cost ratio against rho alone at 64 and 80 bits, op-class v1, with a range; and the same under the size-scaled gcd price.
4. Does any non-map layout (stride, fold, bins) beat a slope of 0.45 per bit? Yes or no.
5. Does the search select the exponent layout (rediscovered p−1) on θ < 0.3 numbers? Scored on the θ sub-map only (§8).
6. **The best genome's map degree d** (the reviewer's addition): is d = 2, or higher? Background: Brent and Pollard (1981) showed that x^(2k) + c maps shorten the expected cycle when p ≡ 1 mod 2k, while each step costs more multiplies under §2's charge (log2 d + popcount d − 1).

## 8. Run plan (only after the user's approval and sealing)

1. Cost model in NOTES for each layout and rule (charges per §3), then code in Python and lampcore. Parity, including stride + per-dot = vl exactly.
2. **Number distributions** (the reviewer's amendment, Oct 29):
   - **Main map, balanced** (θ ≈ 0.5, `semiprimes_pq(bits, n, seed)` as G_rho's reference):
     - training: 48 per size at 48, 56, 64, 72 and 80 bits, seeds 9920000 + bits;
     - validation: 48 per size at 48, 64 and 80 bits (G_rho and the cost ratios) and at 96 bits (G's 80–96 chord, with 80), seeds 9930000 + bits, never seen by the search. Rho alone runs on the same validation numbers (G_rho's paired bootstrap).
   - **θ sub-map for Q5** (θ uniform in 0.20–0.30, drawn as `twilight2_search.numbers()` with the band changed):
     - training: 48 per size at 64 and 80 bits, seeds 9925000 + bits;
     - validation: 96 per size at 64 and 80 bits, seeds 9935000 + bits.
     - The search runs separately on the sub-map. Its genome answers Q5 and nothing else; G_rho, Q1–Q4 and Q6 are scored on the balanced map only.
3. The training map (untimed counts) and the search (a coordinate search over the genes, as the twilight search), on each map. STOP to report the genomes.
4. Validation on held-out numbers: G_rho (frozen, 48–80), G (frozen, 80–96) where defined, cost against rho at 64 and 80 bits; the worst-of set including the scaled gcd price.
5. A wall arm only if a prediction names it.

## 9. Decisions

**Made (the user, Oct 29):**
- gcd pricing: option (a), with the scaled price in this family's worst-of set;
- G_rho frozen on 48–80;
- the exponent layout in the pool, and rediscoveries reported as known lamps;
- the design approved in principle.

**The reviewer's read (Oct 29):** four amendments folded in: squares bins (§2, §5), the number distributions and Q5's sub-map (§8), Q1's meaning (§7), and Q6 (§7). Q5 is kept, with its own sub-map.

**Still open:**
- the predictions (§7), sealed before any run;
- the cost models in NOTES for each layout and rule, before code.
