"""
solution.py — the ONLY file the autoresearch agent edits.

Start from scratch. The goal is a transcript-only algorithm that, given a Quran
recitation transcript (no harakat), decides which ayahs were recited and splits
the transcript by ayah. This is Stage 1 of a memorization checker; mistake
detection (Stage 2) is a separate harness and is out of scope here.

You may add helper files next to this one and import them. Do not edit eval.py
or anything under data/ — those are the fixed dataset and metric.

Reference data
--------------
data/quran_ref.json maps each surah id to its ayahs:

    { "095": [ {"id": "095001", "ar": "<uthmani>", "clean": "<no-harakat>"}, ... ], ... }

Use `clean` for matching against transcripts (transcripts have no harakat).

Contract (what eval.py expects from process())
-----------------------------------------------
Return ONE of:

    {"abstain": True}
        when the transcript is NOT a Quran recitation
        (spoken request, noise, unintelligible, uncertain).

    {"ayahs": [ {"id": "095001", "text": "<transcript words for this ayah>"},
                {"id": "095002", "text": "..."}, ... ]}
        when it IS a recitation. `id` is the 6-digit ayah id
        (3-digit surah + 3-digit ayah). `text` is the slice of the transcript
        assigned to that ayah; concatenating the texts in order should reproduce
        the recited transcript. The ids should follow transcript order, but some
        gold rows skip ayahs, so the id set is not always consecutive.

Scored (lower is better) by eval.py:
    detection_error  — did your ayah-id set exactly match the gold assignment
    split_error      — fraction of transcript words placed in the wrong ayah
    abstain_error    — did you correctly abstain on non-Quran rows
"""
from __future__ import annotations

import math
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))
_HARAKAT_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_NON_WORD_RE = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)
_FOLD = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ى": "ي",
    "ؤ": "ء",
    "ئ": "ء",
    "ة": "ه",
}


def _norm(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    for src, dst in _FOLD.items():
        text = text.replace(src, dst)
    text = _HARAKAT_RE.sub("", text)
    text = _NON_WORD_RE.sub(" ", text)
    return [t for t in text.split() if t]


_ISTIADHA = _norm("اعوذ بالله من الشيطان الرجيم")
_BASMALA = _norm("بسم الله الرحمن الرحيم")
_FATIHA_START = _norm("الحمد لله رب العالمين")


def _preamble_len(toks: list[str]) -> int:
    pos = 0
    if toks[: len(_ISTIADHA)] == _ISTIADHA:
        pos += len(_ISTIADHA)
    if toks[pos : pos + len(_BASMALA)] == _BASMALA:
        after = toks[pos + len(_BASMALA) : pos + len(_BASMALA) + len(_FATIHA_START)]
        if after != _FATIHA_START:
            pos += len(_BASMALA)
    return pos


class Solution:
    def __init__(self) -> None:
        # {surah_id: [{"id", "ar", "clean"}, ...]}
        self.quran: dict[str, list[dict[str, str]]] = json.loads(REF_PATH.read_text(encoding="utf-8"))
        self.ref_tokens: list[str] = []
        self.ref_ids: list[str] = []
        self.ayah_spans: dict[str, tuple[int, int]] = {}
        self.id_order: list[str] = []
        self.id_pos: dict[str, int] = {}

        for surah in sorted(self.quran):
            ayahs = sorted(
                (a for a in self.quran[surah] if len(str(a.get("id", ""))) == 6),
                key=lambda a: a["id"],
            )
            for ayah in ayahs:
                toks = _norm(ayah.get("clean") or ayah.get("ar") or "")
                if not toks:
                    continue
                start = len(self.ref_tokens)
                self.ref_tokens.extend(toks)
                self.ref_ids.extend([ayah["id"]] * len(toks))
                self.ayah_spans[ayah["id"]] = (start, len(self.ref_tokens))
                self.id_pos[ayah["id"]] = len(self.id_order)
                self.id_order.append(ayah["id"])

        self.index: dict[str, list[int]] = defaultdict(list)
        for pos, tok in enumerate(self.ref_tokens):
            self.index[tok].append(pos)
        self.freq = Counter(self.ref_tokens)

    def process(self, transcript: str) -> dict:
        raw_tokens = (transcript or "").split()
        toks = _norm(transcript)
        if len(toks) < 2:
            return {"abstain": True}
        prefix_len = _preamble_len(toks)
        search_toks = toks[prefix_len:] or toks
        raw_prefix = raw_tokens[:prefix_len] if prefix_len <= len(raw_tokens) else []
        raw_search = raw_tokens[prefix_len:] if prefix_len <= len(raw_tokens) else raw_tokens

        offsets: dict[int, float] = defaultdict(float)
        for i, tok in enumerate(search_toks):
            positions = self.index.get(tok)
            if not positions:
                continue
            freq = len(positions)
            if freq > 450:
                continue
            weight = 1.0 / math.sqrt(freq)
            for ref_pos in positions:
                offsets[ref_pos - i] += weight

        if not offsets:
            return {"abstain": True}

        best = None
        for offset, vote in sorted(offsets.items(), key=lambda kv: kv[1], reverse=True)[:24]:
            start = max(0, offset - 12)
            end = min(len(self.ref_tokens), offset + int(len(search_toks) * 1.35) + 28)
            cand_tokens = self.ref_tokens[start:end]
            if not cand_tokens:
                continue

            from difflib import SequenceMatcher

            matcher = SequenceMatcher(a=search_toks, b=cand_tokens, autojunk=False)
            matches: list[tuple[int, int]] = []
            for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
                if tag == "equal":
                    matches.extend((i1 + k, start + j1 + k) for k in range(i2 - i1))
            score = len(matches) / max(len(search_toks), 1)
            # Prefer good token coverage; use the offset vote as a weak tie-breaker.
            rank = (score, vote, len(matches))
            if best is None or rank > best[0]:
                best = (rank, matches, offset)

        if best is None:
            return {"abstain": True}

        (score, _vote, _nmatch), matches, offset = best
        min_score = 0.78 if len(search_toks) <= 4 else 0.42
        if score < min_score or len(matches) < 2:
            return {"abstain": True}

        matched_by_tok = {i: ref for i, ref in matches}
        matched_items = sorted(matched_by_tok.items())
        assigned_ref: list[int] = []
        for i in range(len(search_toks)):
            if i in matched_by_tok:
                assigned_ref.append(matched_by_tok[i])
                continue
            prev = next(((ti, rp) for ti, rp in reversed(matched_items) if ti < i), None)
            nxt = next(((ti, rp) for ti, rp in matched_items if ti > i), None)
            if prev and nxt and nxt[0] != prev[0]:
                frac = (i - prev[0]) / (nxt[0] - prev[0])
                assigned_ref.append(round(prev[1] + frac * (nxt[1] - prev[1])))
            elif prev:
                assigned_ref.append(prev[1] + (i - prev[0]))
            elif nxt:
                assigned_ref.append(nxt[1] - (nxt[0] - i))
            else:
                assigned_ref.append(offset + i)

        assigned_ref = [min(max(p, 0), len(self.ref_ids) - 1) for p in assigned_ref]
        first = min(ref for _, ref in matches)
        last = max(ref for _, ref in matches)
        first_id = self.ref_ids[first]
        last_id = self.ref_ids[last]
        lo = min(self.id_pos[first_id], self.id_pos[last_id])
        hi = max(self.id_pos[first_id], self.id_pos[last_id])
        ids = self.id_order[lo : hi + 1]

        buckets: dict[str, list[str]] = {ayah_id: [] for ayah_id in ids}
        if ids and raw_prefix:
            buckets[ids[0]].extend(raw_prefix)
        for i, ref_pos in enumerate(assigned_ref):
            ayah_id = self.ref_ids[ref_pos]
            if ayah_id not in buckets:
                buckets[ayah_id] = []
            word = raw_search[i] if i < len(raw_search) else search_toks[i]
            buckets[ayah_id].append(word)

        out_ids = [ayah_id for ayah_id in ids if buckets.get(ayah_id)]
        return {"ayahs": [{"id": ayah_id, "text": " ".join(buckets[ayah_id])} for ayah_id in out_ids]}
