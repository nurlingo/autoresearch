# Study 3 preparation

This directory prepares the annotation-and-algorithm experiment described in
[METHODOLOGY-STUDY3.md](../METHODOLOGY-STUDY3.md). It includes the executable v2.1 evaluator and baseline adapters; the isolated
agent experiment is not yet packaged. The historical `stage2/` harness uses a different contract.

1. Review the [annotation guide](ANNOTATION-GUIDE.md) and
   [20 constructed Arabic teaching cases](calibration/teaching-draft.md).
2. Approve/revise the teaching answers, then assemble a separate practice batch
   without answers in its input file. Test comprehension and revise the guide
   before a measured run. Do not use gold cases for this exercise.
3. Review [EVALUATOR.md](EVALUATOR.md) and [BASELINES-v19.md](BASELINES-v19.md).
   Version 2.1 validates labels/spans and reports tolerant plus exact-span F1.
   Freeze matching tolerances, budgets and feedback before the agent run.
4. Prepare a separate unlabelled development pool; freeze model/tool budgets,
   comparison conditions, permitted feedback and final evaluation procedure.

The teaching cases are deliberately constructed transcript variants of the
public Quran reference, not recordings or evidence of naturally occurring
errors. All answers are drafts awaiting human review. Their reference ayah IDs
were checked outside the private evaluation set and the three then-reserved cases.
Exact normalized chunk comparisons are recorded privately; further phrase-overlap
review remains pending. Common Quran words and generic opening formulas are
not exclusive dataset material.

The agent must save its development annotations, annotation revisions, algorithm,
and run log. Final private gold scoring evaluates the resulting algorithm;
self-annotation accuracy and its causal benefit need separate evidence.

The entire authoring repository is not an agent bundle. Build a fresh allowlist
containing approved instructions/examples, Quran references, the separate
unlabelled development inputs and necessary tools. Exclude gold inputs and
answers, source exports, review history, attribution manifests and gold feedback.

See the [recording inventory](RECORDING-INVENTORY.md) for the read-only production
check: 63 additional bot submissions, with 62 stored transcripts and preliminary
duplicate screening. Private production exports are not included here.

[EXPERIMENT.md](EXPERIMENT.md) explains the agent comparison and gold isolation.
The [training release](release/README.md) contains 127 recording cases / 888 input
units; its train-only review sample contains 23 cases / 394 units. Shared clean
ayahs and different error variants are allowed; complete gold copies and copies of
event-bearing gold chunks are excluded. The [submission checklist](SUBMISSION-TODO.md)
tracks remaining approvals and execution work. [Teaching examples](calibration/teaching-review.html)
are constructed drafts awaiting owner approval.
