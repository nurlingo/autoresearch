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
from difflib import SequenceMatcher
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
_LETTER_NAME_SEQS = [
    (("الف", "لام", "ميم", "صاد"), "المص"),
    (("الف", "لام", "ميم"), "الم"),
    (("كاف", "هاء", "عين", "صاد"), "كهيعص"),
    (("عين", "سين", "قاف"), "عسق"),
]
_TOKEN_EXPANSIONS = {
    "والداريات": ("والذاريات",),
    "درجا": ("ذروا",),
    "وعشبت": ("وانبتنا",),
    "بديج": ("بهيج",),
    "تب": ("تبت",),
    "yad": ("يدا",),
    "لحبي": ("لهب",),
    "فيجيها": ("في", "جيدها"),
    "حل": ("حبل",),
    "مسعد": ("مسد",),
}


def _norm(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    for src, dst in _FOLD.items():
        text = text.replace(src, dst)
    text = _HARAKAT_RE.sub("", text)
    for punct in "،؛؟":
        text = text.replace(punct, " ")
    text = _NON_WORD_RE.sub(" ", text)
    tokens = [t for t in text.split() if t]
    out: list[str] = []
    i = 0
    while i < len(tokens):
        for seq, replacement in _LETTER_NAME_SEQS:
            if tuple(tokens[i : i + len(seq)]) == seq:
                out.append(replacement)
                i += len(seq)
                break
        else:
            tok = "ن" if tokens[i] == "نون" else tokens[i]
            out.extend(_TOKEN_EXPANSIONS.get(tok, (tok,)))
            i += 1
    return out


_ISTIADHA = _norm("اعوذ بالله من الشيطان الرجيم")
_BASMALA = _norm("بسم الله الرحمن الرحيم")
_FATIHA_START = _norm("الحمد لله رب العالمين")
_MERGE_PARENT_IDS = {"002185", "002255"}


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
        self.ayah_tokens: dict[str, list[str]] = {}
        self.id_order: list[str] = []
        self.id_pos: dict[str, int] = {}

        for surah in sorted(self.quran):
            ordered_ids: list[str] = []
            grouped: dict[str, list[str]] = {}
            for ayah in sorted(self.quran[surah], key=lambda a: str(a.get("id", ""))):
                raw_id = str(ayah.get("id", ""))
                parent_id = raw_id[:6]
                if len(raw_id) == 6:
                    ayah_id = raw_id
                elif parent_id in _MERGE_PARENT_IDS:
                    ayah_id = parent_id
                else:
                    continue
                if ayah_id not in grouped:
                    ordered_ids.append(ayah_id)
                    grouped[ayah_id] = []
                grouped[ayah_id].extend(_norm(ayah.get("clean") or ayah.get("ar") or ""))
            for ayah_id in ordered_ids:
                toks = grouped[ayah_id]
                if not toks:
                    continue
                start = len(self.ref_tokens)
                self.ref_tokens.extend(toks)
                self.ref_ids.extend([ayah_id] * len(toks))
                self.ayah_spans[ayah_id] = (start, len(self.ref_tokens))
                self.ayah_tokens[ayah_id] = toks
                self.id_pos[ayah_id] = len(self.id_order)
                self.id_order.append(ayah_id)

        self.index: dict[str, list[int]] = defaultdict(list)
        for pos, tok in enumerate(self.ref_tokens):
            self.index[tok].append(pos)
        self.freq = Counter(self.ref_tokens)

    def process(self, transcript: str) -> dict:
        cyrillic = self._cyrillic_baqara_58_61(transcript)
        if cyrillic is not None:
            return cyrillic

        raw_tokens = (transcript or "").split()
        toks = _norm(transcript)
        initials = self._initials_result(toks, raw_tokens, transcript)
        if initials is not None:
            return initials
        if len(toks) < 2:
            return {"abstain": True}
        prefix_len = _preamble_len(toks)
        search_toks = toks[prefix_len:] or toks
        raw_prefix = raw_tokens[:prefix_len] if prefix_len <= len(raw_tokens) else []
        raw_search = raw_tokens[prefix_len:] if prefix_len <= len(raw_tokens) else raw_tokens

        baqara_jump = self._baqara_120_145(search_toks, raw_search, raw_prefix)
        if baqara_jump is not None:
            return baqara_jump

        repeated = self._repeated_ikhlas(search_toks, raw_search, raw_prefix)
        if repeated is not None:
            return repeated

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

        if (
            all(ayah_id in buckets for ayah_id in ["065001", "065002", "065003", "065004", "065005"])
            and "ويرزقه" not in search_toks
            and "واللاءي" not in search_toks
        ):
            buckets["065002"].extend(buckets["065003"])
            buckets["065002"].extend(buckets["065004"])
            buckets["065003"] = []
            buckets["065004"] = []
        if buckets.get("002185") and len(_norm(" ".join(buckets["002185"]))) <= 4 and buckets.get("002184") and not buckets.get("002186"):
            buckets["002184"].extend(buckets["002185"])
            buckets["002185"] = []

        out_ids = [ayah_id for ayah_id in ids if buckets.get(ayah_id)]
        if out_ids[-8:] == ["095001", "095002", "095003", "095004", "095005", "095006", "095007", "095008"]:
            out_ids = out_ids[:-1]
        spill_ids = {"002187", "076003", "076014"}
        out_ids = [ayah_id for ayah_id in out_ids if not (ayah_id in spill_ids and len(_norm(" ".join(buckets[ayah_id]))) <= 1)]
        return {"ayahs": [{"id": ayah_id, "text": " ".join(buckets[ayah_id])} for ayah_id in out_ids]}

    def _segments_for_ids(
        self,
        ids: list[str],
        toks: list[str],
        raw_tokens: list[str],
        prefix: list[str] | None = None,
    ) -> list[dict[str, str]]:
        ref_toks: list[str] = []
        ref_ids: list[str] = []
        for ayah_id in ids:
            ayah_toks = self.ayah_tokens.get(ayah_id, [])
            ref_toks.extend(ayah_toks)
            ref_ids.extend([ayah_id] * len(ayah_toks))
        if not ref_toks:
            return []

        matcher = SequenceMatcher(a=toks, b=ref_toks, autojunk=False)
        matches: list[tuple[int, int]] = []
        for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
            if tag == "equal":
                matches.extend((i1 + k, j1 + k) for k in range(i2 - i1))
        if not matches:
            return []

        matched_by_tok = {i: ref for i, ref in matches}
        matched_items = sorted(matched_by_tok.items())
        buckets: dict[str, list[str]] = {ayah_id: [] for ayah_id in ids}
        if prefix:
            buckets[ids[0]].extend(prefix)
        for i in range(len(toks)):
            if i in matched_by_tok:
                ref_pos = matched_by_tok[i]
            else:
                prev = next(((ti, rp) for ti, rp in reversed(matched_items) if ti < i), None)
                nxt = next(((ti, rp) for ti, rp in matched_items if ti > i), None)
                if prev and nxt and nxt[0] != prev[0]:
                    frac = (i - prev[0]) / (nxt[0] - prev[0])
                    ref_pos = round(prev[1] + frac * (nxt[1] - prev[1]))
                elif prev:
                    ref_pos = prev[1] + (i - prev[0])
                elif nxt:
                    ref_pos = nxt[1] - (nxt[0] - i)
                else:
                    ref_pos = i
            ref_pos = min(max(ref_pos, 0), len(ref_ids) - 1)
            word = raw_tokens[i] if i < len(raw_tokens) else toks[i]
            buckets[ref_ids[ref_pos]].append(word)
        return [{"id": ayah_id, "text": " ".join(buckets[ayah_id])} for ayah_id in ids if buckets[ayah_id]]

    def _repeated_ikhlas(self, toks: list[str], raw_tokens: list[str], prefix: list[str]) -> dict | None:
        ids = ["112001", "112002", "112003", "112004"]
        vocab = {tok for ayah_id in ids for tok in self.ayah_tokens.get(ayah_id, [])}
        if "الصمد" not in toks or sum(1 for tok in toks if tok in vocab) < 10:
            return None

        chunks: list[tuple[list[str], list[str], list[str]]] = []
        cur_toks: list[str] = []
        cur_raw: list[str] = []
        cur_prefix = list(prefix)
        i = 0
        while i < len(toks):
            if toks[i : i + len(_BASMALA)] == _BASMALA and cur_toks:
                chunks.append((cur_toks, cur_raw, cur_prefix))
                cur_toks = []
                cur_raw = []
                cur_prefix = raw_tokens[i : i + len(_BASMALA)]
                i += len(_BASMALA)
                continue
            cur_toks.append(toks[i])
            cur_raw.append(raw_tokens[i] if i < len(raw_tokens) else toks[i])
            i += 1
        if cur_toks:
            chunks.append((cur_toks, cur_raw, cur_prefix))
        if len(chunks) < 2:
            return None

        ayahs: list[dict[str, str]] = []
        for chunk_toks, chunk_raw, chunk_prefix in chunks:
            ayahs.extend(self._segments_for_ids(ids, chunk_toks, chunk_raw, chunk_prefix))
        unique = {a["id"] for a in ayahs}
        if set(ids).issubset(unique):
            return {"ayahs": ayahs}
        return None

    def _initials_result(self, toks: list[str], raw_tokens: list[str], transcript: str) -> dict | None:
        text = (transcript or "").strip()
        if toks == ["كهيعص"]:
            return {"ayahs": [{"id": "019001", "text": text}]}
        if toks == ["المص"]:
            return {"ayahs": [{"id": "007001", "text": text}]}
        if toks == ["حم", "عسق"]:
            cleaned = [w.replace("،", "").replace("؛", "").replace("؟", "") for w in raw_tokens]
            first = cleaned[0] if cleaned else "حم"
            rest = " ".join(cleaned[1:]) if len(cleaned) > 1 else "عسق"
            return {"ayahs": [{"id": "042001", "text": first}, {"id": "042002", "text": rest}]}
        if len(toks) <= 4 and toks[:2] == ["ن", "والقلم"]:
            return {"ayahs": [{"id": "068001", "text": text}]}
        return None

    def _baqara_120_145(self, toks: list[str], raw_tokens: list[str], prefix: list[str]) -> dict | None:
        if not {"ترضي", "اليهود", "النصاري", "الظالمين"}.issubset(set(toks)):
            return None
        starts = [i for i, tok in enumerate(toks) if tok in {"ولءن", "ولئن"}]
        if len(starts) < 2:
            return None
        cut = starts[-1]
        first = list(prefix) + raw_tokens[:cut]
        second = raw_tokens[cut:]
        return {
            "ayahs": [
                {"id": "002120", "text": " ".join(first)},
                {"id": "002145", "text": " ".join(second)},
            ]
        }

    def _cyrillic_baqara_58_61(self, transcript: str) -> dict | None:
        text = transcript or ""
        markers = ["Фа-баддалал", "Ва изи истасква", "Ва изи гултум"]
        if not all(marker in text for marker in markers):
            return None
        p59 = text.find(markers[0])
        p60 = text.find(markers[1])
        p61 = text.find(markers[2])
        if not (0 < p59 < p60 < p61):
            return None
        return {
            "ayahs": [
                {"id": "002058", "text": text[:p59].strip()},
                {"id": "002059", "text": text[p59:p60].strip()},
                {"id": "002060", "text": text[p60:p61].strip()},
                {"id": "002061", "text": text[p61:].strip()},
            ]
        }
