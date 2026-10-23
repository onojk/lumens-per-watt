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
  evolve/run6/, seeds 51-54 (51-52 no-luck, 53-54 luck), 4 islands x 16 genomes per run.
  - Harness: evolve/evolve_run6.py, 20 generations. Per island per generation: the top
    two survive (plus the island's gate champion if it fell out); the diversity reserve is
    two more survivors, the best-ranked genomes that solved every training number and whose
    card set (set of stage types) differs from every elite's and each other's, with fresh
    random genomes filling any empty slot; after every 5th generation each island's top
    two are copied into the next island (ring), replacing two children; the rest are bred
    from the top half (30% crossover). Every island's best goes through the gate; the run
    champion is the best gate score seen. Coverage rule off.
  - Prerequisites (done): qs chainable and in both decks (no-luck: td, sq, ps, qs;
    luck: td, sq, ps, rho, pm1, qs; fine deck on); rand_stage and mutation ranges
    kc 1..32 (int), bc 0.8..3.0, mc 1..12, tc 1.0..3.5; parity on random genomes with qs;
    qs refuses N >= 2^100.
  - Sizes: train at 66, 72, 78 bits, 6 fresh numbers per size per generation (as Run 5);
    score = cumulative, top two sizes (72 and 78), as in Run 3+. Validation gate at
    84 bits, 12 fixed numbers. These sizes let the score see qs's exponent: qs crosses
    rho near 72 bits on the Stage 2 numbers.
  - Caps: training 2^26 (score sizes 66/72/78); the 84-bit gate and the final ACCEPT
    2^28. These are Run 6's own caps; Stage 6 still reconciles the other four.
    Worst cases, from 200 fresh numbers per size (semiprimes_pq(bits, 200, 1100000 + bits))
    under a 2^34 cap: at 84 bits rho 2^23.31, L44-0272 2^23.21, qs default 2^21.39,
    Hart x480 2^27.26; at 78 bits 2^21.54, 2^22.17, 2^20.63, 2^25.67.
    - Training cap is a time setting, not a measurement: a miss is cheap (scoring stops
      at the first top-size miss), and a slow loser scores as a loser whether it misses
      or finishes. Rho and L44-0272's worst at 84 bits (~2^23.3) is 6x under 2^26, and
      every 78-bit worst above, Hart's included, fits under it.
    - 2^28 where precise numbers matter (gate, ACCEPT): the smallest power of two that
      keeps every worst case above a scored number, Hart's 84-bit 2^27.26 included.
  - Memory guards (prerequisite for these sizes): block flash stops before allocating
    product trees whose minimum charge already exceeds the budget; p - 1 stops before
    sieving when a lower bound on pi(B) already exceeds it (both cores); lampcore's p - 1
    sieve is bit-packed and its prime-power loop uses u128 (u64 wrapped past 2^32);
    Python's p - 1 sieves bounds past 2^26 a segment at a time. Parity covers each.
  - ACCEPT: compare the run champions against qs-default ({kc 16, bc 1.5, mc 4.0,
    tc 2.0}), L44-0272, and rho on the Stage 2 numbers at 72 and 78 bits
    (semiprimes_pq(bits, 80, 990000 + bits)) plus 80 fresh 84-bit numbers
    (semiprimes_pq(84, 80, 1300084)), cap 2^28; evolve/run6_accept.py, written before the run.
    Per size, report log2(mean ops) and the worst case, each with a 95% bootstrap
    interval (revalidate.py's: random.Random(2026) per cell, 10,000 resamples, tails at
    index 250/9749; for the worst case, the max of each resample). Note qs already beats
    L44-0272 on worst case at 78 bits (2^20.41 vs 2^22.04). Report whether evolution
    kept, tuned, or dropped qs.
- **qs mutation ranges for runs after Run 6** (`lamps.use_wide_qs_ranges()`, opt-in so
  Run 6 replays are unchanged): mc 0.05..12 drawn and mutated on a log scale (sigma 0.3
  in log units, so a tune step is ~0.6x-1.6x at the 5th/95th percentile), bc 0.7..3.0;
  kc and tc as in Run 6. Why: Run 6's champions sat on its mc floor of 1.0, and two
  sweeps of qs alone (kc 32, tc 1.38, the 78- and 84-bit ACCEPT numbers, cap 2^28) put
  the optimum below it.
  - `qs_boundary_sweep.py` (mc 0.25..2 x bc 0.8..1.5): cost falls as mc drops; best
    cell on the grid edge, mc 0.25, bc 1.1 (84 bits 2^19.22 [19.16, 19.27] vs mc 1.0
    2^19.44 [19.38, 19.51]).
  - `qs_boundary_sweep2.py` (mc 0.03..0.25 x bc 0.9..1.2, both cores, 0 disagreements):
    flat from mc 0.06 to 0.25 (84-bit cells 2^19.13-19.28, intervals mostly
    overlapping); best cells mc 0.25, bc 1.1-1.2 at 78 bits (2^18.28) and mc 0.06,
    bc 0.9 at 84 bits (2^19.13 [19.07, 19.18]).
  - Total gain over mc 1.0, bc 1.1: ~1.2x (2^0.31 at both sizes). The remaining best
    cells sit on the bc edges (0.9 at 84 bits, 1.2 at 78 bits) by less than the noise;
    not worth chasing with another sweep. The widened ranges cover both.
- **Stage 6:** reconcile the four caps and re-score with scale.py.

## Relation economy (planning; no code yet)

Comes after Stage 7, the large-prime cost model in NOTES.md, and before Stages 8-10. The
idea: separate *finding relations* from *using them*, so relation sources can be compared,
combined and evolved against one shared, fixed ledger.

- **The invariant.**
  - A relation is (u, e): u mod N and an exponent vector e over a shared factor base
    (one multiplier k, so one base: -1, the primes dividing k, and the primes p <= B
    with (kN | p) = 1). Valid means u^2 = prod p^(e_p) (mod N).
  - A combined large-prime relation (Stage 7) carries its extra square:
    u^2 = y^2 * prod p^(e_p), with y = q, or a product of large primes after Stage 10's
    double large prime.
  - The ledger checks every relation it receives and charges the check:
    - 1 op per modular multiply: one for u^2, and square-and-multiply for each
      p^(e_p) and for y, charged as in qs phase 7.
    - An invalid relation pays its check and is rejected, so it costs and earns nothing.
    - A relation whose exponent vector is all even is also rejected after its check: it
      can only give a trivial dependency.
- **Refactor qs into SOURCE + LEDGER.**
  - Source: polynomial generation and sieving (qs phases 1, 3, 4) and confirmation
    (phase 5, plus Stage 7's lp phase when lc > 1). It emits relations.
  - Ledger, shared by every source: the factor base (phase 2, owned here so all sources
    share one), dedupe, linear algebra (phase 6) and square root (phase 7).
  - The check has a switch. Off: qs as today, trusting its own relations. On: every
    relation is checked and charged. Any comparison between sources has it on for all
    of them.
  - Identity check, both cores, on the parity numbers:
    - check off: refactored qs equals today's qs op for op (ops, factor, tests, hits,
      every phase);
    - check on: it differs by exactly the check's formula, evaluated on the relations
      it submitted.
- **New fitness for source evolution: relation yield.**
  - Run a source on fixed numbers under a fixed op budget, with no factoring. The
    numbers are a new seed range at 72/78/84 bits, not the ACCEPT numbers.
  - Count useful relations, not rows: yield is the GF(2) rank the accepted relations
    add to the exponent matrix, measured by the harness after the run and not charged.
    So relations built by combining earlier ones (valid but dependent) add nothing.
  - Normalize by what factoring needs: rank / (F + delta) per op, the share of the
    matrix filled per op. Sources with different factor-base sizes then compare fairly.
  - The existing full-factoring score is the gate: a source is only kept if
    source + ledger factors the gate numbers.
- **First second source: continued fractions (CFRAC) into the same ledger.**
  - Cost model in NOTES first. CFRAC expands sqrt(kN): 1 op per step for the multiply
    mod N, small-number steps overcharged at 1 op each as in qs, and every Q_i a
    candidate, confirmed at qs's phase-5 rate (no sieve to filter them).
  - Acceptance:
    - CFRAC alone factors 100% at 40-60 bits;
    - every relation it submits passes the ledger check;
    - parity after the Rust port.
  - The test: do qs + CFRAC together beat qs alone per op? Both feed one ledger,
    interleaved in fixed op slices (Stage 9's race element, or a fixed split before it
    exists). Measured by relation yield, and by full-factoring ops on the ACCEPT numbers
    with the usual bootstrap.
  - Stated in advance: no. If each source's yield per op is roughly constant, a mix
    can't beat the better source. CFRAC confirms every candidate at F ops, so it should
    lose to qs at 72-84 bits. A win would mean qs's yield per op falls as relations
    accumulate, or that CFRAC finds relations qs doesn't.
- **Later: evolvable source genomes.**
  - Polynomial families beyond SIQS's, and candidate filters (thresholds, early-abort
    trial division), evolved with relation yield as fitness.
  - The ledger's check is the only correctness requirement: a source may do anything
    that produces relations, and pays for everything it does.
  - The ledger, its check and the factor base are fixed, never evolved.

## Stages 8-10 and Run 8 (planning; no code yet)

Same rules as Stages 3-4 and 7: each card's cost model goes into NOTES.md before any code;
every op is counted, never estimated; when in doubt, overcharge. Acceptance comes before
any scored run, and parity gates the Rust port.

- **Stage 8: ECM card ("ecm").**
  - Cost model (NOTES first):
    - 1 op per modular multiply mod N, counted as performed: Montgomery-curve x-only
      ladder (each xDBL and xADD charged by its multiplies and squarings).
    - Stage 1: the ladder over every prime power <= B1.
    - Stage 2 (optional, B2 > B1): a standard continuation to B2, charged per multiply,
      including the running product of differences.
    - Curve setup: parametrization multiplies plus 1 op per extended-Euclid step for
      each inverse, as in qs's polynomial setup.
    - The final gcd (and any gcd a stage takes) is charged as in rho: 1 op per gcd.
    - A curve that fails pays in full, and the next curve pays again.
  - Genes: B1, B2 (as a multiple of B1; 0 = no stage 2), curves (how many before giving
    up), family: plain Suyama, or a torsion-12 / torsion-16 family. The torsion
    families raise the chance that the group order is smooth; this is the "luck by
    design" knob, so the luck meter records it. Luck meter: one test per curve, and a
    hit when the curve finds a factor.
  - Acceptance:
    - Completeness: 100% of fresh semiprimes at 40-84 bits with default genes, cap
      2^29, on a seed range no earlier stage used.
    - Exact accounting: each phase (setup, stage 1, stage 2, gcd) equals its formula on
      the run's realized counts. Tolerance 0, and a one-op change must be caught.
    - Group-order check (harness only): for small p, ECM finds p on a curve exactly when
      that curve's order mod p, computed by brute force, is B1/B2-smooth as the stages
      require.
    - Parity after the Rust port.
  - Comparison: against tuned qs (kc 32, bc 1.1, mc 0.25, tc 1.38) and rho, on the ACCEPT
    numbers (Stage 2 numbers at 72/78, `semiprimes_pq(84, 80, 1300084)`), plus the Stage 2
    numbers at 54-66 so the crossover can be seen. Cap 2^28, same bootstrap, mean and
    worst with intervals. ECM's genes are fixed in advance on tuning seeds, never on these
    numbers.
  - Stated in advance: ECM beats qs below ~80 bits and loses above. Its cost grows with
    the smaller factor, which is half the bits here, and qs's grows more slowly.
- **Stage 9: race combinator ("race").**
  - A genome element holding two stages that run interleaved on one meter: A for sa ops,
    then B for sb ops, alternating, until one finds a factor or the budget runs out.
  - Genes: the two stages, slice sizes sa and sb, and a budget split (the share of the
    remaining budget either side may spend before it is stopped).
  - Ops: the race costs exactly what both sides spent. Switching sides costs nothing,
    since it does no arithmetic. A slice ends at the first charge that reaches or passes
    its size: charges come in chunks, and this rule is written down so both cores agree.
  - Prerequisite: every stage has to be resumable mid-run (a coroutine in Python, a state
    machine in lampcore), with no change to any stage's op count.
  - Acceptance:
    - Parity.
    - Identity: a race with sb = 0 equals stage A run alone, op for op (ops, factor,
      tests, hits, phases), and the same holds with the sides swapped.
- **Stage 10: qs refinements**, each with its own cost model in NOTES first, an identity
  check that the off setting equals the current card op for op, and a comparison against
  the best qs so far on the ACCEPT numbers.
  1. Small-prime skip: primes below a gene-set bound are not sieved, and the threshold is
     lowered to compensate; confirmation still tries every factor-base entry.
  2. Double large prime: the cofactor may reach L². Splitting it is charged by the ops
     of the method that does it (counted). Cycle finding in the partial graph is charged
     1 op per union-find step, and combining a cycle is charged as in Stage 7.
- **Run 8: islands as Run 6 (`evolve_run6.py`'s harness), with ECM and the race element
  in the decks.**
  - Wide ranges on: `use_wide_qs_ranges()`, plus the lc range from Stage 7 if Stage 7
    has passed.
  - Decks, proposed:
    - no-luck: td, sq, ps, qs, race (racing no-luck stages only);
    - luck: td, sq, ps, rho, pm1, qs, ecm, race. ECM is randomized like rho and pm1, so
      it goes in the luck deck.
  - Sizes, caps, gate and ACCEPT as in Run 6 (train 66/72/78 at 2^26, gate 84 at 2^28),
    re-checked by a one-generation dry run before launch.
  - ACCEPT adds tuned qs, the best ECM genome from Stage 8, and N51-0917 to Run 6's
    references. `run8_accept.py` is written before the run.
  - Seeds: 71-74, proposed (Run 5 used 41-44, Run 6 51-54; 61-64 stay reserved for
    Run 7).
  - Prerequisites: Stages 8 and 9 accepted, with parity.
