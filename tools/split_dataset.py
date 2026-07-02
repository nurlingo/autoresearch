#!/usr/bin/env python3
"""
Deterministic stratified train/test split for Study 2 (held-out generalization).

    python3 tools/split_dataset.py            # writes data/train.csv, data/test.csv
    python3 tools/split_dataset.py --check    # print split composition, write nothing

Design (see METHODOLOGY.md §12):
- Unit = recording (a row); no row appears in both files.
- 60/40 train/test, seeded shuffle (SEED=42) — reproducible forever.
- Stratified so both sides carry every behavior the metric scores:
    * kind: non-Quran rows split 2/2 (abstention must be testable held-out);
    * flags first: repetition rows and non-contiguous (comma) assignments are
      allocated 60/40 within their own groups — they are too rare (5 and 12)
      to survive plain stratification;
    * remaining Quran rows stratified by (surah, length bucket);
    * singleton strata are pooled and allocated by seeded shuffle.
- Known label quirks are PINNED TO TRAIN so the held-out test set is clean:
  rows whose assignment spans surahs (the 2 oracle-floor rows).

The split is written once, committed to the study record via its manifest hash,
and never regenerated mid-study.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/bot_review.csv"
TRAIN_OUT = ROOT / "data/train.csv"
TEST_OUT = ROOT / "data/test.csv"
SEED = 42
TRAIN_FRAC = 0.6


def length_bucket(transcript: str) -> str:
    n = len(transcript.split())
    return "short" if n < 15 else "med" if n < 60 else "long"


def classify(row: dict) -> dict:
    a = (row["ayah_assignment"] or "").strip()
    quran = a[:1].isdigit()
    info = {"quran": quran, "pin_train": False, "flag": None, "stratum": None}
    if not quran:
        info["flag"] = "non_quran"
        return info
    parts = [p for chunk in a.split(",") for p in chunk.split("-")]
    if len({p[:3] for p in parts}) > 1:
        info["pin_train"] = True  # cross-surah label quirk -> keep test clean
        return info
    ids = [s["id"] for s in json.loads(row["transcript_split_by_ayahs"] or "[]")]
    if len(ids) != len(set(ids)):
        info["flag"] = "repetition"
    elif "," in a:
        info["flag"] = "non_contiguous"
    else:
        info["stratum"] = (a[:3], length_bucket(row["transcript"]))
    return info


def allocate(rows: list[int], rng: random.Random, frac: float) -> tuple[set[int], set[int]]:
    order = rows[:]
    rng.shuffle(order)
    n_train = round(len(order) * frac)
    return set(order[:n_train]), set(order[n_train:])


def split() -> tuple[list[dict], list[dict], list[dict]]:
    with SRC.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    rng = random.Random(SEED)

    train_idx: set[int] = set()
    test_idx: set[int] = set()
    flag_groups: dict[str, list[int]] = defaultdict(list)
    strata: dict[tuple, list[int]] = defaultdict(list)

    for i, row in enumerate(rows):
        info = classify(row)
        if info["pin_train"]:
            train_idx.add(i)
        elif info["flag"]:
            flag_groups[info["flag"]].append(i)
        else:
            strata[info["stratum"]].append(i)

    for _, members in sorted(flag_groups.items()):
        tr, te = allocate(members, rng, TRAIN_FRAC)
        train_idx |= tr
        test_idx |= te

    singles: list[int] = []
    for key in sorted(strata):
        members = strata[key]
        if len(members) == 1:
            singles += members
            continue
        tr, te = allocate(members, rng, TRAIN_FRAC)
        train_idx |= tr
        test_idx |= te
    tr, te = allocate(singles, rng, TRAIN_FRAC)
    train_idx |= tr
    test_idx |= te

    train = [rows[i] for i in sorted(train_idx)]
    test = [rows[i] for i in sorted(test_idx)]
    assert len(train) + len(test) == len(rows)
    assert not (train_idx & test_idx)
    return fieldnames, train, test


def describe(name: str, rows: list[dict]) -> None:
    from collections import Counter
    kinds = Counter("quran" if (r["ayah_assignment"] or "")[:1].isdigit() else "non_quran" for r in rows)
    surahs = Counter((r["ayah_assignment"] or "")[:3] for r in rows if (r["ayah_assignment"] or "")[:1].isdigit())
    rep = sum(1 for r in rows if (ids := [s["id"] for s in json.loads(r["transcript_split_by_ayahs"] or "[]")]) and len(ids) != len(set(ids)))
    nc = sum(1 for r in rows if "," in (r["ayah_assignment"] or ""))
    print(f"{name}: {len(rows)} rows | {dict(kinds)} | surahs={len(surahs)} | repetition={rep} non_contiguous={nc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="print composition only")
    args = parser.parse_args()

    fieldnames, train, test = split()
    describe("train", train)
    describe("test ", test)
    if args.check:
        return 0
    for path, subset in ((TRAIN_OUT, train), (TEST_OUT, test)):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(subset)
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
