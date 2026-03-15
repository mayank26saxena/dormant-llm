#!/bin/bash
# post_run.sh — Process results after evaluate.py completes.
# Usage: ./post_run.sh <model-short-name> <score> <keep|discard> <description>
# Example: ./post_run.sh dormant-model-3 5.369 keep "Symbol scan: zzz→ingszzz"
#
# Does in one call: moves JSON to model subdir, appends results.tsv, git add + commit.

set -euo pipefail

MODEL="${1:?Usage: ./post_run.sh MODEL SCORE STATUS DESC}"
SCORE="${2:?Usage: ./post_run.sh MODEL SCORE STATUS DESC}"
STATUS="${3:?Usage: ./post_run.sh MODEL SCORE STATUS DESC}"
DESC="${4:?Usage: ./post_run.sh MODEL SCORE STATUS DESC}"

COMMIT=$(git rev-parse --short HEAD)

# Move JSON(s) to model subdirectory
mkdir -p "runs/$MODEL"
for f in runs/*_${MODEL}.json; do
    [ -f "$f" ] && mv "$f" "runs/$MODEL/" && echo "Moved $f → runs/$MODEL/"
done

# Append to results.tsv
printf '%s\t%s\t%s\t%s\t%s\n' "$COMMIT" "$MODEL" "$SCORE" "$STATUS" "$DESC" >> results.tsv

# Git add and commit
git add results.tsv "runs/$MODEL/"
git commit -m "results: $MODEL $STATUS $SCORE — $DESC"

echo "Done. Committed as $(git rev-parse --short HEAD)"
