# Annotation-and-algorithm experiment — preparation

## The research question

How do different agents develop transcript-annotation algorithms under the same
data, rubric, tools and budget, and how well do their frozen methods agree with
independent human annotations? Agents may create their own training annotations.
The gold100 test bundle remains fixed and hidden from development agents. Shared
clean Quran units can occur in training; no claim of entirely unseen test inputs.

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

Training release v1.0 contains **127 cases / 888 units**: 83 old and 44 new
recordings. Of the 221 candidates, 36 complete gold copies, 11 event-bearing
gold chunk copies, 20 unresolved cases, one non-Quran case and 26 redundant
training cases are excluded. Shared clean ayahs and different error variants
remain eligible. See [release preparation](release/README.md) for exact rules,
provenance and limitations. The source archive and private attribution are intact.
The train-only review sample contains 23 cases and 394 units, exceeding 10% of
combined train+gold by either count. Sample interpretation still needs confirmation.

## Duplicate policy

Exclude complete gold copies and copies of gold chunks that contain annotated
events, including benign/corrected events. Permit shared clean ayahs and different
error variants; the reference itself is public. This protects event-case separation
without discarding every long recording that contains a common clean ayah.
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

Paper 1 can propose a method-agnostic annotation task: entrants receive approved
label definitions/examples, the Quran reference and separately reviewed ayah-split
unlabelled development transcripts. They decide how to annotate, train, develop
and validate their method; humans, agents and hand-written algorithms are allowed.
Only the final frozen solution is scored. Intermediate iterations, development
annotations and autoresearch logs are not required for competition ranking.
The owner runs the submitted solution on gold100 inputs and scores it privately.
The selected gold test bundle and answers are not supplied during development.
Shared clean units and prior public inputs are disclosed limitations. Ayah splitting
is provided so identification errors do not contaminate annotation evaluation.

Entrants choose their own development checks; organizers need not score iterations
or operate a development leaderboard. Any supplied practice answers are separate
from gold100. Repeated gold leaderboard queries would turn the final set into development data.
Primary scoring is label-aware event F1; exact-span F1 and the provisional 2:1
review cost are supporting metrics. Annotation artifacts may be requested for
optional analysis, but are not independently graded without another human audit.

Paper 1 has been rewritten around final-solution annotation scoring. Track 3
requires a ready-to-use dataset, a 10% review sample, defined metrics and evaluated
baselines ([official call](https://www.musiml.org/events/2026-NeurIPS/index.html)).
The review sample comes entirely from training and is sized to exceed 10% of
train plus gold by both recording and unit count. Its unlabelled, train-only
interpretation still needs confirmation. Gold inputs and answers remain private.
The release and outstanding work are described in [SUBMISSION-TODO.md](SUBMISSION-TODO.md).

## Paper 2 — comparison between agents

The comparison is between agents, not between mandatory and optional annotation
workflows. Give every agent the same unlabelled training inputs, rubric, approved
examples, tools and total budget. They may annotate, train a model, write rules,
or combine these strategies. Require final code and logs; save any annotations
and revisions they choose to create. Score frozen solutions privately on gold100.
No agent-comparison runs have occurred yet.

Use a common instruction to all agents: "Develop a method that outputs the supplied
event labels and spans. You may create and revise training annotations. Preserve
any generated annotations, code, experiment results and costs for analysis."
Whether annotations were produced, how much data was labelled and whether those
labels were used are observations about strategy, not separately scored outcomes.
Choose agent versions, tools and budget before running, repeat runs where feasible,
and report run variation as well as final scores. Do not give gold feedback for
algorithm revision or cherry-pick methods through repeated gold queries.

If annotation delivery is later required for reuse, apply that requirement equally
to all compared agents; that remains an agent comparison, with a shared artifact
requirement. There is no need to human-label the whole training pool. Record the
chosen protocol before starting rather than changing it after seeing scores.

A high-scoring method provides evidence that the overall development process can
produce useful predictions. Its training annotations do not thereby become gold:
the code may ignore them, repair them or succeed despite systematic errors in them.
Retain them as machine-generated, unreviewed artifacts with provenance. Direct
annotation agreement requires a separate human audit, which can use a subset
rather than the entire pool. Review before treating annotations as reliable reused
labels. A human-supervised baseline is an optional additional experiment.

## Before a measured run

1. Finish related-case review and freeze a group-level partition: teaching,
   practice, unlabelled development, and any separately reserved future test.
2. Approve Arabic teaching examples and practice feedback; freeze normalization,
   threshold/anchor rules and the secondary cost preference independently of gold.
3. Fix the model, tools, time/token/cost budget and comparison conditions.
4. Build and inspect a fresh allowlisted runtime. Exclude gold, source exports,
   production identifiers, private notes, previous sessions and answer-bearing
   history; block retrieval of the published benchmark during development.
5. Require final code, run logs and any development annotations/revisions produced.
   Freeze the code, then score privately. Do not optimize it using gold feedback.

Final algorithm performance is evidence about the combined process, not proof of
annotation accuracy or the causal benefit of annotating. Paper 2 will report the
agent comparison and observed strategies; no new agent results are claimed yet.
