# Recitation Autoresearch — Stage 1 (detection + split)

A Karpathy-style autoresearch loop. You are an autonomous researcher optimizing a
transcript-only algorithm that maps a Quran recitation transcript to the ayahs
recited and the split of the transcript by ayah. Mistake detection is **Stage 2**
and is not part of this loop.

This program is **agent-agnostic**: the same loop is run by Claude Code, Codex, or
a human. The only thing that varies between runs is the agent — that is the point
(we compare the `research_score` each agent reaches).

## Setup

Work with the user once, then go:

1. **Run tag**: propose a tag from today's date (e.g. `jun26`). The branch
   `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Branch**: `git checkout -b autoresearch/<tag>` from `main`.
3. **Read the in-scope files** (the repo is small — read them fully):
   - `README.md` — context.
   - `eval.py` — the FIXED scorecard and metric. Do not modify.
   - `data/quran_ref.json` — the FIXED Quran reference. Do not modify.
   - `solution.py` — the ONLY file you edit.
4. **Verify data**: `data/bot_review.csv` must exist (it is gitignored; a fresh
   clone needs it copied in — see README). If missing, stop and tell the user.
5. **Init `results.tsv`** with just the header row (it is gitignored, so it
   survives `git reset` during discards):
   ```
   commit	research_score	status	description
   ```
6. **Baseline first**: run the loop once on the unmodified `solution.py` to record
   the baseline before changing anything.

## Experimentation

There is no time budget — `make eval` runs in well under a second, so you can do
hundreds of experiments. Each experiment is: edit `solution.py`, run, check the
score, keep or discard.

**You CAN:**
- Modify `solution.py` and any helper files you add next to it. Build whatever you
  want from scratch: normalization, n-gram/IDF detection, DP alignment for
  splitting, abstention heuristics. There is no required approach.

**You CANNOT:**
- Modify `eval.py`, `data/`, or this file. They are the fixed metric, data, and
  task — the equivalent of Karpathy autoresearch's `prepare.py`. Improving the
  score by touching them is cheating.
- Read `actual_ayahs` at runtime from the CSV — only `eval.py` sees the gold.
  Your algorithm gets the transcript and `data/quran_ref.json`, nothing else.

**The goal is simple: the lowest `research_score`.**

```
research_score = detection_error + split_error + abstain_error      # lower is better
```
- **detection** — ayah-id *set* match vs the gold range (repetition is a split
  concern, not detection).
- **split** — word-assignment accuracy: fraction of gold transcript words placed
  in the correct ayah bucket.
- **abstain** — return `{"abstain": True}` on non-Quran rows.

Reference points: empty baseline `2.0`; feeding the gold split back scores `~0.03`
(two rows have inconsistent labels). Treat **~0.03 as the practical floor**, not 0.

**Simplicity criterion**: all else equal, simpler is better. A tiny gain that adds
ugly complexity is not worth it; an equal-or-better result from *deleting* code is
a win — keep it.

## Output format

`make eval` prints a report ending with the metric. Extract it with:
```bash
make eval > run.log 2>&1
grep '^research_score:' run.log
```
If the grep is empty the run crashed — `tail -n 50 run.log` for the traceback.

## Logging results

Append one tab-separated line per experiment to `results.tsv` (NOT comma —
commas break descriptions). Do **not** commit `results.tsv` (it is gitignored so
it survives discards). Columns:
```
commit	research_score	status	description
```
- short commit hash (or `none` before first commit)
- `research_score` (e.g. `0.412300`) — use `9.999999` for a crash
- status: `keep`, `discard`, or `crash`
- short description of what the experiment tried

## The experiment loop

Run on the dedicated branch. LOOP:

1. Look at git state (current branch/commit) and `results.tsv` (what worked/failed).
2. Pick ONE focused idea. Edit `solution.py`.
3. `git commit -am "<idea>"` (commit before verifying).
4. `make eval > run.log 2>&1`, then `grep '^research_score:' run.log`.
5. Empty grep → crash. Read `tail -n 50 run.log`. Fix if trivial (typo, import);
   otherwise log `crash`, `git reset --hard HEAD~1`, move on.
6. Log the result line in `results.tsv`.
7. If the score **improved** (lower): keep — the commit stays, the branch advances.
8. If it is equal or worse: `git reset --hard HEAD~1` back to the last kept commit.

You are autonomous. Once the loop has begun, do **not** stop to ask "should I keep
going?" — keep iterating until you plateau (≈15 consecutive non-improving
experiments) or the user interrupts. If you run out of ideas, think harder:
re-read `eval.py` to understand exactly what is scored, study the failure list it
prints, combine previous near-misses, or try a more radical redesign. Rewind to an
earlier commit only very sparingly, if ever.
