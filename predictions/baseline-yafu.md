# baseline-yafu: the adopted reference (2′b) against YAFU on the map numbers (I-038; information only): predictions

**Run** (not yet): `evolve/baseline_yafu.py`, the same design as the msieve baseline (`evolve/baseline_msieve.py`, bb786c6). The runner is committed separately, before timing.
- **YAFU:** built in `~/opt/yafu-src/yafu` from the user's clone, yafu c7d90283972820f99b3b4920bfc1eff05c1f6342 (Oct 15 2026). YAFU 3 builds the ytools and ysieve copies tracked in its own tree; the separate clones (ysieve 21b6f96dea7e72c158c2c430ba6116f2b74ccd1a, ytools ee04dbb6f047e9b6a4e26931439323d87ddf6ba7) were not used by the build, in user space, no sudo. The command was `make yafu GMP_INCDIR=/usr/include/x86_64-linux-gnu USE_AVX2=1 USE_BMI2=1 ECM=1`: gcc -O2, SSE4.1 + AVX2 + BMI2 (this CPU has no AVX-512), linked against the system GMP and GMP-ECM. Binary sha256 f5f9bde1….
- **The design** (the reviewer's, before timing): YAFU runs its **full default `factor()`** (its own trial division, Fermat, rho and ECM before SIQS, by its own choice), as msieve ran its default. One thread; batch; pinned. The exact command line, run in an empty scratch directory with no `yafu.ini` (YAFU's built-in defaults; the `yafu.ini` in the source tree carries another machine's paths and tune data):

      taskset -c 2 ~/opt/yafu-src/yafu/yafu "factor(@)" -threads 1 < in.txt

  `in.txt` holds one number per line. YAFU reads a piped stdin as a batch file, so its start-up is paid once per process. It writes `factor.log`, `factor.json` and `session.log` in the scratch directory, which is emptied before each run.
- **Cells, per size** (72, 84, 96; all map numbers):
  - the sealed comparison: "card" (2′b, the release lampcore) against "yafu" on all map numbers;
  - information: the balanced band (the last band of 80; the same command), the full reference pipeline against YAFU, and one pass per band.
- **Conditions:** 4 replicates, the order rotating and alternating as in the msieve baseline. Cap 2,400 MHz, AC online, TCPU < 70 °C, no Wolfram kernel; else timing is skipped. Pause above 90 °C. Machine state is recorded.
- **Factors:** YAFU's prime factors must be {p, q}, and the card's factor must be p or q, on every number.
- **Information only:** YAFU has no op meter, so it never enters fitness.

**Disclosed before sealing:** a functional check ran once, at 20:07–20:08 Oct 27, before this file was committed. It ran YAFU's batch mode on 5 numbers at 96 bits (3 balanced, 2 with a 16-bit factor), pinned to core 2 under the 2.4 GHz cap, while the fix's parity suite ran on other cores. It was not a timing run.
- It found the stdin batch form; the `-batchfile` form read nothing when stdin was not a terminal.
- Claude saw the times it printed.
- The forecasters' texts below were received before it ran, so it cannot have informed them.

## DeepSeek's D-21 / D-22 (20:04 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
D-21 — YAFU baseline, 96 bits, balanced band. Definition: card wall per number / YAFU wall per number, 96-bit map numbers, balanced band only, one thread, pinned core, 2.4 GHz cap, AC, batch mode, 4 replicates. Base: card = 2'b. Dimensionless; below 1 = card faster.
Sealed range 0.30–1.10 (central 0.55), 60%. Falsifier: <0.15 or >1.40.
Working: card 96-bit wall ≈ 3,430 µs per number at 2.4 GHz (given). YAFU's 96-bit wall on this machine is missing; web figures (mersenneforum ECM level times 0.32 s / 2.85 s / 3.15 s for 15/20/25-digit levels; Quora 0.5 s for a 50-digit semiprime; YAFU source describing tinySIQS as "meant to run very quickly on tiny inputs (less than 115 bits, say)"; a forum note on 60-digit jobs) are not substitutes. Estimate from the msieve ratio: card/msieve = 0.319 all-numbers, 0.210 balanced. If YAFU is 2× faster than msieve, 0.210 × 2 = 0.42; 4×, 0.84; 6×, 1.26. Arithmetic band 0.42–1.26; centred at 0.55 because YAFU may pay setup and parameter-selection costs the card does not; low side extended to 0.30 for YAFU only modestly faster than msieve. The range is the spread of plausible YAFU-vs-msieve speed ratios, not a measured interval. Falsifier glosses as written: "<0.15 (YAFU more than ~7× faster than msieve) or >1.40 (YAFU slower than the card on the balanced band, which would contradict the msieve baseline's direction)".

D-22 — YAFU baseline, 96 bits, all map numbers. Same design as D-21, all 96-bit map numbers. Base: card = 2'b.
Sealed range 0.40–1.25 (central 0.70), 60%. Falsifier: <0.20 or >1.60.
Working: all-numbers msieve ratio 0.319; if YAFU 2–6× faster than msieve, 0.319 × [2,6] = 0.638–1.914. Centred at 0.70 rather than ~1.10 because YAFU's batch mode pays a fixed per-number cost and because the all-numbers form includes numbers where msieve's weak one-factor performance inflated the card's advantage. YAFU's absolute 96-bit wall is missing; estimated range. Falsifier glosses as written: "<0.20 (YAFU more than ~5× faster than msieve on the all-numbers form ...) or >1.60 (YAFU slower than the card on all numbers ...)".
<!-- verbatim end -->

**The reviewer's annotations** (the ranges are unchanged):
- **The D-21 / D-22 falsifier glosses are inverted.** The ratio is card / YAFU, so a ratio above 1 means YAFU is **faster**, and a ratio below 0.15 would mean YAFU is **slower** than msieve. The numbers stand as sealed.
- External figures were labelled and not used: fine.

## The reviewer's R-21 / R-22 (Oct 27; sealed; verbatim)

      R-21 (B) 96 bits, balanced band, card / YAFU: 0.8 to 3.0 (central 1.5, YAFU faster). 65%.
      R-22 (B) 96 bits, all map numbers, card / YAFU: 1.2 to 5.0 (central 2.5). 60%.
      Falsifiers: outside the stated range.

## Grok's G-14 / G-15 (20:07 Oct 27 PT; sealed; verbatim)

<!-- verbatim begin -->
**Sealed predictions (Grok, 27 Oct 2026 ~20:15 PT)**
Using only the numbers supplied. Absolute YAFU wall times on this machine, per-size lookup costs beyond the stated forecasts, and the exact fraction of wall spent in the linear scan are missing.

### G-14 — 96 bits, BALANCED band: card / YAFU
**Range:** 0.25–0.80 (confidence 55 %).
Below 1 = card faster.

(Information only: public YAFU SIQS figures on ~30-decimal-digit numbers are typically a few milliseconds on a single core; the card's ~3.4 ms is in the same order, but pinning, batching and the 2.4 GHz cap differ. Those figures are in decimal digits.)

**Falsifier:** the measured ratio lies outside 0.25–0.80.

### G-15 — 96 bits, ALL map numbers: card / YAFU
**Range:** 0.35–1.10 (confidence 50 %).
Below 1 = card faster.

**Falsifier:** the measured ratio lies outside 0.35–1.10.
<!-- verbatim end -->

**The reviewer's annotation** (the ranges are unchanged): G-14's range (0.25–0.80, card faster) is inconsistent with its own information-only figure. "A few milliseconds" for YAFU on ~30 digits, against the card's ~3.4 ms, implies a ratio near 1. The range appears anchored on the msieve result.
