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
