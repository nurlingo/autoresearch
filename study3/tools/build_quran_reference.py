#!/usr/bin/env python3
"""Build the study's Quran reference from the app's content/quran.json.

`titles.ar` is the vocalized text. Removing the vowel marks from it leaves the
consonantal skeleton with hamza, madda and alif maqsura intact — which is the
level an ASR transcript is actually written at, and the level at which an
accepted spelling can be told from a changed word.

The app's own `titles.clean` goes one step further and folds أ إ آ to bare ا.
That step is what hides a real أ/إ substitution behind a benign one, so it is
not used here. This file's `clean` is the hamza-preserving form.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

WAQF = range(0x06D6, 0x06EE)      # small high marks: waqf signs, sajda, etc.
TATWEEL = "ـ"


def devowel(text: str) -> str:
    """Drop combining marks, tatweel and waqf signs; keep every letter."""
    out = [c for c in text
           if not unicodedata.combining(c) and c != TATWEEL and ord(c) not in WAQF]
    return " ".join("".join(out).split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", type=Path, required=True, help="content/quran.json")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    src = json.loads(a.content.read_text(encoding="utf-8"))
    ref, skipped = {}, 0
    for _surah, ayahs in src.items():
        if not isinstance(ayahs, list):
            continue
        for ayah in ayahs:
            ar = ((ayah.get("titles") or {}).get("ar") or "").strip()
            if not ar:
                skipped += 1
                continue
            ref[ayah["id"]] = devowel(ar)

    a.out.write_text(json.dumps(ref, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out}: {len(ref)} ayahs" + (f", {skipped} skipped (no titles.ar)" if skipped else ""))
    sample = ref.get("001007") or next(iter(ref.values()))
    print(f"  1:7 -> {sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
