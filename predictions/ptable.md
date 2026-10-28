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

## DeepSeek's

Pending.

## Grok's

Pending.
