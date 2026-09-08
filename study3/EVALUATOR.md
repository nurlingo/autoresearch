# Task B evaluator, taxonomy v0.19

`eval19.py` is the executable scorecard for the combined-label rubric. It holds
no gold data: it reads a private gold file by path, so the reviewer bundle stays
outside this repository and outside any agent runtime.

```sh
python3 study3/eval19.py --gold <private gold.jsonl> --self-test
python3 study3/eval19.py --gold <private gold.jsonl> --pred predictions.jsonl
FMR_REPO=<application checkout> python3 study3/tools/run_baselines19.py --gold <gold.jsonl>
```

## Contract

A system receives, per chunk, `transcript_tokens`, `reference_tokens`,
`ayah_id`, `chunk_idx` and `n_chunks`, and returns events of the form
`{"label", "hyp_span": [i, j], "ref_span": [a, b]}` with half-open spans into
those token arrays. Reviewed ayah splits, IDs and references are supplied, so
detection is not scored. `tools/make_inputs.py` produces exactly this input view
from a gold file, dropping every annotation field, which is how baselines are
run without ever seeing an answer.

## Matching

Within a chunk, predicted and gold events are matched **one-to-one** by maximum
total similarity, so a single broad prediction can be credited with at most one
gold event and the remaining gold events count as misses. Similarity is the mean
of hypothesis-span and reference-span similarity; pairs below 0.30 are never
matched. Span similarity treats an empty span as an anchor: two anchors match
within one token, an anchor against a real span scores 0.5 when it falls inside
that span widened by one token, and two real spans use intersection over union.
Corrected and repetition events carry spans over all their attempts, so a
prediction covering only one attempt loses span credit but can still match.

## Score

```
miss        = gold mistake events that no mistake prediction matched / gold mistake events
false_alarm = predicted mistake events matching no gold event / predicted mistake events
benign      = gold benign or corrected events matched by a mistake prediction
              / gold benign and corrected events
clean       = reviewed no-event chunks carrying any predicted mistake / reviewed no-event chunks

study3_v19_score = 2*miss + false_alarm + benign + clean      (lower is better)
```

`miss` is doubled because a missed mistake fails the learner while an extra flag
costs a moment of review. `label_error` (matched pairs whose label differs),
`span_iou` (localization quality of matched pairs) and per-label localization
recall are reported next to the scalar and are not summed into it.

Opening-formula annotations are recorded in the gold set at record level and are
outside evaluator v1.0, which scores chunk events only.

## Oracle tests

`--self-test` checks four properties against the real gold set:

| check | expected | observed |
|---|---|---|
| gold predictions in | 0.0, span IoU 1.0 | 0.0000, 1.000 |
| empty predictions in | 2.0 | 2.0000 |
| one chunk-wide flag per chunk | > 1.0, multi-event chunks keep unmatched gold mistakes | 3.3874, 27 of 37 still missed |
| every gold event relabelled as a mistake | benign 1.0, miss 0.0 | 1.000, 0.000 |

## Status

Evaluator v1.0, frozen before any agent run; no agent has been evaluated
against this gold set. Baseline results are in `BASELINES-v19.md`. Still to
freeze for the measured experiment: model and tool budgets, comparison
conditions, permitted feedback, and the development-pool partition.
