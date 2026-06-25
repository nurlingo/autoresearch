"""
solution.py — the autoresearch agent's algorithm (Stage 1: detect + split).

Approach (built from scratch):
  - Normalize Arabic for *matching* only (fold variants, drop harakat); emit the
    ORIGINAL transcript words as segment text so the scorer aligns them to gold.
  - Index every ayah by its normalized token bigrams.
  - Detect the start ayah by best token overlap over a contiguous window.
  - Greedily assign transcript words to consecutive ayahs proportional to each
    reference ayah's length.
  - Abstain when no Quran window covers enough of the transcript.

See PROGRAM.md for the contract and the metric.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))

_HARAKAT = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء"})

ABSTAIN_COVERAGE = 0.34  # min fraction of transcript words found in a Quran window


def _norm(word: str) -> str:
    word = unicodedata.normalize("NFKC", word or "")
    word = word.replace("ـ", "").translate(_FOLD)
    return _HARAKAT.sub("", word)


class Solution:
    def __init__(self) -> None:
        quran: dict[str, list[dict[str, str]]] = json.loads(REF_PATH.read_text(encoding="utf-8"))
        # Flat list of ayahs in canonical order, with normalized tokens.
        self.ayahs: list[dict] = []
        self.bigram_index: dict[tuple[str, str], list[int]] = {}
        for surah_id, ayahs in quran.items():
            for a in ayahs:
                toks = [t for t in (_norm(w) for w in a.get("clean", "").split()) if t]
                gi = len(self.ayahs)
                self.ayahs.append({"id": a["id"], "surah": surah_id, "toks": toks, "set": set(toks)})
                for bg in zip(toks, toks[1:]):
                    self.bigram_index.setdefault(bg, []).append(gi)

    def _candidates(self, w: list[str]) -> list[int]:
        if len(w) >= 2 and (w[0], w[1]) in self.bigram_index:
            return self.bigram_index[(w[0], w[1])]
        # fall back to any ayah containing the first transcript bigram anywhere
        cands: list[int] = []
        for bg in zip(w, w[1:]):
            cands += self.bigram_index.get(bg, [])
            if len(cands) > 200:
                break
        return list(dict.fromkeys(cands))

    def process(self, transcript: str) -> dict:
        orig = transcript.split()
        pairs = [(o, _norm(o)) for o in orig]
        pairs = [(o, n) for o, n in pairs if n]
        if len(pairs) < 2:
            return {"abstain": True}
        orig_w = [o for o, _ in pairs]
        w = [n for _, n in pairs]
        wset = set(w)

        # 1) Find the best start ayah: highest token coverage over a window that
        #    is roughly long enough to hold the transcript.
        best_start, best_cov = None, 0.0
        for gi in self._candidates(w):
            surah = self.ayahs[gi]["surah"]
            window: set[str] = set()
            j, total = gi, 0
            while j < len(self.ayahs) and self.ayahs[j]["surah"] == surah and total < len(w) + 4:
                window |= self.ayahs[j]["set"]
                total += len(self.ayahs[j]["toks"])
                j += 1
            cov = len(wset & window) / len(wset)
            if cov > best_cov:
                best_cov, best_start = cov, gi

        if best_start is None or best_cov < ABSTAIN_COVERAGE:
            return {"abstain": True}

        # 2) Build a reference token stream from the start ayah, then align the
        #    transcript to it (Needleman-Wunsch). Each transcript word inherits the
        #    ayah of the reference token it aligns to; word→ayah groups are the split.
        surah = self.ayahs[best_start]["surah"]
        ref_tok: list[str] = []
        ref_ayah: list[int] = []
        gi = best_start
        while gi < len(self.ayahs) and self.ayahs[gi]["surah"] == surah and len(ref_tok) < 2 * len(w) + 20:
            for t in self.ayahs[gi]["toks"]:
                ref_tok.append(t)
                ref_ayah.append(gi)
            gi += 1

        assign = self._align(w, ref_tok, ref_ayah, best_start)

        out: list[dict] = []
        for word, gi in zip(orig_w, assign):
            if out and out[-1]["_gi"] == gi:
                out[-1]["text"] += " " + word
            else:
                out.append({"id": self.ayahs[gi]["id"], "text": word, "_gi": gi})
        for seg in out:
            del seg["_gi"]
        return {"ayahs": out} if out else {"abstain": True}

    @staticmethod
    def _align(w: list[str], ref_tok: list[str], ref_ayah: list[int], start_gi: int) -> list[int]:
        """Needleman-Wunsch; return the ayah index each transcript word maps to."""
        n, m = len(w), len(ref_tok)
        MATCH, MIS, GAP = 2, -1, -1
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            dp[i][0] = i * GAP
        for j in range(1, m + 1):
            dp[0][j] = j * GAP
        for i in range(1, n + 1):
            wi = w[i - 1]
            for j in range(1, m + 1):
                diag = dp[i - 1][j - 1] + (MATCH if wi == ref_tok[j - 1] else MIS)
                dp[i][j] = max(diag, dp[i - 1][j] + GAP, dp[i][j - 1] + GAP)
        # backtrack
        assign = [start_gi] * n
        i, j, last = n, m, start_gi
        while i > 0:
            if j > 0 and dp[i][j] == dp[i - 1][j - 1] + (MATCH if w[i - 1] == ref_tok[j - 1] else MIS):
                last = ref_ayah[j - 1]
                assign[i - 1] = last
                i, j = i - 1, j - 1
            elif dp[i][j] == dp[i - 1][j] + GAP:
                assign[i - 1] = last  # insertion in transcript → keep current ayah
                i -= 1
            else:
                j -= 1
        return assign
