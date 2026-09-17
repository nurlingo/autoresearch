# Current study state — 2026-09-16

The dataset is approved and frozen as **`granular-100x100-v1.0`**, with **100 train and 100 hidden test recordings**. All five gap-targeted additions were approved by the owner on September 16. No measured agent experiment has been launched on this edition.

## Verified frozen corpus

| Split | Recordings | Units | Events | Approval |
|---|---:|---:|---:|---|
| Train | 100 | 697 | 290 | All approved |
| Test | 100 | 341 | 179 | All approved |
| Combined | 200 | 1,038 | 469 | All approved |

There are 984 ayah chunks and 54 opening-formula units. All recordings have natural-language summaries and no open review questions. Both splits contain all ten labels.

| Sparse label | Train events | Test events |
|---|---:|---:|
| `omission_corrected` | 7 | 2 |
| `letters_benign` | 2 | 4 |
| `insertion_mistake` | 6 | 3 |
| `substitution_corrected` | 8 | 5 |
| `spelling_benign` | 55 | 11 |

These additions improve coverage, but rare-label estimates remain based on small counts. The unsupported repaired-insertion case and withdrawn candidate remain outside this edition; unused earlier proposals remain historical alternatives.

## Authoritative files and split audit

The private `train_review/granular-corpus/` directory contains current `recordings.jsonl`, `split-train.jsonl`, `split-test.jsonl`, `corpus.json`, `current-cases/`, and `index.html`. The versioned snapshot is `frozen/granular-100x100-v1.0/`, including the data, reference, rubric, teaching examples, evaluator/runtime source and SHA-256 manifest. Use its split files for measured runs. The freeze is private and must never be mounted into the agent workspace.

All 200 recording IDs are unique. Split rows reproduce the combined corpus exactly. There are 52 distinct exact `(ayah_id, transcript)` pairs shared between splits, all clean on both sides, and three permitted generic opening-formula strings. No event-bearing ayah transcript is shared. New source IDs/audio hashes and downloaded originals were checked against the prior active inventory. This does not establish speaker independence or detect all differently encoded copies of an audio take.

The earlier 195-case version is preserved in `archive/20260916-before-100x100-freeze/`. Other old aggregate exports/backups and `cases/` are historical source evidence; current individual exports are in `current-cases/`. Do not use old builders or proposal files to overwrite the approved annotations. The dated [database inventory](RECORDING-INVENTORY.md) records selection provenance without publishing source identities.

## Reference and annotation contract

Use `study3/quran-reference.json`: **6,236 entries**, preserving hamza, madda and alif maqsura. The builder derives text from the application's `titles.ar` by removing vowel marks, tatweel and waqf signs. Every current ayah unit's `reference_text` matches the checked-in reference. The old folded reference in `release/` and earlier inventory snapshots is for historical experiments only.

Current transcripts are devowelled; source provenance is retained privately. A change to normalization or tokenization needs a versioned rebuild and span validation. Do not silently normalize the arrays passed to a solution and then index those modified arrays.

The [guide](ANNOTATION-GUIDE.md), [event representation](annotation-review/README.md) and [hamza policy](annotation-review/HAMZA-POLICY.md) document the current rules: granular attempts and repeated context; every repetition occurrence linked; contextual spelling; initial أ/إ distinguished; missing hamza notation on plain alif benign. Redundant spelling events caused by the old reference joining canonical words were withdrawn.

Single-ayah app recordings remain excluded at the owner's request because their transcription convention differs. Continue with suitable autodetect recordings and one useful transcript per distinct recording/audio take. The September 15 production inventory is a dated snapshot, not a live count.

## Next autoresearch run

The agent receives train inputs, the faithful Quran reference, the rubric and the current adaptation of constructed teaching examples. It may create annotations and develop an algorithm. Preserve any generated annotations for analysis; a strong algorithm score does not certify those annotations individually.

Development feedback, if provided, uses **train annotations only**. Test inputs, answers, case membership, review notes and scores remain outside the development environment. Freeze code and configuration before the owner runs final test inference and scoring; no test-driven revision or selection. For a comparison, fix models, budgets, repeats and selection rules first.

See [EXPERIMENT.md](EXPERIMENT.md) and the corrected [runbook](agent-run/RUNBOOK.md). Input stripping and a separate HOME are not runtime isolation. The grader now executes submitted code in an input-only Docker container and scores returned predictions in a trusted owner process. A separate train feedback service has no test access. The development container mounts only prepared train material and receives only explicitly selected model-API credentials. Its networking permits API calls and is not an internet-retrieval filter.

## Evaluator readiness

`eval21.py` is evaluator **v2.3**, despite its filename. Primary: label-aware micro F1 at MIN_SPAN 0.50 on both transcript/reference spans, with empty-anchor slack 1. Exact F1 now requires matching labels too. Invalid span types, lengths, bounds and event shapes are rejected; reference matching checks ayah identity. Oracle/empty checks pass on both splits and adversarial synthetic tests cover the fixes.

The per-unit adapter still credits one eligible occurrence of a multi-location event. Other-ayah anchors cannot be scored as though their reference belonged to the current unit; the restored occurrence can be used instead. This preserves the existing prediction interface, not a claim to grade reconstruction of every linked attempt. A recording-level prediction task would be a separate contract change.

Docker tests verify private-file/environment isolation, no inference network or Docker socket, output handling and timeouts. A real 98-case preflight round trip through the train-only feedback service passed before finalization. The final 100/100 dataset passes measured preparation, span/reference validation and oracle/empty scoring checks; preparation alone does not launch an experiment. Preparation refuses a measured run unless both splits have 100 approved cases; `--preflight` exists for setup tests only. A Claude Code 2.1.267 image, matching the locally installed CLI version, was built; no model call or agent research run was launched.

## Historical results and paper discussion

The frozen experiment used gold100 (100 cases, 348 units, 162 events), train release v1.0 (127 cases, 888 units), and evaluator v2.1 (`eval19.py`). These are separate artifacts, not the current 100/100 freeze. Eight informal pilots appear in the Track 1 paper; they are not results on the current corpus. The six-run aggregate excludes a later run and a failing run.

The papers and frozen releases are unchanged in this audit. Proposed changes are listed in [the discussion note](../docs/STUDY3-PAPER-DISCUSSION.md). Submission/acceptance cannot be established from this repository alone.

## Before the measured run

- [x] Record owner approval of both existing drafts, completing review of all 195 active cases.
- [x] Owner approved all five gap-targeted additions; merge two train and three test cases.
- [x] Freeze the approved 100/100 allocation and source provenance; measured preparation verifies counts, recording IDs, event-bearing overlaps and reference consistency.
- [x] Rebuild the current viewer; archive stale exports/backups without discarding review history.
- [x] Fix evaluator issues, preserve the adapter scope and add synthetic regressions.
- [x] Implement isolated inference, train-only feedback, a restricted development-container launcher and frozen-solution hashing; test without model calls.
- [x] Adapt twenty constructed teaching examples to the current reference/grouping; validate spans and oracle scores. Original approvals apply to the historical examples; the current adaptation is explicitly assistant-validated.
- [ ] Inspect the refreshed teaching examples and check comprehension outside the test split before the measured comparison.
- [ ] Set exact model/API configuration, time/token/cost budget, repeats, feedback limit and selection rule; record image IDs and commands.
- [ ] Run train development, freeze each selected solution, then perform final private test validation without test-driven revisions.
- [ ] Discuss paper revisions using new results; preserve historical tables with their original versions.

Answers, source identities, audio and review bundles remain private. This page contains aggregate status only. No measured agent experiment has been launched on this edition.
