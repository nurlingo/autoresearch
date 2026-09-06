#!/usr/bin/env python3
"""
Uniform experiment logger for the Stage-2 autoresearch loop (same shape as
the Stage-1 logger; only the score columns differ).

Runs the fixed scorecard, parses the score + component errors, and appends ONE
structured row to results.tsv. Both Claude Code and Codex call this the same way,
so the resulting logs are directly comparable for the paper.

Usage:
    python3 tools/log_experiment.py "what this experiment changed"

Tag the run with the agent under test:
    export AR_AGENT=claude   # or: codex, human, claude+skill, ...

Columns (tab-separated):
    iter timestamp elapsed_sec agent commit study3_score
    miss_err false_alarm benign_err clean_err status description

`status` is keep | discard | crash, derived from whether research_score beat the
best non-crash score so far. results.tsv is gitignored so it survives the
`git reset --hard` used to discard a regression.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results.tsv"
RUN_START = ROOT / ".ar_run_start"
HEADER = [
    "iter", "timestamp", "elapsed_sec", "agent", "commit", "study3_score",
    "miss_err", "false_alarm", "benign_err", "clean_err", "status", "description",
]


def run_eval() -> tuple[dict | None, str]:
    out = subprocess.run(
        [sys.executable, str(ROOT / "eval.py"), "--json"] + os.getenv("AR_EVAL_ARGS", "").split(),
        capture_output=True, text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return None, out.stderr
    try:
        return json.loads(out.stdout)["summary"], ""
    except (json.JSONDecodeError, KeyError) as exc:
        return None, f"{exc}\n{out.stdout[-500:]}"


def existing_rows() -> list[list[str]]:
    if not RESULTS.exists():
        return []
    lines = RESULTS.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].split("\t") != HEADER:
        # schema drift (e.g. an older results.tsv): archive and start fresh.
        RESULTS.rename(RESULTS.with_suffix(".tsv.bak"))
        return []
    return [ln.split("\t") for ln in lines[1:] if ln.strip()]


def main() -> int:
    desc = sys.argv[1] if len(sys.argv) > 1 else "experiment"
    agent = os.getenv("AR_AGENT", "unknown")

    if not RUN_START.exists():
        RUN_START.write_text(str(time.time()))
    elapsed = round(time.time() - float(RUN_START.read_text().strip()), 1)

    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip() or "none"

    rows = existing_rows()
    it = len(rows) + 1
    summary, err = run_eval()

    if summary is None:
        score, comps, status = 9.999999, [9.999999] * 4, "crash"
    else:
        score = summary["study3_score"]
        comps = [summary[k] for k in ("miss_error", "false_alarm", "benign_error", "clean_error")]
        prev = [float(r[5]) for r in rows if len(r) > 10 and r[10] != "crash"]
        best = min(prev) if prev else float("inf")
        status = "keep" if score < best else "discard"

    new_file = not RESULTS.exists()
    with RESULTS.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("\t".join(HEADER) + "\n")
        f.write("\t".join(str(x) for x in [
            it, datetime.now(timezone.utc).isoformat(timespec="seconds"), elapsed,
            agent, commit, f"{score:.6f}", *comps, status, desc,
        ]) + "\n")

    print(f"[exp {it}] study3_score={score:.6f}  status={status}  elapsed={elapsed}s  ({agent})  {desc}")
    if err:
        sys.stderr.write(err[-500:] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
