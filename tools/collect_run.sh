#!/usr/bin/env bash
# Collect one finished Study 2 run: score the final solution on the HELD-OUT
# test set, save both artifacts into runs/, and tear down the worktree.
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
PYTHON="$(pyenv which python 2>/dev/null || command -v python3)"

[ -f "$DIR/results.tsv" ] || { echo "no results.tsv in $DIR"; exit 1; }
cp "$DIR/results.tsv" "$OUT"

# Held-out scoring: run the worktree's final solution against the test split.
# (test.csv lives only in the main repo; the agent never saw it.)
( cd "$DIR" && "$PYTHON" eval.py --csv "$ROOT/data/test.csv" --json > "$HOLDOUT" )
train_best=$(tail -n +2 "$OUT" | awk -F'\t' '$10!="crash"{print $6}' | sort -g | head -1)
test_score=$("$PYTHON" -c "import json;print(json.load(open('$HOLDOUT'))['summary']['research_score'])")
echo "train best: $train_best   heldout test: $test_score"

git -C "$ROOT" worktree remove "$DIR" --force
echo "collected -> runs/$(basename "$OUT") + $(basename "$HOLDOUT")  (worktree removed; branch ar/$NAME kept)"
