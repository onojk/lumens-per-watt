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

*(placeholder: the text was not included in the brief that asked for it; to be appended verbatim when the user pastes it)*

- Its section 3 references: **information only** (no links given).

### The reviewer's annotations (DeepSeek's ranges unchanged)

- **D-8/D-9 rest on a misreading of the robust ratio.** The robust ratio is the worst of the three pricings, so root + pp 3 at +0 bits (robust 0.982 against today's reference) was ≤ 0.982 under official too. Against root alone (official 1.038), pp 3 saved about 5% official, not the 1–1.5% DeepSeek assumed.
- **D-8's ruint reasoning is internally inconsistent:** it computes 0.959–0.978, then seals 0.975–0.990.

## The reviewer's (verbatim; sealed Oct 26, after DeepSeek's second round)

Same cell and base as D-8: 2′b + pp 3 at +0 bits against 2′a, 96 bits, 640 map numbers, re-sieve off, 8 random-order replicates.

      R2-9  official 0.95 to 0.99; ruint 0.84 to 0.90; Montgomery 0.84 to 0.90;
            wall -8% to -16%.
      R2-10 better than 2'a under all three pricings at once: YES, 75%.
            Falsifier: official > 1.000.

**Conditions of these filings:** the user's desktop Mathematica was open (WolframNB and WolframKernel processes running). No timed run was in progress; 2′a acceptance and parity (no timing) were running.
