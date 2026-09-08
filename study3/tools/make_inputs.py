#!/usr/bin/env python3
"""
make_inputs.py - strip a private gold file down to the inputs a system is allowed
to see, so a baseline or an agent can never read the answers.

    python3 study3/tools/make_inputs.py --gold <private gold.jsonl> --out inputs.jsonl

Kept per chunk: review_id, chunk_idx, n_chunks, ayah_id, transcript,
transcript_tokens, reference_text, reference_tokens. A record's opening formula
is emitted as chunk_idx -1 with an empty reference, matching the evaluator.
Dropped: events, chunk labels, review_status, reviewed_by, preamble labels,
transcript hashes, and every other annotation field.

The output still contains transcripts, so it inherits the gold set's
confidentiality: it reveals which recordings were selected. Use it for scoring
baselines, never as an agent's development pool.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KEEP = ("ayah_id", "transcript", "transcript_tokens", "reference_text", "reference_tokens")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    text = a.gold.read_text(encoding="utf-8")
    recs = ([json.loads(l) for l in text.splitlines() if l.strip()]
            if a.gold.suffix == ".jsonl" else json.loads(text))
    n = 0
    with a.out.open("w", encoding="utf-8") as f:
        for r in recs:
            chunks = r.get("chunks", [])
            pre = r.get("preamble") or {}
            if pre.get("text") and (pre.get("label") or pre.get("segments")):
                toks = pre["text"].split()
                f.write(json.dumps({"review_id": r.get("review_id"), "chunk_idx": -1,
                                    "n_chunks": len(chunks), "ayah_id": None,
                                    "transcript": pre["text"], "transcript_tokens": toks,
                                    "reference_text": "", "reference_tokens": []},
                                   ensure_ascii=False) + "\n")
                n += 1
            for c in chunks:
                row = {"review_id": r.get("review_id"), "chunk_idx": c.get("chunk_idx"),
                       "n_chunks": len(chunks), **{k: c.get(k) for k in KEEP}}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} input chunks -> {a.out} (no answers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
