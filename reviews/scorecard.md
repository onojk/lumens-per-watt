# Reviewer scorecard (I-002): the reviewer, DeepSeek and Grok

**Last updated:** 2026-10-27 (overnight stage 3), NOTES at bcc1aed. Maintained by Claude Code. Documentation only: nothing here rescores anything; every count is the score as recorded in NOTES.

## In plain English

- **Tallied:** 566 scored rows. The reviewer (Claude chat, with the user's own sealed predictions) has 333, DeepSeek 161, Grok 72.
  - **The reviewer: 188 held, 135 missed, 3 falsified, 7 information only.**
  - **DeepSeek: 56 held, 51 missed, 33 falsified, 15 information only,** plus 6 rows where only its falsifier was scored.
  - **Grok: 24 held, 37 missed, 7 falsified, 4 information only.**
- **The reviewer's totals flatter it,** because many of its rows score Wolfram model runs rather than card runs: 63 of its 164 rows in NOTES lines 6390–9184, and most of its rows in 4300–6390.
  - **On card runs alone, lines 6390–9184:** the reviewer 62 held / 37 missed; DeepSeek 36 held / 18 missed / 20 falsified; Grok 13 held / 9 missed / 2 falsified.
  - The reviewer is the most often right on card runs, roughly 6 in 10. DeepSeek is right about half the time but falsifies often, because it states hard falsifiers. Grok is right about half the time on card runs and less often overall.
- **Where each one goes wrong:**
  - **The reviewer:** framing and hand calculation, more than physics. Examples:
    - the "241 µs / 7-point gap", which took official's ratio as the priced expectation;
    - the floor/ceiling slip in the free-2 count;
    - intervals sealed for an uncapped clock (R2-8);
    - "+1 and +2 within 1 point";
    - per-polynomial versus per-number units (W4a, H-2);
    - tests that did not isolate what they meant to (the L test).
  - **DeepSeek:**
    - invented or assumed parameters (0.30 µs per copy; F and B values it was not given);
    - wrong op prices (0.0258 for confirm; 0.114 for setup_small);
    - robust-ratio misreadings (D-8 / D-9);
    - unit slips (D-10);
    - carrying factors across runs or pricings (D-15: ruint's factor applied to Montgomery, a cross-run wall factor).
  - **Grok:**
    - answers that contradict its own tables ("best robust +0" against falling official centres);
    - reasoning in which an unpriced cost moves a priced ratio;
    - narrower falsifiers than its ranges (G-8).
  - **Shared:** the outside forecasters repeatedly borrow the reviewer's anchors (the ~40 µs quick check behind R2-20, D-17 and G-10), so their agreement is not independent.
- **Under the corrected meter** (the free-2 fix, 6031239), the re-scored priced items move like this:
  - the reviewer: 14 held / 6 missed → 3 / 16 / 1 falsified;
  - DeepSeek: 7 / 2 / 5 → 1 / 10 / 3;
  - Grok: 10 / 4 / 0 → 2 / 12 / 0.

  The forecasts that expected little official saving from pp 3 (D-9, G-4, D-8 official) gain. The ones centred on the uncorrected saving lose. Original scores stand; these are second scores.

**How this was built, and its limits:**
- A delegated tally. Lines 6390–9184 and predictions/*.md were read line by line. Lines 700–4300 and 4300–6390 were tallied by sub-agents and spot-checked (~20 rows).
- Claude Code then spot-checked R2-10, R2-15, R2-20, D-13, D-17, G-10, H2-2, RC2-4 and the second-score moves against NOTES; all matched.
- Unit of counting: one verdict cell in NOTES. Sub-clauses scored separately count separately, so totals depend on how a table was split.
- Some early rows' definitions (C1..C7, T1..T5, W2a/b) are not in NOTES; they are counted with their recorded verdicts and marked.
- Claude Code's own predictions are excluded. The ambiguities resolved and the unclear items are listed below.

---


Source: /home/onojk123/lumens-per-watt/NOTES.md (9,184 lines, HEAD bcc1aed), cross-checked against predictions/*.md. The repo was only read; nothing in it was edited.

**Forecasters:**
- **Reviewer:** "the reviewer's", "the user's", "Claude chat's". IDs include R-X3, R-L, R-F, R-G, S9, G-1..G-5 of stage G, H-1..18, H2-1..4, I-029a/b, R-1..4, RC2-1..4, R2-1..20, and the Wolfram-run series C, T, W, V, X, Y, Z, R-E, W-1..6.
- **DeepSeek:** D-.., the DeepSeek sides of R-L, R-F, R-G, X3, S9, M3, H, I-029 and R-1..4, and the DeepSeek shift table.
- **Grok:** G-.. from the i032 round on, the earlier G-a/G-rep/GP etc., and the Grok shift table and best-shift answers.
- **Excluded:** Claude Code's own predictions ("mine"). They are listed only by count in the notes.

**Unit of counting:**
- Each row is one verdict cell in NOTES. Where NOTES gives a row several verdicts ("held / held", "missed / held", "held at 84, missed at 96"), each verdict is its own row, marked "sub-clause".
- Where one verdict covers several clauses ("held (all three)", "held (all four)"), it counts once. If those clauses span priced and wall, the category is "mixed (priced+wall)".

**Result mapping:**
- "missed, falsified", "missed (falsified)", "FALSIFIED", "refuted" and a triggered falsifier row count as **falsified**.
- "failed" and "wrong" count as **missed**.
- "information only", "unscored", "VOID", "pending" and "not sealed" count as **info only**.
- DeepSeek's S9-1..S9-5 were recorded as agreement with the reviewer's ranges, so only their falsifiers were scored. Those rows are **not falsified (falsifier-only)**.

Totals are original scores as recorded. The second scores under the corrected meter are in section 2 only.

## 1. Totals

| forecaster / category | held | missed | falsified | info only | not falsified (falsifier-only) | total |
|---|---|---|---|---|---|---|
| Reviewer / priced | 15 | 15 | 1 | 1 | 0 | 32 |
| Reviewer / wall | 28 | 20 | 0 | 1 | 0 | 49 |
| Reviewer / mixed (priced+wall) | 3 | 0 | 0 | 0 | 0 | 3 |
| Reviewer / categorical | 30 | 23 | 1 | 0 | 0 | 54 |
| Reviewer / interval width | 0 | 2 | 0 | 0 | 0 | 2 |
| Reviewer / other | 101 | 67 | 1 | 5 | 0 | 174 |
| Reviewer / other (definition not in NOTES) | 11 | 8 | 0 | 0 | 0 | 19 |
| DeepSeek / priced | 11 | 14 | 7 | 3 | 0 | 35 |
| DeepSeek / wall | 11 | 11 | 8 | 2 | 0 | 32 |
| DeepSeek / mixed (priced+wall) | 3 | 0 | 0 | 0 | 0 | 3 |
| DeepSeek / categorical | 8 | 8 | 8 | 1 | 0 | 25 |
| DeepSeek / interval width | 0 | 1 | 0 | 0 | 0 | 1 |
| DeepSeek / other | 23 | 17 | 10 | 9 | 6 | 65 |
| Grok / priced | 6 | 6 | 4 | 2 | 0 | 18 |
| Grok / wall | 4 | 4 | 1 | 1 | 0 | 10 |
| Grok / mixed (priced+wall) | 3 | 0 | 0 | 0 | 0 | 3 |
| Grok / categorical | 8 | 10 | 1 | 1 | 0 | 20 |
| Grok / interval width | 0 | 1 | 0 | 0 | 0 | 1 |
| Grok / other | 3 | 16 | 1 | 0 | 0 | 20 |

**Per forecaster, all categories:**

| forecaster | held | missed | falsified | info only | not falsified (falsifier-only) | total |
|---|---|---|---|---|---|---|
| Reviewer | 188 | 135 | 3 | 7 | 0 | 333 |
| DeepSeek | 56 | 51 | 33 | 15 | 6 | 161 |
| Grok | 24 | 37 | 7 | 4 | 0 | 72 |

**Per forecaster and NOTES range** (700-4300 and 4300-6390 were tallied by sub-agents and spot-checked; 6390-9184 was done line by line):

| forecaster / range | held | missed | falsified | info only | not falsified (falsifier-only) | total |
|---|---|---|---|---|---|---|
| Reviewer / 700-4300 | 4 | 15 | 1 | 3 | 0 | 23 |
| Reviewer / 4300-6390 | 78 | 64 | 2 | 2 | 0 | 146 |
| Reviewer / 6390-9184 | 106 | 56 | 0 | 2 | 0 | 164 |
| DeepSeek / 700-4300 | 4 | 19 | 0 | 1 | 0 | 24 |
| DeepSeek / 4300-6390 | 16 | 12 | 13 | 1 | 0 | 42 |
| DeepSeek / 6390-9184 | 36 | 20 | 20 | 13 | 6 | 95 |
| Grok / 700-4300 | 5 | 9 | 3 | 1 | 0 | 18 |
| Grok / 4300-6390 | 6 | 19 | 2 | 0 | 0 | 27 |
| Grok / 6390-9184 | 13 | 9 | 2 | 3 | 0 | 27 |

**Lines 6390-9184 only, card-measured against model-scored (Wolfram runs scored by the user):**

| forecaster / basis | held | missed | falsified | info only | not falsified (falsifier-only) | total |
|---|---|---|---|---|---|---|
| Reviewer / card | 62 | 37 | 0 | 2 | 0 | 101 |
| Reviewer / model | 44 | 19 | 0 | 0 | 0 | 63 |
| DeepSeek / card | 36 | 18 | 20 | 13 | 6 | 93 |
| DeepSeek / model | 0 | 2 | 0 | 0 | 0 | 2 |
| Grok / card | 13 | 9 | 2 | 3 | 0 | 27 |

**Reading notes for the totals:**
- **The reviewer's count is inflated by model-scored runs.** A large share of its rows score Wolfram or Mathematica model runs, not card runs: 63 of its 164 rows in 6390-9184, and, by part 2's account, most of its 146 rows in 4300-6390. These are the C, T, W, V, X, Y and Z series, the I-023 to I-028 forecasts, and Claude chat's pre-run expectations. Many of those ranges were never written into NOTES before the run. In 6390-9184 the card-only figures are: reviewer 62 held / 37 missed (101 rows), DeepSeek 36 / 18 / 20 falsified (93), Grok 13 / 9 / 2 (27).
- **Falsification counts reflect the forecasters' practice, not just accuracy.** DeepSeek states falsifiers on almost every item, so its misses often become falsified. The reviewer rarely does, and Grok sometimes.
- **Post hoc items are included and flagged in the rows.** They are DeepSeek D-a1..a3, D-sweep, U3, V3 and G4 (5771); Grok G-a, G-slack (x3) and G-pinv; W2 and C1 for both Grok and Claude chat (4929, 4971); and the reviewer's U3, V3 and 7.5-9.0 (5772). Without them: DeepSeek 3 held / 16 missed in 700-4300, and Grok 4 / 6 / 2 there (per part 1).
- **Grok's G-rep2 (3354) is one row.** NOTES scores it per cell, "0 of 24 cells held". Counted per cell, Grok's priced misses rise by 23.

## 2. Second scores under the corrected meter (NOTES 9115-9184; extra table, does not replace the originals)

The free-2 meter correction (6031239) was applied after the 2b-sizes run. NOTES 9150-9172 re-scores the affected priced clauses beside the originals, at sub-clause level as the table splits them. Here "falsified" includes R2-10, which reads "missed; falsifier triggered".

| forecaster | rows re-scored | original: held / missed / falsified | second: held / missed / falsified |
|---|---|---|---|
| Reviewer: R2-9 o/r/m, R2-10, R2-12 +0/+1 o,r,m/+2 o,r,m, R2-14, R2-15 o/r/m, R2-17 (4 clauses + conjunction) | 20 | 14 / 6 / 0 | 3 / 16 / 1 |
| DeepSeek: D-8 o/r/m, D-9, the shift table's 9 priced ranges, D-13 | 14 | 7 / 2 / 5 | 1 / 10 / 3 |
| Grok: G-3 o/r/m, G-4, the shift table's 9 priced ranges, best robust +0 | 14 | 10 / 4 / 0 | 2 / 12 / 0 |

**Row-level moves** (NOTES lines):
- **Reviewer:**
  - R2-9 (9152): H,H,H to M,M,H.
  - R2-10 (9153): H to missed, falsifier triggered.
  - R2-12 +0 (9160): H to M ("missed as written").
  - R2-12 +1 (9161): H x3 to M x3.
  - R2-12 +2 (9162): M,H,H to M x3.
  - R2-14 (9163): H to H.
  - R2-15 (9168): H,H,M to M x3.
  - R2-17 (9169-9172): official best 72 M to M; official best 84 M to **H**; +1 better 72/84 M/H to M/M; the conjunction M to M.
- **DeepSeek:**
  - D-8 official (9154): F to M (falsifier no longer triggered).
  - D-8 ruint and Montgomery (9155-9156): F to F.
  - D-9 (9157): F to **H**.
  - The shift table (9164): 7 H and 2 M to 9 M.
  - D-13 (9165): F to F.
- **Grok:**
  - G-3 (9158): M,H,H to M x3.
  - G-4 (9159): M to **H**.
  - The shift table (9166): 7 H and 2 M to 9 M.
  - Best robust +0 (9167): H to H.

**What moved and why:**
- The correction helps the outside forecasts that expected little official saving from pp 3 (D-8 official, D-9, G-4).
- It sinks the ranges centred on the uncorrected pp 3 saving: the reviewer's R2-9, R2-10, R2-12 and R2-15, and both outside shift tables (9183).
- Not re-scored: stage H (its code had no free-2 write), root-confirm-2 (no priced items), and every wall clause.

## 3. Recurring error types per forecaster

### Lines 6390-9184 and the predictions/ files (checked directly)

**Reviewer (the user / Claude chat), NOTES 6390-9184 and the predictions/ files**
- **Unit errors, per polynomial vs per number:** W4a compared per-polynomial simulation candidates with the card's per-number +103% (NOTES 7223). The same unit issue was flagged in the sealed H-2 (7225).
- **Official ratio used as the priced expectation:** the "241 µs / 7-point gap" given to DeepSeek and Grok took official's −5.1% as the expected price change for the whole cell. Official prices a sieve update like a root test. Against ruint the gap is about 4 points, 109 µs (NOTES 8538; Claude Code's base note at predictions/pp3-gap-and-shift.md:76; DeepSeek's acceptance at :163). D-11, R2-11 and Grok's phase pick all inherited the anchor and were made information only (8536-8537, 8656).
- **Floor/ceiling slip in the free-2 count:** the brief said floor((width − par)/2); the code writes ⌈(width − par)/2⌉. The user ruled "the reviewer's 'floor' was a slip" (9016-9020).
- **Intervals sealed without the clock cap:** R2-8's ±3 to ±6 was sealed for an uncapped machine. The 2.4 GHz cap narrowed the intervals to ±0.6 to ±2.9, and R2-8 missed (8434; D-7 shares the cause, 8448). RC2-4's interval-width miss came from the noisy reference cell (8129, 8134).
- **"+1 and +2 within 1 point" miss:** R2-13. The two were 2.7 points apart and their intervals do not overlap (8593). Official direction right, size wrong: the reviewer had official rising with the shift (R2-14) but missed the size at +2 (R2-12 +2 official, 8590; 8623).
- **Specification errors:**
  - The step-7 test (lc only) did not isolate L, because lc also sets the threshold. R-L1 to R-L4 were annotated "test did not isolate L (reviewer's spec)" (6557-6559).
  - Stage G ran before DeepSeek's predictions were filed, so DeepSeek's G numbers are information only (7173).
  - R-5 was asked about candidates that root confirm cannot change (7999).
- **Readings and hand calculations that left out a cost term:**
  - The "raise F" reading omitted confirm; R-F2 and R-F3 missed (6566).
  - V5's hand calculation ignored ledger growth (7331); so did the −2 to −3 best shift (7351).
  - The "~4.6 bits" matched-shift figure was wrong (7382).
  - "H(ii) gains almost nothing" was wrong (7335).
  - "A single cap is not the main cause" and "the card loses ~10-17% of fulls" were both wrong (6985-6986).
  - C5 refuted the "L explains the ~0.6 combined share" idea (6643).
- **Parameters relayed wrongly:** the B 1,841 / 1,151 and F ~122 / ~82 relayed to DeepSeek were Claude Code's rough estimates, not the card's (measured B 1,752 / 1,093, F 138 / 93). They are listed under the reviewer's own errors (6565; Claude Code's note at 6508).
- **The reviewer's annotation was itself the error:** the D-2 "missing parameters" note was withdrawn, since the 4.5% was sourced to reviews/card_params.md:33 (predictions/i032-2prime.md:75, :133).
- **Shared anchors (non-independence):** R2-20, D-17 and G-10 all rest on the ~40 µs quick check (predictions/2b-sizes.md:91, :140). R2-11, D-11 and Grok's phase pick all point at the ledger (predictions/pp3-gap-and-shift.md:73, :123).
- **Ranges centred on the uncorrected meter:** under the corrected meter R2-9, R2-10, R2-12 and R2-15 miss (9183).

**DeepSeek, NOTES 6390-9184 and predictions/**
- **Invented or assumed parameters:**
  - 0.30 µs per kept-relation copy (D-14), flagged by DeepSeek itself as a missing parameter (predictions/pp3-gap-and-shift.md:179, :192).
  - A confirm-test price of 0.0258 ruint (a word op) where the card's confirm_td is 0.114, and the wall sieve share used as the priced share (round 47, NOTES 7456).
  - It cited the card's F as ~96 / 151 when the runs used 256 / 400; outside this range at 6224, kept here for context.
- **Factors carried across runs or pricings:**
  - D-15 applied ruint's pp 3 factor to Montgomery and used a cross-run wall factor (−11.2% from run A against −9.4% from the shift run) (predictions/2b-sizes.md:89-90).
  - D-12's anchor subtracted 3 points measured against the old reference and applied them against 2′a, mixing bases (predictions/pp3-gap-and-shift.md:74).
  - It mixed the card's F and full rate with the model's P (round 45, NOTES 7354).
- **Robust-ratio misreading:** D-8 and D-9 assumed pp 3 saves 1-1.5% official. The worst-of-three robust 0.982 meant official was ≤ 0.982 too, and pp 3 actually saved ~5% (predictions/i032-2prime.md:120). D-8's ruint reasoning computes 0.959-0.978 and then seals 0.975-0.990 (:121). The outcome: D-8 o/r/m and D-9 falsified (8450-8454; common failure 8480).
- **Unit slip, per polynomial vs per A:** D-10 charged the per-A index per root per polynomial (predictions/i032-2prime.md:138).
- **Double counting and conflation:** D-5 double counts 2′a's saving; D-3 conflates root mode's second pass with 2′a's start-offset saving (predictions/i032-2prime.md:46-47).
- **Algebra and slot errors:**
  - e_C computed with the all-usable Fulls (NOTES 6517).
  - ε_a read as an acceptance rate (6523).
  - The total confirm elasticity put in the (1 + ε_n) slot (6622).
  - K + c r held at 12.24 for a cheaper confirm (7267), and the same slip repeated in round 45 (7361).
  - The −4.5-bit estimate ignored the ledger term (7351).
  - The R-L2 ln(L/B) reasoning was wrong (6507).
  - The e_F and e_M directions were wrong (6486).
- **2-adic slips:** it assigned the free 2 to the even-y class instead of the odd-y class (7531), wrote P(v2 ≥ 3) = 1/4 where 1/4 is P(v2 ≥ 4) (7539), and gave a wrong quality mechanism (7532).
- **Attribution and record slips:** it claimed RT-1 was filed in round 49, which the record does not support (7737). D-14 called the copies "uncharged" when they are charged but under-priced (predictions/pp3-gap-and-shift.md:191).
- **"Best case" mis-paired extremes** in its consistency note on the user's G-3 / G-5 (7141).
- **Shared anchors:** D-17 uses the reviewer's ~40 µs anchor (predictions/2b-sizes.md:91). D-11's phase choice matches the reviewer's hypothesis (predictions/pp3-gap-and-shift.md:73).
- **Falsifiers fired on wall-clock sizes:** R-1 and R-4 (8039, 8042); H-13, H-16 and H-18 (7699-7704); D-14 size (8651).

**Grok, NOTES 6390-9184 and predictions/**
- **Robust-ratio misreading:** "best robust ratio +0" contradicts its own table, whose official centres fall with the shift (+0 ~0.963, +1 ~0.959, +2 ~0.957) (predictions/pp3-gap-and-shift.md:125). The item scored held, but "its stated reason, unpriced hash load raising official, is not the mechanism" (NOTES 8621). Its reasoning let an unpriced cost change a priced ratio, which cannot happen, and had the threshold direction reversed (predictions/pp3-gap-and-shift.md:126).
- **The same slips as DeepSeek:**
  - G-1's wall reasoning repeats D-3's conflation (predictions/i032-2prime.md:222).
  - G-6 missed that the per-A build was already charged, the same "new charges" reasoning as D-10 (:225, :140).
- **Width and falsifier form mismatches:**
  - G-5 is a full width where R2-8 and D-7 are half-widths (:224; NOTES 8469).
  - G-4's falsifier is stricter than its question (:223).
  - G-7 needs two conditions at once (predictions/pp3-gap-and-shift.md:224); G-8's falsifier is an OR, narrower than its ranges (predictions/2b-sizes.md:138).
  - Its "full widths" note applies to no item (predictions/pp3-gap-and-shift.md:127).
- **Official direction:** its shift table put official flat or falling; official rose at +1 and +2 (NOTES 8623). G-3 official and G-4 assumed a small pp 3 official effect (8480).
- **Non-independence:** G-7 has the same answer and assumption as D-14 (predictions/pp3-gap-and-shift.md:223). Its phase pick matches D-11 and R2-11 (:123). G-10 shares the ~40 µs anchor (predictions/2b-sizes.md:140).
- **Over-generalised mechanism:** "sieve updates are over-charged" holds only under official; under ruint the sieve was under-charged by +33 µs (NOTES 8816).

### Lines 700-4300 (from the part-1 tally)


**DeepSeek**
- Wrong price for the op type: D-gc assumed small-modulus price 0.114 ruint where the card charges setup_small 0.307 (3774); the same error repeated in its later traced statement (3942-3943).
- Wrong count base / wrong denominator: D-ledger assumed one lookup per partial filed (the check runs per relation offered, ~70-150) and divided by a qs ruint cost of ~10^5 when measured is ~29,000 at 84 bits, ranges ~3x low (4060-4061, 4074-4077, 4083).
- Overestimated counts and double pricing: D-pinv overestimated A's per run (10-100 vs 4.2-27.2) and priced the same Euclid run at two prices (3800, 3880).
- Direction reversals: D-cc wording ("sim under-counts") reversed, as was its "below 0.90 = over-predicting" clause (3882; acknowledged 3942); PD_M predicted to rise where a costlier Track M lowers it (3398).
- Parameters imported from a different regime: A-pool constraints (primes > 2000, s > 3) from much larger factorizations, not adopted (1969).
- Incomplete argument scored as given: D-dup covers only within-A neighbours, not cross-A sharing (4059).
- Magnitude overreach on the gene round: D-b1, D-b2, D-b3, D-c1, D-k all missed (3028-3032; tally 3038).
- Post-hoc items: D-a1..a3 (2805-2809), D-sweep (3687, 3691), D-cc (3884, later withdrawn 4081).

**Grok**
- Own table inconsistent with own assumptions: G-ledger's table is 3-6x above what its stated 2-3 word ops x partials gives, and rises with size where the arithmetic falls; its "calibrated > half official" clause is mis-specified (4074-4076; again 4171).
- Wrong count base: per partial, not per relation offered (4077, 4083).
- Direction errors: G-spv slack "reduce" where skipping small primes forces it up (3408); G-spv ruint gaining most, opposite of measured ceilings and the user's Mathematica (3409, 3439); G-slack shape reversed (3659).
- Definition mismatch: G-qr "HOLDS" only on mismatched definitions (per-partial vs per-distinct); falsified on the matched definition and on its own column A (3876, 4050, 4054, 4070).
- Internally inconsistent pair: G-mt and G-dup (3999-4000).
- Op-count assumption: G-gc counted 2 word ops per update; the card's cut is 1 (3803, 4234).
- Non-independence / post hoc: G-a is the user's P1-P2 restated, post hoc (2820); G-slack, G-slack REVISED, G-pinv post hoc (3655, 3698, 3815-3816).

**Reviewer (the user / Claude chat)**
- Op-count slip in an arithmetic note: ECM additions assumed 4 per step; the counted sites are 10 per ladder step (3411).
- Wrong model formula: Claude chat's 1/q share reference assumed log_B q uniform; corrected 0.154/0.153/0.094 -> 0.193/0.189/0.129 (3945).
- Wrong count base in annotations: Claude chat's annotations also used partials filed (4083); the lazy-cache annotation assumed distinct primes <= A's per run, the reverse of measured (3797, 3880).
- Range anchored on a stale baseline: W-qr's combined clause anchored on the earlier 24-28% baseline (3873).
- Toy model undersold a cost term: the slack toy expressed setup as a multiple of each pricing's sieve cost; null rejected (3688-3690).
- A prediction decided by arithmetic before the run (P5, 1516).
- Shared anchor: G2 is "the user's, also DeepSeek's earlier point" (2216); G-a is a Grok restatement of the user's P1-P2 (2820).
- Magnitude misses on gene/PD predictions: U1, U3, U4 (2667-2670); K1, K2 (3019-3020).

### Lines 4300-6390 (from the part-2 tally)


**Reviewer (the user / Claude chat)**
- **Design or prompt flaws that bias a model run:** a re-sieve fit presented as validation, although both prices scale alike, so it is not independent (4396). The DP prompt undercharged p-1 stage 2, because a completed stage 2 cannot be reused (4560). In the I-022 test, a 2-adic law bug, 2^(2−j) instead of 2^(1−j), in the user's own code (5707-5710) produced a "refuted" verdict that was later re-labelled UNTESTED.
- **Metric mixing:** the K1 headline compared a mean of predicted ratios (2.40) with a ratio of measured totals (2.07), "the user's design flaw" (5783).
- **Hand arithmetic or rebuttal numbers wrong:** in the U2 rebuttal, fulls-only e_F was given as ~0.35 instead of ~0.73 (c ~ 1.15 omitted, rough ξ), and the claim that partials steepen the response was wrong (they flatten it) (6128, 6133; scored at 6130 "all usable steeper missed, wrong direction"). The annotation on the D-audit base was compared on the wrong base (4322), and the annotation on G-audit was first written as "at 72 and 96" (4341). The near break-even ECM estimate was too pessimistic (4948).
- **Dismissing an outside point that held:** "DeepSeek's F1 extra 0.4-0.9 held; the user's dismissal of it was wrong" (5616).
- **A theory constant that the measurement rejected:** Claude chat derived c ≈ e^1.2 ≈ 3.4 for p-1 smoothness (4680). DeepSeek agreed (4733), and Grok and Claude chat both sealed M1 at 3-4 (4770). The measured c is 1.41/1.83, and 3.4 is rejected (4743, 4750). This is a shared anchor: all three sources hold the same wrong value.
- **Missing the saddle-point tilt in duplicate rules:** the 1/p and 1/(p p') duplicate rules missed by 3.6x and 13x (6012). The corrected rule is p^−α (6010).
- **Shared answers with Grok (non-independence):** C2 "rho dropped at 84 and 96" (4968-4969, 4998); Q4 "agree" (4645); M1 3-4 (4770).
- **Weak or post hoc tests:** Z3 was written with all three curves visible (6245). W2 and C1 were post hoc (4929, 4971).

**DeepSeek**
- **Invented or wrongly relayed parameters:** "card F 57-151" misattribution repeated after being conceded (5625). F 96/151 used in a U3 inconclusive clause, "F values the user never gave" (6118), and cited again in round 27 (6226). In V3, the clause used Wolfram's M = 20,000, not the card's M (6140). Round 23 used "the card's current 64" for L, which is Wolfram's L (6170). B = 1,993/1,171 was "not given; invented" (6279).
- **Wrong price base or pricing transfer:** D-audit assumed every audited op was charged at 1.0 (4317). Its Montgomery method (the ruint share divided by a total ratio of ~3.4) holds only for full-price ops (4321). D-audit ended FALSIFIED (5052). The D-2x2full Montgomery saving was predicted at 2-4x ruint, although both prices scale ~equally (4377).
- **Internally inconsistent clauses:** D-pool's cv ranges imply 14-30% below pooled, not 8-15% (4329).
- **Wrong factor in a correction:** K4 divided by the untilted 1.5, but the tilted factor was ~1.74 (5786, 5790).
- **Un-derived or unmeasured inputs:** the U2 "-2 to -3" order claim (6133). X1 rests on an unmeasured λ_q exponent of 1.2-1.5 (6196; refuted 6207). Its "computed check" was wrong (6192). The Y1 invariant is contradicted by its own numbers (6224). Y3 extrapolated from a grid-floor value on a flat curve (6242). In R-L2, partials were scaled like ln(L/B) (6280).
- **Formula or sign errors:** a G1 saddle-point sign error, with α 0.1-0.3 and large primes counted twice (5624). A P2 cost-formula sign slip (5951). R1 misapplied Hildebrand-Tenenbaum (6017).
- **Misreading a mixed state:** the κ miss, where "combined ~half of usable" was read as "each q seen many times" (6165).

**Grok**
- **Mis-specified clauses:** the G-ledger2 ratio clause (calibrated > half official) was mis-specified, and it self-falsified (4471-4472). G-ledger2 assumed 1 word op per relation against the cost model's 2-3 (4473).
- **Wrong card prices assumed:** in G-audit, the stated old prices differ from the card's (item 5 at 1.0, items 6-8 at 0.114) (4342). Its benchmark expectation (only the double divide above 3x) missed (5051).
- **Unexplained trends in its ranges:** the G-slackFC off-cell ranges rise with size while the tuned slack falls, with no mechanism given (4389). Its mechanism counts only cheaper setup (4388).
- **Contradicting the available model:** C3 (no ECM at 96) contradicts the honest-price DP (4970).
- **Unsupported bias claims:** the M3 c = 1 "under-predicts" claim is not supported (4772).
- **Ranges overshooting their own falsifier:** Q6 came in below its own 2^9 floor (4618). The G-ledger values were 6-40x lower than its ranges (4468).
- **Shared anchors with the reviewer:** M1 3-4 (4770), C2 (4998).

### Items the brief asked to verify: status
- **Units, per polynomial vs per number:** found. W4a (7223) and the H-2 note (7225) are the reviewer's. D-10's per-polynomial vs per-A slip is DeepSeek's (predictions/i032-2prime.md:138). The 0.5 µs-per-polynomial pass conflation is in D-3 and G-1 (i032-2prime.md:47, :222).
- **Robust-ratio misreadings:** found. Grok's "best robust +0" contradicts its own table, and its reasoning lets unpriced cost change a priced ratio (pp3-gap-and-shift.md:125-126; NOTES 8621). DeepSeek's D-8/D-9 misread the robust ratio (i032-2prime.md:120).
- **Invented or assumed parameters:** found.
  - DeepSeek's 0.30 µs per copy (pp3-gap-and-shift.md:179, :192), and the confirm price 0.0258 (NOTES 7456).
  - F 96/151 and B 1,993/1,171 (6118, 6226, 6279).
  - B and F relayed wrongly by our side: 1,841/1,151 and ~122/~82 (6565, 6508).
- **The reviewer's "241 µs / 7-point gap":** found (8538).
- **The floor/ceiling slip:** found (9016-9020).
- **R2-8 sealed without the cap:** found (8434).
- **"+1 and +2 within 1 point" miss:** found (8593).
- **DeepSeek's cross-run wall factor and ruint factor applied to Montgomery:** found, in D-15's annotations at predictions/2b-sizes.md:89-90. They are not in NOTES itself.
- **Shared anchors:** found.
  - The ~40 µs quick check behind R2-20, D-17 and G-10 (2b-sizes.md:91, :140).
  - The ledger phase pick in D-11, R2-11 and Grok (pp3-gap-and-shift.md:73, :123).
  - D-14 and G-7 (pp3-gap-and-shift.md:223).
  - Earlier: G-a and P1-P2 (2820), G2 (2216), M1 3-4 and c ≈ 3.4 (4680, 4770).

## 3a. Calibration (W4, Oct 27; `wolfram/2026-10-27_w4_calibration.wl`, `.out`; a tally, not a verdict)

**Stated confidence against outcome.** Only nine predictions on file state a confidence, and only five have a recorded score. The reviewer states none.

| forecaster | scored | mean stated | hit (as scored) | Brier | hit / Brier under the corrected meter |
|---|---|---|---|---|---|
| DeepSeek | 2 (D-9 65%, D-14 50%) | 58% | 0 of 2 | 0.336 | 1 of 2 / 0.186 |
| Grok | 3 (G-4 65%, G-7 60%, G-9 75%) | 67% | 1 of 3 | 0.282 | 2 of 3 / 0.182 |

- Brier 0.25 is what always saying 50% scores. As scored, both are worse than that; under the corrected meter, both are better (D-9 and G-4 flip to held).
- Not counted: D-11 (60%) and Grok's phase pick (55%), both information only; GP7 (85%) and Q5 (80%), still pending.
- **Five rows cannot support a calibration curve** (1 hit in 5: 95% interval 4–62%). The data say nothing yet about over- or under-confidence in stated probabilities.

**Sealed ranges: width against hit rate.** 110 numeric ranges from the five card runs since i032-2prime (i032-2prime, pp3-gap-and-shift, shift-past-2, shift-72-84, 2b-sizes). Hit = held as recorded; information-only rows use "measured inside the range". z = |measured − range midpoint| ÷ half-width, so z ≤ 1 is a hit.

| forecaster | rows | hit | median z (quartiles) | ratio ranges: hit, median width | wall % ranges: hit, median width | µs ranges: hit |
|---|---|---|---|---|---|---|
| the reviewer | 35 | 31 (89%) | 0.50 (0.22 / 0.73) | 21 of 25, 3.0 points | 9 of 9, 5.0 points | 1 of 1 |
| DeepSeek | 38 | 23 (61%) | 0.55 (0.14 / 1.56) | 14 of 25, 2.0 points | 8 of 8, 4.5 points | 1 of 5 |
| Grok | 37 | 24 (65%) | 0.53 (0.18 / 2.27) | 17 of 25, 1.8 points | 6 of 9, 3.5 points | 1 of 3 |

- **Who is over-confident:** DeepSeek and Grok. Their median miss is no larger than the reviewer's (median z 0.53–0.55 against 0.50), but their ranges are narrower (ratio ranges 1.8–2.0 points against 3.0) and their misses are far outside (upper quartile z 1.6–2.3 against 0.7). The miss rate comes from tails, not a general bias: a few large misses each run (D-8 by 11 points on ruint and Montgomery, the +2 official cells by 5–6 points, the µs phase excesses by 70–120% of the midpoint).
- **The reviewer** is close to a ~90% interval: 89% hits with median z 0.50. Its wall ranges (9 of 9, z 0.47) are about right, not too wide.
- **µs phase-excess ranges are the worst calibrated** for both outside forecasters (2 hits in 8, median z above 3). Those predictions inherited the "241 µs" anchor (section 3), so this is one error counted several times.
- **Direction:** DeepSeek's ratio ranges sit high on average (mean signed error −1.6 points: measured below the range), largely D-8. The others show no consistent direction.
- **Under the corrected meter** many ratio rows move (the reviewer 12 of 25, DeepSeek 7, Grok 8 hit). The wall rows are unchanged.

**Limits.** Rows within one run share numbers and anchors, so they are not independent, and the intervals in the `.out` are too narrow. Units differ, so z is the comparable measure; widths are per unit. D-14 and G-7 were sealed against 2′b and measured against 2′a (NOTES flags the proxy). Eight ranges were skipped: interval-width ranges (R2-8, D-7, G-5), D-10 (range text not on file), three non-range clauses, and falsifier bands. Extraction was delegated and spot-checked on 8 rows, all of which matched NOTES.

### DeepSeek's range-setting rules (received 05:39 Oct 27 PT; information only; verbatim)

*Its main section appeared twice in the reply; this is the single copy, from "## Recorded" on.*

<!-- verbatim begin -->
## Recorded

- My op-class checklist is recorded with the reviewer's edits (frozen before the new-pricing ratio is computed; scope = every op class official prices at unit cost) and Grok's sixth requirement, **no hand-picked sequences**, with the fix: each class's weight = retired instructions per op over a whole run of the frozen binary, across all call sites. Accepted; that closes the cherry-picking hole my list left open.
- My prediction guards are in PROTOCOL.md for all predictors. Accepted as written.
- **W3 correction accepted**: the ±1.5 "measured drift" was overstated; between-run variation is ~±1.3 (upper limit ±2.9), and ±1.5 is better read as a safe allowance, ±2.0 with 4 replicates. My guard cites it accordingly.
- **W4 calibration recorded** and is the basis for my answer below. **W1, W2, W5** recorded; the W1 conclusion that size will not settle the robust-rule question is noted, and the adoption decision remains the user's.

## How I would change range-setting

Three concrete rules, one target.

**Rule 1 — minimum width set by the arithmetic band, not the point estimate.** No sealed range narrower than **±3 points** (or the equivalent ratio width) for any point prediction, and no range whose center is the model output with a subjective margin around it. The arithmetic band is the **center** of the range, not the bound. For ratios, ±3 points on the percentage scale; for interval widths and counts, the same ±3-point floor in the natural unit, stated explicitly. My median width of 2.0 against an 89%-inside reviewer at 3.0 says the floor is the binding constraint I was missing.

**Rule 2 — widen by the scatter of my own misses, computed not guessed.** W4's upper-quartile z of 1.6–2.3 means my misses land far outside the range, which is what a single model output plus a margin produces. After every 10 scored predictions I will compute the standardized residual of my misses and set the next range as arithmetic band **± 2× the observed median |z|** in the same units. If misses keep landing at z ≈ 2, the range needs to be roughly twice the arithmetic band, not 10% wider — a rule that is checkable and re-tunable from the record.

**Rule 3 — separate computed from transferred.** Directly computed quantity: arithmetic band × 2. Quantity requiring a transfer across size, cell, or pricing: arithmetic band × 2 **plus** the W3 allowance (±1.3, ±2.0 with 4 replicates) **plus** a stated factor for the scaling assumption. D-15 priced is the clean case: the 96→72/84 carryover was the mechanism error, and this rule would have covered 1.0403 and 1.0242.

**Target hit rate: 80–85% inside stated range, and Brier ≤ 0.20 on the next 20 scored predictions.** Not 95%: a 95% target either forces absurdly wide ranges or invites post-hoc narrowing that breaks the sealing contract. The reviewer's 89% is the right neighbourhood; my 61% is the direct consequence of drawing ranges as if the model output were the truth. On confidences, 0.336 is worse than always-50%, which means my stated confidences were too high and too granular; the corrected-meter 0.186 is the target to match, not to beat by narrowing.

One further change, applied to my own filings first: **any categorical or superlative claim gets its comparison direction written into the prediction** ("largest increase" vs "largest absolute difference," "best wall" vs "best robust"), before the run. D-17 is the case that motivated it, and the rule is already in PROTOCOL.md.

No sealed prediction is filed from this message.
<!-- verbatim end -->

**The reviewer's notes:**
- **Rule 1's flat ±3-point floor should depend on the quantity:**
  - wall-clock: at least the measured noise (about ±1.3 cross-run, W3);
  - priced ratios from an exact count model: that model's own uncertainty, often far below 3 points;
  - transferred quantities, or quantities whose mechanism is unverified: wide.
- **Rule 2's units:** a miss's z is in units of the range's half-width. So the rule is "scale the next half-width by the median |z| of past misses", not "± 2 × |z|".
- **Target 80–85% inside range:** agreed.

### Grok's range-setting rules (received 05:40 Oct 27 PT; information only; verbatim)

<!-- verbatim begin -->
[PLACEHOLDER: Grok's reply was not included in the brief that recorded it; to be pasted verbatim.]
<!-- verbatim end -->

**The reviewer's notes:**
- **Q1 is adopted as Grok's own rule:**
  - wall-clock and transferred ranges: at least 2.5 points full width, plus about ±1.3 for comparisons across runs;
  - priced ranges from an exact model: half that;
  - target coverage 75–80%.
- **Q2: neither gaming route applies.**
  - Only the single sealed range is scored, so there is no unscored "safety tail".
  - The interval score charges the full width on both sides, so asymmetry costs what it adds. It is a proper scoring rule for honest quantiles.
  - Whether it favours wide ranges is an empirical question, answered by the computation below.
- **The real gaming route (the reviewer): choosing which questions to predict.** Priced ratios from an exact model are nearly free once the model has run.

### Interval score per sealed range (model, not a verdict; `wolfram/2026-10-27_interval_score2.wl`, `.out`)

**Definition** (lower is better; in the quantity's own units): width + (2/α) × the distance outside the range when missed, with α = 0.2, so each range is read as an 80% interval.

**Rows:** the 110 sealed ranges of W4, with **every information-only prediction excluded**: the priced clauses of R2-18, D-15 and G-8, D-11, Grok's phase pick, and G-6. That leaves 89 ranges. The two "wall ratio" rows (R2-4, D-3) are converted to % change.

**D-14 and G-7 were built on the reviewer's erroneous 241 µs figure.** Their scores are kept and labelled.

This version supersedes the first computation (1195ebe, `2026-10-27_interval_score.wl`), which included the information-only rows.

**(b) Common questions only (all three forecasters answered; 25 after the exclusions). Ranked on this only.**

| type (unit) | questions | the reviewer: coverage, median width, mean score | DeepSeek | Grok |
|---|---|---|---|---|
| wall-clock (% points) | 9 | 100%, 5.0, **5.8** | 100%, 4.0, **4.2** | 67%, 3.5, **7.6** |
| wall-clock (µs; sv:free2) | 1 | 100%, 25, 25 | 100%, 25, 25 | 100%, 20, **20** |
| priced, exact model (points) | 6 | 100%, 2.5, **2.9** | 100%, 1.5, **1.5** | 100%, 1.15, **1.5** |
| priced, by transfer (points) | 9 | 89%, 3.0, **5.6** | 44%, 2.0, **35.0** (median 14.5) | 67%, 1.8, **11.9** (median 3.0) |
| categorical | — | no range, no interval score (see W4's Brier) | | |

**Mean rank per common question** (1 = best, 3 = worst; unit-free; ties share the rank):

| type | the reviewer | DeepSeek | Grok |
|---|---|---|---|
| wall-clock (10) | 2.20 | **1.70** | 2.10 |
| priced, exact model (6) | 2.67 | **1.58** | 1.75 |
| priced, by transfer (9) | 2.11 | 2.39 | **1.50** |
| all types (25) | 2.28 | 1.92 | **1.80** |

- **Overall, Grok ranks first on the common questions (1.80), DeepSeek second (1.92), the reviewer third (2.28).** The ranking is by rank per question; a few very large misses (D-8 ruint and Montgomery, 106 each) drive the means, not the ranks.
- **The reviewer's wall ranges were wider than needed.** DeepSeek had the same coverage (9 of 9, 100%) with narrower ranges (median 4.0 against 5.0) and scores better (4.2 against 5.8).
- **On exact-model priced ratios the reviewer's ranges were also wider than needed:** all three covered 6 of 6, and the reviewer's width cost it the last place.
- **On transferred priced ratios the reviewer's width paid off:** 8 of 9 covered, against DeepSeek's 4 and Grok's 6. Grok still ranks first per question, because its hits were narrow and only the +0 and +2 official cells missed badly. DeepSeek ranks last.
- **Who answered what** (the reviewer's gaming note) is not scored here: (b) compares only questions all three answered.

**(a) All non-information-only sealed ranges** (not ranked, because each forecaster answered different questions):

| unit | the reviewer | DeepSeek | Grok |
|---|---|---|---|
| ratio (points) | n 18, 89%, width 2.6, mean 4.4 (median 3.0) | n 18, 72%, 1.8, 18.3 (2.15) | n 18, 83%, 1.8, 6.7 (1.8) |
| wall (% points) | n 10, 100%, 5.0, 5.6 | n 9, 100%, 4.0, 4.2 | n 9, 67%, 3.5, 7.6 |
| µs per number | n 1 (R2-20), 100%, 25, 25 | n 4 (D-14 ×3, D-17), 25%, 15, 138.8 | n 2 (G-7, G-10), 50%, 22.5, 164.5 |

The µs rows include D-14 and G-7, which were built on the reviewer's erroneous 241 µs figure.

**Limits:**
- The type classification is Claude Code's, stated in the `.wl` header. Exact model covers i032-2prime's 2′a vs REF and 2′b vs 2′a. Transfer covers the pp3 cells (from earlier cells, or from +0).
- Rows within one run share anchors, so they are not independent.
- 25 common questions are few, and one run (i032-2prime) supplies 13 of them.

## 4. Ambiguities resolved, and Unclear items

**Resolved (lines 6390-9184):**
- **DeepSeek R-L2 (6433):** the scoring table says "missed". The reviewer's addendum (6558) says DeepSeek's R-L1/L2/L3 were "falsified". The table is used (missed).
- **Falsifier rows merged into the clause they test:**
  - D-14's "falsifier: lp_ledger < 30 µs" (8651) is merged into D-14 size, giving falsified.
  - G-8's wall-clause falsifier (9071) is merged into G-8 wall 84 (missed, then falsified).
  - D-17 and G-10 "largest" are falsified as written.
  - Falsifier rows reading "none triggered" (8449) or "not triggered" (G-7, 8654) are not counted as items.
- **R2-17 (8752-8756):** counted once, as the conjunction NOTES scores (missed). Its six clause cells (3 held / 3 missed) are in the note. Counted per clause, the reviewer gets +3 held, +2 missed.
- **"The user's" and "the reviewer's" both scored on X3 (6406-6407):** both counted, as two reviewer-side entries.
- **Stage-G IDs G-1..G-5 (7036-7040) are the reviewer's,** not Grok's. DeepSeek's stage-G numbers (7157-7165) are info only, because they were filed after the results commit (7123).
- **G-6 and D-10 (8473-8474):** NOTES labels them information only (the model was committed first), although it also writes "missed". Counted as info only.
- **Hypotheses the user scored:** the reviewer's threshold-cap mechanism (6861, held) and its sieve-rise code-effect hypothesis (8137, "Confirmed"). Each counts as one categorical held. Drop them if only sealed ranges should count.
- **Restatements are not double counted:**
  - the overnight summary (6973-6978);
  - the reviewer's addendum (6988, 6556-6561);
  - DeepSeek's acceptances (6507, 7129, 8797-8800);
  - the per-run "Tally" paragraphs (8476-8480, 8658-8661, 8758-8762, 9076-9089);
  - the "common miss" notes (8480, 8623).
- **The C1..C7 (6643), T1..T5 (6688) and W2a/W2b (7222) definitions are not in NOTES.** They are counted with their recorded verdicts under "other (definition not in NOTES)" or "other", marked model.
- **The priced clauses of R2-18, D-15 and G-8 (9079-9084) are information only** under the time-order ruling. Each counts as one info-only priced row.

**Unclear (lines 6390-9184; not tallied):**
- **DeepSeek round 45's optimum estimates against the Wolfram model (7417-7420):** "+6 to +7 held (by coincidence)", "+5 to +6, model +4 (high by ~1)", never-combined "inside". These are informal estimates, not sealed.
- **RT-1 (DeepSeek round 51; 7744):** sealed for the eventual retune and never scored.
- **R-5 (7998):** counted as info only (DeepSeek), as NOTES labels it.

**Unclear (lines 700-4300, from part 1):**


- The user's Dickman-based p-1 prediction (1686, superseded) and the revised one (1764), and P-1M (2356, "direction only"): registered, no explicit verdict found in 700-4300.
- D-tcfloor (3693-3694): "Recorded as given; refuted by the existing data" -- a mechanism claim, not a scored prediction; not tallied (would be falsified if counted).
- 4082: "The separate row scoring the 54-bit part of the original G-gc stands as recorded (ruint held, Montgomery missed)" -- that row was not found in 700-4300; not tallied.
- G-rho (2826), G-sat (3224), D-p1 (3177), G-p1b (3183): recorded, untested at these sizes / not scored.
- D1 (2146): note says ruint and Montgomery alone were inside range (1.16x, 1.17x); scored on the robust ratio as written -> missed.

**Unclear (lines 4300-6390, from part 2):**


- Reviewer (Claude chat), re-sieve model pre-run expectation, 4407: "mostly held" apart from the two missed clauses (counted). The number of held clauses is not stated.
- Grok Q2, 4618: "held under its falsifier, but its ranges missed at 72 and 84 uniform". The verdict on the range clause is mixed and has no single verdict word.
- Reviewer Q1, 4619: "partial (72 held; 84 at 2^9-2^10 under 2 of 3 priors; 96 failed with ECM, held without)".
- Reviewer Q2, 4619: "held in 6 of 9 cells".
- Grok M5 and reviewer M5, 4774: "second half held for both". The first half is unscored or undefined, and M5's text is not in NOTES.
- Grok R2 and reviewer R2, 4842: "partial for both".
- Reviewer's GP2 guess (the large-prime phase flags too), 5102: "holds at 96 only".
- DeepSeek H2, 5675: "12-30% matched all N but not the movers". This is an explanation and has no verdict word.
- "N1: a q-slope in λ_q is refuted", 5956: the owner is unclear (annotation).
- DeepSeek W3 (i), 6186/6190: "miss at multiple 30, and falsified if the card's measured per-partial price is ≥ ~100". The score is conditional on the card's multiple, so it is pending in this range.
- DeepSeek V1 closed form, 6155: "essentially exact; DeepSeek credited". This is credit for a derivation, not a sealed range. The reviewer's "formula within ±0.05 held" (6162) is counted.
- Re-statements, not counted again: G-rm missed (4338, 4606; scored before 4300); D-gc, D-gc54, G-gc and G-gc54 "still ..." (4669-4672; scored at ~4230); GP1 restated at 4817; U3 and V3 acknowledged at 6271.
- Pending in this range (sealed, not scored here): GP3-GP7, Q5, W3/W4 (re-sieve), C2, C3, D-p0R, D-p0M, D-pool, D-2x2full, G-p0, G-pool, G-slack2x2, G-slackFC, M3 (DeepSeek's light-meter), N2, L3, P2 (I-024), Q3, R2 (waste), S3, T3, R-L1 to R-L4 (both sources), R-E1, R-E2, R-X3 and X3. R-E1, R-E2 and X3 are scored after 6390 (for example 6405-6407, 6477-6478).

**Part-2 conventions (lines 4300-6390):**


- "the user's", "Claude chat's" and "the reviewer's" are all counted as the reviewer. Many "the user's scoring" lists in the Wolfram sections score clauses whose predicted ranges were never written into NOTES before the run. They are counted as recorded; the note column flags this where it applies, for example M1-M6 at 4769 and A1/A2 at 4942.
- "failed" is counted as missed. Grok Q6 (4618) crossed its own stated falsifier floor (2^9), but NOTES says "failed", so it is counted as missed.
- "refuted" is counted as falsified (DeepSeek F2, H3, X1 clauses, the N1 fourth candidate, Y3's "≥ 8" clause, and the reviewer's "best L grows with P").
- "VOID" is counted as info-only (P3 for both). Z3, the reviewer's, is "no weight as a prediction" and is counted as info-only.
- Clauses with per-size or per-clause verdicts ("held at 84-96, missed at 72") are split into separate rows. Single verdicts covering several clauses ("missed on both clauses", P7/D-P7) are one row.
- Pre-run expectations by Claude chat on information-only Mathematica runs (4407, 4489, 4507) were given verdicts in NOTES, so they are counted with those verdicts. They are model runs, not card runs.
- Post hoc scorings are counted, with a note: W2 (4929), C1 (4971), G4 and the reviewer's 7.5-9.0 (5771-5772), U3 and V3 (6335-6339).
- The I-022 first scoring (5694) is counted as written, although 5705-5710 later re-labels I-022 UNTESTED because of the 2-adic bug in the user's code.
- Categories: "priced" covers ruint/Montgomery/official cost shares and savings on the card meter. "wall" covers phase-time anchor ratios and wall-clock speed-ups. "other" covers model quantities (yields, CVs, elasticities, the Dickman c, model DP savings). The model-DP gains and savings (Q3, R3, A2) are under "other" because they come from Mathematica cost models, not the card meter.

## 5. Full per-item list

- Lines 700-4300 and 4300-6390 carry the basis "unsplit": card and model rows are not separated there, but the notes say "(Wolfram)" or "model run" where it applies.
- In 6390-9184, "card" means measured on the card, or the card's own traces or benchmarks. "Model" means a Wolfram run scored by the user.
- Claude Code's own predictions are excluded: about 45 in 700-4300, about 13 in 4300-6390, and A1-A3 plus "clock or cache" in 6390-9184.

| forecaster | ID | run (section) | NOTES line | range | basis | category | result | note |
|---|---|---|---|---|---|---|---|---|
| Reviewer | (b) wider mc loses on balanced | generalization test (b) | 1377 | 700-4300 | unsplit | categorical | missed | registered ~1236 |
| Reviewer | P1 | size-relative budgets | 1512 | 700-4300 | unsplit | categorical | missed | 84-bit clause held by identity |
| Reviewer | P4 | size-relative budgets | 1515 | 700-4300 | unsplit | categorical | missed | = P1 for PRIMARY |
| Reviewer | P5 | size-relative budgets | 1516 | 700-4300 | unsplit | categorical | missed | decided by arithmetic before the run |
| Reviewer | S1 | per-stage budgets | 1648 | 700-4300 | unsplit | other | missed | budgets within one grid step |
| Reviewer | S2 | per-stage budgets | 1649 | 700-4300 | unsplit | categorical | missed | gate + beats alternatives |
| Reviewer | S5 | per-stage budgets | 1652 | 700-4300 | unsplit | other | missed | BI under ruint matched, not the registered reading |
| Reviewer | G2 (the user's) | re-solve, corrected card | 2325 | 700-4300 | unsplit | categorical | missed | "missed as written"; held at 84, 90; shared with DeepSeek's earlier point (2216) |
| Reviewer | correction to D5 (official falls <= 10%) | re-solve, corrected card | 2328 | 700-4300 | unsplit | priced | held | -0.6% |
| Reviewer | ECM on under official / Montgomery, off under ruint | per-pricing optima | 2398 | 700-4300 | unsplit | categorical | held |  |
| Reviewer | U1 | size-scaling rounds 2-3 | 2667 | 700-4300 | unsplit | other | missed | bc + gain |
| Reviewer | U2 | size-scaling rounds 2-3 | 2668 | 700-4300 | unsplit | other | held | budget steps |
| Reviewer | U3 | size-scaling rounds 2-3 | 2669 | 700-4300 | unsplit | priced | missed | PD_M |
| Reviewer | U4 | size-scaling rounds 2-3 | 2670 | 700-4300 | unsplit | priced | missed | PD_R |
| Reviewer | P1 (p-1 off, Track R) | per-track p-1 map check | 2740 | 700-4300 | unsplit | categorical | missed |  |
| Reviewer | P2 (Track M p-1) | per-track p-1 map check | 2741 | 700-4300 | unsplit | categorical | missed | gain clause held |
| Reviewer | P3 (official p-1 on) | per-track p-1 map check | 2742 | 700-4300 | unsplit | categorical | held |  |
| Reviewer | K1 | kc / lc bound round | 3019 | 700-4300 | unsplit | other | missed | kc clause held, gain clause missed |
| Reviewer | K2 | kc / lc bound round | 3020 | 700-4300 | unsplit | priced | missed | PD within 0.15 |
| Reviewer | W-qr (Claude chat's) | large-prime simulation | 3873 | 700-4300 | unsplit | other | falsified | re-scored on matched definition 4049: still FALSIFIED |
| Reviewer | informal pre-run expectation, (B,2B] share | lpdist / shape run | 4189 | 700-4300 | unsplit | other | info only | "informal, not registered in NOTES"; held except 84 |
| Reviewer | informal cv 0.3-0.45 comment | clean-check analysis | 4249 | 700-4300 | unsplit | other | info only | pre-run comment, "slightly low" |
| Reviewer | informal p0 expectation | p0 model | 4287 | 700-4300 | unsplit | other | info only | unregistered; held except 96 gain larger |
| Reviewer | pre-run expectation: z at 84 | Re-sieve model, lambda/z fitted (Mathematica) | 4407 | 4300-6390 | unsplit | other | missed | Claude chat pre-run expectation on a model run; 'mostly held' otherwise (see Unclear) |
| Reviewer | pre-run expectation: worst-of-three saving at 72 | Re-sieve model, lambda/z fitted (Mathematica) | 4407 | 4300-6390 | unsplit | priced | missed | 2.6% against <= ~2%; model run |
| Reviewer | pre-run: balanced prior | Dark-mass scheduler prototype (Mathematica) | 4489 | 4300-6390 | unsplit | categorical | held | Claude chat pre-run expectation; model run |
| Reviewer | pre-run: greedy-mass beats fixed by few%-15% | Dark-mass scheduler prototype (Mathematica) | 4489 | 4300-6390 | unsplit | other | missed | recorded 'failed' |
| Reviewer | pre-run: bits worse than mass | Dark-mass scheduler prototype (Mathematica) | 4489 | 4300-6390 | unsplit | categorical | held | 'held in direction only (negligible)' |
| Reviewer | pre-run: index rule <= fixed everywhere | Index rule and exact optimum (Mathematica) | 4507 | 4300-6390 | unsplit | categorical | missed | recorded 'failed' |
| Reviewer | pre-run: DP beats fixed by 2-8% | Index rule and exact optimum (Mathematica) | 4507 | 4300-6390 | unsplit | other | missed | recorded 'failed' (0.2-1.3%) |
| Reviewer | pre-run: rho + p-1 with modest td (84-96) | Index rule and exact optimum (Mathematica) | 4507 | 4300-6390 | unsplit | categorical | held | sub-clause: held at 84-96 |
| Reviewer | pre-run: rho + p-1 with modest td (72) | Index rule and exact optimum (Mathematica) | 4507 | 4300-6390 | unsplit | categorical | missed | sub-clause: failed at 72 |
| Reviewer | pre-run: index gap largest at 84-96 | Index rule and exact optimum (Mathematica) | 4507 | 4300-6390 | unsplit | categorical | held |  |
| Reviewer | sealed: ECM never chosen in any arm, 0% gain | ECM stage-2 DP (Mathematica) | 4559 | 4300-6390 | unsplit | categorical | missed | recorded 'failed' |
| Reviewer | Q3 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4619 | 4300-6390 | unsplit | other | held | Claude chat: ECM at 96 under 2-3 priors, gain >= 4% |
| Reviewer | Q4 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4619 | 4300-6390 | unsplit | categorical | held |  |
| Reviewer | Q6 (84, 96) | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4619 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | Q6 (72) | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4619 | 4300-6390 | unsplit | other | missed | sub-clause (2^7) |
| Reviewer | M1 | Real-prime measurement run (Mathematica), M1-M6 | 4770 | 4300-6390 | unsplit | other | missed | Claude chat, same 3-4 as Grok; DeepSeek 'also endorsed 3.4' (not counted) |
| Reviewer | M2 | Real-prime measurement run (Mathematica), M1-M6 | 4771 | 4300-6390 | unsplit | other | missed | as Grok |
| Reviewer | M3 (72, 84) | Real-prime measurement run (Mathematica), M1-M6 | 4772 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | M3 (96) | Real-prime measurement run (Mathematica), M1-M6 | 4772 | 4300-6390 | unsplit | other | missed | sub-clause (0.381) |
| Reviewer | M4 | Real-prime measurement run (Mathematica), M1-M6 | 4773 | 4300-6390 | unsplit | other | held |  |
| Reviewer | M6 (72, 84) | Real-prime measurement run (Mathematica), M1-M6 | 4777 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | M6 (96) | Real-prime measurement run (Mathematica), M1-M6 | 4777 | 4300-6390 | unsplit | other | held | sub-clause (0.152 vs 0.15-0.30) |
| Reviewer | R1 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | held | Claude chat |
| Reviewer | R3 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | 'far above' |
| Reviewer | R4 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | missed |  |
| Reviewer | R5 priors | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | held | sub-clause |
| Reviewer | R5 gain | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | R6 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | 'failed narrowly' |
| Reviewer | W2 | W-set (benchmark array), post hoc | 4929 | 4300-6390 | unsplit | categorical | held | post hoc; Claude chat |
| Reviewer | A1 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | other | held |  |
| Reviewer | A2 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | A2 'at most 1 curve' | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | other | held | separately scored clause |
| Reviewer | A3 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | categorical | held | 0 of 27 cells |
| Reviewer | C1 | C-set (card's rho variant), post hoc | 4971 | 4300-6390 | unsplit | categorical | held | post hoc |
| Reviewer | W1 (84, 96) | Audit re-typing items 0-8: predictions scored | 5050 | 4300-6390 | unsplit | priced | held | Claude chat; sub-clause |
| Reviewer | W1 (72) | Audit re-typing items 0-8: predictions scored | 5050 | 4300-6390 | unsplit | priced | missed | sub-clause (-18.1% vs -6 to -15%) |
| Reviewer | W1 shrinking clause | Audit re-typing items 0-8: predictions scored | 5050 | 4300-6390 | unsplit | categorical | held | sub-clause |
| Reviewer | W-audit | Audit re-typing items 0-8: predictions scored | 5053 | 4300-6390 | unsplit | priced | falsified | Claude chat; FALSIFIED (outside at every size) |
| Reviewer | P8 | Step 0b: 84-bit re-sieve on/off equality | 5497 | 4300-6390 | unsplit | categorical | held | the user's: coincidence, not a bug |
| Reviewer | u band | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | held | the user's scoring |
| Reviewer | omega/u at mid F | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | omega/u edge cells | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | missed | sub-clause (5 edge cells, to 1.67) |
| Reviewer | alpha range | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | held |  |
| Reviewer | alpha constant | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | within-cell slope | Wolfram cross-check 1: distinct primes vs Dickman u | 5608 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | slope | Wolfram cross-check 2: exact smoothness | 5616 | 4300-6390 | unsplit | other | held |  |
| Reviewer | threshold-miss | Wolfram cross-check 2: exact smoothness | 5616 | 4300-6390 | unsplit | other | held |  |
| Reviewer | factor-size signature | Wolfram cross-check 2: exact smoothness | 5616 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | c within +-0.4 | Wolfram cross-check 2: exact smoothness | 5616 | 4300-6390 | unsplit | other | missed | a steady +0.5 (later corrected at 5634: offset rises with size) |
| Reviewer | per-cell | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held | the user's own |
| Reviewer | offset (72-96) | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | offset (54) | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | alpha range | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | missed | 'mostly missed low' |
| Reviewer | model slope | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held |  |
| Reviewer | per-relation slope | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held |  |
| Reviewer | KS gain | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held | the user's 0.3-0.8 counterpart to DeepSeek's G3 (5623) |
| Reviewer | u gain | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | missed | 'missed low' |
| Reviewer | net gain | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | held |  |
| Reviewer | k = 1 under 15% | Wolfram: tilted saddle-point model vs 1,219 relations | 5642 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | I-022 (a) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | missed | the user's 'yes'; superseded by the 2-adic bug correction (5705-5710: I-022 UNTESTED), verdict stands as written |
| Reviewer | I-022 (b) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | missed | 35% outside 15-30% |
| Reviewer | I-022 (c) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | missed | -15% |
| Reviewer | within 1.5x | k=1 calibration and exact-rho check (J4) | 5714 | 4300-6390 | unsplit | other | held |  |
| Reviewer | N = 1 mod 8 error larger | k=1 calibration and exact-rho check (J4) | 5714 | 4300-6390 | unsplit | categorical | held |  |
| Reviewer | rho under-predicting absolute counts | k=1 calibration and exact-rho check (J4) | 5714 | 4300-6390 | unsplit | categorical | missed |  |
| Reviewer | rho movers ~1.5x | k=1 calibration and exact-rho check (J4) | 5714 | 4300-6390 | unsplit | other | held |  |
| Reviewer | tilted ~3.5x | k=1 calibration and exact-rho check (J4) | 5714 | 4300-6390 | unsplit | other | held | 'roughly held (3.03)' |
| Reviewer | P1 | Step 1: fills deleted - scored | 5748 | 4300-6390 | unsplit | priced | held | re-sieve cheaper at 84/96 ruint, >= 5% at 96 |
| Reviewer | P2 | Step 1: fills deleted - scored | 5750 | 4300-6390 | unsplit | priced | missed |  |
| Reviewer | touched entries 7.5-9.0 | Step 1: touched-entry predictions, post hoc | 5772 | 4300-6390 | unsplit | other | missed | post hoc; scored definition (with A-primes) missed at every size; without them held 72/84, missed 54/96 |
| Reviewer | K1 | Fixed I-022 re-run (K1-K4) | 5783 | 4300-6390 | unsplit | other | held | held on matched metrics; the printed headline mixed metrics ('the user's design flaw') |
| Reviewer | K2 | Fixed I-022 re-run (K1-K4) | 5784 | 4300-6390 | unsplit | other | held |  |
| Reviewer | K3 | Fixed I-022 re-run (K1-K4) | 5785 | 4300-6390 | unsplit | other | held |  |
| Reviewer | K4 | Fixed I-022 re-run (K1-K4) | 5786 | 4300-6390 | unsplit | other | held |  |
| Reviewer | P5 | Step 3: hash banding | 5830 | 4300-6390 | unsplit | other | missed | hash >= 2x clean price and banding adopted |
| Reviewer | fulls | I-023 tilted model on real SIQS polynomials (Wolfram) | 5855 | 4300-6390 | unsplit | other | held | the user's scoring |
| Reviewer | partials | I-023 tilted model on real SIQS polynomials (Wolfram) | 5855 | 4300-6390 | unsplit | other | held |  |
| Reviewer | partials / fulls | I-023 tilted model on real SIQS polynomials (Wolfram) | 5855 | 4300-6390 | unsplit | other | held |  |
| Reviewer | ablation under 3% at 96 | I-023 tilted model on real SIQS polynomials (Wolfram) | 5855 | 4300-6390 | unsplit | other | held |  |
| Reviewer | ablation +2-10% at 54 | I-023 tilted model on real SIQS polynomials (Wolfram) | 5855 | 4300-6390 | unsplit | other | missed | +12% |
| Reviewer | partials | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | held |  |
| Reviewer | distinct q (54, 84, 96) | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | distinct q (72) | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | combined | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | held |  |
| Reviewer | Poisson shape (84-96) | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | Poisson shape (54, 72) | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | growth | I-023 combined relations from 1LP partials (Wolfram) | 5883 | 4300-6390 | unsplit | other | held |  |
| Reviewer | raw CV fulls 20-35% | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | missed | missed high |
| Reviewer | raw CV partials 15-30% | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | missed | missed high |
| Reviewer | meas/pred within 2 pp of floor, partials | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | held |  |
| Reviewer | meas/pred within 2 pp of floor, fulls (54-72) | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | meas/pred within 2 pp of floor, fulls (84-96) | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | band trend | Wolfram per-N predictability / lambda_q-by-band | 5974 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | P3 'more than half' | Duplicate-polynomial test (Wolfram) | 5992 | 4300-6390 | unsplit | other | info only | void |
| Reviewer | repeats under old generator | Duplicate-polynomial test (Wolfram) | 5994 | 4300-6390 | unsplit | other | held |  |
| Reviewer | distinct within +-2% | Duplicate-polynomial test (Wolfram) | 5994 | 4300-6390 | unsplit | other | held |  |
| Reviewer | duplicates 5-15% | Duplicate-polynomial test (Wolfram) | 5994 | 4300-6390 | unsplit | other | held |  |
| Reviewer | partial rate within +-5% | Duplicate-polynomial test (Wolfram) | 5994 | 4300-6390 | unsplit | other | held |  |
| Reviewer | case A | Duplicate relations between polynomial pairs (Wolfram) | 6012 | 4300-6390 | unsplit | other | held |  |
| Reviewer | case C | Duplicate relations between polynomial pairs (Wolfram) | 6012 | 4300-6390 | unsplit | other | held |  |
| Reviewer | case B (1/p rule) | Duplicate relations between polynomial pairs (Wolfram) | 6012 | 4300-6390 | unsplit | other | missed | 3.6x the user's 1/p |
| Reviewer | case D (1/(p p')) | Duplicate relations between polynomial pairs (Wolfram) | 6012 | 4300-6390 | unsplit | other | missed | 13x |
| Reviewer | k = 1 CV 25-45% (54, 84) | I-023/I-024 model forecast of polynomials to completion (Wolfram) | 6034 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | k = 1 CV 25-45% (72, 96) | I-023/I-024 model forecast of polynomials to completion (Wolfram) | 6034 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | KS CV 12-25% | I-023/I-024 model forecast of polynomials to completion (Wolfram) | 6034 | 4300-6390 | unsplit | other | held |  |
| Reviewer | KS mean saving 15-30% | I-023/I-024 model forecast of polynomials to completion (Wolfram) | 6034 | 4300-6390 | unsplit | other | missed | missed high (38-41%) |
| Reviewer | 2LP counts | I-023 double large primes (Wolfram) | 6050 | 4300-6390 | unsplit | other | held |  |
| Reviewer | 1LP | I-023 double large primes (Wolfram) | 6050 | 4300-6390 | unsplit | other | held |  |
| Reviewer | usable +10-40% / +5-25% | I-023 double large primes (Wolfram) | 6050 | 4300-6390 | unsplit | other | missed | missed badly (4-5x) |
| Reviewer | polynomials to target (84) | I-023 double large primes (Wolfram) | 6050 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | polynomials to target (96) | I-023 double large primes (Wolfram) | 6050 | 4300-6390 | unsplit | other | missed | sub-clause (2 of 3 N) |
| Reviewer | best F 0.7-1.4x and flat within 10% | I-023/I-027 model scan of F and M (Wolfram) | 6100 | 4300-6390 | unsplit | other | missed | proxy-driven |
| Reviewer | best M at 54 smallest | I-023/I-027 model scan of F and M (Wolfram) | 6100 | 4300-6390 | unsplit | categorical | held |  |
| Reviewer | best M at 96 larger | I-023/I-027 model scan of F and M (Wolfram) | 6100 | 4300-6390 | unsplit | categorical | missed |  |
| Reviewer | linear algebra < 15% at the minimum | I-023/I-027 model scan of F and M (Wolfram) | 6100 | 4300-6390 | unsplit | other | held |  |
| Reviewer | fast growth at 2x | I-023/I-027 model scan of F and M (Wolfram) | 6100 | 4300-6390 | unsplit | other | held |  |
| Reviewer | fulls e_F 0.25-0.5 | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | other | missed |  |
| Reviewer | theory within 0.1 (84-96) | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | theory within 0.1 (54, 72) | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | other | missed | sub-clause |
| Reviewer | median overshoot | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | other | held |  |
| Reviewer | all usable steeper | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | categorical | missed | wrong direction |
| Reviewer | e_M | I-027 elasticities by finite difference (Wolfram) | 6130 | 4300-6390 | unsplit | other | held |  |
| Reviewer | kappa_eff 1.3-1.8 | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | missed | 'missed slightly' |
| Reviewer | combined share 40-70% | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | held |  |
| Reviewer | e_f 1.5-1.8 (72-96) | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | held | sub-clause |
| Reviewer | e_f 1.5-1.8 (54) | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | missed | sub-clause (1.99) |
| Reviewer | formula within +-0.05 | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | held |  |
| Reviewer | W3 (ii) | I-027/I-028 large-prime bound scan (Wolfram), W3 | 6184 | 4300-6390 | unsplit | other | missed | 8-15% |
| Reviewer | W3 (iii) | I-027/I-028 large-prime bound scan (Wolfram), W3 | 6185 | 4300-6390 | unsplit | other | missed | 'both < 0.6 missed narrowly' |
| Reviewer | W3 (i) | I-027/I-028 large-prime bound scan (Wolfram), W3 | 6186 | 4300-6390 | unsplit | categorical | missed | 256-512; 'missed badly, in the wrong direction' |
| Reviewer | alpha 0.55-0.9 | I-028 best L against run length (Wolfram) | 6214 | 4300-6390 | unsplit | other | held |  |
| Reviewer | best L grows with P | I-028 best L against run length (Wolfram) | 6215 | 4300-6390 | unsplit | categorical | falsified | 'refuted (both)' |
| Reviewer | P lambda_L < 0.3 | I-028 best L against run length (Wolfram) | 6216 | 4300-6390 | unsplit | other | held |  |
| Reviewer | never-combined 65-85% at 96 / 20,000 (model) | I-028 best L against run length (Wolfram) | 6217 | 4300-6390 | unsplit | other | held | model value 0.80; X3 itself scored on the card later |
| Reviewer | never-combined falls to 40-65% in long runs | I-028 best L against run length (Wolfram) | 6217 | 4300-6390 | unsplit | other | missed | stays 0.81 |
| Reviewer | Y3 3-6 | I-028 finer L grid (Wolfram), Y3 | 6237 | 4300-6390 | unsplit | categorical | missed |  |
| Reviewer | P(L = p_max) >= 1.5x P(best) | I-028 finer L grid (Wolfram), Y3 | 6237 | 4300-6390 | unsplit | other | held | 1.8x |
| Reviewer | sign change matches the minimum | I-028 finer L grid (Wolfram), Y3 | 6237 | 4300-6390 | unsplit | categorical | held |  |
| Reviewer | Z3 | DeepSeek round 29, Z3 | 6243 | 4300-6390 | unsplit | other | info only | 'written with all three visible (no weight as a prediction)' |
| Reviewer | P3 | Step 5: wall-clock re-run with two anchors | 6325 | 4300-6390 | unsplit | wall | missed | median ns per priced unit returns to 60-90 |
| Reviewer | P4 | Step 5: wall-clock re-run with two anchors | 6327 | 4300-6390 | unsplit | wall | missed | setup at 72 under 1.5x on both anchors |
| Reviewer | P6 | Step 5: wall-clock re-run with two anchors | 6328 | 4300-6390 | unsplit | wall | missed | solve at 84-96 under 1.5x on anchor B |
| Reviewer | P7 | Step 5: wall-clock re-run with two anchors | 6329 | 4300-6390 | unsplit | wall | missed | 'missed on both clauses' (one verdict, two clauses) |
| Reviewer | U3 (84) | Step 5: wall-clock re-run with two anchors | 6336 | 4300-6390 | unsplit | priced | held | post hoc |
| Reviewer | U3 (96) | Step 5: wall-clock re-run with two anchors | 6336 | 4300-6390 | unsplit | priced | missed | post hoc |
| Reviewer | V3 | Step 5: wall-clock re-run with two anchors | 6339 | 4300-6390 | unsplit | priced | held | post hoc |
| Reviewer | X3, the user's 65-85% | Step 7b X3 on the card | 6406 | 6390-9184 | card | other | missed | "missed narrowly" (0.852) |
| Reviewer | R-X3, the reviewer's 0.86-0.94 | Step 7b X3 on the card | 6407 | 6390-9184 | card | other | missed | "missed narrowly"; separate entry from the user's 65-85% |
| Reviewer | R-L1 polynomials | Step 7c L test | 6432 | 6390-9184 | card | other | missed | annotation 6557: "test did not isolate L (reviewer's spec)" |
| Reviewer | R-L2 stored partials | Step 7c L test | 6433 | 6390-9184 | card | other | missed |  |
| Reviewer | R-L3 priced ruint mean | Step 7c L test | 6434 | 6390-9184 | card | priced | missed |  |
| Reviewer | R-L4 wall total | Step 7c L test | 6435 | 6390-9184 | card | wall | missed |  |
| Reviewer | R-L4 lp_ledger | Step 7c L test | 6436 | 6390-9184 | card | wall | held | lp_ledger region wall clause, scored separately in the same row group |
| Reviewer | R-E1 e_F all usable (model analog) | Light meter at the card's point (Wolfram) | 6477 | 6390-9184 | model | other | missed | direction right, magnitude too low |
| Reviewer | R-E2 e_M (model analog) | Light meter at the card's point (Wolfram) | 6478 | 6390-9184 | model | other | held |  |
| Reviewer | W-6 e_F fulls | Light meter at the card's point (Wolfram) | 6479 | 6390-9184 | model | other | missed | this W-series (W-1..W-6) differs from the W1a..W4b simulation series |
| Reviewer | W-1 model polynomials | Light meter at the card's point (Wolfram) | 6480 | 6390-9184 | model | other | missed |  |
| Reviewer | W-2 model stored partials | Light meter at the card's point (Wolfram) | 6481 | 6390-9184 | model | other | held |  |
| Reviewer | W-3a never-combined, reference L | Light meter at the card's point (Wolfram) | 6482 | 6390-9184 | model | other | held |  |
| Reviewer | W-3b never-combined, L/B 12 | Light meter at the card's point (Wolfram) | 6483 | 6390-9184 | model | other | held |  |
| Reviewer | W-4 kappa_eff | Light meter at the card's point (Wolfram) | 6484 | 6390-9184 | model | other | held |  |
| Reviewer | W-5 combined share, M 300 | Light meter at the card's point (Wolfram) | 6485 | 6390-9184 | model | other | held | split: held at M 300 |
| Reviewer | W-5 combined share, M 1,000 | Light meter at the card's point (Wolfram) | 6485 | 6390-9184 | model | other | missed | split: missed at M 1,000 |
| Reviewer | R-F1 polynomials (the user's) | Step 8 F test | 6547 | 6390-9184 | card | other | held |  |
| Reviewer | R-F2 solve share (the user's) | Step 8 F test | 6548 | 6390-9184 | card | priced | missed |  |
| Reviewer | R-F3 total priced ruint (the user's) | Step 8 F test | 6549 | 6390-9184 | card | priced | missed |  |
| Reviewer | C1 | Light meter vs card (Wolfram, I-023/I-028/I-030) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held | the user's scoring; clause texts not recorded in NOTES |
| Reviewer | C2 | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | C3 | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | C4 | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | C6b | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | C7 | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | C5a | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | missed | C5 "refutes the reviewer's 'L explains the ~0.6 combined share' idea" |
| Reviewer | C5b | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | C6a | Light meter vs card (Wolfram) | 6643 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | T1 | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | T2a | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | T4a | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | T4c | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | T5b | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | held |  |
| Reviewer | T2b | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | T3a | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | T3b | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | T4b | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | T5a | Light meter with threshold cap (Wolfram) | 6688 | 6390-9184 | model | other (definition not in NOTES) | missed |  |
| Reviewer | S9-1 true-full capture 96 | Stage B step 9 | 6849 | 6390-9184 | card | other | missed |  |
| Reviewer | S9-2 true-partial capture 96 | Stage B step 9 | 6850 | 6390-9184 | card | other | held |  |
| Reviewer | S9-3 low band | Stage B step 9 | 6851 | 6390-9184 | card | other | missed |  |
| Reviewer | S9-3 high band | Stage B step 9 | 6852 | 6390-9184 | card | other | held |  |
| Reviewer | S9-4 true-partial capture 84 | Stage B step 9 | 6853 | 6390-9184 | card | other | held |  |
| Reviewer | S9-5 median under-count at fulls | Stage B step 9 | 6854 | 6390-9184 | card | other | missed |  |
| Reviewer | S9-6 end-to-end partials low band | Stage B step 9 | 6855 | 6390-9184 | card | other | held |  |
| Reviewer | S9-7 end-to-end fulls | Stage B step 9 | 6856 | 6390-9184 | card | other | missed |  |
| Reviewer | S9-8 largest partial loss is not the threshold | Stage B step 9 | 6857 | 6390-9184 | card | categorical | missed |  |
| Reviewer | S9-9 84 vs 96 partials | Stage B step 9 | 6858 | 6390-9184 | card | other | held |  |
| Reviewer | Threshold-cap hypothesis (mechanism) | Stage B step 9 | 6861 | 6390-9184 | card | categorical | held | "The reviewer's hypothesis ... held in mechanism"; a hypothesis, not a sealed range |
| Reviewer | R-G1 (the user's) | Stage E 2x2 | 6900 | 6390-9184 | card | priced | held |  |
| Reviewer | R-G2 (the user's) | Stage E 2x2 | 6901 | 6390-9184 | card | wall | missed | "missed narrowly" |
| Reviewer | M3 at 84 (the user's) | Stage F step 6 | 6935 | 6390-9184 | card | other | held | at the edge |
| Reviewer | M3 at 96 (the user's) | Stage F step 6 | 6935 | 6390-9184 | card | other | missed |  |
| Reviewer | G-1 (stage G) partial capture | Stage G scored | 7036 | 6390-9184 | card | other | held | stage-G IDs, not Grok's G-n |
| Reviewer | G-2 (stage G) polynomials | Stage G scored | 7037 | 6390-9184 | card | other | held |  |
| Reviewer | G-3 (stage G) candidates | Stage G scored | 7038 | 6390-9184 | card | other | held |  |
| Reviewer | G-4 (stage G) priced ruint | Stage G scored | 7039 | 6390-9184 | card | priced | missed |  |
| Reviewer | G-5 (stage G) wall-clock | Stage G scored | 7040 | 6390-9184 | card | wall | missed | reviewer noted beforehand it was expected to miss (7142) |
| Reviewer | W1a | Wolfram card-sieve simulation | 7220 | 6390-9184 | model | other | held |  |
| Reviewer | W1b | Wolfram card-sieve simulation | 7221 | 6390-9184 | model | other | missed |  |
| Reviewer | W2a | Wolfram card-sieve simulation | 7222 | 6390-9184 | model | other | held | definition not in NOTES |
| Reviewer | W2b | Wolfram card-sieve simulation | 7222 | 6390-9184 | model | other | held | definition not in NOTES |
| Reviewer | W3 (under-count 4.59) | Wolfram card-sieve simulation | 7222 | 6390-9184 | model | other | held |  |
| Reviewer | W4b (0.647) | Wolfram card-sieve simulation | 7222 | 6390-9184 | model | other | held |  |
| Reviewer | W4a candidates | Wolfram card-sieve simulation | 7223 | 6390-9184 | model | other | missed | unit error: per-polynomial vs per-number (7223) |
| Reviewer | V1 | Wolfram cost forecast | 7327 | 6390-9184 | model | other | held |  |
| Reviewer | V2a | Wolfram cost forecast | 7328 | 6390-9184 | model | other | held |  |
| Reviewer | V2b | Wolfram cost forecast | 7328 | 6390-9184 | model | other | held |  |
| Reviewer | V2c | Wolfram cost forecast | 7328 | 6390-9184 | model | other | held |  |
| Reviewer | V3a | Wolfram cost forecast | 7329 | 6390-9184 | model | wall | held | model wall vs card +29.4% |
| Reviewer | V3b | Wolfram cost forecast | 7329 | 6390-9184 | model | wall | held |  |
| Reviewer | V4 | Wolfram cost forecast | 7330 | 6390-9184 | model | wall | held |  |
| Reviewer | V5 best shift, cheap confirm | Wolfram cost forecast | 7331 | 6390-9184 | model | categorical | missed | hand calc ignored ledger growth |
| Reviewer | V6 option + cheap confirm best | Wolfram cost forecast | 7332 | 6390-9184 | model | categorical | missed |  |
| Reviewer | X1 (+6) | Wolfram cost forecast, wider grid | 7413 | 6390-9184 | model | categorical | held | model-run X1-X7, not the earlier Claude Code X1-X5 or the X3 share |
| Reviewer | X2 (-8.3%) | Wolfram cost forecast, wider grid | 7413 | 6390-9184 | model | wall | held |  |
| Reviewer | X3 (+4) | Wolfram cost forecast, wider grid | 7413 | 6390-9184 | model | categorical | held |  |
| Reviewer | X4 (-22.5%) | Wolfram cost forecast, wider grid | 7413 | 6390-9184 | model | wall | held |  |
| Reviewer | X5 (-17.3%) | Wolfram cost forecast, wider grid | 7414 | 6390-9184 | model | wall | missed | by 0.3 point |
| Reviewer | X6 (0.807) | Wolfram cost forecast, wider grid | 7415 | 6390-9184 | model | other | held |  |
| Reviewer | X7 (1.24x) | Wolfram cost forecast, wider grid | 7415 | 6390-9184 | model | other | held |  |
| Reviewer | Y1 | Wolfram: which parts of the better sieve pay | 7487 | 6390-9184 | model | wall | held |  |
| Reviewer | Y2 | Wolfram: which parts of the better sieve pay | 7487 | 6390-9184 | model | wall | held |  |
| Reviewer | Y3 best today | Wolfram: which parts of the better sieve pay | 7488 | 6390-9184 | model | categorical | missed |  |
| Reviewer | Y4 | Wolfram: which parts of the better sieve pay | 7489 | 6390-9184 | model | wall | held |  |
| Reviewer | Y5 | Wolfram: which parts of the better sieve pay | 7490 | 6390-9184 | model | wall | missed | narrowly (1.10 points) |
| Reviewer | Y6 B's best shift | Wolfram: which parts of the better sieve pay | 7491 | 6390-9184 | model | categorical | held |  |
| Reviewer | Z1 pair gain | Wolfram: per-parity threshold | 7561 | 6390-9184 | model | wall | held |  |
| Reviewer | Z2 | Wolfram: per-parity threshold | 7562 | 6390-9184 | model | categorical | held |  |
| Reviewer | Z3 | Wolfram: per-parity threshold | 7563 | 6390-9184 | model | wall | held |  |
| Reviewer | Z4 | Wolfram: per-parity threshold | 7564 | 6390-9184 | model | wall | held |  |
| Reviewer | Z5 reproduction | Wolfram: per-parity threshold | 7565 | 6390-9184 | model | other | held |  |
| Reviewer | H-1 capture | Stage H | 7664 | 6390-9184 | card | other | held |  |
| Reviewer | H-2 candidates per number | Stage H | 7665 | 6390-9184 | card | other | held |  |
| Reviewer | H-3 polynomials | Stage H | 7666 | 6390-9184 | card | other | held |  |
| Reviewer | H-4 ruint | Stage H | 7667 | 6390-9184 | card | priced | missed |  |
| Reviewer | H-5 selectivity | Stage H | 7668 | 6390-9184 | card | other | held |  |
| Reviewer | H-6 under-count | Stage H | 7669 | 6390-9184 | card | other | missed |  |
| Reviewer | H-7 capture (ii) | Stage H | 7670 | 6390-9184 | card | other | held | at the edge |
| Reviewer | H-8 polynomials (ii) | Stage H | 7671 | 6390-9184 | card | other | held |  |
| Reviewer | H-9 ruint (ii) | Stage H | 7672 | 6390-9184 | card | priced | missed |  |
| Reviewer | H-10 wall (ii) | Stage H | 7673 | 6390-9184 | card | wall | missed |  |
| Reviewer | H-11 polynomials (iii) | Stage H | 7674 | 6390-9184 | card | other | held |  |
| Reviewer | H-12 candidates per number | Stage H | 7675 | 6390-9184 | card | other | held | sub-clause 1 of 2 (row scores "held; held") |
| Reviewer | H-12 candidates per polynomial | Stage H | 7675 | 6390-9184 | card | other | held | sub-clause 2 of 2 |
| Reviewer | H-13 wall (iii) | Stage H | 7676 | 6390-9184 | card | wall | missed |  |
| Reviewer | H-14 ruint (iii) | Stage H | 7677 | 6390-9184 | card | priced | held |  |
| Reviewer | H-15 never-combined | Stage H | 7678 | 6390-9184 | card | other | held |  |
| Reviewer | H-16 wall (iv) | Stage H | 7679 | 6390-9184 | card | wall | missed |  |
| Reviewer | H-17 ruint (iv) | Stage H | 7680 | 6390-9184 | card | priced | held | at the edge |
| Reviewer | H-18 sieve wall per polynomial | Stage H | 7681 | 6390-9184 | card | wall | missed | narrowly |
| Reviewer | H2-1 (iii) wall | Stage H2 | 7841 | 6390-9184 | card | wall | held |  |
| Reviewer | H2-2 (iv) wall | Stage H2 | 7842 | 6390-9184 | card | wall | held |  |
| Reviewer | H2-3 polynomials | Stage H2 | 7843 | 6390-9184 | card | other | held | sub-clause 1 of 2 |
| Reviewer | H2-3 wall | Stage H2 | 7843 | 6390-9184 | card | wall | held | sub-clause 2 of 2 |
| Reviewer | H2-4 polynomials | Stage H2 | 7844 | 6390-9184 | card | other | held | sub-clause 1 of 2 |
| Reviewer | H2-4 wall | Stage H2 | 7844 | 6390-9184 | card | wall | held | sub-clause 2 of 2 |
| Reviewer | I-029a ns/prime, version (b) | I-029 microbenchmark | 7905 | 6390-9184 | card | wall | missed | benchmark timing; split (b)/(c) as in NOTES |
| Reviewer | I-029a ns/prime, version (c) | I-029 microbenchmark | 7905 | 6390-9184 | card | wall | missed |  |
| Reviewer | I-029b ns/candidate, (b) | I-029 microbenchmark | 7906 | 6390-9184 | card | wall | missed |  |
| Reviewer | I-029b ns/candidate, (c) | I-029 microbenchmark | 7906 | 6390-9184 | card | wall | missed |  |
| Reviewer | R-1 root alone wall | Root confirm | 8039 | 6390-9184 | card | wall | missed |  |
| Reviewer | R-2 root alone priced ruint | Root confirm | 8040 | 6390-9184 | card | priced | held |  |
| Reviewer | R-3 best wall shift | Root confirm | 8041 | 6390-9184 | card | categorical | held | grid extended to +4 so it could fail (8005); +1/+2/+3 not separated |
| Reviewer | R-4 best shift wall | Root confirm | 8042 | 6390-9184 | card | wall | missed |  |
| Reviewer | RC2-1 root alone wall | Root confirm retime | 8126 | 6390-9184 | card | wall | held |  |
| Reviewer | RC2-2 sieve region | Root confirm retime | 8127 | 6390-9184 | card | wall | held |  |
| Reviewer | RC2-3 best shift wall | Root confirm retime | 8128 | 6390-9184 | card | wall | held | best shift not separated |
| Reviewer | RC2-4 interval <= +/-3 | Root confirm retime | 8129 | 6390-9184 | card | interval width | missed |  |
| Reviewer | Sieve-rise hypothesis (~0.65 us/polynomial code effect) | Root confirm retime | 8137 | 6390-9184 | card | categorical | held | "Confirmed" by the user; hypothesis, not a sealed range |
| Reviewer | R2-1 2'a official | I-032 option 2' | 8427 | 6390-9184 | card | priced | held |  |
| Reviewer | R2-2 2'a ruint, Montgomery | I-032 option 2' | 8428 | 6390-9184 | card | priced | held | one verdict, two pricings |
| Reviewer | R2-3 relations identical | I-032 option 2' | 8429 | 6390-9184 | card | other | held |  |
| Reviewer | R2-4 2'a wall | I-032 option 2' | 8430 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-5 2'b o/r/m | I-032 option 2' | 8431 | 6390-9184 | card | priced | held | "held (all three)" |
| Reviewer | R2-6 2'b wall | I-032 option 2' | 8432 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-7 sieve region | I-032 option 2' | 8433 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-8 95% intervals | I-032 option 2' | 8434 | 6390-9184 | card | interval width | missed | sealed without the 2.4 GHz cap |
| Reviewer | R2-9 2'b+pp3 o/r/m/wall | I-032 option 2' | 8435 | 6390-9184 | card | mixed (priced+wall) | held | "held (all four)" |
| Reviewer | R2-10 better under all three | I-032 option 2' | 8436 | 6390-9184 | card | categorical | held |  |
| Reviewer | R2-11 phase | pp3 breakdown (unscored) | 8537 | 6390-9184 | card | wall | info only | breakdown seen first |
| Reviewer | R2-12 +0 priced reproduce | Shift test | 8587 | 6390-9184 | card | priced | held |  |
| Reviewer | R2-12 +0 wall | Shift test | 8588 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-12 +1 o/r/m/wall | Shift test | 8589 | 6390-9184 | card | mixed (priced+wall) | held | all four |
| Reviewer | R2-12 +2 official | Shift test | 8590 | 6390-9184 | card | priced | missed |  |
| Reviewer | R2-12 +2 ruint/Montgomery/wall | Shift test | 8591 | 6390-9184 | card | mixed (priced+wall) | held |  |
| Reviewer | R2-13 best wall +2 | Shift test | 8592 | 6390-9184 | card | categorical | held |  |
| Reviewer | R2-13 +1 and +2 within 1 point | Shift test | 8593 | 6390-9184 | card | wall | missed | 2.7 points apart |
| Reviewer | R2-13 +0 slowest | Shift test | 8594 | 6390-9184 | card | categorical | held |  |
| Reviewer | R2-14 best robust ratio +0 | Shift test | 8595 | 6390-9184 | card | categorical | held |  |
| Reviewer | R2-15 +3 official | Run A shift-past-2 | 8723 | 6390-9184 | card | priced | held |  |
| Reviewer | R2-15 +3 ruint | Run A shift-past-2 | 8724 | 6390-9184 | card | priced | held |  |
| Reviewer | R2-15 +3 Montgomery | Run A shift-past-2 | 8725 | 6390-9184 | card | priced | missed | above by 0.0013 |
| Reviewer | R2-15 +3 wall | Run A shift-past-2 | 8726 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-15 +2 stays best wall | Run A shift-past-2 | 8727 | 6390-9184 | card | categorical | held | by its stated 0.5-point condition; point estimates tied |
| Reviewer | R2-16 no rest sub-region > 25 us | Run A shift-past-2 | 8728 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-17 conjunction (6 clauses) | Run B shift-72-84 | 8756 | 6390-9184 | card | categorical | missed | clause cells 8752-8754: 3 held / 3 missed (official best at +0: missed 72, missed 84; wall best +1/+2: held 72, held 84; +1 better under all three: missed 72, held 84). Counted once as the conjunction. |
| Reviewer | R2-18 wall 72 | 2b-sizes | 9060 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-18 wall 84 | 2b-sizes | 9061 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-19 faster at both sizes | 2b-sizes | 9062 | 6390-9184 | card | categorical | held |  |
| Reviewer | R2-20 sv:free2 size | 2b-sizes | 9063 | 6390-9184 | card | wall | held |  |
| Reviewer | R2-20 largest sub-region | 2b-sizes | 9064 | 6390-9184 | card | categorical | missed | on the committed "absolute" definition |
| Reviewer | R2-18 priced clauses | 2b-sizes | 9079 | 6390-9184 | card | priced | info only | time-order ruling |
| DeepSeek | D1 | on-demand A | 2146 | 700-4300 | unsplit | priced | missed | ruint/Montgomery alone in range |
| DeepSeek | D2 | on-demand A | 2147 | 700-4300 | unsplit | other | held | polynomials per run |
| DeepSeek | D3 | re-solve, corrected card | 2323 | 700-4300 | unsplit | categorical | held | "not scored" at 2148; scored here |
| DeepSeek | D4 | re-solve, corrected card | 2327 | 700-4300 | unsplit | categorical | missed | ECM-off clauses held at 72-84 |
| DeepSeek | D5 | re-solve, corrected card | 2328 | 700-4300 | unsplit | priced | missed |  |
| DeepSeek | size trend (mc, lc up, kc down) | qs-gene size scaling | 2565 | 700-4300 | unsplit | categorical | missed |  |
| DeepSeek | D-a1 | p-1 map check | 2807 | 700-4300 | unsplit | categorical | missed | post hoc |
| DeepSeek | D-a2 | p-1 map check | 2808 | 700-4300 | unsplit | categorical | missed | post hoc |
| DeepSeek | D-a3 | p-1 map check | 2809 | 700-4300 | unsplit | categorical | held | post hoc |
| DeepSeek | D-b1 | kc / lc bound round | 3028 | 700-4300 | unsplit | other | missed |  |
| DeepSeek | D-b2 | kc / lc bound round | 3029 | 700-4300 | unsplit | other | missed |  |
| DeepSeek | D-b3 | kc / lc bound round | 3030 | 700-4300 | unsplit | priced | missed | gain % |
| DeepSeek | D-c1 | kc / lc bound round | 3031 | 700-4300 | unsplit | other | missed | "neither above 2.2" clause held |
| DeepSeek | D-k | kc / lc bound round | 3032 | 700-4300 | unsplit | other | missed |  |
| DeepSeek | D-rep | replacement-rule test | 3351 | 700-4300 | unsplit | categorical | missed |  |
| DeepSeek | D-ecmadd | ECM additions charged | 3578 | 700-4300 | unsplit | priced | missed | PD_M clause deferred |
| DeepSeek | D-sweep | slack sweep | 3691 | 700-4300 | unsplit | other | missed | post hoc |
| DeepSeek | D-pinv | pool-prime inverses | 3800 | 700-4300 | unsplit | priced | missed | counts (A's per run) and net saving |
| DeepSeek | D-qr | large-prime simulation | 3875 | 700-4300 | unsplit | other | missed | matched-definition re-score 4049: MISSED |
| DeepSeek | D-cc | clean check | 3884 | 700-4300 | unsplit | other | info only | scored post hoc "missed" at 3884/4057; withdrawn to PENDING at 4081 |
| DeepSeek | D-rm | re-sieve vs full pass | 3935 | 700-4300 | unsplit | priced | missed |  |
| DeepSeek | D-rm2 | re-sieve vs full pass | 3936 | 700-4300 | unsplit | priced | missed |  |
| DeepSeek | D-gc | Gray-code re-typing | 4230 | 700-4300 | unsplit | priced | missed | official 0% clause held; 54-bit falsifier fires but recorded "missed" |
| DeepSeek | D-gc54 | Gray-code re-typing | 4231 | 700-4300 | unsplit | priced | held | slack clause deferred |
| DeepSeek | D-ledger | Ledger correction, predictions scored as written | 4465 | 4300-6390 | unsplit | priced | missed | main ranges missed; hash-implementation ranges partly in; not falsified |
| DeepSeek | (c) stage-1-only makes 'ECM never chosen' an artifact | ECM stage-2 DP (Mathematica) | 4559 | 4300-6390 | unsplit | categorical | held |  |
| DeepSeek | D-audit | Audit re-typing items 0-8: predictions scored | 5052 | 4300-6390 | unsplit | priced | falsified | FALSIFIED (ruint and Montgomery outside tolerance at every size; hash and sort > 3x) |
| DeepSeek | F2 | Wolfram cross-check 2: exact smoothness | 5611 | 4300-6390 | unsplit | other | falsified | 'refuted' (threshold selection does not explain slope > 1) |
| DeepSeek | F1 | Wolfram cross-check 2: exact smoothness | 5616 | 4300-6390 | unsplit | other | held | extra 0.4-0.9; narrowed at 5643 to 'holds at 72-96 only' |
| DeepSeek | G3 | Wolfram: tilted saddle-point model vs 1,219 relations | 5643 | 4300-6390 | unsplit | other | missed | KS raises sum 2/p by 0.1-0.3 (measured 0.54-0.61) |
| DeepSeek | I-022 (a) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | missed | same caveat |
| DeepSeek | I-022 (b) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | missed | outside range, inside its 10-40% falsification bounds |
| DeepSeek | I-022 (c) | I-022 tilted-score test (Wolfram), first scoring | 5694 | 4300-6390 | unsplit | other | falsified | 'missed', and 'DeepSeek's falsifier < 2% fired' |
| DeepSeek | J4a | k=1 calibration and exact-rho check (J4) | 5713 | 4300-6390 | unsplit | other | held | 72 bits marginally under |
| DeepSeek | J4b | k=1 calibration and exact-rho check (J4) | 5713 | 4300-6390 | unsplit | categorical | held |  |
| DeepSeek | J4c | k=1 calibration and exact-rho check (J4) | 5713 | 4300-6390 | unsplit | other | held |  |
| DeepSeek | D-P1 | Step 1: fills deleted - scored | 5749 | 4300-6390 | unsplit | priced | held |  |
| DeepSeek | G4 | Step 1: touched-entry predictions, post hoc | 5771 | 4300-6390 | unsplit | other | falsified | post hoc (measurement existed); falsified on either definition |
| DeepSeek | K1 | Fixed I-022 re-run (K1-K4) | 5783 | 4300-6390 | unsplit | other | held | 'K1-K3 held for both' (5958) |
| DeepSeek | K2 | Fixed I-022 re-run (K1-K4) | 5784 | 4300-6390 | unsplit | other | held |  |
| DeepSeek | K3 | Fixed I-022 re-run (K1-K4) | 5785 | 4300-6390 | unsplit | other | held |  |
| DeepSeek | K4 | Fixed I-022 re-run (K1-K4) | 5786 | 4300-6390 | unsplit | other | falsified | divided by the untilted 1.5; tilted factor ~1.74 (accepted 5790) |
| DeepSeek | D-P5 | Step 3: hash banding | 5831 | 4300-6390 | unsplit | other | held | 1.3-1.8x |
| DeepSeek | H1 | KS hypotheses H1-H3 (scored 'this morning') | 5958 | 4300-6390 | unsplit | categorical | held | 'DeepSeek right' (5675, 5958); an explanation, not a sealed range |
| DeepSeek | H3 | KS hypotheses H1-H3 (scored 'this morning') | 5958 | 4300-6390 | unsplit | categorical | falsified | 'DeepSeek refuted' (5958); 'H3's density reason wrong' (5675) |
| DeepSeek | P3 | Duplicate-polynomial test (Wolfram) | 5992 | 4300-6390 | unsplit | other | info only | VOID (premise an artefact) |
| DeepSeek | N1 fourth candidate (shared A-prime overdispersion) | Duplicate-polynomial test (Wolfram) | 5992 | 4300-6390 | unsplit | categorical | falsified | 'refuted'; a hypothesis, not a sealed range; accepted 5997 |
| DeepSeek | Q2 (small penalty, not more than a few %) | Duplicate relations between polynomial pairs (Wolfram) | 6012 | 4300-6390 | unsplit | other | held | 'is consistent' (6012); 'holds (~3% at 72 bits)' (6016); qualitative |
| DeepSeek | D-P7 speed-up (72-96) | Step 4: gray flat layout | 6069 | 4300-6390 | unsplit | wall | held | sub-clause: 1.76-1.92x |
| DeepSeek | D-P7 speed-up (54) | Step 4: gray flat layout | 6069 | 4300-6390 | unsplit | wall | missed | sub-clause: above range (2.2-2.7x); NOTES says 'above it', no verdict word -> read as missed |
| DeepSeek | U2 | I-027 elasticities by finite difference (Wolfram) | 6128 | 4300-6390 | unsplit | other | falsified | '-2 to -3' claim falsified at every size; owned by DeepSeek (6133) |
| DeepSeek | kappa_eff 1.3-1.7 | I-027 check of DeepSeek's V1 closed form (Wolfram) | 6162 | 4300-6390 | unsplit | other | missed | 1.87 |
| DeepSeek | W3 (ii) | I-027/I-028 large-prime bound scan (Wolfram), W3 | 6184 | 4300-6390 | unsplit | other | missed | 1.2%; falsifiers not triggered |
| DeepSeek | W3 (iii) | I-027/I-028 large-prime bound scan (Wolfram), W3 | 6185 | 4300-6390 | unsplit | other | missed | ratio 0.66 vs < 0.6; 'missed narrowly' |
| DeepSeek | X1 exponent 1.2-1.5 | I-028 best L against run length (Wolfram) | 6207 | 4300-6390 | unsplit | other | falsified | 'refuted' (alpha 0.73-0.75); 'X1 refuted on all clauses' (6222) |
| DeepSeek | X1 best L grows with P | I-028 best L against run length (Wolfram) | 6215 | 4300-6390 | unsplit | categorical | falsified | 'refuted (both)' |
| DeepSeek | X1 P lambda_L ~ 1 at optimum | I-028 best L against run length (Wolfram) | 6216 | 4300-6390 | unsplit | other | falsified | 'refuted' (~0.21) |
| DeepSeek | Y3 | I-028 finer L grid (Wolfram), Y3 | 6237 | 4300-6390 | unsplit | categorical | falsified | best on grid 8 (its >= 8 clause); true minimum 12 |
| DeepSeek | Z3 | DeepSeek round 29, Z3 | 6243 | 4300-6390 | unsplit | other | held | inside; 'weak test': sealed with two of three cost curves in hand |
| DeepSeek | D-P3 | Step 5: wall-clock re-run with two anchors | 6326 | 4300-6390 | unsplit | wall | falsified | < 45 at 54, 84, 96 |
| DeepSeek | D-P4 | Step 5: wall-clock re-run with two anchors | 6327 | 4300-6390 | unsplit | wall | missed |  |
| DeepSeek | D-P6 | Step 5: wall-clock re-run with two anchors | 6328 | 4300-6390 | unsplit | wall | missed |  |
| DeepSeek | D-P7 | Step 5: wall-clock re-run with two anchors | 6329 | 4300-6390 | unsplit | wall | missed | 'missed on both clauses' |
| DeepSeek | U3 (84) | Step 5: wall-clock re-run with two anchors | 6335 | 4300-6390 | unsplit | priced | held | post hoc (data existed in committed outputs); solve ruint share |
| DeepSeek | U3 (96) | Step 5: wall-clock re-run with two anchors | 6335 | 4300-6390 | unsplit | priced | missed | post hoc; not falsified |
| DeepSeek | V3 | Step 5: wall-clock re-run with two anchors | 6339 | 4300-6390 | unsplit | priced | held | post hoc; setup/(sieve+confirm) ruint |
| DeepSeek | X3 (never-combined share 62-86%) | Step 7b X3 on the card | 6405 | 6390-9184 | card | other | held |  |
| DeepSeek | R-L1 polynomials | Step 7c L test | 6432 | 6390-9184 | card | other | falsified |  |
| DeepSeek | R-L2 stored partials | Step 7c L test | 6433 | 6390-9184 | card | other | missed | AMBIGUOUS: table says missed; addendum 6558 says DeepSeek's R-L1/L2/L3 falsified. Table used. |
| DeepSeek | R-L3 priced ruint mean | Step 7c L test | 6434 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | R-L4 wall total | Step 7c L test | 6435 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | R-L4 lp_ledger | Step 7c L test | 6436 | 6390-9184 | card | wall | held |  |
| DeepSeek | round-31 direction: e_F "modestly lower" than 0.45 | Light meter at the card's point (Wolfram) | 6486 | 6390-9184 | model | categorical | missed | NOTES: "wrong" |
| DeepSeek | round-31 direction: e_M "materially lower" than 0.71 | Light meter at the card's point (Wolfram) | 6486 | 6390-9184 | model | categorical | missed | NOTES: "wrong" |
| DeepSeek | R-F1 polynomials | Step 8 F test | 6547 | 6390-9184 | card | other | held |  |
| DeepSeek | R-F2 solve share (priced) | Step 8 F test | 6548 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | R-F3 total priced ruint | Step 8 F test | 6549 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | S9-1 (falsifier only) | Stage B step 9 | 6849 | 6390-9184 | card | other | not falsified | DeepSeek's S9-1..S9-5 ranges = the reviewer's (recorded as agreement, 6676-6677); only falsifiers scored |
| DeepSeek | S9-2 (falsifier only) | Stage B step 9 | 6850 | 6390-9184 | card | other | not falsified | table cell says "held" on its falsifier bounds 0.12-0.55; summary 6974 counts it among "the rest not [falsified]" |
| DeepSeek | S9-3 low band (falsifier only) | Stage B step 9 | 6851 | 6390-9184 | card | other | not falsified |  |
| DeepSeek | S9-3 high band (falsifier only) | Stage B step 9 | 6852 | 6390-9184 | card | other | not falsified |  |
| DeepSeek | S9-4 (falsifier only) | Stage B step 9 | 6853 | 6390-9184 | card | other | not falsified | table cell "held" on falsifier bounds |
| DeepSeek | S9-5 (falsifier only) | Stage B step 9 | 6854 | 6390-9184 | card | other | not falsified |  |
| DeepSeek | S9-6 (independent range) | Stage B step 9 | 6855 | 6390-9184 | card | other | held | "at the edge" |
| DeepSeek | S9-7 | Stage B step 9 | 6856 | 6390-9184 | card | other | falsified |  |
| DeepSeek | S9-8 | Stage B step 9 | 6857 | 6390-9184 | card | categorical | falsified |  |
| DeepSeek | S9-9 | Stage B step 9 | 6858 | 6390-9184 | card | other | missed | not falsified |
| DeepSeek | R-G1 priced ruint, re-sieve on F x1.3 | Stage E 2x2 | 6900 | 6390-9184 | card | priced | held |  |
| DeepSeek | R-G2 confirm wall-clock | Stage E 2x2 | 6901 | 6390-9184 | card | wall | missed | not falsified |
| DeepSeek | M3 at 84 (card fulls / model fulls) | Stage F step 6 | 6934 | 6390-9184 | card | other | missed |  |
| DeepSeek | M3 at 96 | Stage F step 6 | 6934 | 6390-9184 | card | other | falsified |  |
| DeepSeek | G-1 -4 bits (stage G) | DeepSeek round 41 vs stage G | 7157 | 6390-9184 | card | other | info only | filed after the results commit (7123); "in range" |
| DeepSeek | G-2 -4 bits (stage G) | DeepSeek round 41 vs stage G | 7158 | 6390-9184 | card | other | info only | in range |
| DeepSeek | G-3 -4 bits (stage G) | DeepSeek round 41 vs stage G | 7159 | 6390-9184 | card | other | info only | in range |
| DeepSeek | G-4 -4 bits (stage G) | DeepSeek round 41 vs stage G | 7160 | 6390-9184 | card | priced | info only | outside (high) |
| DeepSeek | G-5 -4 bits (stage G) | DeepSeek round 41 vs stage G | 7161 | 6390-9184 | card | wall | info only | outside (high) |
| DeepSeek | G-1 -2 bits (stage G) | DeepSeek round 41 vs stage G | 7162 | 6390-9184 | card | other | info only | in range |
| DeepSeek | G-2 -2 bits (stage G) | DeepSeek round 41 vs stage G | 7163 | 6390-9184 | card | other | info only | in range |
| DeepSeek | G-1 -6 bits (stage G) | DeepSeek round 41 vs stage G | 7164 | 6390-9184 | card | other | info only | in range |
| DeepSeek | G-2 -6 bits (stage G) | DeepSeek round 41 vs stage G | 7165 | 6390-9184 | card | other | info only | in range |
| DeepSeek | H-1 | Stage H | 7687 | 6390-9184 | card | other | held |  |
| DeepSeek | H-2 per polynomial | Stage H | 7688 | 6390-9184 | card | other | held | sub-clause 1 of 2; at the edge |
| DeepSeek | H-2 per number | Stage H | 7688 | 6390-9184 | card | other | held | sub-clause 2 of 2 |
| DeepSeek | H-3 | Stage H | 7689 | 6390-9184 | card | other | held |  |
| DeepSeek | H-4 | Stage H | 7690 | 6390-9184 | card | priced | missed | not falsified |
| DeepSeek | H-5 | Stage H | 7691 | 6390-9184 | card | other | held |  |
| DeepSeek | H-6 | Stage H | 7692 | 6390-9184 | card | other | missed | not falsified |
| DeepSeek | H-7 | Stage H | 7693 | 6390-9184 | card | other | held |  |
| DeepSeek | H-8 | Stage H | 7694 | 6390-9184 | card | other | missed | not falsified |
| DeepSeek | H-9 | Stage H | 7695 | 6390-9184 | card | priced | held |  |
| DeepSeek | H-10 | Stage H | 7696 | 6390-9184 | card | wall | missed | not falsified |
| DeepSeek | H-11 | Stage H | 7697 | 6390-9184 | card | other | held | at the edge |
| DeepSeek | H-12 per number | Stage H | 7698 | 6390-9184 | card | other | held | sub-clause 1 of 2 |
| DeepSeek | H-12 per polynomial | Stage H | 7698 | 6390-9184 | card | other | held | sub-clause 2 of 2 |
| DeepSeek | H-13 | Stage H | 7699 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | H-14 | Stage H | 7700 | 6390-9184 | card | priced | held |  |
| DeepSeek | H-15 | Stage H | 7701 | 6390-9184 | card | other | held |  |
| DeepSeek | H-16 | Stage H | 7702 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | H-17 | Stage H | 7703 | 6390-9184 | card | priced | missed | not falsified |
| DeepSeek | H-18 | Stage H | 7704 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | I-029a (b) | I-029 microbenchmark | 7905 | 6390-9184 | card | wall | missed | not falsified |
| DeepSeek | I-029a (c) | I-029 microbenchmark | 7905 | 6390-9184 | card | wall | held |  |
| DeepSeek | I-029b (b) | I-029 microbenchmark | 7906 | 6390-9184 | card | wall | missed | not falsified |
| DeepSeek | I-029b (c) | I-029 microbenchmark | 7906 | 6390-9184 | card | wall | held |  |
| DeepSeek | R-5 candidates-closest shift | DeepSeek round 59 | 7998 | 6390-9184 | card | categorical | info only | "recorded as information only, not sealed" |
| DeepSeek | R-1 root alone wall | Root confirm | 8039 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | R-2 | Root confirm | 8040 | 6390-9184 | card | priced | held |  |
| DeepSeek | R-3 | Root confirm | 8041 | 6390-9184 | card | categorical | held |  |
| DeepSeek | R-4 | Root confirm | 8042 | 6390-9184 | card | wall | falsified |  |
| DeepSeek | D-1 official | I-032 option 2' | 8442 | 6390-9184 | card | priced | held |  |
| DeepSeek | D-2 ruint/Montgomery | I-032 option 2' | 8443 | 6390-9184 | card | priced | held |  |
| DeepSeek | D-3 wall | I-032 option 2' | 8444 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-4 2'b o/r/m | I-032 option 2' | 8445 | 6390-9184 | card | priced | held | all three |
| DeepSeek | D-5 wall | I-032 option 2' | 8446 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-6 sieve | I-032 option 2' | 8447 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-7 interval | I-032 option 2' | 8448 | 6390-9184 | card | interval width | missed | sealed without the cap |
| DeepSeek | D-8 official | I-032 option 2' | 8450 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | D-8 ruint | I-032 option 2' | 8451 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | D-8 Montgomery | I-032 option 2' | 8452 | 6390-9184 | card | priced | falsified |  |
| DeepSeek | D-8 wall | I-032 option 2' | 8453 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-9 better under all three | I-032 option 2' | 8454 | 6390-9184 | card | categorical | falsified |  |
| DeepSeek | D-10 same direction as G-6 | I-032 option 2' | 8474 | 6390-9184 | card | priced | info only | model committed first; NOTES also writes "missed" |
| DeepSeek | D-11 rest excess phase | pp3 breakdown (unscored) | 8536 | 6390-9184 | card | wall | info only | breakdown seen first |
| DeepSeek | shift table +0 o/r/m/wall | Shift test | 8601 | 6390-9184 | card | mixed (priced+wall) | held |  |
| DeepSeek | shift table +1 official | Shift test | 8602 | 6390-9184 | card | priced | missed |  |
| DeepSeek | shift table +1 ruint/Montgomery/wall | Shift test | 8603 | 6390-9184 | card | mixed (priced+wall) | held |  |
| DeepSeek | shift table +2 official | Shift test | 8604 | 6390-9184 | card | priced | missed |  |
| DeepSeek | shift table +2 ruint/Montgomery/wall | Shift test | 8605 | 6390-9184 | card | mixed (priced+wall) | held |  |
| DeepSeek | D-12 best wall +2 | Shift test | 8606 | 6390-9184 | card | categorical | held |  |
| DeepSeek | D-12 "+1 within ~1 point" | Shift test | 8607 | 6390-9184 | card | wall | missed |  |
| DeepSeek | D-13 best robust +1 | Shift test | 8608 | 6390-9184 | card | categorical | falsified |  |
| DeepSeek | D-14 most: lp_ledger | Shift test, rest split | 8648 | 6390-9184 | card | categorical | missed | "on the point estimate (tied within noise)" |
| DeepSeek | D-14 size 50-70 us | Shift test, rest split | 8649 | 6390-9184 | card | wall | falsified | missed; falsifier row 8651 (lp_ledger < 30 us) triggered -> merged here |
| DeepSeek | D-14 second: solve 10-20 us | Shift test, rest split | 8650 | 6390-9184 | card | wall | missed | "missed / missed" split |
| DeepSeek | D-14 third: setup 5-15 us | Shift test, rest split | 8650 | 6390-9184 | card | wall | missed |  |
| DeepSeek | D-15 wall 72 | 2b-sizes | 9065 | 6390-9184 | card | wall | held | "held / held" split |
| DeepSeek | D-15 wall 84 | 2b-sizes | 9065 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-16 faster at both sizes | 2b-sizes | 9066 | 6390-9184 | card | categorical | held |  |
| DeepSeek | D-17 sv:free2 size | 2b-sizes | 9067 | 6390-9184 | card | wall | held |  |
| DeepSeek | D-17 largest | 2b-sizes | 9068 | 6390-9184 | card | categorical | falsified | missed; falsifier triggered |
| DeepSeek | D-15 priced clauses | 2b-sizes | 9083 | 6390-9184 | card | priced | info only | time-order ruling |
| Grok | G1 | re-solve, corrected card | 2324 | 700-4300 | unsplit | categorical | held |  |
| Grok | G3 | re-solve, corrected card | 2326 | 700-4300 | unsplit | categorical | info only | "not triggered" |
| Grok | G-a | p-1 map check | 2820 | 700-4300 | unsplit | categorical | missed | post hoc; not independent of the user's P1-P2 |
| Grok | G-b1 | kc / lc bound round | 3034 | 700-4300 | unsplit | other | missed | lc and "no size loses > 2%" clauses held |
| Grok | G-b2 | kc / lc bound round | 3036 | 700-4300 | unsplit | other | missed | kc clause held; ECM missed at 54 |
| Grok | G-p1 | kc / lc bound round | 3037 | 700-4300 | unsplit | other | held |  |
| Grok | G-rep | replacement-rule test | 3353 | 700-4300 | unsplit | categorical | missed |  |
| Grok | G-rep2 | replacement-rule test | 3354 | 700-4300 | unsplit | priced | missed | 0 of 24 cells held (one row here) |
| Grok | G-reref | reference change check | 3426 | 700-4300 | unsplit | categorical | held |  |
| Grok | G-ecmadd | ECM additions charged | 3579 | 700-4300 | unsplit | priced | missed | cost clause held at 54-84 |
| Grok | G-slack | slack sweep | 3659 | 700-4300 | unsplit | other | missed | post hoc; shape reversed |
| Grok | G-slack REVISED, ruint/Montgomery | slack sweep | 3700 | 700-4300 | unsplit | other | held | post hoc; split sub-clause |
| Grok | G-slack REVISED, official | slack sweep | 3700 | 700-4300 | unsplit | other | missed | post hoc; split sub-clause |
| Grok | G-pinv | pool-prime inverses | 3816 | 700-4300 | unsplit | priced | falsified | post hoc; "missed (falsified)" |
| Grok | G-qr | large-prime simulation | 3874 | 700-4300 | unsplit | other | falsified | first HOLDS (3874); flipped to FALSIFIED on matched definition (4050, 4054) and on column A (4070) |
| Grok | G-rm | re-sieve vs full pass | 3937 | 700-4300 | unsplit | priced | missed | revision recorded, original scored |
| Grok | G-gc54 | Gray-code re-typing | 4232 | 700-4300 | unsplit | priced | held | also 4082; slack clause deferred |
| Grok | G-gc | Gray-code re-typing | 4233 | 700-4300 | unsplit | priced | falsified | corrected Oct 26 from "missed" |
| Grok | G-ledger | Ledger correction, predictions scored as written | 4468 | 4300-6390 | unsplit | priced | falsified | 'missed ... and falsified' by its official < 0.3% clause |
| Grok | G-ledger2 | Ledger correction, predictions scored as written | 4469 | 4300-6390 | unsplit | priced | falsified | 'missed; falsified by its ratio clause' (4472); clause flagged mis-specified in advance |
| Grok | Q1 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4618 | 4300-6390 | unsplit | categorical | missed | rho returns at all sizes at 2^12-2^16; 'failed' |
| Grok | Q3 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4618 | 4300-6390 | unsplit | other | missed | ECM at 96 under 1-2 priors, gain 1.5-4.5%; 'failed' (3 of 3 priors, 4.75-7.35%) |
| Grok | Q4 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4618 | 4300-6390 | unsplit | categorical | held | no ECM at 84 |
| Grok | Q6 | Corrected stage-2 DP (Mathematica), sealed Oct 26 | 4618 | 4300-6390 | unsplit | other | missed | p-1 bound; 'failed (2^7-2^9, below its 2^9 floor at 72 and 84)'; its stated falsifier (outside 2^9-2^16) was crossed but NOTES says 'failed', not 'falsified' |
| Grok | GP1 | Word-price calibration (opbench --audit) | 4654 | 4300-6390 | unsplit | other | missed | clean/old word price 0.759 vs 0.60-0.75; not falsified (re-stated 4817) |
| Grok | M1 | Real-prime measurement run (Mathematica), M1-M6 | 4770 | 4300-6390 | unsplit | other | missed | p-1 Dickman divisor c 3-4 (measured 1.41/1.83); 'failed'; sealed in outside chats, not registered in NOTES before the run |
| Grok | M2 | Real-prime measurement run (Mathematica), M1-M6 | 4771 | 4300-6390 | unsplit | other | missed | 'both failed at every size'; M2's text not in NOTES |
| Grok | M3 | Real-prime measurement run (Mathematica), M1-M6 | 4772 | 4300-6390 | unsplit | other | missed | 'failed all three' |
| Grok | M4 | Real-prime measurement run (Mathematica), M1-M6 | 4773 | 4300-6390 | unsplit | other | missed | 0.918 > 0.90 |
| Grok | M6 | Real-prime measurement run (Mathematica), M1-M6 | 4777 | 4300-6390 | unsplit | other | missed | failed at all sizes |
| Grok | R1 (72, 84) | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | missed | stage 2 in optimum: Grok said no at 72/84 |
| Grok | R1 (96) | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | held | sub-clause |
| Grok | R3 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | stage-2 saving (model); 'far above' |
| Grok | R4 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | categorical | missed | rho return pattern |
| Grok | R5 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | ECM priors and gain |
| Grok | R6 | Measured-c stage-2 DP (Mathematica), R1-R6 | 4842 | 4300-6390 | unsplit | other | missed | fixed/optimum gap < 2%; 'failed narrowly' (1.023) |
| Grok | W2 | W-set (benchmark array), post hoc | 4929 | 4300-6390 | unsplit | categorical | missed | post hoc (array comparison committed before the prediction) |
| Grok | A1 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | other | held | A1's text not in NOTES |
| Grok | A2 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | other | missed | ECM at 96: priors and gain; 'failed' |
| Grok | A3 | Honest-price ECM DP (Mathematica), A1-A3 | 4942 | 4300-6390 | unsplit | categorical | missed | no rho at 72 or 84 |
| Grok | C1 | C-set (card's rho variant), post hoc | 4971 | 4300-6390 | unsplit | categorical | held | post hoc (code answer committed before) |
| Grok | W1 | Audit re-typing items 0-8: predictions scored | 5049 | 4300-6390 | unsplit | priced | held | ruint change -18.1/-12.4/-10.0% |
| Grok | G-audit ranges | Audit re-typing items 0-8: predictions scored | 5051 | 4300-6390 | unsplit | priced | held | held at every size under ruint and Montgomery |
| Grok | G-audit benchmark expectation | Audit re-typing items 0-8: predictions scored | 5051 | 4300-6390 | unsplit | categorical | missed | 'only the double divide above 3x'; hash, sort, log also > 3x |
| Grok | GP2 | Wall-clock per phase (GP2) | 5102 | 4300-6390 | unsplit | wall | missed | gray flags at every size; falsifier did not fire |
| Grok | G-1 o/r/m | I-032 option 2' | 8460 | 6390-9184 | card | priced | held |  |
| Grok | G-1 wall | I-032 option 2' | 8461 | 6390-9184 | card | wall | missed |  |
| Grok | G-2 o/r/m | I-032 option 2' | 8462 | 6390-9184 | card | priced | held |  |
| Grok | G-2 wall | I-032 option 2' | 8463 | 6390-9184 | card | wall | held | sub-clause 1 of 2 ("held / held") |
| Grok | G-2 sieve | I-032 option 2' | 8463 | 6390-9184 | card | wall | held | sub-clause 2 of 2 |
| Grok | G-3 official | I-032 option 2' | 8464 | 6390-9184 | card | priced | missed |  |
| Grok | G-3 ruint/Montgomery/wall | I-032 option 2' | 8465 | 6390-9184 | card | mixed (priced+wall) | held |  |
| Grok | G-4 better under all three | I-032 option 2' | 8466 | 6390-9184 | card | categorical | missed |  |
| Grok | G-5 interval full width | I-032 option 2' | 8467 | 6390-9184 | card | interval width | missed | 2 of 4 inside |
| Grok | G-6 2'b official from model | I-032 option 2' | 8473 | 6390-9184 | card | priced | info only | model committed first; NOTES also writes "missed" |
| Grok | shift table +0 o/r/m/wall | Shift test | 8614 | 6390-9184 | card | mixed (priced+wall) | held |  |
| Grok | shift table +1 official | Shift test | 8615 | 6390-9184 | card | priced | missed |  |
| Grok | shift table +1 ruint/Montgomery/wall | Shift test | 8616 | 6390-9184 | card | mixed (priced+wall) | held |  |
| Grok | shift table +2 official | Shift test | 8617 | 6390-9184 | card | priced | missed |  |
| Grok | shift table +2 ruint/Montgomery | Shift test | 8618 | 6390-9184 | card | priced | held |  |
| Grok | shift table +2 wall | Shift test | 8619 | 6390-9184 | card | wall | missed | larger saving |
| Grok | Best wall +2 | Shift test | 8620 | 6390-9184 | card | categorical | held |  |
| Grok | Best robust ratio +0 | Shift test | 8621 | 6390-9184 | card | categorical | held | its stated reason is not the mechanism; contradicts its own table (pp3-gap-and-shift.md:125) |
| Grok | G-7 most: lp_ledger | Shift test, rest split | 8652 | 6390-9184 | card | categorical | missed | on the point estimate |
| Grok | G-7 size 45-70 us | Shift test, rest split | 8653 | 6390-9184 | card | wall | missed | falsifier (two conditions) not triggered (8654) |
| Grok | Grok's phase pick | pp3 breakdown (unscored) | 8656 | 6390-9184 | card | wall | info only | breakdown seen first |
| Grok | G-8 wall 72 | 2b-sizes | 9069 | 6390-9184 | card | wall | held |  |
| Grok | G-8 wall 84 | 2b-sizes | 9070 | 6390-9184 | card | wall | falsified | missed (9070); falsifier row 9071 triggered by 84's -12.9% -> merged here |
| Grok | G-9 faster at both sizes | 2b-sizes | 9072 | 6390-9184 | card | categorical | held |  |
| Grok | G-10 sv:free2 size | 2b-sizes | 9073 | 6390-9184 | card | wall | held |  |
| Grok | G-10 largest | 2b-sizes | 9074 | 6390-9184 | card | categorical | falsified | missed; falsifier triggered |
| Grok | G-8 priced clauses | 2b-sizes | 9084 | 6390-9184 | card | priced | info only | time-order ruling |