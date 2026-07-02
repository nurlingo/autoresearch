#!/usr/bin/env bash
# Collect one finished Study 1 run from its isolated clone: archive the log +
# full experiment history (git bundle), and delete the clone.
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
BUNDLE="${ROOT}/runs/${AGENT}-r${K}-${TAG}.bundle"
PYTHON="$(pyenv which python 2>/dev/null || command -v python3)"

[ -f "$DIR/results.tsv" ] || { echo "no results.tsv in $DIR"; exit 1; }
cp "$DIR/results.tsv" "$OUT"

best=$(tail -n +2 "$OUT" | awk -F'\t' '$10!="crash"{print $6}' | sort -g | head -1)
echo "best research_score: $best"

# Preserve the full per-experiment history (the dataset is gitignored in the
# clone, so the bundle contains no user data), then remove the clone.
git -C "$DIR" bundle create -q "$BUNDLE" --all
rm -rf "$DIR"
echo "collected -> $(basename "$OUT") + $(basename "$BUNDLE")  (clone removed)"
