# Task B evaluator — taxonomy v0.19, evaluator v2.1

The evaluator reads private gold by path. Its source contains no gold records.
The annotation set is fixed. MIN_SPAN=0.50 and anchor slack=1 are frozen; the
secondary cost is reported at both 1:1 and 2:1 rather than frozen at one rate.
No agent experiment has run.

## Evaluation in plain language

1. The agent learns the rubric, annotates a separate development pool and builds
   an algorithm. It can test against practice answers and its own annotations.
2. Freeze the algorithm. An owner-controlled process runs that fixed code on the
   100 held-out recordings. The development agent does not receive these inputs,
   answers, predictions or interim scores during its run.
3. For each event, compare the label and the selected words on both sides.
   Match predictions to gold events one-to-one: one prediction cannot cover
   multiple distinct gold events. A wrong label counts as both an extra wrong
   prediction and a missed correct annotation.
4. Report the primary F1, exact-span F1 and secondary diagnostics. Do not infer
   that every development annotation was correct from final algorithm quality.

`make_inputs.py --gold ...` is an owner-side input exporter for final fixed-code
scoring. Removing answers does not make gold transcripts valid development data.
Its output still reveals selected inputs and membership. This repository,
private exports, gold-review history and the scorer's gold file are not mounted
in the development agent runtime. See [EXPERIMENT.md](EXPERIMENT.md).

## Input and event contract

There are 348 units: 314 reviewed ayah chunks plus 34 opening-text units. The
162 events comprise 115 within-ayah events and 47 opening formulas. Compound
openings carry multiple events in one unit, with `chunk_idx = -1` and an empty
reference. `make_inputs.py` includes nonempty opening text independently of its
answer-side labels. Reviewed ayah IDs, splits and exact references are supplied;
ayah detection is outside this score.

Each prediction row has `review_id`, integer `chunk_idx`, and an `events` list.
Each event has a known combined `label` and `hyp_span` / `ref_span`: two integer,
zero-based half-open endpoints within the supplied original whitespace tokens.
Booleans, floats, negative/out-of-range endpoints and reversed spans are invalid.

| Event | Transcript span | Reference span |
|---|---|---|
| `omission_mistake` | empty anchor | nonempty |
| `insertion_mistake` | nonempty | empty anchor |
| `basmala_benign`, `isti3adha_benign` | nonempty | empty anchor |
| all other event labels | nonempty | nonempty |

`clean` means an empty event list, not an event label. Invalid events count as
false positives and cannot match; invalid gold is rejected. Duplicate or unknown
prediction unit IDs and malformed row envelopes are rejected. Missing units
count as empty predictions. Invalid predictions from a baseline fail the baseline
report generation rather than producing a publishable table silently.

Sweeping MIN_SPAN from 0.05 to 1.00 moves baseline micro F1 by about four points
and leaves strict F1 unchanged, because diff-based baselines emit exact token
spans and rarely depend on the threshold. The value is therefore chosen to be
explainable rather than tuned: at 0.50 the spans overlap more than they do not.
An agent producing looser spans will feel it more than these baselines do.

Anchor slack is 1 because the index of an omission between two tokens is
genuinely ambiguous, not because 1 scored best: sweeping 0 to 10 changes no
baseline score, even though 74 of 162 gold events are anchors.

## Secondary cost

The secondary diagnostic is reported at two exchange rates, `review_cost`
(2:1) and `review_cost_1to1`, because no single rate is defensible on its own
and neither ranks systems; micro F1 does. Ranking is in fact unchanged across
1:1, 2:1, 3:1 and 5:1 on the current baselines. What the rate does control is
whether predicting nothing can win: on gold100 the empty baseline beats naive
diff only below roughly 0.77:1, so any rate at or above 1:1 rules it out.
Rates far above 2:1 push a system toward over-flagging, which in a memorization
app means telling a reciter they erred when they did not.

## MIN_SPAN and matching

For two nonempty spans, overlap is intersection over union (IoU): the number of
selected token positions shared by both spans divided by the positions covered
by either. If gold selects two words and the prediction includes those two plus
one extra, IoU is 2/3. MIN_SPAN=0.50 requires the spans to overlap more than
they do not, on **each side**;
it is not confidence, a proportion of mistakes caught, or a requirement to flag
half the words. One accurate side cannot compensate for a wrong other side.

Empty anchors match only other empty anchors: 1.0 at the same boundary, 0.5 one
boundary away, and zero farther away. An empty anchor never matches a selected
word span. The strict diagnostic requires identical endpoints on both sides.

Eligible pairs are matched by maximum total span similarity for units with at
most seven predictions and seven gold events; larger units use deterministic
greedy one-to-one matching. Similarity is the weaker of the two sides. Pairing
ignores labels, then label-aware credit checks the names. This convention is
shared by the localization diagnostic; its F1 is not localization recall.

This tolerant headline can give event credit for one attempt of a two-attempt
repeat. Exact-span F1 makes the failure to select both attempts visible. Freeze
thresholds using disjoint practice cases, not by optimizing gold rankings.

## Primary and secondary metrics

**Primary: label-aware micro F1 (higher is better).** Precision asks what share
of predicted events have the right label and acceptable spans. Recall asks what
share of gold events were correctly recovered. F1 balances the two:
`2 * TP / (2 * TP + FP + FN)`. It penalizes missed annotations and invented ones,
including benign and corrected events. `event_error = 1 - micro_f1` is the
lower-is-better form of the same metric for optimization on development data.

Also report exact-span `strict_micro_f1`, per-label F1, macro F1 across labels
present in gold, localization precision/recall/F1 without label agreement, and
mean weakest-side IoU over localized pairs (`span_iou`). Macro F1 is a coverage
check with high variance on rare labels; it is not the ranking objective.

**Secondary: application review cost (lower is better).**

```
review_cost = (2 * missed_mistakes + false_flags) / scored_units * 100
```

One missed mistake costs two points; an unnecessary mistake flag costs one.
These are raw counts with a common denominator, so the ratio is implemented
literally. It is an explicit heuristic, not a measured user-cost ratio. Wrong
mistake subtypes are penalized by primary F1 but not this binary mistake-cost
view. `clean_flag_rate` reports mistake flags on no-event units.

## What was fixed

v1.0 omitted benign-label quality from its headline and averaged the two spans.
v2.0 introduced label-aware F1, required both sides, and included opening formulas.
v2.1 closes the zero-word substitution loophole, validates event shapes and
coordinates, rejects duplicate/unknown unit rows, adds exact-span F1 and explicit
localization recall, and corrects the production-component adapter.

The adapter now follows the cleaner's removed-token notes to retain original
word identities, uses alignment's actual token indices and partial-reference
offset, locates the reference phrase, and spans original plus repeated/repaired
attempts. It preserves the production partial-start scoring policy. It retains
an explicit approximation: a stumble is paired with the next equally many
surviving words if they match the reference; an unlocalizable removed fragment
is treated as extra text. The application itself does not implement this rubric.
These adapter choices are disclosed; results do not establish a causal effect
of cleaning or the performance of the full deployed application.

All v1.0 and v2.0 baseline numbers are superseded by [BASELINES-v19.md](BASELINES-v19.md).

## Checks

```sh
FMR_REPO=<application checkout> python3 -m unittest discover -s study3/tests -v
python3 study3/eval19.py --gold <private gold.jsonl> --self-test
FMR_REPO=<application checkout> python3 study3/tools/run_baselines19.py --gold <private gold.jsonl>
```

The gold-in oracle has F1=1; empty predictions have F1=0. Synthetic regressions
cover invalid coordinates, wrong labels, omission anchors, partial repetition
spans, duplicate row IDs, raw cost ratios, and production token mapping. No gold
examples are embedded in the tests. Baseline temporary inputs/predictions are
removed on exit; only aggregate reports are written to this repository.
