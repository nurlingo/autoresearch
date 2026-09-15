# Human annotation of the working corpus

Current state: [194 cases](CURRENT-STATE.md), combining historical gold/train on equal terms with six new autodetect drafts. The owner chose one transcript per identical-audio group and a target of 200. Single-ayah app recordings are excluded because their transcription convention differs. All 15 presented hamza events are approved; remaining drafts and interpretation questions are tracked privately.

The 221 → 127 audit below remains valid for the **frozen experiment release**. Its annotation plan and starting progress are historical, not current corpus totals.

## Selection audit — 2026-09-10

The independent owner-side audit confirms **221 candidates → 127 training cases**.
All 221 source recording identities are unique, the 127 retained and 94 excluded
records form a complete disjoint partition, and none of the retained recording
identities is in gold100. Released transcripts and ayah units match their attributed
source records. Saved prepared-input and gold-bundle hashes match the original audit.

| First applicable exclusion reason | Cases |
|---|---:|
| Complete normalized gold recitation copy | 36 |
| Copy of an event-bearing gold ayah chunk | 11 |
| Unresolved split, reference assignment or source mismatch | 20 |
| Non-Quran material outside this task | 1 |
| Exact duplicate of a retained training case | 10 |
| Shorter ordered passage contained in a retained training case | 16 |
| **Total excluded** | **94** |
| **Retained** | **127** |

Each excluded duplicate/shorter passage has a concrete retained recording as a
witness. The 20 unresolved records are quarantined, not classified as duplicates
or deleted. They may be repaired for a future release.

Shared clean ayahs and different error variants remain eligible. The retained
training set includes 162 ayah units identical under screening normalization to
clean gold units. That is allowed by the declared policy. The audit found no
retained complete gold recitation copy or normalized copy of an event-bearing
gold chunk. This verifies the declared separation, not absence of every related
phrase, semantic overlap or prior public exposure.

Recitation identity uses the original full ASR transcript after comparison
normalization and standard-opening removal. Concatenating only ayah chunks is
insufficient for this check: a basmala can be assigned to ayah 1:1 in one split
and treated as opening text in another. The audit independently confirmed such
cases against the original approved transcripts. It did not merely trust a cached
exclusion flag or edit the frozen release.

The reproducible audit is `tools/audit_train_partition.py`. It accepts prepared
source records, private attribution, canonical gold reviews, the gold bundle and
the release directory. It prints aggregates; optional detailed witnesses must go
to a private report outside the release. All inputs containing answers or source
identities remain owner-side.

## Historical training annotation plan — superseded by the combined corpus

The owner will human-review the **127 training recordings / 888 units**, using the
same event labels and word-span conventions as gold100. The three former approved
reserves already match training inputs exactly; their user approvals were carried
over privately. Initial progress: **3 approved, 124 awaiting review**.

A private review workspace holds one JSON record per training case, a queue and an
offline viewer showing the whole transcript, supplied splits, actual Quran reference,
original word indices and saved events. Unreviewed units have `events: null`;
`events: []` is reserved for an explicitly reviewed clean unit. New suggestions
must remain drafts until the owner approves the recording. Split/reference questions
are recorded separately and block approval, rather than silently changing source text.

Human training labels stay separate from the frozen answer-free training release.
Agents still receive the same unlabelled inputs. The owner's answers can directly
evaluate any training annotations an agent produces, without supplying feedback
from them during development. This is annotation agreement on seen training inputs;
algorithm generalization is still measured against the separate gold100 test.

Under that earlier plan, finishing the review would have yielded **227 human-annotated transcript cases** across
127 training and 100 test cases. It would not create a 227-case unseen test set.
Any later publication of training answers must be versioned and disclosed; future
runs on those published answers would use a different information condition.

Gold100, its annotations and the frozen training release remain unchanged. A repair
found during review requires an explicit versioned input correction; annotation
progress alone does not rewrite the released inputs or earlier pilot results.
