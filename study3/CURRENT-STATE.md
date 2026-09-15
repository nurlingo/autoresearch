# Current study state — 2026-09-15

Use this page for current progress. Historical snapshots and published pilot numbers describe their own frozen data/format, not the expanding working corpus.

| Artifact | Current state |
|---|---|
| Frozen evaluation | gold100: 100 cases, 348 units, 162 events; original single-span contract |
| Frozen development release | 127 answer-free cases, 888 units; reviewer sample 23 cases / 381 units |
| Working annotation corpus | **196 cases, 1,031 units, 465 events** — 96 `r*` (170 events) and **100** `train-*` (295 events) |
| Working source-review statuses | All 193 cases and 454 events owner-approved, 2026-09-15, after a manual pass over every case |
| Granular representation | Recording-level events with multiple locations; every recording and unit has a summary |
| Repetition convention | All matching occurrences linked; 43 events / 89 locations |
| Hamza adjudication | All 15 presented events in 13 existing cases approved: seven benign spelling and eight substitution events. Three further word-boundary spelling events were withdrawn — see below |
| Remaining interpretation questions | One, on train-135: whether a false start drawn from a neighbouring ayah is an insertion or a corrected omission |
| Corpus target | 100 train + 100 gold. Train is complete; **four more gold recordings needed**, selected by missing label |

## New inventory and six-case extension

Read-only production check: 330 bot/autodetect recordings with 305 stored transcripts, and 25,776 single-ayah app recordings with 25,599 transcripts. Against the September 8 inventory, there are nine additional bot IDs and 357 newer single-ayah rows; all additions have stored transcripts.

The owner selected **autodetect only** for this corpus. Single-ayah app transcripts have a different vocalization/transcription convention and are not pooled with them. Six useful autodetect cases were added as drafts, one exact stored transcript per recording. One of them, a full-length 2:219 that shared 81% of its tokens with another in the same batch, was dropped on review; it was also the one vocalized transcript in the batch, so the corpus no longer contains a harakat-bearing autodetect transcript. The five kept were renumbered into the train series as train-128..132 and approved. Three other new bot candidates were left outside this batch because they repeat already-covered text/cases. The target is not filled by adding redundant cases or mixing recording families.

Original objects for the selected recordings were downloaded and their SHA-256 hashes agree with the database. Storage metadata was checked against the existing corpus; no identical-byte audio group was found. This does not prove that differently encoded/clipped recordings are independent takes. Recorded `duration_sec` was not treated as measured audio length; durations come from the audio probe.

The temporary six single-ayah candidates were removed from active files, manifest and review bundle after the owner's clarification. Their read-only export remains private archival material.

## Reference contract

The reference keeps its hamza, and one definition now holds everywhere:
`titles.ar` with vowel marks, tatweel and waqf signs removed, and nothing else.
That text is the corpus `reference_text` (973 ayah units),
`study3/quran-reference.json` built from `content/quran.json` (6,231 ayahs), and
the application's own `titles.clean` (6,362 ayahs) — which no longer folds
hamza, because every consumer of it already folds hamza itself. The earlier
folded form is retained per unit as `reference_folded_text` so the legacy
coordinates stay traceable; both tokenize identically, so no span moved.

Folding أ إ آ to bare ا is what hid eight real substitutions from the audit and
what makes 54% of a transcript's apparent differences turn out to be nothing at
all. An agent scored against the folded text cannot tell a missing hamza mark
from a different word, so it is no longer scored against it.

`titles.clean` in the application's `quran.json` has been rebuilt so that it is
exactly `titles.ar` with vowel marks, tatweel and waqf signs removed and أ إ آ ٱ
folded to ا. It previously disagreed with `titles.ar` in 94 ayahs: six tokenized
differently, and 78 ayah-segment entries had never had their hamza folded at all,
so the field meant two different things depending on the entry. It now agrees
with `content/quran.json` on all 6,231 shared ayahs and drifts from its own
`titles.ar` nowhere.

The tokenization disagreement had reached this corpus in one place,
of which one reaches this corpus: an ayah where the mushaf writes بعد ما as two
words and `clean` had joined it. Three `spelling_benign` events annotated reciters
saying the canonical two-word form against that joined reference. Since the
reference was the artifact and the reciters were right, those three events were
withdrawn rather than kept. The other
word-boundary decisions in the hamza adjudication are unaffected.

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
- [x] Review the additions and resolve the earlier interpretation questions.
- [x] Reach 100 train cases: train-133/134/135 added from production, drafts awaiting review.
- [ ] Collect four more gold recordings to reach 100.
      Choose for the labels the corpus lacks, not for volume: `omission_corrected`
      is absent from the holdout entirely and cannot be measured there,
      `letters_benign` is absent from train and cannot be learned from it, and
      `insertion_mistake` has two events in the holdout. The last batch of six
      added no benign events at all.
- [x] Obtain owner review of all annotations: 193 cases and 454 events approved 2026-09-15.
- [x] Implement/test a multi-location evaluator: `study3/eval21.py`, oracle 1.000 and empty 0.000 on both splits.
- [ ] Refresh constructed teaching examples and comprehension checks for the current rubric, without using private examples.
- [ ] Freeze a new corpus version, reference contract and grouped train/test allocation before new experiments.
- [ ] Rerun baselines/agents on that version; retain old tables as historical results.
- [ ] Check the intended Track 1 submission version/page budget: the current PDF has eight pages, as it already did before this audit.
- [ ] Confirm actual submission/acceptance status and any remaining review-sample/attribution obligations with the authors. The repository alone does not establish submission.

Answers, source identities, audio and review bundles remain private. The full authoring repository is not an agent workspace. Updating documentation does not alter the frozen release, published pilot results or anonymous submission copy.
