# Task B evaluator, taxonomy v0.19 — v2.0

`eval19.py` is the executable scorecard for the combined-label rubric. It holds
no gold data: it reads a private gold file by path, so the reviewer bundle stays
outside this repository and outside any agent runtime.

```sh
python3 study3/eval19.py --gold <private gold.jsonl> --self-test
python3 study3/eval19.py --gold <private gold.jsonl> --pred predictions.jsonl
FMR_REPO=<application checkout> python3 study3/tools/run_baselines19.py --gold <gold.jsonl>
```

## What v1.0 got wrong

v1.0 scored only mistake-flagging. Three faults were therefore free, and all
three together still scored a perfect 0:

| fault | v1.0 | v2.0 |
|---|---:|---:|
| every mistake given the wrong mistake label | 0.000 | micro F1 0.221 |
| every benign and corrected annotation omitted | 0.000 | micro F1 0.791 |
| a fabricated benign event on every clean chunk | 0.000 | micro F1 0.539 |
| all three at once | 0.000 | — |
| exact reference span, hypothesis span misplaced | 0.000 | micro F1 0.136 |

The last one came from averaging the two span similarities, which let an exact
reference span carry a match on its own. v1.0 also described its scalar as
pricing a missed mistake at twice a false flag, which its four differently
normalized terms did not implement. All of this is fixed below; the numbers in
the right column are from `--self-test` against the real gold set.

## Contract

Per unit the system receives `transcript_tokens`, `reference_tokens`,
`ayah_id`, `chunk_idx`, `n_chunks`, and returns events of the form
`{"label", "hyp_span": [i, j], "ref_span": [a, b]}` with half-open spans into
those arrays. Reviewed ayah splits, IDs and references are supplied, so ayah
detection is not scored.

**Opening formulas are scored.** Each record's isti'adhah and basmala are
presented as a unit with `chunk_idx = -1`, the formula text as the transcript
and an empty reference. A compound opening becomes two gold events over the
same token array. Judging that a basmala is benign rather than an insertion is
part of the task, and it is where a plain diff fails hardest. The gold set has
348 scored units and 162 gold events: 115 within-ayah plus 47 formulas.

`tools/make_inputs.py` produces exactly this input view from a gold file,
formulas included, dropping every annotation field. That is how baselines run
without ever seeing an answer.

## Matching

Predictions and gold events are paired one-to-one within a unit by maximum
total similarity, so one broad prediction is credited with at most one gold
event. A pair is eligible only when **both** spans overlap:

```
sim(pred, gold) = min(span_sim(hyp), span_sim(ref))  >=  MIN_SPAN = 0.30
```

`span_sim` treats an empty span as an anchor: two anchors score 1.0 when they
coincide and 0.5 within one token; an anchor against a real span scores 0.5
when it falls inside that span widened by one token; two real spans use
intersection over union. Corrected and repetition events carry spans over all
their attempts, so a prediction covering one attempt loses IoU but can still
match. Pairing ignores labels, which is what lets localization be reported
apart from naming.

## Scores

**Primary — label-aware event F1.** A paired prediction is a true positive only
when its label also matches; a pair with the wrong label counts once as a false
positive and once as a false negative, as does anything unpaired.

- `micro_f1` over all events, the headline, with `precision` and `recall`
- `macro_f1`, the mean of per-label F1, so the labels with one or four
  instances cannot be ignored (high variance by construction — read it as a
  coverage check, not a stable estimate)
- `event_error = 1 - micro_f1`, the lower-is-better scalar for a loop
- `loc_f1`, the same matching with labels ignored: the gap to `micro_f1` is
  naming rather than finding
- `span_iou` over matched pairs

**Secondary — application cost,** in raw event counts so the exchange rate is
the one implemented:

```
review_cost = (2 * missed_mistakes + false_flags) / units * 100
```

One missed mistake is priced at two unnecessary flags; both terms are event
counts in the same unit. `clean_flag_rate` reports the share of no-event units
carrying any predicted mistake.

Reference points: predicting nothing gives micro F1 0.000 and `event_error`
1.000; the gold annotation gives 1.000 and 0.000.

## Oracle tests

`--self-test` runs seven checks against the real gold set: the two endpoints,
the four v1.0 regressions in the table above, and one chunk-wide flag per unit,
which reaches micro F1 0.028 and leaves 81 gold events in multi-event units
unrecovered. All pass.

## Status

Evaluator v2.0. No agent has been evaluated against this gold set. Baseline
results are in `BASELINES-v19.md`. Still to freeze for the measured experiment:
model and tool budgets, comparison conditions, permitted feedback, and the
development-pool partition.

Open for review: `MIN_SPAN = 0.30` and `ANCHOR_SLACK = 1` are proposed, not
agreed. So is the 2:1 cost ratio, which now only affects the secondary metric.
