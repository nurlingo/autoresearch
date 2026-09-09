# Task B baselines under taxonomy v0.19

Scored with `study3/eval19.py` (evaluator v2.1) against the private gold set: 348 scored units (233 with no event), 162 gold events including opening formulas. Baselines read stripped inputs only; no answers are in this repository.

| baseline | micro F1 | strict F1 | macro F1 | P | R | loc F1 | loc recall | span IoU | review cost | clean flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 predict nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 51.150 | 0.000 |
| B1 naive diff | 0.531 | 0.505 | 0.179 | 0.566 | 0.500 | 0.839 | 0.790 | 0.936 | 22.410 | 0.004 |
| B2 adapted production components | 0.518 | 0.505 | 0.284 | 0.536 | 0.500 | 0.799 | 0.772 | 0.931 | 26.720 | 0.004 |

Primary measure is label-aware event F1: a paired prediction counts only when its label also matches. `loc F1` runs the same matching with labels ignored, so the gap between the two columns is naming rather than finding. `review cost` is (2 x missed mistakes + false flags) per 100 scored units. Predicting nothing gives micro F1 0.000; the gold annotation gives 1.000.

Per-label F1 — B1 naive diff:

| label | gold | predicted | P | R | F1 |
|---|---:|---:|---:|---:|---:|
| `basmala_benign` | 18 | 0 | 0.00 | 0.00 | 0.00 |
| `insertion_mistake` | 1 | 46 | 0.00 | 0.00 | 0.00 |
| `isti3adha_benign` | 29 | 0 | 0.00 | 0.00 | 0.00 |
| `letters_benign` | 4 | 0 | 0.00 | 0.00 | 0.00 |
| `omission_corrected` | 1 | 0 | 0.00 | 0.00 | 0.00 |
| `omission_mistake` | 26 | 23 | 1.00 | 0.88 | 0.94 |
| `repetition_benign` | 5 | 0 | 0.00 | 0.00 | 0.00 |
| `spelling_benign` | 12 | 0 | 0.00 | 0.00 | 0.00 |
| `substitution_corrected` | 4 | 0 | 0.00 | 0.00 | 0.00 |
| `substitution_mistake` | 62 | 74 | 0.78 | 0.94 | 0.85 |

Per-label F1 — B2 adapted production components:

| label | gold | predicted | P | R | F1 |
|---|---:|---:|---:|---:|---:|
| `basmala_benign` | 18 | 0 | 0.00 | 0.00 | 0.00 |
| `insertion_mistake` | 1 | 45 | 0.00 | 0.00 | 0.00 |
| `isti3adha_benign` | 29 | 0 | 0.00 | 0.00 | 0.00 |
| `letters_benign` | 4 | 0 | 0.00 | 0.00 | 0.00 |
| `omission_corrected` | 1 | 0 | 0.00 | 0.00 | 0.00 |
| `omission_mistake` | 26 | 25 | 0.84 | 0.81 | 0.82 |
| `repetition_benign` | 5 | 5 | 1.00 | 1.00 | 1.00 |
| `spelling_benign` | 12 | 0 | 0.00 | 0.00 | 0.00 |
| `substitution_corrected` | 4 | 6 | 0.17 | 0.25 | 0.20 |
| `substitution_mistake` | 62 | 70 | 0.77 | 0.87 | 0.82 |

All baseline calls completed without crashes or invalid predictions.

B2 adapts production cleaner/alignment components to this event schema; it is not the full deployed application. See EVALUATOR.md for mapping assumptions. MIN_SPAN=0.30, anchor slack=1 and the secondary 2:1 cost remain provisional. Strict F1 requires exact endpoints and labels.
