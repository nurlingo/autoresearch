# Autoresearch: train development, final gold validation

The frozen split is **100 train / 100 gold**, version `granular-100x100-v1.0`. All 200 cases are approved, including the five gap-targeted additions. Measured preparation refuses to proceed until there are **100 approved cases in each split**. Use `--preflight` only for setup checks; no measured run has been launched.

## Runtime setup

Start Docker Desktop. The inference image is pinned by digest; the development image below pins the base and Claude Code version to the locally verified CLI, 2.1.267. Building does not call a model or use credentials.

```sh
docker pull python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
docker build -f study3/agent-run/Dockerfile.claude \
    -t study3-claude:2.1.267 study3/agent-run
```

Record the resulting image ID; package-manager dependencies can change on a later rebuild. For exact reuse, keep/export that built image, rather than treating its mutable tag or a future rebuild as identical. The launcher resolves and records the immutable local image ID. Other agents can use an image containing their pinned CLI and Python 3 through the same launcher.

## Owner preparation

Run from the trusted owner environment. Set a new workspace path each time. The budget below is an example, not an agreed experiment budget.

```sh
STUDY3="$HOME/Developer/namaz/ar-runs/musiml-annotation-review/study3"
PRIVATE_CORPUS="$HOME/Developer/namaz/follow_my_reading/backend/tests/fixtures/bot_review/train_review/granular-corpus/frozen/granular-100x100-v1.0"
TRAIN_CORPUS="$PRIVATE_CORPUS/split-train.jsonl"
GOLD_CORPUS="$PRIVATE_CORPUS/split-gold.jsonl"
RUN="$HOME/ar-runs4/train-run-001"

python3 "$STUDY3/tools/prepare_agent_run.py" \
    --corpus "$TRAIN_CORPUS" --gold "$GOLD_CORPUS" \
    --out "$RUN" --budget "30 minutes"
```

The finalized split passes the count/approval gate. Point `PRIVATE_CORPUS` at the private `frozen/granular-100x100-v1.0/` snapshot to pin the data version. For an explicitly unmeasured setup check, append `--preflight` and choose a fresh directory. Never substitute the combined `recordings.jsonl` for train.

Preparation checks case/recording-ID separation, event-bearing ayah overlap and
reference consistency, then writes the workspace:

| file | contents |
|---|---|
| `TASK.md` | the task, with budget, train size and held-out size substituted |
| `ANNOTATION-GUIDE.md` | the rubric with the hamza policy inlined |
| `data/corpus-train.jsonl` | the annotated train split — an allowlist of `case_id`, `units`, `events`; preparation aborts if any held-out case id appears in it |
| `data/corpus-inputs.jsonl` | the same recordings reduced to what `detect_events` receives |
| `data/quran-reference.json` | the reference |
| `eval21.py` | the evaluator |
| `score.py` | scores `solution.py` on train locally and appends to `.scores.jsonl` |
| `solution.py` | a stub |

The agent learns from the train annotations directly. They cannot help at
inference: grading stages the solution in a separate container holding only the
solution, the reference and answer-free inputs.

The private `RUN.owner.json` is adjacent to, **outside**, the workspace. It records source hashes, evaluator/reference versions, budget and an exact prepared-file allowlist. The launcher checks the allowlist and hashes before mounting the directory. Gold is read only during owner-side split auditing, never copied to the agent workspace. Gold and train annotation sources must remain outside the workspace.

## Development agent

Run the loop with a Claude subscription token (`claude setup-token`), passed by
name only:

```sh
export CLAUDE_CODE_OAUTH_TOKEN=<token>
"$STUDY3/tools/run_iterating_agent.sh" "$RUN.owner.json" claude-opus-5    # or claude-fable-5-1
```

The script runs one pass over `TASK.md`, then `claude -c` continuation passes
inside the container until the budget is spent or the plateau rule fires: 10
consecutive scored solution versions without a new best train score, counted
from `.scores.jsonl`. It holds `caffeinate` so the host cannot sleep, floors every
pass so a pass that returns instantly cannot spin the loop, and writes a
timestamped transcript. Override with `PLATEAU=`, `MIN_PASS_SECONDS=`,
`MAX_PASSES=` and a third argument for the budget in seconds.

The launcher records image ID, command, credential names (never values),
start, end, elapsed seconds, budget used, exit code, and
`host_suspended_seconds`.

Only the prepared train directory is mounted. The host HOME, owner manifest, gold, authoring checkout and Docker socket are unavailable. A temporary container HOME avoids prior session memory. The CLI's permissive tool mode operates inside this container boundary.

Development networking is enabled for model APIs. This is **not** a domain-level internet/retrieval restriction; if a comparison requires API-only access, configure an egress proxy and declare its allowlist before runs. No claim of previously unseen public inputs follows from local filesystem isolation.

## Freeze the solution

The supported executable deliverable is a self-contained `solution.py` using the Python standard library. Any learned constants must be included there; no extra helper/model files are mounted for inference. Preserve separately any machine annotations and development logs for analysis.

After the development container exits, freeze the solution into a fresh private directory outside the agent workspace:

```sh
FROZEN="$HOME/ar-runs4/final-run-001"
python3 "$STUDY3/tools/freeze_solution.py" \
    --workspace "$RUN" --manifest "$RUN.owner.json" --out "$FROZEN"
```

The command prints the solution SHA-256 and saves a read-only source copy plus `frozen-manifest.json`. Select the solution using train evidence only. Fix model versions, budgets, repeats and selection rules before running a comparison.

## Confirm the run executed before spending a gold evaluation

Every gold reading erodes the holdout, because deciding which run to report is
itself a selection. Check that the run followed the protocol *before* grading
it, using evidence that does not involve gold:

```sh
python3 -c "import json;d=json.load(open('<manifest>.launch.json'));\
print({k:d[k] for k in ('elapsed_seconds','budget_used','exit_code','hit_time_budget')})"
grep -c '═══ continuation pass' "<manifest>.run.log"   # iterations actually made
```

A run that used a small fraction of its budget did not do what was asked.
Record its status -- completed, or interrupted and why -- before reading gold,
and report it with that status rather than dropping it. Every run is logged in
`RUNS.md`.

Write the status down before the score is known. A run's status must not depend
on its number, and afterwards the two cannot be told apart unless the status was
recorded first.

## Final private gold validation

Read the printed SHA-256 (or `solution_sha256` in the frozen manifest) and supply it explicitly:

```sh
python3 "$STUDY3/tools/grade_workspace.py" \
    --workspace "$FROZEN" --corpus "$GOLD_CORPUS" \
    --expected-solution-sha256 "<frozen-sha256>" \
    --predictions-out "$FROZEN/gold-predictions.json" --json \
    > "$FROZEN/gold-score.json"
```

Measured grading requires 100 approved records, the expected code hash and the frozen manifest. It verifies the selected split, reference and evaluator hashes; `--split gold` is the default (`--split train` is available for owner-side checks). Input-only gold units enter a fresh inference container with network disabled, a read-only filesystem, no capabilities, a non-root user, and limits on memory, processes, time and output. Annotation answers stay in the trusted owner process, which scores returned predictions afterward. Submitted code is never imported there.

Per-case predictions and frozen owner manifests stay private. Report final aggregate gold metrics after development; do not revise or select solutions based on them. Record any technical rerun and retain the original artifacts.

## Verification and interpretation

```sh
python3 -m unittest discover -s study3/tests -p test_eval21.py -v
STUDY3_DOCKER_TESTS=1 python3 -m unittest discover -s study3/tests -p test_isolated_run.py -v
```

The current evaluator is v2.3: label-aware micro F1 is primary; exact label-aware F1, localization/per-label/macro F1 and 1:1/2:1 review costs are diagnostics. It retains the per-unit, one-eligible-occurrence adapter. That does not evaluate recovery of every linked attempt in the human annotations. Train agreement measures fit; final gold evaluates the frozen method on held-out recording cases, subject to shared clean text and prior-public-exposure limitations. See [EVALUATOR.md](../EVALUATOR.md).
