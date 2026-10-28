# Working on lumens-per-watt

Plan: [PLAN.md](PLAN.md). Reasoning, cost models, predictions and results: [NOTES.md](NOTES.md). Moves and their statuses: [MOVES.md](MOVES.md).

- The meter is sacred. Any change to charging, op counts or pricing gets its cost model written in NOTES.md BEFORE code. An uncharged op is a critical bug.
- Predictions before results: "under conditions X, Y will be Z x baseline B on metric M", written in NOTES before the run. Scored as written; never restated afterwards.
- Verdicts: sealed numbers run once, paired bootstrap intervals, and all three pricings (official, ruint, Montgomery). Fitness = robust ratio (c); reports call a cell only where all three agree (e).
- Failures are results. Never delete or soften one. Record it in MOVES.md with its conditions. To retry a ruled-out idea, say which condition changed.
- Python and Rust (lampcore) stay in lockstep. Parity must pass; parity failures are blockers.
- Stay classical and at intermediate sizes (roughly 40-100 bits). Look for constant-factor and structural gains inside L[1/2]; no NFS-scale or quantum detours unless asked.
- Parameter tuning is measured (Run 8, with control arms), never presented as a new idea. New ideas are structural or cross-domain moves (MOVES.md).
- Reuse rule: build in-house only what the meter must see; reuse libraries as references and oracles, never in a charged path.
- License: MIT. Port algorithms from descriptions and papers; never copy or translate GPL code line by line.
- One Claude session owns the repo at a time. Park unfinished work in scratch during long runs. Commit at each step. Never push: the user pushes from his terminal.
- Register: dry and evidence-first. Lead with the robust ratio, then the mean, then the failure modes. No hype words.
- Offer next experiments ranked by information per compute.

## Workflow

- How work is done: [PROTOCOL.md](PROTOCOL.md). Wolfram runs: [wolfram/README.md](wolfram/README.md). Outside reviews (DeepSeek): [reviews/README.md](reviews/README.md).
- Scored runs go only through `tools/sealed_run.sh`, with `predictions/<id>.md` committed first.
- Explicit `git add` only (never `commit -a`). Never push.
- Stop and report at decision points: adopting a change, retunes, reference changes and pushes are the user's.
- Documentation addenda go in their own commits, marked "documentation only".

### Novelty Plan check-in (standing rule, Oct 28)

The user's living plan is kept by the reviewer as a doc and mirrored here. Changes to the phases are the user's decision; the reviewer updates the doc and this mirror together.

- **Phase 1, finish wins:** div64 timing, the fixed partials table, all three forecasters sealed. Gate: both scored.
- **Phase 2, meter integrity:**
  - the absolute meter-health check as a routine on every timed comparison;
  - I-001 charged types;
  - the judge (harness, meter, line map, predictions) locked away from any proposer.
  - Gate: I-001 parity clean.
- **Phase 3, measure growth:** the growth-exponent harness (40 to 110 bits); the first untested published method (proposed: Murru-Salvatori). Gate: growth fitness frozen before anything is scored with it.
- **Phase 4, program search:** the building-block DSL, metered by construction; the proposer locked out; scored on growth. Gate: a composed card passes acceptance.
- **In parallel:**
  - the landscape map: the light spectrum across θ, dark regions, MAP-Elites; energy if RAPL is enabled;
  - the twilight band's exchange rate: the marginal op-class cost and success gain of one extra QS partial relation against one extra ECM curve, at matched θ (DeepSeek's suggestion, added Oct 28).

Every report ends with ONE line: "Novelty Plan: phase N, <gate status>; this work advanced / did not advance it (why)". If proposed work serves none of the phases, say so before starting it.

### Wolfram as a research tool

- Use wolframscript (wolfram/ convention, 3ac43ab) on your own initiative whenever a question is a model, forecast or exact computation rather than a code measurement. That covers:
  - cost models before code (op counts × prices under ruint / Montgomery / official);
  - yield forecasts from the light meter or the card-sieve simulation;
  - smoothness probabilities;
  - parameter scans (F, M, slack, pp, small-prime cutoff);
  - sanity checks of hand arithmetic in NOTES;
  - checks of reviewer or DeepSeek numbers.
- Every run: the input is committed as `wolfram/<topic>.wl` and the output as `wolfram/<topic>.out` (named `<date>_<name>` per wolfram/README.md). A NOTES entry says what the run computed and what it does not establish. Wolfram output is a model, never a verdict: verdicts come only from sealed card runs.
- **Order with sealing:** a Wolfram forecast meant to inform predictions is run and committed BEFORE the predictions are sealed, and it may not see the sealed run's results. Post-run Wolfram analysis is labelled post hoc.
- Never run Wolfram (or any heavy job) while a timed run is in progress. Check first that the status line says idle. Note in the run record if the user's desktop Mathematica kernel was running.
- If wolframscript fails on a license error (desktop Mathematica holding the kernel), say so and continue without it; do not retry in a loop.
- Reviewer-written Wolfram prompts (with sealed predictions) still come from the user. Run them through wolframscript when the user pastes them, and record them as given.
