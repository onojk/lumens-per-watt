# ptable: alloc+div64+ptable against alloc+div64, wall-clock (a fixed-size partials table): sealed predictions, filed before any timed run

**The change:** the partial-relation map becomes an open-addressing table with a multiplicative hash, allocated once per attempt, replacing the SipHash `HashMap`. Cost note: NOTES.md, "Cost note (before code): a fixed-size partials table" (3a69b74). Every op count, relation and output is predicted identical, so there is no priced prediction; only wall-clock is measured.

**Status:** the code is not written yet; it waits for div64's parity. The planned run (not yet; its runner will be committed separately before it) is `tools/sealed_run.sh ptable -- bash -c "cd evolve && python3 ptable_time.py"`, with Run A's design: "alloc+div64" (the div64 release build, kept as a copy) against "alloc+div64+ptable"; reference genes; all map numbers at 72 / 84 / 96; 8 alternating replicates; outputs checked identical in the run; AC and the standard conditions. **Not timed until the reviewer's, DeepSeek's and Grok's predictions are filed** (the user, Oct 27 night).

**Information the forecasters have** (filed before this file): the cost note's measured inputs and Wolfram forecast.
- `get` + `insert`: 0.195 / 0.296 / 0.676 M instructions per number for 580 / 922 / 1,924 hash ops.
- Removed: about 0.18 / 0.27 / 0.63 M per number, 3.4 / 2.3 / 2.0%.
- The ρ-rule forecast: central −2.9 / −1.9 / −1.7%; band −1.3 to −4.2 / −0.9 to −2.8 / −0.8 to −2.5%.

The post-code callgrind check will be added here when it exists.

## The reviewer's R-28 (Oct 27 night; sealed; verbatim)

      R-28 partials table vs alloc+div64 card, wall change: 72: -1.7% to -4.4%; 84: -1.1% to -3.0%;
           96: -1.0% to -2.6%. 60%. Basis: cost-note removal 3.4 / 2.3 / 2.0% x rho 0.5-1.3 (central 0.9),
           floored at +/-1 point. Falsifier: outside the range. If the post-code callgrind check differs from
           the cost note by more than 20%, note it beside R-28 (the range stands).

## DeepSeek's D-28

<!-- verbatim begin -->
[PLACEHOLDER: the user's brief carried the slot "[PASTE DEEPSEEK'S D-28 REPLY HERE]" without D-28's text. To be filled verbatim when the user pastes it. ptable is not timed until it is filed (the user, Oct 27 night).]
<!-- verbatim end -->

## Grok's G-21 (23:44 Oct 27 PT; sealed; verbatim, with the header of Grok's reply)

<!-- verbatim begin -->
**Sealed predictions (Grok, 27 Oct 2026 ~23:50 PT)**
Using only the numbers supplied. Absolute post-div64 wall times and the final partials-table instruction counts are missing.
### G-21 — partials-table wall change vs alloc+div64 card (negative = faster)
Rho basis: the change replaces a growable hash map (pointer-chasing, allocations) with a fixed open-addressing table; this is closer to the memory-stalling class that previously pushed rho above 1. Rho = 1.15.
- 72 bits: −2.5 % to −5.0 % (confidence 55 %)
- 84 bits: −1.6 % to −3.6 % (confidence 55 %)
- 96 bits: −1.4 % to −3.2 % (confidence 50 %)
**Falsifiers:** 72: ≥ −1.0 % or ≤ −7.0 %; 84: ≥ 0 % or ≤ −5.0 %; 96: ≥ 0 % or ≤ −4.5 %
<!-- verbatim end -->

**The reviewer's notes** (the ranges are unchanged):
- **The reviewer's unmeasured opinion, recorded after G-21 was sealed:** G-21's ρ 1.15 rests on a "pointer-chasing" map, but Rust's std `HashMap` is open addressing (hashbrown), not pointer-chasing.
- **Scoring G-21.** Its falsifiers are bands wider than its ranges, so ranges and falsifiers are scored separately.
