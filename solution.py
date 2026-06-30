"""
solution.py — transcript-only Quran recitation detector + splitter (Stage 1).

Given a recitation transcript (no harakat), decide which ayahs were recited and
split the transcript by ayah. Approach:

  1. Normalize transcript and reference the same way (fold orthographic variants,
     drop harakat) so they match.
  2. Concatenate every reference ayah into one global token stream G with a
     parallel ayah-id array. Index G by token-bigram.
  3. Anchor the transcript onto G by offset voting (which diagonal of G do the
     transcript's bigrams agree on).
  4. Align the transcript tokens to the anchored window of G to label each
     transcript word with an ayah id, then group consecutive labels into segments.
  5. Abstain when the transcript does not align well to any part of the Quran.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))

# Mirror eval.canon so the algorithm's normalization matches the metric's.
_HARAKAT_RE = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا",
         "ٱ": "ا", "ى": "ي", "ؤ": "ء",
         "ئ": "ء"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    for a, b in _FOLD.items():
        text = text.replace(a, b)
    return _HARAKAT_RE.sub("", text)


def norm_tokens(text: str) -> list[str]:
    return normalize(text).split()


# Abstain when fewer than this fraction of transcript bigrams agree on the anchor.
MIN_COVERAGE = 0.30
WINDOW_PAD = 6
# Bigrams with more postings than this are too ambiguous to vote with.
MAX_POSTINGS = 300
_TAAWWUDH_HEADS = {"اعوذ", "تعوذ", "استعيذ"}


class Solution:
    def __init__(self) -> None:
        self.quran: dict[str, list[dict[str, str]]] = json.loads(
            REF_PATH.read_text(encoding="utf-8")
        )
        self.g_tokens: list[str] = []
        self.g_ids: list[str] = []
        for surah in sorted(self.quran):
            # Keep only real Quran surahs (001-114); skip the 999* adhan/dua extras.
            if not (surah.isdigit() and len(surah) == 3 and 1 <= int(surah) <= 114):
                continue
            for ayah in self.quran[surah]:
                # Long ayahs are split into 9-digit sub-ids; the ayah is id[:6].
                aid = ayah["id"][:6]
                for tok in norm_tokens(ayah.get("clean", "")):
                    self.g_tokens.append(tok)
                    self.g_ids.append(aid)
        self.bindex: dict[tuple[str, str], list[int]] = {}
        for i in range(len(self.g_tokens) - 1):
            self.bindex.setdefault((self.g_tokens[i], self.g_tokens[i + 1]), []).append(i)

    def _anchor(self, toks: list[str]) -> tuple[int, float]:
        """Return (best_offset, coverage) anchoring toks onto G by bigram voting."""
        votes: Counter[int] = Counter()
        n_bigrams = max(len(toks) - 1, 1)
        for i in range(len(toks) - 1):
            postings = self.bindex.get((toks[i], toks[i + 1]))
            if not postings or len(postings) > MAX_POSTINGS:
                continue
            for p in postings:
                votes[p - i] += 1
        if not votes:
            return -1, 0.0
        best_offset, score = votes.most_common(1)[0]
        return best_offset, score / n_bigrams

    def process(self, transcript: str) -> dict:
        raw_words = (transcript or "").split()
        toks = [normalize(w) for w in raw_words]
        # Drop a leading taawwudh ("اعوذ بالله من الشيطان الرجيم"): it is never a
        # Quran ayah, and as a prefix it both drags down the anchor coverage and
        # bleeds into a neighbouring ayah. (Basmala is kept — it is Al-Fatiha 1.)
        if toks and toks[0] in _TAAWWUDH_HEADS:
            for j in range(min(len(toks), 8) - 1, 0, -1):
                if toks[j] == "الرجيم":
                    raw_words = raw_words[j + 1:]
                    toks = toks[j + 1:]
                    break
        if len(toks) < 2:
            return {"abstain": True}

        best_offset, coverage = self._anchor(toks)
        if best_offset < 0 or coverage < MIN_COVERAGE:
            return {"abstain": True}

        # No backward pad: the anchor maps transcript index 0 to G[best_offset], so
        # any leading liturgical prefix (taawwudh/basmala) would otherwise bleed
        # into the *previous* surah's last ayah. Pad only forward.
        lo = best_offset
        hi = min(len(self.g_tokens), best_offset + len(toks) + WINDOW_PAD)
        win_tok = self.g_tokens[lo:hi]
        win_ids = self.g_ids[lo:hi]

        sm = SequenceMatcher(a=toks, b=win_tok, autojunk=False)
        tok_id: list[str | None] = [None] * len(toks)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    tok_id[i1 + k] = win_ids[j1 + k]

        matched = [i for i, t in enumerate(tok_id) if t is not None]
        if not matched:
            return {"abstain": True}

        # Clamp unmatched leading/trailing tokens to the first/last *matched* ayah
        # (so prefix/suffix noise never invents a neighbouring ayah), then
        # forward-fill internal gaps.
        first, last_i = matched[0], matched[-1]
        for i in range(first):
            tok_id[i] = tok_id[first]
        for i in range(last_i + 1, len(tok_id)):
            tok_id[i] = tok_id[last_i]
        last = None
        for i in range(len(tok_id)):
            if tok_id[i] is None:
                tok_id[i] = last
            else:
                last = tok_id[i]

        # Group consecutive same-id raw words into ayah segments.
        segments: list[dict[str, str]] = []
        for word, aid in zip(raw_words, tok_id):
            if aid is None:
                continue
            if segments and segments[-1]["id"] == aid:
                segments[-1]["text"] += " " + word
            else:
                segments.append({"id": aid, "text": word})

        if not segments:
            return {"abstain": True}
        return {"ayahs": segments}
