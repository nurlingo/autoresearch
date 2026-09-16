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

Read `ANNOTATION-GUIDE.md` for the full rubric, then read the annotated train
split: {N_EVENTS} events over {N_CASES} real recordings, labelled to that rubric.
The guide states the conventions; the data shows them applied.

## What to produce

Edit `solution.py`. It must define:

```python
class Solution:
    def detect_events(self, chunk: dict) -> list[dict]:
        ...
```

It is called **once per unit** — one ayah, or one opening formula. The call does not provide the whole recording. This limits inference about
cross-ayah repairs; do not assume information from a previous call will be
available. The data file below supplies recording context during development.

### The unit it receives

| key | what it is |
|---|---|
| `case_id` | the recording this unit belongs to |
| `chunk_idx` | position in the recording; `-1` marks an opening-formula unit |
| `n_chunks` | how many ayah units the recording has |
| `ayah_id` | six digits, e.g. `002219`; `None` on a formula unit |
| `transcript`, `transcript_tokens` | what was recited, and the same split on whitespace |
| `reference_text`, `reference_tokens` | the reference: hamza written, no vowel marks |

The reference is written the way the reciter's transcript is: أ إ آ and ى kept
as they are, no vowel marks. Compare the supplied spellings contextually:

- bare **ا** where the reference writes **أ** or **إ** — hamza notation left off,
  `spelling_benign`
- explicit **initial إ** where the reference writes **أ**, including after an
  attached particle — a meaningful distinction, `substitution_mistake`; contextual
  medial/final seat differences can instead be `spelling_benign`

Vowel marks are deliberately absent: an unwritten vowel is not evidence, and
hamza above an alif does not by itself distinguish one vowel from another.

A formula unit (`chunk_idx == -1`) carries the isti'adhah or basmala as its
transcript and has empty reference fields.

### What it returns

A list of events, each:

```json
{"label": "...", "hyp_span": [start, end], "ref_span": [start, end]}
```

Spans are zero-based and end-exclusive over `transcript_tokens` and
`reference_tokens` — the **original** arrays, not anything you normalize. An
empty hypothesis span anchors an omission at that position; an empty reference
span anchors an insertion or a benign opening formula. Return `[]` for a clean
unit.

### One event per phenomenon, not per occurrence

This is the part that costs the most marks if you get it wrong.

An event describes **something that happened**, not every place you can see it.
When a reciter repeats a phrase, that is *one* `repetition_benign` event, even
though the words appear twice. When they say a word wrongly and then correct
themselves, that is *one* `substitution_corrected` event covering the attempt
and the repair, not one event per attempt.

```
said:      وحيث ما كنتم فولوا وجوهكم شطره  وحيث ما كنتم فولوا وجوهكم شطره
reference: وحيث ما كنتم فولوا وجوهكم شطره

correct:   one repetition_benign event
wrong:     two repetition_benign events — the second scores as a false positive
```

Emit one event and point its `hyp_span` at any one of the occurrences; the
grader accepts whichever you choose within a unit carrying the event's actual
reference ayah. For a cross-ayah omission repair, use the restored occurrence
in that ayah; a neighbouring ayah cannot supply its reference coordinates. Emit one per occurrence and every extra is
a false positive.

The human annotation format links repeated occurrences, wrong attempts and
repairs through multiple locations. Some `substitution_mistake` events also link
several failed attempts at one target. The present prediction interface selects
one location; it does not require reconstructing every linked occurrence.

### The data file is shaped differently from the call

`data/corpus-inputs.jsonl` is one JSON object per **recording**:
`{"case_id": ..., "units": [ ... ]}`. Each entry in `units` is exactly the dict
your `detect_events` will be called with. Read the file to develop against the
data; the grader does the iterating for you.

## Data

- `data/corpus-train.jsonl` — {N_CASES} recordings, {N_UNITS} units,
  **{N_EVENTS} annotated events**. One JSON object per recording with `units`
  and `events`. This is your training data: read it, learn the conventions from
  it, measure against it.
- `data/corpus-inputs.jsonl` — the same recordings reduced to exactly the fields
  `detect_events` receives. Useful for checking what your solution can actually
  see, since the annotations above are *not* available at scoring time.
- `data/quran-reference.json` — canonical ayah text, `{ayah_id: text}`.
- `eval21.py` — the official evaluator, the same one that scores the held-back
  split.

An event in the annotated data carries `label`, a `reference` span, and
`hyp_locations` — every place the phenomenon surfaces. A repetition links both
occurrences; a correction links the wrong attempt and the repair. Your solution
returns one location per event, not the whole linkage (see below).

## Scoring

```sh
python3 score.py                 # metrics + per-label F1 over the train split
python3 score.py --json          # the same, as JSON
```

It runs your `solution.py` over the train recordings and scores it with the
evaluator you have. The primary measure is label-aware micro F1: a prediction
counts only when its label matches and both spans overlap the gold event by at
least half. Score as often as you like; it is your data and your evaluator.

Do not access files outside this workspace.

**These {N_CASES} are not the whole dataset.** An equally sized set of
recordings, annotated to the same rubric, is held back and is not in this
workspace. When you stop, your frozen `solution.py` is run against it. That is
the number that decides whether the method works, and it is never used for
development feedback or solution selection. A solution tuned until train stops
improving, with no reason to expect it to transfer, will show the difference
there. Save the final solution before validation begins.

## Rules

Your solution must be a **general algorithm**. Specifically:

1. **No memorized answers.** Do not hardcode ayah ids, transcript fragments or
   case ids to produce a particular output. A lookup keyed on a recording is not
   a method; it is a copy of an answer. You now hold the train annotations, so
   this matters more, not less — and a lookup cannot work anyway: scoring runs
   your solution in a separate sealed container that is given the input fields
   and the Quran reference, and nothing else. `data/corpus-train.jsonl` is not
   mounted there, and neither is this workspace.
2. **Linguistic tables are fine.** The muqatta'at, the opening formulas, a list
   of words the written tradition spells with ت, particle contractions — these
   are facts about Arabic and the Quran, not about this dataset. Encode as many
   as you find useful.
3. **The distinction is whether it generalizes.** A rule that would help on a
   recitation you have never seen is a method. A rule that fires on exactly one
   recording is a memorized answer.
4. **Inference uses the standard library only.** Submit a self-contained
   `solution.py`; it runs without network in a fresh container, with the supplied
   input data and Quran reference. No additional helper files or dependencies are
   mounted for inference — not `eval21.py`, not the annotated train file, not
   anything else you add to this workspace. Model API networking during
   development is separate.
5. Your solution is re-scored on the held-back recordings. A solution that fits
   these {N_CASES} and nothing else will show it there.

An automated audit runs on your final file and reports hardcoded identifiers,
long literal transcript fragments and file access. Its findings are reported
alongside your score.

## Development strategy

Use the rubric across all ten labels. Repetitions and repairs require linking
attempts, not just isolated diff positions. Accepted spelling differences require
context; do not globally fold away initial hamza distinctions.

The label counts in the train split are uneven, and the held-back split is drawn
from the same pool but is not identically distributed — a label with few train
examples may be no rarer there. Weighing effort purely by train frequency is a
way to lose marks on the held-back set.

Read the annotated events before writing rules. The conventions that cost the
most marks — where a span starts and ends, what counts as one event, when a
difference is benign — are visible in the data and are hard to guess from prose.

Older scores from a different reference, split or evaluator are not a
performance target here.
