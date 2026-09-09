"""
B1 - naive diff under taxonomy v0.19.

Normalize both token lists with this baseline's fixed comparison rules, align with
SequenceMatcher, and call every non-equal opcode a mistake:
    replace -> substitution_mistake
    delete  -> omission_mistake     (reference material absent from the transcript)
    insert  -> insertion_mistake    (extra transcript material)

It has no notion of repetition, self-correction, letter names, opening formulas
or accepted spellings, so it is the reference point for how much the benign
categories actually cost. Spans are half-open indices into the ORIGINAL token
arrays; normalization only affects comparison.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Algorithm-specific comparison choices, not additions to the approved rubric.
# In particular this baseline folds ta marbuta to ha; the gold remains unchanged.
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء", "ة": "ه"}
_HARAKAT = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_PUNCT = re.compile(r"[^\w؀-ۿ]+", re.UNICODE)


def norm(tok: str) -> str:
    t = unicodedata.normalize("NFKC", tok or "").replace("ـ", "")
    for a, b in _FOLD.items():
        t = t.replace(a, b)
    return _PUNCT.sub("", _HARAKAT.sub("", t))


class Solution:
    def detect_events(self, chunk: dict) -> list[dict]:
        hyp = [norm(t) for t in chunk["transcript_tokens"]]
        ref = [norm(t) for t in chunk["reference_tokens"]]
        out = []
        for tag, a, b, i, j in SequenceMatcher(a=ref, b=hyp, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            label = {"replace": "substitution_mistake",
                     "delete": "omission_mistake",
                     "insert": "insertion_mistake"}[tag]
            out.append({"label": label, "hyp_span": [i, j], "ref_span": [a, b]})
        return out
