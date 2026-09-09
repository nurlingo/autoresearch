# autoresearch

## MusIML submission work — 2026-09-09

The revised Track 3 proposal concerns final-solution event annotation, with
127 unlabelled training cases and a private gold100. The training release bundle
itself is not published here: redistribution scope for the newly collected
recordings is unsettled, so it is shared directly with colleagues instead.
Rebuild it from private sources with `study3/tools/build_train_release.py`.
See the [submission checklist](study3/SUBMISSION-TODO.md),
[teaching examples for approval](study3/calibration/teaching-review.html), and
[agent-comparison protocol](study3/EXPERIMENT.md). The historical Task A release
is a different task; it does not supply the new event-annotation training split.


Karpathy-style autoresearch loop for the **Follow My Reading** recitation
algorithm. Goal: a transcript-only memorization checker for Quran reciters that
(1) detects which ayahs were recited, (2) splits the transcript by ayah, and
(3) labels transcript/reference differences under a human-reviewed rubric (Study 3; gold review complete).

The root directory contains the **Stage 1 fixed harness**: a frozen dataset
and scorecard plus an editable algorithm. Study 3 adds an annotation protocol
and legacy pilot artifacts alongside it. This authoring checkout is not an
isolated agent runtime; prepare a separate allowed-data bundle for each run.
Study 3 evaluator v2.1 and rerun baselines are available; matching tolerances and
the agent experiment design remain provisional. See [evaluation](study3/EVALUATOR.md)
and [the isolated experiment plan](study3/EXPERIMENT.md).

## Two stages

| Stage | Input | Output | Status |
| --- | --- | --- | --- |
| **1. Detect + split** | full transcript | ayahs recited + per-ayah split | **active** (this harness) |
| **2. Event annotation** | reviewed ayah chunks + IDs + Quran reference | combined event labels and spans | Study 3: 100/100 approved; v2.1 baselines; no agent runs |

In production, Stage 2 consumes Stage 1's output. The Study 3 evaluation
supplies reviewed splits to isolate event annotation from detection errors.
Study 3 now has a completed v0.19 rubric and 100 approved recordings (314 chunks). The
new experiment asks the agent to annotate its own unlabelled development pool
and build an algorithm, with final code evaluated privately. The old pilot
harness is not the new contract. See [methodology](METHODOLOGY-STUDY3.md) and
[annotation findings](docs/STUDY3-ANNOTATION.md).

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
- **METHODOLOGY-STUDY3.md** — Stage 2 (within-ayah mistake detection): dataset
  and experiment design (100/100 recordings approved; current protocol, no runs).

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
  OpenAI ASR and reviewed (ayah assignment + per-ayah split + confidence) using the
  review tooling in the `follow_my_reading` repo (`make bot-review-*`). It
  contains real user-derived transcripts and learner ids, so it is **gitignored**.
  Regenerate it there with `make bot-review-export-csv` and copy it into `data/`.
- `data/quran_ref.json` — slim reference (id + uthmani + harakat-free `clean`)
  derived from `follow_my_reading/backend/quran.json`. Public text, committed.

Current dataset: 258 reviewed rows (254 Quran, 4 non-Quran). Non-contiguous
recitations use comma-separated ayah ids in `ayah_assignment`.
```
baseline (empty stub):   research_score 2.00
oracle (gold fed back):  research_score 0.00
```

## Study 3 preparation

The [preparation guide](study3/README.md) links the draft annotation instructions,
20 constructed Arabic teaching examples, and the latest aggregate recording
inventory. Teaching annotations await review; gold answers and production
exports remain private.
