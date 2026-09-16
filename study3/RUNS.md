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

## Run 2 — 2026-09-16 — Opus 5 — **REPORTED**

| | |
|---|---|
| workspace | `260917-opus5` |
| solution | `e0505f5cdf74430007e42cc3ab1479820319b32aad1b597491e8f6c847647569` |
| budget | 1800s loop inside a 1980s launcher limit |
| actually used | 1779s (90%), not interrupted, no timeout |
| passes | 1 initial + 23 continuations |
| changes | 47 attempted, 20 kept, 27 reverted |
| transcript | `260917-opus5.owner.20260916-194802.run.log` |

Same corpus, workspace regime and TASK.md as run 1. The differences are in the
harness only, and were decided without reference to run 1's gold result: an
in-container continuation loop so the budget is actually spent, and a transcript
with timing so that can be confirmed. Protocol was confirmed from the launch
record and transcript before gold was read.

| | train | gold | Δ |
|---|---|---|---|
| micro F1 | 0.9463 | **0.9157** | −0.031 |
| exact-span F1 | 0.9185 | 0.8933 | −0.025 |
| macro F1 | 0.9489 | 0.9050 | −0.044 |
| localization F1 | 0.9775 | 0.9270 | −0.051 |

| label | train n | train F1 | gold n | gold F1 |
|---|---:|---:|---:|---:|
| substitution_mistake | 106 | 0.94 | 67 | 0.88 |
| omission_mistake | 47 | 0.98 | 25 | 0.94 |
| spelling_benign | 55 | 0.91 | 11 | 0.91 |
| repetition_benign | 29 | 0.94 | 18 | 0.84 |
| isti3adha_benign | 17 | 1.00 | 28 | 1.00 |
| basmala_benign | 13 | 1.00 | 16 | 1.00 |
| substitution_corrected | 8 | 0.93 | 5 | 0.91 |
| omission_corrected | 7 | 0.92 | 2 | 1.00 |
| insertion_mistake | 6 | 0.86 | 3 | 0.57 |
| letters_benign | 2 | 1.00 | 4 | 1.00 |

**Reading it.** The gain over run 1 on gold, 0.8621 → 0.9157, comes from
iteration within the same task, not from anything learned about gold. The
−0.031 train/gold gap is the expected cost of the loop's selection rule: 47
candidate changes were each kept only if they raised train micro F1, and that is
selection on train, however principled each individual change. The gap is
small, and the largest per-label drops are on the two biggest labels, not the
rare ones.

Labels with fewer than ten gold events -- `substitution_corrected` 5,
`insertion_mistake` 3, `omission_corrected` 2, `letters_benign` 4 -- cannot be
estimated at this support; one event moves `insertion_mistake` by roughly 0.2.
Report them with their counts, not as findings.

**The agent's own account needs two corrections.** Its closing summaries say
"thirteen kept changes out of 47"; its own per-pass tables mark twenty kept. And
it stated at every pass that the file had no file access, which is true, while
the audit reported `FAIL file or network access: open`. The audit was wrong:
it matched the bare word `open` in a comment about the Arabic open tā' (تاء
مفتوحة). The syntax tree confirms imports are `difflib` and `re` only, with no
I/O call anywhere. The audit's I/O check is now AST-based and still catches a
real `open()`, `Path.read_text()`, `import os`, `__import__` and `eval`. Both
frozen solutions re-audit clean.

Audit notes: `الف`, `سين`, `صاد`, `لام` -- muqatta'at letter names, which the
rules permit as linguistic tables.

---

## Run 3 — 2026-09-16 — Fable 5.1 — **EXCLUDED, host slept; gold read afterwards on request**

| | |
|---|---|
| workspace | `260917-fable51` |
| solution | `f9509aac13c77b27a120d74ab32c09366acd2b6e741aa828dbd316366ad03653` |
| wall-clock span | 2928s |
| awake | 1022s |
| host suspended | 1906s |
| passes | 1 initial + 3 continuations |

**Excluded because the Mac went to idle sleep** at 20:41:52 UTC, about fifteen
minutes in, during continuation pass 3 (`pmset -g log`: *Entering Sleep state
due to 'Idle Sleep'*). The container was frozen with it, but the loop's deadline
is read from the container's wall clock, which jumped forward on wake. The loop
concluded the budget was spent after roughly seventeen minutes of real work,
against thirty for Opus in run 2. The two are not comparable, so the held-out
split was not read.

The criterion is environmental and fixed before any held-out result: the run
did not receive its budget. Train was graded, because it costs the holdout
nothing and confirms the agent's report: micro F1 **0.9585**, exact-span 0.9412,
macro 0.9342. Audit clean; notes `اذا`, `ال` are a spelling variant and the
article.

Checked retroactively, run 2 lost 27s of wall time to launch overhead, not
sleep, and stands.

Harness fixes: `run_iterating_agent.sh` holds `caffeinate -is` for the life of
the launch, and the launcher records `host_suspended_seconds` -- wall-clock span
minus monotonic time, which stops while macOS sleeps -- and warns against
grading a run where it exceeds a minute.

**Gold read afterwards, on the owner's request (gold reading 3).** Recorded
here before the rerun, so that the rerun's number cannot be chosen against it.
The rerun, `260917-fable51-r2`, is the Fable result that will be reported,
whichever of the two scores higher. This one stays excluded: its criterion was
fixed before it was read.

| | train | gold | Δ |
|---|---|---|---|
| micro F1 | 0.9585 | **0.9448** | −0.014 |
| exact-span F1 | 0.9412 | 0.9282 | −0.013 |
| macro F1 | 0.9342 | 0.9117 | −0.023 |
| localization F1 | 0.9654 | 0.9503 | −0.015 |

| label | gold n | gold F1 |
|---|---:|---:|
| substitution_mistake | 67 | 0.92 |
| omission_mistake | 25 | 0.96 |
| repetition_benign | 18 | 0.97 |
| spelling_benign | 11 | 1.00 |
| isti3adha / basmala / letters | 28 / 16 / 4 | 1.00 |
| substitution_corrected | 5 | 0.80 |
| omission_corrected | 2 | 0.80 |
| insertion_mistake | 3 | 0.67 |

Worth recording as an observation, not a result: on seventeen minutes of work
and three continuation passes, this solution scores above the fully-budgeted
Opus run on gold (0.9448 against 0.9157), with a smaller train/gold gap (−0.014
against −0.031). Fewer kept changes means less selection on train, which fits a
smaller gap; the rerun will show whether the extra time closes, holds or widens
it.

