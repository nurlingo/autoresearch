# Running an autoresearch iteration on the 194-case corpus

## What the agent sees, and what it does not

The workspace holds inputs and a scorer. The answers stay in the private corpus
and the grader runs **outside** the workspace, printing aggregate metrics and
per-label F1 — never a case id, a transcript or an expected answer.

That separation is the defence against memorisation. Study 1 found Codex
hardcoding 19–41 ayah ids per run, and the harness was what enabled it: the
failure report printed the expected answers, so the agent optimised against a
list rather than the problem. Here there is no such list to read.

## Prepare

```sh
CORPUS=~/Developer/namaz/follow_my_reading/backend/tests/fixtures/bot_review/train_review/granular-corpus/recordings.jsonl
QURAN=~/Developer/namaz/follow_my_reading/backend/tests/fixtures/bot_review/inventory_20260908/train_strict66_snapshot/quran-reference.json
STUDY3=~/Developer/namaz/ar-runs/musiml-annotation-review/study3
RUN=~/ar-runs4/$(date +%y%m%d)-<agent>-<model>

python3 $STUDY3/tools/prepare_agent_run.py \
    --corpus "$CORPUS" --quran "$QURAN" --out "$RUN" --budget "30 minutes"
```

Verify before starting — the workspace must contain exactly six files and no
answers:

```sh
find "$RUN" -type f | sort
grep -rl '"events"' "$RUN" || echo "no answers in workspace"
```

## Isolate

The agent gets its own HOME so its config, credentials and history do not leak
in or out, and no other checkout is reachable.

```sh
mkdir -p "$RUN-home"
export FMR_CORPUS="$CORPUS"
export FMR_GRADER="$STUDY3/tools/grade_workspace.py"
```

`score.py` in the workspace calls the grader through `FMR_GRADER`; the corpus
path is never written into the workspace.

**Claude Code**
```sh
cd "$RUN" && HOME="$RUN-home" FMR_CORPUS="$FMR_CORPUS" FMR_GRADER="$FMR_GRADER" \
  claude --model <model> --permission-mode bypassPermissions \
         -p "$(cat TASK.md)" 2>&1 | tee "$RUN.log"
```

**Codex**
```sh
cd "$RUN" && HOME="$RUN-home" FMR_CORPUS="$FMR_CORPUS" FMR_GRADER="$FMR_GRADER" \
  codex exec --model <model> --sandbox workspace-write "$(cat TASK.md)" 2>&1 | tee "$RUN.log"
```

Record the wall clock — `date +%T` before and after — and keep the log. For a
model comparison, freeze the budget and the model list before starting and run
each model the same number of times.

Stronger isolation, if the machine allows it: run the same command inside a
container with only `$RUN` mounted and no network. The corpus stays outside the
mount; only the grader path crosses in.

## Score and audit

```sh
FMR_CORPUS="$CORPUS" python3 $STUDY3/tools/grade_workspace.py --workspace "$RUN"
FMR_CORPUS="$CORPUS" python3 $STUDY3/tools/grade_workspace.py --workspace "$RUN" --json > "$RUN.score.json"

python3 $STUDY3/tools/audit_solution.py "$RUN/solution.py" --corpus "$CORPUS" --quran "$QURAN"
```

The audit exits non-zero on hardcoded ayah ids, case ids, multi-word literals
that appear in corpus transcripts, or file/network access. Single unusual words
are reported as a note, not a failure — letter names and Uthmani ت-spellings are
legitimate linguistic tables.

Compare several solutions at once:

```sh
python3 $STUDY3/tools/run_solutions.py --corpus "$CORPUS" \
    --solutions ~/ar-runs4/*/solution.py --out /tmp/preds
```

## What the number means

Scoring every iteration against all 194 cases makes the final figure a
**fitting score, not an estimate of generalization**. The agent is choosing its
method by that number, so it is optimistic by construction, and the gap grows
the more iterations it runs.

Two things keep it honest. The grader reveals no case, so the agent has to
improve the method rather than the answers; and the audit catches the
identifiers that memorisation needs. Neither proves generalization. The only
thing that does is re-scoring the frozen solution on recordings that were never
in the workspace — hold some out before the next freeze, and treat the 194-case
number as the training curve it is.
