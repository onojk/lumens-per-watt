# twilight-028-034: a gene-only specialist for θ 0.28–0.34 (the p−1 to QS hand-off): design, for sealing

**Status: SEALED (all three forecasters, Oct 28). Nothing is run.** The runner is written and committed only after this file. The user ruled the next specialist band on Oct 28 (the reviewer's correction, f64f3d2): the twilight at 96 bits is θ ≈ 0.28–0.34, where p−1 hands off to QS. In the light spectrum v1 under op-class, the best non-QS lamp at 96 bits is p−1 at 0.26–0.30, and QS is best from 0.32.

Novelty Plan: phase 3 (and the landscape map in parallel). It is scored on cost ratios, not on growth fitness G.

## 1. Band and sizes

- **θ = (bits of the smaller prime) ÷ (bits of N), uniform in 0.28–0.34,** drawn as in `twilight_search.py numbers()`, with the band changed.
- **The primary size is 96 bits;** 84 bits is secondary. At 84 the op-class hand-off is later (p−1 is best at 0.28–0.34, QS from 0.36), so 84 is reported and scored only where a prediction names it.

## 2. The training map (untimed, counts only)

As `twilight_search.py`:
- **Numbers:** 160 fresh training numbers per size, seeds 9810000 + bits.
- **Each pre-stage alone,** in lampcore `--types`, at every budget of its grid:
  - **td, rho and ECM:** partition.PRE genes; the coarse grid 0, 2^8 … 2^20 (`partition.COARSE`), with ob = the budget. Rho is also run at the reference pipeline's own budget (10,624 at 96; 3,158 at 84).
  - **p−1:** partition.PRE genes; B in {0, 256, 512, …, 8192} (ob = 2B), plus a **refinement pass** of B in steps of 2^(1/4) between the coarse best's neighbours. This is new against the θ 0.33–0.40 search: p−1 is the lamp that matters in this band.
- **The reference QS (2′b genes) alone** on every training number.
- **Composition:** a pipeline's cost on a number is composed exactly from these records. A stage that succeeds within its budget stops the pipeline; otherwise it spends its budget, then the next stage runs; QS is last.
- **The check:** the composition must equal a direct lampcore run of the best genome on every training number. If not, it's a blocker.

## 3. The genes searched

- **The genes:** (td budget, rho budget, p−1 B, ECM budget), in that stage order, with QS last on the reference genes (lctest.ref + goff = 1 + confirm = root), unchanged.
- **Not searched:** QS's own genes, ECM's B1 / B2, p−1's B2, and stage order. These are gene-only and budget-only, as in the θ 0.33–0.40 search.
- **The search:** a coordinate search from the coarse grid's best, then the p−1 refinement.
- **Training fitness:** rule (b), the worst of op-class v1, ruint and Montgomery of (mean pipeline cost ÷ mean QS-alone cost) on the training numbers. Official is reported.

## 4. Validation (sealed; the scored run)

- **Held-out numbers:** 400 fresh numbers per size, seeds 9820000 + bits, never seen by the search. They are drawn by the runner at run time, after this file is sealed.
- **The specialist is compared against both baselines:**
  - **(i) QS alone,** the reference card (2′b genes);
  - **(ii) the reference pipeline** (`sizescale_k_sealed` "(d)": td 0, rho at its budget, p−1 at its B, ECM 0, then QS).
- **The metric:** the robust ratio, rule (b), of mean cost per number (specialist ÷ baseline) under op-class v1, ruint and Montgomery, with a paired bootstrap (10,000 resamples) per pricing. Official is reported. Cells are called only where all three agree (e).
- **Wall-clock:** the specialist against each baseline, 4 replicates, pinned core, Run B's conditions, with the load check (1-min load < 1.5 + own processes, at start and before every replicate). Information only, unless a prediction names it.
- **The meter-health check:** the absolute instruction count per op-class unit on a callgrind subset of 8 numbers per arm, against the reference card.
- **Success:** all three arms must factor every held-out number (QS is last). A miss is a blocker, not a cost.
- **If the search returns QS alone** (all budgets 0), the validation against (i) is 1.000 by construction. The user's Oct 28 rule then applies (the genes are recorded side by side, and the forecasts are scored without running that arm). The arm against (ii) is still run.

## 5. Questions for the forecasters (each needs a range and a confidence)

1. **At 96 bits, the specialist's robust ratio against QS alone** (below 1 = the specialist is cheaper).
2. **At 96 bits, the specialist's robust ratio against the reference pipeline.**
3. **The p−1 B the search selects at 96** (a value or a range of B), or "0" (no p−1 stage).
4. Optional: whether rho's budget at 96 is 0.

## 6. Run order (after sealing)

1. Commit the runner (`twilight2_search.py`), then the training map and search (untimed, counts), through `tools/sealed_run.sh twilight-028-034`.
2. **STOP** to report the selected genome. No validation numbers exist yet.
3. Run the validation counts arm (untimed), then the wall arm (timed, with the load check). Both go through `sealed_run.sh`.

## Claude's estimate (from the committed light-spectrum table; information; NOT RELAYED to DeepSeek or Grok, the user's ruling Oct 28, same rule as the reviewer's opinions)

At 96 bits, θ 0.28–0.30, p−1 at its reference B succeeds on 11 / 40 numbers, at 12.5 M op-class units per success (spending about 3.4 M per number), against QS's 34.0 M. A p−1 stage in front of QS would cost about 3.4 + 0.725 × 34.0 ≈ 28.1 M, about **0.83× QS alone** under op-class at that band edge (ruint, the same arithmetic: about 0.84×).
- The gain shrinks toward 0.34, where p−1 succeeds less often (at 0.32–0.34, 0.015 light against QS's 0.029). Averaged over the band, the specialist would be about **0.85–0.95× QS alone**.
- **Against the reference pipeline,** which already runs p−1 at its B after rho, the specialist would be near **1.0×**: the possible saving is rho's spending (rho rarely succeeds above θ 0.28) plus a better B.
- These estimates are untested.

## The reviewer's R-34 to R-37 (Oct 28; sealed; verbatim; filed before any run)

<!-- verbatim begin -->
  R-34 Specialist / QS alone, 96 bits, theta 0.28-0.34, op-class, band average:
       0.90, range 0.84-0.97, 70%. (Edge arithmetic 0.28-0.30: p-1 11/40 at 12.5M
       per success = 3.4M per attempt; 3.4 + 29/40 x 34.5 = 28.4 -> 0.82; the gain
       fades toward 0.32-0.34.)
  R-35 Specialist / reference pipeline, same band and pricing: 0.85, range
       0.78-0.95, 60%. (The reference's rho pre-stage is nearly dead here, rho 2/40
       at 0.28-0.30; pre-stages cost the reference 1.21-1.26x QS alone at 0.33-0.40.)
  R-36 The search picks a p-1 bound B larger than the reference card's: yes, 60%.
  R-37 Wall clock, specialist / QS alone, 96 bits: 0.88-1.00, 60% (op-class
       under-charges p-1 by ~21%, so the clock gain is smaller than op-class's).
  Disclosure: the reviewer saw Claude Code's estimate on screen before sealing.
<!-- verbatim end -->

**Notes on scope** (the ranges are unchanged):
- **R-36's "the reference card's" p−1 B.** The reference card is QS alone and has no p−1 stage. The p−1 B that exists is the reference pipeline's: 4,096 at 96 bits in the search's grid units (B, with ob = 2B; `twilight_search.json` "reference_pipeline_grid"). R-36 is scored against that B unless the user rules otherwise before the run. "Larger" means strictly larger, and a selected B of 0 (no p−1 stage) is "no".
- **R-37 names wall-clock,** so the wall arm (§4) is scored for R-37, not information only.
- **R-34 and R-35's "band average"** is the mean cost per number over the held-out numbers, θ uniform in 0.28–0.34 (§4), under op-class v1. They name op-class, so they are scored under op-class; rule (b) is reported beside it.

## DeepSeek's D-34 to D-37 (Oct 28; sealed; verbatim, as relayed by the user; filed before any run)

<!-- verbatim begin -->
SEALED — no revisions. Band average = uniform theta 0.28–0.34, 96-bit validation,
400 held-out numbers. "Specialist" = gene-only evolved pipeline with searched
td/rho/ECM budgets and p-1 B, QS last on reference genes. Ratios are specialist
divided by stated base; below 1 = specialist cheaper.

D-34 | 0.92; range 0.64–1.20 | Specialist / QS alone, 96 bits, op-class v1, band
average. From light spectrum at theta 0.28–0.30: p-1 per attempt = (11/40)×12.47
= 3.43 M op-class; QS = 34.01 M. p-1-then-QS lower-subband ratio = [3.43 +
(29/40)×34.01]/34.01 = 0.826. Assumption: p-1 benefit decays linearly to zero by
theta 0.34; if p-1 is off in 0.30–0.34, band average ≈ (1/3)×0.826 + (2/3)×1.00
= 0.94; if it still helps, ≈0.90. Range widened for transfer across theta. |
Confidence 35% | Falsified if <0.64 or >1.20.

D-35 | 0.99; range 0.69–1.29 | Specialist / reference pipeline (rho budget 10,624
ops, then p-1 B=4096 stage 1 op budget 2B, then QS), 96 bits, op-class v1, band
average. Reference pipeline already contains the same p-1 pre-stage; with D-36 =
No (B stays 4096), specialist should nearly match it. The reference rho budget is
tiny relative to QS; removing/retuning it changes ratio only slightly. Prediction
≈1.00, widened for search overfitting and band transfer. | Confidence 30% |
Falsified if <0.69 or >1.29.

D-36 | No; P(No)=0.55, range 0.25–0.85 | Does the search pick p-1 B > 4096 at 96
bits? B=0 counts as No. Doubling B to 8192 roughly doubles p-1 per-attempt cost to
≈6.86 M; to beat B=4096's 0.826 lower-subband ratio it would need p-1 success to
rise from 27.5% to >37.6%. B=16384 would need >57.7% success. Measured B=4096
success is 11/40; No is favored but not strong. | Confidence 55% | Falsified if
chosen B > 4096; B=0 is consistent with No.

D-37 | 0.95; range 0.67–1.24 | Wall clock, specialist / QS alone, 96 bits, band
average. Start from D-34 ≈0.92. Instruction check: p-1 op-class undercharged
(0.789), QS overcharged (1.105), so a p-1-heavy specialist looks worse in wall
than in op-class. With lower-subband p-1 share x≈0.10: wall ≈ 0.92 + x×(1/0.789 −
1/1.105) ≈ 0.92 + 0.04 = 0.96. Range widened for pricing/timer transfer. |
Confidence 25% | Falsified if <0.67 or >1.24.
<!-- verbatim end -->

## Grok's G-27 to G-30 (Oct 28; sealed; verbatim, as relayed by the user; filed before any run)

<!-- verbatim begin -->
G-27 (specialist / QS alone, 96 bits, op-class, band-average 0.28–0.34)
Prediction: 0.85. Range: 0.60–1.10 (±29% around centre; from the 0.28–0.30
spectrum: p-1 alone yields 11/40 successes at 12.47 M op-class per success ⇒
average overhead ≈ 3.4 M if always executed, leaving an expected residual 0.725 ×
34.01 M ≈ 28.1 M or 0.83× QS-alone; centre shifted slightly upward for the full
band where p-1 hit-rate falls, then widened for search stochasticity, budget
discretisation and the fact that the previous 0.33–0.40 specialist collapsed to
pure QS). Base: gene-only evolved pre-stage budgets (td/rho/ECM) + p-1 B, QS genes
frozen, op-class v1, 96-bit held-out average over uniform θ ∈ [0.28, 0.34], vs
reference-card QS alone. Ratio < 1 = specialist cheaper. Confidence: 55%.
Falsifier: measured op-class ratio on the 400 held-out numbers ≥ 1.15.

G-28 (specialist / reference pipeline, 96 bits, op-class)
Prediction: 0.80. Range: 0.55–1.05 (±31%; reference pipeline = rho (fixed 10 624
ops) + p-1 (B = 4 096, budget 2B) + QS previously cost 1.26× QS-alone at 96 bits
on the adjacent band; G-27's arithmetic suggests a tuned p-1 can reach ~0.83×
QS-alone, hence ~0.66× the reference pipeline; centre raised to 0.80 to allow for
the extra rho stage and for the search rediscovering a near-reference budget).
Base: same specialist vs the stated reference pipeline (rho → p-1 B=4096 → QS),
op-class v1, 96-bit band average. Confidence: 50%. Falsifier: measured op-class
ratio ≥ 1.10.

G-29 (search selects p-1 B > 4 096 at 96 bits?)
Prediction: yes. Categorical; support: p-1 already delivers successes at low cost
in the lower half of the band, so a larger bound has positive expected value under
op-class (B = 0 would be strictly dominated). Base: the searched p-1 bound on the
96-bit twilight-028-034 specialist. Confidence: 60%. Falsifier: selected genome
has B ≤ 4096.

G-30 (wall-clock specialist / QS alone, 96 bits)
Prediction: 0.90. Range: 0.60–1.20 (±33%; from G-27's 0.85, then the previously
measured rho factors 0.85–1.35 for allocation/scan-style work and the instruction
check (op-class under-charges p-1 0.789, slightly over-charges QS 1.105): a modest
upward shift and extra width). Base: same specialist vs reference-card QS alone,
wall-clock on the pinned 2.4 GHz core, 96-bit band average. Confidence: 50%.
Falsifier: measured wall-clock ratio ≥ 1.25.
<!-- verbatim end -->

## The reviewer's notes on D-34..D-37 and G-27..G-30 (Oct 28; annotations only; no prediction changes)

<!-- verbatim begin -->
- DeepSeek: arithmetic checked (0.826; 0.94; thresholds 37.6% / 57.7%; wall
  +0.036, p-1 share 0.12 at the 0.28 edge). D-35 calls the rho pre-stage "tiny";
  the relayed table gives 117.15 M x 2/40 = 5.86 M op-class per number (~17% of
  QS), not used. Ranges of +/-30% with 25-35% confidence are inconsistent; interval
  score as before.
- Grok: arithmetic checked (edge 0.83; 0.83/1.26 = 0.66). The 1.26 was measured on
  0.33-0.40 where p-1 barely succeeds. G-29's "B = 0 dominated" does not show a
  larger B pays. G-30's "rho factors" = the rho coefficient, not the rho lamp. All
  four falsifiers are one-sided and consistent with their ranges.
- Disagreements the run settles: vs reference D-35 0.99 / R-35 0.85 / G-28 0.80;
  B > 4,096: D-36 no / R-36 yes / G-29 yes.
<!-- verbatim end -->

**All three forecasters are sealed** (the reviewer's R-34..R-37, DeepSeek's D-34..D-37, Grok's G-27..G-30). Claude's estimate above was not relayed to DeepSeek or Grok.

**Scope notes on the new entries** (the predictions are unchanged):
- **D-36 and G-29** are scored against the reference pipeline's B 4,096, as R-36. A selected B of 0 is "no".
- **D-37 and G-30** name wall clock, so the wall arm is scored for them, as for R-37. D-37 is a two-sided range; G-30's falsifier is one-sided (≥ 1.25) and its range 0.60–1.20 is scored as a range.
- **The p−1 grid tops out at B 8,192** (§2; the refinement stays between the coarse best's neighbours), so D-36's B 16,384 case cannot be selected. This was so in the design before sealing.

## Correction: a relayed fact was mislabelled (Oct 28; found by the reviewer; sealed predictions unchanged)

The relay to all three forecasters said the reference pipeline costs **1.21 / 1.26× QS alone on θ 0.33–0.40 (84 / 96 bits) under op-class.** That figure is mislabelled. The committed data (`evolve/twilight_search.json`, ad4a88d, "reference_scores") gives:

| pricing | 84 bits | 96 bits |
|---|---|---|
| op-class v1 | **1.148** | **1.208** |
| ruint | 1.209 | 1.262 |
| Montgomery | 0.996 | 1.031 |
| official | 0.918 | 0.946 |

The 1.21 / 1.26 is the rule (b) value ("reference_fitness"), which on that band is ruint's. ad4a88d's NOTES headline gave it without naming the pricing; 2edd2f0 gave the per-pricing values correctly. **The op-class figure is 1.15 / 1.21.** R-35 ("1.21-1.26x") and G-28 ("1.26× QS-alone") quote the mislabelled figure. Relayed fact mislabelled; sealed predictions unchanged; the corrected fact goes to DeepSeek and Grok with the scores.
