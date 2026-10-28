# alloc-once: 2′b+fix+alloc against 2′b+fix, wall-clock (allocate once per attempt): sealed predictions, filed before any timed run

**The change:** allocate once per attempt and reuse buffers across polynomials and candidates (the user's go-ahead, Oct 27 late). Cost note: NOTES.md, "Cost note (before code): allocate once per attempt". Every op count, relation and output is predicted identical, so there is no priced prediction; only wall-clock is measured.

**Planned run** (not yet; the runner will be committed separately before it):
- `tools/sealed_run.sh alloc-once -- bash -c "cd evolve && python3 alloconce_time.py"`.
- **Design:** the same as Run A (aprime-fix). "2′b+fix" is the current release lampcore (ef345913…), kept as a copy; "2′b+fix+alloc" is the release build with the change.
  - Reference genes; all map numbers at 72 / 84 / 96; batch, pinned to core 2.
  - Replicates: Run A's 8, alternating, unless the user sets otherwise before the run.
  - Conditions: AC, cap 2,400 MHz, TCPU < 70 °C, no Wolfram kernel.
  - Outputs with `--types` are checked identical in the run.
- **Reported:** the ratio per replicate, its mean and 95% t interval, as a percent change (negative = the change is faster).

**Information the forecasters have** (all filed before this file):
- **Allocation share of the card's instructions:** 26 / 15 / 9% at 72 / 84 / 96 (`evolve/gap_library.json`).
- **Removed at the targeted sites:** 1.96 / 2.11 / 2.73 M instructions per number, 23.9 / 13.5 / 7.6% of all (`evolve/alloc_estimate.out`).
- **The Wolfram model:** −23.9 / −13.5 / −7.6% at k = 1; band −16.7 to −47.7 / −9.5 to −27.0 / −5.3 to −15.2% for k from 0.7 to 2.0 (`wolfram/2026-10-27_alloc_once.out`).
- **The card's wall per number,** all map numbers (Run A, after the fix): 0.832 / 1.554 / 3.353 ms.

## The reviewer's R-26 (Oct 27 late; sealed; verbatim, with its basis)

      R-26 wall change, alloc-once vs current card: 72: -6% to -18%; 84: -4% to -12%; 96: -2% to -8%. 60%.
      Basis: allocation is 26 / 15 / 9% of instructions at 72 / 84 / 96 (gap_library.json); malloc paths
      are cache-friendly short instructions, so the time share is somewhat below the instruction share,
      but freeing memory also reduces cache churn. Widened for both.

**Note** (the range is unchanged): R-26 was written before the cost note's targeted-site estimate and the Wolfram forecast were computed, and its basis cites only `gap_library.json`.

## Added after code, before any timing (information for DeepSeek and Grok; R-26 was sealed before it)

**The cost note's callgrind check** (`evolve/alloconce_check.py`, `.out`; balanced band, reference genes):

| bits | allocator instructions per number, before → after | removed | all instructions per number, before → after |
|---|---|---|---|
| 72 | 2.123 → 0.152 M | 1.970 M | 8.215 → 5.776 M (−29.7%) |
| 84 | 2.347 → 0.235 M | 2.113 M | 15.597 → 12.906 M (−17.3%) |
| 96 | 3.101 → 0.406 M | 2.695 M | 35.820 → 32.212 M (−10.1%) |

- The removed allocator instructions match the cost note's estimate (1.961 / 2.107 / 2.728 M). The Rust wrapper code makes the total removed larger: 2.44 / 2.69 / 3.61 M.
- Acceptance: byte-identical outputs (`evolve/alloconce_accept.out`). Parity: see NOTES.

## DeepSeek's D-26 (22:12 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
## Recorded
- Correction accepted: the card times 0.86 / 1.54 / 3.37 ms were already from the fixed binary, not pre-fix. Annotation only.
- Fair YAFU re-run recorded: card / YAFU QS = 1.718 [1.624, 1.813] / 1.594 [1.551, 1.638] / 1.879 [1.838, 1.919] at 72 / 84 / 96. YAFU siqs() wall − internal = 5.81 / 5.84 / 6.02 ms. D-23, D-24, D-25 all hit, as did R-23–R-25 and G-16–G-18; recorded as calibration, not foresight. Reconciled breakdown recorded.
- Gap located: polynomial set-up 46 / 27 / 26% of the gap; confirm + large primes 43 / 52 / 36%; scan 6 / 10 / 15%; sieve 5 / 14 / 22%; linear algebra + sqrt cheaper for the card; SIMD not the main story; biggest single item memory allocation, 2.1 / 2.3 / 3.1 M instructions per number (26 / 15 / 9%); YAFU makes no allocation calls here.
- Next run recorded: allocate once per attempt; op counts identical; outputs byte-identical; allocator instructions 2.12→0.15 / 2.35→0.24 / 3.10→0.41 M; all instructions −29.7 / −17.3 / −10.1%. Card wall before ~0.88 / 1.59 / 3.43 ms. Instruction drops do not translate one-for-one into time.

## Sealed D-26
Definition: mean wall-clock change per number, alloc-once build vs current card (2'b + lookup fix), at each size, balanced band, 2.4 GHz cap, 4 replicates. Base: current card. Units: percent change; negative = faster. Pure wall-clock prediction.
72: −9.0% to −24.0% (central −16.0%), 55%, falsifier >−9.0% or <−24.0%.
84: −5.0% to −15.0% (central −10.0%), 55%, falsifier >−5.0% or <−15.0%.
96: −2.5% to −9.5% (central −5.5%), 55%, falsifier >−2.5% or <−9.5%.

Working: anchor = instruction drops −29.7 / −17.3 / −10.1%. At 72, 2.12 − 0.15 = 1.97 M out of roughly 1.97/0.297 = 6.63 M, allocator share 2.12/6.63 = 32% (the given 26% may exclude some pre-fix charges); at 96, 3.10 − 0.41 = 2.69 M out of 2.69/0.101 = 26.6 M, allocator share 3.10/26.6 = 11.7% (given 9%, same note). Missing input: the wall-time contribution of allocator instructions. Wall-to-instruction ratio 0.45–0.75, central 0.55: 72: 29.7 × 0.55 = 16.3% (central −16%); 84: 17.3 × 0.55 = 9.5% (−10%); 96: 10.1 × 0.55 = 5.6% (−5.5%). Sealed ranges use the ratio span [0.30, 0.80], widened by the miss-scatter allowance: 72 [8.9%, 23.8%] → [9%, 24%]; 84 [5.2%, 13.8%] → [5%, 15%]; 96 [3.0%, 8.1%] → [2.5%, 9.5%].
Falsifier directions as written: 72 falsified if wall saving is less than 9% or more than 24%; 84 less than 5% or more than 15%; 96 less than 2.5% or more than 9.5%. "A saving smaller than the low end (i.e., more negative than −9% → saving smaller) falsifies at 72, and a saving larger than the high end (i.e., more negative than −24% → saving larger) falsifies at 72."
Confidence 55% per size; sizes correlated (same ratio). Methodological note: all three forecasters saw the callgrind allocator counts before filing, so D-26 is partly a calibration test of the instruction-to-wall ratio.
<!-- verbatim end -->

**The reviewer's notes** (the ranges are unchanged):
- **The set of numbers.** D-26's definition says "balanced band", but the runner times **all map numbers**. It is scored on the run as designed, with the mismatch noted.
- **The back-calculated totals** (e.g. 6.63 M at 72) don't match the measured 8.215 M, because about 0.5 M of the removed instructions are wrapper code. The ranges don't depend on it.
- **One gloss reverses direction** ("more negative than −9% → saving smaller"). Its band statements are correct.

**Claude's note** (the range is unchanged): D-26 says "4 replicates". The runner uses Run A's 8, as this file's design states; the user set no other number.

## Grok's G-19 (22:12 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
**Sealed prediction G-19 (Grok, 27 Oct 2026 ~22:15 PT)**
Using only the numbers supplied. The fraction of wall time spent inside the allocator, cache-miss rates, and the exact translation from instruction drop to time are missing.

### Wall change, alloc-once vs current card (negative = faster)
- **72 bits:** −8 % to −18 % (confidence 60 %)
- **84 bits:** −5 % to −12 % (confidence 60 %)
- **96 bits:** −3 % to −8 % (confidence 55 %)

**Falsifiers (single condition each):**
- 72 bits: measured change ≥ −2 % or ≤ −25 %
- 84 bits: measured change ≥ −1 % or ≤ −18 %
- 96 bits: measured change ≥ 0 % or ≤ −12 %
<!-- verbatim end -->

**The reviewer's notes:**
- G-19's falsifiers are bands wider than its ranges, so ranges and falsifiers are scored separately.
- All three forecasts overlap heavily (low discrimination). This run tests the shared instruction-to-time reasoning.

**All three forecasters are sealed:** the reviewer R-26, DeepSeek D-26, Grok G-19.
