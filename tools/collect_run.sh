#!/usr/bin/env bash
# Collect one finished run's log into the main repo's runs/ and tear down its
# worktree.  TAG=260629 tools/collect_run.sh claude 1
set -euo pipefail

AGENT="${1:?usage: collect_run.sh <agent> <k>}"
K="${2:?usage: collect_run.sh <agent> <k>}"
TAG="${TAG:-$(date +%y%m%d)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${TAG}-${AGENT}-r${K}"
DIR="${ROOT}/../ar-runs/${NAME}"
OUT="${ROOT}/runs/${AGENT}-r${K}-${TAG}.tsv"   # starts with agent → matches compare glob

[ -f "$DIR/results.tsv" ] || { echo "no results.tsv in $DIR"; exit 1; }
cp "$DIR/results.tsv" "$OUT"
git -C "$ROOT" worktree remove "$DIR" --force
echo "collected -> runs/$(basename "$OUT")  (worktree removed; branch ar/$NAME kept)"
