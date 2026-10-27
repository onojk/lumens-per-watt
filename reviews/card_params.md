# The card's parameters — measured values only

This sheet is prepended to every DeepSeek prompt (`tools/ask_deepseek.py`). It holds values measured on the committed card, each with its source. **Use these values; do not assume others.** If a value you need is not here, say so and ask, rather than estimating it.

Maintained by Claude.

**Last updated:** 2026-10-27 (goff = 1 adopted as the reference default; I-032 results added). **Card commit:** 5f0007a (2′a and 2′b built); the phasetime instrumentation fix follows (counts unchanged).

## The card at 96 bits (the reference)

- **Method:** SIQS with single large primes. Lampcore (Rust), with a Python twin kept in lockstep.
- **Reference genes:** bc 0.4325, mc 0.6023, tc 1.0353, lc 1.9737, kc 60, multiplier set sf32, A chosen on demand. Re-sieve is off: confirm divides by every base prime.
- **goff = 1 (adopted by the user, Oct 26, as the reference default; I-032 option 2′a):** the Gray code keeps the sieve's start offsets. Per A, each root is converted once to its offset (1 word per root). The sieve's per-polynomial start-offset add (1 word per root per polynomial) is gone.
  - The reference genes change only by goff = 1. Relations, factors, candidates and polynomials are identical, so earlier results stay valid.
  - Only the word count changes, by exactly −setup_gray: about −35,897 word per number at 96 bits.
  - Priced against the old reference: official 0.9754, ruint 0.9843, Montgomery 0.9842 (i032-2prime, 9b94247).
- **Root confirm** (gene confirm = root; off by default; not adopted): with goff = 1 it reads the kept offsets in place (2′b). Against the goff = 1 reference: official 1.0137, ruint 0.8877, Montgomery 0.8838. With pp 3 at +0 bits: 0.9618 / 0.8703 / 0.8656.
- **Formulas:**
  - B = bc · exp(½ √(ln N ln ln N));
  - M = max(64, mc · B), with the sieve interval [−M, M] (width 2M + 1);
  - L = B^lc;
  - threshold T = log2(M √(kN/2)) − (tc + lc − 1) · log2 B;
  - slack = tc + lc − 1.
- **Means over the 640 map numbers:**
  - B 1,752 (log2 B 10.775); F (factor-base size) 138; M 1,056 (width ~2,113);
  - L/B 1,440 (log2 L ≈ 21.3); slack 2.009 (21.65 bits).
- **The sieve:** adds round(log2 p) per odd base prime per root hit. It does not sieve the prime 2, A's primes or prime powers (unless `pp` is set). The threshold is one value per attempt.
- **Confirm:** for each candidate, tests v mod p for all F − 1 base primes (i128), dividing out repeats. A cofactor below L is a partial.
- **Multipliers (32 map numbers):** kN mod 8 is 1 in 50% of attempts, 3 or 7 in 22%, 5 in 12%, and even in 16%.

## Measured per number at 96 bits (stage G reference, a82b6bd; all 640 map numbers)

- Candidates: 1,013 per number, 6.5 per polynomial.
- Polynomials to completion: 156.0 (median 151). Combinations: 71.9.
- Priced cost: ruint 59,071 (mean), 58,514 (median), 80,787 (slowest-decile mean); Montgomery 216,420; official 1,461,014.
- Wall-clock: 1,898 µs per number. By region: setup 374, gray 45, sieve 456, scan 107, confirm 536, lp_ledger 184, solve 156 µs.
- Sieve updates per sieve position: 2.28.
- Priced shares (ruint): sieve_update 32.8%, confirm_td 27.5%, setup_small 8.4%, sieve_scan 6.9%, word 4.5%, setup_gray 1.6%.

## Capture and yield at 96 bits (stage B, 1f45169; 8 map numbers, 1,285 polynomials)

- **True relations per polynomial:** fulls 0.52, partials 17.1.
- **Passing the threshold:** fulls 0.973, partials 0.316. End to end: fulls 0.961, partials 0.316.
- **Partials passing, by log2(q/B):** 0–2 0.717; 2–4 0.596; 4–6 0.445; 6–8 0.273; 8+ 0.118.
- **The sieve's under-count** (true log2 of the smooth part minus the sieve value):
  - at partials: mean 5.34, median 4.58, p90 11.4 bits;
  - at fulls: mean 7.44, median 6.50, p90 15.0 bits.
  - Its parts at partials (mean / median): prime 2 2.50 / 3.00; prime powers 2.63 / 1.58; A's primes 0.27 / 0; rounding 0.
- **Never-combined share of partials:** 0.852.

## Threshold scan at 96 bits (stage G, a82b6bd; tc only, L unchanged; against the reference)

| shift | candidates / number | candidates / polynomial | polynomials | partial capture | ruint | wall-clock |
|---|---|---|---|---|---|---|
| −2 bits | +41.7% | +59.3% | −11.0% | 0.474 | +5.7% | +9.8% |
| −4 bits | +103.3% | +148.3% | −18.1% | 0.622 | +19.3% | +29.4% |
| −6 bits | +197.4% | +284.1% | −22.6% | 0.752 | +43.6% | +55.7% |

## Op prices (per op, ruint / Montgomery; calibrate.json)

| op | ruint | Montgomery |
|---|---|---|
| word (also sieve_update, setup_gray) | 0.0258 | 0.0951 |
| sieve_scan | 0.01235 | 0.0466 |
| confirm_td (one i128 test v mod p) | 0.1141 | 0.4260 |
| setup_small | 0.3065 | 1.137 |
| setup_euclid | 0.3164 | 1.190 |
| hash | 0.3638 | 1.343 |
| la | 0.01673 | 0.0629 |

Official pricing counts every op as 1.

## Wall-clock against price (stage C, 9402b8b)

- **Anchor B** (time-weighted ns per priced ruint unit) at 96: 31.0 (re-sieve off).
- **Over-priced or under-timed regions at 96, by ratio to anchor B:** lp_ledger 3.10, solve 2.38, confirm with re-sieve 2.25, gray 1.57.
- The large-prime table's hash runs at 1.4–1.7x its price (step 3).
- **The confirm test:** ~3.9 ns per prime tested (i128 v mod p). About 137 primes are tested per candidate, and about 7.6 of them divide (stage D).

## Stage H: the `pp` option (off by default; nothing adopted)

**The option** (built in b2bade2; design 3caf8df):
- Gene `pp`; absent or 0 means off, identical to the reference card.
- Prime powers q = p^j < 2^pp are sieved like base primes: odd base primes not dividing k or A; 2^j for 4 ≤ j < pp, only when kN ≡ 1 mod 8.
- **The free 2:** the prime 2's fixed part is added on one parity class of positions, with no sieve walk.
  - For odd kN, the class is the odd-y positions (y = A x + B): +1 bit for kN ≡ 3 mod 4, +2 for kN ≡ 5 mod 8, +3 for kN ≡ 1 mod 8.
  - For even k (kN ≡ 2 mod 4), it is +1 bit on the even-y class.
- **pp = 3 is "2 free":** the parity add alone, with no powers (an odd power needs p² < 2^pp, and the 2^j walk starts at j = 4).
- Charges: as the stage H cost-model table in NOTES (per-attempt and per-A setup for the power entries; sieve updates for the walks; the parity add costs 2 words per attempt and 1 per A).

**Measured, stage H** (06483b7; results 8cc9d79; 96 bits, 640 numbers, against the reference, same run):

| cell | candidates / number | polynomials | partial capture | ruint | Montgomery | official | wall-clock |
|---|---|---|---|---|---|---|---|
| (i) pp 10, tc 1.0353 | +67.8% | −22.5% | 0.717 | +16.2% | +16.5% | +1.9% | +29.0% |
| (ii) pp 10, tc 0.7623 (matched) | −1.4% | −13.9% | 0.407 | +1.5% | +1.4% | +1.8% | +9.0% |
| (iii) pp 10, +5 bits | −32.9% | −3.2% | 0.225 | −0.8% | −0.8% | +8.2% | +3.8% |
| (iv) pp 3, +3 bits | −28.6% | +10.1% | 0.203 | −2.5% | −2.5% | +4.9% | +3.1% |

- Reference in that run: 2,015 µs per number, partial capture 0.316, never-combined 0.853.
- **Under-count at true partials, median:** 4.58 bits (reference); −0.01 (pp 10); 2.68 (pp 3).
- **With pp 10:** sieve updates per polynomial +28%, sieve wall-clock per polynomial +27.5% to +31%, setup per polynomial +18% to +22% (the per-A power entries).
- **The scan, as built in b2bade2:** a per-position parity check that nearly doubled the scan's wall-clock per polynomial (0.73 → 1.35–1.44 µs), +60 to +120 µs per number. This was slow code, not a charge.
- **The scan fix** (373261d): the free 2 is written into the sieve array at initialisation, with counts identical (pp cells against b2bade2 14,000 / 14,000; option off 8,000 / 8,000; Python = Rust 48 / 48; parity). The scan per polynomial is back to 0.72–0.75 µs. The fill costs ~0.2–0.5 µs per polynomial, inside the sieve region.
- **The matched candidate count with pp = 10** is tc 0.7623, a threshold +2.94 bits higher (32-number search, `hsearch.out`).

**Measured, stage H2** (the re-time after the scan fix; results 5ae47ae, scored in NOTES; 96 bits, 640 numbers, against the reference in the same run, which took 2,100 µs):

| cell | candidates / number | polynomials | ruint | Montgomery | official | wall-clock |
|---|---|---|---|---|---|---|
| (iii) pp 10, +5 bits | −32.9% | −3.2% | −0.8% | −0.8% | +8.2% | +0.2% |
| (iv) pp 3, +3 bits | −28.6% | +10.1% | −2.5% | −2.5% | +4.9% | −3.8% |
| pp 3, +1 bit | +2.0% | −4.5% | −1.9% | −2.0% | −3.4% | +0.9% |
| pp 3, +2 bits | −14.3% | +2.2% | −2.9% | −2.9% | +0.2% | −0.7% |

- The machine's speed drifts between sessions: the same reference took 1,898 / 2,015 / 2,100 µs in stages G / H / H2. Compare only within a run.

## The goff = 1 reference at 96 bits (adopted Oct 26; i032-2prime, 9b94247; 2.4 GHz cap)

- **Priced per number:** official 1,425,117; ruint 58,145; Montgomery 213,006. Candidates and polynomials as above (1,012.7; 156.04).
- **Wall-clock at the 2.4 GHz cap:** 3,855.7 µs per number (sd 33.4, 8 replicates).
  - Only runs at the same cap are comparable (PROTOCOL.md, "Frequency cap").
  - Against the goff = 0 reference: −1.8% [−2.9, −0.6]; sieve region −7.8%.
