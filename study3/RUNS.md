# Run log — granular-100x100-v1.0

Every measured run against the held-out split, including excluded ones. Gold is
read once per run recorded here; the count matters, because choosing which run
to report is itself a selection over the holdout.

Corpus: 100 train / 100 gold, all owner-approved, 290 / 179 annotated events.
Evaluator: eval21 v2.3. Workspace regime: annotated train split visible.

---

## Run 1 — 2026-09-16 — Opus 5 — **EXCLUDED, pilot**

| | |
|---|---|
| workspace | `260916-opus5` |
| solution | `f223441e6fb76372f09a7efbad8394d962be4a1abe5019af65004cc7c47482cd` |
| budget | 1800s |
| actually used | ~420s (~23%) |
| command | single `claude -p` pass |

**Excluded because the protocol did not run.** `claude -p` is one
non-interactive pass: it worked a single turn and exited after roughly seven
minutes of a thirty-minute budget. Nothing timed it out — the agent reported
"Time's up" but the launcher never hit its deadline. The harness of the day also
captured no transcript and recorded no timing, so the early stop was only
visible from the mtime on `solution.py`.

The exclusion criterion is the unused budget, which is independent of the score.
Worth stating plainly: this run scored **0.8621** on gold, better than the train
number, so it is a favourable result being set aside for a protocol failure —
not a disappointing one being explained away.

Scores, retained for the record and not reported as a result:

| | train | gold |
|---|---|---|
| micro F1 | 0.7756 | 0.8621 |
| exact-span F1 | 0.7576 | 0.8506 |
| macro F1 | 0.6627 | 0.6880 |
| localization F1 | 0.8654 | 0.8793 |

Audit clean: no memorised case ids, ayah ids, transcript literals or I/O.

What it established, which is why it was worth running: the harness works
end to end, the annotated-train workspace exports nothing private, the
evaluator round-trips the shipped data at 1.000, and `letters_benign` reached
0.86 on gold from two training examples — the muqatta'at table generalising
where data was nearly absent.

Harness defects it exposed, fixed in `bc36384` and `3ed23a3`: no run transcript,
no timing record, a time budget that could not fire on a hung run, and a
per-label report that labelled every split's reference column "gold".

---

## Run 2 — pending

Same corpus, same workspace regime, same TASK.md. Differences are harness-level
only and were decided without reference to run 1's gold result: an in-container
continuation loop so the budget is actually spent, and a transcript to confirm
it was.
