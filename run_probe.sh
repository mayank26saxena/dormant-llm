#!/bin/bash
# run_probe.sh — Full experiment cycle: commit probe, run, wait for result.
# Usage: ./run_probe.sh <probe-file> "<commit message>"
# Example: ./run_probe.sh probe_model1.py "probe: model-1 exp23 — date triggers"
#
# Does in one call: cp probe file, git add + commit, run evaluate.py, print score.

set -euo pipefail

PROBE_FILE="${1:?Usage: ./run_probe.sh PROBE_FILE COMMIT_MSG}"
COMMIT_MSG="${2:?Usage: ./run_probe.sh PROBE_FILE COMMIT_MSG}"

# Copy probe and commit
cp "$PROBE_FILE" probe.py
git add probe.py
git commit -m "$COMMIT_MSG"

# Run and wait
echo "Running evaluate.py with $(python3 -c 'import probe; print(probe.MODEL)'  2>/dev/null || echo $PROBE_FILE)..."
uv run evaluate.py > run.log 2>&1

# Print result
grep "^anomaly_score:" run.log || echo "No anomaly_score found — check run.log"
