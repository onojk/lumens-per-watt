# 2b-sizes: 2′b alone at 72 and 84 bits; 2′b against 2′b+pp3 at 96 with the sieve breakdown: predictions

**Run:** `tools/sealed_run.sh 2b-sizes -- bash -c "cd evolve && python3 shiftrun.py C"` (the runner is prepared after this file; its commit is named below before "go").
- **72 and 84 bits:** 2′a (the base) against 2′b alone (goff on, root), all map numbers (480, 560).
- **96 bits:** 2′b (the base) against 2′b+pp3 at +0, all 640 map numbers.
- 8 wall-clock replicates per size in seeded random orders; the new clock options (period 0.05 s, skip_launch; inner as set in the runner); cap 2.4 GHz (the user's standing cap; checked before "go").
- At 96, the wall replicates run with `LAMPCORE_SIEVEBREAK` off, then one `LAMPCORE_SIEVEBREAK=1` pass per cell (NOTES, "Sieve breakdown").

## The reviewer's (verbatim; base 2′a unless stated)

      R2-18 2'b vs 2'a: official 72: 1.04 to 1.10; 84: 1.02 to 1.07. ruint 72: 0.89 to 0.94;
            84: 0.87 to 0.92. Montgomery within 0.01 below ruint at each size. Wall 72: -8% to
            -13%; 84: -9% to -14%.
      R2-19 2'b is faster than 2'a on wall at both sizes, with 95% intervals excluding zero
            (80%).
      R2-20 At 96, sv:free2 accounts for 30 to 55 us per number of 2'b+pp3's sieve excess over
            2'b, and is the largest single sieve sub-region difference.

## Time order (Claude Code's record)

- **The brief with R2-18..R2-20 was received before any count was computed.**
- **While preparing the cost note** (item 1 of the same brief), Claude Code ran a count pass (`run_many --types`, no timing). Besides the pp 3 cells, it included 2′b at 72 and 84, and so **printed 2′b's priced totals at 72 and 84** (the quantities R2-18's priced ranges predict). The cost note did not need them.
- **R2-18's priced clauses are therefore deterministic and were seen by Claude Code before this file was committed.** The reviewer had not seen them, and Claude Code has not relayed them. Wall-clock (R2-18's wall clauses, R2-19) and the 96-bit breakdown (R2-20) are unmeasured.
- Whether R2-18's priced clauses count as sealed is the user's call.

## DeepSeek (received 01:39 Oct 27 PT)

- **D-15, D-16 and D-17: sealed.** The 2b-sizes run has not started, and its runner is not yet prepared.
- **Its section 2 (whether to charge the free-2 pass): information only.** It is added to the cost note in NOTES.

### Its reply (verbatim)

<!-- verbatim begin -->
## 0. Recorded

- My second robust-rule view is recorded verbatim, with the reviewer's notes. The safeguards (fraction from op-class instruction counts, frozen before any 2'b run, never re-tuned; procedure → mechanical computation → publish, in that order) are accepted as the right order. The rule decision remains the user's; I am not treating this as a scored prediction.
- The pp3 finding is recorded: at 54–96 bits there are **no prime-power entries**, so pp3's only extra sieve work is the **free-2 stride-2 write**, which is **uncharged** because it falls under the width charge. The quick check (~40 µs per number at 96) and Run A's sieve excess (58–69 µs) are noted as pre-timed evidence, not a timed run.
- Clock sampling fix recorded: 72-bit flags were a launch-sample artifact; new options read 2,400 MHz with ~11 samples per pass and no flag.

## 1. Sealed predictions D-15, D-16, D-17

Registered before the 2b-sizes run. **Base is 2'a.** Ratios new/old; below 1 = cheaper. I state the assumption explicitly: I carry pp3's effect from 96 to 72/84 by inverting the 96-bit 2'b+pp3 → 2'b move, because no 72/84 2'b-only data exists. That is an **assumption**, not a transferred measurement.

### D-15: 2'b alone vs 2'a at 72 and 84

| Size | Official (range, central) | Ruint (range, central) | Montgomery (range, central) | Wall change (range, central) |
|---|---|---|---|---|
| **72** | 1.055–1.115 (1.085) | 0.900–0.945 (0.922) | 0.895–0.940 (0.915) | −8% to −13% (−10.5%) |
| **84** | 1.030–1.085 (1.055) | 0.880–0.920 (0.898) | 0.875–0.915 (0.891) | −9% to −14% (−11.5%) |

**Falsifier:** falsified at either size if official is outside its range, or if ruint or Montgomery is outside its range, or if wall is outside its range.

**Computed working, showing the inversion.**

At 96, pp3 changed 2'b by: official 0.9618 / 1.0137 = 0.94879; ruint 0.8703 / 0.8877 = 0.98040; wall (1 − 0.094) / (1 − 0.112) = 0.906 / 0.888 = 1.02027.

Inverting at 72: official 1.0289 / 0.94879 = 1.0844; ruint 0.9043 / 0.98040 = 0.9224; Montgomery 0.8971 / 0.98040 = 0.9150; wall 0.914 / 1.02027 = 0.8958 ⇒ −10.4%.

Inverting at 84: official 1.0020 / 0.94879 = 1.0561; ruint 0.8805 / 0.98040 = 0.8981; Montgomery 0.8740 / 0.98040 = 0.8915; wall 0.904 / 1.02027 = 0.8860 ⇒ −11.4%.

The ranges are widened by ±0.02 on ratios and ±2 points on wall for the size-transfer assumption and cross-run drift. **Missing parameter:** the 72/84 official per-number totals are not on the parameter sheet, so I cannot anchor D-15 official independently; the central is the inversion, and the range carries that uncertainty.

### D-16: is 2'b faster than 2'a on wall at both sizes with 95% intervals excluding zero?

| ID | Answer | Confidence | Falsifier |
|---|---|---|---|
| **D-16** | **Yes** | **85%** | Falsified if either size's 95% interval includes zero, or if either size's point estimate is non-negative |

**Reasoning:** at 96, 2'b wall is −11.2% with intervals excluding zero. The mechanism (root tests replacing divisions) is size-independent in direction; at 72/84 the confirm share of wall may be smaller, but my central −10.5%/−11.5% is far from zero. The 15% residual is for an unexpectedly small confirm share at 72, where fewer primes are tested.

### D-17: at 96, how much of 2'b+pp3's sieve excess does sv:free2 account for, and is it the largest?

| ID | Answer | Confidence | Falsifier |
|---|---|---|---|
| **D-17** | sv:free2 accounts for **30–55 µs** (central **42 µs**) of the 58–69 µs sieve excess; **yes**, it is the largest sieve sub-region difference | 70% | Falsified if sv:free2 is **<20 µs** or **>60 µs**, or if any other sieve sub-region (zero, prime, power, tail) is **larger than sv:free2** |

**Reasoning:** the finding says pp3 has no prime-power entries at these sizes, so sv:free2 is the only extra sieve work; it should therefore be the largest, and its measured quick-check ~40 µs sits inside the 58–69 µs excess. The range is widened because the quick check was 10 numbers, one pass, not a timed run.

## 2. Information only: should the free-2 pass be charged?

Yes, as a **meter correction**, not a re-pricing. The free-2 stride-2 write is a real operation the card performs and the meter misses because it falls under the width charge; charging it is a fix to **counting**, while re-pricing changes the price of an already-counted op. The caveat: first confirm the width charge was not calibrated to include initialization writes; if it was, the fix is to **split** the width charge (initialization vs clearing) rather than add a second charge, to avoid double-counting.

No sealed prediction is revised. D-15, D-16, D-17 are registered above.
<!-- verbatim end -->

### The reviewer's annotations (ranges unchanged)

- **Arithmetic checked:** all correct.
- **D-15 applies ruint's pp 3 factor to Montgomery** (an unstated assumption).
- **D-15 uses a cross-run wall factor:** −11.2% from run A against −9.4% from the shift run.
- **D-17 shares the reviewer's anchor** (the ~40 µs quick check), so it is not independent of R2-20.
- *Claude Code's note:* the time-order record above (2′b's priced totals at 72 and 84 were printed by Claude Code before this file was first committed) applies to D-15's priced clauses as well. DeepSeek had not seen them; they were not relayed.

## Grok (received 01:41 Oct 27 PT)

- **G-8, G-9 and G-10: sealed.** The 2b-sizes run has not started.
- **Its free-2 answer: information only.**

### Its reply (verbatim)

<!-- verbatim begin -->
**Sealed predictions (Grok, 27 Oct 2026 ~01:45 PT)**  
Using only the numbers supplied. Per-size candidate/polynomial counts, absolute wall times, and the exact free-2 contribution on the full 640 numbers are missing.

### G-8 — 2'b alone vs 2'a at 72 and 84 bits
(Assumption stated: the relative official/ruint movement seen when pp3 was added at 96 is used only as a rough bound; it is not assumed to transfer exactly.)

- **72 bits**  
  Official: 1.030–1.055  
  ruint: 0.910–0.935  
  Montgomery: 0.900–0.925  
  Wall: −7.0 % to −10.0 %

- **84 bits**  
  Official: 1.005–1.025  
  ruint: 0.890–0.910  
  Montgomery: 0.880–0.900  
  Wall: −8.0 % to −11.0 %

**Falsifier (single condition):** official ratio at either size falls below 1.000, or wall improvement at either size exceeds −12 %.

### G-9 — Is 2'b faster than 2'a on wall at both sizes, with 95 % intervals excluding zero?
**Yes** (confidence ~75 %).  
**Falsifier:** the 95 % interval on wall at either 72 or 84 bits includes zero or is positive.

### G-10 — At 96 bits, how many µs/number of 2'b+pp3's sieve excess over 2'b does sv:free2 account for, and is it the largest sieve sub-region difference?
**Range:** 35–55 µs/number.  
**Largest:** yes.  
**Falsifier:** sv:free2 accounts for ≤25 µs or some other single sub-region (zero, prime, power, or tail) accounts for more µs than free2.

---

**Information only:** Charging the free-2 pass is a meter correction (previously uncharged work that falls under the existing width charge), not a re-pricing of operations the meter already counts.
<!-- verbatim end -->

### The reviewer's annotations (ranges unchanged)

- **G-8's falsifier is an OR of two conditions, and narrower than its ranges.** The ranges are scored as predictions and the falsifier as written, separately.
- **G-8's official ranges sit below DeepSeek's D-15 and the reviewer's R2-18 at both sizes.** That is a real disagreement: Grok expects a smaller pp 3 effect at 72 and 84.
- **G-10 shares the ~40 µs quick-check anchor with D-17 and R2-20,** so it is not independent.
- *Claude Code's note:* the time-order record above applies to G-8's priced clauses as well. Grok had not seen 2′b's priced totals at 72 and 84, and they were not relayed.

## Runner, and scoring definitions for R2-20, D-17 and G-10 (Claude Code's, before the run)

- **Runner:** `evolve/shiftrun.py` mode C (the commit is named in the run record), smoke-tested on 4 numbers with output discarded.
  - Clock options: core-2 MHz every 0.05 s, the launch sample skipped; each cell timed 3 / 2 / 1 times back to back per replicate at 72 / 84 / 96 bits (ns averaged); seeds 2112, 2124, 2136.
  - Identity first. Priced and timed as in runs A and B: 72 and 84 against 2′a, 96 against 2′b.
- **"sv:free2 accounts for X µs of the sieve excess":** scored as sv:free2's ns per number in 2′b+pp3 minus 2′b's (2′b has no pp, so its sv:free2 is empty), from the one `LAMPCORE_SIEVEBREAK=1` pass per cell after the wall replicates. One pass, so there is no interval.
- **"The largest single sieve sub-region difference":** the largest absolute difference, 2′b+pp3 minus 2′b, over sv:zero, sv:free2, sv:prime, sv:power and sv:tail, in the same pass.
- **For context only:** the sieve region's excess over its own-rate price, 2′b+pp3 against 2′b, from the wall replicates (with the flag off), as in run A.

## Decisions before "go" (the user's, Oct 27)

- **Time order, consistent with the D-11 ruling:**
  - **The PRICED clauses of R2-18, D-15 and G-8 are information only,** because 2′b's priced totals at 72 and 84 were printed before this file was committed. G-8's falsifier clause "official ratio at either size falls below 1.000" is priced, so it is information only too.
  - **Sealed:** the wall clauses (R2-18 wall, R2-19, D-16, G-9, and G-8's wall ranges and its wall falsifier clause) and the 96-bit breakdown (R2-20, D-17, G-10).
- **PROTOCOL.md (prospective):** a count pass during a cost note hides priced totals for cells with pending predictions.
- **The free-2 meter correction:** the user's choice between APPLY and HOLD was left unfilled in the brief. The reviewer recommends APPLY after this run (NOTES).
- **The user's conditions:** laptop on the fan pad, plugged in, untouched; cap 2.4 GHz as recorded.
