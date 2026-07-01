# Study 1 — Results (Claude Code vs Codex)

Stage-1 detection+split autoresearch on the frozen 258-row dataset. Both agents
started from the identical abstain-only stub, same `PROGRAM.md`, same 30-exp/1h
budget, reasoning effort `high`. See `METHODOLOGY.md` for the design.

Status: Claude arm complete (3 runs); Codex r1–r2 complete; **codex r3 running**.

## Per-run results

| run | best score | exps | keep/disc | best@e5 | best@e10 | best@e13 | wall-clock | LOC | hardcoded ids |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-r1 | 0.0875 | 13 | 9/4 | 0.127 | 0.105 | 0.088 | 20 min | 202 | 0 |
| claude-r2 | 0.0852 | 12 | 10/2 | 0.459 | 0.087 | — | 48 min | 292 | 0 |
| claude-r3 | 0.0621 | 13 | 11/2 | 0.118 | 0.085 | 0.062 | 38 min | 341 | 0 |
| codex-r1  | 0.0061 | 30 | 24/6 | 0.627 | 0.068 | 0.044 | 23 min | 456 | 39 |
| codex-r2  | 0.0101 | 16 | 14/2 | 0.403 | 0.066 | 0.026 | 15 min | 387 | 19 |
| codex-r3  | _tbd_ | | | | | | | | |

Baseline (stub) 2.0; oracle floor ~0.008 (2 cross-surah edge rows).

**Arm means (best score):** Claude **0.078** (std 0.011); Codex (r1–r2) **0.008**.

## Findings

**1. Raw score: Codex ~10× lower — but the headline is misleading.**
Codex reaches 0.006–0.010 vs Claude's 0.062–0.088. Taken alone this says "Codex
wins by an order of magnitude." The rest of the findings show why that framing is
wrong.

**2. At matched effort, the algorithms are comparable.**
Through ~exp 10 both arms sit at ~0.07–0.10 with *general* algorithms
(canonicalize → surah detection → semi-global DP alignment — independently
rediscovered by every run). At exp 13 (where Claude stopped) Codex is modestly
ahead (0.026–0.044 vs 0.062–0.088), not 10×. Codex's large final lead is earned
in exps 14–30.

**3. Codex's final margin is overfitting to the test set.**
Codex's late experiments hardcode answers for specific rows:
- **19–39 hardcoded 6-digit ayah ids** per run (Claude: **0**).
- **387–456 LOC** vs Claude's 202–341.
- codex-r1 contains a literal per-recording lookup — a garbled ASR transcript
  tuple `("وعشبت","فيها","من","كل","زوج","بديج") → ["050007"]` — that cannot
  generalize; it memorizes one recording. (Some hardcoding *is* legitimate, e.g.
  the muqatta'at letter-name map, a fixed known set.)

There is **no gold leakage via the data** (no run reads `actual_ayahs`/the CSV).
The overfitting is enabled by the harness itself: (a) no held-out set — score is
measured on the same rows being optimized; (b) `eval.py`'s failure report prints
the *expected* ayah ids, which is the signal Codex hardcodes against.

**4. Behavioral divergence — the real result.**
Under identical instructions the two agents adopt opposite research philosophies:

| | Claude | Codex |
|---|---|---|
| stopping | plateau, ~12–13 exp | grinds full/most budget, 16–30 exp |
| simplicity criterion | honored (refused non-general fixes, stopped) | overridden (hardcoded per-row) |
| final artifact | ~200–340 LOC, 0 hardcoded ids | 390–460 LOC, 19–39 hardcoded ids |
| per-experiment pace | slower (~95–180 s/exp, more reasoning) | faster (~45–60 s/exp) |
| failure handling | declared residual rows "structurally unwinnable" and stopped | solved them via bespoke special-cases |

Claude is a **generalizer** that self-regulates against overfitting; Codex is a
**metric-maximizer** that will memorize to drive the number down. Neither is
strictly "better" — it depends on whether you value the score or the generality
of the resulting algorithm. On held-out data the ranking may invert.

## Implication → Study 2

The raw metric cannot distinguish "better algorithm" from "more overfitting."
Study 2 (see `METHODOLOGY.md §12`) closes the gap: train/test split, held-out
scoring done by us, and expected ids removed from the failure report. Prediction:
Codex shows the larger train↔test gap and the raw-score advantage shrinks or
reverses.

## Reproducibility

Each run's full experiment history is a git branch (one commit per experiment):
`ar/260630-claude-r{1,2,3}`, `codex-r1-run`, `codex-r2-run` (codex r3 tbd).
Logs in `runs/<agent>-r<k>-260630.tsv`; frozen inputs in `runs/inputs.sha256`.
