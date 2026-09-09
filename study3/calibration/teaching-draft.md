# Constructed Arabic teaching cases

20 deliberately constructed text variants, not collected recordings. Reference text is verbatim `titles.clean`. Spans are zero-based and half-open over whitespace tokens. Taxonomy 0.19.

| ID | Teaching objective | Status |
|---|---|---|
| t01 | Clean after ordinary hamza normalization | approved |
| t02 | Missing beginning | approved |
| t03 | Missing interior word | approved |
| t04 | Missing ending | approved |
| t05 | One unresolved replacement | approved |
| t06 | Adjacent replacements grouped | approved |
| t07 | Two mistakes separated by correct words | approved |
| t08 | Extra words | approved |
| t09 | Matching phrase repeated | approved |
| t10 | Wrong then correct | approved |
| t11 | Correct then wrong on restatement | approved |
| t12 | Omission restored on restart | approved |
| t13 | Complete spoken letter names | approved |
| t14 | Incomplete spoken letter names | approved |
| t15 | Contextual word boundary is benign | approved |
| t16 | Istiadhah outside the ayah | approved |
| t17 | Basmala outside the ayah | approved |
| t18 | Whole intervening ayah omitted | approved |
| t19 | Repeated word already in the reference is clean | approved |
| t20 | Two different errors in one ayah | approved |

## t01 — Clean after ordinary hamza normalization

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:1

- transcript: لا أقسم بهذا البلد
- reference: لا اقسم بهذا البلد
- **clean** — no events


## t02 — Missing beginning

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:4

- transcript: الانسان في كبد
- reference: لقد خلقنا الانسان في كبد
- **omission_mistake** — transcript [0, 0] empty anchor at 0, reference [0, 2] «لقد خلقنا»


## t03 — Missing interior word

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:14

- transcript: او اطعام في يوم مسغبة
- reference: او اطعام في يوم ذي مسغبة
- **omission_mistake** — transcript [4, 4] empty anchor at 4, reference [4, 5] «ذي»


## t04 — Missing ending

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:17

- transcript: ثم كان من الذين امنوا وتواصوا بالصبر
- reference: ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة
- **omission_mistake** — transcript [7, 7] empty anchor at 7, reference [7, 9] «وتواصوا بالمرحمة»


## t05 — One unresolved replacement

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:6

- transcript: يقول اهلكت ذهبا لبدا
- reference: يقول اهلكت مالا لبدا
- **substitution_mistake** — transcript [2, 3] «ذهبا», reference [2, 3] «مالا»


## t06 — Adjacent replacements grouped

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:6

- transcript: يقول اهلكت كنزا كثيرا
- reference: يقول اهلكت مالا لبدا
- **substitution_mistake** — transcript [2, 4] «كنزا كثيرا», reference [2, 4] «مالا لبدا»


## t07 — Two mistakes separated by correct words

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:8

- transcript: هل نجعل له اذنين
- reference: الم نجعل له عينين
- **substitution_mistake** — transcript [0, 1] «هل», reference [0, 1] «الم»
- **substitution_mistake** — transcript [3, 4] «اذنين», reference [3, 4] «عينين»


## t08 — Extra words

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:9

- transcript: ولسانا وعينين وشفتين
- reference: ولسانا وشفتين
- **insertion_mistake** — transcript [1, 2] «وعينين», reference [1, 1] empty anchor at 1


## t09 — Matching phrase repeated

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 91:1

- transcript: والشمس وضحاها والشمس وضحاها
- reference: والشمس وضحاها
- **repetition_benign** — transcript [0, 4] «والشمس وضحاها والشمس وضحاها», reference [0, 2] «والشمس وضحاها»


## t10 — Wrong then correct

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 91:2

- transcript: والشمس والقمر اذا تلاها
- reference: والقمر اذا تلاها
- **substitution_corrected** — transcript [0, 2] «والشمس والقمر», reference [0, 1] «والقمر»


## t11 — Correct then wrong on restatement

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 91:3

- transcript: والنهار اذا جلاها والليل اذا جلاها
- reference: والنهار اذا جلاها
- **substitution_mistake** — transcript [0, 6] «والنهار اذا جلاها والليل اذا جلاها», reference [0, 3] «والنهار اذا جلاها»

Note. The correct attempt comes first and the incorrect restatement follows; the span covers both attempts in that order. The extra material re-renders the same reference words (two of its three tokens match), which makes it a restatement rather than an insertion. Contrast t08, where the extra word restates nothing.


## t12 — Omission restored on restart

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:14

- transcript: او اطعام في يوم مسغبة او اطعام في يوم ذي مسغبة
- reference: او اطعام في يوم ذي مسغبة
- **omission_corrected** — transcript [0, 11] «او اطعام في يوم مسغبة او اطعام في يوم ذي مسغبة», reference [0, 6] «او اطعام في يوم ذي مسغبة»


## t13 — Complete spoken letter names

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 26:1

- transcript: طا سين ميم
- reference: طسم
- **letters_benign** — transcript [0, 3] «طا سين ميم», reference [0, 1] «طسم»


## t14 — Incomplete spoken letter names

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 26:1

- transcript: طا سين
- reference: طسم
- **substitution_mistake** — transcript [0, 2] «طا سين», reference [0, 1] «طسم»


## t15 — Contextual word boundary is benign

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 4:78

- transcript: اين ما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وان تصبهم حسنة يقولوا هذه من عند الله وان تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا
- reference: اينما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وان تصبهم حسنة يقولوا هذه من عند الله وان تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا
- **spelling_benign** — transcript [0, 2] «اين ما», reference [0, 1] «اينما»

Note. Approved. Word-boundary difference only: with whitespace removed the letter sequences are identical (اينما = اين ما), so no letters were changed. The same phrase is written joined in 4:78 and separated in 2:148, so the boundary is contextual. A split that also changes letters is a substitution, not a benign spelling difference.


## t16 — Istiadhah outside the ayah

Status: **approved**. constructed teaching transcript; not a recording.

Preamble (`isti3adha_benign`): أعوذ بالله من الشيطان الرجيم

Ayah 90:13

- transcript: فك رقبة
- reference: فك رقبة
- **clean** — no events


## t17 — Basmala outside the ayah

Status: **approved**. constructed teaching transcript; not a recording.

Preamble (`basmala_benign`): بسم الله الرحمن الرحيم

Ayah 90:13

- transcript: فك رقبة
- reference: فك رقبة
- **clean** — no events


## t18 — Whole intervening ayah omitted

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:12

- transcript: وما ادراك ما العقبة
- reference: وما ادراك ما العقبة
- **clean** — no events

Ayah 90:13

- transcript: _empty — adjudicated whole-ayah omission_
- reference: فك رقبة
- **omission_mistake** — transcript [0, 0] empty anchor at 0, reference [0, 2] «فك رقبة»

Ayah 90:14

- transcript: او اطعام في يوم ذي مسغبة
- reference: او اطعام في يوم ذي مسغبة
- **clean** — no events

Note. Constructed scenario: the intended continuous passage was established as 90:12–14 before event annotation. The supplied empty chunk makes this explicit. Do not infer missing ayahs from arbitrary ID gaps.


## t19 — Repeated word already in the reference is clean

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:17

- transcript: ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة
- reference: ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة
- **clean** — no events

Note. وتواصوا occurs twice in the reference; its two matching occurrences are not an extra repetition.


## t20 — Two different errors in one ayah

Status: **approved**. constructed teaching transcript; not a recording.

Ayah 90:17

- transcript: ثم كان الذين امنوا وتواصوا بالصبر وتواصوا بالرحمة
- reference: ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة
- **omission_mistake** — transcript [2, 2] empty anchor at 2, reference [2, 3] «من»
- **substitution_mistake** — transcript [7, 8] «بالرحمة», reference [8, 9] «بالمرحمة»

Note. A chunk carries every event it contains, and they need not share a label. Finding one error does not end the search. Omission and substitution together are the most common combination in reviewed data.
