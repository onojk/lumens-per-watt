# PLAN

Staged plan from the Oct 23 review.

## History notes
- Run 5 (evolve/run5/, evolve_scale.py, seeds 41-44, cap 2^23, no islands, no qs)
  landed before this plan as a scale probe. It stays exactly as committed.
- The plan's original Stage 5 (islands + qs) is renumbered to Run 6 rather than
  relabeling Run 5, because Run 5 is already fixed in the record: its folder, script,
  seeds, and lineage names (N41-... to L44-...) are committed. Renumbering a future
  run costs nothing; editing committed labels would rewrite the record.
- Run 5's champion L44-0272 (p-1 bound N^0.21, then rho) beats plain rho by 1.3-1.6x
  at 64/72/78 bits (80 fresh numbers each), same exponent (~N^0.256), same worst case.
  It is the bar for later runs, alongside plain rho.
- The Oct 22 scale table in README stays unedited; re-scores go beside it.
- Four caps exist; document all, change none before Stage 6:
  - evolve/scale.py `CAP=2^29`
  - `lamps.cap_for(bits)=2^(bits/2+6)`
  - parity.py `min(cap_for, 2^22)`
  - evolve_scale.py `CAP_LOG2=23`

## Stage 1: square-search window fix, instrumentation, coverage rule

### Diagnosis (reproduced)
Lehman's 66-bit miss is N=23736149549216675201, p=4638920653, q=5116739717.
Lehman's theorem catches it at k=59881 (a=257, b=233), x = x0+1; theory window
width there = N^(1/6)/(4*sqrt(k)) = 1.732, covering x0 and x0+1. lamp_sq uses
W = max(1, int(width)) = 1, testing only x0. The 0.25 constant is correct; do NOT
widen it. The k range is not involved.

### Fix (exact expressions, identical on both sides)
lamps.py `lamp_sq`, per k (kN already x4 when ksq):
```python
s = math.isqrt(kN)
x0 = s if s * s == kN else s + 1
f = float(kN - s * s) / float(2 * s)      # convert first, then divide
width = g["c"] * (N ** g["w"]) / math.sqrt(k)
W = max(1, s + math.floor(f + width) - x0 + 1)
```
main.rs `sq_one_k`:
```rust
let s = isqrt(kn); let exact = s * s == kn;
let x0 = if exact { s } else { s + U256::from(1u64) };
let f = (kn - s*s).to::<u128>() as f64 / (s * U256::from(2u64)).to::<u128>() as f64;
let width = gf(g, "c") * num.f.powf(gf(g, "w")) / (k as f64).sqrt();
let steps = (f + width).floor() as u64;
let w = (if exact { steps + 1 } else { steps }).max(1);
```
Never take a float sqrt of kN itself (loses ~10 bits past 60-bit N).

### Gates (in order; each must pass before the next)
1. **Unit:** k=59881 gives W=2; Lehman baseline factors the repro N with exactly
   1,643,747 ops, factor 5116739717, in both Python and Rust.
2. **Instrumentation** (read-only, both cores, same fields): winning stage index and,
   for a square-search win, the k it succeeded at.
3. **Op-count invariance:** instrumented vs uninstrumented ops identical on every pair.
4. **parity.py:** 0 mismatches, including the new fields (reference: 3,312 pairs, 0).
5. **Wide re-score** with scale.py (seed 880000+bits, 40 per size, cap 2^29, sizes
   54-78): Lehman, Hart x480, and every champion with a square-search stage.
   Reference values (log2(mean ops), old -> new) from an independent run:
   ```
   lehman           17.37->17.37 19.31->19.30 21.15*->21.17 23.31->23.26 25.31->25.31
   run3 no-luck-21  15.33->15.47 16.75->16.93 18.93->19.09 20.86->21.04 23.30->23.46
   run3 no-luck-22  66 bits 18.46->18.47, other sizes unchanged
   run4 luck-34     14.58->14.64 16.73->16.77 18.93->18.87 20.31->20.35 22.80->22.82
   hart x480, run2 no-luck-11/12, run4 no-luck-31/32: unchanged
   run4 no-luck-32 at 78 bits: still one number missed (22.59*)
   ```
   Every cell must match to the hundredth.
   **Per-number drop rule** (all square-search algorithms, all sizes): any number whose
   ops fell must show either (a) same sq stage, earlier stopping k, or (b) now caught
   by an sq stage where a later stage used to catch it. Anything else: stop, report.
6. **Coverage rule** for genomes whose stages stop short of sqrt(N) (no-luck-32's 78-bit
   miss): append a fallback tail, flag it in lineage.jsonl, charge its ops.
   Fallback lamp: trial division to sqrt(N) in the no-luck deck; rho in the luck deck.
7. **Write-up:** NOTES.md entry; README: add the re-scored table beside the Oct 22 one,
   unedited.

One commit for Stage 1, push, then a one-paragraph summary with gate 1's exact
numbers, the parity count, and the old-vs-new table.

## Stage 2: statistical re-validation
- At least 80 fresh semiprimes per size.
- 95% confidence interval on log2(mean ops) per size, by bootstrap over numbers:
  10,000 resamples, resampling within each bit size.
- Re-validate the Run 3 and Run 4 champions plus rho and Hart x480 under the new
  sample, and give a verdict on which past wins survive. Overlapping intervals mean
  within noise (expected for luck-33 vs rho).
- Specifics (so results can be checked against an independent reference):
  - Numbers: semiprimes_pq(bits, 80, 990000 + bits), sizes 54, 60, 66, 72, 78.
  - Genomes: rho, hart x480, the final champion of each Run 3 and Run 4 run
    (no-luck-32 included).
  - Cap 2^29, post-Stage-1 code (inclusive window), coverage rule OFF.
  - Statistic: log2(mean ops) per algorithm and size (total-work scoreboard, same as
    every scale table), computed on each resample.
  - Bootstrap: a fresh random.Random(2026) per (algorithm, size) cell; within a cell,
    10,000 resamples, each n draws of rng.choice(ops), ops in number-generation order
    with misses removed. Percentile method: 2.5th and 97.5th of the sorted resampled
    values, symmetric tails: indices int(0.025 * R) and int(0.975 * R) - 1 (250 and 9749),
    so exactly 250 resamples sit outside each end.
  - Misses: excluded from that cell's mean and CI; cell starred with the miss count.
  - Verdict per past win: overlapping intervals = within noise.

## Later stages (outline)
- **Stages 3-4:** a quadratic-sieve card ("qs") in lamps.py, then its Rust port, gated by
  parity.py. Write its cost model into NOTES.md before any scored run.
- **Run 6** (the plan's original Stage 5): island model (4 islands, top-2 migration
  every 5 generations, ring, 2-slot diversity reserve) with qs in the deck,
  evolve/run6/, seeds 51-54.
  Prerequisites: qs chainable and in both decks, with mutation genes and rand_stage.
  ACCEPT compares against L44-0272 and plain rho, and reports whether evolution kept
  or dropped qs.
- **Stage 6:** reconcile the four caps and re-score with scale.py.
