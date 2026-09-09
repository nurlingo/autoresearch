# MusIML @ NeurIPS 2026 — Track 1, annotation and evaluation (Task B)

Within-ayah recitation events: what counts as a mistake, can existing systems
tell, and what a coding agent gets wrong when handed the rubric. NeurIPS 2026
`dblblindworkshop` style, submitted as an **8-page long paper**; the body
currently runs about 6 pages with references after it. Track 1 accepts 4 pages
(short) or 8 (long). The 2025 NeurIPS and 2026 ICML calls both state the limit
as "including all figures and tables but excluding references"; the 2026 NeurIPS
page gives lengths only and is silent on references.

```sh
pdflatex -interaction=nonstopmode main.tex && bibtex main \
  && pdflatex -interaction=nonstopmode main.tex \
  && pdflatex -interaction=nonstopmode main.tex
```

Citations live in `references.bib` (a local subset of `../references.bib` plus the
annotation and pronunciation-assessment entries this paper adds).

Every number traces to a file in this repository:

- taxonomy and adjudicated rules — [`../../docs/STUDY3-ANNOTATION.md`](../../docs/STUDY3-ANNOTATION.md)
- metric, matching and oracle tests — [`../../study3/EVALUATOR.md`](../../study3/EVALUATOR.md)
- baseline table and per-label F1 — [`../../study3/BASELINES-v19.md`](../../study3/BASELINES-v19.md)
- methodology and what remains unfrozen — [`../../METHODOLOGY-STUDY3.md`](../../METHODOLOGY-STUDY3.md)

The gold annotation itself is not in this repository. It lives in a private
reviewer bundle; `study3/eval19.py` reads it by path and never contains it. The
current draft does not release a gold sample. The private gold input exporter is
only for scoring frozen code; it must not supply the development agent's pool.

Evaluator v2.1 validates span shapes and reports exact-span F1 alongside the
provisional tolerant primary score. Baselines were rerun after correcting the
production-component adapter; the former claim that it cannot recognize
repetition was withdrawn. See the evaluator documentation for remaining choices.

Anonymous: no author, application, organization or repository names.
