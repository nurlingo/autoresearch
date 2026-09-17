#!/usr/bin/env python3
"""Score the current solution.py against the annotated train split, locally.

Train answers ship in this workspace, so there is nothing to ask an owner for:
load them, run the solution over the same input view the grader will use, and
report the metrics the grader reports.

This is development feedback. The held-back split is scored once, elsewhere,
after the solution is frozen -- it is never reachable from here.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Do not leave __pycache__ in the workspace: the launcher hashes every prepared
# file before starting a run, and a stray .pyc makes a clean workspace look
# tampered with.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eval21  # shipped alongside this script; standard library only


def input_view(record):
    """Exactly the dicts detect_events() is handed -- no answers on them."""
    n_chunks = sum(u["chunk_idx"] >= 0 for u in record["units"])
    for u in record["units"]:
        yield {
            "case_id": record["case_id"], "chunk_idx": u["chunk_idx"],
            "n_chunks": n_chunks, "ayah_id": u.get("ayah_id"),
            "transcript": u["transcript"],
            "transcript_tokens": list(u["transcript_tokens"]),
            "reference_text": u["reference_text"],
            "reference_tokens": list(u["reference_tokens"]),
        }


def record_scoring(metrics, crashes):
    """Append this scoring to .scores.jsonl, which the run loop reads.

    The stopping rule is decided from this history rather than from the agent's
    account of its own progress: it counts distinct solution versions scored
    since the train score last reached a new best.
    """
    import hashlib, time
    row = {"t": round(time.time()), "micro_f1": metrics["micro_f1"], "crashes": crashes,
           "solution_sha256": hashlib.sha256((HERE / "solution.py").read_bytes()).hexdigest()}
    try:
        with open(HERE / ".scores.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass


def main() -> int:
    corpus = eval21.load_corpus(HERE / "data/corpus-train.jsonl")
    spec = importlib.util.spec_from_file_location("solution", HERE / "solution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    solution = module.Solution()

    predictions, crashes = {}, 0
    for record in corpus:
        rows = []
        for chunk in input_view(record):
            try:
                events = solution.detect_events(chunk)
            except Exception as exc:                       # noqa: BLE001
                crashes += 1
                print(f"  crash on {record['case_id']} chunk {chunk['chunk_idx']}: "
                      f"{type(exc).__name__}: {exc}", file=sys.stderr)
                continue
            if not isinstance(events, list):
                crashes += 1
                continue
            for event in events:
                if isinstance(event, dict):
                    rows.append({"chunk_idx": chunk["chunk_idx"],
                                 "label": event.get("label"),
                                 "hyp_span": event.get("hyp_span"),
                                 "ref_span": event.get("ref_span")})
        predictions[record["case_id"]] = rows

    metrics = eval21.score(corpus, predictions)
    record_scoring(metrics, crashes)
    if "--json" in sys.argv:
        print(json.dumps({"split": "train", "crashes": crashes, "metrics": metrics},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"train split: {metrics['counts']['cases']} recordings, "
          f"{metrics['counts']['units']} units, "
          f"{metrics['counts']['gold_events']} annotated events")
    if crashes:
        print(f"CRASHES: {crashes}")
    print(f"\n  micro F1 (primary)   {metrics['micro_f1']:.4f}")
    print(f"  precision / recall   {metrics['precision']:.4f} / {metrics['recall']:.4f}")
    print(f"  macro F1             {metrics['macro_f1']:.4f}")
    print(f"  strict micro F1      {metrics['strict_micro_f1']:.4f}")
    print(f"\n  {'label':<24}{'train':>6}{'pred':>6}{'F1':>8}")
    for label, row in sorted(metrics["per_label"].items(), key=lambda x: -x[1]["gold"]):
        print(f"  {label:<24}{row['gold']:>6}{row['pred']:>6}{row['f1']:>8.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
