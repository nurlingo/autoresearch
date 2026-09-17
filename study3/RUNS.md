# Run log — granular-100x100-v1.0

Every attempt against this corpus version, partial and full: what ran, what
happened, and what it scored. All four runs are reported, each with its status —
completed, or interrupted and why — because each shows something the others do
not.
Gold is read once per run recorded here, and the count matters, because choosing
which run to report is itself a selection over the holdout.

Corpus: 100 train / 100 gold, all owner-approved, 290 / 179 annotated events.
Evaluator: eval21 v2.3. Workspace regime: annotated train split visible.
Gold results are described in general terms only; no held-out case is identified.

## All attempts at a glance

| # | model | status | working time | passes | train | gold | gap |
|---|---|---|---|---:|---:|---:|---:|
| — | deployed `event_detection.py` | production baseline | earlier study | — | — | 0.7844 | — |
| 1 | Opus 5 | completed — single pass, no continuation loop yet | ~7 min | 1 | 0.7756 | 0.8621 | +0.087 |
| 2 | Opus 5 | completed | 29.7 min | 1 + 23 | 0.9463 | 0.9157 | −0.031 |
| 3 | Fable 5.1 | interrupted — host slept after ~17 min | ~17 min | 1 + 3 | 0.9585 | 0.9448 | −0.014 |
| 4 | Fable 5.1 | completed | 30.2 min | 1 + 31 | 0.9948 | 0.9051 | −0.090 |

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

## Run 1 — 2026-09-16 — Opus 5 — **completed, single pass**

| | |
|---|---|
| workspace | `260916-opus5` |
| solution | `f223441e6fb76372f09a7efbad8394d962be4a1abe5019af65004cc7c47482cd` |
| budget | 1800s |
| actually used | ~420s (~23%) |
| command | single `claude -p` pass |

**The budget was not used.** `claude -p` is one
non-interactive pass: it worked a single turn and exited after roughly seven
minutes of a thirty-minute budget. Nothing timed it out — the agent reported
"Time's up" but the launcher never hit its deadline. The harness of the day also
captured no transcript and recorded no timing, so the early stop was only
visible from the mtime on `solution.py`.

What it shows: one pass of about seven minutes, with no iteration, already
reached 0.8621 on gold, above its own train score. That is the floor the
iterating runs are measured against.

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

## Run 2 — 2026-09-16 — Opus 5 — **completed**

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

## Run 3 — 2026-09-16 — Fable 5.1 — **interrupted, host slept**

| | |
|---|---|
| workspace | `260917-fable51` |
| solution | `f9509aac13c77b27a120d74ab32c09366acd2b6e741aa828dbd316366ad03653` |
| wall-clock span | 2928s |
| awake | 1022s |
| host suspended | 1906s |
| passes | 1 initial + 3 continuations |

**Interrupted: the Mac went to idle sleep** at 20:41:52 UTC, about fifteen
minutes in, during continuation pass 3 (`pmset -g log`: *Entering Sleep state
due to 'Idle Sleep'*). The container was frozen with it, but the loop's deadline
is read from the container's wall clock, which jumped forward on wake. The loop
concluded the budget was spent after roughly seventeen minutes of real work,
against thirty for Opus in run 2, so its numbers are not a like-for-like
comparison with the completed runs. Train confirms the agent's report: micro F1 **0.9585**, exact-span 0.9412,
macro 0.9342. Audit clean; notes `اذا`, `ال` are a spelling variant and the
article.

Checked retroactively, run 2 lost 27s of wall time to launch overhead, not
sleep, and stands.

Harness fixes: `run_iterating_agent.sh` holds `caffeinate -is` for the life of
the launch, and the launcher records `host_suspended_seconds` -- wall-clock span
minus monotonic time, which stops while macOS sleeps -- and warns against
grading a run where it exceeds a minute.

**Gold.** Read after the run, and recorded before run 4 was launched, so run 4
could not be judged against it.

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

## Run 4 — 2026-09-16 — Fable 5.1 — **completed**

| | |
|---|---|
| workspace | `260917-fable51-r2` |
| solution | `ca226574a4f6db232a6cba44ae21ed3f7035f1e7b1e4a5a58be7400933c212a9` |
| used | 1815s (92%), host suspended 1s, not interrupted |
| passes | 1 initial + 31 continuations |
| transcript | `260917-fable51-r2.owner.20260916-212306.run.log` |

The rerun of run 3 with the full budget. Run 3's interrupted solution scored
higher on gold, which is the most informative comparison in this log.

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

## Summary across runs

| run | model | status | passes | train | gold | gap |
|---|---|---|---:|---:|---:|---:|
| 1 | Opus 5 | completed, single pass | 0 | 0.7756 | 0.8621 | +0.087 |
| 2 | Opus 5 | completed | 23 | 0.9463 | 0.9157 | −0.031 |
| 3 | Fable 5.1 | interrupted, ~17 min | 3 | 0.9585 | 0.9448 | −0.014 |
| 4 | Fable 5.1 | completed | 31 | 0.9948 | 0.9051 | −0.090 |

What the four together show:

- **Iteration helped Opus and hurt Fable.** Opus rose from one pass (0.8621)
  to twenty-three (0.9157). Fable fell from three passes (0.9448) to thirty-one
  (0.9051) as train approached 1.0. That fits gains early and fitting late, but
  four runs over two models cannot establish the curve.
- **The gap tracks how hard train was pushed.** −0.014 at three passes, −0.031 at
  twenty-three, −0.090 once train reached 0.9948.
- **The completed Opus and Fable runs are within what 179 gold events can
  separate.** The finding is about the loop, not a ranking of models: its
  keep-if-train-improves rule rewards fitting once train stops being informative.

---

## Where the solutions fail on gold

General patterns only. Failure rows count a wrong-label match
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
3. **An extra word: insertion, or part of a substitution.** There is no
   separate label for this. When a reciter says two words where the reference
   has one, gold sometimes records a single `substitution_mistake` whose
   locations cover both spoken words — ten such multi-location substitutions
   exist across the corpus — and solutions call the extra word an
   `insertion_mistake` instead.
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
- **A plateau stopping rule is enforced**, as in Study 1, but at 10 rather than
  15. `score.py` appends every scoring to `.scores.jsonl`, and the loop counts
  distinct solution versions scored since the last new best — from the history,
  not from the agent's account. Re-scoring an unchanged file is not an
  experiment; reverting to an older one is.

  Study 1's 15 was set where an experiment took under a second and runs made
  hundreds. Here a thirty-minute run makes 47 to 72, and a pass can hold several
  — Fable tested whole grids of settings in one. Replayed against the
  transcripts:

  | threshold | run 2 stops at | run 4 stops at | kept changes cut off |
  |---:|---|---|---|
  | 5 | pass 17 of 23 | pass 5 of 31 | run 4: several |
  | 8 | pass 20 of 23 | pass 8 of 31 | run 4: two, at passes 9 and 12 |
  | **10** | pass 22 of 23 | pass 22 of 31 | none |
  | 15 | never | pass 27 of 31 | none |

  10 is the lowest of these that cuts only passes in which nothing was kept, in
  both runs. It saves time; it does not change a final solution, because
  non-improving changes are reverted anyway. A lower value would stop an agent
  before changes whose value on gold is unknown, since intermediate solutions
  were not saved.

- **The continuation prompt no longer demands keep-only-if-improved and forbids
  stopping.** It reports the plateau count, restates the unseen evaluation, asks
  for a change expected to hold there, and allows the agent to stop when it has
  none.

What these do not do: a plateau rule stops a run that has stopped improving,
and most of run 4's fitted changes were made while train was still improving.
The framing and the prompt address that, but depend on the agent heeding them.

### Proposed: a development split

The annotations for all 100 train recordings exist. The proposal is to show the
agent 80 of them and keep 20 back — not unannotated, just not in the workspace.
The harness scores every candidate change on those 20 as well as on the 80, and
a change is kept only if it does not make the hidden 20 worse. A rule fitted to
one visible recording then has to survive recordings the agent has not read.
Gold stays untouched until the solution is frozen; the 20 are part of train.

Proposed hidden 20, stratified so each label keeps about a fifth of its events
out of view: train-002, train-003, train-008, train-009, train-010, train-011, train-012, train-013, train-016, train-017, train-020, train-023, train-027, train-046, train-052, train-063, train-071, train-085, train-089, train-103.

| label | train | hidden | visible |
|---|---:|---:|---:|
| substitution_mistake | 106 | 21 | 85 |
| spelling_benign | 55 | 11 | 44 |
| omission_mistake | 47 | 9 | 38 |
| repetition_benign | 29 | 6 | 23 |
| isti3adha_benign | 17 | 3 | 14 |
| basmala_benign | 13 | 3 | 10 |
| substitution_corrected | 8 | 2 | 6 |
| omission_corrected | 7 | 1 | 6 |
| insertion_mistake | 6 | 1 | 5 |
| letters_benign | 2 | 0 | 2 |
| **total** | **290** | **57** | **233** |

`letters_benign` stays entirely visible: with two examples, hiding one would
halve what the agent can learn from and measure nothing. The three rarest
remaining labels keep one or two hidden events each, which can catch a rule that
breaks them but cannot estimate them. Not adopted yet.
