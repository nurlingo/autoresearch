# Annotation-and-algorithm experiment — preparation

## The research question

Can an agent annotate a separate unlabelled transcript pool under our rubric
and develop an algorithm that agrees with independent human annotations?
Gold100 remains fixed and hidden from the development agent, inputs included.

## Separation of roles

| Role | Available material | Feedback |
|---|---|---|
| Human preparation | Private exports, gold100, overlap audit | Review and approve partition/calibration |
| Development agent | Approved guide/examples, separate practice and development inputs, Quran reference, tools | Practice answers and development checks only |
| Final frozen algorithm | Reviewed gold input units during owner-controlled evaluation | No edits, external retrieval or return channel to the development agent |
| Private evaluator | Gold annotations and frozen-code predictions | Final aggregate metrics after the run |

The code returned by the agent necessarily processes gold input at final scoring;
the developing agent must not inspect it or receive gold feedback. Removing labels
from gold is insufficient. `make_inputs.py` is for the owner-controlled evaluation
stage. Do not run an agent with `--gold`, the private reviewer bundle, or the
full source checkout mounted. The current scripts prepare/score data; they do
not themselves implement runtime isolation.

## Candidate inventory, 2026-09-09

There are 321 source recordings and 321 available transcripts: 258 old plus
63 new. Of the new transcripts, 62 were stored in production and one was obtained
with a local ASR call on 2026-09-09; the production export and database were not
changed. That last transcript appears to contain salawat/dua rather than ayahs,
with Urdu-style characters, and needs human review before task inclusion.

Holding gold100 aside leaves **221 transcript candidates = 158 old + 63 new**.
The three former approved reserves are included in the 158 old candidates:
their transcript-only copies now join this pool, while original approved
annotations remain private archives. Gold100 and its reviewer bundle are unchanged.

Preliminary punctuation/mark/alif normalization and standard-opening removal
produce 186 distinct nonempty text groups. Sixteen groups (36 recordings) match
gold recitation cores, leaving **170 candidate groups / 185 recordings**.
Sixty-three groups are flagged for token containment or token similarity >=0.85
with gold, while 107 are unflagged. This screen uses the reviewed gold transcripts;
it does not automatically reject every shared ayah or establish safe independence.
The new non-Quran candidate is included in these raw counts. Related-case review,
within-recording chunk overlap and corrected ayah splits remain to be completed.
All membership maps and candidate transcripts stay private during preparation.

## Duplicate policy

Exclude exact copies of gold inputs and equivalent recitation/error cases from
agent development, even if their answers have been stripped: the agent would
otherwise practice on its final exam. Review near matches at the ayah/chunk level.
Shared Quran references, generic formulas, and the same ayah with materially
different mistake patterns are not automatically leakage. Do not impose an unseen-
ayah split unless that is the intended generalization claim.

Within development, keep one representative per equivalent text case by default;
retain provenance and multiplicity privately. This improves coverage per unit of
annotation cost. Keeping duplicates can represent repeated production patterns,
but overweights common cases and wastes annotation budget; use declared weights
if frequency is the intended objective. Do not silently delete the source archive.

The old inputs already have public Task A answers, and some have legacy Task B
machine labels. Hiding our annotations cannot undo prior public exposure. Build
an allowlisted development environment and state this limitation explicitly.
A group used for development must not later be called unseen final-test material.

## Proposed competition scope

Paper 1 can propose the annotation-and-algorithm task: entrants receive approved
label definitions/examples, the Quran reference and separately reviewed ayah-split
unlabelled development transcripts. They save their annotations and revisions,
then train a model or develop an algorithm. They submit frozen code and logs;
the owner runs that code on gold100 inputs and compares predictions privately.
Neither gold inputs nor answers are available during development. Ayah splitting
is provided so identification errors do not contaminate annotation evaluation.

Use public practice/development feedback for iteration, never gold100 feedback.
Repeated gold leaderboard queries would turn the final set into development data.
Primary scoring is label-aware event F1; exact-span F1 and the provisional 2:1
review cost are supporting metrics. Submitted training annotations make the
process inspectable but are not independently graded without another human audit.

The current two-page Paper 1 still describes detect-and-split (Task A). This is
a proposed replacement scope, not a completed Task B release. Track 3 requires
a ready-to-use dataset, a 10% review sample, defined metrics and evaluated baselines
([official call](https://www.musiml.org/events/2026-NeurIPS/index.html)). Prepare
and approve an actual development sample and specify the sample denominator;
confirm how a hidden-test competition should satisfy the review requirement.
Keeping gold private from agents does not mean withholding required review material.

Paper 2 currently contributes the human annotation, taxonomy, evaluator and
baseline analysis. It has no measured annotation-and-algorithm loop yet. An
empirical extension would compare an explicit annotation-and-development loop
against an algorithm-only loop under equal model/tool budgets and feedback,
then evaluate both frozen methods once on gold100. Distinguish this research
contribution from competition rules if submitting both papers.

## Before a measured run

1. Finish related-case review and freeze a group-level partition: teaching,
   practice, unlabelled development, and any separately reserved future test.
2. Approve Arabic teaching examples and practice feedback; freeze normalization,
   threshold/anchor rules and the secondary cost preference independently of gold.
3. Fix the model, tools, time/token/cost budget and comparison conditions.
4. Build and inspect a fresh allowlisted runtime. Exclude gold, source exports,
   production identifiers, private notes, previous sessions and answer-bearing
   history; block retrieval of the published benchmark during development.
5. Require saved development annotations and revisions, final code and run logs.
   Freeze the code, then score privately. Do not optimize it using gold feedback.

Final algorithm performance is evidence about the combined process. It does not
prove every development annotation correct. To estimate the benefit of an explicit
annotation phase, compare with an equal-budget algorithm-only condition. No such
agent experiment or comparison has run yet.
