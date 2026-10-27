# pp 3's meter-wall gap on 2′b, and the 2′b+pp3 threshold-shift test: predictions

**Scope:**
- The gap question: 2′b+pp3 against 2′b, wall-clock against price, from the i032-2prime run (9b94247).
- The shift test: 2′b+pp3 at +0, +1, +2 bits against 2′a, with the same runner design and the cap recorded. **Not prepared yet** when this file was created.

**Time order:**
- **The phase breakdown came before this filing.** The per-phase wall against priced breakdown for 2′b against 2′b+pp3 (NOTES, "pp 3 on 2′b: the meter against wall-clock"; `wolfram/2026-10-27_pp3_gap.wl`, `.out`) was computed, printed and committed in **8d5ef90**, before the brief asking to file this round reached Claude Code.
- **Items on the gap question are therefore information only:** breakdown seen first (by Claude Code, and in the repo). The reviewer and DeepSeek may not have seen it; the rule as given is about whether it had been printed or read.

## DeepSeek (received 22:10 Oct 26 PT)

- **D-11: information only, because the breakdown was seen first** (8d5ef90, committed before this filing).
  - **Timing, for the user's decision:** DeepSeek's reply was received at 22:10 PT. The breakdown commit 8d5ef90 is stamped 22:11:26 PT. The Wolfram output was printed a few minutes before that commit, in a local session that was not pushed.
  - So DeepSeek could not have seen the breakdown. The label follows the brief's rule (printed before filing). Reclassifying D-11 as sealed is the user's call. R2-11 (written after) is unaffected.
- **D-12, D-13 and the shift table: sealed.** The shift run is not prepared.

### Its reply (verbatim)

*(placeholder: the brief said the reply follows it, but no text followed; to be appended verbatim when the user pastes it)*

### The reviewer's annotations (ranges unchanged)

- **D-11:** its 242 µs arithmetic checks: 3,407.9 × 0.949 = 3,234 priced-implied, against 3,475 measured, about 241 µs. Its phase choice matches the reviewer's stated hypothesis, so it is not independent of it.
- **D-12:** the anchor subtracts 3 points from ratios measured against the OLD reference and applies them to ratios against 2′a (mixed bases). DeepSeek flags this itself as approximate.
- **D-13:** labelled estimated by DeepSeek (per-shift official is not computable from the given numbers).
- *Claude Code's note on bases, for the record:* the ~241 µs takes official's ratio (0.949) as the priced expectation for the whole cell. The breakdown in 8d5ef90 uses each region's own ruint conversion and finds +108.6 µs above price in total. These are different bases.

## Grok (received 22:11 Oct 26 PT)

- **Its phase prediction (section 1): information only, because the breakdown was seen first.** The breakdown commit 8d5ef90 is stamped 22:11:26 PT, and its Wolfram output was printed minutes earlier, local and unpushed.
  - Grok's reply was received at 22:11, so Grok could not have seen it.
  - The label follows the brief's rule (printed before filing). Reclassifying it is the user's call, as for D-11.
- **The shift table and the best-shift answers (section 2): sealed.** The shift run had not been run or prepared for running.
- Filed after DeepSeek's round (f65d7b4, 09f58ee) and after the breakdown (8d5ef90).

### Its reply (verbatim)

<!-- verbatim begin -->

**Sealed predictions (Grok, 26 Oct 2026 ~22:15 PT)**  
Using only the numbers supplied. Absolute phase times, per-op prices, candidate/partial counts per shift, and the exact hash overhead are missing; ranges reflect that.

### 1. Phase that explains most of the ~241 µs/number wall excess on 2'b+pp3 vs 2'b
**Large-prime table + lp_ledger** (confidence ~55 %).  
Expected excess there: 140–220 µs/number at 2.4 GHz.  

pp3 admits more candidates and more partial relations (stated). The known meter gap is that the large-prime table's hash already runs at 1.4–1.7× its price; extra partials therefore add both more hash traffic and more ledger work that the current pricing under-counts. Confirm wall rose from 0.562 to 0.679 of 2'a, consistent with more work landing after the sieve, but the largest unpriced component is the hash/ledger path that scales with partials.  

**Falsifier:** phase breakdown shows sieve + confirm + root_test together account for ≥70 % of the 241 µs, and large-prime table + lp_ledger together account for ≤80 µs.

### 2. Next timed run — 2'b+pp3 at threshold shifts +0 / +1 / +2 bits vs 2'a  
(same design, 2.4 GHz cap; base = 2'a)

| Shift | Official          | ruint             | Montgomery        | Wall (%)          |
|-------|-------------------|-------------------|-------------------|-------------------|
| +0    | 0.955–0.970      | 0.865–0.880      | 0.860–0.875      | −8.5 to −11.5    |
| +1    | 0.950–0.968      | 0.860–0.878      | 0.855–0.873      | −9.0 to −12.5    |
| +2    | 0.948–0.966      | 0.858–0.876      | 0.852–0.872      | −9.5 to −13.0    |

- **Best wall:** +2 bits (the earlier old-code series had +2 best on wall; the new base is cleaner, but the same relative pattern is expected).  
- **Best robust ratio:** +0 bits (official improves least as the shift rises, because more candidates/partials raise the unpriced hash/ledger load; the fast pricings stay similar or improve only marginally).  

(Prior old-code wall ratios vs the old reference were +0 0.930, +1 0.918, +2 0.911; those are not directly transferable, but the direction of the shift effect is the only quantitative clue given.)

---

Notes on scoring: interval widths above are full widths. All ranges are sealed before any phase breakdown or new timings are seen.

<!-- verbatim end -->

### The reviewer's annotations (Grok's ranges unchanged)

- **Not independent:** the phase choice matches DeepSeek's D-11 and the reviewer's R2-11 (the ledger).
- **Its falsifier requires both conditions** (sieve + confirm + root_test ≥ 70% of 241 µs, **and** the ledger ≤ 80 µs). Recorded as written.
- **"Best robust ratio: +0" contradicts its own table,** whose official centres fall with the shift (+0 ~0.963, +1 ~0.959, +2 ~0.957). Both are scored as written.
- **Its reasoning has the direction reversed:** a higher threshold admits fewer candidates (old confirm ratios 0.640 → 0.391 from +0 to +3). It also lets an unpriced cost change a priced ratio, which cannot happen: unpriced work shows only in wall-clock.
- **Its note that "interval widths above are full widths" applies to no item** (this round has no interval prediction).
- *Claude Code's note, for the record:* Grok's table says "same design, 2.4 GHz cap". The shift runner (evolve/i032shift.py) records the cap from the machine state and does not set one. At filing, core 2's limit read 5,000 MHz (the user restored it after i032-2prime).

## The reviewer's (verbatim; information only, under the same condition as D-11: breakdown seen first)

      R2-11 The ~241 us/number wall excess of 2'b+pp3 over its priced expectation sits
      mostly OUTSIDE the sieve (the sieve's wall falls under pp3: 0.949 vs 2'b's 1.014).
      lp_ledger (large-prime table and ledger) is the largest single contributor, 55%;
      confirm/root_test is second. Falsifier: the sieve phase shows a wall excess over
      its priced expectation of more than 60 us, or lp_ledger contributes less than
      confirm/root_test.
