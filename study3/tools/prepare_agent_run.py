#!/usr/bin/env python3
"""Build an isolated agent workspace from the private corpus.

The workspace gets inputs and a scorer. It never gets the answers: the gold
events stay in the private corpus, and the scorer the agent runs reports
aggregate numbers only. That is the structural defence against memorisation —
an agent that cannot see which case failed cannot special-case it.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--quran", type=Path, required=True)
    ap.add_argument("--guide", type=Path, default=HERE / "ANNOTATION-GUIDE.md")
    ap.add_argument("--budget", default="30 minutes")
    a = ap.parse_args()

    corpus = [json.loads(l) for l in a.corpus.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = a.out
    (out / "data").mkdir(parents=True, exist_ok=True)

    n_units = 0
    with (out / "data" / "corpus-inputs.jsonl").open("w", encoding="utf-8") as f:
        for rec in corpus:
            units = []
            for u in rec["units"]:
                row = {
                    "case_id": rec["case_id"],
                    "chunk_idx": u["chunk_idx"],
                    "n_chunks": sum(1 for x in rec["units"] if x["chunk_idx"] >= 0),
                    "ayah_id": u.get("ayah_id"),
                    "transcript": u["transcript"],
                    "transcript_tokens": list(u["transcript_tokens"]),
                    "reference_text": u["reference_text"],
                    "reference_tokens": list(u["reference_tokens"]),
                }
                if u.get("reference_vocalized_tokens"):
                    row["reference_vocalized_tokens"] = list(u["reference_vocalized_tokens"])
                units.append(row)
                n_units += 1
            f.write(json.dumps({"case_id": rec["case_id"], "units": units}, ensure_ascii=False) + "\n")

    # Quran reference, restricted to nothing — the whole book, as before.
    shutil.copy(a.quran, out / "data" / "quran-reference.json")
    if a.guide.exists():
        shutil.copy(a.guide, out / "ANNOTATION-GUIDE.md")

    task = (HERE / "agent-run" / "TASK.md").read_text(encoding="utf-8")
    task = (task.replace("{BUDGET}", a.budget)
                .replace("{N_CASES}", str(len(corpus)))
                .replace("{N_UNITS}", str(n_units)))
    (out / "TASK.md").write_text(task, encoding="utf-8")

    shutil.copy(HERE / "agent-run" / "score_agent.py", out / "score.py")
    (out / "solution.py").write_text(
        '"""solution.py — the only file you edit.\n\n'
        "Contract: Solution().detect_events(chunk: dict) -> list[dict]\n"
        "See TASK.md. Starting point: flags nothing, scores 0.\n"
        '"""\n\n\nclass Solution:\n'
        "    def detect_events(self, chunk: dict) -> list[dict]:\n"
        "        return []\n", encoding="utf-8")

    for name in ("events", "recordings.jsonl", "corpus.json"):
        assert not (out / name).exists(), f"answer file leaked into workspace: {name}"
    leaked = [p.name for p in out.rglob("*") if "gold" in p.name.lower()]
    assert not leaked, f"answer file leaked: {leaked}"

    print(f"workspace: {out}")
    print(f"  {len(corpus)} cases, {n_units} units, answers withheld")
    print(f"  files: {sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
