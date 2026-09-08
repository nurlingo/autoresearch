#!/usr/bin/env python3
"""
make_reviewer_sample.py - build the anonymous reviewer sample that Track 3 asks
for ("a dataset sample for review").

    python3 study3/tools/make_reviewer_sample.py --gold <private gold.jsonl> \
        --out <directory OUTSIDE this repository> [--n 30]

Selection is deterministic (sorted by review_id, no randomness): take the
smallest set of records that covers every label in the taxonomy at least once,
then fill up to --n with the records that add the most remaining events, and
finally with clean-only records so the sample keeps a realistic share of
chunks that carry nothing.

THE OUTPUT CONTAINS GOLD ANSWERS. It is for human paper reviewers only. Never
commit it, and never place it in an agent runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KEEP_CHUNK = ("chunk_idx", "ayah_id", "transcript", "transcript_tokens",
              "reference_text", "reference_tokens", "events")
KEEP_EVENT = ("label", "hyp_words", "ref_words", "hyp_span", "ref_span", "note")


def labels_of(rec: dict) -> set[str]:
    out = {e["label"] for c in rec.get("chunks", []) for e in c.get("events") or []}
    p = rec.get("preamble") or {}
    if p.get("label"):
        out.add(p["label"])
    return out


def n_events(rec: dict) -> int:
    return sum(len(c.get("events") or []) for c in rec.get("chunks", []))


def select(recs: list[dict], n: int) -> list[dict]:
    recs = sorted(recs, key=lambda r: str(r.get("review_id")))
    all_labels = sorted({l for r in recs for l in labels_of(r)})
    chosen: list[dict] = []
    covered: set[str] = set()
    # 1. cover every label, rarest first
    freq = {l: sum(1 for r in recs if l in labels_of(r)) for l in all_labels}
    for lab in sorted(all_labels, key=lambda l: (freq[l], l)):
        if lab in covered:
            continue
        pick = next((r for r in recs if r not in chosen and lab in labels_of(r)), None)
        if pick:
            chosen.append(pick)
            covered |= labels_of(pick)
    # 2. richest remaining records
    rest = [r for r in recs if r not in chosen]
    for r in sorted(rest, key=lambda r: (-n_events(r), str(r.get("review_id")))):
        if len(chosen) >= n:
            break
        if n_events(r):
            chosen.append(r)
    # 3. clean-only records, so reviewers see the majority class too
    for r in [r for r in recs if r not in chosen and not n_events(r)]:
        if len(chosen) >= n:
            break
        chosen.append(r)
    return sorted(chosen[:n], key=lambda r: str(r.get("review_id")))


def strip(rec: dict) -> dict:
    out = {"review_id": rec.get("review_id"), "chunks": []}
    p = rec.get("preamble")
    if p:
        out["opening_formula"] = {"text": p.get("text"), "label": p.get("label")}
    for c in rec.get("chunks", []):
        cc = {k: c.get(k) for k in KEEP_CHUNK if k in c}
        cc["events"] = [{k: e.get(k) for k in KEEP_EVENT if k in e}
                        for e in (c.get("events") or [])]
        cc["label"] = "clean" if not cc["events"] else None
        out["chunks"].append(cc)
    return out


README = """# Reviewer sample - Task B annotation, taxonomy v0.19

{n} of the {total} human-approved recording cases ({chunks} ayah chunks,
{events} within-ayah events, {clean} chunks with no event). Provided so that
reviewers can judge annotation quality directly. Selection is deterministic and
covers every label in the taxonomy at least once, including the labels that
occur only once in the full set; it is therefore denser in events than the full
set, which is {full_clean_pct:.0f}% clean.

## Record format

One JSON object per line of `sample.jsonl`:

    review_id          surrogate reviewer identifier
    opening_formula    the isti'adhah or basmala preceding the recitation, when present
    chunks[]           one entry per assigned ayah
      ayah_id          surah and ayah, SSSAAA
      transcript       unchanged ASR text assigned to this ayah
      transcript_tokens, reference_tokens
                       whitespace token arrays that the spans index
      reference_text   exact clean Quran reference for the ayah
      label            "clean" when the reviewed chunk carries no event
      events[]         label, verbatim words, half-open spans, reviewer note

Spans are zero-based and end-exclusive. An empty hypothesis span is an omission
anchor; an empty reference span is an insertion point. Repetition and corrected
events span every attempt involved.

## Labels

{labels}

## Provenance

Production recordings from a Quran memorization application, contributed by
adult users under terms of service that disclose review for service
improvement. Text only: no audio, and production recording and learner
identifiers are replaced by surrogate reviewer identifiers. The Quran is a
closed public canon, so the transcripts carry essentially no personal
information. Reviewer notes are the annotators' own wording.

This sample carries gold answers. It is supplementary material for paper
review and is not part of any public release.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()

    text = a.gold.read_text(encoding="utf-8")
    recs = ([json.loads(l) for l in text.splitlines() if l.strip()]
            if a.gold.suffix == ".jsonl" else json.loads(text))
    picked = select(recs, a.n)
    stripped = [strip(r) for r in picked]

    a.out.mkdir(parents=True, exist_ok=True)
    with (a.out / "sample.jsonl").open("w", encoding="utf-8") as f:
        for r in stripped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    chunks = sum(len(r["chunks"]) for r in stripped)
    events = sum(len(c["events"]) for r in stripped for c in r["chunks"])
    clean = sum(1 for r in stripped for c in r["chunks"] if not c["events"])
    counts: dict[str, int] = {}
    for r in stripped:
        for c in r["chunks"]:
            for e in c["events"]:
                counts[e["label"]] = counts.get(e["label"], 0) + 1
        if r.get("opening_formula", {}).get("label"):
            lab = r["opening_formula"]["label"]
            counts[lab] = counts.get(lab, 0) + 1
    all_chunks = sum(len(r.get("chunks", [])) for r in recs)
    all_clean = sum(1 for r in recs for c in r.get("chunks", []) if not (c.get("events") or []))
    (a.out / "README.md").write_text(README.format(
        n=len(stripped), total=len(recs), chunks=chunks, events=events, clean=clean,
        full_clean_pct=100 * all_clean / all_chunks,
        labels="\n".join(f"- `{k}` ({v})" for k, v in sorted(counts.items()))), encoding="utf-8")

    missing = {l for r in recs for l in labels_of(r)} - set(counts)
    print(f"{len(stripped)} records, {chunks} chunks, {events} events, {clean} clean -> {a.out}")
    print("labels covered:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if missing:
        print("MISSING LABELS:", missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
