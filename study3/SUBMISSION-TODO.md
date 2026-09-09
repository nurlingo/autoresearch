# MusIML submission checklist — 2026-09-09

[Official call](https://www.musiml.org/events/2026-NeurIPS/index.html): final deadline
September 10, 2026. Track 3 asks for a competition **proposal** in at most two pages,
with a ready-to-use dataset, a 10% review sample, defined metrics and evaluated
baselines. Selection is on social impact, task design, dataset readiness, baseline
evaluation, feasibility, ethics and participation potential.

We are applying, not running a competition. The call requires no dates, organizers,
sandbox or participant support, so those belong to acceptance, not submission, and
are listed separately below. Unchecked items are not claimed as accomplished.

**Everything the call requires is done.** Dataset, sample, metrics and baselines are
frozen and validated; the paper is two pages.

## Paper 1 — final-solution event annotation competition (Track 3)

- [x] Freeze gold100 privately: 100 approved cases, 348 units, 162 events.
- [x] Transcribe the missing new audio locally; retain original database/export.
- [x] Return former reserves' answer-free inputs to the candidate pool; preserve private answers.
- [x] Screen full recordings and event-bearing ayah chunks; allow shared clean ayahs and different error variants.
- [x] Remove redundant training cases and quarantine unresolved/out-of-scope inputs.
- [x] Freeze train v1.0: 127 cases, 888 units, including 44 new recordings.
- [x] Preserve original source tokens and canonical Quran reference text.
- [x] Prepare actual train-only review sample: 23 cases, 381 units (v1.1).
- [x] Implement/test evaluator v2.1 and evaluate empty, diff and production-component baselines.
- [x] Rewrite the two-page proposal around annotation outputs and final-only scoring.
- [x] Document method freedom: no required agents, iteration scoring or annotation phase.
- [x] Document public-input exposure and assistant-reviewed new splits.
- [x] Prepare 20 constructed teaching cases with references and word spans for owner approval.
- [x] Owner approved all twenty teaching cases. t11 was rebuilt as a restatement after
      review found it indistinguishable from the t08 insertion; a duplicate of t01's
      normalization rule was dropped and the set renumbered t01-t20; t20 adds the
      omission-plus-substitution combination that no case previously carried.
- [ ] Freeze executable comparison normalization and contextual spelling boundaries.
- [x] Freeze MIN_SPAN=0.50 and anchor slack=1; report the secondary cost at both 1:1
      and 2:1 instead of freezing one rate. Sweeps showed MIN_SPAN moves baseline micro
      F1 about four points across its whole range and anchor slack moves it none, so both
      are chosen to be explainable rather than tuned.
- [ ] Confirm that a train-only, unlabelled 10% sample meets the workshop review
      requirement. Sample frozen as v1.1 (23 recordings, 381 units), discloses zero
      previously-unpublished recordings; interpretation still needs organizer
      confirmation, not the disclosure question.
- [x] License the release CC BY 4.0 with a no-re-identification condition; the privacy
      policy already permits publishing anonymised data as an open dataset.
- [x] Name the source of the Quran reference text. It is Tanzil `simple-clean`,
      reached via the application's quran.com/QUL-assembled `quran.json`; our copy
      is a normalized derivative (basmala prefix removed, hamza and alif maqsura
      folded), so it is not verbatim Tanzil text. See [README.md](README.md).
- [ ] Before redistributing: add Tanzil attribution plus the tanzil.net link and
      copyright notice to the release, and stop describing the reference as
      "verbatim" canonical text.
- [x] Provide anonymous reviewer access/upload. The training release, 10% review
      sample (v1.1, 0 previously-unpublished recordings), reference, evaluator v2.1
      and one runnable baseline are published anonymously at
      https://anonymous.4open.science/r/quran-recitation-event-review-5C71/ and linked
      from the proposal. The GitHub branch itself still identifies authors and is not
      linked from either paper.
- [ ] Final cross-paper overlap/anonymity review and submission by the authors.

Do not publish or mount the selected gold test bundle, labels, private maps or
annotation-session memory in development environments. Shared clean units are permitted
by the documented partition policy. New annotations are hidden; old source inputs were
already public. No claim of an unseen-input test. Prepared training is versioned;
future repairs require a new version and fresh hashes, not silent file changes.

## Only if the proposal is accepted

The call asks for none of these; they are what running the competition would need.

- [ ] Finalize inference resource limits, external-data/API rules, tie handling and
      submission instructions.
- [ ] Build and test the isolated final-execution service; the evaluator is not a sandbox.
- [ ] Set competition dates, accountable organizers and participant support.
- [ ] Destroy the surrogate-id map at public release (see below) and record that it was done.

## Paper 2 — dataset/evaluator and comparison between agents (Track 1)

- [x] Complete the annotation, rubric, evaluator audit and baseline analysis.
- [x] Specify an agent-comparison experiment using the same train/gold split and total budget.
- [x] Treat annotation as an available strategy; save produced annotations for inspection/reuse.
- [x] State that final algorithm scores do not independently validate training annotations.
- [ ] Choose agents/models/versions, budget, tools, seeds/repeated runs and common instructions.
- [ ] Decide uniformly whether annotation delivery is optional or required for every compared agent.
- [ ] Approve common teaching examples and freeze all evaluation choices before runs.
- [ ] Prepare isolated agent workspaces without gold or answer-bearing repository/history access.
- [ ] Run agents; preserve code, costs, logs and any generated annotations and revisions.
- [ ] Freeze each final method and score it privately; no gold-driven edits/retries.
- [ ] Report agent comparison, uncertainty and observed annotation strategies; update paper tables.
- [ ] Review any machine annotations proposed for reuse; label their provenance accurately.
- [ ] Recompile, review and submit. No new agent results are claimed before runs occur.

A full human-labelled training set is not required. If later measuring annotation
accuracy directly, review a separate audit subset; a human-supervised baseline is
an optional additional experiment.
