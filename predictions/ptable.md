# ptable: alloc+div64+ptable against alloc+div64, wall-clock (a fixed-size partials table): sealed predictions, filed before any timed run

**The change:** the partial-relation map becomes an open-addressing table with a multiplicative hash, allocated once per attempt, replacing the SipHash `HashMap`. Cost note: NOTES.md, "Cost note (before code): a fixed-size partials table" (3a69b74). Every op count, relation and output is predicted identical, so there is no priced prediction; only wall-clock is measured.

**Status:** the code is not written yet; it waits for div64's parity. The planned run (not yet; its runner will be committed separately before it) is `tools/sealed_run.sh ptable -- bash -c "cd evolve && python3 ptable_time.py"`, with Run A's design: "alloc+div64" (the div64 release build, kept as a copy) against "alloc+div64+ptable"; reference genes; all map numbers at 72 / 84 / 96; 8 alternating replicates; outputs checked identical in the run; AC and the standard conditions. **Not timed until the reviewer's, DeepSeek's and Grok's predictions are filed** (the user, Oct 27 night); all three now are.

**Information the forecasters have** (filed before this file): the cost note's measured inputs and Wolfram forecast.
- `get` + `insert`: 0.195 / 0.296 / 0.676 M instructions per number for 580 / 922 / 1,924 hash ops.
- Removed: about 0.18 / 0.27 / 0.63 M per number, 3.4 / 2.3 / 2.0%.
- The ρ-rule forecast: central −2.9 / −1.9 / −1.7%; band −1.3 to −4.2 / −0.9 to −2.8 / −0.8 to −2.5%.

**The post-code callgrind check** (`evolve/ptable_check.py`, `.out`; after acceptance, before timing; added after all three forecasts were sealed):

| bits | instructions per number, alloc+div64 → +ptable | removed | the cost note's estimate | difference |
|---|---|---|---|---|
| 72 | 5.270 → 5.242 M (−0.53%) | 0.028 M | 0.180 M | **−85%** |
| 84 | 12.082 → 11.943 M (−1.16%) | 0.140 M | 0.273 M | **−49%** |
| 96 | 30.957 → 30.351 M (−1.96%) | 0.606 M | 0.631 M | −4% |

- **The cause:** `PTable::new` costs 155–164 k instructions per number, all in the zeroed allocation of its 4,096 slots (32 KB of keys + 128 KB of values) once per attempt. The cost note assumed about 2 k per number for the clear.
- **The lookups and inserts themselves** cost 17 / 27 / 61 k per number against the map's 195 / 296 / 676 k.
- **The table never doubles at these sizes:** at most 1,194 inserts per attempt on 10 balanced 96-bit numbers (Python trace), against a doubling threshold of 2,048. That answers D-28's missing input: the rehash side does not apply.
- **The 160 KB allocation** is above glibc's default mmap threshold (128 KB), so it may also pay page-fault time that callgrind does not count. Not measured.

## The reviewer's R-28 (Oct 27 night; sealed; verbatim)

      R-28 partials table vs alloc+div64 card, wall change: 72: -1.7% to -4.4%; 84: -1.1% to -3.0%;
           96: -1.0% to -2.6%. 60%. Basis: cost-note removal 3.4 / 2.3 / 2.0% x rho 0.5-1.3 (central 0.9),
           floored at +/-1 point. Falsifier: outside the range. If the post-code callgrind check differs from
           the cost note by more than 20%, note it beside R-28 (the range stands).

**Note beside R-28** (as R-28 asks; the range stands): the post-code check differs from the cost note by more than 20% at 72 (−85%) and 84 (−49%), and by −4% at 96. See the check above.

## DeepSeek's D-28 (00:07 Oct 28 PT; sealed; verbatim; filed before the partials-table run started)

<!-- verbatim begin -->
Definition: mean wall-clock change per number, partials-table build vs the alloc+div64 card, each size, all map numbers, AC, 2.4 GHz cap, 8 alternating replicates. Base: alloc+div64 card. Units: percent change; negative = faster. Pure wall-clock prediction.
72 (3.4% removed): −1.5% to −3.9% (central −2.7%), 60%, falsifier >−1.5% or <−3.9%.
84 (2.3%): −0.8% to −2.8% (−1.8%), 60%, falsifier >−0.8% or <−2.8%.
96 (2.0%): −0.6% to −2.6% (−1.6%), 60%, falsifier >−0.6% or <−2.6%.
Rho band 0.40–1.20, central 0.80. Basis, stated without using any reviewer opinion: the cost note class is "mostly (a) arithmetic into a table that fits in L2", upper side widened for rehash moves; removed work is predominantly SipHash rounds (cheap register arithmetic, pushes rho below 1); the replacement removes scattered HashMap access (pushes rho above 0.40); central 0.80. The two measured rho values (alloc 0.85–1.06, scan 1.01–1.35) are recorded as bracketing context, not anchors, because their removed work is scattered memory, a different class.
Working: ΔW = ρ · ΔI/I_total. Natural range from [0.40, 1.20]: 72 [1.36, 4.08]; 84 [0.92, 2.76]; 96 [0.80, 2.40]. Central at 0.80: 2.72 / 1.84 / 1.60. Width rule (half-width ≥ max(0.30 × central, 1.0 point)): 72 sealed [1.5, 3.9]; 84 forced to [0.84, 2.84], sealed [0.8, 2.8] (implied low-end rho 0.365, below the cost-note floor, forced by the ±1 rule); 96 forced to [0.60, 2.60], sealed [0.6, 2.6] (implied low-end rho 0.30, forced by the ±1 rule). A saving inside the sealed range but below the rho-band range would be "a range hit forced by the width rule", not a rho hit.
60% per size; sizes correlated through the shared rho. Falsifier direction checked: falsified if the measured saving is smaller than the low-magnitude end or larger than the high-magnitude end.
Missing inputs: measured rho for this class; the post-code instruction count reconciliation (pending); rehash frequency at the tested sizes (if the table never doubles past 4,096 at 96, the upper side is nearer 0.90).
<!-- verbatim end -->

**The reviewer's note** (the ranges are unchanged): D-28 is independent of the reviewer's opinions, as it states. Its 84 and 96 low ends are set by the protocol's ±1-point minimum, below its own ρ band; DeepSeek records this itself.

**All three ptable forecasters are sealed:** R-28, D-28, G-21. The timing may proceed after div64's run and the table's own acceptance and parity (the user, Oct 28).

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
