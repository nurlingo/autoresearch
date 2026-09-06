# Quran Recitation Checking from ASR Transcripts — competition dataset (v1.1 + Stage-2 pilot)

Anonymized release accompanying a Track-3 competition proposal (Muslims in ML @
NeurIPS 2026). License: CC BY 4.0. No audio, no user identifiers.

Two tasks on one set of 258 real, human-reviewed ASR transcripts of Quran
recitation (254 Quranic, 4 non-Quran negatives; 1,267 gold ayah chunks; 604
distinct ayahs from 37+ surahs; 10 reciters):

| | Task A — detect + split | Task B — within-ayah mistake events |
|---|---|---|
| input | one raw transcript | one gold ayah chunk + reference ayah text |
| output | ayah ids recited + per-ayah split of the words, or *abstain* | list of events, each `benign` / `corrected` / `mistake` / `uncertain` |
| files | `taskA/train.csv`, `taskA/test.csv` | `taskB/train.jsonl`, `taskB/test.jsonl` |
| metric | `research_score` = detection + split + abstain error (lower is better) | `study3_score` = 2·miss + false-alarm + benign + clean error |
| status | **frozen v1.1**, fully labeled, public | pilot: 99 chunks / 20 recordings labeled (LLM-proposed, human review pending); 1,168 chunks awaiting labels |

Both tasks share one recording-level 60/40 train/test split (151/107 rows) and
one id space: Task-B chunk `train-004-c00` is chunk 0 of Task-A row `train-004`.

## Files

```
taskA/train.csv, test.csv      id, transcript, ayah_assignment, confidence, transcript_split_by_ayahs, actual_ayahs
taskA/quran_ref.json           {surah: [{id, ar, clean}]} — Uthmani text + harakat-free canonical form
taskB/train.jsonl, test.jsonl  one JSON object per gold chunk (schema below)
sample/                        the 10% review sample: 26 recordings (both tasks), IDS.txt
SHA256SUMS
```

### Task A row
`ayah_assignment` is an ayah id (`SSSAAA`), a contiguous range (`002001-002005`), a
comma-separated list for non-contiguous recitations, or `non_quran`.
`transcript_split_by_ayahs` is a JSON list of `{id, transcript}` — the gold
assignment of transcript words to ayahs (repeated ids = the ayah was recited
twice). `confidence` is the reviewer's confidence (high/medium; medium rows are
scored, low would not be).

### Task B chunk
```json
{"chunk_id": "train-004-c00", "row_id": "train-004", "chunk_idx": 0, "n_chunks": 11,
 "is_last_chunk": false, "ayah_id": "044019",
 "chunk_text": "…", "reference_text": "…", "confidence": "high",
 "label_status": "machine" | "reviewed" | "unlabeled", "labeled_by": "…",
 "events": [{"type": "substitution", "verdict": "mistake",
             "hyp_words": "أعيدكم", "ref_words": "اتيكم",
             "hyp_span": [1, 2], "ref_span": [6, 7], "note": "…"}] | null}
```
`events == []` is a reviewed **clean** chunk; `null` = not yet labeled (never
scored). Event types: `restart_repeat`, `full_repeat`, `stutter`,
`self_correction`, `substitution`, `omission`, `insertion`, `word_order`,
`truncation`, `asr_garble`. Spans are `[start, end)` indices into the
whitespace tokens of the canonicalized text (NFKC; fold أ/إ/آ/ٱ→ا, ى→ي, ؤ/ئ→ء;
harakat removed); a zero-length span is an insertion point.

## Provenance, consent, privacy

Recordings are production interactions of adult users with a
Quran-memorization chat bot, contributed under the application's terms of
service, which disclose that recitations may be reviewed to improve the
service. Audio was transcribed by a commercial ASR model; only the
**transcript text** is released. Learner and recording identifiers are removed
and replaced by sequential surrogate ids. The four non-Quran transcripts were
checked by hand and contain no personal content. Quranic text is a closed
public canon, so transcripts carry essentially no personal information.

Gold labels for Task A were produced by LLM-assisted pre-labeling followed by
human review of every row. Task-B pilot labels were proposed by an LLM from
the transcript and reference text and are marked `labeled_by:
claude+human-pending` until a human reviewer signs them off; a competition
release will contain only `reviewed` chunks.

## Integrity

`SHA256SUMS` pins every file. Task-A files are byte-identical to the public
v1.1 release used in the accompanying paper (hashes `fa2cb114…` / `deef397e…`).
