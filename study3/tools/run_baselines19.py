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
    ("B2 incumbent application pipeline", "incumbent19"),
]
COLS = [("study3_v19_score", "score"), ("miss", "miss"), ("false_alarm", "false alarm"),
        ("benign", "benign"), ("clean", "clean"), ("label_error", "label err"),
        ("span_iou", "span IoU")]


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
    a = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="study3-"))
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
    c = first["summary"]["counts"]
    md = [
        "# Task B baselines under taxonomy v0.19",
        "",
        f"Scored with `study3/eval19.py` (evaluator v{first['summary']['evaluator_version']}) "
        f"against the private gold set: {c['chunks']} chunks, {c['clean_chunks']} clean, "
        f"{c['gold_mistakes']} mistake events, {c['gold_benign_corrected']} benign or corrected events. "
        "Lower is better. Baselines read stripped inputs only; no answers are in this repository.",
        "",
        "| baseline | " + " | ".join(t for _, t in COLS) + " |",
        "|---|" + "---:|" * len(COLS),
    ]
    for name, d in rows:
        if not d:
            md.append(f"| {name} | " + " | ".join(["n/a"] * len(COLS)) + " |")
            continue
        s = d["summary"]
        md.append(f"| {name} | " + " | ".join(f"{s[k]:.3f}" for k, _ in COLS) + " |")
    md += ["", "`score = 2*miss + false_alarm + benign + clean`. `label_error` and `span_iou` "
               "describe matched pairs and are reported, not summed. Predicting nothing scores "
               "2.000; returning the gold annotation scores 0.000.", ""]
    last = next((d for _, d in reversed(rows) if d), None)
    if last and last["per_label"]:
        md += ["Localization recall per gold label, strongest baseline:", "",
               "| label | matched / gold |", "|---|---:|"]
        for lab, dd in last["per_label"].items():
            md.append(f"| `{lab}` | {dd['matched']}/{dd['gold']} |")
        md.append("")
    if notes:
        md += ["Notes:", ""] + [f"- {n}" for n in notes] + [""]
    a.out.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
