# Hamza and contextual spelling — 2026-09-15

This is the current working annotation policy, separate from the frozen experimental release and its scores.

## Distinguish alignment from equivalence

The legacy clean reference folds أ, إ and آ to ا. It is useful for locating candidate correspondences but cannot establish that a written difference is benign. The application's `quran.json` also has vocalized `titles.ar`; use that evidence at the same ayah/word positions. The current `reference_text` is the hamza-preserving view; legacy folded text and raw source provenance remain private for traceability. A lexical alignment produced by lossy normalization is not a pronunciation verdict.

1. Preserve explicit **initial أ versus إ**, including after attached particles. They can distinguish different word forms/vowels. Above-alif hamza alone does not distinguish /a/ from /u/; do not infer an unwritten vowel.
2. Preserve **madda**. Do not generally identify آ with ا or أ. Contextually accepted orthography needs an explicit justification.
3. Preserve **wasl versus qat3** as a reading distinction. But an unvowelled plain ا in a transcript may simply omit hamza notation. It does not prove the writer intended wasl. The owner has settled the convention: annotate missing written hamza with plain alif as `spelling_benign`. Do not manufacture a wasl pronunciation from omitted notation.
4. **Medial/final hamza seat variants** can be benign when they represent the same hamza and do not change an explicitly supplied vowel or other pronounced segment. This is a contextual word correspondence, not a global ء/ئ/ؤ/أ/إ replacement table. Initial above/below hamza must not disappear through this rule.
5. Previously accepted silent letters or connected-reading spellings remain contextual. Missing written wasl in connected recitation does not imply that qat3 may also be deleted. Explicitly changing a pronounced consonant or vowel remains a mistake.

The [Quranic Arabic Corpus orthography model](https://corpus.quran.com/java/orthographymodel.jsp) represents hamza-above, hamza-below, madda, wasl and vowel marks separately. Its [phonetic documentation](https://corpus.quran.com/documentation/phonetic.jsp) also emphasizes contextual pronunciation. The specific annotation decisions here are our working rubric, not assertions that every orthographic difference proves an audio error.

## Completed audit

All 188 working recordings were scanned against the vocalized reference at aligned word positions. Eight initial above/below-hamza occurrences in six recordings were hidden by the old folding. Seven new substitution events were added; one existing contiguous substitution was enlarged. The owner approved all thirteen reviewed recordings’ hamza decisions: eight substitution events and seven benign spelling events. Five bare-alif spellings now have explicit spelling events, one final-seat spelling event is approved, and the previously accepted madda correspondence is reaffirmed. No hamza questions remain. This is event-level approval, not approval of unrelated draft annotations.

The latest consistency review restores granular grouping for parallel-passage replacements and treats unanchored opening fragments as insertions. The broader passage interpretation is kept as a note only; the owner-approved boundary correction remains. The 188-case checkpoint after adjudication had 452 events, including 43 repetition events with 89 explicitly linked occurrences. Unit count and recording text are unchanged; one reviewed boundary moves two words between adjacent ayahs.

Actual case IDs, transcripts and annotation answers remain in the private review bundle. The public repository contains the policy and aggregate findings only. The historical frozen releases retain their original reference. Current input preparation supplies hamza-preserving `reference_text` and `study3/quran-reference.json` to the agent, so these distinctions are available at inference time.

## Owner adjudication

Missing hamza notation on alif is benign spelling. Medial/final above-versus-below seat variation is also benign when it preserves the same word and other explicit pronunciation-bearing information. Initial أ / إ remains distinct. The individually reaffirmed madda correspondence does not license a global madda normalization. All affected data points carry owner approval, date and the exact localized words.

The intermediate six-case extension reached 194 cases. Later additions and withdrawals produced the intermediate **195-case, 98-train/97-gold** edition, followed by the approved **200-case, 100/100** freeze. The 15-event hamza approval describes that specific audit, not approval of subsequent additions. See [current state](../CURRENT-STATE.md).
