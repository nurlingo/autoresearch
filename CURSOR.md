# Running the autoresearch arm with Cursor

Instructions for running the same experiments (Study 1 and Study 2) with **Cursor
Agent** as an additional agent arm. The harness is agent-agnostic: you change
nothing in the repo — you only launch a different agent inside a run folder.

## What you need

1. **Repo access** — collaborator on `nurlingo/autoresearch`, cloned locally.
2. **The dataset** — received privately from the team:
   - Study 1 (`main`): `data/bot_review.csv`
   - Study 2 (`study2`): `data/train.csv` + `data/test.csv` (test is for
     held-out scoring only — never placed in the run clone)
3. **Verify hashes** before any run:
   ```bash
   git checkout study2
   shasum -a 256 -c runs/inputs.sha256
   shasum -a 256 -c runs/worktree.sha256
   ```
4. **Cursor** in **Auto mode** (model routing left to Cursor — not a manually
   pinned model) with **auto-run / YOLO** enabled (no per-action approval) —
   counterpart to Claude `--dangerously-skip-permissions` and Codex
   `--full-auto`.

## The one non-negotiable: full autonomy, isolated folder

The agent must run **without approval prompts** and **only inside the run
folder** that the tooling creates. Run folders are **fresh single-commit
clones** — their git history contains nothing but the harness snapshot + train
split, so there are no sibling branches, prior run logs, or test set to read.

**Open ONLY the run folder as the Cursor workspace** — never the main repo
clone (which contains `runs/`, other agents' bundles, and `data/test.csv`).

Sanity-check before a real run, inside the run folder:

```bash
git log --oneline          # exactly ONE commit
ls runs/ 2>/dev/null       # must not exist
ls data/                   # quran_ref.json + train.csv only (Study 2)
```

## Study 2 (held-out — current paper focus)

```bash
cd autoresearch && git checkout study2
shasum -a 256 -c runs/inputs.sha256
shasum -a 256 -c runs/worktree.sha256
export TAG=$(date +%y%m%d) AR_AGENT=cursor
tools/new_run.sh cursor 1          # -> ../ar-runs/<tag>-cursor-r1
```

Open `../ar-runs/<tag>-cursor-r1` as the **only** Cursor workspace. Give the
agent exactly this prompt (verbatim):

> Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour, whichever
> first. Do not push.

Before it starts: `export AR_AGENT=cursor` (stamped on every `make exp` row).

When the agent reports done:

```bash
cd autoresearch
TAG=<tag> tools/collect_run.sh cursor 1   # train best + heldout test
```

Repeat for runs 2 and 3. **Each run = one uninterrupted session.**

## Study 1 (full dataset — optional / historical)

```bash
git checkout main
export TAG=$(date +%y%m%d) AR_AGENT=cursor SRC_REF=main
# temporarily copy bot_review.csv into data/ and verify runs/inputs.sha256
tools/new_run.sh cursor 1
```

(Study 1 `new_run.sh` on `main` uses `bot_review.csv`; Study 2 default uses
`train.csv`.)

## What to send back (per run)

- `runs/cursor-r<k>-<tag>.tsv` + `-holdout.json` + `.bundle` (from
  `collect_run.sh`)
- Cursor version, **Auto mode** (record that routing was Auto, not a fixed model),
  auto-run/YOLO settings, machine OS/CPU for the confounds table

**Recorded (Study 2 runs, TAG=260702):** Cursor Agent, **Auto mode**, auto-run
enabled; same Linux machine as the other arms. Auto mode means the underlying
model may vary by step — report Cursor app version and date; do not assume a
single pinned model id like Claude/Codex/Antigravity.

## Rules (same as every arm)

- Do not hint approaches, point at failures, or intervene mid-run.
- Do not edit `eval.py`, `data/`, `PROGRAM.md`, or the budget.
- Do not read `runs/` or other agent branches in the main repo during a run.
