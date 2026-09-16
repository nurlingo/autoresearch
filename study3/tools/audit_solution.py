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
import ast
import json
import re
from pathlib import Path

ARABIC = re.compile(r"[؀-ۿ]{2,}")
STRINGS = re.compile(r"['\"]([^'\"\n]{2,})['\"]")


IO_CALLS = {"open", "exec", "eval", "compile", "__import__", "breakpoint", "input"}
IO_MODULES = {"os", "io", "sys", "pathlib", "shutil", "socket", "subprocess", "urllib",
              "http", "requests", "ctypes", "importlib", "pickle", "marshal", "tempfile"}
IO_METHODS = {"read_text", "read_bytes", "write_text", "write_bytes", "urlopen", "fdopen"}


def io_access(src):
    """I/O the code actually performs, read from the syntax tree.

    A word search flagged the comment "spelled with an open ta" -- the Arabic
    letter -- as file access. Names in comments and strings are not calls; what
    counts is an import of an I/O module, a call to an I/O builtin, or a call to
    a file/network method, wherever in the program it appears.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return ["unparseable source"]
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(f"import {a.name}" for a in node.names
                         if a.name.split(".")[0] in IO_MODULES)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in IO_MODULES:
                found.add(f"from {node.module} import")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in IO_CALLS:
                found.add(f"{f.id}()")
            elif isinstance(f, ast.Attribute) and f.attr in IO_METHODS:
                found.add(f".{f.attr}()")
            elif isinstance(f, ast.Attribute) and f.attr == "open":
                found.add(".open()")
    return sorted(found)


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

    io = io_access(src)
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
