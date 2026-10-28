# baseline-yafu-qs: the card's QS against YAFU's QS called directly (the fair re-run; information only): predictions

**Status:** being filed. **Not timed.** The user's answers (Oct 27 evening):
- DeepSeek's and Grok's predictions are filed before timing.
- YAFU's internal SIQS time is measured by **(a)**, the instrumented copy, with (b) recorded beside it.

**Design:** NOTES.md, "Proposed: a fair YAFU re-run". The user decided to run it (Oct 27 evening): the card against YAFU's `siqs()` called directly; YAFU's fixed per-line cost timed as its own cell (`abs(@)`); YAFU's internal SIQS time recorded beside wall; a callgrind cross-check; the CPU-tuned YAFU build optional.

**The card:** the **current** reference binary, 2′b plus the A-prime lookup fix (lampcore release, sha256 ef345913…).
- **The user's note, as given:** "all forecasters' predictions quoted pre-fix card times (0.86 / 1.54 / 3.37 ms), ~2-6% slower than the current card. The ratios are scored as measured, with that noted."
- **A correction to that note, from the record:** the quoted times are Run B's card on the balanced band, and **Run B already used the post-fix binary.** The binary was rebuilt with the fix at 20:03:47 (f988aab, 20:05); Run A timed it as "2′b+fix" (ef345913…, de74839, 20:55); Run B started at 20:56:15 on the same binary (`baseline_yafu.json`: `card_binary` is the release build).
  - So 0.86 / 1.54 / 3.37 ms **are current-card times**, and there is no 2–6% offset to note.
  - The pre-fix times would be about 2–6% slower: Run A, all map numbers, 846.6 / 1,594.9 / 3,555.3 µs before against 831.8 / 1,553.8 / 3,352.7 after.
- The ratios are scored as measured either way.

**Information all forecasters saw:** the unsealed diagnosis estimate (5eadb1e). card / YAFU's QS alone (smallmpqs − abs) was **1.33 / 1.32 / 1.71** at 72 / 84 / 96 on the balanced band. YAFU's QS alone was 0.65 / 1.17 / 1.97 ms; the card's balanced wall was 0.86 / 1.54 / 3.37 ms (Run B).

**The reconciliation, before timing** (`evolve/yafu_reconcile.py`, `.out`, `.json`; 96 bits, balanced band, batches of 80 / 160 / 320 lines, a straight-line fit). `siqs()` direct at 10.5 ms per number in 20-number batches decomposes as:
- **4.38 ms:** YAFU's per-line floor (`abs(@)`);
- **1.99 ms:** tinysiqs, the QS itself (smallmpqs − abs per line);
- **0.51 ms:** `siqs()`'s primality, square and power checks (siqs − smallmpqs per line);
- **about 3.85 ms:** a one-time cost of 77 ms (the prime sieve to 10⁸ and start-up), spread over 20 numbers. Over 80 numbers it is about 1 ms, giving the 7.8 ms measured there.
- The parts add to 10.7 ms.

**YAFU's internal SIQS time: YAFU does not report one on this path.** Below 115 bits `siqs()` goes straight to tinysiqs (`check_specialcase` in `factor/qs/siqs_test.c`). Its log has only second-resolution timestamps, and `-v -v` prints no elapsed time. `factor()`'s "Total factoring time" includes the rho pretest. Two ways to get it, the user's choice:
- **(a)** an instrumented copy of YAFU, built in Claude's scratch with the user's clone untouched: a monotonic clock read before and after the `tinysiqs` call, printed per number. The QS code is unchanged.
- **(b)** the per-replicate difference yafu_qs − yafu_floor (smallmpqs − abs) as the internal time: no YAFU change, but a difference of two timings.

## The reviewer's R-23 / R-24 / R-25 (Oct 27 evening; sealed; verbatim)

      R-23 96 bits, balanced band, card / YAFU-QS (YAFU's internal SIQS time): 1.2 to 2.2 (YAFU faster).
           70%.
      R-24 72 bits, same: 1.0 to 1.8. 65%.
      R-25 YAFU's wall per number via siqs() direct minus its internal SIQS time (the unexplained
           overhead) at 96 bits: more than 3 ms. 60%.

**Note on R-25** (the range is unchanged): siqs() direct's wall per number depends on the batch length, through the one-time 77 ms. The design's batch is the balanced band, 80 numbers, so the one-time cost adds about 1 ms per number there.

## DeepSeek's D-23 / D-24 / D-25 (21:17 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
Ratio = card / YAFU-QS; >1 means YAFU is faster. Base: card = 2'b, balanced band, 2.4 GHz cap, AC, one pinned core, 4 replicates. YAFU configuration named in every definition: YAFU's siqs() called directly, internal SIQS time as reported by YAFU's own timer.

D-23 — 96 bits, balanced band, card / YAFU internal SIQS. Definition: card wall per number / YAFU's internal SIQS time per number, YAFU = siqs() direct, internal SIQS timer, 96-bit balanced band. Sealed range 0.55–2.00 (central 1.15), 55%. Falsifier: <0.40 or >2.60.
Working: card balanced wall at 96 = 3.37 ms. YAFU internal SIQS not measured; two estimates disagree: (1) cost-note subtraction 1.97 ms, 3.37/1.97 = 1.71; (2) siqs() direct minus fixed per-line cost, 10.5 − 4.6 = 5.9 ms, 3.37/5.9 = 0.57. They don't reconcile (4.6 + 1.97 = 6.57 vs 10.5; ~4 ms unexplained). Plausible internal SIQS 1.5–6 ms, ratio 3.37/[1.5, 6] = [0.56, 2.25]. Centred at 1.15 rather than 1.71 because the unreconciled 4 ms is more likely to belong to SIQS than to vanish; top narrowed to 2.00 because the direct siqs() measurement caps how small internal SIQS can be. 55%: the range covers the plausible span; the centre is a judgement. Falsifier: <0.40 (internal SIQS more than ~8 ms) or >2.60 (internal SIQS below ~1.3 ms).

D-24 — 72 bits, balanced band, same definition. Card balanced wall at 72 = 0.86 ms; YAFU estimate 0.65 ms (0.86/0.65 = 1.32). Plausible internal SIQS 0.4–1.4 ms, ratio [0.61, 2.15]. Sealed range 0.65–2.10 (central 1.15), 55%. Falsifier: <0.45 or >2.60, same direction as D-23.

D-25 — 96 bits, YAFU siqs() direct wall minus internal SIQS time (the overhead), ms per number, balanced band. siqs() direct wall 10.5 ms; internal SIQS plausibly 1.5–6 ms; overhead 10.5 − [1.5, 6] = [4.5, 9.0] ms. Low end extended to 3.5 (fixed per-line cost 4.6 ms could be smaller at this size), high end to 9.5 (internal SIQS could be ~1 ms). Sealed range 3.5–9.5 ms (central 6.5), 55%. Missing input: internal SIQS time not measured; if the re-run reports it directly, D-25 is computed and scored as such. Falsifier: <2.5 ms (internal SIQS >8 ms) or >11.0 ms (negative internal SIQS).

Direction check on every falsifier: D-23/D-24 falsify if the ratio is too low (YAFU much slower than estimated) or too high (YAFU much faster than estimated); D-25 falsifies if overhead is too low (internal SIQS too large) or too high (internal SIQS too small).
<!-- verbatim end -->

**The reviewer's notes** (the ranges are unchanged): the falsifier directions are checked and correct; the YAFU configuration is named in every definition.

**Claude's notes for the record** (the ranges are unchanged):
- **The reconciliation.** D-23 says the two estimates "don't reconcile". The reconciliation (above) was committed in 7af3d61 at 21:16:32, one minute before D-23's 21:17 timestamp. Whether DeepSeek saw it is not known.
- **Replicates.** D-23 says "4 replicates"; the design in NOTES says 8. The run uses the design's 8; the definitions are otherwise the same.
- **"YAFU's own timer."** By the user's choice (a), the internal time is a monotonic clock around the `tinysiqs` call in an instrumented copy of YAFU, since YAFU prints none on this path. D-25 is scored with that time.
- **Batch length.** D-25's "siqs() direct wall 10.5 ms" was a 20-number batch. The re-run's batch is the 80-number balanced band, where the one-time 77 ms adds about 1 ms per number, not 3.85.

