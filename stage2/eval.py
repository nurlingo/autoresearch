#!/usr/bin/env python3
"""
eval.py — the FIXED scorecard for the Stage 2 autoresearch loop
(within-ayah recitation mistake events).

    python3 eval.py                    # score solution.py on data/train.jsonl
    python3 eval.py --data data/test.jsonl
    python3 eval.py --json
    python3 eval.py --include-machine  # also score LLM-proposed, human-pending chunks (pilot mode)

Input per chunk (SCHEMA.md): chunk_text (what was recited for one ayah),
reference_text (the ayah) and ctx = {ayah_id, chunk_idx, n_chunks, is_last_chunk}
(position of the chunk in its recording — needed for the last-ayah truncation
rule). The solution returns a list of events:
    {"type": <taxonomy type>, "verdict": "benign"|"corrected"|"mistake"|"uncertain",
     "hyp_span": [i, j], "ref_span": [a, b] | None}
Spans index the canon() token lists of chunk_text / reference_text.

Score (lower is better; every component in [0, 1]):
    miss_error     = (FN + 0.5 * half) / gold_mistakes         # gold mistake events not flagged
                     half = gold mistakes covered only by an `uncertain` prediction
    false_alarm    = FP / predicted_mistakes                   # flags that hit no gold mistake/uncertain event
    benign_error   = gold benign|corrected events flagged as mistake / gold benign|corrected events
    clean_error    = clean chunks with >=1 mistake flag / clean chunks   # the false-flag rate
    study3_score   = 2*miss_error + false_alarm + benign_error + clean_error

Predicted events of the same type+verdict with touching hyp_spans are merged
before scoring (gold events are phrase-level; word-level detectors are not
penalised per word).

Reported but not in the scalar: type_error (matched gold mistakes whose predicted
type differs), uncertain_rate (fraction of predictions that are `uncertain`).

Reference points: the empty stub scores 2.0 (misses everything, flags nothing);
returning the gold events scores 0.0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DEFAULT_DATA = HERE / "data" / "train.jsonl"
SCORED_CONFIDENCE = {"high", "medium"}
MISTAKE_TYPES = {"substitution", "omission", "insertion", "word_order", "truncation"}

# --- canonicalizer: identical to Stage 1 eval.canon (metric-only) -------------
_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ؤ": "ء", "ئ": "ء"}
_HARAKAT_RE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")


def canon(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("ـ", "")
    for a, b in _FOLD.items():
        text = text.replace(a, b)
    text = _HARAKAT_RE.sub("", text)
    return text.split()


# --- matching ------------------------------------------------------------------
def _overlap(a: list[int] | None, b: list[int] | None) -> bool:
    if not a or not b:
        return False
    if a[0] == a[1] and b[0] == b[1]:          # two insertion points
        return abs(a[0] - b[0]) <= 1
    if a[0] == a[1]:                            # insertion point vs span
        return b[0] <= a[0] <= b[1]
    if b[0] == b[1]:
        return a[0] <= b[0] <= a[1]
    return a[0] < b[1] and b[0] < a[1]


def merge_adjacent(pred: list[dict]) -> list[dict]:
    """Merge predicted events of the same type+verdict whose hyp_spans touch, so
    a word-level and a phrase-level detector are scored alike (gold events are
    phrase-level). Applied to predictions only."""
    out: list[dict] = []
    for p in sorted(pred, key=lambda e: (e.get("hyp_span") or [10**9])[0]):
        if out and out[-1].get("type") == p.get("type") and out[-1].get("verdict") == p.get("verdict") \
                and out[-1].get("hyp_span") and p.get("hyp_span") and out[-1]["hyp_span"][1] >= p["hyp_span"][0]:
            q = dict(out[-1])
            q["hyp_span"] = [q["hyp_span"][0], max(q["hyp_span"][1], p["hyp_span"][1])]
            if q.get("ref_span") and p.get("ref_span"):
                q["ref_span"] = [min(q["ref_span"][0], p["ref_span"][0]), max(q["ref_span"][1], p["ref_span"][1])]
            out[-1] = q
        else:
            out.append(dict(p))
    return out


def matches(pred: dict, gold: dict) -> bool:
    return _overlap(pred.get("hyp_span"), gold.get("hyp_span")) or _overlap(pred.get("ref_span"), gold.get("ref_span"))


@dataclass
class ChunkResult:
    chunk_id: str
    gold_mistakes: int = 0
    gold_benign: int = 0
    is_clean: bool = False
    tp: int = 0
    half: int = 0
    fn: int = 0
    fp: int = 0
    benign_flagged: int = 0
    clean_flagged: bool = False
    type_wrong: int = 0
    n_pred: int = 0
    n_pred_uncertain: int = 0
    pred: list[dict] = field(default_factory=list)
    error: str | None = None


def score_chunk(chunk: dict, solution) -> ChunkResult:
    r = ChunkResult(chunk["chunk_id"])
    gold = chunk["events"] or []
    g_m = [g for g in gold if g["verdict"] == "mistake"]
    g_b = [g for g in gold if g["verdict"] in ("benign", "corrected")]
    g_u = [g for g in gold if g["verdict"] == "uncertain"]
    r.gold_mistakes, r.gold_benign, r.is_clean = len(g_m), len(g_b), not gold
    try:
        ctx = {k: chunk[k] for k in ("ayah_id", "chunk_idx", "n_chunks", "is_last_chunk")}
        pred = solution.detect_events(chunk["chunk_text"], chunk["reference_text"], ctx) or []
        pred = [p for p in pred if isinstance(p, dict)]
    except Exception as exc:  # keep crashes visible, don't abort the run
        r.error = str(exc)
        pred = []
    pred = merge_adjacent(pred)
    r.pred = pred
    p_m = [p for p in pred if p.get("verdict") == "mistake"]
    p_u = [p for p in pred if p.get("verdict") == "uncertain"]
    r.n_pred, r.n_pred_uncertain = len(pred), len(p_u)
    for g in g_m:
        hits = [p for p in p_m if matches(p, g)]
        if hits:
            r.tp += 1
            if all(p.get("type") != g["type"] for p in hits):
                r.type_wrong += 1
        elif any(matches(p, g) for p in p_u):
            r.half += 1
        else:
            r.fn += 1
    for p in p_m:
        if not any(matches(p, g) for g in g_m + g_u):
            r.fp += 1
    r.benign_flagged = sum(1 for g in g_b if any(matches(p, g) for p in p_m))
    r.clean_flagged = r.is_clean and bool(p_m)
    return r


def summarize(results: list[ChunkResult]) -> dict[str, Any]:
    gm = sum(r.gold_mistakes for r in results)
    gb = sum(r.gold_benign for r in results)
    clean = [r for r in results if r.is_clean]
    tp, half, fn, fp = (sum(getattr(r, k) for r in results) for k in ("tp", "half", "fn", "fp"))
    pm = sum(1 for r in results for p in r.pred if p.get("verdict") == "mistake")
    miss = (fn + 0.5 * half) / gm if gm else 0.0
    false_alarm = fp / pm if pm else 0.0
    benign = sum(r.benign_flagged for r in results) / gb if gb else 0.0
    clean_err = sum(1 for r in clean if r.clean_flagged) / len(clean) if clean else 0.0
    npred = sum(r.n_pred for r in results)
    return {
        "study3_score": round(2 * miss + false_alarm + benign + clean_err, 6),
        "score_direction": "lower_is_better",
        "stage": "2_within_ayah_events",
        "chunks": len(results),
        "miss_error": round(miss, 4), "false_alarm": round(false_alarm, 4),
        "benign_error": round(benign, 4), "clean_error": round(clean_err, 4),
        "type_error": round(sum(r.type_wrong for r in results) / tp, 4) if tp else 0.0,
        "uncertain_rate": round(sum(r.n_pred_uncertain for r in results) / npred, 4) if npred else 0.0,
        "counts": {"gold_mistakes": gm, "gold_benign": gb, "clean_chunks": len(clean),
                   "tp": tp, "half": half, "fn": fn, "fp": fp, "predicted_mistakes": pm,
                   "crashes": sum(1 for r in results if r.error)},
    }


def print_report(s: dict[str, Any], results: list[ChunkResult]) -> None:
    print("---")
    print(f"study3_score:     {s['study3_score']:.6f}")
    print(f"score_direction:  {s['score_direction']}")
    print()
    print("Stage 2 scorecard (within-ayah mistake events)")
    c = s["counts"]
    print(f"  Chunks scored:    {s['chunks']} (clean {c['clean_chunks']}, gold mistakes {c['gold_mistakes']}, gold benign {c['gold_benign']})")
    print(f"  miss_error:       {s['miss_error']:.3f}  (fn {c['fn']}, half {c['half']}, tp {c['tp']})  x2 in score")
    print(f"  false_alarm:      {s['false_alarm']:.3f}  (fp {c['fp']} of {c['predicted_mistakes']} flags)")
    print(f"  benign_error:     {s['benign_error']:.3f}")
    print(f"  clean_error:      {s['clean_error']:.3f}")
    print(f"  type_error:       {s['type_error']:.3f}   uncertain_rate: {s['uncertain_rate']:.3f}   crashes: {c['crashes']}")
    fails = [r for r in results if r.error or r.fn or r.fp or r.half or r.clean_flagged or r.benign_flagged]
    if fails:
        print(f"  Failures ({len(fails)}):")
        for r in fails[:40]:
            if r.error:
                print(f"    {r.chunk_id} ERROR: {r.error}")
            else:
                # R2: predicted events only — never gold events or verdicts.
                pv = ", ".join(f"{p.get('type')}/{p.get('verdict')}@{p.get('hyp_span')}" for p in r.pred) or "∅"
                print(f"    {r.chunk_id} fn={r.fn} fp={r.fp} half={r.half} pred=[{pv}]")
        if len(fails) > 40:
            print(f"    ... {len(fails) - 40} more")


def load_chunks(path: Path, *, include_machine: bool, score_low: bool) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        if c["events"] is None:
            continue
        if c["label_status"] == "reviewed" or (include_machine and c["label_status"] == "machine"):
            if score_low or c.get("confidence", "high") in SCORED_CONFIDENCE:
                out.append(c)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2 autoresearch scorecard.")
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--include-machine", action="store_true", help="score LLM-proposed (human-pending) chunks too")
    ap.add_argument("--score-low", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--solution", default="solution", help="module name exposing Solution")
    a = ap.parse_args()
    import importlib
    mod = importlib.import_module(a.solution)
    solution = mod.Solution()
    chunks = load_chunks(a.data, include_machine=a.include_machine, score_low=a.score_low)
    if not chunks:
        print("no scorable chunks (labels missing?) — nothing to do", file=sys.stderr)
        return 1
    results = [score_chunk(c, solution) for c in chunks]
    summary = summarize(results)
    if a.json:
        print(json.dumps({"summary": summary, "chunks": [asdict(r) for r in results]}, ensure_ascii=False, indent=1))
    else:
        print_report(summary, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
