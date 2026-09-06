"""Baseline B1 — naive diff: canonicalize, SequenceMatcher against the reference,
every non-equal opcode is a `mistake`. No repetition handling, no uncertainty.
This is what a plain WER-style comparison flags — the design the product moved
away from because it over-flags benign recitation behaviour."""
from difflib import SequenceMatcher
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from eval import canon


class Solution:
    def detect_events(self, chunk_text, reference_text, ctx):
        h, r = canon(chunk_text), canon(reference_text)
        out = []
        for tag, a, b, i, j in SequenceMatcher(a=r, b=h, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            typ = {"replace": "substitution", "delete": "omission", "insert": "insertion"}[tag]
            if tag == "delete" and b == len(r):
                typ = "truncation"
            out.append({"type": typ, "verdict": "mistake", "hyp_span": [i, j], "ref_span": [a, b]})
        return out
