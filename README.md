# lumens-per-watt

Growing factoring algorithms by evolution, and measuring them by **lumens per watt**.

## The idea

Every algorithm lights up the number line as it runs: some stations are queued, some staged, some being crunched, some kept as afterglow. Two quantities fall out of that picture:

- **Watts**: compute spent, counted in operations (one modular multiply, square test, or gcd = 1 op).
- **Lumens**: candidate stations for *p* ruled out. For a balanced semiprime N = pq, finishing means all ~√N candidates are dark.

**Lumens per watt** is stations ruled out per operation, the efficacy of the bulb. Running more hardware in parallel raises the watts, not the efficacy. Only a better bulb moves the wall.

If an algorithm's worst-case work grows like N^e, its efficacy grows like N^(1/2 − e):

| Method | Work | Lumens per watt |
|---|---|---|
| Trial division | N^(1/2) | 1 |
| Lehman | N^(1/3) | N^(1/6) |
| Pollard–Strassen | N^(1/4) | N^(1/4) |
| Harvey | N^(1/5) | N^(3/10) |

## The experiment

Algorithms are built from lamp parts:

- `td`: trial division up to N^a
- `sq`: square search on kN, which covers Fermat (k = 1, wide window), Lehman (k up to N^(1/3), windows ~N^(1/6)/√k), and Hart (window 1)
- `rho`: Brent's rho with batched gcds
- `pm1`: Pollard p − 1

A genome is a chain of up to four parts with tunable settings. Evolution mutates settings, inserts, deletes, reorders, and splices chains.

**Fitness is worst luck.** Each genome runs on balanced semiprimes at 20, 26, 32, 38, and 44 bits. The score is the slope of the *worst* operation count across sizes, fitted as N^e. A genome that misses any test number within budget is treated as not finished.

Two decks evolve separately:

- **no-luck**: `td` and `sq` only, square-search methods with deterministic structure
- **luck**: adds `rho` and `pm1`, whose speed rests on behaving as if random

## Running

```
cd evolve
python3 evolve.py 30 24     # generations, population
```

Results go to `results.json` and `evolve.log`.

## First results (Oct 22, 2026)

30 generations, population 24, two runs per deck. Training fit on 20–44 bits; validation on 12 fresh semiprimes each at 36, 42, 48, 54 bits, worst case.

| Algorithm | Training work | Validated work | Validated lumens/watt | Worst ops at 54 bits |
|---|---|---|---|---|
| Trial division | — | N^0.518 | N^-0.02 | 2^26.0 |
| Fermat | — | N^0.431 | N^0.07 | 2^20.6 |
| Lehman (hand-built) | — | N^0.339 | N^0.16 | 2^17.7 |
| Rho (hand-built) | — | N^0.272 | N^0.23 | 2^15.4 |
| Evolved no-luck-1 | N^0.255 | N^0.426 | N^0.07 | 2^20.1 |
| Evolved no-luck-2 | N^0.233 | N^0.410 | N^0.09 | 2^18.0 |
| Evolved luck-3 | N^0.126 | N^0.206 | N^0.29 | 2^15.1 |
| Evolved luck-4 | N^0.188 | N^0.271 | N^0.23 | 2^15.4 |

What it shows:

- **The no-luck deck overfit.** Its winners looked like N^0.23 in training and came out N^0.41–0.43 on fresh numbers, worse than hand-built Lehman.
- **The luck deck rediscovered rho.** luck-4 is essentially rho. luck-3 is a portfolio of rho runs with different constants; its lower slope comes mostly from extra cost at small N, and at 54 bits it is level with plain rho.
- **Nothing beat the known ceilings** of the parts: about N^(1/3) without luck, about N^(1/4) with it.

Known issue: the `hart` baseline in `evolve.py` is mis-specified (window 1 without the 4kN form) and misses 8 of 48 validation numbers.

## Honest limits

- Evolution can only recombine the parts it's given. A plateau shows the ceiling of the deck, not of mathematics.
- Exponents fitted from 20–44 bit numbers are noisy. Constants and small-N effects are large at this size, so validate any winner on bigger, unseen numbers.
- The fitness can be gamed: a lower slope can come from being slower on small N rather than faster on large N. Check the worst-case op counts at the largest size, not just the slope.
