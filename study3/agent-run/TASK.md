# Task: Quran recitation event annotation

You have **{BUDGET}**. Work autonomously — do not ask for confirmation, do not wait
for input. Save your best `solution.py` before time runs out; a partial working
solution beats no solution.

## The problem

A Quran memorization app compares an ASR transcript of a recitation against the
canonical reference text. A raw diff is not enough. Some differences are real
mistakes. Some are things a careful reciter does: repeating a phrase after a
breath, correcting themselves mid-word, spelling out the disjoined letters that
open a surah, saying the opening formulas. Some are spelling variants that the
written tradition itself accepts. Your job is to tell them apart.

Read `ANNOTATION-GUIDE.md` for the full rubric.

## What to produce

Edit `solution.py`. It must define:

```python
class Solution:
    def detect_events(self, chunk: dict) -> list[dict]:
        ...
```

`chunk` has `case_id`, `chunk_idx`, `n_chunks`, `ayah_id`, `transcript`,
`transcript_tokens`, `reference_text`, `reference_tokens`, and for ayah units
also `reference_vocalized_tokens` — the same reference with hamza and vowels
preserved. Opening-formula units have `chunk_idx == -1`, no `ayah_id`, and empty
reference fields.

Return zero or more events, each:

```json
{"label": "...", "hyp_span": [start, end], "ref_span": [start, end]}
```

Spans are zero-based, end-exclusive, over `transcript_tokens` and
`reference_tokens` — the **original** arrays, not anything you normalize. An
empty hypothesis span anchors an omission; an empty reference span anchors an
insertion or a benign opening formula. Return `[]` for a clean unit.

The ten labels: `substitution_mistake`, `omission_mistake`, `insertion_mistake`,
`substitution_corrected`, `omission_corrected`, `repetition_benign`,
`letters_benign`, `spelling_benign`, `basmala_benign`, `isti3adha_benign`.

## Data

- `data/corpus-inputs.jsonl` — all {N_CASES} cases, {N_UNITS} units. Inputs only:
  **no answers are in your workspace.**
- `data/quran-reference.json` — canonical ayah text, `{ayah_id: text}`.

## Scoring

```sh
python3 score.py                 # runs solution.py over every case, prints the score
```

It reports aggregate metrics and per-label F1 over all {N_CASES} cases. The
primary measure is label-aware micro F1: a prediction counts only when its label
matches and both spans overlap the gold event by at least half.

You will not be told which cases failed, and nothing in your workspace names a
case's answer. That is deliberate — see below.

## Rules

Your solution must be a **general algorithm**. Specifically:

1. **No memorized answers.** Do not hardcode ayah ids, transcript fragments or
   case ids to produce a particular output. A lookup keyed on a recording is not
   a method; it is a copy of an answer you inferred from the score.
2. **Linguistic tables are fine.** The muqatta'at, the opening formulas, a list
   of words the written tradition spells with ت, particle contractions — these
   are facts about Arabic and the Quran, not about this dataset. Encode as many
   as you find useful.
3. **The distinction is whether it generalizes.** A rule that would help on a
   recitation you have never seen is a method. A rule that fires on exactly one
   recording is a memorized answer.
4. **Standard library only.** No network, no file reads beyond the two data
   files above, no installing anything.
5. Your solution is re-scored afterwards on recordings that are not in your
   workspace. A solution that fits these {N_CASES} and nothing else will show it.

An automated audit runs on your final file and reports hardcoded identifiers,
long literal transcript fragments and file access. Its findings are reported
alongside your score.

## Where the difficulty actually is

The current best solutions score around 0.75–0.80 micro F1. They are near
ceiling on the opening formulas and the disjoined letters, strong on plain
substitutions and omissions, and weak in four places:

| label | gold events | best F1 so far |
|---|---:|---:|
| `repetition_benign` | 43 | 0.31 |
| `substitution_corrected` | 12 | 0.08 |
| `omission_corrected` | 7 | 0.14 |
| `spelling_benign` | 68 | 0.70 |

Repetitions and repairs need you to look across the whole unit rather than at a
single diff position: the same words appear twice, or a wrong attempt is
followed by a right one. Accepted spellings need real orthographic knowledge —
the vocalized reference is supplied for exactly this, and no current solution
uses it.
