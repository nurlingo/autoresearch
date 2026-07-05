# Production Stage-1 solution (detect + split)

`solution.py` is the winner of the autoresearch study — Study 2 run **codex-r3**,
selected on held-out evidence (see RESULTS.md).

## Why this one
- Best held-out split accuracy of all 12 runs (97.8%); tied-best overall test
  score (0.0793 vs claude-r1's 0.0796); clearly best on the full v1.1 dataset
  (0.0336 vs 0.0548).
- Compositions tested and rejected: union-abstention hurts (false abstains,
  test 0.098); claude-on-disagreement is within noise (0.0790) and doubles the
  maintenance surface. One file wins on the simplicity criterion.
- Study 1 artifacts were ruled out on principle: optimized on all 258 rows with
  no held-out measurement (Study-1 codex additionally contains memorized
  answers). Study 2 artifacts are the only ones with unbiased evidence.

## Known limitations
- Abstention is validated on few non-Quran examples (2 test + 4 total); treat
  the abstain path as under-tested and keep upstream guards in the app.
- Harakat-blind and transcript-only by design; within-ayah mistake detection is
  Stage 2 (not built yet).
- Repetitions are handled; the detection id-set convention matches eval.py.

## Verify
    cd production && python3 - <<'PY'
    from solution import Solution
    s = Solution()
    print(s.process("والتين والزيتون وطور سينين"))
    PY

Next integration step: port into follow_my_reading worker (replace
AyahDetector + segmenter path), mapping {"ayahs":[{id,text}]} onto the
pipeline's detected_range + segments.
