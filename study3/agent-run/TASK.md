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

It is called **once per unit** — one ayah, or one opening formula. It never sees
a whole recording at once, so everything it decides must be decidable from the
unit in front of it.

### The unit it receives

| key | what it is |
|---|---|
| `case_id` | the recording this unit belongs to |
| `chunk_idx` | position in the recording; `-1` marks an opening-formula unit |
| `n_chunks` | how many ayah units the recording has |
| `ayah_id` | six digits, e.g. `002219`; `None` on a formula unit |
| `transcript`, `transcript_tokens` | what was recited, and the same split on whitespace |
| `reference_text`, `reference_tokens` | the reference with hamza folded to bare alif: أ إ آ all written ا |
| `reference_spelling_text`, `reference_spelling_tokens` | the same reference with hamza written: أيها, الأرض, أحل |

**Use both.** They are aligned token for token — `reference_tokens[i]` and
`reference_spelling_tokens[i]` are the same word — and your spans index the
plain `reference_tokens`. But they disagree on 19% of tokens, and the
disagreement is always hamza, which the plain view has thrown away.

That matters because the two directions mean opposite things:

- the reciter wrote bare alif where the reference writes hamza — notation
  omitted, `spelling_benign`
- the reciter wrote a *different* hamza than the reference — أن against إن,
  say — a different word, `substitution_mistake`

Against the plain reference both look identical, so the spelling view is the
only way to tell them apart. Vowel marks are deliberately not supplied: an
unwritten vowel is not evidence, and hamza above an alif does not by itself
distinguish one vowel from another.

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
grader accepts whichever you choose. Emit one per occurrence and every extra is
a false positive.

Every `repetition_benign`, `substitution_corrected` and `omission_corrected`
event in this data spans more than one place in the transcript. So does a small
number of `substitution_mistake` events, where several failed attempts share
one target.

### The data file is shaped differently from the call

`data/corpus-inputs.jsonl` is one JSON object per **recording**:
`{"case_id": ..., "units": [ ... ]}`. Each entry in `units` is exactly the dict
your `detect_events` will be called with. Read the file to develop against the
data; the grader does the iterating for you.

## Data

- `data/corpus-inputs.jsonl` — {N_CASES} recordings, {N_UNITS} units. Inputs only:
  **no answers are in your workspace.**
- `data/quran-reference.json` — canonical ayah text, `{ayah_id: text}`.

## Scoring

```sh
python3 score.py                 # runs solution.py over every case, prints the score
```

It reports aggregate metrics and per-label F1 over the {N_CASES} recordings in
your workspace. The primary measure is label-aware micro F1: a prediction counts
only when its label matches and both spans overlap the gold event by at least
half.

You will not be told which recordings failed, and nothing in your workspace
names an answer. That is deliberate — see below.

**These {N_CASES} are not the whole dataset.** A separate set of recordings,
annotated to the same rubric, is held back. When you stop, your frozen
`solution.py` is run against it. That is the number that decides whether the
method works, and no amount of fitting to the recordings you can see will move
it. Iterate here; aim there.

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
5. Your solution is re-scored on the held-back recordings. A solution that fits
   these {N_CASES} and nothing else will show it there.

An automated audit runs on your final file and reports hardcoded identifiers,
long literal transcript fragments and file access. Its findings are reported
alongside your score.

## Where the difficulty actually is

The best existing solution scores 0.788 micro F1 on these recordings. It is at
or near ceiling on the opening formulas, strong on plain substitutions and
omissions, and weak in four places:

| label | annotated events here | best F1 so far |
|---|---:|---:|
| `repetition_benign` | 29 | 0.30 |
| `substitution_corrected` | 7 | 0.00 |
| `omission_corrected` | 7 | 0.14 |
| `spelling_benign` | 56 | 0.70 |

One label, `letters_benign`, does not occur in these recordings at all but does
occur in the held-back set. The rubric describes it; you will get no feedback on
it here. The same is true of anything else the rubric covers and these
recordings happen not to contain.

Repetitions and repairs need you to look across the whole unit rather than at a
single diff position: the same words appear twice, or a wrong attempt is
followed by a right one. Accepted spellings need real orthographic knowledge — the
spelling reference view is supplied for exactly this, and no current solution
reads it.
