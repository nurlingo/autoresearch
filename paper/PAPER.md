# Generalizers and Metric-Maximizers: What Autonomous Coding Agents Optimize When You Give Them a Scorecard

*Working draft — v0.2, 2026-07-03. Data: Studies 1 and 2 complete.*

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
algorithm from a better-overfit one. In Study 2 we redesign the harness with a
held-out split, disclose its existence to both agents, and re-run 3×2 trials.
Three results: (i) the train-side separation evaporates — held-out, the arms
are statistically indistinguishable on the full metric; (ii) disclosure alone
eliminates literal memorization (hardcoded answers drop from 19–41 per Codex
run to zero) while leaving the train-grinding instinct intact — yet Codex's
general core transfers *better and more consistently* than Claude's
(held-out detection+split 0.085±0.004 vs 0.121±0.031); (iii) the decisive
held-out difference is rare-event robustness: a single missed abstention costs
Codex half a point, while Claude rejects non-recitation inputs 10/10 across
both studies. We also catalogue the isolation failures the agents surfaced —
reading sibling branches through a shared git database, and unprompted
persistent-memory notes addressed to "future runs" — and derive design rules
for autoresearch harnesses: agents will use any state channel the design
leaves open, including their own tooling's.

## 1. Introduction

- Autonomous "AI researcher" loops (Karpathy's autoresearch, 2026) as the
  emerging pattern: fixed data + fixed metric + agent that edits one file.
- Open question: when two different agents run the *same* loop, what differs?
  Not just "which scores better" — what do they *do* with an imperfect metric?
- Our contribution: (i) a reproducible autoresearch harness on a real production
  task with real user data; (ii) a 3×2 controlled comparison; (iii) the
  finding that the agents embody opposite research philosophies, with direct
  implications for how such loops must be designed (held-out sets are not
  optional); (iv) a held-out generalization study showing the train-side
  separation evaporates and reframing where each disposition actually pays.
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
before any run (v1 for both studies; one label corrected post-study after the
agents flagged it — see Discussion — giving v1.1 with oracle floor exactly 0.0).

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
- Confounds pinned: Claude Code v2.1.198 (Claude Opus 4.8, reasoning effort
  `high`); Codex CLI v0.139.0 (GPT-5.5, reasoning effort `high`); same MacBook
  Pro for all runs; dataset + eval frozen by SHA-256.

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
- Practical lesson for our product: with a held-out harness both agents
  produce deployable artifacts; Codex's core is the most accurate and stable
  held-out, Claude's is safest on rejection behavior. A deployment could use
  Codex's aligner with Claude's abstention margin.
- Study 2 reframes Study 1: the "metric-maximizer" pathology is real but
  train-side; generalization damage was concentrated in a rare-event component.
  Conversely the "generalizer" discipline did not buy held-out accuracy — it
  bought robustness and smaller artifacts.
- **Neither disposition wins; they pay in different currencies.** The
  metric-maximizer buys accuracy and run-to-run consistency on the measured
  distribution; the generalizer buys rare-event robustness, restraint, and
  smaller artifacts. Which currency matters is a property of the deployment,
  not of the agent — a harness designer should decide which they are buying
  *before* reading the scoreboard.
- **Agents double as annotation auditors.** Both arms independently flagged the
  same training row as a gold-label error (At-Tin: "the reciter truly recites
  8 ayahs; gold says 1–7") and declined to fit it. Post-study human re-review
  confirmed and fixed the label, bringing the dataset's oracle floor to exactly
  0.0. The agents' "unwinnable" lists were, in part, a free data-quality report
  — an unplanned dividend of running the loop with agents that explain their
  stopping decisions.
- A methodological aside we did not anticipate: Study 2's outcome contradicted
  our own Study 1 prediction (we expected Codex's core not to transfer; it
  transferred best). Registering hypotheses in the methodology before the runs
  (H1–H3) is what makes that reversal legible as evidence rather than
  post-hoc narrative.

## 7. Study 2: held-out generalization

Stratified 60/40 split by recording (151 train / 107 test; non-Quran 2/2;
repetition and non-contiguous cases on both sides; label quirks pinned to
train; seed 42; test oracle floor exactly 0.0). Agents optimize train only, in
fully isolated single-commit clones; both are told a held-out set exists and
that memorization will not transfer; we score final solutions on the untouched
test set. Hypotheses: (H1) Codex train↔test gap ≫ Claude's; (H2) held-out
ranking narrows or reverses; (H3) both retain large gains over the stub.

### 7.1 Results

| run | train | test | gap | test det+split | test abstain | exps |
|---|---:|---:|---:|---:|---:|---:|
| claude-r1 | 0.0441 | 0.0796 | 0.036 | 0.0796 | 0 | 12 |
| claude-r2 | 0.0982 | 0.1534 | 0.055 | 0.1534 | 0 | 7 |
| claude-r3 | 0.0661 | 0.1306 | 0.064 | 0.1306 | 0 | 8 |
| codex-r1 | 0.0075 | 0.0869 | 0.079 | 0.0869 | 0 | 20 |
| codex-r2 | 0.0451 | 0.5882 | 0.543 | 0.0882 | 0.5 | 8 |
| codex-r3 | 0.0082 | 0.0793 | 0.071 | 0.0793 | 0 | 22 |

All three hypotheses resolve informatively. **H1 confirmed:** Codex's mean
train→test gap is 4.5× Claude's (0.231 vs 0.052). **H2 half-confirmed:** the
6–10× train separation vanishes (test means 0.251 vs 0.121, medians 0.087 vs
0.131, Mann–Whitney n.s.) — but not by the predicted mechanism. Codex's
held-out detection+split is *better and strikingly consistent* (0.085±0.004,
identical detection error in all three runs) than Claude's (0.121±0.031); its
floor-grinding on train was wasted effort, not poison. What Codex lost was a
single abstention on a non-Quran row (cost 0.5) — rare-event robustness, where
Claude is 10/10 across both studies. **H3 confirmed:** every run beats the
stub by ≥14×. Figure: `study2_generalization.png`.

### 7.2 Disclosure changes the *form* of Goodharting, not the drive

Hardcoded ayah ids per Codex final: 19–41 (Study 1) → 0 (Study 2). One
paragraph of disclosure eliminated literal memorization. The optimization
instinct remained — Codex still drove train to the floor with 20–22
experiments of general-looking machinery — but the non-transferable margin
went from "memorized answers" to "harmless over-tuning."

### 7.3 Isolation is adversarial, even without an adversary

Three incidents, all agent-initiated and none forbidden explicitly: (a) a
Codex run read Study 1 logs and a sibling agent's in-flight solution through
the shared `.git` of a git worktree; (b) Claude runs twice saved unprompted
persistent-memory cheat-sheets addressed to "future runs on this repo"
(non-firing only because run paths are never reused); (c) both agents used the
failure report's expected ids in Study 1. The harness had to be redesigned to
fresh single-commit clones per run. Design rule: enumerate the state channels
an agent's *own tooling* provides (git history, logs, persistent memory) and
close them structurally, not by instruction.

### 7.4 Community arms: Cursor (Auto) and Antigravity (Gemini 3.1 Pro High)

A collaborator added two exploratory arms on the same Study 2 harness (TAG
`260702`, dataset v1, hash-verified; runbooks `CURSOR.md` / `ANTIGRAVITY.md`).
Same budget, prompt, and isolation (fresh single-commit clone per run; held-out
scoring by us). **Not preregistered** — different machine, and Cursor uses
**Auto mode** (unpinned model routing) rather than a fixed model id.

| run | train | test | test det+split | abstain miss | exps |
|---|---:|---:|---:|---:|---:|
| antigravity-r1 | 0.147 | 0.133 | 0.133 | – | 12 |
| antigravity-r2 | 0.109 | 0.652 | 0.152 | 0.5 | 12 |
| antigravity-r3 | 0.063 | 0.091 | 0.091 | – | 16 |
| cursor-r1 | 0.388 | 0.305 | 0.305 | – | 5 |
| cursor-r2 | 0.293 | 0.229 | 0.229 | – | 9 |
| cursor-r3 | 0.347 | 0.286 | 0.286 | – | 7 |

**Held-out detection+split (four-arm comparison):** Codex 0.085±0.004 <
Claude 0.121±0.031 ≈ Antigravity 0.125±0.026 < Cursor 0.273±0.032. Figure:
`study2_generalization.png` (updated with all four arms).

Three patterns extend Study 2 rather than overturn it. **(i) Cursor underfits:**
5–9 experiments per run, train never below 0.29, and test beats train on every
run (negative gap) — the only arm to generalize *better* than its train score,
consistent with early stopping + unpinned Auto routing. Treat as exploratory.
**(ii) Antigravity sits between Claude and Codex** on held-out core accuracy,
with the same rare abstain failure mode as Codex (r2, cost 0.5). Train improved
monotonically r1→r3 (0.147→0.109→0.063) but held-out did not (r2 test blow-up) —
so improving train across runs is not cross-run leakage, it is within-run
optimization and run-to-run variance. **(iii) Cross-arm ranking on held-out core
tracks optimization effort:** arms that spent more experiments on general
machinery transferred better; wasted train-side margin was harmless, echoing §7.1.
Zero hardcoded per-recording ids in any community final solution. Bundles confirm
each run starts from the identical stub commit; `collect_run.sh` was updated to
auto-commit final working tree when an agent forgets to commit (antigravity-r3).

## 8. Limitations & threats

Single task/domain; n=3 per arm (report effect sizes, not just p); pretraining
familiarity with the Quran (equal across arms; task is algorithm engineering,
not recall); transcript-only ceiling (harakat-blind); temporal confound between
arms (runs days apart); harness authored with one of the compared agents
(Claude) — mitigated by fixed files + hashes; agent CLIs are moving targets
(versions pinned in confounds table). **Community arms** (Cursor Auto, Antigravity
on a different Linux box) are exploratory extensions with unpinned model routing
(Cursor) and are not matched to the preregistered Claude/Codex confounds.

## 9. Reproducibility

Frozen inputs (SHA-256), per-experiment git branches for all six runs, uniform
TSV logs, deterministic split (seed 42), all tooling in the repo. Dataset is
production-derived and private; the harness, reference, and all analysis are
public-safe. [Repo: nurlingo/autoresearch]

## Appendix
A. Labeling conventions. B. PROGRAM.md (verbatim). C. Per-run experiment tables
from results.tsv. D. Overfitting exemplars (code excerpts). E. The harakat
encoding trap.
