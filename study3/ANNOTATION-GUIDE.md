# Transcript event annotation — teaching draft

Status: draft for human review, based on taxonomy v0.19. The teaching examples
and operational details below are not yet a frozen experiment contract.

## What you annotate

Compare the supplied ASR text with the supplied Quran reference. Annotate what
is written; do not infer the audio, the speaker's intent or whether ASR caused
a mismatch. Do not remove repeats or repair the transcript before annotation.
Unwritten vowels and tajweed are outside this task.

Inputs contain reviewed ayah chunks, ayah IDs and exact reference texts. Do not
redetect ayahs or change their assignment. Opening formulas remain separately
available as unlabelled text. Source corrections and gold review notes are not
part of the input. The executable envelope still needs to be frozen.

Reference text comes verbatim from `quran.json` → `titles.clean`. Normalization
is a comparison operation; never rewrite the saved transcript or reference.

## Labels

| Label | Use when |
|---|---|
| `clean` | The chunk has no events after agreed comparison normalization. Use an empty event list; do not create a clean event. |
| `substitution_mistake` | Reference words are replaced by an unresolved alternative, including a correct attempt followed by an incorrect restatement. |
| `omission_mistake` | Reference material is absent, including missing beginnings or endings. |
| `insertion_mistake` | Extra transcript words are neither a repeat nor part of a recognizable repair/restatement. |
| `repetition_benign` | A reference-matching phrase is repeated. Select the original and all extra copies against one reference copy. |
| `substitution_corrected` | A wrong attempt is followed by its reference-matching repair. Select both attempts. |
| `omission_corrected` | An incomplete attempt is restarted and the missing material restored. Select both attempts. |
| `letters_benign` | Spoken letter names express the complete reference letter sequence. |
| `spelling_benign` | An explicitly accepted contextual spelling difference remains after normalization. Explain it; do not excuse arbitrary letter changes. |
| `isti3adha_benign` | An istiadhah is used outside the assigned ayah. |
| `basmala_benign` | A basmala is used outside the assigned ayah. A basmala that is the assigned ayah is ordinary reference text. |

These are single semantic labels, not separate event/verdict fields. Review
approval is metadata, not a prediction label. Multiple events can occur in one
chunk. `clean` is mutually exclusive with a nonempty chunk event list.

## Working procedure

1. Read the whole chunk and reference before aligning individual words.
2. Compare under agreed normalization. Ordinary hamza-bearing alif differences,
   diacritics and punctuation alone do not create events. The exact executable
   normalization table still needs freezing; do not add equivalences silently.
3. Look for attempts, restarts and repairs. Classify their outcome before
   labelling leftover replacements, omissions and insertions.
4. Attach exact transcript/reference words and spans to every event.
5. Check complete coverage: do not omit an error because another event already
   exists in the chunk, and do not flag the same attempt twice.

Possible ASR origin never changes `substitution_mistake` into benign. If a new
context is ambiguous during practice, record a question for review rather than
inventing a label or silently broadening a rule. The final-run handling of
unsupported cases must be settled before freezing.

## Spans and grouping

The teaching cases use original whitespace tokens, zero-based half-open spans:
`[start, end]` selects tokens from start through end minus one. Quoted words must
equal the joined selected tokens. Normalized strings never supply the indices.
An omission has an empty hypothesis span at its location; an insertion has an
empty reference span. Do not assign an omitted word to a neighboring token.

Merge adjacent same-label replacements only when both sides are continuous.
Correct words, gaps and distinct attempt boundaries separate events. A word
containing a changed connective is selected as a whole; explain the differing
letters in the note. Character spans are not required.

A repeat spans original plus copies. A repair spans wrong plus corrected
attempts. A correct-to-incorrect restatement spans both attempts and receives
`substitution_mistake`; note their order. Context inside such a span is not all
erroneous. Do not additionally annotate the same span as an insertion/repetition.

Missing initial/final material is an omission even at a recording boundary.
A wholly absent ayah is an empty supplied chunk only after human adjudication
establishes the intended continuous passage. Do not infer omissions from
arbitrary ID gaps or beyond a completed final ayah.

## Normalization versus spelling

A context-independent comparison equivalence receives no event. A residual
spelling equivalence requiring explicit contextual acceptance receives
`spelling_benign`; wasl belongs in the explanation, not the label name.

The teaching draft includes a proposed word-boundary example. It requires
approval and does not authorize joining arbitrary words. There is no blanket
equivalence between all final letters, between ة and ت, or between a missing
connective and its presence. Letter-name sequences have their own label; an
incomplete sequence for a one-token reference is a substitution with the
missing letter identified in the note.

## Before this becomes the agent guide

Approve the Arabic examples, add counterexamples for every accepted contextual
spelling category, and freeze normalization (including punctuation-only token
handling). The current private rubric contains a punctuation-token wording
ambiguity; resolve it without changing existing saved event indices silently.
Then verify comprehension on separate practice inputs. Teaching, practice,
development and final evaluation are different roles; no gold answers or
selected-case hints belong in this guide or an agent runtime.
