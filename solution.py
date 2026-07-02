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

# Leading invocations that precede a recitation. Istiadha is never a counted
# ayah; basmala is ayah 001001 only in Al-Fatiha. Both shift the anchor offset
# into the previous ayah if left in, so they are stripped before alignment and
# reattached afterwards. Stored as normalized token tuples.
_ISTIADHA = tuple("اعوذ بالله من الشيطان الرجيم".split())
_BASMALA = tuple("بسم الله الرحمن الرحيم".split())


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
            if not re.fullmatch(r"\d{3}", surah_id):
                continue  # skip the 999xxx non-Quran reference block (adhan/duas)
            for ayah in self.quran[surah_id]:
                # Some long ayahs (e.g. Ayat al-Kursi) are stored pre-split with
                # 9-digit sub-ids; the gold uses the 6-digit ayah id, so collapse.
                aid = ayah["id"][:6]
                for tok in norm_tokens(ayah["clean"]):
                    self.corpus_tok.append(tok)
                    self.corpus_id.append(aid)
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

        # Strip leading istiadha, then basmala (each optional). Keep the words to
        # reattach after alignment so the split still reproduces the transcript.
        def strip_prefix(pairs, phrase):
            toks = [n for _, n in pairs]
            if toks[: len(phrase)] == list(phrase):
                return pairs[: len(phrase)], pairs[len(phrase) :]
            return [], pairs
        inv_istiadha, pairs = strip_prefix(pairs, _ISTIADHA)
        inv_basmala, rest = strip_prefix(pairs, _BASMALA)
        had_basmala = bool(inv_basmala)
        lead_words = [w for w, _ in inv_istiadha] + [w for w, _ in inv_basmala]
        pairs = rest
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
        # No leading slack: token 0 should align at best_off, so anything before
        # it belongs to the previous ayah and only leaks spurious ids in.
        lo = max(0, best_off)
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

        # Reattach stripped invocations. In Al-Fatiha, basmala is ayah 001001, so
        # emit it as its own leading segment; otherwise fold the invocation words
        # into the first real ayah (they carry no separate ayah id).
        if lead_words:
            if had_basmala and segments and segments[0]["id"] == "001002":
                segments.insert(0, {"id": "001001", "text": " ".join(lead_words)})
            else:
                segments[0]["text"] = " ".join(lead_words + [segments[0]["text"]])
        return {"ayahs": segments}
