# Experiment protocol

1. **Predictions.** Write `predictions/<experiment>.md`: each prediction is "under X, Y will be Z × baseline B on metric M", with ranges and, where useful, falsifiers.
2. **Commit** the predictions file (documentation only).
3. **DeepSeek ask.** Run `tools/ask_deepseek.py <prompt>`. It prepends `reviews/card_params.md`, the measured parameter sheet. The reply lands in `reviews/deepseek_rNN.md`, and its sealed predictions must name the experiment ID.
4. **Commit** the reply and its prompt.
5. **Run.** Use `tools/sealed_run.sh <experiment> [--deepseek] -- <command>`. It refuses unless step 2 (and step 4 with `--deepseek`) is committed and unchanged, then runs the command, saves `results/<experiment>_<time>.out` and commits it, naming the prediction commit.
6. **Score** every prediction as written, in NOTES.md, and **commit**. Never restate a prediction afterwards. Failures are results.

- **Wolfram runs** follow the same order: `wolfram/<date>_<name>.pred.md` is committed before `wolframscript -file wolfram/<date>_<name>.wl` runs (see `wolfram/README.md`).
- **Decisions are always the user's:** adopting a change, retuning genes, changing the reference, and every push. Claude reports; it does not adopt, retune or push.

**Guard self-test (2026-10-26):** `predictions/guard-selftest.md` (d7ceaf5).
- Refused as it should: an uncommitted predictions file, a missing file, a file edited after its commit, and `--deepseek` with no reply on file.
- Ran and committed: ed34500 (ok) and 9477742 (a failing command, committed as FAILED).
- **Bug found:** two runs in the same second shared one output name, so 9477742 overwrote ed34500's output file. Fixed so that a name is never reused (39c838e, 6950a1d ran after the fix).
- The `--deepseek` path that should pass is untested until a real reply is committed.
