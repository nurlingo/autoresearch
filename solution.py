"""
solution.py — transcript-only Quran recitation detector + splitter (Stage 1).

Given a recitation transcript (no harakat), decide which ayahs were recited and
split the transcript by ayah. Abstain on non-Quran input.

Approach
--------
1. Normalize transcript + reference words with the same canonicalizer the metric
   uses (fold orthographic variants, drop harakat/tatweel).
2. Anchor: IDF-weighted word voting picks the most likely surah(s).
3. Align: semi-global (free end-gaps on the reference) Needleman-Wunsch aligns the
   transcript tokens to the surah's reference tokens, which carry ayah ids.
4. Split: each transcript word inherits the ayah id of the reference word it
   aligned to (gaps carry the previous id). Consecutive words are grouped.
5. Abstain when the best alignment is too weak to be a recitation.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import defaultdict
from math import log
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))

_HARAKAT_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء"}


def normalize(text: str) -> list[str]:
    """Canonicalize like the metric: NFKC, drop tatweel, fold variants, strip
    harakat. Returns a token list."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    for a, b in _FOLD.items():
        text = text.replace(a, b)
    text = _HARAKAT_RE.sub("", text)
    return text.split()


class Solution:
    def __init__(self) -> None:
        self.quran: dict[str, list[dict[str, str]]] = json.loads(
            REF_PATH.read_text(encoding="utf-8")
        )
        # Per surah: flat token list and the ayah id of each token (parallel).
        self.surah_tokens: dict[str, list[str]] = {}
        self.surah_ids: dict[str, list[str]] = {}
        df: dict[str, set[str]] = defaultdict(set)  # word -> surahs (for IDF)
        for surah, ayahs in self.quran.items():
            toks: list[str] = []
            ids: list[str] = []
            for ayah in ayahs:
                for w in normalize(ayah["clean"]):
                    toks.append(w)
                    ids.append(ayah["id"])
                    df[w].add(surah)
            self.surah_tokens[surah] = toks
            self.surah_ids[surah] = ids
        n = len(self.quran)
        self.idf: dict[str, float] = {w: log(n / len(s)) for w, s in df.items()}
        self.word_surahs: dict[str, set[str]] = dict(df)

    # ---- anchoring -------------------------------------------------------
    def _candidate_surahs(self, tokens: list[str], top: int = 3) -> list[str]:
        score: dict[str, float] = defaultdict(float)
        for w in set(tokens):
            surahs = self.word_surahs.get(w)
            if not surahs:
                continue
            weight = self.idf.get(w, 0.0)
            for s in surahs:
                score[s] += weight
        return sorted(score, key=lambda s: score[s], reverse=True)[:top]

    # ---- alignment -------------------------------------------------------
    def _align(self, tokens: list[str], surah: str):
        """Semi-global alignment: free gaps at the ends of the reference so the
        transcript can match any substring of the surah. Returns (ids, matches):
        ids[i] is the ayah id aligned to tokens[i] (None on insertion), matches
        is the count of exact token matches."""
        ref = self.surah_tokens[surah]
        ref_ids = self.surah_ids[surah]
        m, k = len(tokens), len(ref)
        if m == 0 or k == 0:
            return [None] * m, 0
        MATCH, MIS, GAP = 2, -1, -1
        dp = [[0.0] * (k + 1) for _ in range(m + 1)]
        bt = [[0] * (k + 1) for _ in range(m + 1)]  # 0=diag 1=token-gap 2=ref-gap
        for i in range(1, m + 1):
            dp[i][0] = i * GAP
            bt[i][0] = 1
        for j in range(1, k + 1):
            bt[0][j] = 2  # free reference prefix (dp stays 0)
        for i in range(1, m + 1):
            ti = tokens[i - 1]
            row, prow, brow = dp[i], dp[i - 1], bt[i]
            for j in range(1, k + 1):
                diag = prow[j - 1] + (MATCH if ti == ref[j - 1] else MIS)
                up = prow[j] + GAP
                left = row[j - 1] + GAP
                best, b = diag, 0
                if up > best:
                    best, b = up, 1
                if left > best:
                    best, b = left, 2
                row[j] = best
                brow[j] = b
        # Free reference suffix: pick best column in the last row.
        j = max(range(k + 1), key=lambda x: dp[m][x])
        i = m
        ids: list = [None] * m
        matches = 0
        while i > 0:
            b = bt[i][j]
            if b == 0:
                ids[i - 1] = ref_ids[j - 1]
                if tokens[i - 1] == ref[j - 1]:
                    matches += 1
                i -= 1
                j -= 1
            elif b == 1:
                i -= 1
            else:
                j -= 1
        return ids, matches

    def process(self, transcript: str) -> dict:
        tokens = normalize(transcript)
        if not tokens:
            return {"abstain": True}

        best = None  # (matches, ids)
        for surah in self._candidate_surahs(tokens):
            ids, matches = self._align(tokens, surah)
            if best is None or matches > best[0]:
                best = (matches, ids)
        if best is None:
            return {"abstain": True}
        matches, ids = best
        if matches < max(2, 0.5 * len(tokens)):
            return {"abstain": True}

        # Carry ayah id forward over insertion gaps, then back-fill leading None.
        last = None
        for i in range(len(ids)):
            if ids[i] is None:
                ids[i] = last
            else:
                last = ids[i]
        nxt = None
        for i in range(len(ids) - 1, -1, -1):
            if ids[i] is None:
                ids[i] = nxt
            else:
                nxt = ids[i]
        if any(x is None for x in ids):
            return {"abstain": True}

        words = transcript.split()
        if len(words) != len(ids):
            # Normalizer changed the token count; fall back to a single bucket.
            uniq = []
            for x in ids:
                if x not in uniq:
                    uniq.append(x)
            return {"ayahs": [{"id": uniq[0], "text": transcript}]}

        ayahs: list[dict] = []
        cur_id, buf = ids[0], [words[0]]
        for i in range(1, len(words)):
            if ids[i] == cur_id:
                buf.append(words[i])
            else:
                ayahs.append({"id": cur_id, "text": " ".join(buf)})
                cur_id, buf = ids[i], [words[i]]
        ayahs.append({"id": cur_id, "text": " ".join(buf)})
        return {"ayahs": ayahs}
