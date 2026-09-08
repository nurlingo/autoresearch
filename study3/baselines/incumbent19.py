"""
B2 - the deployed application's hand-built pipeline, wrapped in the v0.19 contract.

    transcript_cleaner.clean_transcript   repetition / restart / stumble /
                                          wrong-continuation notes
    alignment.evaluate_with_timings       DP word alignment over the cleaned text

The cleaner's notes become benign or corrected events, and the alignment's
remaining S/D/I operations become mistakes. This is the strongest system that
existed before the study, so it is the number an entrant has to beat.

Set FMR_REPO to a checkout of the application repository.
"""
from __future__ import annotations

import logging
import os
import pathlib
import sys

from naive_diff19 import norm  # same agreed normalization

F = os.getenv("FMR_REPO", "")
if F:
    sys.path.insert(0, F)
    os.environ.setdefault("AYAH_JSON_PATH", F + "/backend/quran.json")
os.environ.setdefault("FMR_EVAL_LOG_LEVEL", "ERROR")
logging.disable(logging.CRITICAL)

from backend.worker.services.transcript_cleaner import clean_transcript  # noqa: E402
from backend.worker.services.alignment import evaluate_with_timings  # noqa: E402

# The cleaner's note types, mapped onto v0.19 combined labels.
NOTE_LABEL = {
    "phrase_repetition": "repetition_benign",
    "restart": "repetition_benign",
    "stumble": "substitution_corrected",
    "wrong_continuation": "insertion_mistake",
}


def _back_map(orig: list[str], kept: list[str]) -> list[int]:
    """Index of each surviving token in the original array (the cleaner only deletes)."""
    idx, j = [], 0
    for w in kept:
        while j < len(orig) and norm(orig[j]) != w:
            j += 1
        idx.append(min(j, len(orig) - 1) if orig else 0)
        j += 1
    return idx


class Solution:
    def detect_events(self, chunk: dict) -> list[dict]:
        orig = chunk["transcript_tokens"]
        ref_txt = chunk["reference_text"]
        ayah = {"id": chunk.get("ayah_id", ""), "text": ref_txt, "text_clean": ref_txt}
        events: list[dict] = []

        cleaned_text, notes = clean_transcript(chunk["transcript"], [ayah])
        for n in notes:
            label = NOTE_LABEL.get(n.type)
            if not label:
                continue
            width = max(1, len(n.text.split()))
            start = min(n.position, len(orig))
            events.append({"label": label,
                           "hyp_span": [start, min(start + width, len(orig))],
                           "ref_span": [0, 0]})

        kept = [norm(t) for t in cleaned_text.split()]
        back = _back_map(orig, kept)
        res = evaluate_with_timings(ayah, cleaned_text, None, compare_mode="clean")
        hi, ri = 0, res.get("ref_offset", 0) or 0
        for o in res.get("ops", []):
            op = o["op"]
            if op == "C":
                hi += 1; ri += 1
                continue
            pos = back[hi] if hi < len(back) else len(orig)
            if op == "S":
                events.append({"label": "substitution_mistake",
                               "hyp_span": [pos, pos + 1], "ref_span": [ri, ri + 1]})
                hi += 1; ri += 1
            elif op == "D":
                events.append({"label": "omission_mistake",
                               "hyp_span": [pos, pos], "ref_span": [ri, ri + 1]})
                ri += 1
            elif op == "I":
                events.append({"label": "insertion_mistake",
                               "hyp_span": [pos, pos + 1], "ref_span": [ri, ri]})
                hi += 1
        return _merge(events, len(orig))


def _merge(events: list[dict], n: int) -> list[dict]:
    """Join consecutive same-label events with touching spans, as rubric v0.19
    requires for continuous replacements."""
    out: list[dict] = []
    for e in sorted(events, key=lambda x: (x["hyp_span"][0], x["ref_span"][0])):
        if out and out[-1]["label"] == e["label"] \
                and out[-1]["hyp_span"][1] >= e["hyp_span"][0] \
                and out[-1]["ref_span"][1] >= e["ref_span"][0]:
            p = out[-1]
            p["hyp_span"] = [p["hyp_span"][0], max(p["hyp_span"][1], e["hyp_span"][1])]
            p["ref_span"] = [p["ref_span"][0], max(p["ref_span"][1], e["ref_span"][1])]
        else:
            out.append(dict(e))
    return out
