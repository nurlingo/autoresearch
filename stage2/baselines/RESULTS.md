# Stage 2 baselines

Scored with `eval.py --include-machine` (lower is better). Pilot labels: LLM-proposed, human-pending (`--include-machine`).

## train — 47 labeled chunks (clean 41, gold mistakes 6, gold benign 2)

| baseline | study3_score | miss_error | false_alarm | benign_error | clean_error | type_error |
|---|---:|---:|---:|---:|---:|---:|
| B0 empty stub | 2.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B1 naive diff | 1.358 | 0.000 | 0.333 | 1.000 | 0.024 | 0.167 |
| B2 incumbent production stack | 0.167 | 0.000 | 0.143 | 0.000 | 0.024 | 0.167 |

## test — 52 labeled chunks (clean 45, gold mistakes 2, gold benign 1)

| baseline | study3_score | miss_error | false_alarm | benign_error | clean_error | type_error |
|---|---:|---:|---:|---:|---:|---:|
| B0 empty stub | 2.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B1 naive diff | 1.111 | 0.000 | 0.111 | 1.000 | 0.000 | 0.000 |
| B2 incumbent production stack | 1.111 | 0.000 | 0.111 | 1.000 | 0.000 | 0.000 |

