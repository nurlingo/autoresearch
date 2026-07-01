"""
solution.py — transcript-only Stage 1 algorithm (detection + split).

Given a Quran recitation transcript (no harakat), decide which ayahs were
recited and split the transcript by ayah. See PROGRAM.md / eval.py for the
contract and metric.

Approach
--------
1. Normalize words (fold alef/hamza/ya variants, drop harakat) — mirrors the
   metric canonicalizer so alignment operates in the same space.
2. Detect the surah by voting: which surah's token-bigrams best cover the
   transcript. Abstain when coverage is too low (non-Quran).
3. Align the transcript token sequence to the surah's token sequence with a
   semi-global DP (free start/end gaps, cheap reference skips so unrecited
   ayahs cost little). Each transcript token inherits the ayah id of the ref
   token it aligns to.
4. Group consecutive transcript words by ayah id -> per-ayah split.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REF_PATH = Path(os.getenv("QURAN_REF_PATH", DATA_DIR / "quran_ref.json"))

_HARAKAT_RE = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا",
         "ٱ": "ا", "ى": "ي", "ؤ": "ء",
         "ئ": "ء"}
_NONLETTER_RE = re.compile("[^ء-ي]")


def _is_subseq(a: str, b: str) -> bool:
    """True if a is a subsequence of b (a's chars appear in order within b)."""
    it = iter(b)
    return all(ch in it for ch in a)


def norm_word(w: str) -> str:
    w = unicodedata.normalize("NFKC", w or "")
    w = w.replace("ـ", "")
    for a, b in _FOLD.items():
        w = w.replace(a, b)
    w = _HARAKAT_RE.sub("", w)
    w = _NONLETTER_RE.sub("", w)
    return w


# alignment scores
MATCH = 1.0
MISMATCH = -0.5
GAP_REF = -0.05     # skip a reference token (unrecited ayah words) — cheap
GAP_TRANS = -0.6    # extra transcript token not in reference
ABSTAIN_COVERAGE = 0.15  # min transcript-bigram coverage to treat as Quran
AYAH_MIN_MATCH = 3       # keep ayah if >= this many of its words matched, OR
AYAH_MIN_COVER = 0.4     # >= this fraction of the ayah's words matched
CAND_MARGIN = 0.7        # keep surahs scoring >= this * best vote as candidates
CAND_LIMIT = 5           # max candidate surahs to align against

# The 14 disconnected letters (muqatta'at). When a surah opens with these,
# reciters spell the letter *names* ("ألف لام ميم صاد"), which never match the
# joined reference form ("المص"). Map each spoken name back to its letter(s).
MUQ_LETTERS = set("المصركهيعطسحقن")
LETTER_NAME = {
    "الف": "ا", "لام": "ل", "ميم": "م", "صاد": "ص", "راء": "ر", "را": "ر",
    "كاف": "ك", "هاء": "ه", "ها": "ه", "ياء": "ي", "يا": "ي", "عين": "ع",
    "طاء": "ط", "طا": "ط", "سين": "س", "حاء": "ح", "حا": "ح", "قاف": "ق",
    "نون": "ن", "الف لام": "ال",
    # already-joined two-letter names spoken as one token
    "طه": "طه", "يس": "يس", "حم": "حم", "طس": "طس",
}


class Solution:
    def __init__(self) -> None:
        self.quran: dict[str, list[dict[str, str]]] = json.loads(
            REF_PATH.read_text(encoding="utf-8")
        )
        # Per surah: flat token list + parallel ayah-id list.
        self.surah_tokens: dict[str, list[str]] = {}
        self.surah_ayahids: dict[str, list[str]] = {}
        self.surah_bigrams: dict[str, set[str]] = {}
        self.ayah_len: dict[str, int] = {}
        for sid, ayahs in self.quran.items():
            # Skip pseudo-surah blocks (e.g. '999xxx'): keep only 001..114.
            if not (len(sid) == 3 and sid.isdigit() and 1 <= int(sid) <= 114):
                continue
            toks: list[str] = []
            ids: list[str] = []
            for a in ayahs:
                # Long ayahs are stored as 9/12-digit sub-segments; the gold uses
                # the 6-digit base ayah id, so collapse to it.
                base = a["id"][:6]
                for w in a.get("clean", "").split():
                    t = norm_word(w)
                    if t:
                        toks.append(t)
                        ids.append(base)
                        self.ayah_len[base] = self.ayah_len.get(base, 0) + 1
            self.surah_tokens[sid] = toks
            self.surah_ayahids[sid] = ids
            self.surah_bigrams[sid] = {
                toks[i] + " " + toks[i + 1] for i in range(len(toks) - 1)
            }

        # Index unique muqatta'at openings: a surah's leading run of
        # single-token, pure-letter ayahs -> [(ayah_id, letters), ...].
        # Ambiguous keys (e.g. "الم", shared by many surahs) are dropped, since
        # the letters alone can't say which surah was meant.
        muq: dict[str, list[tuple[str, str]]] = {}
        for sid, ayahs in self.quran.items():
            if not (len(sid) == 3 and sid.isdigit() and 1 <= int(sid) <= 114):
                continue
            entries: list[tuple[str, str]] = []
            for a in ayahs[:2]:
                ct = [norm_word(w) for w in a.get("clean", "").split()]
                ct = [t for t in ct if t]
                if len(ct) == 1 and len(ct[0]) <= 5 and set(ct[0]) <= MUQ_LETTERS:
                    entries.append((a["id"][:6], ct[0]))
                else:
                    break
            if entries:
                key = "".join(t for _, t in entries)
                muq[key] = entries if key not in muq else None  # mark ambiguous
        self.muq = {k: v for k, v in muq.items() if v is not None}

    @staticmethod
    def _strip_devotional(toks: list[str]) -> list[str]:
        """Drop a leading isti'adha / basmala for surah voting: reciters often
        prepend them but they are not part of the assigned ayah, and the basmala
        matches many surahs (e.g. 027030) which derails the vote. Alignment
        still sees the full transcript, so these words remain in the output."""
        i = 0
        if i < len(toks) and toks[i] == "اعوذ":
            for j in range(i + 1, min(i + 8, len(toks))):
                if toks[j] == "الرجيم":
                    i = j + 1
                    break
        if toks[i:i + 4] == ["بسم", "الله", "الرحمن", "الرحيم"]:
            i += 4
        return toks[i:] or toks

    # ------------------------------------------------------------------
    def _candidate_surahs(self, toks: list[str]) -> tuple[list[str], float]:
        """Rank surahs by transcript-bigram coverage. Return (top candidates,
        best coverage). Several near-tied surahs can share the same phrase
        (e.g. 073020 vs 002110), so the aligner picks the final one."""
        toks = self._strip_devotional(toks)
        if len(toks) < 2:
            cands = [sid for sid, st in self.surah_tokens.items() if toks and toks[0] in st]
            return cands[:CAND_LIMIT], (1.0 if cands else 0.0)
        query_bigrams = [toks[i] + " " + toks[i + 1] for i in range(len(toks) - 1)]
        total = len(query_bigrams)
        scored = []
        for sid, bg in self.surah_bigrams.items():
            hits = sum(1 for b in query_bigrams if b in bg)
            if hits:
                scored.append((hits, sid))
        if not scored:
            return [], 0.0
        # Highest vote first; break vote ties toward the lower surah id so a
        # phrase shared across surahs (e.g. "الحمد لله رب العالمين") keeps the
        # canonical/earliest surah in the shortlist.
        scored.sort(key=lambda hs: (-hs[0], hs[1]))
        best_hits = scored[0][0]
        cutoff = max(1, best_hits * CAND_MARGIN)
        cands = [sid for h, sid in scored if h >= cutoff][:CAND_LIMIT]
        return cands, best_hits / total if total else 0.0

    def _align(self, toks: list[str], sid: str) -> list[tuple[str | None, bool]]:
        """Return, per transcript token, (aligned ayah id or None, is_match)."""
        ref = self.surah_tokens[sid]
        ids = self.surah_ayahids[sid]
        n, m = len(toks), len(ref)
        NEG = float("-inf")
        dp = [[NEG] * (m + 1) for _ in range(n + 1)]
        bt = [[0] * (m + 1) for _ in range(n + 1)]  # 0 diag,1 up(trans gap),2 left(ref gap)
        dp[0][0] = 0.0
        for j in range(1, m + 1):
            dp[0][j] = 0.0  # free leading ref skip
            bt[0][j] = 2
        for i in range(1, n + 1):
            dp[i][0] = dp[i - 1][0] + GAP_TRANS
            bt[i][0] = 1
        for i in range(1, n + 1):
            ti = toks[i - 1]
            dpi = dp[i]
            dpi1 = dp[i - 1]
            bti = bt[i]
            for j in range(1, m + 1):
                s = MATCH if ti == ref[j - 1] else MISMATCH
                diag = dpi1[j - 1] + s
                up = dpi1[j] + GAP_TRANS
                left = dpi[j - 1] + GAP_REF
                best = diag
                b = 0
                if up > best:
                    best, b = up, 1
                if left > best:
                    best, b = left, 2
                dpi[j] = best
                bti[j] = b
        best_j, best_val = m, dp[n][m]
        for j in range(m + 1):
            if dp[n][j] > best_val:
                best_val, best_j = dp[n][j], j
        i, j = n, best_j
        out: list[tuple[str | None, bool]] = [(None, False)] * n
        while i > 0:
            b = bt[i][j]
            if b == 0:
                out[i - 1] = (ids[j - 1], toks[i - 1] == ref[j - 1])
                i, j = i - 1, j - 1
            elif b == 1:
                out[i - 1] = (None, False)
                i -= 1
            else:
                j -= 1
        return out

    def _try_muqattaat(self, words: list[str], toks: list[str]) -> dict | None:
        """If the whole transcript is spelled-out disconnected letters, map it
        to the surah that opens with them and split by ayah."""
        letters = ""
        seen = False
        for t in toks:
            if not t:
                continue
            nm = LETTER_NAME.get(t)
            if nm is None:
                return None  # a non-letter-name token -> not a muqatta'at row
            letters += nm
            seen = True
        if not seen:
            return None
        entries = self.muq.get(letters)
        if entries is None:
            # ASR sometimes drops a letter (e.g. "كهيعص" heard as "كهعص"). If the
            # spoken letters are a subsequence of exactly one single-ayah key,
            # accept it — the whole thing is one ayah anyway.
            hits = [
                e for k, e in self.muq.items()
                if len(e) == 1 and _is_subseq(letters, k)
            ]
            if len(hits) != 1:
                return None
            entries = hits[0]
        if len(entries) == 1:  # whole transcript is one muqatta'at ayah
            return {"ayahs": [{"id": entries[0][0], "text": " ".join(words)}]}
        # Assign words to ayahs by consuming the expected number of letters.
        ayahs: list[dict[str, str]] = []
        wi, acc, ei = 0, 0, 0
        buf: list[str] = []
        for w in words:
            buf.append(w)
            t = toks[wi] if wi < len(toks) else ""
            wi += 1
            if t:
                acc += len(LETTER_NAME[t])
                if ei < len(entries) and acc >= len(
                    "".join(x[1] for x in entries[: ei + 1])
                ):
                    ayahs.append({"id": entries[ei][0], "text": " ".join(buf)})
                    buf, ei = [], ei + 1
        if buf and ayahs:
            ayahs[-1]["text"] += " " + " ".join(buf)
        return {"ayahs": ayahs} if ayahs else None

    def process(self, transcript: str) -> dict:
        words = (transcript or "").split()
        toks = [norm_word(w) for w in words]
        keep = [i for i, t in enumerate(toks) if t]
        core = [toks[i] for i in keep]
        if not core:
            return {"abstain": True}

        muq = self._try_muqattaat(words, toks)
        if muq is not None:
            return muq

        cands, coverage = self._candidate_surahs(core)
        if not cands or coverage < ABSTAIN_COVERAGE:
            return {"abstain": True}

        # Break near-ties by actual alignment quality: the surah whose tokens
        # match the transcript best (most matched tokens) wins.
        aligned = None
        best_matched = -1
        for sid in cands:
            al = self._align(core, sid)
            mc = sum(1 for _, ok in al if ok)
            if mc > best_matched:
                best_matched, aligned = mc, al
        # Drop ayahs that only caught a stray token or two: an ayah counts as
        # recited only if enough of ITS reference words were matched. Prevents
        # boundary "extra ayah" false positives.
        matched: dict[str, int] = {}
        for aid, ok in aligned:
            if aid is not None and ok:
                matched[aid] = matched.get(aid, 0) + 1
        kept = {
            aid for aid, c in matched.items()
            if c >= AYAH_MIN_MATCH or c / max(self.ayah_len.get(aid, 1), 1) >= AYAH_MIN_COVER
        }
        core_ids = [aid if aid in kept else None for aid, _ in aligned]

        word_ids: list[str | None] = [None] * len(words)
        for k, orig_idx in enumerate(keep):
            word_ids[orig_idx] = core_ids[k]
        # fill unaligned words with nearest previous, then next
        last = None
        for i in range(len(words)):
            if word_ids[i] is None:
                word_ids[i] = last
            else:
                last = word_ids[i]
        nxt = None
        for i in range(len(words) - 1, -1, -1):
            if word_ids[i] is None:
                word_ids[i] = nxt
            else:
                nxt = word_ids[i]

        if all(w is None for w in word_ids):
            return {"abstain": True}

        ayahs: list[dict[str, str]] = []
        cur_id = word_ids[0]
        buf = [words[0]]
        for i in range(1, len(words)):
            if word_ids[i] == cur_id:
                buf.append(words[i])
            else:
                ayahs.append({"id": cur_id, "text": " ".join(buf)})
                cur_id = word_ids[i]
                buf = [words[i]]
        ayahs.append({"id": cur_id, "text": " ".join(buf)})
        return {"ayahs": ayahs}
