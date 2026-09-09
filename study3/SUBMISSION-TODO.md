# MusIML submission checklist — 2026-09-09

[Official call](https://www.musiml.org/events/2026-NeurIPS/index.html): final deadline
September 10, 2026. Track 3: at most two pages, ready-to-use data, 10% review sample,
metrics and evaluated baselines. This list distinguishes preparation from approvals
and completed experiments; unchecked items are not claimed as accomplished.

## Paper 1 — final-solution event annotation competition (Track 3)

- [x] Freeze gold100 privately: 100 approved cases, 348 units, 162 events.
- [x] Transcribe the missing new audio locally; retain original database/export.
- [x] Return former reserves' answer-free inputs to the candidate pool; preserve private answers.
- [x] Screen full recordings and event-bearing ayah chunks; allow shared clean ayahs and different error variants.
- [x] Remove redundant training cases and quarantine unresolved/out-of-scope inputs.
- [x] Freeze train v1.0: 127 cases, 888 units, including 44 new recordings.
- [x] Preserve original source tokens and canonical Quran reference text.
- [x] Prepare actual train-only review sample: 23 cases, 394 units.
- [x] Implement/test evaluator v2.1 and evaluate empty, diff and production-component baselines.
- [x] Rewrite the two-page proposal around annotation outputs and final-only scoring.
- [x] Document method freedom: no required agents, iteration scoring or annotation phase.
- [x] Document public-input exposure and assistant-reviewed new splits.
- [x] Prepare 20 constructed teaching cases with references and word spans for owner approval.
- [ ] Owner approves teaching cases, especially contextual spelling example t16; resolve any changes.
- [ ] Freeze executable comparison normalization and contextual spelling boundaries.
- [ ] Approve/freeze MIN_SPAN=0.30, anchor slack=1 and secondary 2:1 cost (current defaults).
- [ ] Confirm that a train-only, unlabelled 10% sample meets the workshop review requirement.
- [ ] Confirm redistribution/license scope for newly collected text and complete release metadata.
- [ ] Finalize inference resource limits, external-data/API rules, tie handling and submission instructions.
- [ ] Build/test the isolated final-execution service; current evaluator is not a sandbox.
- [ ] Set competition dates, accountable organizers and participant support arrangements.
- [ ] Provide anonymous reviewer access/upload; GitHub branch itself identifies authors.
- [ ] Final cross-paper overlap/anonymity review and submission by the authors.

Do not publish or mount the selected gold test bundle, labels, private maps or
annotation-session memory in development environments. Shared clean units are permitted
by the documented partition policy. New annotations are hidden; old source inputs were
already public. No claim of an unseen-input test. Prepared training is versioned;
future repairs require a new version and fresh hashes, not silent file changes.

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
