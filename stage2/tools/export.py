#!/usr/bin/env python3
"""
export.py — build the Stage-2 (within-ayah mistake events) dataset from the
Stage-1 gold split + the Review-tab event labels, with surrogate ids.

    python3 stage2/tools/export.py                 # writes stage2/data/{train,test}.jsonl + release/
    python3 stage2/tools/export.py --check         # validate + print stats, write nothing

Inputs (root of the repo, production-derived, gitignored):
    data/train.csv, data/test.csv      Stage-1 frozen split (tools/split_dataset.py)
    data/bot_events.jsonl              Review-tab labels, one line per recording

Outputs (de-identified, committed):
    stage2/data/train.jsonl, stage2/data/test.jsonl   one line per chunk (SCHEMA.md)
    release/ids.private.json                          recording_id -> row_id (gitignored)

Surrogate ids: rows are numbered in the order they appear in the frozen split
files (seeded, reproducible): train-001..., test-001.... Chunk id = row id +
chunk index: train-001-c00. learner_id is dropped entirely.

Span derivation (SCHEMA.md, question 4): labelers write verbatim `words`
(hypothesis) and `ref` (reference). This script derives `hyp_span` / `ref_span`
as [start, end) token indices by locating those words in the canonicalized
chunk / reference token lists. If a span cannot be located it is null and the
chunk's `label_status` is downgraded to `needs_review` (never silently guessed).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval import canon  # noqa: E402  — the one metric-only canonicalizer, shared with Stage 1

DATA = ROOT / "data"
OUT = ROOT / "stage2" / "data"
RELEASE = ROOT / "release"
QURAN = json.load(open(DATA / "quran_ref.json", encoding="utf-8"))
REF = {a["id"]: a for s in QURAN.values() for a in s}
# Long ayahs are stored as sub-parts (002255001, 002255002, ...); join them.
for _sid, _rows in QURAN.items():
    _parts: dict[str, list[dict]] = {}
    for _a in _rows:
        if len(_a["id"]) == 9:
            _parts.setdefault(_a["id"][:6], []).append(_a)
    for _aid, _ps in _parts.items():
        REF.setdefault(_aid, {"id": _aid, "ar": " ".join(p["ar"] for p in _ps),
                              "clean": " ".join(p["clean"] for p in _ps)})

TYPES = {"restart_repeat", "full_repeat", "stutter", "self_correction", "substitution",
         "omission", "insertion", "word_order", "truncation", "asr_garble"}
VERDICTS = {"benign", "corrected", "mistake", "uncertain"}


def find_span(tokens: list[str], words: str) -> list[int] | None:
    """Locate canonicalized `words` as a contiguous sub-sequence of `tokens`.
    Returns [start, end) or None. Prefers the LAST occurrence for hypothesis
    (labelers usually cite the final attempt) — callers pass reversed=True."""
    w = canon(words)
    if not w:
        return None
    n, k = len(tokens), len(w)
    hits = [i for i in range(n - k + 1) if tokens[i:i + k] == w]
    if not hits:
        # tolerate a single-token fuzzy match on prefix (final-letter drops)
        if k == 1:
            hits = [i for i, t in enumerate(tokens) if t.startswith(w[0][:-1]) and len(w[0]) > 2]
        if not hits:
            return None
    return [hits[0], hits[0] + k]


def derive(chunk_tokens: list[str], ref_tokens: list[str], ev: dict, is_last: bool) -> tuple[dict, list[str]]:
    """Return (event with spans, problems)."""
    problems: list[str] = []
    t, v = ev.get("type", ""), ev.get("verdict", "")
    if t not in TYPES:
        problems.append(f"unknown type {t!r}")
    if v not in VERDICTS:
        problems.append(f"unknown verdict {v!r}")
    hyp_words, ref_words = (ev.get("words") or "").strip(), (ev.get("ref") or "").strip()
    hyp_span = find_span(chunk_tokens, hyp_words) if hyp_words else None
    ref_span = None
    if ref_words and "..." not in ref_words:
        ref_span = find_span(ref_tokens, ref_words)
    elif ref_words and "..." in ref_words:  # "start ... end" shorthand for a tail
        a, b = [x.strip() for x in ref_words.split("...", 1)]
        sa, sb = find_span(ref_tokens, a), find_span(ref_tokens, b)
        if sa and sb:
            ref_span = [sa[0], sb[1]]
    if t in ("restart_repeat", "full_repeat", "stutter") and hyp_span is not None:
        # Labelers cite the abandoned first attempt; the span covers both copies
        # (the echo follows immediately by definition), so a prediction that
        # flags EITHER copy matches the event (SCHEMA.md §5).
        k = hyp_span[1] - hyp_span[0]
        hyp_span = [hyp_span[0], min(hyp_span[1] + k, len(chunk_tokens))]
    if t == "truncation":
        # what was NOT recited = reference tail after the last matched hyp token
        if ref_span is None:
            ref_span = [len(chunk_tokens), len(ref_tokens)] if len(chunk_tokens) < len(ref_tokens) else None
        if hyp_span is None:
            hyp_span = [len(chunk_tokens), len(chunk_tokens)]
        # Schema default Q2: last chunk of a recording -> benign, else mistake
        expected = "benign" if is_last else "mistake"
        if v != expected:
            problems.append(f"truncation verdict {v} but is_last={is_last} (schema Q2 says {expected})")
    if t == "omission":
        if hyp_span is None and ref_span is not None:
            # insertion point in hyp: after the hyp token matching the ref token before the gap
            prev = ref_tokens[ref_span[0] - 1] if ref_span[0] > 0 else None
            pos = 0
            if prev and prev in chunk_tokens:
                pos = len(chunk_tokens) - chunk_tokens[::-1].index(prev)
            hyp_span = [pos, pos]
    if hyp_words and hyp_span is None:
        problems.append(f"hyp words not found: {hyp_words!r}")
    if ref_words and ref_span is None and t != "full_repeat":
        problems.append(f"ref words not found: {ref_words!r}")
    out = {
        "type": t, "verdict": v,
        "hyp_words": hyp_words, "ref_words": ref_words,
        "hyp_span": hyp_span, "ref_span": ref_span,
        "note": ev.get("note", ""),
    }
    return out, problems


def load_events() -> dict[str, dict]:
    p = DATA / "bot_events.jsonl"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            out[d["recording_id"]] = d["review"]
    return out


def build(split: str, events: dict[str, dict], ids: dict[str, str]) -> tuple[list[dict], list[str]]:
    rows = list(csv.DictReader(open(DATA / f"{split}.csv", encoding="utf-8")))
    chunks, problems = [], []
    for n, r in enumerate(rows, 1):
        rid = r["recording_id"]
        row_id = f"{split}-{n:03d}"
        ids[rid] = row_id
        segs = json.loads(r["transcript_split_by_ayahs"] or "[]")
        if not segs:  # non-Quran rows have no chunks
            continue
        rev = events.get(rid)
        for i, seg in enumerate(segs):
            ayah = REF.get(seg["id"])
            if ayah is None:
                problems.append(f"{row_id}-c{i:02d}: unknown ayah {seg['id']}")
                continue
            chunk_tokens = canon(seg.get("transcript", ""))
            ref_tokens = canon(ayah["clean"])
            is_last = i == len(segs) - 1
            rec = {
                "chunk_id": f"{row_id}-c{i:02d}", "row_id": row_id, "chunk_idx": i,
                "n_chunks": len(segs), "is_last_chunk": is_last,
                "ayah_id": seg["id"], "chunk_text": seg.get("transcript", ""),
                "reference_text": ayah["clean"],
                "confidence": (r.get("confidence") or "high").strip().lower(),
                "label_status": "unlabeled", "labeled_by": None, "events": None,
            }
            if rev is not None:
                cl = next((c for c in rev.get("chunks", []) if c.get("idx") == i), None)
                if len(rev.get("chunks", [])) != len(segs) and i == 0:
                    problems.append(f"{row_id}: label file has {len(rev.get('chunks', []))} chunks, gold split has {len(segs)} (extra labels ignored)")
                if cl is not None and cl.get("ayah_id") != seg["id"]:
                    problems.append(f"{rec['chunk_id']}: label ayah {cl.get('ayah_id')} != gold split ayah {seg['id']}")
                    cl = None
                if cl is not None:
                    evs, status = [], "machine" if "pending" in (rev.get("labeled_by") or "") else "reviewed"
                    for ev in cl.get("events", []):
                        e, pr = derive(chunk_tokens, ref_tokens, ev, is_last)
                        evs.append(e)
                        for msg in pr:
                            problems.append(f"{rec['chunk_id']}: {msg}")
                            status = "needs_review"
                    rec.update(events=evs, label_status=status, labeled_by=rev.get("labeled_by"))
            chunks.append(rec)
    return chunks, problems


def stats(chunks: list[dict]) -> str:
    lab = [c for c in chunks if c["events"] is not None]
    evs = [e for c in lab for e in c["events"]]
    clean = sum(1 for c in lab if not c["events"])
    from collections import Counter
    ty = Counter((e["type"], e["verdict"]) for e in evs)
    st = Counter(c["label_status"] for c in chunks)
    return (f"chunks={len(chunks)} rows={len({c['row_id'] for c in chunks})} labeled={len(lab)} "
            f"clean={clean} events={len(evs)} status={dict(st)}\n  events by (type,verdict): {dict(ty)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    events = load_events()
    ids: dict[str, str] = {}
    allp = []
    out = {}
    for split in ("train", "test"):
        chunks, problems = build(split, events, ids)
        out[split] = chunks
        allp += problems
        print(f"[{split}] {stats(chunks)}")
    if allp:
        print(f"\n{len(allp)} problem(s) (chunks marked needs_review):")
        for p in allp:
            print("  -", p)
    if a.check:
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for split, chunks in out.items():
        with open(OUT / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
    RELEASE.mkdir(exist_ok=True)
    json.dump(ids, open(RELEASE / "ids.private.json", "w"), indent=1)
    print(f"\nwrote {OUT}/train.jsonl, test.jsonl; id map -> release/ids.private.json (gitignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
