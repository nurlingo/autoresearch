# autoresearch

Karpathy-style autoresearch loop for the **Follow My Reading** recitation
algorithm. Goal: a transcript-only memorization checker for Quran reciters that
(1) detects which ayahs were recited, (2) splits the transcript by ayah, and
(later) (3) finds genuine recitation mistakes.

This repo is the **fixed harness**: a frozen dataset + a frozen scorecard, plus a
blank-slate algorithm an agent rewrites from scratch. It is deliberately isolated
from the production app so the algorithm cannot lean on existing code — which also
makes it a clean arena for comparing agents (e.g. **Claude Code vs Codex**): point
each agent at the same loop, compare the `research_score` they reach.

## Two stages

| Stage | Input | Output | Status |
| --- | --- | --- | --- |
| **1. Detect + split** | full transcript | ayahs recited + per-ayah split | **active** (this harness) |
| **2. Mistake detection** | one gold ayah chunk + reference | recitation mistakes | future, separate harness |

The stages are separate because Stage 2 consumes Stage 1's output. Evaluating
Stage 2 on the *gold* split keeps split errors from polluting the mistake score.
Mistakes are still to be defined; Stage 2 needs a gold `mistakes` label that does
not exist yet.

## Layout

```
solution.py          # EDITABLE — the algorithm, start from scratch
eval.py              # FIXED — the scorecard (research_score, lower is better)
PROGRAM.md           # the agent's task spec / loop instructions
results.tsv          # log of kept improvements
data/
  bot_review.csv     # FIXED ground truth — gitignored (production-derived)
  quran_ref.json     # FIXED Quran reference: {surah: [{id, ar, clean}]}
```

## Run

Uses the `env313` pyenv interpreter (Python 3.13 + matplotlib); the Makefile
resolves it via `pyenv which python`. Otherwise `pip install -r requirements.txt`.

```bash
make eval                       # score solution.py against the dataset
make exp DESC="what changed"    # score + append a uniform row to results.tsv
make plot                       # render this run -> progress.png
make archive AGENT=claude       # save run log -> runs/claude-<ts>.tsv
make compare RUNS="runs/claude-*.tsv runs/codex-*.tsv"   # -> comparison.png
```

- **PROGRAM.md** — the loop and the rules on what may/may not change.
- **METHODOLOGY.md** — how to run the Claude-vs-Codex comparison for the paper.

## Launching an agent

```bash
cd autoresearch
export AR_AGENT=claude            # tags every logged row with the agent
claude --dangerously-skip-permissions
# then: "Read PROGRAM.md and kick off a new experiment — do the setup first."
```

`CLAUDE.md` / `AGENTS.md` auto-prime Claude Code / Codex with the same task.

## Data & provenance

- `data/bot_review.csv` — Telegram bot auto-detect recordings, transcribed with
  OpenAI ASR and reviewed (ayah range + per-ayah split + confidence) using the
  review tooling in the `follow_my_reading` repo (`make bot-review-*`). It
  contains real user-derived transcripts and learner ids, so it is **gitignored**.
  Regenerate it there with `make bot-review-export-csv` and copy it into `data/`.
- `data/quran_ref.json` — slim reference (id + uthmani + harakat-free `clean`)
  derived from `follow_my_reading/backend/quran.json`. Public text, committed.

Current dataset: 79 reviewed rows (76 ayah-range, 3 non-Quran). Two rows have
inconsistent labels (split ids vs assigned range) — flagged for re-review; they
cap the achievable score at ~0.03.
```
baseline (empty stub):   research_score 2.00
oracle (gold fed back):  research_score 0.03
```
