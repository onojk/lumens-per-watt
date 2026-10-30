#!/usr/bin/env bash
# tools/search_sandbox.sh EXPERIMENT -- COMMAND [ARGS...]
#
# Runs a search (the proposer) where it cannot touch the judge (design docs/planning/arrangement_lamps.md §6):
#   1. a detached git worktree of HEAD at ../lpw-search-<EXPERIMENT>-<HEAD>, with the pinned lampcore binary copied in
#      (target/ is not in git); refused if the main repo has uncommitted changes to any judge file;
#   2. the worktree's judge files are checked against the last pin in predictions/EXPERIMENT.md (tools/judge.py;
#      pending entries, such as a scoring harness not yet written, are allowed here and nowhere else), then made
#      read-only (chmod a-w), with the judge's directories;
#   3. COMMAND runs from the worktree's evolve/ under bwrap: the whole file system read-only except the output
#      directory <worktree>/search_out (bound writable; also $LPW_SEARCH_OUT), a private /tmp, no network, LAMPCORE
#      unset. The search's only output is what it writes there (genome files).
# The sandbox is the guard's minimum: the proposer runs as the same user, so the read-only mounts, not the file modes,
# are what stops it. The pins catch any change to the judge whatever its route: sealed_run.sh checks them before and
# after every scored run. Never commits, never pushes.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"

[ $# -ge 3 ] && [ "$2" = "--" ] || { echo "usage: $0 EXPERIMENT -- COMMAND [ARGS...]" >&2; exit 2; }
exp=$1; shift 2
[[ "$exp" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "experiment ID must be [A-Za-z0-9._-]+" >&2; exit 2; }
command -v bwrap >/dev/null || { echo "REFUSED: bwrap is not installed; the search may not run unsandboxed" >&2; exit 1; }

mapfile -t judge < <(python3 tools/judge.py paths "$exp")
[ ${#judge[@]} -gt 0 ] || { echo "REFUSED: predictions/$exp.md has no judge pins" >&2; exit 1; }
bin=lampcore/target/release/lampcore
for f in "${judge[@]}"; do
    [ "$f" = "$bin" ] && continue
    [ -e "$f" ] || continue                                  # a pending file: judge.py check reports it
    git diff --quiet HEAD -- "$f" || { echo "REFUSED: $f has uncommitted changes" >&2; exit 1; }
done

head=$(git rev-parse --short HEAD)
wt=$(dirname "$root")/lpw-search-$exp-$head
if [ ! -d "$wt" ]; then
    git worktree add --detach "$wt" HEAD >/dev/null
    mkdir -p "$wt/lampcore/target/release" "$wt/search_out"
    cp "$bin" "$wt/$bin"
fi
echo "worktree: $wt (HEAD $head)"
python3 "$wt/tools/judge.py" check "$exp" --allow-pending
for f in "${judge[@]}"; do [ -e "$wt/$f" ] && chmod a-w "$wt/$f"; done
for d in lampcore lampcore/src lampcore/target/release evolve opclass reviews predictions tools; do chmod a-w "$wt/$d"; done

out=$wt/search_out
echo "running (sandboxed; writable: $out only): $*"
exec bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --ro-bind "$wt" "$wt" --bind "$out" "$out" \
    --unshare-net --die-with-parent --unsetenv LAMPCORE --setenv PYTHONDONTWRITEBYTECODE 1 \
    --setenv LPW_SEARCH_OUT "$out" --chdir "$wt/evolve" -- "$@"
