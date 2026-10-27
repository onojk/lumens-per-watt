# Stage H predictions — a copy of already-sealed predictions (not new ones)

Every prediction below was sealed earlier and recorded in NOTES.md before any stage H comparison ran. This file copies those NOTES lines verbatim (by line extraction) so that `tools/sealed_run.sh stage-h` can check them. The commit where each block was first recorded is given above it. NOTES.md remains the record; scoring goes there.

Reference: 96 bits, all 640 map numbers, re-sieve off, reference genes (tc 1.0353). Cells: (i) pp 10, tc 1.0353; (ii) pp 10, tc 0.7623 (candidates matched, `hsearch.out`); (iii) pp 10, tc 0.5713 (+5 bits); (iv) pp 3, tc 0.7569 (+3 bits, "2 free").

## The user's (the reviewer's): H-1 … H-10, first recorded in 69860d5


**Stage H, sealed predictions (the reviewer's).** 96 bits, all 640 map numbers, against the reference (re-sieve off).

*(i) option on, reference threshold:*
- **H-1** partial capture (stage B's 8-number subset): 0.60–0.80.
- **H-2** candidates per number: +35% to +120%.
- **H-3** polynomials: −15% to −27%.
- **H-4** priced ruint mean: −3% to +15%.
- **H-5** selectivity (extra partials looked up per extra candidate, against the reference): 1.3x to 3x the value of stage G's −4-bit cell.
- **H-6** median sieve under-count at true partials: 0.5–2.0 bits (from 4.6).

*(ii) option on, tc set so candidates per number match the reference:*
- **H-7** partial capture: 0.40–0.58 (from 0.316).
- **H-8** polynomials: −6% to −16%.
- **H-9** priced ruint mean: −12% to −2%.
- **H-10** wall-clock mean (two replicates): −12% to +2%.

## DeepSeek round 43: H-1 … H-10, first recorded in 7cae56e


**SEALED, stage H** (96 bits, all 640 numbers, against the reference, re-sieve off):

*(i) option on, reference threshold:*
- **H-1** partial capture 0.62–0.82 (0.74). Falsified if < 0.55 or > 0.90.
- **H-2** candidates per polynomial +115% to +145% (+130%); per number +45% to +110% (+75%). Falsified (per number) if < +20% or > +150%.
- **H-3** polynomials −18% to −30% (−24%). Falsified if > −10% or < −36%.
- **H-4** priced ruint −3% to +15% (+5%). Falsified if < −9% or > +22%.
- **H-5** extra partials per extra candidate, as a ratio to the −4-bit cut: 1.25x–1.85x (1.55x). Falsified if < 1.00x or > 2.20x.
- **H-6** median under-count at true partials 0.0–1.5 bits (0.4). Falsified if < −0.5 or > 2.5.

*(ii) option on, matched candidates:*
- **H-7** partial capture 0.33–0.48 (0.39). Falsified if < 0.28 or > 0.55.
- **H-8** polynomials −1% to −12% (−5%). Falsified if > +2% or < −18%.
- **H-9** priced ruint −8% to +2% (−3%). Falsified if < −14% or > +10%.
- **H-10** wall-clock −8% to +4% (−2%). Falsified if < −14% or > +12%.

## The user's: H-11 … H-15, cell (iii), first recorded in cd4e1bd

**Cell (iii):** option on (pp 10), threshold raised by +5 bits relative to today's, through tc only (tc = 1.0353 − 5 / 10.775 = 0.5713; L unchanged). All 640 numbers, reported as (i) and (ii), with candidates both per number and per polynomial.

- **H-11** (iii) polynomials: −2% to −11% (model −6.5%).
- **H-12** (iii) candidates per number: −18% to −38% (model ~−28%); per polynomial −15% to −32%.
- **H-13** (iii) wall-clock (two replicates): −3% to −13% (model −8.3%).
- **H-14** (iii) priced ruint: −14% to +4% (no model value; priced may disagree with wall-clock).
- **H-15** (iii) never-combined share: 0.70–0.82 (model 0.769).

## DeepSeek round 47: H-11 … H-15, first recorded in 130135d


**SEALED, cell (iii)** (option on, threshold +5 bits, tc only, all 640 numbers):
- **H-11** polynomials −3% to −12% (−7%). Falsified if > +2% or < −18%.
- **H-12** candidates per number −18% to −38% (−28%); per polynomial −15% to −32% (−23%). Falsified (per number) if > −8% or < −48%.
- **H-13** wall-clock −3% to −14% (−8%). Falsified if > +3% or < −20%.
- **H-14** priced ruint −10% to +2% (−4%). Falsified if < −18% or > +8%.
- **H-15** never-combined 0.72–0.81 (0.77). Falsified if < 0.65 or > 0.86.

## The user's: H-16 … H-18, cell (iv), first recorded in 3356813


**Cell (iv):** "2 free" (pp = 3) at +3 bits, tc only (tc = 1.0353 − 3 / 10.775 = 0.7569; L unchanged). All 640 numbers, same reporting.
- **H-16** (iv) wall-clock: −2% to −10% (model −6.6%).
- **H-17** (iv) priced ruint: −2% to −12% (no added sieve work and fewer candidates, so priced should not lag wall-clock as it may for G).
- **H-18** (iv) extra sieve hits / sieve wall-clock: ~0 (the sieve region within ±3% of the reference per polynomial).

## DeepSeek round 49: H-16 … H-18, first recorded in 55dd791


**SEALED, cell (iv)** ("2 free" at +3 bits, tc only, all 640 numbers; cell (iv) was added, as pp = 3, in 3356813):
- **H-16** wall-clock −3% to −11% (−6.5%). Falsified if > +2% or < −17%.
- **H-17** priced ruint −3% to −13% (−7%). Falsified if < −20% or > +3%.
- **H-18** sieve wall-clock per polynomial −1% to +1% (0%). Falsified if < −3% or > +3%.
