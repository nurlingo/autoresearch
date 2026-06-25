#!/usr/bin/env python3
"""
Plot autoresearch progress (Karpathy-style progress.png).

Single run (results.tsv -> progress.png):
    python3 tools/plot.py

Agent comparison (overlay best-so-far -> comparison.png):
    python3 tools/plot.py --compare runs/claude-*.tsv runs/codex-*.tsv

Left panel = sample efficiency (best score vs experiment number).
Right panel = wall-clock efficiency (best score vs elapsed seconds).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FLOOR = 0.03  # oracle floor: feeding the gold split back


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    iters = [int(r["iter"]) for r in rows]
    scores = [float(r["research_score"]) for r in rows]
    elapsed = [float(r["elapsed_sec"]) for r in rows]
    status = [r["status"] for r in rows]
    best, b = [], float("inf")
    for s, st in zip(scores, status):
        if st != "crash" and s < b:
            b = s
        best.append(b)
    return {"iters": iters, "scores": scores, "elapsed": elapsed,
            "status": status, "best": best, "name": Path(path).stem}


def plot_single(path: str, out: str) -> None:
    d = load(path)
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    colors = {"keep": "#2a9d3f", "discard": "#bbbbbb", "crash": "#d62728"}
    for it, s, st in zip(d["iters"], d["scores"], d["status"]):
        ax[0].scatter(it, s, color=colors.get(st, "#888"), s=26, zorder=3)
    ax[0].step(d["iters"], d["best"], where="post", color="#1f77b4", lw=2, label="best so far")
    ax[0].axhline(FLOOR, ls="--", color="#888", lw=1, label=f"oracle floor ~{FLOOR}")
    ax[0].set(xlabel="experiment", ylabel="research_score (lower is better)", title="Score per experiment")
    ax[0].legend()
    ax[1].step(d["elapsed"], d["best"], where="post", color="#1f77b4", lw=2)
    ax[1].axhline(FLOOR, ls="--", color="#888", lw=1)
    ax[1].set(xlabel="wall-clock seconds", ylabel="best research_score", title="Best score vs time")
    fig.suptitle(f"autoresearch progress — {d['name']}")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)


def plot_compare(paths: list[str], out: str) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for p in paths:
        d = load(p)
        ax[0].step(d["iters"], d["best"], where="post", lw=2, label=d["name"])
        ax[1].step(d["elapsed"], d["best"], where="post", lw=2, label=d["name"])
    for a, xl, t in ((ax[0], "experiment", "Sample efficiency"),
                     (ax[1], "wall-clock seconds", "Wall-clock efficiency")):
        a.axhline(FLOOR, ls="--", color="#888", lw=1, label=f"oracle floor ~{FLOOR}")
        a.set(xlabel=xl, ylabel="best research_score", title=t)
        a.legend()
    fig.suptitle("autoresearch — agent comparison")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compare", nargs="+", help="TSV run logs to overlay")
    ap.add_argument("--in", dest="inp", default="results.tsv")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.compare:
        plot_compare(args.compare, args.out or "comparison.png")
    else:
        plot_single(args.inp, args.out or "progress.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
