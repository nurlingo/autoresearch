# MusIML Track 3 — event annotation competition

The historical directory name is retained, but the proposal now concerns within-ayah
event annotation, not Task A detection/splitting. Only final solutions are scored;
entrants choose their method and whether to annotate or use agents.

Data: `study3/release/` (127 train cases, 888 units). Review sample: 23 train cases,
394 units. Private test: gold100, 348 units, 162 events. No gold data is committed.
Evaluator: `study3/eval19.py` v2.1; baselines: `study3/BASELINES-v19.md`.

See `study3/SUBMISSION-TODO.md` for remaining approvals, sample interpretation,
licensing, execution rules and reviewer access. Do not claim everything is submitted
or that the private-input execution service is already implemented.

Compile with `pdflatex -interaction=nonstopmode main.tex` twice in this directory.
