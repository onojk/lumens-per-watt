# div64: alloc+div64 against alloc, wall-clock (divide hits in 64-bit hardware steps): sealed predictions, filed before any timed run

**The change:** when the candidate value v is below 2^64 (always at these sizes), the A-prime checks and the division of hits run in u64: one hardware divide gives the quotient and the remainder, instead of libgcc's `__modti3` / `__divti3`. Cost note: NOTES.md, "Cost note (before code): divide hits in 64-bit hardware steps" (935e3b1). Every op count, relation and output is identical (acceptance, the code commit), so there is no priced prediction; only wall-clock is measured.

**Planned run** (not yet): `tools/sealed_run.sh div64 -- bash -c "cd evolve && python3 div64_time.py"`.
- **Design:** Run A's.
  - Cells: "alloc" is lampcore f6aa08d (13554a61…, a copy in Claude's scratch); "alloc+div64" is this change's release build.
  - Reference genes; all map numbers at 72 / 84 / 96; batch, core 2; 8 alternating replicates.
  - Outputs with `--types` are checked identical in the run.
  - Conditions: AC, cap 2,400 MHz, TCPU < 70 °C, no Wolfram kernel. **No battery override:** that was for Run D only.
- **Reported:** the ratio per replicate, its mean and 95% t interval, as a percent change (negative = faster).

**Information the forecasters have** (all filed before this file):
- **The cost note's measured inputs:** 8,430 / 13,705 / 20,875 calls per number into `__modti3` / `__divti3` from the divide-hits and A-prime sub-steps, 0.496 / 0.806 / 1.228 M instructions per number (balanced band).
- **The callgrind check after code** (`evolve/div64_check.out`, balanced band): the card's instructions per number fall 5.776 → 5.270 / 12.906 → 12.082 / 32.212 → 30.957 M, **−8.76 / −6.38 / −3.90%**. The 128-bit calls fall 0.533 → 0.037 / 0.863 → 0.057 / 1.347 → 0.119 M.
- **The ρ rule** (PROTOCOL.md): the removed code is class (a), register-resident arithmetic in a software routine. Class (a) is unmeasured, so the default 0.85–1.06 is widened toward Grok's direction (lower). The cost note also states an upper extension: the change halves the hardware divides per hit, and a divide is a long-latency instruction that counts as one.
- **The cost note's model forecast** (Wolfram, before code; ρ 0.40–1.30 against its pre-code instruction estimate): central −6.4 / −4.6 / −2.8%; band −2.9 to −10.2 / −2.1 to −7.4 / −1.3 to −4.5%.
- **Measured ρ so far:** class (b), alloc-once (Run D): 0.85 / 0.92 / 1.06. Class (c), the A-prime fix (Run A, I-047): 1.01 / 0.98 / 1.35.
- **The card's wall per number,** all map numbers: Run D's after-cell, on battery and not comparable with AC runs, was 0.623 / 1.302 / 3.000 ms. There is no AC measurement of the alloc-once card yet.

## The reviewer's R-27 (Oct 27 night; sealed; verbatim)

      R-27 div64 vs current card (alloc-once), wall change: 72: -3.5% to -9.6%; 84: -2.6% to -7.0%;
           96: -1.6% to -4.3%. 65%. Basis: callgrind-measured removal 8.76 / 6.38 / 3.90% x rho 0.4-1.1
           (central 0.7). Unmeasured opinion behind the centre: a software 128-by-64 division routine is
           replaced by hardware divides, which cost more time per instruction. Falsifier: outside the range.

## DeepSeek's D-27 (23:44 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
Definition: mean wall-clock change per number, div64 build vs current card, each size, 2.4 GHz cap, within-run comparison. Base: current card (root confirm + A-prime fix + alloc-once). Units: percent change; negative = faster. Pure wall-clock prediction.
72 (8.76% removed): −2.2% to −5.0% (central −3.5%), 60%, falsifier >−2.2% or <−5.0%.
84 (6.38%): −1.6% to −3.8% (−2.6%), 60%, falsifier >−1.6% or <−3.8%.
96 (3.90%): −0.9% to −2.4% (−1.5%), 60%, falsifier >−0.9% or <−2.4%.
Working: ΔW = ρ · ΔI/I_total. Band choice: the cost note's class is "register-resident arithmetic, band rho 0.40–1.30", but the reviewer's unmeasured opinion says the removed instructions are a software division routine, cheap per instruction, so rho falls below that band. I accept that direction and use rho 0.25–0.58, central 0.40, declared before the run. 72: 8.76% × [0.25, 0.58] = [2.19%, 5.08%]; 84: 6.38% × [0.25, 0.58] = [1.60%, 3.70%]; 96: 3.90% × [0.25, 0.58] = [0.98%, 2.26%]. Missing input: no measured rho for hardware-divide replacement; the band is a declared assumption. Falsifier direction checked. 60% per size; sizes correlated through the shared rho. (DeepSeek's copy of the update was truncated; change (2) was resent.)
<!-- verbatim end -->

## Grok's G-20 (23:44 Oct 27 PT; sealed; verbatim, with the header of Grok's reply)

<!-- verbatim begin -->
**Sealed predictions (Grok, 27 Oct 2026 ~23:50 PT)**
Using only the numbers supplied. Absolute post-div64 wall times and the final partials-table instruction counts are missing.
### G-20 — div64 wall change vs current card (negative = faster)
Rho basis: reviewer's unmeasured opinion that hardware divides cost more time per instruction than the software routine they replace, so rho is taken at the low end of the stated register-arithmetic band (0.40–1.30). Rho = 0.55.
- 72 bits: −3.3 % to −6.3 % (confidence 60 %)
- 84 bits: −2.2 % to −4.8 % (confidence 60 %)
- 96 bits: −1.2 % to −3.0 % (confidence 55 %)
**Falsifiers:** 72: ≥ −2.0 % or ≤ −8.0 %; 84: ≥ −1.0 % or ≤ −6.0 %; 96: ≥ 0 % or ≤ −4.5 %
<!-- verbatim end -->

**The reviewer's notes** (the ranges are unchanged):
- **Not independent.** D-27 and G-20 both took the reviewer's labelled "unmeasured opinion" as their ρ basis (D-27 ρ 0.25–0.58; G-20 ρ 0.55), so the three div64 forecasts are not independent. Recorded.
- **Scoring G-20.** Its falsifiers are bands wider than its ranges, so ranges and falsifiers are scored separately.

**All three div64 forecasters are sealed:** R-27, D-27, G-20.
