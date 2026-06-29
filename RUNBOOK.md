# Runbook — executing the Claude vs Codex study

10 runs total: 5 `claude` + 5 `codex`, each 30 experiments or 1 h (whichever
first), each in an isolated git worktree. See METHODOLOGY.md for the why.

## 0. Prerequisites

- `env313` pyenv interpreter (matplotlib); `pyenv which python` resolves it here.
- Claude Code CLI and Codex CLI installed and authenticated.
- Dataset review finished and copied to `data/bot_review.csv`.

## 1. Freeze the dataset (once, before any run)

```bash
make freeze                 # writes runs/inputs.sha256 (data + eval hashes)
make eval                   # record the frozen baseline (stub == 2.0)
```
Commit `runs/inputs.sha256`. Every run is hash-checked against it.

## 2. One run

```bash
export TAG=$(date +%y%m%d)             # one tag for the whole study
tools/new_run.sh claude 1              # isolated worktree + branch + data copy

cd ../ar-runs/$TAG-claude-r1
AR_AGENT=claude claude --dangerously-skip-permissions \
  "Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour, whichever first. Do not push."
```
Codex run is identical with `codex --full-auto` and `AR_AGENT=codex`.

When it finishes (budget or plateau):
```bash
cd -                                   # back to main repo
tools/collect_run.sh claude 1          # -> runs/claude-r1-<tag>.tsv, removes worktree
```

## 3. Run in parallel (isolated)

Each run is a separate worktree + process, so parallelism is safe. It is bounded
by **API rate limits / cost**, not CPU. Use tmux, one pane per run:

```bash
tools/new_run.sh claude 1
tools/new_run.sh codex 1
tmux new -s ar
#  pane 1: cd ../ar-runs/$TAG-claude-r1 && AR_AGENT=claude claude --dangerously-skip-permissions "...loop..."
#  pane 2: cd ../ar-runs/$TAG-codex-r1  && AR_AGENT=codex  codex  --full-auto                    "...loop..."
```
Run a few at a time; collect each as it finishes, then start the next.

## 4. Aggregate

```bash
make compare RUNS="runs/claude-*.tsv runs/codex-*.tsv"   # -> comparison.png
git add runs/ comparison.png && git commit -m "study <tag>: 5x claude vs 5x codex" && git push
```

## YOLO & isolation notes

- **Both agents run full-auto** (no per-action approval) — required for a hands-off
  loop, and equal autonomy avoids a confound. Claude: `--dangerously-skip-permissions`;
  Codex: `--full-auto` (sandboxed workspace-write).
- **Contain the autonomy.** Each run is confined to its worktree dir. For Claude's
  unsandboxed yolo, prefer running inside a container/VM (or a user without access
  to credentials/secrets); keep network to the model API only. This matches
  Codex's built-in sandbox and keeps the two comparable.
- Agents are told **not to push** (CLAUDE.md / AGENTS.md); runs stay local until
  you collect. Don't let two worktrees check out the same branch (the tooling
  names them uniquely, so they can't).
- After the study, prune leftover worktrees: `git worktree prune`. Run branches
  `ar/<tag>-*` are kept for the reproducibility bundle.
