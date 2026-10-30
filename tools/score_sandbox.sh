#!/usr/bin/env bash
# tools/score_sandbox.sh EXPERIMENT -- COMMAND [ARGS...]
#
# Runs a scoring command (the judge's harness) in a fresh sandbox (DeepSeek's b1-b2, Oct 30); run it through
# tools/sealed_run.sh, which checks the judge's pins before and after:
#   1. first, every search of EXPERIMENT is stopped: for each ../lpw-search-<EXPERIMENT>-*/.search.pgid written by
#      tools/search_sandbox.sh, the whole process group is killed (SIGKILL) and checked empty; a survivor refuses
#      the run;
#   2. COMMAND runs from the repo root under bwrap: the file system read-only, a private /tmp, /proc and /dev; new PID,
#      network, IPC and UTS namespaces, a new session, dying with its parent; a clean environment (env -i: only
#      PATH=/usr/bin:/bin, HOME=/tmp, LANG=C.UTF-8, PYTHONDONTWRITEBYTECODE=1; no LD_PRELOAD, no LAMPCORE, nothing
#      inherited); in its own process group, killed when COMMAND ends.
# The harness writes only to stdout (sealed_run.sh saves it). Never commits.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"

[ $# -ge 3 ] && [ "$2" = "--" ] || { echo "usage: $0 EXPERIMENT -- COMMAND [ARGS...]" >&2; exit 2; }
exp=$1; shift 2
[[ "$exp" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "experiment ID must be [A-Za-z0-9._-]+" >&2; exit 2; }
command -v bwrap >/dev/null || { echo "REFUSED: bwrap is not installed; scoring may not run unsandboxed" >&2; exit 1; }

for f in "$(dirname "$root")"/lpw-search-"$exp"-*/.search.pgid; do
    [ -f "$f" ] || continue
    pg=$(cat "$f")
    [[ "$pg" =~ ^[0-9]+$ ]] || { echo "REFUSED: $f does not hold a process group id" >&2; exit 1; }
    kill -KILL -- "-$pg" 2>/dev/null || true
    sleep 0.2
    pgrep -g "$pg" >/dev/null && { echo "REFUSED: the search's process group $pg ($f) survived the kill" >&2; exit 1; }
    echo "search process group $pg ($f): none running"
done

binds=(--ro-bind "$root" "$root")                  # the repo and the searches' worktrees stay visible (read-only) even
for d in "$(dirname "$root")"/lpw-search-"$exp"-*; do   # when they live under /tmp, which the sandbox replaces
    [ -d "$d" ] && binds+=(--ro-bind "$d" "$d")
done
echo "scoring (fresh sandbox, clean environment): $*"
set +e
setsid bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp "${binds[@]}" \
    --unshare-pid --unshare-net --unshare-ipc --unshare-uts --die-with-parent --new-session \
    --clearenv --setenv PATH /usr/bin:/bin --setenv HOME /tmp --setenv LANG C.UTF-8 --setenv PYTHONDONTWRITEBYTECODE 1 \
    --chdir "$root" -- "$@" &
pg=$!
wait "$pg"
rc=$?
kill -KILL -- "-$pg" 2>/dev/null
exit $rc
