#!/usr/bin/env bash
# Spin up an ISOLATED worktree for one autoresearch run.
#
#   TAG=260629 tools/new_run.sh claude 1
#
# Creates ../ar-runs/<tag>-<agent>-r<k> on a fresh branch from main, starting from
# the pristine stub, with the frozen dataset copied in and hash-verified. Each run
# is fully isolated: its own working tree, branch, results.tsv and data copy.
set -euo pipefail

AGENT="${1:?usage: new_run.sh <agent: claude|codex> <k>}"
K="${2:?usage: new_run.sh <agent> <k>}"
TAG="${TAG:-$(date +%y%m%d)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${TAG}-${AGENT}-r${K}"
DIR="${ROOT}/../ar-runs/${NAME}"
BRANCH="ar/${NAME}"

cd "$ROOT"
git worktree add -b "$BRANCH" "$DIR" main >/dev/null
mkdir -p "$DIR/data"
cp data/bot_review.csv "$DIR/data/bot_review.csv"   # gitignored → not in the worktree

# Verify the run's inputs match the frozen study hash, if one exists.
if [ -f runs/inputs.sha256 ]; then
  ( cd "$DIR" && shasum -a 256 -c "${ROOT}/runs/inputs.sha256" ) \
    || { echo "!! HASH MISMATCH in $DIR — aborting"; exit 1; }
fi

cat <<EOF

worktree: $DIR
branch:   $BRANCH

Launch (full-auto, isolated to this dir):
  cd "$DIR"
  AR_AGENT=$AGENT <agent-launch-cmd> \\
    "Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour, whichever first. Do not push."

  claude:  claude --dangerously-skip-permissions
  codex:   codex --full-auto        # sandboxed workspace-write
EOF
