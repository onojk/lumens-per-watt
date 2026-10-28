# aprime-fix: 2′b+fix against 2′b, wall-clock (the A-prime lookup fix): sealed predictions, filed before any timed run

**The change:** the A-primes' base indices once per A instead of a linear base scan per kept relation. Cost note: NOTES.md, "Cost note (before code): the A-prime lookup fix" (9164007). Code and acceptance: the commit after it. Every op count, relation and output is identical, so there is no priced prediction; only wall-clock is measured.

**Planned run** (not yet): `tools/sealed_run.sh aprime-fix -- bash -c "cd evolve && python3 aprimefix_time.py"`. The runner is committed separately, before the run.
- **Cells:** "2′b" is the reference genes (`lctest.ref` + goff = 1 + confirm = root) on the pre-fix lampcore (`opclass/bin/lampcore-release`, sha256 1505efbf…, built from 735fd67). "2′b+fix" is the same genes on the post-fix release build. The two binaries differ only by the fix.
- **Numbers:** all map numbers at 72, 84 and 96 bits (480 / 560 / 640), in batch: one process per cell per replicate, pinned to core 2.
- **Replicates:** 8 per size; the order alternates (2′b first in odd replicates, 2′b+fix first in even ones).
- **Conditions,** checked before timing (else no timing): AC online, cap 2,400 MHz on every core, TCPU < 70 °C, no Wolfram kernel. Pause above 90 °C until below 70. Core 2's MHz is sampled per cell.
- **Reported:** the wall per number per cell, and the ratio 2′b+fix / 2′b within each replicate, with its mean and 95% t interval over the 8 pairs (t 0.975, 7 df = 2.3646). As a percent change: (ratio − 1) × 100, negative = the fix is faster.
- **Checked:** the factors and all per-type counts of both cells are identical on every number (`--types`, once per size).

## DeepSeek's D-20 (20:04 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
D-20 — A-prime lookup fix, wall change vs 2'b. Definition: mean wall-clock per number, 2'b+fix vs 2'b, at 72 / 84 / 96 bits, all map numbers, same design as the sealed runs. Base: 2'b. Units: percent change; negative = fix faster. Op counts identical by design; no priced prediction.
72: −0.8% to −2.6% (central −1.6%), 75%, falsifier outside range. 84: −1.4% to −3.6% (−2.4%), 75%, outside range. 96: −2.8% to −6.0% (−4.3%), 75%, outside range.
Working: cost note per-relation A-prime scan 47 / 82 / 165 ns at 72 / 84 / 96, giving 1.6% / 2.4% / 4.3%. Kept-relation counts and wall totals per number are missing, so centred on the cost-note forecast and widened by ±60% of the central (miss-scatter allowance from round 61). Mechanism: per-relation linear scan replaced by a once-per-A lookup; saving grows with size. 75% because the wall benefit depends on cache behaviour; a once-per-A lookup may cost more per A than the per-relation scan saves at small sizes. Each size scored independently.
<!-- verbatim end -->

**The reviewer's annotation** (the ranges are unchanged): D-20 is centred on the cost note, with its own miss allowance: fine.

## The reviewer's R-20 (Oct 27; sealed; verbatim)

      R-20 (A) 2'b+fix vs 2'b wall: 72: -0.5% to -2.2%; 84: -1.0% to -3.2%; 96: -2.0% to -5.0%. 70%.
           (Expect a little below the cost note: out-of-order overlap hides part of the lookup's latency.)
      Falsifiers: outside the stated range.

## Model forecast (filed before; not a prediction)

The cost note's model (Stage 3, `wolfram/2026-10-27_copies_cost`): −1.6% / −2.4% / −4.3% at 72 / 84 / 96.
