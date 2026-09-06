# Stage 2 — Within-ayah mistake events: data schema v1 (proposed freeze)

Status: **v1-proposed (2026-09-06)** — defaults for the four open questions of
`METHODOLOGY-STUDY3.md` §2 are set below; awaiting sign-off (Nursultan /
Mohamad). Once signed off, this file is frozen with the dataset (SHA-256 in
`stage2/runs/inputs.sha256`) and any later change is a version bump.

## 1. Unit of data: one gold chunk

One line of `stage2/data/{train,test}.jsonl` per `(recording, ayah)` chunk of the
Stage-1 gold split — the transcript words a reviewer assigned to one ayah.
Row ids are the public surrogate ids of the released Stage-1 dataset
(`train-001`…, `test-001`…; identical to the Hugging Face release), so both
tasks share one recording-level split and one id space.

```json
{"chunk_id": "train-004-c00", "row_id": "train-004", "chunk_idx": 0, "n_chunks": 11,
 "is_last_chunk": false, "ayah_id": "044019",
 "chunk_text": "<transcript words of this ayah, as recited>",
 "reference_text": "<canonical harakat-free ayah text from quran_ref.json>",
 "confidence": "high",
 "label_status": "reviewed" | "machine" | "needs_review" | "unlabeled",
 "labeled_by": "claude+human-pending",
 "events": [ {event}, ... ] | null }
```

`events == []` means the chunk was reviewed and is **clean**. `events == null`
means not yet labeled (never scored). Only `reviewed` chunks are scored in the
frozen competition data; `machine` (LLM-proposed, human-pending) chunks are
scored in the pilot and flagged as such.

## 2. Event

```json
{"type": "substitution", "verdict": "mistake",
 "hyp_words": "أعيدكم", "ref_words": "اتيكم",
 "hyp_span": [1, 2], "ref_span": [6, 7], "note": "free text"}
```

| field | meaning |
|---|---|
| `type` | one of the ten taxonomy types (METHODOLOGY-STUDY3 §1) |
| `verdict` | `benign` \| `corrected` \| `mistake` \| `uncertain` |
| `hyp_words` | verbatim words in the *chunk* the event covers (empty for omission) |
| `ref_words` | verbatim words in the *reference* the event covers (empty for repeats/insertions) |
| `hyp_span` | `[start, end)` token indices into `canon(chunk_text)`; zero-length `[i, i]` = insertion point (omission) |
| `ref_span` | `[start, end)` token indices into `canon(reference_text)`; `null` when not applicable |

Spans are **derived** by `stage2/tools/export.py` from the verbatim words
(labelers never type indices). Tokenization is `eval.canon` — the same
metric-only canonicalizer as Stage 1 (NFKC, fold أإآٱ→ا, ى→ي, ؤ/ئ→ء, strip
harakat, split on whitespace). A span that cannot be derived is `null` and the
chunk becomes `needs_review`.

## 3. Verdicts

- **benign** — normal recitation behaviour, not a mistake: restart/breath
  repeat, full repeat, stutter, last-ayah truncation.
- **corrected** — a mistake the reciter fixed themself (self_correction).
  Reported to the learner as a note, *not* as a flag.
- **mistake** — a genuine recitation error that should be flagged.
- **uncertain** — the transcript alone cannot separate ASR error from
  recitation error. Neither rewarded nor punished by the metric.

## 4. Decisions on the four open questions (defaults, v1)

1. **Final-letter drops** (يغشى→يغش, كاشفو→كاشف, فتنا→فتن): `substitution` with
   verdict **`uncertain`**. Rationale: word-final vowels/alif are exactly what
   the production ASR drops most; on transcript-only input this is not
   separable from a recitation error. A system may output `mistake` or
   `uncertain` on these without penalty. If the *whole word* changes
   (ادوا→أنذروا) it is a `mistake`.
2. **Truncation on the last ayah of a recording**: **exemption kept** — verdict
   `benign` when `is_last_chunk` is true (the reciter simply stopped the
   recording), `mistake` otherwise. The `is_last_chunk` flag is in the data,
   so the rule is mechanically checkable.
3. **Mistakes inside an abandoned first attempt** (within `full_repeat` /
   `restart_repeat`): **swallowed by the repeat** — one benign repeat event
   whose `hyp_span` covers the abandoned attempt; only the *final* attempt is
   assessed for mistakes. Rationale: the product question is "should this
   reciter be flagged"; a self-abandoned attempt is by definition corrected.
   The labeler may record the abandoned-attempt error in `note`.
4. **Format**: verbatim `hyp_words`/`ref_words` remain the human-facing label
   (what the Review tab stores); `hyp_span`/`ref_span` are derived, not typed.
   Confidence stays per *chunk* (Stage-1 `confidence`), and per-event
   uncertainty is expressed through the `uncertain` verdict, not a number.

## 5. Matching rule used by the metric

For repeat-type gold events (`restart_repeat`, `full_repeat`, `stutter`) the
derived `hyp_span` covers both copies (first attempt + echo), so flagging either
copy counts as touching the event. A predicted event *matches* a gold event when their `hyp_span`s overlap in at
least one token, or — for zero-length spans (omissions) — when the insertion
points are within one token of each other, or when both have `ref_span`s that
overlap. Type is **not** required to match for the flag components; type
agreement among matched pairs is reported separately (`type_error`).
