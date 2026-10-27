#!/usr/bin/env bash
# tools/friend_run.sh RUN-NAME: time the cells listed in the committed run file runs/RUN-NAME.json on this machine
# (FRIEND.md). Writes ONE file, results_RUN-NAME_HOST_DATE.json, in the repo's top folder, and prints a one-screen
# summary. Refuses to run if the repo has local changes to tracked files or the run file is not committed, so the
# results always match a commit. Uploads nothing.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

[ $# -eq 1 ] || { echo "usage: $0 RUN-NAME   (the cells come from runs/RUN-NAME.json)" >&2; exit 2; }
run=$1
[[ "$run" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "the run name must be letters, digits, '.', '_' or '-'" >&2; exit 2; }
rf=runs/$run.json
[ -f "$rf" ] || { echo "REFUSED: $rf does not exist (did you pull the latest version?)" >&2; exit 1; }
git ls-files --error-unmatch -- "$rf" >/dev/null 2>&1 || { echo "REFUSED: $rf is not committed" >&2; exit 1; }
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "REFUSED: this copy of the repo has local changes. Undo them (git stash, or git checkout .) and try again." >&2
    git status --short --untracked-files=no >&2
    exit 1
fi
[ -x lampcore/target/release/lampcore ] || { echo "REFUSED: lampcore is not built; run tools/friend_setup.sh first" >&2; exit 1; }

host=$(hostname | tr -c 'A-Za-z0-9._-\n' '_')
out=results_${run}_${host}_$(date -u +%Y%m%dT%H%M%SZ).json
case "$(uname -s)" in
    Darwin) echo "NOTE: macOS has no taskset, so the run is not pinned to one core; timings will be noisier." ;;
esac
command -v taskset >/dev/null || echo "NOTE: taskset not found; the run is not pinned to one core."
echo "Running '$run' from commit $(git rev-parse --short HEAD). Leave the computer plugged in and idle until it finishes."
(cd evolve && python3 friend_timing.py "../$rf" "../$out")
