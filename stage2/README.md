# Stage 2 — legacy within-ayah pilot harness

**Current Study 3 status (2026-09-08): 100/100 recordings approved, 314 chunks; taxonomy v0.19.**
The new rubric uses one combined label and different event conventions. This
directory retains the old type/verdict schema, machine labels, scorecard,
and baselines for reproducibility. The commands below run that legacy pilot,
not the new annotation-and-development protocol. No new-protocol agent runs
have started. See [annotation findings](../docs/STUDY3-ANNOTATION.md).

The second autoresearch harness of this repo: given ONE gold ayah chunk (from the
Stage-1 split) and its reference text, return the recitation *events* in it,
each with a verdict (`benign` / `corrected` / `mistake` / `uncertain`).
Design: `../METHODOLOGY-STUDY3.md`. Data contract: `SCHEMA.md`.

```
SCHEMA.md            # legacy proposed schema + old matching rule
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

Legacy release audit (2026-09-08): `release/taskB` contains 1,268 records,
99 machine-labeled chunks from 20 recordings and 1,169 unlabelled records.
Task A has 1,267 chunks; the legacy Task B export adds a chunk to one training
recording. See `../release/README.md`. Preserve these artifacts as historical;
reconcile the export in a separately versioned dataset before new scoring.
A naive-diff match is a review hint, not a substitute for checking complete
transcripts, splits, openings, and repeated ayah context.
