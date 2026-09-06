# Recitation Autoresearch — Stage 2 (within-ayah mistake events)

A Karpathy-style autoresearch loop. You are an autonomous researcher optimizing a
transcript-only algorithm that, given the transcript words of ONE recited ayah
(a gold Stage-1 chunk) and the reference ayah text, returns the list of
recitation *events* in it — and, for each, whether it is a genuine mistake
that should be flagged, a benign behaviour (breath repeat, restart, stutter,
stopping the recording), a self-corrected slip, or undecidable from text alone.
Detection + split is **Stage 1** and is not part of this loop.

This program is **agent-agnostic**: the same loop is run by Claude Code, Codex, or
a human. The only thing that varies between runs is the agent — that is the point
(we compare the `study3_score` each agent reaches).

## Setup

This directory is a dedicated, single-purpose experiment repository prepared for
you. You are already on the correct branch (`run`).

1. **Do not create branches** — commit directly to the current branch. Do not
   push anywhere.
2. **Read the in-scope files** (the repo is small — read them fully):
   - `eval.py` — the FIXED scorecard and metric. Do not modify.
   - `SCHEMA.md` — the event taxonomy, verdicts and span conventions.
   - `../data/quran_ref.json` — the FIXED Quran reference. Do not modify.
   - `solution.py` — the ONLY file you edit.
3. **Verify data**: `data/train.jsonl` must exist. If missing, stop and tell the
   user. **Held-out evaluation**: a test set of recordings you will NEVER see
   exists outside this repository. Your final solution is scored on it after the
   run. Changes that memorize specific train rows will not transfer — only
   general improvements count in the end.
4. **`results.tsv`** is created automatically by `make exp` (it is gitignored,
   so it survives `git reset` during discards).
5. **Baseline first**: run `make exp` once on the unmodified `solution.py` to
   record the baseline before changing anything.

## Experimentation

There is no time budget — `make eval` runs in well under a second, so you can do
hundreds of experiments. Each experiment is: edit `solution.py`, run, check the
score, keep or discard.

**You CAN:**
- Modify `solution.py` and any helper files you add next to it. Build whatever you
  want from scratch: normalization, alignment, repetition/restart modelling,
  orthographic (Uthmani) tolerance, uncertainty handling. There is no required
  approach.

**You CANNOT:**
- Modify `eval.py`, `data/`, or this file. They are the fixed metric, data, and
  task — the equivalent of Karpathy autoresearch's `prepare.py`. Improving the
  score by touching them is cheating.
- Read `events` at runtime from the JSONL — only `eval.py` sees the gold.
  Your algorithm gets `chunk_text`, `reference_text`, `ctx` and
  `../data/quran_ref.json`, nothing else.
- Access the held-out test set. It is not in this working tree; do not go
  looking for it.

**The goal is simple: the lowest `study3_score`.**

```
study3_score = 2*miss_error + false_alarm + benign_error + clean_error   # lower is better
```
- **miss_error** — gold mistakes you did not flag (an `uncertain` prediction on
  a gold mistake costs half).
- **false_alarm** — your `mistake` flags that touch no gold mistake/uncertain event.
- **benign_error** — gold benign/corrected events you flagged as `mistake`.
- **clean_error** — clean chunks (no events at all) on which you raised a flag.
  Most chunks are clean: this is the false-flag rate the product cares about.

`uncertain` is a first-class verdict: it is never a false alarm, and it earns
half credit on a real mistake. Over-using it costs you the other half.

Reference points on the train split: empty baseline `2.0`; feeding the gold
events back scores `0.0` — the dataset is internally consistent, so `0.0` is the
true floor. The held-out test set is scored separately after the run.

**Simplicity criterion**: all else equal, simpler is better. A tiny gain that adds
ugly complexity is not worth it; an equal-or-better result from *deleting* code is
a win — keep it.

## Output format

`make eval` prints a report ending with the metric. Extract it with:
```bash
make eval > run.log 2>&1
grep '^study3_score:' run.log
```
If the grep is empty the run crashed — `tail -n 50 run.log` for the traceback.

## Logging results

Do **not** hand-edit `results.tsv`. After committing an experiment, run:
```bash
make exp DESC="short description of what changed"
```
This runs the scorecard, parses the score + component errors, and appends one
uniform row (iter, timestamp, elapsed, agent, commit, scores, status). Identical
logging for every agent — that is what makes the runs comparable. `results.tsv`
is gitignored so it survives the `git reset` used to discard a regression.

Tag the run with the agent under test once, before you start:
```bash
export AR_AGENT=claude     # or: codex, human
```

## The experiment loop

Run on the dedicated branch. LOOP:

1. Look at git state (current branch/commit) and `results.tsv` (what worked/failed).
2. Pick ONE focused idea. Edit `solution.py`.
3. `git commit -am "<idea>"` (commit before verifying).
4. `make exp DESC="<idea>"`. It prints `study3_score` and `status`.
5. `status=crash` → read `tail -n 50 run.log` or rerun `make eval`. Fix if trivial
   (typo, import); otherwise `git reset --hard HEAD~1` and move on.
6. If `status=keep` (score improved): keep — the commit stays, the branch advances.
7. If `status=discard` (equal or worse): `git reset --hard HEAD~1` back to the last
   kept commit.

Every few experiments, `make plot` regenerates `progress.png` so you (and the
human) can see the curve. At the end of a run: `make archive AGENT=$AR_AGENT`.

You are autonomous. Once the loop has begun, do **not** stop to ask "should I keep
going?" — keep iterating until you plateau (≈15 consecutive non-improving
experiments) or the user interrupts. If you run out of ideas, think harder:
re-read `eval.py` to understand exactly what is scored, study the failure list it
prints, combine previous near-misses, or try a more radical redesign. Rewind to an
earlier commit only very sparingly, if ever.
