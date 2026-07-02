---
name: recitation-autoresearch-dataset-quirks
description: Key non-obvious facts for the Stage-1 recitation autoresearch loop (ar-runs/260702-claude-r2)
metadata: 
  node_type: memory
  type: project
  originSessionId: 92dd00be-cb8f-4eec-8200-355fe33a49ee
---

Autoresearch task: map a Quran recitation transcript → ayah-id set + per-ayah split. Edit only `solution.py`; metric is `make eval` `research_score` (lower better). Baseline abstain-all = 2.0; practical floor ~0.007 (two known train label quirks). My run reached **0.098** with a surah-sequence semi-global DP aligner.

Non-obvious things that cost effort to discover:
- **`data/quran_ref.json` has irregular ids.** Long ayahs are stored as phrase pieces with 9-digit ids (e.g. `002255001..006` instead of `002255`), and there are pseudo-surahs keyed `999xxx` duplicating popular passages. Gold uses only standard 6-digit ids, so: skip non-3-char surah keys and collapse every entry id to `id[:6]`. This one fix took the score 0.68 → 0.11.
- **Determinism:** anchoring over a Python `set` makes the score vary with `PYTHONHASHSEED`. Sort candidates. Always sanity-check with `for s in 0 1 2; do PYTHONHASHSEED=$s python3 eval.py; done`.
- **Preamble:** transcripts often start with isti'adha ("أعوذ بالله من الشيطان الرجيم") and basmala; gold split drops them, EXCEPT the basmala of Al-Fatiha (which is ayah 001001).
- **eval canon regex** `[ؐ-ًؚ-ٰٟۖ-ۭ]` must be written with `\u` escapes — pasting the literal combining marks bidi-scrambles the range and eats base letters.
- Hard remaining cases (don't chase, low value / overfit risk): repeated ayahs (monotonic aligner can't repeat), spelled-out muqattaat ("الف لام ميم صاد"→المص), ayah-gap jumps, mis-transcriptions, and the ~2 label quirks.
