# Run B (shift-72-84): the 2′b+pp3 shift test at 72 and 84 bits: predictions

**Run:** `tools/sealed_run.sh shift-72-84 -- bash -c "cd evolve && python3 shiftrun.py B"`.
- 72 and 84 bits, all map numbers (480 and 560), re-sieve off; each size's reference genes with goff = 1.
- Cells per size: 2′a (the base); 2′b+pp3 (goff on, root, pp 3) at +0, +1, +2 bits.
- **Shift:** tc − d / log2 B̄, with B̄ the mean of the card's B (`lctest.bnd`) over the size's map numbers: **588.5 at 72, 1,094.5 at 84** (at 96 the same computation gives 1,754.3; the 96-bit runs use 1,752, the measured mean in NOTES).
- Same design as pp3-gap-and-shift (`evolve/i032shift.py`, 0afa437): identity first; priced with paired 95% bootstrap (10,000, random.Random(2026)); 8 wall-clock replicates per size in seeded random orders (seed 2030 + bits), lampcore `--phasetime` on core 2, every region saved with its own ruint and calls; region excess against 2′a (information); one LPBREAK pass per cell (information).
- **Cap:** the user's standing 2.4 GHz cap (PROTOCOL.md); checked before "go"; never set by Claude Code.

## The reviewer's (verbatim; sealed Oct 27, before any run at 72 or 84 of this design)

      R2-17 (B) At both 72 and 84: official is best at +0, wall is best at +1 or +2, and +1
            is better than 2'a under all three pricings. 60% for all three holding at both
            sizes.

### Claude Code's notes on scoring (before the run)

- **"Official is best at +0":** the lowest official ratio against 2′a of the three shifts, on the point estimate. **"Wall is best at +1 or +2":** the lowest wall ratio, point estimate.
- **"+1 is better than 2′a under all three pricings":** all three ratios below 1. The (e) call (all three 95% intervals below 1) is reported next to it.
- **The 60% is on the conjunction:** all three clauses at both sizes (six clauses). Each clause is also reported.

## The user's provisional choice (recorded before the run)

- **2′b+pp3 at +1, provisional; not adopted; pending runs A and B** (NOTES, "Provisional choice (the user's, Oct 27)").
