# 2b-sizes: 2′b alone at 72 and 84 bits; 2′b against 2′b+pp3 at 96 with the sieve breakdown: predictions

**Run:** `tools/sealed_run.sh 2b-sizes -- bash -c "cd evolve && python3 shiftrun.py C"` (the runner is prepared after this file; its commit is named below before "go").
- **72 and 84 bits:** 2′a (the base) against 2′b alone (goff on, root), all map numbers (480, 560).
- **96 bits:** 2′b (the base) against 2′b+pp3 at +0, all 640 map numbers.
- 8 wall-clock replicates per size in seeded random orders; the new clock options (period 0.05 s, skip_launch; inner as set in the runner); cap 2.4 GHz (the user's standing cap; checked before "go").
- At 96, the wall replicates run with `LAMPCORE_SIEVEBREAK` off, then one `LAMPCORE_SIEVEBREAK=1` pass per cell (NOTES, "Sieve breakdown").

## The reviewer's (verbatim; base 2′a unless stated)

      R2-18 2'b vs 2'a: official 72: 1.04 to 1.10; 84: 1.02 to 1.07. ruint 72: 0.89 to 0.94;
            84: 0.87 to 0.92. Montgomery within 0.01 below ruint at each size. Wall 72: -8% to
            -13%; 84: -9% to -14%.
      R2-19 2'b is faster than 2'a on wall at both sizes, with 95% intervals excluding zero
            (80%).
      R2-20 At 96, sv:free2 accounts for 30 to 55 us per number of 2'b+pp3's sieve excess over
            2'b, and is the largest single sieve sub-region difference.

## Time order (Claude Code's record)

- **The brief with R2-18..R2-20 was received before any count was computed.**
- **While preparing the cost note** (item 1 of the same brief), Claude Code ran a count pass (`run_many --types`, no timing). Besides the pp 3 cells, it included 2′b at 72 and 84, and so **printed 2′b's priced totals at 72 and 84** (the quantities R2-18's priced ranges predict). The cost note did not need them.
- **R2-18's priced clauses are therefore deterministic and were seen by Claude Code before this file was committed.** The reviewer had not seen them, and Claude Code has not relayed them. Wall-clock (R2-18's wall clauses, R2-19) and the 96-bit breakdown (R2-20) are unmeasured.
- Whether R2-18's priced clauses count as sealed is the user's call.
