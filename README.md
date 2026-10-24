# lumens-per-watt

Growing factoring algorithms by evolution, and measuring them by **lumens per watt**.

## In plain English

**The idea.** Picture a factoring algorithm as a light moving along the number line, ruling out spots where the secret factor could be hiding. That gives a way to grade any algorithm: how much of the line it darkens for each unit of work. We call that **lumens per watt**. More light per watt means a better bulb.

**What this repo does.** It breeds factoring algorithms the way a gardener breeds plants. It starts with a box of known parts (trial division, square searches, rho, and so on), snaps them together in random combinations, tests each one on real numbers, keeps the best, mutates them, and repeats. Every algorithm gets a name and a family tree, so you can trace how a winner came to be.

**What we've learned so far.**

- **The scoring has to be cheat-proof.** Early on, algorithms "won" by memorizing the test numbers or by being slow on small numbers so their growth looked flatter. The scoring now uses fresh numbers every round, and every winner is rechecked on numbers it has never seen.
- **Evolution rediscovers real tricks.** Starting from a plain search, it worked out on its own the multiplier trick that Hart published.
- **How you keep score decides who wins.** Judged by the worst case, rho (the "lucky" method) won. Judged by total work across many numbers, a luck-free square search won. We chose the running total as the scoreboard and wrote that down in `NOTES.md`.
- **"Luck by design" only pays when guessing is cheaper than trying.** Making each test luckier cost more than it saved, so evolution mostly ignored those parts.
- **Size changes everything.** To test bigger numbers, the core was rebuilt in Rust and proven to give identical answers to the Python version, case for case. On bigger numbers the winner flipped: the square searches that led at small sizes lose clearly to rho from about 60 bits up. At small sizes fixed overhead decides the race; at large sizes the growth rate does. Every growth rate we measured matched what the mathematics predicts.

**The honest bottom line.** Evolution has become good at fine-tuning known algorithms. Scored on big numbers, it found a combination (p − 1 before rho) that beats plain rho by 1.3–1.6×, but nothing it has grown beats the known speed limits of its parts. That's a clean, reproducible measurement of where those limits sit, and the tools are now strong enough to keep pushing.

The sections below have the details: the parts, the scoring rules, every run's results, and how to reproduce them.

## The idea

Every algorithm lights up the number line as it runs: some stations are queued, some staged, some being crunched, some kept as afterglow. Two quantities fall out of that picture:

- **Watts**: compute spent, counted in operations (one modular multiply, square test, or gcd = 1 op).
- **Lumens**: candidate stations for *p* ruled out. For a balanced semiprime N = pq, finishing means all ~√N candidates are dark.

**Lumens per watt** is stations ruled out per operation, the efficacy of the bulb. Running more hardware in parallel raises the watts, not the efficacy. Only a better bulb moves the wall.

If an algorithm costs N^e operations, its efficacy is N^(1/2 − e):

| Method | Work | Lumens per watt |
|---|---|---|
| Trial division | N^(1/2) | 1 |
| Lehman | N^(1/3) | N^(1/6) |
| Pollard–Strassen | N^(1/4) | N^(1/4) |
| Harvey | N^(1/5) | N^(3/10) |

## The lamp parts

- `td`: trial division up to N^a
- `sq`: square search on kN, which covers Fermat (k = 1, wide window), Lehman (k up to N^(1/3), windows ~N^(1/6)/√k), and Hart (window 1, smooth multiplier)
- `ps`: **block flash** (Pollard–Strassen). One polynomial f(x) = (x+1)…(x+B) is evaluated at every block start with a product tree and remainder tree, so each block of B stations is ruled out in one gcd. Polynomial products are charged by the FFT cost model, 3·(n/2)·log₂n + n ring multiplies; the Python computes the same products exactly by Kronecker substitution. See `evolve/blockflash.py`.
- `rho`: Brent's rho with batched gcds
- `pm1`: Pollard p − 1

A genome is a chain of up to four parts with tunable settings. Evolution tunes settings, inserts, deletes, swaps, replaces, and splices chains.

Two decks evolve separately:

- **no-luck**: `td`, `sq`, `ps`
- **luck**: adds `rho` and `pm1`, whose speed rests on behaving as if random

## The meter (v2)

- **Fresh numbers every generation.** Each generation trains on new balanced semiprimes at 32, 38, and 44 bits (8 per size), so nothing can memorize them.
- **Score = effective exponent at the sizes actually run:** log₂(worst ops) / bits, averaged over the top two sizes. Being slow on small N can't lower it. The fitted slope is still reported, as the trend.
- **Worst luck.** Worst case over every test number. Missing any number counts as not finished.
- **Validation gate.** Each generation's training winner is re-run on a fixed held-out set of 48-bit numbers. It becomes the champion only if it beats the current champion there.
- **Lineage catalog.** Every genome gets a name (`N11-0140` = no-luck run 11, individual 140), its parents, the mutation that made it, and its birth generation. Every generation writes every individual's scores to `lineage.jsonl`.

## Running

```
cd evolve
python3 evolve.py 25 20 8      # generations, population, worker processes
python3 validate.py            # champions vs baselines on fresh 36–54 bit numbers
python3 ancestry.py            # family line of each run's champion
python3 ancestry.py N11-0076   # family line of any named genome
```

Outputs: `evolve.log`, `results.json`, `lineage.jsonl`, `validation.json`. Runs are seeded, so the same commands reproduce the same numbers on any machine.

## Relation economy: CFRAC (Oct 23, 2026)

qs is now a relation *source* feeding a shared *ledger* (`evolve/ledger.py`: factor base, dedupe, linear algebra, square root), and is op for op unchanged (`evolve/relation_economy_identity.py`, both cores). The ledger has an opt-in charged relation check (`evolve/ledger_accept.py`). A second source, continued fractions (`evolve/cfrac.py`, cost model in `NOTES.md`), feeds the same ledger with one multiplier k and one factor base. It is accepted at 40–60 bits (`evolve/cfrac_accept.py`), with lampcore parity.

The comparison (`evolve/cfrac_compare.py`) runs three setups on the Run 6 ACCEPT numbers, cap 2^28; there were no misses:
- CFRAC alone, with tuned qs's kc 32 and bc 1.1;
- tuned qs;
- qs + CFRAC into one ledger: CFRAC fills a fixed share cs of the needed relations first, then qs fills the rest.

log₂(mean ops) [95% interval] / worst:

| Algorithm | 72 bits | 78 bits | 84 bits | Growth per bit, 72→84 | Ops vs tuned qs (72 / 84 bits) |
|---|---|---|---|---|---|
| **tuned qs** | **17.43** [17.36, 17.51] / 18.30 | **18.28** [18.21, 18.36] / 19.10 | **19.22** [19.16, 19.27] / 19.90 | 0.149 | 1 |
| qs + CFRAC, cs 0.1 | 17.80 [17.73, 17.88] / 18.67 | 18.74 [18.66, 18.82] / 19.67 | 19.74 [19.68, 19.79] / 20.36 | 0.161 | 1.30× / 1.43× |
| qs + CFRAC, cs 0.25 | 18.19 [18.12, 18.27] / 18.90 | 19.21 [19.12, 19.29] / 20.18 | 20.25 [20.19, 20.31] / 21.02 | 0.171 | 1.70× / 2.05× |
| qs + CFRAC, cs 0.5 | 18.69 [18.62, 18.76] / 19.29 | 19.74 [19.66, 19.82] / 20.63 | 20.87 [20.80, 20.94] / 21.82 | 0.182 | 2.39× / 3.14× |
| CFRAC alone | 19.32 [19.26, 19.38] / 19.82 | 20.42 [20.34, 20.50] / 21.34 | 21.58 [21.51, 21.65] / 22.59 | 0.188 | 3.7× / 5.2× |

What it shows:

- **CFRAC loses, as predicted.** It needs 3.7× tuned qs's ops at 72 bits and 5.2× at 84. The prediction stated in advance was ~6× and ~10×, so this is inside the stated uncertainty, on the low side. Its growth is steeper, so the gap widens with size.
- **Mixing doesn't help.** Every share of CFRAC makes qs worse, and more CFRAC is worse still: a CFRAC relation costs more than the sieving it saves.
- **Where CFRAC's ops go.** About 95% go to trial-dividing every residue (there is no sieve). That is the target of the planned early-abort gene.

Data: `evolve/cfrac_compare.json` (and `.out`), `evolve/cfrac_accept.json`, `evolve/ledger_accept.json`.

## Growth to 96 bits (Oct 23, 2026)

Does N51-0917's 0.136 log₂-ops per bit hold past 84 bits? 80 fresh numbers each at 90 and 96 bits (`semiprimes_pq(bits, 80, 1400000 + bits)`, cap 2^30), joined to the committed ACCEPT rows at 72/78/84 (cap 2^28). Same bootstrap; no misses. log₂(mean ops):

| Algorithm | 72 | 78 | 84 | 90 | 96 | Growth 72→84 | 84→96 | 72→96 |
|---|---|---|---|---|---|---|---|---|
| **tuned qs + lc 1.4** | **17.24** | **18.14** | **19.08** | **20.03** [20.00, 20.07] | **20.83** [20.80, 20.86] | 0.153 | 0.146 | 0.151 |
| tuned qs | 17.43 | 18.28 | 19.22 | 20.17 [20.12, 20.22] | 20.94 [20.89, 20.99] | 0.149 | 0.143 | 0.148 |
| N51-0917 | 17.81 | 18.60 | 19.45 | 20.43 [20.37, 20.49] | 21.25 [21.19, 21.31] | 0.136 | 0.150 | 0.145 |
| rho | 18.90 | 20.29 | 21.94 | 23.29 [23.11, 23.45] | 24.84 [24.67, 24.99] | 0.253 | 0.242 | 0.248 |

What it shows:

- **One exponent for every qs variant.** All three grow about 0.145–0.15 log₂-ops per bit over 72–96.
- **N51-0917's 0.136 at 72–84 was constants.** From 84 to 96 bits it grows 0.150, and it falls further behind tuned qs: 0.23 log₂ at 84 bits, 0.31 at 96. That fits its mc of 1.0, above the boundary sweep's optimum.
- **lc 1.4's lead persists to 96 bits:** a constant 0.1–0.2 log₂ below tuned qs.
- **Rho stays at 0.248 per bit.**
- **A seam:** 72–84 are the ACCEPT numbers and 90/96 are new seeds, so slopes across 84→90 mix two sets of numbers. Tuned qs's 0.143 dip from 84 to 96 is likely that seam, not a real change.

The run used a scratch script, not committed; the data are as above.

## Stage 7: large primes (Oct 23, 2026)

qs gains one gene, lc: a sieve candidate whose leftover cofactor is a prime below L = B^lc is kept as a partial relation, and two partials with the same large prime combine into one full relation (lc = 1.0 is today's qs, op for op). Cost model in `NOTES.md` ("Stage 7"), written before the code; acceptance in `evolve/stage7_accept.py` (40–60 bits: complete, exact per-phase accounting including the new lp phase, every relation and dependency verified, every lp charge caught by a one-op mutation); lampcore parity on 2,638 qs pairs. lc = 1.4 was fixed in advance on separate tuning seeds (`evolve/stage7_lc_sweep.py`).

Comparison (`evolve/stage7_compare.py`): tuned qs (kc 32, bc 1.1, mc 0.25, tc 1.38) against the same genes with lc 1.4, on the Run 6 ACCEPT numbers, cap 2^28, no misses, no retries.

log₂(mean ops) [95% interval] / worst [95% interval]:

| Algorithm | 72 bits | 78 bits | 84 bits | Growth per bit, 72→84 |
|---|---|---|---|---|
| **qs + lc 1.4** | **17.24** [17.18, 17.30] / 18.15 [17.61, 18.15] | **18.14** [18.09, 18.20] / **18.79** [18.59, 18.79] | **19.08** [19.03, 19.12] / **19.54** [19.43, 19.54] | 0.153 |
| tuned qs (lc 1.0) | 17.43 [17.36, 17.51] / 18.30 [18.02, 18.30] | 18.28 [18.21, 18.36] / 19.10 [18.89, 19.10] | 19.22 [19.16, 19.27] / 19.90 [19.57, 19.90] | 0.149 |

What it shows:

- **A constant gain of about 1.1×.** On the same numbers lc 1.4 needs 1.14×, 1.10× and 1.10× fewer ops at 72, 78 and 84 bits. The mean intervals separate at every size (at 78 bits by 0.01). The worst case is better at 78 and 84 bits; at 72 the intervals overlap.
- **Growth unchanged.** 0.153 log₂-ops per bit against 0.149: a better constant, not a better exponent.
- **Where the ops moved.** Sieving falls about 1.6× and polynomial setup 1.2–1.3× (fewer polynomials are needed); confirmation rises 1.9–2.1× (more candidates, each paying full trial division); the lp phase itself costs 2^12–2^13.5. About 0.14 combined relations per partial, and about 30% of the matrix rows are combined relations.
- **The comparison favours tuned qs.** Tuned qs's genes were picked by the boundary sweep on these same ACCEPT numbers, while lc 1.4 was picked on separate seeds, so tuned qs's numbers carry some selection bias in its favour.
- **Against the prediction.** NOTES expected little or no gain at 72–84 bits, because confirmation is overcharged; the gain is small but real.

Data: `evolve/stage7_compare.json` (and `.out`), `evolve/stage7_accept.json`, `evolve/stage7_lc_sweep.json`.

## Run 6: island model with qs in the deck (Oct 23, 2026)

Four islands of 16 genomes per run, top-2 ring migration every 5 generations, a 2-slot diversity reserve, 20 generations, seeds 51–54 (51–52 no-luck, 53–54 luck), qs in both decks. Training at 66, 72, and 78 bits (cap 2^26), gate at 84 bits (cap 2^28). Outputs in `evolve/run6/`; harness `evolve/evolve_run6.py`; plan in `PLAN.md`.

ACCEPT (`evolve/run6_accept.py`, written before the run): the four champions against qs-default, Run 5's L44-0272, and rho, through `lampcore` at cap 2^28, on Stage 2's 80 numbers at 72 and 78 bits plus 80 fresh 84-bit numbers (`semiprimes_pq(84, 80, 1300084)`). The reference rows reproduce `qs_stage2.json` exactly at 72 and 78 bits. No misses.

```
cd evolve && python3 run6_accept.py 8
```

log₂(mean ops) [95% interval] / worst [95% interval]:

| Algorithm | 72 bits | 78 bits | 84 bits | Growth per bit, 72→84 |
|---|---|---|---|---|
| **N51-0917** (no-luck-51: qs → 2 square searches) | **17.81** [17.74, 17.89] / 18.60 [18.48, 18.60] | **18.60** [18.52, 18.68] / 19.45 [19.20, 19.45] | **19.45** [19.38, 19.52] / **20.27** [19.93, 20.27] | **0.136** |
| N52-0833 (no-luck-52: qs → trial → qs) | 17.87 [17.79, 17.95] / 18.68 [18.44, 18.68] | 18.66 [18.57, 18.75] / 19.73 [19.33, 19.73] | 19.51 [19.44, 19.59] / 20.38 [19.99, 20.38] | 0.137 |
| L53-0972 (luck-53: p − 1 → qs → p − 1 → qs) | 17.65 [17.45, 17.83] / 18.80 [18.60, 18.80] | 18.63 [18.45, 18.78] / 19.68 [19.51, 19.68] | 19.57 [19.41, 19.71] / 20.62 [20.22, 20.62] | 0.160 |
| L54-0938 (luck-54: p − 1 → qs → trial) | 18.06 [17.90, 18.20] / 18.92 [18.76, 18.92] | 18.96 [18.81, 19.09] / 19.74 [19.57, 19.74] | 19.83 [19.67, 19.97] / 20.86 [20.33, 20.86] | 0.148 |
| qs default | 18.88 [18.81, 18.95] / 19.78 [19.30, 19.78] | 19.73 [19.66, 19.79] / 20.41 [20.20, 20.41] | 20.67 [20.61, 20.72] / 21.13 [21.02, 21.13] | 0.149 |
| Run 5 L44-0272 (p − 1, then rho) | 18.56 [18.28, 18.82] / 20.19 [20.16, 20.19] | 20.05 [19.76, 20.30] / 22.04 [21.23, 22.04] | 21.58 [21.32, 21.81] / 23.38 [23.05, 23.38] | 0.252 |
| Rho | 18.90 [18.73, 19.05] / 20.06 [20.02, 20.06] | 20.29 [20.09, 20.47] / 21.56 [21.27, 21.56] | 21.94 [21.76, 22.10] / 23.15 [23.12, 23.15] | 0.253 |

What it shows:

- **Evolution kept qs on both decks.** All four champions contain qs, each with a tuned first qs stage: kc 10–32, bc 1.06–1.89, mc 1.0–1.83, tc 1.07–1.68 (qs-default is kc 16, bc 1.5, mc 4.0, tc 2.0).
- **The best bulb so far.** At 84 bits the best no-luck champion, N51-0917, needs 2.3× fewer operations on average than qs-default, 4.4× fewer than L44-0272 and 5.6× fewer than rho; on the worst case, 1.8×, 8.6× and 7.4×. Its intervals separate from all three on both the mean and the worst case.
- **Luck champions: no better overall.** L53-0972's intervals overlap N51-0917's at every size, and L54-0938, whose chain is p − 1 → qs, is the weakest of the four. Within the luck champions the leading p − 1 pays (removing it costs 1.05–1.24×; it wins 12–23 of 80); they lose to N51-0917 on weaker qs genes. Stages after the first qs never run (ablation, 240/240), so the no-luck champions are tuned qs.
- **Mostly tuned constants.** N51-0917 grows 0.136 log₂-ops per bit from 72 to 84 bits (N52-0833 0.137), against qs-default's 0.149 and 0.25 for rho and L44-0272. Most of its lead over qs-default is already there at 72 bits (1.07 of the 1.22 log₂ at 84), so it is mostly a better constant, with a small exponent gain on top.
- **Still under the overcharging rule.** Every small-number step in qs costs a full op, so these totals overstate qs's real work.
- **The mutation range binds.** Three champions sit at or near mc = 1.0, the bottom of mc's mutation range (1.0–12.0), so the optimum may lie below it.

Data: `evolve/run6/accept.json`, `results.json`, `lineage.jsonl`, `evolve.log` (`nohup.out` is the same log captured by nohup).

Two follow-up measurements on the ACCEPT numbers (cap 2^28, same bootstrap; not scored runs):

- **Ablation** (`evolve/run6_ablation.py`): each champion in full, with every non-qs stage removed, and with only its first qs stage. On every one of its 240 numbers, each champion was finished by its first qs or a stage before it; removing the later stages changes nothing, op for op. Removing the leading p − 1 from the luck champions costs 1.05–1.24× (L53-0972) and 1.14–1.17× (L54-0938) in total ops at 72–84 bits.
- **Boundary sweep** (`evolve/qs_boundary_sweep.py`): qs alone with N51-0917's kc 32 and tc 1.38, mc ∈ {0.25, 0.5, 0.75, 1, 1.5, 2} × bc ∈ {0.8, 1.0, 1.1, 1.3, 1.5} at 78 and 84 bits. Cost falls as mc drops in every column but one (78 bits, bc 0.8: mc 0.25 and 0.5 within noise); the best cell is the grid's edge, mc 0.25, bc 1.1: 2^19.22 [19.16, 19.27] at 84 bits against 2^19.44 [19.38, 19.51] at mc 1.0, bc 1.1 (about 1.17× fewer ops, intervals separated). The optimum is below Run 6's mutation floor of mc = 1.0. Every cell was computed by `lamps.py`, because at mc 0.25 lampcore disagreed on all 80 numbers per cell: a sieved prime wider than the interval made `qs.rs` underflow (fixed in the next commit, with parity pairs).

## Run 5: evolution scored at scale (Oct 23, 2026)

Fitness measured through `lampcore` at 52, 58, and 64 bits (6 fresh numbers each per generation), gate at 68 bits, fine deck, seeds 41–44, cap 2^23. Outputs in `evolve/run5/`; script `evolve/evolve_scale.py`.

Champions rechecked on 80 fresh numbers per size (mean / worst ops, log₂):

| Algorithm | 64 bits | 72 bits | 78 bits |
|---|---|---|---|
| Rho | 16.80 / 18.52 | 18.99 / 20.21 | 20.41 / 21.57 |
| **Run 5 luck-44 (L44-0272: p − 1, then rho)** | **16.15** / 18.24 | **18.61** / 20.39 | **19.73** / 21.54 |
| Run 5 luck-43 (rho variant) | 16.88 / 18.30 | 18.93 / 20.27 | 20.55 / 22.12 |
| Run 5 no-luck-41 (×480 square search) | 18.08 / 20.70 | 20.92 / 23.37 | 22.71 / 24.99 |
| Run 5 no-luck-42 (square search) | 20.28 / 23.27 | 22.81 / 25.62 | 25.11 / 28.21 |

What it shows:

- **The first evolved bulb to beat plain rho at scale.** L44-0272 runs p − 1 (bound N^0.21) before rho and needs 1.3–1.6× fewer operations on average at 64–78 bits. The cheap p − 1 stage catches secrets whose p − 1 is made of small factors; at 64 bits the median drops from 2^16.4 to 2^14.9.
- **A better constant, not a better exponent.** Its growth from 64 to 78 bits is about N^0.256, the same as rho's, and its worst case is unchanged. Running p − 1 before rho is also established practice: evolution rediscovered it.
- **The first time luck by design paid.** The p − 1 stage is a cheap bet that wins often enough to save watts overall, which is the rule from Run 4: guessing has to cost less than trying.
- **The scale lesson holds.** Scored at 52–64 bits, the no-luck champions still sit on the N^(1/3) line.
- **Two baseline notes.** The block-flash baseline logs "misses 1" here only because it is over budget: it needs about 2^27 operations at 64 bits, far above this run's 2^23 cap, so it isn't a correctness miss. Lehman is clean at 52–64 bits, but that doesn't cover its known 66-bit miss, which is a window-rounding issue fixed in Stage 1 (see `PLAN.md`).

## At scale: 54–78 bits through the Rust core (Oct 22, 2026)

`lampcore/` is a Rust port of the lamps with operation counting identical to `lamps.py`. `evolve/parity.py` checks this before any big-number result is trusted: 3,312 genome × number pairs (every baseline, every champion of Runs 2–4, 120 random genomes) matched exactly on ops, factor, tests, and hits. The block flash is replayed rather than recomputed: its charges depend only on block sizes, and which block lights up is fixed by where p and q sit; parity confirms the replay against the real polynomial arithmetic.

```
(cd lampcore && cargo build --release)
cd evolve && python3 parity.py && python3 scale.py 40 8
```

Mean cumulative ops per number, log₂, 40 fresh balanced semiprimes per size, cap 2^29 (* = one number not caught):

| Algorithm | 54 | 60 | 66 | 72 | 78 | Trend | Worst at 78 |
|---|---|---|---|---|---|---|---|
| Rho | 14.3 | 15.7 | 17.1 | 18.7 | 20.3 | N^0.249 | 2^21.2 |
| Run 4 luck-33 (rho variant) | 14.3 | 15.8 | 17.5 | 19.0 | 20.2 | N^0.250 | 2^21.4 |
| Runs 2–3 luck champions (rho variants) | 14.1 | 15.8 | 17.4 | 18.6–18.7 | 20.4–20.5 | N^0.258 | 2^21.3 |
| Hart ×480 | 14.8 | 17.2 | 18.5 | 20.4 | 22.7 | N^0.314 | 2^25.1 |
| Run 3 no-luck-22 | 15.3 | 16.6 | 18.5 | 20.5 | 22.8 | N^0.317 | 2^24.8 |
| Run 4 no-luck-31 | 15.3 | 16.5 | 18.5 | 20.5 | 22.8 | N^0.317 | 2^24.8 |
| Run 4 no-luck-32 | 15.0 | 16.4 | 18.3 | 20.7 | 22.6* | N^0.317 | 2^25.0 |
| Run 4 luck-34 (square search + backups) | 14.6 | 16.7 | 18.9 | 20.3 | 22.8 | N^0.334 | 2^24.7 |
| Lehman | 17.4 | 19.3 | 21.1* | 23.3 | 25.3 | N^0.331 | 2^26.3 |
| Block flash | 24.6 | 26.3 | 28.1 | over cap | over cap | N^0.292 | — |

What it shows:

- **Rho wins from about 60 bits up, and the gap widens.** At 78 bits it needs 2^20.3 operations on average; the best luck-free bulb needs 2^22.6, about 5× more.
- **Measured exponents match theory.** Rho variants: 0.249–0.258 (theory 1/4). Hart and every evolved square-search champion: 0.31–0.33 (Hart's heuristic 1/3). Lehman: 0.33 (proven 1/3). The block flash trends at 0.29 and is still falling toward its 1/4, but its ballast puts it over the cap past 66 bits.
- **Run 3's "luck-free beats rho" was a small-number effect.** The Hart family has a smaller constant but a larger exponent; the lines cross between 54 and 60 bits.
- **Evolution at 32–48 bits tuned constants, never exponents.** Every champion sits on its parent method's exponent line. Within this deck, nothing grew a new exponent.
- The two misses are real: Lehman's window constant here is tighter than Lehman's theorem needs, and no-luck-32's stages stop just short of √N.

## Re-scored after the square-search window fix (Stage 1, Oct 23, 2026)

The Oct 22 table above stays as it was; this is the same set re-run (`scale.py`'s numbers, 40 per size, cap 2^29) after Stage 1 of `PLAN.md`. Every square-search genome, old → new mean cumulative ops per number, log₂ (* = one number not caught):

| Algorithm | 54 | 60 | 66 | 72 | 78 | Trend | Worst at 78 |
|---|---|---|---|---|---|---|---|
| Lehman | 17.37 → 17.37 | 19.31 → 19.30 | 21.15* → **21.17** | 23.31 → 23.26 | 25.31 → 25.31 | N^0.331 | 2^26.3 |
| Run 3 no-luck-21 | 15.33 → 15.47 | 16.75 → 16.93 | 18.93 → 19.09 | 20.86 → 21.04 | 23.30 → 23.46 | N^0.335 | 2^25.2 |
| Run 3 no-luck-22 | 15.32 | 16.55 | 18.46 → 18.47 | 20.53 | 22.84 | N^0.317 | 2^24.8 |
| Run 4 luck-34 | 14.58 → 14.64 | 16.73 → 16.77 | 18.93 → 18.87 | 20.31 → 20.35 | 22.80 → 22.82 | N^0.332 | 2^24.7 |
| Run 4 no-luck-32 | 15.02 | 16.41 | 18.30 | 20.73 | 22.59* | N^0.317 | 2^25.0 |
| Hart ×480, Run 2 no-luck-11/12, Run 4 no-luck-31 | unchanged | | | | | | |

What changed:

- **Lehman's 66-bit miss was the window, not the constant.** On N = 23736149549216675201 (p = 4638920653), Lehman's theorem catches it at k = 59881 on the second x of the window. The theory width there is N^(1/6)/(4√k) = 1.73, but the window was `int(1.73)` = 1 wide, so only the first x was tested. The search used up every multiplier and stopped after 4,426,055 tests, far below the cap, with no factor. The 0.25 constant was right all along; the note above blaming it is wrong.
- **The fix.** The window now ends at √(kN) + width, inclusive. √(kN) is taken as s + f from the exact integer square root s, never from a float square root of kN, which loses about 10 bits past 60-bit N. Lehman now catches the number in exactly 1,643,747 operations. Windows only ever get wider, so a mean can rise (more x tested per k) or fall (caught at an earlier k).
- **Every drop has a reason.** Each number whose cost fell was caught either by the same square-search stage at an earlier multiplier, or by a square-search stage where a later stage used to catch it (16 numbers, counting Lehman's former miss; no exceptions). Trends move by at most 0.002, and no conclusion of the Oct 22 table changes.
- **Checks.** The Rust core reports which stage won and, for a square-search win, its k. `parity.py 120 6` matches 3,312 pairs on ops, factor, tests, hits, stage, and k. Turning the instrumentation on changes no op count (4,448 pairs compared).
- **Coverage rule.** A run champion whose stages stop short of √N is now scored with a fallback tail: trial division to √N for a no-luck deck, rho for a luck deck. The tail is charged like any stage and flagged (`fallback` in `lineage.jsonl` and in `scale_coverage.json`). It changed no number in this table: no-luck-32's 78-bit miss (p = 2^38.3, above both its block flash's and its trial division's reach) is still over budget, because its block-flash stage uses up the 2^29 cap by itself before the tail is reached. Trial division to √N would need about 2^37.3 operations there.

Data: `evolve/scale_window_fix.json` (old vs new, coverage rule off) and `evolve/scale_coverage.json` (rule on).

## Statistical re-validation (Stage 2, Oct 23, 2026)

Do the past wins survive a bigger sample with error bars? Rho, Hart ×480, and every Run 3 and Run 4 champion on 80 fresh balanced semiprimes per size (`semiprimes_pq(bits, 80, 990000 + bits)`), cap 2^29, post-Stage-1 code, coverage rule off.

```
cd evolve && python3 revalidate.py 8
```

log₂(mean ops) with a 95% bootstrap interval (10,000 resamples over the numbers in each cell, `random.Random(2026)` per cell, percentile method with 250 resamples outside each end; * = one number not caught, left out of the mean and interval):

| Algorithm | 54 | 60 | 66 | 72 | 78 |
|---|---|---|---|---|---|
| Rho | 14.26 [14.09, 14.41] | 15.84 [15.67, 16.01] | 17.42 [17.24, 17.58] | 18.90 [18.73, 19.05] | 20.29 [20.09, 20.47] |
| Hart ×480 | 14.42 [14.04, 14.74] | 16.94 [16.32, 17.55] | 18.77 [18.37, 19.12] | 20.50 [20.19, 20.78] | 22.37 [22.02, 22.68] |
| Run 3 no-luck-21 | 15.08 [14.81, 15.33] | 17.18 [16.93, 17.42] | 18.94 [18.70, 19.17] | 21.28 [21.03, 21.50] | 23.28 [23.01, 23.53] |
| Run 3 no-luck-22 | 14.64 [14.30, 14.95] | 17.00 [16.51, 17.46] | 18.40 [18.08, 18.69] | 20.79 [20.49, 21.07] | 22.83 [22.44, 23.16] |
| Run 3 luck-23 | 14.41 [14.25, 14.55] | 15.84 [15.64, 16.02] | 17.33 [17.14, 17.51] | 18.72 [18.49, 18.92] | 20.06 [19.85, 20.25] |
| Run 3 luck-24 | 14.42 [14.26, 14.56] | 15.85 [15.65, 16.03] | 17.34 [17.15, 17.52] | 18.73 [18.50, 18.93] | 20.07 [19.87, 20.26] |
| Run 4 no-luck-31 | 14.64 [14.29, 14.95] | 16.99 [16.51, 17.45] | 18.39 [18.08, 18.68] | 20.79 [20.48, 21.07] | 22.83 [22.44, 23.16] |
| Run 4 no-luck-32 | 14.73 [14.35, 15.06] | 16.44 [16.12, 16.73] | 18.52* [18.10, 18.90] | 20.84 [20.50, 21.15] | 22.91 [22.55, 23.22] |
| Run 4 luck-33 | 14.40 [14.23, 14.55] | 16.03 [15.84, 16.20] | 17.35 [17.16, 17.52] | 19.13 [18.97, 19.29] | 20.34 [20.15, 20.51] |
| Run 4 luck-34 | 14.44 [14.09, 14.74] | 16.78 [16.49, 17.03] | 18.64 [18.34, 18.90] | 20.69 [20.38, 20.97] | 22.88 [22.57, 23.17] |

Which past wins survive (overlapping intervals = within noise):

- **Run 3: "a luck-free evolved bulb beats rho" — no, not at 54–78 bits.** no-luck-22 is within noise of rho at 54 and worse from 60 up. Its win was measured at 36–48 bits, which this sample doesn't cover.
- **Runs 3–4: "evolved square searches beat Hart ×480" — no, within noise at these sizes.** no-luck-22, no-luck-31, no-luck-32, and luck-34 overlap Hart at every size. no-luck-21 is worse than Hart at 54, 72, and 78.
- **Run 4: "luck-34 beats rho" — no, not at 54–78 bits.** Within noise at 54, worse from 60 up. (The original claim was at 40 bits.)
- **Run 4: "luck-33 is a better rho" — within noise at every size,** as Run 4 already concluded. The Run 2–3 rho variants (luck-23, luck-24) are within noise of rho too.
- **"Rho beats the square searches from 60 bits up" — yes.** Rho and every rho-family champion are better than Hart at 60–78 bits, with intervals that don't overlap, and within noise at 54. This is the scale lesson again, now with error bars.
- **no-luck-32 misses at 66 bits here** (N = 32724704014144553683). The cause is the one behind its 78-bit miss in the Stage 1 set: its block flash and trial division stop below p (2^32.12), so the number can never be caught, and the trial division runs out the cap first.

Data: `evolve/revalidation.json` (per-cell intervals, verdicts, and every number's ops, winning stage, and k).

## qs vs rho on the Stage 2 numbers (Oct 23, 2026)

A measurement, not a scored run. The quadratic-sieve card alone (its acceptance genome, never tuned above 60 bits) runs on Stage 2's 80 numbers per size, cap 2^29, with Stage 2's bootstrap. qs runs in the Python core, whose accounting was verified phase by phase; the Rust port and parity check are pending (Stage 4). The other rows run through `lampcore`. Rho and Hart ×480 reproduce their Stage 2 rows exactly.

```
cd evolve && python3 qs_stage2.py 8
```

log₂(mean ops) [95% interval], then worst:

| Algorithm | 54 | 60 | 66 | 72 | 78 | Growth per bit |
|---|---|---|---|---|---|---|
| **qs** | 16.09 [16.01, 16.18] / 16.92 | 17.03 [16.96, 17.11] / 17.72 | 17.91 [17.84, 17.98] / 18.58 | 18.88 [18.81, 18.95] / 19.78 | **19.73** [19.66, 19.79] / **20.41** | **0.152** |
| Rho | 14.26 [14.09, 14.41] / 15.58 | 15.84 [15.67, 16.01] / 17.32 | 17.42 [17.24, 17.58] / 19.01 | 18.90 [18.73, 19.05] / 20.06 | 20.29 [20.09, 20.47] / 21.56 | 0.252 |
| Run 5 L44-0272 (p − 1, then rho) | 13.94 [13.68, 14.18] / 16.07 | 15.52 [15.26, 15.75] / 17.27 | 16.94 [16.67, 17.17] / 18.38 | 18.56 [18.28, 18.82] / 20.19 | 20.05 [19.76, 20.30] / 22.04 | 0.254 |
| Hart ×480 | 14.42 [14.04, 14.74] / 17.01 | 16.94 [16.32, 17.55] / 21.10 | 18.77 [18.37, 19.12] / 21.09 | 20.50 [20.19, 20.78] / 22.40 | 22.37 [22.02, 22.68] / 24.91 | 0.325 |

What it shows:

- **qs crosses rho at about 72 bits.** The two are tied at 72 bits (intervals overlap). At 78 bits qs is ahead and the intervals separate: about 1.5× fewer operations on average (19.73 vs 20.29).
- **The worst case crosses first.** qs's worst case drops below rho's from 66 bits (2^18.58 vs 2^19.01), before the means cross. At 78 bits its worst case is about 2.2× lower (2^20.41 vs 2^21.56).
- **The first exponent win in the project.** qs grows about 0.15 log₂-ops per bit; rho, L44-0272 and every earlier winner grow about 0.25 or more. Every earlier win was a constant.
- **Not yet ahead of the best evolved bulb.** Against L44-0272, qs is within noise at 78 bits (intervals overlap) and behind below 72. L44-0272 grows like rho, so the gap should open past 78 bits, but these numbers don't show it yet.
- **Conservative, not a fair fight.** qs is overcharged by rule (every small-number step costs a full op), and its genes were tuned only at 40–60 bits.
- **Narrow intervals.** qs's cost depends on the size of N much more than on which N it is, so its intervals are less than half as wide as rho's.

Data: `evolve/qs_stage2.json`.

## Run 4: luck-by-design cards and the hit-rate meter (Oct 22, 2026)

Same cumulative scoreboard as Run 3, fresh seeds (31–34), with new cards and a new meter column. Outputs in `evolve/run4/`.

```
cd evolve
python3 evolve.py 25 20 8 cumulative fine
python3 validate.py run4
python3 curves.py run4 40 120 8
python3 ancestry.py run4
```

**New cards**

- **Ranked multipliers** (square search mode `ks`): multipliers are taken in chunks of `r` (a gene), each chunk scored Knuth–Schroeppel-style for how square-friendly kN is mod small primes, and tried best-first. Scoring costs one op per small prime per candidate, charged to the meter.
- **Rho degree and start**: genes `d` (x^d + c, d even; costs about log₂d + popcount(d) − 1 multiplies per step) and `x0` (starting value).

**New meter column: hit rate.** Every lamp counts *tests* (checks against its invariant event: a division, a square test, a gcd) and *hits* (the event firing, useful or not). Hit rate = hits ÷ tests separates "luckier per test" from "cheaper per test".

**The cards tested alone**, cumulative at 42 and 48 bits:

| Bulb | Mean ops at 48 bits | Hit rate |
|---|---|---|
| Hart ×480, plain order | 2^13.1 | 2^-12.2 |
| Hart ×480, ranked multipliers | 2^17.0 | 2^-12.2 |
| Rho x² | 2^12.6 | 2^-4.7 |
| Rho x⁴ | 2^13.3 | 2^-4.5 |
| Rho x⁶ | 2^13.4 | 2^-4.2 |

- **Ranking multipliers doesn't pay for a Hart-style search.** Scoring a candidate costs 14 ops; just trying it costs 1. The ranking also left the hit rate unchanged, so it predicts the wrong thing for this method. Luck by design only pays when a test is much more expensive than predicting it (as in the quadratic sieve, where one multiplier choice feeds millions of sieve steps).
- **Higher-degree rho is luckier per test but costs more per step**, so its cumulative total gets worse: the two levers trading against each other.

**Run 4 validation** (12 fresh semiprimes each at 36–54 bits):

| Algorithm | Cumulative score | Hit rate | Mean ops at 48 / 54 bits | Worst at 54 bits |
|---|---|---|---|---|
| Rho | N^0.267 | 2^-5.3 | 2^12.9 / 2^14.3 | 2^15.4 |
| Hart ×480 | N^0.264 | 2^-13.0 | 2^12.3 / 2^14.7 | 2^16.8 |
| **Champion no-luck-31** | **N^0.253** | 2^-12.7 | 2^11.5 / 2^14.4 | 2^16.0 |
| Champion no-luck-32 | N^0.263 | 2^-12.9 | 2^12.4 / 2^14.5 | 2^16.4 |
| Champion luck-33 | N^0.262 | 2^-7.1 | 2^12.9 / 2^13.8 | 2^14.6 |
| Champion luck-34 | N^0.265 | 2^-13.0 | 2^12.5 / 2^14.6 | 2^15.6 |

Champions: no-luck-31 = ×720 square search → block flash → a small ranked-multiplier tail; luck-33 = rho (c = 13, gcd every 13, start 4) → short trial division; luck-34 = ×24 square search → p − 1 → block flash.

What it shows:

- **Evolution mostly declined the new cards.** No champion uses a higher-degree rho. Ranked multipliers survive only as a small tail stage. The best no-luck score ties Run 3's (N^0.253).
- **The luck deck chose a luck-free bulb.** Champion luck-34 is a square search with p − 1 and block-flash backups, not rho, and it beats rho on lumens per watt at 40 bits (2^10.0 vs 2^9.1).
- **Luck-33 looked like a better rho, but a bigger sample says not really.** Its 54-bit mean on the 12 validation numbers was 2^13.8 vs rho's 2^14.3. On 80 fresh 54-bit numbers it was 2^14.23 vs 2^14.40 (about 12% fewer ops, same worst case). Rho with the same constant but the default start showed no gain, and theory says a starting value shouldn't help on average, so this is treated as within noise.
- **Low hit rate doesn't mean unlucky.** Luck-33's hit rate (2^-7.1) is lower than rho's (2^-5.3) only because it runs a gcd test every 13 steps instead of every 64, so it makes more, cheaper tests.

Curves (`curves.py`, 120 planted secrets at 40 bits):

| Algorithm | Median watts | Mean watts | Worst watts | Lumens per watt |
|---|---|---|---|---|
| Champion no-luck-31 | 2^9.3 | 2^9.9 | 2^12.6 | 2^10.1 |
| Champion no-luck-32 | 2^9.5 | 2^10.0 | 2^12.6 | 2^10.0 (1 of 120 never dark) |
| Champion luck-34 | 2^9.5 | 2^10.0 | 2^12.2 | 2^10.0 |
| Champion luck-33 | 2^10.6 | 2^10.9 | 2^12.3 | 2^9.1 |
| Rho | 2^11.1 | 2^10.9 | 2^12.3 | 2^9.1 |

"Never dark" means the bulb's stages stop short of √N, so a secret sitting there is never caught. That secret adds no lumens; the curves tool now counts it instead of crashing.

## Run 3: cumulative scoreboard, started over (Oct 22, 2026)

Same deck and gate as Run 2, fresh seeds (21–24), but scored on the **cumulative total**: watts summed over every test number (see `NOTES.md`). Outputs in `evolve/run3/`.

```
cd evolve
python3 evolve.py 25 20 8 cumulative
python3 validate.py run3
python3 curves.py run3 40 120 8
python3 ancestry.py run3
```

Validation on 12 fresh semiprimes each at 36–54 bits. Score = log₂(mean watts)/bits at 48 and 54 bits.

| Algorithm | Cumulative score | Lumens per watt | Mean ops at 48 / 54 bits | Worst at 54 bits |
|---|---|---|---|---|
| Trial division | N^0.470 | N^0.03 | 2^22.4 / 2^25.5 | 2^26.0 |
| Pollard–Strassen (block flash) | N^0.464 | N^0.04 | 2^22.7 / 2^24.6 | 2^24.8 |
| Fermat | N^0.341 | N^0.16 | 2^15.8 / 2^19.0 | 2^20.6 |
| Lehman | N^0.318 | N^0.18 | 2^15.2 / 2^17.2 | 2^17.7 |
| Rho | N^0.267 | N^0.23 | 2^12.9 / 2^14.3 | 2^15.4 |
| Hart ×480 | N^0.264 | N^0.24 | 2^12.3 / 2^14.7 | 2^16.8 |
| Champion no-luck-21 | N^0.264 | N^0.24 | 2^12.2 / 2^14.8 | 2^15.6 |
| **Champion no-luck-22** | **N^0.253** | **N^0.25** | **2^11.5 / 2^14.4** | 2^16.0 |
| Champion luck-23 | N^0.273 | N^0.23 | 2^13.4 / 2^14.3 | 2^15.6 |
| Champion luck-24 | N^0.273 | N^0.23 | 2^13.4 / 2^14.3 | 2^15.6 |

Curves (`curves.py`, 120 planted secrets at 40 bits):

| Algorithm | Median watts | Mean watts | Worst watts | Lumens per watt |
|---|---|---|---|---|
| Evolved no-luck-22 | 2^9.3 | 2^9.9 | 2^12.6 | 2^10.1 |
| Evolved no-luck-21 | 2^9.6 | 2^10.1 | 2^12.7 | 2^9.9 |
| Hart ×480 | 2^9.3 | 2^10.6 | 2^15.8 | 2^9.4 |
| Rho | 2^11.1 | 2^10.9 | 2^12.3 | 2^9.1 |
| Lehman | 2^12.5 | 2^12.6 | 2^13.6 | 2^7.4 |
| Trial division | 2^18.3 | 2^18.4 | 2^18.9 | 2^1.6 |
| Block flash | 2^20.2 | 2^20.2 | 2^20.3 | 2^-0.2 |

What it shows:

- **On the cumulative scoreboard, a luck-free evolved bulb beats rho.** Champion no-luck-22 (a ×720 multiplier square search with a short trial-division tail) has the best cumulative score and the best lumens per watt at 36–48 bits. At 54 bits it is level with rho (2^14.4 vs 2^14.3 mean), so rho's flatter growth may take over above that.
- **The curve shapes are the story.** The Hart family darkens most secrets very early (median 2^9.3) but has a long tail of stubborn ones (Hart's worst is 2^15.8). Rho's curve is a narrow cliff: almost nothing before 2^9, almost everything by 2^12. The evolved champions keep Hart's early light and shorten its tail.
- **Worst-case and cumulative scoring pick different winners.** Under Run 2's worst-case meter, rho led. Under the cumulative meter, the layered square search leads, because the score now rewards darkening most secrets cheaply, not just the hardest one.

## Run 2: honest meter plus the block flash (Oct 22, 2026)

25 generations, population 20, two runs per deck. Validation on 12 fresh semiprimes each at 36, 42, 48, 54 bits, worst case. Score = effective exponent at 48 and 54 bits.

| Algorithm | Validated score | Lumens per watt | Trend | Worst ops at 54 bits |
|---|---|---|---|---|
| Trial division | N^0.478 | N^0.02 | N^0.518 | 2^26.0 |
| Pollard–Strassen (block flash) | N^0.467 | N^0.03 | N^0.319 | 2^24.8 |
| Fermat | N^0.375 | N^0.13 | N^0.431 | 2^20.6 |
| Lehman | N^0.332 | N^0.17 | N^0.339 | 2^17.7 |
| Hart ×480 | N^0.300 | N^0.20 | N^0.340 | 2^16.8 |
| Rho | N^0.290 | N^0.21 | N^0.272 | 2^15.4 |
| Champion N11-0140 (no-luck) | N^0.300 | N^0.20 | N^0.317 | 2^16.7 |
| Champion N12-0154 (no-luck) | N^0.299 | N^0.20 | N^0.319 | 2^16.3 |
| Champion L13-0161 (luck) | N^0.293 | N^0.21 | N^0.255 | 2^15.5 |
| Champion L14-0196 (luck) | N^0.293 | N^0.21 | N^0.255 | 2^15.5 |

What it shows:

- **The overfitting is gone.** Run 1's no-luck winners lost about 0.18 in the exponent between training and validation. Run 2's champions score within 0.015 of their gate scores (the gate is 48 bits only; validation adds 54).
- **Evolution rediscovered Hart's multiplier trick.** Champion N11-0140 descends from a plain k = 1, 2, 3… square search. Its line went: seed (N^0.321) → added a trial-division tail → tuned the multiplier to k = 720i (N^0.275) → k = 60i. The other no-luck run found k = 12i independently. Both match hand-built Hart ×480.
- **The luck deck regrew rho** and matches it to the third decimal.
- **The block flash was dropped by every run.** It's the better bulb asymptotically (trend falling toward 1/4), but its tree overhead is heavy ballast: at 54 bits it costs 2^24.8, barely under trial division. A fit to its cost model (N^(1/4)·log² N) projects it overtaking trial division at about 54 bits and Lehman only at about **179 bits**.
- **Luck buys the block flash's exponent without the ballast.** Rho and the block flash share the N^(1/4) exponent; rho gets there with almost no memory or overhead, which is why it wins at every size tested here.

## Run 1 (Oct 22, 2026)

The first meter fitted a slope over 20–44 bits on a fixed training set, with no block flash. Validated on fresh 36–54 bit numbers:

| Algorithm | Training work | Validated work | Worst ops at 54 bits |
|---|---|---|---|
| Lehman (hand-built) | — | N^0.339 | 2^17.7 |
| Rho (hand-built) | — | N^0.272 | 2^15.4 |
| Evolved no-luck-1 | N^0.255 | N^0.426 | 2^20.1 |
| Evolved no-luck-2 | N^0.233 | N^0.410 | 2^18.0 |
| Evolved luck-3 | N^0.126 | N^0.206 | 2^15.1 |
| Evolved luck-4 | N^0.188 | N^0.271 | 2^15.4 |

The no-luck winners had overfit, and the luck-3 slope came mostly from being slower on small N. Those two failures are what the v2 meter fixes.

## Honest limits

- Evolution can only recombine the parts it's given. A plateau shows the ceiling of the deck, not of mathematics.
- Sizes here are small (32–54 bits). Constants and log factors matter a lot, which is exactly why the block flash loses. Asymptotic claims need bigger numbers.
- Op counts are a model: one ring multiply, square test, or gcd = 1 op regardless of operand size, and block-flash polynomial products are charged at FFT cost.
- Hart's method and rho are heuristic: they behave well in practice, but neither has a proven worst-case bound like Lehman or Pollard–Strassen.
- The quadratic-sieve card (`evolve/qs.py`, cost model in `NOTES.md`) is deliberately overcharged. Every small-number step (an add mod p, a log-add into a sieve cell, a word XOR, a Euclid step) costs a full op, the same as one of rho's multiplies mod N. The rule is that qs is never cheaper than rho per unit of work. Its acceptance test factored 240/240 fresh numbers at 40–60 bits, with 1 retry paid in full, and every phase's op count matched its written formula exactly.
- The sieve array uses numpy for speed. This changes no op count: updates and scanned cells are charged one by one, whatever does the arithmetic.
