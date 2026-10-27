# Wolfram runs

Wolfram is run from the command line: wolframscript 1.14.0 at `/usr/bin/wolframscript`, kernel Wolfram 15.0.1 under `/usr/local/Wolfram/Wolfram/15.0`, licensed on this machine.

**Convention:**
- Each run is a script, `wolfram/<date>_<name>.wl` (date as YYYY-MM-DD).
- Sealed predictions for a run go in `wolfram/<date>_<name>.pred.md`, committed **before** the run.
- Run it from the repo root with:

  ```
  wolframscript -file wolfram/<date>_<name>.wl > wolfram/<date>_<name>.out 2>&1
  ```

- Commit the `.out` with the script. `*.out` is gitignored repo-wide, so use `git add -f`.
- Scripts print their results with `Print` and read no files outside the repo. Inputs taken from card runs are copied into the script or read from committed files.

`2026-10-26_smoke.wl` checks that the setup works.
