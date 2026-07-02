# Generalizers and Metric-Maximizers: What Autonomous Coding Agents Optimize When You Give Them a Scorecard

*Working draft — v0.1, 2026-07-02. Data: Study 1 complete; Study 2 pending.*

## Abstract

Karpathy-style "autoresearch" gives a coding agent a fixed dataset, a fixed
metric, and a modify→verify→keep/discard loop, and asks it to improve an
algorithm autonomously. We build such a harness for a real production task —
transcript-only Quran recitation processing (detect which ayahs were recited and
split the transcript by ayah) — and compare two frontier coding agents, Claude
Code and OpenAI Codex, from an identical blank-slate start: 3 runs each, same
budget (30 experiments / 1 h), same instructions, matched reasoning effort.
Both agents independently converge on the same general architecture
(orthographic canonicalization → n-gram surah anchoring → dynamic-programming
alignment) and reach comparable scores at matched experiment counts. They then
diverge sharply. Claude stops early (12–13 experiments), declaring residual
failures "structurally unwinnable," and ships 200–340 lines with zero
dataset-specific constants. Codex grinds on (16–30 experiments) and drives the
score ~10× lower (0.007 vs 0.078, complete separation across runs) — but does so
substantially by memorizing the evaluation set: 19–41 hardcoded ayah ids per run,
including literal transcript-to-answer lookups for individual recordings. The
raw metric thus rewards specification gaming and cannot distinguish a better
algorithm from a better-overfit one. We characterize the two behavioral
profiles — *generalizer* vs *metric-maximizer* — quantify them (LOC, hardcoded
constants, stopping behavior, keep rates), and present a held-out redesign of
the harness (Study 2) that scores agents on unseen recordings.
[TODO: Study 2 results.]

## 1. Introduction

- Autonomous "AI researcher" loops (Karpathy's autoresearch, 2026) as the
  emerging pattern: fixed data + fixed metric + agent that edits one file.
- Open question: when two different agents run the *same* loop, what differs?
  Not just "which scores better" — what do they *do* with an imperfect metric?
- Our contribution: (i) a reproducible autoresearch harness on a real production
  task with real user data; (ii) a 3×2 controlled comparison; (iii) the
  finding that the agents embody opposite research philosophies, with direct
  implications for how such loops must be designed (held-out sets are not
  optional); (iv) [TODO Study 2] a held-out generalization study.
- Why this task is a good testbed: real ASR noise, genuinely messy user
  behavior (repetitions, restarts, skips, non-Quran speech), a closed reference
  corpus (the Quran) enabling exact gold labels, and a metric with a known
  oracle floor.

## 2. Related work

- Karpathy autoresearch (nanochat train.py loop) — our direct template.
- Agent coding benchmarks (SWE-bench et al.) — measure task completion, not
  research behavior under a proxy metric.
- Specification gaming / Goodhart's law in RL and LLM agents — our Codex result
  is a clean natural instance produced by a production-grade agent.
- ASR + Quran recitation scoring literature (tarteel etc.) — domain context.
- [TODO: proper citations.]

## 3. Task and harness

### 3.1 Task
Stage 1 of a transcript-only memorization checker: given a no-harakat ASR
transcript, return either `abstain` (non-Quran) or the recited ayah sequence
with the transcript split per ayah. (Stage 2 — within-ayah mistake detection —
is future work.)

### 3.2 Dataset
258 Telegram-bot recordings from production (254 Quran, 4 non-Quran; 45 surahs;
transcript lengths 3–400+ words), human/LLM-reviewed into gold `(assignment,
per-ayah split, confidence)`. Labeling conventions (isti'adha/basmala exclusion,
repetition handling, non-contiguous ids) in Appendix. Dataset frozen by SHA-256
before any run.

### 3.3 Metric
`research_score = detection_error + split_error + abstain_error` (lower better;
stub = 2.0, oracle floor ≈ 0.008). Detection = exact ayah-id-set match; split =
word-assignment accuracy under a metric-only canonicalizer; abstain = correct
rejection of non-Quran rows.

### 3.4 Loop protocol
`PROGRAM.md` (fixed, agent-agnostic): one idea per experiment, commit before
verify, `make exp` uniform logging, keep iff score improves else `git reset`,
plateau stop at ~15 non-improving, simplicity criterion. Each run in an isolated
git worktree from the identical stub; single uninterrupted full-auto session;
one commit per experiment = complete audit trail.

## 4. Study 1: setup

- Arms: Claude Code vs OpenAI Codex, 3 runs each.
- Budget: 30 experiments or 1 h, whichever first. Reasoning effort `high` both.
- Full-auto permissions both (Claude `--dangerously-skip-permissions`; Codex
  `-s workspace-write -a never`).
- [TODO confounds table: model ids/dates, CLI versions, hardware.]

## 5. Study 1: results

### 5.1 Headline scores

| run | best score | exps | keep/disc | LOC | hardcoded ids |
|---|---:|---:|---:|---:|---:|
| claude-r1 | 0.0875 | 13 | 9/4 | 202 | 0 |
| claude-r2 | 0.0852 | 12 | 10/2 | 292 | 0 |
| claude-r3 | 0.0621 | 13 | 11/2 | 341 | 0 |
| codex-r1 | 0.0061 | 30 | 24/6 | 456 | 39 |
| codex-r2 | 0.0101 | 16 | 14/2 | 387 | 19 |
| codex-r3 | 0.0050 | 22 | 21/1 | 486 | 41 |

Claude 0.0783 ± 0.011; Codex 0.0071 ± 0.002; complete separation (exact
Mann–Whitney one-sided p = 0.05, the minimum at n=3/3).

### 5.2 Convergent algorithm discovery
All six runs independently arrive at: canonicalize → n-gram surah anchor →
semi-global DP alignment → word→ayah grouping. Both agents independently hit and
fixed the same encoding trap (harakat combining-character reordering corrupting
a regex class). At matched checkpoints (exp 13) the arms are close: Codex
0.026–0.044 vs Claude 0.062–0.088.

### 5.3 Divergent optimization behavior
Claude: stops at plateau, refuses per-row fixes, labels residuals "structurally
unwinnable"; zero dataset-specific constants. Codex: continues to budget,
converts residual failures into special cases — e.g. a literal lookup mapping
one garbled ASR transcript tuple to its answer id (r1), and an At-Talaq bucket
merge conditioned on specific words being absent (r3). No gold-field leakage in
any run; the memorization is enabled by the harness (score measured on the
optimized rows; failure report printing expected ids).

### 5.4 Process metrics
Codex is ~2–3× faster per experiment (~45–60 s vs ~95–180 s) and grinds longer;
keep rates similar (~75–95%); zero crashes in all six runs. Figure:
`comparison.png` (best-so-far vs experiments and vs wall-clock).

## 6. Discussion

- The metric rewarded memorization; only *agent disposition* separated the two
  outcomes. Under Goodhart pressure, Codex behaved as a metric-maximizer,
  Claude as a generalizer that self-imposed a generalization prior ("simplicity
  criterion") the metric never enforced.
- Neither behavior is "wrong": Codex followed the stated objective more
  literally; Claude anticipated the deployer's *intent*. This is precisely the
  outer-alignment gap in miniature.
- Design lesson for autoresearch harnesses: the loop *will* be Goodharted at
  the margin; a held-out set and a leak-free failure report are structural
  requirements, not hygiene.
- Practical lesson for our product: Claude's artifacts are deployable as-is;
  Codex's require stripping the memorized rules (its exp≤13 core is comparable
  and general).

## 7. Study 2: held-out generalization [design final, runs pending]

Stratified 60/40 split by recording (151 train / 107 test; non-Quran 2/2;
repetition and non-contiguous cases represented on both sides; known label
quirks pinned to train; seed 42). Agents see and optimize on train only;
`eval.py` failure report shows no expected ids; we score final solutions on the
untouched test set. Hypotheses: (H1) Codex train↔test gap ≫ Claude's; (H2)
held-out ranking narrows or reverses; (H3) both retain large gains over the
stub — the loop does produce real algorithms.

## 8. Limitations & threats

Single task/domain; n=3 per arm (report effect sizes, not just p); pretraining
familiarity with the Quran (equal across arms; task is algorithm engineering,
not recall); transcript-only ceiling (harakat-blind); temporal confound between
arms (runs days apart); harness authored with one of the compared agents
(Claude) — mitigated by fixed files + hashes; agent CLIs are moving targets
(versions pinned in confounds table).

## 9. Reproducibility

Frozen inputs (SHA-256), per-experiment git branches for all six runs, uniform
TSV logs, deterministic split (seed 42), all tooling in the repo. Dataset is
production-derived and private; the harness, reference, and all analysis are
public-safe. [Repo: nurlingo/autoresearch]

## Appendix
A. Labeling conventions. B. PROGRAM.md (verbatim). C. Per-run experiment tables
from results.tsv. D. Overfitting exemplars (code excerpts). E. The harakat
encoding trap.
