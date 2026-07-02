#!/usr/bin/env bash
# Collect one finished Study 2 run from its isolated clone: score the final
# solution on the HELD-OUT test set, archive the log + full experiment history
# (git bundle), and delete the clone.
#
#   TAG=260702 tools/collect_run.sh claude 1
set -euo pipefail

AGENT="${1:?usage: collect_run.sh <agent> <k>}"
K="${2:?usage: collect_run.sh <agent> <k>}"
TAG="${TAG:-$(date +%y%m%d)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${TAG}-${AGENT}-r${K}"
DIR="${ROOT}/../ar-runs/${NAME}"
OUT="${ROOT}/runs/${AGENT}-r${K}-${TAG}.tsv"
HOLDOUT="${ROOT}/runs/${AGENT}-r${K}-${TAG}-holdout.json"
BUNDLE="${ROOT}/runs/${AGENT}-r${K}-${TAG}.bundle"
PYTHON="$(pyenv which python 2>/dev/null || command -v python3)"

[ -f "$DIR/results.tsv" ] || { echo "no results.tsv in $DIR"; exit 1; }
cp "$DIR/results.tsv" "$OUT"

# Held-out scoring: the clone's final solution vs the test split the agent
# never had access to.
( cd "$DIR" && "$PYTHON" eval.py --csv "$ROOT/data/test.csv" --json > "$HOLDOUT" )
train_best=$(tail -n +2 "$OUT" | awk -F'\t' '$10!="crash"{print $6}' | sort -g | head -1)
test_score=$("$PYTHON" -c "import json;print(json.load(open('$HOLDOUT'))['summary']['research_score'])")
echo "train best: $train_best   heldout test: $test_score"

# Preserve the full per-experiment history (train.csv is gitignored in the
# clone, so the bundle contains no user data), then remove the clone.
git -C "$DIR" bundle create -q "$BUNDLE" --all
rm -rf "$DIR"
echo "collected -> $(basename "$OUT") + $(basename "$HOLDOUT") + $(basename "$BUNDLE")  (clone removed)"
