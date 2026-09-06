"""
solution.py — the ONLY file the agent edits (Stage 2).

Contract:
    Solution().detect_events(chunk_text: str, reference_text: str, ctx: dict) -> list[dict]
ctx = {"ayah_id", "chunk_idx", "n_chunks", "is_last_chunk"} — the chunk's position in its recording.
Each event: {"type": <taxonomy type>, "verdict": "benign"|"corrected"|"mistake"|"uncertain",
             "hyp_span": [i, j], "ref_span": [a, b] | None}
Spans index eval.canon(chunk_text) / eval.canon(reference_text).
The Quran reference is available in ../data/quran_ref.json if needed.

Starting point: the empty stub (flags nothing; scores 2.0).
"""


class Solution:
    def detect_events(self, chunk_text: str, reference_text: str, ctx: dict) -> list[dict]:
        return []
