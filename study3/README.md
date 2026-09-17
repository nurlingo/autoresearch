# Study 3 preparation

**Current status (2026-09-16):** [200 approved cases: 100 train / 100 gold](CURRENT-STATE.md), frozen as `granular-100x100-v1.0`. Use [the current experiment protocol](EXPERIMENT.md) for train-only development and final hidden-gold validation. The gold100/127-train counts, single-span examples and pilot numbers below describe the historical frozen release, not the working corpus.

Start with the [current-state index](CURRENT-STATE.md), [experiment protocol](EXPERIMENT.md), [runbook](agent-run/RUNBOOK.md) and [evaluator audit](EVALUATOR.md). The working evaluator is v2.3 (`eval21.py`); the historical evaluator is v2.1 (`eval19.py`). Current helpers provide train-only preparation, isolated inference, a train feedback service and a restricted development-container launcher.

The private working corpus has 200 distinct recordings and 469 granular events, with natural-language summaries and linked locations for attempts and repeats. All 200 cases are now owner-approved. See [the representation](annotation-review/README.md) and [train review status](TRAIN-ANNOTATION.md).

The agent develops on answer-free train inputs, using the [rubric](ANNOTATION-GUIDE.md), faithful `quran-reference.json` and refreshed constructed examples. Any feedback is train-only. Freeze the solution before isolated final test inference and private scoring. Save any machine annotations produced; final algorithm quality does not certify them independently.

The entire authoring repository is not an agent bundle. Keep test inputs and answers, case membership, source exports, review notes and history outside the development environment. The grader runs submitted code in a separate input-only Docker container and scores predictions afterward; the development container mounts only its prepared train workspace.

## Historical experimental artifacts

The historical training release has 127 cases / 888 units, with a train-only review sample of 23 cases / 381 units. Its corresponding gold100 has 100 cases / 348 units / 162 events. Eight informal pilots in the paper use that older contract; they are not scores on the new 100/100 split. The [221-to-127 audit](TRAIN-ANNOTATION.md) remains historical selection evidence.

The twenty [constructed teaching cases](calibration/teaching-review.html) were approved for the earlier contract. A [current adaptation](calibration/teaching-current.md) updates references and granular grouping and is explicitly assistant-validated. They are constructed examples, not recorded recitations.

The [submission checklist](SUBMISSION-TODO.md) tracks historical preparation separately from current work. Manuscript changes remain for discussion in [the audit note](../docs/STUDY3-PAPER-DISCUSSION.md).

## Corrections to frozen training release v1.0

The historical `release/` bundle is not present in this checkout. Its archived
`SHA256SUMS` are authoritative; the following notes describe the frozen bundle,
so these two
corrections are recorded here rather than by editing the bundle. Neither affects
the data; a repair would require a new version and fresh hashes, not a silent
file change.

- `release/README.md` says the constructed teaching cases are "awaiting owner
  approval". They were approved after the bundle was frozen: all twenty are
  approved, renumbered t01-t20.
- `release/manifest.json` records `reference_source_sha256`
  `2cf019e8...` for `quran.json`. That is the sha256 of the raw source file used
  during preparation (`tools/build_train_release.py` hashes the `--quran` bytes),
  and it does not match any committed revision of the application's
  `backend/quran.json`, whose bytes at that audit hashed to `cda42941...`. The reference
  text itself is unaffected: deriving `{id: titles.clean}` from the application
  file reproduces `release/quran-reference.json` on all 6231 entries with no key
  or text differences. The discrepancy is confined to parts of the source file
  the reference does not use.

## Historical release reference provenance and redistribution

Established 2026-09-09 against the application's `backend/quran.json` and Tanzil's
published `simple-clean` text.

The following counts and transformations concern `release/quran-reference.json`,
not the current 6,236-entry hamza-preserving `study3/quran-reference.json`.

**Chain.** `release/quran-reference.json` is `{ayah_id: titles.clean}` derived from
the application's `backend/quran.json`; deriving it reproduces the released file on
all 6231 entries with no key or text differences.

**Upstream.** The application file carries quran.com / Quranic Universal Library
word-by-word data and audio from `verses.quran.com` and QuranicAudio (everyayah);
the reciter keys `ar.husary` and `ar.abdulbasitmurattal` are Al-Quran Cloud edition
identifiers. The Arabic itself is **Tanzil simple-clean**. Comparing the 6231
released entries against Tanzil `simple-clean` (`txt-2`):

| Relationship to Tanzil simple-clean | Entries |
|---|---:|
| Reproduced by removing the surah-initial basmala prefix and folding hamza-bearing alif to bare alif | 6225 |
| Residual, all orthographic: `بعد ما`→`بعدما` (3), final alif maqsura→alif (3) | 6 |

All 6231 of our ayah ids exist in Tanzil. Five Tanzil ids do **not** appear in our
reference — `002030`, `002185`, `002255`, `002285`, `002286` — because the source
file stores those long/popular ayahs as phrase pieces under 9-digit ids, which the
release builder's `len(id)==6` filter drops. Neither test nor train references any
of the five, and every ayah id used by either split resolves against the released
reference, so this is a coverage note rather than a defect. **The released
reference is not a complete Quran text** and should not be described as one.

**Redistribution.** Tanzil's terms require that the source be clearly indicated
with a link to tanzil.net, state that changing the text is not allowed, and
require the copyright notice to be reproduced in derived files. What we
redistribute is a *normalized derivative* — basmala prefixes removed, hamza and
alif maqsura folded — not verbatim Tanzil text. Before redistributing:

- Name Tanzil as the source of the Arabic text, with the link, in the release and in both papers.
- Reproduce Tanzil's copyright notice in the release directory.
- Describe the reference as normalized for comparison, never as verbatim canonical text.
- The application's own MIT LICENSE covers its code only, not this third-party text.

## Current annotation review

See [the granular review checkpoint](annotation-review/README.md) for the combined private corpus, multi-location events and per-transcript summaries. The frozen experiment remains separate.

## Documentation map and cleanup

Use `CURRENT-STATE.md` for counts/readiness, `EXPERIMENT.md` for the protocol, `agent-run/RUNBOOK.md` for commands, and `EVALUATOR.md` for scoring. `ANNOTATION-GUIDE.md` and `annotation-review/HAMZA-POLICY.md` define the rubric. The focused paper discussion note records changes to discuss without editing manuscripts.

The temporary September 16 documentation audit was consolidated into those pages and removed. Twenty-one stale private aggregate/report exports and scratch backups were archived with hashes; canonical data and approval history were preserved.

Keep `METHODOLOGY-STUDY3.md`, `docs/STUDY3-ANNOTATION.md`, the 221-to-127 selection audit, `BASELINES-v19.md`, the historical submission checklist and the original teaching files as explicitly historical evidence. They explain earlier paper/release results; deleting them would make those results harder to reproduce. The word `draft` in the original teaching filenames is historical, not their approval status. Use `calibration/teaching-current.md` for the adapted current examples.
