# Decision log

## 2026-10-22 — The cumulative total is the scoreboard

- **Efficiency is judged by cumulative totals.** Watts are counted from the first operation to the last, for every test number, and summed. Lumens are the stations darkened by the end. Cumulative lumens ÷ cumulative watts is the algorithm's efficiency; its inverse is the inefficiency.
- **The running curve is the diagnostic, not the score.** Lumens plotted against cumulative watts shows *where* the watts went (steady sweep, ballast up front, scattered lucky hits), which is what you need to improve a bulb.
- **How a station goes dark.** A station s is dark once the algorithm would have caught p if p = s. This is measured by planting the secret: run on many semiprimes whose p values are spread across the stations, and record the cumulative watts each one took. It works the same way for lucky and luck-free methods.
- **Runs 1 and 2 used worst-case scoring.** Run 3 starts over on cumulative scoring, with fresh seeds, and records worst cases alongside so the two can be compared.

## 2026-10-22 — Luck by design has to pay for its prediction

- A luck-by-design card only helps when predicting a good test is cheaper than running a bad one. For Hart-style square searches a test costs 1 op, so ranking candidates (14 ops each) can't pay.
- The hit-rate column is per *test*, and what counts as a test differs by lamp (a gcd batch in rho, a square test in a square search). Compare hit rates within a lamp family, not across families.
- A gain on 12 validation numbers is a lead, not a result. Recheck on a larger fresh sample before writing it down (luck-33 shrank from 0.5 to 0.17 in log₂ on 80 numbers).

## 2026-10-22 — Small sizes pick constants; scale picks exponents

- Below about 54 bits, constants decide the winner: the Hart family's small constant beat rho. From 60 bits up, the exponent decides: rho's N^(1/4) beats the Hart family's N^(1/3), by about 5× at 78 bits.
- Evolution scored at 32–48 bits can only tune constants. To grow a better exponent, fitness has to be measured where exponents dominate: run evolution through the Rust core at 60+ bits.
- Big-number results are trusted only through `lampcore` after `parity.py` passes.

## 2026-10-23 — Square-search windows end at √(kN) + width, inclusive

- **The window is a range of x, not a count.** The theory window for multiplier k is √(kN) ≤ x ≤ √(kN) + width. The old code tested `int(width)` values from ⌈√(kN)⌉, which drops the last x whenever √(kN)'s fractional part pushes the range across an integer. This caused Lehman's 66-bit miss (k = 59881, width 1.73, needed x0 + 1). The 0.25 constant was correct, and widening it would have hidden the bug.
- **Never take a float sqrt of kN.** Past 60-bit N it loses about 10 bits. Use the exact integer square root s and add f = (kN − s²)/(2s), converting both to float before dividing. Python and Rust use the same expressions, so parity holds.
- **Instrumentation is read-only.** Both cores report the winning stage and a square-search win's k. Every gate compares op counts with and without it.
- **Coverage rule: complete is not the same as affordable.** A genome whose stages stop short of √N gets a fallback tail, charged and flagged. The no-luck fallback, trial division to √N, is provably complete but can exceed the cap. The luck fallback, rho, is heuristic: it has no proven bound, and it can return nothing when its gcd hits N. The rule is opt-in (`lamps.use_coverage_rule()`), so replays of Runs 2–5 are unchanged.
- **no-luck-32 at 78 bits.** Its square search, block flash, and trial division all stop below the secret (p = 2^38.3), so it can never be caught. Under the 2^29 cap it never gets that far: the block flash uses up the budget first. With the tail it becomes catchable in principle (trial division needs about 2^37.3 operations) but is still over budget, so the cell keeps its *.

## 2026-10-23 — Past wins need error bars at the sizes they claim

- **Stage 2's comparisons come with a 95% interval.** The statistic is log₂(mean ops), the total-work scoreboard. The interval is a bootstrap over the numbers in each (algorithm, size) cell: a fresh `random.Random(2026)` per cell, 10,000 resamples, percentile method. Misses are left out of the cell and counted beside it. Overlapping intervals mean within noise.
- **At 54–78 bits only the exponent result survives.** Rho and its variants beat Hart ×480 from 60 bits up. Every evolved win from Runs 3–4 (beating rho, beating Hart ×480, luck-34 over rho, luck-33 over rho) is within noise or reversed at these sizes. The small-size wins were measured at 36–48 bits, so this doesn't refute them there; it says they don't carry to scale.
- **Complete vs affordable is a property of the genome.** no-luck-32 misses at 66 bits in the Stage 2 set (N = 32724704014144553683) as well as at 78 bits in the Stage 1 set, both times because its stages stop short of √N (here p = 2^32.12, above the block flash's 2^31.99 and the trial division's 2^31.97). The shortfall shows up at more than one size, so it belongs to the genome, not to one unlucky number.

## 2026-10-23 — Quadratic-sieve card ("qs"): cost model, written before any code

The op unit is the one rho pays: one modular multiply of N-sized numbers = 1 op. **Principle: qs is never cheaper per unit of work than rho; when in doubt, overcharge.** Every small-number step below (an add mod p, a log-add into a sieve cell, a word XOR) costs a full op, even though it is far cheaper than a multiply mod N. The model is fixed before the first scored run, and the charges below are the only ones qs pays.

**Variant.** Self-initializing multiple-polynomial QS (SIQS) on kN, no large-prime variation in this version. Factor base: −1, 2, the primes p ≤ B dividing k, and the odd primes p ≤ B with (kN | p) = 1, F entries in all. Sieve interval [−M, M] per polynomial, 2M + 1 cells. Genes (provisional): k by the existing `ks` ranking, B, M, and the sieve threshold slack.

**Charges, phase by phase** (each is counted separately so the per-phase breakdown can be checked):

1. **Multiplier choice.** `ks` scoring, charged as now: 14 ops per candidate k (one per small prime).
2. **Factor base.** For each prime p ≤ B: Euler's criterion (kN mod p)^((p−1)/2) mod p, charged 1 op per modular multiply of square-and-multiply, i.e. bit_length(e) + popcount(e) − 1 for exponent e. For each prime kept: Tonelli–Shanks √(kN) mod p, 1 op per modular multiply it actually performs (counted, not estimated). **A prime that divides N:** if kN ≡ 0 (mod p) and p ∤ k, then p divides N, and qs returns p as the factor at once, having paid for the Euler-criterion work up to and including that prime.
3. **Polynomial setup.** Per A (product of s factor-base primes): 1 op per modular multiply and 1 op per extended-Euclid step for every inverse (A⁻¹ mod p for each p in the base, and the B_l values), plus 1 op per multiply building A and the B_l. Per switch to the next B within the same A (Gray code): 1 op per root updated, over the sieved primes (two roots for most primes, one for a prime dividing k).
4. **Sieve.** 1 op per sieve-array update (each step of p through the interval, for each root of each sieved prime), **and** 1 op per array cell scanned against the threshold (2M + 1 per polynomial). Small primes are sieved and charged like the rest. Four kinds of factor-base entry are **not sieved**, and they show up only through the threshold slack and in confirmation (phase 5), where every entry is tried: −1 (a sign, not a prime); 2; the s primes dividing A, where Q(x)/A has a single root mod p, which SIQS doesn't sieve; and prime powers p², p³, …, which are never sieved for any p.
5. **Candidate confirmation.** Per candidate cell that passes the threshold: 2 ops to form Q(x) = (Ax + B)² − kN, then 1 op per factor-base prime tried (all F of them, plus 1 op per extra division when p divides more than once). Candidates that turn out not smooth still pay in full.
6. **Linear algebra.** Dense Gaussian elimination over GF(2): ⌈rows × cols × rows / 64⌉ word ops, with rows = relations kept (F + δ, δ = 10 surplus) and cols = F. This is cubic, the honest cost of dense elimination, not rows × cols / 64. Block Lanczos and Wiedemann are not used; if they ever are, their formula gets written here first.
7. **Square root.** Per dependency tried: 1 op per modular multiply forming X = ∏(Ax + B) mod N and Y = ∏ p^(e_p/2) mod N (each power charged by square-and-multiply as in phase 2). Then gcd(X − Y, N), charged 1 op per Euclid step. Rho pays 1 op per gcd, so this deliberately overcharges qs, following the principle. A dependency giving a trivial factor still pays, and the next one is tried.

**Failures cost too.** If no dependency splits N, or the sieve runs out of polynomials, qs returns None after paying for everything it did, like every other lamp. Any retry pays again.

**Expected-value formulas** (to check measured counts against, per polynomial): sieve updates ≈ (2M + 1) · Σ_{sieved p} r_p / p, where the sum runs over the sieved primes only (not −1, not 2, not the s primes dividing the current A, no prime powers), with r_p = 1 for p | k and r_p = 2 otherwise; scans = 2M + 1; root switches = Σ_{sieved p} r_p per new B (one op per root updated, as in phase 3).

**Acceptance test (before any scored run):**

- **Completeness.** qs alone, cap 2^29, factors 100% of fresh balanced semiprimes `semiprimes_pq(bits, 40, 770000 + bits)` at 40, 44, 48, 52, 56, and 60 bits (240 numbers, a seed range no earlier stage has used). Any miss fails the test.
- **Exact accounting.** For every one of those runs, each phase's measured ops equal its formula above evaluated on that run's realized counts (primes tested, Tonelli–Shanks multiplies, A and B values, updates, cells, candidates, rows, dependencies, Euclid steps). Tolerance 0: a single op of difference fails.
- **Model agreement.** Over each size's 40 numbers, measured sieve updates and root switches agree with the expected-value formulas within ±5% in total, per phase.
- **Parity.** Gated by `parity.py` once the Rust port exists (Stage 4): ops, factor, tests, hits, stage, and k identical on every pair.

**Implementation notes (added with the code; the cost model above is unchanged):**

- **Acceptance result.** 240/240 factored, with 1 retry (40 bits, paid in full). Exact accounting matched on every phase of every run, tolerance 0. Sieve updates came within 0.01% of the expected-value formula at every size, and root switches matched exactly. `evolve/qs_accept.py` recomputes each formula from the run's raw inputs, and a one-op change to any phase's charge is caught.
- **bc = 1.5 is a tuned constant, not derived.** It was chosen on seeds 550000 + bits and 660000 + bits, never the acceptance seeds. At bc = 1.0, small N get a 12–17 prime factor base and sometimes run out of A combinations.
- **Open question: trivial dependencies.** On the tuning numbers at 40–48 bits, 1–2% had every dependency trivial (11–14 dependencies each). Chance would give about 2^-11 to 2^-14 per number, so these dependencies are not independent. The failure depends on N, k, and the factor-base size, and the mechanism is unexplained. The stopgap is to retry with the next multiplier in ks order, paying again in full.
- **Tests and hits.** One test per candidate confirmed (hit = smooth), and one per dependency tried (hit = it splits N).

## 2026-10-23 — qs beats rho from ~72 bits on an exponent

- qs beats rho from ~72 bits on an exponent, under overcharging; Run 6 must include sizes >= 72 or it can't see this.
- The worst case crosses first: qs's worst case is below rho's from 66 bits (2^18.58 vs 2^19.01), before the means cross at about 72. At 78 bits its worst case is about 2.2× lower and its mean about 1.5× lower (19.73 vs 20.29).
- Against Run 5's L44-0272, qs is still within noise at 78 bits. The bar for Run 6 is L44-0272 as well as plain rho, so this is not yet a win over the best evolved bulb.

## 2026-10-23 — qs in lampcore (Stage 4)

- `lampcore/src/qs.rs` is a line-by-line port of `evolve/qs.py`, with every charge made at the same point and in the same chunk, so even a run cut off by the cap stops in the same phase with the same tests and hits. No new charges. `parity.py` matches 692 qs pairs on ops, factor, tests, hits, stage, k, and the per-phase breakdown. These cover the acceptance numbers, the Stage 2 numbers at 66–78 bits, 12 numbers that force a retry, gene variants, qs after another stage, and a low cap. The 3,312 existing pairs still match. `qs_accept.py 8 rust` passes 240/240 with exact accounting. Rust is about 7× faster than the numpy-backed Python at 72–78 bits. The `kc` default is now 16 in both cores (it was 1 in Python; every committed run set it explicitly).

## 2026-10-23 — Bugs only random genomes caught

- Hand-picked parity cases missed three bugs; random genomes from the Run 6 decks found them.
  Parity now covers each, and none changed a committed result.
- **Two qs stages, one trace.** With qs twice in a genome, Python's per-phase trace kept only
  the last stage (lampcore's added up). Ops and factors always matched; only the per-phase
  report was wrong. The trace now accumulates over the run.
- **Block flash allocated before charging.** At 78–84 bits a random block size can mean
  2^30+ leaves, so lampcore built product trees of tens to hundreds of GB before charging a
  single op. Both cores now stop before allocating when the trees' minimum charge exceeds
  the budget (the run would miss anyway).
- **p − 1 sieve size and overflow.** A large bound made lampcore sieve ~2 GB per worker (now
  bit-packed, and both cores skip the sieve when B/ln B alone exceeds the budget). The
  prime-power loop's `pk * p` would wrap in u64 for primes past 2^32 (now u128). No cap used
  so far reaches primes that large, so the wrap never affected a result.
- **qs sieve count past the interval.** With a small sieve interval (mc below about 0.5), a
  factor-base prime can be wider than the interval (p > 2M + 1), so a root can start past its
  end. Python counts (width - 1 - start) // p + 1 = 0 steps there; lampcore computed it in
  usize, which wrapped to ~2^58 sieve ops and missed. Found by the boundary sweep below; no
  committed run used mc < 1. lampcore now guards start < width, and parity covers mc 0.05,
  0.1, 0.25 and 0.5 at 48-84 bits, asserting such roots occur for mc <= 0.25.

## 2026-10-23 — Run 6

- Run 6: evolution keeps qs on both decks; within the luck champions the leading p − 1 pays (removing it costs 1.05–1.24×; it wins 12–23 of 80); they lose to N51-0917 on weaker qs genes. Stages after the first qs never run (ablation, 240/240), so the no-luck champions are tuned qs; mc pinned at the bottom of its mutation range (1.0).

## 2026-10-23 — Stage 7: large-prime variation for qs, cost model, written before any code

Same principle as qs: **never cheaper per unit of work than rho; when in doubt, overcharge.** Every step below costs a full op, and these are the only new charges. Phases 1–7 of the qs model are unchanged; a new phase 8 holds the large-prime work so the breakdown stays checkable.

**Variant.** Single large prime (1LP) on the existing SIQS card, as one new gene, not a new card: `lc` in [1.0, 2.0], large-prime bound L = B^lc. A candidate whose cofactor after factor-base trial division is 1 is a full relation, as now; one whose cofactor q satisfies 1 < q < L is a **partial**, filed by q; two partials with the same q combine into one full relation. **lc = 1.0 is today's qs, op for op** (no cofactor can be both > 1 and < B, and the threshold below reduces to today's), and every existing genome, which has no lc, reads as 1.0. So no committed result moves.

- **Why a cofactor below L is prime, with no primality test.** After trial division by the whole factor base, the cofactor has no prime factor ≤ B: the primes ≤ B outside the base have (kN | p) = −1 and never divide Q(x). A composite cofactor is therefore ≥ B², and L ≤ B² because lc ≤ 2.
- **Threshold.** Sieve threshold T = log₂(M·√(kN/2)) − (tc + lc − 1)·log₂ B: the usual slack plus log₂(L/B), so candidates with one large prime can pass. More candidates pass, and each one pays phase 5 in full. That is where most of the variant's extra cost is.

**Charges.**

5. **Candidate confirmation (unchanged, more candidates).** Every candidate that passes the lowered threshold pays 2 ops to form Q(x), F ops of trial division, and 1 per extra division, whether it ends up full, partial, or discarded. This *is* the cofactor's trial division, charged in full.
8. **Large primes** (new phase "lp"), for each candidate whose cofactor q is > 1:
   - **Bound check:** 1 op (q < L). A cofactor ≥ L is discarded after this op.
   - **Divides N:** 1 op (N mod q). If q divides N, qs returns q at once, like a factor-base prime dividing N in phase 2.
   - **Hash:** 1 op for the lookup by q. A miss costs 1 op more to insert the partial (stores u = Ax + B, its exponent vector, and q).
   - **Combine** (on a hit): 1 op for u₁u₂ mod N, plus F ops to add the two exponent vectors, 1 per entry. The combined relation goes into the same table as full ones; the stored partial stays, so k partials sharing a q give k − 1 relations. A combination whose u₁u₂ repeats one already seen (up to sign) is dropped after paying.
6. **Linear algebra (unchanged):** rows = relations kept (F + δ, δ = 10), columns F. Large primes need no columns: each appears squared in a combined relation.
7. **Square root (one addition):** each combined relation in a dependency also multiplies its q into Y: 1 op per modular multiply, as for the other factors of Y.

**Failures cost too:** a run that misses pays for everything, partial table included. A retry with the next multiplier starts with an empty table and pays again.

**Tests and hits (luck meter):** one test per candidate confirmed, as now. A hit is a full relation or a partial that passes the bound check. Combining is bookkeeping, not a new test.

**Acceptance test (before any scored run):**

- **Identity.** With lc = 1.0, the card matches today's qs on ops, factor, tests, hits, and every phase (lp = 0), on the qs acceptance numbers (40–60 bits) and the Stage 2 numbers at 66/72/78. Tolerance 0.
- **Completeness.** With lc at a value tuned on seeds 1700000 + bits (never the acceptance or ACCEPT seeds), it factors 100% of `semiprimes_pq(bits, 40, 770000 + bits)` at 40–60 bits, cap 2^29.
- **Exact accounting.** Each phase's measured ops, phase 8 included, equal the formulas above evaluated on the run's realized counts: candidates, cofactors > 1, cofactors < L, lookups, inserts, combinations, duplicate combinations, and large primes multiplied into Y. Tolerance 0. A one-op change to any lp charge must be caught (as in `qs_accept.py`).
- **Relation check (harness only, not charged):** every combined relation satisfies (u₁u₂)² ≡ the product its exponent vector and q² describe (mod N), and every dependency tried satisfies X² ≡ Y² (mod N).
- **Parity:** after the Rust port, gated by `parity.py` as qs was, including lc = 1.0 identity pairs and random genomes with lc > 1.

**In evolution:** lc gets a mutation range of 1.0..2.0, opt-in like `use_wide_qs_ranges()`. Without the opt-in, rand_stage and mutate never touch lc, so Run 6 replays stay unchanged.

**Clarifications made while implementing (qs.py; the charges are unchanged):**
- With lc = 1.0, phase 8 does not run at all: there is no bound check. Charging 1 op per cofactor > 1 there would break the lc = 1.0 identity. The bound check, and everything after it, runs only when lc > 1.
- Order per candidate: the bound check, then the luck-meter test (hit = smooth, or a cofactor below L), then N mod q (if q divides N, qs returns q), then the lookup, then the insert or the combination.
- The threshold slack is computed as tc + (lc − 1), not tc + lc − 1, so lc = 1.0 gives today's threshold bit for bit in floating point. The Rust port must match.
- A partial isn't deduplicated by u: duplicates are caught when relations combine (u₁u₂ up to sign), as written above. A relation from a partial combined with itself can only give a trivial dependency.

**lc sweep (`evolve/stage7_lc_sweep.py`, tuning seeds).** lc = 1.4 is pre-registered for the ACCEPT comparison: best mean at 72/78/84 on the tuning seeds, tied with 1.2 at 84. Pairing yield is 0.07–0.21 combined relations per partial, so partials do pair. The gain over lc = 1.0 is about 1.1×, inside the intervals at 78 and 84 bits. Identity check (`evolve/stage7_identity.py`): lc = 1.0, and lc absent, equal today's qs op for op on 1,920 runs.

**Comparison against tuned qs (the bar).** Tuned qs means qs alone with kc 32, bc 1.1, mc 0.25, tc 1.38 (the best cell of `qs_boundary_sweep.py`). The large-prime card uses the same genes plus one lc. That lc is fixed in advance from a sweep over lc ∈ {1.0, 1.2, 1.4, 1.6, 1.8}, with bc and mc held at tuned qs's values. The sweep sees only the tuning seeds, `semiprimes_pq(bits, 40, 1700000 + bits)` at 72, 78 and 84 bits; their one job is to pick lc, and they are never used to judge the card. For each lc the sweep reports the pairing yield (combined relations per partial) beside the cost. A flat result can then be told apart from one where partials never paired, which would mean lc did nothing. The comparison runs on the Run 6 ACCEPT numbers: the Stage 2 numbers at 72 and 78 bits, and `semiprimes_pq(84, 80, 1300084)`, cap 2^28. For each size it reports log₂(mean ops) and the worst case with the index-250/9749 bootstrap, the per-phase breakdown (how much of any gain comes from fewer polynomials versus more confirmation), the pairing yield (combined relations per partial), and the growth per bit from 72 to 84. Verdict: a win only where the large-prime card's interval sits below tuned qs's; overlap means within noise. The expectation, stated in advance: at 72–84 bits the gain is small or negative. A single large prime typically pays off at larger N than these, and the overcharged confirmation (F ops per extra candidate) works against it here.
