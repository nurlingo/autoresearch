# ============================================================================
# PRODUCTION ARTIFACT — Stage 1 ayah detection + split (transcript-only)
#
# Provenance: Study 2 run codex-r3 (GPT-5.5 high, Codex CLI v0.139.0), final
# commit in runs/codex-r3-260703.bundle. Selected 2026-07-06 over claude-r1 and
# two compositions (see production/README.md):
#   held-out test (107 rows, never seen in training): research_score 0.0793
#     detection 99/105 exact, split 97.8%, abstain 2/2
#   full dataset v1.1 (258 rows): research_score 0.0336
# Contract: Solution.process(transcript) -> {"abstain": True} | {"ayahs": [...]}
# Requires: data/quran_ref.json (QURAN_REF_PATH env to relocate).
# ============================================================================
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
_NON_WORD_RE = re.compile(r"[^\w]+")
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء"}
_LETTER_NAMES = {
    "ا": "الف", "ل": "لام", "م": "ميم", "ص": "صاد", "ر": "را", "ك": "كاف",
    "ه": "ها", "ي": "يا", "ع": "عين", "ط": "طا", "س": "سين", "ح": "حا",
    "ق": "قاف", "ن": "نون",
}
_MUQATTAAT = {"الم", "المص", "الر", "المر", "كهيعص", "طه", "طسم", "طس", "يس", "ص", "حم", "عسق", "ق", "ن"}


def _canon_tokens(text: str) -> list[tuple[str, str]]:
    text = unicodedata.normalize("NFKC", text or "").replace("ـ", "")
    for a, b in _FOLD.items():
        text = text.replace(a, b)
    text = _HARAKAT_RE.sub("", text)
    out: list[tuple[str, str]] = []
    for raw in text.split():
        clean = _NON_WORD_RE.sub("", raw)
        if clean:
            out.append((clean, raw))
    return out


def _ref_words(text: str) -> list[str]:
    words: list[str] = []
    for word, _ in _canon_tokens(text):
        words.append(word)
        if word in _MUQATTAAT:
            words.extend(_LETTER_NAMES[ch] for ch in word)
    return words


class Solution:
    def __init__(self) -> None:
        # {surah_id: [{"id", "ar", "clean"}, ...]}
        self.quran: dict[str, list[dict[str, str]]] = json.loads(REF_PATH.read_text(encoding="utf-8"))
        self.ref_words: list[str] = []
        self.ref_labels: list[str] = []
        self.muqattaat_ids: set[str] = set()
        self.short_ayahs: list[tuple[str, str, int]] = []
        self.ayah_words: dict[str, list[str]] = {}
        for surah_id in sorted(self.quran):
            if not (surah_id.isdigit() and len(surah_id) == 3) or surah_id == "999":
                continue
            for ayah in self.quran[surah_id]:
                ayah_id = ayah["id"][:6]
                ayah_words = _ref_words(ayah.get("clean", ""))
                self.ayah_words.setdefault(ayah_id, []).extend(ayah_words)
                if any(word in _MUQATTAAT for word, _ in _canon_tokens(ayah.get("clean", ""))):
                    self.muqattaat_ids.add(ayah_id)
                for word in _ref_words(ayah.get("clean", "")):
                    self.ref_words.append(word)
                    self.ref_labels.append(ayah_id)
                if 1 <= len(ayah_words) <= 10:
                    self.short_ayahs.append((ayah_id, " ".join(ayah_words), len(ayah_words)))
        self.word_positions: dict[str, list[int]] = defaultdict(list)
        for i, word in enumerate(self.ref_words):
            self.word_positions[word].append(i)
        self.word_freq = Counter(self.ref_words)
        self.unique_ref_words = list(self.word_positions)
        self.ref_words_by_len: dict[int, list[str]] = defaultdict(list)
        for word in self.unique_ref_words:
            if self.word_freq[word] <= 50:
                self.ref_words_by_len[len(word)].append(word)
        self.similar_cache: dict[str, list[str]] = {}
        self.prefixes = [
            [w for w, _ in _canon_tokens("اعوذ بالله من الشيطان الرجيم بسم الله الرحمن الرحيم")],
            [w for w, _ in _canon_tokens("أعوذ بالله من الشيطان الرجيم")],
            [w for w, _ in _canon_tokens("بسم الله الرحمن الرحيم")],
        ]

    def process(self, transcript: str) -> dict:
        token_pairs = _canon_tokens(transcript)
        if not token_pairs:
            return {"abstain": True}

        words = [w for w, _ in token_pairs]
        raw_words = [raw for _, raw in token_pairs]
        stripped_words, stripped_raw, intro_offset = self._strip_intro(words, raw_words)
        if not stripped_words:
            return {"abstain": True}

        match = self._best_match(stripped_words)
        if match is None:
            return self._short_or_abstain(stripped_words, stripped_raw)
        score, ref_start, matcher = match
        min_score = 0.75 if len(stripped_words) <= 3 else 0.60 if len(stripped_words) <= 4 else 0.33
        if score < min_score:
            return self._short_or_abstain(stripped_words, stripped_raw)

        labels, evidence = self._assign_labels(stripped_words, ref_start, matcher)
        self._trim_weak_edges(labels, evidence)
        self._repair_complete_prefix(stripped_words, labels, evidence)
        self._repair_unsupported_suffix(stripped_words, labels, evidence)
        self._merge_weak_bridges(labels, evidence)
        self._trim_weak_edges(labels, evidence)
        if not any(labels):
            return {"abstain": True}
        segments = self._segments(stripped_raw, labels)
        self._restore_fatiha_basmala(segments, raw_words, intro_offset)
        return {"ayahs": segments}

    def _short_or_abstain(self, words: list[str], raw_words: list[str]) -> dict:
        if len(words) > 8:
            return {"abstain": True}
        text = " ".join(words)
        best = (0.0, "", 0.0)
        second = 0.0
        for ayah_id, ref_text, ref_len in self.short_ayahs:
            if abs(ref_len - len(words)) > 4:
                continue
            ratio = SequenceMatcher(a=text, b=ref_text, autojunk=False).ratio()
            if ratio > best[0]:
                second = best[0]
                best = (ratio, ayah_id, second)
            elif ratio > second:
                second = ratio
        if best[0] >= 0.80 and best[0] - second >= 0.15:
            return {"ayahs": [{"id": best[1], "text": " ".join(raw_words)}]}
        return {"abstain": True}

    def _strip_intro(self, words: list[str], raw_words: list[str]) -> tuple[list[str], list[str], int]:
        offset = 0
        changed = True
        while changed:
            changed = False
            for prefix in self.prefixes:
                if words[offset:offset + len(prefix)] == prefix:
                    offset += len(prefix)
                    changed = True
                    break
        return words[offset:], raw_words[offset:], offset

    def _best_match(self, words: list[str]) -> tuple[float, int, SequenceMatcher] | None:
        seed_bases: list[int] = []
        for j, word in enumerate(words):
            # Common words are useful inside SequenceMatcher but make poor seeds.
            if self.word_freq.get(word, 0) <= 100:
                seed_bases.extend(pos - j for pos in self.word_positions.get(word, ()))
            if len(word) >= 4 and self.word_freq.get(word, 0) == 0:
                for similar in self._similar_ref_words(word):
                    seed_bases.extend(pos - j for pos in self.word_positions.get(similar, ()))

        if not seed_bases:
            for j, word in enumerate(words[:20]):
                seed_bases.extend(pos - j for pos in self.word_positions.get(word, ())[:200])
        if not seed_bases:
            return None

        best: tuple[float, int, SequenceMatcher] | None = None
        n = len(words)
        for base, _ in Counter(seed_bases).most_common(100):
            start = max(0, base - 8)
            end = min(len(self.ref_words), base + n + 24)
            ref = self.ref_words[start:end]
            matcher = SequenceMatcher(a=words, b=ref, autojunk=False)
            equal = self._match_score(words, ref, matcher)
            score = equal / max(n, 1)
            if best is None or score > best[0]:
                best = (score, start, matcher)
        return best

    def _similar_ref_words(self, word: str) -> list[str]:
        if word in self.similar_cache:
            return self.similar_cache[word]
        out: list[str] = []
        for size in range(len(word) - 2, len(word) + 3):
            for ref_word in self.ref_words_by_len.get(size, ()):
                if self._word_ratio(word, ref_word) >= 0.74:
                    out.append(ref_word)
                    if len(out) >= 20:
                        self.similar_cache[word] = out
                        return out
        self.similar_cache[word] = out
        return out[:20]

    def _word_ratio(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        return SequenceMatcher(a=a, b=b, autojunk=False).ratio()

    def _match_score(self, words: list[str], ref: list[str], matcher: SequenceMatcher) -> float:
        score = 0.0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                score += i2 - i1
            elif tag == "replace" and (i2 - i1) == (j2 - j1):
                for a, b in zip(words[i1:i2], ref[j1:j2]):
                    if len(a) >= 4 and self._word_ratio(a, b) >= 0.74:
                        score += 0.75
        return score

    def _assign_labels(
        self, words: list[str], ref_start: int, matcher: SequenceMatcher
    ) -> tuple[list[str | None], list[bool]]:
        labels: list[str | None] = [None] * len(words)
        evidence = [False] * len(words)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    labels[i1 + k] = self.ref_labels[ref_start + j1 + k]
                    evidence[i1 + k] = True
            elif tag in {"replace", "insert"}:
                ref_len = j2 - j1
                for k in range(i1, i2):
                    if ref_len > 0:
                        rel = (k - i1) / max(i2 - i1, 1)
                        jj = j1 + min(int(rel * ref_len), ref_len - 1)
                    else:
                        jj = j1
                    if 0 <= ref_start + jj < len(self.ref_labels):
                        labels[k] = self.ref_labels[ref_start + jj]
                        if j1 <= jj < j2 and self._word_ratio(words[k], self.ref_words[ref_start + jj]) >= 0.74:
                            evidence[k] = True

        last: str | None = None
        for i, label in enumerate(labels):
            if label is None:
                labels[i] = last
            else:
                last = label
        next_label: str | None = None
        for i in range(len(labels) - 1, -1, -1):
            if labels[i] is None:
                labels[i] = next_label
            else:
                next_label = labels[i]
        return labels, evidence

    def _trim_weak_edges(self, labels: list[str | None], evidence: list[bool]) -> None:
        def distinct() -> list[str]:
            out: list[str] = []
            for label in labels:
                if label and label not in out:
                    out.append(label)
            return out

        def edge_stats(label: str, from_left: bool) -> tuple[int, int, int]:
            indexes = range(len(labels)) if from_left else range(len(labels) - 1, -1, -1)
            n = ev = 0
            last = -1
            for i in indexes:
                if labels[i] != label:
                    break
                n += 1
                ev += int(evidence[i])
                last = i
            return n, ev, last

        while True:
            ids = distinct()
            if len(ids) <= 1:
                break
            first = ids[0]
            _, ev, last = edge_stats(first, True)
            if ev:
                break
            repl = ids[1]
            for i in range(last + 1):
                labels[i] = repl

        while True:
            ids = distinct()
            if len(ids) <= 1:
                break
            last_id = ids[-1]
            _, ev, last = edge_stats(last_id, False)
            if ev:
                break
            repl = ids[-2]
            for i in range(last, len(labels)):
                labels[i] = repl

    def _repair_unsupported_suffix(
        self, words: list[str], labels: list[str | None], evidence: list[bool]
    ) -> None:
        starts: set[int] = set()
        last_true = max((i for i, ok in enumerate(evidence) if ok), default=-1)
        if 0 <= last_true < len(words) - 5:
            starts.add(last_true + 1)

        if labels and labels[-1] is not None:
            final_label = labels[-1]
            start = len(labels) - 1
            while start > 0 and labels[start - 1] == final_label:
                start -= 1
            count = len(labels) - start
            ev = sum(evidence[start:])
            if count >= 5 and ev / count <= 0.35:
                starts.add(start)

        best: tuple[float, int, list[str | None], list[bool]] | None = None
        for start in sorted(starts):
            suffix = words[start:]
            match = self._best_match(suffix)
            if match is None or match[0] < 0.70:
                continue
            _, ref_start, matcher = match
            new_labels, new_evidence = self._assign_labels(suffix, ref_start, matcher)
            self._trim_weak_edges(new_labels, new_evidence)
            if not any(new_labels) or set(new_labels) == set(labels[start:]):
                continue
            if best is None or match[0] > best[0]:
                best = (match[0], start, new_labels, new_evidence)

        if best is None:
            return
        _, start, new_labels, new_evidence = best
        labels[start:] = new_labels
        evidence[start:] = new_evidence

    def _repair_complete_prefix(
        self, words: list[str], labels: list[str | None], evidence: list[bool]
    ) -> None:
        first_true = next((i for i, ok in enumerate(evidence) if ok), None)
        if first_true is None or first_true == 0:
            return
        current = labels[first_true]
        if current is None or any(evidence[:first_true]):
            return
        prev = f"{current[:3]}{int(current[3:]) - 1:03d}"
        if self.ayah_words.get(prev) == words[:first_true]:
            for i in range(first_true):
                labels[i] = prev
                evidence[i] = True

    def _merge_weak_bridges(self, labels: list[str | None], evidence: list[bool]) -> None:
        runs: list[tuple[int, int, str, int]] = []
        i = 0
        while i < len(labels):
            label = labels[i]
            j = i + 1
            while j < len(labels) and labels[j] == label:
                j += 1
            if label is not None:
                runs.append((i, j, label, sum(evidence[i:j])))
            i = j

        for idx in range(1, len(runs) - 1):
            start, end, label, ev = runs[idx]
            prev_label = runs[idx - 1][2]
            next_label = runs[idx + 1][2]
            if label[:3] != prev_label[:3] or label[:3] != next_label[:3]:
                continue
            if int(next_label[3:]) <= int(label[3:]) + 1:
                continue
            if (end - start) >= 3 and ev / (end - start) <= 0.35:
                for pos in range(start, end):
                    labels[pos] = prev_label

    def _segments(self, raw_words: list[str], labels: list[str | None]) -> list[dict[str, str]]:
        segments: list[dict[str, str]] = []
        current_id: str | None = None
        current_words: list[str] = []
        for raw, label in zip(raw_words, labels):
            if label is None:
                continue
            clean_raw = _NON_WORD_RE.sub("", raw)
            if label in self.muqattaat_ids and clean_raw in _MUQATTAAT:
                raw = clean_raw
            if label != current_id:
                if current_id and current_words:
                    segments.append({"id": current_id, "text": " ".join(current_words)})
                current_id = label
                current_words = [raw]
            else:
                current_words.append(raw)
        if current_id and current_words:
            segments.append({"id": current_id, "text": " ".join(current_words)})
        return segments

    def _restore_fatiha_basmala(
        self, segments: list[dict[str, str]], raw_words: list[str], intro_offset: int
    ) -> None:
        if not segments or segments[0]["id"] != "001002" or intro_offset < 4:
            return
        bismala = [w for w, _ in _canon_tokens("بسم الله الرحمن الرحيم")]
        intro_words = [w for w, _ in _canon_tokens(" ".join(raw_words[:intro_offset]))]
        if intro_words[-4:] == bismala:
            segments.insert(0, {"id": "001001", "text": " ".join(raw_words[intro_offset - 4:intro_offset])})
