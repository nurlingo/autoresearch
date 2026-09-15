# Granular annotation review

Current update: [hamza policy and audit](HAMZA-POLICY.md). The working edition now has 194 cases, 1,028 units and 458 events, including six new autodetect drafts; the checkpoint below records the state before that audit. Granular grouping is applied consistently, including parallel-ayah passage replacements. A broader episode interpretation may be documented in a note, without changing event grouping. For opening fragments, a donor phrase alone is insufficient to establish a corrected substitution; require repeated matching context or other independent evidence of two attempts at the same reference target. Otherwise use insertion for extra text before an intact opening.

## Checkpoint before the hamza audit — 2026-09-15

The private working corpus contains 188 distinct recordings, selected from 227 transcript candidates by retaining one transcript per identical-audio group. Its current review edition has 1,022 units and 439 localized events. It combines historical gold and development cases; it does not redefine the frozen experimental split.

Every recording and every ayah has a brief natural-language `summary` describing the observed transcript and event sequence. Original IDs, source hashes and human review statuses are retained. Source statuses are 146 reviewed, one partially reviewed and 41 draft; the revised representation is assistant-reviewed, not a new set of human approvals. Ten cases still carry interpretation questions.

## Event representation

A recording stores `case_id`, `recording_id`, `summary`, full `transcript`, ordered `units`, and one canonical `events` list. Units contain transcript/reference text, word tokens, `summary`, `chunk_idx`, `ayah_id`, and `event_ids` linking to the recording's events.

An event has one `label`, `hyp_locations` and `reference`. Each transcript location supplies `chunk_idx`, a zero-based, end-exclusive whitespace-word `span`, and exact `words`. The reference supplies its own `ayah_id`, word `span` and exact `words`. Empty spans anchor omissions or insertions. Multiple locations remain one event; cross-ayah events are not duplicated for scoring.

- Correct words repeated: `repetition_benign`, listing every occurrence, including the final one. The checkpoint has 43 repetition events with 89 locations.
- Wrong wording repaired: `substitution_corrected`, linking attempts and the final matching replacement. Correct repeated context is a separate repetition event.
- Wrong wording left unresolved: `substitution_mistake`. Multiple failed attempts or a correct-to-wrong transition can share a target event.
- Missing wording restored: `omission_corrected`, linking the initial empty position and later text, within or across ayahs.
- Missing wording left absent: `omission_mistake`. Extra wording: `insertion_mistake`. Initial position alone does not decide insertion versus corrected substitution; surrounding lexical context matters.
- Contextual spelling, spelled-out opening letters, isti3adha and basmala retain their corresponding `_benign` labels.

Summaries explain annotations; they do not infer unheard audio or whether an error came from a speaker or ASR. Spelling is benign when the accepted reading in that context is equivalent. Hamza-seat variants do not authorize arbitrary addition or deletion of pronounced hamza. The audit is complete and all 15 presented hamza events are owner-approved. Remaining work is listed in [CURRENT-STATE.md](../CURRENT-STATE.md).

## Reproducibility and access

The private `train_review/granular-corpus/` directory contains individual JSON data points, `recordings.jsonl`, a self-contained HTML viewer, source manifest, change log and validation reports. Source text/ID/hash checks, exact spans, repeated/corrected correspondence, word accounting and viewer rendering pass. One documented spelling-within-repair overlap is intentional.

The author keeps the annotation answers and source attribution outside this public repository. Colleagues need the private review bundle to inspect actual cases. It must not enter an evaluation agent's workspace. Frozen gold100 and the existing agent input release are byte-unchanged.

The existing evaluator does not support the new multi-location format. Scoring support, approval of remaining interpretations and a new frozen release are outstanding work; previous experiment numbers remain tied to their original release and evaluator.
