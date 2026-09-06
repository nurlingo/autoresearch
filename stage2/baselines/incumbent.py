"""Baseline B2 — the incumbent production stack of the follow_my_reading app,
wrapped in the Stage-2 contract:

    transcript_cleaner.clean_transcript   (phrase repetition / restart / stumble /
                                           wrong-continuation notes -> benign|corrected events)
    alignment.evaluate_with_timings       (DP word alignment; S/D/I ops -> mistake events)

Set FMR_REPO to the follow_my_reading checkout (default: sibling directory).
Requires only the pure-python service modules (no API keys, no audio).
"""
from __future__ import annotations

import os
import sys
import logging
import pathlib

F = os.getenv("FMR_REPO", str(pathlib.Path(__file__).resolve().parents[3] / "follow_my_reading"))
sys.path.insert(0, F)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("AYAH_JSON_PATH", F + "/backend/quran.json")
os.environ.setdefault("FMR_EVAL_LOG_LEVEL", "ERROR")
logging.disable(logging.CRITICAL)

from backend.worker.services.transcript_cleaner import clean_transcript  # noqa: E402
from backend.worker.services.alignment import evaluate_with_timings  # noqa: E402
from eval import canon  # noqa: E402

NOTE_TYPE = {"phrase_repetition": ("restart_repeat", "benign"), "restart": ("restart_repeat", "benign"),
             "stumble": ("self_correction", "corrected"), "wrong_continuation": ("insertion", "mistake")}
OP_TYPE = {"S": "substitution", "D": "omission", "I": "insertion"}


def _map_cleaned_to_orig(orig: list[str], cleaned: list[str]) -> list[int]:
    """cleaned is a subsequence of orig (the cleaner only deletes words)."""
    idx, j = [], 0
    for w in cleaned:
        while j < len(orig) and orig[j] != w:
            j += 1
        idx.append(min(j, len(orig) - 1) if orig else 0)
        j += 1
    return idx


class Solution:
    def detect_events(self, chunk_text: str, reference_text: str, ctx: dict) -> list[dict]:
        ayah = {"id": ctx.get("ayah_id", ""), "text": reference_text, "text_clean": reference_text}
        orig = canon(chunk_text)
        events: list[dict] = []
        cleaned_text, notes = clean_transcript(chunk_text, [ayah])
        for n in notes:
            typ, verdict = NOTE_TYPE.get(n.type, ("asr_garble", "uncertain"))
            k = max(1, len(canon(n.text)))
            events.append({"type": typ, "verdict": verdict, "hyp_span": [n.position, min(n.position + k, len(orig))], "ref_span": None})
        cleaned = canon(cleaned_text)
        back = _map_cleaned_to_orig(orig, cleaned)
        res = evaluate_with_timings(ayah, cleaned_text, None, compare_mode="clean")
        ops = res.get("ops", [])
        ref_off = res.get("ref_offset", 0) or 0
        hi, ri = 0, ref_off
        for o in ops:
            op = o["op"]
            if op == "C":
                hi += 1; ri += 1
                continue
            if op == "S":
                hs = [back[hi], back[hi] + 1] if hi < len(back) else [len(orig), len(orig)]
                events.append({"type": "substitution", "verdict": "mistake", "hyp_span": hs, "ref_span": [ri, ri + 1]})
                hi += 1; ri += 1
            elif op == "D":
                pos = back[hi] if hi < len(back) else len(orig)
                typ = "truncation" if hi >= len(back) else "omission"
                if typ == "truncation" and ctx.get("is_last_chunk"):
                    events.append({"type": typ, "verdict": "benign", "hyp_span": [pos, pos], "ref_span": [ri, ri + 1]})
                else:
                    events.append({"type": typ, "verdict": "mistake", "hyp_span": [pos, pos], "ref_span": [ri, ri + 1]})
                ri += 1
            elif op == "I":
                hs = [back[hi], back[hi] + 1] if hi < len(back) else [len(orig), len(orig)]
                events.append({"type": "insertion", "verdict": "mistake", "hyp_span": hs, "ref_span": None})
                hi += 1
        return events
