# Current study state — 2026-09-15

Use this page for current progress. Historical snapshots and published pilot numbers describe their own frozen data/format, not the expanding working corpus.

| Artifact | Current state |
|---|---|
| Frozen evaluation | gold100: 100 cases, 348 units, 162 events; original single-span contract |
| Frozen development release | 127 answer-free cases, 888 units; reviewer sample 23 cases / 381 units |
| Working annotation corpus | **193 cases, 1,027 units, 457 events** — 96 `r*` and 97 `train-*` |
| Working source-review statuses | 146 reviewed, one partially reviewed, 41 draft, five approved; these are provenance, not blanket approval of every revised event |
| Granular representation | Recording-level events with multiple locations; every recording and unit has a summary |
| Repetition convention | All matching occurrences linked; 43 events / 89 locations |
| Hamza adjudication | All 15 presented events in 13 existing cases approved: seven benign spelling and eight substitution events |
| Remaining interpretation questions | Ten existing cases; the five additions are approved |
| Corpus target | 200 cases; **seven more suitable autodetect recordings needed** |

## New inventory and six-case extension

Read-only production check: 330 bot/autodetect recordings with 305 stored transcripts, and 25,776 single-ayah app recordings with 25,599 transcripts. Against the September 8 inventory, there are nine additional bot IDs and 357 newer single-ayah rows; all additions have stored transcripts.

The owner selected **autodetect only** for this corpus. Single-ayah app transcripts have a different vocalization/transcription convention and are not pooled with them. Six useful autodetect cases were added as drafts, one exact stored transcript per recording. One of them, a full-length 2:219 that shared 81% of its tokens with another in the same batch, was dropped on review; it was also the one vocalized transcript in the batch, so the corpus no longer contains a harakat-bearing autodetect transcript. The five kept were renumbered into the train series as train-128..132 and approved. Three other new bot candidates were left outside this batch because they repeat already-covered text/cases. The target is not filled by adding redundant cases or mixing recording families.

Original objects for the selected recordings were downloaded and their SHA-256 hashes agree with the database. Storage metadata was checked against the existing corpus; no identical-byte audio group was found. This does not prove that differently encoded/clipped recordings are independent takes. Recorded `duration_sec` was not treated as measured audio length; durations come from the audio probe.

The temporary six single-ayah candidates were removed from active files, manifest and review bundle after the owner's clarification. Their read-only export remains private archival material.

## Current rubric

- Granular events remain consistent across parallel-passage replacements. More natural episode interpretations may be notes, without changing grouping.
- Opening fragments are insertions unless repeated matching context or another independent anchor establishes two attempts at one reference target. A recognizable donor phrase alone is insufficient.
- Plain alif in place of written hamza is `spelling_benign`. Contextual medial/final seat variants can be benign; explicit initial أ versus إ remains distinct. An individually accepted madda spelling does not establish a global madda equivalence.
- Reference display preserves hamza using vocalized `titles.ar` from the same application source. Legacy clean-reference text and original word coordinates remain traceable.

See [the representation](annotation-review/README.md) and [hamza policy](annotation-review/HAMZA-POLICY.md).

## What has run, and what has not

The Track 1 paper already reports **eight informal 20-minute pilot runs**, seven with no invalid predictions and one with invalid events. Its six-run aggregate analysis intentionally excludes the later Fable run and the failing run. These are single runs, not a preregistered repeated comparison. Seven did not use the training pool; Fable applied its finished detector to it as a check. A mandatory annotate-first experiment has not been demonstrated.

Those results use frozen evaluator v2.1 and the original 162 events. They have not been recomputed on the granular working corpus. The existing evaluator cannot score multiple locations or cross-chunk events under the new contract.

## Completed / next

- [x] Audit selection, preserve original transcripts, and keep one representative per identical-audio group.
- [x] Prepare granular events, summaries, approval provenance and an offline reviewer.
- [x] Apply owner-approved hamza decisions and retain faithful reference evidence.
- [x] Check live production inventory read-only; add six verified autodetect drafts.
- [ ] Review the six additions and resolve the ten earlier interpretation questions.
- [ ] Collect/select six more suitable autodetect recordings to reach 200.
- [ ] Obtain owner review of all remaining draft annotations and revised representations.
- [ ] Implement/test a multi-location evaluator, including event matching across chunks and empty omission anchors.
- [ ] Refresh constructed teaching examples and comprehension checks for the current rubric, without using private examples.
- [ ] Freeze a new corpus version, reference contract and grouped train/test allocation before new experiments.
- [ ] Rerun baselines/agents on that version; retain old tables as historical results.
- [ ] Check the intended Track 1 submission version/page budget: the current PDF has eight pages, as it already did before this audit.
- [ ] Confirm actual submission/acceptance status and any remaining review-sample/attribution obligations with the authors. The repository alone does not establish submission.

Answers, source identities, audio and review bundles remain private. The full authoring repository is not an agent workspace. Updating documentation does not alter the frozen release, published pilot results or anonymous submission copy.
