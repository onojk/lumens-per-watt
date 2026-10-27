# pp 3's meter-wall gap on 2′b, and the 2′b+pp3 threshold-shift test: predictions

**Scope:**
- The gap question: 2′b+pp3 against 2′b, wall-clock against price, from the i032-2prime run (9b94247).
- The shift test: 2′b+pp3 at +0, +1, +2 bits against 2′a, with the same runner design and the cap recorded. **Not prepared yet** when this file was created.

**Time order:**
- **The phase breakdown came before this filing.** The per-phase wall against priced breakdown for 2′b against 2′b+pp3 (NOTES, "pp 3 on 2′b: the meter against wall-clock"; `wolfram/2026-10-27_pp3_gap.wl`, `.out`) was computed, printed and committed in **8d5ef90**, before the brief asking to file this round reached Claude Code.
- **Items on the gap question are therefore information only:** breakdown seen first (by Claude Code, and in the repo). The reviewer and DeepSeek may not have seen it; the rule as given is about whether it had been printed or read.

## DeepSeek (received 22:10 Oct 26 PT)

- **D-11: information only, because the breakdown was seen first** (8d5ef90, committed before this filing).
- **D-12, D-13 and the shift table: sealed.** The shift run is not prepared.

### Its reply (verbatim)

*(placeholder: the brief said the reply follows it, but no text followed; to be appended verbatim when the user pastes it)*

### The reviewer's annotations (ranges unchanged)

- **D-11:** its 242 µs arithmetic checks: 3,407.9 × 0.949 = 3,234 priced-implied, against 3,475 measured, about 241 µs. Its phase choice matches the reviewer's stated hypothesis, so it is not independent of it.
- **D-12:** the anchor subtracts 3 points from ratios measured against the OLD reference and applies them to ratios against 2′a (mixed bases). DeepSeek flags this itself as approximate.
- **D-13:** labelled estimated by DeepSeek (per-shift official is not computable from the given numbers).
- *Claude Code's note on bases, for the record:* the ~241 µs takes official's ratio (0.949) as the priced expectation for the whole cell. The breakdown in 8d5ef90 uses each region's own ruint conversion and finds +108.6 µs above price in total. These are different bases.

## The reviewer's (verbatim; information only, under the same condition as D-11: breakdown seen first)

      R2-11 The ~241 us/number wall excess of 2'b+pp3 over its priced expectation sits
      mostly OUTSIDE the sieve (the sieve's wall falls under pp3: 0.949 vs 2'b's 1.014).
      lp_ledger (large-prime table and ledger) is the largest single contributor, 55%;
      confirm/root_test is second. Falsifier: the sieve phase shows a wall excess over
      its priced expectation of more than 60 us, or lp_ledger contributes less than
      confirm/root_test.
