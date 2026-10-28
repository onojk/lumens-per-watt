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

## DeepSeek's and Grok's

Pending: the user relays the cost note and the information above. Nothing is timed until the user says so.
