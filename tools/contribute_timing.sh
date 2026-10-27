#!/usr/bin/env bash
# tools/contribute_timing.sh [RUN-NAME]: a contributor's short timed check (CONTRIBUTING.md). Runs the reference and the
# current candidate cells (runs/contribute.json by default: 640 numbers at 96 bits, 2 replicates), records the machine
# state (tools/machine_state.sh where it works, plus the machine record friend_timing.py keeps), and writes one results
# file to attach to an issue. Information only: not a sealed run. Uploads nothing.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
run=${1:-contribute}
state=$(mktemp)
{ echo "## before"; tools/machine_state.sh 2>/dev/null || echo "(machine_state.sh unavailable on this system)"; } > "$state"
tools/friend_run.sh "$run"
{ echo; echo "## after"; tools/machine_state.sh 2>/dev/null || true; } >> "$state"
res=$(ls -t results_"$run"_*.json | head -1)
python3 - "$res" "$state" <<'EOF'
import json, sys
res, state = sys.argv[1], sys.argv[2]
d = json.load(open(res))
d["machine_state_sh"] = open(state).read()
json.dump(d, open(res, "w"), indent=1)
EOF
rm -f "$state"
echo "Attach $res to your issue (it is the only file needed)."
