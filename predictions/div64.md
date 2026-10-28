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

## DeepSeek's

Pending.

## Grok's

Pending.
