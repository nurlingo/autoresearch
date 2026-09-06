# Stage 2 — within-ayah mistake events

The second autoresearch harness of this repo: given ONE gold ayah chunk (from the
Stage-1 split) and its reference text, return the recitation *events* in it,
each with a verdict (`benign` / `corrected` / `mistake` / `uncertain`).
Design: `../METHODOLOGY-STUDY3.md`. Data contract: `SCHEMA.md`.

```
SCHEMA.md            # frozen event schema (v1-proposed) + matching rule
PROGRAM.md           # the agent's loop instructions (Stage-2 variant)
eval.py              # FIXED scorecard -> study3_score (lower is better)
solution.py          # EDITABLE — start from the empty stub
data/train.jsonl     # one line per gold chunk; events=null where not yet labeled
data/test.jsonl      # held-out (experimenters only)
baselines/           # B1 naive diff, B2 incumbent production stack, RESULTS.md
tools/export.py      # rebuild data/ from the root split + Review-tab labels
tools/run_baselines.py
tools/log_experiment.py
```

```bash
make eval                     # score solution.py (pilot mode: --include-machine)
make test                     # held-out
make baselines                # -> baselines/RESULTS.md   (B2 needs FMR_REPO=<follow_my_reading checkout>)
make data                     # regenerate data/ (needs ../data/{train,test}.csv + ../data/bot_events.jsonl)
```

Label status (2026-09-06): 1,267 chunks over 254 recordings; 98 chunks
(20 recordings) carry pilot labels proposed by an LLM and pending human
review; the rest are `unlabeled`. The 21% of chunks that a naive diff flags
(269) are the ones that need real labeling judgment; the remaining 79% match
the reference exactly after canonicalization and can be confirmed clean in bulk.
