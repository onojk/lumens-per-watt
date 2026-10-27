# Root confirm retime (root-confirm-2): sealed predictions, filed before any timed run

The user's predictions are given verbatim from the user's brief (Oct 27). They are filed after root-confirm's results (574f356, b1e5ed7) and after the code inspection of the sieve region (d7a1fd0), and they are sealed against this run only. NOTES.md remains the record; scoring goes there.

**Planned run** (not yet; `tools/sealed_run.sh root-confirm-2 -- bash -c "cd evolve && python3 rootconfirm2.py"`, runner 6a40164):
- 96 bits, all 640 map numbers, re-sieve off, card e13603a. The same numbers and genes as root-confirm.
- Cells: the reference (full pass, pp absent, tc 1.0353); root alone; root + pp 3 ("2 free") at threshold shifts 0, +1, +2 and +3 bits (tc − d / log2 1,752; L unchanged).
- Wall-clock: 8 replicates. Each replicate times every cell once (lampcore --phasetime, taskset core 2), in its own random order from random.Random(2026), one shuffle per replicate (`evolve/timing.shuffled`).
  - The orders are fixed by the seed and recorded in the output. The reference falls first in r2, r5 and r8 and last in r1 and r4 (5th of 6 in r3, 2nd in r6, 4th in r7). A random order does not guarantee balance.
- Core 2's MHz is sampled every second per cell. Each cell is flagged if its median is more than 10% off the reference's. The machine state is read before each replicate and before and after the run.
- **Frequency cap:** if the user sets one before the run, it is recorded from the machine state (frequency limits: scaling_min/max_freq, intel_pstate no_turbo, min/max_perf_pct, added in 6a40164). Claude does not set it.
- Per cell, the report gives:
  - wall-clock, sieve and confirm regions, as the mean, sd, min and max over the 8 replicates;
  - the ratio to the reference within each replicate (same replicate pairs), with its mean and a 95% t interval over the 8 pairs (t 0.975 with 7 df = 2.3646), for wall, sieve and confirm.
- Counts and priced totals are root-confirm's (identical genes and numbers); only the timing is new.

## The user's (verbatim)

      RC2-1 root alone, wall-clock vs the reference: -6% to -12%.
      RC2-2 the sieve region with root on stays above the reference by +8% to +25% (a code effect, not clock).
      RC2-3 root + pp 3, best shift among 0..+3: wall-clock -7% to -13%.
      RC2-4 the replicate-based 95% interval for root alone's wall ratio is no wider than +-3 points.
