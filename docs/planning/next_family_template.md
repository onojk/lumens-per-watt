# Design template for the next search family (after arrangement-v1)

**Status: TEMPLATE, not frozen.** It carries the user's rulings of Oct 30 into the next family's design. It is frozen, and its fitness and harness rules pinned, only when that family's predictions are sealed (`predictions/<id>.md`, `tools/judge.py pin`), not before. Until then it may change; any change is a commit of its own.

## 0. The reference: the FRONTIER, not rho alone (the user's ruling, Oct 30)

- **Definition:** a new family's reference is the **frontier**, the per-size minimum cost over all known lamps (rho, ECM, p − 1, QS, and any other existing lamp), under the worst-of pricing set.
- **Per pricing:** the frontier's cost at a size is the minimum over the lamps priced under it. A candidate's ratio against the frontier is the worst (max) over the worst-of pricings of its cost / the frontier's cost.
- **The win rules below apply against the frontier,** wherever they say "rho": G_rho becomes the candidate's doubling period ÷ the frontier's over the chord, and the cost-ratio intervals are against the frontier at every measured size.
- **The measured frontier** is recorded in `results/frontier_*` (Oct 30) with the bound rule used for p − 1 and ECM.
- **Arrangement-v1's results stay as recorded,** scoped to rho.

## 1. Fitness: G_rho with a cost condition at every size (the user's ruling, Oct 30: a strengthened option (a))

- **Primary growth fitness:** G_rho, as frozen (`reviews/growth_fitness_rho.md` v2): the candidate's doubling period ÷ rho's over the chord, worst-of {op-class v1, ruint, Montgomery, scaled gcd}, paired bootstrap.
- **The rule:** a G_rho win counts only if the genome is no dearer than rho at every measured size of the chord. At no measured size may its robust cost-ratio interval (worst-of, paired bootstrap, the same numbers as rho) lie entirely above 1. A genome that fails it gets no slope win, whatever its G_rho, and the report says why.
- **The check against arrangement-v1** (held-out intervals; NOTES):
  - The Q5 pick, map(c = 5, d = 2, x0 = 2) + Brent(512), training G_rho 1.133: at 64 bits its interval is 1.267 [1.077, 1.491], entirely above 1. **It fails**, as it must.
  - The balanced pick: at 64 bits 0.993 [0.831, 1.180], at 80 0.988 [0.807, 1.218]. **It passes** at the measured sizes.
- **Why not the original options:**
  - (a), which checks only the top size of the chord, would pass the Q5 pick: at 80 it is 0.990 [0.804, 1.227].
  - (b), which ranks on projected cost at a fixed target size, extrapolates the slope. A flatter, padded curve projects as cheaper, so (b) would rank the Q5 pick higher, not lower.
- **A LEVEL win** (G_rho about 1, i.e. the same growth and a claimed lower cost; the user's ruling, Oct 30) counts only if the genome's robust cost-ratio interval lies entirely below 1 at every measured chord size, under the worst-of pricing set. A level win under op-class alone (or any single pricing) is a pricing artifact, flagged and not adopted. Slope wins stay under the strengthened rule (a) above.
- **What the harness must add:** robust cost-ratio intervals at **every** chord size. arrangement-v1's harness reports them only at 64 and 80. For a 48–80 chord: 48, 64 and 80, plus any intermediate size the design draws.
- **In the search** (the proposer), the cost guard stays, made consistent with the rule: rank only genomes whose training robust ratio is ≤ 1.25 at every training size. That limits padding during the search; the rule above is the judge's.

- **Harness requirement (recorded Oct 30; no code yet):** the scoring harness reports robust cost-ratio intervals (worst-of, paired bootstrap, the same numbers as rho) at every chord size including 48, as both win rules above need. The pinned arrangement-v1 harness does not; the next family's harness adds it before its predictions are sealed.

## 2. Held-out sets: sized for ±5% on the cost ratio (the user's ruling, Oct 30)

- **Sizes:** about **600 numbers at 64 bits and 850 at 80**, paired with rho on the same numbers.
  - Source: NOTES 5f9131d, `wolfram/2026-10-30_heldout_n_resolution.wl`. Interval half-widths scale as 1/√n from arrangement-v1's 48 per size (±17.6% at 64, ±21.1% at 80). This is a model.
  - Other held-out sizes (48 bits for the chord's bottom; 84 and 96 for G and its gene check) are set in the family's design, by the metric each one decides.
  - Seeds: a fresh base per family, recorded before sealing, never seen by the search (the search sandbox's seed check is updated to the new base).
- **Training sets:** unchanged, 48 per size at the chord's sizes.
- **Scoring time** (estimate; 2 workers, 2.4 GHz cap, governor powersave, as recorded in arrangement-v1's machine-state files):
  - **lampcore, the cost-ratio arms** (rho and a rho-like candidate):
    - measured 5.63 s for 48 rho runs at 80 bits and 0.20 s at 64;
    - so about 100 s per arm at 850 × 80 bits and about 2.5 s per arm at 600 × 64;
    - the two arms run in parallel: about **1.7 min** of wall time.
    - A candidate dearer than rho scales its arm, up to about 1.25 × under the search's guard.
  - **The paired bootstrap** (10,000 resamples, single-threaded Python):
    - measured 5.3 s for one one-size ratio at n = 850, and 9.4 s for one two-size period over 600 and 850;
    - arrangement-v1's harness makes about 33 such calls per genome, most at small n;
    - with the 64/80 calls at full size: about **3–4 min**.
  - **The remaining sizes** (48, 84, 96 at 48 each, QS included): about 2 min, as in arrangement-v1's scoring.
  - **A report run** that re-runs the 64/80 arms (D-44's kind): about 2 min more.
  - **Total: about 8–10 min per scored rho-like genome.** A genome near the search's budget limit takes longer, in proportion to its cost.

## 3. Ranking, reruns, forecasts (the user's rulings, Oct 30)

- **Ties:** every ranking tie (search sweep, best overall, top-k lists in report scripts) is broken on the genome's sorted JSON, never on evaluation order (56e635f).
- **Rerun-identical check:** evaluated lists are compared as sorted sets, plus the order-independent fields (`evolve/arr_compare_search.py`).
- **Forecast ranges** must be at least as wide as the metric's stated resolution (G_rho: ±4%). It applies from the next family's sealing on.

## 4. Carried over unchanged from arrangement-v1

- **The guard:** the judge pinned in the predictions, checked twice by `tools/sealed_run.sh`; pin commits stand alone.
- **Sandboxes:** the training-only search sandbox (allow-listed files, the held-out seed check) and the fresh scoring sandbox (clean environment, new namespaces, the search's process group killed first).
- **Inputs:** the total genome reader; the `search_out` allow-list.
- **Early-exit audit:** an error or abort invalidates a score.
- **Before scoring:** a held-out-free test seed for every code check (`--test-seed`), and the rerun-identical check before scoring.
- **Cost model in NOTES before code;** parity Python ↔ lampcore, including a mutation check; predictions sealed before any run.
