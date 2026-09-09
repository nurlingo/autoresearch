"""Production cleaner/alignment components adapted to original-token event spans.

The application does not implement the v0.19 event API. This adapter preserves
removed-token identities, restores reference offsets, and maps cleaner notes to
reference locations and both attempts. It is an adapted baseline, not a direct
measurement of all deployed application behavior. No gold data is consulted.
"""
from __future__ import annotations

import logging
import os
import sys

F = os.getenv("FMR_REPO", "")
if F:
    sys.path.insert(0, F)
    os.environ.setdefault("AYAH_JSON_PATH", F + "/backend/quran.json")
os.environ.setdefault("FMR_EVAL_LOG_LEVEL", "ERROR")
logging.disable(logging.CRITICAL)

from backend.worker.services.transcript_cleaner import clean_transcript
from backend.worker.services.alignment import (
    normalize_ar, align_words, _find_best_ref_offset,
    _adjust_ops_for_repetitions, _fix_merged_split_words,
)


def _normalized(tokens, positions=None):
    """Track every production-normalized token back to a supplied raw token."""
    words, back = [], []
    for i in positions if positions is not None else range(len(tokens)):
        for word in normalize_ar(tokens[i]).split():
            words.append(word)
            back.append(i)
    return words, back


def _removed_tokens(orig, cleaned, notes):
    removed, note_positions = set(), []
    for note in notes:
        indices, cursor = [], note.position
        for word in note.text.split():
            while cursor < len(orig) and (cursor in removed or orig[cursor] != word):
                cursor += 1
            if cursor == len(orig):
                raise ValueError("Cleaner note cannot be mapped to original tokens")
            indices.append(cursor)
            cursor += 1
        removed.update(indices)
        note_positions.append(indices)
    kept = [i for i in range(len(orig)) if i not in removed]
    if [orig[i] for i in kept] != cleaned.split():
        raise ValueError("Cleaner output differs from its recorded removals")
    return kept, note_positions


def _span(indices):
    return [min(indices), max(indices) + 1]


class Solution:
    def detect_events(self, chunk: dict) -> list[dict]:
        orig, refs = chunk["transcript_tokens"], chunk["reference_tokens"]
        ayah = {"id": chunk.get("ayah_id"), "text": chunk["reference_text"],
                "text_clean": chunk["reference_text"]}
        cleaned, notes = clean_transcript(chunk["transcript"], [ayah])
        kept, removed_per_note = _removed_tokens(orig, cleaned, notes)
        hyp, hmap = _normalized(orig, kept)
        ref, rmap = _normalized(refs)
        offset = _find_best_ref_offset(ref, hyp)
        raw_ops, _ = align_words(ref[offset:], hyp)
        ops = _fix_merged_split_words(_adjust_ops_for_repetitions(raw_ops))
        # Use the indices returned by production alignment; operation counts
        # lose positions whenever its postprocessors drop or merge operations.
        surviving_ref = {}
        for op, _, _, ri, hi in raw_ops:
            if ri is not None and hi is not None:
                surviving_ref[hmap[hi]] = rmap[ri + offset]
        events = []
        h_cursor, r_cursor = 0, offset
        for op, _, _, ri, hi in ops:
            hpos = hmap[hi] if hi is not None else (hmap[h_cursor] if h_cursor < len(hmap) else len(orig))
            rpos = rmap[ri + offset] if ri is not None else (rmap[r_cursor] if r_cursor < len(rmap) else len(refs))
            if op in ("S", "D", "I"):
                events.append({"label": {"S": "substitution_mistake", "D": "omission_mistake", "I": "insertion_mistake"}[op],
                               "hyp_span": [hpos, hpos + (op != "D")],
                               "ref_span": [rpos, rpos + (op != "I")]})
            if hi is not None:
                h_cursor = hi + 1
            if ri is not None:
                r_cursor = ri + offset + 1
        # Preserve the production policy: its partial-reference offset omits
        # initial words from scoring. Do not silently improve that policy here.
        repair_events = []
        for note, removed in zip(notes, removed_per_note):
            if not removed:
                continue
            after = [i for i in kept if i > removed[-1]]
            anchor = surviving_ref.get(after[0], len(refs)) if after else len(refs)
            label = {"phrase_repetition": "repetition_benign", "restart": "repetition_benign",
                     "stumble": "substitution_corrected", "wrong_continuation": "insertion_mistake"}.get(note.type)
            target = []
            if label == "repetition_benign":
                phrase = [normalize_ar(orig[i]) for i in removed]
                for j in range(len(after) - len(phrase) + 1):
                    window = after[j:j + len(phrase)]
                    if [normalize_ar(orig[i]) for i in window] == phrase:
                        target = window
                        break
            elif label == "substitution_corrected":
                # The source note supplies only the removed fragment. The
                # explicit adapter convention pairs it with the next equally
                # many surviving words, provided they form a matching repair.
                target = after[:len(removed)]
            mapped = [surviving_ref.get(i) for i in target]
            matching_target = (target and len(target) == len(removed)
                               and all(i is not None for i in mapped)
                               and mapped == list(range(mapped[0], mapped[0] + len(mapped)))
                               and all(normalize_ar(orig[h]) == normalize_ar(refs[r])
                                       for h, r in zip(target, mapped)))
            if label in {"repetition_benign", "substitution_corrected"} and matching_target:
                repair_events.append({"label": label, "hyp_span": _span(removed + target), "ref_span": _span(mapped)})
            else:
                # A removed fragment without an identifiable matching repair
                # stays extra text; never invent an empty-reference correction.
                events.append({"label": "insertion_mistake", "hyp_span": _span(removed), "ref_span": [anchor, anchor]})
        # Identical repeats can produce one note per extra copy. Combine their
        # shared final attempt without absorbing independent alignment errors.
        combined = []
        for event in sorted(repair_events, key=lambda e: e['hyp_span']):
            if combined and combined[-1]['label'] == event['label'] and combined[-1]['ref_span'] == event['ref_span'] and combined[-1]['hyp_span'][1] > event['hyp_span'][0]:
                combined[-1]['hyp_span'][1] = max(combined[-1]['hyp_span'][1], event['hyp_span'][1])
            else:
                combined.append(event)
        return sorted(_merge(events) + combined, key=lambda e: (e['hyp_span'], e['ref_span'], e['label']))


def _merge(events):
    out = []
    for event in sorted(events, key=lambda e: (e['hyp_span'], e['ref_span'])):
        if out and out[-1]['label'] == event['label'] and out[-1]['hyp_span'][1] == event['hyp_span'][0] and out[-1]['ref_span'][1] == event['ref_span'][0]:
            out[-1]['hyp_span'][1] = event['hyp_span'][1]
            out[-1]['ref_span'][1] = event['ref_span'][1]
        else:
            out.append(dict(event))
    return out
