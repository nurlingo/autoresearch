# Running the autoresearch arm with Google Antigravity

Instructions for running the same experiments (Study 1 and Study 2) with Google
Antigravity / Gemini 3.1 Pro as a third agent arm. The harness is agent-agnostic:
you change nothing in the repo — you only launch a different agent inside a run
worktree.

## What you need

1. **Repo access** — accept the collaborator invite to `nurlingo/autoresearch`,
   then:
   ```bash
   git clone git@github.com:nurlingo/autoresearch.git
   cd autoresearch
   ```
2. **The dataset** — `data/bot_review.csv` is intentionally NOT in git (real
   user-derived transcripts). You will receive it privately. Place it at
   `data/bot_review.csv`, then **verify it is byte-identical to the frozen
   study version**:
   ```bash
   git checkout main
   shasum -a 256 -c runs/inputs.sha256     # every line must say OK
   ```
   If this fails, stop and ask — do not proceed with a mismatched dataset.
3. **Python 3.11+** (stdlib only for the loop; `pip install matplotlib` only if
   you want plots). On Linux, if `shasum` is missing: `apt install libdigest-sha-perl`
   (or compare with `sha256sum` manually).
4. **Google Antigravity** installed and signed in, with **Gemini 3.1 Pro,
   thinking level High** selected — this arm's counterpart to Claude Opus 4.8
   `high` and GPT-5.5 `high`.

## The one non-negotiable: full autonomy, isolated folder

The agent must run **without approval prompts** (the loop is hands-off) and
**only inside the run folder** that the tooling creates. Run folders are
**fresh single-commit clones** — their git history contains nothing but the
harness snapshot, so there are no sibling branches or prior-run logs to read.
In Antigravity: enable automatic terminal-command execution (the "always
allow"/turbo-style policy) for the workspace, and open ONLY the run folder as
the workspace — never your main repo clone.

Sanity-check before a real run, inside the run folder: `git log --oneline`
shows exactly ONE commit; there is no `runs/` directory; `data/` contains only
`quran_ref.json` + the split you expect (`train.csv` for Study 2,
`bot_review.csv` for Study 1) and never `test.csv`.

## Study 1 (full dataset visible — like our Study 1 runs)

```bash
cd autoresearch && git checkout main
export TAG=$(date +%y%m%d) AR_AGENT=antigravity
tools/new_run.sh antigravity 1          # -> ../ar-runs/<tag>-antigravity-r1 (fresh clone)
```
Open `../ar-runs/<tag>-antigravity-r1` as the Antigravity workspace and give
the agent exactly this prompt (verbatim — it is the same for every arm):

> Read PROGRAM.md and run the loop. Budget: 30 experiments or 1 hour, whichever
> first. Do not push.

Before it starts, make sure the session environment has `AR_AGENT=antigravity`
(e.g. tell the agent as part of setup to `export AR_AGENT=antigravity` — it runs
`make exp`, which stamps every log row with it).

When the agent reports done:
```bash
cd autoresearch
TAG=<tag> tools/collect_run.sh antigravity 1
```
Repeat for runs 2 and 3 (`new_run.sh antigravity 2`, …). **Each run must be one
uninterrupted session** — if Antigravity hits rate limits and stalls mid-run,
note it; an interrupted run is discarded and redone (see RESULTS.md protocol).

## Study 2 (held-out — agent sees only the train split)

```bash
cd autoresearch && git checkout study2
python3 tools/split_dataset.py          # regenerates train/test deterministically (seed 42)
shasum -a 256 -c runs/inputs.sha256     # verifies YOUR split == the frozen study split
export TAG=$(date +%y%m%d) AR_AGENT=antigravity
tools/new_run.sh antigravity 1          # clone contains train.csv ONLY
```
Launch in the worktree exactly as above (same verbatim prompt). Collection also
scores the held-out test set automatically:
```bash
TAG=<tag> tools/collect_run.sh antigravity 1   # prints train best + heldout test
```

## What to send back (per run)

- `runs/antigravity-r<k>-<tag>.tsv` (+ `-holdout.json` for Study 2) — created by
  collect_run.sh in your clone; commit them on a branch or just send the files.
- `runs/antigravity-r<k>-<tag>.bundle` — the full experiment history (one
  commit per experiment + final solution.py), created by collect_run.sh.
- Antigravity/Gemini version info for the confounds table: model id, thinking
  level, app version, and your machine (OS/CPU).

## Rules (same as every arm — the agent must discover its own path)

- Do not hint approaches, point at failures, or intervene mid-run: launch the
  verbatim prompt, walk away, collect.
- Do not edit `eval.py`, `data/`, `PROGRAM.md`, or the budget.
- Wall-clock comparisons across machines are reported with a machine flag;
  sample-efficiency (per-experiment) curves are the primary cross-arm metric.
