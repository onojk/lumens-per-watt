# lumens-per-watt

Growing factoring algorithms by evolution, and measuring them by **lumens per watt**.

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
