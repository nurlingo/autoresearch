#!/usr/bin/env bash
# Spin up an ISOLATED worktree for one Study 2 autoresearch run.
#
#   TAG=260702 tools/new_run.sh claude 1
#
# Creates ../ar-runs/<tag>-<agent>-r<k> on a fresh branch from study2, starting
# from the pristine stub, with ONLY the train split copied in (the held-out
# test set never enters the worktree). Inputs are hash-verified.
set -euo pipefail

AGENT="${1:?usage: new_run.sh <agent: claude|codex> <k>}"
K="${2:?usage: new_run.sh <agent> <k>}"
TAG="${TAG:-$(date +%y%m%d)}"
BASE_REF="${BASE_REF:-study2}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${TAG}-${AGENT}-r${K}"
DIR="${ROOT}/../ar-runs/${NAME}"
BRANCH="ar/${NAME}"

cd "$ROOT"
git worktree add -b "$BRANCH" "$DIR" "$BASE_REF" >/dev/null
mkdir -p "$DIR/data"
cp data/train.csv "$DIR/data/train.csv"   # gitignored → not in the worktree checkout
# The held-out test.csv is deliberately NOT copied.

# Verify the run's visible inputs match the frozen study hash, if present.
if [ -f runs/worktree.sha256 ]; then
  ( cd "$DIR" && shasum -a 256 -c "${ROOT}/runs/worktree.sha256" ) \
    || { echo "!! HASH MISMATCH in $DIR — aborting"; exit 1; }
fi

cat <<EOF

worktree: $DIR
branch:   $BRANCH   (from $BASE_REF)

Launch (full-auto, isolated to this dir):
  cd "$DIR"
  AR_AGENT=$AGENT <agent-launch-cmd> \\
    "Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour, whichever first. Do not push."
EOF
