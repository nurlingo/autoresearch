# Recording inventory

## Current read-only check — 2026-09-15

| Family | Total recordings | Stored transcripts | New since prior inventory |
|---|---:|---:|---:|
| Bot/autodetect | 330 | 305 | 9 IDs, all with transcripts |
| Single-ayah app | 25,776 | 25,599 | 357 newer rows, all with transcripts |

Six autodetect cases have been added as drafts, bringing the working corpus from 188 to 194. Each has one stored transcript and verified original audio bytes. Single-ayah cases are excluded at the owner’s direction because their transcription convention differs. Six further suitable autodetect cases are needed for 200. See [current state](CURRENT-STATE.md). No production rows were changed.

## Historical check — 2026-09-08

The production PostgreSQL database was inspected using read-only transactions.

| Recording family | Historical inventory | Current total | Current stored transcripts |
|---|---:|---:|---:|
| Bot auto-detect | 258 | 321 | 296 |
| Single-ayah app | 21,053 | 25,419 | 25,242 |

All 258 old bot recording IDs remain present. There are 63 new IDs, created
from July 6 through August 24: 62 done rows with stored transcripts and one
failed row without a stored transcript. Five learner IDs contributed the new
batch; three are absent from the old bot export. No production rows were changed.

The initial comparison removes marks/punctuation, normalizes hamza-bearing alif,
and strips standard opening formulas for duplicate checks only. The exact stored
transcript text is preserved separately in the private local export.

The 62 new transcripts form 60 nonempty normalized recitation groups; 57 groups
do not equal a group in the old export. Six of those 57 are flagged for
containment or token similarity of at least 0.85 against old texts. These flags
need human review. They do not establish duplicate audio or independent cases.
No new dataset split or claim of unpublished input has been established.

The current single-ayah count is 4,366 higher than the historical inventory;
that difference is not a verified count of new IDs because the old inventory
contains no full single-ayah ID manifest. Of current single-ayah rows, 4,085
were created on or after July 1, and 4,074 of those have stored transcripts.

Next: review new bot text/related-case flags, partition candidate groups before
annotation, and keep teaching, practice, unlabelled development and any future
unseen-input evaluation collection separate. Gold100 is unchanged. Raw exports,
source IDs, learner IDs and private overlap mappings stay outside this repository.
The twenty teaching drafts are constructed examples, not these new recordings.
