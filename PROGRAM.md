# Recitation Autoresearch — Stage 1 (detection + split)

A Karpathy-style autoresearch loop. You are optimizing a transcript-only algorithm
that maps a Quran recitation transcript to the ayahs recited and the split of the
transcript by ayah. Mistake detection is **Stage 2** and is not part of this loop.

This program is **agent-agnostic**: the same loop is run by Claude Code, Codex, or
a human. The only thing that varies between runs is the agent.

## The loop

1. Read `eval.py` (the metric) and `solution.py` (the algorithm — currently a
   stub that abstains on everything).
2. Run the baseline:
   ```bash
   make eval
   ```
   Record `research_score` (lower is better). The empty baseline is ~2.0.
3. Form ONE hypothesis. Edit **only** `solution.py` (and any helper files you add
   next to it). Implement `Solution.process(transcript)` per the contract in its
   docstring.
4. Re-run `make eval`. If `research_score` dropped, keep the change and append a
   row to `results.tsv`. If not, revert.
5. Commit each kept improvement with the score in the message. Repeat.

Keep diffs small enough that one `results.tsv` line explains them.

## Fixed surface — do NOT edit

- `eval.py` — the scorecard
- `data/bot_review.csv` — the ground-truth dataset (transcripts + reviewed splits)
- `data/quran_ref.json` — the Quran reference (id, ar, clean per ayah)
- `PROGRAM.md` — this file

These are the equivalent of Karpathy autoresearch's `prepare.py`: fixed data,
fixed metric, fixed task. Improving the score by changing them is cheating.

## Editable surface

- `solution.py` — and any modules you import from it.

You may build whatever you want from scratch: normalization, n-gram detection,
alignment-based splitting, etc. There is no required approach.

## The metric (what `research_score` measures)

```
detection_error = 1 - (exact ayah-id-set matches / range rows)
split_error     = 1 - mean(word-assignment accuracy / range rows with a gold split)
abstain_error   = 1 - (correct abstentions / non-Quran rows)
research_score  = detection_error + split_error + abstain_error      # lower is better
```

- **Detection** compares the *set* of ayah ids you return to the gold range.
  Repeated ayahs (a reciter repeating a surah) do not hurt detection — that is a
  split concern.
- **Split** is word-assignment accuracy: of all gold transcript words, the
  fraction you placed in the correct ayah bucket. Comparison is done on a
  canonicalized token form (harakat-folded) so spelling noise is not penalized.
- **Abstain**: on non-Quran rows you must return `{"abstain": True}`.

Reference floor: feeding the gold split straight back scores ~0.03 (two dataset
rows have inconsistent labels). Treat ~0.03 as the practical best, not 0.

## Logging

`results.tsv` columns: `commit  research_score  description`. One line per kept
change. `make baseline DESC="..."` runs eval and appends a line automatically.
