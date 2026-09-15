#!/usr/bin/env python3
"""Grader. Holds the answers, runs outside the agent workspace.

Loads the workspace's solution.py, runs it over every case, scores against the
private corpus with eval21, and prints aggregate metrics and per-label F1.
It never prints a case id, a transcript or an expected answer.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21  # noqa: E402

CORPUS = os.environ.get("FMR_CORPUS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, default=Path(CORPUS) if CORPUS else None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.corpus:
        return print("grader: no corpus configured") or 2

    corpus = eval21.load_corpus(a.corpus)
    sol_path = a.workspace / "solution.py"
    spec = importlib.util.spec_from_file_location("agent_solution", sol_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        sol = mod.Solution()
    except Exception as exc:
        print(f"solution.py failed to load: {type(exc).__name__}: {exc}")
        return 1

    preds, crashes = {}, 0
    for rec in corpus:
        rows = []
        for u in rec["units"]:
            chunk = {
                "case_id": rec["case_id"], "chunk_idx": u["chunk_idx"],
                "n_chunks": sum(1 for x in rec["units"] if x["chunk_idx"] >= 0),
                "ayah_id": u.get("ayah_id"), "transcript": u["transcript"],
                "transcript_tokens": list(u["transcript_tokens"]),
                "reference_text": u["reference_text"],
                "reference_tokens": list(u["reference_tokens"]),
            }
            for extra in ("reference_vocalized_tokens", "reference_vocalized_text",
                          "reference_spelling_tokens", "reference_spelling_text"):
                if u.get(extra):
                    chunk[extra] = list(u[extra]) if extra.endswith("tokens") else u[extra]
            try:
                events = sol.detect_events(chunk) or []
            except Exception:
                crashes += 1
                events = []
            for e in events:
                if isinstance(e, dict):
                    rows.append({"chunk_idx": u["chunk_idx"], "label": e.get("label"),
                                 "hyp_span": e.get("hyp_span"), "ref_span": e.get("ref_span")})
        preds[rec["case_id"]] = rows

    s = eval21.score(corpus, preds)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    c = s["counts"]
    print(f"cases {c['cases']}   units {c['units']}   gold events {c['gold_events']}")
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
    print("  per label            gold  pred     F1")
    for l, d in s["per_label"].items():
        if d["gold"] or d["pred"]:
            print(f"  {l:<22}{d['gold']:>5}{d['pred']:>6}{d['f1']:>7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
