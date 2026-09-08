# Constructed Arabic teaching cases — draft

All 20 cases require human review. These are deliberately constructed text variants, not collected recordings. Reference text is verbatim `titles.clean`. The word-boundary example additionally needs explicit linguistic approval.

| ID | Teaching objective | Status |
|---|---|---|
| t01 | Clean after ordinary hamza normalization | draft |
| t02 | Missing beginning | draft |
| t03 | Missing interior word | draft |
| t04 | Missing ending | draft |
| t05 | One unresolved replacement | draft |
| t06 | Adjacent replacements grouped | draft |
| t07 | Two mistakes separated by correct words | draft |
| t08 | Extra words | draft |
| t09 | Matching phrase repeated | draft |
| t10 | Wrong then correct | draft |
| t11 | Correct then wrong | draft |
| t12 | Omission restored on restart | draft |
| t13 | Ordinary spelling normalization is clean | draft |
| t14 | Complete spoken letter names | draft |
| t15 | Incomplete spoken letter names | draft |
| t16 | Contextual word boundary — requires explicit approval | draft |
| t17 | Istiadhah outside the ayah | draft |
| t18 | Basmala outside the ayah | draft |
| t19 | Whole intervening ayah omitted | draft |
| t20 | Repeated word already in the reference is clean | draft |

## t01 — Clean after ordinary hamza normalization

Expected annotation is shown below for review.

```json
{
  "example_id": "t01",
  "name": "Clean after ordinary hamza normalization",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090001",
      "transcript": "لا أقسم بهذا البلد",
      "reference_text": "لا اقسم بهذا البلد",
      "transcript_tokens": [
        "لا",
        "أقسم",
        "بهذا",
        "البلد"
      ],
      "reference_tokens": [
        "لا",
        "اقسم",
        "بهذا",
        "البلد"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```

## t02 — Missing beginning

Expected annotation is shown below for review.

```json
{
  "example_id": "t02",
  "name": "Missing beginning",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090004",
      "transcript": "الانسان في كبد",
      "reference_text": "لقد خلقنا الانسان في كبد",
      "transcript_tokens": [
        "الانسان",
        "في",
        "كبد"
      ],
      "reference_tokens": [
        "لقد",
        "خلقنا",
        "الانسان",
        "في",
        "كبد"
      ],
      "events": [
        {
          "label": "omission_mistake",
          "hyp_words": "",
          "ref_words": "لقد خلقنا",
          "hyp_span": [
            0,
            0
          ],
          "ref_span": [
            0,
            2
          ],
          "note": "The two initial reference words are absent."
        }
      ]
    }
  ]
}
```

## t03 — Missing interior word

Expected annotation is shown below for review.

```json
{
  "example_id": "t03",
  "name": "Missing interior word",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090014",
      "transcript": "او اطعام في يوم مسغبة",
      "reference_text": "او اطعام في يوم ذي مسغبة",
      "transcript_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "مسغبة"
      ],
      "reference_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "ذي",
        "مسغبة"
      ],
      "events": [
        {
          "label": "omission_mistake",
          "hyp_words": "",
          "ref_words": "ذي",
          "hyp_span": [
            4,
            4
          ],
          "ref_span": [
            4,
            5
          ],
          "note": "ذي is missing between يوم and مسغبة."
        }
      ]
    }
  ]
}
```

## t04 — Missing ending

Expected annotation is shown below for review.

```json
{
  "example_id": "t04",
  "name": "Missing ending",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090017",
      "transcript": "ثم كان من الذين امنوا وتواصوا بالصبر",
      "reference_text": "ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة",
      "transcript_tokens": [
        "ثم",
        "كان",
        "من",
        "الذين",
        "امنوا",
        "وتواصوا",
        "بالصبر"
      ],
      "reference_tokens": [
        "ثم",
        "كان",
        "من",
        "الذين",
        "امنوا",
        "وتواصوا",
        "بالصبر",
        "وتواصوا",
        "بالمرحمة"
      ],
      "events": [
        {
          "label": "omission_mistake",
          "hyp_words": "",
          "ref_words": "وتواصوا بالمرحمة",
          "hyp_span": [
            7,
            7
          ],
          "ref_span": [
            7,
            9
          ],
          "note": "The last two reference words are absent, even if the recording stops here."
        }
      ]
    }
  ]
}
```

## t05 — One unresolved replacement

Expected annotation is shown below for review.

```json
{
  "example_id": "t05",
  "name": "One unresolved replacement",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090006",
      "transcript": "يقول اهلكت ذهبا لبدا",
      "reference_text": "يقول اهلكت مالا لبدا",
      "transcript_tokens": [
        "يقول",
        "اهلكت",
        "ذهبا",
        "لبدا"
      ],
      "reference_tokens": [
        "يقول",
        "اهلكت",
        "مالا",
        "لبدا"
      ],
      "events": [
        {
          "label": "substitution_mistake",
          "hyp_words": "ذهبا",
          "ref_words": "مالا",
          "hyp_span": [
            2,
            3
          ],
          "ref_span": [
            2,
            3
          ],
          "note": "ذهبا replaces مالا."
        }
      ]
    }
  ]
}
```

## t06 — Adjacent replacements grouped

Expected annotation is shown below for review.

```json
{
  "example_id": "t06",
  "name": "Adjacent replacements grouped",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090006",
      "transcript": "يقول اهلكت كنزا كثيرا",
      "reference_text": "يقول اهلكت مالا لبدا",
      "transcript_tokens": [
        "يقول",
        "اهلكت",
        "كنزا",
        "كثيرا"
      ],
      "reference_tokens": [
        "يقول",
        "اهلكت",
        "مالا",
        "لبدا"
      ],
      "events": [
        {
          "label": "substitution_mistake",
          "hyp_words": "كنزا كثيرا",
          "ref_words": "مالا لبدا",
          "hyp_span": [
            2,
            4
          ],
          "ref_span": [
            2,
            4
          ],
          "note": "Two continuous replaced words form one event."
        }
      ]
    }
  ]
}
```

## t07 — Two mistakes separated by correct words

Expected annotation is shown below for review.

```json
{
  "example_id": "t07",
  "name": "Two mistakes separated by correct words",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090008",
      "transcript": "هل نجعل له اذنين",
      "reference_text": "الم نجعل له عينين",
      "transcript_tokens": [
        "هل",
        "نجعل",
        "له",
        "اذنين"
      ],
      "reference_tokens": [
        "الم",
        "نجعل",
        "له",
        "عينين"
      ],
      "events": [
        {
          "label": "substitution_mistake",
          "hyp_words": "هل",
          "ref_words": "الم",
          "hyp_span": [
            0,
            1
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "هل replaces الم."
        },
        {
          "label": "substitution_mistake",
          "hyp_words": "اذنين",
          "ref_words": "عينين",
          "hyp_span": [
            3,
            4
          ],
          "ref_span": [
            3,
            4
          ],
          "note": "اذنين replaces عينين. The correct words between the changes separate the events."
        }
      ]
    }
  ]
}
```

## t08 — Extra words

Expected annotation is shown below for review.

```json
{
  "example_id": "t08",
  "name": "Extra words",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090009",
      "transcript": "ولسانا وعينين وشفتين",
      "reference_text": "ولسانا وشفتين",
      "transcript_tokens": [
        "ولسانا",
        "وعينين",
        "وشفتين"
      ],
      "reference_tokens": [
        "ولسانا",
        "وشفتين"
      ],
      "events": [
        {
          "label": "insertion_mistake",
          "hyp_words": "وعينين",
          "ref_words": "",
          "hyp_span": [
            1,
            2
          ],
          "ref_span": [
            1,
            1
          ],
          "note": "وعينين is extra material, not a matching repeated phrase or a restatement."
        }
      ]
    }
  ]
}
```

## t09 — Matching phrase repeated

Expected annotation is shown below for review.

```json
{
  "example_id": "t09",
  "name": "Matching phrase repeated",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "091001",
      "transcript": "والشمس وضحاها والشمس وضحاها",
      "reference_text": "والشمس وضحاها",
      "transcript_tokens": [
        "والشمس",
        "وضحاها",
        "والشمس",
        "وضحاها"
      ],
      "reference_tokens": [
        "والشمس",
        "وضحاها"
      ],
      "events": [
        {
          "label": "repetition_benign",
          "hyp_words": "والشمس وضحاها والشمس وضحاها",
          "ref_words": "والشمس وضحاها",
          "hyp_span": [
            0,
            4
          ],
          "ref_span": [
            0,
            2
          ],
          "note": "Select original plus extra copy against one reference occurrence."
        }
      ]
    }
  ]
}
```

## t10 — Wrong then correct

Expected annotation is shown below for review.

```json
{
  "example_id": "t10",
  "name": "Wrong then correct",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "091002",
      "transcript": "والشمس والقمر اذا تلاها",
      "reference_text": "والقمر اذا تلاها",
      "transcript_tokens": [
        "والشمس",
        "والقمر",
        "اذا",
        "تلاها"
      ],
      "reference_tokens": [
        "والقمر",
        "اذا",
        "تلاها"
      ],
      "events": [
        {
          "label": "substitution_corrected",
          "hyp_words": "والشمس والقمر",
          "ref_words": "والقمر",
          "hyp_span": [
            0,
            2
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "The first word is wrong and the following attempt restores والقمر. Select both attempts."
        }
      ]
    }
  ]
}
```

## t11 — Correct then wrong

Expected annotation is shown below for review.

```json
{
  "example_id": "t11",
  "name": "Correct then wrong",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "091003",
      "transcript": "والنهار والليل اذا جلاها",
      "reference_text": "والنهار اذا جلاها",
      "transcript_tokens": [
        "والنهار",
        "والليل",
        "اذا",
        "جلاها"
      ],
      "reference_tokens": [
        "والنهار",
        "اذا",
        "جلاها"
      ],
      "events": [
        {
          "label": "substitution_mistake",
          "hyp_words": "والنهار والليل",
          "ref_words": "والنهار",
          "hyp_span": [
            0,
            2
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "The first attempt matches والنهار; the final restatement changes it to والليل. Select both attempts."
        }
      ]
    }
  ]
}
```

## t12 — Omission restored on restart

Expected annotation is shown below for review.

```json
{
  "example_id": "t12",
  "name": "Omission restored on restart",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090014",
      "transcript": "او اطعام في يوم مسغبة او اطعام في يوم ذي مسغبة",
      "reference_text": "او اطعام في يوم ذي مسغبة",
      "transcript_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "مسغبة",
        "او",
        "اطعام",
        "في",
        "يوم",
        "ذي",
        "مسغبة"
      ],
      "reference_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "ذي",
        "مسغبة"
      ],
      "events": [
        {
          "label": "omission_corrected",
          "hyp_words": "او اطعام في يوم مسغبة او اطعام في يوم ذي مسغبة",
          "ref_words": "او اطعام في يوم ذي مسغبة",
          "hyp_span": [
            0,
            11
          ],
          "ref_span": [
            0,
            6
          ],
          "note": "The first attempt lacks ذي; the complete restart restores it. Do not double-label the same attempt."
        }
      ]
    }
  ]
}
```

## t13 — Ordinary spelling normalization is clean

Expected annotation is shown below for review.

```json
{
  "example_id": "t13",
  "name": "Ordinary spelling normalization is clean",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "092003",
      "transcript": "وما خلق الذكر والأنثى",
      "reference_text": "وما خلق الذكر والانثى",
      "transcript_tokens": [
        "وما",
        "خلق",
        "الذكر",
        "والأنثى"
      ],
      "reference_tokens": [
        "وما",
        "خلق",
        "الذكر",
        "والانثى"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```

## t14 — Complete spoken letter names

Expected annotation is shown below for review.

```json
{
  "example_id": "t14",
  "name": "Complete spoken letter names",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "026001",
      "transcript": "طا سين ميم",
      "reference_text": "طسم",
      "transcript_tokens": [
        "طا",
        "سين",
        "ميم"
      ],
      "reference_tokens": [
        "طسم"
      ],
      "events": [
        {
          "label": "letters_benign",
          "hyp_words": "طا سين ميم",
          "ref_words": "طسم",
          "hyp_span": [
            0,
            3
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "The three spoken letter names express طسم in order."
        }
      ]
    }
  ]
}
```

## t15 — Incomplete spoken letter names

Expected annotation is shown below for review.

```json
{
  "example_id": "t15",
  "name": "Incomplete spoken letter names",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "026001",
      "transcript": "طا سين",
      "reference_text": "طسم",
      "transcript_tokens": [
        "طا",
        "سين"
      ],
      "reference_tokens": [
        "طسم"
      ],
      "events": [
        {
          "label": "substitution_mistake",
          "hyp_words": "طا سين",
          "ref_words": "طسم",
          "hyp_span": [
            0,
            2
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "The one-token reference sequence طسم lacks its final ميم in the hypothesis; use the one-token substitution convention."
        }
      ]
    }
  ]
}
```

## t16 — Contextual word boundary — requires explicit approval

Review this linguistic example explicitly before including it in an agent guide.

```json
{
  "example_id": "t16",
  "name": "Contextual word boundary — requires explicit approval",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "Review this linguistic example explicitly before including it in an agent guide.",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "004078",
      "transcript": "اين ما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وان تصبهم حسنة يقولوا هذه من عند الله وان تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا",
      "reference_text": "اينما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وان تصبهم حسنة يقولوا هذه من عند الله وان تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا",
      "transcript_tokens": [
        "اين",
        "ما",
        "تكونوا",
        "يدرككم",
        "الموت",
        "ولو",
        "كنتم",
        "في",
        "بروج",
        "مشيدة",
        "وان",
        "تصبهم",
        "حسنة",
        "يقولوا",
        "هذه",
        "من",
        "عند",
        "الله",
        "وان",
        "تصبهم",
        "سيئة",
        "يقولوا",
        "هذه",
        "من",
        "عندك",
        "قل",
        "كل",
        "من",
        "عند",
        "الله",
        "فمال",
        "هؤلاء",
        "القوم",
        "لا",
        "يكادون",
        "يفقهون",
        "حديثا"
      ],
      "reference_tokens": [
        "اينما",
        "تكونوا",
        "يدرككم",
        "الموت",
        "ولو",
        "كنتم",
        "في",
        "بروج",
        "مشيدة",
        "وان",
        "تصبهم",
        "حسنة",
        "يقولوا",
        "هذه",
        "من",
        "عند",
        "الله",
        "وان",
        "تصبهم",
        "سيئة",
        "يقولوا",
        "هذه",
        "من",
        "عندك",
        "قل",
        "كل",
        "من",
        "عند",
        "الله",
        "فمال",
        "هؤلاء",
        "القوم",
        "لا",
        "يكادون",
        "يفقهون",
        "حديثا"
      ],
      "events": [
        {
          "label": "spelling_benign",
          "hyp_words": "اين ما",
          "ref_words": "اينما",
          "hyp_span": [
            0,
            2
          ],
          "ref_span": [
            0,
            1
          ],
          "note": "Proposed teaching equivalence: اين ما / اينما in this clause. Human approval is required; this is not an approved expansion of normalization."
        }
      ]
    }
  ]
}
```

## t17 — Istiadhah outside the ayah

Expected annotation is shown below for review.

```json
{
  "example_id": "t17",
  "name": "Istiadhah outside the ayah",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [
    {
      "text": "أعوذ بالله من الشيطان الرجيم",
      "label": "isti3adha_benign"
    }
  ],
  "chunks": [
    {
      "ayah_id": "090013",
      "transcript": "فك رقبة",
      "reference_text": "فك رقبة",
      "transcript_tokens": [
        "فك",
        "رقبة"
      ],
      "reference_tokens": [
        "فك",
        "رقبة"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```

## t18 — Basmala outside the ayah

Expected annotation is shown below for review.

```json
{
  "example_id": "t18",
  "name": "Basmala outside the ayah",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "",
  "preamble": [
    {
      "text": "بسم الله الرحمن الرحيم",
      "label": "basmala_benign"
    }
  ],
  "chunks": [
    {
      "ayah_id": "090013",
      "transcript": "فك رقبة",
      "reference_text": "فك رقبة",
      "transcript_tokens": [
        "فك",
        "رقبة"
      ],
      "reference_tokens": [
        "فك",
        "رقبة"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```

## t19 — Whole intervening ayah omitted

Constructed scenario: the intended continuous passage was established as 90:12–14 before event annotation. The supplied empty chunk makes this explicit. Do not infer missing ayahs from arbitrary ID gaps.

```json
{
  "example_id": "t19",
  "name": "Whole intervening ayah omitted",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "Constructed scenario: the intended continuous passage was established as 90:12–14 before event annotation. The supplied empty chunk makes this explicit. Do not infer missing ayahs from arbitrary ID gaps.",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090012",
      "transcript": "وما ادراك ما العقبة",
      "reference_text": "وما ادراك ما العقبة",
      "transcript_tokens": [
        "وما",
        "ادراك",
        "ما",
        "العقبة"
      ],
      "reference_tokens": [
        "وما",
        "ادراك",
        "ما",
        "العقبة"
      ],
      "events": [],
      "label": "clean"
    },
    {
      "ayah_id": "090013",
      "transcript": "",
      "reference_text": "فك رقبة",
      "transcript_tokens": [],
      "reference_tokens": [
        "فك",
        "رقبة"
      ],
      "events": [
        {
          "label": "omission_mistake",
          "hyp_words": "",
          "ref_words": "فك رقبة",
          "hyp_span": [
            0,
            0
          ],
          "ref_span": [
            0,
            2
          ],
          "note": "The reviewed intended continuous passage includes this entirely missing ayah."
        }
      ]
    },
    {
      "ayah_id": "090014",
      "transcript": "او اطعام في يوم ذي مسغبة",
      "reference_text": "او اطعام في يوم ذي مسغبة",
      "transcript_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "ذي",
        "مسغبة"
      ],
      "reference_tokens": [
        "او",
        "اطعام",
        "في",
        "يوم",
        "ذي",
        "مسغبة"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```

## t20 — Repeated word already in the reference is clean

وتواصوا occurs twice in the reference; its two matching occurrences are not an extra repetition.

```json
{
  "example_id": "t20",
  "name": "Repeated word already in the reference is clean",
  "review_status": "draft",
  "provenance": "constructed teaching transcript; not a recording",
  "annotation_note": "وتواصوا occurs twice in the reference; its two matching occurrences are not an extra repetition.",
  "preamble": [],
  "chunks": [
    {
      "ayah_id": "090017",
      "transcript": "ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة",
      "reference_text": "ثم كان من الذين امنوا وتواصوا بالصبر وتواصوا بالمرحمة",
      "transcript_tokens": [
        "ثم",
        "كان",
        "من",
        "الذين",
        "امنوا",
        "وتواصوا",
        "بالصبر",
        "وتواصوا",
        "بالمرحمة"
      ],
      "reference_tokens": [
        "ثم",
        "كان",
        "من",
        "الذين",
        "امنوا",
        "وتواصوا",
        "بالصبر",
        "وتواصوا",
        "بالمرحمة"
      ],
      "events": [],
      "label": "clean"
    }
  ]
}
```
