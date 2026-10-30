#!/usr/bin/env bash
# tools/sealed_run.sh EXPERIMENT [--deepseek] -- COMMAND [ARGS...]
#
# Runs COMMAND only if the experiment's predictions were sealed first (PROTOCOL.md):
#   (a) predictions/EXPERIMENT.md exists, is committed, and has no uncommitted changes (staged or not), so its
#       content is exactly what an earlier commit recorded;
#   (b) with --deepseek: some reviews/deepseek_r*.md that mentions EXPERIMENT is committed and clean.
# Then it runs COMMAND from the repo root, saves stdout and stderr to results/EXPERIMENT_<UTC time>.out, and commits
# that file and the machine state before and after (results/EXPERIMENT_<UTC time>.machine.txt, tools/machine_state.sh)
# alone (explicit git add), naming the prediction commit (and the DeepSeek commit). A failing command is
# committed too, with its exit code in the message: failures are results. Never pushes.
# Judge pins (design docs/planning/arrangement_lamps.md §6): if predictions/EXPERIMENT.md carries a "## Judge pins"
# block, tools/judge.py check runs twice, before COMMAND and again after it, before the result is committed; both
# reports head the result file. A mismatch before the run skips COMMAND; a mismatch at either check makes the run a
# failure, committed as a result. Pending pins fail (a scored run needs every judge file pinned). With pins, COMMAND
# must be tools/score_sandbox.sh or tools/search_sandbox.sh (refused otherwise, before anything runs).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

[ $# -ge 3 ] || { echo "usage: $0 EXPERIMENT [--deepseek] -- COMMAND [ARGS...]" >&2; exit 2; }
exp=$1; shift
need_ds=0
if [ "$1" = "--deepseek" ]; then need_ds=1; shift; fi
[ "$1" = "--" ] || { echo "expected -- before the command" >&2; exit 2; }
shift
[[ "$exp" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "experiment ID must be [A-Za-z0-9._-]+" >&2; exit 2; }

clean_committed() {   # $1 path: prints its last commit if tracked, committed and clean; else fails
    local f=$1
    git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 || return 1
    git diff --quiet -- "$f" || return 1
    git diff --cached --quiet -- "$f" || return 1
    git log -1 --format=%h -- "$f"
}

pred=predictions/$exp.md
[ -f "$pred" ] || { echo "REFUSED: $pred does not exist" >&2; exit 1; }
pc=$(clean_committed "$pred") || { echo "REFUSED: $pred is not committed, or has uncommitted changes" >&2; exit 1; }
echo "predictions: $pred, sealed in $pc ($(git log -1 --format='%ci' "$pc"))"

dsnote=""
if [ $need_ds = 1 ]; then
    found=""
    for f in $(grep -lF -- "$exp" reviews/deepseek_r*.md 2>/dev/null | grep -v '\.prompt\.md$' || true); do
        if c=$(clean_committed "$f"); then found="$f $c"; fi
    done
    [ -n "$found" ] || { echo "REFUSED: no committed DeepSeek reply in reviews/ mentions $exp" >&2; exit 1; }
    echo "DeepSeek: $found"
    dsnote="; DeepSeek ${found#* } (${found%% *})"
fi

mkdir -p results
out=results/${exp}_$(date -u +%Y%m%dT%H%M%SZ).out
i=1
while [ -e "$out" ]; do out=results/${exp}_$(date -u +%Y%m%dT%H%M%SZ)_$i.out; i=$((i + 1)); done   # never overwrite a result
ms=${out%.out}.machine.txt
{ echo "## before"; tools/machine_state.sh; } > "$ms"      # the machine's state, saved beside the result
grep -q "governor: powersave" "$ms" && echo "NOTE: the CPU governor is powersave (not changed; the user's call)"
pinned=0
grep -qF -- '<!-- judge-pins begin -->' "$pred" && pinned=1
if [ $pinned = 1 ] && [ "$1" != tools/score_sandbox.sh ] && [ "$1" != tools/search_sandbox.sh ]; then
    echo "REFUSED: a pinned experiment runs only through tools/score_sandbox.sh (scoring) or tools/search_sandbox.sh (the search)" >&2
    exit 1
fi
judge_fail=""
set +e
if [ $pinned = 1 ]; then
    { echo "## judge check 1 (before the run)"; python3 tools/judge.py check "$exp"; } > "$out" 2>&1
    [ $? = 0 ] || judge_fail="judge check before the run"
else
    : > "$out"
fi
if [ -z "$judge_fail" ]; then
    echo "running: $*  ->  $out"
    "$@" >> "$out" 2>&1
    rc=$?
else
    echo "NOT RUN: the judge does not match its pins (see $out)"
    rc=1
fi
if [ $pinned = 1 ]; then
    { echo; echo "## judge check 2 (after the run, before the result is committed)"; python3 tools/judge.py check "$exp"; } >> "$out" 2>&1
    if [ $? != 0 ]; then judge_fail="${judge_fail:+$judge_fail and }judge check after the run"; rc=1; fi
fi
set -e
{ echo; echo "## after"; tools/machine_state.sh; } >> "$ms"
hot=$(awk '/^temperature TCPU:/ {if ($3 + 0 > 90) print $3}' "$ms" | tr '\n' ' ')
[ -n "$hot" ] && echo "FLAG: TCPU above 90 C during the run (readings: $hot C); see $ms"
status="ok"; [ $rc = 0 ] || status="FAILED (exit $rc)"
[ -n "$judge_fail" ] && status="FAILED: judge mismatch ($judge_fail)"
[ -n "$hot" ] && status="$status; TCPU above 90 C ($hot C)"
git add -f -- "$out" "$ms"
git commit -q -m "Sealed run $exp: $status; predictions $pc$dsnote

Command: $*
Output: $out
Machine state: $ms

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$out" "$ms"
echo "$status; committed $(git log -1 --format=%h) ($out)"
exit $rc
