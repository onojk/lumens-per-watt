# Untested or thinly tested factoring methods: literature sweep

**Status:** a documentation draft, Oct 28 (the user's novelty programme, item 2). Nothing here was measured in this repository, and nothing is adopted. Every claim below is the source's claim as written. **UNVERIFIED** marks anything that could not be checked from a source that was opened. Implementations here would follow the reuse and licence rules: papers and descriptions only, no code copied.

**How it was made:**
- **The sweep:** a sub-agent of Claude Code, with web search. It opened the sources listed at the end; where a page was blocked (HTTP 403), the claim rests on search snippets or secondary sources, and is marked.
- **Spot-checked by the main session,** against the full texts the sub-agent downloaded:
  - **Murru–Salvatori §5 and §6** (the regulator, Vollmer, "(conjectured)", "more efficient than CFRAC and SQUFOF", "polynomial-time, provided knowledge of a (not too large) multiple of the regulator"): confirmed.
  - **Bradford–Wagstaff §9** ("no faster than the Quadratic Sieve"; "30-digit integers in about half a minute"; "subexponential time"): confirmed.
  - **Not re-checked:** the other items.
- **Every numeric forecast below is hand arithmetic.** Per CLAUDE.md, it goes through wolframscript before any prediction is sealed.

**The main correction to the brief's premise:** Murru–Salvatori do **not** claim L[1/2, ~1.06] for their new algorithm itself.
- Their new algorithm is polynomial **given** a (not too large) multiple of the regulator of Q(√N).
- The constant 3/√8 ≈ 1.0607 is the cost of computing the regulator with Vollmer's accelerated Buchmann algorithm (2002; Monte Carlo, under GRH).
- The authors call the end-to-end bound "(conjectured)". It is a larger constant than the quadratic sieve's L[1/2, 1], and the paper claims only to beat CFRAC and SQUFOF.
- The same constant appears in Bradford–Wagstaff's SQUFOF2: 3/(2√2) with r = 3 Gaussian elimination.

"Info / compute" below is a judgement of information per unit of compute at 40–100 bits: a recommendation, not a result.

## 1. Murru & Salvatori: SQUFOF infrastructure plus a regulator (2024 / 2025)

- **Source:** N. Murru, G. Salvatori, "Integer Factorization via Continued Fractions and Quadratic Forms", arXiv:2409.03486 (v1 2024-09-05, v2 2025-01-20; 21 pp.; no journal reference).
  - Related: Salvatori's talk at the One World Numeration Seminar, 2025-02-04.
  - It builds on M. Elia, "Continued Fractions and Factoring", arXiv:1905.10704 (Rend. Sem. Mat. Torino 78(1), 2020, per its reference list).
- **The claim:**
  - The abstract: "a computational complexity of O(exp((3/√8) √(ln N ln ln N)))", "more efficient than the classical SQUFOF and CFRAC algorithms". The algorithm "is polynomial-time, provided knowledge of a (not too large) multiple of the regulator of Q(√N)".
  - **§5:** given R⁺(N), or k·R⁺(N) with k = O(N^α), the new algorithm costs O((ln N)²) reduction and giant steps. "The cost of elementary arithmetic operations … and logarithm valuations are not counted."
  - The L[1/2, 3/√8] is the regulator step's cost. Vollmer's method is "a Monte Carlo algorithm that computes R(N) in time O(exp((3/√8)√(ln N ln ln N))), assuming the Generalized Riemann Hypothesis".
  - The conclusion: "a factorization method of (conjectured) time complexity" L[1/2, 3/√8]. **The status is conjectural and conditional on GRH.**
- **Where it applies** (§3, Table 3): it needs an even period with Q_{τ/2} ≠ 2, or the odd-period variant.
  - Guaranteed for N = pq with p ≡ q ≡ 3 (mod 4), and with p ≡ 5 (mod 8), q ≡ 3 (mod 4).
  - It gives a trivial factor for p ≡ 1 (mod 8), q ≡ 3 (mod 4) with (p/q) = −1.
  - Other classes are conditional.
  - The talk: "identifies a family of integers the method applies to, including certain RSA moduli".
- **Benchmarking: none found.** The paper has worked examples only (N = 15725, 445, 731), with no timings and no code. Searched: arXiv, indexed pages, the seminar page.
- **Implementing it here:**
  - (a) **The infrastructure** on the principal cycle: the reduction operator ρ / ρ⁻¹; the distance δ, exact or as a scaled log; composition plus reduction (the giant step). This is small and mostly shared with SQUFOF: about 1–2 weeks with parity.
  - (b) **A regulator multiple:** the real cost.
    - A subexponential regulator (Buchmann / Vollmer) needs prime-form relations, integer HNF / SNF and real-valued distances with controlled precision. That is weeks to months, and floating-point distances are awkward for Python / Rust lockstep.
    - At 40–100 bits the realistic substitute is an exponential regulator: baby-step giant-step in the infrastructure, about N^{1/4} or N^{1/5} under ERH (exact constants UNVERIFIED). That makes it an N^{1/4}-class method against SQUFOF.
- **A fair test:**
  - **Arm A:** phase 2 given an oracle R⁺(N), with the oracle charged zero. It checks the claimed O((ln N)²) form-operation count. The prediction: form ops grow as (ln N)², so a log-log slope against ln N of about 2.
  - **Arm B:** end to end with an in-house regulator, against SQUFOF, Hart's one-line factoring, rho and SIQS.
    - Balanced semiprimes, split by (p mod 8, q mod 8), with the success rate per class. Table 3 predicts 100% for the 3/3, 3/7, 7/7, 5/3 and 5/7 classes.
  - **For a subexponential regulator:** an ops ratio to SIQS of about L[1/2, 0.06], about 2.2× at 64 bits and 2.8× at 100 bits, ignoring o(1). Hand arithmetic; check in Wolfram.
  - **Info / compute:** high for Arm A (cheap; it settles the polynomial-phase claim); low for a subexponential regulator.

## 2. Bradford & Wagstaff: SQUFOF2 (2022)

- **Source:** C. Bradford, S. S. Wagstaff Jr., "Square Form Factorization, II", Bull. Polish Acad. Sci. Math. 70(1) (2022) 13–34. Author PDF: homes.cerias.purdue.edu/~ssw/squfof2.pdf. It is based on Bradford's Purdue PhD thesis.
- **The claim:**
  - It turns "SQUFOF from a O(N^{1/4}) algorithm into one with subexponential time".
  - **Theorem 4** (heuristic, under Hypotheses 1–4): expected time L(N)^{r/√(4r−4)+o(1)}, where r is the linear-algebra exponent. r = 3 gives 3/(2√2) ≈ 1.06, and r = 2.49 gives 1.02 (quoted in the introduction).
  - **The method:** sieve a binary form over a 2-D rectangle; GF(2) linear algebra to a square value; compose to a square form; SQUFOF's inverse square root; then a walk to a symmetry point.
- **Benchmarking:** the authors only, and no table.
  - §9: "SQUFOF2 factors 30-digit integers in about half a minute on a PC, while SQUFOF would take about a minute … A basic Quadratic Sieve would also take about half a minute."
  - The conclusion: "no faster than the Quadratic Sieve".
  - No independent tests were found.
- **Implementing it here:** SIQS-style parts (factor base, sieve, GF(2) elimination) plus indefinite-form composition and SQUFOF's reverse cycle. Moderate effort given the in-house QS; the walk's charged ops are new.
- **A fair test:**
  - The same factor base, sieve kernel and linear algebra as the in-house SIQS.
  - Compare yield per sieve cell, ops per relation, and post-processing ops, on balanced semiprimes at 40–100 bits.
  - **The prediction implied:** the same L exponent as QS, so the SQUFOF2 / SIQS ops ratio stays roughly constant in N.
  - **Hypothesis 2** (smoothness like random integers of size √N·L^{2β}) can be measured directly.
  - **Info / compute:** medium. It is a structural move inside L[1/2]; the open quantity is the constant.

## 3. The deterministic N^{1/5} line: Hittmeir 2018 → Harvey 2021 → Harvey–Hittmeir 2022 → Gao et al. 2025

- **Sources:**
  - M. Hittmeir, arXiv:1608.08766 (DOI 10.1090/mcom/3313);
  - D. Harvey, arXiv:2010.05450 (Math. Comp. 90 (2021) 2937–2950);
  - D. Harvey, M. Hittmeir, arXiv:2105.11105 (Math. Comp. 91 (2022) 1367–1379; search snippet only);
  - Y. Gao, Y. Feng, H. Hu, Y. Pan, arXiv:2512.19076 (2025).
- **The claims** (proven, deterministic):
  - Hittmeir: Õ(N^{1/4} exp(−C log N / log log N));
  - Harvey: N^{1/5+o(1)};
  - Harvey–Hittmeir: O(N^{1/5} log^{16/5} N / (log log N)^{3/5}) bit operations;
  - Gao et al.: O(N^{1/5} log^{13/5} N / (log log N)^{3/5}) for balanced semiprimes (Coppersmith with a rank-3 lattice).
- **Benchmarking: none found.** No implementation is mentioned in the abstracts. Per-paper code was not searched.
- **Implementing it here:** heavy. An element of large order mod N, baby-step giant-step over a Lehman / Hittmeir sieve, fast multipoint evaluation. The Gao variant needs a rank-3 LLL. The meter would need polynomial-arithmetic op classes.
- **A fair test:**
  - A rough model at 64 bits: N^{1/5}·(ln N)^{16/5} ≈ 10⁹, against rho's ~6.6×10⁴ multiplies (hand arithmetic; check in Wolfram).
  - **The prediction:** it loses to rho, SQUFOF and SIQS by orders of magnitude at 40–100 bits.
  - **The testable content is the growth exponent:** a log-log slope of ops against N of about 0.2 plus a polylog drift.
  - **Info / compute:** low, except as an exponent check (Phase 3's growth harness).

## 4. Hittmeir: factorisation as subset-sum (2022 / 2023)

- **Source:** M. Hittmeir, "Integer factorization as subset-sum problem", arXiv:2205.10074 (2022; DOI 10.1016/j.jnt.2023.02.010).
- **The claim:**
  - a polynomial-time reduction to a multiple-choice subset-sum instance;
  - it refines Fermat's runtime "by a large subexponential factor" for N with divisors of small difference;
  - a deterministic rigorous procedure, and a heuristically faster one.
  - The exact factor is UNVERIFIED (the full text was not read).
- **Benchmarking: none found.**
- **Implementing it here:** moderate (a sieve over residues plus a subset-sum / meet-in-the-middle stage). It is special-purpose: |p − q| small.
- **A fair test:**
  - Semiprimes with |p − q| ≤ N^{1/4+δ} for several δ, against Fermat, Lehman, Hart's one-line factoring and rho.
  - The prediction for random balanced numbers: no better than Fermat-class, so do not test there.
  - **Info / compute:** low to medium; a niche.

## 5. Mulder: class-group square-free decomposition, n = a²b (2023)

- **Source:** E. Mulder, "Fast square-free decomposition of integers using class groups", arXiv:2308.06130 (2023, 43 pp.).
- **The claim:**
  - heuristic Õ(L_b[1/2,1] ln n + L_b[1/2,1/2] ln(n)²);
  - "If a, b are both primes of roughly the same cryptographic size, then our method is currently the fastest known method to factor n";
  - L_n[1/2, √(1/3)] for n = p²q with p ≈ q.
  - It is a corrected Schnorr–Lenstra (its §7); its assumptions are "still just conjectures".
- **Benchmarking:** the author only. A Magma implementation against Magma's ECM on n = p²q (Table 1, 50–100 numbers each):
  - at q ≈ 10¹⁵: 0.11 s against 0.07 s;
  - at q ≈ 10³⁵: 136 s against 1,549 s.
  - The method wins for q ≥ ~10²⁰.
- **Implementing it here:** imaginary quadratic class-group arithmetic (composition, reduction, NUCOMP), exponentiation by a smooth exponent, a stage 2, a multiplier loop. Moderate, about 2–3 weeks.
- **A fair test:** only meaningful on n = p²q. At 40–100 bits, q is about 13–33 bits, far below the author's crossover (q ≈ 66 bits). So it is predicted to lose to ECM and rho throughout. **Info / compute:** low unless p²q targets are added.

## 6. The Schnorr–Lenstra class-group method (1984) and the Lenstra–Pomerance rigorous bound (1992)

- **Sources** (the AMS pages returned 403; search-indexed abstracts plus Mulder §3.2):
  - C. P. Schnorr, H. W. Lenstra Jr., Math. Comp. 43 (1984) 289–311;
  - H. W. Lenstra Jr., C. Pomerance, J. AMS 5 (1992) 483–516.
- **The claims:**
  - **Schnorr–Lenstra:** factors n when h(−n) (with multipliers) is smooth; heuristic L_n[1/2, 1] under three assumptions. Assumption (c) fails for n with a large prime-square divisor (Lenstra–Pomerance, per Mulder).
  - **Lenstra–Pomerance:** a rigorous L_n[1/2, 1+o(1)].
- **Benchmarking:** no public comparison against SIQS or ECM found. The rigorous variant reads as a theory result (UNVERIFIED).
- **Implementing it here:** the class-group machinery of item 5. For balanced N, the class group's size is ~√N, as ECM's group order is ~p.
- **A fair test:**
  - Schnorr–Lenstra against ECM, with the same stage-1 bound schedule, on balanced semiprimes at 40–100 bits. Compare group ops × cost per op (form composition against curve addition).
  - **The prediction:** an equal exponent. The ratio is set by the cost per op and by smoothness (Cohen–Lenstra: h slightly more often smooth).
  - **Info / compute:** medium. A cross-domain structural move with a direct ECM control.

## 7. Kleinjung: "Quadratic sieving" (2016)

- **Source:** T. Kleinjung, Math. Comp. 85 (2016) 1861–1873 (the AMS page returned 403; snippet level).
  - An independent study: Q. Luo, "On the Performance of Kleinjung's Quadratic Sieving Method", MSc thesis, Univ. Calgary, 2020 (abstract opened).
- **The claim:** a variant of the initialisation step of quadratic sieving, framed for class-group computation. A constant-factor claim; details UNVERIFIED.
- **Benchmarking:** thin.
  - Luo reports it "performs better than the SIQS method", most when many primes build the polynomial set, with the advantage shrinking as the sieve interval grows.
  - That is in the class-group setting. No factoring benchmark at 40–100 bits was found.
- **Implementing it here:** a change to SIQS polynomial generation and root initialisation. Small to moderate, from the paper only.
- **A fair test:**
  - In-house SIQS against SIQS with Kleinjung's initialisation, at 72 / 84 / 96 bits, with Run 8-style control arms (it is close to a parameter change).
  - The metric: initialisation ops and wall per polynomial, and total.
  - **The prediction (from Luo):** a small gain at our sizes (few A-primes).
  - **Info / compute:** medium-high (cheap and on the hot path).

## 8. McKee: "Speeding Fermat's factoring method" (1999), a contrast

- **Source:** J. McKee, Math. Comp. 68 (1999) 1729–1737 (snippet level).
- **The claim:** heuristic O(n^{1/4+ε}).
- **Benchmarking exists:** the TIFA library and J. Milan's comparisons (not opened; UNVERIFIED by this sweep).
- **Excluded as untested.** Listed as the natural N^{1/4} control for item 1's Arm B.

## 9. Schnorr: "Fast factoring integers by SVP algorithms" (2021), a contrast: tested and refuted

- **Source:** C. P. Schnorr, IACR ePrint 2021/933.
- **The claim:** 2^400 and 2^800 factored "much faster than the quadratic and the number field sieve"; "This destroys the RSA cryptosystem."
- **Testing:**
  - Ducas's implementation did not reproduce the claim (secondary sources; not opened).
  - Khattar & Yosri, arXiv:2307.09651: a QAOA-Schnorr variant factors "only up to 70 bits".
  - Aboumrad, Widdows, Kaushik, arXiv:2308.07804: lattice factoring "does not scale successfully to larger numbers".
- **Excluded as untested.** It is the model case of how a lattice claim is checked: relation yield per reduction against size.

## Excluded after inspection

- **Friedlander,** arXiv:2504.21168 (2025): claims ~√n, no better than trial division. A third-party review (not opened) reports failure on n = 21.
- **Bansimba & Babindamana,** arXiv:2507.07055 (2025): reformulations only, no complexity claim.
- **"Rational Base Descent",** arXiv:2605.08846 (2026): special-form semiprimes only. Not opened; UNVERIFIED.
- **Quantum variants:** out of scope (classical only).
- **Lehman / Hart's one-line factoring:** widely benchmarked; no untested claim found.

## Suggested order (information per compute; a judgement, the user's decision)

1. **Murru–Salvatori Arm A** (an oracle regulator: measures the O((ln N)²) phase and Table 3's classes). Cheap.
2. **Kleinjung's initialisation in SIQS:** cheap, on the hot path, with control arms.
3. **SQUFOF2 against SIQS** with a shared sieve: tests the "same exponent" claim.
4. **Schnorr–Lenstra against ECM:** a cross-domain move with a direct control.
5. **Murru–Salvatori Arm B** with a baby-step giant-step regulator, against SQUFOF and McKee.
6. **Low at 40–100 bits:** Hittmeir's subset-sum (close factors), Mulder (p²q only), and the N^{1/5} line (an exponent check only).

## Sources opened

- arxiv.org/abs/2409.03486 and its v2 PDF (full text: §3, §5, §6, references); arxiv.org/abs/1905.10704; researchseminars.org/talk/OWNS/143/
- homes.cerias.purdue.edu/~ssw/squfof2.pdf (full text: §8–§9)
- eprint.iacr.org/2021/933; arxiv.org/abs/2307.09651; arxiv.org/abs/2308.07804
- arxiv.org/abs/2010.05450; arxiv.org/abs/1608.08766; arxiv.org/abs/2512.19076; arxiv.org/abs/2205.10074
- arxiv.org/abs/2308.06130 and its PDF (§3.2, §5); arxiv.org/abs/2504.21168; arxiv.org/abs/2507.07055
- the Luo thesis abstract (ucalgary.scholaris.ca)

**Blocked (403):** the AMS pages for Schnorr–Lenstra 1984, Lenstra–Pomerance 1992 and Kleinjung 2016.

**Search snippets only:** Harvey–Hittmeir 2105.11105; McKee 1999 and the TIFA / Milan pages; Ducas's implementation; 2605.08846; the third-party Friedlander review.
