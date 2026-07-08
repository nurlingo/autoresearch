# Study 3 — Within-Ayah Mistake Detection (Stage 2)

Design document: dataset and experiment methodology. Status: **planned** —
labeling not yet started; no runs. This document is written *before* any data
or code so that the harness is preregistered, per rule R5 of Studies 1–2.

## 1. Task

Stage 2 of the transcript-only memorization checker. Input: **one ayah chunk**
(the transcript words Stage 1 assigned to a single ayah) plus the reference
ayah text. Output: a list of **events**, each classified:

```
{"type": <event-type>, "verdict": "benign" | "corrected" | "mistake" | "uncertain",
 "hyp_span": [i, j], "ref_words": [...], "hyp_words": [...]}
```

The product question is: *should this reciter be flagged, and for what?* A raw
diff cannot answer it — recitation is full of benign phenomena that a diff
reports as errors. The canonical example: a reciter stops to breathe, repeats
the last few words, and continues; a naive diff calls that an insertion.

### Event taxonomy (v1 — frozen before labeling)

| type | description | default verdict |
|---|---|---|
| `restart_repeat` | stops, re-recites last 1–5 words, continues | benign |
| `full_repeat` | entire ayah (or long span) recited again | benign |
| `stutter` | same word repeated adjacently 2–3× | benign |
| `self_correction` | wrong word immediately followed by its correction | corrected |
| `substitution` | wrong word in place of a reference word | mistake |
| `omission` | reference word(s) skipped | mistake |
| `insertion` | word(s) not in the reference, not explained above | mistake |
| `word_order` | reference words recited out of order | mistake |
| `truncation` | ayah abandoned partway (last ayah of recording exempt) | mistake |
| `asr_garble` | diff without recitation-plausible structure | uncertain |

`uncertain` is a first-class output, not a failure: transcript-only input
cannot always separate ASR error from recitation error (accepted ceiling since
Stage 1; also invisible: vowel/tajweed mistakes). The metric treats `uncertain`
separately — an algorithm that says "uncertain" is not rewarded as correct nor
punished as wrong on those events (see §4).

## 2. Dataset

### Sources

**Phase 1 (current scope): bot-split chunks only.** The 258 gold-split rows
(v1.1) explode into per-ayah `(chunk, reference)` pairs — ~1,000+ chunks with
real ASR noise and real recitation behavior. Ayah-level repeats are already
encoded (repeated ids in the split); within-ayah events are what Phase-1
labeling adds. One dataset, one review pass, both stages verifiable per
recording.

Deferred to later phases (documented so they are not forgotten):
- **Single-ayah app recordings (scale):** 21,053 production recordings with
  `payload.ayah_id` — stratified sampling once Phase 1 saturates.
- **User feedback events (adversarial gold):** app approve/report stream —
  enriched for benign-flagged-as-mistake cases; label all reported cases,
  analyze as `source=user_report` subgroup.

### Timestamps (known gap)

The gold dataset has **no time alignments** — splits are word-level text only,
and the production STT configuration (gpt-4o-mini-transcribe / Tarteel) does
not return word timestamps. Consequence: review is full-recording audio +
highlighted text, not per-chunk seeking. If per-ayah audio becomes necessary,
two derivation routes exist: (a) CTC forced alignment of the stored transcript
against the audio (`ctc_alignment_service.py` already in the worker), or
(b) re-transcription with a timestamp-capable model. Out of scope for Phase 1.

### Labeling — STATUS (2026-07-08)

**A calibration batch of 20 recordings is labeled** (99 chunks, 87% clean; 17
events: 11 substitution, 3 omission, 2 truncation, 1 full_repeat) and visible
in the deployed dataset editor (Review tab). Labels are marked
`labeled_by: claude+human-pending` — machine-proposed, awaiting human review.

**The storage format below is PROVISIONAL, not signed off.** Events currently
store verbatim `words` (hypothesis) + `ref` (expected) + `note`, attached to
gold-split chunks by index, one JSONL line per recording
(`fixtures/bot_review/bot_events.jsonl`). Known open questions from the
calibration batch, to resolve before scaling to all 258:
1. Final-letter drops (e.g. يغشى→يغش): policy for `uncertain` vs `mistake`?
2. Truncation on the recording's last ayah: keep the benign exemption?
3. Mistakes inside abandoned first attempts (within a `full_repeat`):
   separate events or swallowed by the repeat?
4. Format itself (verbatim words vs word indices; per-event vs per-chunk
   confidence) — revisit after human review of the calibration batch.

### Labeling

- **Schema per chunk:** `chunk_id, recording_id, ayah_id, chunk_text,
  reference_text, events[] (taxonomy above), confidence (high/medium/low),
  notes`. Chunks with no events are labeled `clean` — the majority class and
  the most important one to protect (false-flag rate).
- **Workflow:** LLM-assisted pre-labeling → human review, the same pipeline
  that produced the 258 Stage-1 splits.
- **Review tooling (built):** the dataset editor's **Review tab**
  (`follow_my_reading/backend/tests/dataset_editor.py`, tab "Review") shows,
  per recording: audio (production proxy), full transcript, each gold chunk
  against its reference (words absent from the reference underlined), a
  split correct/wrong verdict (Stage-1 verification), and per-chunk event
  labeling with this taxonomy (Stage-2). Labels persist to
  `fixtures/bot_review/bot_events.jsonl` (gitignored, production-derived).
- **Conventions (frozen with the taxonomy):** events are anchored to the
  *hypothesis* word indices; a self-correction consumes both the wrong word
  and its correction; a restart_repeat span must re-match ≥1 reference word
  already consumed; when two readings are defensible, label `uncertain` and
  set confidence=medium. `low`-confidence chunks are kept but not scored.
- **Versioning:** dataset frozen by SHA-256 before any run (`make freeze`
  pattern); labels never change mid-study; corrections happen between studies
  with a version bump (v1 → v1.1 precedent from Study 2).

### Split (R1 — held out from day one)

Stratified 60/40 **by recording** (never by chunk — chunks from one recording
share ASR quirks and reciter behavior; splitting them would leak). Strata:
event-type presence, clean/non-clean, source (bot / app / user_report),
chunk length. Test oracle floor must be exactly 0 before freezing. The loop
optimizes train only; experimenters score held-out.

## 3. Harness (applying the five rules from Studies 1–2)

- **R1 Held-out:** as above; train↔test gap reported per arm.
- **R2 Leak-free feedback:** the scorecard's failure report shows chunk ids
  and the *predicted* events only — never gold events or verdicts.
- **R3 Isolation by construction:** fresh single-commit clone per run
  (`tools/new_run.sh` pattern); clone contains harness + train.csv only.
- **R4 Agent-tooling state channels:** unique run paths, post-run audit of
  persistent memory and global config (both agents; procedure in
  METHODOLOGY.md).
- **R5 Components + preregistration:** hypotheses in §6 below, fixed before
  labeling completes; the scalar score always reported with its components.

Editable surface: `solution3.py` implementing
`Solution.detect_events(chunk_text, reference_text) -> [events]`. Fixed:
`eval3.py`, `data/`, `PROGRAM3.md`. Reference (`quran_ref.json`) available as
in Stages 1–2.

## 4. Metric (DRAFT — schema under review)

> The reward/penalty weights below are a starting proposal, not preregistered
> yet. They will be reviewed (weighting of FN vs FP, uncertain pricing,
> per-event vs per-chunk aggregation) BEFORE the dataset is frozen; H1–H4
> freeze together with the final metric.

Event matching: predicted event matches a gold event if types match and hyp
spans overlap ≥50%. Then:

```
flag_error    = (FP_mistake + 2·FN_mistake) / gold_mistake_opportunities
benign_error  = fraction of benign/corrected gold events predicted as mistake
clean_error   = fraction of clean chunks with ≥1 predicted mistake   # false-flag rate
study3_score  = flag_error + benign_error + clean_error              # lower is better
```

- FN weighted 2× (missing a real mistake is worse than an extra review —
  carried over from the Stage-1 harness design).
- `uncertain` predictions: excluded from FP counts, but a gold *mistake*
  predicted `uncertain` counts 1 (half-credit vs FN=2). This prices timidity
  without making "uncertain everywhere" viable.
- `clean_error` is the user's headline case (breath-repeat flagged) as its own
  component; with the majority of chunks clean, it is deliberately hard to
  game.
- Components reported always; scalar exists only for the loop.

## 5. Arms, budget, protocol

Same design as Study 2 unless noted: Claude Code (Opus, `high`) vs Codex
(GPT-5.5, `high`), 3 runs each, 30 experiments or 1 h per run, identical
verbatim launch prompt, uniform `make exp` logging, collection with automatic
held-out scoring + git bundle. Community arms welcome after the core matrix
(exploratory, separate hardware/confounds table, per Study 2 §7 precedent).

**Incumbent baseline on day one:** the production stack — `repetition_handler`
+ `transcript_cleaner` + `asr_compare` ops — wrapped in the Stage-2 contract
and scored on the frozen test split *before* any agent run. (Study 1–2 lesson:
the incumbent comparison is the applied headline, not an afterthought.)

## 6. Preregistered hypotheses

- **H1:** Every agent arm beats the incumbent heuristic stack on held-out
  `study3_score`, driven primarily by `clean_error` (the destructive
  normalize-then-diff design over-flags benign events).
- **H2:** The behavioral signatures of Studies 1–2 persist: Codex uses more
  experiments and reaches lower train scores; train↔test gap larger for
  Codex; disposition stable across runs.
- **H3:** With the held-out split disclosed (as in Study 2), no arm hardcodes
  per-chunk answers (≤ fixed-closed-set constants only, muqatta'at-style).
- **H4:** `uncertain` usage differs by arm — the generalizer profile uses it
  more; over-use is bounded by the half-credit pricing (§4).

## 7. Deliverables & sequencing

1. Labeling tooling extension (`bot_review.py` event mode) + chunk export.
2. Labeled dataset v1 (target: all bot chunks + 300–500 app chunks + all
   user-report cases), frozen split, oracle-floor check.
3. `eval3.py` + `PROGRAM3.md` + stub `solution3.py`; incumbent baseline run.
4. 3×2 core matrix; collection; analysis vs H1–H4.
5. Paper 2 candidate: "Stage 2: agents vs the heuristic stack, with
   user-reported ground truth."

Timing: starts after the AIST submission (paper deadline 2026-07-10). Step 1
can run in the background before that (labeling is human-time-bound, not
compute-bound).
