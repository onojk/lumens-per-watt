# MOVES

A move is a transformation that recurs across algorithms: batching, pruning, changing the group, and so on. Each row is a candidate part for our deck. Statuses are measured, never guessed: a row says "pays" or "ruled out" only with the conditions it was measured under and the evidence. The plan for working through this table is in PLAN.md, ["Learning from all algorithms"](PLAN.md#learning-from-all-algorithms).

| Move | Where it comes from | Already in factoring | Untried candidate in our deck | Status | Conditions | Evidence |
|---|---|---|---|---|---|---|
| Batch the expensive step | Product/remainder trees (Bernstein) | Rho's one-gcd-per-batch | Batch smoothness test for qs and CFRAC residues | untested | — | — |
| Early abort | Branch-and-bound pruning | Pomerance's early abort for CFRAC | CFRAC early-abort gene; qs candidate abort | untested | — | charging written in NOTES.md (CFRAC entry, planned gene a, b) |
| Change the group | Algebra | p-1 to ECM | p+1 card (Lucas sequences); other curve families | untested | — | — |
| Meet in the middle | Shanks' BSGS; cryptanalysis | ECM stage 2 | p-1 stage 2 with the w = 210 machinery | untested | — | — |
| Parallel collision search | Distinguished points (van Oorschot-Wiener) | Parallel rho in cryptanalysis | Side-by-side numberlines sharing one rho meter | untested | — | — |
| Relax, then repair | LP relaxation | Large-prime partial relations | Double large primes with union-find cycle counting | untested | — | — |
| Approximate, then verify | Floating point; sketching | Sieving with rounded logs (tc gene) | Coarser log rounding, priced honestly | untested | — | — |
| Precompute and cache | Memoization | Knuth-Schroeppel multiplier | Cached factor-base tables shared across races | untested | — | — |
| Iterative sparse solver | Lanczos / Wiedemann | Block Lanczos in big sieves | Ledger LA, only if per-phase counts say it matters | untested | — | — |
| Lattice reduction | LLL | Coppersmith; NFS poly selection | Small: polynomial choice in SIQS | untested | — | — |
| Divide and conquer | Mergesort; recursion | Recursive cofactor splitting | Route cofactors back into the race as new numbers | untested | — | — |
| Portfolio and selection | SAT solvers (SATzilla) | ECM-before-sieve pipelines | Learned selector on N's size; Stage 9 race | IN PROGRESS | Stage 9: race(ECM, qs + lc 1.4) and race(rho, qs + lc 1.4) on the Stage 8 populations, slices 2^8 / 2^10 / 2^14 | NOTES.md, Stage 9 (draft, under review) |
| Adaptive scheduling | Multi-armed bandits | not seen | Bandit-chosen race slices instead of fixed 2^8/2^10/2^14 | untested | — | — |
| Restart on bad luck | SAT solver restarts | New curves in ECM | Rho restart with a new polynomial after a budget | untested | — | — |
| Fast multiplication | Karatsuba; FFT | Inside bignum libraries | METER QUESTION, not a gene (a multiply costs 1 op) | untested | — | — |
| Memory layout / buckets | Bucket sort; cache blocking | Lattice-siever bucket sieving | METER QUESTION, not a gene (meter counts ops, not memory) | untested | — | — |
| p-1 front | Pipelines: a cheap specialist before the general method | p-1 / ECM run before sieving | measured (leading p-1 before qs, evolved in Run 6) | PAYS | 1.05-1.24x in total ops at 72-84 bits (Run 6 ablation, L53-0972; 1.14-1.17x for L54-0938), official pricing. | README.md, Run 6; `evolve/run6_ablation.py` |
| CFRAC standalone | Continued fractions; Morrison-Brillhart | CFRAC, the method before QS | measured (CFRAC card into the shared ledger) | RULED OUT | 3.7x / 5.2x tuned qs's ops at 72 / 84 bits (predicted ~6x / ~10x), official op pricing. | NOTES.md, CFRAC result; `evolve/cfrac_compare.json` |

Rules:
- A loss is recorded, never deleted.
- A ruled-out move is retried only if its conditions change, and the entry says which condition changed.
- Pricing is never a gene.
