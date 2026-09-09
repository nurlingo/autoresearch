#!/usr/bin/env python3
"""
run_baselines19.py - score every baseline against a private gold set and write
study3/BASELINES-v19.md.

    FMR_REPO=/path/to/app python3 study3/tools/run_baselines19.py --gold <gold.jsonl>

The baselines read only the stripped inputs produced by make_inputs.py, so no
baseline ever sees an answer. Only aggregate scores are written to the report.
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "baselines"))

BASELINES = [
    ("B0 predict nothing", None),
    ("B1 naive diff", "naive_diff19"),
    ("B2 adapted production components", "incumbent19"),
]
COLS = [("micro_f1", "micro F1"), ("strict_micro_f1", "strict F1"), ("macro_f1", "macro F1"), ("precision", "P"),
        ("recall", "R"), ("loc_f1", "loc F1"), ("loc_recall", "loc recall"), ("span_iou", "span IoU"),
        ("review_cost", "review cost"), ("clean_flag_rate", "clean flags")]


def predict(module: str | None, inputs: Path, out: Path) -> str:
    sol = None
    if module:
        try:
            sol = importlib.import_module(module).Solution()
        except Exception as exc:
            return f"import failed: {exc}"
    crashes = 0
    with out.open("w", encoding="utf-8") as f:
        for line in inputs.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            events = []
            if sol is not None:
                try:
                    events = sol.detect_events(c) or []
                except Exception:
                    crashes += 1
            f.write(json.dumps({"review_id": c["review_id"], "chunk_idx": c["chunk_idx"],
                                "events": events}, ensure_ascii=False) + "\n")
    return f"{crashes} chunk crashes" if crashes else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=HERE / "BASELINES-v19.md")
    ap.add_argument("--json-out", type=Path, help="Aggregate metrics only; no predictions or gold records")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="study3-") as tmpdir:
        tmp = Path(tmpdir)
        inputs = tmp / "inputs.jsonl"
        subprocess.run([sys.executable, str(HERE / "tools" / "make_inputs.py"),
                        "--gold", str(a.gold), "--out", str(inputs)], check=True)

        rows, notes = [], []
        for name, module in BASELINES:
            pred = tmp / f"{(module or 'empty')}.jsonl"
            note = predict(module, inputs, pred)
            if note:
                notes.append(f"{name}: {note}")
            r = subprocess.run([sys.executable, str(HERE / "eval19.py"), "--gold", str(a.gold),
                                "--pred", str(pred), "--json"], capture_output=True, text=True)
            if r.returncode != 0:
                notes.append(f"{name}: scoring failed: {r.stderr.strip()[-300:]}")
                rows.append((name, None))
                continue
            rows.append((name, json.loads(r.stdout)))

    first = next((d for _, d in rows if d), None)
    if first is None:
        print("every baseline failed", file=sys.stderr)
        return 1
    if a.json_out:
        a.json_out.write_text(json.dumps({"baselines": {name: d for name, d in rows}, "notes": notes}, indent=2) + "\n")
    if notes:
        raise RuntimeError("Baseline execution failed: " + "; ".join(notes))
    if any(d["counts"]["invalid_predictions"] for _, d in rows):
        raise RuntimeError("Baseline emitted invalid events; fix the adapter before reporting results")
    c = first["counts"]
    md = [
        "# Task B baselines under taxonomy v0.19",
        "",
        f"Scored with `study3/eval19.py` (evaluator v{first['evaluator_version']}) "
        f"against the private gold set: {c['chunks']} scored units "
        f"({c['clean_chunks']} with no event), {c['gold_events']} gold events including opening formulas. "
        "Baselines read stripped inputs only; no answers are in this repository.",
        "",
        "| baseline | " + " | ".join(t for _, t in COLS) + " |",
        "|---|" + "---:|" * len(COLS),
    ]
    for name, d in rows:
        if not d:
            md.append(f"| {name} | " + " | ".join(["n/a"] * len(COLS)) + " |")
            continue
        md.append(f"| {name} | " + " | ".join(f"{d[k]:.3f}" for k, _ in COLS) + " |")
    md += ["", "Primary measure is label-aware event F1: a paired prediction counts only when its "
               "label also matches. `loc F1` runs the same matching with labels ignored, so the gap "
               "between the two columns is naming rather than finding. `review cost` is "
               "(2 x missed mistakes + false flags) per 100 scored units. Predicting nothing gives micro "
               "F1 0.000; the gold annotation gives 1.000.", ""]
    for name, d in rows:
        if name.startswith("B0"):
            continue
        md += [f"Per-label F1 — {name}:", "",
               "| label | gold | predicted | P | R | F1 |", "|---|---:|---:|---:|---:|---:|"]
        for lab, dd in d["per_label"].items():
            md.append(f"| `{lab}` | {dd['tp'] + dd['fn']} | {dd['tp'] + dd['fp']} | "
                      f"{dd['precision']:.2f} | {dd['recall']:.2f} | {dd['f1']:.2f} |")
        md.append("")
    md += ["All baseline calls completed without crashes or invalid predictions.", "",
           "B2 adapts production cleaner/alignment components to this event schema; "
           "it is not the full deployed application. See EVALUATOR.md for mapping assumptions. "
           "MIN_SPAN=0.30, anchor slack=1 and the secondary 2:1 cost remain provisional. "
           "Strict F1 requires exact endpoints and labels.", ""]
    if notes:
        md += ["Notes:", ""] + [f"- {n}" for n in notes] + [""]
    a.out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
