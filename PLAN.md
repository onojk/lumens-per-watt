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

## Working rules

- **Reuse rule: don't rebuild what exists unless rebuilding helps.**
  - **Build** in-house only what the meter must see: card arithmetic. Published algorithms
    are ported step by step, with every op charged.
  - **Reuse** everything else:
    - search machinery: a quality-diversity library for MAP-Elites (e.g. pyribs);
      OpenEvolve or ShinkaEvolve for the Phase 2 LLM loop, with our harness as the
      evaluator;
    - published parameters as starting genes (Gower-Wagstaff's SQUFOF multipliers,
      Milan's fast-return threshold and early-abort constant);
    - existing factoring tools (TIFA, YAFU) as reference oracles for correctness and
      sanity checks, never for cost.
  - Before adopting a dependency: its license is compatible, it is maintained, and its
    version is pinned. It never sits inside a charged code path.
  - When a section of this plan proposes building something, it names the existing tool it
    considered and says, in one line, why it isn't used.
- **Reporting rules (all comparisons from Oct 24 on):**
  - A paired bootstrap of per-number log-ratios is reported beside the separate intervals
    (the same numbers give tighter intervals; old results stay comparable).
  - Before each comparison, a power estimate: the numbers per cell needed to detect the
    predicted effect. A test too small to see its own prediction is not run.
  - Each stage's write-up counts the predictions scored (held / missed), so chance holds and
    misses stay visible.
  - The median is reported beside the mean (fitness stays the mean).
- One Claude session owns the repo at a time; others read only. Unfinished work is parked
  in scratch while long tests run (after the Oct 23 stray-revert incident).

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

## Order of work (after Run 6)

Stage 7 (large primes, done) -> relation-economy refactor (done), with the illumination
tracer as a side task -> Stage 8 (ECM) -> Stage 9 (race) -> Stage 9.5 (across-numbers selector,
planning only) -> partition study (done) -> per-type counters (done) -> partition study part 2
(map only) -> Stage 10 (qs refinements) -> theory checks -> Run 8 with control arms.
Learning from all algorithms: the move catalogue is done (MOVES.md); its Phase 1 follows
Stage 9, with the math-survey items appended; the code-level pilot follows Run 8. Nothing
from the math survey jumps the queue.

The partition study comes after Stage 9 because its allocations run as race schedules,
and it needs ECM in the cost map.

The relation-economy refactor comes before ECM for three reasons:
- it reshapes the qs card that every later stage builds on;
- CFRAC, the second relation source, needs the shared ledger;
- Stage 7 is already changing the same code, so doing it now is cheaper than retrofitting.

## Relation economy (done, Oct 23)

Done, each accepted with parity:
- qs split into source + ledger (`ledger.py`), op for op unchanged;
- the opt-in charged relation check;
- CFRAC as a second source. Comparison in README ("Relation economy: CFRAC").

Decisions:
- CFRAC stays in no deck: it loses to tuned qs, and mixing it in only costs.
- Early abort (NOTES, CFRAC entry) stays a planned gene, low priority: it can only narrow
  a constant, and CFRAC's growth is steeper than qs's.

Not started: relation-yield fitness and evolvable source genomes (below).


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
  - With the check on (see the switch below), the ledger checks every relation a source
    submits and charges the check (cost model: NOTES.md, "Ledger: the charged relation
    check"):
    - 1 op per modular multiply: one for u^2, and square-and-multiply for each
      p^(e_p) and for y, charged as in qs phase 7.
    - An invalid relation pays its check and is rejected, so it costs and earns nothing.
    - A relation whose exponent vector is all even is a one-row dependency: it splits N
      unless u = +-Y (mod N), Y = y * prod p^(e_p/2). It is kept unless it is trivial
      (u = +-Y), which costs an extra test, charged only on all-even relations; a
      trivial one pays and is rejected.
- **Decision: one k per ledger.**
  - Every source feeding a ledger uses the same multiplier k and the same factor base.
    CFRAC expands sqrt(kN) with that k, so nothing is lost.
  - Multi-k ledgers are out of scope. If they are ever wanted, they get their own cost
    model first.
- **Refactor qs into SOURCE + LEDGER.**
  - Source: polynomial generation and sieving (qs phases 1, 3, 4) and confirmation
    (phase 5, plus Stage 7's lp phase when lc > 1). It emits relations.
  - Ledger, shared by every source: the factor base (phase 2, owned here so all sources
    share one), dedupe, linear algebra (phase 6) and square root (phase 7).
  - The check has a per-source switch, off by default. Off: the source's relations are
    trusted, and qs costs exactly what it costs today. On: every relation the source
    submits is checked and charged. qs never needs it (correct by construction); it is
    opt-in for other sources, and required for evolved ones. In a comparison between
    sources the check is on for all of them if and only if any of them needs it.
  - Identity check, both cores, on the parity numbers:
    - check off: refactored qs equals today's qs op for op (ops, factor, tests, hits,
      every phase);
    - check on: it differs by exactly the check's formula, evaluated on the relations
      it submitted, with nothing rejected (rejections reported; expected 0 for qs).
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
    - every relation it submits passes the harness relation check (and the ledger
      check, turned on as a test);
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
  - **Prediction (stated before measurement):** ECM beats qs below ~80 bits and loses
    above. Its cost grows with the smaller factor, which is half the bits here, and
    qs's grows more slowly.
  - On balanced semiprimes, with p ~ sqrt(N), ECM's L_p[1/2, sqrt2] equals L_N[1/2, 1],
    the same class as qs: expect a constants race (a crossover, ECM possibly ahead at
    the small end), not an exponent change. ECM's distinct shape shows on unbalanced
    numbers (one factor much smaller than sqrt N): the partition study and Run 8's mixed
    population are where it should pay.
- **Stage 9: race combinator ("race"). Done (Oct 24).** The combinator is accepted with
  parity; the fixed-slice race against qs is ruled out (NOTES.md, "Stage 9 result").
  Finer qs charge chunks stay a condition that would reopen the race; not planned.
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
  - Prerequisites: the relation-economy refactor, and Stages 8 and 9, accepted with
    parity.
  - **Scoring, decided (Oct 23, user): (c) as fitness, (e) in reports** (NOTES.md,
    calibration result).
    - Fitness, corrected Oct 24 (NOTES.md, partition study): per pricing P (official,
      ruint-calibrated, Montgomery-calibrated, median P-core prices), score_P(g) = mean cost
      of g under P / mean cost of the reference genome under P, on the same numbers; fitness
      = max over P of score_P. Reference for Run 8: tuned qs + lc 1.4 (default, named here).
      The first wording (the worst raw cost) collapsed to the official count.
    - Reports call a cell only where all three pricings agree; otherwise the cell is
      "undecided".
    - **ACCEPT gate (written Oct 24, before Run 8):** a champion must not be worse than 1.5×
      the reference genome on any band, under any pricing. A gate, not fitness: a
      champion that fails it is not accepted, whatever its score.
    - **Report: population-robust score** (report only): a champion's worst ratio across
      several fixed populations (balanced, mixed, mixed with another band spread).
  - **Control arms** (same evaluation budget, seeds and fitness as evolution):
    - TPE (Optuna) as the primary baseline; its license and maintenance checked and its
      version pinned (reuse rule). Random search as the null. CMA-ES (pycma) optional.
    - Pre-registered meanings, stated neutrally:
      - TPE matches evolution on gene tuning: gene tuning needs no evolution machinery,
        and evolution must show value on structure.
      - Evolution beats TPE: check TPE's convergence before crediting evolution.
      - Random search matches both: the fitness surface is flat at that genome.
  - **Run 8 design (Oct 24, planning; predictions written now).** Where it differs from the
    deck and size outline above, this design governs the evolution-vs-control comparison.
    - **Shared genome space, identical bounds for evolution, TPE (Optuna, pinned) and random
      search:** pre-stage budgets td, rho, ecm in {0} ∪ [2^8, 2^20] (log scale), pm1 in
      {0, full}; card order of the four pre-stages as one categorical gene (24 orders); final
      qs genes kc in 1..32, bc 0.7..3.0, mc 0.05..12 (log), tc 1.0..3.5, lc 1.0..2.0 (the
      wide ranges and Stage 7's lc range). Stage genes fixed at the partition study's
      values (td a 0.5, rho c 1 / b 64, pm1 b 0.1991, ECM 1.0 / 50).
    - **Budget: Run 6's actual one.** Run 6 made 1,360 genome evaluations per run (20
      generations × (4 islands × 16 genomes re-scored, plus 4 island-best gate evaluations)),
      5,440 over its 4 runs (`evolve_run6.py`; `run6/lineage.jsonl` holds the 5,120 training
      ones). Run 8: **1,360 evaluations per run per method, 8 seeds per method** (71–78;
      the run is cheap). Every method sees the same fixed tuning numbers for a given seed (a
      change from Run 6's fresh set per generation, so TPE's objective is stationary).
      Reported: best-of-8 and median-of-8 final fitness, and evaluations-to-best.
    - **Overfitting check:** each method's tuning-vs-sealed gap (its genomes' fitness on the
      tuning set against the same genomes on the sealed numbers), since TPE optimizes against
      a fixed set more aggressively, compared with the gap of an untuned reference genome
      (allocation A) on the same tuning and sealed sets. A run is marked **OVERFIT** if its gap
      exceeds A's by more than the paired bootstrap interval (not a fixed percentage).
      Bracketed by two reference gaps per tuning/sealed set: qs + lc 1.4 alone (never
      selected: pure sampling) and allocation A (selected on the map: sampling + selection).
      A method above qs alone's gap has overfit at all; above A's, it has overfit more than
      the map's own selection. A's gap stays the primary bar.
    - **Third arm** (reported separately, not in the primary comparison): evolution on fresh
      batches each generation, as Run 6 did, with the same budget and seeds. It shows
      whether the fixed tuning set changes evolution's result.
    - **qs-gene probe (warm-started TPE)** (separate, not a candidate): TPE warm-started from
      allocation A, with qs genes = qs + lc 1.4, compared with cold-start TPE on the qs-gene
      sub-experiment below (does the prior help?). Question: is A near-optimal? Improvement
      is judged by the paired bootstrap interval on the sealed numbers, and NOTES records
      either "A near-optimal" or "partition study under-explored by Z".
    - **qs-gene sub-experiment:** budgets and order fixed at A; all three methods search
      only kc, bc, mc, tc and lc, with the same evaluation counting, seeds and fitness.
    - **Convergence, pre-registered:** T1 = evaluations to enter A's paired interval; T2 =
      evaluations to reach A's point estimate or better. A's values are computed on each
      seed's own tuning set, not the partition map's. Computed per seed, aggregated as the
      median and IQR across the 8 seeds (not pooled), with the number of seeds that reached
      T1 and T2 at all, per method.
    - **Winning genomes reported split** into budgets / order and qs genes, side by side
      across methods.
    - **Card order, pre-registered:** evolution changes it by swap mutation (transpositions);
      TPE and random search treat it as a 24-way categorical. This tests whether
      structural locality helps.
    - **Free exhaustive baseline, before Run 8 (map only):** with qs fixed at qs + lc 1.4,
      the best budgets for each of the 24 stage orders from partition_map, and the overall
      best order: the exact optimum over the map's budget grid ({0, 2^8..2^20} for td, rho
      and ECM, pm1 {0, full}; 14 × 14 × 14 × 2 per order), not over all real-valued budgets.
      All 24 per-order optima are reported; card order "doesn't matter" only if every order's
      optimum is within the paired bootstrap interval of the best. The landscape (robust
      fitness over all 131,712 order × budget combinations: the share within the best's
      interval, plateau or isolated minimum) is reported too. Prediction: td ->
      rho -> ECM (p-1 off), or an order with ECM before rho at large budgets; within noise of
      A. The Run 8 searches should reach at least this on that subspace.
    - **Operators:** evolution's mutation and crossover come from `evolve/run8_space.py`, one
      bounds table shared with random search and TPE (the existing card-list operators did
      not cover this space); `run8_space_test.py` shows they reach all 24 orders, pm1 on and
      off, and every budget and qs gene across its bounds without leaving them.
    - **Order: a small balanced sanity arm first** (balanced 84-bit numbers, 18 per
      evaluation, 340 evaluations per run): every method should find about qs alone; worse
      means a harness bug, and the mixed arm does not start until it is fixed. **Then the
      mixed arm** (84-bit N, smaller factor in the partition study's seven bands, 12 per band
      = 84 numbers per evaluation).
    - **Fitness (c), robust**, reference qs + lc 1.4 alone on the same numbers; **ACCEPT
      gate** (no band worse than 1.5× the reference under any pricing), **checked on the
      sealed numbers, 80 per band** as in the partition study; **verdict on sealed numbers,
      run once.** Seeds: tuning 8000000 + 100·pb + 84, sealed 8500000 + 100·pb + 84
      (unused so far); every population through `oracle.check`.
    - **Reported:** the winning genomes' cards and budgets, per-band ratios under all three
      pricings, and the official-only vs robust difference (as in the partition study).
    - **Prediction (two clauses, each falsifiable):**
      - (a) TPE reaches a fitness at least as good as evolution's best-of-4 final fitness
        within fewer evaluations;
      - (b) at the full budget, TPE's best ties or beats evolution's best.
      - TIE = the paired bootstrap interval of the per-number log-ratio on the same sealed
        numbers includes 0. If a clause fails, it is recorded which: (a) failing = evolution
        converges faster; (b) failing = evolution finds better genomes. Random search is
        predicted clearly worst.
    - **Time estimate, re-measured at 84 numbers per evaluation** (lampcore --types, one
      process, Oct 24): 0.31–0.76 s per evaluation on the mixed arm (allocation A 0.32, the
      official-only optimum 0.31, wide budgets 0.57, qs + lc 1.4 alone 0.65, slow qs genes
      kc 1 / mc 12 0.76), and 0.14–0.33 s on the balanced arm (18 numbers). Allowing 1.0 s
      for slow genomes: mixed arm 3 methods × 8 seeds × 1,360 = 32,640 evaluations, 2.8–9.1
      core-hours, about 21–68 minutes on 8 cores. TPE is sequential within a seed (7–23
      minutes per seed plus Optuna's own overhead), with its 8 seeds in parallel. Sanity
      arm: 3 × 8 × 340 = 8,160 evaluations at 0.14–0.5 s, about 2–9 minutes. Sealed verdict
      (560 numbers per genome, about 4–6 s each): a few minutes.
  - **Consequence: every run scored for Run 8 must record per-type op counts** (the
    types `calibrate.py` reprices), not just total ops. **MET Oct 24:** lampcore --types,
    with parity against Python on every parity pair and existing results recomputed exactly
    (NOTES.md, lampcore per-type op counters). Remaining: Run 8's harness must call
    run_many(types=True) and optypes.robust; sq, ps and cfrac stay unpriced. As it stood:
    - Run 8's evaluation path (Run 6's harness: `evolve_scale.measure_fast` ->
      `fastlamps.run_many`) records total ops, factor, tests and hits only, without
      even the phase columns.
    - Phase columns are not enough: the repricing needs splits within phases (sieve
      updates vs scans; setup, confirm and lp full vs small; sqrt multiplies vs gcd
      steps; ECM setup Euclid steps), which today come only from Python traces, far too
      slow for evolution.
    - `calibrate.py` prices only ecm, qs and rho. td, sq, ps, pm1 and cfrac (and the race,
      by its sides) have no mapping.
    - Needed before Run 8, planning only for now: lampcore emits per-type counters for
      every card (with parity against Python and an identity check that they sum to
      each phase and to total ops), a price mapping for every card written in NOTES
      before use, and the robust fitness computed from those counters in the harness.

## Illumination maps (planning; visualization only)

Pictures of what each lamp touches, op by op. Nothing here changes a score, a cap or a
card: every op count stays exactly as it is.

- **Opt-in tracer.**
  - Start from `~/lpwvideo/tracer_draft.patch`: a module-level `lamps.EVENTS`, None by
    default. Set it to [] and each lamp appends (kind, op index, ...) tuples naming what
    each op touched. It covers td, sq, rho, pm1, ps, and the stage boundaries in run();
    qs needs its own events (below).
  - Read-only: events read m.ops and never charge.
  - Acceptance:
    - parity.py unchanged and still 0 mismatches. The tracer is Python only; lampcore
      is untouched.
    - A new check: on the parity numbers, EVENTS on vs off gives identical ops, factor,
      tests, hits and phases. Every event's op index is non-decreasing, and the last
      one is at most the run's total.
- **Per-lamp station maps.**
  - One map per lamp: the positions it visits (td's divisors, sq's x per multiplier k,
    rho's walk, pm1's primes, ps's blocks), against the op clock.
  - Counts drawn on each map:
    - overlap: positions visited more than once, within a lamp or across the stages of
      one genome (e.g. td's divisors re-covered by a ps block);
    - waste: ops spent on positions that could not have split this N. For planted
      factors this is known exactly: td past p, sq windows that cannot contain the
      square, a ps block that contains neither p nor q.
- **The qs ledger picture.**
  - qs events: each polynomial, each sieve candidate (full, partial, discarded), each
    relation entering the matrix, each large-prime pair combined, the dependency that
    split N.
  - The picture: rows filling toward F + delta on the op clock, coloured by source
    (full vs combined), with the phase split underneath. It is the relation economy's
    ledger, drawn before the refactor exists.
- **Parallel lines on a shared op clock.**
  - Per lamp: the stages of one genome as parallel lines, so a run reads as which lamp
    was lit when.
  - Per number: several numbers on one clock, the same genome on each, so the spread
    behind the mean and the worst case is visible.
  - CRT view: one lamp's walk shown twice, mod p and mod q, as two lines. A split is the
    moment one line closes (a collision, a square, p-1 smooth) and the other does not.
    For rho and pm1 this is the whole mechanism.
  - Visualization only: no op is charged for any of it, and nothing is read back into a
    score or into evolution.
- **Bits-per-op measures (report only, never fitness),** two separate measures, never
  merged: (1) size-posterior bits removed per op, for all lamps; (2) location-window facts
  per op, only for td, sq and ps.

## Stage 9.5: across-numbers selector (planning only)

After Stage 9, before the partition study. The portfolio move (MOVES.md, "Learned selector
across numbers"): instead of racing stages on every number, choose the stage or race for each
number from what is known about it before any work is done.

- **Selector input:** only what is free or charged. N's bit length is free. Any feature that
  does arithmetic on N (a quick trial division, a residue test) is charged as performed, on
  the same meter as the factoring.
- **Learned across numbers, not within one:** trained on tuning seeds, scored on sealed
  numbers, with the usual bootstrap.
- **Why not a per-N bandit:** rho and ECM report only success (ECM's curves are
  memoryless), so within one number they give no reward signal before they finish. Only qs
  reports progress (relations found / relations needed). A per-N bandit could only steer qs.
- **Expected shape:** on balanced numbers of one size, a selector by size alone reduces to a
  lookup table of the best genome per size, so it should only pay on a mixed population.
  That ties it to the partition study, which measures that population.
- Cost model and prediction go into NOTES before any code, as for every stage.

## Sanity checks after Stage 9 (outside references only)

- ECM miss rate at 56-70 bits against Milan's ~1% (two-prime numbers, tuned B1/B2).
- Our tuned qs factor-base size and sieve width against Milan's SIQS table (60 bits: FB 60,
  M 10000; 80 bits: FB 110, M 14000), as a reference only. Any large gap is explained;
  his values are not copied.

## Partition study (planning; no code yet)

How should a fixed op budget be split across lamps when the size of the smaller factor
is not known in advance?

- **Cost map.**
  - Bands: the smaller factor p in log-spaced bands, bits(p) in [b, b + w) for a fixed
    width w, from small factors up to balanced (p near sqrt N).
  - Planted factors: in each band, numbers N = p * q of a fixed total size with p drawn
    uniformly from the band (fixed seeds, new seed range).
  - Each lamp (and the tuned qs card) is run on every band, giving the ops to factor
    by band, with the usual bootstrap intervals and misses at the cap marked.
- **Optimal search allocation under a prior.**
  - A prior: the probability of each band.
  - Allocation: **sequential budgets, not races** (Stage 9 ruled out the fixed-slice race
    against qs). Each pre-stage (td, rho, p-1, ECM) gets a fixed op budget, in order, then
    qs runs to the cap. The budgets are the genes: the deferred budget-split idea, without
    interleaving. The allocation minimizes expected ops under the prior, given the cost
    map; it is computed from the map, then measured by running it, not trusted as computed.
  - **Prerequisite: a per-stage op-budget gene.** Checked Oct 24: no stage has one. Stages
    end only by their own bounds (td's a, pm1's b, ECM's curves) or the shared cap, which
    ends the whole run as a miss. The gene is added so that reaching a stage's budget ends
    that stage without a factor and the next stage runs. Cost model and prediction in NOTES
    first; then a one-switch identity (budget 0 = stage skipped; budget at or past the
    stage's own end = today's behaviour), parity and a mutation test.
  - **Prediction (to be written in NOTES before it runs):** on a mixed population,
    sequential budgets beat qs alone, as the p-1 front already does; on a single-kind
    balanced population, budgets near 0 win (qs alone).
- **Scores.**
  - Total ops over the population (expected cost under the prior).
  - The largest band's ops (the worst band's mean), so an allocation cannot buy a good
    total by abandoning one band.
  - Span reported alongside work: span = max ops over lanes, work = total ops. Span is
    never fitness unless decided.
  - The "best single lamp per band" column is a hindsight benchmark: it needs each
    number's band, i.e. the unknown factor size, so it must never be promoted to fitness.
- **Prediction (stated before measurement).**
  - Balanced semiprimes: little gain. The prior puts all its mass on one band, so the
    best allocation is close to the best single lamp for that band.
  - A mixed population (prior spread over bands): clear gain over any single lamp,
    because cheap small-factor lamps (td, rho, pm1, ECM) clear the low bands for a
    small share of the budget before qs takes the rest.

## Partition study part 2 (map only, no new runs)

- Index-rule stage order (Weitzman 1979): order the pre-stages by success chance per unit
  cost from the existing partition map, and compare with td -> rho -> pm1 -> ecm.

## Theory checks (after Stage 10)

- Fitted L-constants against theory: qs ~1, CFRAC ~sqrt 2, ECM ~sqrt 2 in p.
- Psi(x, y)-predicted qs relation yield against measured, per size.
- rho steps against sqrt(pi p / 2) plus Brent's overhead.
- A pre-registered extrapolation: fit on 54-84 bits, predict cost and crossovers at 96-100
  bits, write the predictions down, then measure.

## Search structure after Run 8 (planning only)

Ideas from evolving bodies over terrain, for after Run 8. Each gets a cost model and a
prediction in NOTES before code, as usual. Fitness is (c) robust throughout (Run 8 scoring).

1. **MAP-Elites over the number line** (Mouret & Clune 2015, arXiv 1504.04909).
   - Grid = total bits x smaller-factor bits (the leader-table cells).
   - One elite genome per cell, fitness (c) robust. Each step: mutate a random cell's
     elite, evaluate it, and replace an elite only if better.
   - The filled grid is the illumination map, which ties the tracer side task to search.
   - Optional second grid by behaviour: shares of ops in sieve / ECM / rho.
   - Prediction: the per-cell elites match or beat Run 8's single-fitness winner in most
     cells, with lineages crossing cells (stepping stones).
   - Tool: pyribs, reused (reuse rule); our harness is its evaluator, outside any charged
     path.
2. **POET-style populations** (Wang et al. 2019, arXiv 1901.01753).
   - Mutate population settings (bits, factor ratio, p-1 smoothness, multiplier class).
     Keep a population only if no lamp finishes it trivially and not all hit the cap.
   - Pair each population with its champion. Try transfers between pairs; replace only if
     better.
   - **Guard:** generated populations are training only. Verdicts stay on the fixed sealed
     populations.
   - Tool considered: Uber's POET reference code. Not used: it is built around its own
     terrain generator and neural-network agents; the outer loop is small enough to write.
3. **NEAT-style protection of new structure** (Stanley & Miikkulainen 2002).
   - Group genomes by card structure. A new structure gets a fixed tuning budget inside its
     group before competing overall.
   - Required before new cards (SQUFOF mode, p+1, torsion ECM) enter Run 8-style evolution.
   - Tool considered: neat-python. Not used: it evolves neural networks; we borrow only the
     speciation idea, a grouping step inside our existing islands harness.
4. **Structure and genes co-evolved** (Sims 1994): which cards, and in what order, evolve
   together with their genes. After Run 8. Tool: none to reuse; our mutation operators
   already change card lists and genes, and this extends them.

## Learning from all algorithms

Status: Phase 0 (MOVES.md) done, Oct 23. Phase 1 waits for Stage 9. The code-level pilot
comes after Run 8.

So far evolution only tunes genes inside cards we wrote. This asks where new cards and new
code come from: first by cataloguing the moves good algorithms are made of, then by letting
a model propose code changes to one card, under a harness it cannot touch.

- **Move catalogue (`MOVES.md`, repo root).**
  - One row per move: where it comes from, where it already appears in factoring, one
    untried candidate in our deck, and Status | Conditions | Evidence.
  - A catalogue, not a commitment: a row becomes work only with a full cost model in
    NOTES first, as for any card. The cost-model sketch for a row is written then.
  - Pilot proposals (below) name the move they use, so wins and losses can be read back
    against the catalogue.
- **Phase 0: create MOVES.md (done, Oct 23).**
  - Built from the deep-dive table: 16 moves, plus the two measured rows below.
  - Status column per move: pays / ruled out / untested, each with its conditions: the
    sizes, the pricing (official, ruint- or Montgomery-calibrated), and the cards it was
    measured with.
  - Statuses at creation: Portfolio and selection IN PROGRESS (Stage 9); every other move
    untested; and two measured rows, from results already in NOTES/README:
    - p - 1 front (leading p - 1 before qs): PAYS 1.05-1.24x in total ops at 72-84 bits
      (Run 6 ablation, L53-0972; 1.14-1.17x for L54-0938), official pricing.
    - CFRAC standalone: RULED OUT. 3.7x / 5.2x tuned qs's ops at 72 / 84 bits (predicted
      ~6x / ~10x), official op pricing.
- **Phase 1: five moves, one at a time, in this order, each through the full sequence.**
  1. CFRAC early abort (genes a, b; charging already in NOTES).
  2. SQUFOF mode on the CFRAC card (the same sqrt(kN) recurrence and Q_i stream; its
     rival is rho/Hart, class N^1/4, not qs). Its multiplier race (none first, then
     Gower-Wagstaff's 15 square-free multipliers) runs through the Stage 9 race.
  3. Batch smoothness test (product / remainder tree in place of per-candidate trial
     division), checked on qs's confirmation as well as on CFRAC's residues.
     Prerequisite: the oversized-multiply pricing rule (rounded up to N-sized multiplies)
     in NOTES first. MET: rule written in NOTES, Oct 24.
  4. p + 1 card (Lucas sequences).
  5. ECM torsion gene (family suyama12 | z2z8, both in Montgomery form, the same x-only
     ladder).
  6. Residue filters before square tests (sq card, SQUFOF mode).
  7. Luby restarts for rho.
  8. ECM PRAC chains.
  9. ECM batch inversion across curves.
  10. Relation filtering + excess-stop rule (ledger).
  (6-10 appended from the math survey; MOVES.md has each row's prediction.)
  - **Before Phase 2 (the code-level pilot): the charged number type in lampcore** (MOVES.md,
    meter guard).
- **Race reopened (from the math survey):** geometric (doubling) slices on the mixed
  population, against sequential budgets (MOVES.md, "Geometric (doubling) race slices").
  - Outside priors (MOVES.md, outside evidence), stated in each move's prediction: CFRAC
    still loses after batching; SQUFOF is only competitive below ~60 bits.
  - Per move, in order:
    1. cost model and predicted ratio in NOTES, before code;
    2. implementation;
    3. one-op mutation test;
    4. Python/Rust parity;
    5. genes fixed on tuning seeds, then the verdict on sealed seeds (run once);
    6. scored under the official count and both calibrated pricings (`calibrate.py`);
    7. verdict recorded in MOVES.md with its conditions.
  - A loss is recorded, not deleted. A ruled-out move is not retried unless its
    conditions change (a different size, pricing or card), and the entry says which
    changed.
- **Code-level evolution pilot: one card, CFRAC first (after Run 8).**
  - **License gate (Phase 2, before the pilot starts; the repo is MIT):** a code-similarity
    check of generated code against the known GPL factoring codebases (java-math-library,
    GMP-ECM, YAFU, msieve), or a stated restriction on what the model may be shown and
    produce. No pilot run without one of the two in place.
  - Why CFRAC: it loses (3.7x / 5.2x tuned qs's ops at 72/84 bits), and its cost has an
    obvious target. Every Q_i is a candidate, trial-divided at F ops, with no sieve to
    filter them.
  - Baseline: if Phase 1 has run (it comes first), the baseline is CFRAC with early abort,
    not plain CFRAC.
  - A proposal that rediscovers a move already in the deck is recorded as "rediscovered",
    not counted as a win.
  - What the model may change: the card's source only (`cfrac.py`). It never sees or
    edits the harness: meter, ledger, factor base, relation check, acceptance tests,
    parity, numbers.
  - Charging lives in the harness, not the card:
    - The card receives a meter it cannot modify or bypass. Arithmetic on N-sized values
      goes through charged harness operations.
    - A static check on every proposal (AST, before it runs) rejects imports outside an
      allowlist and any uncharged route to the same arithmetic (builtin three-argument
      pow, math.gcd, other big-number libraries, reaching into the meter's state).
    - If the existing card cannot be written against that interface as it stands, the
      interface comes first, with an identity check: today's CFRAC on it equals today's
      CFRAC op for op.
    - The ledger's relation check is on for every proposal (required for evolved sources,
      per the relation-economy rules), so an invalid relation pays and earns nothing.
  - Every proposal, before it is scored:
    - acceptance as for CFRAC (100% at 40-60 bits, every relation passes the check);
    - mutation tests: a one-op change to the charging of the touched code is caught;
    - the cfrac identity and parity checks rerun. Parity for the final candidate needs
      its Rust port, which is done by hand and checked like any port.
  - Selection on tuning seeds only (a new seed range at 72/78/84 bits). The final verdict
    is on sealed numbers: a seed range fixed and written here before the pilot starts,
    never run until the verdict, run once.
  - Budget stated in advance: a fixed number of proposals and evaluation runs, written
    here before the pilot starts. No rerunning the sealed numbers.
  - Success: a correct, honestly charged change that beats the baseline on the sealed
    numbers (log2 mean ops, with the usual bootstrap interval clear of the baseline's).
  - Prediction (stated before measurement): a win on the trial-division target, narrowing
    CFRAC's constant but not its growth, so it still loses to tuned qs. Beating qs is not
    the test. Against plain CFRAC the obvious win is early abort; against the
    early-abort baseline that would only be "rediscovered", so the prediction is restated
    with the baseline when the pilot starts.
  - Reported whatever the outcome, including proposals that failed the static check,
    acceptance or mutation tests, and why.
