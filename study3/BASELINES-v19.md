# Task B baselines under taxonomy v0.19

Scored with `study3/eval19.py` (evaluator v2.0) against the private gold set: 348 scored units (233 with no event), 162 gold events including opening formulas. Baselines read stripped inputs only; no answers are in this repository.

| baseline | micro F1 | macro F1 | P | R | loc F1 | span IoU | review cost | clean flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 predict nothing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 51.150 | 0.000 |
| B1 naive diff | 0.531 | 0.179 | 0.566 | 0.500 | 0.931 | 0.893 | 18.100 | 0.004 |
| B2 incumbent application pipeline | 0.447 | 0.170 | 0.464 | 0.432 | 0.786 | 0.883 | 26.720 | 0.004 |

Primary measure is label-aware event F1: a paired prediction counts only when its label also matches. `loc F1` runs the same matching with labels ignored, so the gap between the two columns is naming rather than finding. `review cost` is (2 x missed mistakes + false flags) per 100 chunks. Predicting nothing gives micro F1 0.000; the gold annotation gives 1.000.

Per-label F1, strongest baseline (B1 naive diff):

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
