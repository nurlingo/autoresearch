# Study 3 preparation

This directory prepares the annotation-and-algorithm experiment described in
[METHODOLOGY-STUDY3.md](../METHODOLOGY-STUDY3.md). It is not a runnable evaluation
harness yet. The historical `stage2/` harness uses a different contract.

1. Review the [annotation guide](ANNOTATION-GUIDE.md) and
   [20 constructed Arabic teaching cases](calibration/teaching-draft.md).
2. Approve/revise the teaching answers, then assemble a separate practice batch
   without answers in its input file. Test comprehension and revise the guide
   before a measured run. Do not use gold cases for this exercise.
3. Freeze an executable input/output schema and evaluator: one-to-one event
   matching, label metrics, span metrics, omission anchors, both-attempt spans,
   and false flags on clean/benign material. Validate with synthetic oracle cases.
4. Prepare a separate unlabelled development pool; freeze model/tool budgets,
   comparison conditions, permitted feedback and final evaluation procedure.

The teaching cases are deliberately constructed transcript variants of the
public Quran reference, not recordings or evidence of naturally occurring
errors. All answers are drafts awaiting human review. Their reference ayah IDs
were checked outside the private evaluation set and its approved reserves.
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
