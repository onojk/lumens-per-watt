# MOVES

A move is a transformation that recurs across algorithms: batching, pruning, changing the group, and so on. Each row is a candidate part for our deck. Statuses are measured, never guessed: a row says "pays" or "ruled out" only with the conditions it was measured under and the evidence. The plan for working through this table is in PLAN.md, ["Learning from all algorithms"](PLAN.md#learning-from-all-algorithms).

| Move | Where it comes from | Already in factoring | Untried candidate in our deck | Status | Conditions | Evidence |
|---|---|---|---|---|---|---|
| Batch the expensive step | Product/remainder trees (Bernstein) | Rho's one-gcd-per-batch | Batch smoothness test for qs and CFRAC residues. METER QUESTION: product/remainder trees multiply numbers far larger than N; a pricing rule for oversized multiplies (rounded UP to N-sized multiplies) must be in NOTES before this move is built. Prerequisite MET: rule written in NOTES, Oct 24 ("Phase 1 pricing rule: oversized multiplies"). | untested (outside evidence: batching 128 residues lets the CFRAC factor base roughly double; CFRAC is still not viable against SIQS) | — | [Milan] |
| Early abort | Branch-and-bound pruning | Pomerance's early abort for CFRAC | CFRAC early-abort gene; qs candidate abort. The outside values below are the gene's starting range. | untested (outside evidence: Pomerance's c = 1/7 impractical; Milan used c = 4/7) | — | charging written in NOTES.md (CFRAC entry, planned gene a, b); [Milan] |
| Change the group | Algebra | p-1 to ECM | p+1 card (Lucas sequences); other curve families | untested | — | — |
| Meet in the middle | Shanks' BSGS; cryptanalysis | ECM stage 2 | p-1 stage 2 with the w = 210 machinery | untested | — | — |
| Parallel collision search | Distinguished points (van Oorschot-Wiener) | Parallel rho in cryptanalysis | Side-by-side numberlines sharing one rho meter | untested | — | — |
| Relax, then repair | LP relaxation | Large-prime partial relations | Double large primes with union-find cycle counting | untested | — | — |
| Approximate, then verify | Floating point; sketching | Sieving with rounded logs (tc gene) | Coarser log rounding, priced honestly | untested | — | — |
| Precompute and cache | Memoization | Knuth-Schroeppel multiplier | Cached factor-base tables shared across races | untested | — | — |
| Iterative sparse solver | Lanczos / Wiedemann | Block Lanczos in big sieves | Ledger LA, only if per-phase counts say it matters | untested | — | — |
| Lattice reduction | LLL | Coppersmith; NFS poly selection | Small: polynomial choice in SIQS | untested | — | — |
| Divide and conquer | Mergesort; recursion | Recursive cofactor splitting | Route cofactors back into the race as new numbers | untested | — | — |
| Sequential portfolio (cheap lamp, then the sieve) | SAT solvers (SATzilla); pipelines | ECM-before-sieve pipelines | measured: see the p-1 front row | PAYS | 1.05-1.24x, official pricing (Run 6 ablation): the p-1 front row below | the p-1 front row |
| Fixed-slice race (interleaved) | SAT solver portfolios | parallel portfolios | Stage 9 race (the learned selector has its own row) | RULED OUT | Fixed-slice race of ECM or rho against qs (tuned + lc 1.4, or N51-0917's qs) on the Stage 8 populations (balanced 54-84; unbalanced 72-84 x 24-32), slices 2^8 / 2^10 / 2^14 equal or pi-scaled, cap 2^28, all three pricings: mean below both sides in 0/810 cases, worst case below both in 0/135, robust bar failed in 253/270; cause: qs's per-slice overshoot. Not tested (would reopen): finer qs charge chunks, adaptive or budget-split slices, two non-qs sides, a mixed population. A mixed population is the case where interleaving is meant to pay: every tested cell was a single-kind population. | NOTES.md, Stage 9 result; `evolve/race_compare.json`, `evolve/race_report.out` |
| Adaptive scheduling | Multi-armed bandits | not seen | Bandit-chosen race slices instead of fixed 2^8/2^10/2^14 | untested | — | — |
| Restart on bad luck | SAT solver restarts | New curves in ECM | Rho restart with a new polynomial after a budget | untested | — | — |
| Fast multiplication | Karatsuba; FFT | Inside bignum libraries | METER QUESTION, not a gene (a multiply costs 1 op) | untested | — | — |
| Memory layout / buckets | Bucket sort; cache blocking | Lattice-siever bucket sieving | METER QUESTION, not a gene (meter counts ops, not memory) | untested | — | — |
| p-1 front | Pollard p-1 (1974) | cheap first stage before a sieve (common in practice) | measured (leading p-1 before qs, evolved in Run 6) | PAYS | 1.05-1.24x in total ops at 72-84 bits (Run 6 ablation, L53-0972; 1.14-1.17x for L54-0938), official pricing. | README.md, Run 6; `evolve/run6_ablation.py` |
| CFRAC standalone | Morrison-Brillhart (1975), continued fractions | the first L[1/2] method | measured (CFRAC card into the shared ledger) | RULED OUT | 3.7x / 5.2x tuned qs's ops at 72 / 84 bits (predicted ~6x / ~10x), official op pricing. | NOTES.md, CFRAC result; `evolve/cfrac_compare.json` |
| Quadratic-form cycle | Shanks | SQUFOF | A SQUFOF mode of the CFRAC card: the same sqrt(kN) recurrence and Q_i stream; stop at a square Q at an even index, then walk the reverse cycle. Class N^1/4, so its rival is rho/Hart, not qs. Genes: the multiplier list (none first, then Gower-Wagstaff's 15 square-free multipliers raced through the Stage 9 race combinator) and the fast-return threshold (Milan: 4096 forms). Prediction: beats rho/Hart at 40-52 bits; loses to qs above (class gap). | untested (outside evidence: competitive with ECM up to ~60 bits; fast return negligible below 60 bits) | — | [Milan] |
| Higher-torsion curves | EECM-MPFQ (Bernstein, Birkner, Lange, Peters) | ECM with Suyama (order divisible by 12), in our deck | Family gene suyama12 \| z2z8, both in Montgomery form, the same x-only ladder at 11 ops/bit. Prediction: 1.05-1.15x, larger at the top sizes. | untested | — | — |
| Infrastructure + Gauss composition | Murru-Salvatori, arXiv 2409.03486 (v2, Jan 2025) | claimed L[1/2, 3/sqrt(8) ~ 1.06]; theoretical only, no benchmarks | Cost model only. If the claim holds, it would beat CFRAC and lose to qs. | untested | cost model only | — |
| Learned selector across numbers | SAT solvers (SATzilla) | — | Stage 9.5 (PLAN). Note: a per-N bandit has no reward signal for rho/ECM (success only; curves are memoryless); only qs reports progress (relations / needed). | untested | — | — |
| Class-group square-free decomposition | Mulder, ANTS XVI, arXiv 2308.06130 | — | — | RULED OUT (argument, not measured) | Finds a^2 b; gives nothing for a squarefree pq, which is all we factor. | the paper's scope |
| SAT + lattice | SAT solving; lattice reduction | factoring with partial key exposure | — | RULED OUT (argument, not measured) | Needs leaked bits of a factor; we have none. | — |
| Coppersmith / LLL | Coppersmith; LLL | Coppersmith's method | — | RULED OUT (argument, not measured) | Needs leaked bits of a factor; we have none. The polynomial-choice use stays in the Lattice reduction row. | — |
| Number field sieve | NFS | the L[1/3] method | — | RULED OUT (argument, not measured) | Crossover with qs around 100+ digits, far above our sizes (up to 96 bits, about 29 digits). | — |
| Hyperelliptic ECM (HECM) | Hyperelliptic curves | HECM | — | RULED OUT (argument, not measured) | Not competitive with elliptic curves. | — |
| Pell conics | Conics x^2 - D y^2 = 1 | — | — | RULED OUT (argument, not measured) | The same move as p+1 (Change the group row). | — |
| Quantum / Ising | Shor; annealing | — | — | RULED OUT (argument, not measured) | Not runnable here. | — |
| Sieve, then batch (SIQS) | Milan's SIQS | sieving with a batch test behind it | A looser sieve threshold, with the extra candidates confirmed by a batch test instead of trial division. Genes: tc x batch, tuned jointly. Same METER QUESTION as the Batch row. | untested | — | [Milan] |
| Fermat (McKee greedy variant) | McKee | Fermat-type square search | — | untested (outside evidence: loses to SQUFOF at 45-60 bits) | — | [Milan] |
| Quality-diversity archive (MAP-Elites) | Mouret & Clune 2015 | — | One elite genome per (total bits x smaller-factor bits) cell (PLAN, "Search structure after Run 8") | untested | — | — |
| Co-evolved environments (POET) | Wang et al. 2019 | — | Generated training populations paired with champions, with transfers; verdicts stay on sealed populations | untested | — | — |
| Speciation / innovation protection (NEAT) | Stanley & Miikkulainen 2002 | — | A protected tuning budget for a new card structure before it competes overall | untested | — | — |
| Cycle segments (parallel SQUFOF) | Parallel SQUFOF | segments of one SQUFOF cycle, reached by powers of a form, one lane each | Split one cycle into segments, one lane each. Saves span, not work. METER QUESTION: span is reported next to total ops for parallel studies, never as fitness unless decided. | untested | — | [McMath et al.] |

Rules:
- A loss is recorded, never deleted.
- A ruled-out move is retried only if its conditions change, and the entry says which condition changed.
- Pricing is never a gene.
- "untested (outside evidence: ...)" means others have measured it, on wall clock and on their own implementations. It informs priors and gene ranges and is never counted as our verdict: the row stays untested until our meter has scored it.
- "RULED OUT (argument, not measured)" rows rest on the stated reason, not on a run. If the reason stops holding (new sizes, new information about the numbers), the row goes back to untested.

Sources:
- [Milan] J. Milan, "Factoring small integers: an experimental comparison", https://www.lix.polytechnique.fr/~milanj/files/factoring_small_int.pdf; the TIFA library, https://www.lix.polytechnique.fr/~milanj/tifa/overview.xhtml
- [McMath et al.] S. McMath, F. Crabbe, D. Joyner, "Continued fractions and parallel SQUFOF", arXiv math/0601263, https://arxiv.org/pdf/math/0601263
