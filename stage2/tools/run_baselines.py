#!/usr/bin/env python3
"""Score every baseline on train and test; write baselines/RESULTS.md.
    FMR_REPO=/path/to/follow_my_reading python3 tools/run_baselines.py
"""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
ARGS = os.getenv("AR_EVAL_ARGS", "--include-machine").split()
BASELINES = [("B0 empty stub", "solution"), ("B1 naive diff", "baselines.naive_diff"), ("B2 incumbent production stack", "baselines.incumbent")]
COLS = ["study3_score", "miss_error", "false_alarm", "benign_error", "clean_error", "type_error"]

def score(mod, data):
    out = subprocess.run([sys.executable, str(HERE / "eval.py"), "--json", "--solution", mod, "--data", str(data)] + ARGS,
                         capture_output=True, text=True, cwd=HERE)
    if out.returncode != 0:
        return None, out.stderr[-400:]
    return json.loads(out.stdout)["summary"], ""

rows, notes = [], []
for name, mod in BASELINES:
    r = {"name": name}
    for split in ("train", "test"):
        s, err = score(mod, HERE / "data" / f"{split}.jsonl")
        if s is None:
            notes.append(f"{name} [{split}] failed: {err}")
            r[split] = None
        else:
            r[split] = s
    rows.append(r)

md = ["# Stage 2 baselines", "", f"Scored with `eval.py {' '.join(ARGS)}` (lower is better). "
      "Pilot labels: LLM-proposed, human-pending (`--include-machine`).", ""]
for split in ("train", "test"):
    any_ = next((r[split] for r in rows if r[split]), None)
    if not any_:
        continue
    c = any_["counts"]
    md += [f"## {split} — {any_['chunks']} labeled chunks (clean {c['clean_chunks']}, gold mistakes {c['gold_mistakes']}, gold benign {c['gold_benign']})", "",
           "| baseline | " + " | ".join(COLS) + " |", "|---|" + "---:|" * len(COLS)]
    for r in rows:
        s = r[split]
        md.append(f"| {r['name']} | " + (" | ".join(f"{s[k]:.3f}" for k in COLS) if s else "crash | " * len(COLS)) + " |")
    md.append("")
if notes:
    md += ["Notes:", ""] + [f"- {n}" for n in notes]
(HERE / "baselines" / "RESULTS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
