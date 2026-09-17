# Granular annotation review

The current working edition has **200 distinct recordings / 1,038 units / 469 events**, split into 100 train and 100 test cases. All 200 cases are now owner-approved; there are no open `review_questions` entries. See [CURRENT-STATE.md](../CURRENT-STATE.md) for the 100/100 freeze, split audit and remaining work.

## Event representation

A recording stores `case_id`, `recording_id`, a natural-language `summary`, full `transcript`, ordered `units`, and one canonical `events` list. Units contain supplied transcript/reference text, whitespace tokens, their own `summary`, `chunk_idx`, `ayah_id`, and `event_ids` linking to the recording's events.

An event has one combined `label`, `hyp_locations` and `reference`. Each hypothesis location supplies `chunk_idx`, a zero-based, end-exclusive word `span`, and exact `words`. The reference supplies its own `ayah_id`, word `span` and exact `words`. Empty spans anchor omissions or insertions. Multiple locations remain one event; a cross-ayah event is not duplicated.

- Correct words repeated: `repetition_benign`, linking every occurrence, including the final one. Currently 45 events / 93 locations.
- Wrong wording repaired: `substitution_corrected`, linking wrong attempts and the final matching replacement. Correct repeated context is a separate repetition event.
- Wrong wording left unresolved: `substitution_mistake`. Multiple failed attempts or a correct-to-wrong transition can share one target.
- Missing wording restored: `omission_corrected`, linking the initial empty position and later text, within or across ayahs.
- Missing wording left absent: `omission_mistake`. Extra wording: `insertion_mistake`.
- Contextual spelling, spelled-out opening letters, isti3adha and basmala retain their corresponding `_benign` labels.

For ambiguous opening fragments, require repeated matching context or another independent anchor to establish two attempts at one reference target. Otherwise use insertion for extra wording before an intact opening. A donor phrase from another ayah is insufficient by itself. Keep granular grouping consistent even when a whole-passage interpretation seems more natural; record the alternative in a note.

Summaries describe transcript evidence, not unheard audio or attribution of a difference to the speaker versus ASR. The reference now preserves hamza. Follow the approved [hamza policy](HAMZA-POLICY.md), including plain-alif notation and contextual seat differences.

## Reproducibility and access

The authoritative private files are `train_review/granular-corpus/recordings.jsonl`, `split-train.jsonl` and `split-gold.jsonl`. Obsolete aggregate exports, reports and scratch backups have been archived privately; per-case exports and dated adjudication notes remain historical source evidence. The current viewer is rebuilt from the JSONL.

Colleagues need a current private bundle to inspect actual cases. Test answers, case membership and review history must not enter the development agent environment. The agent uses answer-free train inputs; final frozen code is evaluated against test separately.

Evaluator v2.3 (`eval21.py`) reads recording-level multi-location annotations but accepts per-unit single-span predictions. It credits any one matching location per event and does not score recovery of all linked attempts. See [EVALUATOR.md](../EVALUATOR.md) for the verified fixes and retained adapter limitations.

## Historical checkpoint

Before the hamza audit on September 15, the authoring corpus had 188 recordings, 1,022 units and 439 events, selected from 227 transcript candidates. Its old source-review statuses and ten interpretation questions are historical; they are not today's approval status. Frozen gold100 and train release v1.0 remain separate experimental artifacts.
