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

# Diacritic ranges as explicit escapes (literal combining marks get reordered on
# save, which corrupts the character class). Mirrors eval.py's canonicalizer.
_HARAKAT_RE = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_FOLD = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ؤ": "ء", "ئ": "ء",
}


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
            # Skip app-specific pseudo-surahs (999* duas etc.); keep canonical
            # surahs 1..114 only — gold never references the rest.
            if not (surah.isdigit() and 1 <= int(surah) <= 114):
                continue
            toks: list[str] = []
            ids: list[str] = []
            for ayah in ayahs:
                # Long ayahs (e.g. Ayat al-Kursi 002255) are stored split with
                # 9-digit ids; the canonical ayah id is the first 6 digits.
                canon_id = ayah["id"][:6]
                for w in normalize(ayah["clean"]):
                    toks.append(w)
                    ids.append(canon_id)
                    df[w].add(surah)
            self.surah_tokens[surah] = toks
            self.surah_ids[surah] = ids
        n = len(self.surah_tokens)
        self.idf: dict[str, float] = {w: log(n / len(s)) for w, s in df.items()}
        self.word_surahs: dict[str, set[str]] = dict(df)
        # Bigram -> surahs index: word pairs are far more discriminative than
        # single words (every big surah contains "الله"; few contain "الله احد").
        self.surah_bigrams: dict[str, set[tuple[str, str]]] = {}
        for surah, toks in self.surah_tokens.items():
            self.surah_bigrams[surah] = {
                (toks[i], toks[i + 1]) for i in range(len(toks) - 1)
            }

    # ---- anchoring -------------------------------------------------------
    def _candidate_surahs(self, tokens: list[str], top: int = 3) -> list[str]:
        # Primary signal: how many of the transcript's bigrams a surah contains.
        bigrams = {(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)}
        bg_score: dict[str, int] = defaultdict(int)
        for surah, sb in self.surah_bigrams.items():
            hits = len(bigrams & sb)
            if hits:
                bg_score[surah] = hits
        # Secondary signal: IDF-weighted unigram vote (breaks ties, and covers
        # single-word transcripts that have no bigram).
        uni: dict[str, float] = defaultdict(float)
        for w in set(tokens):
            surahs = self.word_surahs.get(w)
            if not surahs:
                continue
            weight = self.idf.get(w, 0.0)
            for s in surahs:
                uni[s] += weight
        cands = set(bg_score) | set(uni)
        # Deterministic order: bigram hits desc, idf vote desc, surah id asc.
        return sorted(
            cands,
            key=lambda s: (-bg_score.get(s, 0), -round(uni.get(s, 0.0), 9), s),
        )[:top]

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
        best_score = dp[m][j]
        i = m
        ids: list = [None] * m
        matches = 0
        while i > 0:
            b = bt[i][j]
            if b == 0:
                # Only EXACT matches anchor an ayah id. Substitutions (e.g. a
                # leading basmala/ta'awwudh forced against a neighbouring ayah)
                # are left None so they inherit a real neighbour's id — this
                # prevents phantom leading/trailing ayahs in the detection set.
                if tokens[i - 1] == ref[j - 1]:
                    ids[i - 1] = ref_ids[j - 1]
                    matches += 1
                i -= 1
                j -= 1
            elif b == 1:
                i -= 1
            else:
                j -= 1
        return ids, matches, best_score

    # Leading formulae reciters say before the ayahs but reviewers exclude from
    # the gold split: ta'awwudh (seeking refuge), ended by "الرجيم".
    _TAAWWUDH_END = "الرجيم"

    def _strip_prefix_len(self, tokens: list[str]) -> int:
        """Number of leading tokens that are a ta'awwudh formula (so their common
        words like 'من' don't make spurious matches in the previous ayah)."""
        if tokens and tokens[0] in ("اعوذ", "تعوذ"):
            for k in range(1, min(len(tokens), 8)):
                if tokens[k] == self._TAAWWUDH_END:
                    return k + 1
        return 0

    @staticmethod
    def _fill_nearest(ids: list):
        """Assign each None token the id of the nearest anchored token (left on
        ties). Returns None if there is no anchor at all."""
        n = len(ids)
        left = [None] * n   # (id, distance) nearest anchor at or left of i
        d = None
        cur = None
        for i in range(n):
            if ids[i] is not None:
                cur, d = ids[i], 0
            elif d is not None:
                d += 1
            left[i] = (cur, d) if cur is not None else None
        cur, d = None, None
        out = list(ids)
        for i in range(n - 1, -1, -1):
            if ids[i] is not None:
                cur, d = ids[i], 0
            elif d is not None:
                d += 1
            if ids[i] is None:
                r = (cur, d) if cur is not None else None
                l = left[i]
                if l is None and r is None:
                    return None
                if l is None:
                    out[i] = r[0]
                elif r is None or l[1] <= r[1]:
                    out[i] = l[0]
                else:
                    out[i] = r[0]
        return out

    def process(self, transcript: str) -> dict:
        tokens = normalize(transcript)
        if not tokens:
            return {"abstain": True}

        prefix = self._strip_prefix_len(tokens)
        core = tokens[prefix:]
        if len(core) < 2:
            return {"abstain": True}

        best = None  # (score, matches, ids)
        for surah in self._candidate_surahs(core, top=6):
            ids, matches, score = self._align(core, surah)
            # Select by alignment score (gap-penalised), so a compact contiguous
            # match beats words scattered across a long surah.
            key = (score, matches)
            if best is None or key > best[0]:
                best = (key, matches, ids)
        if best is None:
            return {"abstain": True}
        _, matches, core_ids = best
        # Abstain on non-Quran: real recitations produce a contiguous run of
        # exact matches, whereas noise/spoken text yields only isolated
        # coincidental word matches. A run-based test is robust to repetition
        # (where matches/len is low) and to long ta'awwudh/basmala prefixes.
        run = best_run = 0
        for x in core_ids:
            run = run + 1 if x is not None else 0
            best_run = max(best_run, run)
        if matches < 2 or best_run < 2:
            return {"abstain": True}
        # Prefix tokens (ta'awwudh) get no anchor; back-fill folds them into the
        # first real ayah so the output text still reproduces the transcript.
        ids = [None] * prefix + core_ids

        # Fill unmatched tokens by NEAREST anchor (ties go left). A run of gaps
        # between two ayahs is split at its midpoint, so a boundary word lands in
        # the ayah it is closest to rather than always the previous one.
        ids = self._fill_nearest(ids)
        if ids is None:
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
