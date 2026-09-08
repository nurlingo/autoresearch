# Task B baselines under taxonomy v0.19

Scored with `study3/eval19.py` (evaluator v1.0) against the private gold set: 314 chunks, 233 clean, 89 mistake events, 26 benign or corrected events. Lower is better. Baselines read stripped inputs only; no answers are in this repository.

| baseline | score | miss | false alarm | benign | clean | label err | span IoU |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 predict nothing | 2.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B1 naive diff | 0.988 | 0.045 | 0.009 | 0.885 | 0.004 | 0.241 | 0.921 |
| B2 incumbent application pipeline | 0.768 | 0.079 | 0.068 | 0.538 | 0.004 | 0.184 | 0.883 |

`score = 2*miss + false_alarm + benign + clean`. `label_error` and `span_iou` describe matched pairs and are reported, not summed. Predicting nothing scores 2.000; returning the gold annotation scores 0.000.

Localization recall per gold label, strongest baseline:

| label | matched / gold |
|---|---:|
| `insertion_mistake` | 1/1 |
| `letters_benign` | 4/4 |
| `omission_corrected` | 1/1 |
| `omission_mistake` | 22/26 |
| `repetition_benign` | 1/5 |
| `spelling_benign` | 8/12 |
| `substitution_corrected` | 2/4 |
| `substitution_mistake` | 59/62 |
