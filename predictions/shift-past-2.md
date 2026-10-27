# Run A (shift-past-2): 96 bits, 2′a, 2′b, 2′b+pp3 at +1 and +3: predictions

**Run:** `tools/sealed_run.sh shift-past-2 -- bash -c "cd evolve && python3 shiftrun.py A"`.
- 96 bits, all 640 map numbers, re-sieve off; the reference genes with goff = 1 (the reference since Oct 26).
- Cells: 2′a (the base), 2′b (goff on, root), 2′b+pp3 at +1 and +3 bits (tc − d / log2 1,752, as in pp3-gap-and-shift).
- Same design as pp3-gap-and-shift (`evolve/i032shift.py`, 0afa437): identity first; priced with paired 95% bootstrap (10,000, random.Random(2026)); 8 wall-clock replicates in seeded random orders (seed 2029), lampcore `--phasetime` on core 2, every region saved with its own ruint and calls; one LPBREAK pass per cell (information).
- **Region excess over own-rate price** (the D-14 / G-7 method of the pp3-gap-and-shift scoring, NOTES): per region, (wall ratio − ruint ratio) × the base's region mean, per replicate, mean and 95% t. **Base 2′b** for R2-16 (2′a also printed, information).
  - **scan has no ops of its own** (sieve_scan is charged in the sieve region), so its expected ratio is the ratio of its calls (polynomials scanned). This definition is Claude Code's, set in the runner before sealing; the reviewer did not specify one.
- **Cap:** the user's standing 2.4 GHz cap (PROTOCOL.md); checked before "go"; never set by Claude Code.

## The reviewer's (verbatim; sealed Oct 27, before any run of this design)

      R2-15 (A) 2'b+pp3 +3 vs 2'a: official 1.035 to 1.075; ruint 0.870 to 0.895;
            Montgomery 0.865 to 0.890; wall -11% to -15%. +2 stays the best wall shift at
            96 (+3 no better than +2 by more than 0.5 points), 60%.
      R2-16 (A) Against 2'b, no rest sub-region shows a wall excess over its own-rate price
            above 25 us per number at +1.

### Claude Code's notes on scoring (before the run)

- **R2-15's "+2 stays the best wall shift":** run A has no +2 cell (the cells are as briefed). Unless +2 is added before "go", it is scored against +2's wall from pp3-gap-and-shift (9ed805a): 0.8650 against 2′a (−13.5%), a cross-run comparison of ratios to each run's own 2′a. +1 is in both runs and is reported in both, as a check of run-to-run drift.
- **R2-16's sub-regions:** setup, gray, scan, lp_ledger and solve (the rest split as briefed). mult and fb are printed as well (a few µs per number).
- **"Above 25 µs" is scored on the point estimate;** the 95% interval is reported next to it.

## The user's provisional choice (recorded before the run)

- **2′b+pp3 at +1, provisional; not adopted; pending runs A and B** (NOTES, "Provisional choice (the user's, Oct 27)").
