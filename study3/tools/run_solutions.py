#!/usr/bin/env python3
"""Run frozen solution.py files over the granular corpus and score them.

Each solution keeps the per-unit contract it was written against: it sees one
unit and returns events over that unit's tokens. This script feeds it every
unit of every case and collects the predictions per case for eval21.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21  # noqa: E402


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location(f"sol_{path.parent.name.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Solution()


def predict(sol, corpus):
    preds, crashes = {}, 0
    for rec in corpus:
        rows = []
        for u in rec["units"]:
            ref_tokens = u["reference_tokens"]
            chunk = {
                "review_id": rec["case_id"],
                "chunk_idx": u["chunk_idx"],
                "n_chunks": sum(1 for x in rec["units"] if x["chunk_idx"] >= 0),
                "ayah_id": u.get("ayah_id"),
                "transcript": u["transcript"],
                "transcript_tokens": list(u["transcript_tokens"]),
                "reference_text": " ".join(ref_tokens),
                "reference_tokens": list(ref_tokens),
            }
            try:
                events = sol.detect_events(chunk) or []
            except Exception:
                crashes += 1
                events = []
            for e in events:
                if not isinstance(e, dict):
                    continue
                rows.append({"chunk_idx": u["chunk_idx"], "label": e.get("label"),
                             "hyp_span": e.get("hyp_span"), "ref_span": e.get("ref_span")})
        preds[rec["case_id"]] = rows
    return preds, crashes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--solutions", nargs="+", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="write per-solution predictions here")
    a = ap.parse_args()
    corpus = eval21.load_corpus(a.corpus)

    print(f"corpus: {len(corpus)} cases, "
          f"{sum(len(r['units']) for r in corpus)} units, "
          f"{sum(len(r.get('events') or []) for r in corpus)} events")
    print("reference given to solutions: hamza preserved\n")
    print(f"{'solution':<34}{'micro':>7}{'exact':>7}{'macro':>7}{'loc':>7}{'cost2:1':>9}{'cleanflag':>10}{'inval':>7}")
    print("-" * 88)
    for sp in a.solutions:
        name = sp.parent.name
        try:
            sol = load_solution(sp)
        except Exception as exc:
            print(f"{name:<34}  load failed: {exc}")
            continue
        preds, crashes = predict(sol, corpus)
        s = eval21.score(corpus, preds)
        c = s["counts"]
        print(f"{name:<34}{s['micro_f1']:>7.3f}{s['strict_micro_f1']:>7.3f}{s['macro_f1']:>7.3f}"
              f"{s['loc_f1']:>7.3f}{s['review_cost']:>9.1f}{s['clean_flag_rate']:>10.4f}"
              f"{c['invalid_predictions']:>7}" + (f"  ({crashes} crashes)" if crashes else ""))
        if a.out:
            a.out.mkdir(parents=True, exist_ok=True)
            (a.out / f"{name}.json").write_text(json.dumps(preds, ensure_ascii=False), encoding="utf-8")
            (a.out / f"{name}.score.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
