# Quran transcript checking — Task A v1.1 and legacy Task B pilot

**Documentation updated 2026-09-08.** The data files are unchanged. This
release accompanied the earlier MusIML Track 3 proposal. It is not the new
40-recording human-reviewed annotation set and does not implement taxonomy
v0.16. See [current methodology](../METHODOLOGY-STUDY3.md) and
[annotation findings](../docs/STUDY3-ANNOTATION.md).

## What is in the published files

| | Task A | Legacy Task B |
|---|---|---|
| Input | Full transcript | One assigned ayah chunk and reference |
| Output | Ayah ids and splits, or abstain | Events with separate type/verdict fields |
| Rows | 258 recordings: 151 train / 107 test | 1,268 chunks: 712 train / 556 test |
| Annotation | Reviewed assignments/splits: 1,267 chunks (711/556) | 99 machine-labeled chunks from 20 recordings; 1,169 unlabelled |
| Metric | Existing `research_score` | Historical `study3_score`; incompatible with the new rubric |
| Exposure | Already public | Already public, including machine-pilot answers |

Task A covers 254 Quranic recordings and four non-Quran negatives, 604 ayahs,
and 45 surahs. Task B's 99 labeled chunks contain 86 no-event chunks and 17
machine-labeled events (11 substitutions, three omissions, two truncations,
one full repeat), not new human-reviewed ground truth.

The legacy pipeline uses the same recording partition and surrogate row ids.
**Export discrepancy:** Task A row `train-008` has seven chunks, but the Task B
export has eight. This accounts for 1,268 versus 1,267. The public files are
preserved so existing checksums and historical results remain reproducible;
resolve the discrepancy in a separately versioned dataset before new scoring.
Do not claim a one-to-one split match until it has been reconciled.

## Files and historical contract

- `taskA/train.csv`, `taskA/test.csv`: surrogate id, transcript, assignment,
  confidence, serialized ayah split, and reference metadata.
- `taskA/quran_ref.json`: public Quran reference.
- `taskB/train.jsonl`, `taskB/test.jsonl`: old per-chunk events and label status.
- `sample/`: the historical 26-recording review sample; it is public.
- `SHA256SUMS`: checksums for data and documentation in this release directory.

Task A assignments can be individual ayahs, ranges, comma-separated lists,
or `non_quran`. Repeated ids may represent repeated ayahs. Task B events use
`type`, `verdict`, selected words, and spans under the **legacy** canonicalizer.
See [legacy schema](../stage2/SCHEMA.md) for exact details. An empty events list
alone does not establish human review: inspect `label_status`. All 99 labeled
pilot chunks currently have `label_status: machine`; null events are unlabelled.
The old uncertainty, final-ayah exemption, and repeat-absorption rules are
superseded for the new protocol but retained in historical data and code.

## New review and exposure

The separate current review has **40/100 unique recordings approved**, with
71 chunks and a new combined-label rubric. Its gold answers are not added to
this release. All 40 inputs already match published Task A transcripts, and
five overlap recordings carrying public legacy Task B labels. Keep new
adjudications and selection membership private, exclude public-release access
from experimental agents, and disclose this exposure. An unseen-input final
test requires a separately collected, previously unreleased corpus.

The new development agent will annotate an unlabelled pool and build an
algorithm. Final code is scored privately. No new metric is frozen and no
algorithm has been evaluated on the new gold set. Do not score the new format
with the legacy executable or treat legacy scores as new results.

## Provenance and reuse

The original release documents adult-user bot recordings, commercial ASR,
terms-of-service disclosure of review, text-only release with surrogate ids,
and a CC BY 4.0 license. These are the existing release's provenance statements,
not a new consent audit. Verify the permitted scope before new redistribution
or collection; scan free text independently of its expected Quran content.
No production user identifiers or new gold annotations are added here.

## Integrity

The existing data bytes are preserved. Documentation changes are reflected in
`SHA256SUMS`. Its full file hashes, rather than historical abbreviated hash
claims, are authoritative for this checkout. From this directory run:

```sh
shasum -a 256 -c SHA256SUMS
```
