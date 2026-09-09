# Annotation findings and decisions — 2026-09-08

**Completed review: 100/100 selected recording cases approved**, 314 ayah
chunks and 274 ayahs across 38 surahs. Taxonomy **v0.19**, recording format
**v0.6**. Three additional approved recordings are held as reserves outside
the scored set. No selected annotation decisions remain unresolved. These are
annotation findings. Evaluator v2.1 baseline results are now available; no
annotation-and-algorithm agent experiment has run.

Shared documentation contains aggregate results and synthetic examples.
Selected recording identities, transcripts, answer spans, reviewer notes and
dismissed interpretations remain in the separate private review workspace.

## Approved labels and counts

| Label | Meaning | Approved count |
|---|---|---:|
| `clean` | Chunk with no event after agreed comparison normalization | 233 chunks |
| `substitution_mistake` | Unresolved word/phrase replacement, including an incorrect final restatement | 62 events |
| `omission_mistake` | Missing reference material, including partial first/final ayahs | 26 events |
| `insertion_mistake` | Extra words not explained by a repeat or recognizable restatement | 1 event |
| `repetition_benign` | Reference-matching phrase repeated; span includes original and repeat | 5 events |
| `substitution_corrected` | Wrong attempt followed by a matching repair; span both | 4 events |
| `omission_corrected` | Missing material restored on a restart; span both attempts | 1 event |
| `letters_benign` | Spoken letter names faithfully represent the reference letter sequence | 4 events |
| `spelling_benign` | Specifically accepted spelling difference remaining after normalization | 12 events |
| `isti3adha_benign` | Istiadhah outside the assigned ayah | 29 formulas |
| `basmala_benign` | Basmala outside the assigned ayah | 18 formulas |

There are 115 within-ayah events and 47 opening formulas. Counts use different
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
- **Whole-ayah omissions require adjudication.** Under a reviewed continuous
  passage, an entirely absent intervening ayah can be represented by an empty
  chunk. Preserve the original source split and the explicit correction. Do
  not infer omissions from every gap or beyond a completed final ayah.
- **Normalization and spelling events differ.** Agreed hamza/diacritic and
  representation normalization receives no event. A residual spelling form
  that needs contextual acceptance receives `spelling_benign`. Wasl is a
  rationale in the note, not the label name. Approved contexts also include
  a standard-spelling/Quranic-orthography equivalence; neither category
  permits blanket final-letter deletion or arbitrary letter substitution.
  Accepted contextual categories include hamza-seat variants, word boundaries,
  and joined/assimilated written forms. Punctuation remains in raw tokens but
  is ignored for lexical comparison.
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

All 100 selected transcripts exactly match public Task A inputs; twelve also
match transcripts represented in the public machine-labelled Task B pilot.
Protect new adjudications and membership, enforce runtime isolation, and
report this exposure. A claim of unseen-input competition ranking requires a
separate previously unreleased collection.

The final algorithm receives **reviewed ayah splits, IDs and exact reference
texts**, with opening text but without gold labels. Ayah detection is outside
this event-annotation score. The executable interface, event matcher, scalar
weights and run design still need to be frozen. Legacy pilot code and scores
do not validate the completed set.

## Identity and distinct-case selection

All selected IDs and transcripts agree with both local source exports. There
are no reused recording IDs or audio paths and no full recitation duplicates
after punctuation-aware normalization. This does not prove distinct audio
bytes. Redundant clean subpassages are excluded; other overlaps are retained
only for a documented different event pattern or explicit clean/error contrast.
Token similarity and shared event signatures guide this review, not automatic
annotation. The set covers ten learner IDs, with 46 records from one learner;
no learner-balanced or independent-sample claim is made.

See [the methodology](../METHODOLOGY-STUDY3.md) for the full protocol.

## Colleague access and examples

[Illustrative JSON examples](STUDY3-LABEL-EXAMPLES.json) cover each label,
including both-attempt spans and an incorrect restatement. Non-Quran tokens
are deliberately invented; spelling and letter-name placeholders illustrate
structure, not linguistic allowances. Generic opening formulas have no
recording association. Prepare disjoint Quran-context teaching examples before
agent calibration.

The completed 100-recording answer set is in a separate owner-held reviewer bundle
(`index.html`, `gold.json`, `gold.jsonl`, `rubric.md`, `SHA256SUMS`). Human
colleagues can inspect the full transcript, every ayah reference, and event
spans offline. The bundle is not committed or publicly hosted; share it via a
private reviewer channel and exclude it from agent environments.

The bundle includes an offline searchable viewer, JSON/JSONL, the private rubric
and checksums. It excludes production identifiers and audio paths; the owner
retains a private attribution manifest. Approved reserves are separate. Ask
the dataset owner for the private human-review copy; it is not hosted in this
repository. The v2.1 baselines were evaluated privately; see
[the scorecard](../study3/EVALUATOR.md) and [results](../study3/BASELINES-v19.md).
