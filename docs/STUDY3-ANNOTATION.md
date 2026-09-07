# Annotation findings and decisions — 2026-09-08

Current review: **40/100 unique recordings approved**, 71 ayah chunks.
Taxonomy **v0.16**, recording format **v0.6**. This is a methods/status report;
no Study 3 agent results are available. The remaining 60 recordings have not
been approved. This document deliberately contains no selected recording ids,
user ids, gold transcripts, gold spans, or private codebook examples.

## Approved labels and counts

| Label | Meaning | Approved count |
|---|---|---:|
| `clean` | Chunk with no event after agreed comparison normalization | 36 chunks |
| `substitution_mistake` | Unresolved word/phrase replacement, including an incorrect final restatement | 28 events |
| `omission_mistake` | Missing reference material, including partial first/final ayahs | 14 events |
| `insertion_mistake` | Extra words not explained by a repeat or recognizable restatement | 1 event |
| `repetition_benign` | Reference-matching phrase repeated; span includes original and repeat | 4 events |
| `substitution_corrected` | Wrong attempt followed by a matching repair; span both | 3 events |
| `omission_corrected` | Missing material restored on a restart; span both attempts | 1 event |
| `letters_benign` | Spoken letter names faithfully represent the reference letter sequence | 2 events |
| `spelling_benign` | Specifically accepted spelling difference remaining after normalization | 3 events |
| `isti3adha_benign` | Istiadhah outside the assigned ayah | 11 formulas |
| `basmala_benign` | Basmala outside the assigned ayah | 5 formulas |

There are 56 within-ayah events and 16 opening formulas. Counts use different
units as indicated and must not be summed as independent recordings. Multiple
events can occur in one chunk. Coverage selection is deliberate; these counts
do not estimate real-world error prevalence.

## What the review changed

- **Text is the evidence.** We compare the unchanged ASR transcript to the
  clean Quran reference. We do not infer audio content or excuse a textual
  mismatch because ASR may have caused it. The old `uncertain` event verdict
  is outside this rubric; unresolved annotation decisions stay unapproved.
- **One semantic label.** Use one word for the event and one for its verdict,
  separated by an underscore. `clean` is the sole no-event chunk marker.
  Approval metadata is separate. No parallel type/verdict fields.
- **Partial ayahs are omissions.** Missing initial, interior, and final
  reference material is localized explicitly. A final recording position
  does not grant a benign exemption. This does not establish intent to err.
- **Normalization and spelling events differ.** Agreed hamza/diacritic and
  representation normalization receives no event. A residual spelling form
  that needs contextual acceptance receives `spelling_benign`. Wasl is a
  rationale in the note, not the label name. Approved contexts also include
  a standard-spelling/Quranic-orthography equivalence; neither category
  permits blanket final-letter deletion or arbitrary letter substitution.
  Exact accepted contexts remain in the private rubric until disjoint public
  teaching examples are prepared.
- **Repetitions include both copies.** The previous extra-copy-only convention
  is superseded. The transcript span includes the original phrase and its
  repeat(s); the reference span contains one copy. Actual repetition in the
  reference is clean. Existing repeat events were updated retroactively.
- **Repairs retain their mistake.** Wrong-then-correct is a corrected event,
  spanning both attempts. It is not absorbed into a benign repeat.
  Correct-then-incorrect restatement uses `substitution_mistake` across both
  attempts, with order explained in the note. No new special label is needed;
  speaker intent is not inferred.
- **Word spans are practical anchors.** Store exact selected words and
  zero-based half-open spans into original tokens. A connective change can
  select a word that also contains unchanged letters; the note explains the
  actual change. Character-level annotation is not currently required.
- **Group continuous replacements.** Merge adjacent same-label replacements
  across continuous spans. Matching words or separate attempt boundaries
  split events. This avoids arbitrary per-word event counts and double flags.
- **Openings are accounted for.** Review both istiadhah and basmala. Multiple
  formulas are ordered preamble segments; basmala assigned to its Quran ayah
  is ordinary reference text rather than an extra formula event.

## Synthetic span examples

These invented tokens illustrate the format and are not Quran/gold examples.
Reference tokens are `["A", "B"]`.

| Transcript tokens | Label | hyp_span | ref_span |
|---|---|---|---|
| `["A", "B", "A", "B"]` | `repetition_benign` | `[0,4]` | `[0,2]` |
| `["X", "B", "A", "B"]` | `substitution_corrected` | `[0,4]` | `[0,2]` |
| `["A", "B", "X", "B"]` | `substitution_mistake` | `[0,4]` | `[0,2]` |
| `["A"]` | `omission_mistake` | `[1,1]` | `[1,2]` |

The text order and quoted spans retain the difference between a repair and an
incorrect restatement without a second verdict field.

## Experimental interpretation and remaining work

The agent will annotate an unlabelled development pool and build an algorithm.
Only final algorithm outputs have independent gold comparison. Development
annotations remain unscored directly; successful final code is indirect
process evidence, not proof that every self-generated annotation was correct.

All 40 current inputs match the public Task A corpus; five approved recordings
overlap the published machine-labeled Task B pilot. Protect new adjudications
and membership, enforce runtime isolation, and report exposure honestly. A
claim of an unseen-input competition test requires a separate unreleased
collection. No record-level overlap list is published here.

Review findings settle the rules above but not the final algorithm input
contract, event matcher, scalar weights, run budgets, learner-disjointness
claim, or new-data availability. Those must be frozen before experiments.
The old pilot executable, old type/verdict schema, and old baseline scores
remain historical artifacts, not validation of this rubric.

See [the methodology](../METHODOLOGY-STUDY3.md) for the full protocol.
