# baseline-yafu-qs: the card's QS against YAFU's QS called directly (the fair re-run; information only): predictions

**Status:** being filed. **Not timed.** The user is asked first whether DeepSeek's and Grok's predictions are to be filed too, and how YAFU's "internal SIQS time" is to be defined (below).

**Design:** NOTES.md, "Proposed: a fair YAFU re-run". The user decided to run it (Oct 27 evening): the card against YAFU's `siqs()` called directly; YAFU's fixed per-line cost timed as its own cell (`abs(@)`); YAFU's internal SIQS time recorded beside wall; a callgrind cross-check; the CPU-tuned YAFU build optional.

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
