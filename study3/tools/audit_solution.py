#!/usr/bin/env python3
"""Audit a frozen solution for answers memorised from the score.

Linguistic tables are legitimate and expected: the muqatta'at, the opening
formulas, words the written tradition spells with ت. What is not legitimate is
a rule keyed to a particular recording. The signal that separates them is
whether a literal in the code appears in the corpus transcripts and nowhere in
the Quran reference — that is a copy of an input, not a fact about Arabic.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ARABIC = re.compile(r"[؀-ۿ]{2,}")
STRINGS = re.compile(r"['\"]([^'\"\n]{2,})['\"]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("solution", type=Path)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--quran", type=Path, required=True)
    a = ap.parse_args()

    src = a.solution.read_text(encoding="utf-8")
    corpus = [json.loads(l) for l in a.corpus.read_text(encoding="utf-8").splitlines() if l.strip()]
    quran = json.load(a.quran.open(encoding="utf-8"))
    quran_words = {w for v in quran.values() for w in str(v).split()}
    transcripts = {r["case_id"]: r["transcript"] for r in corpus}
    case_ids = set(transcripts)

    findings = []

    ids = sorted(set(re.findall(r"['\"](\d{6})['\"]", src)))
    if ids:
        findings.append(("hardcoded 6-digit ayah ids", len(ids), ids[:12]))

    hit = sorted(i for i in case_ids if i in src)
    if hit:
        findings.append(("case ids referenced in code", len(hit), hit[:8]))

    phrases = []
    for lit in STRINGS.findall(src):
        lit = lit.strip()
        if len(lit.split()) < 3 or not ARABIC.search(lit):
            continue
        if any(lit in t for t in transcripts.values()):
            phrases.append(lit[:50])
    if phrases:
        findings.append(("multi-word literals found in corpus transcripts", len(phrases), phrases[:6]))

    novel = []
    for lit in STRINGS.findall(src):
        for w in lit.split():
            if ARABIC.fullmatch(w) and w not in quran_words and any(w in t for t in transcripts.values()):
                novel.append(w)
    novel = sorted(set(novel))
    # Single words outside the reference are usually legitimate: spoken letter
    # names, Uthmani ت-spellings, particle contractions. Report, do not fail.
    soft = [("single words not in the Quran reference (usually linguistic, check them)",
             len(novel), novel[:12])] if novel else []

    io = sorted(set(re.findall(r"\b(open|read_text|urlopen|requests|socket|subprocess)\b", src)))
    if io:
        findings.append(("file or network access", len(io), io))


    print(f"audit: {a.solution}   {len(src.splitlines())} lines")
    for name, n, sample in findings:
        print(f"  FAIL [{n}] {name}")
        for x in sample:
            print(f"          {x}")
    for name, n, sample in soft:
        print(f"  note [{n}] {name}")
        print(f"          {', '.join(sample)}")
    if not findings:
        print("  no memorised case ids, ayah ids, transcript literals or I/O")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
