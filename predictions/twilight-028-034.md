# twilight-028-034: a gene-only specialist for θ 0.28–0.34 (the p−1 to QS hand-off): design, for sealing

**Status: DESIGN. Nothing is run.** The forecasters' sections below are empty, and the runner is written and committed only after they are sealed. The user ruled the next specialist band on Oct 28 (the reviewer's correction, f64f3d2): the twilight at 96 bits is θ ≈ 0.28–0.34, where p−1 hands off to QS. In the light spectrum v1 under op-class, the best non-QS lamp at 96 bits is p−1 at 0.26–0.30, and QS is best from 0.32.

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

## DeepSeek's

Pending (the user decides whether to relay).

## Grok's

Pending (the user decides whether to relay).
