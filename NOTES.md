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
- Under calibrated pricing, qs + lc 1.4 alone beats L53-0972 by 1.67× (ruint, partition sealed run, Oct 24); Run 6's champion was tuned under official pricing.

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

## 2026-10-23 — Ledger: the charged relation check, cost model, written before any code

Part of the relation-economy refactor (PLAN.md, "Relation economy"; `ledger.py`, `qs.rs`'s `Ledger`). Same principle as every card: **every op counted, when in doubt overcharge.** The check is new phase 9, "check", charged by the ledger; phases 1–8 are unchanged.

**Switch.** The check is a per-source setting, **off by default**. With it off, the ledger trusts what it is given and every source costs exactly what it costs today, op for op (qs: `relation_economy_identity.py`). qs never turns it on: its relations are correct by construction (the harness relation check in `stage7_accept.py` verifies that on every run). The check exists for sources whose relations are *not* correct by construction, first of all evolved source genomes (PLAN.md, "Later"), where it is required. A source opts in; the ledger then checks every relation that source submits, before dedupe.

**Charges, per relation (u, e, y) checked**, for u² ≡ y²·∏ p^(e_p) (mod N):

- **u²:** square-and-multiply as in qs phase 7: cpow(u, 2, N) = 2 ops (the reduction of u mod N counted as the first multiply, then the square).
- **Right-hand side:** for each base entry with e_p > 0 (p ≥ 2), cpow(p, e_p, N) = bit_length(e_p) + popcount(e_p) − 1 ops, and 1 op per multiply joining it to the running product after the first. A combined relation (y > 1) adds cpow(y, 2, N) = 2 ops and 1 op to multiply it in. The sign entry e₋₁ costs 1 op when odd (negation mod N).
- **Compare:** 1 op (the two residues; an overcharge, it is not a multiply).
- **Parity scan:** ceil(F/64) ops to read e mod 2 as F bits, at the same 64-bit-word rate as phase 6.

**Rejections pay first.**

- An **invalid** relation (the two sides differ) has paid the multiplies and the compare. It is rejected: not deduped, never a row.
- An **all-even** relation (every e_p even, y included) is a one-row dependency on its own: X = u, Y = y·∏ p^(e_p/2). It splits N exactly when u ≢ ±Y (mod N), so it is **not** rejected for being all even. That is the useful case of the square-Qᵢ relations CFRAC can produce below. It is rejected only when it is **trivial**, u ≡ ±Y (mod N): the gaming case, e.g. a source that submits u = 6 with e = (2 at 2, 2 at 3). Testing costs, for all-even relations only: cpow(p, e_p/2, N) per entry with e_p > 0, 1 op per joining multiply, 2 ops for y if y > 1 (1 op to raise y to the first power, 1 to multiply it in), and 2 ops for the two compares (u = Y, u = N − Y). This replaces "an all-even relation pays and is rejected" from the first brief and PLAN.md (decided with this entry). Rejecting every all-even relation would throw away real splits, and with the check on would change qs's relation set, so qs's ops would differ by more than the check's formula.

**Identity rule.** Check off: today's ops exactly, on every phase, every pair (parity's qs pairs plus the Run 6 ACCEPT numbers), Python and Rust. Check on, for qs as a test only: ops equal the check-off run's plus the formula above evaluated on the relations qs submitted, with the identical relation set, provided nothing was rejected. The run reports the rejection count; the expectation for qs is 0.

**Acceptance test:**
- the identity rule above;
- injected relations, harness only: a corrupted u (invalid), a trivial all-even relation, and a nontrivial all-even one are each charged exactly the formula. The first two are rejected, and the third is kept and splits N or not as its gcd says;
- a one-op mutation of each check charge is caught;
- parity after the Rust port, with lampcore printing a 9th phase column, "check" (0 when off), appended after lp.

**Clarifications made while implementing (`ledger.py`, `qs.rs`; the charges are unchanged):**
- Joining multiplies: y (or y², or y¹ in the trivial test) is one more factor of the product, joined like the primes: 1 op if a factor came before it, none if it is the only one. Square-and-multiply on u² is cpow(u, 2, N), the reduction of u mod N first, then the square.
- Order per relation: u², right-hand side, sign, compare (stop if invalid), parity scan (stop if any odd entry), trivial test. The check runs before dedupe, so a repeat pays its check and is then dropped as before.
- **qs does produce trivial relations**, against this entry's expectation of 0. Two partials with the same large prime and the same u mod N combine into u₁u₂ ≡ ±Y, which is the "partial combined with itself" case from Stage 7's clarifications. With the check off, that relation becomes a zero row and costs a useless square root later. With the check on, it is rejected, and qs collects one more relation instead, so on such a run the phases other than "check" differ from the check-off run. The acceptance test (`ledger_accept.py`) therefore asks for identity with the check-off run only on runs with no rejection. On every run it asks that the check phase equals the formula on the submitted relations, and that the rejections are exactly the relations the harness finds invalid or trivial.

**Comparisons between sources:** the check is on for all sources in a comparison if and only if any of them needs it. qs vs CFRAC runs with it off: both are correct by construction, and the harness relation check verifies both. (Decided with this entry; PLAN.md's relation-economy section amended to match, along with the all-even rule.)

## 2026-10-23 — CFRAC as a second relation source, cost model, written before any code

Continued fractions (Morrison–Brillhart) feeding the same `Ledger` as qs: one multiplier k per ledger, the same factor base (−1, 2, primes dividing k, odd p ≤ B with (kN | p) = 1). The base fits CFRAC unchanged: a prime p can divide Qᵢ only if kN is a square mod p. Same principle: **every op counted, every small-number step a full op, when in doubt overcharge.** Its own phases, "cf_step" and "cf_td", so the per-phase breakdown separates it from qs in a mixed run.

**The expansion of √(kN).** g = ⌊√(kN)⌋; P₀ = 0, Q₀ = 1, a₀ = g; then
Pᵢ₊₁ = aᵢQᵢ − Pᵢ, Qᵢ₊₁ = Qᵢ₋₁ + aᵢ(Pᵢ − Pᵢ₊₁), aᵢ₊₁ = ⌊(g + Pᵢ₊₁)/Qᵢ₊₁⌋, and numerators Aᵢ = aᵢAᵢ₋₁ + Aᵢ₋₂ (mod N), A₋₁ = 1, A₀ = g.
Relation: A²ᵢ₋₁ ≡ (−1)ⁱ Qᵢ (mod kN), so mod N, with 0 < Qᵢ < 2√(kN). So u = Aᵢ₋₁, y = 1, and e is (−1)ⁱQᵢ's exponent vector. It is correct by construction, so the ledger check stays off (see the ledger section).

**Charges.**

1. **Multiplier ("mult"):** as qs: 14 ops per candidate multiplier (ks scoring, kc candidates). On failure the next k gets a fresh ledger and pays again for everything.
2. **Factor base ("fb"):** the ledger's, as qs phase 2.
3. **Setup ("cf_step"):** g = ⌊√(kN)⌋, charged bit_length(kN) ops: an overcharge, since Newton converges in far fewer iterations.
4. **Per step ("cf_step"): 4 ops.** 1 for aᵢ₊₁ (one division), 1 for Pᵢ₊₁ (the multiply aᵢQᵢ), 1 for Qᵢ₋₁ + aᵢ(Pᵢ − Pᵢ₊₁) (one multiply), 1 for Aᵢ mod N (one modular multiply plus add). Every Qᵢ is produced at that price.
5. **Trial division of every Qᵢ ("cf_td"):** there is no sieve, so every residue is a candidate. The charge is qs phase 5's rate without the 2 ops to form g(x), since Qᵢ is already formed: F ops (1 per base entry tried, −1 included, as qs) plus 1 per extra division. The sign entry is free (the parity of i). One luck-meter test per residue; hit = smooth.
6. **Into the ledger:** a smooth Qᵢ gives (Aᵢ₋₁, e, 1), submitted with dedupe as qs's (free). Phases 6 and 7 (linear algebra, square root) are the ledger's, unchanged.

**Stopping.** The source runs until the ledger is full, or until Qᵢ = 1 at some i > 0, after that step is paid. That marks the end of the period, after which the relations repeat, and the attempt fails to the next k. Either way the cap applies, as everywhere.

**Genes.** kc and bc, read exactly as qs reads them (so a shared ledger built from either source's genes is the same ledger). There are no sieve genes. Large primes for CFRAC (the cofactor rule from Stage 7) are out of scope here, a later gene with its own cost model.

**Planned gene, not in the first implementation: early abort (genes a, b).** After trial division of Qᵢ by the first a primes of the base, the residue is dropped unless what is left has shrunk below Qᵢ^b. It is charged as the trial division actually done: an abandoned residue pays 1 op per base entry tried up to that point (−1 and 2 included, as now), plus its extra divisions, plus 1 op for the size comparison. A residue that survives goes on to pay the rest of the F entries as usual. No relation is ever accepted on a partial division. a = F (or b = 1) is today's charge plus the compare, so the identity is stated with the early abort absent, not at a particular (a, b). It is written down now so that the prediction below can be revisited with it: early abort is the classic remedy for CFRAC's full trial division of every residue, and could shrink the predicted gap by a constant factor, not change the growth.

**Residue size vs qs's.** CFRAC: 0 < Qᵢ < 2√(kN), typically about √(kN). qs: |g(x)| ≤ about M·√(kN/2), with M = mc·B. With tuned qs (mc 0.25, bc 1.1), B ≈ 1,190 at 72 bits and ≈ 2,400 at 84 bits, so M ≈ 300 and 600. qs's residues are about 2^7.7 and 2^8.7 times larger: CFRAC's are the smoother numbers, by roughly 8–9 bits. qs makes up for it by sieving: it confirms only the few cells above its threshold, while CFRAC trial-divides every residue at F ops each.

**Prediction (stated before measurement).** CFRAC alone, with tuned qs's kc and bc, loses to tuned qs at 72–84 bits, and the gap grows with size, because its growth per bit is steeper than qs's 0.149 (heuristically L^√2 against qs's L^1). The rough estimate behind the numbers: a CFRAC residue of about √(kN) is B-smooth with probability ≈ ρ(u), u = log Qᵢ / log B (Dickman's function; the base's half-density is offset by each base prime dividing twice as often). That gives about ρ(3.7) ≈ 0.01 at 72 bits and ρ(3.9) ≈ 0.006 at 84 bits, at F + 6 ops per residue and F + 10 relations needed. CFRAC alone is then about 2^20 at 72 bits and 2^22.5 at 84 bits: about 6× and about 10× tuned qs's 2^17.4 and 2^19.2. These are uncertain by about 2–3× either way, and a different bc may suit CFRAC better. qs + CFRAC into one ledger: no better than qs alone, as PLAN.md already states.

**Acceptance test:**
- CFRAC alone factors 100% of `semiprimes_pq(bits, 40, 770000 + bits)` at 40–60 bits, cap 2^29;
- exact accounting of every phase against the formulas above, on the realized counts (steps, residues, extra divisions);
- every relation passes the harness relation check;
- a one-op mutation of each charge is caught;
- parity after the Rust port.

**Result (`cfrac_compare.py`, Run 6 ACCEPT numbers, cap 2^28, no misses).**
- **CFRAC alone** (tuned qs's kc 32, bc 1.1) needs 3.7× tuned qs's ops at 72 bits and 5.2× at 84 (paired, intervals well clear of 1). The prediction was ~6× and ~10×. The result is inside the stated 2–3× uncertainty, but on the low side: the smoothness estimate was about 1.7× pessimistic.
- **Growth:** 0.188 log₂-ops per bit over 72→84, against tuned qs's 0.149. Steeper, as predicted, so the gap widens with size.
- **Where the ops go:** about 95% are in cf_td, the trial division of every residue (2^21.50 of 2^21.58 at 84 bits). That is exactly what early abort targets.
- **qs + CFRAC into one ledger** (fixed split: CFRAC first, to cs·(F + 10) relations) is worse than qs alone at every share, as predicted:

  | cs | Ops vs tuned qs |
  |---|---|
  | 0.1 | 1.30–1.43× |
  | 0.25 | 1.70–2.05× |
  | 0.5 | 2.39–3.14× |

  A CFRAC relation costs more than the sieving it saves.
- **Identity:** the split card at cs = 0 equals tuned qs op for op on all 240 numbers.

## 2026-10-23 — Stage 8: elliptic-curve card ("ecm"), cost model, written before any code

Same principle as every card: **every op counted as performed, never cheaper per unit of work than rho, when in doubt overcharge.** As in rho (where y² + c is one op), 1 op is one multiply or squaring mod N. Additions and subtractions mod N are free, and so is generating primes, as in pm1. Four phases, so the breakdown is checkable: "ecm_setup", "ecm_s1", "ecm_s2", "ecm_gcd". lampcore appends them after cf_td.

**Arithmetic.** Montgomery curves By² = x³ + Ax² + x, x-only in projective (X : Z), with a24 = (A + 2)/4 kept as a residue.

- **xDBL:** (X+Z)², (X−Z)², their product, a24·(difference), and the final multiply for Z: 2 squarings + 3 multiplies = **5 ops**.
- **xADD** (differential, P + Q from P, Q and P − Q = (X_d : Z_d)): two cross multiplies, two squarings, then multiplies by Z_d and X_d = **6 ops**. These are always performed, even when Z_d = 1: no special case, an overcharge.
- **Ladder for a scalar k ≥ 2:** R₀ = P, R₁ = xDBL(P), then for each bit of k below the top bit, one xADD and one xDBL. That is **5 + 11·(bit_length(k) − 1) ops**. It is used for every scalar multiply below, including powers of 2: one rule, an overcharge for 2^e.
- **Per ladder bit: 11 modular multiplies, every one charged:**

  | Step | Multiplies | Squarings |
  |---|---|---|
  | xADD | 4 (two cross products, then ·Z_d and ·X_d) | 2 |
  | xDBL | 3 | 2 |

  Optimized implementations do the same step in 10 or fewer (by keeping Z_d = 1, or merging with a24), so 11 is an overcharge.
- **The ladder is where an under-charge would hide.** It is more than 90% of a curve's stage-1 ops and runs one bit at a time inside two loops, so a step that skips a multiply, or charges a step once per prime instead of once per bit, would cut the total silently. The acceptance test therefore recounts the ladder independently: bits per scalar times 11, plus 5 per ladder. The mutation test raises each of the 11 charges in turn.

**Curve setup ("ecm_setup") and gcds are charged on rho's rule:** 1 op per modular multiply, and 1 op per gcd. Rho's own setup has no arithmetic (its x0 and c are genes). ECM's setup does arithmetic, so every multiply in it is charged, plus 1 op per Euclid step of its one inverse, as in qs's polynomial setup. That is an overcharge against rho's flat gcd charge.

**Curve setup, Suyama's parametrization, per curve.** σ is the curve's parameter (genes below). u = σ² − 5, v = 4σ; the starting point is (X : Z) = (u³ : v³), projective, so it needs no inverse. Then a24 = (v − u)³(3u + v) / (16u³v).

- **Charges:** 1 op each for σ², u², u³, v², v³, (v − u)², (v − u)³, ·(3u + v), u³·v, and ·16 (an overcharge: a small constant, still 1 op). One inverse of the denominator, 1 op per extended-Euclid step, as in qs's polynomial setup. 1 op for numerator · inverse. In all **11 + Euclid steps**.
- If the denominator is not invertible, gcd(denominator, N) is already computed by that Euclid run. If it is a proper factor, the card returns it (found in setup, still a hit for that curve). If it equals N, the curve is degenerate: it pays its setup and the next σ is tried.
- Suyama curves have group order divisible by 12. That is the torsion this family gives.

**Stage 1 ("ecm_s1").** For each prime p ≤ B1 in increasing order, multiply the point by q = p^e, the largest power of p not above B1, by the ladder: 5 + 11·(bit_length(q) − 1) ops. Then **1 op** for gcd(Z, N) ("ecm_gcd"; rho's charge for a gcd).
- 1 < g < N: return g, a hit.
- g = N: the curve failed (both factors at once). It pays and the next curve is tried, not stage 2.
- g = 1: go on to stage 2 if B2 > B1, else to the next curve.

As a rough check, stage 1 costs about 11·log₂(lcm(1..B1)) ≈ 16·B1 ops.

**Stage 2 ("ecm_s2", optional; B2 = b2·B1, b2 = 0 means none).** Standard baby-step giant-step continuation with fixed w = 210 (not a gene). Q is the stage-1 point.

- **Baby steps:** 2Q by xDBL (5 ops), then bQ for odd b < w/2 by xADD chains (b + 2 from b, 2Q and b − 2): 6 ops each, about 52 xADDs. Only the 24 values of b coprime to 210 are kept.
- **Giant steps:** W = wQ by the ladder; S_j0 = j₀W and S_(j0+1) by one ladder (it yields both), with j₀ = ⌊B1/w⌋. Then S_(j+1) = S_j + W, with difference S_(j−1): 6 ops per giant step, up to ⌈B2/w⌉.
- **Per pair (j, b)** where jw + b or jw − b is a prime in (B1, B2]: the cross term X_(S_j)·Z_b − X_b·Z_(S_j) (2 ops) multiplied into the running product (1 op), so **3 ops per pair**. One term covers both jw ± b.
- **Stage 2 is charged on the same rule as stage 1:** every modular multiply.
  - Baby and giant steps are xADDs at 6 each (4 multiplies + 2 squarings), and their ladders are charged as above.
  - The cross terms are 2 multiplies and the accumulation 1.
  - Nothing is precomputed for free except the primes in (B1, B2] and the list of b coprime to w.
- **Final:** 1 op for gcd(product, N) ("ecm_gcd"), read as after stage 1.

**Failures pay in full:** a curve that finds nothing pays setup, stage 1, stage 2 and its gcds, and the next curve (σ + 1) pays again. The card stops at the first factor, after `curves` curves, or at the cap.

**Genes.**
- **b1:** B1 = max(10, ⌊b1·exp((1/√2)·√(ln s · ln ln s))⌋) with s = √N, the factor size of a balanced semiprime (the card does not know p). That is about 570 at 72 bits and 1,100 at 84 with b1 = 1. Default 1.0.
- **b2:** B2 = b2·B1 (0 = no stage 2). Default 50.
- **curves:** default 10,000, so in practice the cap decides.
- **s0:** the first σ, an integer ≥ 6; curve i uses σ = s0 + i. Default 6. It is deterministic, so both cores agree.

**Luck meter (PLAN):** one test per curve, and a hit when the curve finds a factor (in setup, stage 1 or stage 2).

**Torsion families: a change from PLAN.md to review.** PLAN lists "plain Suyama, or a torsion-12 / torsion-16 family", but plain Suyama already is the torsion-12 family.
- **Proposal:** the first implementation is Suyama only. A second family with Z/2 × Z/8 torsion (16 | order), the luck-by-design knob, comes as a gene `family` with its own NOTES addendum: its parametrization multiplies are listed and counted the same way. They are not written here because I would rather pin the exact formula than state one I have not checked.

**Acceptance (before any scored run):**
- **Completeness, balanced:** default genes, cap 2^29, 100% of `semiprimes_pq(bits, 40, 2700000 + bits)` at 40–84 bits, a seed range no stage has used.
- **Completeness, unbalanced:** the same, on 40 semiprimes at each of 72, 78 and 84 bits with a smaller factor of 24, 28 and 32 bits. They come from a new generator `semiprimes_unbalanced(bits, pbits, count, seed)`: p a random pbits-bit prime, q a random (bits − pbits)-bit prime, seeds 2800000 + 100·pbits + bits. The card's B1 still comes from s = √N: it does not know p, and that is part of what is tested.
- **Exact accounting:** each of the four phases equals its formula on the run's realized counts (curves, Euclid steps per setup, prime powers ≤ B1, baby/giant steps, prime pairs, gcds), recomputed independently. Tolerance 0, and a one-op mutation of each charge is caught.
- **Group-order check (harness only):** for factors p < 2^24, ECM finds p on a curve exactly when that curve's group order mod p, counted by brute force, is B1-smooth (stage 1). The same holds with stage 2 for an order that is B1-smooth apart from one prime in (B1, B2]. The check allows the cases where both factors are found at once.
- **Parity** after the Rust port, including degenerate σ, a curve that finds both factors at once, and caps inside each phase.

**Tuning:** before the comparison, b1 and b2 are fixed on tuning seeds `semiprimes_pq(bits, 40, 3000000 + bits)` at 72/78/84 bits, a new range, then frozen. curves stays at its default, and s0 at 6. They are never chosen on the acceptance or comparison numbers. The acceptance runs at the defaults above.

**Comparison (PLAN), on two populations.** Against tuned qs and rho, cap 2^28, reporting mean and worst with intervals, curves per number, the phase breakdown, and growth per bit:
- **Balanced:** the ACCEPT numbers plus the Stage 2 numbers at 54–66 bits.
- **Unbalanced:** 80 numbers at each (N bits, p bits) in {72, 78, 84} × {24, 28, 32}, from `semiprimes_unbalanced` with new seeds 2900000 + 100·pbits + bits. On this population it also reports growth per bit of p at fixed N.

**The complexity class.** On balanced semiprimes, with p ≈ √N, ECM's L_p[1/2, √2] equals L_N[1/2, 1], the same class as qs. So expect a constants race, a crossover with ECM possibly ahead at the small end, not an exponent change (PLAN.md, Stage 8).

**Prediction 1 (PLAN.md, stated before measurement):** ECM beats qs below ~80 bits and loses above.

**Prediction 2 (refined from this cost model, stated before measurement).** A rough estimate moves the crossover lower:

| | p at 36 bits (72-bit N) | p at 42 bits (84-bit N) |
|---|---|---|
| B1 | ≈ 300–600 | ≈ 1,000 |
| Expected curves | ≈ 10 | ≈ 15 |
| Ops per curve (stage 1 + stage 2) | ≈ 15,000 | ≈ 50,000 |
| ECM total | ≈ 2^17.2 | ≈ 2^19.5 |
| Tuned qs | 2^17.4 | 2^19.2 |

So prediction 2 is:
- **Means:** ECM and tuned qs within 2× of each other at 72 bits; ECM behind at 84 bits by about 1.5–3×.
- **Growth:** steeper, about 0.18–0.2 log₂-ops per bit against qs's 0.149.
- **Crossover:** somewhere in 60–78 bits, most likely near 72.
- **Worst case:** worse than qs's at every size, because the number of curves has a long tail. A number that needs 3× the expected curves costs 3×.
- **Against rho:** ECM beats rho from about 60 bits up (rho grows 0.25 per bit), and is roughly level with it at 54 bits (both near 2^14.5 by this estimate).

All of this is uncertain by about 2× either way: the estimate of expected curves and the overcharged ladder dominate.

**Unbalanced prediction (stated before measurement).** With p of 24–32 bits, ECM's cost follows p, not N.

| p | ECM estimate |
|---|---|
| 24 bits | about 2^13–2^14 |
| 32 bits | about 2^15–2^16 |

- **Against qs:** whose cost does not depend on p, ECM is far cheaper, by roughly 8× or more at every (N, p) cell.
- **Against rho:** rho also follows p (about √p steps). The two are roughly level at 24-bit p, and ECM pulls ahead as p grows toward 32 bits.
- **The B1 handicap:** it is sized for balanced numbers, so it is too large here. That costs ECM a constant, but not the ordering.
- **Growth:** at fixed N, growth per bit of p should be well below rho's 0.5 per bit of p.

**Clarifications made while implementing (`ecm.py`; the charges are unchanged):**
- **Stage 2's giant steps start at j₀ = max(1, ⌊B1/w⌋).** With j ≥ 1 and b < w/2, stage 2 never covers primes below w/2 = 105. When B1 < 105 (about 40–44 bits at default b1), primes in (B1, 105) are simply not covered. The accounting and the group-order check use the same rule.
- **The ladder serves every multiply by k ≥ 1.** For k = 1 it is one xDBL (5 ops), giving (W, 2W) when j₀ = 1. The formula 5 + 11·(bit_length(k) − 1) covers it.
- **Giant steps:** S_(j+1) = S_j + W with difference S_(j−1), one xADD per step from j₀ to jmax − 1 = ⌈B2/w⌉ − 1. The step after the last j used is not computed.
- **x-only degeneracy.** A differential addition is only valid when its difference point has X·Z ≢ 0. Mod N that holds, but mod a factor p it can fail:
  - a stage-1 base can land on the 2-torsion point (0, 0);
  - a baby/giant-step difference can be O when the stage-1 point's order is small.

  Then the card's point mod p leaves the group law, and it may "find" p where group theory says it cannot, or miss it. Any gcd it takes is still a true divisor, so its answers stay correct; only the ideal prediction fails. That is ordinary x-only ECM behavior and the card is not changed. The group-order check detects these curves and counts them separately. They are common only when B1 is small, because Suyama orders are divisible by 12 and leftover factors of 2 and 3 beyond the stage-1 prime powers then make giant-step differences O. So the check runs at b1 = 4 (B1 ≈ 220) on its small numbers, with both factors below 2^20 (not 2^24: brute-force point counting stays cheap).

**Tuning (`ecm_tune.py`, seeds 3000000 + bits at 72/78/84, 40 numbers each, cap 2^29).** Grid: b1 ∈ {0.25, 0.5, 1, 2, 4} × b2 ∈ {0, 25, 50, 100, 200}. Rule, fixed before running: the lowest average of log₂(mean ops) over the three sizes. The winner is **b1 = 1.0, b2 = 50** (the defaults), at 15.70 / 17.03 / 17.80 for 72 / 78 / 84 bits. These are now frozen for the comparison. The intervals are wide, because the number of curves has a heavy tail, and 1.0/25 is within noise; the rule decides.

## 2026-10-23 — Pricing sensitivity for the ECM comparison, stated before running

The official op counts stay as they are; this is reported beside them, never in place of them. The question is whether ECM's lead over qs survives if qs's small-number work is priced fairly. Every op of ECM and rho is a multiply, squaring or gcd on N-sized numbers (ECM's Euclid steps run on den mod N), so ECM and rho are not re-priced.

qs's charges split by operand size. A **small-number** op works on numbers below the factor-base bound (or on bytes and machine words); it is re-priced at r = 1/8 and r = 1/32 of a modular multiply. Everything else stays at 1. The split by phase, from the cost model's own charges:

| Phase | Small-number (× r) | Full price (× 1) |
|---|---|---|
| mult | — | all (ks scoring, 14 per multiplier; under 2^9 ops in total) |
| fb | all: Euler's criterion and Tonelli–Shanks are arithmetic mod p ≤ B | — |
| setup | per A and q_l: the inverse mod q_l (Euclid steps) and γ (mod q_l); per sieved prime: the inverse mod p, the 2 root multiplies, the s values 2B_l·A⁻¹ mod p; every Gray-code root update | forming A ((s − 1) per combination), A/q_l, and B_l = (A/q_l)·γ (numbers of about half of N's size): (s − 1)·combinations + 2·s per A |
| sieve | all: array updates and cell scans | — |
| confirm | the F trial divisions per candidate and every extra division (a big g(x) by one small prime) | the 2 ops forming g(x) = (Ax + 2B)x + C |
| la | all: 64-bit word operations | — |
| sqrt | — | all (multiplies and the gcd mod N) |
| lp (lc 1.4) | the bound check, N mod q (one small modulus, like a trial division), the hash lookup and insert, the F-entry vector add | u₁u₂ mod N |

fb and lp are not in the brief's list (sieve, cell scans, confirmation trial division, setup's small arithmetic, la word ops). They are added here because their operands are just as small.

The split is computed per run from lamps.py's trace, never estimated:
- setup full = (s − 1)·combinations + 2·s·(polynomials A tried);
- confirm full = 2·candidates;
- lp full = combinations of partials;
- every other op of those phases is small.

Re-priced qs = mult + sqrt + setup full + confirm full + lp full + r·(fb + setup small + sieve + confirm small + la + lp small).

Reported: re-priced log₂(mean) at r = 1/8 and r = 1/32 for tuned qs + lc 1.4 on both populations, beside ECM's and rho's unchanged numbers, and whether ECM still leads at each size.

**Result (`ecm_compare.py`, cap 2^28, no misses).** ECM with the frozen genes (b1 1.0, b2 50) against our best qs (tuned qs + lc 1.4) and rho.

*Balanced* (Stage 2 numbers at 54–78 bits, `semiprimes_pq(84, 80, 1300084)`): ECM beats qs at every size from 54 to 84 bits on the official op count, by 1.9–2.6× (paired), with mean intervals separated everywhere. At 84 bits ECM is 2^17.84 [17.52, 18.13] against qs's 2^19.08 [19.03, 19.12].

| Prediction (stated before measurement) | Result | Verdict |
|---|---|---|
| **1 (PLAN):** ECM beats qs below ~80 bits and loses above | ECM wins at 84 bits too | **Wrong** above 80 |
| **2:** crossover in 60–78 bits | no crossover in 54–84 | **Wrong** |
| **2:** within 2× at 72 bits | 2.0×, in ECM's favour | at the edge |
| **2:** behind 1.5–3× at 84 bits | ahead 2.35× | **Wrong** |
| **2:** growth 0.18–0.2 per bit | 0.134 (72→84), 0.142 (54→84); qs 0.153 / 0.140 | **Wrong**: the same class as qs |
| **2:** worst case worse than qs at every size | observed worst worse everywhere; intervals separated at 60, 66 and 84 bits | **Held** |
| **2:** ahead of rho from ~60 bits, level at 54 | already ahead at 54 bits (13.53 against 14.26, separated) | slightly off |

The miss in prediction 2 is mostly expected curves: ECM needed about half the curves the estimate assumed (7.8 per number at 84 bits against ~15), because stage 2 at B2 = 50·B1 catches most factors. The growth result is the constants race PLAN.md describes: L_p[1/2, √2] = L_N[1/2, 1] on balanced numbers.

*Unbalanced* (24/28/32-bit factor at 72/78/84 bits): the prediction was partly right.
- **Against qs:** ECM beats qs in every cell, by 2.7× to 16×. But the prediction of at least 8× holds in only 3 of 9 cells (78/24, 84/24, 84/28).
- **Against rho:** the direction is right (ECM pulls ahead as p grows), the crossover is not. Rho is clearly ahead at 24-bit p (by 2–3.5×), the two are level around 28 bits, and ECM leads at 32 bits.
- **Growth per bit of p:** ECM 0.17–0.19, well below rho's 0.51, as predicted.
- **The B1 handicap is real:** sized from √N, it makes ECM's cost grow 0.055–0.077 per bit of N even at fixed p.

*Pricing sensitivity* (the classification above, stated before the run):
- **Balanced: ECM's lead does not survive.** With qs's small-number ops at 1/8 of a multiply, qs beats ECM at 60–84 bits with separated intervals (at 84 bits: 2^16.93 against 2^17.84), and they tie at 54. At 1/32, qs leads at every size.
- **Unbalanced: ECM's lead survives where p ≪ √N.**
  - At 1/8: ECM still leads at 24-bit p at every N, and at 78/28, 84/28 and 84/32. 72/28 and 78/32 are ties, and qs leads at 72/32.
  - At 1/32: ECM leads at 78/24, 84/24 and 84/28.

The balanced lead comes from the overcharging rule, which bills every sieve byte-add as a full modular multiply.

**Caveat:** tuned qs's genes were picked on the 72–84-bit ACCEPT numbers, which favours qs. ECM's genes came from separate tuning seeds.

## 2026-10-23 — Op-price calibration on this laptop: plan, before running (measurement only)

Nothing here changes a score. The official count stays 1 op per charge. This measures what each kind of charge costs in wall time on this machine (an Intel Core Ultra 9 288V: hybrid, with cpu0–3 performance cores at up to 5.0–5.1 GHz and cpu4–7 efficiency cores at up to 3.7 GHz; governor `powersave`), so that a calibrated price table can be reported beside the official numbers, as the pricing sensitivity was. Prices are ratios to one 84-bit modular multiply, so the machine's absolute speed cancels.

**What is timed.** One Rust binary, `lampcore/src/bin/opbench.rs`, built with `--release` against the same crates as lampcore (ruint 1.20.1), using the same types lampcore uses for each kind of charge:

| # | Primitive | As lampcore does it | Access pattern |
|---|---|---|---|
| 1 | 84-bit modular multiply | `U256::mul_mod`, operands < N, N 84 bits; also N at 60 and 100 bits, for the size dependence | dependent chain (x = x·y mod N: ladders, rho, sqrt) and independent (throughput) |
| 2 | sieve byte-add | `arr[i] += logp[j]` on the i32 array, stepping by p, over width 2M + 1 with tuned qs's M at 84 bits (≈ 600, so width ≈ 1,201: L1-resident), primes and roots from a real factor base | as the sieve loop |
| 3 | cell scan | `(arr[i] as f64) >= thr` over the same array | as the confirm scan |
| 4 | trial division of a ~50-bit value by a small prime | `v % p` with i128 v ≈ 2^50, p ≤ B ≈ 2,400 | independent |
| 5 | 64-bit XOR | `mat[r][w] ^= pm[w]` over the dense GF(2) rows, F ≈ 190 at 84 bits | as the elimination loop |
| 6 | Euclid step | small: one `div_euclid` step of extended Euclid on i128 values < 2^12 (setup's inverses mod p); N-sized: one step on 84-bit values (ECM's inverse mod N, and the gcd mod N in sqrt) | dependent within a run |
| 7 | small modular multiply (added: fb, Tonelli–Shanks and setup's root arithmetic are this) | `u64` multiply then `% p`, p ≤ B | dependent chain |

**Two references for "one modular multiply".**
- **ruint:** `U256::mul_mod`, what lampcore uses.
- **Montgomery:** a hand-written two-limb Montgomery multiply (u64 limbs with u128 intermediates, R = 2^128, REDC, valid for odd N < 2^100). Before timing, it is verified against `U256::mul_mod` on 10⁶ random inputs: from_mont(mont(to_mont(a), to_mont(b))) must equal a·b mod N, with any mismatch fatal.

The price table and the calibrated re-score are reported under both references. **These ratios depend on implementation quality.** A generic 256-bit `mul_mod` and a tuned two-limb Montgomery multiply can differ several-fold, so neither reference is "the" price of an op, and neither is chosen after seeing the results. Both sets are reported side by side. For each reference, the timed form is the dependent chain (x = x·y mod N), the way multiplies occur in ladders, rho and sqrt.

**Method.**
- Inputs are precomputed (random operands, a real factor base and roots from an 84-bit ACCEPT-style number with seeds not used elsewhere) and passed through `std::hint::black_box`, so the compiler cannot fold the work away.
- No RNG inside timed loops.
- **Warm-up:** 10⁶ iterations of each primitive before timing.
- **Timing:** batches of at least 10⁷ operations (or 50 ms, whichever is longer), each timed with `std::time::Instant`. 31 batches per primitive, reported as the median ns per op, with min and interquartile range. A loop-overhead baseline (the same loop with the operation replaced by an add of the index) is timed and reported, but not subtracted, so the overhead stays visible rather than hidden.
- **Environment:**
  - pinned to one performance core (`taskset -c 2`; cpu0–3 are the P-cores), and the same run repeated once on an efficiency core (cpu 5) to show how much the core type changes the ratios;
  - the machine otherwise idle, with no tests or runs in the background;
  - governor left at `powersave` and recorded, and the whole run repeated 3 times, to see how stable it is under frequency scaling;
  - if the three runs disagree by more than 10% on any ratio, that is reported, not averaged away.

**How the prices would map onto phases** (a calibrated re-score, computed from the per-phase counts already recorded, plus the qs small/full split from the traces, as in the pricing sensitivity; no new factoring runs):

| Phase | Price |
|---|---|
| mult | #7 |
| fb | #7 (Euler's criterion, Tonelli–Shanks) |
| setup | small part: #6 small for Euclid steps, #7 for root multiplies and Gray-code updates; full part (forming A, A/q_l, B_l): #1 |
| sieve | updates at #2, cell scans at #3 (split by the trace: width per polynomial is scans, the rest updates) |
| confirm | F + extra divisions at #4; the 2 ops forming g(x) at #1 (an upper bound: it is an i128 multiply) |
| la | #5 per word op (the charge already counts 64-bit words) |
| sqrt | multiplies at #1; gcd steps at #6 N-sized |
| lp | N mod q and the bound check at #4; lookup, insert and the F-entry vector add at #4 (flagged: a hash operation, not measured separately); u₁u₂ mod N at #1 |
| check | #1 |
| cf_step | #1 (the 4 per step: one mod-N multiply and three i128 operations, all priced as #1, an upper bound) |
| cf_td | #4 |
| ECM: setup, s1, s2 | #1 (dependent chain), and setup's Euclid steps at #6 N-sized |
| ECM: gcd | one gcd mod N is about 50 Euclid steps, not one op. Priced at its measured cost (#6 N-sized × the steps actually taken), and reported as a finding about the model |
| rho, pm1 | multiplies at #1 (chain). Their gcds get the same treatment as ECM's: the official model charges 1 op per gcd, which calibration would show as an under-charge |
| td | one `N % d`, timed as #4 with an 84-bit N |

**Operation counts the re-score needs, all already recorded or recomputable exactly:**
- **rho:** its gcds equal its luck-meter tests (one test per gcd), and every other op is a multiply mod N.
- **ECM:** its gcds are the ecm_gcd phase. Its setup Euclid steps are recomputed from each curve's σ, as `ecm_accept.py` does.
- **qs:** the small/full split, the sieve's updates against scans (width per polynomial), the Euclid steps in setup, and the gcd steps in sqrt all come from lamps.py's trace.
- **The cost of one gcd mod N:** the mean Euclid steps of gcd(x, N) over 1,000 random residues x for each number. The gcd operands are pseudo-random residues, so this approximates "the steps actually taken": an approximation, stated as such.

**The gcd finding.** The official model charges 1 op per gcd for rho, pm1 and ECM, while a real gcd costs about 50 N-sized Euclid steps. That is reported as a finding about the model, with the calibrated re-score showing its effect. It is not corrected silently in any official number.

**Reported:**
- the ns/op table and the price ratios, under both references;
- the calibrated log₂(mean) of ECM, qs + lc 1.4, rho and N51-0917 on the Stage 8 balanced and unbalanced numbers, beside the official numbers;
- which leads change under calibration;
- where the official model under-charges (gcds), as well as where it over-charges (qs's small work).

**Caveats:**
- These are one laptop's prices; a different CPU (cache sizes, divider latency) changes them.
- The i128 and U256 code paths are lampcore's, not the fastest possible ones.
- The results are a sanity check on the op model, not a replacement for it.

## 2026-10-23 — Stage 9: race combinator ("race"), cost model, written before any code (accepted for implementation, Oct 23)

**Accepted for implementation (Oct 23),** with the review folded in (addenda 5–8, the restated calibrated predictions, and the race bound under each pricing). The predictions below are fixed before any race runs.

**Element.** `{"t": "race", "a": stageA, "b": stageB, "sa": opsA, "sb": opsB}`, where a and b are any non-race stages (td, sq, ps, rho, pm1, qs, cfrac, ecm). A runs for a slice of sa ops, then B for a slice of sb ops, alternating on **one meter**, until one side returns a factor or the cap is reached.
- Nesting a race inside a race is out of scope.
- sa = sb = 0 is invalid: rejected when the genome is built, never run.

**Ops: the race costs exactly the sum of the slices actually run.** Switching sides is bookkeeping, with no arithmetic, and costs **0 ops**. No op is charged for the race itself. Resume is free in ops; any wall-clock cost of the handoff is not measured and not scored.

**The slice rule** (written down so both cores agree):
- A slice starts with a fresh slice counter at 0. Every charge the running side makes is applied whole, to the meter and to the counter, exactly as it would be alone: a chunk is never split.
- The slice ends at the first charge that brings the counter to or past the slice size. The overshoot counts as ops spent by that side, and nothing carries over: the next slice of either side starts at 0.
- The cap is the shared meter's cap. A charge that crosses it raises Budget inside whichever side is running, and the whole race ends as a miss, exactly as a single stage does.
- Prechecks that read the meter (ps's product-tree fit, pm1's stop before a huge sieve) read the shared meter, which includes the other side's spending. That is consistent with one meter, and it leaves the identity cases unchanged, since the idle side never adds ops.

**When a side ends without a factor** (td or sq exhausted, pm1's gcd is 1 or N, ECM's curves used up, qs or CFRAC out of multipliers), the race continues with the other side alone until it finishes or the cap is reached, with no further switching. If both end without a factor, the race returns None and the genome moves to its next stage, as for any stage.

**Found mid-slice:** the race returns at once; total ops are the meter's.

**Luck meter and instrumentation:** tests and hits accumulate on the shared meter, from both sides, in the order they happen. The winning stage index is the race element's index. A square-search win's k is kept per side, and the winner's k is reported.

**What "resume" means.** Each side keeps its whole state between slices, and nothing is redone:

| Lamp | State kept between slices |
|---|---|
| rho | x, y, q, r, k, the batch position |
| pm1 | the running power a, the position in the prime list |
| ECM | the curve, its σ, the ladder position within the prime power, stage-2 baby/giant tables and the accumulator |
| qs | the ledger (relations, dedupe sets), the partials table, the polynomial list and position, the Gray-code state, the sieve array of the polynomial in progress |
| CFRAC | the expansion state (P, Q, A, i) and the ledger |
| td | the next divisor |
| sq | the multiplier k and the window position x |
| ps | the product tree or multipoint evaluation in progress |

- **Mechanism, proposed.** Each side runs as its own coroutine with its own stack, with control handed over at a charge boundary when the slice counter fills:
  - in Python, a thread per side with strict handoff (exactly one runs at any moment, so it stays deterministic);
  - in lampcore, the same pattern with two threads and a handoff, rather than rewriting every lamp as a state machine.

  The point is that **no lamp's code changes**. Resuming is exact by construction, so the identity cases follow structurally rather than from per-lamp care. A paused side whose race has ended (a factor found, or the cap) is torn down without running further.
- **No lamp needs special handling, because every pause falls on a charge boundary.** The only effect of big single charges is overshoot:
  - qs's linear algebra is one chunk of rows·F·rows/64, about 2^16.5 at 84 bits;
  - ps's product-tree precheck can raise Budget before allocating.

  A side whose next charge is a large chunk therefore overshoots its slice by up to that chunk. The overshoot is recorded, not avoided.

**Acceptance (before any scored run):**
- **Identity:** sb = 0 equals A alone, and sa = 0 equals B alone, op for op: ops, factor, tests, hits, stage, k, and every phase. This covers every pair of lamp types (including qs with lc 1.4, CFRAC, and ECM), on numbers at 40–84 bits.
- **Interleaving check:** in a race, each side's own charge sequence (phase, size, in order) equals the prefix of that lamp's charge sequence when run alone. That proves nothing is redone or skipped. Each slice's length is at least its size, and below its size plus the side's largest single charge, except the final slice of the race.
- **The race bound (a provable property, checked on every run).** With slices s_a = s_b = s, if A alone needs T_A ops and B alone T_B, the race uses at most 2·min(T_A, T_B) + s + c ops, where c is the larger side's largest single charge. A single-side end and the cap are handled as above.
  - **Correction (Oct 24, to the math only; flagged).** The bound above is wrong when a side charges in large chunks: the other side overshoots its slice on every slice, not once, so a single c does not cover it. Found while writing the acceptance test, confirmed by a smoke test before any comparison (60 bits, s = 256: ECM alone 3,945 ops, race(ECM, qs) 14,998). The corrected forms, with equal slices s:
    - **A priori:** if side A finishes first at T_A ops, race ≤ T_A + (⌈T_A/s⌉ + 1)·(s + c_B), where c_B is the other side's largest single charge. For c_B ≈ 1–2 (ECM, rho, td) this is about 2×. For B = qs at s = 2^8 or 2^10, the factor is about 1 + (s + c_qs)/s.
    - **Measured check (must hold on every run):** race ≤ 2·min(T_A, T_B) + s + O_other, where O_other is the other side's total overshoot (the sum over its slices of length − s). Each slice's overshoot is below that side's largest charge. The maximum single charge c per side is reported beside it.
  - **The prediction is not restated** ("at most about twice the cheaper side" stays as written). If races against qs at 2^8 or 2^10 exceed 2×, that is recorded as a **prediction miss**, with the cumulative overshoot as the measured cause.
- **Caps that stop mid-slice** on either side, and in the middle of a large chunk, asserted.
- **Parity** after the Rust port, on all of the above, plus random races.

**PLAN's budget-split gene** (the share of the remaining budget either side may spend) is deferred. The first implementation has sa and sb only. The split comes as an addendum with its own identity case: a split of 1.0 equals no split.

**First comparison.** race(ECM, qs + lc 1.4), race(rho, qs + lc 1.4) and race(ECM, N51-0917's qs stage) (addenda 6 and 7), each against its two sides alone, on both Stage 8 populations (balanced 54–84 bits; unbalanced 72/78/84 × 24/28/32), cap 2^28. Slice sizes are genes. For this comparison, three settings fixed before measurement, sa = sb ∈ {2^8, 2^10, 2^14}, are all reported, so the sensitivity to slice size is visible. Tuning them on seeds comes with Run 8. [Status, Oct 24: not done. Run 8's genome space had no race card (Stage 9 ruled the race out first), so slice sizes were never tuned.] Means and worst cases with intervals; the pricings and the per-cell calls are as in addendum 6.

**Prediction (stated before measurement).**
- **Per number:** a race costs at most about twice the cheaper side, by the race bound. So it can never beat the better side alone on a given number by more than one slice, and it loses to it by up to 2× where one side dominates.
- **Where a race wins on the mean:** in cells where neither side dominates, it wins against both, because there it takes the cheaper of two variable times. ECM's time is heavy-tailed; qs's is nearly fixed.
- **Balanced, official count:**
  - race(ECM, qs): its mean is worse than ECM alone by 1.3–2×, and better than qs alone by about 1.3–1.6×. Its worst case is no worse than about 2× qs's (qs's near-fixed time caps ECM's tail), so it is better than ECM's worst at 84 bits.
  - race(rho, qs) is about 2× qs alone at 72–84 bits, where qs dominates. At 54–60 bits it may beat both, because the two are close there.
- **Unbalanced, official count:**
  - race(rho, qs) is within about 2× of rho at 24-bit p (far better than qs alone), and close to qs at 32-bit p.
  - race(ECM, qs) beats qs alone in every cell, and is within about 2× of ECM.
  - race(ECM, N51-0917's qs): ECM leads in every cell, so the race is within about 2× of ECM and beats N51-0917's qs.
- **Calibrated, restated from the committed leader tables** (`evolve/calibrate.json`, median P-core prices; pairwise calls between the race's two sides, a tie meaning overlapping intervals). The rule, per cell and per pricing (addendum 4): where one side leads, the race loses to it by up to the pricing's bound (below) and beats the other side; where the sides are tied, the race beats both.
  - **Balanced:**
    - At 60–84 bits the leader among all four algorithms is N51-0917's qs under both calibrated references, not qs + lc 1.4.
    - race(ECM, qs + lc 1.4): ruint: qs + lc 1.4 leads at 54–84, so the race loses to qs alone and beats ECM. Montgomery: ECM leads at 54 (the race loses to ECM, beats qs); tied at 60–84, so the race beats both.
    - race(rho, qs + lc 1.4): qs leads at 54–84 under both references, so the race loses to qs alone and beats rho.
    - race(ECM, N51-0917's qs): ruint: N51-0917 leads at 54–84, so the race loses to it and beats ECM. Montgomery: ECM leads at 54 (the race loses to ECM, beats N51-0917); tied at 60 and 66, so there the race beats both sides alone; N51-0917 leads at 72–84 (the race loses to it).
    - **54 bits,** per pricing: official, ECM leads both its pairs and rho leads qs, so every race is within the bound of ECM or rho; ruint, the qs side leads every pair, so every race is within the bound of its qs side; Montgomery, ECM leads both its pairs and qs leads rho.
  - **Unbalanced:**
    - race(ECM, qs + lc 1.4): ruint: qs leads 72/32; ECM leads 78/24, 84/24, 84/28; tied (the race beats both) at 72/24, 72/28, 78/28, 78/32, 84/32. Montgomery: ECM leads every cell except 72/32, which is tied.
    - race(rho, qs + lc 1.4): ruint: rho leads 72/24, 78/24, 84/24, 84/28; qs leads 72/28, 72/32, 78/32, 84/32; tied at 78/28. Montgomery: rho leads 72/24, 78/24, 78/28, 84/24, 84/28; qs leads 72/32, 78/32; tied at 72/28 and 84/32.
    - race(ECM, N51-0917's qs): ruint: N51-0917 leads 72/28, 72/32, 78/28, 78/32, 84/32 (the race loses to it and beats ECM); ECM leads 84/24; tied at 72/24, 78/24, 84/28. Montgomery: ECM leads every cell except 72/32 and 78/32, which are tied.
    - **Where N51-0917 leads all four under ruint** (72/28, 78/28, 78/32, 84/32), race(ECM, qs + lc 1.4) beats or ties its own sides but is expected to stay behind N51-0917 alone: a race cannot cost less than the cheaper side on each number, and N51-0917 leads both of its sides there. race(ECM, N51-0917's qs) is within the bound of N51-0917 there.
- **What the race is for:** not the best mean on any one population, but robustness on a mixed one, never far from the best side on any number. That is what the partition study will measure.
- **The race bound under each pricing.** Scheduling stays on official ops (addendum 5). Under a pricing in which side A's average price per official op is π_A and side B's is π_B (its calibrated cost divided by its official ops), equal slices give approximately

  race cost ≤ (1 + π_other / π_winner) · (winner alone's cost) + slice terms,

  because the losing side spends about as many official ops as the winner before the winner finishes. Under the official count π_A = π_B = 1 and this is the 2× bound. Under a calibrated pricing it exceeds 2× wherever the losing side costs more per official op than the winner (ECM's multiplies against qs's cheap sieve ops, for example). Measured π_A / π_B is reported per cell and per pricing, so the bound can be checked. Unequal slices (sa : sb, already genes) could equalize the calibrated spend; tuning that is Run 8 work, not the first comparison.
- **How the result is judged.** The race's bar is robustness: never far from the better side. It is not winning. A result like "loses to ECM by 1.8× on balanced numbers" is within this prediction, not a failure. The failure test is applied **under each of the three pricings**: a failure is a race that is worse than about 2× the better side (beyond the slice and chunk terms), or worse than the worse side. Where that pricing's π ratio makes the bound itself exceed 2×, a failure is reported with the measured ratio, so "predicted by the bound" and "beyond the bound" stay distinguishable. The robust verdict per cell is the worst of the three, with the (e) call per cell (addendum 6).

**Addenda to the Stage 9 cost model** (before review):

1. **Resume is free, and nothing is set up again: per lamp.** Under the coroutine mechanism each side's state lives in its own frame, so resuming charges **0 ops for every lamp**, and no setup is repeated:
   - qs does not rebuild its factor base or polynomials;
   - ECM does not restart its curve or recompute its baby steps;
   - pm1 does not restart its power;
   - rho does not restart its walk;
   - td and sq do not restart their scan.

   If the Rust port ever implements a lamp as a state machine that recomputes anything on resume (a cached table, say), that recomputation is charged as performed, in the lamp's own phase, and stated in an addendum before the port is accepted. The one-switch identity below would catch an uncharged recomputation.
2. **One-switch identity, for every lamp as the resumed side.** For each lamp X (td, sq, ps, rho, pm1, qs with lc 1.0 and 1.4, CFRAC, ECM):
   - **Setup:** race(X, E) with E a stage that ends without a factor during its first slice: td with a bound far below the factor (`{"t": "td", "a": 0.05}`) at sizes where that bound is exhausted. sa is chosen so that X is paused exactly once, mid-run, after its first slice.
   - **Check 1:** total ops = X alone + E alone; factor = X's; tests and hits = the sums.
   - **Check 2:** X's charge sequence in the race equals X alone's, with E's whole sequence inserted at the one switch point.
   - **Coverage:** tested at three switch points per lamp (early, mid-run, inside X's largest-chunk phase), including mid-stage-2 for ECM and between polynomials for qs.
3. **Switches per run:** reported for every run (mean, median and max per cell), with the ops each side spent. That makes it visible whether a race really interleaved or one side did nearly all the work.
4. **Prediction per pricing reference.** The race prediction above is stated three times: under the official count, under the ruint-calibrated prices and under the Montgomery-calibrated prices. Under each, it follows that reference's leader table from `calibrate.py` (balanced sizes and unbalanced cells), which is fixed before any race runs:
   - where one side leads with separated intervals, the race loses to that side by up to 2× and beats the other;
   - where the two sides are tied, the race beats both.

   Wherever the references disagree on the leader, the race prediction disagrees with them, and the race comparison is reported per reference without picking one.

**Slice overshoot: reported, and the large-chunk lamps.**
- **Per run and per side:** the mean and maximum ops by which a slice exceeded its size, and the share of slices that overshot. This goes beside the official totals.
- **Lamps that charge in large chunks,** so that a slice smaller than the chunk cannot really interleave with them (the effective slice is the chunk):
  - **qs:** each polynomial's sieve updates are one charge (thousands at 84 bits) and its cell scan another (2M + 1). Forming the A's is one charge of (s − 1)·combinations at the start, the linear algebra is one charge of rows·F·rows/64 (about 2^16.5 at 84 bits), and each confirmation charges F at once.
  - **ps:** each product-tree and multipoint multiply is one fft_cost chunk, growing to the full tree at the top.
  - **pm1:** bit_length(p^e) per prime, which is small.
  - **CFRAC:** F per residue.
  - **ECM, rho and td** charge 1–2 ops at a time, so they interleave at any slice size.

  At sa = sb = 2^8 and 2^10 in the first comparison, qs's slices will mostly be a single polynomial: an effective qs slice of a few thousand ops at 84 bits. The race bound's c term carries that, and the overshoot report shows its size.

5. **Slices are measured on the official meter.** sa and sb count official ops, so the schedule (which side runs when, and every switch point) is deterministic and identical under every pricing. Calibrated scores are computed afterwards from per-type counts, never used to schedule. The race records per-type counts (the types `calibrate.py` reprices) separately for each side, so each pricing can reprice both sides; the per-type counts of the two sides sum to the race's totals, checked on every acceptance run.
6. **The comparison adds race(ECM, N51-0917)** (meaning N51-0917's qs stage: addendum 7), because N51-0917 leads balanced 60–84 bits under both calibrated pricings (calibration result entry). race(ECM, qs + lc 1.4) and race(rho, qs + lc 1.4) stay. Every race result is reported under all three pricings (official, ruint-calibrated, Montgomery-calibrated, with median P-core prices), plus the (e) call per cell: the leader where all three pricings agree, "undecided" elsewhere.

## 2026-10-23 — Op-price calibration: result (measurement only)

Nothing here changes a score; the official count stays as it is. Code: `lampcore/src/bin/opbench.rs`, `evolve/calibrate.py` (modes counts, price, extra); outputs `evolve/calibrate_counts.json`, `evolve/calibrate.json`, and the raw benchmark runs in `evolve/calibrate_bench/`. Plan: the entry "Op-price calibration on this laptop" above.

**Deviations from the plan, and one failed run.**
- The first run hung on "sieve update" and was killed after 25 primitives. Its update count was (width − 1 − start)/p + 1, and primes above the sieve width (the base reaches B ≈ 2,295, the width is 1,147) can start past the end, so the subtraction wrapped. Each call then returned a huge count after one pass, and the batch-size doubling overflowed to 0 and spun. Fixed: a prime that misses the interval counts 0.
- Batching changed: each batch is sized from a short probe to ~50 ms (not "at least 10⁷ operations"), warm-up is ~0.1 s per primitive (not 10⁶ iterations), and a primitive past 30 s records a timeout. No timeouts occurred; each run took about 48 s.
- The 25 lines of the killed run are reproduced within 10% by all three P-core repeats (worst 8.2%).
- The cost of one gcd mod N is timed directly (`U256::gcd` on random residues, with its mean Euclid steps reported), not computed per number.

**Price spread** (ratios to one 84-bit multiply; P1-P3 on cpu 2, E1 on cpu 5; all in `calibrate.json`):
- Across the three P-core repeats every price agrees within 7.5%, except sieve update: 17% (1.054 / 0.929 / 0.901 ns).
- The E-core changes the ratios: its big multiplies are 1.4–1.6× slower, while gcd, Euclid steps and small mulmod are only 1.0–1.2× slower, so most small-number ratios fall by 10–35% (xor rises 30%).
- The two references differ 3.7×: one 84-bit multiply is 27.3 ns with ruint and 7.37 ns with Montgomery. Every small-number price moves by that factor. For example, a sieve update is 0.032–0.039 ruint multiplies, or 0.12–0.14 Montgomery multiplies.

**Scoring uses P-core prices only** (the median of the three P-core repeats). The E-core run is reported for spread, not used to score: its ratios shift by 10–35%.

**Leaders** (median P-core prices; a tie means intervals overlapping the leader's):

| Cell | Official | ruint | Montgomery | Agree? |
|---|---|---|---|---|
| 54 | ECM | N51-0917 (tie qs) | ECM | no |
| 60 | ECM | N51-0917 (tie qs) | N51-0917 (tie ECM, qs) | leader yes, ties differ |
| 66 | ECM | N51-0917 | N51-0917 (tie ECM) | leader yes, ties differ |
| 72, 78, 84 | ECM | N51-0917 | N51-0917 | yes |
| 72/24, 78/24, 84/24 | rho | rho | rho | yes |
| 72/28 | ECM | N51-0917 | ECM | no |
| 72/32 | ECM | N51-0917 | N51-0917 (tie ECM) | leader yes, ties differ |
| 78/28 | rho (tie ECM) | N51-0917 | ECM (tie rho) | no |
| 78/32 | ECM | N51-0917 | ECM (tie N51-0917) | no |
| 84/28 | rho (tie ECM) | N51-0917 (tie ECM, rho) | rho (tie ECM) | no |
| 84/32 | ECM | N51-0917 | ECM | no |

- **Official pricing and both calibrated pricings disagree on the balanced leader from 60 bits up** (ECM against N51-0917; under Montgomery, ECM is still tied with the leader at 60 and 66 bits, and is separated from 72 bits up): the pricing decides the winner. The 24-bit-p cells (rho) agree under all three.
- **Where the references disagree** (54, 72/28, 78/28, 78/32, 84/28, 84/32), the meter's calibration decides the winner, not the algorithms.
- ECM's official lead on balanced numbers does not survive calibration at 72–84 bits under either reference, as the 1/8 and 1/32 re-pricings had suggested.
- **N51-0917 overtakes tuned qs + lc 1.4 under calibration**: 15.38 against 16.63 at 84 bits (ruint), and 17.06 against 17.64 (Montgomery), where the official count has 19.45 against 19.08. Its work leans more on cheap sieve operations.
- Within a reference: ruint leaders are identical in P1–P3, and E1 only drops ties. Under Montgomery the tied cells reorder between runs (at 60 bits P1's leader is qs, and P2/P3's is N51-0917; E1 reorders the ECM–N51-0917 ties at 72/32, 78/32 and 84/32).

**Is the price ratio stable enough to settle qs against ECM?** The multiplier on all of qs's small-number prices at which qs + lc 1.4 and ECM are level (above 1: qs leads by that margin):

| | 54 | 60 | 66 | 72 | 78 | 84 |
|---|---|---|---|---|---|---|
| ruint | 1.88 | 4.43 | 4.29 | 5.14 | 4.85 | 4.53 |
| Montgomery | 0.52 | 1.20 | 1.16 | 1.39 | 1.31 | 1.22 |

Under ruint, qs's lead at 60–84 bits is settled: the margin is far beyond any measured spread. Under Montgomery it is not: the 16–22% margins at 60–84 bits are the size of the sieve update's 17% spread between P-core repeats. The 3.7× gap between the references is larger than every margin, so the ratio settles the question only once a reference is chosen.

**The gcd finding (a model finding; not corrected).** The official model charges 1 op per gcd mod N. Measured: at 84 bits one gcd is 49.6 Euclid steps, about 214 ns, which is 7.8 ruint or 29 Montgomery multiplies; at 100 bits, 59.5 steps × about 19.9 ns. The effect on scores is small, because both lamps batch their gcds:
- ECM: 4–15 gcds per number against 10⁴–10⁵ ops, so 0.01 log₂ or less.
- rho: gcds are about 0.45% of its ops, raising its calibrated score by 0.04 (ruint) and 0.13–0.17 (Montgomery) log₂.
- It decides no cell. The only cell it could touch, 84/28, is a tie under every scoring.
- qs's square-root gcd is already charged per Euclid step.

**Run 8 scoring rule: OPEN.** The options:
- (a) The official count decides.
- (b) One calibrated pricing, named in advance, decides.
- (c) **Robust:** a candidate's score is its worst result across the three pricings (official, ruint-calibrated and Montgomery-calibrated, with median P-core prices). *Corrected Oct 24 (partition study entry): the worst is taken over per-pricing ratios to a reference genome on the same numbers, not over raw costs, which collapsed to the official count.*
- (d) **Lexicographic:** rank by the worst-case pricing first, with ties broken by the official count.
- (e) **Reporting rule:** a cell is called only where all three pricings agree, and is "undecided" elsewhere.

Recommended: (c) as evolution's fitness + (e) in reports. Decision (Oct 23, user): (c) as fitness, (e) in reports.

**Caveats.** One laptop, one build. The i128 and U256 paths are lampcore's, not the fastest possible. The confirm, lp and cf_step mappings are upper bounds, as planned. One unexplained oddity, not used in any price: the loop-overhead baseline is 0.31 ns on the E-core against 1.25 ns on the P-core.
7. **race(ECM, N51-0917) is race(ECM, N51-0917's qs stage)**: `{"t": "qs", "kc": 32, "bc": 1.13, "mc": 1.00, "tc": 1.38}` (exact values from `run6/accept.json`), with no lc. A race side is a single stage, and N51-0917's two sq stages never run: the Run 6 ablation (240/240 finished by the first qs), and on the Stage 8 populations `calibrate.py`'s trace assert (each run's ops equal its qs trace's). This race and race(ECM, qs + lc 1.4) differ in the qs genes and also in large primes (lc 1.0 against 1.4).
8. **Per-type counts in Stage 9 come from Python traces**, per side, which is fine at this scale. Lampcore per-type counters are a Run 8 prerequisite (PLAN.md, Run 8) and do not block Stage 9.
9. **A fourth slice setting: unequal slices that equalize calibrated spend** (written Oct 24, before race_compare runs).
   - For each race and each s in {2^8, 2^10, 2^14}: sa = s for the non-qs side, and sb = round(s · π_other / π_qs) for the qs side.
   - π is the card's mean ruint-calibrated price per official op on that population: its total calibrated cost divided by its total official ops, over the solved numbers of the cell, from `calibrate_counts.json` (the Stage 8 traces) and the median P-core ruint prices in `calibrate.json`. Computed now, never from race results. For race(rho, qs), rho's π the same way.
   - The ratios π_other / π_qs, per cell:

     | Cell | ECM / qs + lc 1.4 | rho / qs + lc 1.4 | ECM / N51-0917's qs |
     |---|---|---|---|
     | 54 | 3.18 | 3.28 | 5.23 |
     | 60 | 4.25 | 4.39 | 6.97 |
     | 66 | 5.54 | 5.70 | 8.93 |
     | 72 | 6.33 | 6.52 | 11.93 |
     | 78 | 5.85 | 6.03 | 14.38 |
     | 84 | 5.45 | 5.62 | 16.75 |
     | 72/24 | 6.88 | 7.11 | 12.01 |
     | 72/28 | 6.89 | 7.11 | 11.87 |
     | 72/32 | 6.92 | 7.13 | 12.10 |
     | 78/24 | 4.94 | 5.11 | 14.45 |
     | 78/28 | 5.88 | 6.06 | 14.44 |
     | 78/32 | 5.10 | 5.26 | 14.31 |
     | 84/24 | 5.26 | 5.44 | 16.81 |
     | 84/28 | 5.71 | 5.89 | 16.52 |
     | 84/32 | 5.05 | 5.20 | 16.86 |

     (π_ECM ≈ 1.000, π_rho ≈ 1.03; π for qs + lc 1.4 is 0.15–0.31, and for N51-0917's qs 0.06–0.19.)
   - **Prediction (stated before measurement):**
     - At 2^8: little change against equal slices. qs's turn is already about one polynomial (the overshoot), so the ratio barely moves its share.
     - At 2^10 and 2^14: calibrated cost moves toward the better side. Under ruint and Montgomery the race gets closer to the calibrated leader than with equal slices. Under the official count it gets slightly worse (more qs spend at official prices).
   - Reported like the other settings: three pricings, the (e) call, overshoot, and the maximum single charge per side.
   - Seen before this addendum was written: one equal-slice smoke test at 60 bits (three numbers; race(ECM, qs + lc 1.4) and race(rho, qs + lc 1.4) at s = 256, 1024 and 16384), e.g. s = 256: ECM alone 3,945 ops, race(ECM, qs) 14,998. No unequal-slice result had been seen.

## 2026-10-24 — Meter safety: the outside case

Digital-evolution anecdotes of evolved agents exploiting simulator bugs (Lehman et al. 2018, arXiv 1803.03453) are the outside case for the sealed meter, the mutation tests and robust pricing: an evolved genome that finds an under-charge in our meter would "win" in exactly that way.

## 2026-10-24 — Phase 1 pricing rule: oversized multiplies (before the batch smoothness move is built)

Oversized multiplies (product/remainder trees) are charged per actual operand sizes: ⌈L1/b_N⌉ · ⌈L2/b_N⌉ N-sized multiplies per product, minimum 1, where b_N = bit length of N and L1, L2 are the operands' bit lengths. Each remainder-tree reduction is charged as a multiply of the same operand sizes. This is overcharge-safe against Karatsuba/FFT; a faster implementation is an unclaimed improvement, not a meter defect.

## 2026-10-24 — Stage 9 result: the fixed-slice race fails its robustness bar

Code: `evolve/race.py`, `lampcore/src/race.rs` (accepted: `race_accept.py`, 0 failures; parity 653 race pairs, 0 mismatches). Comparison: `evolve/race_compare.py` (committed before running), `race_compare.json`/`.out`; scoring against the predictions above: `race_report.py`/`.out`. 21,600 races (3 races × 15 Stage 8 cells × 6 slice settings × 80 numbers), cap 2^28, no misses; Python and lampcore agree on every race's ops and per-side ops. The unequal-slice ratios were asserted equal to addendum 9's table before the run.

**Headline.**
- The race's mean is below both its sides alone in **0 of 810** (race, setting, cell, pricing) cases.
- Its official worst case is below both sides' worst in **0 of 135** equal-slice cells.
- The robust verdict (a failure under any pricing: worse than 2× the better side, or worse than the worse side) fails in **253 of 270** (race, setting, cell) combinations.

**The measured cause: qs's per-slice overshoot.** qs charges each polynomial's sieve updates and scan as single chunks, so its turns run past the slice: mean overshoot 1.6 slice lengths at s = 2^8, 0.9 at 2^10 and 0.5 at 2^14 (against tuned qs + lc 1.4; against N51-0917's qs, with its wider interval, 4.2, 2.2 and 0.2 slice lengths). The qs side spends 65–83% of the race's official ops at 2^8 and 2^10, and 45–52% at 2^14. Equal official slices already give about 2× the faster side when one side dominates; the overshoot pushes the race past that.

**Predictions, scored** (stated before measurement; none restated):
- **"At most about twice the cheaper side": PREDICTION MISS** at 2^8 and 2^10, with the cumulative overshoot as the measured cause (the bound correction, Oct 24). Official race(ECM, qs) over ECM: balanced 1.95–2.49× at 2^8 and 1.90–2.31× at 2^10; unbalanced 2.4–4.9× and 2.2–4.2×. At 2^14 it holds on balanced numbers (1.27–1.93×) and misses on unbalanced (1.48–3.29×).
- **Tied sides → the race beats both: PREDICTION MISS in every tied cell** (0 of 126 tie cases across races, settings and the calibrated pricings).
- **Balanced, official, race(ECM, qs):** worse than ECM by 1.3–2×: holds at 2^14 (1.27–1.93×), misses at most sizes at 2^8 and 2^10 (1.90–2.49×). Better than qs alone by 1.3–1.6×: **miss** (0.94–1.13× at 2^8 and 2^10; 1.14–2.04× at 2^14, in range only at 66 bits). Worst case no worse than about 2× qs's: **holds** (1.2–1.9×).
- **race(rho, qs) about 2× qs at 72–84, official: holds** (1.31–1.91×). It does not beat both at 54–60 bits.
- **Unbalanced, official:** race(rho, qs) within about 2× of rho at 24-bit p: **miss** (3.1–5.0× at 2^8, 1.6–2.9× at 2^14); close to qs at 32-bit p: holds (0.71–1.72×). race(ECM, qs) beats qs alone in every cell: **holds** (9/9 at every s); within about 2× of ECM: **miss** (2.4–4.9× at 2^8, 1.5–3.3× at 2^14). race(ECM, N51-0917's qs) within about 2× of ECM: **miss** at 2^8 and 2^10 (3.2–6.0×), 1.5–2.1× at 2^14.
- **Calibrated, the addendum 4 rule** (lose to a leading side by at most the pricing's bound and beat the other; beat both when tied), passes per setting out of 15 cells: race(ECM, qs + lc 1.4) ruint 0–7, Montgomery 0–3; race(rho, qs + lc 1.4) ruint 5–10, Montgomery 5–7; race(ECM, N51-0917's qs) ruint 2–9, Montgomery 1–6. Every pass is a lead cell; no tie cell passes.
- **Addendum 9 (unequal slices),** change in log₂(race / better side), unequal minus equal, median over cells:
  - At 2^8, "little change": **miss.** ruint −0.26 / −0.71 / −0.50 for the three races; official +0.40 / −0.08 / +0.41.
  - At 2^10 and 2^14, calibrated cost moves toward the better side: **holds under ruint** (−0.14 to −0.62) and for race(rho, qs) under Montgomery (−0.38, −0.17); **misses under Montgomery for the two ECM races** (−0.02 to +0.09).
  - Official gets slightly worse: worse, but **not slightly** for the ECM races (+0.50 to +1.29, i.e. 1.4–2.4×); about unchanged for race(rho, qs) (−0.07, +0.09).

**Verdict: the fixed-slice race is RULED OUT** for ECM or rho against qs (tuned qs + lc 1.4, or N51-0917's qs), on the Stage 8 populations (balanced 54–84 bits; unbalanced 72/78/84 × 24/28/32), with equal slices 2^8 / 2^10 / 2^14 or addendum 9's π-scaled slices, under all three pricings. The combinator itself stays (accepted, with parity), since later work runs schedules through it. Conditions not tested, any of which would reopen the question: qs's sieve charged in smaller chunks per polynomial (smaller overshoot), adaptive or budget-split slices, a race between two non-qs lamps, and a mixed population (the partition study).

## 2026-10-24 — Per-stage op budget ("ob"): cost model, written before any code

Prerequisite for the partition study's sequential budgets (PLAN.md, Partition study). Checked first: no stage has an op-budget gene today; a stage ends only by its own bounds (td's a, pm1's b, ECM's curves) or the shared cap, which ends the whole run as a miss.

**The gene.** `"ob": n`, a non-negative integer, on any lamp stage (td, sq, ps, rho, pm1, ecm, cfrac; allowed on qs, where a final qs doesn't need it). The stage may spend up to n official ops of its own. The charge that takes its spending past n is applied whole (a charge is never split, as in Stage 9), and then the stage ends **without a factor** and the next stage runs. The ops spent count; nothing carries over (sunk cost). Not allowed on a race element or on a race's sides (rejected when the genome is built, both cores): the race has its own slices, and combining the two is out of scope.

**Why "past n", not "reaching n".** A stage whose natural total is exactly n would otherwise end on its last charge, before returning its factor, and the identity "ob at the natural end = today's behaviour" would fail in the "at" case. With "past", the stage spends at most n plus the overshoot of one charge. It is recorded per stage.
- **Correction (Oct 24, before the Python commit; flagged).** The overshoot is between 1 and the passing charge's size, not that size minus 1: spending can sit at exactly n before the next charge, which then passes n by its whole size. So the overshoot is **at most** the stage's largest single charge, not strictly below it (for a lamp that charges 1 op at a time it is always exactly 1). Found by the acceptance test (td, sq and rho). A strict bound would need "reaching n", which breaks the identity at the natural end, so "past n" stays.

**Charging: zero extra ops.** The check reads the stage's own spending, counted as charges are applied; it does no arithmetic. Prechecks that read the meter (ps, pm1) still read the shared meter and cap, not the stage budget (no lamp code changes).

**Identities (both cores, op for op: ops, factor, tests, hits, stage, k, per-phase ops):**
- ob absent = today's genome;
- ob = 0 = the stage skipped (no lamp code runs; the winning stage index still counts it);
- ob at or past the stage's natural end (its total ops when run alone, whether it ends with a factor or without) = today's behaviour.
- Below the natural end: the stage's charge sequence is today's prefix up to and including the first charge that takes it past ob, and the rest of the genome runs after it exactly as it would alone.
- **Prechecks read the budget (Oct 24, added with the precheck fix).** The ps and pm1 prechecks compare against min(cap, the meter total at which the stage's budget runs out). Where the precheck's minimum charge before any test (ps: (B − 1) + (blocks − 1); pm1 past 2^26: B / ln B) exceeds what the budget allows, the stage ends before any charge, with 0 ops spent, and the next stage runs; when the cap is the lower limit it is a miss, as before. This is a deduction from the genes, not a saving bought by work: the stage could not have tested anything within its budget. The skip is free: it is decided from N's size and the stage's genes alone, which the Stage 9.5 rule allows (N's bit length is free). Unchanged whenever ob is absent or at least the stage's natural total, since that total already exceeds the precheck's minimum.

**Acceptance:** the identities for every lamp; overshoot between 1 and the passing charge (so at most the stage's largest single charge); a mutation test in which an ob that fails to end the stage, and one that ends it one charge early, must each be caught. Parity: budget pairs in parity.py.

**Prediction (stated before measurement):** on its own the gene changes nothing measurable on the Stage 8 single-kind populations unless it is set below a stage's natural length. It exists for the partition study.

## 2026-10-24 — Partition study: cost model and predictions (written before any study code)

How should a fixed op budget be split across cheap lamps before qs, when the smaller factor's size is not known in advance? (PLAN.md, Partition study: sequential budgets, not races.)

**Populations** (fixed now; tuning and sealed seeds disjoint, and unused by any earlier stage):
- **Mixed:** 84-bit N, smaller factor in one of seven bands, 16, 20, 24, 28, 32, 36 or 42 bits (42 = balanced), 80 numbers per band: `semiprimes_unbalanced(84, pb, 80, seed)`, or `semiprimes_pq(84, 80, seed)` for 42. Equal counts per band make the prior exactly uniform over the bands (stratified, a proposal: the brief said "drawn uniformly"). Tuning seeds 4000000 + 100·pb + 84; sealed seeds 5000000 + 100·pb + 84.
- **Single-kind control:** balanced 84 only (the 42-bit band's numbers, from the same two seed ranges).

**Genome:** td(ob1) → rho(ob2) → pm1(ob3) → ecm(ob4) → final qs, with two final-qs variants: tuned qs + lc 1.4, and N51-0917's qs stage. Fixed stage genes (not tuned here): td a = 0.5 (so only its budget stops it short of √N), rho c = 1, b = 64 (the rho baseline), pm1 b = 0.1991 (L53-0972's p-1 front), ECM b1 = 1.0, b2 = 50 (Stage 8).
- **Limitation:** the stage genes are fixed, not retuned for the small bands (ECM's b1/b2 were tuned on 24–42-bit factors).
- **pm1 takes one gcd, at the end.** A pm1 budget below its natural total finds nothing and wastes everything it spent. The optimizer searches pm1's ob over {0, natural total} only. The map already reflects this: pm1's ops-to-success, when it succeeds, is always its full length.
- **ECM ends per curve** (a gcd at the end of each curve's stage 1 and stage 2), so a budget wastes at most one partial curve; searching ECM's ob on the log grid is fine.
- td and rho test as they go (td every divisor, rho every batch), so any budget can succeed.

**Cost map** (tuning seeds only). Each lamp is run alone on every tuning number (Python, with traces): its ops-to-success (or "none within the largest budget", run to a cap of 2^21), its charge sequence, and its per-type counts; each final qs alone to the cap of 2^28. From these, the cost of any budget vector on a number is composed exactly: a stage whose ops-to-success T is at most its ob finds the factor at T; otherwise it spends its charge prefix up to and including the first charge past ob (or 0, where the precheck rule applies) and the next stage runs.
- **Proposal: per-number composition.** Lamps compute on N alone and never read another stage's state (only the ps/pm1 prechecks read the meter, and pm1 here has B < 2^26), so composing per number on the same numbers is exact on the tuning seeds and needs **no independence assumption**. The brief's version, from each lamp's per-band ops-to-success distribution with stages assumed independent per number, is the alternative. It would be needed only to extrapolate to bands not run. With per-number composition, a gap between the map and the sealed measurement is sampling (the tuning numbers differ from the sealed ones), not dependence.
- Calibrated costs of a truncated stage: its official prefix × that stage's price per official op on that band (π, from its alone runs). This is exact for td (every op is N mod d) and for pm1's multiplies, and close for rho and ECM, whose gcd share is under 0.5%. The verdict run uses exact per-type counts per stage.
- **Prerequisite, before study code:** price mappings for every op type td and pm1 charge, in `optypes.py` / `calibrate.py`, as the calibration plan specified them. Checked: pm1 charges bit_length(p^e) per prime power (the modular exponentiation) and 1 for its final gcd, and its prime generation is not charged; td charges one op per divisor (the N mod d test), and its divisor stepping is not charged separately. So td is one type, N mod d at #4 ("N84 mod small d (i128)"), and pm1 splits as rho does: multiplies (ops − tests) at #1 and gcds (tests) at one measured gcd. Had either charged small-number work (prime generation, stepping), it would be priced at the sieve-update price, not as a full multiply.

**Allocation.** Minimize under the prior, on the map: a coarse grid of ob ∈ {0, 2^8, 2^9, …, 2^20} for td, rho and ECM, ob ∈ {0, natural} for pm1, then coordinate refinement on log₂ ob (scipy's bounded scalar minimization per coordinate, repeated until no coordinate moves). numpy/scipy, no optimizer built. One allocation per final-qs variant.

**Fitness: (c) robust, as ratios to a reference.** Per pricing P (official, ruint-calibrated, Montgomery-calibrated; median P-core prices): score_P(g) = mean cost of g under P / mean cost of the reference under P, on the same numbers; fitness(g) = max over P of score_P(g). The reference here is qs alone, per final-qs variant (the same shape as Stage 9's per-pricing ratios). Also reported: the worst band's ratio per pricing, so an allocation can't buy a good average by sacrificing a band.
- *Corrected Oct 24 before any study code. The raw-cost form collapsed to the official count:* the official count charges every small op 1 where the calibrated prices charge 0.03–0.14, so the official cost is almost always the largest.

**Verdict.** Run the chosen allocation **once** on the sealed seeds, with exact per-type counts per stage. Compare against qs alone (each variant), the Run 6 p-1 front genome (L53-0972, as accepted), and the map's prediction for the sealed numbers. Report means with intervals under all three pricings, the worst band's mean, and the (e) call per comparison (the leader where all three pricings agree, else "undecided").
- **Also reported, information only (not fitness): against the best single lamp per band.** For each band, the cheapest of td, rho, pm1, ECM and qs run alone on that band's numbers. This is a hindsight benchmark (it knows each number's band), so it shows whether the allocation helps within bands or only by covering them.
- **If pm1 turns on:** reported per band, its savings where it succeeds and the cost it adds where it fails (it runs its full length on every number that reaches it), so "earned its budget" can be told apart from "won by a hair".
- **If pm1 turns on but gains less than the p-1 front's 1.05–1.24×:** check first whether rho's larger ob absorbed the small-band gain (rho is pm1's real competitor there), before blaming the smoothness estimates.

**Predictions (stated before any study code):**
- **Mixed population, official:** sequential budgets beat qs alone by about 2×. Reason: bands 16–28 are solved for 2^8–2^16 ops by rho/ECM against qs's ~2^19, and the budgets added to the hard bands are small next to 2^19.
- **Mixed, calibrated (ruint, Montgomery):** still beats qs alone, but by less (about 1.3–1.7×). qs's work is cheaper per op under real prices, so rho/ECM time costs relatively more.
- **The sealed mean falls inside the map's 95% bootstrap interval, overall and in at least 5 of 7 bands.** The interval comes from bootstrapping over the tuning numbers, per band, with 10,000 resamples and random.Random(2026) per cell (revalidate.py's structure; the overall interval resamples within each band, keeping the strata). Each band's interval and where the sealed point lands are reported. Rho, ECM and p-1 are heavy-tailed or bimodal, so the intervals will be wide in those bands. (This replaces "within about 10%", before any study code.)
- **Balanced-only control:** the optimizer drives all budgets to about 0 (qs alone wins), or at most a small p-1 budget (the p-1 front's 1.05–1.24×).
- **Expected budget shape:** td small, rho moderate (catches 16–24-bit p), ECM largest (28–36-bit p), p-1 off, or on at full length.
  - **Why p-1 is on or off:** Dickman estimates with B ≈ 2^16.7 give p − 1 B-smooth for certain at 16-bit p, about 60–80% at 20–24 bits, about 30–45% at 28–32, and about 13% per factor at 42 (either factor counts, so about 25% on balanced numbers). So p-1 competes with rho and ECM for the small bands: on if its full length beats their cost there, otherwise off. The budgets are one vector for the whole population, not per band.

## 2026-10-24 — Partition study result: sequential budgets pay on the mixed population

**Scope (added Oct 24, after the generalization tests):** Allocation A is the 84-bit allocation: its absolute budgets fail the gate at 72 bits.

Code: `evolve/partition.py` (map, optimize and sealed modes, each committed before it ran); outputs `partition_map.json`/`.out` (tuning seeds), `partition_alloc.json`/`.out` (allocations and the map's predictions), `partition_sealed.json`/`.out` (the sealed run, once). Prerequisites: the ob gene with the precheck fix, td/pm1 price mappings (`price_accept.py`), per-stage tests in the ob record. On the sealed run, lampcore agreed on every official count, and every run's per-stage split summed exactly to its ops.

**Chosen allocations** (tuning map, fitness (c) as per-pricing ratios to the variant's qs alone):
- **A, qs + lc 1.4:** rho 5,793 (2^12.5), ECM 32,768 (2^15); td and pm1 off.
- **B, N51-0917's qs:** rho 5,793 only; ECM off, because ruint is the binding pricing there (N51-0917's qs costs about 0.06 ruint per official op, so ECM's spending costs more than the qs work it saves).
- **Balanced control,** both variants: every budget 0 (qs alone).

**Sealed results** (log₂ mean, 95% interval; speed-up over the variant's own qs alone):

| | official | ruint | Montgomery |
|---|---|---|---|
| A | 17.96 [17.86, 18.06]: 2.19× | 16.04 [15.95, 16.13]: 1.51× | 16.76 [16.67, 16.85]: 1.85× |
| qs + lc 1.4 alone | 19.09 [19.07, 19.11] | 16.63 [16.57, 16.68] | 17.65 [17.62, 17.68] |
| B | 18.95 [18.91, 18.99]: 1.44× | 15.08 [15.04, 15.11]: 1.26× | 16.62 [16.58, 16.66]: 1.38× |
| N51-0917's qs alone | 19.48 [19.45, 19.50] | 15.41 [15.39, 15.43] | 17.09 [17.06, 17.11] |
| L53-0972 (p-1 front) | 19.00 [18.91, 19.09] | 17.36 [17.35, 17.38] | 17.79 [17.74, 17.83] |

- **Worst band** (ratio to its own qs alone): A's is the 36-bit band, 0.90× official, 1.20× ruint, 1.01× Montgomery; B's is 32 bits, 1.01×, 1.14×, 1.05×. Under ruint both allocations cost more than qs alone in their hard bands; the population mean still wins.
- **(e) calls:** A over qs + lc 1.4 alone: **A**. A over L53-0972: **A**. B over N51-0917's qs alone: **B**. B against L53-0972: undecided (tie under official). L53-0972 against qs + lc 1.4 alone: undecided.
- **Cross-comparison under one reference (qs + lc 1.4 alone), robust ratio = max over pricings:** A 0.666 (map 0.641), B 0.907 (map 0.896), N51-0917's qs alone 1.305, L53-0972 1.667. **A ranks first.** B is cheapest under ruint (0.34) and Montgomery (0.49), but its official 0.91 binds. The (e) call between A and B is **undecided** (official A; ruint and Montgomery B).
- **The p-1 front genome loses to qs + lc 1.4 alone under ruint** (1.67×): its weaker qs genes and its full-multiply p-1 cost dominate at real prices.

**Predictions, scored as written:**
- **Mixed, official, about 2×: holds for A** (2.19×); **miss for B** (1.44×).
- **Mixed, calibrated, 1.3–1.7×:** A ruint 1.51× holds; **A Montgomery 1.85× is a miss on the high side**; **B ruint 1.26× is a miss on the low side**; B Montgomery 1.38× holds.
- **The sealed mean falls inside the map's 95% interval overall and in at least 5 of 7 bands: holds** for both allocations under all three pricings (A 6/7 bands, B 5/7; the 20-bit band misses for both, and B's 42-bit band too).
- **Balanced-only control, budgets about 0: holds** (exactly 0 for both variants).
- **Budget shape:** td small (0) holds; rho moderate holds; p-1 off holds (so the pm1 per-band report and the rho-absorption check did not trigger); **ECM largest held only for qs + lc 1.4** (with N51-0917's qs, ECM is off).

**The gap to the best single lamp per band (hindsight, information only).** In the 24–42-bit bands A costs 2.3–9.6× the best single lamp for that band (official), so the allocation pays by covering the bands, not by beating the right lamp within a band. This gap cannot be closed by a selector on this population: every N is 84 bits, so no free feature reveals the band, and the budgets are the probe. Stage 9.5's selector is only useful where free features differ (mixed sizes).

**Mechanisms, from the tuning map (information only, no new runs; ratio = forced allocation's mean cost / the chosen one's, per pricing):**
- **ECM off in B (N51-0917's qs + rho 2^12.5): ruint binds.** Forcing ECM to 2^10 gives 1.001 / 1.020 / 1.007 (official / ruint / Montgomery); 2^12 gives 1.006 / 1.081 / 1.028; 2^14 gives **0.985** / 1.292 / 1.076. ECM would help slightly on the official count at 2^14, but it costs more than it saves under real prices, where N51-0917's qs is cheap.
- **p-1 off because rho + ECM cover the small bands more cheaply than p-1's full ~2^17.** p-1's full length is 2^17.13 ops on average (124,044–160,609). Forcing it on in A gives 1.005 / **2.121** / **1.526**: neutral on the official count, much worse under real prices. Per band (mean per number of the band, saved where p-1 succeeds / added where it fails):
  - official: 24 bits −16,514 / 32,462; 28 bits +77,040 / 67,951; 32 bits +113,798 / 85,291; 42 bits +107,973 / 104,062;
  - ruint: negative savings in every band (e.g. 28 bits −33,891 / 67,955; 42 bits −5,583 / 104,067).
  
  Where p-1 succeeds, it often replaces an ECM success that would have come cheaper, so even its successes save nothing in the small bands. In the hard bands, under the official count, its successes save about as much as its failures cost. Under ruint, qs is cheap, so p-1's full-multiply length never pays. (The 16-bit band never reaches p-1: rho finishes first.)

**Per band and pricing: official-only best against robust best (map only, tuning numbers; `evolve/partition_bands.py`/`.out`).** Ratios to qs + lc 1.4 alone. The official-only optimum is rho 3,158 and ECM 2^20 (td and p-1 off); the robust optimum A is rho 5,793 and ECM 2^15.

| | official-only | A | primefac |
|---|---|---|---|
| all bands, official | 0.144 | 0.450 | 0.493 |
| all bands, ruint | 0.782 | 0.641 | 1.102 |
| all bands, Montgomery | 0.392 | 0.527 | 0.764 |
| robust (max of the three) | 0.782 | **0.641** | 1.102 |

- **The difference is ECM's budget, not rho's.** On the official count, ECM alone costs less than qs alone in every band (0.03–0.37), so the official-only optimum lets ECM run almost to completion, and it is 3.1× cheaper than A there. Under ruint, ECM alone costs more than qs alone at 36 and 42 bits (1.68×, 1.97×), and 132% of the official-only plan's extra ruint cost comes from those two bands (50% + 82%), partly offset by its savings at 24–32 bits (−36%). So A gives up 3.1× on the official count to avoid that.
- **Rho is cheaper than qs at 20–28 bits under every pricing** (rho alone over qs alone: 0.005, 0.021, 0.069 official; 0.027, 0.112, 0.395 ruint; 0.016, 0.063, 0.212 Montgomery), and cheaper than ECM alone there too. Yet both optima keep rho small (3,158 and 5,793 ops).
- **The rho side of the between-band trade** shows against primefac's 168,000-op rho budget. It makes 20–28 bits cheaper than A under ruint (0.03, 0.11, 0.40 against 0.05, 0.37, 0.71), but every number at 32–42 bits pays the whole budget: 1.9–2.7× qs alone under ruint, against A's 1.0–1.2×. qs's cost is cheap at real prices, so a failed rho budget weighs more there than on the official count.

**Exhaustive baseline before Run 8 (map only, tuning numbers; `evolve/partition_orders.py`/`.out`/`.json`; prediction in PLAN first).** qs fixed at qs + lc 1.4; all 24 orders of td, rho, pm1, ECM.
- **Every order's optimum is one of two plans.** td and p-1 are off in all of them, so only whether rho runs before ECM matters. Rho before ECM (12 orders): the exact optimum over the map's budget grid is rho 4,096, ECM 32,768 (fitness 0.6480), and refinement on the 1/8-octave grid gives rho 5,793, ECM 32,768: **exactly A** (0.6408). ECM before rho (12 orders): the optimum switches rho off, ECM 65,536 (0.6731), worse than the best by log₂ +0.071 [+0.006, +0.131] (paired).
- **Card order matters** (12 of 24 orders sit above the best beyond the paired interval), but only as rho-before-ECM.
- **Restated: rho with a budget, run first as a cheap pre-filter before ECM, against ECM alone (rho off).** With ECM at 2^15 and td and p-1 off, turning rho off costs log₂ +0.056 [+0.037, +0.079] against rho 4,096, and +0.072 [+0.047, +0.102] against rho 5,793 (paired 95%): **about 4–5%** in robust fitness, well outside noise. ECM-first orders lose for this reason: their optimum turns rho off.
- **Prediction** ("td → rho → ECM, p-1 off, or ECM before rho at large budgets; within noise of A"): **the first form held** (rho before ECM, p-1 off, td off), **the ECM-first alternative did not** (worse beyond noise), and **within noise of A held**: the refined optimum is A itself; the grid-exact optimum is 1.1% worse only by grid resolution.
- **Landscape:** 131,712 grid combinations; robust fitness from 0.648 (minimum) through 0.676 (1%), 0.728 (5%) and 1.435 (median) to 4.325. 2,600 combinations (1.97%) lie within the best grid point's own 95% interval (fitness ≤ 0.688), all with p-1 off and ECM 2^15–2^17, td anywhere from 0 to 2^16 and rho from 0 to 2^14. **A plateau, not an isolated minimum:** any search that turns p-1 off and puts ECM near 2^15–2^17 lands near the optimum. That threshold is the best point's own sampling interval, which is wide; paired comparisons separate finer differences (the ECM-first plan, 4.9% worse, is inside it yet distinguishable by the paired interval).

**Limitations:** stage genes fixed, not retuned for the small bands (ECM's b1/b2 were tuned on 24–42-bit factors); one population shape (84-bit N, seven bands, uniform prior).

## 2026-10-24 — lampcore per-type op counters: cost model, written before any code (Run 8 prerequisite)

PLAN.md, Run 8: every run scored for Run 8 must record per-type op counts, the types `optypes.py` splits and `calibrate.py` prices, not just total ops. Today they come only from Python traces. This adds them to lampcore. **Read-only instrumentation: no op count changes.**

**What is counted, per run** (every card, race sides and budgeted stages included), using the types `optypes.per_type` emits:
- qs: mult, fb, setup_full, setup_euclid, setup_small, sieve_update, sieve_scan, confirm_full, confirm_td, la, sqrt_mul, sqrt_gcd, lp_full, lp_small, and **check** (the opt-in ledger check phase; added now to `optypes.qs_counts`, priced at a full multiply, as the calibration plan's phase table says);
- ecm: setup_mul, setup_euclid_N, mul, gcd;
- rho and pm1: mul, gcd; td: td_mod;
- sq, ps, cfrac: one type each (sq_ops, ps_ops, cfrac_ops), still unpriced, as in `optypes.py`.

**How lampcore matches the Python split exactly.** Python's qs split takes each full-price part from trace events and each small part as the phase total minus it. lampcore keeps one event counter per full-price part, incremented at the same program points as Python's trace updates:
- (s − 1)·combinations after forming the A's, and 2s at the start of each A (before its charges, as Python's a_count);
- each setup Euclid inverse's steps after its charge;
- 2M + 1 after each polynomial's sieve charges;
- 2 after each candidate's confirm charges;
- each sqrt gcd's steps after its charge;
- 1 after each large-prime combination's charges;
- for ECM, each curve's setup Euclid steps at their charge (this reproduces `ecm_counts`' rule for a curve still in setup).

Small parts are phase total minus full parts, as in Python. The split is taken **per stage** from that stage's own deltas (ops, tests, phases, event counters), so genomes mixing cards that share phases (qs and cfrac share the ledger's) split correctly; rho and pm1 split by the stage's ops and tests; a race adds each side's split; a budgeted stage's split covers what it spent. The in-progress attribution documented in `optypes.py` (a torn-down side's unfinished unit) is reproduced, not corrected, because the counters sit where Python's trace updates do.

**Output.** Behind a flag (`lampcore --types`), so the default output stays byte-identical: each line gains " T" and the counts in a fixed type order. `fastlamps.run_many(types=True)` parses them. A robust-fitness helper (in `optypes.py`) prices counts with `calibrate.json`'s median P-core prices (the price table is not duplicated) and computes the (c) fitness: per pricing, mean cost / the reference's mean cost on the same numbers, then the max over the three pricings.

**Checks:**
- **Identities, every run:** the per-type counts sum to total ops, and each card's types sum to its phases' ops.
- **Parity:** lampcore's counts equal the Python per-type counts (per-stage traces) on every parity pair (parity.py extended).
- **Mutation:** a counter that drops or double-counts one type must be caught (by the sum identity or by parity).
- **Against existing results:** calibrate.json's per-number counts and scores, and the partition study's sealed per-number counts and costs, recomputed from lampcore's counters, must match the Python-trace values exactly.

**Prediction (stated before measurement):** the hot path costs at most about 2%. The counters are integer adds at a few event points beside existing charges, plus a per-stage snapshot. Measured against the current binary.

## 2026-10-24 — Library references and oracles (reuse rule): references, test oracles, published parameters; never inside a charged path

**Repo license: none.** The repo has no LICENSE file and no license field in `lampcore/Cargo.toml`, so it is all rights reserved by default. Consequences: no GPL (or other third-party) code is copied in. Algorithms are ported step by step from their published descriptions and from reading reference implementations, with every op charged and attribution in code comments and here. Choosing a license, and whether GPL-derived code could ever be accepted, is the user's decision.
- **License decided (Oct 24, user): MIT only.** `LICENSE` (MIT, copyright 2026 Jonathan Kendall), `license = "MIT"` in `lampcore/Cargo.toml`, and a License line in README. The porting policy stays coupled to the license: algorithms are ported from descriptions and papers; GPL sources (java-math-library, GMP-ECM) are read for understanding only, never translated line by line or copied. num-prime (MIT OR Apache-2.0) is compatible.

**References** (read, never imported into a card):
- **Python.** primefac 2.0.12 (MIT): Williams p+1 (`williams_pp1`) for the p+1 card; two-stage `pollard_pm1` for the p-1 stage 2 candidate (MOVES, Meet in the middle row, linked to the checkpointed p-1 row). sympy.ntheory (`pollard_pm1`, `ecm`, `qs`): readable cross-references. FLINT's qsieve: relation filtering (`reduce_matrix`, then block Lanczos) for the filtering + excess-stop pick; its size-indexed tuning table is a published starting point for qs genes (reference only: any large gap from ours is explained, not copied).
- **Java.** java-math-library (Tilman Neumann, GPL-3): SquFoF31Preload / SquFoF63 for the SQUFOF mode, Hart / Lehman for the sq card, PollardRhoBrentMontgomery64 (Montgomery-arithmetic rho), TinyEcm (small-factor ECM settings), CFrac63. Its stated size limits are outside reference points, to be recorded from its documentation when a move that uses it is ported (not checked here). GPL-3: read for the algorithm, never copied.
- **C.** GMP-ECM (GPL program, LGPL library): p+1, p-1 stage 2, ECM PRAC and stage 2. CADO-NFS: out of range (the NFS crossover is far above 96 bits).

**primefac's default plan, read from its source** (primefac 2.0.12, `primefac()`; downloaded to a scratch folder and read, not installed): trial division by the primes up to `trial = 1000`; then plain Floyd rho, not Brent, for up to `rho = 42000` rounds, each round three squarings mod n and one gcd; then `multifactor` on what is left. In our charging, one round is 4 ops (3 modular multiplies + 1 gcd), so 42,000 rounds = 168,000 ops. Trial division to 1000 is our td with ob = 499 (odd divisors 3-999 and the one passing charge, 500 ops), which overcharges primefac's 168 prime trials by about 330 ops.

**Outside baseline for the partition study (map only, no new sealed run), prediction written before it is computed:** primefac's plan encoded as td(ob 499) → rho(ob 168,000) → final qs + lc 1.4, evaluated from the existing map on the tuning numbers under all three pricings, as **information beside allocation A**. **Prediction: A beats it by about 1.1–1.3×,** because its larger rho budget is mostly spent on bands rho can't reach.

**primefac baseline, result (map only, tuning numbers; `evolve/partition_primefac.py`/`.out`):** primefac's plan / allocation A = **1.10×** official, **1.72×** ruint, **1.45×** Montgomery; robust ratio against qs + lc 1.4 alone: primefac 1.102, A 0.641 (primefac / A 1.72×). Under ruint, primefac's plan is worse than qs alone.
- **Prediction (A beats it by about 1.1–1.3×): held on the official count, at the low edge (1.10×); A's lead is larger under the calibrated pricings (1.72×, 1.45×), above the stated range.**
- **The stated reason is half right.** primefac's 168,000-op rho budget is wasted where rho can't reach (rho succeeds within it on 38/80 numbers at 32 bits, 2/80 at 36, 0/80 at 42), so it costs 1.0–1.5× A there (official), and up to 2.3× under ruint. But in the 20–28-bit bands, where rho always succeeds within it, primefac's plan is 3–8× cheaper than A (official). A's robust optimum gives rho only 2^12.5 and lets ECM (2^15) take those bands, because under ruint every rho or ECM op costs a full multiply while qs's cost is cheap; on the official count alone a larger rho budget would pay there.

**Oracles** (harness and tests only; versions pinned and recorded with the oracle commit): Python, `sympy.factorint` plus a primality check on every newly generated (N, p, q); Rust, num-prime as a lampcore dev-dependency only, unreachable from charged code (shown by `cargo tree`). gmpy2 / primesieve are allowed only in the harness (generation, primality), not used yet.
- **Built (Oct 24).** Python: `evolve/oracle.py`, sympy **1.14.0** (the system package, version asserted in code); `check(nums)` asserts p·q = N, p and q prime, and `sympy.factorint(N) == {p: 1, q: 1}`. New populations go through `check()` when generated. On every population the committed studies use (Stage 8's 15 cells, partition tuning and sealed): 2,320 numbers in 29 populations, all confirmed, 26 s. python-flint is not installed and not needed.
- Rust: **num-prime =0.7.0** (MIT OR Apache-2.0) as a `[dev-dependency]` of lampcore only; `lampcore/tests/oracle.rs` checks a fixture of 32 committed study numbers (4 per partition band and 4 balanced 84-bit Stage 8 numbers): num-prime's `factorize128` gives exactly {p, q}, and lampcore's answers (tuned qs + lc 1.4, ECM, rho) are always p or q. `cargo tree -e normal` lists only ruint and serde_json, so num-prime cannot reach charged code. Cargo.lock was gitignored at first, so num-prime's own dependencies were not pinned by that commit.
- **Cargo.lock committed (Oct 24).** `lampcore/Cargo.lock` is now tracked (removed from .gitignore), so the dependency versions (ruint 1.20.1, serde_json 1.0.154, num-prime 0.7.0 and their transitive dependencies, 200 packages in the lock including platform-specific ones that never build here) are pinned for reproducibility. Checked: `cargo build --release` had nothing to rebuild, and the oracle tests pass.

## 2026-10-24 — Run 8 tooling: Optuna in a project virtual environment (reuse rule)

- **Environment:** `.venv` (gitignored), created with `--system-site-packages`, so numpy 2.4.4 (user site) and sympy 1.14.0 (system) are exactly what every earlier result used; the oracle asserts the sympy version. Run 8 scripts run under `.venv/bin/python`; earlier scripts keep working under the system python, unchanged.
- **Optuna 5.0.0, pinned** in `requirements-run8.txt` with what the venv added: alembic 1.20.1, colorlog 6.12.0, SQLAlchemy 2.1.6. Its other requirements come from the system site packages: packaging 25.0, PyYAML 6.0.2, tqdm 4.67.1 (and Mako 1.3.9.dev0, typing_extensions 4.13.2, MarkupSafe 2.1.5 for alembic/SQLAlchemy).
- **License:** MIT (the installed package's metadata: OSI classifier "MIT License", with a LICENSE file and a LICENSE_THIRD_PARTY file). Compatible with the repo's MIT license. It is a search driver only, never inside a charged path: it proposes genomes, and lampcore scores them.
- **Maintenance:** an active project by the release history pip lists (4.0.0 through 4.9.0, then 5.0.0, the current version; repository github.com/optuna/optuna). Release dates were not checked: the request for PyPI's metadata was declined in this session.
- **Harness tests** (`evolve/run8_test.py`, before any arm ran): identical scoring through every method's path, TPE and random samples inside the shared bounds (TPE proposed all 24 orders), exact evaluation counts (340 and 1,360) for every method including the fresh-batch arm and the warm-started probe, and the qs-gene sub-experiment keeping A's budgets and order: 0 failures, exit 0.

## 2026-10-24 — Primes and gaps as the reference line: does any lamp's cost depend on p's arithmetic beyond its size? (map-only test; predictions before computing; never fitness)

**Data:** `partition_map.json`, the 560 tuning numbers (84-bit N, smaller factor p in seven bands, 80 each), with each lamp's ops-to-success recorded alone (td, rho, p-1, ECM to a cap of 2^21; qs + lc 1.4 to 2^28). No new runs.

**Responses:** td, rho and ECM, log₂ ops-to-success on the numbers each solved within its cap (td only reaches the 16- and 20-bit bands); p-1, success or not (it is all or nothing at its full length); qs + lc 1.4, log₂ ops.

**Features of p** (computed with sympy, harness only): gap before p and gap after p, each divided by ln p; twin-prime flag (p − 2 or p + 2 prime); log(largest prime factor of p − 1) / log p and the same for p + 1 (smoothness); p mod 4; p mod 3; and, as a control for td, log p within its band.

**Method:** within each band, rank-transform each feature and each response; a pooled Spearman correlation over the bands' within-band ranks; a permutation test permuting responses within bands (10,000 permutations, random.Random(2026)); Holm's correction over every (lamp, feature) pair tested.

**Predictions (stated before computing):**
- **p-1 correlates with the smoothness of p − 1** (success more likely when the largest prime factor of p − 1 is small). **Positive control:** if it is not found, the test is too weak and nothing else is read.
- **rho, ECM and qs show no correlation with the gap features** (null).
- **td depends on p's size only:** a strong correlation with log p within its band, and none with any other feature.
- Any gap correlation that survives Holm is a candidate pattern only, and is re-tested on the sealed partition numbers before it is believed. A null result goes into MOVES as ruled out (conditions: these sizes, these lamps).

**Result (`evolve/primes_gaps.py`/`.out`/`.json`; 40 tests).**
- **Positive control holds:** p-1's success against log LPF(p − 1) / log p, rank correlation −0.528, Holm-adjusted p 0.004. The test can see a real arithmetic dependence.
- **td depends on p's size only: holds** (+1.000 with log p within its band; nothing else survives).
- **rho, ECM and qs show no correlation with the gap features: holds.** No gap, twin, smoothness or residue feature survives Holm for any of them (the largest raw effect, ECM against the gap after p, +0.094, raw p 0.026, Holm 0.90). With 560 numbers and Holm over 40 tests, correlations above ~0.17 pooled within bands would likely have been detected (80% power, strictest Holm step); single-band effects below ~0.43 are not ruled out. [Reworded Oct 24 after an outside power check (NOTES, "Outside checks, second round"); was "this rules out within-band rank correlations above about 0.15".]
- **Size effects:** qs + lc 1.4 against log p within its band, +0.164 (Holm 0.004), and rho, +0.145 (Holm 0.056). For qs this is N's size, not p's: within a band log N tracks log p (+0.71 to +0.88), and qs's cost tracks log N at least as strongly (+0.19 to +0.29 against +0.13 to +0.30). For rho it is the expected sqrt(p) scaling.
- No gap correlation survived, so there is no candidate pattern to re-test on the sealed numbers. Recorded in MOVES as ruled out.

**Also (visualization, information only):** an exact picture at small sizes (N ~ 2^24-2^32): the candidate line 2..√N with every prime as a point and every gap as a span, and per lamp which stations its work rules out or finds over time: td walks every station; rho lights primes by size; p-1 lights only primes whose p − 1 is B-smooth; ECM is a probabilistic speckle; sq lights primes near √N; qs finds the answer without walking the line. With it, td's share of work spent on gap interiors (composites) against primes.

## 2026-10-24 — Run 8 balanced sanity arm: verdicts (before the mixed arm)

`evolve/run8_sanity.json`, `run8_sanity_report.out`, `run8_sanity_paired.out`; 8 seeds x 4 methods x 340 evaluations, balanced 84-bit numbers (18 per evaluation), sealed 80. Fitness against qs + lc 1.4 alone (1.0); paired 95% intervals.
- **Evolution: passed.** Best-of-8 0.920 tuning / 0.969 sealed [0.856, 1.087]; median genomes 0.993 [0.974, 1.011] and 1.049 [1.025, 1.073] sealed.
- **TPE: passed.** Best-of-8 0.817 tuning / 0.951 sealed [0.866, 1.030]; median genomes 0.999 [0.972, 1.059] and 0.983 [0.961, 1.003] sealed. **Seeds 77 and 78 stuck on flat regions** (best 1.714 and 1.896): more than half of seed 78's trials scored exactly 1.896, in a region where a 725k-op ECM budget run first finishes every balanced number, so the qs genes TPE kept varying change nothing; seed 77 settled around p-1 on at full length. Deterministic (the exact jobs reproduce their traces; no evaluation missed): search behaviour on plateaus, not a scoring fault.
- **Random search: failed, as predicted** (every pick worse than qs alone beyond noise; best-of-8 sealed 1.072 [1.046, 1.098]).
- **Fresh-batch evolution: borderline** (median genomes 1.265 [1.152, 1.370] and 1.073 [0.988, 1.153] sealed; median-of-8 sealed 1.203): 18-number batches are noisy.
- **Decisions for the mixed arm:** the primary TPE stays at Optuna's defaults and carries the two-clause prediction; a secondary "tpe-tuned" arm (n_startup_trials 136 = 10%, multivariate) is pre-registered and reported separately. The OVERFIT bracket (gap against A's gap, bracketed by qs alone's 0, paired bootstrap) and both clauses are computed by `evolve/run8_final_report.py`, written and tested on the sanity data before the mixed arm ran. Time estimate revised to about 4-4.5 h (PLAN).


## 2026-10-24 — Run 8 mixed and mixed-qs arms: results (sealed numbers, run once)

Files (all in `evolve/`): `run8_mixed.json`, `run8_mixed-qs.json` (runs, traces, convergence); `run8_mixed.out`, `run8_mixed-qs.out` (wall times; both arms exited 0); `run8_mixed_final.out`/`.json`, `run8_mixed-qs_final.out`/`.json` (`run8_final_report.py`, committed before launch in 3b0e015); `run8_mixed_gate.out`/`.json`, `run8_mixed-qs_gate.out`/`.json` (`run8_gate.py`, written after the run: no new selection, only checks of what was pre-registered). 8 seeds (71–78) × 1,360 evaluations per method; mixed: 84 tuning numbers per evaluation (12 per band); sealed 560 (80 per band, seven bands 16–42). Fitness (c) = robust ratio to qs + lc 1.4 alone (1.0); lower is better. Intervals are paired 95% bootstraps resampled within bands (10,000).

**Fixes to the report script after the run (both found reading the output; neither changes a number the run produced):**
1. clause (a) printed `evolution_evaluations: None`: the target recomputed on the tuning set (0.3896320334158959) differed from the traced value (0.389632033415896) in the last ulp, so `f <= target` never fired. Now compared with a 1e-12 relative tolerance. Evolution now reaches the target at 1,356; TPE still never reaches it, so the verdict did not change.
2. A sealed miss was scored at its capped cost. The mixed-qs evolution genome for seed 74 (kc 1) does not factor sealed number 446 (83-bit N, band 36) within 2^28. The report printed sealed 0.474; it is now scored as the Evaluator scores a miss (MISS, gap +inf, counted OVERFIT). This is the only sealed miss among the 72 genomes. The run itself scored misses during tuning as 1e9: mixed 26, mixed-qs 181 such evaluations.

**Headline.**
- **qs + lc 1.4 alone is beaten by about 2x on the mixed population**, and most of the gain comes from the five qs genes, not from budgets or order.
- Best sealed fitness:
  - mixed: TPE 0.455 (evolution 0.484, tpe-tuned 0.459, fresh batches 0.525, random 0.561);
  - mixed-qs (budgets and order fixed at A): TPE 0.472 (random 0.472, evolution 0.480, probe 0.482).
- Allocation A, with qs genes at qs + lc 1.4, scores 0.675 on the same sealed numbers.
- The mixed winners' budgets and order sit near A: rho before ECM (except random's), td 0 or small, pm1 off, rho about 1k–14k, ECM about 32k–71k. That is what the partition study found.

### Best-of-8 and median-of-8 (tuning / sealed)

| arm | method | best-of-8 tuning (seed) | its sealed | median-of-8 tuning | median-of-8 sealed |
|---|---|---|---|---|---|
| mixed | evolution | 0.390 (77) | 0.484 | 0.481 | 0.503 |
| mixed | TPE | 0.452 (71) | 0.455 | 0.494 | 0.509 |
| mixed | random | 0.558 (72) | 0.561 | 0.577 | 0.624 |
| mixed | evolution-fresh (third arm) | 0.449 (77) | 0.525 | 0.534 | 0.538 |
| mixed | tpe-tuned (secondary) | 0.417 (76) | 0.459 | 0.478 | 0.511 |
| mixed-qs | evolution | 0.381 (77) | 0.480 | 0.444 | 0.470 (seed 74 MISS counted as worst) |
| mixed-qs | TPE | 0.377 (77) | 0.472 | 0.448 | 0.469 |
| mixed-qs | random | 0.398 (77) | 0.472 | 0.477 | 0.496 |
| mixed-qs | tpe-warm (probe) | 0.379 (77) | 0.482 | 0.446 | 0.465 |

**Failure mode of best-of-8 by tuning fitness.** It compares fitness across eight different tuning sets, so it partly selects the easiest set. Seed 77's set gives the best-of-8 for all four methods in mixed-qs and for two of five in mixed. Its gap is +0.25 to +0.35 log2 for every method there. Sealed fitness is the comparable number.

### T1 / T2 (evaluations; median [IQR], seeds reached of 8; against A on each seed's own tuning set)

| arm | method | T1 (enter A's interval) | T2 (reach A's point) |
|---|---|---|---|
| mixed | evolution | 16 [11, 78], 8/8 | 162 [108, 252], 8/8 |
| mixed | TPE | 10 [3, 30], 6/8 | 40 [21, 63], 6/8 |
| mixed | random | 6 [5, 17], 8/8 | 138 [75, 320], 8/8 |
| mixed | tpe-tuned | 34 [5, 152], 8/8 | 146 [48, 366], 8/8 |
| mixed | evolution-fresh | not computed (no fixed tuning set) | — |
| mixed-qs | evolution | 14 [6, 23], 8/8 | 20 [6, 42], 8/8 |
| mixed-qs | TPE | 6 [6, 8], 8/8 | 8 [6, 10], 8/8 |
| mixed-qs | random | 16 [8, 42], 8/8 | 35 [14, 86], 8/8 |
| mixed-qs | tpe-warm | 1 [1, 1], 8/8 | 1 [1, 2], 8/8 (trivial: trial 1 is A) |

**TPE stalls in the mixed arm**, the same failure as in the sanity arm. Seeds 72 and 75 never reached A. They ended at 0.859 and 0.881, each with pm1 on at full length and an ECM budget of 451k–837k: the plateau where ECM finishes nearly everything and the qs genes stop mattering. tpe-tuned (136 startup trials, multivariate) had no stalled seed.

### Winning genomes (best-of-8 by tuning), split

| arm | method | order | td | rho | pm1 | ecm | kc | bc | mc | tc | lc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | allocation A (reference for T1/T2) | td>rho>pm1>ecm | 0 | 5793 | 0 | 32768 | 32 | 1.10 | 0.250 | 1.38 | 1.40 |
| mixed | evolution | rho>td>pm1>ecm | 0 | 11811 | 0 | 33422 | 11 | 0.99 | 0.925 | 1.26 | 1.35 |
| mixed | TPE | rho>pm1>ecm>td | 0 | 12593 | 0 | 32795 | 7 | 1.13 | 0.476 | 1.24 | 1.38 |
| mixed | random | ecm>td>pm1>rho | 0 | 1129 | 0 | 71413 | 22 | 1.27 | 1.125 | 1.28 | 1.31 |
| mixed | evolution-fresh | rho>pm1>ecm>td | 5043 | 5001 | 0 | 49369 | 26 | 1.09 | 0.893 | 1.45 | 1.13 |
| mixed | tpe-tuned | pm1>td>rho>ecm | 504 | 13762 | 0 | 31959 | 6 | 1.08 | 0.434 | 1.27 | 1.33 |
| mixed-qs | evolution | (A) | | | | | 5 | 1.01 | 0.672 | 1.04 | 1.63 |
| mixed-qs | TPE | (A) | | | | | 4 | 0.90 | 0.734 | 1.10 | 1.66 |
| mixed-qs | random | (A) | | | | | 7 | 1.05 | 0.577 | 1.39 | 1.41 |
| mixed-qs | tpe-warm | (A) | | | | | 2 | 0.85 | 0.801 | 1.08 | 1.72 |

- **Effective order.** pm1 is off in every winner, and td is 0 in most, so rho runs before ECM in every mixed winner except random's (ECM first, rho 1.1k).
- **qs genes, against qs + lc 1.4.** Lower kc (2–11 in the TPE and evolution winners, against 32), higher mc (0.43–0.93 against 0.25), lower tc (1.04–1.27 against 1.38). With budgets fixed at A (mixed-qs), lc is higher in the evolution, TPE and probe winners (1.63–1.72 against 1.40).
- Per-seed genomes are in the `_final.out` files.

### OVERFIT bracket (gap = log2 sealed/tuning of each run's best; paired bootstrap)

| arm | method | OVERFIT (gap above A's) | overfit at all (gap above 0) |
|---|---|---|---|
| mixed | evolution | 1/8 (seed 73) | 2/8 |
| mixed | TPE | 0/8 | 0/8 |
| mixed | random | 1/8 (seed 73) | 1/8 |
| mixed | evolution-fresh | 1/8 (seed 73) | 1/8 |
| mixed | tpe-tuned | 1/8 (seed 73) | 2/8 |
| mixed-qs | evolution | 1/8 (seed 74, sealed MISS) | 2/8 |
| mixed-qs | TPE | 0/8 | 1/8 |
| mixed-qs | random | 0/8 | 0/8 |
| mixed-qs | tpe-warm | 1/8 (seed 77) | 1/8 |

- **Seed 73's tuning set misleads four of five methods** in the mixed arm toward ECM budgets of 392k–1.05M. On sealed numbers those genomes run 1.4x–2.2x worse than on tuning (gap +0.45 to +1.13 log2).
- **The premise that TPE optimizes against a fixed set more aggressively** (the reason for the check) is not borne out: TPE has the fewest OVERFIT runs (0/8 in both arms).

### ACCEPT gate (no band worse than 1.5x qs + lc 1.4 alone under any pricing; sealed, 80 per band)

- **Every method's best-of-8 champion passes in both arms.** The worst champion band is 1.058: evolution-fresh, band 36, official. Allocation A passes, at worst 1.266 (band 36, ruint).
- **Non-champion runs that fail:**
  - mixed: seed 73 for evolution (2.055), random (4.548, Montgomery), evolution-fresh (2.151) and tpe-tuned (2.009); TPE seeds 72 (2.019) and 75 (2.170). All are band 42, ruint unless noted, and all have ECM budgets of 392k or more.
  - mixed-qs: evolution seed 74 (the sealed miss).

### Per-band sealed ratios, best-of-8 genome (official / ruint / Montgomery)

| arm | method | 16 | 20 | 24 | 28 | 32 | 36 | 42 |
|---|---|---|---|---|---|---|---|---|
| mixed | evolution | .001/.008/.005 | .006/.031/.018 | .077/.192/.118 | .570/.541/.475 | .718/.680/.596 | 1.010/.775/.763 | .989/.753/.747 |
| mixed | TPE | .001/.008/.005 | .006/.031/.018 | .073/.191/.119 | .550/.564/.516 | .676/.704/.635 | .946/.812/.824 | .916/.780/.795 |
| mixed | random | .034/.179/.092 | .056/.237/.125 | .118/.342/.193 | .429/.579/.430 | .659/.743/.592 | .965/.930/.803 | .989/.921/.815 |
| mixed | evolution-fresh | .001/.008/.005 | .012/.064/.034 | .190/.354/.234 | .620/.613/.529 | .745/.716/.626 | 1.058/.857/.822 | 1.035/.829/.803 |
| mixed | tpe-tuned | .002/.009/.006 | .006/.032/.019 | .073/.196/.122 | .533/.578/.518 | .677/.739/.655 | .940/.829/.836 | .934/.837/.831 |
| mixed-qs | evolution | .001/.008/.005 | .006/.036/.020 | .191/.315/.224 | .585/.546/.509 | .678/.625/.580 | .940/.729/.757 | .939/.705/.741 |
| mixed-qs | TPE | .001/.008/.005 | .006/.036/.020 | .185/.313/.221 | .577/.543/.502 | .656/.619/.569 | .921/.724/.746 | .940/.722/.751 |
| mixed-qs | random | .001/.008/.005 | .006/.036/.020 | .191/.320/.235 | .586/.566/.543 | .668/.660/.622 | .927/.755/.803 | .910/.743/.789 |
| mixed-qs | tpe-warm | .001/.008/.005 | .006/.036/.020 | .191/.314/.223 | .626/.558/.526 | .659/.619/.568 | .944/.726/.749 | .931/.703/.734 |

- **The three pricings agree** (all below 1) on every band except three mixed-arm cells above 1 under official only: evolution band 36 and evolution-fresh bands 36 and 42. Per (e), those cells are undecided.
- **At band 42** (balanced 84-bit), the mixed-qs genes are about 0.70–0.75x the reference under the calibrated pricings but about 0.93x official. The gain on balanced numbers comes mostly from operations the calibrated pricings charge more, consistent with the sanity arm's best of 0.951 (official dominating the robust max there).
- **Bands 16–24 are decided by the pre-stages**; the qs genes barely matter there.

### Predictions, scored as written

1. **Clause (a)**, as written in PLAN: "TPE reaches a fitness at least as good as evolution's best-of-4 final fitness within fewer evaluations". The wording predates the move to 8 seeds, and the report committed before launch implements it as best-of-8, so both readings are given.
   - mixed, best-of-4 (seeds 71–74, target 0.473): **holds**. TPE reaches it at 439, evolution at 1,347.
   - mixed, best-of-8 (target 0.390, evolution's seed 77): **fails**. Evolution reaches it at 1,356; TPE never does (its best is 0.452). Recorded as "evolution converges faster" per the pre-registered meaning. The target is seed 77's tuning value, which overfits (gap +0.313 [+0.070, +0.487]).
   - mixed-qs, best-of-4 (target 0.427): **fails** (TPE never reaches it). Best-of-8 (target 0.381): **holds** (TPE 405, evolution 1,275).
2. **Clause (b)**, "at the full budget, TPE's best ties or beats evolution's best" (sealed, paired):
   - mixed: **holds, TPE better**. log2 TPE/evolution −0.090 [−0.107, −0.063].
   - mixed-qs: **holds, tie**. −0.023 [−0.053, +0.010].
3. **"Random search is predicted clearly worst."**
   - mixed: **holds**. Random's best sealed 0.561 against 0.484 (evolution) and 0.455 (TPE); median-of-8 sealed 0.624 against 0.503 and 0.509.
   - mixed-qs: **fails**. Random's best sealed is 0.472, equal to TPE's and below evolution's 0.480. The pre-registered meaning ("the fitness surface is flat at that genome") fits only near the winners: random found the same region all methods found, about 1.4x better than A.
4. **Exhaustive baseline: "The Run 8 searches should reach at least this [A] on that subspace."** **Holds.** Every method's best-of-8 beats A's sealed 0.675 in both arms. Every mixed-arm method reached T2 on 8/8 seeds, except TPE (6/8).
5. **Probe vs cold TPE ("does the prior help?"): no.** log2 warm/cold +0.031 [−0.014, +0.076], a tie.
6. **"A near-optimal" or "partition study under-explored by Z": partition study under-explored by 1.40x.**
   - The probe's own best (tpe-warm, seed 77) against A: log2 −0.485 [−0.543, −0.429].
   - The best method overall (cold TPE): 1.43x [−0.574, −0.458].
   - The under-exploration is in the qs genes, which the partition study held fixed at qs + lc 1.4. On its own axes (budgets, order) the mixed winners stay near A.

Predictions scored in this entry: 6. (a) holds or fails depending on the reading, as above; (b) holds in both arms; 3 holds in mixed and fails in mixed-qs; 4 holds; 5 and 6 are answered questions, not directional predictions.

**Omissions against the reporting rules (PLAN).**
- No power estimate was written before the clause (b) comparison. For the record, the intervals' half-widths are about 0.02 log2, which resolves differences of about 1.5%.
- The paired intervals are of each method's best-of-8 genome. Separate per-method intervals beside them were not computed.

**Timing.**
- mixed: 5,475 s. mixed-qs: 3,642 s. Total 2.5 h, against the measured estimate of 4–4.5 h. The estimate was flagged as likely high, because mixed numbers are cheaper for genomes with rho or ECM budgets.

**Next experiments, ranked by information per compute.**
1. **Re-run the partition map with the mixed-qs qs genes** (for example TPE's kc 4 / bc 0.90 / mc 0.734 / tc 1.10 / lc 1.66). This shows whether A's budgets stay optimal once qs is cheaper. Map only, minutes.
2. **The qs-gene winners on the balanced population** (sanity arm's sealed set) under all three pricings. This checks whether the new qs genes should replace qs + lc 1.4 as the reference. Minutes.
3. **A paired comparison of the mixed winners against the mixed-qs winners** on sealed numbers. This measures what budget and order freedom adds beyond A (point estimates: 0.455 against 0.472, about 3.5%). Minutes, with a power estimate first.
4. **The illumination picture** (primes and gaps brief), already queued.

## 2026-10-24 — Run 8 wrap-up: clause (a) verdict, lessons, recorded misses

- **Clause (a): pre-registered scoring: fails in mixed, holds in mixed-qs (the best-of-8 reading the pre-launch report implemented; PLAN's literal best-of-4 wording gives the reverse); wrap-up verdict: INCONCLUSIVE.** The change of method is on the record here. The two readings scored in the results entry disagree, and neither is valid:
  - (i) PLAN's wording said "best-of-4". It was stale after the move to 8 seeds, so the best-of-4 reading scores a sentence the design no longer meant.
  - (ii) Best-of-N by tuning fitness compares different tuning sets and selects the easiest one. Seed 77 gives the best-of-8 for all four mixed-qs methods and two of five mixed ones, with gaps of +0.25 to +0.35 log2. The best-of-8 reading measures the set as much as the method.
  - The results entry's scoring stands as written; this verdict is added beside it.
- **Lesson (now a PLAN reporting rule):** method comparisons use per-seed paired comparisons on SEALED numbers (each seed: method X's best against method Y's best, same seed), summarized by a sign test over seeds plus the paired bootstrap.
- **Lesson (now a PLAN working rule):** a pre-launch consistency check. After any design change, grep PLAN and NOTES for numbers that depend on it and update them before launch.
- **Missed reporting rules, recorded as misses** (not fixed retroactively):
  - (1) No power estimate was written before the clause (b) comparison.
  - (2) No separate per-method intervals were reported beside the paired ones.
- **MOVES rows added:**
  - "Island evolution vs TPE for gene tuning": RULED OUT as superior.
  - "qs genes retuned for the mixed population": PAYS ~1.40x over A, under the stated conditions.

## 2026-10-24 — Run 8 per-seed paired comparison (added after the run; written before computing)

**Design (the new PLAN reporting rule).**
- Pairs: TPE vs evolution and TPE vs random, both arms, existing genomes, sealed numbers (560, 80 per band). No new runs.
- Per seed: d_s = log2(fitness of TPE's best / fitness of the other method's best, same seed), with a paired bootstrap interval resampling the sealed numbers within bands (10,000, random.Random(2026)).
- **Sign test:** the number of seeds with d_s < 0, two-sided exact binomial. A sealed miss counts as a loss for the method that missed and is left out of the bootstrap means.
- **Aggregate:** the mean of d_s over seeds, with two bootstraps:
  - (i) numbers resampled, seeds fixed (conditional on these 8 runs);
  - (ii) seeds and numbers both resampled (generalizes over runs).
- Labeled as added after the run, beside the pre-registered clauses, which stand as scored.

**Power estimate.**
- **Sign test:** with 8 seeds, only 8/8 or 0/8 reaches p < 0.05 (p = 0.0078). 7/8 gives p = 0.070. The test detects only a unanimous effect.
- **Per seed:** the paired half-width on sealed numbers is about 0.02–0.03 log2 (Run 8 results), so a per-seed difference of about 2% is resolvable.
- **Aggregate (ii):** its width is set by the spread of sealed fitness between seeds. From the results entry, sealed fitness spans 0.455–0.843 (mixed TPE) and 0.459–0.493 (mixed-qs TPE), so (ii) will be wide on the mixed arm, where TPE has two stalled seeds.

**Predictions.**
- **TPE vs evolution:**
  - mixed: no consistent sign (sign test p > 0.05). TPE's two stalled seeds (72, 75) lose by more than 0.5 log2, and (ii) includes 0.
  - mixed-qs: no consistent sign; (ii) includes 0.
- **TPE vs random:**
  - mixed: TPE better on at least 6/8 seeds, and (i) excludes 0.
  - mixed-qs: TPE better on at least 5/8, and (i) excludes 0 by at most 0.05 log2.

### Results (added after the run; `evolve/run8_perseed.py`, `run8_mixed_perseed.out`/`.json`, `run8_mixed-qs_perseed.out`/`.json`)

d = log2(fit TPE / fit other), same seed, sealed numbers; below 0 means TPE is better.

| arm | pair | TPE better (sign p) | intervals below / above 0 | mean d (median) | (i) numbers resampled | (ii) seeds + numbers |
|---|---|---|---|---|---|---|
| mixed | TPE vs evolution | 3/8 (0.727) | 2 / 3 | +0.090 (+0.037) | [+0.064, +0.110] | [−0.218, +0.395] |
| mixed | TPE vs random | 6/8 (0.289) | 6 / 2 | −0.217 (−0.280) | [−0.248, −0.189] | [−0.634, +0.172] |
| mixed-qs | TPE vs evolution | 5/8 (0.727) | 2 / 1 (+ seed 74: evolution's sealed miss) | +0.008 (−0.011), 7 seeds | [−0.012, +0.034] | [−0.023, +0.058] |
| mixed-qs | TPE vs random | 7/8 (0.070) | 4 / 1 | −0.051 (−0.052) | [−0.072, −0.024] | [−0.103, +0.006] |

- **Mixed, TPE vs evolution:** TPE's stalled seeds lose heavily (72: +0.728, 75: +0.699). Seed 73 is where evolution's run overfit, and there TPE wins (−0.751). Conditional on these 8 runs, the mean favours evolution by about 6–8% ((i) excludes 0). Over runs, (ii) is wide and includes 0.
- **This disagrees in direction with the best-of-8 comparison** (TPE better, −0.090 [−0.107, −0.063]). That comparison is the evidence behind the MOVES row "Island evolution vs TPE for gene tuning". Under the per-seed rule, neither method is shown superior over runs. On these runs, evolution's average is better because TPE at Optuna defaults stalled on 2/8 seeds. The per-seed result has been added to that row's conditions; its status is left as decided, pending review.
- **Mixed-qs:** TPE and evolution tie. TPE is better than random on 7/8 seeds, with an effect of about 3.5% ((i)). The sign test misses p < 0.05, as the power estimate said it would unless the result was unanimous.

**Predictions scored as written:** 4 scored, 4 held, 0 missed.
- TPE vs evolution, mixed: no consistent sign (held: 3/8, p 0.73). Stalled seeds lose by more than 0.5 log2 (held: +0.73, +0.70). (ii) includes 0 (held).
- TPE vs evolution, mixed-qs: no consistent sign (held: 5/8). (ii) includes 0 (held).
- TPE vs random, mixed: at least 6/8 and (i) excludes 0 (held: 6/8, [−0.248, −0.189]).
- TPE vs random, mixed-qs: at least 5/8, and (i) excludes 0 by at most 0.05 log2 (held: 7/8, upper end −0.024).

## 2026-10-24 — After Run 8: (1) partition map with the new qs genes, (2) the new qs genes on balanced numbers (predictions before computing)

**The new qs genes** are mixed-qs TPE's best-of-8 genome (seed 77), the one named in the Run 8 results entry's next experiments: kc 4, bc 0.8994, mc 0.7341, tc 1.1045, lc 1.6612. On the Run 8 sealed numbers it scores 0.472, with A's budgets. The other mixed-qs winners are within 0.459–0.493 sealed, so the choice among them is not expected to matter. The name "new qs" below means these genes.

### (1) Partition map re-run with the new qs (map only, tuning numbers; `evolve/partition_newqs.py`)

**Design.**
- The map's pre-stage records do not depend on the final qs, so they are reused unchanged (`partition_map.json`, 560 tuning numbers, seeds 4000000 + 100·pb + 84).
- New: the new qs alone on those 560 numbers, cap 2^28, per-type counts from lampcore `--types`.
- **Parity check first:** lampcore's per-type counts for qs + lc 1.4 must equal the map's stored Python per-type counts on all 560 numbers. A mismatch is a blocker.
- **Re-optimization:**
  - the fixed order td → rho → pm1 → ECM by `partition.optimize` (coarse grid, then 1/8-octave refinement);
  - all 24 orders as in `partition_orders.py` (exact grid optimum per order, then refinement), with the paired bootstrap against the best order.
- **Fitness (c)** is reported against qs + lc 1.4 alone (the Run 8 reference) and against the new qs alone.
- **The comparison point** is A's budgets with the new qs. The re-optimized budgets are compared with it by the paired stratified bootstrap (10,000, within bands).

**Power.** The orders baseline resolved a +0.071 log2 difference with interval [+0.006, +0.131], a half-width of about 0.06 for a large budget change. Budget changes near the optimum share most per-number costs, so their intervals are expected to be narrower. An effect at the low end of the prediction (0.015 log2) may not be resolved; if so, it is reported as unresolved, not as a tie.

**Predictions.**
- (1a) The re-optimized budgets (fixed order) put less into ECM than A: ECM ≤ 2^14, possibly 0, as the map chose with N51-0917's qs. rho in [2^11, 2^14], td 0, pm1 off.
- (1b) The re-optimized robust fitness (against qs + lc 1.4 alone) is 1–5% better than A's budgets with the new qs (log2 between −0.015 and −0.075).
- (1c) A's budgets with the new qs score 0.43–0.50 on the map against qs + lc 1.4 alone (Run 8 sealed: 0.472).
- (1d) The best order still runs rho before ECM wherever both are on. Card order still matters: at least one order's interval lies above 0.

### (2) The new qs on balanced numbers: should it replace qs + lc 1.4 as the reference? (`evolve/newqs_balanced.py`)

**Design.**
- Fresh balanced numbers: `semiprimes_pq(bits, 240, 8700000 + bits)` at 54, 60, 66, 72, 78 and 84 bits. These seeds are unused, and every number goes through `oracle.check`.
- Genomes, each alone, lampcore `--types`, cap 2^28: the new qs, qs + lc 1.4, and N51-0917's qs (information only: the calibrated leader at 60–84 bits, NOTES calibration entry).
- **Per size and pooled:** log2 of the mean-cost ratio new / qs + lc 1.4 under each pricing, paired bootstrap (10,000, random.Random(2026)), the robust ratio (c), the (e) call, and misses. The median per-number log2 ratio is reported beside it.

**Power** (from the Run 8 sealed band 42, 80 balanced 84-bit numbers, new qs against qs + lc 1.4, paired bootstrap of the mean-cost ratio):
- official −0.089 log2 (se 0.078); ruint −0.470 (se 0.074); Montgomery −0.413 (se 0.064).
- At 240 per size the se is about 0.045. The calibrated effects are resolved per size; an official effect is resolved per size only if it is ≥ about 0.13 log2.
- Pooled over 1,440 numbers (se about 0.02), effects of about 0.05 log2 are resolved. An official 84-bit effect of −0.089 needs about 480 numbers: about two sizes' worth, so it is judged pooled.

**Replacement rule (decided now).** Recommend replacing the reference only if all of these hold:
- at every size, no pricing's paired interval lies above 0 (the new qs is never clearly worse);
- no misses;
- pooled, all three pricings are below 1 with intervals excluding 0.

Otherwise, qs + lc 1.4 stays the reference, and the new genes are a mixed-population qs.

**Predictions.**
- (2a) At 84 bits, ruint and Montgomery ratios are 0.65–0.80. The official ratio is 0.85–1.0, and its per-size interval includes 0.
- (2b) The gain shrinks at smaller sizes. The robust ratio is below 1 at 72–84 bits and at least 0.95 at 54 bits.
- (2c) At most 1 miss in 1,440 per genome.
- (2d) The replacement rule fails, because at 54 or 60 bits at least one pricing's interval lies above 0, so qs + lc 1.4 stays the reference.

## 2026-10-24 — Run 8 wrap-up addendum (user): plateau, scope, search policy, generalization tests

- **The qs-gene axis is a PLATEAU.**
  - Random search ties TPE on the qs genes alone (mixed-qs best-of-8 sealed 0.472 vs 0.472; per-seed, TPE is better by about 3.5% on 7/8 seeds, sign p 0.07).
  - Winning genes spread widely: kc 2–11 and mc 0.43–0.93 across the TPE and evolution winners of both arms.
  - The retuned genes are reported as a region, not point values. Further qs-gene-only search is expected to add little.
- **Scope of "partition study under-explored by 1.40x":** the partition study held the qs genes fixed at qs + lc 1.4 by design. The 1.40x is along an axis it did not search. Its conclusions are unaffected: A vs B, the robust-fitness results, and coverage, not selection, as the mechanism.
- **Search policy:** recorded in PLAN ("Search policy after Run 8"):
  - TPE is the default for fixed-shape gene tuning.
  - Island evolution is kept only pending the variable-length structural test, whose prediction is written there.
  - NSGA-II (Optuna) for multi-objective search; pyribs for MAP-Elites.
  - 24 numbers per band in future fixed tuning sets; the sealed ACCEPT gate stays; reports name the seeds whose tuning sets misled methods; no hand-picked "hard" numbers.

### Generalization tests (predictions before computing; not yet run)

**Design.**
- new qs genes (the region's representative: kc 4, bc 0.8994, mc 0.7341, tc 1.1045, lc 1.6612) against qs + lc 1.4's genes, both with budgets and order held at A (td 0, rho 5793, pm1 0, ECM 32768).
- Paired on fresh sealed numbers; fitness (c) against qs + lc 1.4 alone; all three pricings; per-seed paired bootstrap within bands; the ACCEPT gate.
- (a) Mixed populations at 72 and 96 bits: the smaller factor in bands from 16 bits up to the balanced band (72: 16–36; 96: 16–48), 80 per band, fresh seeds. The exact bands and seeds are fixed in the script's header before it runs.
- (b) Balanced 84-bit numbers.

**Predictions.**
- (a), mine: the new genes beat qs + lc 1.4's genes at both sizes; robust ratio new/old 0.70–0.90 at 72 bits and 0.60–0.85 at 96 bits (Run 8, 84 bits: 0.472/0.675 = 0.70).
- (b), the user's, verbatim: "the wider mc (0.43-0.93) loses on balanced (population-specific genes)."
  - **Evidence already on record, against it:** on the Run 8 sealed band 42 (80 balanced 84-bit numbers, A's budgets), the mixed-qs winners' ratios to qs + lc 1.4 alone are 0.91–0.94 official, 0.70–0.76 ruint and 0.73–0.80 Montgomery. That is better, not worse.
  - Those 80 numbers were scored in Run 8's report, so (b) on fresh numbers is the test. The prediction is scored as written.

### (1) Results: partition map with the new qs (`evolve/partition_newqs.py`, `partition_newqs.out`/`.json`; 67 s)

**Checks.**
- **Parity:** lampcore `--types` matches the map's Python per-type counts for qs + lc 1.4 on 560/560 numbers.
- **The new qs alone:** 0 misses on the 560 tuning numbers.

**Fitness (c) against qs + lc 1.4 alone, map (560 tuning numbers).**

| plan | robust | official | ruint | Montgomery |
|---|---|---|---|---|
| A with qs + lc 1.4 (partition study) | 0.641 | 0.450 | 0.641 | 0.527 |
| new qs alone | 0.963 | 0.963 | 0.405 | 0.630 |
| A's budgets + new qs | 0.438 | 0.438 | 0.408 | 0.380 |
| re-optimized + new qs (td 0, rho 11585, pm1 0, ECM 32768; best of all 24 orders and the fixed order) | 0.431 | 0.431 | 0.424 | 0.385 |

- **Re-optimized against A's budgets, both with the new qs:** log2 −0.0235 [−0.0510, +0.0334]. Unresolved: the point is a 1.6% gain and the interval includes 0. Only rho moved, from 5793 to 11585; ECM stayed at 32768.
- **Card order matters**, in the same pattern as with qs + lc 1.4. The 12 orders that put ECM before rho are +0.066 [+0.035, +0.100] worse. The other 12 share the optimum.
- **Mechanism (found while checking the numbers).**
  - The new qs alone is uniformly cheaper than qs + lc 1.4 in every band: about 0.41 ruint, 0.61–0.64 Montgomery and 0.94–0.98 official.
  - The gain is almost entirely in what the calibrated pricings charge. The official count hardly moves, so after the change official is the binding pricing of the robust max.
  - Against the new qs alone, the re-optimized allocation is 0.45 official, 0.61 Montgomery and 1.05 ruint. Under ruint, the pre-stages no longer pay once qs is this cheap; under official and Montgomery they still do. Per (e), "pre-stages pay over the new qs alone" is undecided.
  - So the budgets are held where they are by the official count. ECM stays at 32768 because official still prices ECM's multiplies at 1 op.
- **Per-band ratios** of the re-optimized plan to qs + lc 1.4 alone:
  - official: 16: 0.001, 20: 0.005, 24: 0.106, 28: 0.419, 32: 0.743, 36: 0.871, 42: 0.866;
  - ruint: 0.008, 0.027, 0.210, 0.537, 0.703, 0.769, 0.760;
  - Montgomery: 0.005, 0.016, 0.143, 0.427, 0.647, 0.734, 0.733.

**Predictions scored as written:** 4 scored; 2 held, 1 missed, 1 unresolved.
- (1a) **Missed.** ECM stayed at 32768, against the prediction of ≤ 2^14 or 0. rho 11585 (in [2^11, 2^14]), td 0 and pm1 off all held, but the clause is compound. The reasoning behind it, that a cheaper qs makes ECM worth less, holds under ruint only. The binding official count did not change.
- (1b) **Unresolved.** The point estimate (−0.0235 log2, 1.6%) is in the predicted 1–5% range, but the interval includes 0.
- (1c) **Held.** 0.438, in 0.43–0.50.
- (1d) **Held.** rho before ECM in every order at the optimum; 12 orders' intervals lie above 0.

**Consequence for (2a), recorded before (2) runs.** (2a)'s ruint and Montgomery ranges (0.65–0.80) were taken from Run 8's band-42 cells, which include A's pre-stage spending. The new qs alone is about 0.41 ruint and 0.63 Montgomery on this map's balanced band. (2a) stays as written and is expected to miss on ruint.

### (2) Results: the new qs on balanced numbers (`evolve/newqs_balanced.py`, `newqs_balanced.out`/`.json`; 123 s)

Fresh balanced numbers, 240 per size (54–84 bits, seeds 8700000 + bits), each genome alone, cap 2^28. **No misses** for any genome (0/1,440 each). Each cell is the mean-cost ratio with its paired 95% interval in log2.

**new qs / qs + lc 1.4**

| bits | official | ruint | Montgomery | robust (c) | (e) call |
|---|---|---|---|---|---|
| 54 | 1.276 [+0.298, +0.412] | 0.944 [−0.102, −0.064] | 0.925 [−0.137, −0.082] | 1.276 | undecided |
| 60 | 1.249 [+0.285, +0.356] | 0.952 [−0.082, −0.058] | 0.919 [−0.143, −0.102] | 1.249 | undecided |
| 66 | 1.206 [+0.235, +0.306] | 0.931 [−0.119, −0.088] | 0.895 [−0.182, −0.137] | 1.206 | undecided |
| 72 | 1.129 [+0.137, +0.213] | 0.800 [−0.448, −0.208] | 0.824 [−0.334, −0.230] | 1.129 | undecided |
| 78 | 1.018 [−0.010, +0.063] | 0.517 [−1.084, −0.811] | 0.691 [−0.593, −0.474] | 1.018 | undecided |
| 84 | 0.953 [−0.099, −0.040] | 0.408 [−1.374, −1.204] | 0.627 [−0.713, −0.635] | 0.953 | new qs |
| pooled (mean of per-size log2) | 1.132 [+0.163, +0.195] | 0.722 [−0.503, −0.437] | 0.805 [−0.330, −0.298] | | |

- **The new qs's gain over qs + lc 1.4 is size-dependent and pricing-dependent.**
  - Under official it is worse by 13–28% at 54–72 bits, about even at 78 and 5% better at 84.
  - Under both calibrated pricings it is better at every size, and the gain grows with size: ruint 0.94 → 0.41, Montgomery 0.93 → 0.63.
  - The genes were tuned at 84 bits and carry fewer, cheaper-priced operations; below 78 bits the official count prefers qs + lc 1.4's genes.

**new qs / N51-0917's qs** (information; N51-0917 was the calibrated leader at 60–84 bits).
- The new qs is better under all three pricings at every size: an (e) call of "new qs" in 6/6 sizes. Robust 0.93–0.97; official 0.73–0.77, ruint 0.93–0.97, Montgomery 0.89–0.94.
- Pooled: official 0.750 [−0.433, −0.394], ruint 0.960 [−0.069, −0.048], Montgomery 0.925 [−0.125, −0.100].
- N51-0917's qs against qs + lc 1.4: worse under official at every size (1.30–1.69); better under the calibrated pricings from 60–66 bits up.

**Replacement rule: fails. qs + lc 1.4 stays the reference.**
- Never clearly worse: no (official, 54–72 bits).
- No misses: yes.
- Pooled all three below 1: no (official 1.132).
- **The new genes are a mixed-population and 84-bit qs**, and on balanced numbers they replace N51-0917's qs as the best calibrated-pricing qs at 54–84 bits. Whether the reference itself should change is the user's decision; the pre-registered rule says no.

**Predictions scored as written:** 4 scored; 2 held, 2 missed.
- (2a) **Missed.** At 84 bits: ruint 0.408 and Montgomery 0.627, both below the predicted 0.65–0.80 (the band-42 anchoring recorded under (1)). Official 0.953 is in 0.85–1.0, but its interval excludes 0, against the prediction.
- (2b) **Missed.** The gain does shrink toward small sizes, and the robust ratio at 54 is 1.276 (≥ 0.95). But the robust ratio is below 1 only at 84, not at 72–84 (72: 1.129, 78: 1.018).
- (2c) **Held.** 0 misses.
- (2d) **Held.** The rule fails at 54–72 bits on official.

**For the generalization test (b)** (the user's prediction: the wider mc loses on balanced 84-bit numbers; budgets held at A; not yet run): with qs alone on fresh balanced 84-bit numbers, the new genes win under all three pricings (0.953 / 0.408 / 0.627). Test (b) adds A's pre-stages, which cost both genomes the same ops on balanced numbers, so the qs-alone result points against the prediction. It is scored only when (b) runs.

## 2026-10-24 — Decisions after (1)/(2) (user), and a post hoc check of tpe-tuned

- **Reference: KEEP qs + lc 1.4** (the pre-registered replacement rule failed).
  - **Scope:** the reference (qs + lc 1.4) is kept fixed for comparability with every earlier result, not because the new genes are worse; they are the calibrated-pricing leader.
  - The new qs genes (the region's representative: kc 4, bc 0.90, mc 0.73, tc 1.10, lc 1.66) are the calibrated-pricing leader on balanced 54–84 bits, replacing N51-0917's qs in that role.
  - They are best under all three pricings only at 84 bits.
- **MISLEADING rule:** the operational reading in PLAN (OVERFIT = gap above A's gap) is confirmed.
- **Search default: revisited.** The per-seed comparison makes default TPE vs evolution a TIE over seeds, with TPE's stalls as a risk.

### Post hoc check (labelled post hoc: chosen after seeing the per-seed result; existing genomes, mixed arm, sealed)

**Design.**
- tpe-tuned vs evolution, and tpe-tuned vs default TPE, with the same per-seed paired comparison as before (`run8_perseed.py`, pairs given on the command line).
- **Stalled seed:** a seed whose run never reaches T2 (A's point estimate on its own tuning set). From the run: TPE stalled on seeds 72 and 75; tpe-tuned reached T2 on 8/8 (seed 72 late, at 875); evolution reached it on 8/8.
- **Wall time per run** (mixed arm, median [2nd–7th of 8]): evolution 705 s [673–741], TPE 661 s [626–744], tpe-tuned 773 s [725–800], random 2,238 s.
- **PLAN rule, decided by the user before computing:**
  - if tpe-tuned has no stalled seeds and ties or beats evolution per seed, the default is tpe-tuned;
  - otherwise there is no default winner; the tie is recorded and the method is picked by cost.
- **Power:** as in the per-seed entry. The sign test detects only 8/8 or 0/8. The per-seed paired half-width is about 0.02–0.1 log2.

**Expectation (post hoc, not a pre-registered prediction):**
- tpe-tuned vs evolution: tie over seeds and numbers.
- tpe-tuned vs TPE: tpe-tuned better on seeds 72 and 75 by more than 0.5 log2; mixed signs elsewhere.

**Results (post hoc; `evolve/run8_mixed_perseed_posthoc.out`/`.json`).** d = log2(fit X / fit Y), same seed, sealed; below 0 means X is better.

| pair | X better (sign p) | intervals below / above 0 | mean d (median) | (i) numbers resampled | (ii) seeds + numbers |
|---|---|---|---|---|---|
| tpe-tuned vs evolution | 5/8 (0.727) | 3 / 3 | −0.011 (−0.010) | [−0.031, +0.006] | [−0.063, +0.033] |
| tpe-tuned vs TPE | 5/8 (0.727) | 3 / 3 | −0.101 (−0.060) | [−0.120, −0.078] | [−0.402, +0.197] |

- **tpe-tuned vs evolution:** a tie under both bootstraps. No per-seed difference exceeds 0.12 log2. Its largest loss is seed 78 (+0.066); its largest win is seed 76 (−0.112).
- **tpe-tuned vs TPE:** tpe-tuned removes TPE's two stalls (seeds 72 and 75: −0.70 each). It loses heavily on seed 73 (+0.714), where its run followed seed 73's misleading tuning set to an ECM budget of 711k and failed the sealed gate.
- **Expectation (post hoc) vs result:** tie with evolution, as expected; better than TPE on 72 and 75 by more than 0.5 log2, as expected.
- **Rule applied:** tpe-tuned has no stalled seeds (T2 on 8/8) and ties evolution per seed, so **the default for fixed-shape gene tuning is tpe-tuned** (n_startup_trials = 10% of the budget, multivariate). It costs about 10% more wall time per run than evolution (773 s vs 705 s median), well below random search (2,238 s).

## 2026-10-24 — Generalization tests (a) and (b): results (`evolve/newqs_general.py`, `newqs_general.out`/`.json`; 144 s)

**Design.** The populations and seeds were fixed in the script header before the run:
- (a) mixed 72-bit (bands 16–32 unbalanced, 36 balanced) and mixed 96-bit (16–42 unbalanced, 48 balanced), 80 per band;
- (b) balanced 84-bit, 240 numbers;
- seeds 8800000 + 100·pb + bits, all through `oracle.check`;
- budgets and order at A; new qs genes vs qs + lc 1.4's genes; fitness (c) against qs + lc 1.4 alone; lampcore `--types`, cap 2^28.

**No misses** in any population.

| population | new genes: robust (off / ruint / Mont) | old genes: robust (off / ruint / Mont) | new / old robust, log2 [paired 95%] | by pricing, log2: official / ruint / Montgomery | (e) | ACCEPT gate (new / old) |
|---|---|---|---|---|---|---|
| (a) mixed 72 | 1.100 (0.410 / 1.100 / 0.570) | 1.152 (0.379 / 1.152 / 0.613) | 0.955, −0.066 [−0.111, −0.031] | +0.111 [+0.076, +0.144] / −0.066 [−0.111, −0.031] / −0.107 [−0.140, −0.080] | undecided | FAIL (2.161) / FAIL (2.279), band 36, ruint |
| (a) mixed 96 | 0.688 (0.638 / 0.688 / 0.588) | 0.744 (0.640 / 0.744 / 0.675) | 0.924, −0.114 [−0.122, −0.106] | −0.003 [−0.022, +0.015] / −0.114 [−0.122, −0.106] / −0.200 [−0.215, −0.185] | undecided (official tie) | PASS (1.081) / PASS (1.169) |
| (b) balanced 84 | 0.902 (0.902 / 0.699 / 0.726) | 1.219 (0.935 / 1.219 / 1.051) | 0.740, −0.435 [−0.478, −0.393] | −0.052 [−0.086, −0.017] / −0.802 [−0.863, −0.739] / −0.533 [−0.568, −0.499] | new genes | PASS (0.902) / PASS (1.219) |

- **The new genes generalize in the same pattern as (2)'s qs-alone test.** They are better under the calibrated pricings at every size. Under official they are worse at 72 bits (+8%), tied at 96 and better at 84 balanced (−3.5%). The robust ratio is below 1 everywhere because ruint binds for the old genes.
- **A's budgets do not transfer to 72 bits; this is independent of the qs genes.**
  - Both genomes are worse than qs + lc 1.4 alone under ruint (robust 1.10 and 1.15), and both fail the ACCEPT gate (band 36: 2.16x and 2.28x under ruint; band 32: 1.91x and 2.03x).
  - At 72 bits qs costs about 2.5–3x fewer official ops than at 84 bits (about 190–230k vs about 560k on balanced numbers), so A's fixed absolute budgets (rho 5793, ECM 32768 ops) overspend on every number they don't finish.
  - At 96 bits the same budgets are relatively small: they pass, with band ratios near 1.
  - Op budgets fixed in absolute ops are size-specific. A size-relative budget (a share of the expected qs cost at that size) is a candidate structural move; it is not added to MOVES until it has a cost model.
- **At 96 bits, A's pre-stages pay only below the balanced bands.** The 42 and 48 bands are 1.02–1.08 under official and ruint with either genes.

**Predictions scored as written:** 2 scored, 0 held, 2 missed.
- (a), mine, "the new genes beat qs + lc 1.4's genes at both sizes; robust ratio new/old 0.70–0.90 at 72 bits and 0.60–0.85 at 96 bits": **missed.** The direction held at both sizes (intervals below 0), but the magnitudes are outside both ranges: 0.955 at 72 and 0.924 at 96. The ranges were extrapolated from Run 8's 84-bit 0.70, which is the size the genes were tuned at.
- (b), the user's, "the wider mc (0.43-0.93) loses on balanced (population-specific genes)": **missed.** The new genes win on balanced 84-bit numbers under all three pricings (robust 0.740 [−0.478, −0.393]), as the qs-alone evidence recorded beforehand indicated.

## 2026-10-24 — Size-relative op budgets: cost model and predictions (written before any code)

**Why.** At 72 bits A's absolute budgets (rho 5793, ECM 32768 ops) fail the ACCEPT gate with either qs genes (generalization test (a)). qs is about 2.5–3x cheaper there, so the same absolute pre-stage spend is a larger share of the qs cost it is meant to save.

**The move.** Each pre-stage budget becomes a share of the expected qs cost at N's size:
- ob_s(N) = snap(s_s · Q(bits(N))), for s in {rho, ECM}; td and pm1 stay at A's 0.
- Q(bits) = fitted mean official ops of qs + lc 1.4 alone at that bit length (the curve below). Official ops, because ob counts meter ops.
- snap(x) = the value of the map's 1/8-octave grid 2^(k/8) (`partition.FINE`) nearest to x in log2. Budgets are quantized so that the map records their spending exactly; the quantization error is at most 2^(1/16), about 4.4%.
- Genes: s_rho and s_ECM (shares, dimensionless) instead of absolute ops.

**Meter.** No change to charging, op counts or pricing.
- bits(N) is N's bit length: free, as reading N is free today.
- Q is a fixed table indexed by bit length, computed offline from tuning numbers: a genome constant, like any gene value. Looking it up is free.
- Each stage still runs with an absolute ob and charges exactly as today; the move changes only which ob a stage gets. lampcore and Python are untouched; the test passes ob per size.

**Identity.** At 84 bits, shares s_s = A_s / Q(84) give ob_s = snap(A_s) = A_s (5793 and 32768 are grid points), so the genome is A op for op. Checked by running both on fresh 84-bit numbers and asserting identical per-number counts.

**The curve Q(bits).** Fresh balanced tuning numbers, semiprimes_pq(bits, 60, 9100000 + bits) for bits 60, 64, ..., 100, through `oracle.check`; qs + lc 1.4 alone, lampcore, cap 2^28. Fit log2(mean official ops) = a + b·bits + c·bits² by least squares. Only the curve's shape matters: ob_s(bits) = snap(A_s · Q(bits)/Q(84)).

**Test.**
1. Tuning: on the existing 84-bit partition map (tuning seeds 4000000 + 100 pb + 84), the best (s_rho, s_ECM) with td 0, pm1 0 and the fixed order, by the partition study's grid plus 1/8-octave coordinate refinement under fitness (c). Expected: A's budgets (A was the unrestricted optimum on this map with td 0 and pm1 0), i.e. s = A / Q(84).
2. Maps at 72 and 96 bits on fresh numbers (seeds 9000000 + 100 pb + bits; 72: bands 16, 20, 24, 28, 32 unbalanced and 36 balanced; 96: 16, 20, 24, 28, 32, 36, 42 unbalanced and 48 balanced; 80 per band; `oracle.check`). Pre-stages alone in Python with spending records (`partition.run_alone`, cap 2^21); qs + lc 1.4 alone through lampcore `--types` (parity: on 4 numbers per band, Python's per-type counts must equal lampcore's; a mismatch is a blocker).
3. Verdict, on those fresh numbers (seen by nothing before this test): the share genome (ob = snap(s · Q(bits))) vs A's absolute budgets, each run directly in lampcore `--types` (the map's composed official cost must equal the direct run's on every number: a cross-check). Fitness (c) against qs + lc 1.4 alone; paired bootstrap resampling numbers within bands (10,000, random.Random(2026)); per pricing; per band; ACCEPT gate (no band > 1.5x under any pricing, no misses).
4. Information only: the hindsight best absolute budgets on each size's own map, and where the share budgets land against them.

**Predictions** (scored as written):
- (P1, the user's) The share genome passes the ACCEPT gate at 72 bits where A's absolute budgets fail, and matches A within noise at 84 and 96.
  - At 84 "within noise" is guaranteed by the identity; the content of P1 is the 72-bit gate and the 96-bit tie.
- (P2, mine) Robust ratio share / A at 72 bits: 0.80–0.92 (interval below 0). Reasoning: at 72 the balanced band's ruint overspend is about 1.16x qs under A; scaling budgets down by Q(84)/Q(72) ≈ 2.7 leaves about 0.43, so band 36 lands near 1.4–1.5 under ruint (a borderline gate pass), and the overall ruint score drops from about 1.15 to about 0.95–1.0.
- (P3, mine) At 96 bits budgets grow by about 3–4x (ECM about 100–130k). Share / A robust ratio 0.92–1.02 with the interval including 0 (a tie, P1's reading); the share genome's worst band stays below 1.5.

## 2026-10-24 — Budget/order freedom beyond A: design and predictions (before computing; existing genomes)

**Question.** Does searching budgets and order (mixed arm) beat holding them at A and tuning only the qs genes (mixed-qs arm), method for method and seed for seed?

**Design.**
- Both arms used the same tuning set per seed and the same sealed set (`run8.sealed_set`: the mixed population, seeds 8500000 + 100 pb + 84, 80 per band), so a seed's two runs are paired.
- Pairs: mixed X vs mixed-qs X, same seed, for X in {evolution, TPE, random} (the methods run in both arms). Extra pair: mixed tpe-tuned vs mixed-qs tpe-warm (each arm's TPE variant with the better start).
- d_s = log2(fit mixed / fit mixed-qs) on the sealed numbers; below 0 means the freedom pays. Same machinery as `run8_perseed.py`: per-seed interval (numbers resampled within bands), sign test, mean and median d with (i) numbers resampled, seeds fixed, and (ii) seeds and numbers resampled; sealed misses count in the sign test and are left out of the means.
- Seen before writing this: the best-of-8 sealed numbers (mixed TPE 0.455, evolution 0.484, random 0.561; mixed-qs about 0.47 for every method), TPE's stalls on mixed seeds 72 and 75, the mixed-qs evolution miss on seed 74. Not seen: any per-seed sealed value for mixed-qs.

**Predictions** (scored as written):
- (F1) evolution: tie. Mean d in [−0.05, +0.05], (ii) includes 0.
- (F2) TPE: mean d above 0, driven by mixed seeds 72 and 75 (d > +0.5 on both); (ii) includes 0.
- (F3) random: mixed worse. Mean d in [+0.10, +0.25], (ii) above 0 (four more dimensions for a method with no model).
- (F4) Overall: the freedom does not pay at 84 bits with 1,360 evaluations: no pair has (ii) below 0.

### Budget/order freedom beyond A: results (`evolve/run8_freedom.py`, `run8_freedom.out`/`.json`; 168 s)

d = log2(fit mixed X / fit mixed-qs Y), same seed, sealed (560 numbers); below 0 means the freedom pays.

| pair | mixed better (sign p) | intervals below / above 0 | mean d (median) | (i) numbers resampled | (ii) seeds + numbers |
|---|---|---|---|---|---|
| evolution vs evolution | 1/8 (0.070) | 1 / 6 | +0.203 (+0.100), 7 seeds | [+0.141, +0.270] | [+0.052, +0.444] |
| TPE vs TPE | 1/8 (0.070) | 0 / 5 | +0.268 (+0.110) | [+0.212, +0.322] | [+0.047, +0.539] |
| random vs random | 0/8 (0.008) | 0 / 8 | +0.434 (+0.385) | [+0.373, +0.501] | [+0.229, +0.746] |
| tpe-tuned vs tpe-warm | 1/8 (0.070) | 0 / 6 | +0.186 (+0.122) | [+0.135, +0.240] | [+0.052, +0.393] |

- **The freedom costs, for every method.** Every pair's interval over seeds and numbers lies above 0: searching budgets and order as well as the qs genes gave worse sealed genomes than holding budgets and order at A and tuning only the qs genes.
- **The typical loss is about 7–8% (median d +0.10 to +0.12),** plus large losses where a mixed run followed a misleading tuning set: seed 73 (evolution +0.82, tpe-tuned +0.80, random +1.34) and TPE's two stalls (seeds 72 and 75, +0.85 and +0.88).
- **The mixed-qs arm's sealed fitness is tight:** 0.458–0.511 over all 32 runs (one miss: evolution seed 74, which is the only "mixed better" entry in the evolution row).
- **Confound, stated:** A's budgets were chosen on the partition map (560 tuning numbers, 80 per band). Each Run 8 run tuned on its own 12-per-band set (84 numbers). Holding budgets at A therefore imports a budget choice made on about 7x more data. The result says "with Run 8's tuning sets and 1,360 evaluations, searching budgets loses to A's map-chosen budgets", not that A's budgets are optimal on every set.

**Predictions scored as written:** 4 scored, 1 held, 3 missed.
- (F1) evolution tie, mean d in [−0.05, +0.05], (ii) includes 0: **missed** (+0.203, (ii) above 0).
- (F2) TPE: mean above 0, d > +0.5 on seeds 72 and 75, (ii) includes 0: **missed.** The first two clauses held (+0.268; +0.850 and +0.876); the third failed ((ii) [+0.047, +0.539]).
- (F3) random: mean d in [+0.10, +0.25], (ii) above 0: **missed.** (ii) is above 0, but the mean (+0.434) is outside the range.
- (F4) no pair has (ii) below 0: **held** (every pair's (ii) is above 0).

### Size-relative budgets: addendum (user, Oct 24; written before the eval ran; the 72/96 maps were built, nothing evaluated)

**Three budget rules, all evaluated.** ob = snap(A's budget × ratio(bits)); identical to A at 84 bits by construction.

| rule | ratio 72/84 | ratio 96/84 | ob at 72: rho / ECM | ob at 96: rho / ECM |
|---|---|---|---|---|
| PRIMARY, measured share (dedicated curve) | 0.2906 | 3.4420 | 1,722 / 9,742 | 19,484 / 110,218 |
| SENSITIVITY, measured share (earlier-run curve) | 0.2689 | 4.5152 | 1,579 / 8,933 | 25,268 / 142,935 |
| SECONDARY, theory L(N) = exp(sqrt(ln N ln ln N)) | 0.2432 | 3.7814 | 1,448 / 8,192 | 21,247 / 120,194 |

- **Curve source, and a deviation from the addendum as written.** The addendum asks for a curve fitted on earlier runs' data and frozen.
  - Earlier data: `calibrate_counts.json` (the calibration run): qs + lc 1.4 alone on balanced 54, 60, ..., 84 bits, 80 numbers each. Fit (the form fixed above): log2 mean ops = 11.7096 + 0.006365·bits + 0.0009715·bits². It stops at 84, so 96 is a 12-bit extrapolation; the quadratic fitted over 54–84 gives 4.52x there. (A linear fit to the same data gives 3.22x.)
  - Dedicated curve: fresh balanced tuning numbers (seeds 9100000 + bits, 60–100 bits, 60 each; disjoint from every evaluation set). Fitted and committed (`2b22d08`) before the 72/96 maps existed: log2 mean ops = 6.5903 + 0.14846·bits + 0.0000008·bits².
  - I kept the dedicated curve as PRIMARY because it covers 96 without extrapolation and was frozen before any evaluation number existed, which is the addendum's purpose. The earlier-run curve is evaluated beside it as SENSITIVITY, so the literal rule is not lost. The user may re-designate.
- **L ratio:** computed at the bit length (ln N = bits · ln 2), as both measured rules are.
- **Measured qs-cost ratios** (reported beside the L ratio; information, not inputs): dedicated curve 0.291 (72/84) and 3.44 (96/84); calibration run raw means 72/84 = 0.270; the evaluation maps themselves (fresh mixed numbers, qs alone) 0.271 and 3.35. L asymptotics give 0.243 and 3.78: the measured cost grows more slowly than L(N) going from 72 to 84 bits and from 84 to 96 bits (log2 slope 0.148 per bit vs L's 0.170 at 72–84 and 0.160 at 84–96).

**Predictions** (scored as written):
- (P4, the user's) "The measured-share rule passes the ACCEPT gate (< 1.5x) at 72 bits and matches A within noise at 84 and 96." (The same as P1, applied to the PRIMARY rule.)
- (P5, the user's) "The theory rule shrinks budgets less than the measured-share rule at 72 (0.24 vs the measured ratio)."
  - **Already decided by arithmetic, before the run: missed.** 0.243 is below every measured ratio (0.27–0.29), so the theory rule shrinks the 72-bit budgets more than the measured rule (rho 1,448 vs 1,722; ECM 8,192 vs 9,742), not less.
- (P6, mine, from that gap) The theory rule passes the gate at 72 bits: it spends about 16% less than the PRIMARY rule on numbers it does not finish, so its worst band is at or below the PRIMARY rule's. Theory / PRIMARY robust ratio at 72 bits within ±0.03 log2 (interval includes 0). At 96 bits the theory rule (3.78x) lies between PRIMARY (3.44x) and SENSITIVITY (4.52x); all three tie with A there (intervals include 0).
- (P7, mine) SENSITIVITY at 96 bits (ECM 142,935) is no better than PRIMARY: SENSITIVITY / PRIMARY log2 ≥ −0.02.

### Size-relative budgets: results (`evolve/size_budgets.py eval`, `size_budgets.out`/`.json`; maps `size_map.out`/`.json`; curve `size_curve.out`/`.json`)

**Checks.**
- Tuning on the 84-bit map returned A's budgets (rho 5,793, ECM 32,768; fitness 0.6408).
- Identity: at 84 bits all three rules give A's budgets. Per-number counts are identical to A's on 560/560 fresh numbers.
- Map parity: Python qs per-type counts matched lampcore's on 24/24 (72 bits) and 32/32 (96 bits). The map's composed official cost equals the direct lampcore run on every number for every genome (480/480, 640/640).
- No misses anywhere.

**72 bits** (480 numbers; fitness (c) against qs + lc 1.4 alone):

| genome (rho / ECM) | robust | official | ruint | Montgomery | gate (worst band) |
|---|---|---|---|---|---|
| A (5,793 / 32,768) | 1.127 | 0.376 | 1.127 | 0.606 | FAIL (2.171, band 36, ruint) |
| PRIMARY (1,722 / 9,742) | 1.067 | 0.735 | 1.067 | 0.837 | FAIL (1.515, band 36, ruint) |
| SENSITIVITY (1,579 / 8,933) | 1.038 | 0.731 | 1.038 | 0.826 | PASS (1.472, band 36, ruint) |
| theory (1,448 / 8,192) | 1.113 | 0.817 | 1.113 | 0.908 | PASS (1.444, band 36, ruint) |
| hindsight, own map (3,158 / 0) | 0.817 (map) | | | | information only |

Paired, log2 [95%]: PRIMARY / A −0.079 [−0.163, +0.010] robust; official +0.968 [+0.835, +1.114], ruint −0.079, Montgomery +0.466 [+0.367, +0.573]. Theory / A −0.019 [−0.110, +0.079]. SENSITIVITY / A −0.119 [−0.204, −0.029]. Theory / PRIMARY +0.061 [+0.015, +0.117]. SENSITIVITY / PRIMARY −0.040 [−0.041, −0.038].

**96 bits** (640 numbers):

| genome (rho / ECM) | robust | official | ruint | Montgomery | gate (worst band) |
|---|---|---|---|---|---|
| A (5,793 / 32,768) | 0.741 | 0.634 | 0.741 | 0.670 | PASS (1.155, band 42, ruint) |
| PRIMARY (19,484 / 110,218) | 0.687 | 0.422 | 0.687 | 0.513 | PASS (1.452, band 48, ruint) |
| SENSITIVITY (25,268 / 142,935) | 0.680 | 0.367 | 0.680 | 0.475 | FAIL (1.537, band 48, ruint) |
| theory (21,247 / 120,194) | 0.654 | 0.373 | 0.654 | 0.470 | PASS (1.435, band 48, ruint) |
| hindsight, own map (12,634 / 60,097) | 0.627 (map) | | | | information only |

Paired, log2 [95%]: PRIMARY / A −0.108 [−0.177, −0.039] (all three pricings below 0); theory / A −0.179 [−0.253, −0.107]; SENSITIVITY / A −0.122 [−0.196, −0.049]; theory / PRIMARY −0.072 [−0.111, −0.036] (all three below 0); SENSITIVITY / PRIMARY −0.015 [−0.060, +0.027].

**Reading.**
- **At 96 bits size-relative budgets pay** against A under all three pricings ((e) call: each rule beats A). Theory is the best of the three: 0.883x A, and better than PRIMARY under all three pricings. The hindsight optimum on the 96-bit map (rho 12,634, ECM 60,097) scales A by about 2x, less than any rule (3.4–4.5x). The rules overshoot it, and their worst band (48, balanced) rises to 1.44–1.54 under ruint.
- **At 72 bits no proportional rule fixes A.** Every rule's robust ratio is above 1, i.e. worse than qs + lc 1.4 alone. Shrinking budgets lowers ruint waste on the balanced band (2.17 → 1.44–1.52), but it costs heavily under official (0.38 → 0.73–0.82): the shrunk rho and ECM stop finishing the 20–24-bit factors (band 20 official 0.017 under A, 0.51–0.68 under the rules). (e) call PRIMARY vs A at 72: undecided (official favours A, ruint favours the rule within noise, Montgomery favours A).
- **Mechanism, read from the per-band numbers:** a pre-stage's cost to find a factor depends on the factor's size, not on N. Scaling the budget with qs cost at N's size helps when qs gets dearer (96: more of the 24–36-bit bands are covered) but hurts when qs gets cheaper (72: the small-factor bands are lost). The hindsight 72-bit optimum is a different shape: ECM off, rho 3,158. At 72 bits under the robust objective (ruint binding), ECM's spending no longer pays. One scale factor per size cannot express a stage switching off.
- **The gate at 72 is borderline for every rule** (1.44–1.52 under ruint, band 36). PRIMARY fails by 0.015 and the other two pass by 0.03–0.06; no per-band interval was pre-registered, so the gate is scored as the point value.
- **L asymptotics vs measured:** measured qs cost grows by 0.27–0.29x (72/84) and 3.35–3.44x (96/84); L(N) gives 0.243x and 3.78x. At 96 bits the theory ratio did better than the measured one, but neither is near the hindsight scaling (about 2x). The best budget scaling is not the qs-cost scaling.

**Predictions scored as written:** 7 scored, 1 held, 6 missed.
- (P1, the user's) share genome passes the gate at 72 and matches A within noise at 84 and 96: **missed.** PRIMARY fails at 72 (1.515), and at 96 it beats A ([−0.177, −0.039]) instead of tying. (The 84-bit clause held by identity.)
- (P2, mine) PRIMARY / A at 72 in 0.80–0.92 with the interval below 0: **missed** (0.946, [−0.163, +0.010]).
- (P3, mine) at 96, PRIMARY / A in 0.92–1.02 with the interval including 0, worst band below 1.5: **missed.** 0.928 is in range and the worst band is 1.452, but the interval lies below 0.
- (P4, the user's) = P1 for the PRIMARY rule: **missed**, as P1.
- (P5, the user's) the theory rule shrinks less than the measured rule at 72: **missed** (decided by arithmetic before the run: 0.243 vs 0.29).
- (P6, mine) theory passes the gate at 72; theory / PRIMARY at 72 within ±0.03 with the interval including 0; at 96 all three tie with A: **missed.** The gate clause held (1.444); theory / PRIMARY at 72 is +0.061 [+0.015, +0.117]; at 96 all three beat A.
- (P7, mine) SENSITIVITY / PRIMARY at 96 ≥ −0.02: **held** (−0.015).

## 2026-10-24 — Decisions after the size-relative budgets test (user)

- **PRIMARY curve stays the dedicated one** (fresh 60–100-bit balanced tuning seeds 9100000 + bits, frozen in `2b22d08` before any evaluation number existed). The earlier-run curve (calibration run, 54–84 bits) is SENSITIVITY.
- **A wrong estimate, recorded:** the user estimated "qs ~8x cheaper at 72 bits (ratio 0.125)". The measured ratio 72/84 is 0.27–0.29. P5 was settled by arithmetic before the run, as recorded.
- **Design principle from the freedom result:** budgets are chosen from maps (exact per-number composition, many numbers); search tunes only the qs genes. Confound: A's budgets came from a 560-number map, while each Run 8 run tuned on 84 numbers, so the freedom comparison also compares tuning-set sizes.
- **Gate verdicts at 72 bits were point values:** no per-band interval was pre-registered. From now on gate rules carry per-band intervals (defined in the next entry and used from then on).

## 2026-10-24 — Per-stage budgets by size from a stopping rule: cost model and predictions (before code)

**Rule (derived from maps only; no search).**
- For each pre-stage s, in order (rho, then ECM; td and pm1 stay off as in A), on the numbers still unsolved when s starts:
  - hazard h_s(t) on the map's 1/8-octave grid (`partition.FINE`): for the window (t_k, t_{k+1}], h = (numbers whose T_s falls in the window) / (numbers alive at t_k, i.e. T_s > t_k) / (t_{k+1} − t_k). The first window is (0, 256].
  - Under pricing P: marginal value of an op = h(t) · Q_P(bits); marginal cost = c_{s,P}, the stage's price per official op averaged over the numbers alive at t_k (the map's per-band price per op, `Map.pib`; 1 under official).
  - Budget_P = the upper edge t_{k+1} of the LAST window with h · Q_P ≥ c_{s,P}; 0 (stage off) if no window qualifies.
  - Budget = min over the three pricings (the most conservative). The next stage's alive set is computed after this stage at this budget.
- Q_P(bits) = Q(bits) · r_P(bits). Q is the frozen dedicated curve (official ops). r_P is qs's price per official op (mean qs cost under P / mean qs official ops) measured on the map at that size: 1 under official.
- **Simplification, stated:** a success is valued at Q only, not at Q plus the later stage's spending it also avoids. For rho (before ECM) the rule therefore undervalues success, and its rho budget leans low.
- **Noise, stated:** on the 1/8-octave grid, late windows hold few events, and "the last window" is decided by whether one more success happens late. As SENSITIVITY (pre-registered here, reported beside the primary, not used for the verdict) the same rule on half-octave windows (every 4th grid point).

**Derivation check.** Apply the rule to the 72-, 84- and 96-bit maps (each map's own hazard and r_P). Compare with the hindsight optima found by search on the same maps: 72 rho 3,158, ECM off; 84 rho 5,793, ECM 32,768 (A); 96 rho 12,634, ECM 60,097. "One grid step" = one 1/8-octave step.

**Test at 78 and 90 bits.**
- Fresh mixed populations, seeds 9200000 + 100 pb + bits, 80 per band, `oracle.check`. 78: smaller factor 16, 20, 24, 28, 32, 36 (unbalanced) and 39 (balanced). 90: 16, 20, 24, 28, 32, 36, 42 (unbalanced) and 45 (balanced). Maps built as for 72/96 (`size_budgets.py` machinery, parity sample, map-vs-direct cross-check).
- The rule's budgets at a test size use no data from that size: h = the arithmetic mean, window by window, of the two neighbouring derivation maps' hazards (78: 72 and 84; 90: 84 and 96), computed stage by stage with each neighbour's own alive sets; c_{s,P} likewise averaged; r_P interpolated linearly in bits between the neighbours; Q from the frozen curve.
- Compared, paired, against (i) A's absolute budgets and (ii) the theory scaling rule (A × L(N)/L(N_84), snapped). Each is run directly in lampcore `--types`. Fitness (c) against qs + lc 1.4 alone; paired bootstrap over numbers within bands (10,000, random.Random(2026)); all three pricings; (e) calls.
- **ACCEPT gate with per-band intervals (new rule):** per band and pricing, the 95% interval of mean cost / mean reference cost (numbers resampled within the band, 10,000, random.Random(2026)).
  - PASS: every band's upper bound ≤ 1.5 under every pricing, and no misses.
  - FAIL: some band's lower bound > 1.5 under some pricing, or a miss.
  - BORDERLINE: otherwise. The point values are reported beside.

**Predictions** (scored as written):
- (S1, the user's) The rule reproduces the hindsight optima within one grid step at 72, 84 and 96, including ECM off at 72.
- (S2, the user's) The stopping-rule budgets pass the gate at 78 and 90 and beat both alternatives on the robust score. Scored as gate PASS under the rule above, and robust-ratio intervals below 0 against both A and theory at both sizes.
- (S3, mine) S1 misses on the 1/8-octave grid. The rho budget lands at or below the hindsight value (success undervalued), and at least one ECM budget is more than one grid step away (late single events). The half-octave SENSITIVITY lands closer to the hindsight values than the primary in at least 4 of the 6 (size, stage) cells.
- (S4, mine) At 78 the rule beats A (robust interval below 0); against theory, a tie at both sizes. At 90 the rule beats A.

### Stopping-rule derivation: result of the pre-registered (Q-valued) rule (`evolve/stopping_derive.out`/`.json`)

| size | hindsight (rho / ECM) | rule, 1/8-octave windows | rule, half-octave (SENSITIVITY) | map fitness: hindsight / rule / half |
|---|---|---|---|---|
| 72 | 3,158 / off | 17,867 / 50,535 | 5,793 / 16,384 | 0.817 / 1.385 / 1.042 |
| 84 | 5,793 / 32,768 | 35,734 / 1,048,576 | 46,341 / 65,536 | 0.641 / 0.882 / 0.755 |
| 96 | 12,634 / 60,097 | 142,935 / 240,387 | 46,341 / 65,536 | 0.627 / 0.901 / 0.661 |

- The rule's budgets are 16–40 grid steps above the hindsight optima, and ECM is on at 72 bits. Ruint gives the smallest per-pricing budget almost everywhere; official runs to the cap.
- **Why (two flaws, both visible in the design):**
  - Valuing a rho success at Q ignores that ECM, the next stage, would find most of the same factors far more cheaply. A rho success is worth the remaining pipeline's cost, not Q. (The user's addendum, from Grok's review, says the same.)
  - "The last window with h · Q ≥ c" ignores loss-making stretches before that window. With a non-monotone hazard, the right stopping point maximizes cumulative net gain, not the last crossing. 1/8-octave windows add noise from single late events.
- S1 and S3 are scored after the test, with the rest.

### Per-stage budgets: addendum (user, from Grok's review; written before the test ran)

**Data status, stated explicitly.** The 78- and 90-bit populations (seeds 9200000 + 100 pb + bits) are fresh and untouched by any derivation. Their maps were built before this addendum. The only output seen from them is each pre-stage's solve count per band and qs's mean cost per band (`stopping_map.out`); no genome has been costed on them. They carry the final claim.

**Answer per size (72, 84, 96): the robust grid optimum on that size's map.**
- Joint over (rho, ECM) with td and pm1 off (the structure this line of work has used), exhaustive over the 1/8-octave grid (`FINE`, 98 × 98 vectors). Fitness (c): min over budgets of max over pricings. Exhaustive here, where the earlier hindsight values came from grid-plus-coordinate search; any difference is reported.
- Information: the 4-stage robust optimum (`partition.optimize`, td and pm1 free), to show whether td or pm1 would switch on at some size.

**Explanation beside it: backward induction with remaining-pipeline values, exact per-number composition.**
- Per pricing P: ECM last, e_P(r) = argmin over the grid of the exact composed cost of (ECM at e, then qs) on the numbers still alive after rho at r; then r_P = argmin over r of the composed cost of (rho at r, ECM at e_P(r), qs).
- So a rho success is valued at what the rest of the pipeline would have cost on that number. With exact composition and an exhaustive grid this equals P's joint grid optimum (the nested argmin over a 2-D grid is exact). It differs from the robust optimum only through the max over pricings.
- Conservative combination: rho_c = min_P r_P, ECM_c = min_P e_P(rho_c).
- Reported per pricing, combined, and whether each matches the robust optimum within one grid step.

**Test at 78 and 90 (no data from the test size):**
- Transferred maps: the two neighbouring derivation maps (78: 72 and 84; 90: 84 and 96) pooled number by number. Pre-stage records are used as recorded (pre-stage ops do not depend on N's size). Each number's qs cost under P is rescaled to the target size by [Q(t) · r_P(t)] / [Q(s) · r_P(s)] (Q = the frozen dedicated curve; r_P interpolated linearly in bits between the neighbours).
- Genomes, each run directly in lampcore `--types` on the fresh numbers:
  - **TRANSFER (primary):** the robust grid optimum on the transferred maps.
  - BI-conservative on the transferred maps (the explanation, also costed).
  - Q-RULE: the pre-registered stopping rule (neighbour-averaged hazards, 1/8 octave), as registered.
  - A's absolute budgets; theory scaling.
- Paired bootstrap, all three pricings, gate with per-band intervals (PASS / BORDERLINE / FAIL as defined above).
- **Two references:** qs + lc 1.4 alone (primary, for comparability), and the new qs genes alone (secondary column: fitness, scores and gate against it). Every genome keeps qs + lc 1.4 as its final stage.

**Predictions** (scored as written):
- (S5, the user's) The backward-induction budgets match the robust grid optimum within one grid step at 72, 84 and 96.
- (S6, mine) S5 holds in at least 5 of the 6 (size, stage) cells. Where it fails, the BI-conservative budget is below the robust one (min over pricings undershoots when no single pricing binds).
- (S7, mine) At 78 and 90, TRANSFER beats A (robust interval below 0) and ties or beats theory (interval includes 0 or lies below it). Gate: PASS at 90; PASS or BORDERLINE at 78.
- (S8, mine) Q-RULE is worse than A at both sizes (robust interval above 0); it overspends, as on the derivation maps.
- S2 (the user's, registered earlier) is scored on Q-RULE, the "stopping-rule budgets" it was written for.

### Per-stage budgets: results (`evolve/stopping_derive2.out`/`.json`, `stopping_test.out`/`.json`)

**Derivation (72, 84, 96): the robust grid optimum is the answer; backward induction explains it.**

| size | robust grid optimum (rho / ECM), fitness | BI under ruint | BI under official | BI under Montgomery | BI conservative (min over pricings), fitness | steps (rho, ECM) |
|---|---|---|---|---|---|---|
| 72 | 3,158 / off, 0.8172 | 3,158 / off | 1,448 / 285,870 | 1,448 / 285,870 | 1,448 / off, 0.8424 | 9, 0 |
| 84 | 5,793 / 32,768 (A), 0.6408 | 5,793 / 32,768 | 3,158 / 1,048,576 | 3,158 / 808,563 | 3,158 / 32,768, 0.6411 | 7, 0 |
| 96 | 12,634 / 60,097, 0.6269 | 12,634 / 60,097 | 5,793 / 1,048,576 | 4,871 / 480,774 | 4,871 / 60,097, 0.6354 | 11, 0 |

- The exhaustive optimum equals the earlier coordinate-search hindsight values at all three sizes. The 4-stage optimum keeps td and pm1 off at every size.
- **Ruint binds everywhere, and backward induction under ruint alone is the robust optimum, exactly.** Under official and Montgomery, ECM is cheap per op relative to qs, so they want ECM near the cap and less rho.
- **The conservative combination mixes incompatible vectors.** Componentwise min takes rho from official/Montgomery (which have ECM running long behind it) and ECM from ruint. Its rho is 7–11 steps low, but its fitness is close (+0.000 to +0.025): the robust surface is flat along rho near the optimum.
- The rule for "which budget" is therefore: backward induction under the binding pricing, not the min over pricings.

**Test (78 and 90; fresh numbers untouched by the derivation; they carry the claim).** Fitness (c) against qs + lc 1.4 alone (primary); against the new qs genes alone in brackets.

| 78 bits (560) | rho / ECM | robust [vs new qs] | official / ruint / Mont | gate, per-band intervals (worst band) |
|---|---|---|---|---|
| TRANSFER | 5,793 / off | 0.745 [1.523] | 0.694 / 0.745 / 0.719 | PASS (1.127 [1.107, 1.152], band 32) [vs new qs: FAIL] |
| BI-conservative | 3,158 / off | 0.810 [1.655] | 0.769 / 0.810 / 0.787 | PASS (1.070) [FAIL] |
| Q-RULE | 35,734 / 285,870 | 1.226 [2.506] | 0.243 / 1.226 / 0.615 | FAIL (2.821 [2.301, 3.507], band 39) [FAIL] |
| A | 5,793 / 32,768 | 0.826 [1.688] | 0.494 / 0.826 / 0.620 | BORDERLINE (1.534 [1.360, 1.723], band 36) [FAIL] |
| theory | 2,896 / 16,384 | 0.940 [1.921] | 0.728 / 0.940 / 0.808 | PASS (1.381 [1.323, 1.457], band 36) [FAIL] |
| hindsight on its own map (info) | 5,793 / off | 0.744 (map) | | |

| 90 bits (640) | rho / ECM | robust [vs new qs] | official / ruint / Mont | gate (worst band) |
|---|---|---|---|---|
| TRANSFER | 9,742 / 65,536 | 0.665 [0.737] | 0.457 / 0.665 / 0.542 | PASS (1.270 [1.181, 1.354], band 45) [BORDERLINE] |
| BI-conservative | 4,871 / 65,536 | 0.670 [0.743] | 0.467 / 0.670 / 0.548 | PASS (1.242) [PASS] |
| Q-RULE | 71,468 / 311,744 | 0.848 [0.940] | 0.253 / 0.848 / 0.499 | FAIL (2.113 [1.884, 2.344], band 45) [FAIL] |
| A | 5,793 / 32,768 | 0.789 [0.875] | 0.662 / 0.789 / 0.714 | PASS (1.220 [1.217, 1.222], band 45) [PASS] |
| theory | 11,585 / 65,536 | 0.667 [0.739] | 0.456 / 0.667 / 0.542 | PASS (1.281) [BORDERLINE] |
| hindsight on its own map (info) | 9,742 / 46,341 | 0.633 (map) | | |

Paired, robust log2 [95%] (the robust ratio between two genomes is the same against either reference here, because ruint binds for both):
- 78: TRANSFER / A −0.148 [−0.235, −0.056] (official +0.491, Montgomery +0.214: **(e) undecided**); TRANSFER / theory −0.334 [−0.407, −0.262] (all three pricings below 0: **TRANSFER**); TRANSFER / BI-conservative −0.120 [−0.182, −0.064]; Q-RULE / A +0.570 [+0.454, +0.682].
- 90: TRANSFER / A −0.247 [−0.312, −0.186] (all three below 0: **TRANSFER**); TRANSFER / theory −0.004 [−0.011, +0.008] (tie); TRANSFER / BI-conservative −0.010 [−0.033, +0.010] (tie); Q-RULE / A +0.103 [+0.010, +0.192].

**Reading.**
- **Budgets transferred from the neighbouring sizes' maps work.** At 78 bits the transferred optimum (rho 5,793, ECM off) is exactly the hindsight optimum on the 78-bit map. At 90 bits it is 4 grid steps above the hindsight ECM (65,536 vs 46,341; map fitness 0.665 vs 0.633). It passes the gate with per-band intervals at both sizes and beats A on the robust score at both.
- **ECM switches off between 84 and 72 bits.** It is off at 72 and 78, and on at 84 and above. The theory rule, a single scale factor, cannot express this, and at 78 it is 0.79x worse than TRANSFER under all three pricings.
- **The robust optimum gives up official cost to buy ruint cost.** At 78 TRANSFER loses to A under official (+0.49 log2) and Montgomery (+0.21) while winning under ruint (−0.15). By the (e) rule it is not "better than A" at 78; it is better on the robust score only.
- **Against the new qs genes alone (secondary reference):** at 78 bits every genome here, all with qs + lc 1.4 as the final stage, is worse than the new qs alone under ruint (robust 1.52–2.51), and fails the gate against it. At 90 the best is 0.737. The final-stage genes matter as much as the budgets at these sizes; the size-scaling test (next) combines the two.
- **The Q-valued stopping rule is ruled out:** it overspends at both sizes (1.07x and 1.49x A), as on the derivation maps.

**Predictions scored as written:** 8 scored, 2 held, 6 missed.
- (S1, the user's) the Q-valued rule reproduces the hindsight optima within one grid step, incl. ECM off at 72: **missed** (16–40 steps over; ECM on at 72).
- (S2, the user's; scored on Q-RULE) passes the gate at 78 and 90 and beats both alternatives: **missed** (gate FAIL at both; worse than A and theory at both).
- (S3, mine) S1 misses; rho at or below hindsight; at least one ECM > 1 step away; half-octave closer in ≥ 4 of 6 cells: **missed.** The rho clause failed (far above, not below). The other three held (half-octave closer in 4 of 6: 72 rho, 84 ECM, 96 rho, 96 ECM).
- (S4, mine) the rule beats A at 78 and ties theory at both: **missed** (Q-RULE worse than A and theory at both).
- (S5, the user's) backward-induction budgets match the robust optimum within one grid step at 72, 84 and 96: **missed** for the conservative combination as registered (rho 7–11 steps low; ECM exact at all three). BI under the binding pricing (ruint) matches exactly at all three; that was not the registered reading.
- (S6, mine) S5 holds in ≥ 5 of 6 cells; where it fails, BI-conservative is below the robust value: **missed** (3 of 6). The second clause held.
- (S7, mine) TRANSFER beats A at 78 and 90, ties or beats theory, gate PASS at 90 and PASS or BORDERLINE at 78: **held** (robust intervals; gate PASS at both).
- (S8, mine) Q-RULE worse than A at both sizes: **held** (+0.570, +0.103).

## 2026-10-24 — Outside check (Wolfram Language 15), and a queued small-bound p-1 map check (prediction before the map is extended)

### Outside check (user, Wolfram Language 15, Oct 24): agrees

Figures computed outside the repo, each checked here against the repo's own record:

- **L(N) growth per bit:** 0.1700 (72→84) and 0.1599 (84→96). These are log₂ of the theory ratios 0.2432 and 3.781 divided by 12, as in the size-relative budgets table (0.2432 / 3.7814).
- **Dedicated-curve ratios:** 0.2906 and 3.442, as in that table (0.2906 / 3.4420).
- **log₂(lcm(1..B)) / B:** 1.417, 1.444, 1.446 and 1.441 at B = 2^8, 2^10, 2^12 and 2^16. Recomputed here: the same values. This matches the ECM stage-1 rough check (≈ 16·B1 ≈ 11·log₂ lcm) and the MOVES row's "~1.44 B multiplies".
- **Doubling race:** 19 complete doubling turns under 2^28, from 2^9(2^m − 1) ≤ 2^28. This matches the MOVES row's "~19 turns".
- **rho on 16-bit p:** sqrt(πp/2) = 321 iterations at p = 2^16, so the measured 2^9.6 means about 2.4 ops per iteration. The partition map's band-16 rho mean is 802 ops (2^9.65; 793 multiplies on average), about 2.5 ops per iteration. [Corrected Oct 24, second outside check: both per-iteration figures use p = 2^16. Band-16 primes lie in [2^15, 2^16), and their mean sqrt(πp/2) is 272.7, so the map's 802 ops are 2.94 ops per sqrt(πp/2). The breakdown is below, under the second round.]
- **td on 16-bit p:** mean p/2 over 16-bit primes is 24,461, against rho's 776, a ratio of 31x. The partition map's band-16 means are td 23,912 and rho 802, a ratio of 29.8x. Neither the 24,461 nor the 776 appears in NOTES; the map values are given beside them here. The map's figures are within 3% of the outside figures.

No number in NOTES changes.

### Queued: p-1 with a small bound, as a map check (after the qs-gene size-scaling test)

**What changes from the ruled-out test.** The MOVES row "td and p-1 as pre-stages before qs" was ruled out with pm1 b = 0.1991 (B ≈ 2^16.7 at 84 bits). The changed condition is the bound: B = 2^8, 2^9 and 2^10 (b ≈ 0.10–0.12 at 84 bits). That row already names this as a reopening condition.

**Meter.** No change to charging, op counts or pricing. `lamp_pm1` and its lampcore twin are already charged and in parity. Only the bound gene takes new values. The bound is fixed in absolute terms (B), so b = log₂ B / bits varies with size; the card is given as B.

**Exact stage-1 charge on the meter** (`lamp_pm1` charges bit_length(p^k) per prime power, plus 1 gcd): 388, 787 and 1,558 ops at B = 2^8, 2^9 and 2^10. This is about 5% above log₂ lcm(1..B) (363, 743, 1,479), because bit lengths round up. pm1 has one gcd, at the end, so it is all or nothing: every number that reaches it pays the full charge.

**Plan.**
- Run the three small-bound cards alone on the numbers of the existing maps: the 84-bit partition map, the 72/96-bit size maps and the 78/90-bit stopping maps. That is one cheap pass per card, with success or failure recorded per number. No other lamp is rerun, and no new population.
- Then re-solve the robust grid optimum with the card available, as in `stopping.py derive2`. The card goes in the pm1 slot with ob ∈ {0, full}, alone or with rho and ECM in A's order.
- Report the result per size and per pricing, with the gate (per-band intervals), and how much the card costs where it fails.
- If the maps cannot be extended (for example, the numbers are not recoverable from them), stop and report rather than build a new population.

**Prediction (user's, from Dickman ρ; written before the map is extended).** [Superseded, Oct 24, by the user's revised prediction under the second round below. That revision was also written before the map was extended. This text is kept.]
- ρ underestimates the smoothness chance, because p − 1 is even.
- At B = 2^10 (~1,480 multiplies), the chance that p − 1 is smooth is 0.31, 0.16, 0.074 and 0.032 at p of 20, 24, 28 and 32 bits.
- Expected cost per factor found is therefore ~4,800, ~9,500 and ~20,000 at 20, 24 and 28 bits, against rho's average ~3,100, ~12,400 and ~50,000.
- Worth switching on only if it pays at 24–32 bits after rho's budget.

Recomputed here as a check (not part of the user's prediction):
- ρ(2.0, 2.4, 2.8, 3.2) = 0.307, 0.156, 0.073 and 0.032.
- 1,480 / ρ = 4,823, 9,488, 20,166 and 46,683.
- rho at 2.4 ops per iteration costs 3,080, 12,321, 49,282 and 197,129, so at 32 bits the user's comparison extends to ~47,000 against ~197,000.
- At the meter's 1,558 ops, the p-1 figures are 5% higher.

**Prediction (mine, written before the map is extended).**
- (P1) The re-solved robust optimum leaves the small-bound card off at 84 bits. If it turns on anywhere among 72/78/84/90/96, its robust gain over the same optimum without it is under 2% (log₂ > −0.03).
- (P2) Under ruint, the card costs at least as much relative to qs as it does under official, so if any pricing turns it on, official does.

Reason: every number that reaches pm1 pays ~1,560 ops. That includes the balanced band, where pm1 almost never hits, and the 16–20-bit bands, which rho has mostly already solved. On 24–32-bit p, ECM at A's 2^15 budget already finds most factors, so pm1 saves only part of ECM's cost on its 3–16% of hits.

### Outside checks, second round (user, Wolfram Language 15 cloud, Oct 24; SeedRandom[2026]; code in the user's reply)

Checked in the repo with `evolve/outside_checks.py` (`outside_checks.out`/`.json`; 2 s). That script is information only and has no charged path. It reruns the rho card on the partition map's 80 band-16 numbers, and its ops are asserted equal to the map's on every number. It recomputes pm1's outcome on all 560 map numbers, and draws random primes with random.Random(2026).

**Confirmed again (user).** The figures of the first round, plus the sign test: 3/8 and 5/8 give p = 0.727, as in the Run 8 per-seed table.

**rho.**
- *User:* tail + cycle = 1.02–1.03 × sqrt(πp/2), from 500 primes each at 16, 20 and 24 bits. Brent detection takes about 1.57x that (445 steps at p = 2^16). So 2^9.6 = 776 ops implies about 1.74 ops per Brent step.
- *Repo, on the band-16 map numbers:*
  - mean ops 802.0 = 552.0 f evaluations + 241.2 product accumulations + 8.8 gcds;
  - mean sqrt(πp/2) is 272.7, and mean μ + λ is 279.4 (1.025x, which agrees with the user);
  - Brent with b = 1 takes 515.0 f evaluations to detection (1.888x);
  - the card itself takes 552.0 f evaluations, 7.2% more, because its gcd is batched every 64 products and it overshoots.
- **The charging is as described**, and is confirmed exactly: 1 op per squaring and 1 per product accumulation. Products are skipped on Brent's power-of-two advance steps (44% of f evaluations carry a product). Add 1 op per gcd, about 1 per 64 products, plus the backtrack.
- **Ops per Brent step depends on what counts as a step.** It is 1.56 per f evaluation to detection (b = 1). With the user's 1.57 × sqrt(πp/2) applied to these primes (428 steps), it is 1.87. The user's 1.74 uses p = 2^16 for a band whose primes start at 2^15.

**Primes-and-gaps power (user; correction).**
- 80% power at the strictest Holm step (α = 0.05/40, Fisher z) needs r = 0.171 pooled (n = 560) and r = 0.433 within one band (n = 80). Rank correlations need slightly more.
- Recomputed here: z₀.₉₉₉₃₈ + z₀.₈ = 3.227 + 0.842 = 4.068; tanh(4.068/√557) = 0.171; tanh(4.068/√77) = 0.433.
- The primes-and-gaps result and its MOVES row are reworded to match, each with a bracketed record of the old wording.

**pm1 on the partition map against random-prime powersmooth rates** (B = int(N^0.1991) ≈ 2^16.7). Columns: the map's solve fraction; the exact prediction (ord(2) divides the stage-1 exponent for exactly one of p, q); p − 1 B-powersmooth for the smaller factor; the user's random-prime rate (2000 primes per size); and hits by factor (small only / large only / both, where gcd = N and the run fails).

| band | map | exact prediction | p − 1 powersmooth | user | map − user | 2 SE | hits small / large / both |
|---|---|---|---|---|---|---|---|
| 16 | 0.988 | 0.988 | 1.000 | 1.000 | −0.012 | 0 | 79 / 0 / 1 |
| 20 | 0.800 | 0.800 | 0.825 | 0.886 | −0.086 | 0.072 | 64 / 0 / 2 |
| 24 | 0.700 | 0.700 | 0.713 | 0.700 | +0.000 | 0.104 | 55 / 1 / 2 |
| 28 | 0.525 | 0.525 | 0.525 | 0.531 | −0.006 | 0.114 | 41 / 1 / 1 |
| 32 | 0.412 | 0.412 | 0.412 | 0.404 | +0.008 | 0.112 | 30 / 3 / 3 |
| 36 | 0.287 | 0.287 | 0.263 | 0.276 | +0.011 | 0.102 | 19 / 4 / 2 |
| 42 | 0.275 | 0.275 | 0.087 | 0.143 | +0.132 | 0.080 | 6 / 16 / 1 |

(The user's 39-bit rate, 0.195, has no map band.)

- **The meter's pm1 matches the exact prediction on all 560 numbers.**
- **Three bands are off by more than 2 SE, each for a reason in the table:**
  - *Band 16:* one number has both p − 1 and q − 1 within the bound, so the gcd is N and the run fails. The user's rate has no sampling error at 1.00, so any failure counts as "off".
  - *Band 20:* the same failure on 2 numbers (0.025), plus a low draw: 66/80 = 0.825 smooth against 0.879–0.886 random, 1.5 binomial SE.
  - *Band 42:* the balanced band, where either factor can be the smooth one. Single hits are 22/80, against 2r(1 − r) ≈ 0.24 at r = 0.14.
- No band disagrees beyond these.

**Random-prime rates recomputed** (random.Random(2026), 2000 primes per size; the user's figures in brackets):
- **B = 2^16.7 (106,463):**
  - 16 bits: 1.000 [1.00]
  - 20 bits: 0.879 [0.886]
  - 24 bits: 0.711 [0.700]
  - 28 bits: 0.536 [0.531]
  - 32 bits: 0.393 [0.404]
  - 36 bits: 0.274 [0.276]
  - 39 bits: 0.224 [0.195]
  - 42 bits: 0.138 [0.143]
- **B = 2^10:**
  - 20 bits: 0.392 [0.38]
  - 24 bits: 0.205 [0.18]
  - 28 bits: 0.092 [0.096]
  - 32 bits: 0.035 [0.046]
- The largest gaps between the two samples are about 2 SE of a difference of two samples of 2000: 39 bits at 2^16.7 (+0.029, 2.3 SE), 24 bits at 2^10 (+0.025, 2.0 SE) and 32 bits at 2^10 (−0.011, 1.8 SE). Two independent samples, 12 comparisons; not chased further.
- At the meter's 1,558 ops for B = 2^10, the cost per factor found from these rates is 3,974 / 7,600 / 16,843 / 45,159 at 20 / 24 / 28 / 32 bits. The user's figures are ~3,900 / ~8,400 / ~15,400 / ~32,500.

**Queued small-bound p-1 check: the user's revised prediction** (Oct 24, written before the map is extended; this supersedes the user's Dickman-based prediction above).
- *Inputs:* empirical powersmooth rates at B = 2^10 of 0.38 / 0.18 / 0.096 / 0.046 at 20 / 24 / 28 / 32 bits, for ~1,480 multiplies. That makes the cost per factor found ~3,900 / ~8,400 / ~15,400 / ~32,500, against rho's average ~3,100 / ~12,400 / ~50,000 / ~200,000.
- *Prediction:* a small-B p-1 stage switches on after rho at 84–96 bits and pays a few percent in robust fitness. It is off at 72–78 if ruint's multiply price for p-1 outweighs it.
- My P1–P2 above stand as written; P1 predicts the opposite at 84 bits.

## 2026-10-25 — Type mix of the two qs references by size (information only; before the size-scaling test)

**Status.** This check had not run before; no earlier entry records it. It ran now. Code: `evolve/typemix.py`, outputs `typemix.out`/`.json` (37 s).

**Data.** The existing map numbers: 72 and 96 bits (`size_map.json`, 480 and 640 numbers), 78 and 90 bits (`stopping_map.json`, 560 and 640), and 84 bits (`partition_map.json`, 560).
- qs + lc 1.4's per-type counts are taken from the maps. The new qs genes were run in `stopping.py test` and `partition_newqs.py`, but their per-type counts were not saved, so the new qs alone was rerun here: lampcore `--types`, cap 2^28, the same numbers.
- The maps' qs + lc 1.4 counts reproduce exactly when rerun, at every size. The 84-bit map stores zero-valued types, which are dropped before comparing.

**new qs alone / qs + lc 1.4 alone** (mean cost ratio):

| bits | official | ruint | Montgomery | numbers at s = 4: old / new |
|---|---|---|---|---|
| 72 | 1.149 | 0.826 | 0.841 | 0.019 / 0.000 |
| 78 | 1.010 | 0.489 | 0.673 | 0.243 / 0.000 |
| 84 | 0.963 | 0.405 | 0.630 | 0.554 / 0.004 |
| 90 | 1.045 | 0.902 | 0.875 | 1.000 / 0.930 |
| 96 | 1.003 | 0.908 | 0.859 | 1.000 / 1.000 |

At 78, 84 and 90 these are the figures already reported: stopping test 1.01 / 0.49 / 0.67 and 1.04 / 0.90 / 0.88, and `partition_newqs` 0.963 / 0.405 / 0.630.

**Mean ops per type** (old = qs + lc 1.4's genes, kc 32, bc 1.1, mc 0.25, tc 1.38, lc 1.4; new = kc 4, bc 0.899, mc 0.734, tc 1.104, lc 1.661). Full tables, including fb, mult, sqrt and lp, are in `typemix.out`. The types that matter:

| bits | setup_full old / new | setup_small old / new | sieve_update old / new | sieve_scan old / new | confirm_td old / new | la old / new |
|---|---|---|---|---|---|---|
| 72 | 8,506 / 6,596 | 8,799 / 5,843 | 43,475 / 73,046 | 19,549 / 37,963 | 38,508 / 28,589 | 17,681 / 10,530 |
| 78 | 31,224 / 6,603 | 14,985 / 9,403 | 80,450 / 126,064 | 35,998 / 63,328 | 73,829 / 54,785 | 40,646 / 24,560 |
| 84 | 62,714 / 6,974 | 24,280 / 15,073 | 146,587 / 222,273 | 63,400 / 107,003 | 135,580 / 102,191 | 91,642 / 55,336 |
| 90 | 107,952 / 100,841 | 38,936 / 23,879 | 258,942 / 400,000 | 110,846 / 193,231 | 254,891 / 193,201 | 210,462 / 127,724 |
| 96 | 107,969 / 107,944 | 64,610 / 38,312 | 460,027 / 695,450 | 191,231 / 325,218 | 483,247 / 358,196 | 480,677 / 287,415 |

**Each type's share of cost, old / new.**
- *ruint:*
  - setup_full 0.377 / 0.353 (72), 0.563 / 0.243 (78), 0.606 / 0.166 (84), 0.609 / 0.630 (90), 0.466 / 0.513 (96);
  - confirm_td 0.15–0.24 / 0.14–0.28;
  - setup_small 0.07–0.12 / 0.05–0.11;
  - sieve_update 0.05–0.07 / 0.09–0.18.
- *Montgomery:*
  - setup_full 0.149 / 0.137 (72), 0.268 / 0.084 (78), 0.302 / 0.053 (84), 0.302 / 0.323 (90), 0.194 / 0.226 (96);
  - confirm_td 0.27–0.37 / 0.25–0.33;
  - setup_small 0.12–0.18 / 0.09–0.14;
  - sieve_update 0.09–0.10 / 0.16–0.21.
- Every other type is under 0.10 at every size, under both pricings.

**What drives the 78-bit gap: setup_full, through s.**
- *How the charge works.* qs forms every candidate A up front: all C(P, s) combinations of a pool of P = 16 + 4s primes, at (s − 1) full-price multiplies each (`qs.py`, phase 3). That is 2·C(28, 3) = 6,552 ops at s = 3, and 3·C(32, 4) = 107,880 at s = 4: a 16.5x step. s is set by the target A ≈ sqrt(2kN)/M, with M = mc·B.
- *Under ruint.* setup_full is the only type whose contribution to new − old (as a share of old's total cost) is large:
  - 72: −0.085; 78: −0.444; 84: −0.539; 90: −0.040; 96: 0.000.
  - The new genes' extra sieve work adds +0.03 to +0.04; confirm_td and setup_small give back −0.03 to −0.06 each.
  - Under Montgomery setup_full gives −0.212 at 78 and −0.268 at 84.
  - Under official every contribution is small, and sieve_update/scan (+0.24 at 78) cancel confirm_td and la.
- *Where the step falls.* The old genes cross s = 3 → 4 between 72 and 90 bits (1.9%, 24.3%, 55.4% and 100% of numbers at 72, 78, 84 and 90). The new genes cross between 84 and 90 (0.4% at 84, 93% at 90). The ruint gap is wide only where the two genomes sit on opposite sides of the step (78–84), and it closes once both are at s = 4 (0.90 at 90 and 96).
- **The old-gene parameter: mc** (sieve half-width M = mc·B; 0.25 against 0.734). One-gene swaps on the same numbers (new / old cost ratio, official / ruint / Montgomery):
  - At 78:
    - old genes with mc → 0.734: 1.059 / 0.525 / 0.733, which closes most of the 0.489 ruint gap;
    - new genes with mc → 0.25: 1.015 / 1.363 / 1.137;
    - next comes kc (old with kc → 4: 0.963 / 0.594 / 0.851). A smaller multiplier set keeps kN, and so the target A, lower.
  - Making bc smaller alone *raises* the old genes' ruint cost (1.647), since a smaller B pushes the target A up.
  - Swapping tc or lc alone moves ruint by 4–8% or less.
  - The same pattern holds at 84: mc gives 0.531 ruint against the full gap of 0.405.
- So **the ruint/Montgomery gain of the new genes at 78–84 bits is mostly qs + lc 1.4's short sieve interval (mc 0.25) pushing it to s = 4**, where the up-front A enumeration costs about 108,000 full multiplies. It is not a better sieve.

**Do any optypes prices depend on operand size?**
- **In the price table, no.** `optypes.prices()` is one table per pricing, calibrated once against an 84-bit multiply (the P-core median), and no price takes N's size.
- **The underlying timings** (opbench, median of P1–P3):
  - Montgomery mulmod is flat: chain 7.44 / 7.36 / 7.46 ns at 60 / 84 / 100 bits. It uses two limbs throughout.
  - ruint `U256::mul_mod` is 16.81 / 27.35 / 30.26 ns. The big step is at 64 bits (one limb to two), below this range. From 84 to 100 bits it rises 11%.
  - No timing exists at 72 or 90 bits. Interpolating within two limbs, full-price ops would move by about ±4% between 72 and 90 against the 84-bit basis, with small-number prices moving by the inverse.
  - gcd Euclid steps grow with N (49.6 at 84 bits, 59.5 at 100), but qs's gcd work is charged per step (sqrt_gcd) and is under 0.2% of cost.
- None of this approaches the 0.49 → 0.90 swing between 78 and 90 bits, which is a count effect (s), not a price effect.

**What MOVES' 0.955x (72) and 0.924x (96) compare.**
- They come from generalization test (a) (`newqs_general.py`; seeds 8800000 + 100 pb + bits, mixed 72 and 96 bits, 480 and 640 numbers). Two full pipelines with A's budgets (rho 5,793, ECM 32,768; td and pm1 off) are compared, differing only in the final qs's genes (new against qs + lc 1.4's). Each is scored as robust fitness against qs + lc 1.4 alone, and the ratio is fitness(new) / fitness(old).
- In both cases the binding pricing is ruint:
  - at 72, 1.100 against 1.152;
  - at 96, 0.688 against 0.744.
- Per pricing (log₂): at 72, official +0.111, ruint −0.066, Montgomery −0.107; at 96, −0.003, −0.114 and −0.200.
- So they are pipeline-level robust ratios on different numbers, with pre-stage costs in both numerator and denominator. They are not the qs-alone ratios above. Both sizes sit outside the 78–84 step, which is consistent with the gain being small there.

## 2026-10-25 — On-demand A selection for the qs card: cost model (before any code)

**Why.** The type mix (entry above) showed that the qs card forms every candidate A up front: all C(P, s) combinations of a pool of P = 16 + 4s primes (P = 40 when s = 1), at (s − 1) full multiplies each. It then sorts them (uncharged) and uses them best-first. A run uses 5–21 A's (traced: 2–3 numbers per size at 72–96 bits, both genomes) out of 3,276 (s = 3) or 35,960 (s = 4) formed. The enumeration costs 6,552 ops at s = 3 and 107,880 at s = 4, all priced as full multiplies. Under ruint that is 38–61% of qs + lc 1.4's cost at 72–96 bits. The decision (user, Oct 25): fix this before the size-scaling test.

**Option, not a replacement.** A new qs gene, `a_mode`, set by hand and never mutated:
- `enumerate` (default; absent means enumerate) is today's card, op for op. Every earlier result stays valid under it.
- `on_demand` is defined below.

**Reference policy (user).** qs + lc 1.4 with a_mode = enumerate stays the frozen reference for comparability with every earlier result. It carries the setup overcharge: up to ~60% of its ruint cost at 78–96 bits (56% at 78, 61% at 84 and 90, 47% at 96; 38% at 72). Results under on_demand are reported beside it. Changing the reference is a separate decision after the numbers, and is decided by the pre-registered replacement rule (below), not by a post hoc reading.

**on_demand rule** (for s ≥ 2; s, P, the pool and the target are unchanged). A selection rule, ported from the description the user gave (choose s − 1 primes near the target, solve for the last). It was not taken from any code.
1. `by_q` is the pool sorted by |ln(p/q)|, ties to the smaller p, where q = target^(1/s): the closest primes to q come first.
2. Prefixes are the (s − 1)-combinations of `by_q`, in itertools order. The first prefixes therefore use the primes closest to q.
3. For each prefix: A′ = product of the prefix, t′ = target / A′, and `last` = the pool prime not in the prefix that minimizes |ln(p/t′)|, ties to the smaller p. Then A = A′·last.
4. **Target check:** accept only if |log₂(A/target)| ≤ 0.25. This is a guard against a prefix that drives t′ outside the pool. It keeps A within ±19% of the target.
5. **Dedupe:** the sorted tuple must not have been used already (different prefixes can complete to the same set).
6. Accepted A's go to the unchanged per-A code (B_l, roots, Gray-code polynomials, sieve, confirm, large primes) in the order they are found. A new candidate is formed only when the previous A's polynomials are used up and the ledger still needs relations.
7. **Exhaustion:** when the prefixes run out, the polynomials have run out, exactly as when enumerate's list runs out. The card returns None for this k and the next multiplier is tried, paying again for everything.
8. **s = 1:** there is only one prefix (the empty one), so on_demand falls back to enumerate's single-prime list. That list costs 0 multiplies under either mode. s = 1 does not occur at 72–96 bits.

**Charges for on_demand** (only these are new; every other charge is unchanged):

| per candidate formed | ops | type |
|---|---|---|
| A′ = product of s − 1 primes | s − 2 multiplies | setup_full |
| t′ = target / A′ | 1 (a division of a number of A's size) | setup_full |
| choosing `last`: one comparison per pool prime not in the prefix | P − (s − 1) | setup_small |
| A = A′ · last | 1 multiply | setup_full |
| target check | 1 | setup_full |
| dedupe lookup (only if the check passes) | 1 | setup_small |

So each candidate costs s + 1 full ops (the brief's s − 1 multiplies plus the target check, plus the division, which a description that "solves for the last prime" needs). Each also costs P − s + 1 (+1) small ops. The division and the full-price check are deliberate overcharges.

**Per-A setup stays charged per A used, in both modes** (outside review, item 1; confirmed in `qs.py` and `qs.rs`):
- B_l: per q_l, 1 op for A/q_l, the Euclid steps of its inverse, 1 op for γ and 1 op for A/q_l·γ. Of these, 2s full ops per A are setup_full (`optypes.qs_counts`: + 2s·a_count) and the Euclid steps are setup_euclid.
- Per sieved prime: the Euclid steps of A⁻¹ mod p (setup_euclid), 2 root multiplies and s multiplies for 2·B_l·A⁻¹ mod p (setup_small: small-number operands).
- Per Gray-code switch: 1 op per root updated (setup_small).

on_demand removes only the up-front enumeration of all C(P, s) candidates.

**Type split** (`optypes.qs_counts`, lampcore `--types`):
- setup_full = (s − 1)·combos [enumerate only] + (s + 1)·od_cands [on_demand only] + 2s·a_count.
- The selection's small ops go to setup_small, which remains setup minus setup_full minus setup_euclid.
- Trace fields: `od_cands` (candidates formed) and `a_seq` (the A's used, in order).
- lampcore records the same counts as events (EV_SETUP_FULL).

**Expected setup_full per run.** From the traces: about 1.3 candidates are formed per A used (offline simulation of the rule above on the traced runs; range 1.0–1.5). a_count is about 6–21 (mean ~10). So:
- s = 3: ≈ 4·13 + 6·10 ≈ 110, against enumerate's 6,552 + 60 ≈ 6,600.
- s = 4: ≈ 5·13 + 8·10 ≈ 145, against 107,880 + 80 ≈ 107,960.

| bits | enumerate, observed mean (old / new genes) | on_demand, expected (old / new) |
|---|---|---|
| 72 | 8,506 / 6,596 | ~115 / ~110 |
| 78 | 31,224 / 6,603 | ~120 / ~110 |
| 84 | 62,714 / 6,974 | ~130 / ~110 |
| 90 | 107,952 / 100,841 | ~145 / ~145 |
| 96 | 107,969 / 107,944 | ~145 / ~145 |

**A quality.**
- *Distance from the target.* In the offline simulation of the rule on the traced runs, on_demand's first a_count A's are 0.004–0.03 log₂ from the target on average (max 0.05). Enumerate's are 0.0001–0.006. The exception is the top-of-base case (the new genes at 90 bits with s = 3, where q is above the pool), with 0.08–0.15 against enumerate's 0.05–0.09. Candidates passing the 0.25 check number 158–4,556 per run, against at most 31 needed, so exhaustion is not a practical risk.
- *Effect on yield.* For A = ρ·target, the polynomial values on [−M, M] scale as M·sqrt(kN/2)·|2ρt² − 1/ρ|, t ∈ [−1, 1]. The mean log₂ size changes by at most 0.009 bits at |log₂ ρ| ≤ 0.03, 0.037 bits at 0.1 and 0.066 at 0.15 (numerical integration). With about 20% fewer smooth values per extra bit near u ≈ 4.5, the expected yield loss is under 0.2% typically, and about 1% in the top-of-base case.
- *Order.* on_demand's A's come in prefix order, not sorted by closeness. A different A sequence means different relations, so every downstream count differs per number; only its distribution should match enumerate's.

**Identity and parity tests** (before any measurement):
1. *enumerate is unchanged:* lampcore reproduces every map's qs + lc 1.4 per-type counts exactly (as `typemix.py` asserts), and the existing parity suite passes.
2. *Downstream depends only on the A sequence:* a test-only gene `a_given` (a list of A's as prime tuples, Python only, never mutated, like `check`) feeds the card a fixed A sequence with no selection charge. On sample numbers at 72–96 bits, both genomes:
   - for enumerate, every phase's ops equal those of `a_given` = enumerate's own used A's, except setup, which differs by exactly (s − 1)·C(P, s);
   - for on_demand, every phase equals `a_given` = on_demand's own a_seq, except setup, which differs by exactly the selection charges: (s + 1)·od_cands full, plus the logged small ops.

   This shows the sieve, confirm, LA, sqrt and large-prime phases are unchanged given the same A sequence.
3. *Python = Rust count for count:* on_demand runs on sample numbers from every map (2 per band per size, both genomes), with Python's `qs_counts` equal to lampcore `--types` on every type, and the same factor. The parity suite also gets on_demand qs pairs.

### On-demand A: measurement plan and predictions (written before any on_demand code or run)

**Facts under enumerate, recorded before the fix.** N51-0917's qs (kc 32, bc 1.128, mc 1.003, tc 1.379, no lc) on the same map numbers (outside review, item 3):
- It is at s = 4 on 0 / 0 / 0 / 20.3 / 54.4% of numbers at 72 / 78 / 84 / 90 / 96 bits, against qs + lc 1.4's 1.9 / 24.3 / 55.4 / 100 / 100%.
- Its cost against qs + lc 1.4 (official / ruint / Montgomery):
  - 72: 1.503 / 0.850 / 0.894
  - 78: 1.351 / 0.506 / 0.715
  - 84: 1.305 / 0.420 / 0.670
  - 90: 1.297 / 0.508 / 0.715
  - 96: 1.336 / 0.737 / 0.827
- Its wide interval (mc 1.0) keeps it at s = 3 through 84 bits. **So allocation B's calibrated lead (B = A's budgets with N51-0917's qs final) is, at least in part, the same setup artifact.** The ruint gap at 78–84 bits matches the s = 4 step, as for the new genes. How large a part is measured below.

**Runs** (lampcore `--types`, cap 2^28; information plus the gate):
- (R1) Map numbers at 72 / 78 / 84 / 90 / 96 bits (480 / 560 / 560 / 640 / 640; those of `typemix.py`). Each of qs + lc 1.4's genes, the new genes and N51-0917's qs is run alone with a_mode = on_demand. They are reported beside the enumerate figures and against the frozen reference (qs + lc 1.4, enumerate), per pricing and per size:
  - new/old with both on_demand;
  - setup_full share;
  - polynomials per run (sieve_scan / (2M + 1));
  - per-band intervals and the gate against the frozen reference;
  - misses.
- (R2) **Replacement rule, as pre-registered** (generalization test (2), "Replacement rule (decided now)"), on its own populations: balanced semiprimes_pq(bits, 240, 8700000 + bits), 54–84 bits step 6. It compares the new genes with qs + lc 1.4's genes, both with a_mode = on_demand. The rule decides; there is no post hoc reading.
- (R3) **Balanced control:** the partition optimizer on band 42 of `partition_map.json` (the control as run in the partition study), with the final qs's costs replaced by qs + lc 1.4 on_demand. The pre-stage records are unchanged.
- **Not rerun now** (stated only): allocation A's fitness, the per-stage budgets by size and allocation B under an on_demand reference.

**Data status.** These are not sealed numbers. The map numbers were used to derive budgets, but no qs on_demand run has seen them. The R2 populations were used once before, for the enumerate replacement verdict. A fresh sealed set is not part of this brief.

**Projection used for the predictions.** Each run's enumeration charge is replaced by the expected on_demand selection (~110 at s = 3, ~145 at s = 4); every other count is held fixed. Applied to `typemix.json`, this gives the following ratios (official / ruint / Montgomery):

| bits | qs + lc 1.4, on_demand / enumerate | new, on_demand / enumerate | new / old, both on_demand | N51-0917 / old, both on_demand |
|---|---|---|---|---|
| 72 | 0.945 / 0.628 / 0.853 | 0.963 / 0.653 / 0.865 | 1.171 / 0.858 / 0.853 | 1.546 / 0.897 / 0.915 |
| 78 | 0.897 / 0.439 / 0.733 | 0.979 / 0.761 / 0.917 | 1.102 / 0.847 / 0.842 | 1.483 / 0.886 / 0.899 |
| 84 | 0.888 / 0.395 / 0.699 | 0.987 / 0.836 / 0.947 | 1.070 / 0.857 / 0.854 | 1.456 / 0.904 / 0.915 |
| 90 | 0.896 / 0.392 / 0.698 | 0.907 / 0.371 / 0.678 | 1.058 / 0.853 / 0.850 | 1.418 / 0.907 / 0.916 |
| 96 | 0.942 / 0.535 / 0.806 | 0.943 / 0.488 / 0.774 | 1.003 / 0.829 / 0.826 | 1.383 / 0.882 / 0.888 |

**Predictions (mine).**
- (O1) on_demand's mean setup_full per run is within a factor of 2 of the cost model's table at every size, for both genomes.
- (O2) Downstream work is unchanged in distribution. Per size and genome, mean polynomials per run under on_demand are within ±5% of enumerate's, and mean official ops excluding setup_full are within ±5%.
- (O3) qs + lc 1.4 on_demand / enumerate matches the projection column within ±0.04 under each pricing at each size. Official barely moves (0.89–0.95); ruint falls to 0.39–0.63, Montgomery to 0.70–0.85.
- (O4) **The new genes' advantage survives only under the calibrated pricings, and shrinks to ~15%.** With both on_demand, new/old is 0.80–0.90 under ruint and Montgomery at every size, and official is 1.00–1.20. So the robust ratio new/old is above 1 at 72–90 bits (official binds), and the new genes lose on the robust score at 72–90.
- (O5) N51-0917's calibrated lead over qs + lc 1.4 mostly disappears. Both on_demand, its ruint ratio is 0.85–0.95 at 78–84 bits, against 0.42–0.51 under enumerate.
- (O6) The replacement rule (R2) fails again. The official intervals at 54–72 bits stay above 0, because official barely moves.
- (O7) The balanced control's budgets stay 0 under on_demand.
- (O8) Gate against the frozen reference (R1): every on_demand genome passes at every size, because each is cheaper than or close to qs + lc 1.4 enumerate per band under the calibrated pricings, and within 1.2x official. The exception is N51-0917, which fails on official (above 1.5x per band at 72–84 bits, as already under enumerate).
- (O9, stated only, not run) Under an on_demand reference, qs costs 40–60% less under ruint at 78–96 bits. Pre-stage spending is then relatively dearer: allocation A's robust ratio against qs alone rises (gets worse) at 78–96, and the robust-optimal pre-stage budgets shrink.

**Outside predictions (DeepSeek, via the user; recorded as given).**
- (D1) The new-gene gain over qs + lc 1.4 falls from ~1.40x to 1.10–1.20x at 84 bits after the fix. *Scoring, fixed now:* the 1.40x was a pipeline gain at 84-bit mixed (A's budgets). The pipeline is not rerun here, so D1 is scored on R1's 84-bit qs-alone result: held if old/new with both on_demand lies in 1.10–1.20 under the binding (robust) pricing. It is also reported per pricing.
- (D2) On-demand A loses at most 5% yield against enumerate at the same A size. *Scoring:* held if, per size and genome, mean polynomials per run under on_demand are at most 1.05x enumerate's. Relations needed per run are the same, so more polynomials means less yield.
- (D3) ECM budgets shrink when qs gets cheaper. Scored when the pipeline is re-solved with an on_demand reference (not in this brief).
- DeepSeek's A-pool constraints (primes > 2000, s > 3) are **not** adopted. They come from much larger factorizations and do not fit 72–96 bits, where the pool sits at 130–2,600 and s is 3 or 4.

### On-demand A: amendment after acceptance (before any measurement), cost model first

**Failure found by the acceptance run** (`evolve/ondemand_accept.py`, first version). The identity test held on 58/58 runs. But on_demand with the new genes missed one 89-bit map number (547073454933842939659158479) where enumerate succeeds on its first multiplier:
- All four multipliers (kc = 4) filled the ledger, yet none of 14–32 dependencies split N. Python and lampcore agree on the miss and its 5,554,055 ops.
- A second run (96 bits, new genes) needed 3 multipliers under on_demand.
- **Mechanism, measured on the miss:**
  - all 180 relations are valid modulo N, and there are no duplicate relations;
  - but the dependencies are single relations whose exponent vector is already all even, so X ≡ ±Y by construction.
- **Why.** on_demand's early A's share s − 1 primes. For example (331, 359, 373, 379), (331, 359, 373, 383) and (331, 359, 373, 389): the prefix order holds the closest primes fixed. Every polynomial samples u = Ax + B over about the same range, ±sqrt(2kN). A u with u² ≡ kN modulo the lcm of two A's that differ in one prime is therefore found by both families, about once per 2/e candidates for the differing prime e.
- The ledger dedupes full relations by |u|, but a repeated *partial* (large-prime) relation is combined with its own twin. That gives u² with a doubled vector: a trivial relation. Enough of them use up the ledger's surplus rows.
- Enumerate's best-first order spreads its A's over the pool, which makes this rare (no misses on the 2,880 map numbers). The ledger's self-combination weakness is left as it is, because changing it would change enumerate's counts, and so the frozen reference.

**Amended on_demand rule** (it replaces step 5, the dedupe, of the rule above). A candidate that passes the target check is accepted only if it **shares at most s − 2 primes with every A already used** in this attempt. The usual SIQS precaution, as commonly described, is that A's should not differ in a single prime.
- A duplicate shares s primes, so the old dedupe is subsumed.
- Two A's sharing at most s − 2 primes produce the same u only if u satisfies the roots modulo at least two further primes, about 1/40,000 per pair at these sizes.
- Steps 1–4 and 6–8 are unchanged.

**Amended charges** (replacing the dedupe row): for a candidate that passes the target check, **s small ops per A already used** (comparing two s-tuples of small primes), as setup_small. Every other charge is as before: s + 1 full ops and P − (s − 1) small ops per candidate.
- *Expected setup_full:* unchanged per candidate. Candidates per A used rise somewhat, because more are rejected for overlap.
- *Expected extra setup_small:* about s·a_count²/2 ≈ 200–600 small ops per run, priced 0.31 ruint and 1.14 Montgomery. That is under 1% of qs's calibrated cost at 72 bits and less above.

**Predictions O1–O9 and D1–D3 stand as written.** They were written for on_demand before any measurement. No measurement had run; the failure was found by the acceptance tests. The trace field `od_small` now counts the overlap comparisons in place of the dedupe lookups. The identity test's selection charge for on_demand is (s + 1)·od_cands + od_small, as before.

**Added to acceptance:** (4) under on_demand on all 2,880 map numbers (lampcore), report misses and multiplier retries, beside enumerate's. A run that needs more multipliers than under enumerate is reported, not hidden.

### On-demand A: second amendment after acceptance (before any measurement), cost model first

**Failure found by the second acceptance run** (the overlap rule above):
- No misses on the 2,880 map numbers, but 8 of 180 sampled on_demand runs needed a second multiplier (under enumerate: 0 of 180). They are at 83–96 bits, across all three genomes.
- **Mechanism, measured:** in each, the first attempt used all 378 prefixes (s = 3) after accepting only 6–9 A's. The ledger was still short (32–154 of ~165 relations), so the polynomials "ran out" and the next multiplier was tried, paying again.
- Each prefix offered only its single nearest last prime. Once an A {a, b, c} is used, any prefix containing two of its primes, and any completion landing on such a pair, is rejected, so the supply collapses at s = 3.
- The trivial-relation count in those first attempts was 0, so the overlap rule did its job. This is a separate failure.

**Amended rule, version 2** (it replaces steps 3–5). For each prefix, in the same order:
- (a) **Prefix check.** If the prefix already lies within a used A (it shares s − 1 primes with it), skip the prefix: no completion can pass.
- (b) A′ = product of the prefix and t′ = target / A′, as before.
- (c) **Try last primes in order of closeness to t′.** Each try takes the closest remaining pool prime not in the prefix and forms A = A′·last.
  - If it fails the target check (|log₂(A/target)| > 0.25), stop this prefix: every later prime is farther, and |ln(last/t′)| = |ln(A/target)| exactly.
  - If it passes, compare with every used A. If it shares at most s − 2 primes with each, accept it, yield it, and move to the next prefix (the prefix now lies within a used A).
  - Otherwise try the next prime.
- Exhaustion and s = 1 are as before.

**Charges, version 2:**

| | ops | type |
|---|---|---|
| prefix check | (s − 1) per used A | setup_small |
| A′ (prefixes passing the check) | s − 2 multiplies | setup_full |
| t′ = target / A′ | 1 | setup_full |
| each try: finding the closest remaining prime | 1 per remaining pool prime scanned | setup_small |
| each try: A = A′·last | 1 multiply | setup_full |
| each try: target check | 1 | setup_full |
| each try passing the target check: overlap comparison | s per used A | setup_small |

- *Type split:* setup_full = (s − 1)·combos [enumerate] + (s − 1)·od_prefixes + 2·od_cands [on_demand] + 2s·a_count.
- *Trace fields:* `od_prefixes` (prefixes past the check), `od_cands` (tries) and `od_small` (all small selection ops).
- With one try per prefix this reduces to version 1's s + 1 full ops per candidate.
- *Expected setup_full:* still of order 100–300 per run against 6,600 / 107,960, since each accepted A takes a few prefixes and tries.

The predictions stand as written; the acceptance tests and their checks are unchanged. The identity test's on_demand selection charge is (s − 1)·od_prefixes + 2·od_cands + od_small.

### On-demand A: third amendment after acceptance (before any measurement), cost model first

**Failure found by the third acceptance run** (version 2):
- 2 of 180 sampled on_demand runs still needed a second multiplier (enumerate: 0): the new genes at s = 3, at 84 and 89 bits. Both first attempts used every prefix after accepting only 9 and 14 A's (ledger 101/160 and 152/178 relations).
- **Mechanism, measured on the 84-bit case:** it is the top-of-base case. q = 1,866 lies just under the largest factor-base prime (1,877), so the whole pool (1,493–1,877) lies below q. Only 229 of the 3,276 triples are within the 0.25 target check, and nearly all of those use the same few largest primes. Under "share at most one prime", greedy selection finds only 9.
- Enumerate copes by letting its A's share primes.

**Amended rule, version 3:** two passes over the prefixes.
- *Pass 1* is version 2 exactly: share at most s − 2 primes with every used A, with the prefix check.
- *Pass 2* runs only if pass 1 exhausts its prefixes. It walks them again in the same order, with no prefix check, and accepts any try that passes the target check and is not an A already used (it shares at most s − 1 primes with each).
- Pass 2 can bring back the trivial-relation risk of version 1, but only where pass 1 has run out, and it never comes first.
- Exhaustion of pass 2 ends the attempt, as before.

**Charges, version 3:** identical per operation in both passes. Pass 2 re-forms A′, t′ and every try, and pays again: (s − 2) + 1 full per prefix, the scans, 2 full per try, and s small per used A per try passing the check (the duplicate comparison). It has no prefix-check charge, because it has no prefix check. The type split and trace fields are unchanged; `od_pass2` records that pass 2 ran.

**Design data, disclosed.** The three amendments were shaped on the acceptance sample: 180 runs (2 per band per size for two genomes, 1 for N51-0917) and 60 identity runs. The measurement uses all 2,880 map numbers for three genomes, and the replacement-rule populations (1,440 balanced numbers), which the amendments never saw. Retries and pass-2 use are reported there for both modes.

### On-demand A: uncharged sorts (item 3 of the user's follow-up), and a meter finding in the frozen card

**on_demand's prefix-order sort is excluded, for this reason.** `by_q`, the pool sorted by closeness to q (73–109 comparisons per attempt, counted on sample numbers), is exactly the first P entries of the pool-selection sort that both modes already perform. In both cores, `pool` is built by sorting the odd factor-base primes by |ln(p/q)| and keeping the first P. Re-sorting those P primes by the same key recovers that order: no new information is computed. It is a reimplementation convenience, so charging it would charge on_demand twice for an order enumerate also has.

**Meter finding (pre-existing, frozen card; not corrected, for comparability, like the gcd finding).** The qs card's cost model (Stage 6) charges no sorting. Three sorts in phase 3 are uncharged in both cores. Comparisons were counted with a counting comparator on 2 numbers per size per genome at 72–96 bits:

| sort | modes | comparisons per attempt |
|---|---|---|
| pool selection: odd factor-base primes by closeness to q | both | 146–557 (grows with F) |
| the P chosen primes, ascending | both | 27–31 |
| all C(P, s) candidate A's by closeness to target (plus a product and a log per candidate) | enumerate only | ~31,000 (s = 3); 455,000–471,000 (s = 4) |

- **Enumerate is undercharged.** Its up-front cost is larger than its (s − 1)·C(P, s) multiplies, so every on_demand/enumerate ratio measured here understates on_demand's gain.
- The two sorts both modes share would add, if charged as small ops (ruint 0.306, Montgomery 1.137 per comparison), about 55–180 ruint and 200–670 Montgomery units per attempt. That is under ~1.5% of qs's on_demand cost at 72 bits under either pricing, and less at larger sizes.
- Charging sorts would be a meter change: it needs a cost model first, and would change the frozen reference. **For the user to decide;** nothing is changed here.

### On-demand A: results (`evolve/ondemand.py`, `ondemand.out`/`.json`; rule version 3; after acceptance and the full parity suite)

**Acceptance and parity:**
- *Acceptance* (`ondemand_accept.out`): enumerate is unchanged on all 2,880 map numbers; identity 60/60; Python = Rust 180/180; no multiplier retries in the sample; 0 misses on 2,880 numbers for three genomes, both modes.
- *Full parity suite* (`parity_ondemand.out`): qs 3,778 pairs (on_demand pairs included), 0 mismatches; per-type 6,102 pairs, 0 mismatches; mutations 46/46.

**R1, map numbers: ratio to the frozen reference** (qs + lc 1.4, enumerate), official / ruint / Montgomery.

| bits | old on_demand | new enumerate | new on_demand | N51-0917 enumerate | N51-0917 on_demand |
|---|---|---|---|---|---|
| 72 | 0.952 / 0.650 / 0.886 | 1.149 / 0.826 / 0.841 | 1.112 / 0.554 / 0.750 | 1.503 / 0.850 / 0.894 | 1.485 / 0.580 / 0.803 |
| 78 | 0.911 / 0.459 / 0.766 | 1.010 / 0.489 / 0.673 | 0.991 / 0.380 / 0.631 | 1.351 / 0.506 / 0.715 | 1.337 / 0.397 / 0.671 |
| 84 | 0.897 / 0.408 / 0.720 | 0.963 / 0.405 / 0.630 | 0.955 / 0.351 / 0.617 | 1.305 / 0.420 / 0.670 | 1.288 / 0.360 / 0.644 |
| 90 | 0.901 / 0.398 / 0.708 | 1.045 / 0.902 / 0.875 | 0.950 / 0.338 / 0.599 | 1.297 / 0.508 / 0.715 | 1.270 / 0.359 / 0.645 |
| 96 | 0.943 / 0.539 / 0.813 | 1.003 / 0.908 / 0.859 | 0.946 / 0.445 / 0.669 | 1.336 / 0.737 / 0.827 | 1.307 / 0.476 / 0.723 |

**The card itself: on_demand / enumerate, same genes** (robust ratio [paired 95%]; (e) call).
- *qs + lc 1.4:*
  - robust: 0.952 [0.942, 0.962], 0.911, 0.897, 0.901, 0.943 at 72 / 78 / 84 / 90 / 96;
  - ruint: 0.650, 0.459, 0.408, 0.398, 0.539;
  - Montgomery: 0.886, 0.766, 0.720, 0.708, 0.813.
  - Called "on_demand cheaper" under all three pricings at every size.
- *New genes:* robust 0.968, 0.981, 0.992, 0.909, 0.943. Called at every size except 84 on the unseen subset, where official's interval reaches 0.000.
- *N51-0917:* robust 0.988, 0.990, 0.988, 0.980, 0.978; called at every size.
- **On-demand A pays under all three pricings at 72–96 bits** for all three genomes. The size of the gain follows how much each genome spent on enumeration.

**setup_full and its ruint share, on_demand** (enumerate in brackets):
- qs + lc 1.4: 162 / 208 / 249 / 174 / 236 ops [8,506 / 31,224 / 62,714 / 107,952 / 107,969], ruint share 0.2–1.1% [38–61%];
- new genes: 113 / 138 / 260 / 160 / 147;
- N51-0917: 84 / 105 / 139 / 166 / 187.

**Downstream work** (polynomials per run; official ops excluding setup_full):
- On_demand is within −0.9% to +1.8% of enumerate in polynomials for every genome and size.
- It is within −0.4% to +1.7% in non-setup official ops.
- Yield is unchanged within the measured noise.

**The new genes against qs + lc 1.4's genes, both on_demand** (log₂ [paired 95%] as ratios):

| bits | official | ruint | Montgomery | robust | (e) |
|---|---|---|---|---|---|
| 72 | 1.168 | 0.852 | 0.847 | 1.168 [1.146, 1.191] | undecided |
| 78 | 1.087 | 0.828 | 0.824 | 1.087 [1.070, 1.105] | undecided |
| 84 | 1.065 | 0.860 | 0.856 | 1.065 [1.050, 1.081] | undecided |
| 90 | 1.055 | 0.850 | 0.847 | 1.055 [1.042, 1.068] | undecided |
| 96 | 1.003 | 0.826 | 0.823 | 1.003 [0.990, 1.016] | undecided |

- Under enumerate the same comparison was robust 1.149 / 1.010 / 0.963 / 1.045 / 1.003, with ruint 0.826 / 0.489 / 0.405 / 0.902 / 0.908.
- **The new genes' advantage survives only under the calibrated pricings, at a steady ~14–18% at every size.** The 78–84-bit spike (ruint 0.40–0.49) was the enumeration step.
- On the robust score the new genes are now worse than qs + lc 1.4's genes at 72–90 bits (official binds), and tie at 96.

**N51-0917 against qs + lc 1.4's genes, both on_demand:**
- ruint 0.891 / 0.864 / 0.883 / 0.902 / 0.883, against 0.850 / 0.506 / 0.420 / 0.508 / 0.737 under enumerate;
- official 1.56 / 1.47 / 1.44 / 1.41 / 1.39.
- **Allocation B's calibrated lead is mostly the enumeration artifact.** At 84 bits N51-0917's qs went from 0.42 to 0.88 of qs + lc 1.4 under ruint once both stop enumerating. (B's own pipeline was not rerun.)

**Gate against the frozen reference** (per-band intervals):
- PASS for qs + lc 1.4 on_demand and the new genes on_demand at every size.
- N51-0917 on_demand is BORDERLINE at 72 (worst band upper 1.637, lower 1.481, official) and PASS at 78–96, as under enumerate (BORDERLINE at 72).
- No misses anywhere.

**Unseen subset** (the 72 acceptance-sample numbers excluded; 2,808 numbers): every ratio above moves by at most 0.003, the calls are the same, and the gates are the same (`ondemand.out`, "unseen"). The 1,440 balanced numbers of R2 were not seen by any amendment.

**R2, replacement rule (as pre-registered):** new / old, both on_demand, balanced 54–84.
- official: +0.458, +0.365, +0.277, +0.198, +0.122, +0.089 log₂ (all intervals above 0);
- ruint: −0.102 to −0.277; Montgomery: −0.104 to −0.280;
- pooled: official +0.252 [+0.234, +0.269], ruint −0.204, Montgomery −0.211;
- no misses.
- "Never clearly worse": no. "Pooled all three below 0": no. **The rule fails, so qs + lc 1.4 (enumerate) stays the reference.** Changing the reference is the user's separate decision.

**R3, balanced control** (band 42, partition optimizer): budgets td 0, rho 0, pm1 0, ECM 0 with the final qs under enumerate, and **the same under on_demand.** The card change does not move the control.

**Predictions, scored as written.**
- (O1) setup_full within 2x of the cost model's table at every size, both genomes: **missed.** The new genes at 84 bits average 260 against ~110 expected (2.4x). Everything else is within 2x (1.0–1.9x).
- (O2) polynomials and non-setup official ops within ±5%: **held** (within 2%).
- (O3) qs + lc 1.4 on_demand / enumerate within ±0.04 of the projection, official 0.89–0.95, ruint 0.39–0.63, Montgomery 0.70–0.85: **missed as written.** The ±0.04 clause held at every size and pricing (largest deviation +0.033, Montgomery at 72 and 78). The stated ranges fail at 72 bits: official 0.952, ruint 0.650 and Montgomery 0.886 are above their upper ends.
- (O4) new/old both on_demand: ruint and Montgomery 0.80–0.90 at every size, official 1.00–1.20, robust above 1 at 72–90, the new genes losing on robust there: **held.**
- (O5) N51-0917's ruint ratio 0.85–0.95 at 78–84, both on_demand: **held** (0.864, 0.883).
- (O6) the replacement rule fails, with official intervals at 54–72 above 0: **held.**
- (O7) balanced-control budgets stay 0: **held.**
- (O8) every on_demand genome passes the gate at every size, except N51-0917 failing on official at 72–84: **missed.** N51-0917 is BORDERLINE at 72 and PASS at 78–84; the other two clauses held.
- (O9) not run.
- (D1, DeepSeek) the new-gene gain at 84 bits falls to 1.10–1.20x, scored as old/new under the robust pricing, both on_demand: **missed.** The robust ratio is 1.065, so the "gain" is 0.94x: a loss, with official binding. Under ruint and Montgomery alone the gain is 1.16x and 1.17x, inside the range.
- (D2, DeepSeek) on-demand loses at most 5% yield (polynomials per run at most 1.05x enumerate): **held** (at most 1.018x).
- (D3) not scored; the pipeline was not re-solved.

Mine: **5 held (O2, O4, O5, O6, O7), 3 missed (O1, O3, O8), 1 not run (O9).** DeepSeek: 1 held (D2), 1 missed (D1), 1 not scored.

**How the pipeline results that depend on qs's cost would move (not rerun).**
- Under an on_demand reference, qs alone costs 35–60% less under ruint, 11–29% less under Montgomery and 5–10% less official, at 72–96 bits.
- Every pipeline result so far is a ratio to qs + lc 1.4 enumerate. Allocation A, the per-stage budgets by size and allocation B all spend pre-stage ops that are unchanged, against a qs that is now much cheaper under the calibrated pricings, so their robust ratios against an on_demand reference will rise (get worse).
- Their robust optima will move toward smaller pre-stage budgets. The binding pricing was ruint, and ruint's qs cost fell most. Where it fell most (78–90 bits, 0.40–0.46x), ECM's and rho's budgets should shrink most.
- Allocation B's calibrated lead over A should mostly disappear (N51-0917's qs is only 0.86–0.90 of qs + lc 1.4 under ruint once both use on_demand).
- None of this was computed. It needs a re-solve on the maps with the final qs's costs under on_demand, which is the next decision.

## 2026-10-25 — Sort decision (user) and the `sort_charge` option: cost model (before any code)

**Decision (user, Oct 25).**
- The frozen enumerate card stays unchanged, and is recorded as **undercharged**: its sorts were never charged (finding above).
- A new qs option, `sort_charge` (0 or 1; absent means 0), charges every sort in the card. With it off, every count is unchanged.
- **The corrected card is a_mode = on_demand with sort_charge = 1.** Results under it are labelled "corrected card". The frozen reference (qs + lc 1.4, enumerate, sort_charge 0) stays the reference for comparability.

**What is charged when sort_charge = 1.** Sorts are charged by a formula, not by the comparisons a particular sort performs. Python's timsort and Rust's sort_by are different algorithms, and a formula keeps the two cores count for count. A sort of n ≥ 2 items costs **n·⌈log₂ n⌉ comparisons**, the merge-sort upper bound, plus **1 op per key computed** where the key is not already charged. All of these are small-number operations (comparisons of floats or small integers, one log of a small ratio).

| sort (both cores) | n | key ops | phase / type |
|---|---|---|---|
| multipliers ranked by ks score | kc | 0 (each score is already charged: 14 ops per candidate) | mult / mult |
| pool selection: odd factor-base primes not dividing k, by closeness to q | len(pool_all) | n (one log each) | setup / setup_small |
| the P chosen primes, ascending | P | 0 | setup / setup_small |
| enumerate only: all C(P, s) candidates by closeness to target | C | C (one log each; the product is already charged as the (s − 1) multiplies) | setup / setup_small |
| on_demand only: a candidate's s primes, sorted into its key | s, per try passing the target check | 0 | setup / setup_small |

- **Not charged: on_demand's prefix-order sort (`by_q`).** It reproduces the first P entries of the pool-selection sort, which is charged above (reason in the entry above).
- The multiplier sort is charged once per run. The pool sorts are charged once per attempt, so a retry with the next multiplier pays again.
- No new op type is needed: mult and setup_small are already priced (ruint 0.306, Montgomery 1.137), and setup_small remains setup minus setup_full minus setup_euclid.

**Expected size per attempt, from the counted sample** (len(pool_all) 79–299; P = 28 or 32):
- the pool-selection sort costs 80 + 80·7 ≈ 640 up to 300 + 300·9 ≈ 3,000;
- the ascending sort 140 (s = 3) or 160 (s = 4);
- the multiplier sort 160 (kc 32) or 8 (kc 4);
- on_demand key sorts about 6–8 per try, ~100–300 per run.

With the card's other costs, on_demand + sort_charge adds about 1,000–3,600 small ops per run. That is about 2.5% of qs + lc 1.4 on_demand's ruint cost at 72 bits (~0.9% at 96), about 2.7% of its Montgomery cost at 72, and under 1% official at every size. Under enumerate, sort_charge would add ~43,000 (s = 3) or ~611,000 (s = 4) for the candidate sort alone.

**Tests:**
1. sort_charge = 0 reproduces every existing count (the maps, and the acceptance and parity suites unchanged).
2. *Identity:* with sort_charge = 1 against 0, on sample numbers in both modes, every phase is equal except mult and setup. Each differs by exactly the formula, computed from the trace: kc, len(pool_all), P, C and the tries passing the target check.
3. Python = Rust count for count with sort_charge = 1 (parity pairs added).

## 2026-10-25 — Re-solve on the existing maps with the corrected card: plan and predictions (before computing)

**Card.** The final qs is qs + lc 1.4's genes with a_mode = on_demand and sort_charge = 1 (the corrected card; sort_charge accepted: `sortcharge_accept.out`; full parity running). The pre-stage records of every map are unchanged. Every robust ratio uses the same card in numerator and denominator ("corrected" column). The enumerate figures already recorded stay as they are, and are recomputed here only as a check ("enumerate" column).

**What is computed** (map-only; exact per-number composition as in `stopping.py derive2`):
1. Per size, 72 / 78 / 84 / 90 / 96: the robust grid optimum over rho and ECM budgets (td and pm1 off; 1/8-octave grid), its fitness, backward induction under each pricing, the conservative combination, and grid steps from the enumerate optimum.
2. At 84 bits: the four-stage partition optimizer (td, rho, pm1, ECM) for allocation A (final qs + lc 1.4) and allocation B (final N51-0917's qs), both corrected. Each is scored against its own final qs alone, and in the **cross-comparison** against the single reference, qs + lc 1.4 corrected alone. A's original budgets are also scored under the corrected card.
3. The 78/90 transfer test, map-only: the robust optimum of the transferred maps (neighbours 72/84 and 84/96; qs costs rescaled by the frozen Q curve × r_P, with r_P taken from the corrected maps), scored on the 78 and 90 maps against A's budgets, the theory budgets and the local corrected optimum.
   - **A sealed rerun follows only if an optimum moves more than one grid step** (corrected against enumerate, at any size). It would be the genome runs of `stopping.py test` on the 78/90 populations with the corrected final qs.

**Predictions (mine, before computing).**
- (C1) The corrected robust optima shrink against the enumerate optima by ≥ 2 grid steps in at least one stage at each of 78 / 84 / 90 / 96 bits. The ECM budget shrinks or switches off at 84–96. At 72 the change is at most 1 step.
- (C2) Backward induction under ruint equals the corrected robust optimum at all five sizes (as under enumerate at 72/84/96).
- (C3) The robust map fitness of the corrected optimum (against corrected qs alone) is 0.80–0.95 at 84–96 bits (enumerate: about 0.64 at 84), and above 0.95 at 72–78.
- (C4) A's original budgets scored under the corrected card: robust ratio 0.85–1.05 at 84 bits.
- (C5) Cross-comparison at 84: the corrected A is ahead of the corrected B against the single reference by more than under enumerate (B / A larger than before).
- (C6) The transfer at 78 and 90 lands within one grid step of the local corrected optimum in both stages.
- **Scoring rules, fixed now.**
  - *O9* (allocation A's robust ratio against qs alone rises at 78–96; the robust-optimal pre-stage budgets shrink) is scored by C3/C4's quantities: A's budgets at 84, and the per-size optima at 78–96.
  - *D3* (ECM budgets shrink when qs gets cheaper) is scored per size at 78–96, corrected optimum against enumerate optimum: it holds if ECM's budget is smaller or off at every size where the enumerate optimum had ECM on.

**Outside predictions for the re-solve (user, from outside reviews; recorded before running).**
- (G1, Grok) The pre-stages' gain over qs alone shrinks at every size under the corrected card (a lower remaining-pipeline value per success). *Scored:* holds if the corrected robust optimum's fitness against corrected qs alone is higher (worse) than the enumerate optimum's against enumerate qs alone, at each of 72–96 bits.
- (G2, the user's, also DeepSeek's earlier point) The per-size budgets' gain over allocation A does not shrink, and may grow, at 84–96 bits, because A's fixed budgets (rho 5,793 / ECM 32,768) overspend more once the optimal budgets shrink. *Scored:* holds if fitness(per-size optimum) / fitness(A's budgets) under the corrected card is ≤ the same ratio under enumerate, at each of 84, 90 and 96.
- (G3, Grok) Official may become the binding pricing at some sizes once ruint's qs cost falls 35–60%. If so, backward induction under a single pricing no longer equals the robust grid optimum there. *Scored:* the binding pricing of each corrected optimum is reported. G3 holds if official binds at one or more sizes and, at every such size, BI under the binding pricing differs from the robust optimum. It is reported as "not triggered" if official binds nowhere.
- G1 and G2 can both hold.

**Reported per size:** the binding pricing of each genome (per-size optimum, A's budgets, transfer, theory), each pipeline against qs alone and against A with both cards side by side, and whether BI under the binding pricing equals the exhaustive robust optimum.

**More outside predictions for the re-solve (DeepSeek via the user, checked; recorded before running).**
- (D4) After the re-solve, ECM switches off at 84 bits, shrinks but stays on at 96, and stays off below 84; rho shrinks modestly. DeepSeek flags 96 as the case most likely to invert. *Scored on the corrected per-size robust optima:*
  - ECM off at 72, 78 and 84;
  - ECM on at 96 with a budget below the enumerate optimum's (60,097);
  - rho below the enumerate optimum at every size, by 1–4 grid steps.

  Held only if all of these hold; each clause is reported. 90 bits has no clause.
- (D5) Allocation A's calibrated gains over qs alone shrink substantially. The user's correction: the official 2.19x should largely survive, since official qs cost moved only 0.90–0.95x. *Scored on the 84-bit map* (A's budgets, map speed-ups, enumerate against corrected; the sealed figures 2.19 / 1.51 / 1.85x are not rerun):
  - D5 holds if A's ruint and Montgomery speed-ups over qs alone each fall by ≥ 20% (relative).
  - The user's correction holds if the official speed-up falls by ≤ 10%.
- No README wording on A's gains until these are scored.

## 2026-10-25 — Type mix under the corrected card (information only; `evolve/typemix.py corrected`, `typemix_corrected.out`/`.json`)

Both genomes and all ten one-gene swaps were run with a_mode = on_demand and sort_charge = 1 (the corrected card) on the same 2,880 map numbers. **new / old:**
- official 1.164 / 1.085 / 1.064 / 1.054 / 1.002 at 72 / 78 / 84 / 90 / 96;
- ruint 0.848 / 0.825 / 0.859 / 0.850 / 0.825;
- Montgomery 0.843 / 0.821 / 0.856 / 0.846 / 0.822.

**Contributions to new − old** (share of old's total cost; official / ruint / Montgomery; range over 72–96):

| type | official | ruint | Montgomery | gene behind it |
|---|---|---|---|---|
| sieve_update | +0.13 to +0.20 | +0.06 to +0.07 | +0.06 to +0.07 | mc (wider interval) |
| sieve_scan | +0.08 to +0.13 | +0.01 | +0.01 to +0.02 | mc |
| confirm_td | −0.07 | −0.07 to −0.11 | −0.08 to −0.12 | bc (smaller base: fewer primes tried per candidate) |
| la | −0.05 to −0.11 | −0.01 to −0.03 | −0.01 to −0.03 | bc |
| setup_small | −0.02 to −0.03 | −0.07 to −0.09 | −0.07 to −0.09 | bc, mc (fewer sieved primes per A, fewer A's) |
| fb | −0.00 to −0.01 | −0.01 to −0.02 | −0.01 to −0.02 | bc |

setup_full is now under 1% of cost for both genomes.

**One-gene swaps** (ratio to old's total; official / ruint / Montgomery):
- **mc trades official for calibrated cost, as expected.** Old genes with mc 0.734: 1.13–1.17 official, 0.89–0.96 calibrated, at every size.
- **bc does not trade; it wins under all three pricings.** Old genes with bc 0.899: 0.946 / 0.971 / 0.965 (72), 0.903 / 0.902 / 0.901 (78), 0.875 / 0.851 / 0.851 (84), 0.850 / 0.863 / 0.862 (90) and 0.827 / 0.848 / 0.847 (96). Putting bc back to 1.1 in the new genes raises official by 16–23%. DeepSeek's account (mc and lc, no bc) misses the largest gene.
- **kc: the new genes' kc 4 loses under all three pricings under the corrected card.** The new genes with kc 32: 1.084 / 0.794 / 0.788 (72), 1.024 / 0.787 / 0.784 (84) and 0.959 / 0.776 / 0.773 (96), each below the new genes' own ratios. Old genes with kc 4 are worse under all three. Under enumerate, kc 4 helped by keeping kN, and so s, low; that reason is gone.
- **lc trades the other way at 90–96.** The new genes' lc 1.661 against 1.4: lc 1.4 raises official (1.06–1.34) but lowers calibrated cost at 84–96 (0.75–0.85). Old genes with lc 1.661 are worse under all three at every size (1.08–1.13 official, 1.13–1.26 calibrated).
- **tc:** old genes with tc 1.104 are neutral on official (0.97–1.02) and lower calibrated cost from 78 up (0.87–0.95).

**Reading, information only (not a verdict, and not a new idea; this is parameter tuning).**
- Under the corrected card the official-for-calibrated trade is mc's, partly offset by bc.
- qs + lc 1.4's genes with bc 0.899 alone are cheaper than qs + lc 1.4 under all three pricings at every size on these numbers (0.83–0.97; 0.83–0.90 at 78–96), and the new genes with kc 32 are cheaper than the new genes everywhere.
- These are post hoc observations on the map numbers. A replacement claim needs its own pre-registered test on fresh numbers, and the next search over the qs genes (the size-scaling test) should run on the corrected card. It should not inherit the enumerate-era winners' kc.

### Re-solve with the corrected card: results (`evolve/resolve.py map` / `sealed`; `resolve.out`, `resolve_sealed.out`, `.json`)

**Per-size robust grid optimum** (rho, ECM; td and pm1 off). Fitness is against the same card's qs + lc 1.4 alone; "A" is A's fixed budgets (rho 5,793, ECM 32,768) on the same map.

| bits | enumerate: optimum (fitness) | corrected: optimum (fitness) | grid steps moved | A's budgets: enum / corr | optimum / A: enum / corr | binding (all) |
|---|---|---|---|---|---|---|
| 72 | rho 3,158, ECM off (0.817) | rho 1,579, ECM off (0.869) | rho 8 | 1.126 / 1.569 | 0.726 / 0.554 | ruint |
| 78 | rho 5,793, ECM off (0.745) | rho 5,312, ECM off (0.865) | rho 1 | 0.825 / 1.333 | 0.903 / 0.649 | ruint |
| 84 | rho 5,793, ECM 32,768 (0.641) | rho 5,793, ECM off (0.793) | ECM on → off | 0.641 / 0.989 | 1.000 / 0.802 | ruint |
| 90 | rho 9,742, ECM 46,341 (0.633) | rho 10,624, ECM off (0.781) | rho +1, ECM on → off | 0.789 / 1.021 | 0.802 / 0.764 | ruint |
| 96 | rho 12,634, ECM 60,097 (0.627) | rho 12,634, ECM off (0.729) | ECM on → off | 0.740 / 0.846 | 0.847 / 0.861 | ruint |

- **ECM switches off at every size under the corrected card.** The enumerate card's ECM budgets at 84–96 bits were bought by qs's enumeration overcharge under ruint.
- ruint binds for the optimum and for A's budgets at every size under both cards.
- **Backward induction under the binding pricing (ruint) equals the exhaustive robust optimum at all five sizes, under both cards.** The conservative combination still undershoots rho by up to 8 steps.
- **A's fixed budgets are now no better than qs alone** at 84 (0.989), and worse at 72, 78 and 90 (1.57, 1.33, 1.02). The corrected per-size optimum beats A by 14–45%.

**A's speed-up over qs alone at its own budgets** (map; enumerate → corrected):
- official: 2.66 → 2.60, 2.02 → 1.98, 2.22 → 2.21, 1.51 → 1.50, 1.58 → 1.57 at 72 / 78 / 84 / 90 / 96;
- ruint: 0.89 → 0.64, 1.21 → 0.75, 1.56 → 1.01, 1.27 → 0.98, 1.35 → 1.18;
- Montgomery: 1.66 → 1.56, 1.62 → 1.46, 1.90 → 1.75, 1.40 → 1.34, 1.49 → 1.46.

The official gains survive almost intact. The ruint gains largely vanish.

**Allocations at 84 bits** (four-stage optimizer; tuning numbers):
- *Enumerate:* A = (td 0, rho 5,793, pm1 0, ECM 32,768), fitness 0.641; B = (rho 5,793, ECM off), 0.792. Against the single reference: A 0.641, B 0.896; B / A 1.399.
- *Corrected:* A = (rho 5,793, ECM off), 0.793; B = (rho 5,793, ECM off), 0.806. **The two allocations now have the same budgets** and differ only in the final qs. Against the single reference: A 0.793 (0.691 / 0.793 / 0.717), B 0.985 (0.985 / 0.713 / 0.643); B / A 1.241.
- B still loses on the robust score: N51-0917's qs costs 1.4x official.

**Transfer test at 78 / 90.**
- *Map-only:*
  - 78: TRANSFER (3,158, off), 0.869, against the local optimum (5,312, off), 0.865 (6 rho steps apart; the landscape is flat).
  - 90: TRANSFER (12,634, off), 0.785, against the local (10,624, off), 0.781 (2 steps).
  - Optima moved more than one grid step (72 rho; ECM at 84 / 90 / 96), so the sealed rerun ran.
- *Sealed rerun* (genome runs on the 78/90 populations, final qs corrected; 560 / 640 numbers; robust fitness [95%]; gate with per-band intervals):

| | 78, vs corrected qs alone | 78, vs frozen reference | 90, vs corrected qs alone | 90, vs frozen reference |
|---|---|---|---|---|
| TRANSFER (corrected maps) | 0.871 [0.852, 0.889] PASS | 0.707 PASS | 0.786 [0.769, 0.803] PASS | 0.597 PASS |
| TRANSFER (enumerate maps) | 0.870 PASS (budgets (5,793, off)) | 0.642 PASS | 1.040 FAIL (ECM 65,536) | 0.424 PASS |
| A | 1.334 FAIL (worst band upper 2.37) | 0.626 PASS | 1.022 FAIL (upper 1.57) | 0.602 PASS |
| theory | 1.253 FAIL | 0.674 PASS | 1.047 FAIL | 0.425 PASS |

- **TRANSFER (corrected) against A, against corrected qs alone:**
  - at 78: robust −0.616 [−0.673, −0.557] log₂, but official +0.611 and Montgomery +0.211 favour A, so (e) is undecided;
  - at 90: robust −0.379 [−0.419, −0.337]; ruint −0.379 and Montgomery −0.109 favour TRANSFER; official −0.011 [−0.063, +0.043]. (e) is undecided (official ties).
- **Every pipeline with ECM on fails the gate against corrected qs alone at 78 and 90.** Only the rho-only pipelines pass.
- Against the frozen reference everything passes: that comparison credits the pipeline with the enumeration overcharge.

**Predictions, scored as written.**
- (C1) Optima shrink by ≥ 2 steps in one or more stages at each of 78–96; at 72 at most 1 step: **missed.** At 78 rho moved 1 step and ECM stayed off. At 72 rho moved 8 steps. 84–96 held (ECM off).
- (C2) BI under ruint = corrected robust optimum at all five sizes: **held.**
- (C3) Corrected optimum fitness 0.80–0.95 at 84–96 and above 0.95 at 72–78: **missed** (0.793 / 0.781 / 0.729; 0.869 / 0.865). Pre-stages still pay more than I predicted.
- (C4) A's budgets 0.85–1.05 at 84 under the corrected card: **held** (0.989).
- (C5) B / A cross larger than under enumerate: **missed** (1.241 against 1.399). B's calibrated edge disappeared, but so did A's ECM spending.
- (C6) Transfer within one grid step of the local corrected optimum at 78 and 90: **missed** (6 and 2 rho steps; robust fitness within 0.004 of the local optimum at both).
- (O9) A's robust ratio against qs alone rises at 78–96, and the robust-optimal pre-stage budgets shrink: **held** for A's ratio (0.825 → 1.333, 0.641 → 0.989, 0.789 → 1.021, 0.740 → 0.846). The optimal total pre-stage budget shrinks at every size because ECM switches off, though rho itself is 1 step larger at 90.
- (D3) ECM budgets shrink or switch off wherever the enumerate optimum had ECM on (84, 90, 96): **held** (off at all three).
- (G1) The pre-stages' gain over qs alone shrinks at every size: **held** (optimum fitness higher at all five sizes).
- (G2) The optimum's gain over A does not shrink at 84–96: **missed as written.** It held at 84 (0.802 against 1.000) and 90 (0.764 against 0.802), but not at 96 (0.861 against 0.847).
- (G3) Official becomes binding somewhere: **not triggered.** ruint binds at every size for every genome, and BI equals the optimum everywhere.
- (D4) ECM off at 72 / 78 / 84, on but smaller at 96, rho below enumerate by 1–4 steps everywhere: **missed.** The ECM-off clauses held at 72–84, but ECM is also off at 96 (DeepSeek's flagged case inverted). rho is lower by 8 at 72 and 1 at 78, equal at 84 and 96, and 1 step higher at 90.
- (D5) A's ruint and Montgomery speed-ups fall by ≥ 20% at 84: **missed.** ruint fell 35%, Montgomery only 7.9%. *The user's correction* (official falls by ≤ 10%): **held** (−0.6%).

Mine: 2 held (C2, C4), 4 missed (C1, C3, C5, C6); O9 held. Outside: D3 and G1 held; G2, D4 and D5 missed; G3 not triggered; the user's correction held.

**What this changes.**
- Under the corrected card the sequential pipeline at 72–96 bits is rho-only, with a rho budget growing with size (1.6k → 12.6k ops), at 0.73–0.87 of qs alone (ruint binding).
- ECM's role in every earlier allocation came from the enumerate card's overcharge.
- Allocation A, the per-stage budgets "PASS at 78/90" and allocation B's calibrated lead all stand as recorded under the frozen card and labelled so. Under the corrected card, A and every ECM-on genome fail the gate at 78 and 90.

## 2026-10-25 — Outside check: P-1M, a textbook pipeline model for a p-1 stage (user; information only, not the meter)

The script was written and first run by the user in their own workspace, and is saved verbatim as `evolve/outside_pm1_model.py`. It was rerun here (`outside_pm1_model.out`, ~1 min, sympy + numpy).
- **The model:** official pricing only, 84-bit N, p in bands 16–42, equally likely. The pipeline is rho (Rayleigh catch law; Brent 1.57x; 1.56 ops per step), then p-1 stage 1 (cost ⌈log₂ lcm(1..B)⌉), then ECM (stage-1 model: group order 12m, m B1-powersmooth, 11 ops per bit of lcm(1..B1)), then qs at a fixed cost Q.

**Reproduction** (the user's figures in brackets):
- *Part 1* (rho 5,793 and ECM 32,768 fixed; cost with p-1 / without):
  - Q = 300k: best 0.876 at 2^14 [0.877], 2^16 1.034 [1.040];
  - Q = 550k: best 0.840 at 2^14 [0.841];
  - Q = 1M: best 0.800 at 2^15 [0.803].
- *Part 2* (rho, B, ECM and B1 jointly optimized; cost / qs alone):
  - Q = 100k: 0.708 → 0.669 with p-1, B 4,096 [same];
  - 300k: 0.597 → 0.546, B 16,384 [0.547];
  - 550k: 0.500 → 0.458, B 16,384 [same];
  - 1M: 0.401 → 0.363, B 32,768 [0.364].
- **Reproduced within 0.006.** Sympy's randprime has its own random source, so rates differ by about 1% between runs. Wolfram Language reproduced Part 2 independently (user): 0.708 / 0.676, 0.597 / 0.546 and 0.515 / 0.460 on a coarser grid.

**Known failure, recorded.** The joint optimum never lands near allocation A. It picks rho 11k–33k, with ECM either off or at 131k–262k (with B1 800–1,600). Likely causes: ECM is modelled as stage 1 only at 11 ops per bit, and pricing is official only. The model also takes qs's cost as a constant per number.

**Amended prediction, P-1M (the user's; direction only).**
- A moderate-bound p-1 stage (B ~ 2^12–2^15, searched) between rho and ECM switches on at 84–96 bits under official pricing.
- Size unknown: the model says 5–11% once rho and ECM are re-optimized, and 12–20% with them fixed.
- It may stay off under ruint.
- Mechanism: p-1 costs about 1 op per exponent bit against ECM's 11 in this model, so a more efficient real ECM card shrinks the case.

**Lesson (user):** textbook catch-rate models give direction; maps from the real cards give magnitudes.

**Queued p-1 map check, amended.** Search B = 2^8 … 2^15 (not only 2^8–2^10), with rho and ECM re-optimized jointly, on the corrected card, on the 72–96 maps. The re-solve above adds a condition: under the corrected card ECM is already off at every size, so the check is p-1 between rho and qs, with ECM still searched. Predictions go in NOTES before the map is extended. The earlier P1/P2 (mine) and the user's revised prediction stand as written; they were stated for the enumerate-era pipeline.

## 2026-10-25 — Per-pricing optima under the corrected card: is "ECM off" a ruint-only result? (predictions before reading)

**Disclosure.** Each pricing's own grid optimum equals backward induction under that pricing (exact composition), and `resolve.json` already stores those as `bi_per_pricing` for both cards. They were written by the re-solve and have not been read; these predictions are written before reading them. A short script, `evolve/per_pricing.py`, prints them beside the robust optimum, with each pricing's fitness, from the same maps.

**Predictions.**
- *The user's:* ECM stays on at 84–96 under official, probably on under Montgomery at 90–96, and off under ruint.
- *Mine (Q1):*
  - under official, ECM is on at every size, 72–96 (under enumerate the official optimum had ECM at 285,870–1,048,576 everywhere, and official qs cost moved only 0.90–0.96x);
  - under Montgomery, ECM is on at 84–96 with a smaller budget than under enumerate (808,563 at 84; 480,774 at 96), and on or off at 72–78;
  - under ruint, ECM is off at every size.
  - So "ECM off" is a ruint-only result.

**Note on the binding pricing (the user's; recorded now).** Under the robust score ruint binds at every size, for every pipeline, under both cards. Its 27 ns generic 256-bit multiply (against Montgomery's 7.4 ns) therefore decides every pipeline verdict so far. Whether ruint should stay a binding pricing is the user's decision; nothing is changed here.

**Recorded for the queued p-1 map check.** P-1M's direction was stated for official pricing. Under the robust score, with ruint binding, expect p-1 to stay off: ruint already priced the forced-on p-1 card at 2.12x in the partition study.

### Per-pricing optima: results (`evolve/per_pricing.py`, `per_pricing.out`/`.json`)

Each pricing's own grid optimum under the corrected card, with its cost against corrected qs alone (official / ruint / Montgomery):

| bits | official alone | Montgomery alone | ruint alone (= robust) |
|---|---|---|---|
| 72 | rho 1,448, ECM 285,870: 0.211 / 2.040 / 0.596 | rho 1,448, ECM 185,364: 0.214 / 2.024 / 0.596 | rho 1,579, ECM off: 0.783 / 0.869 / 0.804 |
| 78 | rho 3,158, ECM 881,744: 0.208 / 2.215 / 0.638 | rho 1,579, ECM 92,682: 0.303 / 1.685 / 0.598 | rho 5,312, ECM off: 0.709 / 0.865 / 0.748 |
| 84 | rho 3,158, ECM 1,048,576: 0.160 / 1.886 / 0.535 | rho 3,158, ECM 311,744: 0.189 / 1.733 / 0.525 | rho 5,793, ECM off: 0.691 / 0.793 / 0.717 |
| 90 | rho 5,793, ECM 1,048,576: 0.159 / 1.917 / 0.547 | rho 5,793, ECM 220,436: 0.271 / 1.401 / 0.521 | rho 10,624, ECM off: 0.673 / 0.780 / 0.699 |
| 96 | rho 5,793, ECM 1,048,576: 0.156 / 1.551 / 0.466 | rho 4,871, ECM 404,281: 0.217 / 1.209 / 0.437 | rho 12,634, ECM off: 0.657 / 0.729 / 0.675 |

- **"ECM off" is a ruint-only result.** Under official alone the optimum puts a large ECM budget (up to the 2^20 grid edge) at every size, at 0.16–0.21 of qs alone. Under Montgomery alone ECM stays on at every size (93k–404k, below the enumerate-card Montgomery optima of 185k–809k), at 0.44–0.60.
- Each of those optima costs 1.2–2.2x qs alone under ruint, which is why the robust score rejects them.
- Under the enumerate card the pattern was the same, except that ruint itself kept ECM on at 84–96.
- **Scored:**
  - the user's prediction (ECM on at 84–96 under official, probably on under Montgomery at 90–96, off under ruint): **held**;
  - mine (Q1: official on everywhere; Montgomery on at 84–96 with smaller budgets than under enumerate; ruint off everywhere): **held.**
- So the robust verdict "rho then qs" is the ruint verdict. With a Montgomery-class multiply, ECM belongs in the pipeline; under the official count, a much larger ECM budget does.

## 2026-10-25 — qs-gene size-scaling test on the corrected card: design (before any run)

The design is the queued test (PLAN, "Queued: size-scaling test for the qs genes"), moved to the corrected card with the user's two cautions: range over kc (the old winners' kc 4 now loses), and tune under the per-size rho-only pipeline. No meter change: the card is the accepted corrected card. Code: `evolve/sizescale.py`.

- **Card:** the final qs with a_mode = on_demand and sort_charge = 1.
- **Pipeline per size:** rho at that size's rho-only robust budget, then qs; td, pm1 and ECM off. The budgets are 72: 1,579; 84: 5,793; 96: 12,634 (corrected re-solve). The 54-bit budget comes from a new 54-bit map (seeds 9500000 + 100 pb + 54, 80 per band, bands 16/20/24/27), solved the same way. It is a design input, computed before the predictions.
- **Fitness (c):** the robust ratio against qs + lc 1.4's genes alone under the corrected card, on the same numbers; a miss scores 1e9.
- **Search:** qs genes only, over Run 8's bounds: kc 1–32 (integer), bc 0.7–3.0, mc 0.05–12 (log), tc 1.0–3.5, lc 1.0–2.0. TPE with the tpe-tuned settings (10% random start-up, multivariate), seeds 0–3, 200 trials each, per size.
- **Tuning numbers:** 24 per band (PLAN's fixed-tuning-set rule), seeds 9300000 + 100 pb + bits. Bands: 54: 16/20/24/27; 72: 16–36; 84: 16–42; 96: 16–48 (balanced band = bits/2).
- **Frozen genome per size:** the best of its four seeds on the tuning numbers.
- **Sealed:** 80 per band, seeds 9400000 + 100 pb + bits, run once. Four frozen genomes plus qs + lc 1.4's genes and the new genes (both on the corrected card), each run in every size's pipeline, so 4 × 6 cells. Each cell reports:
  - per-pricing ratios and the robust ratio [paired 95%], with the binding pricing;
  - two references: qs + lc 1.4 corrected alone (primary) and the frozen reference (qs + lc 1.4, enumerate);
  - the gate with per-band intervals;
  - paired comparisons against qs + lc 1.4's genes in the same pipeline;
  - misses.
- **Trend test** (DeepSeek's prediction: mc and lc up, kc down with size). Per gene, the four seeds' best values per size. A trend counts as monotone only if the per-size medians move monotonically **and** the 54-bit and 96-bit seed ranges do not overlap. Spearman over the 16 points is reported beside it. The landscape is a plateau, so the seed spread is the interval.
- **Seeds checked unused:** 9300000+, 9400000+ and 9500000+ appear nowhere else in the repo.

**54-bit design input** (`sizescale.py map54`, `sizescale_map54.json`; 320 numbers, bands 16/20/24/27):
- The rho-only robust optimum is **rho 0: qs alone.** The two-stage optimum is also (0, 0).
- qs + lc 1.4 corrected alone averages 25,930 official, 3,641 ruint and 11,805 Montgomery.
- A rho budget of 362–5,793 lowers official and Montgomery cost (official 0.99 → 0.57) but raises ruint (1.06–1.49), so ruint rejects it.
- The 54-bit pipeline in this test is therefore qs alone.

**Predictions (mine, before tuning).**
- (S1) At every size, the frozen tuned genome beats qs + lc 1.4's genes in the same pipeline on the sealed numbers: robust log₂ interval below 0, by 5–15% at 72–96 and 0–10% at 54.
- (S2) The frozen genomes have kc ≥ 8 at 72–96.
- (S3) The frozen genomes have bc ≤ 1.0 at 84–96.
- (S4) DeepSeek's trend (mc and lc up, kc down with size) is not borne out: at most one of mc, lc and kc meets the monotone rule (medians monotone in the predicted direction and the 54/96 seed ranges separated).
- (S5) Cross-size:
  - in each sealed size, the genome tuned at that size is within 3% (robust) of the best of the four tuned genomes there;
  - the 54-tuned genome loses ≥ 5% at 96, and the 96-tuned genome loses ≥ 5% at 54.
- (S6) ruint binds for every tuned pipeline at 72–96. At 54 (qs alone against qs + lc 1.4's genes alone) official binds.
- (S7) Every frozen genome passes the gate against the corrected reference at its own size.

**Outside prediction (DeepSeek, queued with the test):** the optimum shifts monotonically with size, with mc and lc up and kc down. It is scored by the trend rule in the design above.

**Size-scaling test: paused (Oct 25).** The user asked that it not start until the scoring rule is decided (PLAN, "PENDING DECISION: which pricing decides").
- The tuning run had already started. It was stopped before any result was written: its output file was empty and was deleted, and no `sizescale_tune.json` exists. No tuning result has been seen.
- The design, the 54-bit design input and predictions S1–S7 stand as written, under the current robust rule. If the rule changes, the user's caveat (2) applies: new predictions are written after the change, before the test runs.

## 2026-10-25 — Decision (user): two tracks; the size-scaling test on both

**The rule, from now on** (for tests whose predictions are written after this decision; PLAN, scoring):
- **Track R (ruint decides):** today's robust rule (ruint binds everywhere). Gate: per-band 1.5x under all three pricings.
- **Track M (Montgomery decides):** fitness = Montgomery cost / the reference's Montgomery cost. Gate: per-band 1.5x under Montgomery. ruint and official are reported for every result, and a ruint per-band gate is reported as information only. A Track M winner that fails that gate is labelled "conditional on a fast multiply".
- **Every report** gives both tracks' winners, each priced under the other track's pricing. That cross-pricing is the headline: how much the answer depends on the multiply.
- **Earlier verdicts stay as recorded;** they are Track R by construction.

**The size-scaling test under the rule.**
- *Track R:* predictions S1–S7 were written before this decision, under the robust rule, which is Track R. They stand as written, and the Track R design is the one above (rho-only pipeline per size; qs alone at 54).
- *Track M:* new predictions are written below, before the Montgomery re-solve and before any tuning.
- The tuning budget is the same per track: tpe-tuned settings, seeds 0–3, 200 trials per size, kc 1–32.

**Track M predictions (mine; written after the decision, before the Montgomery re-solve and any tuning).**
- *Known inputs:* the Montgomery-alone optima at 72 / 84 / 96 were already computed by the per-pricing run (1,448 / 185,364; 3,158 / 311,744; 4,871 / 404,281). 54 bits has not been solved under Montgomery.
- (M1) **Budgets.**
  - The Montgomery re-solve reproduces those three optima.
  - At 54 the Montgomery optimum has rho on (≥ 724) and ECM off or at most 2^15.
  - No Montgomery optimum sits at the grid's top edge (2^20).
  - Official sits at the edge at 84, 90 and 96. With the ECM grid widened to 2^22, the official optimum's ECM moves above 2^20 at those sizes.
- (M2) **Genes.** The Track M frozen genomes have kc ≥ 8 at 72–96, and a smaller mc than the Track R frozen genome at the same size. Under Montgomery, small ops cost nearly as much as a full multiply (1.137), so a wide sieve is dearer. No gene meets the monotone rule in Track M either (at most one of mc, lc, kc does).
- (M3) **Gain.** The Track M tuned genome beats qs + lc 1.4's genes in the Track M pipeline by 5–15% under Montgomery at 72–96 (interval below 0).
- (M4) **Gates.** Track M winners pass the Montgomery gate at every size. They fail the ruint per-band gate at 72–96 (every ECM-on pipeline failed it at 78 and 90), so they are labelled "conditional on a fast multiply". The 54-bit winner passes the ruint gate if its ECM is off.
- (M5) **Headline cross-pricing.**
  - PD_M = Montgomery cost of the Track R winner / Montgomery cost of the Track M winner: 1.3–1.6 at 72–96.
  - PD_R = ruint cost of the Track M winner / ruint cost of the Track R winner: 1.6–2.4 at 72–96.
  - Both are at most 1.2 at 54.
  - (From the per-pricing optima with qs + lc 1.4's genes: PD_M 1.35 / 1.37 / 1.54 and PD_R 2.33 / 2.19 / 1.66 at 72 / 84 / 96. The tuned genes should move these little.)
- (M6) **The pipeline decides, not the genes.** For each gene and size, the Track R and Track M seed ranges overlap.

**Definitions, fixed now.** The *winner* of a track at a size is the best, by the track's fitness on the sealed numbers in the track's pipeline at that size, of that track's four tuned genomes plus qs + lc 1.4's genes and the new genes. PD_M and PD_R are computed from the two winners' sealed mean costs.

### Two tracks: per-size pipelines (`sizescale.py msolve`, `sizescale_msolve.out`, `sizescale_tracks.json`; corrected maps)

Per-pricing grid optima (rho, ECM; td and pm1 off), fitness against corrected qs + lc 1.4 alone:

| bits | official | ruint (= robust = Track R) | Montgomery (= Track M) |
|---|---|---|---|
| 54 | rho 1,218, ECM 60,097 (0.343) | qs alone (1.000) | rho 3,158, ECM 6,317 (0.759) |
| 72 | rho 1,448, ECM 285,870 (0.211) | rho 1,579, ECM off (0.869) | rho 1,448, ECM 185,364 (0.596) |
| 78 | rho 3,158, ECM 881,744 (0.208) | rho 5,312, ECM off (0.865) | rho 1,579, ECM 92,682 (0.598) |
| 84 | rho 3,158, ECM 1,048,576 [edge] (0.160) | rho 5,793, ECM off (0.793) | rho 3,158, ECM 311,744 (0.525) |
| 90 | rho 5,793, ECM 1,048,576 [edge] (0.159) | rho 10,624, ECM off (0.780) | rho 5,793, ECM 220,436 (0.521) |
| 96 | rho 5,793, ECM 1,048,576 [edge] (0.156) | rho 12,634, ECM off (0.729) | rho 4,871, ECM 404,281 (0.437) |

**The ECM grid widened to 2^22 where an optimum sat at the 2^20 edge** (official at 84, 90 and 96; ECM rerun alone to 2^22 on every number it had not solved by 2^20; same deterministic curves):
- at 84 the optimum stays at ECM 1,048,576 (0.160): 2^20 is interior once the grid extends;
- at 90 and 96 it moves to ECM 2,719,670 (2^21.4): 0.150 at 90 and 0.122 at 96.
- Neither is at the new edge. No Montgomery or ruint optimum is near an edge.

**Track pipelines for the test:**
- Track R: qs alone at 54; rho 1,579 / 5,793 / 12,634 with ECM off at 72 / 84 / 96.
- Track M: (3,158, 6,317), (1,448, 185,364), (3,158, 311,744) and (4,871, 404,281) at 54 / 72 / 84 / 96.

**M1, scored:** **missed as written.**
- Held: the three known optima reproduced; the 54-bit Montgomery optimum has rho on (3,158 ≥ 724) and ECM at most 2^15 (6,317); no Montgomery optimum is at the edge; official is at the edge at 84 / 90 / 96.
- Missed: with the grid widened, official moves above 2^20 at 90 and 96 but not at 84.

### qs-gene size-scaling test, both tracks: results (`sizescale.py tune` / `sealed`; `sizescale_tune.out`, `sizescale_sealed.out`, `.json`)

Corrected card; sealed numbers 80 per band (320 / 480 / 560 / 640 at 54 / 72 / 84 / 96), run once. The reference is qs + lc 1.4 corrected alone; ratios are official / ruint / Montgomery.

**Winners per size** (each is that size's own tuned genome; at 72 the Track M genomes tuned at 54 and 72 tie):

| bits | Track R winner (pipeline): ratios; track fitness [95%]; gate | Track M winner (pipeline): ratios; Montgomery fitness [95%]; Montgomery gate; ruint gate (info) |
|---|---|---|
| 54 | R-tuned@54 (qs alone): 0.963 / 0.948 / 0.928; 0.963 [0.951, 0.976] (official binds); PASS | M-tuned@54 (rho 3,158, ECM 6,317): 0.598 / 1.796 / 0.742; 0.742 [0.694, 0.792]; PASS; FAIL |
| 72 | R-tuned@72 (rho 1,579): 0.762 / 0.772 / 0.699; 0.772 [0.747, 0.799]; PASS | M-tuned@72 (rho 1,448, ECM 185,364): 0.255 / 2.237 / 0.668; 0.668 [0.610, 0.728]; BORDERLINE; FAIL |
| 84 | R-tuned@84 (rho 5,793): 0.618 / 0.618 / 0.539; 0.618 [0.604, 0.635] (official binds by 0.0001); PASS | M-tuned@84 (rho 3,158, ECM 311,744): 0.194 / 1.719 / 0.513; 0.513 [0.472, 0.556]; PASS; FAIL |
| 96 | R-tuned@96 (rho 12,634): 0.525 / 0.530 / 0.475; 0.530 [0.519, 0.541]; PASS | M-tuned@96 (rho 4,871, ECM 404,281): 0.204 / 1.103 / 0.372; 0.372 [0.346, 0.399]; PASS; FAIL |

**Every Track M winner fails the ruint per-band gate: each is "conditional on a fast multiply".**

**Headline: cross-pricing (round 1).** *Label added Oct 25:* these budgets were solved with qs + lc 1.4's genes, and the genes were then tuned inside those fixed budgets. Under Montgomery the tuned Track R genes gained the most (−0.11 to −0.53 log₂), so the Montgomery budgets may move once they are re-solved with tuned genes (round 2). PD_M is the Montgomery cost of the Track R winner over the Track M winner's; PD_R is the ruint cost of the Track M winner over the Track R winner's.

| bits | PD_M [95%] | PD_R [95%] | official, M winner / R winner |
|---|---|---|---|
| 54 | 1.250 [1.171, 1.336] | 1.894 [1.805, 1.986] | 0.621 |
| 72 | 1.045 [0.956, 1.151] | 2.899 [2.647, 3.160] | 0.335 |
| 84 | 1.050 [0.967, 1.143] | 2.783 [2.579, 2.998] | 0.313 |
| 96 | 1.277 [1.188, 1.380] | 2.082 [1.956, 2.209] | 0.389 |

- **The dependence on the multiply is lopsided.** The ruint answer (rho, then a tuned qs) costs only 0–28% more than the Montgomery answer under Montgomery prices; at 72 and 84 the difference is within noise.
- The Montgomery answer (rho, a large ECM budget, then qs) costs 1.9–2.9x more than the ruint answer under ruint prices.
- Under the official count the Montgomery answer is 2.6–3.2x cheaper at 72–96.
- So the Track R winner is the safe choice across multiplies. The Track M winner is much better under official counting, slightly better under Montgomery, and much worse under ruint.

**Tuned genes against qs + lc 1.4's genes in the same pipeline** (track metric, log₂ [95%]):
- *Track R:* −0.054 [−0.073, −0.036] (3.7%), −0.196 (12.7%), −0.377 (23%) and −0.480 (28%) at 54 / 72 / 84 / 96. All three pricings agree at every size, and the Montgomery gain is the largest (−0.11 to −0.53).
- *Track M:* −0.073 (4.9%), −0.009 (0.6%), −0.039 (2.7%) and −0.170 (11%). The official cost rises at 54–84 (+0.02 to +0.32).
- Against the frozen reference (enumerate), the Track R winners are 0.81 / 0.35 / 0.66 (54), 0.74 / 0.53 / 0.65 (72), 0.55 / 0.26 / 0.39 (84) and 0.50 / 0.29 / 0.39 (96). These ratios mostly come from the corrected qs card (on-demand A, sorts charged), not from tuning; the tuning gain is the line above.

**Cross-size** (track fitness of each size's tuned genome, scored at every size):
- *Track R:* each size's own genome is best at its size. The 54-tuned genome is 32% worse than the 96-tuned at 96 (0.699 against 0.530); the 96-tuned is 75% worse at 54 (1.688 against 0.963). The genes matter by size.
- *Track M:* the four genomes are within 1% of each other at 72 and 84, and within 6% at 96. The large ECM budget dominates, and the qs genes matter little.

**Genes** (the four seeds' best per size; frozen = best seed):
- *Track R:*
  - mc rises monotonically (median 0.23 → 0.40 → 0.42 → 0.47), with the 54/96 ranges separated;
  - bc falls to the search's lower bound (0.87 → 0.80 → 0.71 → 0.71);
  - lc falls (1.69 → 1.45–1.52); kc stays 9–32 with no trend.
- *Track M:* mc 0.8–1.3 (2–3x Track R's), bc at the bound (0.70–0.89), lc falls 1.76 → 1.45 (not separated), kc 9–30.
- **Condition: bc sits at the search's lower bound (0.70) in most Track R genomes at 84–96 and most Track M genomes.** These winners are bound-limited. A lower bc bound might do better; that would be a new test with its own predictions.

**Predictions, scored as written.**
- *Track R* (S1–S7, written before the decision):
  - (S1) tuned beats old genes, robust interval below 0, by 5–15% at 72–96 and 0–10% at 54: **missed.** The direction held everywhere, and 54 (3.7%) and 72 (12.7%) were in range. 84 (23%) and 96 (28%) gained more than predicted.
  - (S2) kc ≥ 8 at 72–96: **held** (32 / 23 / 31).
  - (S3) bc ≤ 1.0 at 84–96: **held** (0.704 / 0.711; at the bound).
  - (S4) at most one of mc, lc and kc meets the monotone rule in DeepSeek's direction: **held** (only mc).
  - (S5) own genome within 3% of the best tuned genome at each size, and the 54- and 96-tuned genomes each lose ≥ 5% at the other end: **held.**
  - (S6) ruint binds for every tuned pipeline at 72–96, official at 54: **missed.** At 84 official binds by 0.0001 (0.6180 against 0.6179). The other sizes held.
  - (S7) every frozen genome passes the gate at its own size: **held.**
- *Track M* (M1–M6, written after the decision):
  - (M1) missed (scored above).
  - (M2) kc ≥ 8 (held), mc smaller than Track R's (**missed**: 2–3x larger), no monotone gene (held): **missed.**
  - (M3) tuned beats old genes by 5–15% under Montgomery at 72–96: **missed.** Only 96 (11%) was in range; 72 (0.6%) and 84 (2.7%) were below.
  - (M4) Montgomery gate PASS everywhere, ruint gate FAIL at 72–96: **missed** (72 is BORDERLINE under Montgomery). The ruint clause held; the 54 winner also fails the ruint gate, consistent with its ECM being on.
  - (M5) PD_M 1.3–1.6 and PD_R 1.6–2.4 at 72–96, both ≤ 1.2 at 54: **missed.** PD_M was 1.05 / 1.05 / 1.28 and PD_R 2.90 / 2.78 / 2.08; at 54, 1.25 and 1.89.
  - (M6) the two tracks' seed ranges overlap for every gene and size: **missed** (mc never overlaps at 72–96).
- *Outside:*
  - (DeepSeek) the optimum shifts monotonically with size, mc and lc up, kc down: **missed.** In Track R mc rises, but lc falls and kc has no trend. In Track M no gene meets the rule.

Mine: Track R 5 held, 2 missed. Track M 0 held, 6 missed.

## 2026-10-25 — Size-scaling test, round 2 (two tracks): protocol and predictions (before any run)

**Protocol (user's, with the rules made exact here).**
- **Round 2 tuning.** Gene bounds widened: bc 0.3–3.0 (was 0.7–3.0) and mc 0.01–12 log (was 0.05–12). kc stays 1–32, tc 1.0–3.5 and lc 1.0–2.0. Settings as round 1 (tpe-tuned, seeds 0–3, 200 trials per size, 24 per band tuning numbers, seeds 9300000+), in each track's round-1 budgets. The frozen genome per size is the best seed.
- **Bound hits.** A gene value is reported as a bound hit if it lies within 10% of a bound's value: bc ≤ 0.33 or ≥ 2.7; mc ≤ 0.011 or ≥ 10.8; kc ≤ 1 or ≥ 29; tc ≤ 1.1 or ≥ 3.15; lc ≤ 1.1 or ≥ 1.8.
- **Re-solve.** Per track and size, the two-stage grid optimum (rho, ECM; td and pm1 off) is solved on the corrected maps with that track's round-2 frozen genome as the final qs.
  - Track R minimizes max over pricings of cost / cost of qs + lc 1.4 corrected alone; Track M minimizes Montgomery cost.
  - The ECM grid runs to 2^22 wherever an optimum sits at 2^20, and is widened again if it sits at 2^22.
  - The 54-bit map is `sizescale_map54.json`'s numbers.
- **Round 3** runs only if any budget (either track, any size) moves by more than one 1/8-octave grid step, or switches between off and on. It retunes both tracks once in the re-solved budgets, with the same settings. **It is the cap.**
  - The *final budgets* are then one more re-solve with the final genes, used without further tuning; its movement is reported as "settled" (≤ 1 step everywhere) or not.
  - If round 3 is not triggered, the final genes are round 2's and the final budgets are round 2's re-solve.
- **Sealed scoring on fresh numbers:** seeds 9410000 + 100 pb + bits (checked unused), 80 per band, run once.
  - Per track and size, three rows: (a) the round-1 winner in round-1 budgets; (b) the final winner's genes in round-1 budgets; (c) the final winner's genes in the final budgets.
  - The *final winner* uses round 1's definition: the best by the track's fitness in the track's final pipeline, among that track's final-round tuned genomes (four sizes) plus qs + lc 1.4's and the new genes.
  - Both references; all three pricings; gates as in the two-track rule.
  - **The headline is PD_M and PD_R from row (c), with round 1 beside it** (round 1's PD values were measured on the 9400000 numbers; the (a) rows give them again on the fresh numbers).

**Predictions (the user's, labelled as the user's).**
- (U1) With bc widened, the frozen genomes choose bc 0.45–0.65 at 84–96. The gain over the round-1 genes in the same pipeline is at most 5% under the track's metric.
- (U2) Re-solved with round-2 genes, Track M's ECM budget falls at 72–96, by at least one grid step at two or more of the three sizes. Track R's rho budget moves at most one grid step.
- (U3) Round-2 PD_M is between 1.00 and 1.15 at 72–96.
- (U4) Round-2 PD_R stays between 1.8 and 3.0: the lopsidedness survives.
- *Scoring:* U1's bc clause uses the round-2 frozen genomes of both tracks at 84 and 96. Its gain clause is row (b) against row (a) under the track's metric (sealed), at 84–96. U2 uses the round-2 re-solve. U3 and U4 use row (c) at 72–96, whichever round is final.

**Predictions (mine).**
- (V1) Round-2 Track R frozen genomes have bc 0.45–0.70 at 84–96; Track M's at 0.5–0.75. Row (b) against (a) gains at most 5% in Track R and at most 3% in Track M at 84–96.
- (V2) The Track R re-solve keeps ECM off at 72–96, with rho within one step of round 1. In Track M, ECM falls by ≥ 1 step at two or more of 72 / 84 / 96, and rho stays within 2 steps.
- (V3) Round 3 is triggered by Track M (an ECM move above one step), not by Track R.
- (V4) The final re-solve after round 3, if any, moves every budget by at most one step (settled).
- (V5) Ablation: in Track R most of the change from (a) to (c) comes from genes ((b) against (a)), since its budgets barely move. In Track M at 84–96, the budget part ((c) against (b)) is at least as large as the gene part.
- (V6) PD_M final: 1.00–1.20 at 72–96. PD_R final: 1.8–3.0 at 72–96.
- (V7) Bound hits: one or more final frozen genomes still have kc ≥ 29; no mc lower-bound hit (≤ 0.011) at 72–96.
- (V8) Gates: Track R final winners PASS at every size. Track M final winners pass the Montgomery gate at 84–96 and fail the ruint gate (information) at every size.

### Size-scaling test, rounds 2–3: results (`sizescale2.py`; `sizescale_r2_tune.out`, `sizescale_r2_resolve.out`, `sizescale_r3_tune.out`, `sizescale_r3_resolve.out`, `sizescale_r2_sealed.out`, `.json`)

**Round 2 tuning** (bc 0.3–3.0, mc 0.01–12; round-1 budgets):
- With the bound widened, bc moved below 0.7: Track R 0.57 / 0.53 / 0.48 at 72 / 84 / 96 (frozen), and Track M 0.49–0.66.
- At 54, Track R's round-2 best (0.936 on the tuning numbers) is worse than round 1's frozen genome (0.927). By protocol the round-2 best was frozen.

**Round 2 re-solve** (each track's round-2 frozen genome as the final qs):
- Track M's ECM fell by 12–26 grid steps: 54 off (was 6,317), 72 65,536 (was 185,364), 84 32,768 (was 311,744), 96 120,194 (was 404,281).
- Track R moved at most one step (72: rho 1,579 → 1,448).
- **Round 3 was triggered.**

**Round 3** (the cap; both tracks retuned in the re-solved budgets):
- Track R's frozen genomes are identical to round 2's at 54 / 84 / 96: unchanged budgets and a deterministic search.
- At 96, Track M's round-3 best (0.3848) is marginally worse in the new budgets than round 2's frozen genome (0.3839). By protocol the round-3 best was frozen.

**Final re-solve:** every budget is settled (≤ 1 step) **except Track M at 72**, where ECM moved another 7 steps (65,536 → 35,734). The final budgets were used without further tuning, so **the budgets had not fully settled at 72 under Track M** when the cap was reached.

**Final pipelines:**
- Track R: qs alone at 54; rho 1,448 / 5,793 / 12,634 with ECM off at 72 / 84 / 96.
- Track M: rho 3,158 with ECM off at 54; (1,448, 35,734) at 72; (3,158, 32,768) at 84; (4,871, 120,194) at 96.

**Remaining bound hits (final frozen genomes):** kc 32 at R@72, R@84 and M@84; lc 1.81–1.87 at R@72, M@54 and M@84. No bc or mc hits remain. kc's upper bound (32) and lc's (2.0) now limit several winners.

**Sealed, fresh numbers** (9410000 + 100 pb + bits, 80 per band, run once). Track metric [95%] against qs + lc 1.4 corrected alone, with official / ruint / Montgomery:

| bits | track | (a) round-1 winner, round-1 budgets | (b) final genes, round-1 budgets | (c) final genes, final budgets | gate (c) |
|---|---|---|---|---|---|
| 54 | R | 0.940 (0.939 / 0.932 / 0.906) | 0.945 | 0.945 (0.944 / 0.945 / 0.917) | PASS |
| 54 | M | 0.740 (0.606 / 1.779 / 0.740) | 0.737 | 0.676 (0.748 / 1.131 / 0.676) | PASS; ruint FAIL |
| 72 | R | 0.776 (0.771 / 0.776 / 0.703) | 0.741 | 0.740 (0.724 / 0.740 / 0.665) | PASS |
| 72 | M | 0.642 (0.245 / 2.150 / 0.642), BORDERLINE | 0.641 | 0.598 (0.494 / 1.544 / 0.598) | PASS; ruint FAIL |
| 84 | R | 0.607 (0.607 / 0.607 / 0.528) | 0.584 | 0.584 (0.584 / 0.583 / 0.502) | PASS |
| 84 | M | 0.500 (0.184 / 1.690 / 0.500) | 0.499 | 0.461 (0.463 / 0.878 / 0.461) | PASS; **ruint PASS** |
| 96 | R | 0.537 (0.531 / 0.537 / 0.480) | 0.504 | 0.504 (0.503 / 0.504 / 0.445) | PASS |
| 96 | M | 0.403 (0.226 / 1.186 / 0.403) | 0.395 | 0.362 (0.336 / 0.776 / 0.362) | PASS; ruint BORDERLINE |

**Headline: cross-pricing, round 1 against the final round.** PD_M = Montgomery cost of the R winner / the M winner; PD_R = ruint cost of the M winner / the R winner.

| bits | round 1 as recorded (9400000) | round 1 on fresh numbers ((a) rows) | **final ((c) rows)** | official M / R, final |
|---|---|---|---|---|
| 54 | 1.250 / 1.894 | 1.225 / 1.909 | **1.355 [1.290, 1.425] / 1.197 [1.149, 1.245]** | 0.793 |
| 72 | 1.045 / 2.899 | 1.096 / 2.772 | **1.112 [1.035, 1.200] / 2.087 [1.972, 2.203]** | 0.682 |
| 84 | 1.050 / 2.783 | 1.055 / 2.786 | **1.088 [1.033, 1.148] / 1.505 [1.450, 1.559]** | 0.792 |
| 96 | 1.277 / 2.082 | 1.191 / 2.210 | **1.232 [1.160, 1.310] / 1.541 [1.473, 1.612]** | 0.668 |

- **The lopsidedness shrinks once the budgets are re-solved with tuned genes.** Using Track M's answer under ruint now costs 1.5–2.1x (was 2.2–2.9x at 72–96, 1.9x at 54). Using Track R's answer under Montgomery still costs 1.09–1.36x.
- **Track M's final answer is no longer conditional at 84:** it passes the ruint per-band gate (against qs alone), though under ruint it still costs 1.5x Track R's answer. At 96 it is BORDERLINE, and at 54 and 72 it still fails ("conditional on a fast multiply").
- Its final 84-bit pipeline (rho 3,158, ECM 32,768) has the same ECM budget as allocation A.
- Under the official count, Track M's answer is 1.3–1.5x cheaper than Track R's (it was 2.3–3.3x in round 1, when its ECM budgets were 3–10x larger).

**Ablation: genes against budgets** (track metric, log₂ [95%]):
- *Track R:*
  - genes ((b) against (a)): +0.008 (54, not significant), −0.066, −0.055 and −0.091 at 72 / 84 / 96 (4–6%; all three pricings agree at 72–96);
  - budgets ((c) against (b)): 0.000 at 54 / 84 / 96 and −0.002 at 72.
  - All of Track R's change is genes.
- *Track M:*
  - genes: −0.005, −0.002, −0.003 and −0.029 (0.1–2%);
  - budgets: −0.124, −0.100, −0.114 and −0.128 (7–8% under Montgomery).
  - The budget change also cuts ruint cost by −0.48 to −0.94 log₂ and raises official cost by +0.43 to +1.36: smaller ECM budgets trade official ops for real multiply time.
  - **Track M's change is almost all budgets.**

**Predictions, scored as written.**
- *The user's:*
  - (U1) bc 0.45–0.65 at 84–96, both tracks, and gain (b) against (a) at most 5%: **missed.** bc held at R@84 (0.526), R@96 (0.479) and M@84 (0.494), but M@96 is 0.421. The gain held at R@84 (3.7%), M@84 and M@96, but R@96 is 6.1%.
  - (U2) Track M ECM falls ≥ 1 step at 2 or more of 72–96, and Track R rho moves ≤ 1 step: **held** (12 / 26 / 14 steps; Track R 1 / 0 / 0).
  - (U3) PD_M 1.00–1.15 at 72–96: **missed** (1.112, 1.088, 1.232: 96 is outside).
  - (U4) PD_R 1.8–3.0 at 72–96: **missed** (2.087, 1.505, 1.541). The lopsidedness survives in direction but shrinks below the predicted range at 84 and 96.
- *Mine:*
  - (V1) bc ranges and gain limits: **missed** (M@84 0.494 and M@96 0.421 are below 0.5; R@96 gained 6.1% against ≤ 5%).
  - (V2) Track R ECM off with rho within one step; Track M ECM falls at 2 or more sizes with rho within 2 steps: **held.**
  - (V3) round 3 triggered by Track M, not Track R: **held.**
  - (V4) the final re-solve settled everywhere: **missed** (Track M at 72 moved 7 steps).
  - (V5) Track R's change is mostly genes; Track M's budget part ≥ gene part at 84–96: **held.**
  - (V6) PD_M 1.00–1.20 and PD_R 1.8–3.0 at 72–96: **missed** (PD_M 1.232 at 96; PD_R 1.505 and 1.541).
  - (V7) a final frozen genome still has kc ≥ 29, and no mc lower-bound hit at 72–96: **held.**
  - (V8) Track R PASS everywhere; Track M passes the Montgomery gate at 84–96 and fails the ruint gate everywhere: **missed** (Track M passes the ruint gate at 84 and is BORDERLINE at 96).
- The user's U1–U4: 1 held (U2), 3 missed. Mine: 4 held, 4 missed.

**Conditions:**
- Winners selected on the sealed numbers (six candidates per track per size); a second fresh set confirms in the replacement test.
- The Track M budget at 72 had not settled when the cap was reached.
- kc and lc sit at their upper bounds in several final genomes.
- 54 bits' Track R round-2 genome is slightly worse than round 1's (row (b) against (a): +0.008, not significant).

## 2026-10-25 — Per-track p-1 map check (B = 2^8 … 2^15; protocol and predictions before the map is extended)

**Meter.** No change to charging, op counts or pricing. The existing pm1 card (`lamp_pm1`: bit_length(p^k) per prime power plus one gcd; all or nothing) runs with new bound values only. The card computes B = max(10, int(N^b)); here b = log₂(2^k + 0.5) / log₂ N, so B = 2^k exactly, k = 8 … 15. B is absolute, so b varies with size.

**Protocol.**
- *Map extension:* the eight cards run alone on the numbers of the corrected maps at 54 / 72 / 84 / 96 (`sizescale_map54.json` and the maps `sizescale2.py resolve` uses), with success or failure and per-type counts recorded per number. Python `run_alone`, as for the maps' existing pm1 column. Nothing else is rerun.
- *Final qs per track and size:* that track's final winner from `sizescale_r2_sealed.json` (each is its own size's round-3 frozen genome).
- *Joint optimum:* rho ∈ the map grid; p-1 B ∈ {off, 2^8, …, 2^15}; ECM ∈ {0} ∪ the 1/8-octave grid to 2^22 (widened to 2^24 if at the edge). Order rho → p-1 → ECM → qs; p-1 is paid in full by every number that reaches it. Track R minimizes the robust score (max over pricings of cost / qs + lc 1.4 corrected alone); Track M minimizes Montgomery. Exact composition on the map, as in the re-solves.
- *Report per track per size:* the joint optimum (rho, B, ECM); its track fitness against the final pipeline's on the same map (log₂); whether p-1 is on; the no-p-1 optimum as a check (it should reproduce the final budgets, which were solved on these maps with these genes). Also the official-alone, ruint-alone and Montgomery-alone joint optima, for P3.
- **Map-only, in-sample.** No sealed numbers. If p-1 switches on anywhere, step 2 (the kc / lc bound round) tunes in the p-1-inclusive budgets, and its sealed scoring carries the p-1 verdict.

**Predictions (the user's, labelled as the user's).**
- (P1) Track R: p-1 stays off at every size (the user's recorded expectation).
- (P2) Track M: p-1 switches on at at least one of 84 / 96 bits, with B at most 2^12. Where it does, ECM falls by at least one grid step, and the Montgomery gain over the final pipeline is at most 5%.
- (P3) Under official, p-1 is on at 84–96 bits in the official-alone optimum (direction only, as in the earlier outside model).
- *Scoring:* P3 uses each track's final genes; it holds if p-1 is on at both 84 and 96 for both tracks' genes. The earlier P1/P2 (mine, Oct 24) and the user's revised Oct 24 prediction were stated for the enumerate-era pipeline and stay as written; they are not rescored here.

**Predictions (mine, labelled W to avoid a clash with the Oct 24 P1/P2).**
- (W1) Track R: p-1 switches **on** at 84 and 96 (against P1), with B 2^9–2^12, and robust gain 1–5% over the final pipeline on the map (log₂ −0.015 to −0.074). Off at 54, where Track R runs qs alone. Reason: rho is on in Track R, so ruint already pays for modmul ops at the margin. For p of 24–32 bits, small-B p-1 costs ~7,600–45,000 ops per factor found, against rho's ~12,400–200,000. The 2.12x ruint figure was for B ≈ 2^16.7, ~100k ops per number.
- (W2) Track M: p-1 on at 72, 84 and 96, B 2^10–2^13. ECM falls by ≥ 1 step where p-1 is on. Montgomery gain ≤ 4% at every size.
- (W3) Official-alone optimum: p-1 on at 72–96 for both tracks' genes.

### Per-track p-1 map check: results (`evolve/pm1check.py`; `pm1check.out`, `pm1check.json`, `pm1check_map.json`)

**Map extension.** The eight cards ran on all 2,000 map numbers (54: 320, 72: 480, 84: 560, 96: 640). Charge per number at B = 2^8 … 2^15: 388, 787, 1,558, 3,085, 6,181, 12,259, 24,526 and 48,802 ops, as computed in the Oct 24 entry. Solve fraction at B = 2^10: 0.350, 0.242, 0.193 and 0.166 at 54 / 72 / 84 / 96. **Check:** the no-p-1 optimum reproduces the final budgets in all eight cells.

**Joint optimum per track** (map, in-sample; the track's fitness against qs + lc 1.4 corrected alone; gain = joint / final pipeline on the same map):

| bits | track | final pipeline (rho, ECM): fitness | joint optimum (rho, p-1 B, ECM): fitness | official / ruint / Montgomery (joint) | gain (log₂) | p-1 |
|---|---|---|---|---|---|---|
| 54 | R | (0, 0): 0.9371 | (0, 2^8, 0): 0.8818 | 0.791 / 0.882 / 0.786 | 5.9% (−0.088) | ON |
| 54 | M | (3,158, 0): 0.6698 | (1,448, 2^10, 0): 0.6021 | 0.660 / 1.061 / 0.602 | 10.1% (−0.154) | ON |
| 72 | R | (1,448, 0): 0.7349 | (790, 2^9, 0): 0.7068 | 0.681 / 0.707 / 0.624 | 3.8% (−0.056) | ON |
| 72 | M | (1,448, 35,734): 0.5584 | (664, 2^11, 17,867): 0.5150 | 0.530 / 1.162 / 0.515 | 7.8% (−0.117) | ON |
| 84 | R | (5,793, 0): 0.5899 | (3,158, 2^11, 0): 0.5794 | 0.566 / 0.579 / 0.490 | 1.8% (−0.026) | ON |
| 84 | M | (3,158, 32,768): 0.4377 | (2,896, 2^12, 32,768): 0.4214 | 0.394 / 0.859 / 0.421 | 3.7% (−0.055) | ON |
| 96 | R | (12,634, 0): 0.5004 | (10,624, 2^12, 0): 0.4784 | 0.455 / 0.478 / 0.406 | 4.4% (−0.065) | ON |
| 96 | M | (4,871, 120,194): 0.3660 | (2,896, 2^13, 120,194): 0.3496 | 0.331 / 0.744 / 0.350 | 4.5% (−0.066) | ON |

- **p-1 switches on in every cell, both tracks.** In Track R, ruint still binds and B is 2^8–2^12, rising with size.
- p-1 replaces part of rho: rho falls in seven of eight cells (Track R 1,448 → 790, 5,793 → 3,158, 12,634 → 10,624; at 54, rho was already off).
- Track M's ECM falls only at 72 (35,734 → 17,867, 8 steps). At 84 and 96 ECM is unchanged, and p-1 replaces rho.
- Track M's B is 2^10–2^13, one octave above Track R's at the same size.
- The per-B profiles are shallow near the optimum. At 84, Track R's best at 2^10 is 0.5797 against 0.5794 at 2^11; at 96, Track M's 2^12 is 0.3514 against 0.3496 at 2^13. Map-only, the chosen B is uncertain by about an octave.
- **Per-pricing joint optima** (each track's genes, with p-1 against without):
  - official: p-1 on at every size, with B 2^10 / 2^11 / 2^12 / 2^14 at 54 / 72 / 84 / 96. Official's ECM budget (60,097–2,719,670) solves every number, so qs genes do not matter and both tracks give the same optimum. Gain 1.9–11.7%.
  - ruint: p-1 on at every size, B 2^8 / 2^9 / 2^10 / 2^12, ECM off; gain 2.6–5.5%.
  - Montgomery (Track R's genes): p-1 on at every size, B 2^10 / 2^11 / 2^12 / 2^13; gain 3.9–13.8%.
- **Caveats.** In-sample on the map: nine B options per cell are chosen on the same numbers that score them. No gate was run. Sealed scoring comes with step 2 (the kc / lc round), which tunes in these p-1-inclusive budgets.

**Predictions, scored as written.**
- *The user's:*
  - (P1) Track R: p-1 off at every size: **missed** (on at all four sizes).
  - (P2) Track M: on at 84 or 96 with B ≤ 2^12; where on, ECM falls ≥ 1 step; Montgomery gain ≤ 5%: **missed.** On at 84 with B 2^12 and at 96 with 2^13; the gain clause held at 84 (3.7%) and 96 (4.5%); but ECM did not fall at 84 or 96. (Outside P2's sizes: at 72, ECM fell 8 steps and the gain was 7.8%.)
  - (P3) official-alone optimum has p-1 on at 84–96: **held** (2^12 at 84, 2^14 at 96, for both tracks' genes).
- *Mine:*
  - (W1) Track R: on at 84 and 96 with B 2^9–2^12, gain 1–5%, off at 54: **missed.** On at 84 (2^11, 1.8%) and 96 (2^12, 4.4%) as predicted, but also on at 54 (2^8, 5.9%).
  - (W2) Track M: on at 72–96 with B 2^10–2^13; ECM falls ≥ 1 step where on; Montgomery gain ≤ 4%: **missed.** On with B in range everywhere; ECM fell only at 72; the gain was above 4% at 72 (7.8%) and 96 (4.5%).
  - (W3) official-alone optimum: p-1 on at 72–96 for both genes: **held.**
- The user's: 1 held (P3), 2 missed. Mine: 1 held (W3), 2 missed.
- The MOVES row "td and p-1 as pre-stages before qs" reopens on the changed condition (small B, re-optimized rho and ECM, corrected card, per-track genes). Status: map-only, pending sealed scoring in step 2.

## 2026-10-25 — kc / lc bound round (pre-registered; two card amendments, protocol and predictions before code)

### Card amendments (cost models before code)

**(A1) pm1: absolute bound gene `B`.** The pm1 card computes its bound as max(10, int(N^b)), so one genome gives a different B for each N. To put a fixed B = 2^k in a pipeline genome shared by many numbers, the card gains an optional integer gene `B`. If present, the bound is B; otherwise it is as today.
- *Charges unchanged:* bit_length(p^e) per prime power ≤ B, plus one gcd. All or nothing, as before.
- *Identity:* without `B`, nothing changes. With `B` = 2^k, ops, factor and per-type counts equal the b-card's entries in `pm1check_map.json` (b chosen so int(N^b) = 2^k).
- *Acceptance:* that equality on all 2,000 map numbers at k = 8 … 15 (Python), Python = Rust on a sample, and a parity pair. In a pipeline the pm1 stage gets ob = 2B, above its charge (≤ 1.53 B at these B), so it always completes.

**(A2) qs: lc clamp raised from 2.0 to 3.0** (Python and Rust). The card clamps lc to [1.0, 2.0] because L = B^lc ≤ B² guarantees that a cofactor below L is prime. The requested bound of 2.5 would otherwise be a no-op above 2.0.
- For lc in (2.0, 3.0], a cofactor v in [B², B^lc) may be composite. It is filed and combined exactly like a prime partial, with the same charges: bound check, N mod v, hash lookup, then insert, or combine (1 op u₁u₂ mod N plus F ops vector add).
- No primality test is run on v, so no op is skipped or uncharged.
- Two relations with the same cofactor v multiply to v² times smooth parts, a valid relation for any v. The ledger multiplies v into the square root exactly as for a prime.
- A composite v that shares a factor with N but does not divide it is not detected (missed only, not wrong).
- *Exactness:* in Rust the partial test compares v against L as f64. L ≤ (3·e^{0.5√(ln N ln ln N)})³ < 2^42 for N < 2^100 at bc ≤ 3, so the f64 comparison stays exact.
- *Identity:* for lc ≤ 2.0, the card is unchanged op for op (only the clamp constant moves).
- *Acceptance:* the full parity suite, plus Python = Rust pairs at lc 2.3 and 2.5 on map samples.

### Protocol (user's; rules made exact here)

- **Budgets for tuning:** step 1 switched p-1 on everywhere, so tuning uses the p-1-inclusive joint optima (rho, B, ECM) of the p-1 map check, per track and size.
- **Tuning:** settings as rounds 2–3 (tpe-tuned, seeds 0–3, 200 trials per size, 24 per band tuning numbers, seeds 9300000+). Bounds: kc 1–64 (int), lc 1.0–2.5; bc 0.3–3.0, mc 0.01–12 (log) and tc 1.0–3.5 unchanged. The frozen genome is the best seed. Baselines reported: qs + lc 1.4's genes and the current final genome in the same pipeline.
- **Bound hits** (same rule, within 10% of a bound's value): kc ≤ 1.1 or ≥ 57.6; lc ≤ 1.1 or ≥ 2.25; bc ≤ 0.33 or ≥ 2.7; mc ≤ 0.011 or ≥ 10.8; tc ≤ 1.1 or ≥ 3.15.
- **Re-solve:**
  - every cell once, with its new frozen genome, using the joint (rho, B, ECM) solver of the p-1 check (ECM grid to 2^22, widened if at the edge). These are (d)'s budgets.
  - *Movement:* rho and ECM in 1/8-octave steps, B in octaves; "settled" means ≤ 1 step for each and no off/on switch.
- **Track M at 72:**
  - If its re-solve moves more than one step from the tuning budgets, M@72 is retuned in the re-solved budgets (same settings), then re-solved again.
  - At most two re-solves follow the tuning round. The report says whether it settled or the limit was reached.
  - (d) for M@72 uses the last re-solve's budgets with the last genes.
- **Sealed:** fresh numbers 9420000 + 100 pb + bits (checked unused), 80 per band, run once.
  - (c) the current final winners in their final pipelines (no p-1);
  - (c+p) the current final winners in the step-1 joint (p-1) budgets; added by me as an information row: it is the sealed p-1 verdict, separated from kc / lc;
  - (d) the new winners in (d)'s budgets. New winner: the best by the track's fitness on the sealed numbers, among the track's four new tuned genomes, the cell's current final genome, and qs + lc 1.4's and the new genes (seven candidates).
  - Both references; all three pricings; gates as in the two-track rule (Track M's ruint gate is information only).
- **Headline:** PD_M and PD_R from (d), next to the final round's values (the (c) rows of the 9410000 set) and (c) on this set.

### Predictions (the user's, labelled as the user's)

- (K1) kc moves above 32 in at least two of the bound-hit genomes. The gain from (c) to (d) is at most 4% under the track's metric at every size.
- (K2) PD_M and PD_R each stay within 0.15 of the final round's values at 72–96 bits.
- *Scoring:* the bound-hit genomes are the three kc-32 hits (R@72, R@84, M@84) and the three lc hits (R@72, M@54, M@84), i.e. the cells R@72, R@84, M@54 and M@84; K1's kc clause counts how many of these cells' new frozen genomes have kc > 32. "The final round's values" are the recorded (c) values on the 9410000 set.

### Predictions (mine)

- (L1) kc > 32 in at least three of the eight new frozen genomes. lc > 2.0 in at most two of the eight.
- (L2) Sealed p-1 verdict, (c+p) against (c): lower under the track's metric in all eight cells. The interval excludes 0 in at least six. Track R gains 1–6%; Track M gains 3–10% (Montgomery).
- (L3) The kc / lc part, (d) against (c+p): at most 2% under the track's metric in every cell, with the interval including 0 in at least four of eight.
- (L4) PD_R at 72 falls by more than 0.15 (Track M's ECM halves there). At 84–96, PD_R stays within 0.15. PD_M stays within 0.15 at 72–96.
- (L5) Track M at 72 settles within the two re-solves.

### Addendum (user, Oct 25): outside predictions, two checks, a reporting rule

**Timing.** This addendum arrived after the p-1 map check (step 1) had run and been recorded, and after step 2's protocol, predictions and card amendments were committed, but **before any step-2 tuning ran**. So the step-1 predictions below are **post hoc**: recorded after the result was known, and scored now only for the record. The step-2 predictions are pre-registered.

**DeepSeek's predictions** (labelled as DeepSeek's; its stated confidence: medium).
- *Step 1, post hoc (the result was already recorded above):*
  - (D-a1) Track R: p-1 off at all four sizes; if on anywhere, at 84 with B = 2^10 and gain ≤ 1% (undecided). Scored post hoc: **missed** (on at all four sizes; 84 with B 2^11, 1.8%).
  - (D-a2) Track M: p-1 on at 72 / 84 / 96 with B = 2^10, off at 54; gain 4–10% at 84–96 and 1–3% at 72; ECM falls ≥ 2 grid steps at 96 and 1 at 84. Scored post hoc: **missed.** On at 72–96, but with B 2^11 / 2^12 / 2^13; also on at 54 (2^10); gain 3.7% / 4.5% at 84 / 96 and 7.8% at 72; ECM unchanged at 84 and 96.
  - (D-a3) Official: p-1 on at 84–96. Scored post hoc: **held.**
- *Step 2, pre-registered:*
  - (D-b1) kc hits 64 again for Track R at 72 and 84; it settles at 20–40 for Track M. Scoring rule: if kc hits 64 again, note "kc is effectively unbounded"; restructuring is a separate decision.
  - (D-b2) lc hits 2.5 for Track R at 96 (DeepSeek said 90–96; scored at 96); it settles at 1.8–2.2 for Track M.
  - (D-b3) Gain from the kc / lc round: 3–8% for Track R at 72–84 and 1–3% for Track M. PD_M and PD_R unchanged within intervals.
  - *Scoring choices (mine):*
    - "hits 64" means the frozen genome's kc is within the bound-hit rule (≥ 57.6); "settles at 20–40" applies to all four Track M frozen genomes.
    - "Gain from the round" is (d) against (c) on the sealed numbers, under the track's metric. That includes the p-1 budgets; the (d) against (c+p) gain is reported beside it.
    - "Unchanged within intervals" means (d)'s PD interval overlaps the final round's.

**Grok's predictions** (labelled as Grok's).
- (G-a) p-1: the same as the user's prediction already on record (off under Track R; Track M on at 84 or 96 with B ≤ 2^12 and gain ≤ 5%). **Not independent** of P1–P2, and post hoc for step 1. As scored for P1 and P2: missed.
- (G-b1) Track R: kc mostly ≥ 40, several at 64; lc 1.6–2.2. Gain 3–12% on the robust score, largest at 84–96. No size loses more than 2%. Pre-registered. *Scoring (mine):*
  - "mostly ≥ 40": at least three of the four Track R genomes;
  - "several at 64": at least two at the bound-hit rule;
  - the gain is (d) against (c), as for D-b3.
- (G-b2) Track M: kc moves up less than in Track R. ECM budgets stay within one grid step after the re-solve, or drop further at 84. Pre-registered.
- (G-rho) Track R's rho budget goes to zero somewhere in 110–130 bits. Untested at our sizes (the study stays at 40–100 bits). The observed trend points the other way: Track R's rho rises 1,448 → 5,793 → 12,634 from 72 to 96 bits, with no p-1. With p-1 in the step-1 joint optima it is 790 → 3,158 → 10,624, still rising.

**Check B1: absolute sieve interval M and s, final frozen genomes** (information only).
- *Formulas, from qs.py / qs.rs:*
  - B = max(30, ⌊bc · e^{0.5 √(ln N ln ln N)}⌋) and M = max(64, ⌊mc · B⌋), with sieve width 2M + 1.
  - The target A is √(2kN) / M. s starts at 1 and rises while target^{1/s} exceeds the largest pool prime (s ≤ 8), then falls while target^{1/s} is below the third pool prime.
  - Pool primes are the factor-base primes > 2 that do not divide k. k is the top-ranked multiplier.
- *Computed* on each size's map numbers (first attempt; base built with the card's own `Ledger`; no sieving):

| bits | track | bc | mc | mc·bc | B (median) | M (median, range) | s |
|---|---|---|---|---|---|---|---|
| 54 | R | 0.943 | 0.289 | 0.273 | 298 | 86 (80–91) | 3 (all 320) |
| 54 | M | 0.728 | 0.944 | 0.687 | 230 | 217 (202–230) | 3 (all) |
| 72 | R | 0.572 | 0.350 | 0.200 | 584 | 204 (192–215) | **4** (all 480) |
| 72 | M | 0.659 | 1.603 | 1.057 | 674 | 1,080 (1,018–1,136) | **3** (all) |
| 84 | R | 0.526 | 0.512 | 0.269 | 1,095 | 560 (527–587) | 4 (all 560) |
| 84 | M | 0.513 | 0.672 | 0.345 | 1,069 | 718 (675–753) | 4 (all) |
| 96 | R | 0.479 | 0.518 | 0.248 | 1,943 | 1,007 (954–1,056) | 4 (all 640) |
| 96 | M | 0.433 | 0.984 | 0.426 | 1,755 | 1,727 (1,638–1,810) | 4 (all) |

- **Track M's wider mc is not the same absolute sieve in other coordinates.** Its B is similar to Track R's, so M = mc·B is also wider in absolute terms: 2.5x / 5.3x / 1.28x / 1.7x Track R's at 54 / 72 / 84 / 96.
- **Only at 72 does s differ** (Track M 3, Track R 4). At the other sizes both tracks use the same s, and Track M simply sieves a wider interval with fewer polynomials.

**Check B2: ECM curves.** The ECM card uses Montgomery curves, x-only, with **Suyama's parametrization** (σ = s0 + i, s0 = 6; `ecm.py` header). Suyama's family gives group orders divisible by 12 by construction; the card adds no further torsion step.

**Check E (hypothesis: is Track M's ECM dip at 84 tied to the qs s = 3 → 4 step?).**
- The final Track M genomes use s = 3 at 72 and s = 4 at 84 and 96.
- The 84-bit dip (ECM 32,768, against 35,734 at 72 and 120,194 at 96) therefore coincides with Track M's s = 3 → 4 step between 72 and 84. Under s = 4, qs is cheaper relative to ECM, so less ECM pays.
- This is consistent with the hypothesis but does not test it. A test would re-solve 84 with an s = 3 genome, or 72 with an s = 4 genome. Step 2's re-solve reports the s of the new genomes beside the budgets.

**Reporting rule (adopted from Grok, Oct 25).** Every cross-pricing table carries the gate status on the same row as PD_M and PD_R. Examples: "M: conditional on a fast multiply"; "M: passes ruint gate against qs alone; 1.5x Track R under ruint".

**pm1 stage 2 (information, Oct 25).** The pm1 card has **no stage 2**: it runs stage 1 to the bound B (one modular exponentiation per prime power, charged bit_length(p^e)), then takes one gcd, with no B2 bound like the ECM card's b2. A MOVES row "pm1 stage 2 (B2 = c x B)" is added, untested, with the user's outside estimate: for 32-bit factors at B = 1024, the catch rate rises from 3.8% to 22.8% with B2 = 50B (Mathematica, 3,000 primes; stage-2 cost not included, roughly 3x stage 1). The running round is unchanged.
- *DeepSeek's predictions for a future pm1 stage-2 test* (labelled as DeepSeek's; written before any stage-2 code; pre-registered for any future stage-2 test):
  - (D-s1) Track R: stage 2 on at 84 and 96 with B = 2^11 and B2 = 2^14–2^15; gain 3–6% over stage-1-only p-1; off at 54–72.
  - (D-s2) Track M: on at 72–96 with B = 2^10–2^11 and B2 = 2^14–2^16; gain 8–15% at 84–96 and 3–5% at 72; ECM falls at least one grid step at 84 and 96.
  - (D-s3) c = B2 / B: about 10 wins in Track R, 20–50 in Track M.
  - *Note:* DeepSeek's cost model charged one gcd per stage-2 candidate. The standard method accumulates a product and takes one gcd at the end, so its Track R cost estimate is high.
- *DeepSeek's kc test, recorded for the kc / lc report (information only):* how often Knuth–Schroeppel's top-ranked multiplier matches the best-observed multiplier on the sealed numbers. Not run yet. It needs qs run with each multiplier forced, which is a separate information-only pass; its definition (which k's, which genome, which pricing defines "best") is fixed before it runs.
- *Grok's predictions for a future pm1 stage-2 test* (labelled as Grok's; written before any stage-2 code; pre-registered for any future stage-2 test):
  - (G-s1) Track R: with a pm1 stage 2 (B2 ~ 50B), B stays 2^11–2^13. Robust gain 2–6% over stage-1-only p-1, concentrated on the 28–36-bit factor bands. ECM stays off; rho keeps rising with size.
  - (G-s2) Track M: B 2^10–2^12, B2 ~ 50B; Montgomery gain 4–9% over stage-1-only at 72–96; ECM falls about one grid step at 84 and 96.
- *Grok's prediction on stage-1 p-1, scored in the kc / lc sealed run* (pre-registered; that run has not started):
  - (G-p1) Stage-1 p-1's catches come mostly from the 24–36-bit factor bands.
  - *Scoring (mine):* held if, in the (c+p) rows, at least half of p-1's catches (pooled over the four sizes, per track) are numbers whose smaller factor is in bands 24–36.
- *Reporting addition for the kc / lc sealed run* (information only): for the without-p-1 row (c) and the with-p-1 rows (c+p) and (d), the catches per band for each stage (rho, p-1, ECM, qs). This shows which bands p-1 takes over, and from which stage.

**DeepSeek, after the user's Mathematica KS result (recorded Oct 25, before the kc / lc tuning ran).**
- **D-b1 REVISED** (a revision; the original D-b1 stays the scored prediction, since it was pre-registered before the round): kc settles at 20–40, with no consistent bound-hitting across seeds. If kc hits 64, the hits are spread across seeds (drift). DeepSeek recommends making kc a constant: score 32 candidates and keep the best.
- **D-s1 REVISED** (still pre-registered: no stage-2 code or test exists yet): Track R's stage-2 gain is 5–10%, on at 84–96 with B = 2^11 and B2 = 2^14–2^15, off at 54–72. Track M unchanged (8–15%). It now expects ECM to fall one grid step at 84–96 when p-1 gets stage 2.
- **(D-k)** At 84 bits, the median selected Knuth–Schroeppel k is 15–35 (DeepSeek leans 15–25), with the 90th percentile under 50. Scored with the queued kc check (selected-k distribution per final genome on the map numbers), using both tracks' 84-bit final genomes. DeepSeek's decision rule: a median above 30 means keep kc as a gene with max 64; below 20 means retire it.
- **(D-lp)** If an in-repo k test with large primes is run, the median best k shifts up by at most 3 against no large primes.
- **Proposed rule (recommended; the user's decision; future rounds only):** a gene at a bound counts as "demand" only if, on the sealed numbers, the frozen genome beats the same genome with that gene set to the median of its interior values by more than the paired 95% interval. Otherwise the hit is drift, and the gene is a candidate for a constant. Recorded in PLAN under the bound-hit rule as "proposed, pending user".

**p-1 map check rerun on commit bdca53e: identical.** The map was recomputed from scratch, with no cache; `pm1check_map.json`, `pm1check.json` and the printed optima are byte-identical to step 1's. Step 1 used the b-card (b set per number so that int(N^b) = 2^k, asserted on every number), not the B gene. The p-1-inclusive budgets stand for the kc / lc round. *Disclosure:* the card code for (A1) and (A2) entered the repo in commit bb89d20 (the addendum's NOTES commit, through `commit -a`), before the parity suite had passed. The code is unchanged since then; parity passed on it (0 mismatches; `parity_bround.out`), and bdca53e adds the parity pairs, the acceptance test and the round driver.

**Decision (user, Oct 25): the demand-vs-drift rule is ADOPTED for future rounds** (PLAN, bound-hit rule). It is not retroactive. The kc / lc round was pre-registered before the adoption, so it is scored by its own protocol. It also reports the demand-vs-drift comparison for each bound-hit gene as information.

**How lc sets the large-prime bound (information, Oct 25; the kc / lc tuning is running).**
- The card's large-prime bound is **L = B^lc**, in both qs.py and qs.rs. A cofactor v with 1 < v < L is a partial.
- lc also lowers the sieve threshold: T = log₂(M√(kN/2)) − (tc + lc − 1)·log₂ B.
- *Outside context (user, Mathematica; 18-digit N, B = 3000, bound B^lc; sieve values needed for the factor base + 10 relations):*
  - lc 1.0 → 35,287; 1.3 → 20,419; 1.6 → 19,371; 2.0 → 19,274; 2.3 and 2.6 → 19,274 (identical).
  - The gain is flat above about 1.6 and exactly flat above 2.0, because large primes above B² almost never repeat at this size.
- *Context for scoring G-b1's lc clause and D-b2:* in our card, lc > 2.0 is not free.
  - The threshold keeps falling with lc, so more candidates are confirmed by trial division (charged).
  - Each extra cofactor in [B², B^lc) is charged a bound check, N mod v, a lookup and an insert, even though such cofactors rarely pair.
  - So the card's cost above 2.0 should rise rather than stay flat, unless tc moves down to offset the threshold term.

**DeepSeek's lc / tc predictions** (labelled as DeepSeek's; recorded Oct 25 while the kc / lc tuning was running, before any kc / lc result was read; Track R at 54, 72 and 84 had finished and were not looked at beyond their progress lines).
- (D-c1) At 84–96 bits:
  - lc 1.7–1.9 in Track R and 1.9–2.1 in Track M, neither above 2.2;
  - tc 0.7–1.1 in both tracks;
  - tc + lc 2.6–3.0 (DeepSeek's least confident clause);
  - lc(96) − lc(72) in [0, +0.2] per track.
- Its Q1 answer implied tc + lc of 2.8–3.2; the Q2 numbers above are the scored ones.
- *Note (mine):* the round's tc search bound is 1.0–3.5, so tc in 0.7–1.0 is outside the searchable range. The tc clause can hold only at 1.0–1.1, and a frozen tc near 1.0 would be a bound hit.
- *Factor base size, for the 2LP MOVES row* (information; the card's own Ledger on every 8th map number, final genomes): median F is 34 / 28 at 54 (R / M), 57 / 65 at 72, 96 / 94 at 84 and 151 / 141 at 96. A run needs F + 10 relations (ledger DELTA = 10).
- Two MOVES rows added, UNTESTED: "qs threshold reparameterization (slack s = tc + lc − 1, lc)" and "Double large prime variation", the latter with DeepSeek's estimate and the corrections recorded beside it.

**Grok, after the user's Mathematica lc result** (labelled as Grok's; recorded Oct 25 while the kc / lc tuning was running, before any kc / lc result was read).
- **G-b1 REVISED** (a revision; the original G-b1 stays the scored prediction). At 84–96 bits:
  - Track R: lc 1.5–1.9 (mode ~1.6–1.7), tc + lc 2.8–3.4;
  - Track M: lc 1.4–1.8, tc + lc 2.7–3.3;
  - any lc ≥ 2.0 winner should fail the demand-vs-drift test.
- *Direction to report:* this puts Track M's lc below Track R's, the opposite of DeepSeek's D-c1. The kc / lc report states which direction holds at 84–96.
- **Threshold coupling (Grok's view, disputed).** Grok calls the coupling of the threshold to lc a historical accident.
  - *Recorded counterpoint:* a partial whose cofactor is up to B^lc falls short of the sieve estimate by up to about (lc − 1)·log₂ B, so a wider large-prime bound does need more slack to admit those partials.
  - In the user's Mathematica run, partials below B² supplied most of the combined relations (492 against 317 full at lc = 2.0).
  - The reparameterization MOVES row stands; the coupled form stays the card's default.
- **kc, pending the selected-k check:** if kc is flat above ~20, replace it with a constant: score squarefree k ≤ 32 only, and keep the KS winner. Both outside reviewers recommend dropping non-squarefree k. Today the card's candidate list is every integer k = 1 … kc, including non-squarefree k such as 4, 8 and 9. Changing that is a card change: cost model first, and a new decision.

**Paperwork (Oct 25): sq card, small-prime variation, seven MOVES rows** (information only; the running round is unchanged).
- **What the "sq" card is:** a square search on kN, with three modes: Fermat (k = 1, wide window), Lehman (windows of about N^(1/6)/√k) and Hart's one-line method (window 1). Every test of x² − kN is one op. It is **not SQUFOF**.
- **Small-prime variation:** the qs card does **not** use it. It sieves every odd factor-base prime, including 3, 5 and 7 (log weight max(1, round(log₂ p))), and skips only −1, 2 and the primes dividing A.
- **MOVES rows added, all UNTESTED:**
  - p+1 (Williams);
  - an ECM curve family with larger torsion;
  - a SQUFOF card for small N;
  - small-prime variation in the qs sieve;
  - bandit (BaSE-style) allocation of tuning budget;
  - anytime curves for every search method;
  - a GPU-style pricing track.
  - The card and pricing changes each carry "cost model in NOTES before code".

### kc / lc bound round: results (`sizescale3.py`; `sizescale_k_tune.out`, `sizescale_k_resolve.out`, `sizescale_k_sealed.out`, `.json`; `kcheck.out`; `dvd.out`)

**Tuning** (kc 1–64, lc 1.0–2.5; step-1 p-1-inclusive budgets). Frozen genomes:

| cell | kc | bc | mc | tc | lc | tc + lc | bound hits |
|---|---|---|---|---|---|---|---|
| R@54 | 23 | 0.870 | 0.507 | 1.318 | 1.741 | 3.059 | — |
| R@72 | 36 | 0.576 | 0.393 | 1.528 | 1.698 | 3.226 | — |
| R@84 | 60 | 0.511 | 0.480 | 1.268 | 1.737 | 3.005 | kc 60 |
| R@96 | 60 | 0.432 | 0.602 | 1.035 | 1.974 | 3.009 | kc 60; tc 1.035 |
| M@54 | 12 | 0.678 | 0.854 | 1.516 | 1.768 | 3.284 | — |
| M@72 | 46 | 0.501 | 0.719 | 1.540 | 1.650 | 3.190 | — |
| M@84 | 44 | 0.479 | 0.787 | 1.266 | 1.792 | 3.058 | — |
| M@96 | 19 | 0.496 | 0.837 | 1.295 | 1.613 | 2.908 | — |

- No frozen genome has lc above 2.0. The only seed best above 2.0 was R@72 seed 1 (lc 2.133), one of the worst seeds (0.801 against 0.646).
- kc rose above 32 in five of eight cells. tc's lower bound (1.0) is new as a bound hit (R@96).

**Re-solve** (joint rho, p-1 B, ECM, with the new frozen genomes):
- Seven of eight cells are settled (0 steps).
- **Track M at 72 settled on the first re-solve**, so no retune was needed.
- **Track M at 54 moved:** rho 1,448 → off and ECM off → 6,317, with B 2^10 unchanged. By protocol only M@72 is retuned; (d) uses the re-solved budgets.

**Sealed, fresh numbers** (9420000 + 100 pb + bits, 80 per band, run once). Track metric [95%] against qs + lc 1.4 corrected alone, with official / ruint / Montgomery:

| bits | track | (c) current final, no p-1 | (c+p) current final, p-1 budgets | (d) new winner, new budgets | (d) winner; budgets (rho, B, ECM) |
|---|---|---|---|---|---|
| 54 | R | 0.958 (0.954 / 0.958 / 0.929) | 0.877 (0.779 / 0.877 / 0.780) | 0.829 (0.829 / 0.815 / 0.719) | R-k@54; (0, 2^8, 0) |
| 54 | M | 0.682 (0.756 / 1.134 / 0.682) | 0.629 (0.694 / 1.086 / 0.629) | 0.595 (0.459 / 1.506 / 0.595) | current final; (0, 2^10, 6,317) |
| 72 | R | 0.723 (0.711 / 0.723 / 0.650) | 0.716 (0.696 / 0.716 / 0.638) | 0.710 (0.710 / 0.709 / 0.630) | R-k@72; (790, 2^9, 0) |
| 72 | M | 0.592 (0.495 / 1.527 / 0.592) | 0.538 (0.585 / 1.160 / 0.538) | 0.538 (= (c+p)) | current final; (664, 2^11, 17,867) |
| 84 | R | 0.590 (0.590 / 0.587 / 0.506) | 0.573 (0.564 / 0.573 / 0.486) | 0.573 (= (c+p)) | current final; (3,158, 2^11, 0) |
| 84 | M | 0.455 (0.455 / 0.864 / 0.455) | 0.426 (0.406 / 0.854 / 0.426) | 0.426 (= (c+p)) | current final; (2,896, 2^12, 32,768) |
| 96 | R | 0.502 (0.502 / 0.502 / 0.444) | 0.489 (0.462 / 0.489 / 0.415) | 0.484 (0.479 / 0.484 / 0.410) | R-k@96; (10,624, 2^12, 0) |
| 96 | M | 0.350 (0.324 / 0.753 / 0.350) | 0.338 (0.306 / 0.743 / 0.338) | 0.335 (0.272 / 0.741 / 0.335) | M-k@84; (2,896, 2^13, 120,194) |

- Every track gate passes in every row.
- Track M's ruint gate (information):
  - (c): FAIL / FAIL / **PASS** / BORDERLINE at 54 / 72 / 84 / 96 (the 84 PASS of the final round replicates on fresh numbers);
  - (c+p): BORDERLINE / FAIL / BORDERLINE / BORDERLINE;
  - (d): FAIL / FAIL / BORDERLINE / BORDERLINE.
- No misses.

**The sealed p-1 verdict, (c+p) against (c)** (track metric, log₂ [95%]):
- *Track R:* −0.128 [−0.197, −0.066] at 54 (8.5%); −0.015 [−0.064, +0.033] at 72 (1.0%); −0.042 [−0.089, +0.003] at 84 (2.9%); −0.038 [−0.081, +0.000] at 96 (2.6%).
  - **Significant only at 54.** At 72–96 the direction favours p-1 under every pricing, but the robust interval includes 0. At 84 and 96 its upper end is +0.003 and +0.000, so ruint does not agree with official and Montgomery, which are significant there.
  - Under the reporting rule (call a cell only where all three agree), Track R's p-1 gain at 72–96 is within noise.
- *Track M (Montgomery):* −0.116 [−0.209, −0.023] at 54 (7.7%); −0.137 [−0.227, −0.051] at 72 (9.1%); −0.096 [−0.155, −0.040] at 84 (6.4%); −0.052 [−0.099, −0.009] at 96 (3.5%). **Significant at every size.**
  - At 72, p-1 also cuts Track M's ruint cost by −0.396 log₂ (ECM halves) but raises official cost by +0.243.

**The kc / lc part, (d) against (c+p):**
- *Track R:* −0.081 [−0.120, −0.043] at 54 (5.4%; it raises official cost by +0.090); −0.011 (not significant) at 72; 0 at 84 (the current final genome won); −0.016 [−0.030, −0.001] at 96 (1.1%).
- *Track M:*
  - 54: −0.081 (not significant). The winner is the current final genome in the M@54 re-solved budgets (rho off, ECM on), which raises ruint cost by +0.47.
  - 72 and 84: 0 (the current final genome won in the same budgets).
  - 96: −0.012 (not significant).
- **Widening kc and lc bought ≤ 1.1% at 72–96.** The current final genomes won four of the eight cells (R@84, M@54, M@72, M@84).
- The 54-bit gains in both tracks come with large moves in the other pricings.

**Headline: cross-pricing, (d) against the final round.** The gate status is on the PD row, per the Oct 25 reporting rule.

| bits | final round (9410000), PD_M / PD_R | (c) on 9420000 | **(d) PD_M [95%]** | **(d) PD_R [95%]** | official M/R (d) | Track M gate status (d) |
|---|---|---|---|---|---|---|
| 54 | 1.355 / 1.197 | 1.362 / 1.184 | **1.207 [1.103, 1.322]** | **1.848 [1.727, 1.975]** | 0.554 | M: conditional on a fast multiply (ruint gate FAIL; ECM on in its re-solved budgets) |
| 72 | 1.112 / 2.087 | 1.098 / 2.113 | **1.170 [1.099, 1.250]** | **1.637 [1.558, 1.719]** | 0.824 | M: conditional on a fast multiply (ruint gate FAIL) |
| 84 | 1.088 / 1.505 | 1.113 / 1.471 | **1.142 [1.082, 1.207]** | **1.490 [1.435, 1.544]** | 0.719 | M: ruint gate BORDERLINE against qs alone (PASS without p-1); 1.49x Track R under ruint |
| 96 | 1.232 / 1.541 | 1.269 / 1.501 | **1.224 [1.150, 1.308]** | **1.532 [1.461, 1.605]** | 0.567 | M: ruint gate BORDERLINE against qs alone; 1.53x Track R under ruint |

- At 72, PD_R falls from 2.09 to 1.64, because p-1 halves Track M's ECM there. At 84–96 nothing moves beyond 0.04.
- At 54, PD_R rises from 1.20 to 1.85, because Track M's re-solved budgets switch ECM on. PD_M falls at 54 (1.36 → 1.21) and rises slightly at 72–84 (by 0.03–0.06).

**Catches per band (G-p1 and the reporting addition).**
- In Track R, p-1 takes numbers mainly from **qs** at 24–36 bits and from **rho** at 16–24. At 84, rho's band-20 catches fall 79 → 62 and qs's band-24 catches 64 → 61, with p-1 taking 8 / 14 / 10 / 8 in bands 20 / 24 / 28 / 32.
- In Track M, it takes from **ECM and rho**: at 96, ECM's band-24 catches fall 68 → 35 and rho's band-20 catches 71 → 45, with p-1 taking 38 and 21.
- p-1 catches in bands 24–36, pooled over sizes, (c+p): Track R 111 / 204 (54%), Track M 221 / 364 (61%).

**Selected-k check** (information; `kcheck.out`; scoring only, on the map numbers):
- The median selected k is 2–3 in every genome, current and new; k = 1 is the most common pick. The 90th percentile is 7–29.
- All selected k are squarefree, in every genome: KS never picks a non-squarefree k, so including them in the list only costs their scoring.
- **kc is not flat:** the selected k stays the same for all kc ≥ 59–61 only. Between kc 32 and 64 it changes on 5–11% of the numbers.
- *Demand vs drift* (information; `dvd.out`; adopted for future rounds; R@96 is the only winner with bound hits):
  - **kc 60 is drift:** against the interior median 31, the winner is −0.0075 log₂ [−0.019, +0.003].
  - **tc 1.035 is demand:** against the interior median 1.40, the winner is −0.129 log₂ [−0.140, −0.118].
  - With lc 1.97, the low tc keeps tc + lc near 3.0, so the threshold, not tc as such, is what is demanded. That is consistent with the reparameterization MOVES row.
- *Check E:* the new M@72 genome uses s = 4, where the current final one used s = 3. Its re-solve kept ECM at 17,867, the same as with the s = 3 genome. This is weak evidence against tying the ECM budget to s at 72, and it does not test the 84 dip.

**Predictions, scored as written.**
- *The user's:*
  - (K1) kc > 32 in ≥ 2 of the bound-hit cells (R@72 36, R@84 60, M@54 12, M@84 44: three); gain (c) → (d) ≤ 4% at every size: **missed.** The kc clause held, but the gain was 13.5% / 12.7% at 54, 9.1% at M@72, 6.4% at M@84 and 4.3% at M@96, mostly from p-1.
  - (K2) PD_M and PD_R within 0.15 of the final round at 72–96: **missed** (PD_R at 72: 1.637 against 2.087). The other five values are within 0.06.
- *Mine:*
  - (L1) kc > 32 in ≥ 3 of 8 (five) and lc > 2.0 in ≤ 2 (none): **held.**
  - (L2) (c+p) lower in all eight cells, interval excluding 0 in ≥ 6, Track R 1–6%, Track M 3–10%: **missed.** Lower in all eight, but significant in five (Track R only at 54), and Track R at 54 gained 8.5%.
  - (L3) (d) against (c+p) ≤ 2% everywhere: **missed** (5.4% at R@54 and M@54).
  - (L4) PD_R at 72 falls by more than 0.15; PD_R at 84–96 and PD_M at 72–96 within 0.15: **held.**
  - (L5) Track M at 72 settles within two re-solves: **held** (first re-solve).
- *DeepSeek's (pre-registered):*
  - (D-b1) kc hits 64 for Track R at 72 and 84 (36 and 60); Track M settles at 20–40 (12 / 46 / 44 / 19): **missed.** By its scoring rule, kc hit 64 again (R@84, R@96): "kc is effectively unbounded". The selected-k check and the demand-vs-drift test say the hits are drift: they matter for 5–11% of numbers, and the R@96 kc hit is within noise against kc 31.
  - (D-b2) lc hits 2.5 for Track R at 96 (1.974); Track M lc 1.8–2.2 (1.61–1.79): **missed.**
  - (D-b3) gain 3–8% Track R at 72–84 (1.8%, 2.9%), 1–3% Track M (4.3–12.7%), PD unchanged within intervals (PD_R at 72 and 54 move outside): **missed.**
  - (D-c1) at 84–96: Track R lc 1.7–1.9 (1.737, 1.974), Track M lc 1.9–2.1 (1.792, 1.613), neither above 2.2 (held), tc 0.7–1.1 (1.27, 1.04, 1.27, 1.30), tc + lc 2.6–3.0 (3.005, 3.009, 3.058, 2.908), lc(96) − lc(72) in [0, 0.2] (R +0.276, M −0.037): **missed.**
  - (D-k) median selected k at 84 is 15–35 (it is 3 for both tracks' genomes), 90th percentile under 50 (29 and 22): **missed.** By DeepSeek's decision rule (median < 20), retire kc as a gene.
- *Grok's (pre-registered):*
  - (G-b1) Track R kc mostly ≥ 40 (two of four: 60, 60), several at 64 (two), lc 1.6–2.2 (held), gain 3–12% largest at 84–96 (13.5% at 54, 1.8–3.7% at 72–96), no size loses > 2% (held): **missed.**
  - (G-b1 revised, recorded, not scored) Track R lc 1.5–1.9 at 84–96 (1.737; 1.974 outside); Track M 1.4–1.8 (1.792, 1.613); tc + lc in range. *Direction:* neither holds consistently. At 84 Track M's frozen lc is above Track R's (1.792 vs 1.737); at 96 it is below (1.613 vs 1.974).
  - (G-b2) Track M kc moves up less than Track R's (mean change +8 against +18.5: held); ECM budgets within one grid step after the re-solve: **missed** at 54 (ECM off → 6,317). It held at 72–96.
  - (G-p1) stage-1 p-1 catches mostly from bands 24–36: **held** (54% Track R, 61% Track M).
- Tally: the user's 0 of 2. Mine 3 of 5. DeepSeek's pre-registered 0 of 4 (D-b1, D-b2, D-b3, D-c1) plus D-k missed. Grok's 1 of 3 (G-p1).

**Conditions.**
- Winners selected on the sealed numbers among seven candidates per cell; the replacement test (queued) uses its own fresh set.
- p-1's budgets were chosen on the maps (in-sample) and scored here on fresh numbers.
- Track M at 54 moved at the re-solve and was not retuned (by protocol).
- Track R's p-1 gain at 72–96 is within noise under ruint.

**Outside context: threshold slack against relation type** (user, Mathematica, Oct 25; 18-digit N, B = 3000, 20,000 sieve values with exact per-x sizes; slack t in units of log₂ B; 525 full relations and 4,751 partials below B²).
- *Shortfall bands* (how far a value falls short of the sieve estimate): full relations 0 to ~1, partials ~1–2.3, useless candidates ~2–3.8.
- *Sieving every prime* (full caught / partials caught / candidates per useful relation):

| slack t | full caught | partials caught | candidates per useful relation |
|---|---|---|---|
| 2.0 | 100% | 68% | 1.00 |
| 2.2 (tc + lc − 1 at tc 1.38, lc 1.8) | 100% | 84% | 1.10 |
| 2.5 | 100% | 97% | 1.45 |
| 3.0 | ~100% | ~100% | 2.43 |

- Partials need about one unit more slack than full relations. This supports the coupled threshold (context for Grok's disputed view under "Grok, after the user's Mathematica lc result").
- *In our card*, the slack is t = tc + lc − 1, since T = log₂(M√(kN/2)) − (tc + lc − 1)·log₂ B. The kc / lc round's frozen genomes sit at t = 1.91–2.28 (tc + lc 2.91–3.28): the region where full relations are all caught and most partials are, before candidates per useful relation climb.
- *Skipping primes below 30:* about 0.5 units of extra slack are needed for the same catch (at t = 2.0: 93% of full relations and 21% of partials). This is context for the "Small-prime variation in the qs sieve" MOVES row.

## 2026-10-25 — Decision (user): kc becomes a constant; cost model for the `kset` option (before code)

**Decision (user, Oct 25).** The qs card scores squarefree k ≤ 32 only and keeps the Knuth–Schroeppel winner; the fallback order is unchanged. kc leaves the gene list for future rounds. The frozen reference (qs + lc 1.4, enumerate) keeps its own kc.
- *Basis:* the median selected k is 2–3 and always squarefree (`kcheck.out`), and R@96's kc 60 against 31 is drift (−0.0075 log₂, interval includes 0; `dvd.out`).

**Card option `kset`** (not a gene; set by hand like `a_mode`; never mutated or tuned).
- `"kset": "sf32"` makes the candidate multipliers the 20 squarefree integers ≤ 32 (1, 2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31), and kc is ignored.
- Absent: today's card, op for op (candidates 1 … kc). Every existing genome and the frozen reference are unchanged.
- *Order:* candidates are ranked by KS score, best first, ties to the smaller k, exactly as now; a failed attempt moves to the next k, as now.
- *Charges:* the same per-candidate charges as today, with the candidate count 20 in place of kc:
  - "mult" 20 × |KS_PRIMES| = 20 × 14 = 280 ops for the scores;
  - under sort_charge, sort_cost(20) = 20 · ⌈log₂ 20⌉ = 100 ops for the ranking.
  - The list itself is a constant in the card (like KS_PRIMES), so forming it is not charged.
  - So the multiplier phase costs exactly what kc = 20 costs today; only which 20 k's are scored changes.
- *Acceptance:*
  - Identity: with `kset` absent, lampcore is unchanged on the map numbers (per type, per number).
  - With `kset` = sf32, the multiplier-phase charge equals today's kc = 20 charge, and every other phase follows from the selected k. The selected k equals the top squarefree KS pick (checked in Python against `kcheck.py`'s scoring).
  - Python = Rust parity pairs: kset with both a_modes, sort_charge, a retry and a low cap.
- **Corrected card for future rounds:** a_mode = on_demand, sort_charge = 1, kset = sf32. Past results keep their recorded cards.

**Item 1 (user's order, Oct 25): the slack observation.**
- The user's threshold-slack context is recorded above under "Outside context: threshold slack against relation type". It covers the shortfall bands, the catch table at t = 2.0 / 2.2 / 2.5 / 3.0, and about 0.5 units more slack when skipping primes below 30.
- **Observation:** all eight frozen genomes of the kc / lc round have slack tc + lc − 1 between 1.91 and 2.28 (R 2.06 / 2.23 / 2.01 / 2.01; M 2.28 / 2.19 / 2.06 / 1.91 at 54 / 72 / 84 / 96). That is the Mathematica knee: every full relation and most partials are caught before candidates per useful relation climb.
- **R@96's tc "demand"** (tc 1.035 with lc 1.97; `dvd.out`) is demand for slack near 2.0. It is a product of the tc / lc coupling: with lc at 1.97, only a tc near 1.0 keeps the slack there. Replacing tc by the interior median 1.40 at the same lc raises the slack to 2.37, past the knee.
- This is added as evidence on the "qs threshold reparameterization" MOVES row.
- **Open (user, Oct 25):** the Track M 54-bit retune (its budgets moved at the kc / lc re-solve: rho off, ECM on) is skipped for now.

**Item 2 (information only; no card change): sieve-update share and small-prime share** (`evolve/sieveshare.py`, `sieveshare.out`). Each track's kc / lc-round (d) winner, run as qs alone.
- The sieve-update share is from lampcore per-type counts on all map numbers.
- The share from primes below 30 is from exact per-polynomial update counts in Python's trace, (width − 1 − start) // p + 1 per root, as the card charges (asserted equal to the charged total per polynomial). It uses 4 map numbers per size and track (2 balanced, 2 band 24).

| bits | track | sieve updates / qs cost: official ops / ruint / Montgomery | updates from primes < 30 |
|---|---|---|---|
| 54 | R | 0.339 / 0.095 / 0.112 | 0.781 |
| 54 | M | 0.413 / 0.142 / 0.169 | 0.815 |
| 72 | R | 0.413 / 0.153 / 0.169 | 0.668 |
| 72 | M | 0.524 / 0.295 / 0.320 | 0.643 |
| 84 | R | 0.480 / 0.232 / 0.245 | 0.727 |
| 84 | M | 0.525 / 0.290 / 0.305 | 0.728 |
| 96 | R | 0.547 / 0.322 / 0.331 | 0.680 |
| 96 | M | 0.534 / 0.328 / 0.338 | 0.677 |

- Primes below 30 give two thirds to four fifths of all sieve updates. The card charges 1 op per update whatever p is, and the KS multiplier favours kN being a residue mod small primes, so small primes are over-represented in the factor base.
- *Sizing the small-prime-variation row* (upper bound, before the offset): skipping primes below 30 would remove 0.64–0.82 of sieve updates. That is ~22–40% of qs's official ops, but only ~6–25% of its ruint and Montgomery cost, where sieve updates are cheap.
- The offset is about 0.5 log₂ B units more slack for the same catch (user's Mathematica), which means more candidates confirmed by trial division (charged).
- Recorded as information on the MOVES row; untested.

**DeepSeek, before any stage-2 code** (labelled as DeepSeek's; recorded Oct 25).
- **(D-m1) Stage-2 method.**
  - Implement prime-gap stepping first (~2 multiplies per prime) as the clean reference, then paired baby-step giant-step (~1 per prime plus setup ~2√B2).
  - Paired wins by 1.5–1.7x under ruint and Montgomery and ties (~1.0x) under official, because the pairing bookkeeping (~1 small op per prime) is charged at multiply price there.
  - *Meter audit:* if paired also wins clearly under official, the pairing bookkeeping is undercharged. If pairing sorts, the charged sort (~π(B2) log₂ π(B2), ~80k at B2 = 2^16) makes it lose; bucket by gap instead.
- **D-s1 REVISED again** (still pre-registered; no stage-2 code exists): Track R on at 54 (B 2^10, B2 2^13–2^14, c ~8–16) with gain 6–10% over stage-1-only. At 72–96 the gain is 1–3%, undecided (if on, B 2^11 and B2 2^14). The best stage-1 B falls from ~2^12 to 2^11. Falsified if the Track R 54-bit gain is under 3%.
- **D-s2 REVISED again:**
  - Track M on at all sizes; gain 5–8% at 54, 8–12% at 72–84, 4–7% at 96;
  - c 20–50 (paired) or 10–25 (gap stepping);
  - ECM falls one grid step at 72–84;
  - at 54, rho stays off and ECM and p-1 share the small-band work.
  - (Its heading said "rho returns", but the prediction says rho stays off; the prediction is scored.)
- **(D-r54)** Track M at 54 after a settled re-solve: rho stays off, ECM within 1–2 grid steps of 6,317, and PD_R improves. *Note:* DeepSeek gave the current PD_R at 54 as 1.20–1.36; the current (d) value is 1.85, and "improves" is scored against 1.85. (The Track M 54-bit retune is open, skipped for now by the user.)
- **(D-knee)** The frozen slack tc + lc − 1 stays within 1.9–2.3 in future rounds; above 2.5 would mean the threshold or slack accounting changed. **A standing check for every round that tunes tc or lc.**

**Grok, before any stage-2 code** (labelled as Grok's; recorded Oct 25; pre-registered).
- **G-s1 / G-s2 REVISED** (assumes paired baby-step giant-step stage 2, ~1 multiply per prime):
  - Track R: 54 B 2^10–2^11, c 10–20, gain 4–8%; 72 B 2^11, c 15–25, 3–6%; 84 B 2^11–2^12, c 10–20, 2–5%; 96 B 2^12, c 10–15, 1–4%; ECM stays off.
  - Track M: 54 B 2^10, c 20–40, 6–12%; 72 B 2^11, c 20–50, 5–10%; 84 B 2^11–2^12, c 15–40, 4–9%; 96 B 2^12, c 10–30, 3–7%; ECM falls about one grid step at 84 and 96.
- **(G-m1)** Paired BSGS against prime-gap stepping, on stage 2: under official at most 1.1–1.3x, or a tie; under Montgomery 1.3–1.8x (outside that range means the pairing cost model needs adjusting); smaller under ruint.
- **(G-r54)** Track M at 54 after a settled re-solve: rho stays off; ECM 4k–8k (most likely 5k–7k); ruint penalty 0.3–0.6 log₂; the same shape on a second fresh set.

**The user's prediction** (labelled as the user's; recorded beside G-m1 and D-m1, both of which put the paired advantage under Montgomery at 1.3–1.8x):
- **(W-m)** Pairing trades multiplies for small-op bookkeeping, so its advantage scales with the multiply-to-small-op price ratio. It should be largest under ruint and near a tie under official, and also near a tie under Montgomery if Montgomery prices a small op near a multiply.
- *Scoring:* W-m, G-m1 and D-m1 are scored against the measured stage-2 cost per pricing once both stage-2 methods exist.

**Small-op / multiply price ratios** (information; the price table `P.prices()`, the median of the three calibration runs, normalized to 1 full modmul of N):
- *official:* 1 : 1 for every op.
- *ruint:* word-level small ops (sieve_scan 0.012, la 0.017, sieve_update 0.034) at 0.01–0.03; small-modulus ops at 0.11–0.31 (confirm_td and lp_small 0.114, td_mod 0.146, setup_small / fb / mult 0.307); gcd 7.9.
- *Montgomery:* word-level small ops at 0.05–0.13 (sieve_scan 0.047, la 0.063, sieve_update 0.125); small-modulus ops at 0.43–1.14 (confirm_td and lp_small 0.426, td_mod 0.55, setup_small / fb / mult 1.137); gcd 29.1.
- So **Montgomery prices small ops about 3.7x higher relative to a multiply than ruint does**, because its multiply is cheaper (7.4 ns against 27 ns).
- If pairing bookkeeping is charged as a word-level op, it costs ~0.01–0.03 of a multiply under ruint and ~0.05–0.13 under Montgomery: the advantage holds under both, largest under ruint. If it is charged as a small-modulus op (like setup_small), it costs ~0.3 under ruint and ~1.1 under Montgomery: then Montgomery ties, as W-m allows.
- Which type the stage-2 cost model assigns to the bookkeeping is part of that cost model.

**Fixed before any stage-2 code or result (user, Oct 25): how stage-2 operations are typed.**
- The pm1 stage-2 cost model classifies every stage-2 operation by what it physically is, and that classification is stated in NOTES before implementation.
- **Pairing and bucketing bookkeeping** (prime-gap indexing, pair tables, bucket placement, loop counters) is index arithmetic on machine-word integers. It is charged at the **word-level price**, like sieve_update. The exception is an operation that actually reduces modulo a small prime, which is charged as a small-modulus op.
- Products and multiplications mod N are full multiplies; the final gcd is a gcd.
- This is fixed now because it decides W-m, G-m1 and D-m1: under word-level pricing, the bookkeeping costs ~0.01–0.03 of a multiply under ruint and ~0.05–0.13 under Montgomery.
- **Beside D-m1:** the price table puts a gcd at 7.9 multiplies (ruint) and 29.1 (Montgomery), not ~50. DeepSeek's correction (one gcd per candidate overstates the cost against one accumulated product and a final gcd) still holds, by that smaller factor.

## 2026-10-25 — Replacement-rule test, final Track R genes (protocol and predictions before the run)

**Card.** The corrected card: a_mode = on_demand, sort_charge = 1, kset = sf32 (kc constant).
- This assumes the kset parity suite passes. If it fails, this entry is amended before anything runs: the genes run as they are, without kset.
- The final Track R genes are the kc / lc round's (d) winners: R-k@54, R-k@72, the round-3 genome at 84 (current final) and R-k@96. Under kset their kc is ignored.

**Fresh set, per size (54 / 72 / 84 / 96)** (seeds checked unused; every number through oracle.check):
- 240 balanced numbers, `semiprimes_pq(bits, 240, 9600000 + bits)`;
- a banded population, `SS.pop(bits, 80, 9430000)` (9430000 + 100 pb + bits; the top band is balanced).

**Two comparisons, both on the same numbers, every genome as qs alone** (user's design, Oct 25):
- **(2) as-frozen:** the final Track R genes on the corrected card against the frozen reference (qs + lc 1.4, enumerate, old card). **The pre-registered rule scores this comparison** (the replacement decision as the rule was written).
- **(1) card-matched:** the same genes against qs + lc 1.4's genes on the same corrected card (with kset). Reported beside (2), so the card fix is not credited to the genes.

**The rule** (as pre-registered in generalization test (2), plus the per-band gate). Recommend replacing only if all hold:
- at every size, no pricing's paired interval on the balanced numbers lies above 0;
- no misses (balanced and banded);
- pooled over the four balanced sets (960 numbers), all three pricings below 1 with intervals excluding 0;
- the per-band 1.5x gate on the banded set (every band, all three pricings, as in the two-track rule) does not FAIL.

The rule recommends; changing the reference is the user's decision.

**Information:**
- each genome in its (d) pipeline (rho, p-1 B, ECM from the kc / lc round) against both references, on the balanced numbers and on the banded set. The balanced-only ratio is reported per size for the full pipeline and for the genes as qs alone, which separates early-stage overhead from the genes;
- the median per-number log₂ ratio beside each mean.

**Predictions (DeepSeek's, labelled as DeepSeek's).**
- **D-m1 REVISED** (pre-registered; assumes word-level bookkeeping, conditional on bucketing): paired BSGS beats prime-gap stepping by 1.75–1.95x under ruint, 1.55–1.75x under Montgomery and 0.95–1.10x under official. *Meter check:* the same ratio under ruint and Montgomery would mean the bookkeeping charge is not reaching the pairing code. If pairing sorts, expect below 1.0x.
- **(D-p1)** p+1, ordered after p-1 and a p-1 extension, pays 1–3% only at 84–96, Track M only, and only with a p-1 stage 2 present. More than 5% anywhere would mean extending p-1 is worse than the user's Mathematica suggests. Practical: exclude square D; prefer small D.
- **(D-rep)** Replacement rule: FAIL at 54–72; at 84–96, pass only if the final genes' mc < 0.7 (they are 0.39–0.60), by under 5% robust. Scored on comparison (2), as written.
  - *Note beside it:* its reasoning assumed the final Track R genes cost 5–17% more under official; that was the Run 8 mixed-qs genes. The final Track R genes beat qs + lc 1.4's genes under all three pricings at every size (4–28%, corrected card, size-scaling round 1).
  - "FAIL at 54–72" is read per size: some pricing's balanced interval lies above 0 at 54 or 72. "Pass at 84–96 by under 5%" is read as the robust balanced ratio of (2) in 0.95–1.00 at 84 and 96.

**Predictions (Grok's, labelled as Grok's).**
- **G-m1 REVISED** (assumes word-level pairing bookkeeping; stage-2 work only): paired against prime-gap stepping 0.9–1.2x under official, 1.4–1.9x under ruint and 1.2–1.5x under Montgomery. DeepSeek's revised D-m1 is 0.95–1.10 / 1.75–1.95 / 1.55–1.75; both are reported against the measurement.
- **(G-p1b)** p+1 earns a slot only if p-1 has an efficient stage 2 and a large bound, or the population has a residual band where p-1 is rough and p+1 smooth; until then it is low priority.
- **(G-rep)** Pass at 84 and 96; borderline or fail at 54 and 72 on balanced numbers, which lose 5–15% there (early-stage budget that balanced numbers never use); at 84–96 balanced numbers pass too. Grok's own threshold, which scores only G-rep: fail if any size's balanced loss exceeds 10% or any per-band robust ratio exceeds 1.5x. *Scoring (mine):* the balanced loss is read from the (d) pipeline row on the balanced numbers against the frozen reference, which is what Grok's mechanism refers to. The qs-alone row is reported beside it.

**Predictions (mine).**
- (X1) Card-matched (1), robust balanced ratio: 0.85–1.00 at 54, 0.80–0.92 at 72, 0.70–0.85 at 84 and 0.65–0.80 at 96. All three pricings below 1 at 72–96.
- (X2) As-frozen (2): lower than (1) at 84–96, because the frozen reference enumerates C(P, 4) A's there. Within 0.05 of (1) at 54–72. Robust balanced ratio 0.85–1.02 at 54, 0.75–0.92 at 72 and 0.45–0.70 at 84–96.
- (X3) The rule passes on (2), and also on (1).
- (X4) The per-band gate PASSes at every size, in both comparisons.
- (X5) On balanced numbers, the (d) pipeline costs 1–8% more than the genes as qs alone, more under ruint (where rho and p-1 multiplies are relatively dear) than under official.

**The rule's balanced-number condition, verbatim, and what it compares** (user's request, Oct 25). This arrived after the predictions above were committed (1c715b4) and before anything ran.
- *Verbatim* (generalization test (2), "Replacement rule (decided now)"):
  > Recommend replacing the reference only if all of these hold:
  > - at every size, no pricing's paired interval lies above 0 (the new qs is never clearly worse);
  > - no misses;
  > - pooled, all three pricings are below 1 with intervals excluding 0.
  >
  > Otherwise, qs + lc 1.4 stays the reference, and the new genes are a mixed-population qs.
- *What it compares:* the design ran "Genomes, each alone": the candidate **qs genes alone** against the reference qs alone, on balanced numbers (`semiprimes_pq(bits, 240, …)`). It compares qs genes against reference qs genes, not full pipelines. Comparison (2) above matches it; the (d)-pipeline rows are information only.
- *Correction to the outside implication:* the earlier 13–28% balanced loss at 54–72 bits (the Run 8 mixed-qs genes, official) was also qs alone, with no front end. It was a gene effect, not the front-end surcharge.
- **Amendment, before the run (pooling as written):** the original "pooled" figure was the **mean over sizes of the per-size log₂ ratio** (its table: "pooled (mean of per-size log2)"). `replace_r.py` first pooled by concatenating the 960 numbers into one mean-cost ratio, which weights the 96-bit numbers most. It now uses the mean of the per-size log₂, with a bootstrap that resamples each size's numbers.

**Outside context for the (d)-pipeline balanced rows** (user, Mathematica toy pipeline: rho, then stage-1 p-1, then qs at flat cost Q; bands 16–42 bits, 2,000 primes each; rho length ~ Rayleigh with mean √(πp/2); 1 op per rho step or p-1 squaring).
- At the mixed-population optimum, a rho + p-1 front end costs ~1.20x qs alone on balanced numbers at every Q: 1.205 (Q 1e4: rho 2,048, p-1 off), 1.200 (Q 1e5: rho 16,384, B 2^12) and 1.216 (Q 1e6: rho 262,144, B 2^14). The optimal front-end budget scales with Q (~20% of it), so the balanced surcharge is structural.
- The mixed-population cost against qs alone is 0.865 / 0.578 / 0.283. The worst band is 1.2x, under the 1.5x gate.
- As the balanced share rises from 0 to 0.9, the best rho budget falls from 16,384 to 1,024. p-1 holds until ~0.8, and everything is off only at 100% balanced.
- *So* a ~20% balanced surcharge for the full pipeline is the expected price of the front end, not a gene effect. The qs-alone rows carry the gene comparison.
- My X5 (the (d) pipeline costs 1–8% more than qs alone on balanced numbers) stands as written. Our front-end budgets are far below 20% of qs's cost (e.g. rho 10,624 + p-1 ~6,200 ops at 96 bits against qs's ~10^6), so X5 and the toy differ in their assumption about budget size, and the run will show which holds here.

**Population-generator fault found by the oracle (Oct 25, before any replacement-test measurement).**
- The banded set `SS.pop(54, 80, 9430000)` contained (10087959220554499, 15829633, 637283203). The "prime" 15,829,633 = 43 × 547 × 673 is a **Carmichael number** (42, 546 and 672 all divide n − 1).
- `lamps.rand_prime` tests candidates with Fermat tests to bases 2, 3, 5, 7, 11 and 13, which every Carmichael number coprime to those bases passes.
- `oracle.check` rejected it, and the run stopped before measuring anything. This is a harness fault, not a meter fault: no charged path generates numbers.
- **Fix (harness only):** `rand_prime` uses a strong (Miller–Rabin) test to the 12 bases 2 … 37, deterministic for n < 3.3 × 10^24 (all our primes are ≤ 50 bits).
- *Why no committed population changes:* a strong test accepts every prime, and it rejects a candidate only if the Fermat test would also reject it or the candidate is composite. So the random sequence differs from before only where the old test accepted a composite. Every committed population has passed `oracle.check` (no composites), so each regenerates identically. This is checked by regenerating them (`oracle.py`, and the map rows' N against `map_nums`).
- The pre-registered fresh sets change only from the rejected draw on: the 54-bit band-24 subset of the 9430000 set. The seeds and the protocol are otherwise as registered.
- *Check:* 31 population calls were regenerated with the old (Fermat) and new (strong) generator: every size-scaling set (9300000 / 9400000 / 9410000 / 9420000 / 9430000 / 9500000 at all four sizes), the four 9600000 balanced sets, `calibrate.pops()` and both partition populations. **Only `SS.pop(54, 80, 9430000)` differs**, as expected. The strong test agrees with sympy on 20,000 random odd n of 8–50 bits.

**Grok, before the replacement test** (labelled as Grok's).
- *Timing disclosure:* the user's message arrived after the replacement test had started (relaunched after the generator fix), but **before any of its output was read**. Its predictions are recorded as pre-registered on that basis.
- **(G-sat)** The optimal rho budget scales linearly with downstream cost Q until it clears the small-factor population, then saturates; in our setup, not before ~110–130 bits.
  - *Note beside it:* Grok's earlier G-rho predicted that rho goes to zero at 110–130 bits. Saturating (the budget stops growing) and switching off are different claims; both are recorded as given.
- **(G-rep2)** Balanced numbers, qs alone, log₂ ratios (official / ruint / Montgomery ranges):

| bits | (2) as-frozen | (1) card-matched |
|---|---|---|
| 54 | −0.05..+0.10 / −0.05..+0.12 / −0.05..+0.10 | +0.05..+0.20 / +0.05..+0.22 / +0.05..+0.20 |
| 72 | −0.10..+0.05 / −0.08..+0.08 / −0.10..+0.05 | −0.02..+0.12 / −0.02..+0.15 / −0.02..+0.12 |
| 84 | −0.15..−0.02 / −0.12..+0.02 / −0.15..−0.02 | −0.12..+0.02 / −0.10..+0.05 / −0.12..+0.02 |
| 96 | −0.18..−0.05 / −0.15..−0.02 / −0.18..−0.05 | −0.15..−0.02 / −0.12..0.00 / −0.15..−0.02 |

  - *Note beside (2):* it implies a small card effect. The earlier measurement put the Track R winners at 0.81 / 0.35 / 0.66 of the frozen reference at 54 bits (full pipeline, mixed population), mostly from the card. Scored as written, cell by cell (a cell holds if the measured log₂ lies in its range).
- **Grok's view on the reference:** keep one formal reference, plus a side table of the card-matched comparison at every size. This matches the adopted default (the frozen reference stays formal; card-matched comparisons are reported beside it).

## 2026-10-25 — pm1 stage 2: cost model (before any code; item 4 of the user's order)

**Scope.** This is the cost model only; no code exists. When built, it goes into Python (`lamp_pm1`) and lampcore together, with parity, and is scored against the pre-registered predictions: DeepSeek's D-s1 / D-s2 (revised twice), D-s3, D-m1 (revised) and D-p1; Grok's G-s1 / G-s2 (revised), G-m1 (revised) and G-p1b; and the user's W-m.

**Genes and options.**
- `c`: B2 = c · B. **c = 0 or absent means no stage 2: today's card, op for op.** Searched over at least 5–200 (the user's Mathematica: the best c depends on the per-prime stage-2 cost).
- `s2`: the method, "gap" (prime-gap stepping) or "pair" (paired baby-step giant-step). It is an option, not a tuned gene, so both methods are measured and compared.

**Order of work** (stage 1 unchanged):
1. Stage 1 as now: b = 2^E mod N with E = Π p^e ≤ B; charged bit_length(p^e) "mul" per prime power, then 1 gcd(b − 1, N). If that gcd is nontrivial, the card returns as now and stage 2 does not run.
2. Stage 2 runs only if the stage-1 gcd is 1. It accumulates acc = Π (f-difference) over the primes in (B, B2], then takes one gcd(acc, N).

**Classification of every stage-2 operation, by what it physically is** (user's rule, fixed before code):

| operation | what it is | type charged | official | ruint | Montgomery |
|---|---|---|---|---|---|
| multiply or square mod N (table steps, ladders, giant steps, acc ← acc · d) | full multiply of N-size residues | "mul" (as stage 1) | 1 | 1 | 1 |
| d = X − Y mod N (one per accumulated factor) | multi-limb subtraction, no multiply | word-level, priced as sieve_update | 1 | 0.034 | 0.125 |
| gap q − q_prev, table index, q div D and q mod D, bitmap set, test and scan, loop counters | index arithmetic on machine-word integers | word-level, priced as sieve_update | 1 | 0.034 | 0.125 |
| the final gcd(acc, N) | gcd | "gcd" | 1 | 7.86 | 29.06 |

- No stage-2 operation reduces modulo a small prime, so none is typed small-modulus.
- *Mod-N additions and subtractions:* the ECM card's cost model counts them as free ("additions free"). Here they are charged at the word-level price, by the user's classification rule. The ECM card is not changed by this entry; the mismatch is flagged for the user's decision.
- *The prime list (B, B2]* does not depend on N. It is treated as a precomputed table, as stage 1's primes ≤ B and the ECM card's prime list are today (both uncharged). This is an existing convention, and it is flagged here so that it is a stated decision rather than an omission. Scanning the list (one word op per prime) is charged.
- *Implementation:* a word-level type means a new per-type column ("pm1_word") whose ruint and Montgomery prices are set equal to sieve_update's calibrated price, with no new calibration. Official counts it as 1 op, like every op.

**(gap) Prime-gap stepping.** For the primes q₁ < q₂ < … in (B, B2]:
- *Table:* D[d] = b^d for even d up to the largest gap g_max. Cost: 1 "mul" for b², then 1 "mul" per further entry, so g_max/2 "mul" in all.
- *Start:* X = b^{q₁} by left-to-right square-and-multiply: (bit_length(q₁) − 1) squarings plus (popcount(q₁) − 1) multiplies, all "mul".
- *Per prime:* 1 word op (gap) + 1 word op (index) + 1 "mul" (X ← X · D[gap]) + 1 word op (X − 1) + 1 "mul" (acc ← acc · (X − 1)). So **2 "mul" + 3 word ops per prime.**
- acc starts at 1, so its first product counts as a "mul" like the others.
- *End:* 1 gcd.
- Total ≈ 2 π(B2..B) + g_max/2 + 1.5 log₂ q₁ "mul", + 3 π(B2..B) word ops, + 1 gcd.

**(pair) Paired baby-step giant-step** (Montgomery's pairing, with f(n) = b^{n²}, so one factor f(kD) − f(j) catches both kD − j and kD + j):
- *D:* 210 if B2 ≤ 2^17, otherwise 2310. It is a constant of the card, not a gene; the table is recorded with the code.
- *Baby table:* f(j) = b^{j²} for j < D/2 coprime to D, built by second differences: b^{(j+2)²} = b^{j²} · b^{4j+4} and b^{4(j+2)+4} = b^{4j+4} · b^8. That is 2 "mul" per odd j up to D/2 (D/4 odd j's), plus 3 "mul" for b², b⁴ and b⁸ (b^{4·1+4} = b⁸ starts the difference chain, and f(1) = b).
- *Giants:* G_k = b^{(kD)²} for k from ⌊B / D⌋ to ⌈B2 / D⌉, by second differences: b^{((k+1)D)²} = G_k · b^{(2k+1)D²}, with b^{(2k+3)D²} = b^{(2k+1)D²} · b^{2D²}. That is 2 "mul" per giant step, plus a start-up of two ladders (b^{(k₀D)²} and b^{(2k₀+1)D²}, square-and-multiply as above) and one for b^{2D²}.
- *Pairs:* for each k, the set of j with kD − j or kD + j prime in (B, B2]. Each prime q costs 2 word ops (q div D, q mod D; folded to j ≤ D/2) + 1 word op (set the pair's bit).
- *Per pair* (k, j) with at least one of kD ± j prime: 1 word op (test and scan the bit), 1 word op (G_k − f(j)), 1 "mul" (acc ← acc · d). A pair with both primes costs once: that is the pairing gain.
- *Bucketing, not sorting:* primes are assigned to (k, j) directly by div and mod, so there is no sort (DeepSeek's D-m1 note: a charged sort would cost ~π(B2) log₂ π(B2) and make pairing lose).
- *End:* 1 gcd.
- Total ≈ (number of pairs) + 2 · (number of giants) + D/2 + ladders "mul", + 3 π(B2..B) + 2 · (number of pairs) word ops, + 1 gcd. Here number of pairs = π(B2..B) − (pairs with both primes), and number of giants ≈ (B2 − B) / D.

**Expected per-prime costs, before measurement** (information; the scored predictions are the outside ones above):
- (gap): 2 "mul" + 3 word per prime.
- (pair) with D = 210 and B2 ~ 2^15–2^17: per prime, ~0.8–0.9 "mul" for the pairs (10–20% of pairs carry both primes at these sizes), plus ~0.1–0.3 "mul" amortized giants and babies, plus ~4–5 word ops.
- So under official, pair ≈ 1.0–1.2 "mul"-equivalents + 4–5 word ≈ 5–6 ops per prime, against gap's 5. It roughly ties or loses slightly.
- Under ruint and Montgomery the word ops are cheap (0.034 and 0.125), so pair costs ~1.1–1.4 and gap ~2.1–2.4 multiply-equivalents per prime: about 1.6–2.0x in pairing's favour, somewhat less under Montgomery than under ruint.

**Charging points and acceptance (for the code, later).**
- Every op above is charged where it is performed, in both cores.
- Acceptance:
  - c absent or 0 is today's card on all map numbers;
  - the stage-2 charge equals the formula from a trace (primes, pairs, giants, table sizes) on a sample;
  - a number whose p − 1 is (B, B2]-smooth-except-one-prime is caught by both methods;
  - both methods find the same set of factors on the map numbers when given the same B and B2;
  - Python = Rust parity, per type.
- In pipelines, pm1's ob must cover stage 1 + stage 2; the pipeline sets ob from the formula's upper bound.

### Replacement-rule test: results (`evolve/replace_r.py`; `replace_r.out`, `replace_r.json`)

The final Track R genes run as qs alone on the corrected card with kset = sf32. Fresh sets: 240 balanced numbers per size (9600000) and banded populations (9430000, 80 per band). No misses anywhere (1,920 balanced and 2,000 banded numbers per comparison).

**(2) As-frozen (scored): against the frozen reference (qs + lc 1.4, enumerate), balanced, log₂ [95%]:**

| bits | official | ruint | Montgomery | robust ratio [95%] | per-band gate (banded) |
|---|---|---|---|---|---|
| 54 | −0.237 [−0.261, −0.213] | −1.613 [−1.645, −1.582] | −0.738 [−0.764, −0.713] | 0.849 [0.834, 0.863] | PASS (upper 0.93) |
| 72 | −0.196 [−0.233, −0.161] | −0.908 [−1.027, −0.807] | −0.506 [−0.562, −0.457] | 0.873 [0.851, 0.894] | PASS (0.99) |
| 84 | −0.394 [−0.427, −0.362] | −1.731 [−1.825, −1.639] | −0.965 [−1.012, −0.918] | 0.761 [0.744, 0.778] | PASS (0.83) |
| 96 | −0.460 [−0.497, −0.421] | −1.551 [−1.590, −1.506] | −0.967 [−1.004, −0.925] | 0.727 [0.709, 0.747] | PASS (0.79) |
| pooled (mean of per-size log₂) | −0.322 [−0.339, −0.305] | −1.451 [−1.492, −1.412] | −0.794 [−0.817, −0.772] | | |

**The replacement rule PASSES:** no pricing's interval lies above 0 at any size, there are no misses, all three pooled values are below 0 with intervals excluding 0, and no per-band gate fails. The rule recommends replacing the frozen reference; **changing it is the user's decision.**

**(1) Card-matched (reported beside it): against qs + lc 1.4's genes on the same corrected card (with kset), balanced:**

| bits | official | ruint | Montgomery | robust ratio | per-band gate |
|---|---|---|---|---|---|
| 54 | +0.013 [−0.010, +0.035] | −0.175 [−0.204, −0.147] | −0.226 [−0.250, −0.202] | 1.009 [0.993, 1.024] | PASS (1.08) |
| 72 | −0.139 [−0.167, −0.111] | −0.339 [−0.368, −0.311] | −0.376 [−0.403, −0.348] | 0.908 [0.891, 0.926] | PASS (1.01) |
| 84 | −0.255 [−0.281, −0.228] | −0.530 [−0.554, −0.506] | −0.549 [−0.573, −0.525] | 0.838 [0.823, 0.854] | PASS (0.91) |
| 96 | −0.381 [−0.417, −0.344] | −0.669 [−0.704, −0.629] | −0.681 [−0.716, −0.641] | 0.768 [0.749, 0.788] | PASS (0.85) |
| pooled | −0.191 [−0.205, −0.176] | −0.429 [−0.443, −0.413] | −0.458 [−0.472, −0.443] | | |

- The rule passes on (1) too: the official interval at 54 includes 0, so the genes are not clearly worse there. **The genes' own gain (card held fixed) is 0% official at 54, rising to 9–23% official and 21–38% ruint and Montgomery at 72–96.**
- The rest of (2)'s gain is the card: on_demand A, the sort charge and kset against the frozen reference's enumerate. The card is most of the calibrated gain at 54 (ruint −1.44 of −1.61 log₂) and 57–69% of it at 84–96 (ruint −1.20 of −1.73 at 84, −0.88 of −1.55 at 96).
- The robust ratio is set by official in every row (official moves least).

**Balanced numbers: the (d) pipeline against the genes as qs alone** (information; same reference, so the ratio is 2^(pipeline log₂ − qs log₂)):

| bits | official | ruint | Montgomery |
|---|---|---|---|
| 54 | 0.985 | 1.095 | 1.012 |
| 72 | 0.997 | 1.123 | 1.031 |
| 84 | 0.974 | 1.172 | 1.025 |
| 96 | 0.996 | 1.202 | 1.048 |

- Under ruint, the front end (rho and p-1 multiplies, which ruint prices dearly against its cheap sieve ops) costs balanced numbers 10–20%, growing with size. At 96 that matches the user's toy ~1.20x.
- Under official it costs nothing or saves a little: p-1 and rho catch a few balanced factors, and qs's official cost is large enough that those catches pay for the front end.
- Montgomery is in between (1–5%).

**Information: the (d) pipeline on the banded set against the frozen reference alone:** robust 0.725 / 0.684 / 0.532 / 0.449 at 54 / 72 / 84 / 96. All three pricings agree; no misses.

**Predictions, scored as written.**
- *Mine:*
  - (X1) card-matched robust 0.85–1.00 / 0.80–0.92 / 0.70–0.85 / 0.65–0.80, all pricings below 1 at 72–96: **missed.** 54 is 1.009, above its range; 72–96 held (0.908, 0.838, 0.768, all pricings below 1).
  - (X2) as-frozen lower than (1) at 84–96 (held), within 0.05 of (1) at 54–72, robust 0.85–1.02 / 0.75–0.92 / 0.45–0.70: **missed.** At 54, (2) is 0.16 below (1); 54 is 0.849 (just below 0.85); 84–96 are 0.761 and 0.727 (above 0.70).
  - (X3) the rule passes on (2) and on (1): **held.**
  - (X4) the per-band gate PASSes everywhere in both: **held.**
  - (X5) on balanced numbers, the pipeline costs 1–8% more than qs alone, more under ruint than official: **missed.** The direction held (ruint dearest), but ruint is 9.5–20% and official is 0.974–0.997, so it does not cost more there.
  - Mine: 2 of 5.
- *DeepSeek's:* (D-rep) FAIL at 54–72; at 84–96 pass only by under 5% robust: **missed** (passes at every size, by 13–27% robust). Scored on (2), as written.
- *Grok's:*
  - (G-rep) pass at 84 and 96; borderline or fail at 54 and 72, with balanced numbers losing 5–15% there; by Grok's own threshold, fail if any balanced loss exceeds 10% or any per-band ratio exceeds 1.5x: **missed.** The (d) pipeline on balanced numbers gains against the frozen reference at every size (robust 0.836 / 0.870 / 0.741 / 0.724), and no per-band ratio exceeds 1.08.
  - (G-rep2) per-cell log₂ ranges: **0 of 24 cells held.** Every as-frozen cell is far below its range (the card effect, as the note beside it anticipated), and every card-matched cell is below its range.

**Conditions.**
- Genes are as frozen after the kc / lc round, with kc replaced by kset (kc was 23 / 36 / 32 / 60).
- Corrected card for the candidate; the frozen reference on its old card in (2).
- One generator fault (a Carmichael "prime") was found by the oracle and fixed before measurement; the affected set is the 54-bit banded one.
- The rule recommends; the reference stays the frozen one until the user decides.

## 2026-10-25 — Decisions (user): new reference; ECM additions charged; stage-2 prime list

**1. The reference is replaced** (user, Oct 25; the replacement rule passed).
- The new reference is the final Track R genes **per size** as qs alone on the corrected card (a_mode = on_demand, sort_charge = 1, kset = sf32): R-k@54 at 54, R-k@72 at 72, the round-3 genome at 84 and R-k@96 at 96 bits.
- **It is size-dependent by construction** (per-size genes). At sizes between or outside these four, the nearest size's genes are used, and which ones is stated with the result.
- **Bridge:** for one round, results also report the old frozen reference (qs + lc 1.4, enumerate) in a side column.
- Results before Oct 25 keep the reference they were measured against.

**2. ECM additions are charged** (user, Oct 25; card change, cost model below, before code).

**3. The stage-2 prime list stays an uncharged N-independent table** (user's decision; the existing convention for stage 1's primes ≤ B and the ECM card's prime list, now stated as a decision).

### Cost model: ECM modular additions, subtractions and small-constant multiplies at the word-level price (before code)

**New per-type column "word"** (shared with the coming pm1 stage 2): one machine-word-level op.
- Its ruint and Montgomery prices are set equal to sieve_update's calibrated price (0.034 and 0.125 multiplies), with no new calibration. Official counts 1 op, like every op.
- lampcore gets a new phase slot for it, and Python's optypes maps it.

**What is charged as "word" in the ECM card** (each where it is performed, in both cores):
- *xDBL:* X + Z, X − Z, t1 − t2, t2 + e: **4 per xDBL** (beside its 5 multiplies).
- *xADD:* XP − ZP, XQ + ZQ, XP + ZP, XQ − ZQ, uu + vv, uu − vv: **6 per xADD** (beside its 6 multiplies).
- *Setup, per curve:* σ² − 5, 4σ, v − u, 3u, 3u + v: **5 per curve.** Multiplying a residue by a small constant is word × residue, so it is word-level. The existing charged "16 · den" stays a full multiply, as recorded in Stage 8; it is not reclassified.
- *Stage 2:* the factor S·Z − X·S′ (p1 − p2): **1 per accumulated pair**. Also, per (j, b) candidate, the bookkeeping the pm1 stage-2 model charges for its prime table: 2 index computations (jW ± b) and 2 prime-table tests, so **4 per candidate whether or not it hits.**
- *Not charged* (flagged convention, both cards): the ladder's bit scanning and loop control in stage 1, as in pm1's stage 1 and the qs card's loops.

**Expected effect, before measurement.**
- Stage 1 dominates ECM's ops: per ladder bit, 11 multiplies plus 10 word ops.
- So ECM's cost rises by about **+3% under ruint** (10 × 0.034 / 11) and **+11% under Montgomery** (10 × 0.125 / 11).
- Under **official it rises by about +80–90%**, because official counts every op as 1 and the additions nearly double ECM's op count. This is a consequence of the decision as stated: the official count is a raw op count. It will move official-alone optima, where ECM is large.
- *Measurement:* before and after on all map numbers (ECM alone at every grid budget, per pricing), then a re-solve of the Track M final budgets on the corrected maps (and the p-1-inclusive joint optimum), reporting whether any budget moves.
- *Acceptance:* the multiply counts are unchanged per number (only word ops are added); the word count equals the formula from a trace (xDBLs, xADDs, curves, pairs and candidates); Python = Rust parity, per type.

**DeepSeek, before any small-prime-variation or ECM-addition code** (labelled as DeepSeek's; recorded Oct 25. The ECM cost model above was committed before this message; no ECM or small-prime code exists).
- **(D-spv)** Small-prime variation at 84–96 bits: best cutoff 30 under official (gain 18–28%); 10–15 under ruint (3–8%); 10 or off under Montgomery (−2% to +4%). Slack correction ~+0.5 for cutoff 30, ~+0.3 for cutoff 10.
  - *Notes beside it:* (a) its mechanism compares one sieve update with one confirmation step (price ratio 3.4x), but each extra candidate costs a full trial-division pass over the factor base (~F td ops), so the magnitudes are unsupported. (b) Primes 3, 5 and 7 are ~65% of the sub-30 1/p mass, not ~52%.
- **(D-ecmadd)** Charging ECM additions (~4 per ladder step beside ~10 multiplies): ECM cost +5% under Montgomery and +1.4% under ruint; no Track M budget moves at 72–96, possibly one step down at 54.
  - *Note beside it:* DeepSeek predicted that PD_M rises to 1.18–1.28. But PD_M = (R winner's cost) / (M winner's cost) under Montgomery, so a costlier Track M lowers PD_M, and ECM is only part of the total. The budget clause is scored as written; the PD_M clause is recorded with this direction note.
  - *Charge sites, counted from the code:* 4 per xDBL and 6 per xADD, so **10 per ladder step** (one xADD + one xDBL) beside 11 multiplies, not ~4. My expectation in the cost model (+3% ruint, +11% Montgomery, +80–90% official) uses the counted 10.
- **Reference change, recorded precisely** (DeepSeek's point, adopted as a task):
  - Track M winners cannot change: each is one Montgomery ratio over a fixed per-size reference, so the ordering is unchanged.
  - Track R winners can change, because the robust max weighs each pricing by its reference cost. The per-band gates change too.
  - *Task:* with the new reference, re-run winner selection and gates for the last sealed round (the kc / lc round, 9420000), on the lampcore build before the ECM change (kset included, saved), and report any change. PD values stand only where the winners are unchanged.

**Grok, before any small-prime-variation or ECM-addition result** (labelled as Grok's; recorded Oct 25).
- *Timing disclosure:* when this arrived, the ECM-addition code was being written (uncommitted, not yet built or run), and the reference re-selection (`reselect.py`) was running with none of its output read. No small-prime code exists.
- **(G-spv)** Small-prime variation at 84–96 bits: official cutoff 20, gain 4–9%; ruint cutoff 30, gain 8–15%; Montgomery cutoff 20–25, gain 6–12%.
  - *Notes beside it:* (a) Grok says the slack should be REDUCED by 0.15–0.40. But skipping small primes lowers the sieve estimate, so the slack must rise (~+0.5 in the user's Mathematica threshold run). The cutoff and gain clauses are scored; the slack clause is recorded as direction-wrong. (b) This predicts that ruint gains most and official least, the opposite of DeepSeek's D-spv (official 18–28%, ruint 3–8%). The measured ceilings (22–40% official, 6–25% calibrated) favour DeepSeek's direction; the result will report which holds.
- **(G-reref)** Re-selecting winners under the new per-size reference: no Track R winner changes at 84–96, and at most a swap among near-ties at 54–72.
- **(G-ecmadd)** Charging ECM additions: Track M's ECM cost rises 12–18%; budgets possibly one step lower at 84–96, unlikely at 54–72; PD_M up 0.05–0.12.
  - *Notes beside it:* the user's arithmetic note (4 additions × 0.125 on ~10 multiplies ≈ +5% Montgomery, +1.4% ruint) assumes 4 per step. The counted sites are 10 per ladder step (4 per xDBL + 6 per xADD) beside 11 multiplies, which gives ≈ +11% Montgomery and +3% ruint on stage 1.
  - Track R has no ECM at 72–96, so a costlier Track M lowers PD_M (Montgomery cost of R / Montgomery cost of M). Both outside reviewers predicted that PD_M rises; the direction is recorded.

**Reference change check: results** (`evolve/reselect.py`, `reselect.out`; the kc / lc round's sealed numbers, candidates and budgets; the lampcore build before the ECM change).
- The old-reference column reproduces the recorded (d) values (e.g. R@54 0.8289).
- **No winner changes in any of the eight cells.** Every gate passes under the new reference (upper end 1.14–1.30). **The round's PD values stand.**

| bits | Track R (d) winner: robust, old ref → new ref (official / ruint / Montgomery, new) | Track M (d) winner: Montgomery, old → new |
|---|---|---|
| 54 | R-k@54: 0.829 → 0.933 (0.819 / 0.933 / 0.851) | current final: 0.595 → 0.705 |
| 72 | R-k@72: 0.710 → 0.896 (0.780 / 0.896 / 0.815) | current final: 0.538 → 0.697 |
| 84 | current final: 0.573 → 0.824 (0.667 / 0.824 / 0.707) | current final: 0.426 → 0.620 |
| 96 | R-k@96: 0.484 → 0.769 (0.618 / 0.769 / 0.656) | M-k@84: 0.335 → 0.536 |

- Under the new reference, the Track R (d) pipeline beats qs alone (same genes, corrected card, kset) by 7–23% on the robust score. That is the front end's net gain on the mixed population.
- **(G-reref)** no Track R winner changes at 84–96, at most a near-tie swap at 54–72: **held** (no change anywhere).

**Outside context for the small-prime-variation cost model** (user, Mathematica; 18-digit N, B = 3000, F = 237, 20,000 positions; sieve cost = hits × update price; each candidate charged a full trial-division pass over the factor base, F divisions; a partial valued at 0.3 of a full relation; best slack chosen per case).
- Saving in cost per useful relation against sieving every prime, for cutoffs 10 / 20 / 30: official 8.7 / 9.1 / 9.3%; ruint 2.7 / 2.6 / 2.2%; Montgomery 2.6 / 2.6 / 2.2%. Official gains most (DeepSeek's direction, not Grok's). The best cutoff is 30 under official and 10–20 under the calibrated pricings.
- *The user's stated limitation:* the toy's best slack is ~1.0 (full relations only), while the card's tuned slack is ~2.0, so the user supposed the card confirms candidates more cheaply than a full F-division pass.

**How a candidate is confirmed in the card** (qs.py "5. confirm" and its qs.rs twin; stated as the cost model requires):
- For each sieve position at or above the threshold, the card evaluates v = (A·x + 2B)·x + C. That is **2 ops of type confirm_full** (full price: 1 multiply each under every pricing).
- It then trial-divides v by **every** factor-base prime: **F ops of type confirm_td**, one division per prime whether or not it divides, charged as one block of F. Each repeated division by a prime that divides again costs **1 more confirm_td**.
- confirm_td is priced as a small-modulus op: 1 (official), 0.114 (ruint), 0.426 (Montgomery).
- The cofactor test, and the large-prime steps if lc > 1, follow under their own types.
- **So the card does charge a full F-division pass per candidate, as the toy does.** The toy does not over-charge candidates relative to the card.
- The slack difference (toy ~1.0, card ~2.0) comes from the large-prime variation: the card's tuned lc of 1.6–2.0 makes partials worth admitting, and admitting them needs about one more unit of slack. The toy values a partial at 0.3 and has no lc term in its threshold.
- So the toy's savings are not upper estimates on the confirmation side. The open question for the cost model is how the sub-30 skip interacts with the partials' larger slack.

**DeepSeek, before any small-prime-variation or stage-2 code** (labelled as DeepSeek's; recorded Oct 25).
- **D-spv REVISED** (assumes candidates are confirmed by dividing only by root-matching primes, ~5–10 divisions):
  - On the sieve + confirm slice: official 15–22%, ruint 5–9%, Montgomery 5–9%, best cutoff 30 everywhere.
  - On total qs cost: official 7–12%, calibrated 2–5%.
  - Falsified for "cutoff 30 everywhere" if the calibrated gains peak at 20.
  - *Note beside it:* its assumption does not match the card, which charges a full F-division pass per candidate (stated above). Scored as written.
- **(D-cslack)** At the tuned slack, the extra candidates' confirm cost equals the extra relations' value, so the tuned slack implies an effective confirm cost.
  - Its numbers (a relation "~500 ops" on average at 84 bits; a marginal value much below average) are not supported.
  - *Adopted as information in the small-prime-variation cost model:* count the divisions actually charged per confirmed candidate in the card's traces, per size.
- **(D-c)** The pm1 stage-2 c chosen by the map check:
  - Track R 10–25 / 30–60 / 60–120 at 72 / 84 / 96; Track M 20–40 / 50–90 / 90–150; c rises with size in both;
  - c(Montgomery) / c(ruint) 1.2–1.5 at every size (reason given: qs is small-op heavy, so a catch saves more multiply-equivalents under Montgomery);
  - paired chosen everywhere.
  - *Notes:* Track R's stage-1 p-1 was within noise at 72–96, so stage 2 may stay off there. Pairing's setup is genuinely multiplies and is charged as such.
- **Reference policy:** recorded in PLAN. DeepSeek's proposed criterion (no change that reverses a PD sign) is recorded but not adopted, because PD ratios do not depend on the reference.

**Grok, before any stage-2 or small-prime-variation code** (labelled as Grok's; recorded Oct 25).
- **G-spv REVISED** (written after the user's Mathematica cost run; a revision, so the original G-spv stays the scored prediction): total qs gain official 6–11% (cutoff 30, slack +0.4–0.6); ruint 1.5–4% (cutoff 10–20, slack +0.3–0.5); Montgomery 1.5–4% (cutoff 10–20, slack +0.3–0.5). Cutoff 30 is neutral to slightly worse under the calibrated pricings.
- **(G-c)** The pm1 stage-2 c from the map check: Track R 8–15 / 6–12 / 5–10 at 72 / 84 / 96; Track M 15–30 / 12–25 / 10–20; Track M's c exceeds Track R's at every size.
  - *Note:* this has c **falling** with size, the opposite of DeepSeek's D-c (rising: R 10–25 → 60–120, M 20–40 → 90–150). The user's Mathematica stage-2 run found that the best c rises with the value per catch (5–20 at V = 1e5, 20–100 at V = 1e6), and the value per catch rises with size. The map check will report which direction holds.
- **(G-r2)** Track R stage 2: off at 72; short (c ≤ 10) at 84–96 with robust gain at most 1–3%. It is reported as off if the gain is inside the noise of stage-1-only.

**Outside context for the pm1 stage-2 map check** (user, Mathematica toy: rho, then p-1 stage 1 with optional stage 2, then qs; mixed bands 16 … N/2 bits, 1,200 primes each; qs cost scaled like L(N): 49k / 200k / 756k at 72 / 84 / 96; Q multiplied by 0.5 / 1 / 2 to mimic ruint-like / normal / Montgomery-like qs cost in multiply units; grids rho 0 and 2^8 … 2^18, B 0 and 2^8 … 2^14, c ∈ {1, 5, 10, 20, 50, 100, 200}).
- With paired stage 2 (k = 1), the best c is 20 in 8 of 9 cells. It is 50 only at 96 bits with Q × 2, where B sits at the grid top (2^14).
- The extra value from size and Q goes into stage-1 B (2^10 → 2^14) and the rho budget (2k → 131k), not into c.
- Stage 2's gain over the best stage-1-only pipeline: 6.5–11% (paired), 4.6–5.8% (simple stepping, best c 10–20).
- The rho budget scales roughly with Q, consistent with the budget-as-share-of-qs MOVES row.
- *Implications, adopted for the protocol:* c ~ 20 as a default; the search covers c 5–200; **B above 2^14 is allowed in the stage-2 map check** (the grid runs to 2^16), since B hits the grid top at the high-Q end.
- Against the pre-registered c predictions: DeepSeek's D-c (rising steeply to 60–150 at 96) and Grok's G-c (falling with size) both mostly miss in this toy. They are scored on the real map check, not on this.

**DeepSeek, before stage-2 code** (labelled as DeepSeek's; recorded Oct 25).
- **(D-c2, revised)** Map-check c with B allowed up to 2^16: Track R 15–25 / 20–30 / 25–40 at 72 / 84 / 96; Track M 20–35 / 30–50 / 40–65; c(M) / c(R) ≥ 1.2 at every size.
  - *Mechanism (accepted):* raising B raises both stage-1 catches and what stage 2 can catch (the rest of p − 1 must be B-smooth), so B absorbs value before c does.
  - *Note:* DeepSeek says a flat c = 20 would mean the per-track value isn't reaching the optimiser. But the user's toy varied the qs cost ×0.5–×2 and c stayed at 20, so a flat c is a legitimate outcome, not evidence of a bug.
- **(D-s3b)** Sealed stage-2 totals (stage 1 + 2 against no p-1): Track R 13–16% at 54, 6–10% at 72–84, 5–8% at 96; Track M 14–17 / 16–19 / 13–16 / 10–13% at 54 / 72 / 84 / 96; Track M's total exceeds Track R's at every size.
- Its claim that the card's confirmation must cost ~50–100 divisions rests on unsupported slope values. The trace count of divisions per confirmed candidate decides it.

**Stage-2 map-check protocol, addition** (information; adopted from DeepSeek):
- With each track's chosen B, c is frozen at 10, 20 and 50, and the three are compared on sealed numbers with paired intervals.
- If c = 20 (or the chosen c) beats both by more than the interval, c stays a gene with bounds 5–50. If they tie, c is proposed as a constant (the user's decision).
- B is allowed up to 2^16 in the map check.

**Decision (user, Oct 25): the old frozen reference stays in a side column for the next two sealed runs**, then is dropped unless a replacement check is triggered again (end condition written into PLAN; this replaces "for one round").

**Grok, before stage-2 code** (labelled as Grok's; recorded Oct 25).
- **G-c REVISED** (written after the user's c-vs-N toy; a revision, so the original G-c stays scored): c ~ 15–25 for Track R and 15–30 for Track M at 72 / 84 / 96 (central 20; Track M possibly one step higher at 96 if B hits 2^16). c no longer falls with size.
- **(G-r3)** Track R stage 2 at 72: off, or on but inside noise. Falsified if the map check shows a robust gain of 4% or more at 72.
  - *Note beside it:* one of Grok's reasons (the robust max may reject a setting that gains under ruint because it loses under official or Montgomery) is backwards. Ruint is where stage 2 helps least, since qs is cheapest there in multiply terms, so ruint decides the robust score. Its other reasons (rho's overlap with stage-2 catches; a lumpier real population than the toy) are recorded as given.
- **(G-cconst)** If c = 10, 20 and 50 tie on sealed numbers, make c a constant at 20 (DeepSeek proposes the same rule). **Adopted as the default for that outcome, pending the user's confirmation when it happens.**

**Ledger early stop: replay of the card's relations** (information only; `evolve/earlystop.py`, `earlystop.out`).
- Setup: final Track R genes (the new reference) as qs alone, corrected card with kset; 4 balanced map numbers per size. Ledger.add is wrapped only to note the sieve ops at each kept relation; no charge changes.

| bits | F | relations at stop (F + 10) | primes active in ≥ 1 / ≥ 2 relations | null-space dimension at stop | ≥ 5 deps: relations before stop; share of sieve ops after | ≥ 10 deps: relations before stop; share of sieve ops after |
|---|---|---|---|---|---|---|
| 54 | 30–42 | 40–52 | all but 0–1 / all but 0–2 | 12–13 | 7–9; 7.7–14.2% | 2–3; 0–10% |
| 72 | 49–67 | 59–77 | all but 0–2 / all but 2–3 | 11–13 | 8–24; 9.3–28.7% | 1–3; 0–4.4% |
| 84 | 86–97 | 96–107 | all but 0–5 / all but 3–10 | 12–16 | 8–16; 6.2–11.3% | 2–6; 1.3–2.5% |
| 96 | 131–150 | 141–160 | all but 1–5 / all but 4–9 | 13–17 | 9–13; 2.5–5.5% | 3–8; 0.5–2.0% |

- **Almost every factor-base prime is active.** At 0–5 inactive primes, the card's null space at the stop is only 11–17, against the user's Mathematica toy (F = 237, ~38 free dependencies from primes that never or rarely appear). The card's factor bases are small (30–150 primes), and the KS multiplier makes the small primes residues, so nearly every prime appears.
- **Stopping at ≥ 10 dependencies** (failure chance ~0.1%) saves only 1–8 relations: 0–4.4% of sieve ops (≤ ~2% of qs's official ops, less under the calibrated pricings, where sieve updates are cheap).
- **Stopping at ≥ 5 dependencies** saves 7–24 relations: 2.5–29% of sieve ops, typically 3–11%, i.e. ~1–5% of qs's official cost. A ~3% failure chance per number costs a full retry with the next multiplier, so most of that would be given back.
- **Not a large saving, so no MOVES row is added.** It is recorded here in case the factor base grows (larger N or larger bc), where inactive primes become common.

**Root-matched confirmation: sizing** (information; `evolve/confirmshare.py`, `confirmshare.out`). New reference genes as qs alone, corrected card with kset. Shares come from lampcore types on all map numbers; per-candidate counts from Python traces on 8 map numbers per size.

| bits | confirmation share of qs cost: official / ruint / Montgomery | of which the F-prime trial-division pass (confirm_td) | F | primes dividing a confirmed v | repeat divisions |
|---|---|---|---|---|---|
| 54 | 0.232 / 0.313 / 0.281 | 0.219 / 0.207 / 0.247 | 35 | 5.06 | 0.88 |
| 72 | 0.209 / 0.330 / 0.306 | 0.202 / 0.255 / 0.283 | 58 | 5.39 | 1.38 |
| 84 | 0.163 / 0.307 / 0.291 | 0.160 / 0.260 / 0.278 | 93 | 6.46 | 1.33 |
| 96 | 0.105 / 0.230 / 0.220 | 0.104 / 0.205 / 0.213 | 135 | 6.95 | 1.10 |

- Confirmation is 23–33% of qs's calibrated cost, almost all of it the trial-division pass. Only 5–7 of the F primes divide a typical confirmed candidate.
- A MOVES row "Root-matched candidate confirmation" is added, untested and sized from this. *Caveat (fixed classification rule):* a root test that computes x mod p reduces modulo a small prime, so it is small-modulus. Only a reduction-free form (e.g. re-sieving) would be word-level. The cost model must say which, and it is costed together with small-prime variation.
- **Correction recorded:** the earlier claim (outside context, the user's) that the card must confirm candidates more cheaply than a full pass was wrong. The card charges a full F-division pass per candidate. The slack gap between the toy (~1.0) and the card (~2.0) comes from the large-prime variation, as recorded above.

**DeepSeek, before any root-matching or small-prime-variation code** (labelled as DeepSeek's; recorded Oct 25, after the confirmation sizing above was committed).
- *Stated assumption for rescaling:* candidate confirmation is X = 20–30% of qs cost (official), 25–35% (ruint), 30–40% (Montgomery). Its predictions are rescaled linearly by the measured X.
  - **Measured X** (`confirmshare.out`, new reference genes): official 0.105–0.232, ruint 0.230–0.330, Montgomery 0.220–0.306 (54–96 bits; falling with size under official).
- **(D-rm)** Root-matched confirmation, total qs saving: official −2% to +1%; ruint 18–23%; Montgomery 21–26% (saving ~0.66 × X under the calibrated pricings).
  - *Meter checks (its):* an official saving above 3% means the root test is charged below a division; a ruint saving below 12% means X < 20% or the root test is charged at the small-modulus price.
  - The second check coincides with the classification caveat on the MOVES row: if the root test reduces x mod p, it is small-modulus by the fixed rule.
- **(D-rm+spv)** Root-matching plus skipping primes below 30: official 8–12%, ruint 22–30%, Montgomery 25–33% (super-additive under the calibrated pricings). If the slack rises 0.3–0.6 with cheap confirmations (it predicts so, absorbing ~25% of the root-match gain), subtract ~5 points from the calibrated figures.
- **(D-slack-cut)** Best slack by cutoff (none / < 10 / < 20 / < 30): official 2.0–2.2 / 2.2–2.4 / 2.3–2.6 / 2.5–2.9; ruint 2.0–2.2 / 2.3–2.5 / 2.5–2.8 / 2.7–3.1; Montgomery 2.0–2.2 / 2.4–2.6 / 2.6–2.9 / 2.8–3.2. Slack below 2.0 with the skip on means the skip doesn't pay at that pricing.
- **Priority note (DeepSeek's; the measured X supports it):** with X near 30% under the calibrated pricings (measured 0.22–0.33), root-matched confirmation may be the largest remaining calibrated gain. It is costed before small-prime variation; the two are costed together, as the MOVES row says.

**Grok, before any root-matching, small-prime-variation or stage-2 code** (labelled as Grok's; recorded Oct 25, after the confirmation sizing was committed).
- *Stated assumption:* confirmation is 25–35% of qs cost under official, 12–20% under ruint and 18–28% under Montgomery.
  - *Note beside it:* the direction is likely backwards. qs's other large cost, sieve updates, is word-level, much cheaper relative to small-modulus divisions under the calibrated pricings, so confirmation's share should be larger under ruint and Montgomery than under official. **The measurement confirms the note:** official 0.105–0.232, ruint 0.230–0.330, Montgomery 0.220–0.306. Grok's predictions are rescaled by the measured share.
- **(G-rm)** Root-matched confirmation, total qs saving: official −1% to +3%, ruint 8–14%, Montgomery 10–16%.
- **(G-rm+spv)** Root-matching plus skipping small primes: official 7–12% (cutoff 30), ruint 12–18%, Montgomery 14–20% (cutoff 20–30). The interaction is positive but sub-additive (DeepSeek says super-additive); the result reports which.
- *Grok's build order:* root-matched confirmation, then small-prime skipping, then pm1 stage 2, then the threshold reparameterization.

**Ordering decision rule** (recommended; the user to confirm):
- Finish the ECM-additions change and the confirmation-share measurement first.
- If confirmation is ≥ 20% of qs cost under ruint or Montgomery, build root-matched confirmation (cost model first) before pm1 stage 2. Otherwise keep pm1 stage 2 next, as planned.
- *Outcome of the measurement:* confirmation is 23–33% (ruint) and 22–31% (Montgomery) at every size, so the rule's condition holds and root-matched confirmation would come before pm1 stage 2. **Pending the user's confirmation;** the ECM change finishes first in either case.

### ECM additions charged: before / after (`evolve/ecmword_measure.py`, `ecmword_measure.out`; ratios recomputed to completion)

**ECM alone, cost new / old, every map number run to completion** (lampcore, cap 2^34, the saved pre-change build against the current one; every run finds its factor):

| bits | official | ruint | Montgomery | word ops per ECM multiply |
|---|---|---|---|---|
| 54 | 2.335 | 1.045 | 1.166 | 1.34 |
| 72 | 2.392 | 1.047 | 1.174 | 1.40 |
| 84 | 2.416 | 1.048 | 1.177 | 1.42 |
| 96 | 2.451 | 1.049 | 1.182 | 1.45 |

- The first printed ratios at 84 and 96 (`ecmword_measure.out`) were biased: under the new count, 1 and 36 numbers no longer finish within the map's ECM cap of 2^21, and their partial costs were compared. The table above replaces them. The re-solves are unaffected, because rows beyond 2^20 are extended to 2^22 / 2^24 as before.
- **Larger than my expectation** (+80–90% official, +3% ruint, +11% Montgomery), because stage 2's per-candidate bookkeeping (4 word ops for each of the 24 baby values per giant step, hit or not) is heavy at b2 = 50. Word ops are 1.34–1.45 per ECM multiply, against the 0.91 I took from stage 1 alone.

**Units.** An ECM op budget (ob) is counted in meter ops, and the meter now counts word ops. So the same ob buys ~2.4x fewer multiplies. Below, ECM budgets are also given in **work-equivalent** terms (new ob ÷ the official ratio at that size), which is what is comparable with the old budgets.

**Re-solves with the new ECM columns** (rho, [p-1 B,] ECM):

| bits | track | no p-1: new (work-equivalent ECM) vs final round | with p-1: new (work-equivalent ECM) vs kc / lc (d) |
|---|---|---|---|
| 54 | R | (0, 0), unchanged | (0, 2^8, 0), unchanged |
| 54 | M | (3,158, 0), unchanged | (1,448, 2^10, **0**) vs (0, 2^10, 6,317): **ECM switches off**, rho back on |
| 72 | R | unchanged | unchanged |
| 72 | M | (5,312, **0**) vs (1,448, 35,734): **ECM switches off**, rho +15 steps | (5,312, 2^11, **0**) vs (664, 2^11, 17,867): **ECM off**, rho +24 steps |
| 84 | R | unchanged | unchanged |
| 84 | M | (5,793, 77,936 ≈ 32,258) vs (3,158, 32,768): ECM work unchanged, rho +7 steps | (3,158, 2^12, 77,936 ≈ 32,258) vs (2,896, 2^12, 32,768): ECM work unchanged, rho +1 step |
| 96 | R | unchanged | unchanged |
| 96 | M | (12,634, 285,870 ≈ 116,634) vs (4,871, 120,194): ECM work unchanged, rho +11 steps | (12,634, 2^13, 142,935 ≈ 58,317) vs (2,896, 2^13, 120,194): **ECM work halves** (−8 steps), rho +17 steps |

- **Track R does not move anywhere** (no ECM in its pipelines).
- **Track M moves at every size with p-1:**
  - ECM switches off at 54 and 72;
  - its work halves at 96 and stays the same at 84;
  - rho rises everywhere ECM gives way.
- **Track M at 72 now has no ECM.** Its pipeline (rho 5,312, p-1 2^11, qs) has the same shape as Track R's, so PD_M and PD_R at 72 should move toward 1. That is measured in the next sealed run; no PD is claimed from the map.

**Predictions on this change, scored as written.**
- (D-ecmadd, DeepSeek) ECM cost +5% Montgomery and +1.4% ruint; no Track M budget moves at 72–96, possibly one step down at 54: **missed** (+16.6–18.2% and +4.5–4.9%; ECM switches off at 72 and rho moves at 72–96). Its PD_M clause awaits a sealed run, with the direction note recorded.
- (G-ecmadd, Grok) Track M ECM cost +12–18%; budgets possibly one step lower at 84–96, unlikely at 54–72: **missed.** The cost clause held at 54–84 (16.6–17.7%), with 96 just above (18.2%). The budget clause missed: ECM switched off at 54 and 72. The PD_M clause awaits a sealed run.
- *My expectation in the cost model* (+80–90% official, +3% ruint, +11% Montgomery): **missed** (×2.34–2.45, +4.5–4.9%, +16.6–18.2%; stage 2's bookkeeping was not in my estimate).
- **Any Track M budget move (user's question): yes, at every size with p-1, and at 72–96 without it.**
- **Consequence:** the kc / lc round's Track M (d) budgets, and the final-round Track M budgets, are in the old ECM units and are superseded. A re-solve with the new columns is needed before any further Track M sealed run; the table above is that re-solve.

**Outside context for root-matching** (user, Mathematica; 18-digit N, B = 3000, F = 237; partials = leftover < B^1.8, valued 0.3; prices for update / small-modulus division / word op: 1 / 1 / 1 official, 0.034 / 0.114 / 0.034 ruint, 0.125 / 0.426 / 0.125 Montgomery; best slack per case; sieve + confirm only).
- Confirmation's share of sieve + confirm, the card as today: 70% official, 89% ruint, 89% Montgomery.
- Saving against today's card: root-matched alone −1.8% official, 56% ruint, 59% Montgomery; skipping primes < 30 alone 9.2 / 2.6 / 2.7%; both together 7.5 / 59 / 63%.
- *The user's stated limits:* F here (237) is larger than the card's (57–151), and the card's measured sieve-update share (10–34% of qs cost under the calibrated pricings) means its confirmation share is well below the toy's. The toy's best slack stays ~1.0 (it undervalues partials). Treat it as direction: root-matching is likely the largest calibrated gain available. Size it from the measured confirmation share (measured: 23–33% ruint, 22–31% Montgomery of total qs cost).
- **Ordering (user, restated):** confirmation is ≥ 20% of qs cost under ruint and Montgomery, so root-matched confirmation is costed and built before pm1 stage 2.
- *Note:* the toy prices the root test as a word op. Whether the card's root test can be word-level is the design question in the cost model below.

## 2026-10-25 — Root-matched candidate confirmation: cost model (before code; one design decision for the user)

**What it replaces.** Today each candidate costs 2 confirm_full (evaluating v) plus F confirm_td (one division of v by every factor-base prime) plus repeats. Measured: only 5.1–7.0 primes divide a confirmed v, and the F-pass is 10–22% of qs official cost and 21–28% of its ruint and Montgomery cost.

**The design question: how is "does p divide v" decided without dividing v by p?** The fixed classification rule types an operation that reduces modulo a small prime as small-modulus (0.114 ruint, 0.426 Montgomery, the same as a division of v).
- **(i) Root test by x mod p:** reduces the sieve index modulo p, so it is a small-modulus op by the rule. It costs the same as today's division and saves nothing. *Rejected.*
- **(ii) Root test by a precomputed reciprocal (Barrett / multiply-high and compare):** physically a word multiply, a shift and a compare, with no division instruction. But it computes x mod p, so the rule as written would type it small-modulus. **The user's decision:** does a reduction done by multiply-high count as "reduces modulo a small prime" (small-modulus), or as word-level arithmetic? If word-level, this is the simplest form: F word-level tests (each ~3 word ops: multiply-high, multiply-subtract, compare against the two roots) plus a division for each matching prime.
- **(iii) Re-sieving (reduction-free; word-level by the rule as written):** after a polynomial's sieve pass, the candidate positions are marked in a bitmap (1 word op per candidate). For each factor-base prime p ≥ P0, its two root progressions are walked again across the interval, testing the bitmap at each position (2 word ops per position: index step and bitmap test). Primes that hit a candidate are recorded for it (1 word op per hit). v is then divided only by the recorded primes and by the primes below P0 (small-modulus ops, plus repeats).
  - The walk costs about as many positions as the sieve updates of primes ≥ P0. Primes below 30 give 64–82% of all updates, so with P0 = 30 the re-sieve walks only 18–36% of the update count.
  - **P0 is a card option** (default 30; P0 = 2 re-sieves every prime).

**Charges, option (iii), per polynomial:**
- 1 word op per candidate (bitmap set);
- for each prime p ≥ P0 (not dividing A), for each root, 2 word ops per position visited (positions = (width − 1 − start) // p + 1, as in the sieve);
- 1 word op per recorded hit;
- per candidate: 2 confirm_full (unchanged), one confirm_td per prime below P0 plus one per recorded prime, plus repeats as now.
- The large-prime and ledger steps are unchanged.

**Expected effect, before measurement** (84 bits, new reference genes; shares from `sieveshare.out` and `confirmshare.out`):
- *The F-pass part:* 93 → ~5 (primes < 30 in the base) + ~6.5 (dividing primes ≥ 30, at most) divisions per candidate. That removes ~88% of confirm_td, i.e. about 0.23 of qs's ruint cost and 0.24 of its Montgomery cost.
- *The re-sieve:* 2 word ops per position over ~27% of the update count. That adds ~0.54 × sieve_update cost ≈ 0.13 of qs's ruint cost (sieve updates are 0.23) and ~0.16 Montgomery.
- **Net: roughly 8–12% of qs cost under ruint and Montgomery. Under official it loses** (the re-sieve's word ops count 1 each, like the divisions they replace, and there are more of them).
- Option (ii), if typed word-level, would save more (~15–20% calibrated), with no re-sieve walk.

**Acceptance (for the code):**
- the option absent is today's card, op for op;
- with it on, the relations found are identical to today's on every map number (same candidates, same factorizations; only the charges differ);
- the word and confirm_td counts equal the formula from a trace;
- Python = Rust parity, per type.
- It is then costed together with small-prime variation (DeepSeek's and Grok's predictions are recorded above).
- **Decision (user, Oct 25): re-sieve only.** The classification rule stays strict: any reduction modulo a small prime, including one done by multiply-high (Barrett), is small-modulus. Root-matched confirmation is built as option (iii), re-sieving with cutoff P0 (default 30). Option (ii) is not built.

**DeepSeek, before any root-matching code** (labelled as DeepSeek's; recorded Oct 25, after the confirmation share was measured and committed).
- **X REVISED:** the card's confirmation share of total qs cost (calibrated) is 40–50% at F 57, 50–62% at F 100 and 60–70% at F 151.
  - *Note beside it:* its scaling multiplies a confirm / update ratio of 1.9–5.1 by an assumed update share of 20–30%, which gives more than 100% at F 151, so the numbers are internally inconsistent. They are treated as a loose upper range; the measured share decides (measured: 22–33%).
- **(D-rm2)** Root-matching saves ~0.60 × X: 24–30% ruint, 26–33% Montgomery and −2% to +1% official at 84 bits, ±5 points across sizes. The saving ratio rises with F: ~0.58 at F 57, ~0.63 at F 100, ~0.68 at F 151, because each candidate's few real divisions and repeats are a fixed overhead. So root-matching pays more at larger sizes.
- **(D-pv)** The card's slack of ~2.0 implies an effective partial value of ~0.75–0.8. Revised slack increments for skipping primes: +0.15 / +0.30 / +0.45 at cutoffs 10 / 20 / 30.
  - *Note beside it:* in the user's large-prime Mathematica run, ~14,000 partials gave 492 combined relations (~0.04 each), so 0.75 is not supported.
  - *Alternative mechanism, recorded:* per-polynomial setup cost, which a looser threshold amortizes over more relations per sieve interval (absent in the toy).
- **Recorded (user):** root-matching is slightly negative under official (−1.8% in the toy; the cost model above expects a loss under official), so it is a **card option each track can take or leave**. The official count would reject it.

**Slack check: optimum or plateau?** (information; `evolve/slackcheck.py`, `slackcheck.out`; the committed lampcore build). New reference genes as qs alone on all map numbers; lc fixed as tuned, tc set so that the slack tc + lc − 1 is 1.0 / 1.5 / 2.0 / 2.5; cost relative to the tuned slack (official / ruint / Montgomery). No misses at any slack.

| bits (tuned slack) | 1.0 | 1.5 | 2.0 | 2.5 |
|---|---|---|---|---|
| 72 (2.23) | 3.45 / 3.51 / 3.75 | 1.72 / 1.51 / 1.59 | 1.07 / 0.99 / 1.01 | 1.03 / 1.13 / 1.11 |
| 84 (2.10) | 2.55 / 2.22 / 2.31 | 1.51 / 1.30 / 1.33 | 1.03 / 0.99 / 0.99 | 1.05 / 1.25 / 1.22 |
| 96 (2.01) | 2.48 / 2.33 / 2.38 | 1.51 / 1.36 / 1.38 | 1.00 / 1.00 / 1.00 | 0.99 / 1.22 / 1.20 |

Cost split under ruint (setup = multiplier, factor base and polynomial setup; then sieve, confirmation, large primes, linear algebra + square root):

| bits | slack 1.0 | slack 1.5 | slack 2.0 | slack 2.5 |
|---|---|---|---|---|
| 72 | setup 0.75, sieve 0.22, confirm 0.02 | 0.64 / 0.26 / 0.07 | 0.48 / 0.22 / 0.23 | 0.31 / 0.14 / 0.47 |
| 84 | 0.58 / 0.38 / 0.02 | 0.51 / 0.38 / 0.08 | 0.39 / 0.29 / 0.26 | 0.24 / 0.18 / 0.52 |
| 96 | 0.53 / 0.45 / 0.02 | 0.46 / 0.46 / 0.06 | 0.36 / 0.37 / 0.23 | 0.23 / 0.24 / 0.49 |

- **Under ruint and Montgomery, ~2.0 is a true optimum, not a plateau.** The cost rises steeply below it (×1.3–1.6 at 1.5, ×2.2–3.7 at 1.0) and clearly above it (+11–25% at 2.5).
- Under official it is flat above 2.0 (0.99–1.05 at 2.5), since confirmation is cheap relative to the sieve in official ops.
- **The mechanism is the per-polynomial setup cost** (DeepSeek's alternative under D-pv). At low slack, few relations come per polynomial, and setup is 53–75% of ruint cost at slack 1.0. A looser threshold amortizes setup over more relations, until confirmation (0.47–0.52 of ruint cost at 2.5) takes over. The toy, with no setup cost, misses this, which is why its best slack is ~1.0.
- **Setup is 35–40% of qs's ruint cost at the tuned slack.** That is a target in its own right, the largest single slice under ruint at 72–84.
- *For root-matching:* cheaper confirmation lowers the cost of a looser threshold, so the optimal slack should rise and setup's share fall. The saving after retuning can exceed the static estimate in the cost model.

**Grok, after the user's root-matching toy** (labelled as Grok's; revisions, so the originals stay scored).
- *Timing:* this arrived after the slack sweep had run and been committed (a20bb11). G-slack is therefore **post hoc**, recorded and scored only for the record.
- **Confirmation share REVISED** (total qs, F 57–151): official 35–50%, ruint 45–65%, Montgomery 45–65%. (Measured: 10.5–23% / 23–33% / 22–31%.)
- **G-rm REVISED:** root-matching alone saves −2% to +2% official, 20–32% ruint and 22–35% Montgomery (now close to DeepSeek's D-rm2).
- **(G-slack, post hoc)** qs cost against slack 1.0–2.5: official has a clear minimum at 1.8–2.2, rising below 1.5 and above 2.4; ruint and Montgomery have a broader, shallower minimum at 1.9–2.3, not a flat plateau; the mechanism is per-polynomial setup amortization.
  - *Scored post hoc:* **missed.** The mechanism and "not a plateau" agree with the sweep, but the shape is the other way round. Official is flat above 2.0 (0.99–1.05 at 2.5, and lowest at 2.5 at 96), while ruint and Montgomery have the sharper minimum (+11–25% at 2.5).
- *Grok's build order, if root-matching delivers ~24–33% calibrated:* root-matching, then small-prime skipping, then the threshold reparameterization, then pm1 stage 2.

**Recommended order (the user's, to confirm):**
1. root-matched confirmation first (the confirmation share is ≥ 20% under ruint and Montgomery: measured 22–33%);
2. then pm1 stage 2 (cost model written, predictions on record, ~6.5–11% in the toy, mostly Track M);
3. then small-prime skipping (mainly an official gain, ~9%, and 2–4 points calibrated on top of root-matching);
4. then the threshold reparameterization (search-space cleanup, no cost change).
- Step 1 already follows from the ordering rule; the rest of the order is pending the user's confirmation.

**Slack, further figures** (user's request, Oct 25; information; `evolve/slack2.py`, `slack2.out`). The cost-per-pricing sweep and split are under "Slack check" above. This adds Python traces on 3 balanced map numbers per size, new reference genes (corrected card, kset), lc fixed, tc adjusted.
- *Timing:* the user's toy context (slack 1.0 best in the toy unless setup is ≥ 4–16x the sieve; partial values 0.04–0.3) arrived after the cost sweep had run. **The sweep shows cost rising at 1.0–1.5 (×1.3–3.7), so the tuned slack is not drift and there is no free gain there.**

| bits | slack | candidates per relation | share of relations combined from partials | pairing yield (combined per partial filed) | partials filed per number |
|---|---|---|---|---|---|
| 72 | 1.0 / 1.5 / 2.0 / 2.5 (tuned 2.23) | 1.15 / 1.88 / 4.85 / 11.49 (6.78) | 0.01 / 0.16 / 0.47 / 0.62 (0.58) | 0.17 / 0.20 / 0.16 / 0.15 (0.17) | 2 / 50 / 186 / 271 (223) |
| 84 | same (tuned 2.10) | 1.08 / 2.57 / 6.28 / 16.44 (7.66) | 0.00 / 0.26 / 0.47 / 0.56 (0.49) | 0.05 / 0.17 / 0.13 / 0.12 (0.13) | 6 / 157 / 357 / 464 (394) |
| 96 | same (tuned 2.01) | 1.04 / 2.55 / 6.69 / 18.59 (7.19) | 0.00 / 0.25 / 0.49 / 0.59 (0.50) | 0.06 / 0.16 / 0.09 / 0.06 (0.08) | 6 / 231 / 834 / 1,462 (902) |

- **Why the card's optimum is ~2.0 and the toy's is ~1.0:**
  - At the tuned slack, **about half of the card's relations come from combined partials.** Its pairing yield is 0.08–0.17 combined relations per partial filed, 2–4x the 0.04 of the user's large-prime run, because the card needs only F + 10 relations (F = 50–150) from a small large-prime range.
  - The **per-polynomial setup** is 35–40% of ruint cost at the optimum and 53–75% at slack 1.0. A looser threshold amortizes it over more relations per polynomial.
  - The toy's optimum stays near 1.0. *Caveat (corrected Oct 25):* the toy's setup range (up to 16x the sieve) covers the card's ratio (1–3.4 under ruint), so setup size alone does not explain the difference. Partial value and confirmation cost relative to setup remain the candidates.
- **Threshold reference against each position's own size.** The card's threshold uses one reference per polynomial, log₂(M√(kN/2)), the largest |Q(x)| on the interval, since |Q(x)| = M√(kN/2) · |2u² − 1| with u = x / M.
  - Over uniform positions the true |Q(x)| is smaller than the reference by **1.09 bits on average** (median 0.60 bits, 90th percentile 2.83). That is **~0.10–0.12 slack units** (one unit = log₂ B ≈ 9.3 / 10.0 / 10.8 bits at 72 / 84 / 96).
  - So the effective looseness at typical positions is the stated slack plus ~0.1, and more near the roots of Q.
  - Two things push the other way: the card does not sieve 2 or prime powers, so a position's sieve sum understates its smooth part.

**Slack-sweep predictions and context** (user and DeepSeek; recorded Oct 25). *Timing:* these arrived **after the slack sweep had run and been committed** (a20bb11, 8d49d2f), so the sweep predictions are **post hoc**, recorded and scored only for the record. D-rmslack is pre-registered: no re-sieve measurement has run.
- *Null (the user's toy):* best slack ~1.0 under every pricing (full-pass confirmation, partials ~0.04–0.3, setup up to 16x the sieve).
  - *The user's note:* the toy expressed setup as a multiple of each pricing's sieve cost. Under ruint and Montgomery, sieve updates are very cheap (0.034, 0.125) while setup is priced at small-modulus or full-multiply rates, so the card's setup / sieve ratio there may far exceed 16, and the toy undersold setup amortization.
  - *The sweep:* at the tuned slack, ruint setup is 0.35–0.48 of qs cost against sieve 0.22–0.37. That is setup / sieve ≈ 1–2 in cost, i.e. roughly 30–60 sieve updates' worth of price per unit of sieve cost, far beyond the toy's 16. The null is rejected.
- **(D-sweep, DeepSeek's; post hoc)** minimum at 1.5 under official (0–4% below the tuned ~2.0); at 1.0–1.5 under ruint (8–18% saving) and Montgomery (6–15%): **missed.** Cost at 1.5 is ×1.3–1.7 the tuned cost under every pricing, and ×2.2–3.7 at 1.0.
- **(D-tcfloor, DeepSeek's)** the tc lower bound (1.0) forces slack ≥ lc, so tc should sit at the floor in most cells; test by lowering the bound.
  - *Note beside it:* the kc / lc round's frozen tc is 1.27–1.54 in 7 of 8 cells (only R@96 at 1.035), so the floor was not binding there, and lc could also have been lowered. Recorded as given; refuted by the existing data.
- *DeepSeek's linear-algebra counter-mechanism*, recorded with a note: the relations needed (F + 10) do not depend on slack, so linear-algebra cost cannot favour a looser threshold. The sweep's la + sqrt share is 0.01–0.05 at every slack.
- **(D-rmslack, DeepSeek's; pre-registered)** after root-matched confirmation, the best slack rises 0.3–0.6 under ruint and Montgomery and stays flat under official.
- **X REVISED again (DeepSeek's):** confirmation 25–50% of total qs cost; D-rm2's saving 15–30% ruint and 16–33% Montgomery. **D-pv is withdrawn by DeepSeek.**

**Grok, before the slack sweep** (labelled as Grok's; recorded Oct 25). *Timing:* this arrived after the sweep had run and been committed, so G-slack REVISED is **post hoc**. G-rmslack is pre-registered.
- **G-slack REVISED (conditional; post hoc):** under ruint and Montgomery there is a clear minimum near 2.0 only if setup is ~25–45% of qs cost (~30–60x the sieve-update cost); if the measured setup share is below ~20%, the minimum is at 1.4–1.8. Under official, a minimum near 2.0 with setup ~10–20x the sieve.
  - *Scored against the measured split:* the ruint setup share at the tuned slack is 0.35–0.48 (in or just above 25–45%), and there is a clear minimum near 2.0 under ruint and Montgomery: **held.** Official: the setup share is 0.07–0.12, and cost is flat above 2.0 (0.99–1.05 at 2.5) rather than a clear minimum: **missed.**
- **(G-rmslack; pre-registered)** after root-matched confirmation, the best slack stays flat under official (−0.1 to +0.2) and rises 0.2–0.4 under ruint and Montgomery; more than 0.5 would surprise Grok. (DeepSeek's D-rmslack: 0.3–0.6.)
- *Grok's view:* if the sweep showed slack 1.0–1.5 cheaper than ~2.0 by 8–18% under ruint, adopt it immediately, then drop tc's lower bound and retune. **Moot:** the sweep shows the opposite.

**Protocol for sweep results (recommended; the user to confirm):**
- A sweep result on map numbers is not adopted directly.
- If a lower (or different) slack wins in a sweep, run one sealed check on fresh numbers (per-band gate, paired intervals, all three pricings).
- Because it changes the reference genes, adoption goes through the pre-registered replacement rule. Dropping tc's lower bound and retuning come after.
- For this sweep, no slack beat the tuned one, so nothing is adopted.

**Decisions (user, Oct 25):**
1. Order after root-matched confirmation: pm1 stage 2, then small-prime skipping, then the threshold reparameterization.
2. After re-sieve passes parity: measure it against full-pass confirmation on the map numbers per pricing; then retune slack with re-sieve on (D-rmslack and G-rmslack predict that the best slack rises); then a sealed check before any reference change.
3. A MOVES row "Cheaper polynomial setup", untested, with the setup breakdown as a first information step (below).
4. Commits use explicit `git add` only (no `commit -a`).
- *Disclosure:* commit 783e885 (a NOTES correction made with `commit -a`) swept in the re-sieve code (qs.py, qs.rs, main.rs, optypes.py, parity.py) before the parity suite finished. Acceptance had passed (`resieve_accept.out`), and the parity suite is running on exactly that code. This is the second such slip (the first was bb89d20), and decision 4 rules it out from here on.

**Setup breakdown** (information; `evolve/setupshare.py`, `setupshare.out`). New reference genes as qs alone (corrected card, kset), Python traces on 3 balanced and 3 band-24 map numbers per size. Each charge is attributed to its call site; counts are unchanged. Shares of total qs cost, official / ruint / Montgomery:

| part | 54 | 72 | 84 | 96 |
|---|---|---|---|---|
| Gray-code switching (root updates per polynomial) | 0.023 / 0.058 / 0.069 | 0.042 / 0.141 / 0.155 | 0.029 / 0.128 / 0.136 | 0.026 / 0.146 / 0.150 |
| A selection (on-demand search, pool sort, forming A) | 0.030 / 0.089 / 0.090 | 0.030 / 0.113 / 0.108 | 0.012 / 0.059 / 0.056 | 0.012 / 0.072 / 0.068 |
| per-A roots (r1, r2, 2 B_l A⁻¹ per sieved prime) | 0.022 / 0.055 / 0.065 | 0.019 / 0.064 / 0.070 | 0.013 / 0.057 / 0.060 | 0.011 / 0.064 / 0.066 |
| inverse of A mod each sieved prime | 0.017 / 0.046 / 0.055 | 0.015 / 0.053 / 0.059 | 0.011 / 0.052 / 0.056 | 0.011 / 0.063 / 0.066 |
| factor base (Legendre, Tonelli–Shanks) | 0.040 / 0.102 / 0.121 | 0.017 / 0.058 / 0.063 | 0.011 / 0.049 / 0.052 | 0.004 / 0.024 / 0.025 |
| multiplier scoring (KS) and ranking | 0.014 / 0.035 / 0.042 | 0.003 / 0.009 / 0.010 | 0.001 / 0.004 / 0.004 | 0.000 / 0.001 / 0.001 |
| inverses for B_l and B_l per A | 0.003 / 0.009 / 0.011 | 0.002 / 0.007 / 0.008 | 0.001 / 0.003 / 0.004 | 0.000 / 0.003 / 0.003 |
| **setup, all parts** | 0.150 / 0.393 / 0.452 | 0.128 / 0.444 / 0.472 | 0.077 / 0.354 / 0.368 | 0.066 / 0.374 / 0.379 |

- **Gray-code switching is the largest part at 72–96 (13–15% of qs's calibrated cost):** one op per root per polynomial switch, over every sieved prime. That op, r ± 2B_l A⁻¹ mod p, is an addition followed by a conditional subtraction, not a reduction, yet it is charged as setup_small (0.307 ruint), the small-modulus price. Under the fixed classification rule it is word-level arithmetic; re-typing it is a pricing change with its own cost-model entry (adopted below).
- Next, per A: A selection (6–11%), the inverse of A mod each sieved prime (5–6%) and the roots (6%). Those are paid once per A, so they shrink with more polynomials per A (larger s).
- The factor base and the multiplier matter only at 54–72.

**Decisions and corrections (user, Oct 25):**
1. **Gray-code root update re-typing: ADOPTED**, by the fixed classification rule (the same principle as the ECM-additions decision). The per-polynomial update r ± 2 B_l A⁻¹ (mod p) is an add and a conditional subtract, so it is charged at the word-level price, not setup_small.
   - This is a pricing change, not an algorithm change. A cost-model entry comes first. It applies to every qs genome including both references, then parity, then before / after qs cost per pricing on the map numbers, with the reference comparisons re-stated under the corrected pricing.
   - The card is audited for any other add / conditional-subtract steps charged as small-modulus; they are listed, not re-typed without a note.
   - It is reported separately from re-sieve, so their effects are not mixed. The order is unchanged: re-sieve parity, measure, retune slack, sealed check.
2. The MOVES "Cheaper polynomial setup" candidate (c) is corrected: Montgomery's batch inversion needs a common modulus and does not apply. It is replaced by precomputing the inverses of the A-pool primes modulo every factor-base prime once per number, so each A's inverse mod p costs s − 1 small multiplications instead of a Euclid run.
3. **Beside DeepSeek's D-setup** (as relayed by the user; its text was not recorded here before): the measured shares contradict it. The inverses are ~5–6% of qs cost, ~15% of setup, against its 60–75% of setup; Gray-code switching is ~35–40% of setup against its 20–35%.

**Setup by type** (information, lampcore types on all map numbers, new reference genes; share of total qs cost, ruint / Montgomery):
- setup_full: 0.025 / 0.008 (54), 0.017 / 0.005 (72), 0.008 / 0.002 (84), 0.006 / 0.002 (96);
- setup_small: 0.215–0.265 / 0.255–0.293;
- setup_euclid: 0.052–0.062 / 0.058–0.067.
- **A selection's 6–11% (ruint) is mostly setup_small**, not the full-price A formation. It is the on-demand search's closeness scans over the pool, the overlap checks against used A's, the sort comparisons and the target check: comparisons and index arithmetic on word-size values. These go on the audit list below.

**Large primes: distribution and the realistic 2LP rate** (information; `evolve/lpdist.py`, `lpdist.out`). New reference genes as qs alone (corrected card, kset), Python traces on 3 balanced map numbers per size.
- *Outside context (user, Mathematica):* the simulated 1LP pairing yield (large primes drawn ∝ 1/q in (B, B^lc)) is 0.076 / 0.064 / 0.051 at 72 / 84 / 96, against the measured 0.17 / 0.13 / 0.08 (1.6–2.2x higher). Simulated combined relations are ~24–28% of F + 10, against ~50% measured. 2LP cycles would add 1.3–9.5% of F + 10 at 0.25–1 two-large-prime relations per partial (before the splitting cost).

| bits | lc | candidates / full / partials filed per number | log_B q of filed partials: median (mean) | share in [1, 1.2) / [1.2, 1.4) / [1.4, 1.6) / [1.6, 1.8) / [1.8, 2) | 2LP-qualifying cofactors per number (per partial) |
|---|---|---|---|---|---|
| 54 | 1.74 | 202 / 29 / 142 | 1.364 (1.376) | 0.22 / 0.34 / 0.28 / 0.17 / 0 | 0 (0) |
| 72 | 1.70 | 429 / 30 / 260 | 1.363 (1.355) | 0.27 / 0.31 / 0.28 / 0.14 / 0 | 3.0 (0.012) |
| 84 | 1.64 | 771 / 52 / 444 | 1.358 (1.345) | 0.26 / 0.31 / 0.35 / 0.08 / 0 | 2.3 (0.005) |
| 96 | 1.97 | 1,069 / 75 / 976 | 1.469 (1.470) | 0.19 / 0.23 / 0.24 / 0.21 / 0.13 | 0 (0) |

- **(a)** Under a 1/q prior, log_B q has density ∝ 1/t on [1, lc], with median √lc = 1.32 / 1.30 / 1.28 / 1.40. The measured medians are 1.36 / 1.36 / 1.36 / 1.47.
  - *[Corrected Oct 25 (user); the first conclusion here was "no skew toward small q, so the threshold-skew explanation is not supported". That was wrong.]* The 1/q prior is not the right baseline for skew. Without a threshold, a partial with a larger q has a smaller smooth part and is much likelier to be smooth, so unfiltered partials would lean strongly toward B^lc. **Medians near √lc therefore mean the threshold does filter large leftovers**, which supports the user's mechanism.
  - What the data does show: the filed q's have about the same shape as the user's 1/q simulation, so **shape does not explain the 1.6–2.2x repeat gap** against that simulation.
  - The quadratic-residue restriction (only q with (kN/q) = 1 can occur, about half the primes) is the leading candidate for the gap. A test is pending (user, Mathematica, residue-restricted draws).
  - **(W-qr, Claude chat's prediction; pre-registered before that test):** the residue-restricted simulated pairing yield is within ±25% of the measured 0.17 / 0.13 / 0.08 at 72 / 84 / 96, and the simulated combined relations rise from 24–28% to 40–55% of F + 10.
- **(b) The realistic 2LP rate at the card's threshold is essentially zero:** 0–3 qualifying cofactors per number, 0–1.2% per partial.
  - A 2LP cofactor is ≥ B², a shortfall of ≥ 2 in log_B units, at or beyond the tuned slack (~2.0).
  - The counts are small (3 numbers per size; about 9 and 7 qualifying cofactors in total at 72 and 84), so the rate is rough.
  - Admitting them would need a much looser threshold, where candidates per relation are already 11–19 at slack 2.5.
- **The 2LP MOVES row stays "marginal; revisit after re-sieve and small-prime skipping".** Cheaper confirmation lowers the cost of a looser threshold, which is the only way 2LP cofactors would reach confirmation.
- *Recorded for the Gray-code cost-model entry (user, Oct 25):* it states the word ops per update (add; compare; conditional subtract) and the update count per switch, and derives the expected cut of the slice from those (one op: ~89%; two: ~78% under ruint). The same goes for any audit item. Before / after qs cost per pricing is reported in absolute terms (op cost per number), with shares secondary.

**DeepSeek's reply (Oct 25, late), with annotations** (labelled as DeepSeek's; the annotations are Claude chat's, relayed by the user).
1. **Beside D-setup:** DeepSeek acknowledges that D-setup was wrong by 4–5x (and that the earlier batch-inversion suggestion did not apply), and lowers its confidence on setup predictions.
2. **Pre-registered as given:**
   - **(D-gc)** Gray-code re-typing: official 0% (exact); ruint 9–11%; Montgomery 9–11%; falsified outside 7–13%. Slack: re-typing alone lowers the tuned slack by 0.1–0.3; with re-sieve on, the net slack rises 0.1–0.4.
     - *Annotation:* D-gc assumed the small-modulus price 0.114 (ruint), but the card charges setup_small at 0.307 (ruint) and 1.14 (Montgomery). At the charged price, one word op per update gives 11.6–13.4%, and two ops give 10.1–11.7%. So its test "above 13% means more than one op was counted" is reversed: more ops per update means a smaller saving. The headline is scored against the stated range regardless.
   - **(D-pinv)** Precomputed pool-prime inverses: break-even at ~0.32 P A's; A's per run 10–20 / 20–40 / 30–60 / 50–100 at 54 / 72 / 84 / 96; net saving 0–0.5 / 0.5–1.5 / 1–3 / 2–4% of qs cost; falsified above 6%.
     - *Annotation:* its break-even prices the precompute's Euclid runs at word level and the per-A Euclid runs at small-modulus. Priced consistently, the break-even is ~P A's. Its 29 Euclid steps per inverse is high for p < ~2000 (typically ~6–7 steps); the card's measured setup_euclid share is used instead.
     - A lazily filled cache (compute a pool prime's inverses mod every factor-base prime the first time it appears in an A) costs at most (distinct pool primes used) × F Euclid runs, so it never costs more than today. This is noted on the MOVES row, candidate (c). [Wrong, Claude chat's error: it assumed distinct pool primes ≤ A's per run; measured 9–29 distinct against 4–27 A's. See the A-count step.]
   - **(D-qr, on W-qr)** the restricted simulated yield is 0.07–0.09 at every size; W-qr misses at 72–84 and holds at 96.
     - *Annotation:* it doubled a baseline of 0.04, but the simulated yields were 0.076 / 0.064 / 0.051. Doubling those gives ~0.15 / 0.13 / 0.10, within W-qr's ±25% at all three sizes. Both are scored as written when the user's Mathematica run arrives.
   - *DeepSeek on 2LP:* it stays marginal regardless of W-qr (scarcity: 0–3 candidates per number). Reopen it only if a looser threshold (+0.5–1.0 slack) pays after re-sieve. This is added to the 2LP MOVES row.
3. **Confounding guard (adopted as a rule, user, Oct 25):** the Gray-code re-typing changes prices only, not op counts.
   - For the re-sieve slack retune, op counts by type are logged per run, and every sweep is priced both ways (current and re-typed).
   - The existing full-pass slack sweep is re-priced both ways if its by-type counts are recoverable; if not, this says so.
   - The report gives the 2×2 (re-sieve off / on × re-typed no / yes): best slack and qs cost per pricing, per size. D-rmslack, G-rmslack and D-gc's slack clauses are scored from that table.

**A-count information step** (`evolve/acount.py`, `acount.out`). New reference genes as qs alone (corrected card, kset), Python traces on 3 balanced and 3 band-24 map numbers per size.

| bits | A's per run (range) | distinct pool primes used | P | s | polynomials per A | F | Euclid steps per inverse | per-A inverses today: share of qs cost, off. / ruint / Mont. | lazy cache instead | net |
|---|---|---|---|---|---|---|---|---|---|---|
| 54 | 4.2 (3–7) | 9.3 | 28 | 3 | 3.6 | 35 | 4.03 | 0.017 / 0.046 / 0.055 | 0.053 / 0.138 / 0.165 | −0.035 / −0.092 / −0.110 |
| 72 | 9.0 (6–14) | 17.0 | 32 | 4 | 7.6 | 56 | 4.83 | 0.015 / 0.053 / 0.059 | 0.041 / 0.142 / 0.156 | −0.026 / −0.089 / −0.098 |
| 84 | 10.5 (6–17) | 21.0 | 32 | 4 | 7.8 | 92 | 5.31 | 0.011 / 0.052 / 0.056 | 0.030 / 0.138 / 0.147 | −0.019 / −0.086 / −0.091 |
| 96 | 27.2 (13–42) | 28.7 | 32 | 4 | 7.9 | 136 | 5.76 | 0.011 / 0.063 / 0.066 | 0.018 / 0.102 / 0.106 | −0.007 / −0.039 / −0.040 |

- **The lazy cache loses at every size, under every pricing** (−0.7% to −11% of qs cost).
  - A run uses only 4–27 A's but touches 9–29 distinct pool primes: on-demand selection with its overlap limit brings in about one new prime per A. So filling the cache (distinct primes × F Euclid runs) costs more than today's per-A Euclid runs (A's × F), before the s − 1 extra multiplications per A per prime.
  - *The annotation's "never costs more than today" assumed distinct primes ≤ A's; here it is the other way round.*
  - A full precompute (P × F) is worse still. **Candidate (c) does not pay at 54–96 bits.** It could pay only with many more A's per run (larger N), or with A's chosen from a small fixed subset of the pool.
- Euclid takes 4.0–5.8 steps per inverse (not ~29).
- **(D-pinv, DeepSeek's)** A's per run 10–20 / 20–40 / 30–60 / 50–100 and net saving 0–0.5 / 0.5–1.5 / 1–3 / 2–4%: **missed.** A's per run are 4.2 / 9.0 / 10.5 / 27.2, below every range, and the lazy-cache net is negative everywhere. (Its precompute variant would be worse.)

**Grok's predictions (Oct 25, late), with annotations** (labelled as Grok's; annotations by Claude chat, relayed by the user). Recorded while the full-pass re-pricing (`slackrep.py`) was running, before any of its output was read. *Timing:* G-pinv arrived **after** the A-count result had been committed (642f91d), so it is post hoc.
1. **(G-gc)** Gray-code re-typing (Grok counts 2 word ops per update; re-sieve off; the current tuned genes). Saving in total qs cost: ruint 4–7% / 5–9% / 6–10% / 6–11% at 54 / 72 / 84 / 96; Montgomery 3–6% / 4–8% / 5–9% / 5–10%. Falsified if any size shows a cost increase, or if the ruint saving falls outside 3–12%.
   - *Annotation:* at 2 ops (2 × 0.034 against 0.307 ruint; 2 × 0.125 against 1.14 Montgomery) about 78% of the slice disappears. Applied to the measured shares, that implies ruint ~4.5 / 11.0 / 10.0 / 11.4% and Montgomery ~5.4 / 12.1 / 10.6 / 11.7%, above Grok's ranges at 72 and 96 (ruint) and at 72–96 (Montgomery). Its lower ranges hold only if the "Gray-code switching" slice contains charges other than the update. The cost-model entry must list what the slice contains.
2. **(G-slack2x2)** Best slack at 72 / 84 / 96: off/no 2.00 / 2.05 / 2.10 (baseline; not scored); on/no 2.30 / 2.35 / 2.40; off/yes 1.85 / 1.90 / 1.95; on/yes 2.20 / 2.25 / 2.30.
   - Effects: re-sieve alone +0.25–0.45; re-typing alone −0.10 to −0.25; combined +0.15–0.35.
   - Falsified if re-sieve raises the slack by less than 0.15, or if the combined cell lands below 2.0.
3. **Slack scoring rule (ADOPTED, user, Oct 25, before results).** It applies to G-slack2x2, G-rmslack, D-rmslack and D-gc's slack clauses.
   - Slack is scored under ruint and Montgomery separately; official is reported but not scored (its curve is flat above ~2.0).
   - The best slack is the lowest-cost grid point, reported with a paired-bootstrap interval for its shift against off/no.
   - A shift counts as real only if the interval excludes zero.
   - The sweep grid step is 0.1 or finer around 1.6–2.8.
   - A prediction that names no pricing is scored under ruint.
   - *Note:* the running `slackrep.py` (full pass, coarse grid 1.0 / 1.5 / 2.0 / 2.5 / tuned) is the re-pricing information step, not the scored 2×2. The scored 2×2 retune uses the 0.1 grid.
4. **(G-pinv; post hoc)** lazy pool-prime inverse cache, net saving of total qs ruint cost at the tuned genes: 1.5–3% / 2–4% / 2.5–4.5% / 3–5% at 54 / 72 / 84 / 96. Falsified if above 7% at any size, or below 1% at 84–96.
   - Note beside it: DeepSeek's D-pinv is lower. *Scored post hoc against `acount.out`:* **missed (falsified).** The lazy cache's net is −9.2 / −8.9 / −8.6 / −3.9% under ruint, below 1% at 84–96.
5. **(G-qr)** residue-restricted simulated pairing yield: 0.14–0.20 at 72, 0.11–0.16 at 84, 0.07–0.11 at 96; W-qr holds. Falsified if any size is outside ±30% of the measured 0.17 / 0.13 / 0.08, or if the simulated combined-relation share stays below 35% of F + 10.

**Full-pass slack sweep, priced both ways** (information; the confounding guard; `evolve/slackrep.py`, `slackrep.out`, `.json`).
- Python traces on 3 balanced and 3 band-24 map numbers per size. Gray-code updates are counted exactly, one charged op per root per switch, as the card charges today. Re-typed means those updates are priced at the word-level price (sieve_update's) instead of setup_small's. Op counts are identical; only prices differ.
- **The saved `slackcheck.out` could not be re-priced:** it kept only ratios, and lampcore's types do not separate Gray-code updates from the rest of setup_small. Hence this rerun on a sample.

Cost per number (op-cost units, absolute), current / re-typed:

| bits | slack | official | ruint | Montgomery | Gray updates per number |
|---|---|---|---|---|---|
| 72 | 1.0 | 540,134 | 55,714 / 48,521 | 200,019 / 173,310 | 26,396 |
| 72 | 1.5 | 261,841 | 22,300 / 18,596 | 78,893 / 65,139 | 13,593 |
| 72 | 2.0 | 155,750 | 13,364 / 11,374 | 45,958 / 38,567 | 7,304 |
| 72 | 2.5 | 145,042 | 14,700 / 13,333 | 48,505 / 43,427 | 5,018 |
| 72 | 2.226 (tuned) | 140,040 | 12,801 / 11,192 | 43,449 / 37,473 | 5,906 |
| 84 | 1.0 | 1,132,075 | 65,654 / 54,768 | 238,910 / 198,490 | 39,945 |
| 84 | 1.5 | 657,787 | 38,244 / 32,101 | 138,076 / 115,266 | 22,542 |
| 84 | 2.0 | 438,706 | 29,141 / 25,565 | 102,339 / 89,058 | 13,125 |
| 84 | 2.5 | 449,071 | 36,501 / 33,722 | 125,980 / 115,662 | 10,197 |
| 84 | 2.098 (tuned) | 424,731 | 29,104 / 25,780 | 102,283 / 89,942 | 12,196 |
| 96 | 1.0 | 5,580,673 | 333,948 / 291,181 | 1,227,604 / 1,068,805 | 156,935 |
| 96 | 1.5 | 2,963,660 | 151,811 / 128,818 | 556,183 / 470,810 | 84,371 |
| 96 | 2.0 | 1,802,531 | 99,004 / 86,061 | 357,778 / 309,718 | 47,496 |
| 96 | 2.5 | 1,702,585 | 112,623 / 102,434 | 400,212 / 362,381 | 37,386 |
| 96 | 2.009 (tuned) | 1,799,926 | 99,037 / 86,151 | 358,425 / 310,576 | 47,288 |

- **Re-typing cuts qs cost at the tuned slack by 12.6 / 11.4 / 13.0% (ruint) and 13.8 / 12.1 / 13.3% (Montgomery) at 72 / 84 / 96; official 0% (exact).** This is with one charged op per update, as today. If the cost model counts two word ops per update, the cut is smaller (≈ 78% of the slice instead of ≈ 89%).
- **The best slack barely moves on this coarse grid:** 72 stays at the tuned 2.23. 84: 2.0 and the tuned 2.10 are within 1% under both pricings (6 numbers, no interval); under the adopted slack rule this is not a shift. 96 stays at 2.0 (official's best is 2.5 at 96).
- The scored 2×2 retune uses the 0.1 grid and paired intervals, per the adopted rule. This table is information.

**Decisions (user, Oct 25), for the Gray-code cost-model entry and scoring:**
1. **Op count: ONE word-level op per root update** (the add and conditional subtract as a single word op), priced at the word-level (sieve_update) price.
   - Reasons: it keeps the op counts unchanged, so this stays a pure pricing change with official exactly 0%; and it matches the current count and the ECM modular-additions precedent.
   - *What the slice contains (answers the open point in the G-gc annotation):* the slice is essentially all updates. Two independent measurements agree: setupshare's "Gray-code switching" slice, attributed by call site, is 0.141 / 0.128 / 0.146 of qs's ruint cost at 72 / 84 / 96, and slackrep's exact update count priced at setup_small gives 0.141 / 0.128 / 0.146.
   - (slackrep's cut / Gray-share ratio of 0.889 is 1 − 0.034 / 0.307 by construction, since it re-priced exactly the counted updates. The evidence is the equality of the two shares.)
2. G-gc and D-gc are **not** scored from slackrep (a 6-number information sample, 72–96 only). They are scored from the formal before / after on all map numbers, including 54, after the cost-model entry and parity.
3. The order is unchanged: re-sieve parity, commit, re-sieve measurement, Gray-code cost model and audit list, formal before / after, the scored 2×2 retune.

**Residue-restricted large-prime simulation** (user, Mathematica, Oct 25; information only).
- *Setup:* 200 trials per size; balanced N, k = 1; B 619 / 1,171 / 1,993; lc 1.698 / 1.64 / 1.97; partials per number 260 / 444 / 976 (from lpdist); large primes drawn with weight 1/q from (B, B^lc); combined = partials − distinct q. Three arms: all primes; residue primes only ((kN/q) = 1); a random half of the primes. Simulated F (residue primes ≤ B, + 2) = 58 / 97 / 153.

| bits | all primes: yield [5%, 95%]; combined / (F + 10) | residue only | random half | measured (as stated) |
|---|---|---|---|---|
| 72 | 0.089 [0.062, 0.119]; 0.34 | 0.157 [0.123, 0.192]; 0.60 | 0.156; 0.60 | 0.17 |
| 84 | 0.087 [0.065, 0.106]; 0.36 | 0.152 [0.122, 0.180]; 0.63 | 0.152; 0.63 | 0.13 |
| 96 | 0.056 [0.044, 0.067]; 0.33 | 0.101 [0.084, 0.118]; 0.61 | 0.100; 0.60 | 0.08 |

- *The user's findings:*
  1. Residue-only and random-half agree to within 0.001: the effect is the halved support, not anything particular to residues. The quadratic-residue restriction, which halves the support in the real card, accounts for the repeat gap.
  2. The unrestricted arm does not reproduce the earlier simulation (0.076 / 0.064 / 0.051), most likely because of different partial counts. Comparisons within this run are sound; the doubling annotation on D-qr used the old baseline.
  3. Open, low priority: the overshoot at 84–96. A clean check measures the pairing yield on the same traces lpdist used; it is queued as information, not before the current order.
- **Definition caveat (found while recording):** the "measured" 0.17 / 0.13 / 0.08 (`slack2.out`) is combined relations **per partial filed**, and the card files a q only the first time it appears, so the denominator is the distinct q's. The simulation's yield is combined relations **per partial**. The two denominators differ by exactly the combined count: distinct q + combined = 260 / 443 / 976, the lpdist partial counts.
  - On the simulation's definition, the measured yields from the same traces are **0.141 / 0.112 / 0.076**, and residue / measured is **1.12 / 1.36 / 1.32** (not 0.92 / 1.17 / 1.26).
  - The definition-free comparison, combined / (F + 10), gives measured 0.58 / 0.49 / 0.50 against the residue arm's 0.60 / 0.63 / 0.61.
  - *So:* the halved support explains most of the repeat excess, close at 72 and over-accounting by ~25–35% at 84–96. Finding 3's check (yield on the same traces, matched definition) is the way to settle the remainder.
- **Scores, as written** (the predictions named the stated figures 0.17 / 0.13 / 0.08, so they are scored against them):
  - **(W-qr, Claude chat's) FALSIFIED.** The yield clause holds at 72 (0.92) and 84 (1.17) but misses at 96 (1.26 > 1.25). The combined clause misses (0.60–0.63 against 40–55%); its range was anchored on the earlier 24–28% baseline.
  - **(G-qr, Grok's) HOLDS** at all sizes (0.157 in 0.14–0.20, 0.152 in 0.11–0.16, 0.101 in 0.07–0.11; within ±30%; combined ≥ 35%).
  - **(D-qr, DeepSeek's) MISSED** at all sizes (0.157 / 0.152 / 0.101 against 0.07–0.09).
  - *Beside the scores:* on the matched definition, G-qr's ±30% clause would fail at 84 (1.36) and 96 (1.32), and W-qr's ±25% would fail at 84 and 96. The scores above stand as written; the caveat is recorded so the ratios are not read as matched.

**DeepSeek's reply (Oct 25, latest), with annotations** (labelled as DeepSeek's; annotations by Claude chat, relayed by the user).
1. **Beside D-pinv:** DeepSeek attributes its miss to assuming distinct pool primes ≤ A's per run.
   - *Annotation:* that assumption was Claude chat's (in the lazy-cache annotation), not DeepSeek's. DeepSeek's own D-pinv missed because it overestimated A's per run (10–100 against 4.2–27.2) and its break-even priced the same Euclid run at two prices. DeepSeek marks its setup predictions low confidence.
2. **(D-cc)** clean check, residue-restricted simulation / pairing yield measured on the same traces as the partial counts: ratio 0.98–1.08 at 72, 1.05–1.15 at 84, 1.10–1.20 at 96. Falsification as stated: a matched ratio above 1.25 at 96; below 0.90 at 72; all three within ±5% of 1.0 would mean the whole gap was run mismatch.
   - *Annotation:* the ratio is sim / measured, so an overshoot means the simulation over-counts collisions. Filed q's that sit heavier toward large q (medians above √lc) spread the draws and lower real collisions, which explains the overshoot. DeepSeek's wording ("narrows support, sim under-counts") has the direction reversed, and so does its "below 0.90 at 72 = over-predicting" clause (below 0.90 means under-predicting). Its proposed simulation fix (weight draws by the card's observed q distribution) is sound. The ratios are scored as given.
   - **Timing (mine):** the clean check is already done. `slack2.py` and `lpdist.py` ran the same three balanced map numbers with the same genes at the tuned slack, and their partial counts agree exactly (distinct q + combined = 260 / 443 / 976). The matched ratios **1.12 / 1.36 / 1.32** were committed in 86eb28f **before D-cc was written**. So D-cc is scored post hoc.
   - *Scored post hoc:* **missed.** 72 is 1.12 (range 0.98–1.08), 84 is 1.36 (1.05–1.15), 96 is 1.32 (1.10–1.20), and its own falsifier fires (above 1.25 at 96).
   - The queued "clean check" item (6 below) is therefore already answered by the existing traces. A larger sample would only tighten it.
3. **(D-gc54)** formal Gray-code before / after at 54 bits, one word op per update: ruint 4.6–5.8% (point 5.2%), Montgomery 5.4–6.8% (point 6.1%), official 0% exact; the best slack at 54 does not move on the 0.1 grid. Pre-registered; the formal before / after has not run.
   - *Annotation:* its ">7% ruint means more than one op per update" clause is reversed (more ops means a smaller cut). Under the adopted one-op count, >7% would mean the 54-bit share is under-measured.
4. **Finding (not a MOVES row):** in the simulation, the residue-only and random-half arms are identical, so the large-prime collision rate depends on the size of the support (roughly 1 / support for spread weights), not on residues as such.
5. A MOVES row "Pool-reusing A selection" is added (untested, low priority), with DeepSeek's prediction and the ceiling annotation.
6. *Queued (information, low priority):* the pairing yield on exactly the lpdist traces. **Already available** from `slack2.out` and `lpdist.out` (item 2); only a larger sample remains.

**Large-prime simulation with the filed q shape** (user, Mathematica, Oct 26; information only; post hoc, since no prediction was registered on it).
- *Setup:* as the previous run (residue primes only). Arm 1: weight 1/q. Arm 2: draws matched to lpdist's filed shares of log_B q in 0.2-wide bins, 1/q within each bin.

| bits | arm 1 (1/q): yield [5%, 95%]; ratio to 0.17 / 0.13 / 0.08; combined / (F + 10); median log_B q | arm 2 (filed shape) | filed median (lpdist) |
|---|---|---|---|
| 72 | 0.159 [0.127, 0.192]; 0.94; 0.61; 1.304 | 0.129 [0.096, 0.162]; 0.76; 0.49; 1.345 | 1.363 |
| 84 | 0.151 [0.124, 0.178]; 1.16; 0.62; 1.283 | 0.104 [0.079, 0.131]; 0.80; 0.43; 1.353 | 1.358 |
| 96 | 0.100 [0.083, 0.117]; 1.25; 0.60; 1.406 | 0.068 [0.053, 0.082]; 0.85; 0.41; 1.462 | 1.469 |

- *The user's findings:*
  1. Arm 1 reproduces the previous run, and arm 2's drawn medians match the filed ones (the sanity checks pass).
  2. Matching the filed shape over-corrects: the simulation now under-predicts at every size (0.76–0.85). Collisions come mostly from q just above B. The filed partials put less weight there than 1/q (the lowest bin is 0.27 against ~0.34 at 72), and that small shift (median +0.06) removes 20–30% of collisions.
  3. The card therefore repeats ~1.2–1.3x more than a shape-matched simulation. Open candidates: (i) within-bin concentration near B that 0.2-wide bins cannot see; (ii) a run mismatch between the measured yields and the partial counts.
  4. Nothing is scored. Note only: the shape-matched ratios rise with size (the direction of G-cc's monotone clause), and DeepSeek's "skew explains the 84–96 residual" holds in direction, but the full shape over-corrects.
- **Definition caveat again (mine):** the ratios above divide by the per-partial-filed figures 0.17 / 0.13 / 0.08 (denominator: distinct q). On the simulation's per-partial definition, the measured yields on the same traces are 0.141 / 0.112 / 0.076 (86eb28f).
  - On the matched definition, arm 2 / measured is **0.91 / 0.93 / 0.89** (the shape-matched simulation under-predicts by ~7–11%, not 15–24%), and arm 1 / measured is 1.13 / 1.35 / 1.32.
  - The combined / (F + 10) shares, which need no definition, give measured 0.58 / 0.49 / 0.50 against arm 2's 0.49 / 0.43 / 0.41: under-prediction of 14–18%.
  - Candidate (ii), run mismatch, is excluded: the measured yields and the partial counts come from the same traces (slack2 and lpdist ran the same three numbers with the same genes; their counts agree exactly).
- **The clean check, upgraded** (information; queued after the current order; now the decisive step for this thread). On exactly the lpdist traces, per size 72 / 84 / 96:
  - (a) the measured pairing yield on **both** definitions (combined per partial occurrence, and combined per distinct q filed), and combined / (F + 10);
  - (b) a histogram of log_B q of filed partials in 0.05-wide bins from 1 to lc, and the share of filed q in (B, 2B];
  - (c) the number of distinct q and the count of q filed 2, 3 and 4+ times.
  - D-cc and G-cc are scored from (a) against this run's residue 1/q arm 1 (0.159 / 0.151 / 0.100). The definition used for the score is stated; the user's choice decides, defaulting to per occurrence (matching the simulation).

### Re-sieve against full-pass confirmation (`evolve/resieve_measure.py`, `resieve_measure.out`, `.json`)

- *Setup:* qs alone on all map numbers, at each genome's own tuned slack, current pricing (the Gray-code re-typing is not applied; it is reported separately), p0 = 30. No misses. Cost per number in op-cost units, full pass → re-sieve (ratio re-sieve / full pass).

| bits | new reference genes: official / ruint / Montgomery | frozen reference (old): official / ruint / Montgomery | old genes on the corrected card: official / ruint / Montgomery |
|---|---|---|---|
| 54 | 25,934 → 26,889 (1.037) / 3,131 → 2,906 (0.928) / 9,800 → 8,951 (0.913) | 1.020 / 0.975 / 0.946 | 1.025 / 0.935 / 0.925 |
| 72 | 133,430 → 144,189 (1.081) / 12,106 → 10,909 (0.901) / 40,597 → 36,087 (0.889) | 0.973 / 0.879 / 0.820 | 0.973 / 0.820 / 0.805 |
| 84 | 428,755 → 498,417 (1.162) / 30,087 → 27,934 (0.928) / 105,227 → 97,016 (0.922) | 0.960 / 0.898 / 0.809 | 0.956 / 0.753 / 0.739 |
| 96 | 1,380,373 → 1,743,100 (1.263) / 79,657 → 81,953 (1.029) / 286,099 → 293,985 (1.028) | 0.935 / 0.824 / 0.726 | 0.932 / 0.678 / 0.667 |

- **On the new reference genes, re-sieve saves 7–11% under ruint and Montgomery at 54–84, and loses ~3% at 96. It loses under official at every size (+4% to +26%).**
- **On the old genes it saves far more:** 25–33% calibrated at 84–96, and it even gains under official (4–7%).
- *Why:* the walk costs about the update count of primes ≥ p0 across the whole interval (2 word ops per position), while the saving is proportional to candidates × F.
  - The old genes (kc 32, bc 1.1, mc 0.25) have a large F and a narrow interval: many divisions saved per walked position.
  - The new genes have a small bc (0.43–0.87) and a wide interval (mc 0.39–0.60): a small F, few candidates per position walked. The walk then outweighs the divisions saved, more so at 96 (bc 0.43, mc 0.60).
- So **re-sieve's value depends on the genes,** and the genes were tuned for full-pass confirmation. The retune with re-sieve on (next) is where it is judged. The tuned genes should move toward larger F, narrower intervals and a looser slack. These are fixed-gene numbers, not a verdict.
- *Against my cost model's expectation* (net 8–12% under ruint and Montgomery, a loss under official): held at 54–84 for the new reference genes (7.2–11.1%, with 54 ruint at 7.2% marginally below), missed at 96 (−2.9%). The official loss held.
- **Predictions, scored as written at the current tuned genes** (none specified a retune):
  - (D-rm, DeepSeek's) official −2% to +1%, ruint 18–23%, Montgomery 21–26%: **missed** (official +3.7% to +26%; ruint 7.2 / 9.9 / 7.2 / −2.9%).
  - (D-rm2) 24–30% ruint, 26–33% Montgomery at 84, ±5 points across sizes: **missed** (7.2% / 7.8% at 84).
  - (G-rm, Grok's) official −1% to +3%, ruint 8–14%, Montgomery 10–16%: **missed.** Ruint is in range only at 72 (9.9%); official is +3.7–26%.
  - The revisions (G-rm revised 20–32%; D-rm2) are recorded as revisions; the originals are the scored ones.
  - D-rm+spv and G-rm+spv await small-prime skipping.

**DeepSeek's reply (Oct 26), with annotations; two corrections** (labelled as DeepSeek's; annotations by Claude chat, relayed by the user).
1. DeepSeek acknowledges both direction reversals (the D-cc reading and the D-gc54 audit clause). Its traced statement on D-gc54 is "saves 0.114 − k × 0.034 per update".
   - *Annotation:* that repeats the original D-gc price error. setup_small is 0.307 under ruint, so the saving per update is 0.307 − k × 0.034: 0.273 (89% of the slice) at k = 1, 0.239 (78%) at k = 2, 0.205 (67%) at k = 3, and negative only at k ≥ 9. The direction is now correct; the numbers are not.
   - The "Pool-reusing A selection" MOVES row's prediction is reworded, per DeepSeek, to "recovers at most the cache's loss, at the cost of a narrower A choice" (ceiling ~2% of qs cost, as annotated).
2. **Correction (Claude chat's error):** the 1/q reference for the share of filed q in (B, 2B] given in the last DeepSeek update was ln 2 / (ln B · (lc − 1)), which assumes log_B q is uniform. Under 1/q weighting on primes, the density of t = log_B q is ∝ 1/t on [1, lc]. So the share is ln(1 + log_B 2) / ln(lc) = **0.193 / 0.189 / 0.129** at 72 / 84 / 96 (not 0.154 / 0.153 / 0.094). The lowest-bin reference (~0.34 at 72) was already correct.
3. **Pre-registered as given:**
   - **(D-b2b)** share of filed q in (B, 2B]: 0.11–0.13 / 0.12–0.14 / 0.09–0.11 at 72 / 84 / 96. Falsified if the share exceeds the 1/q reference at any size, is below 0.08 at 72 or 84, or rises monotonically across sizes.
     - *Annotation:* its ranges were scaled from the wrong reference (item 2). Its ranges are scored as given; the "exceeds the reference" clause is scored against the corrected reference 0.193 / 0.189 / 0.129.
   - **(D-mt)** pairing yield measured on the lpdist traces: 0.16–0.18 / 0.12–0.14 / 0.075–0.085 (within 10% of the old values); the shape-matched simulation keeps under-predicting at a ratio of 0.76–0.85. If the matched-trace yield moves more than 15% from the old values, all large-prime predictions (W-qr, D-qr, G-qr, D-cc, G-cc) are re-scored against the new target as well as the old, both reported.
     - *Note (mine):* the old values 0.17 / 0.13 / 0.08 are per distinct q filed. D-mt is scored on that same definition, and the per-occurrence figure is reported beside it.
   - *DeepSeek's proposal* that the repeat histogram predicts the yield independently.
     - *Annotation:* not independent. Combined from partials = partials − distinct q = Σ over q of (count − 1), so the histogram and the yield are the same count.
4. **Clean check, item (c) extended:** repeats of a large prime q are split into
   - (i) genuine repeats (different relations sharing q), and
   - (ii) exact duplicate partials (the same relation found twice, e.g. by A's sharing s − 1 primes; see the dedupe MOVES row, which measured 0.30 per run under enumerate and "more" under on-demand, unmeasured).
   - The pairing yield is reported with and without exact duplicates. Exact duplicates are a candidate for the card's ~1.2–1.3x excess over the shape-matched simulation, alongside within-bin concentration near B. (Run mismatch is already excluded: same traces.)
   - *Note (mine):* the ledger's dedupe keys full relations by |u| and combined ones by min(cu, N − cu). A partial found twice (same u, same q) combines with its own first copy into u² · …, a trivial relation, unless the check is on. The clean check counts these.

## 2026-10-26 — Gray-code root update re-typed to word-level: cost-model entry (before code), and the card audit

**What changes.** In qs's polynomial switching (Gray code), each switch updates every sieved prime's roots: r ← r ± 2 B_v A⁻¹ (mod p) for each root (1 or 2 per prime).
- Today it is charged `setup` (typed setup_small: 1 / 0.307 / 1.137 under official / ruint / Montgomery), n_roots ops per switch (qs.py, "charge("setup", n_roots)"; qs.rs, the same).
- **New:** the same n_roots ops per switch, charged to the word-level phase (type "word": 1 / 0.034 / 0.125).
- **Ops per update: one word op** (the add and conditional subtract as a single word op; user's decision). **Updates per switch:** n_roots = Σ over sieved primes of their root count, as now. Switches per A: 2^(s−1) − 1.
- **Op counts are unchanged**, so official changes by exactly 0%. Only the type label moves from setup_small to word.
- *Expected cut of the slice:* 1 − 0.034 / 0.307 = 89% (ruint) and 1 − 0.125 / 1.137 = 89% (Montgomery). The slice is the Gray-code switching share measured by setupshare: ruint 0.058 / 0.141 / 0.128 / 0.146, Montgomery 0.069 / 0.155 / 0.136 / 0.150 at 54 / 72 / 84 / 96. Expected qs cost cut: **ruint 5.2 / 12.5 / 11.4 / 13.0%, Montgomery 6.1 / 13.8 / 12.1 / 13.4%; official 0%.** The formal before / after on all map numbers measures it.
- **The slice contains only these updates** (setupshare's call-site slice equals slackrep's exact update count; see above).
- *Applies to every qs genome,* including both references. *Acceptance:* every type except setup_small and word is unchanged per number; setup_small falls by exactly the word count, which equals Σ switches × n_roots from the trace; Python = Rust parity.

**Audit: other steps charged above word level that are, physically, adds, compares, word multiplies or lookups.** Listed only; **none is re-typed without its own note and the user's decision.**

| # | step (where) | today's type and price (ruint / Montgomery) | what it physically is | candidate type |
|---|---|---|---|---|
| 0 | **Ledger duplicate check, `add()`: a set lookup of \|u\| (full) or min(cu, N − cu) (combined) per relation offered** | **uncharged** | a hash lookup | word, 1 per relation offered. **An uncharged op: a critical bug by CLAUDE.md. Small (~F + 10 to a few hundred lookups per run), but it must be charged; cost-model note and fix proposed as the next pricing commit.** |
| 1 | On-demand A selection: overlap checks against used A's ((s − 1)·\|used\| per prefix, s·\|used\| per accepted A), the closeness scan over remaining pool primes, the target check, t′ = target / A′ | setup_small, 0.307 / 1.137 | comparisons of small integers and floats, a float divide | word |
| 2 | The sorts under sort_charge: multiplier ranking (mult), pool selection, enumerate's candidate sort (setup) | mult / setup_small, 0.307 / 1.137 | comparisons | word |
| 3 | Forming A and its prefixes: (s − 1) multiplies per prefix or candidate; A′ = product of s − 2 primes | setup_full, 1.0 / 1.0 (full mod-N multiply) | products of primes < 2^16 into A < 2^40: a word multiply | word |
| 4 | B_l = A/q · γ (and the 2s-per-A part of setup_full) | setup_full, 1.0 / 1.0 | a word multiply (A/q < 2^40, γ < q) | word |
| 5 | Evaluating v = (A x + 2B) x + C per candidate (2 confirm_full) | confirm_full, 1.0 / 1.0 | |v| ≤ M√(kN/2) ≤ ~2^60 at 96 bits: one- or two-word multiplies, not a mod-N multiply | word (or a two-word multiply type) |
| 6 | Large primes: the bound check v < L, the hash lookup and insert | lp_small, 0.114 / 0.426 | a compare, a lookup, an insert | word |
| 7 | Large primes: the F-entry exponent-vector add per combination | lp_small, 0.114 / 0.426 | F small-integer adds | word |
| 8 | The confirmation's sign check (the "1 +" in re-sieve's charge, and inside today's F) | confirm_td, 0.114 / 0.426 | a compare | word |

Not candidates, because they really reduce modulo a small prime: the factor-base Legendre symbols and Tonelli–Shanks, the KS scores' Legendre symbols, A/q mod q and γ = t · inv mod q, the per-A roots r1, r2 and 2 B_l A⁻¹ mod p, the Euclid inverses, the trial divisions and repeats, and N mod q for a large prime.

- *Sizes, for ordering (information, from the setupshare / confirmshare splits; not measured per item):*
  - item 1 is most of A selection's 6–11% (ruint) at 54–72;
  - items 3–4 are setup_full, 0.6–2.5% of ruint cost;
  - item 5 is confirm_full, about 1–3% of ruint cost (2 per candidate);
  - items 6–7 are lp_small, ~1–3%.

**Grok's predictions (Oct 26), with annotations** (labelled as Grok's; annotations by Claude chat, relayed by the user). Pre-registered; the clean check has not run.
1. **(G-b2b)** share of filed q in (B, 2B]: 0.155–0.185 / 0.150–0.180 / 0.100–0.135 at 72 / 84 / 96 (centres ~0.17 / 0.165 / 0.12; reference 0.193 / 0.189 / 0.129). Falsified if any share is outside 0.12–0.22, or if the shares fail to decline with size.
   - *Annotation:* the decline clause is weakly informative (the reference itself declines with size).
2. **(G-mt)** pairing yield on the lpdist traces: with duplicates 0.15–0.19 / 0.11–0.15 / 0.07–0.10; without duplicates 0.13–0.17 / 0.09–0.13 / 0.055–0.085 (10–20% lower). Falsified if any "with" yield is outside 0.05–0.25, or if without / with is outside 0.70–0.95 at any size.
   - *Note (mine):* the "with" ranges match the per-distinct-q definition (old values 0.17 / 0.13 / 0.08), so G-mt is scored on that definition, with the per-occurrence figures beside it.
3. **(G-dup)** exact duplicates as a share of all repeats: 25–45% / 30–50% / 35–55% at 72 / 84 / 96. Primary explanation of the 1.2–1.3x excess: exact duplicates; secondary: concentration near B; smallest: run mismatch. Falsified if the duplicate share is under 15% or over 70% at any size, or if, after duplicate removal, (measured without duplicates) / (residue 1/q simulation) exceeds 1.25 at two or more sizes.
   - *Annotations:*
     - G-mt and G-dup are mutually inconsistent. Removing duplicates gives without / with ≈ (1 − d) / (1 − y·d) for duplicate share d and yield y. G-dup's ranges imply 0.60–0.78 / 0.53–0.73 / 0.47–0.67, mostly below G-mt's 0.70–0.95; they overlap only at the low end of G-dup, and not at all at 96. Both are scored as given.
     - To remove a 1.2–1.3x excess, duplicates would need to be ~17–24% of repeats. G-dup's ranges would over-explain it, putting the measured yield below the shape-matched simulation.
     - The residual clause compares with the residue 1/q arm (0.159 / 0.151 / 0.100), but the 1.2–1.3x excess was measured against the shape-matched arm (0.129 / 0.104 / 0.068). The clause is scored as written, and the residual against the shape-matched arm is also reported.
   - *Note (mine):* run mismatch is already excluded (same traces).
4. **Clean-check reporting, added:** per size, the duplicate share d of repeats, the without / with yield ratio, and the residual ratio of the without-duplicates yield to both simulation arms (1/q and shape-matched), on both yield definitions.

**Report and hold before the 2×2 retune (user, Oct 26).**

*1. Re-sieve parity:* it finished and passed (qs 4,410 pairs, types 6,830, mutations 48/48, 0 mismatches; `parity_resieve.out` ends "exit 0"). It is committed in **7d3b4b3**, with the acceptance output. The card code itself entered in 783e885 (the disclosed `commit -a` slip).

*2. Pairing-yield definitions, exactly:*
- (i) **The old "measured" 0.17 / 0.13 / 0.08** (`slack2.py`) is Rc / ins. Rc = at["lp"]["combos"], the number of times a partial met an already-filed q and was combined. ins = at["lp"]["inserts"], the number of q's filed for the first time, i.e. the distinct q. So it is **per-distinct-q** = (partials − distinct q) / distinct q. The printed values were 0.166 / 0.125 / 0.082 (distinct q 223 / 394 / 902 per number).
- (ii) **lpdist** counts every candidate whose cofactor after trial division is 1 < v < L, i.e. every partial occurrence: 260 / 443 / 976 per number. Its label "partials filed" is a misnomer: these are occurrences, = distinct q + combinations. It computes no yield.
- **The old values on both definitions:** per-distinct-q 0.166 / 0.125 / 0.082; **per-partial = (partials − distinct q) / partials = 37.0 / 260 = 0.142, 49.3 / 443 = 0.111, 74.0 / 976 = 0.076.**
- **So the simulation comparisons (W-qr, D-qr, G-qr, and both Mathematica runs) compared different definitions.** The simulations used per-partial; the "measured" target was per-distinct-q. This is a miss in the setup of the comparison (Claude chat's: the Wolfram prompts did not check the definition).
- Re-stated per-partial (measured 0.142 / 0.111 / 0.076): ratio to the residue 1/q arm (0.159 / 0.151 / 0.100) = **1.12 / 1.36 / 1.32**; to the shape-matched arm (0.129 / 0.104 / 0.068) = **0.91 / 0.94 / 0.89**. (The user's approximations were 0.145 / 0.115 / 0.074, 1.10 / 1.31 / 1.35 and 0.89 / 0.90 / 0.92.)
- **Proposed, not applied until the user confirms:** score all large-prime predictions on the per-partial definition, with the original scores kept beside them.

*4. The audit list:* in full in the Gray-code cost-model entry above (items 0–8). Item 0 in detail:
- **What it does:** `Ledger.add` (ledger.py; `Ledger::add` in qs.rs, line ~340) rejects a relation already kept. For a full relation (y = 1) it looks up |u| in a hash set and inserts it if absent. For a combined relation it looks up min(cu, N − cu) in a second set and inserts it if absent.
- **Charged today:** nothing. In Rust it is one `HashSet::insert` (a lookup and an insert in one call); in Python a membership test plus an add.
- **Ops per run if charged** at one word op per relation offered (the lookup-and-insert as one op, as Rust does it), or two (lookup + insert): relations offered ≈ full relations + combinations. From the slack2 traces that is ≈ 30 + 37 / 52 + 49 / 75 + 74 per number at 72 / 84 / 96, i.e. **~70–150 ops per run (140–300 at two ops)**. Under ruint that is ~2–10 op-cost units against qs's 12k–80k (< 0.05%); under official, < 0.1%.
- **Type and price:** word (1 / 0.034 / 0.125).
- **Affected:** every genome that uses the ledger: **both references and the new reference genes, every qs genome, and the cfrac card** (it shares the Ledger). min(cu, N − cu) also involves one multi-word subtraction (word-level).
- **It changes official counts, so it is a meter correction, not a re-pricing.** It needs its own cost-model entry, application to every genome, parity and a separate report. **Not fixed yet** (user's instruction).
- *Found while checking this:* the square-search card ("sq", mode "smooth", main.rs ~line 306 and its lamps.py twin) also keeps an uncharged set of tried multipliers (insert per k, contains per k up to kk). The sq card is not in any current pipeline. It is listed as audit item 9, same treatment.

*5. Re-sieve scoring:* the formal re-sieve measurement (all sizes, per pricing, against the full pass, on all map numbers) **has already run and is committed** (772632a, "Re-sieve against full-pass confirmation"). D-rm, D-rm2 and G-rm were scored there "as written at the current tuned genes". The user's instruction not to score before the formal measurement is met by that run. If the user prefers the scores held until the retune, they can be marked provisional; they are left as recorded.

**Pairing yield on both definitions** (user, Mathematica, Oct 26; information only; post hoc).
- *Setup:* as the previous run (residue primes only, 200 trials, same B, lc and partials); arm 1 1/q, arm 2 filed shape. Per-partial = combined / partials; per-distinct = combined / (partials − combined).

| bits | arm 1: per-partial / per-distinct | arm 2: per-partial / per-distinct | user's ratios if the measured 0.17 / 0.13 / 0.08 were per-partial (A) / per-distinct (B) |
|---|---|---|---|
| 72 | 0.157 / 0.187 | 0.126 / 0.145 | arm 1 A 0.92, B 1.10; arm 2 A 0.74, B 0.85 |
| 84 | 0.151 / 0.179 | 0.103 / 0.115 | arm 1 A 1.16, B 1.38; arm 2 A 0.79, B 0.88 |
| 96 | 0.100 / 0.111 | 0.067 / 0.071 | arm 1 A 1.25, B 1.39; arm 2 A 0.83, B 0.89 |

- *The user's findings:*
  1. The definition matters but does not close the gap. Under B, the shape-matched simulation is short by 11–15% (under A, by 17–26%). Claude chat's earlier statement that most of the excess "would be a definitional artifact" overstated it; about half would be.
  2. Under either definition the truth lies between the two arms, consistent with the open candidates (concentration near B within 0.2-wide bins; exact duplicate partials).
  3. The arms reproduce the previous runs.
- **The definition behind 0.17 / 0.13 / 0.08, confirmed from the code** (`slack2.py`: Rc / ins, inserts = first filings of a q): **(B) per-distinct q.** The unrounded values are 0.166 / 0.125 / 0.082 per-distinct, and 0.142 / 0.111 / 0.076 per-partial. **Column B is the matching column.**
- Matched ratios with the unrounded measured values (per-distinct): arm 1 = 0.187 / 0.166 = **1.13**, 0.179 / 0.125 = **1.43**, 0.111 / 0.082 = **1.35**; arm 2 = 0.145 / 0.166 = **0.87**, 0.115 / 0.125 = **0.92**, 0.071 / 0.082 = **0.87**.

**Large-prime predictions re-scored on the matched definition** (per-distinct, column B; the original scores, which compared different definitions, are kept beside them):

| prediction | original score (mismatched definitions) | matched-definition score |
|---|---|---|
| (W-qr, Claude chat's) residue simulation within ±25% of measured; combined share 40–55% | FALSIFIED (96 at 1.26; combined clause missed) | **FALSIFIED** (1.13 / 1.43 / 1.35: holds at 72 only; the combined clause is definition-free and still missed) |
| (D-qr, DeepSeek's) restricted simulated yield 0.07–0.09 at every size | MISSED | **MISSED** (per-distinct simulated yield 0.187 / 0.179 / 0.111) |
| (G-qr, Grok's) simulated yield 0.14–0.20 / 0.11–0.16 / 0.07–0.11; falsified if any size outside ±30% of measured, or combined share < 35% | HOLDS | **FALSIFIED** (simulated per-distinct yield 0.179 at 84 and 0.111 at 96 are above their ranges; ratios 1.43 and 1.35 are outside ±30%) |
| (D-cc, DeepSeek's; post hoc) clean-check ratio 0.98–1.08 / 1.05–1.15 / 1.10–1.20 | MISSED (per-partial 1.12 / 1.36 / 1.32) | **MISSED** (1.13 / 1.43 / 1.35) |

- The clean-check predictions (D-b2b, D-mt, G-b2b, G-mt, G-dup) await the clean check itself.
- **G-qr flips from held to falsified on the matched definition.** The others keep their verdicts.

**DeepSeek's reply (Oct 26, 00:18), with annotations** (labelled as DeepSeek's; annotations by Claude chat, relayed by the user).
1. **Definitions:** DeepSeek states that D-cc assumed per-partial on both sides, so D-cc is scored on column A (per-partial), with the column-B score beside it. *Scores:* per-partial 1.12 / 1.36 / 1.32 against 0.98–1.08 / 1.05–1.15 / 1.10–1.20: **missed** (column B, 1.13 / 1.43 / 1.35: missed). D-mt is definition-neutral: it predicts the matched-trace yield within 10% of the old values, on whatever definition those used (per-distinct).
2. **(D-dup)** exact duplicate partials are under 1% of all repeats; removing them moves the yield by under 0.5% on either definition; they do not explain the definition gap. Falsified if the duplicate share exceeds 5%, if the yield moves by more than 1% when duplicates are removed, or if the definition gap closes when they are removed.
   - *Annotation:* its derivation shows only that Gray-code neighbours within one A (B differing by ±2 B_j) cannot produce the same relation. It does not cover duplicates across different A's sharing s − 1 primes, which the dedupe MOVES row measured (0.30 per run under enumerate, about 0.7% of ~44 repeats at 72; "more" under on-demand, unmeasured; one caused an 89-bit miss under on-demand version 1). Scored as given; the argument is incomplete.
3. **(D-ledger)** the cost of the duplicate check once charged. It assumes one lookup per partial filed (hash = 1 word op, sorted list ~9 word ops) and predicts 0.02–0.15% of qs cost (ruint / Montgomery) and 0.2–1.5% official. By implementation: hash 0.01–0.05% calibrated / 0.04–0.5% official; sorted 0.1–0.5% / 0.4–5%; linear scan 0.5–5% / 5–50%. Falsified above 2% calibrated or 10% official; under 0.01% calibrated means bookkeeping only.
   - *Annotation:* it divided by a qs ruint cost of ~10^5 per number; measured at 84 bits it is ~29,000 ruint and ~425,000 official (slackrep). With its own assumptions, hash gives ~0.05% ruint / ~0.10% official and sorted ~0.47% / ~0.94%, so its calibrated ranges are ~3x low. Also, the check compares relation values u (multi-word at 84–96 bits); the type is for the cost model to set, not assumed word-level. Its point stands: the check should be charged regardless of size, because an uncharged term that grows with partials goes silent as lc rises.
4. **The ledger check's details** (added to item 0 of the audit):
   - *Implementation:* a hash set, in both cores (Python `set` membership plus `add`; Rust `HashSet::insert`, which looks up and inserts in one call). Two sets: |u| for full relations, min(cu, N − cu) for combined ones.
   - *When it runs:* once per relation offered to the ledger, i.e. per full relation found and per combination formed. **Not per partial filed:** a partial goes into the large-prime table (`partials` dict), whose lookup and insert are already charged (lp_small, 1 each). DeepSeek's "per partial filed" base therefore overstates the count (partials 260–976 per number against relations offered ~70–150).
   - *Ops per relation offered:* one hash lookup-and-insert. The key is u (up to ~2N for full relations, a residue mod N for combined ones): multi-word at 84–96 bits, so hashing and comparing it is a few word ops. **The type and op count are for the cost model to set.**
   - *Share once priced* (provisional, at one word op per relation offered): ruint 2.3 / 12,106 = 0.019% at 72 and 5.1 / 79,657 = 0.006% at 96; official 67 / 133,430 = 0.05% at 72 and 150 / 1,380,373 = 0.011% at 96. **Measured after the fix**, per pricing, in its separate report.
