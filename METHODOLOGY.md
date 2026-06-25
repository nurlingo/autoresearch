# Comparison Methodology (for the paper)

How to run a fair, reproducible comparison of coding agents (Claude Code vs Codex,
and optionally others) on this autoresearch task, and what to measure.

## Research question

> Given an identical autoresearch harness — a fixed metric, a fixed dataset, and a
> blank algorithm — how do different coding agents differ in their ability to
> autonomously improve the algorithm?

The algorithm is built **from scratch** (`solution.py` starts as an abstain-only
stub), so this measures an agent's research/engineering ability, not its ability
to tweak existing code.

## Controlled design

**Held fixed (the harness):** `eval.py`, `data/`, `PROGRAM.md`, the starting
`solution.py`, and the machine. Hash the dataset and reference so a run is
pinned to exact inputs:

```bash
shasum -a 256 data/bot_review.csv data/quran_ref.json eval.py > runs/inputs.sha256
```

**Independent variable:** the agent (set `AR_AGENT`).

**Dependent variables:** see *Metrics*.

**No human intervention** during a run. The agent reads `PROGRAM.md` and loops
autonomously until the stopping rule fires.

## Protocol

For each agent:

1. Fresh branch from `main` per run: `autoresearch/<agent>-<tag>-r<k>`.
   Reset `solution.py` to the committed stub so every run starts identical.
2. `export AR_AGENT=<agent>` and launch the agent in the repo (see README).
3. The agent runs the loop, logging every experiment via `make exp`.
4. **Equal budget** — fix ONE and hold it constant across all runs and agents:
   - *iteration budget* (recommended): e.g. 60 experiments, or
   - *wall-clock budget*: e.g. 90 minutes.
5. `make archive AGENT=<agent>` → `runs/<agent>-<tag>-r<k>.tsv`.
6. **Repeat ≥3 runs per agent** (5 is better). LLM agents are stochastic; a single
   run is an anecdote. Report all runs, not the best.

Then:
```bash
make compare RUNS="runs/claude-*.tsv runs/codex-*.tsv"   # -> comparison.png
```

## Metrics

| Class | Metric | From |
|---|---|---|
| **Quality** | best `research_score` reached (primary) | min over run |
| | component breakdown at best (detection / split / abstain error) | log columns |
| **Sample efficiency** | experiments to reach a threshold (e.g. < 0.5) | log |
| | area under the best-so-far curve (lower = faster) | log |
| **Wall-clock efficiency** | time to threshold; best score at the fixed time budget | `elapsed_sec` |
| **Process** | # experiments, keep rate, crash rate, mean iteration wall-clock | log |
| **Cost** | tokens / USD per run (if the agent exposes it) | agent side |
| **Artifact** | final `solution.py` LOC + a qualitative taxonomy of strategies tried | git diff + descriptions |

The `keep`/`discard`/`crash` status column gives keep-rate and crash-rate
directly; the `description` column is the qualitative record of what each agent
tried (read it to taxonomize approaches: n-gram detection, DP alignment,
abstention heuristics, …).

## Statistics

With small N, report **mean ± std across runs** and show every run on the plot.
For "is agent A better than B," use a nonparametric test (Mann–Whitney U) on the
per-run best scores rather than assuming normality. Do not over-claim from 3 runs.

## Confounds to pin (record these in the paper)

- **Model id + date** for each agent (e.g. Claude Opus 4.x build; Codex model).
- **Settings**: permission mode (full-auto), temperature/reasoning effort if set.
- **Tooling parity**: both agents get shell + file edit + git, nothing more. No
  extra skills/plugins (a skill like uditgoenka/autoresearch would confound the
  agent comparison — run it only as a separate, clearly-labeled condition).
- **Same hardware**, same dataset hash, **identical `PROGRAM.md`**.

## Threats to validity

- **Ceiling effect.** The dataset is small (79 rows) with a known floor ~0.03; if
  both agents saturate, differences compress. Mitigate by growing/cleaning the
  dataset (the two inconsistent-label rows) and/or reporting sample-efficiency
  (curve shape) rather than only the final score.
- **Transcript-only / ASR-confound.** The metric cannot see audio; it measures
  detection+split fidelity, not true recitation correctness.
- **Single task/domain.** Results are about this harness; generalization claims
  need more tasks.
- **Stochasticity.** Mandates multiple runs.

## Reproducibility bundle to keep per run

- the archived `runs/<agent>-…​.tsv`,
- the agent's branch (each commit = one experiment) and final `solution.py`,
- the agent session transcript,
- `runs/inputs.sha256`.
