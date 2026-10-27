# I-032, option 2′ (start offsets kept by the Gray code): sealed predictions, filed before any code

**Definitions** (NOTES, "Design note: root confirm without the per-polynomial offset pass"; the user chose option 2′ on Oct 26):
- **2′a:** the Gray code keeps the start offsets in sieve coordinates (`sr`, `qr`), with the full-pass confirm. Every reader changes: the sieve loop, re-sieve and the root pass; the Gray update's arithmetic is unchanged. Built as a gene, off by default.
- **2′b:** 2′a plus root confirm reading the kept offsets in place (no per-polynomial pass). Not built yet.

**Time order:**
- The reviewer's R2-1..R2-8 were written at 20:04 on Oct 26, before the Wolfram cost model (f12ae23, committed 20:07:24) was seen.
- DeepSeek's D-1..D-7 were sealed at 20:08 on Oct 26, without the model.
- This file is committed before any 2′a code exists. **No acceptance or parity run of 2′a has printed priced totals**, because no 2′a code has run.
- The model's ratios (f12ae23) were in the repo before this file. They are recorded below as model, for reference only.

**Planned comparisons** (not yet; separate runs, each with its own run record):
- 2′a against today's reference: priced (official / ruint / Montgomery, means per number at 96, all 640 map numbers), relations, and wall-clock.
- 2′b against 2′a: priced, wall-clock and the sieve region.

## The reviewer's (verbatim; written 20:04 Oct 26, before f12ae23 was seen)

      R2-1 2'a vs today's reference, official: 0.965 to 0.985.
      R2-2 2'a vs today's reference, ruint and Montgomery: each 0.95 to 0.995.
      R2-3 2'a relations: identical per number (any difference is a bug, not a result).
      R2-4 2'a vs today's reference, wall: 0.93 to 1.00.
      R2-5 2'b vs 2'a, official 1.005 to 1.020; ruint 0.875 to 0.900;
           Montgomery 0.870 to 0.895.
      R2-6 2'b vs 2'a, wall: -7% to -14%.
      R2-7 2'b vs 2'a, sieve region: within +/-5%.
      R2-8 95% intervals: +/-3 to +/-6 points without a frequency cap.

## DeepSeek (Oct 26, 20:08), sealed

As transcribed in the user's brief (DeepSeek sealed these without the model). **DeepSeek's full reply text is to be appended verbatim when the user pastes it**; until then, this transcription is the record.

      D-1 official 0.965-0.985; D-2 ruint 0.982-0.992, Montgomery 0.980-0.990;
      D-3 wall 0.975-0.990; D-4 2'b vs 2'a official 1.008-1.018, ruint 0.878-0.898,
      Montgomery 0.874-0.894; D-5 wall -7% to -13%; D-6 sieve -2% to +2%;
      D-7 interval +/-4 to +/-6.
      Falsifiers: 2'a official > 1.000; 2'b vs 2'a official > 1.030;
      2'b vs 2'a wall > 0%.

### DeepSeek's full reply (verbatim)

*(placeholder: not yet pasted)*

## The reviewer's annotations on DeepSeek (DeepSeek's ranges unchanged)

- **D-5:** the reasoning double-counts. It uses today's root mode (wall 0.919) as "2′b with the pass" and divides by 2′a's saving, which 2′b also receives. The reviewer's estimate is ~−12%. The range stands as sealed.
- **D-3:** the reasoning conflates two things. The ~4% second pass exists only in root mode, while 2′a's saving against the reference is the sieve loop's start-offset recomputation, a separate quantity.
- **D-2's "word ops are 4.5% of ruint":**
  - **Source present:** `reviews/card_params.md:33` ("Priced shares (ruint): … word 4.5% …"). Recomputed from the reference's counts at 96: 103,028.95 word × 0.0258 / 59,071 = 4.50%.
- **D-2's "Montgomery's word price exceeds ruint's":**
  - **True per op:** 0.0951 against 0.0258 (`evolve/calibrate.json`; `reviews/card_params.md:58`).
  - But the two pricings are in different units. As a share of each total, word is 4.50% (ruint) and 4.53% (Montgomery), so word weighs about the same under both.
- **Uncited web claims in the reply:** information only.

## Model, after both sets were sealed (reference only; not a prediction; `wolfram/2026-10-27_i032_cost.wl`, f12ae23)

- New reference (2′a) against today's reference: official / ruint / Montgomery **0.9754 / 0.9843 / 0.9842**.
- 2′b against 2′a (root alone against the new reference): **1.0137 / 0.8877 / 0.8838**.

## DeepSeek, second round (Oct 26, ~20:14), sealed

Filed before any 2′a or 2′b timing run. 2′a acceptance had run (`evolve/goff_accept.py`; counts by type and identity only; no priced totals printed or compared).

### Its "Recorded" section, D-8, D-9 and the D-9 falsifier (verbatim)

*Filed late (Oct 26, after d4a0da6), received before any timed run: DeepSeek's second round, ~20:14 Oct 26 PT. Copied verbatim from the user's brief.*

<!-- verbatim begin -->

## 0. Recorded

- **D-1–D-7 and the three falsifiers are sealed** and will be scored as written. No revision.
- **D-5 correction accepted**: 0.919 was today's root mode including the per-polynomial pass, not "2'b with the pass." Dividing by 2'a's saving double-counts because 2'b also receives that saving. My range still covers the reviewer's ~−12%. Annotation only.
- **D-3 correction accepted**: the ~4% wasted pass exists only in root mode; 2'a's saving on the full-pass reference is the removed per-polynomial start-offset recomputation, a different quantity. My D-3 range is unchanged and is now read as the offset-recomputation saving on the full-pass reference. Annotation only.
- **D-2 guard**: the statements "word ops are 4.5% of ruint" and "Montgomery's word price exceeds ruint's" were **not** in the update. I record them as **missing parameters**, not as given values. D-2's range stands as a model-anchored range, but its reasoning should not be read as using those numbers as inputs.
- **Web references**: the earlier reply named mechanisms without links. The SIQS root-confirm and 256-bit Montgomery remarks are recorded as **information only**, not as card parameters.
- Wolfram cost model recorded as post-sealing, model not verdict; its forecast 2'a 0.9754 / 0.9843 / 0.9842 and 2'b 1.0137 / 0.8877 / 0.8838 are noted. No D-score is changed.

## 1. Sealed predictions D-8 and D-9

Registered now, before the timing run. 96 bits, 640 map numbers, re-sieve off. **Base for D-8 is 2'a, not today's reference.** Ratios are new/old; below 1 = cheaper.

| ID | Definition / pricing / base | Sealed range (central) | Falsifier |
|---|---|---|---|
| **D-8** | 2'b + pp3 at +0 bits vs **2'a**: official / ruint / Montgomery ratios, and wall-clock change | official **0.995–1.010** (1.003); ruint **0.975–0.990** (0.983); Montgomery **0.970–0.988** (0.979); wall **−6% to −12%** (−9%) | official **>1.030** or **<0.975**; ruint **>1.005** or **<0.955**; Montgomery **>1.000** or **<0.950**; wall **>+2%** or **<−18%** |
| **D-9** | Is 2'b + pp3 better than 2'a under **all three pricings at once**? yes/no, with confidence | **No** (confidence **65%**) | Falsified if 2'b + pp3 is **≤1.000 under all three pricings simultaneously** |

### Computed anchors and reasoning

**D-8 official.** 2'b vs 2'a is model **1.0137** official. Adding pp3 at +0 bits adds sieve hits and admits more partials but removes no confirm work by itself. In the earlier root + pp3 cell, root + pp3 at +0 was the only cell better under all three pricings, **robust ratio 0.982** against **today's reference**. Against **2'a**, the pp3 contribution should not repeat the full 0.982 because 2'a already carries the offset saving. A rough decomposition: 2'b official ≈ 1.0137, pp3 at +0 on top ≈ 1 − 0.010 to 1 − 0.015, giving **0.998–1.004**. I widen to 0.995–1.010.

**D-8 ruint.** 2'b vs 2'a is model **0.8877**. pp3 at +0 adds sieve word ops but removes candidates and partials; against today's reference the combined cell was 0.982. On top of 2'a, the incremental pp3 effect is smaller. A reasonable range is 2'b's 0.8877 multiplied by a factor near 1.08–1.11, giving **0.959–0.978**? That is wider than my central. I choose central **0.983**, range **0.975–0.990**, because the pp3 candidate and partial savings under ruint are partly offset by the extra sieve word ops, and the measured root-alone ruint ratio was 0.9051 with the pass still present.

**D-8 Montgomery.** The mechanism is the same; the range is widened slightly because the Montgomery total is not on the parameter sheet and the root-test price sensitivity is larger there. Central **0.979**.

**D-8 wall.** Root + pp3 at best shift (+2) was **−8.9% [95%: −12.9, −4.9]** against today's reference. Against 2'a, the saving is smaller because 2'a already removes the wasted pass. I centre **−9%**, range **−6% to −12%**.

**D-9.** The model says 2'b is **+1.37% official**, **0.8877 ruint**, **0.8838 Montgomery**. Adding pp3 at +0 bits can flip official slightly below or above 1.0, but it is unlikely to be **≤1.000 under all three at once** because the official ratio is already above 1 and pp3's incremental official effect is small. Hence **No**, confidence **65%**. The confidence is not high because the pp3 incremental effect on official pricing is not measured and the negative-x share is assumed 0.5, not measured.

## 2. Falsifier for D-9

D-9 is falsified if **2'b + pp3 at +0 bits is ≤1.000 under official, ruint and Montgomery simultaneously**. That would mean pp3's incremental saving is large enough to flip the official ratio below 1 and to keep the other two below 1, making the combined option better than 2'a under every pricing at once.

No other sealed prediction is revised.

## 3. Information-only references (not card parameters)

- SIQS smoothness checking and the use of sieve roots for candidate confirmation are standard; a Rust SIQS implementation describes confirming a candidate by checking whether the prime divides `Q(x)` exactly when the index lands on one of its roots, "turn[ing] thousands of big-integer divisions per candidate into a handful". The card's root-confirm mode is an instance of that idea.
- Log-sieving and report thresholds are standard: sieve cells accumulate log p, and candidates are those exceeding the report threshold, after which trial division or root comparison retrieves factors. The card's threshold and partial-capture behaviour should be read in that framework.
- Montgomery multiplication benchmarks show that per-operation cost depends strongly on implementation and word size; 256-bit Montgomery modular multiplication has been measured at roughly 199–216 cycles in some libraries, with 358-bit at 268–344 cycles, ratios ~1.35–1.6. This is **information only** and is not used as a card price.

No sealed prediction is revised. D-8 and D-9 are registered above.

<!-- verbatim end -->

- Its section 3 references: **information only** (no links given).

### The reviewer's annotations (DeepSeek's ranges unchanged)

- **D-8/D-9 rest on a misreading of the robust ratio.** The robust ratio is the worst of the three pricings, so root + pp 3 at +0 bits (robust 0.982 against today's reference) was ≤ 0.982 under official too. Against root alone (official 1.038), pp 3 saved about 5% official, not the 1–1.5% DeepSeek assumed.
- **D-8's ruint reasoning is internally inconsistent:** it computes 0.959–0.978, then seals 0.975–0.990.

## DeepSeek, third round (received 20:54 Oct 26 PT)

- **D-10: information only, because the model was committed first.** The exact-count 2′b cost model (18efd55) was committed at 20:52:39 PT, before this reply arrived at 20:54.

### Its reply (verbatim)

*(placeholder: the brief said the reply follows it, but no text followed; to be appended verbatim when the user pastes it)*

### Its acceptances (recorded as given; all ranges unchanged)

- **D-2's "missing parameters" note is withdrawn:** the reviewer's annotation was the error. The 4.5% is sourced to reviews/card_params.md:33, as annotated above.
- **Accepted as annotations:** the reviewer's D-8/D-9 robust-ratio reading and the D-8 ruint inconsistency.

### The reviewer's annotation (D-10's range unchanged)

- **D-10's anchor is a unit slip, per polynomial against per A.** It charges the per-A index per root per **polynomial** (263.8 × 156.04 = 41,163 per number). `ka` is built per A (~264 roots × ~20 A's, about 5,300 per number).
  - The per-A build and the per-candidate root reads were already in f12ae23's model, so they are not additional charges.
  - The same "new charges" reasoning appears in Grok's G-6.
  - *Claude Code's note, for the record:* the cost note (18efd55) charges 2 per sieved prime per A, i.e. 2 × 2,638.08 = 5,276.2 per number, not per root.

## The reviewer's (verbatim; sealed Oct 26, after DeepSeek's second round)

Same cell and base as D-8: 2′b + pp 3 at +0 bits against 2′a, 96 bits, 640 map numbers, re-sieve off, 8 random-order replicates.

      R2-9  official 0.95 to 0.99; ruint 0.84 to 0.90; Montgomery 0.84 to 0.90;
            wall -8% to -16%.
      R2-10 better than 2'a under all three pricings at once: YES, 75%.
            Falsifier: official > 1.000.

**Conditions of these filings:** the user's desktop Mathematica was open (WolframNB and WolframKernel processes running). No timed run was in progress; 2′a acceptance and parity (no timing) were running.

## Grok

Sealed predictions (Grok, received 20:54 Oct 26 PT, labelled ~21:00 by Grok).

- **G-1..G-5: sealed.** The run had not happened when they were received.
- **G-6: information only, because the model was committed first.** The exact-count 2′b cost model (18efd55) was committed at 20:52:39 PT, before 20:54.
- **Its "Optional" answer:** information only.
- *(Until 20:54 this section read "not received", as of the runner's commit, 3f4034e.)*

### Grok's reply (verbatim)

*Filed late (Oct 26, after d4a0da6), received before any timed run: 20:54 Oct 26 PT. Copied verbatim from the user's brief.*

<!-- verbatim begin -->

**Sealed predictions (Grok, 26 Oct 2026 ~21:00 PT)**  
Using only the numbers supplied. Missing quantities (absolute wall-clock per number, word-op share, exact per-op prices, exact-count model outputs) are marked as such rather than assumed.

### G-1 — 2'a vs today's reference
- Official: 0.970–0.981 (model 0.9754)
- ruint: 0.980–0.988 (model 0.9843)
- Montgomery: 0.980–0.988 (model 0.9842)
- Wall-clock: −2.5 % to −5.5 %  

(The ~0.5 µs/poly waste was stated to be ~4 % of wall and ~2.8 official points; 2'a removes that waste from the reference path. Absolute wall time per number is not given, so the percentage range is bounded by the stated 4 % figure.)

### G-2 — 2'b vs 2'a
- Official: 1.008–1.020 (model 1.0137)
- ruint: 0.875–0.900 (model 0.8877)
- Montgomery: 0.870–0.897 (model 0.8838)
- Wall-clock: −6 % to −12 %
- Sieve-region wall: −1 % to +4 %  

(Prior root-alone run showed +14.5 % sieve because of the second pass over ~264 roots. That pass is now removed and the kept offsets are read in place; the residual sieve-region change should therefore be far smaller. Absolute µs figures beyond the stated ~0.5 µs are not given.)

### G-3 — 2'b + pp3 (+0 bits) vs 2'a
- Official: 0.990–1.005
- ruint: 0.860–0.890
- Montgomery: 0.855–0.885
- Wall-clock: −8 % to −15 %  

(Previous root+pp3 at +0 already reached robust 0.982 vs the old reference; 2'a has already removed the waste, so the further gain is smaller than that earlier comparison but still material on the two fast pricings.)

### G-4 — Is 2'b + pp3 better than 2'a under all three pricings at once?
**No** (confidence ~65 %).  
Falsifier: official ratio ≤ 0.995 with both ruint and Montgomery also ≤ 0.95 and the paired-bootstrap intervals excluding 1.0 on all three.

(The model already has official slightly above 1 for 2'b vs 2'a; adding pp3 is not guaranteed to pull official below 1 while the two fast pricings stay well below.)

### G-5 — 95 % interval width on wall-clock ratios (points)
1.5–3.5 percentage points on the ratios that appear in G-1–G-3.  

(Prior 8-replicate intervals were roughly 4–8 points wide; with the same design and the dominant waste term removed, tighter intervals are expected, but the exact residual variance is not given.)

### G-6 — Exact-count cost model, 2'b vs 2'a official ratio
**Above** the estimated 1.0137 (range 1.015–1.030).  

(The new model adds the per-A index build and per-candidate root reads that the earlier Wolfram model treated more approximately; those are positive official costs. The model has not yet been committed, so this remains a sealed prediction only if it arrives first.)

---

**Optional:** Prefer **I-038** (external wall-clock baseline) first.  
It needs no kernel or privilege changes and immediately places the current SIQS card against a mature hand-tuned implementation on the identical 640 numbers and machine; I-039's RAPL counters are root-only on this system and therefore blocked until the author decides to enable them.

<!-- verbatim end -->

### The reviewer's annotations (Grok's ranges unchanged)

- **G-1:** the wall reasoning makes the same slip as DeepSeek's D-3. The ~0.5 µs/polynomial pass exists only in root mode; 2′a's saving on the reference is the sieve loop's start-offset recomputation.
- **G-4:** scored as asked, "better under all three": official, ruint and Montgomery each ≤ 1.000. Grok's stated falsifier (ruint and Montgomery ≤ 0.95, with intervals excluding 1) is stricter than the question; it is recorded but not used to score.
- **G-5:** a full interval width (Grok reads the last run as "4–8 points wide"), whereas R2-8 and D-7 are half-widths (±). Each is scored in its own form, and both forms are stated.
- **G-6:** the reasoning misses that the per-A build was already charged in f12ae23 (531.8 word per A for 2′). The direction of the exact-count shift is open.

## State before the run (recorded Oct 26, after 3f4034e)

- **Sealed sets present:**
  - the reviewer's R2-1..R2-10 (verbatim);
  - DeepSeek's D-1..D-7 and three falsifiers (as transcribed in the user's brief).
- **Not present as text:**
  - DeepSeek's full first reply;
  - DeepSeek's second reply with D-8, D-9 and the D-9 falsifier. Only the reviewer's annotations quote their ranges in part ("D-8 … seals 0.975–0.990" for ruint).
  - Unless the text is pasted before the run, D-8 and D-9 cannot be scored as written.
- **2′b is not built.** The code's goff + root still runs root confirm's per-polynomial pass, reading the kept offsets instead of recomputing them. The design's 2′b removes that pass by reading the offsets in place (per-A `ka`). The runner's "2′b" cells (`goff=1, confirm="root"`) measure whatever is built at the run's commit.
- **Frequency cap:** none (scaling_max_freq 5,000 MHz, no_turbo 0, max_perf_pct 100); governor powersave.
- **Desktop Mathematica:** running (WolframNB front end and 3 WolframKernel processes). Not changed.

### Update to "State before the run" (after the texts above were filed)

- **DeepSeek's D-8, D-9 and the D-9 falsifier are now on file verbatim** (second round, received ~20:14 Oct 26 PT; filed late), so they can be scored as written. The earlier line saying their text was absent is superseded.
- **Grok's G-1..G-6 and "Optional" are on file verbatim** (received 20:54 Oct 26 PT; filed late).
- **Still placeholders:** DeepSeek's full first reply (D-1..D-7 are on file as transcribed) and DeepSeek's third reply (D-10, information only).
