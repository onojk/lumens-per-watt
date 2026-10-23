# Decision log

## 2026-10-22 — The cumulative total is the scoreboard

- **Efficiency is judged by cumulative totals.** Watts are counted from the first operation to the last, for every test number, and summed. Lumens are the stations darkened by the end. Cumulative lumens ÷ cumulative watts is the algorithm's efficiency; its inverse is the inefficiency.
- **The running curve is the diagnostic, not the score.** Lumens plotted against cumulative watts shows *where* the watts went (steady sweep, ballast up front, scattered lucky hits), which is what you need to improve a bulb.
- **How a station goes dark.** A station s is dark once the algorithm would have caught p if p = s. This is measured by planting the secret: run on many semiprimes whose p values are spread across the stations, and record the cumulative watts each one took. It works the same way for lucky and luck-free methods.
- **Runs 1 and 2 used worst-case scoring.** Run 3 starts over on cumulative scoring, with fresh seeds, and records worst cases alongside so the two can be compared.

## 2026-10-22 — Luck by design has to pay for its prediction

- A luck-by-design card only helps when predicting a good test is cheaper than running a bad one. For Hart-style square searches a test costs 1 op, so ranking candidates (14 ops each) can't pay.
- The hit-rate column is per *test*, and what counts as a test differs by lamp (a gcd batch in rho, a square test in a square search). Compare hit rates within a lamp family, not across families.
- A gain on 12 validation numbers is a lead, not a result. Recheck on a larger fresh sample before writing it down (luck-33 shrank from 0.5 to 0.17 in log₂ on 80 numbers).

## 2026-10-22 — Small sizes pick constants; scale picks exponents

- Below about 54 bits, constants decide the winner: the Hart family's small constant beat rho. From 60 bits up, the exponent decides: rho's N^(1/4) beats the Hart family's N^(1/3), by about 5× at 78 bits.
- Evolution scored at 32–48 bits can only tune constants. To grow a better exponent, fitness has to be measured where exponents dominate: run evolution through the Rust core at 60+ bits.
- Big-number results are trusted only through `lampcore` after `parity.py` passes.

## 2026-10-23 — Square-search windows end at √(kN) + width, inclusive

- **The window is a range of x, not a count.** The theory window for multiplier k is √(kN) ≤ x ≤ √(kN) + width. The old code tested `int(width)` values from ⌈√(kN)⌉, which drops the last x whenever √(kN)'s fractional part pushes the range across an integer. This caused Lehman's 66-bit miss (k = 59881, width 1.73, needed x0 + 1). The 0.25 constant was correct, and widening it would have hidden the bug.
- **Never take a float sqrt of kN.** Past 60-bit N it loses about 10 bits. Use the exact integer square root s and add f = (kN − s²)/(2s), converting both to float before dividing. Python and Rust use the same expressions, so parity holds.
- **Instrumentation is read-only.** Both cores report the winning stage and a square-search win's k. Every gate compares op counts with and without it.
- **Coverage rule: complete is not the same as affordable.** A genome whose stages stop short of √N gets a fallback tail, charged and flagged. The no-luck fallback, trial division to √N, is provably complete but can exceed the cap. The luck fallback, rho, is heuristic: it has no proven bound, and it can return nothing when its gcd hits N. The rule is opt-in (`lamps.use_coverage_rule()`), so replays of Runs 2–5 are unchanged.
- **no-luck-32 at 78 bits.** Its square search, block flash, and trial division all stop below the secret (p = 2^38.3), so it can never be caught. Under the 2^29 cap it never gets that far: the block flash uses up the budget first. With the tail it becomes catchable in principle (trial division needs about 2^37.3 operations) but is still over budget, so the cell keeps its *.
