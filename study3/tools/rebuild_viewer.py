#!/usr/bin/env python3
"""Regenerate the corpus viewer's embedded dataset from recordings.jsonl.

The viewer carries the corpus as a JSON blob inside its own HTML. That blob
drifts the moment the corpus changes, so it is rebuilt from the data rather
than edited: the HTML shell and the page's script are left untouched, only the
dataset and the counts in the header are replaced.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--html", type=Path, required=True)
    a = ap.parse_args()

    recs = [json.loads(l) for l in a.corpus.read_text(encoding="utf-8").splitlines() if l.strip()]
    html = a.html.read_text(encoding="utf-8")
    m = re.search(r'(<script id="dataset" type="application/json">)(.*?)(</script>)', html, re.S)
    if not m:
        return print("viewer: dataset block not found") or 1
    data = json.loads(m.group(2))

    events = [e for r in recs for e in (r.get("events") or [])]
    units = [u for r in recs for u in r["units"]]
    reps = [e for e in events if e["label"] == "repetition_benign"]
    s = data["corpus"]["summary"]
    s.update({
        "recordings": len(recs), "units": len(units), "events": len(events),
        "event_counts": dict(Counter(e["label"] for e in events)),
        "source_review_status_counts": dict(Counter(r.get("source_review_status") for r in recs)),
        "cases_with_review_questions": [r["case_id"] for r in recs if r.get("review_questions")],
        "repetition_events": len(reps),
        "repetition_locations": sum(len(e.get("hyp_locations") or []) for e in reps),
        "cross_chunk_events": [
            {"case_id": r["case_id"], "event_id": e["event_id"], "label": e["label"]}
            for r in recs for e in (r.get("events") or [])
            if len({l["chunk_idx"] for l in (e.get("hyp_locations") or [])}) > 1],
        "multi_location_events": sum(1 for e in events if len(e.get("hyp_locations") or []) > 1),
        "train_cases": sum(1 for r in recs if r["case_id"].startswith("train")),
        "gold_cases": sum(1 for r in recs if r["case_id"].startswith("r")),
    })
    data["corpus"]["records"] = recs
    drafts = [r["case_id"] for r in recs if r.get("review_status") != "approved"]
    data["changed"] = drafts

    blob = json.dumps(data, ensure_ascii=False, separators=(", ", ": "))
    html = html[:m.start(2)] + blob + html[m.end(2):]
    html = re.sub(r"<p>[\d,]+ recordings · [\d,]+ units · [\d,]+ events\.",
                  f"<p>{len(recs)} recordings · {len(units):,} units · {len(events)} events.", html, count=1)

    a.html.write_text(html, encoding="utf-8")
    print(f"viewer rebuilt: {len(recs)} recordings, {len(units)} units, {len(events)} events")
    print(f"  highlighted as unapproved: {drafts or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
