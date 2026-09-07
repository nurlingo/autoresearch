# Study 3 — annotation-assisted transcript checking

Status as of **2026-09-08**: human review is in progress. **40 of the target
100 unique recordings are approved**, covering 71 ayah chunks. Taxonomy v0.16
and recording format v0.6 reflect the current adjudication decisions. They
are versioned working specifications, not a frozen competition contract.
No agent run or algorithm evaluation under this protocol has begun.

This document supersedes the earlier Study 3 plan. The old 20-recording,
99-chunk machine-labeled pilot is a separate artifact, not these 40 approved
recordings. The MusIML branch retains that pilot and its original executable
harness for historical reproducibility; neither implements this protocol.

## 1. Question and scope

Can an agent annotate an unlabelled development pool under a supplied rubric,
then develop an algorithm that generalizes to independently reviewed data?
The agent is responsible for both development annotations and algorithm
construction. The final executable algorithm is the scored deliverable.

The annotation unit is the **whole recording**, including opening formulas
and all existing ayah splits. Review preserves the ASR transcript exactly
and compares each chunk against `backend/quran.json` → `titles.clean` from
the source application. Quran reference text and event reference words remain
verbatim; normalization is only a comparison operation.

The labels describe observable **transcript/reference differences**. They do
not establish whether the speaker or ASR caused a difference. Audio intent,
unwritten vowel errors, and tajweed are outside this text-only review. An
ASR-origin explanation does not turn an unresolved substitution into an
`uncertain` event. Review uncertainty is handled by withholding approval,
not by adding a second event verdict.

The final algorithm input contract remains to be frozen: full transcripts
with detection/splitting, or supplied ayah chunks for an isolated event task.
If full transcripts are used, report split/detection quality separately from
event quality. Do not assume the legacy one-chunk interface has settled this
choice.

## 2. Corpus construction and current evidence

The local source export contains 258 recordings: 220 distinct exact full
transcripts, 218 normalized full transcripts, and 214 normalized recitation
text groups when existing ayah chunks are concatenated without preambles.
Inventory keys guide selection, but existing splits can omit text; always
check full-recording coverage as well. Exact and normalized duplicates must
stay in one partition. Review near-duplicates and record shared ayah coverage.

Select 100 unique recordings for coverage of clean cases, omissions,
substitutions, additions, repeats, repairs, spelling variants, lengths, and
ayahs. Retain clean controls; do not require an error in every recording.
Selection is purposive, not a prevalence sample. Learner balance and repeated
ayah contexts must be audited before freezing; recording-level separation
alone does not guarantee unseen-reciter generalization.

The current approved set has 40 recordings / 71 chunks: 36 chunks without
within-ayah events, 56 within-ayah events, and 16 opening-formula annotations.
These are review counts, not performance results or population proportions.
The remaining 60 recordings still require review. Historical pilot labels
are not imported as gold. See [annotation findings](docs/STUDY3-ANNOTATION.md)
for the definitions, counts, and resolved questions.

Existing Stage-1 assignments are inspected before any correction. Preserve
source splits and record an agreed correction explicitly. A missing beginning,
interior span, or ending of an assigned ayah is an omission, including at the
recording boundary. This convention records missing reference material; it
does not infer why the recording started or stopped there.

## 3. Annotation contract

Each recording stores its exact transcript, source metadata and hash,
preamble, ordered ayah chunks, and review status. Each chunk stores exact
transcript/reference text, reproducible token arrays, and an `events` list.
A reviewed no-event chunk has `label: clean` and `events: []`; an unexamined
chunk can have `events: null`. Only human-approved whole recordings count
against the target.

Each event has one combined `event_verdict` label, `hyp_words`, `ref_words`,
and zero-based half-open `hyp_span` / `ref_span` into the chunk's stored token
arrays. Notes explain contextual judgments. A missing word uses an empty
hypothesis span at the gap; an unrelated addition uses an empty reference
span. A record may contain several events. Ordinary annotation review status
is separate from this single semantic label.

Use whitespace tokens retaining original spelling, excluding standalone
punctuation tokens that contain no letters or digits where present. Do not
compute locations from a normalized string that changes token boundaries.
Preambles with one formula have `text` and `label`; multiple formulas use
full `text` plus ordered `segments`, each with its own text and combined label.

Repetition spans include the **original phrase and its extra copy or copies**;
the reference span contains the phrase once. Correction spans likewise include
both attempts. A recognizable correct-to-incorrect restatement is an unresolved
`substitution_mistake` spanning both attempts, with their order in the note.
Keep a repaired mistake explicit instead of swallowing it inside a benign
repeat. Reference-native repetition is clean.

Merge adjacent same-label substitutions into a phrase event when they are
continuous on both sides without matching text or a distinct attempt boundary
between them. Whitespace need not give equal-length spans: a changed attached
connective may map to a separate reference word. Notes identify unchanged
context inside a selected word span; avoid double-counting it as another error.

## 4. Development annotations and evaluation

Supply the agent with a separate unlabelled development pool, the public Quran
reference, the label definitions, a frozen output schema, and worked examples
that do not disclose evaluation answers. Use synthetic or separately reserved
examples. A disjoint practice exercise and a fixed clarification phase can
check rubric understanding before the measured run.

The agent may annotate its development pool, train or optimize against those
annotations, and revise its algorithm. Archive annotations, code, and run
history for process analysis. Agreement with self-generated labels is **not**
an independent accuracy measurement. Good final gold performance provides
indirect evidence for the usefulness of the overall process; it does not prove
every development annotation was correct or establish annotation as the cause
of any gain. A causal annotation-benefit claim would require a controlled arm.

Freeze the gold set, rubric, input interface, scoring/matching rules, models,
run budgets, and hypotheses before executing the study. These choices remain
open; earlier named models, budgets, H1–H4, and uncertain-credit weights were
planning suggestions, not this protocol's preregistration.

Evaluate the frozen final algorithm privately after the run. Report event-label
and localization quality, missed mistakes, false flags on clean/benign/corrected
cases, and per-label results. Matching must prevent one broad prediction from
claiming multiple distinct gold events, and must explicitly handle zero-length
omission anchors and both-attempt spans. Scalar weights and matching tolerances
are not yet chosen. Do not reuse or report the legacy pilot score as a result
on this set. Re-evaluate baselines only after the new contract is frozen.

## 5. Isolation and public-input exposure

Keep both evaluation transcripts and answers out of the development bundle.
Remove duplicate-equivalent transcripts from development. Do not give agents
this authoring checkout, review files, internal codebook examples, inventory
hints, earlier annotation sessions, private tools, or git history containing
answers. Use a fresh runtime with only allowed inputs mounted and no access to
private answer sources. A gitignored folder or a prompt prohibition is not
an isolation boundary. Return no gold feedback during the run.

**Exposure audit, 2026-09-08:** all 40 approved recording transcripts already
occur in the published Task A release. Five overlap recordings with public
legacy Task B pilot annotations. The new adjudicated labels and selected
recording identities remain private, but the inputs cannot be described as
unpublished. Public-release retrieval must be excluded from agent runtimes;
report this exposure, and do not claim publication-level input secrecy or an
uncontaminated hidden test from runtime isolation alone.

For a competition claiming unseen-input final ranking, acquire and review a
separate set of previously unreleased recordings before launch. Production
availability, permitted reuse, de-identification, and the actual number of
usable new submissions must be checked; historic volume figures are not a
verified new test set. The present 100-recording target is the current private
annotation benchmark, not evidence that such a new collection already exists.

## 6. Next steps

1. Complete the remaining 60 recordings; revisit affected cases whenever a
   taxonomy rule changes and preserve the adjudication history.
2. Audit duplicate groups, split coverage, reference consistency, learner
   concentration, public pilot overlap, and permission for intended reuse.
3. Freeze the input contract, taxonomy, matching rules, and study design;
   publish a sanitized rubric with disjoint examples.
4. Build the new evaluator and isolated development bundle. Verify baseline
   behavior and oracle cases under that contract, then freeze artifacts.
5. Run the annotation-and-development experiments and score final code
   privately. Keep feasibility/pilot observations separate from new results.
