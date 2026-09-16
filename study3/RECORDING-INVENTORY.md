# Recording inventory

## Current read-only check — 2026-09-16 07:14 UTC

| Family | Total recordings | Stored transcripts | Change since September 15 snapshot |
|---|---:|---:|---|
| Bot/autodetect | 356 | 330 | 26 new IDs; 25 have transcripts |
| Single-ayah app | 25,784 | 25,607 | +8 rows and +8 transcripts; excluded from this dataset |

Of the 26 new autodetect recordings, two are already active dataset cases, now explicitly owner-approved. Twenty-four are outside the active corpus, of which 23 have stored transcripts. This includes a previously dismissed duplicate, a deferred taxonomy case and an annotation withdrawn for fresh review; new inventory rows are not automatically new useful cases.

The first five-case recommendation was superseded after the owner prioritized rare-label gaps. Five assistant-labelled candidates were subsequently owner-approved and merged: spoken letters and a corrected substitution for train; an uncorrected insertion, a benign hamza-seat spelling and a corrected omission for gold. They complete 100 train / 100 gold. A subsequent read-only targeted search found the exact newer transcript supplied by the owner, filling the omission-repair slot. It was submitted at 12:59:55 database time, after the 07:14 UTC inventory snapshot; the totals above remain the dated snapshot, not a fresh full count. Previously deferred/withdrawn cases are not automatically reinstated to fill this gap.

All five are included in the private `granular-100x100-v1.0` freeze. Exact reference spans and stored transcript preservation were validated; no event-bearing ayah text collides with the opposite active split. Source IDs and database audio hashes are distinct from all 195 active recordings. Original audio for the earlier five-case proposal was already downloaded and hash-verified; the revised review bundle tracks its additional source audio separately.

Recording identities, transcripts, exports, audio and annotations remain in private `inventory_20260916/`, with the historical candidate proposals in `gap-targeted-drafts.jsonl` and `gap-targeted-review.html`. Single-ayah app recordings stay excluded. Production rows and storage objects were not changed.

## Previous checkpoint — 2026-09-15

The previous snapshot had 330 autodetect recordings / 305 transcripts and 25,776 single-ayah recordings / 25,599 transcripts. The intermediate six-case extension and 194-case corpus were later superseded by additions, withdrawals and split updates; see [CURRENT-STATE.md](CURRENT-STATE.md).

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
