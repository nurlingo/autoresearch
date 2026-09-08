# MusIML @ NeurIPS 2026 — Track 3, competition proposal (Task A)

Detect and split: which ayahs a transcript contains and where each begins.
NeurIPS 2026 `dblblindworkshop` style, **2 pages**, the Track 3 limit.

```sh
pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
```

Track 3 requires a ready dataset, a sample for review, defined metrics and
evaluated baselines. All four are satisfied by material that is already public:

| requirement | where |
|---|---|
| ready dataset | `release/taskA/` — 258 recordings, frozen v1.1, public |
| review sample | `release/sample/` — 26 recordings, ten percent, public |
| defined metric | `eval.py`, `research_score`, oracle floor exactly 0 |
| evaluated baselines | empty 2.000, incumbent 0.760, best agent run 0.079 held out |

Nothing here depends on the private Task B annotation. The companion Track 1
submission in `../musiml/` covers that, and the two papers cite each other
without naming authors.

Anonymous: no author, application, organization or repository names, and the
earlier AIST study is cited by title only.
