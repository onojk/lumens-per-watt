# Contributing

lumens-per-watt measures the cost of factoring with an op meter: every operation in a charged path is counted and priced. A change is worth something here only if the meter can be trusted afterwards, so the rules below exist to protect the meter and the record. The full workflow is in [PROTOCOL.md](PROTOCOL.md); the reasoning behind every result is in [NOTES.md](NOTES.md).

## How a change is accepted

1. **Open an issue first.** Say what you want to change and why. For a change to charging, op counts or prices, **write the cost model in the issue before any code.** That means which ops are added or removed, of which type, how many per number, and what they cost under the three pricings (official, ruint, Montgomery). An uncharged op is a critical bug.
2. **Both cores, in lockstep.** The Python reference (`evolve/`) and the Rust core (`lampcore/`) must give identical op counts, per number and per op type. A parity failure is a blocker.
3. **New behaviour is a gene, off by default.** With the gene off, results must be identical to the previous commit on every number and every op type.
4. **Acceptance.** Every change ships with an acceptance script (see `evolve/*_accept.py` for examples). The script shows:
   - off identical to before;
   - on identical in relations and factors (unless the change is meant to alter yield, which needs a stated reason);
   - Python = Rust per type.
5. **Parity.** `evolve/parity.py` must pass with cases for the new gene added.
6. **CI** (`.github/workflows/parity.yml`) runs a quick subset, `evolve/ci_quick.py`, on every pull request. Passing CI is necessary, not sufficient: the maintainer runs the full acceptance and parity before merging.

Code must be your own or MIT-compatible. Port algorithms from papers and descriptions; do not copy or translate GPL code.

## What only the maintainer decides

- the reference genes, and any retune;
- prices and the pricing tables;
- adopting any change into the card;
- pushes to `main`, and what counts as a result.

A pull request can propose any of these; it cannot settle them.

## Predictions

Every scored run is sealed: its predictions are committed **before** it runs, and it runs only through `tools/sealed_run.sh`.

To submit predictions for an announced run, open an issue titled `predictions: <run id>`. Use the form "under conditions X, Y will be Z × baseline B on metric M", with a range and, if you like, a falsifier. Predictions posted after a run's results exist are recorded as information only. Predictions are scored as written and never restated afterwards.

## Timing on your own machine

`tools/contribute_timing.sh` times the reference and the current candidate cells (`runs/contribute.json`, 2 replicates) and writes one results file. Attach that file to an issue. It uploads nothing itself.
- Ratios are compared within one machine, never pooled across machines without saying so.
- A contributor's timing is information, not a sealed result.
- For a full replication run, see [FRIEND.md](FRIEND.md).

## Style

Dry and evidence-first. Lead with the number, then the failure modes. Failures are results: record them, never delete or soften them.
