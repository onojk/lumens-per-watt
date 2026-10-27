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
