# Study 3 — annotation-assisted transcript checking

Status as of **2026-09-09**: **100/100 selected recording cases are human-approved**,
covering 314 ayah chunks and 274 ayahs across 38 surahs. Three additional
approved recordings are reserves outside the scored set. Taxonomy v0.19 and
recording format v0.6 describe the completed annotation snapshot. The input
choice is settled: supply reviewed ayah chunks and references. The event matcher
is frozen (MIN_SPAN=0.50, anchor slack=1); the executable comparison
normalization and the experiment design still need to be frozen.
Evaluator v2.1 and corrected baseline adapters have been tested and scored;
no agent experiment has run. See [the scorecard](study3/EVALUATOR.md) and
[baseline results](study3/BASELINES-v19.md).

This document supersedes the earlier Study 3 plan. The old 20-recording,
99-chunk machine-labeled pilot is a separate artifact, not these 100 approved
recordings. The MusIML branch retains that pilot and its original executable
harness for historical reproducibility; neither implements this protocol.

## 1. Question and scope

Can an agent annotate an unlabelled development pool under a supplied rubric,
then develop an algorithm that generalizes to independently reviewed data?
The agent is responsible for both development annotations and algorithm
construction. The final executable algorithm is the scored deliverable.

The annotation unit is the **whole recording**, including opening formulas
and all human-reviewed ayah splits. Review preserves the ASR transcript exactly
and compares each chunk against `backend/quran.json` → `titles.clean` from
the source application. Quran reference text and event reference words remain
verbatim; normalization is only a comparison operation.

The labels describe observable **transcript/reference differences**. They do
not establish whether the speaker or ASR caused a difference. Audio intent,
unwritten vowel errors, and tajweed are outside this text-only review. An
ASR-origin explanation does not turn an unresolved substitution into an
`uncertain` event. Review uncertainty is handled by withholding approval,
not by adding a second event verdict.

The final algorithm receives **human-reviewed ayah splits, ayah IDs, and exact
reference texts**, with opening text retained without its gold labels. Score
event labels and localization conditional on these supplied inputs; ayah
identification and splitting are outside this score. Source split history,
reviewer notes, events and verdicts are private answer-side data. Corrections
to source assignments are explicit and preserve the raw transcript.

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

The completed selected set contains **100 recordings / 314 chunks**: 233
chunks without within-ayah events, 115 within-ayah events, and 47 opening-formula
annotations. Three approved reserves are excluded from these counts. No
selected annotation decisions remain open. These are coverage counts, not
performance results or population proportions. Historical pilot labels are
not imported as gold. See [annotation findings](docs/STUDY3-ANNOTATION.md).

The source-attribution audit checked all selected recording IDs and exact
transcripts against both the CSV and original recording export. No IDs or
stored audio paths are reused. Selection normalization also ignores punctuation;
this catches duplicates missed by the earlier inventory keys. Complete
normalized duplicates and redundant clean subpassages are excluded. Shared
passages are retained only for an explicit difference in the whole-recording
event pattern, such as a repaired versus unresolved error or a complete versus
partial ayah. Containment, token similarity and shared event signatures are
review flags, not proof of identical audio; audio bytes were not compared.

The selected records come from ten learner IDs; one accounts for 46 records.
Do not describe this purposive set as learner-balanced, statistically
independent, or evidence of unseen-reciter generalization.

Existing Stage-1 assignments are inspected before any correction. Preserve
source splits and record an agreed correction explicitly. A missing beginning,
interior span, or ending of an assigned ayah is an omission, including at the
recording boundary. This convention records missing reference material; it
does not infer why the recording started or stopped there. A wholly missing
intervening ayah can be an explicit empty chunk only after human adjudication
of a continuous passage; an ayah-ID gap alone does not establish an omission.
A recording ending after a complete ayah does not imply omitted future ayahs.

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
run budgets, and hypotheses before executing the study. The supplied-split
input choice is approved; remaining executable and scoring details stay open.
Earlier named models, budgets, H1–H4, and uncertain-credit weights were
planning suggestions, not this protocol's preregistration.

Evaluate the frozen final algorithm privately after the run. Report event-label
and localization quality, missed mistakes, false flags on clean/benign/corrected
cases, and per-label results. Matching must prevent one broad prediction from
claiming multiple distinct gold events, and must explicitly handle zero-length
omission anchors and both-attempt spans. The current primary metric is label-aware micro F1, with exact-span F1 alongside
it and a raw-count mistake cost as a secondary metric. MIN_SPAN=0.50 and anchor
slack=1 are frozen; the secondary cost is reported at both 1:1 and 2:1 rather
than frozen at one rate. Baselines have been rerun against
v2.1; do not reuse v1.0/v2.0 or legacy pilot numbers. Freeze the experiment
contract after disjoint practice validation.

## 5. Isolation and public-input exposure

Keep both evaluation transcripts and answers out of the development bundle.
Remove duplicate-equivalent transcripts from development. Do not give agents
this authoring checkout, review files, internal codebook examples, inventory
hints, earlier annotation sessions, private tools, or git history containing
answers. Use a fresh runtime with only allowed inputs mounted and no access to
private answer sources. A gitignored folder or a prompt prohibition is not
an isolation boundary. Return no gold feedback during the run.

**Exposure audit, 2026-09-08:** all 100 selected transcripts exactly match
published Task A inputs. Twelve also exactly match at least one recording
represented in the public legacy Task B labelled pilot. This is a transcript
exposure check, not proof of the same production recording ID. New adjudicated
answers and selected membership remain private, but inputs are not unpublished.
Exclude public-release retrieval from agent runtimes and report this exposure;
runtime isolation cannot establish absence of prior model or agent exposure.

For a competition claiming unseen-input final ranking, acquire and review a
separate set of previously unreleased recordings before launch. Production
availability, permitted reuse, de-identification, and the actual number of
usable new submissions must be checked; historic volume figures are not a
verified new test set. The completed 100-recording set is the current private
annotation benchmark, not evidence that such a new collection already exists.

## 6. Next steps

1. Version and protect the completed gold snapshot and approved reserves;
   preserve adjudication history if later corrections change membership.
2. Enforce the audited duplicate/related-case groups when preparing development
   data, and verify permission for intended reuse or a new collection.
3. Finalize the supplied-split interface, matching rules and study design;
   publish a sanitized rubric with disjoint examples.
4. Build the isolated development bundle; retain the validated evaluator and
   adapter regressions, and freeze the chosen scoring contract and artifacts.
5. Run the annotation-and-development experiments and score final code
   privately. Keep feasibility/pilot observations separate from new results.

## Candidate pool after new submissions

The 321 source recordings have 321 transcripts, including the original local ASR
repairs. Holding gold100 aside leaves 221 transcripts; the three approved
reserves' transcript-only copies are included in that pool. The preliminary
text screen leaves 166 distinct
groups after removing exact normalized held-out equivalents; 65 require closer
overlap review. See [the experiment plan](study3/EXPERIMENT.md). No pool has been
allocated or exposed to a development agent. Gold inputs stripped of answers
remain evaluation inputs and must not be used as the development pool.
