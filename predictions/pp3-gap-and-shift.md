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

*Filed after the breakdown (8d5ef90) and after Grok's round (ae97145); received 22:10 Oct 26 PT, before the shift runner was committed (ba253c2) and before any shift run. Copied verbatim from the user's brief.*

<!-- verbatim begin -->

## 0. Recorded

- **D-1–D-6 held; D-7 missed** (measured ±0.6 to ±2.9 under the 2.4 GHz cap; D-7 was sealed assuming no cap). **D-8 falsified on all three pricings, held on wall.** **D-9 falsified.** No first-round falsifiers triggered. **D-10 information-only: "above 1.0137" missed** — exact model and card both gave 1.0137. Recorded as scored; no rescore.
- Cause of D-8/D-9 accepted: pp3's official saving was underestimated; the robust-ratio annotation said so before the run. Grok's G-3/G-4 miss noted. Reviewer R2-8 missed; 9/10 held. Recorded.
- The meter/clock disagreement on pp3 is recorded as a live finding, not a resolved one.

## 1. Sealed phase prediction

Registered before the phase breakdown is read. The gap is **7.1 points** (price −5.1%, wall +2.0%). In wall terms at 2.4 GHz: 3,407.9 µs × 0.071 = **242 µs**.

So the phase carrying the excess should show roughly **240 µs per number** beyond what the meter charges it.

| ID | Prediction | Sealed answer | Falsifier |
|---|---|---|---|
| **D-11** | Phase explaining most of the 7-point gap; per-number wall excess in that phase | **lp_ledger** (large-prime table hash + ledger storage), confidence **60%**; excess **180–300 µs** (central **240 µs**) | Falsified if lp_ledger contributes **<120 µs** of the excess, or if sieve or confirm/root_test contributes **more than lp_ledger** |

**Reasoning, one sentence:** pp3 admits more candidates and more partial relations, so the ledger's lookups and storage grow, and the hash is already known to run at 1.4–1.7× its price; that is the one phase with both a measured underpricing and a direct pp3-driven workload increase.

Anchor: 2'b+pp3 confirm ratio 0.679 vs 2'b 0.562 means pp3 **raises** confirm work relative to 2'b, consistent with more candidates admitted, which also means more partials filed and more ledger traffic. The known 1.4–1.7× hash underpricing then converts that traffic into wall excess the meter does not see. I do not have the phase breakdown, so the 240 µs figure is **estimated** from the 7.1-point gap, not computed from per-phase data.

## 2. Sealed predictions for the shift test

Registered before the run. 96 bits, 640 numbers, re-sieve off, cap 2.4 GHz. **Base is 2'a.** Ratios new/old; below 1 = cheaper; robust = worst of the three.

| Shift | Official (range, central) | Ruint (range, central) | Montgomery (range, central) | Wall change (range, central) |
|---|---|---|---|---|
| **+0** | 0.955–0.970 (0.962) | 0.862–0.880 (0.870) | 0.858–0.875 (0.866) | −8.5% to −11.5% (−10.0%) |
| **+1** | 0.950–0.968 (0.959) | 0.855–0.878 (0.866) | 0.850–0.874 (0.861) | −10.0% to −13.5% (−11.8%) |
| **+2** | 0.952–0.972 (0.962) | 0.855–0.880 (0.868) | 0.850–0.876 (0.863) | −10.5% to −14.5% (−12.5%) |

| ID | Question | Sealed answer | Falsifier |
|---|---|---|---|
| **D-12** | Which shift has the **best wall**? | **+2 bits** (central −12.5%), with +1 within ~1 point | Falsified if +0 or +1 beats +2 by **>0.5 points** |
| **D-13** | Which shift has the **best robust ratio**? | **+1 bit** (official is the worst of three, and +1 gives the lowest official), with +0 close | Falsified if +0 or +2 gives a robust ratio **>0.005 lower** than +1 |

**Computed anchor for D-12.** Old-code wall ratios vs old reference: +0 0.930, +1 0.918, +2 0.911 (best), +3 0.925. New code at +0 is 0.901 vs 2'a, a ~3-point improvement over old +0 (0.930). Carrying that shift forward approximately: +1: 0.918 − 0.030 = 0.888 (−11.2%); +2: 0.911 − 0.030 = 0.881 (−11.9%).

The ledger finding (D-11) pushes the optimum slightly higher because raising the threshold reduces partials and ledger traffic; hence central −12.5% at +2 rather than −11.9%.

**Computed anchor for D-13.** At +0, robust = official = 0.9618. Official falls as the shift rises while confirm-op count falls, then turns up when polynomial word ops dominate. The old confirm ratios fell 0.640 → 0.545 → 0.458 from +0 to +2, while sieve rose 1.073 → 1.147 → 1.226; the official optimum is where those marginal costs balance, which I expect near **+1**. I cannot compute the official per-shift totals from the numbers given; the D-13 answer is **estimated**, and the per-shift official ranges above are centred accordingly.

**Falsifier scope.** D-12 and D-13 are one-shot categorical claims for this grid. If the +0, +1, +2 wall values land within 0.5 points of each other, I will record the "best" as **tied within noise** rather than claim a winner; the falsifiers above still apply.

No sealed prediction is revised. D-11, D-12, D-13 are registered above.

<!-- verbatim end -->

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

## The reviewer's (verbatim; sealed Oct 26, before any shift run; base 2′a, now the reference; cap 2.4 GHz; 8 replicates)

      R2-12 +0 priced ratios reproduce tonight's exactly (0.9618 / 0.8703 / 0.8656);
            +0 wall -8.5% to -11.5%.
            +1: official 0.962 to 0.985; ruint 0.855 to 0.880; Montgomery 0.850 to 0.875;
                wall -10% to -13%.
            +2: official 0.968 to 0.995; ruint 0.850 to 0.880; Montgomery 0.845 to 0.875;
                wall -10% to -14%.
      R2-13 Best wall: +2 (50%); +1 and +2 within 1 point of each other; +0 the slowest.
      R2-14 Best robust ratio: +0 (70%), because official rises with the shift (official
            prices sieve updates like root tests, and a higher shift needs more
            polynomials). Falsifier: +1 or +2 has official below 0.9618.

## DeepSeek (received 22:20 Oct 26 PT)

- **D-14: sealed.** The shift run has not started, and the runner's sub-region split has not been read; the smoke checks printed no results.
- **Its "Note on D-12":** information only. **D-12 stays sealed as written.**

### Its reply (verbatim)

<!-- verbatim begin -->

## 0. Recorded

- **D-11 arithmetic correction accepted.** My 241 µs figure was correct for the number I was given, but the number was wrong: official charges sieve updates and root tests equally, so most of official's −5.1% is sieve savings. Using each phase's own ruint rate, the price gap is **−2.0%** and the wall gap **+2.0%**, for about **4 points, 109 µs per number**. My 241 µs is annotated as based on the wrong price expectation. **D-11 is information only**, with the whole "rest" bucket at 81 µs under my 120 µs floor; the falsifier would trigger, and I record that.
- Phase breakdown recorded: sieve +33 µs above price, confirm −5 µs (tracks price), rest +81 µs. Confirm is priced honestly at ~0.60 µs/candidate. Hash under-pricing explains only 4–7 µs. Kept-relation copies (+198/number, ~4× price) are the likelier part of the 81 µs but not established.
- Instrumentation bug noted: `--phasetime` dropped root_test; the meter and `--types` are correct.
- **D-12, D-13, shift table remain sealed.** The reviewer and Grok both picked +2 for best wall; reviewer and Grok picked +0 for best robust ratio; I picked +1. **D-12 and D-13 are a genuine disagreement** with the reviewer and Grok on the robust-ratio question.
- 2'a adopted as the reference default; 2.4 GHz cap is standing; earlier uncapped runs are not comparable; interval predictions from now assume the cap. The +0 cell reproduces tonight's priced ratios exactly.

## 1. Sealed D-14

Registered before the shift runner's split is read. **Assumption stated explicitly:** I assume the kept-relation copies are attributed to **lp_ledger**, consistent with the round-29 measurement that placed the copying of each kept relation's sparse list inside lp_ledger. If the shift runner instead attributes those copies to solve, then solve would be my answer by the same reasoning.

| ID | Question | Sealed answer | Falsifier |
|---|---|---|---|
| **D-14** | Of the ~81 µs "rest" excess at +0, which sub-region carries most? | **lp_ledger**, confidence **50%**; **50–70 µs** (central **60 µs**). Second: solve, ~10–20 µs. Third: setup, ~5–15 µs. | Falsified if lp_ledger carries **<30 µs**, or if solve or setup carries **more than lp_ledger** |

**Reasoning, one sentence:** pp3 admits about 21% more candidates and correspondingly more partials, so the ledger's hash lookups and kept-relation copies grow, and the hash is already known to run at 1.4–1.7× its price while the copies are uncharged by the meter; that combination is the only sub-region with both a measured underpricing and a direct pp3-driven workload increase.

**Size estimate, showing work:** if the 198 extra kept-relation copies carry ~0.30 µs each in wall (a plausible heap allocation plus sparse-list copy), that is 198 × 0.30 = 59.4 µs. Adding the measured 4–7 µs hash excess gives about 63–66 µs, inside my central 60 µs once some of the copy cost is priced. This is **estimated**, not computed; the per-copy wall cost is not on the parameter sheet and is a **missing parameter** I am flagging rather than assuming as measured.

## 2. Note on D-12 (optional, does not revise it)

The corrected gap is 109 µs, not 241 µs. A smaller wall excess in "rest" means the ledger-related penalty for pp3 is smaller, so raising the threshold (which reduces partials and ledger traffic) has less to gain. That pushes the optimum slightly **lower**, toward +1 rather than +2. **D-12 stays sealed as written** (−12.5% at +2); the note is that if the excess is mostly ledger-driven, I would expect the +1 and +2 wall values to be closer than my sealed table suggests, and the +2 margin over +1 to shrink toward zero. No change to D-12's sealed answer.

No sealed prediction is revised. D-14 is registered above.

<!-- verbatim end -->

### The reviewer's annotations (ranges unchanged)

- **D-14 says the kept-relation copies are "uncharged by the meter".** The breakdown found them charged but measured at ~4× their price: under-priced, not uncharged.
- **The 0.30 µs per copy is DeepSeek's assumption,** which it flags as a missing parameter.
- **Attribution (checked against NOTES and the code):**
  - The kept-relation copy is timed **inside lp_ledger**. Its sub-timer `lp:copy` opens within the lp_ledger region (`lampcore/src/qs.rs`, region 8; NOTES "DeepSeek, Oct 26, round 29 (I-028)": four sub-regions inside lp_ledger: lp:copy, lp:hash, lp:comb, lp:add). The shift runner's lp_ledger region includes it.
  - **D-14 is therefore scored on lp_ledger, as sealed.** Its "solve if the copies fall there" branch does not apply.
- *Claude Code's note:* the ~100 ns per copy for ~25 ns priced (NOTES, step 3) was measured **before** the lp_ledger arena fix (A2, bd89a24), which changed how kept relations are stored. The "~4× price" figure quoted in the breakdown (8d5ef90) may therefore overstate today's per-copy cost. This run's LPBREAK pass measures it again (information).

## Grok (received 22:24 Oct 26 PT)

- **G-7: sealed.** The shift run has not started, and the runner's sub-region split has not been read.

### Its reply (verbatim)

<!-- verbatim begin -->

**Sealed prediction G-7 (Grok, 26 Oct 2026 ~22:30 PT)**  
Using only the numbers supplied. Absolute per-sub-region times, exact copy costs, and the split of the prior "rest" bucket are missing.

### Of the ~81 µs wall excess in "rest" (2'b+pp3 vs 2'b, +0 cell)
**lp_ledger** (confidence ~60 %).  
Expected size: 45–70 µs/number at 2.4 GHz.  

I assume the kept-relation copies (+198 per number, previously measured at ~4× their price) are counted inside **lp_ledger**. That is the only concrete under-priced item named for this bucket; the large-prime hash itself accounts for only 4–7 µs, so the bulk of the residual must be the copy traffic that scales with the extra partials pp3 admits. Setup, gray, and scan have no stated extra work of this magnitude; solve is downstream of the ledger and would see the copies only after they have already been paid for in the ledger phase.

**Falsifier:** the split shows lp_ledger accounts for ≤30 µs of the excess and some other single sub-region (setup, gray, scan, or solve) accounts for ≥45 µs.

(The prediction is sealed before the shift runner's phase split is examined.)

<!-- verbatim end -->

### The reviewer's annotations (range unchanged)

- **Not independent:** the same answer and assumption as DeepSeek's D-14 (lp_ledger, with the copies counted there).
- **The falsifier needs both conditions:** it was requested as a single condition, but Grok's requires lp_ledger ≤ 30 µs **and** another single sub-region ≥ 45 µs. Recorded and scored as written.
- **Attribution:** as for D-14, the kept-relation copy is timed inside lp_ledger (sub-timer `lp:copy` within region 8, `lampcore/src/qs.rs`). **G-7 is scored on lp_ledger.**

## Shift run: the runner and its base

- **Runner:** `evolve/i032shift.py`, committed first in ba253c2. Before the run it is amended to also record ruint per region (setup, gray, scan, lp_ledger, solve split out); the commit that does so is named in the run record.
- **Base:** 2′a (goff = 1, full pass), the reference since the user's adoption (NOTES, "Decision (the user's, Oct 26): goff = 1 adopted").
- **Instrumentation:** the per-region priced counts use lampcore with the `--phasetime` fix (root_test attributed; the lp_ledger region closed on its early returns). `--types` and every result are identical to the pre-fix binary (14,000 / 14,000).

## State before the shift run (recorded before "go")

- **Runner and instrumentation:** `evolve/i032shift.py` and the `--phasetime` instrumentation fix, both as of **0afa437**. That commit adds ruint per region and attributes root_test and the lp_ledger early returns to their regions; counts are unchanged.
- **Machine-read:**
  - scaling_max_freq 2,400 MHz on all 8 cores (the user's standing cap); turbo enabled; governor powersave.
  - AC online, battery 94% and charging; TCPU 46 °C; load 1.2–1.6.
  - No Wolfram processes; 24 browser processes open.
- **Not stated for this run:** desk or lap, and the charger.
- **The user's conditions line (with "go", 00:08 Oct 27 PT):** laptop on the fan cooling pad, plugged in, untouched during the run. The desk/lap, charger and browser fields were left as template brackets (not stated); machine-read at go: cap 2,400 MHz on all 8 cores, AC online, no Wolfram processes, 27 browser processes, load 0.77.
