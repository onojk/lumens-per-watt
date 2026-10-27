# Root confirm (I-029 in the card): sealed predictions, filed before any timed run

The user's predictions are given verbatim from the user's brief (Oct 27). DeepSeek's (round 57) are copied verbatim from NOTES.md, where they were first recorded in **a1c8e7c**. NOTES.md remains the record; scoring goes there.

**Planned run** (not yet; `tools/sealed_run.sh root-confirm`):
- 96 bits, all 640 map numbers, card with confirm = "root" built (option off by default).
- Cells, all against the reference (re-sieve off, full pass, pp absent, tc 1.0353), in the same run:
  - root alone;
  - root + "2 free" (pp 3) at threshold shifts 0, +1, +2, +3 and +4 bits (tc − d / log2 1,752; L unchanged).
- Timing interleaved and counterbalanced (`evolve/timing.py`), two replicates, machine state before and after and per replicate, core 2's MHz sampled every second per cell (cells off the reference's median by more than 10% flagged).
- Priced with root_test at 0.0581 ruint / 0.2142 Montgomery (NOTES, "Root confirm (I-029) as a card option", 1a7cd8d).

## The user's (verbatim)

      R-1 root confirm alone (96 bits, all 640 numbers, vs the reference, same run): wall-clock -11% to -19%.
      R-2 root confirm alone: priced ruint -8% to -15% (with the new op priced as in the cost note).
      R-3 root confirm + "2 free" (pp 3) at shifts 0, +1, +2 bits: the best wall-clock shift is 0, +1 or +2.
      R-4 root confirm + "2 free" at its best shift: wall-clock -13% to -22%.

*Annotation on R-3 (the user's, before any run):* "on a 0..+2 grid it would hold automatically; the grid was extended to +4 before any run so it can fail". The grid is 0, +1, +2, +3, +4 bits.

## DeepSeek, round 57 (verbatim from NOTES.md, first recorded in a1c8e7c)

- **SEALED, before any root-confirm timing:**
  - **R-1** root confirm alone, wall-clock against the reference: −13% to −19% (central −16%). Falsified if < −9% or > −23%.
    - Working: confirm is 27.1% of wall-clock × (1 − 219/569) = −16.7% (version c); −14.8% for version b.
  - **R-2** root confirm alone, priced ruint: −8.5% to −14.5% (central −12.0%). Falsified if < −5% or > −17%.
    - Working: per candidate 138 × 0.0582 + 7.06 × 0.114 = 8.84 ruint against 138 × 0.114 = 15.73 (ratio 0.562). Confirm is 27.5% of 59,071 ruint, so the saving is 7,115 ruint, −12.0%.
  - **R-3** root confirm + "2 free": the best wall-clock shift is +2 bits (+1 close). Falsified if ≤ 0 or ≥ +4.
  - **R-4** root confirm + "2 free" at its best shift: wall-clock −14% to −22% (central −18%). Falsified if < −10% or > −26%.
- **Loop bottleneck:** its explanation emphasises dependency latency.
