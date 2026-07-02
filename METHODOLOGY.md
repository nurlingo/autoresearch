# Methodology

Full experimental design for the paper: *can coding agents do autonomous
algorithm research?* — comparing Claude Code and Codex on a real, from-scratch
task using a Karpathy-style autoresearch loop.

---

## 1. Research questions

**RQ1 (feasibility).** Given a fixed metric, a fixed dataset, and a *blank*
algorithm, can a coding agent autonomously build and improve a non-trivial
algorithm purely by the modify → verify → keep/discard loop?

**RQ2 (comparison).** How do agents (Claude Code vs Codex) differ in
- *quality* — best score reached,
- *sample efficiency* — improvement per experiment,
- *wall-clock efficiency* — improvement per unit time,
- *process* — keep rate, crash rate, exploration strategy?

The algorithm starts as an abstain-only stub, so this measures **research and
engineering ability**, not the ability to tweak pre-existing code.

## 2. The task

Stage 1 of a transcript-only Quran memorization checker: given a recitation
transcript (no harakat), (a) **detect** which ayahs were recited, including
skips/non-contiguous cases, and (b) **split** the transcript by ayah. Mistake
detection is **Stage 2** and is out of scope for this paper (it needs labels that
do not yet exist; see §10).

Pipeline: `transcript → [detect + split] → per-ayah chunks`. Detection and
splitting are one decision — labeling each transcript word with an ayah id yields
the id set and the split (contiguous runs) simultaneously.

## 3. The harness (fixed surface)

Three things are frozen, the agent never edits them:

| File | Role |
|---|---|
| `eval.py` | the scorecard / metric (the "ground truth") |
| `data/bot_review.csv` | the labeled dataset |
| `data/quran_ref.json` | the Quran reference (id, ar, clean per ayah) |

The agent edits **only** `solution.py` (+ helper files it adds). Contract:
`Solution.process(transcript)` returns `{"abstain": True}` or
`{"ayahs": [{"id","text"}, …]}`. See `PROGRAM.md`.

### Metric

```
detection_error = 1 - (exact ayah-id-set matches / Quran rows)
split_error     = 1 - mean(word-assignment accuracy / Quran rows)
abstain_error   = 1 - (correct abstentions / non-Quran rows)
research_score  = detection_error + split_error + abstain_error      # lower is better
```

- **Detection** compares the *set* of predicted ayah ids to the gold assignment, so a
  reciter repeating ayahs is not a detection error (it is a split concern).
- **Split** = word-assignment accuracy: of all gold transcript words, the fraction
  the algorithm placed in the correct ayah bucket. Tokens are compared on a
  harakat-folded canonical form (metric-only; not the algorithm's normalizer) so
  orthographic noise (`آ`/`ا`, Uthmani spelling) is not scored as error.
- **Abstain**: non-Quran rows must return `{"abstain": True}`.

`research_score ∈ [0, 3]`. **Reference points** (recompute when the dataset
changes): empty stub `= 2.0`; feeding the gold split straight back should score
`0.0` once the dataset is internally consistent.

## 4. Dataset

Telegram-bot auto-detect recordings, transcribed with OpenAI ASR and reviewed
(ayah assignment + per-ayah split + confidence) with the `bot_review` tooling in the
`follow_my_reading` repo. Production-derived → **gitignored** (real user
transcripts + learner ids); only the slim public `quran_ref.json` is committed.

Current snapshot: 258 reviewed rows (254 Quran, 4 non-Quran). **The dataset is
frozen when review is finished**, then hashed
(`runs/inputs.sha256`); all trials run on that one version. Do not change the
dataset mid-study. Recompute the baseline and oracle floor at freeze time.

### Labeling conventions (must hold for every row)

1. **Exclude leading isti'adha and basmala** from gold segment text — they are not
   recited ayah text. (Exception: Al-Fatiha, where the basmala *is* ayah 001001.)
   The concatenated split should reproduce the recited transcript *minus* that
   prefix. *Known fix needed:* row `fcdb0888` currently includes the basmala.
2. **Repetition is allowed.** If the reciter repeats ayahs, the split may repeat
   ids in sequence (e.g. `f6c38e66`, Al-Ikhlas ×3). Detection scores the id set,
   so this is not penalized; the repeated segments matter for Stage 2.
3. **Split id set equals assignment id set.** `ayah_assignment` is the unique
   Quran id set, represented as a single id, contiguous range, or comma-separated
   non-contiguous ids; `transcript_split_by_ayahs` is the per-ayah (possibly
   repeated) sequence.
4. **Confidence** `high`/`medium` are scored; `low` is excluded (kept in file).
5. `actual_ayahs` is human reference only — **never** read by the algorithm or
   used for scoring.

## 5. Conditions (independent variable)

The agent. **This study compares two conditions**, tagged via `AR_AGENT` (logged
in every row):

- `claude` — Claude Code (Study 1 & 2: Claude Opus 4.8, reasoning effort `high`)
- `codex` — OpenAI Codex (Study 1 & 2: GPT-5.5, reasoning effort `high`)

A `human` baseline and a `claude+skill` arm (Claude Code + the
uditgoenka/autoresearch skill) are **deferred to future work** — out of scope
here to keep the A/B clean.

Pin and report for each: model id + build date, permission mode (full-auto),
reasoning effort, CLI version. **Recorded (Study 2 runs, 2026-07-05):** Claude
Code v2.1.198 (Opus 4.8, effort `high`, `--dangerously-skip-permissions`);
Codex CLI v0.139.0 (GPT-5.5, effort `high`, `-s workspace-write -a never`).
Machine: the same MacBook Pro for both arms. **Reasoning effort is matched across arms:** Claude
`high` and Codex `high`. The scales differ (Claude: low/medium/high/xhigh/max;
Codex: low/medium/high/xhigh) but `high` is the same named tier on both.

## 6. Protocol

Per agent, per run *k*:

1. Fresh branch `autoresearch/<agent>-<tag>-r<k>` from `main`; reset `solution.py`
   to the committed stub so every run starts identical.
2. `export AR_AGENT=<agent>`; launch the agent in the repo (README §Launching).
3. Agent reads `PROGRAM.md` and loops autonomously, logging each experiment with
   `make exp` (uniform schema → directly comparable).
4. **Run in ONE uninterrupted session** — see §9 (wall-clock validity).
5. `make archive AGENT=<agent>` → `runs/<agent>-<tag>-r<k>.tsv`.

**Budget** (held constant across all runs and agents): **30 experiments or 1 hour,
whichever comes first** — iteration-primary, with the hour as a wall-clock safety
stop. Report at both a fixed-iteration checkpoint (e.g. exp 30) and a fixed-time
checkpoint (e.g. 1 h). This is a deliberately small budget: it makes the full
3×2 matrix cheap to run first; scale up later if results warrant.

**Stopping rule:** budget reached, or plateau (≈15 consecutive non-improving
experiments).

**3 runs per agent → 6 runs total (3 Claude + 3 Codex).** LLM agents are
stochastic; report every run, not the best.

Compare: `make compare RUNS="runs/claude-*.tsv runs/codex-*.tsv"` → `comparison.png`
(best-so-far vs experiment and vs wall-clock, with the oracle-floor line).

## 7. Metrics (dependent variables)

| Class | Metric | Source |
|---|---|---|
| Quality | best `research_score`; component errors at best | min over run |
| Sample efficiency | experiments to threshold (e.g. <0.5); AUC of best-so-far curve | log |
| Wall-clock efficiency | time to threshold; best score at the fixed-time checkpoint | `elapsed_sec` |
| Process | # experiments, keep rate, crash rate, mean iteration time | log |
| Cost | tokens / USD per run (if exposed) | agent side |
| Artifact | final `solution.py` LOC; qualitative taxonomy of strategies tried | git diff + `description` column |

The `description` column is the qualitative record of *what each agent tried* —
read it to taxonomize approaches (n-gram detection, DP alignment, prefix
handling, abstention heuristics, …).

## 8. Statistics

Small N (3 per arm) → report **mean ± std across runs** and plot every run. For
"is A better than B," use a nonparametric test (Mann–Whitney U) on per-run best
scores. With 3 vs 3 the best achievable p is 0.05 (complete separation), so treat
significance cautiously and lean on effect size + the per-run curves. Do not
over-claim from N=3.

## 9. Controls, confounds, validity

**Held fixed:** harness, dataset hash, starting `solution.py`, `PROGRAM.md`,
machine. **Tooling parity:** both agents get shell + file edit + git, nothing
more — no extra skills/plugins in the core A/B.

**Confounds to record:** model id+date, settings, CLI version, hardware.

**Wall-clock validity (lesson from the pilot).** `elapsed_sec` is only meaningful
when a run executes in one continuous autonomous session. The pilot run spanned
multiple conversation turns, inflating its time axis to ~65 min of mostly idle
time. *Formal runs must be single, uninterrupted sessions* (a reason to use a
long-lived session / server for overnight or parallel runs).

**Threats to validity:**
- *Ceiling effect.* Small dataset with a 0.0 oracle floor; if both agents saturate,
  differences compress. Mitigate by growing/cleaning the dataset and by reporting
  curve shape (sample efficiency), not only the final score.
- *Transcript-only / ASR-confound.* The metric measures detection+split fidelity,
  not true recitation correctness; it is harakat-blind by construction.
- *Prior knowledge.* Both agents have the Quran memorized from pretraining; this
  is equal across conditions and the task is algorithm engineering against a
  held-out metric, not Quran recall. Worth a sentence in the paper.
- *Single task/domain.* Generalization claims need more tasks.
- *Stochasticity.* Mandates multiple runs.

## 10. Pilot run (preliminary result)

One Claude Code run, 5 experiments (`runs/claude-260628-1931.tsv`, branch
`autoresearch/jun25`):

| exp | change | research_score | status |
|----|---|---|---|
| 1 | baseline abstain stub | 2.000 | keep |
| 2 | bigram-anchor detection + proportional split | 1.683 | keep |
| 3 | DP (Needleman–Wunsch) alignment split | 1.656 | keep |
| 4 | **strip leading isti'adha/basmala** | **0.535** | keep |
| 5 | abstain on low alignment match-rate | 0.561 | discard |

At best (exp 4): detection 84%, split 96%, abstain 2/3.

**Lessons.**
- The harness *discriminates* and rewards real insight: one conceptual fix
  (prefix strip) moved the score 1.66 → 0.54, far more than mechanical tweaks.
- DP alignment beat proportional splitting only marginally at this stage.
- A plausible idea can regress (the match-rate abstain guard) — the keep/discard
  mechanic correctly reverted it. Good: the loop is self-correcting.
- Remaining headroom to the floor is detection misses + non-Quran abstention —
  enough to discriminate agents, wider if the dataset grows.

## 11. Out of scope (future work)

**Stage 2 — mistake detection.** Operates on a *single* gold ayah chunk +
reference, detecting substitution/deletion/insertion. Scored separately so split
errors do not pollute it. Needs a gold `mistakes` field that does not yet exist;
the mistake taxonomy is still to be defined. Transcript-only → cannot catch
vowel/tajweed errors.

## 12. Study 2 — held-out generalization (planned)

Study 1 scores agents on the same 254 rows they optimize, and `eval.py` prints
expected ids in its failure report — which *rewards memorization*. Codex exploited
this (per-recording hardcoding, e.g. a garbled-transcript→id lookup); Claude did
not, and stopped early. Through ~exp 13 both arms held comparable *general*
algorithms (~0.04–0.09); Codex's final 0.006 came from non-generalizing test-row
fixes. Study 2 measures **generalization**:

- **Train/test split.** Implemented in `tools/split_dataset.py` (seed 42,
  deterministic): 151 train / 107 test, stratified by (surah, length bucket);
  repetition and non-contiguous rows allocated 60/40 within their own groups;
  non-Quran split 2/2; cross-surah label quirks pinned to train so test is
  clean. The loop scores `research_score` on **train only**.
- **Close the leak.** The failure report shows `recording_id` + predicted ids
  only — never the expected ids.
- **Held-out scoring.** After each run, *we* (not the agent) score the final
  `solution.py` on the untouched test set. Report the **test** score; the
  train↔test gap quantifies overfitting per agent.
- **Both agents are told** (identically, in PROGRAM.md) that a held-out test set
  exists and that memorizing train rows will not transfer — so Study 2 also tests
  whether disclosure changes optimization behavior.
- Train floor ~0.007 (quirk rows pinned to train); test oracle floor exactly 0.0.
- Re-run 3 Claude + 3 Codex. Hypothesis: the raw-score gap collapses (or reverses)
  on held-out data, and Codex shows the larger train↔test gap.

**Isolation postmortem (2026-07-02).** The first Study 2 attempts leaked and were
discarded: (a) a Claude run was launched in the main repo, where `data/test.csv`
was visible; (b) a Codex run in a git *worktree* used the shared git database to
read Study 1 run logs (committed under `runs/`) and the in-flight Claude solution
on a sibling branch (`git show`) — resourceful, not forbidden by PROGRAM.md, but
fatal to independence. Isolation is now a **fresh single-commit clone** per run
(`tools/new_run.sh`): harness snapshot + train split only; no shared `.git`, no
other branches, no logs, no test set. **Retroactive threat to Study 1:** its runs
shared one `.git`, so later runs (Codex ran after Claude) could in principle have
browsed earlier run branches; session transcripts should be audited. Study 1's
overfitting conclusion rests on code-artifact analysis (hardcoded ids), which is
unaffected.

**No existing data is held-out.** The `follow_my_reading` test manifest is NOT
usable as a held-out set: 20/22 of its cases are the same recordings/transcripts
as dataset rows (verified by fuzzy transcript match, ratios ≥0.94). The held-out
set must come from partitioning the 258 rows — or from labeling *new* production
recordings made after the 2026-06 export, which would be a genuinely unseen,
same-distribution test set.

## 13. Reproducibility bundle (per run)

- archived `runs/<agent>-…​.tsv`,
- the run branch (each commit = one experiment) + final `solution.py`,
- the agent session transcript,
- `runs/inputs.sha256` (dataset + eval hashes),
- model id + date + settings.
