#!/usr/bin/env bash
# Spin up a FULLY ISOLATED, single-commit clone for one Study 2 run.
#
#   TAG=260702 tools/new_run.sh claude 1
#
# The run directory is a fresh `git init` repo containing ONLY the harness
# snapshot + the train split. No shared git database, no other branches, no
# prior run logs, no held-out test set — there is nothing to leak. (Worktrees
# were abandoned after an agent read sibling branches through the shared .git.)
set -euo pipefail

AGENT="${1:?usage: new_run.sh <agent> <k>}"
K="${2:?usage: new_run.sh <agent> <k>}"
TAG="${TAG:-$(date +%y%m%d)}"
SRC_REF="${SRC_REF:-study2}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${TAG}-${AGENT}-r${K}"
DIR="${ROOT}/../ar-runs/${NAME}"

[ -e "$DIR" ] && { echo "!! $DIR already exists"; exit 1; }
mkdir -p "$DIR"

# Snapshot the committed harness (never the possibly-dirty working tree).
git -C "$ROOT" archive "$SRC_REF" -- \
    PROGRAM.md CLAUDE.md AGENTS.md Makefile eval.py solution.py \
    requirements.txt .python-version .gitignore \
    tools/log_experiment.py tools/plot.py data/quran_ref.json \
  | tar -x -C "$DIR"
cp "$ROOT/data/train.csv" "$DIR/data/train.csv"   # gitignored inside the clone

# Verify the run's visible inputs match the frozen study hash.
if [ -f "$ROOT/runs/worktree.sha256" ]; then
  ( cd "$DIR" && shasum -a 256 -c "$ROOT/runs/worktree.sha256" ) \
    || { echo "!! HASH MISMATCH in $DIR — aborting"; exit 1; }
fi

# Fresh, history-free repo: one branch, one commit.
# (git init -b needs 2.28+; checkout -b works on older git)
git -C "$DIR" init -q
git -C "$DIR" checkout -b run
git -C "$DIR" add -A
git -C "$DIR" -c user.name=autoresearch -c user.email=autoresearch@local \
  commit -q -m "autoresearch experiment snapshot"

cat <<EOF

run dir: $DIR   (fresh clone, branch 'run', single commit)

Launch (full-auto, isolated to this dir):
  cd "$DIR"
  claude:  AR_AGENT=claude claude --dangerously-skip-permissions "<prompt>"
  codex:   AR_AGENT=codex  codex -s workspace-write -a never \\
             -c model_reasoning_effort="high" "<prompt>"
           (no --add-dir needed: the clone owns its .git)

  prompt:  Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour,
           whichever first. Do not push.
EOF
