# Run log — granular-100x100-v1.0

Every attempt against this corpus version, partial and full, including excluded
ones: what ran, what happened, what it scored, and why it counts or does not.
Gold is read once per run recorded here, and the count matters, because choosing
which run to report is itself a selection over the holdout.

Corpus: 100 train / 100 gold, all owner-approved, 290 / 179 annotated events.
Evaluator: eval21 v2.3. Workspace regime: annotated train split visible.
Per-case gold detail is private (`granular-corpus/analysis-20260917/`); this file
carries aggregates only.

## All attempts at a glance

| # | model | status | working time | passes | train | gold | gap |
|---|---|---|---|---:|---:|---:|---:|
| — | deployed `event_detection.py` | production baseline | earlier study | — | — | 0.7844 | — |
| 1 | Opus 5 | excluded: single pass, protocol did not run | ~7 min | 1 | 0.7756 | 0.8621 | +0.087 |
| 2 | Opus 5 | **reported** | 29.7 min | 1 + 23 | 0.9463 | **0.9157** | −0.031 |
| 3 | Fable 5.1 | excluded: host slept; gold read afterwards on request | ~17 min | 1 + 3 | 0.9585 | 0.9448 | −0.014 |
| 4 | Fable 5.1 | **reported** | 30.2 min | 1 + 31 | 0.9948 | **0.9051** | −0.090 |

Gold has been read five times: runs 1–4, and the deployed baseline once for the
deployment comparison below. Runs 2–4 were re-scored for the failure analysis;
re-scoring a frozen solution adds no selection.

## What took place

The harness changed between attempts, and several of those changes were forced
by failures found only by running it. In order:

1. **Inputs-only workspace replaced by an annotated train split** (`800703a`).
   The agent had been given 24 hand-made teaching events and a scalar score, and
   never saw the 290 real annotations it was scored against. A first attempt at
   exporting them leaked absolute private paths, production recording ids, review
   metadata and notes naming held-out cases; the export became a field allowlist
   that aborts if any held-out case id appears.
2. **Run 1 stopped after one pass.** `claude -p` is a single non-interactive
   pass, and "You have 30 minutes" in TASK.md was prose nothing enforced. No
   transcript or timing existed to show it; only an mtime did.
3. **Run records and a real time limit** (`bc36384`, `3ed23a3`). Transcripts,
   start/end/elapsed/exit, and a fix to a budget that could not fire on a hung
   run, because reading the agent's output inline blocked until it exited.
4. **A continuation loop** (`5b9b34b`) so the budget is spent: one pass, then
   `claude -c` passes inside the container, where session state survives. Testing
   it with a stub found it would spin twenty thousand times in ten seconds if a
   pass returned instantly with status 0; every pass is now floored.
5. **Gold gated on protocol** (`7d320d2`): confirm from the launch record and
   transcript that a run executed as specified before grading it on gold.
6. **Run 3 lost half its time to sleep.** The Mac idle-slept for 1906 of 2928
   seconds; the in-container deadline kept counting. `caffeinate` now holds for
   the whole launch and the launcher records `host_suspended_seconds` (`6f9dcdd`).
7. **Run 4 overfit.** Thirty-one passes of keep-if-train-improves drove train to
   0.9948 and gold to 0.9051. The continuation prompt, written for this harness,
   told the agent to keep a change only if train micro F1 rose and not to stop
   early — both of which reward fitting once train has nothing left to teach, and
   the second of which contradicts Study 1's own stopping rule.
8. **Stopping rule and unseen-set framing** (this change): see
   *Protocol for the next run*.

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


---

## Run 4 — 2026-09-16 — Fable 5.1 — **REPORTED**

| | |
|---|---|
| workspace | `260917-fable51-r2` |
| solution | `ca226574a4f6db232a6cba44ae21ed3f7035f1e7b1e4a5a58be7400933c212a9` |
| used | 1815s (92%), host suspended 1s, not interrupted |
| passes | 1 initial + 31 continuations |
| transcript | `260917-fable51-r2.owner.20260916-212306.run.log` |

The rerun of run 3, and as committed before it was launched, the Fable result
that is reported -- although run 3's partial solution scored higher on gold.

| | train | gold | Δ |
|---|---|---|---|
| micro F1 | 0.9948 | **0.9051** | **−0.090** |
| exact-span F1 | 0.9740 | 0.8780 | −0.096 |
| macro F1 | 0.9887 | 0.8554 | −0.133 |
| localization F1 | 0.9948 | 0.9160 | −0.079 |

| label | train n | train F1 | gold n | gold pred | gold F1 |
|---|---:|---:|---:|---:|---:|
| substitution_mistake | 106 | 1.00 | 67 | 68 | 0.89 |
| omission_mistake | 47 | 1.00 | 25 | **34** | **0.81** |
| repetition_benign | 29 | 0.96 | 18 | 18 | 1.00 |
| spelling_benign | 55 | 1.00 | 11 | 11 | 0.91 |
| isti3adha / basmala | 17 / 13 | 1.00 | 28 / 16 | | 1.00 |
| substitution_corrected | 8 | 1.00 | 5 | 5 | 1.00 |
| omission_corrected | 7 | 0.92 | 2 | 3 | 0.80 |
| letters_benign | 2 | 1.00 | 4 | 3 | 0.86 |
| insertion_mistake | 6 | 1.00 | 3 | 4 | **0.29** |

**Reading it: this run overfit train.** It reached 0.9948 on train -- every
in-unit discrepancy resolved, precision 1.000 -- and lost 0.090 on gold, three
times Opus's gap. The same model, on the same task, stopped by accident after
three continuation passes, scored 0.9448 on gold; thirty-one passes of
keep-if-train-improves took it to 0.9051.

The transcript shows how. Several kept changes were fitted to one or two
recordings, which the agent sometimes said outright: a forward window set to two
words because "every accepted restored-omission case in the data jumps at most
two", chosen to separate exactly two units; an attempt boundary keyed on a
restart distance found by diffing two units; a dedupe rule; a wasl rule written
around one misfiring word. Each was a defensible reading of the data. Together
they encode train's particular cases. `omission_mistake` over-predicts on gold
(34 for 25), the clearest single sign.

From pass 13 on, the agent reported "no in-unit discrepancies left on the train
split" and spent the remaining eighteen passes on probes that could not move the
number -- robustness rules for patterns absent from train, each reverted because
the rule kept only changes that improved train. Several of those, such as the
longer isti'adhah with السميع العليم, are plausible gains on unseen recordings.
The keep rule could not see that.

Audit clean. Notes are letter names, particles, and the article.

---

## Summary across reported runs

| run | model | passes | train | gold | gap |
|---|---|---:|---:|---:|---:|
| 2 | Opus 5 | 23 | 0.9463 | **0.9157** | −0.031 |
| 4 | Fable 5.1 | 31 | 0.9948 | **0.9051** | −0.090 |

The reported Opus and Fable numbers are within what 179 gold events can
separate. The result worth reporting is about the loop, not the models: its
keep-if-train-improves rule rewards fitting once train stops being informative,
and the run that drove train closest to 1.0 lost the most on held-out data — while
the same model, stopped by accident after three continuation passes, scored
0.9448.

---

## Where the solutions fail on gold

Aggregates; per-case detail is private. Failure rows count a wrong-label match
once as a false positive and once as a false negative.

| solution | gold F1 | failure rows | recordings affected |
|---|---:|---:|---:|
| deployed | 0.7844 | 64 | 22 |
| run 2, Opus | 0.9157 | 28 | 14 |
| run 3, Fable partial | 0.9448 | 19 | 8 |
| run 4, Fable | 0.9051 | 33 | 14 |

The failures fall into five families, shared across solutions in different
proportions:

1. **Event granularity on long garbled passages.** When a reciter substitutes
   the ending of a different ayah, or skips a clause and garbles the next,
   gold groups by what the reciter was doing — one substitution over a
   replaced passage, or an omission plus a substitution. Alignment-first
   solutions group by token similarity, pairing locally similar words across the
   passage into several small events, or merging an omission into a neighbouring
   substitution. The largest source for runs 2 and 3: eleven of run 3's nineteen
   rows come from three such recordings.
2. **Kind of self-correction.** Repetition against corrected substitution, and
   corrected substitution against corrected omission, decided within a few
   tokens of a restart.
3. **An extra word: insertion or failed attempt.** A stray word before the
   target is sometimes gold's substitution linking two attempts, sometimes an
   insertion.
4. **Input robustness.** Muqatta'at letter names written with an attached Arabic
   comma defeat exact matching. Run 3 turns one such token into a substitution;
   run 4 turns a comma-separated letter sequence into an omission of the whole
   opener. The recogniser emits punctuation, so this recurs in production.
5. **Fitted rules that do not transfer (run 4).** Fifteen spurious predictions,
   ten of them `omission_mistake` against one for run 3: a five-letter opener run
   3 handled and run 4 missed; joined or portmanteau words split into a
   substitution plus an omission despite a rule written for exactly that, fitted
   on train examples; single-word omissions invented beside repeats. These are
   regressions introduced after run 3's stopping point.

The deployed solution fails mostly on span placement (26 gold events overlapped
but mislocated) and on orthography: eight `spelling_benign` events reported as
mistakes, because it was built on the folded reference and cannot see the
hamza distinctions the current reference preserves.

---

## What is hardcoded

Every solution audits clean: no case ids, ayah ids, transcript literals or I/O.
What each does encode:

| | run 3, Fable partial | run 2, Opus | run 4, Fable |
|---|---|---|---|
| lines | 511 | 627 | 468 |
| opening formulas | isti'adha and basmala word lists | same | same |
| muqatta'at | letter-name table | letter-name table with variant spellings | letter-name table |
| orthographic word lists | 5 words with a silent final alif; 21 with an elided final yā'; the إذا/إذن pair | 18 words the mushaf spells with open tā' | 8 silent-final-alif words; 11 wasl nouns |
| other lists | — | 6 article/clitic prefixes | 7 particles; 11 attached pronouns |
| folding | hamza seats, alif forms | hamza seats, ة/ه, ى/ي | hamza seats, alif forms, ة/ه, ى/ي |
| numeric constants | 10 costs and thresholds | 5 thresholds | 8, including a 1e9 sentinel |

The word lists are facts about Quranic orthography rather than copies of the
data. For run 3, the deployment candidate, this was checked: of its twenty-six
listed words, three occur anywhere in the train transcripts or references, and
none in gold. That is the pattern the rules
allow — knowledge the agent brought, not answers it read.

What the tables cannot show is the fitting inside ordinary code: a window of two
words chosen because it separates two training units, an attempt boundary keyed
on a distance found by diffing two units, a dedupe rule. Those are thresholds
and conditions, not literals, and an audit for literals does not see them. Run
4's transcript names several; its gold gap is where they show.

---

## Deployment candidate

Run 3's solution, `f9509aac13c77b27a120d74ab32c09366acd2b6e741aa828dbd316366ad03653`.

| | gold F1 | vs run 3, paired bootstrap over recordings |
|---|---:|---|
| **run 3, Fable partial** | **0.9448** | — |
| run 2, Opus | 0.9157 | +0.029, 95% CI [−0.030, +0.093], P(better) 0.83 |
| run 4, Fable | 0.9051 | +0.040, 95% CI [−0.005, +0.084], P(better) 0.96 |
| deployed | 0.7844 | +0.159, 95% CI [+0.073, +0.248], P(better) 1.00 |

Why this one:

- **It is the only clear improvement over production that is also the best
  point estimate.** Every candidate beats the deployed solution by a margin whose
  interval excludes zero; run 3 by the most.
- **It is the least fitted.** Its train/gold gap is −0.014, against −0.031 and
  −0.090; it kept fewer changes on train evidence, and its word lists come from
  orthography rather than the data.
- **It fits production without adaptation.** It reads only `chunk_idx`,
  `transcript_tokens` and `reference_tokens`, all of which the production
  adapter supplies; the production reference matches the corpus reference on all
  984 units; latency is median 0.3 ms, p95 9 ms, max 36 ms per ayah, comparable
  to the deployed solution.

Caveats that belong with the choice:

- Its lead over Opus is not significant; the bootstrap interval spans zero. The
  choice rests on the point estimate and the smaller gap, not on a demonstrated
  difference.
- Selecting the best of three on gold makes 0.9448 an optimistic estimate of its
  production accuracy. For deployment that is acceptable; it means gold no longer
  gives an unbiased figure for the deployed system, and a fresh sample of bot
  recordings would.
- It remains excluded as a *study* result. Deploying it is an engineering
  decision and does not change what is reported for the experiment.
- Known gap to close at deployment: attached punctuation on tokens. Stripping
  punctuation characters inside each token in the adapter, without removing
  tokens, keeps span indices valid and should remove the attached-punctuation cases; it needs checking on the corpus before it ships.

---

## Protocol for the next run

Changes made after run 4, before any further gold reading:

- **TASK.md states the evaluation up front**: the solution is scored on 100
  unseen recordings, the workspace is for development only, and a rule that
  fixes one or two training recordings will usually not help there. The
  development strategy asks, before keeping a change, how many training
  recordings it affects, and allows robustness rules for patterns absent from
  train to be kept on judgement.
- **Study 1's stopping rule is enforced**: stop after 15 consecutive experiments
  without improvement. `score.py` appends every scoring to `.scores.jsonl`, and
  the loop counts distinct solution versions scored since the last new best —
  from the history, not from the agent's account. Re-scoring an unchanged file is
  not an experiment; reverting to an older one is.
- **The continuation prompt no longer demands keep-only-if-improved and forbids
  stopping.** It reports the plateau count, restates the unseen evaluation, asks
  for a change expected to hold there, and allows the agent to stop when it has
  none.

What these do not do: the plateau rule stops a run that has stopped improving,
and run 4's fitted changes were made while train was still improving. The
framing and the prompt address that directly but depend on the agent heeding
them. A development split held out from train — scored by the harness and used
to decide whether a change is kept — would enforce it, and remains the stronger
fix if the next run's gap is still large.
