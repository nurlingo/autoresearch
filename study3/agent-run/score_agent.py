#!/usr/bin/env python3
"""Score solution.py. Aggregate numbers only — no case is ever named.

The grader that produces these numbers holds the answers and runs outside this
workspace. What you get back is what you would get from a leaderboard: how well
the method does, not which rows it missed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRADER = os.environ.get("FMR_GRADER")

if not GRADER:
    sys.exit("score.py: grader not configured in this workspace (FMR_GRADER unset).")

r = subprocess.run([sys.executable, GRADER, "--workspace", str(HERE)],
                   capture_output=True, text=True)
sys.stdout.write(r.stdout)
if r.returncode != 0:
    sys.stderr.write(r.stderr[-2000:])
sys.exit(r.returncode)
