#!/usr/bin/env python3
"""Run frozen solution.py files over the granular corpus and score them.

Each solution keeps the per-unit contract it was written against: it sees one
unit and returns events over that unit's tokens. This script feeds it every
unit of every case and collects the predictions per case for eval21.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21  # noqa: E402
from predict_isolated import predict_isolated


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
            result = predict_isolated(sp, corpus)
        except Exception:
            print(f"{name:<34}  isolated execution failed")
            continue
        preds, crashes = result["predictions"], result["crashes"]
        s = eval21.score(corpus, preds)
        s["execution"] = {"crashes": crashes, **result["provenance"]}
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
