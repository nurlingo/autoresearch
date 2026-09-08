# MusIML @ NeurIPS 2026 — Track 3 competition proposal

Updated **2026-09-08** after the human review reached **40/100 unique
recordings (71 chunks)**. The proposal distinguishes public Task A, the legacy
machine-labeled Task B pilot, and the new annotation-assisted development
protocol. New Task B scores, a frozen metric, and a new unreleased final test
set are not claimed.

`main.tex` uses the NeurIPS 2026 `dblblindworkshop` style; maximum two pages.
Build from this directory:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdfinfo main.pdf
```

`main.pdf` is committed for colleague review. The source remains anonymous:
no authors, application names, repository links, local paths, or selected gold
recording identifiers. The earlier AIST study is cited without authors.

## Evidence and supporting documents

- [Current methodology](../../METHODOLOGY-STUDY3.md): design, isolation, and
  decisions that still need freezing.
- [Annotation findings](../../docs/STUDY3-ANNOTATION.md): approved counts,
  combined labels, span rules, and synthetic examples.
- [Label examples](../../docs/STUDY3-LABEL-EXAMPLES.json): illustrative JSON;
  no gold examples or answers.
- [Release notes](../../release/README.md): actual artifact counts, export
  mismatch, exposure limitations, and historical schema.
- [Legacy baseline results](../../stage2/baselines/RESULTS.md): machine-pilot
  results only. New-rubric baseline evaluation remains future work.

All 40 reviewed inputs match public Task A transcripts; five overlap the old
machine-labeled pilot. New answers and selection membership are withheld.
A private label set is not the same as unpublished inputs. The proposed final
competition needs a separate previously unreleased collection before it can
claim unseen-input ranking.

Gold review access is separate from this repository: the owner has a local
reviewer bundle containing the 40 approved data points, an HTML view, and
checksums. Share that bundle with human reviewers through a private channel;
do not mount it in an experimental agent environment.
