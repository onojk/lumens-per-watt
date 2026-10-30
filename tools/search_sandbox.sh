#!/usr/bin/env bash
# tools/search_sandbox.sh EXPERIMENT -- COMMAND [ARGS...]
#
# Runs a search (the proposer) where it can neither touch the judge nor see held-out data (design
# docs/planning/arrangement_lamps.md §6; DeepSeek's items 2 and b1-b2, Oct 30):
#   1. a detached git worktree of HEAD at ../lpw-search-<EXPERIMENT>-<HEAD>, with the pinned lampcore binary copied in
#      (target/ is not in git); refused if the main repo has uncommitted changes to any judge file;
#   2. the worktree's judge files are checked against the last pin in predictions/EXPERIMENT.md (tools/judge.py;
#      pending entries are allowed here and nowhere else), then made read-only (chmod a-w), with the judge's dirs;
#   3. training data only: the sandbox's file system is /usr (read-only), a private /tmp, /proc and /dev, and under
#      /lpw ONLY the allow-listed files below (SEARCH_FILES: the search, the meter it runs, its prices and the
#      binary), read-only, in the repo's layout, plus /lpw/search_out (<worktree>/search_out, the only writable
#      path; also $LPW_SEARCH_OUT). No /home, no repo, no predictions, docs, NOTES or results. Each allow-listed file
#      is checked for the held-out seeds (an integer 993[05]0xx: arrangement-v1's validation maps); a match refuses
#      the run. The training seeds are in the search's own code;
#   4. COMMAND runs from /lpw/evolve under bwrap with a clean environment (only PATH, HOME=/tmp, LPW_SEARCH_OUT,
#      PYTHONDONTWRITEBYTECODE; no LD_PRELOAD or anything else inherited), in new PID, network, IPC and UTS
#      namespaces, a new session, dying with its parent. It runs in its own process group (setsid), whose id is
#      written to <worktree>/.search.pgid; when COMMAND ends, the whole group is killed (SIGKILL) before this script
#      returns, and tools/score_sandbox.sh kills it again before any scoring.
# The proposer runs as the same user, so the mounts, not the file modes, are what stop it. The pins catch any change
# to the judge whatever its route: sealed_run.sh checks them before and after every scored run. Never commits.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"

[ $# -ge 3 ] && [ "$2" = "--" ] || { echo "usage: $0 EXPERIMENT -- COMMAND [ARGS...]" >&2; exit 2; }
exp=$1; shift 2
[[ "$exp" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "experiment ID must be [A-Za-z0-9._-]+" >&2; exit 2; }
command -v bwrap >/dev/null || { echo "REFUSED: bwrap is not installed; the search may not run unsandboxed" >&2; exit 1; }

SEARCH_FILES=(
    evolve/arr_search.py evolve/arr_price.py
    evolve/lamps.py evolve/arr.py evolve/fastlamps.py evolve/optypes.py evolve/gcdscale.py
    evolve/qs.py evolve/cfrac.py evolve/ecm.py evolve/race.py evolve/ledger.py evolve/blockflash.py
    evolve/calibrate.json opclass/opclass_v1.json bench/gcdbench/gcd_ir.json
    lampcore/target/release/lampcore
)
HELD_OUT='(?<![0-9.])993[05]0[0-9]{2}(?![0-9])'

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

mounts=()
for f in "${SEARCH_FILES[@]}"; do
    [ -f "$wt/$f" ] || { echo "REFUSED: allow-listed file $f is missing from the worktree" >&2; exit 1; }
    if grep -qaP "$HELD_OUT" "$wt/$f"; then
        echo "REFUSED: allow-listed file $f contains a held-out seed (993[05]0xx); the search may not see it" >&2; exit 1
    fi
    mounts+=(--ro-bind "$wt/$f" "/lpw/$f")
done

out=$wt/search_out
echo "running (sandboxed; training data only; mounted: ${#SEARCH_FILES[@]} allow-listed files; writable: $out): $*"
set +e
setsid bwrap --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --symlink usr/bin /bin \
    --symlink usr/sbin /sbin --ro-bind /etc/ld.so.cache /etc/ld.so.cache --proc /proc --dev /dev --tmpfs /tmp \
    --dir /lpw "${mounts[@]}" --bind "$out" /lpw/search_out \
    --unshare-pid --unshare-net --unshare-ipc --unshare-uts --die-with-parent --new-session \
    --clearenv --setenv PATH /usr/bin:/bin --setenv HOME /tmp --setenv PYTHONDONTWRITEBYTECODE 1 \
    --setenv LPW_SEARCH_OUT /lpw/search_out --chdir /lpw/evolve -- "$@" &
pg=$!
echo "$pg" > "$wt/.search.pgid"
wait "$pg"
rc=$?
kill -KILL -- "-$pg" 2>/dev/null
pgrep -g "$pg" >/dev/null && { echo "FAILED: processes of the search's group $pg survived the kill" >&2; rc=1; }
echo "search ended (exit $rc); its process group $pg killed"
exit $rc
