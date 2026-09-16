# Current constructed teaching examples
These are synthetic examples, never recordings or gold answers. The original twenty examples were approved; this adaptation updates reference spelling and granular grouping under the current rubric. The adaptation is assistant-validated. Do not count scores on exposed teaching answers as held-out evidence.

t10 now repeats the clause context so the corrected substitution is anchored. t11 and t12 separate the changed words from correctly repeated context. t01 now matches the faithful reference exactly.

## t01 — Exact reference match.
Ayah 090001 · chunk 0
Transcript: لا أقسم بهذا البلد
Reference: لا أقسم بهذا البلد

```json
[]
```

## t02 — Missing beginning
Ayah 090004 · chunk 0
Transcript: الإنسان في كبد
Reference: لقد خلقنا الإنسان في كبد

```json
[
  {
    "event_id": "t02:e001",
    "label": "omission_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          0
        ],
        "words": ""
      }
    ],
    "reference": {
      "ayah_id": "090004",
      "span": [
        0,
        2
      ],
      "words": "لقد خلقنا"
    },
    "note": "The two initial reference words are absent."
  }
]
```

## t03 — Missing interior word
Ayah 090014 · chunk 0
Transcript: أو إطعام في يوم مسغبة
Reference: أو إطعام في يوم ذي مسغبة

```json
[
  {
    "event_id": "t03:e001",
    "label": "omission_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          4,
          4
        ],
        "words": ""
      }
    ],
    "reference": {
      "ayah_id": "090014",
      "span": [
        4,
        5
      ],
      "words": "ذي"
    },
    "note": "ذي is missing between يوم and مسغبة."
  }
]
```

## t04 — Missing ending
Ayah 090017 · chunk 0
Transcript: ثم كان من الذين آمنوا وتواصوا بالصبر
Reference: ثم كان من الذين آمنوا وتواصوا بالصبر وتواصوا بالمرحمة

```json
[
  {
    "event_id": "t04:e001",
    "label": "omission_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          7,
          7
        ],
        "words": ""
      }
    ],
    "reference": {
      "ayah_id": "090017",
      "span": [
        7,
        9
      ],
      "words": "وتواصوا بالمرحمة"
    },
    "note": "The last two reference words are absent, even if the recording stops here."
  }
]
```

## t05 — One unresolved replacement
Ayah 090006 · chunk 0
Transcript: يقول أهلكت ذهبا لبدا
Reference: يقول أهلكت مالا لبدا

```json
[
  {
    "event_id": "t05:e001",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          2,
          3
        ],
        "words": "ذهبا"
      }
    ],
    "reference": {
      "ayah_id": "090006",
      "span": [
        2,
        3
      ],
      "words": "مالا"
    },
    "note": "ذهبا replaces مالا."
  }
]
```

## t06 — Adjacent replacements grouped
Ayah 090006 · chunk 0
Transcript: يقول أهلكت كنزا كثيرا
Reference: يقول أهلكت مالا لبدا

```json
[
  {
    "event_id": "t06:e001",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          2,
          4
        ],
        "words": "كنزا كثيرا"
      }
    ],
    "reference": {
      "ayah_id": "090006",
      "span": [
        2,
        4
      ],
      "words": "مالا لبدا"
    },
    "note": "Two continuous replaced words form one event."
  }
]
```

## t07 — Two mistakes separated by correct words
Ayah 090008 · chunk 0
Transcript: هل نجعل له أذنين
Reference: ألم نجعل له عينين

```json
[
  {
    "event_id": "t07:e001",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          1
        ],
        "words": "هل"
      }
    ],
    "reference": {
      "ayah_id": "090008",
      "span": [
        0,
        1
      ],
      "words": "ألم"
    },
    "note": "هل replaces الم."
  },
  {
    "event_id": "t07:e002",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          3,
          4
        ],
        "words": "أذنين"
      }
    ],
    "reference": {
      "ayah_id": "090008",
      "span": [
        3,
        4
      ],
      "words": "عينين"
    },
    "note": "اذنين replaces عينين. The correct words between the changes separate the events."
  }
]
```

## t08 — Extra words
Ayah 090009 · chunk 0
Transcript: ولسانا وعينين وشفتين
Reference: ولسانا وشفتين

```json
[
  {
    "event_id": "t08:e001",
    "label": "insertion_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          1,
          2
        ],
        "words": "وعينين"
      }
    ],
    "reference": {
      "ayah_id": "090009",
      "span": [
        1,
        1
      ],
      "words": ""
    },
    "note": "وعينين is extra material, not a matching repeated phrase or a restatement."
  }
]
```

## t09 — Matching phrase repeated
Ayah 091001 · chunk 0
Transcript: والشمس وضحاها والشمس وضحاها
Reference: والشمس وضحاها

```json
[
  {
    "event_id": "t09:e001",
    "label": "repetition_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          2
        ],
        "words": "والشمس وضحاها"
      },
      {
        "chunk_idx": 0,
        "span": [
          2,
          4
        ],
        "words": "والشمس وضحاها"
      }
    ],
    "reference": {
      "ayah_id": "091001",
      "span": [
        0,
        2
      ],
      "words": "والشمس وضحاها"
    },
    "note": ""
  }
]
```

## t10 — Wrong then correct
Ayah 091002 · chunk 0
Transcript: والشمس إذا تلاها والقمر إذا تلاها
Reference: والقمر إذا تلاها

```json
[
  {
    "event_id": "t10:e001",
    "label": "substitution_corrected",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          1
        ],
        "words": "والشمس"
      },
      {
        "chunk_idx": 0,
        "span": [
          3,
          4
        ],
        "words": "والقمر"
      }
    ],
    "reference": {
      "ayah_id": "091002",
      "span": [
        0,
        1
      ],
      "words": "والقمر"
    },
    "note": "Repeated matching clause context establishes the two attempts."
  },
  {
    "event_id": "t10:e002",
    "label": "repetition_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          1,
          3
        ],
        "words": "إذا تلاها"
      },
      {
        "chunk_idx": 0,
        "span": [
          4,
          6
        ],
        "words": "إذا تلاها"
      }
    ],
    "reference": {
      "ayah_id": "091002",
      "span": [
        1,
        3
      ],
      "words": "إذا تلاها"
    },
    "note": ""
  }
]
```

## t11 — Correct then wrong on restatement
Ayah 091003 · chunk 0
Transcript: والنهار إذا جلاها والليل إذا جلاها
Reference: والنهار إذا جلاها

```json
[
  {
    "event_id": "t11:e001",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          1
        ],
        "words": "والنهار"
      },
      {
        "chunk_idx": 0,
        "span": [
          3,
          4
        ],
        "words": "والليل"
      }
    ],
    "reference": {
      "ayah_id": "091003",
      "span": [
        0,
        1
      ],
      "words": "والنهار"
    },
    "note": "First correct, then wrong; final attempt remains wrong."
  },
  {
    "event_id": "t11:e002",
    "label": "repetition_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          1,
          3
        ],
        "words": "إذا جلاها"
      },
      {
        "chunk_idx": 0,
        "span": [
          4,
          6
        ],
        "words": "إذا جلاها"
      }
    ],
    "reference": {
      "ayah_id": "091003",
      "span": [
        1,
        3
      ],
      "words": "إذا جلاها"
    },
    "note": ""
  }
]
```

## t12 — Omission restored on restart
Ayah 090014 · chunk 0
Transcript: أو إطعام في يوم مسغبة أو إطعام في يوم ذي مسغبة
Reference: أو إطعام في يوم ذي مسغبة

```json
[
  {
    "event_id": "t12:e001",
    "label": "omission_corrected",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          4,
          4
        ],
        "words": ""
      },
      {
        "chunk_idx": 0,
        "span": [
          9,
          10
        ],
        "words": "ذي"
      }
    ],
    "reference": {
      "ayah_id": "090014",
      "span": [
        4,
        5
      ],
      "words": "ذي"
    },
    "note": ""
  },
  {
    "event_id": "t12:e002",
    "label": "repetition_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          4
        ],
        "words": "أو إطعام في يوم"
      },
      {
        "chunk_idx": 0,
        "span": [
          5,
          9
        ],
        "words": "أو إطعام في يوم"
      }
    ],
    "reference": {
      "ayah_id": "090014",
      "span": [
        0,
        4
      ],
      "words": "أو إطعام في يوم"
    },
    "note": ""
  },
  {
    "event_id": "t12:e003",
    "label": "repetition_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          4,
          5
        ],
        "words": "مسغبة"
      },
      {
        "chunk_idx": 0,
        "span": [
          10,
          11
        ],
        "words": "مسغبة"
      }
    ],
    "reference": {
      "ayah_id": "090014",
      "span": [
        5,
        6
      ],
      "words": "مسغبة"
    },
    "note": ""
  }
]
```

## t13 — Complete spoken letter names
Ayah 026001 · chunk 0
Transcript: طا سين ميم
Reference: طسم

```json
[
  {
    "event_id": "t13:e001",
    "label": "letters_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          3
        ],
        "words": "طا سين ميم"
      }
    ],
    "reference": {
      "ayah_id": "026001",
      "span": [
        0,
        1
      ],
      "words": "طسم"
    },
    "note": "The three spoken letter names express طسم in order."
  }
]
```

## t14 — Incomplete spoken letter names
Ayah 026001 · chunk 0
Transcript: طا سين
Reference: طسم

```json
[
  {
    "event_id": "t14:e001",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          2
        ],
        "words": "طا سين"
      }
    ],
    "reference": {
      "ayah_id": "026001",
      "span": [
        0,
        1
      ],
      "words": "طسم"
    },
    "note": "The one-token reference sequence طسم lacks its final ميم in the hypothesis; use the one-token substitution convention."
  }
]
```

## t15 — Contextual word boundary is benign
Ayah 004078 · chunk 0
Transcript: أين ما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وإن تصبهم حسنة يقولوا هذه من عند الله وإن تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا
Reference: أينما تكونوا يدرككم الموت ولو كنتم في بروج مشيدة وإن تصبهم حسنة يقولوا هذه من عند الله وإن تصبهم سيئة يقولوا هذه من عندك قل كل من عند الله فمال هؤلاء القوم لا يكادون يفقهون حديثا

```json
[
  {
    "event_id": "t15:e001",
    "label": "spelling_benign",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          0,
          2
        ],
        "words": "أين ما"
      }
    ],
    "reference": {
      "ayah_id": "004078",
      "span": [
        0,
        1
      ],
      "words": "أينما"
    },
    "note": "Proposed teaching equivalence: اين ما / اينما in this clause. Human approval is required; this is not an approved expansion of normalization."
  }
]
```

## t16 — Istiadhah outside the ayah
Ayah None · chunk -1
Transcript: أعوذ بالله من الشيطان الرجيم
Reference: ∅

Ayah 090013 · chunk 0
Transcript: فك رقبة
Reference: فك رقبة

```json
[
  {
    "event_id": "t16:e001",
    "label": "isti3adha_benign",
    "hyp_locations": [
      {
        "chunk_idx": -1,
        "span": [
          0,
          5
        ],
        "words": "أعوذ بالله من الشيطان الرجيم"
      }
    ],
    "reference": {
      "ayah_id": null,
      "span": [
        0,
        0
      ],
      "words": ""
    },
    "note": ""
  }
]
```

## t17 — Basmala outside the ayah
Ayah None · chunk -1
Transcript: بسم الله الرحمن الرحيم
Reference: ∅

Ayah 090013 · chunk 0
Transcript: فك رقبة
Reference: فك رقبة

```json
[
  {
    "event_id": "t17:e001",
    "label": "basmala_benign",
    "hyp_locations": [
      {
        "chunk_idx": -1,
        "span": [
          0,
          4
        ],
        "words": "بسم الله الرحمن الرحيم"
      }
    ],
    "reference": {
      "ayah_id": null,
      "span": [
        0,
        0
      ],
      "words": ""
    },
    "note": ""
  }
]
```

## t18 — Whole intervening ayah omitted
Ayah 090012 · chunk 0
Transcript: وما أدراك ما العقبة
Reference: وما أدراك ما العقبة

Ayah 090013 · chunk 1
Transcript: ∅
Reference: فك رقبة

Ayah 090014 · chunk 2
Transcript: أو إطعام في يوم ذي مسغبة
Reference: أو إطعام في يوم ذي مسغبة

```json
[
  {
    "event_id": "t18:e001",
    "label": "omission_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 1,
        "span": [
          0,
          0
        ],
        "words": ""
      }
    ],
    "reference": {
      "ayah_id": "090013",
      "span": [
        0,
        2
      ],
      "words": "فك رقبة"
    },
    "note": "The reviewed intended continuous passage includes this entirely missing ayah."
  }
]
```

## t19 — Repeated word already in the reference is clean
Ayah 090017 · chunk 0
Transcript: ثم كان من الذين آمنوا وتواصوا بالصبر وتواصوا بالمرحمة
Reference: ثم كان من الذين آمنوا وتواصوا بالصبر وتواصوا بالمرحمة

```json
[]
```

## t20 — Two different errors in one ayah
Ayah 090017 · chunk 0
Transcript: ثم كان الذين آمنوا وتواصوا بالصبر وتواصوا بالرحمة
Reference: ثم كان من الذين آمنوا وتواصوا بالصبر وتواصوا بالمرحمة

```json
[
  {
    "event_id": "t20:e001",
    "label": "omission_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          2,
          2
        ],
        "words": ""
      }
    ],
    "reference": {
      "ayah_id": "090017",
      "span": [
        2,
        3
      ],
      "words": "من"
    },
    "note": ""
  },
  {
    "event_id": "t20:e002",
    "label": "substitution_mistake",
    "hyp_locations": [
      {
        "chunk_idx": 0,
        "span": [
          7,
          8
        ],
        "words": "بالرحمة"
      }
    ],
    "reference": {
      "ayah_id": "090017",
      "span": [
        8,
        9
      ],
      "words": "بالمرحمة"
    },
    "note": ""
  }
]
```

