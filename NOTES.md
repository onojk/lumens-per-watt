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

**First comparison.** race(ECM, qs + lc 1.4), race(rho, qs + lc 1.4) and race(ECM, N51-0917's qs stage) (addenda 6 and 7), each against its two sides alone, on both Stage 8 populations (balanced 54–84 bits; unbalanced 72/78/84 × 24/28/32), cap 2^28. Slice sizes are genes. For this comparison, three settings fixed before measurement, sa = sb ∈ {2^8, 2^10, 2^14}, are all reported, so the sensitivity to slice size is visible. Tuning them on seeds comes with Run 8. Means and worst cases with intervals; the pricings and the per-cell calls are as in addendum 6.

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
- (c) **Robust:** a candidate's score is its worst result across the three pricings (official, ruint-calibrated and Montgomery-calibrated, with median P-core prices).
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
- **pm1 takes one gcd, at the end.** A pm1 budget below its natural total finds nothing and wastes everything it spent. The optimizer searches pm1's ob over {0, natural total} only. The map already reflects this: pm1's ops-to-success, when it succeeds, is always its full length.
- **ECM ends per curve** (a gcd at the end of each curve's stage 1 and stage 2), so a budget wastes at most one partial curve; searching ECM's ob on the log grid is fine.
- td and rho test as they go (td every divisor, rho every batch), so any budget can succeed.

**Cost map** (tuning seeds only). Each lamp is run alone on every tuning number (Python, with traces): its ops-to-success (or "none within the largest budget", run to a cap of 2^21), its charge sequence, and its per-type counts; each final qs alone to the cap of 2^28. From these, the cost of any budget vector on a number is composed exactly: a stage whose ops-to-success T is at most its ob finds the factor at T; otherwise it spends its charge prefix up to and including the first charge past ob (or 0, where the precheck rule applies) and the next stage runs.
- **Proposal: per-number composition.** Lamps compute on N alone and never read another stage's state (only the ps/pm1 prechecks read the meter, and pm1 here has B < 2^26), so composing per number on the same numbers is exact on the tuning seeds and needs **no independence assumption**. The brief's version, from each lamp's per-band ops-to-success distribution with stages assumed independent per number, is the alternative. It would be needed only to extrapolate to bands not run. With per-number composition, a gap between the map and the sealed measurement is sampling (the tuning numbers differ from the sealed ones), not dependence.
- Calibrated costs of a truncated stage: its official prefix × that stage's price per official op on that band (π, from its alone runs). This is exact for td (every op is N mod d) and for pm1's multiplies, and close for rho and ECM, whose gcd share is under 0.5%. The verdict run uses exact per-type counts per stage.
- **Prerequisite, before study code:** price mappings for td and pm1 in `optypes.py` / `calibrate.py`, as the calibration plan already specified them: td's N mod d at #4 ("N84 mod small d (i128)"); pm1's multiplies at #1 and its gcd as ECM's.

**Allocation.** Minimize under the prior, on the map: a coarse grid of ob ∈ {0, 2^8, 2^9, …, 2^20} for td, rho and ECM, ob ∈ {0, natural} for pm1, then coordinate refinement on log₂ ob (scipy's bounded scalar minimization per coordinate, repeated until no coordinate moves). numpy/scipy, no optimizer built. One allocation per final-qs variant.

**Fitness: (c) robust.** The worst (largest) of log₂(mean cost) under the official count, ruint-calibrated and Montgomery-calibrated prices (median P-core prices), each in its own unit. The units are commensurable by construction: one official op is one multiply, and the calibrated unit is one reference multiply. Also reported: the worst band's mean, so an allocation can't buy a good average by sacrificing a band.

**Verdict.** Run the chosen allocation **once** on the sealed seeds, with exact per-type counts per stage. Compare against qs alone (each variant), the Run 6 p-1 front genome (L53-0972, as accepted), and the map's prediction for the sealed numbers. Report means with intervals under all three pricings, the worst band's mean, and the (e) call per comparison (the leader where all three pricings agree, else "undecided").

**Predictions (stated before any study code):**
- **Mixed population, official:** sequential budgets beat qs alone by about 2×. Reason: bands 16–28 are solved for 2^8–2^16 ops by rho/ECM against qs's ~2^19, and the budgets added to the hard bands are small next to 2^19.
- **Mixed, calibrated (ruint, Montgomery):** still beats qs alone, but by less (about 1.3–1.7×). qs's work is cheaper per op under real prices, so rho/ECM time costs relatively more.
- **The map predicts the sealed measured cost within about 10%.** If it doesn't, the first suspect is the independence assumption, or (with per-number composition, which has none) sampling between the tuning and sealed numbers.
- **Balanced-only control:** the optimizer drives all budgets to about 0 (qs alone wins), or at most a small p-1 budget (the p-1 front's 1.05–1.24×).
- **Expected budget shape:** td small, rho moderate (catches 16–24-bit p), ECM largest (28–36-bit p), p-1 small (with its search over {0, natural}: off, or on only if its whole length pays).

