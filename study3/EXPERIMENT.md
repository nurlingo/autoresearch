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

There are 321 source recordings and 320 available transcripts (including local
ASR repairs in the original export): 258 old plus 63 new recordings, of which
62 new recordings have stored transcripts. One new recording lacks a transcript.

Holding gold100 aside leaves **220 transcripts = 158 old + 62 new**. Holding the
three approved reserves aside too leaves 217. Preliminary punctuation/mark/alif
normalization and standard-opening removal produce 182 distinct nonempty text
groups; 16 match a held-out gold or reserve group, leaving **166 candidate groups**.
Of those, 65 are flagged for containment or token similarity >=0.85 with held-out
text, while 101 are not flagged by this screen. These are candidate counts, not
a finalized independent development set. Shared ayah/event patterns and split
coverage still need review. Gold membership and overlap maps remain private.

The old inputs already have public Task A answers, and some have legacy Task B
machine labels. New recordings alone do not establish unseen text. The newly
collected candidates also appear in the proposed Task A hidden-test plan: assign
each related group a role before sharing it. A group used for practice or agent
development must not later be described as unseen final-test material.

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
