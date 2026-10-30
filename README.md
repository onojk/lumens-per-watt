# lumens-per-watt

How much of the number line does each step of a factoring algorithm light up, per unit of real cost?

lumens-per-watt evolves and tunes integer-factoring pipelines and scores them by the work they actually do. Each method is a **lamp**: trial division, Pollard rho, Pollard p-1, ECM and a self-initializing quadratic sieve ("qs"). A pipeline is a sequence of lamps, each with a budget. Every operation a lamp performs is charged on an exact **op meter**, and pipelines are compared by how cheaply they find factors.

The picture behind it: place a number's smaller factor on the line θ = log p / log N, from 0 (tiny factors) to ½ (balanced semiprimes). Each lamp lights part of that line brightly and the rest dimly. Some regions are walls, expensive to light by any method. A good pipeline covers the line with the least total cost.

Independent research by Jonathan Kendall. Rust ("lampcore") for the fast core, Python for the harness and analysis; the two cores must agree exactly.

## Status and how to pick this up

**Status: paused after phase 1 (Oct 30, 2026).**
- **What phase 1 did:**
  - built an exact op meter for six factoring lamps, with a Rust core and Python twins that must agree;
  - scored them under four pricings;
  - ran a sealed program search (arrangement-v1) under a judge the search could not touch or see past.
- **What it found:**
  - the search rediscovered Pollard rho;
  - two further families, square-form walks and change-the-group, were stopped at cost-model pre-checks;
  - the missing quadratic-sieve refinements are worth about 10% or less;
  - the cheapest known method per size (the frontier) was measured: the quadratic sieve on balanced semiprimes, rho on numbers with one small factor.
- **Within 40–100 bits** (measured at 48–96), under the worst-of pricing set, nothing tried lands ahead of that frontier.
- **No novelty is claimed.** See [Findings so far](#findings-so-far-oct-30-2026) and the phase conclusion there for the numbers and their scope.

**What's ready to reuse:**
- **The judge:**
  - `tools/judge.py` pins every file that decides a score by sha256, in the predictions file;
  - `tools/sealed_run.sh` refuses to run unless the predictions are committed, checks the pins before and after, and commits each result;
  - `tools/search_sandbox.sh` runs a search with only training data visible (an allow-list, a held-out-seed check, no network, a clean environment, its own process group);
  - `tools/score_sandbox.sh` scores in a fresh sandbox after killing any search.
- **The meter:** `lampcore/` (Rust) and its Python twins in `evolve/` (`lamps.py`, `qs.py`, `ecm.py`, `arr.py` and the rest), with parity suites (`evolve/parity.py`, `evolve/arr_parity.py`) that must agree op for op.
- **The four pricings:** official op count, ruint, Montgomery and op-class v1 (`evolve/optypes.py`, `evolve/calibrate.json`, `opclass/opclass_v1.json`), plus a size-scaled gcd view (`evolve/gcdscale.py`).
- **The frontier measurement:** `explore/frontier.py` measures each lamp's cost per size under every pricing and finds the cheapest. Results: `results/frontier_table.md`, `results/frontier.png` and `results/frontier.json`.
- **The next-family template:** `docs/planning/next_family_template.md` holds the frontier reference, the level and slope win rules, held-out sizing, tie-breaking and the guards. It is frozen and pinned only when a family's predictions are sealed.
- **The forecast workflow:** `predictions/<id>.md` is sealed before any run (forecasters' text verbatim, with notes). Results are scored as written (`results/arrangement-v1_forecast_scores.md`). Model runs live in `wolfram/` (input and output committed, labelled as models).

**Open doors** (each with its conditions in [MOVES.md](MOVES.md) and [NOTES.md](NOTES.md)):
- **Square-form walks (SQUFOF-like):** worth reopening if a variant's measured step constant A falls below about 2.1 (Shanks's queue might help), or if the pricing set changes.
- **Change the group:** worth reopening for a cheaper p + 1 (one seed per number), a stage 2 shared between p − 1 and p + 1, or populations where p + 1 is often smooth.
- **Cheaper candidate rejection / resieving** in the quadratic sieve: a tuning experiment, not a new idea. Confirmation is 35–57% of the sieve's cost at 48–80 bits. It needs approval and a cost model first.
- **Past 2^100:** lampcore's QS, ECM and CFRAC keep kN in 128-bit integers and refuse larger N. Widening means changing the core and the Python twins together, a cost-model note, parity at the new sizes and re-pinning the judge. It is also a scope decision: the project targets roughly 40–100 bits.
- **The θ map's ECM-vs-rho crossover:** on numbers with one small factor, ECM's cost against rho falls from 22 × at 48 bits to 4.6 × at 96, so a crossover probably lies just past 96 bits. It is not measured.
- **The Illumination program** (PLAN.md, Oct 26): a watt meter (energy counters against priced cost), a price map (where in price space each pipeline wins), a light spectrum (success against θ per unit cost) and the steps after them. Planning only.
- **Larger held-out sets:** about 600 numbers at 64 bits and 850 at 80 to resolve cost ratios to ±5% (the 48 per size used so far resolve about ±15–20%).

**How to start:**
1. Build the core: `cd lampcore && cargo build --release` (Rust stable; ruint 1.20.1 is pinned in `Cargo.lock`).
2. Check the meter: `cd evolve && python3 parity.py` (lamps against lampcore) and `python3 arr_parity.py` (the arrangement lamp). Both must report no mismatches.
3. Check the judge: `python3 tools/judge.py check arrangement-v1` should print `ok` with nothing pending.
4. Reproduce the frontier: `python3 explore/frontier.py > explore/frontier.out` (2 workers; tens of minutes at the 2.4 GHz cap used here). Its bound rule is in the script's docstring.
5. **Any new family starts with a cost-model pre-check against the frontier, before any code:** charges in existing op types written in NOTES; the unknown constants measured unmetered in `explore/`; the expected cost ratio against the frontier under the worst-of pricing set; a go/no-go.

**Contributing:**
- Issues and pull requests are welcome.
- A new family must follow `docs/planning/next_family_template.md`:
  - the frontier as the reference;
  - the worst-of pricing set;
  - held-out numbers the search never sees;
  - predictions sealed before any run;
  - a cost model in NOTES before code.

## Findings so far (Oct 30, 2026)

Every claim below is scoped to its sizes, budgets and pricings. Details: [NOTES.md](NOTES.md) (cost models, runs, results) and [MOVES.md](MOVES.md) (ideas and their statuses).

**A sealed program search rediscovered Pollard rho (arrangement-v1).**
- **The family:** about 15 "arrangement + detection rule" pairs (stride walks, folds, polynomial maps, bins, exponent towers; per-dot, batched, Floyd, Brent and bin-compare detection), searched by coordinate search.
- **The judge:** pinned by hash, checked before and after each scored run, with the search sandboxed away from held-out numbers.
- **The pick** on balanced numbers was a polynomial map with Brent cycle detection, i.e. rho.
- **Held-out cost:** 0.99 × rho at 64 and 80 bits (robust over op-class, ruint, Montgomery and a size-scaled gcd price; intervals about ±20% at 48 numbers per size).
- **Selection bias:** its growth fitness fell from 1.048 on training numbers to 0.968 held out, which is why held-out numbers are kept.
- **On numbers with one small factor** (θ 0.20–0.30) the search again picked a rho variant. p − 1 lost on cost.
- **Forecasts:** 20 sealed forecasts from three forecasters: 15 genuine passes, 3 not falsified by default, 2 falsified.
- **Scope:** 48–96 bits, the search's budget (16 × rho's worst training cost per number); no genome beat rho by more than about 15–20%.

**Growth fitness can be bought by padding.** A genome that is dearer at the bottom of the size range looks as if it grows slowly. The θ pick did this: 1.27 × rho at 64 bits, 0.99 × at 80. The rules for future families therefore require:
- **a slope win** to be no dearer than the reference at any measured size;
- **a level win** to be cheaper at every size under every pricing in the worst-of set.

**Two candidate families were stopped at the pre-check, before any search code.**
- **Square-form walks (SQUFOF-like):**
  - **Measured:** its step constant, and the cost of a 64-bit division on this machine.
  - **Expected cost:** 1.31–1.41 × rho at 48–80 bits under the worst-of pricing, even at the low end of the measured step count. One-word arithmetic does not make up for the extra steps once divisions are timed.
- **Change the group (p − 1, p + 1, small elliptic curves):** wins exist only for lamps already in the project (ECM, and p − 1 with stage 2) on balanced numbers. p + 1, the new member, wins nowhere, and on θ 0.20–0.30 numbers no group method beats rho at 48–64 bits.

**The measured frontier:** the cheapest existing lamp per size, exact charges, frozen genes, 96 fresh numbers per size, robust over the worst-of pricing set.
- **Balanced:** the quadratic sieve at every size from 48 to 96 bits. At 48 bits p − 1 with stage 2 ties it under some pricings.
- **θ 0.20–0.30:** rho at 56–96 bits; trial division at 48 under op-class.
- **No crossovers in 48–96.** This frontier is the reference future families must beat.

**Phase conclusion.**
- **Families:** within 40–100 bits (measured at 48–96), every family tried or pre-checked lands on or behind the known-lamp frontier. That covers the sealed arrangement search, square-form walks, change of group and sieve refinements.
- **The frontier:** quadratic sieve on balanced numbers; rho on θ 0.20–0.30.
- **Rules:** this holds under the worst-of pricing set and the win rules above.
- **No novelty is claimed.**
- **Scope:** these families at their stated budgets and gene grids, random semiprimes of the two kinds measured, and lampcore's charges.

![The frontier: op-class cost per factorisation against N's size, per lamp, balanced and θ 0.20–0.30](results/frontier.png)

## How it is measured

- **The op meter.** Every operation is charged by what it physically is (a fixed classification rule): a full multiply mod N, a reduction modulo a small prime, a word-level step (an add, a compare, an index move), a gcd, and so on.
- **Three pricings of the same counts.**
  - official: every op costs 1;
  - ruint: prices relative to a generic 256-bit multiply, calibrated on this machine;
  - Montgomery: prices relative to a fast multiply.
- **Two tracks.** Track R (robust: worst of the three pricings) and Track M (Montgomery decides).
- **Discipline.**
  - Predictions are registered before results, including those of outside reviewers.
  - Claims are confirmed on sealed fresh numbers, per size band, with paired bootstrap intervals.
  - The reference changes only through a pre-registered replacement rule.
  - Every change to the card or the meter comes with a cost-model entry first, an acceptance test, and a full Python/Rust parity run.
  - Meter corrections (charging work that was uncharged) are kept separate from re-pricings (charging the same work at its correct type), and each is reported on its own.

## Where it stands (Oct 2026)

- Two-track size scaling at 54-96 bits is done. Stage-1 p-1 pays for Track M at every size; for Track R only at 54 bits.
- The quadratic sieve's reference genes were replaced through the replacement rule. Most of the gain came from fixing the card, not from tuning.
- An audit of the meter is in progress. It found:
  - operations charged above what they physically are (the Gray-code root update; candidate evaluation; search, sort and bookkeeping steps);
  - operations not charged at all (the ledger's duplicate check; sieve start offsets; a sort inside re-sieving).
  Each is being corrected with its own cost model, parity run and report.
- Root-matched confirmation ("re-sieve") pays only when its prime cutoff p0 is tuned. A cost model puts the best p0 in the hundreds at 84-96 bits, and suggests it matters for Track M but barely for Track R. A scored slack retune with a p0 sweep is next.
- Large-prime pairing is explained by three things: only quadratic-residue primes can occur (halving the support), the filed size distribution, and pooling across numbers. The double-large-prime variation stays marginal at these sizes.

## How this project works

- **Sealed predictions.** Every scored experiment has its predictions committed in `predictions/` before it runs, including those of outside reviewers (DeepSeek), whose rounds are kept in `reviews/`.
- **The guard.** Scored runs go through `tools/sealed_run.sh`. It refuses to run unless the predictions are committed and unchanged, and it commits each run's output to `results/`, naming the prediction commit.
- **Model against card.** Model work (Wolfram, run from the command line in `wolfram/`) produces forecasts, recorded as "model" and never scored. Only the card's measured runs score predictions.
- **The record.** Results and scores are in `NOTES.md`, which is append-only. The full workflow is in `PROTOCOL.md`.
- **Decisions.** Nothing is adopted, retuned or pushed without the author's decision.

New ideas and opportunities are logged and evaluated in `IDEAS.md`.

Details, numbers and every prediction with its score are in `NOTES.md`; candidate moves in `MOVES.md`; the plan in `PLAN.md`.

## Roadmap: the Illumination program

After the current meter corrections, five phases (full plan in `PLAN.md`):

1. **Watt meter.** Measure real energy (CPU energy counters), instructions and time per run and per phase, and check them against priced cost. A phase that costs more in joules than its price says is hiding work. This makes "lumens per watt" literal, and turns meter holes into something a run detects rather than something found by reading code.
2. **Price map.** Since cost is op counts times a price vector, store the counts and show, for any two pipelines, the region of price space where each wins, instead of judging at three fixed hardware points. Decisions become boundaries, such as "re-sieve pays when word / small-modulus price is below r*".
3. **Light spectrum.** Replace a single efficiency number with a curve: the probability of success as a function of θ, per unit cost, for each lamp and pipeline. Pipelines are compared by which curve dominates, and the dark regions of the line become visible.
4. **Hazard monitor.** Track each running stage by its chance of success in the next unit of cost (or, for qs, relations collected toward F + 10), giving anytime curves and a rule for when to switch lamps.
5. **Dark mass.** Treat the factor's position on the θ line as uncertain. Every stage, including one that fails, rules part of it out. Score lamps by bits of uncertainty removed per unit cost, and schedule them greedily by that measure.

## Repository layout

- `lampcore/`: the Rust core (lamps, op meter, per-type counters, benchmarks)
- `evolve/`: the Python harness (lamps, ledger, qs, pricing, tuning, acceptance and parity tests, analysis scripts)
- `NOTES.md`: the running lab notebook: decisions, cost models, results, predictions and scores
- `MOVES.md`: candidate moves (card changes, pricing changes, search methods) and their status
- `PLAN.md`: the plan and the order of work
- `IDEAS.md`: ideas and opportunities: proposed, adopted, parked, rejected

## Running it

```
cd lampcore && cargo build --release   # the fast core the harness calls
cd ../evolve
python3 evolve.py 25 20 8      # generations, population, worker processes
python3 validate.py            # champions vs baselines on fresh 36–54 bit numbers
python3 ancestry.py            # family line of each run's champion
python3 ancestry.py N11-0076   # family line of any named genome
```

Outputs: `evolve.log`, `results.json`, `lineage.jsonl`, `validation.json`. Runs are seeded, so the same commands reproduce the same numbers on any machine.

## License

License: MIT (see [LICENSE](LICENSE)). Copyright (c) 2026 Jonathan Kendall.
