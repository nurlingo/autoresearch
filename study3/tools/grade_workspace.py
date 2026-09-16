#!/usr/bin/env python3
"""Owner-side grader: isolated input-only inference, then trusted scoring.

Never imports submitted code in this process. Gold paths are owner arguments,
not environment variables passed into a development agent.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21  # noqa: E402

from predict_isolated import predict_isolated, read_solution, IsolationError


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--expected-solution-sha256")
    ap.add_argument("--split", choices=["train", "gold"], default="gold")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--predictions-out", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--preflight", action="store_true", help="allow incomplete data or an unfrozen solution for setup checks")
    a = ap.parse_args()
    corpus = eval21.load_corpus(a.corpus)
    eval21.validate_corpus(corpus)
    if not a.preflight and (len(corpus) != 100 or any(r.get("review_status") != "approved" for r in corpus)
                           or not a.expected_solution_sha256):
        ap.error("measured grading requires 100 approved cases and --expected-solution-sha256; use --preflight for setup checks")
    reference_path = HERE / "quran-reference.json"
    frozen_path = a.workspace / "frozen-manifest.json"
    if not frozen_path.exists() and not a.preflight:
        ap.error("measured grading requires frozen-manifest.json from freeze_solution.py")
    if frozen_path.exists():
        frozen = json.loads(frozen_path.read_text())
        reference_path = Path(frozen["reference_path"])
        required = [(a.corpus, frozen[a.split + "_sha256"]),
                    (reference_path, frozen["reference_sha256"]),
                    (HERE / "eval21.py", frozen["evaluator_sha256"])]
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != digest for path, digest in required):
            ap.error("frozen split/reference/evaluator hash mismatch")
        if a.expected_solution_sha256 and frozen["solution_sha256"] != a.expected_solution_sha256:
            ap.error("provided solution hash disagrees with frozen manifest")
    source = read_solution(a.workspace / "solution.py")
    if a.expected_solution_sha256 and hashlib.sha256(source).hexdigest() != a.expected_solution_sha256:
        return print("solution hash does not match the frozen artifact") or 2
    try:
        result = predict_isolated(a.workspace / "solution.py", corpus, reference_path, timeout=a.timeout, source=source)
    except IsolationError as exc:
        return print(f"grader: {exc}") or 1
    preds, crashes = result["predictions"], result["crashes"]
    if a.predictions_out:
        a.predictions_out.write_text(json.dumps(preds, ensure_ascii=False) + "\n")
    s = eval21.score(corpus, preds)
    s["execution"] = {"crashes": crashes, **result["provenance"]}
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    c = s["counts"]
    print(f"cases {c['cases']}   units {c['units']}   "
          f"annotated events {c['gold_events']}   [{a.split} split]")
    print()
    print(f"  micro F1 (primary)  {s['micro_f1']:.4f}")
    print(f"  exact-span F1       {s['strict_micro_f1']:.4f}")
    print(f"  macro F1            {s['macro_f1']:.4f}")
    print(f"  localization F1     {s['loc_f1']:.4f}")
    print(f"  review cost         {s['review_cost']:.1f} (2:1)  {s['review_cost_1to1']:.1f} (1:1)")
    print(f"  clean-unit flag rate{s['clean_flag_rate']:>8.4f}")
    print(f"  predicted {c['predicted_events']}   invalid {c['invalid_predictions']}"
          + (f"   crashes {crashes}" if crashes else ""))
    print()
    print(f"  per label       {a.split:>9}  pred     F1")
    for l, d in s["per_label"].items():
        if d["gold"] or d["pred"]:
            print(f"  {l:<22}{d['gold']:>5}{d['pred']:>6}{d['f1']:>7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
