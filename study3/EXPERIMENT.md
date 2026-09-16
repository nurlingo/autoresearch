# Agent development on train, final validation on gold

## Current plan — 2026-09-16

**100 annotated train recordings and 100 annotated gold recordings are approved and frozen** as `granular-100x100-v1.0` (1,038 units; 469 events). Development uses train only; final validation uses hidden gold. No measured experiment has been run on this edition. [CURRENT-STATE.md](CURRENT-STATE.md) records verified counts and readiness gaps.

The comparison is between agents under the same rubric, inputs, tools and budget. Annotation is an available development strategy: an agent may annotate, train a model, write rules or combine them. Preserve annotations it creates, but do not silently make annotate-first a requirement. If annotation delivery becomes mandatory, fix that requirement uniformly before comparing runs.

## Who sees what

| Role | Inputs and access | Feedback |
|---|---|---|
| Owner preparing the dataset | Both annotated splits, provenance and review notes | Human review and data checks |
| Development agent | Answer-free train units, faithful Quran reference, rubric, constructed examples and permitted tools | Train-only aggregate/per-label metrics if the isolated feedback service is enabled |
| Frozen inference process | Input-only gold units and frozen solution artifacts | Produces predictions; no answers or development-agent return channel |
| Trusted final evaluator | Gold annotations and saved predictions | Final aggregate scores after development ends |

Under the current run design, human train annotations are grader targets, not files given to the agent. Train feedback is supervised development even when only aggregates are returned; disclose it in the experiment description. Revealing train labels directly would be a different condition to choose in advance. Gold inputs, selection membership, answers, review histories and scores remain unavailable during development.

Prepared inputs use the current hamza-preserving reference and human-reviewed ayah assignments. Ayah detection and splitting are outside the score. The current adapter invokes `detect_events` once per unit; the fuller recording-level annotation format and this restricted inference interface must not be conflated.

## Data separation

Retain one useful transcript per distinct recording/audio take, preserving source provenance privately. Different recordings of a common clean ayah are eligible. Exclude exact copies of event-bearing ayah cases across train/gold; generic opening formulas and shared Quran references are allowed. The current audit found no repeated recording IDs and no shared event-bearing ayah transcripts. Shared clean text, speaker dependence and prior public source exposure limit generalization claims.

Do not move a case used for development into gold and describe it as unseen. Any subsequent split or rubric change requires a new version and fresh hashes. Old `release/` files and gold100 are frozen historical artifacts, not the new split.

Single-ayah app recordings remain outside this collection at the owner's direction. The target is 200 useful autodetect cases, not 200 rows filled by repeated transcripts or a different transcription convention.

## Development and final selection

1. Freeze train/gold membership, normalization, reference, event schema and evaluator. Use the repaired v2.3 [evaluator](EVALUATOR.md); its single-location-per-event adapter remains explicit. Full occurrence reconstruction is a separate task change.
2. Inspect the current adapted teaching examples and verify comprehension on constructed practice data outside gold.
3. Record model/runtime versions, prompts, dependencies, tools, time/token/cost budget, feedback allowance, repetitions and final-solution selection rule.
4. Run development in an allowlisted environment. If iterative scoring is provided, use only train labels in a separate trusted service. A directory boundary, prompt restriction or isolated HOME does not protect private files.
5. Save all run logs, code, configuration, learned artifacts and any generated annotations. Choose and hash the final solution using train evidence only.
6. End development. Execute the frozen method in isolation on input-only gold and score its saved predictions privately. No edits or model selection based on gold results.
7. Report the outcome of every predeclared run, including failures. Document technical reruns and repeated-run variation.

The [runbook](agent-run/RUNBOOK.md) prepares train-only inputs, including a self-contained guide and constructed examples. Submitted code now runs in a restricted input-only Docker container; trusted scoring happens afterward. A separate train-only feedback service and development-container launcher keep private annotations outside the agent runtime. Development networking permits model API access; inference networking is disabled.

## What we measure

Primary: **label-aware micro F1** on final gold predictions. An event needs the correct label and acceptable transcript/reference spans. Report per-label support and F1, macro F1, localization F1, invalid outputs and mistake review costs at 1:1 and 2:1. Exact-span label-aware F1 is repaired in v2.3. All ten labels occur in both working splits, but some have only one or two examples.

The current v2.3 adapter accepts one hypothesis location per event, even when the human annotation links several attempts. It does not independently measure complete multi-location annotation recovery. Settle that scope before comparing agents or describing annotation fidelity in the paper.

Human annotations now exist for train too. After freezing a run, its saved machine annotations can be compared directly with reviewed train annotations under a compatible representation. If the agent received train score feedback, this is in-sample agreement, not an independent generalization result. A good algorithm score does not establish that its intermediate annotations were correct or used. Preserve machine-generated provenance and review before reuse.

## Relationship to the papers

The proposed competition judges entrants' final solutions; it need not require autoresearch, an annotation phase or organizer-scored iterations. Our agent experiment may provide train-only feedback as a declared experimental condition. Those are different roles, even if they share a dataset and rubric.

Eight informal pilot runs are already reported in the Track 1 paper under evaluator v2.1 and the older 162-event gold set. They are not evidence from this 100/100 split, and a repeated comparison on the new freeze is not complete. Keep old results tied to their versions. Paper changes remain for discussion; see [the audit/discussion note](../docs/STUDY3-PAPER-DISCUSSION.md).

The historical 221-to-127 training selection audit remains in [TRAIN-ANNOTATION.md](TRAIN-ANNOTATION.md); the historical release and review sample are separate archived artifacts (the old `release/` directory is not present in this checkout). They do not define the next run's membership or count.
