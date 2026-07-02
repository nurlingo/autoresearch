"""
solution.py — transcript-only ayah detection + split.

Approach (corpus alignment):
  1. Build a global token corpus over the whole Quran: a flat list of normalized
     tokens, each tagged with its ayah id, in surah/ayah order.
  2. Normalize the transcript the same way, keeping a map back to original words.
  3. Anchor: vote for the corpus offset (corpus_pos - transcript_pos) using shared
     token n-grams. A contiguous recitation aligns at one dominant offset.
  4. Align the transcript tokens to the corpus window around that offset with
     difflib, assigning each transcript token the ayah id of the corpus token it
     matched (carry-forward for unmatched tokens).
  5. Group consecutive original words by assigned ayah id -> split; unique ids in
     order -> detection. Abstain when the anchor match is too weak.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))

_HARAKAT_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء", "ة": "ه"}
_NONARAB_RE = re.compile(r"[^ء-ي ]")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    text = _HARAKAT_RE.sub("", text)
    for a, b in _FOLD.items():
        text = text.replace(a, b)
    text = _NONARAB_RE.sub(" ", text)
    return text


def norm_tokens(text: str) -> list[str]:
    return normalize(text).split()


class Solution:
    def __init__(self) -> None:
        self.quran: dict[str, list[dict[str, str]]] = json.loads(
            REF_PATH.read_text(encoding="utf-8")
        )
        # Flat corpus of (token, ayah_id) in surah/ayah order.
        self.corpus_tok: list[str] = []
        self.corpus_id: list[str] = []
        for surah_id in sorted(self.quran):
            for ayah in self.quran[surah_id]:
                for tok in norm_tokens(ayah["clean"]):
                    self.corpus_tok.append(tok)
                    self.corpus_id.append(ayah["id"])
        # Bigram anchor index: bigram -> list of corpus start positions.
        self.bigram: dict[tuple[str, str], list[int]] = {}
        for i in range(len(self.corpus_tok) - 1):
            key = (self.corpus_tok[i], self.corpus_tok[i + 1])
            self.bigram.setdefault(key, []).append(i)

    def process(self, transcript: str) -> dict:
        words = transcript.split()
        # (original_word, normalized_token) keeping only tokens with content.
        pairs = [(w, normalize(w).replace(" ", "")) for w in words]
        pairs = [(w, n) for w, n in pairs if n]
        if len(pairs) < 2:
            return {"abstain": True}
        tnorm = [n for _, n in pairs]

        # --- anchor: vote for corpus offset via shared bigrams ---
        votes: dict[int, int] = {}
        for j in range(len(tnorm) - 1):
            for pos in self.bigram.get((tnorm[j], tnorm[j + 1]), ()):
                off = pos - j
                votes[off] = votes.get(off, 0) + 1
        if not votes:
            return {"abstain": True}
        best_off = max(votes, key=lambda o: votes[o])
        votes_best = votes[best_off]
        # Weak anchor -> not a recognizable recitation.
        if votes_best < max(2, 0.15 * (len(tnorm) - 1)):
            return {"abstain": True}

        # --- align transcript tokens to corpus window around best_off ---
        n = len(tnorm)
        lo = max(0, best_off - 5)
        hi = min(len(self.corpus_tok), best_off + n + 5)
        win_tok = self.corpus_tok[lo:hi]
        win_id = self.corpus_id[lo:hi]

        matcher = SequenceMatcher(a=tnorm, b=win_tok, autojunk=False)
        assigned: list[str | None] = [None] * n
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    assigned[i1 + k] = win_id[j1 + k]
        # carry-forward / back-fill unmatched tokens
        last = None
        for i in range(n):
            if assigned[i] is None:
                assigned[i] = last
            else:
                last = assigned[i]
        first = next((a for a in assigned if a is not None), None)
        for i in range(n):
            if assigned[i] is None:
                assigned[i] = first
        if first is None:
            return {"abstain": True}

        # --- group original words by assigned ayah id ---
        segments: list[dict[str, str]] = []
        for (orig, _), aid in zip(pairs, assigned):
            if segments and segments[-1]["id"] == aid:
                segments[-1]["text"] += " " + orig
            else:
                segments.append({"id": aid, "text": orig})
        return {"ayahs": segments}
