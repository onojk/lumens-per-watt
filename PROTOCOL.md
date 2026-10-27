# Protocol: how work is done here

This file is the single source of truth for the workflow. Tool details are in `wolfram/README.md` and `reviews/README.md`.

## Roles

- **The user** decides: adopting a change, retuning genes, changing the reference, and every push.
- **Claude Code** builds, runs, records and scores. It does not adopt, retune or push.
- **The reviewer** (Claude, in chat) checks reports and writes briefs.
- **DeepSeek** (and Grok when available) gives independent sealed predictions and derivations.
- **Wolfram** is run from the command line for model work.

## Sealing

- Every scored experiment has `predictions/<id>.md` committed **before** it runs, and runs through `tools/sealed_run.sh <id> [--deepseek] -- <command>`. There are no scored runs outside the guard.
- Predictions filed after a run, or after its results exist in the repo, are **information-only**, and their record says so.
- A copied predictions file states that it is a verbatim copy and names each block's first commit.
- Never re-run an experiment whose predictions are already scored. A new run needs new predictions and a new ID (for example stage H → stage H2).

## Order

predictions → commit → (DeepSeek ask → commit) → run → commit → score → commit → report.

Scores go in NOTES.md, each prediction as written ("under X, Y will be Z × baseline B on metric M"); predictions are never restated afterwards. Failures are results.

## Change types

- **Counts-identical code changes** (slow code, layout, buffers):
  1. a cost note in NOTES before code;
  2. acceptance: identical per number and per type against the previous build, and Python = Rust;
  3. parity.
- **Meter changes** (charging, op counts, pricing): the cost model is written in NOTES before code. An uncharged op is a critical bug.
- **Card-changing options** are genes, off by default until the user adopts them.
- **Experiments are report-only.**

## Timed runs

- `tools/sealed_run.sh` saves the machine's state before and after each run beside its result (`results/<id>_<time>.machine.txt`, from `tools/machine_state.sh`): date and time; CPU governor; current and max MHz of the pinned core (core 2); load average; AC power; CPU temperature; and the top 5 processes by current CPU.
- **Noise:** wall-clock differences within ~2% (the replicate spread seen in H2) are treated as noise.
- **Comparisons are only within one run.** The same reference has taken 1,898 / 2,015 / 2,100 µs in different sessions.
- If the governor is "powersave", the report says so. Changing it is the user's call.
- **Timed comparisons are interleaved and counterbalanced** (`evolve/timing.py`): replicate 1 times the cells forward (reference first), replicate 2 backward, and so on. The order is recorded in the results, and the machine state is read before each replicate as well as before and after the run.
- **The pinned core's clock is sampled every second while each cell is timed** (`evolve/timing.py`). The report gives each cell's MHz range and median, and flags any cell whose median differs from the reference's by more than 10%.
- **TCPU above ~90 °C is flagged:** the guard prints a flag and puts it in the commit message, and the report states it. No system setting (governor, cooling) is changed; that is the user's call.

## Model against card

- Wolfram and other model outputs are forecasts, recorded as "model" and never scored as predictions.
- Sealed predictions about a model run go in `wolfram/<date>_<name>.pred.md`, committed before the run.

## Records

- **NOTES.md is append-only.** Corrections are new entries; superseded items are marked in place, never deleted.
- **IDEAS.md IDs are fixed:** a new idea takes the next free number, and nothing is renumbered.
- **Documentation addenda go in their own commits,** separate from step commits, and commit messages say "documentation only" where true.
- **Git:** explicit `git add` only (never `commit -a`), and never push: the user pushes.

## Guard self-test (2026-10-26)

- Predictions file `predictions/guard-selftest.md` (d7ceaf5).
- The guard refused, as it should: an uncommitted predictions file, a missing file, a file edited after its commit, and `--deepseek` with no reply on file.
- It ran and committed: ed34500 (ok) and 9477742 (a failing command, committed as FAILED).
- **Bug found:** two runs in the same second shared one output name, so 9477742 overwrote ed34500's output file. Fixed so that a name is never reused (39c838e and 6950a1d ran after the fix).
- The `--deepseek` path that should pass is untested until a real reply is committed.

## Replications on other machines (friend runs and contributors' timings)

- **Kit:** `tools/friend_setup.sh` (setup and self-test), `tools/friend_run.sh <run-name>` (cells from a committed `runs/<run-name>.json`) and `tools/contribute_timing.sh`. Plain-English guide: FRIEND.md.
- **A friend run is a replication, labelled by machine** (host, CPU model, cores, OS, taskset or not). It times the same cells, numbers, seed and commit as the run file names. friend_run.sh refuses to run with local changes to tracked files, and the results record the git HEAD.
- **Ratios are compared within a machine.** Results from different machines are never pooled, averaged or set side by side as one figure without saying so explicitly in the report.
- **Scoring:** a friend run is scored only against predictions sealed for that run (its own predictions file, committed before the run file is sent out). Otherwise it is information.
- **The user commits the returned file** (results/, with the machine named in the commit message). Claude Code does not request, fetch or upload results files.
- A contributor's `tools/contribute_timing.sh` output is information only, never a sealed result.

## Frequency cap (standing condition from Oct 26, 2026)

- **The user keeps the CPU capped at 2.4 GHz** (scaling_max_freq). Claude Code never sets, changes or removes it.
- **Comparability:** timed runs from i032-2prime onward are at 2.4 GHz and comparable across runs. Earlier timed runs (uncapped, throttling at 98–100 °C) are not comparable with them, nor reliably with each other.
- **Before every timed run** the machine state is checked. If the cap is absent (scaling_max_freq above 2,400 MHz on the pinned core, for example after a reboot), **STOP and tell the user.** The check is made by Claude Code before launching; sealed_run.sh records the limits in the machine state but does not yet enforce the cap.
- **Interval predictions from now on assume the cap.**
