#!/usr/bin/env python3
"""
build_release.py — assemble the de-identified competition dataset package.

    python3 tools/build_release.py            # writes release/ (idempotent)

Inputs
    data/train.csv, data/test.csv         Stage-1 frozen split (production ids)  [gitignored]
    stage2/data/{train,test}.jsonl        Stage-2 chunks with surrogate ids       [committed]
    data/quran_ref.json
Outputs (release/, committed — contains no learner or recording identifiers)
    taskA/{train,test}.csv                surrogate `id`, byte-identical to the public HF release
    taskA/quran_ref.json
    taskB/{train,test}.jsonl              copy of stage2/data
    sample/                               the 10% review sample (26 recordings, both tasks)
    SHA256SUMS
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "release"
A_COLS = ["id", "transcript", "ayah_assignment", "confidence", "transcript_split_by_ayahs", "actual_ayahs"]


def task_a(split: str) -> list[dict]:
    rows = list(csv.DictReader(open(ROOT / "data" / f"{split}.csv", encoding="utf-8")))
    out = []
    for n, r in enumerate(rows, 1):
        out.append({"id": f"{split}-{n:03d}", **{k: r[k] for k in A_COLS[1:]}})
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=A_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for d in ("taskA", "taskB", "sample"):
        (REL / d).mkdir(parents=True, exist_ok=True)
    a = {s: task_a(s) for s in ("train", "test")}
    for s, rows in a.items():
        # Keep the public HF files byte-identical when present (same content; only CSV quoting differs).
        hf = ROOT / "data" / "hf" / f"{s}.csv"
        if hf.exists() and list(csv.DictReader(open(hf, encoding="utf-8"))) == rows:
            shutil.copy(hf, REL / "taskA" / f"{s}.csv")
        else:
            write_csv(REL / "taskA" / f"{s}.csv", rows)
    shutil.copy(ROOT / "data" / "quran_ref.json", REL / "taskA" / "quran_ref.json")
    b = {}
    for s in ("train", "test"):
        shutil.copy(ROOT / "stage2" / "data" / f"{s}.jsonl", REL / "taskB" / f"{s}.jsonl")
        b[s] = [json.loads(l) for l in (REL / "taskB" / f"{s}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    # ---- 10% review sample: 26 of 258 recordings -------------------------------
    labeled_rows = sorted({c["row_id"] for s in b for c in b[s] if c["events"] is not None})  # 20 pilot recordings
    by_id = {r["id"]: r for s in a for r in a[s]}
    extra: list[str] = []

    def pick(pred, k=1):
        for rid in sorted(by_id):
            if len(extra) >= 99:
                break
            if rid in labeled_rows or rid in extra:
                continue
            if pred(by_id[rid]):
                extra.append(rid)
                k -= 1
                if k == 0:
                    return

    pick(lambda r: r["ayah_assignment"] == "non_quran", 2)                        # abstention rows (1 train, 1 test)
    pick(lambda r: "," in r["ayah_assignment"], 1)                                # non-contiguous recitation
    pick(lambda r: r["confidence"] == "medium", 1)                                # a medium-confidence row
    pick(lambda r: r["ayah_assignment"].startswith("002") and "-" in r["ayah_assignment"], 1)  # long al-Baqarah range
    pick(lambda r: len(r["transcript"].split()) > 120, 1)                         # a long recording
    sample_ids = sorted(labeled_rows + extra)
    assert len(sample_ids) == 26, len(sample_ids)
    write_csv(REL / "sample" / "taskA_sample.csv", [by_id[i] for i in sample_ids])
    with open(REL / "sample" / "taskB_sample.jsonl", "w", encoding="utf-8") as f:
        for s in ("train", "test"):
            for c in b[s]:
                if c["row_id"] in sample_ids:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
    (REL / "sample" / "IDS.txt").write_text("\n".join(sample_ids) + "\n")

    # ---- checksums --------------------------------------------------------------
    files = sorted(p for p in REL.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "ids.private.json"))
    (REL / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(REL)}\n" for p in files))
    print((REL / "SHA256SUMS").read_text())
    print(f"sample: {len(sample_ids)} recordings -> {sample_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
