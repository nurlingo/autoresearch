# Study 3 preparation

This directory prepares the annotation-and-algorithm experiment described in
[METHODOLOGY-STUDY3.md](../METHODOLOGY-STUDY3.md). It includes the executable v2.1 evaluator and baseline adapters; the isolated
agent experiment is not yet packaged. The historical `stage2/` harness uses a different contract.

1. Review the [annotation guide](ANNOTATION-GUIDE.md) and
   [20 constructed Arabic teaching cases](calibration/teaching-draft.md).
2. Approve/revise the teaching answers, then assemble a separate practice batch
   without answers in its input file. Test comprehension and revise the guide
   before a measured run. Do not use gold cases for this exercise.
3. Review [EVALUATOR.md](EVALUATOR.md) and [BASELINES-v19.md](BASELINES-v19.md).
   Version 2.1 validates labels/spans and reports tolerant plus exact-span F1.
   Freeze matching tolerances, budgets and feedback before the agent run.
4. Prepare a separate unlabelled development pool; freeze model/tool budgets,
   comparison conditions, permitted feedback and final evaluation procedure.

The teaching cases are deliberately constructed transcript variants of the
public Quran reference, not recordings or evidence of naturally occurring
errors. Their reference ayah IDs
were checked outside the private evaluation set and the three then-reserved cases.
Exact normalized chunk comparisons are recorded privately; further phrase-overlap
review remains pending. Common Quran words and generic opening formulas are
not exclusive dataset material.

The agent must save its development annotations, annotation revisions, algorithm,
and run log. Final private gold scoring evaluates the resulting algorithm;
self-annotation accuracy and its causal benefit need separate evidence.

The entire authoring repository is not an agent bundle. Build a fresh allowlist
containing approved instructions/examples, Quran references, the separate
unlabelled development inputs and necessary tools. Exclude gold inputs and
answers, source exports, review history, attribution manifests and gold feedback.

See the [recording inventory](RECORDING-INVENTORY.md) for the read-only production
check: 63 additional bot submissions, with 62 stored transcripts and preliminary
duplicate screening. Private production exports are not included here.

[EXPERIMENT.md](EXPERIMENT.md) explains the agent comparison and gold isolation.
The [training release](release/README.md) contains 127 recording cases / 888 input
units; its train-only review sample contains 23 cases / 381 units. Shared clean
ayahs and different error variants are allowed; complete gold copies and copies of
event-bearing gold chunks are excluded. The [submission checklist](SUBMISSION-TODO.md)
tracks what the call requires against what only matters if the proposal is accepted.
[Teaching examples](calibration/teaching-review.html) are constructed cases, all twenty
approved by the owner.

## Corrections to frozen training release v1.0

`release/` is byte-frozen and its `SHA256SUMS` are authoritative, so these two
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
  `backend/quran.json`, whose current bytes hash to `cda42941...`. The reference
  text itself is unaffected: deriving `{id: titles.clean}` from the application
  file reproduces `release/quran-reference.json` on all 6231 entries with no key
  or text differences. The discrepancy is confined to parts of the source file
  the reference does not use.

## Quran reference provenance and redistribution

Established 2026-09-09 against the application's `backend/quran.json` and Tanzil's
published `simple-clean` text.

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
release builder's `len(id)==6` filter drops. Neither gold nor train references any
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
