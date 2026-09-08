#!/usr/bin/env python3
"""
eval19.py - executable scorecard for Study 3 Task B, taxonomy v0.19.

    python3 study3/eval19.py --gold <private gold.jsonl> --pred <predictions.jsonl>
    python3 study3/eval19.py --gold <gold.jsonl> --pred <pred.jsonl> --json
    python3 study3/eval19.py --gold <gold.jsonl> --self-test

This file contains NO gold data. It reads a private gold file by path; the
reviewer bundle stays outside this repository and outside agent runtimes.

--------------------------------------------------------------------------
Contract
--------------------------------------------------------------------------
A system is given, per chunk: `transcript_tokens`, `reference_tokens`,
`ayah_id`, `chunk_idx`, `n_chunks`. Ayah detection and splitting are supplied,
not scored (rubric v0.19, "Input and selection").

It returns, per chunk, a list of events:

    {"label": "<one of the v0.19 combined labels>",
     "hyp_span": [i, j],      # half-open, into transcript_tokens
     "ref_span": [a, b]}      # half-open, into reference_tokens

An empty hypothesis span [i, i] is an omission anchor; an empty reference span
[a, a] is an insertion point. A chunk with no events is `clean`.

Predictions file: one JSON object per line,
    {"review_id": ..., "chunk_idx": ..., "events": [...]}
Chunks present in gold but absent from predictions count as predicted-clean.

--------------------------------------------------------------------------
Matching
--------------------------------------------------------------------------
Within a chunk, predicted and gold events are matched ONE-TO-ONE by maximum
total similarity. One broad prediction therefore cannot take credit for several
distinct gold events: it can be matched to at most one, and the rest count as
misses. Similarity is the mean of the hypothesis-span and reference-span
similarities; a pair below MIN_SIM is never matched.

Span similarity handles the empty spans the rubric requires:
  - two empty spans: 1.0 when their anchors are within ANCHOR_SLACK tokens,
    decaying to 0 beyond that;
  - one empty span against a real one: 0.5 when the anchor falls inside the
    other span (widened by ANCHOR_SLACK), else 0.0;
  - two real spans: intersection over union.
Both-attempt spans (corrected and repetition events cover all attempts) are
scored by this same IoU, so a prediction that covers only one attempt loses
span credit but can still match.

--------------------------------------------------------------------------
Score (lower is better; each component in [0, 1])
--------------------------------------------------------------------------
    miss         = gold mistake events with no matched mistake prediction
                   / gold mistake events
    false_alarm  = predicted mistake events matched to no gold event
                   / predicted mistake events
    benign       = gold benign/corrected events matched by a *mistake*
                   prediction / gold benign+corrected events
    clean        = reviewed clean chunks carrying any predicted mistake
                   / reviewed clean chunks

    study3_v19_score = 2*miss + false_alarm + benign + clean

`miss` is doubled: a missed mistake fails the learner, while an extra flag
costs a moment of review. Reported alongside but NOT summed: label_error
(matched pairs whose label differs), span_iou (localization quality of matched
pairs), and a per-label table.

Reference points: predicting nothing scores 2.0; returning gold scores 0.0.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from itertools import permutations
from pathlib import Path
from typing import Any

MIN_SIM = 0.30       # below this, a predicted/gold pair is never matched
ANCHOR_SLACK = 1     # tokens of tolerance for omission/insertion anchors

LABELS = (
    "substitution_mistake", "omission_mistake", "insertion_mistake",
    "substitution_corrected", "omission_corrected",
    "repetition_benign", "letters_benign", "spelling_benign",
    "basmala_benign", "isti3adha_benign",
)
MISTAKE = {l for l in LABELS if l.endswith("_mistake")}
FORGIVEN = {l for l in LABELS if l.endswith(("_benign", "_corrected"))}


# ---------------------------------------------------------------- similarity
def span_sim(a: list[int] | None, b: list[int] | None) -> float:
    """Similarity of two half-open spans, empty spans being anchors."""
    if a is None or b is None or len(a) != 2 or len(b) != 2:
        return 0.0
    a0, a1 = int(a[0]), int(a[1])
    b0, b1 = int(b[0]), int(b[1])
    if a1 < a0 or b1 < b0:
        return 0.0
    a_empty, b_empty = a0 == a1, b0 == b1
    if a_empty and b_empty:
        d = abs(a0 - b0)
        return 1.0 if d == 0 else (0.5 if d <= ANCHOR_SLACK else 0.0)
    if a_empty or b_empty:
        point, lo, hi = (a0, b0, b1) if a_empty else (b0, a0, a1)
        return 0.5 if lo - ANCHOR_SLACK <= point <= hi + ANCHOR_SLACK else 0.0
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union else 0.0


def event_sim(pred: dict, gold: dict) -> float:
    return 0.5 * span_sim(pred.get("hyp_span"), gold.get("hyp_span")) \
         + 0.5 * span_sim(pred.get("ref_span"), gold.get("ref_span"))


def match_events(pred: list[dict], gold: list[dict]) -> list[tuple[int, int, float]]:
    """One-to-one maximum-similarity matching. Returns (pred_i, gold_j, sim)."""
    if not pred or not gold:
        return []
    sim = [[event_sim(p, g) for g in gold] for p in pred]
    n, m = len(pred), len(gold)
    idx_p, idx_g = range(n), range(m)
    best: tuple[float, list[tuple[int, int, float]]] = (-1.0, [])
    if n <= 7 and m <= 7:                       # exact: chunks hold few events
        rows, cols = (idx_p, idx_g) if n <= m else (idx_g, idx_p)
        for perm in permutations(cols, len(list(rows))):
            pairs, total = [], 0.0
            for r, c in zip(rows, perm):
                i, j = (r, c) if n <= m else (c, r)
                s = sim[i][j]
                if s >= MIN_SIM:
                    pairs.append((i, j, s))
                    total += s
            if total > best[0]:
                best = (total, pairs)
        return sorted(best[1])
    # fallback for pathological outputs: greedy, deterministic
    order = sorted(((sim[i][j], i, j) for i in idx_p for j in idx_g), reverse=True)
    used_p: set[int] = set()
    used_g: set[int] = set()
    pairs = []
    for s, i, j in order:
        if s < MIN_SIM or i in used_p or j in used_g:
            continue
        used_p.add(i); used_g.add(j); pairs.append((i, j, s))
    return sorted(pairs)


# ---------------------------------------------------------------- scoring
@dataclass
class ChunkResult:
    key: str
    is_clean: bool = False
    gold_mistakes: int = 0
    gold_forgiven: int = 0
    pred_mistakes: int = 0
    miss: int = 0
    false_alarm: int = 0
    benign_flagged: int = 0
    clean_flagged: bool = False
    label_wrong: int = 0
    matched: int = 0
    sim_sum: float = 0.0
    error: str | None = None
    pred: list[dict] = field(default_factory=list)


def score_chunk(gold_chunk: dict, pred_events: list[dict], key: str) -> ChunkResult:
    r = ChunkResult(key)
    gold = list(gold_chunk.get("events") or [])
    pred = [p for p in pred_events if isinstance(p, dict)]
    r.pred = pred
    r.is_clean = not gold
    r.gold_mistakes = sum(1 for g in gold if g.get("label") in MISTAKE)
    r.gold_forgiven = sum(1 for g in gold if g.get("label") in FORGIVEN)
    p_mist = [p for p in pred if p.get("label") in MISTAKE]
    r.pred_mistakes = len(p_mist)

    pairs = match_events(pred, gold)
    matched_p = {i for i, _, _ in pairs}
    matched_g = {j for _, j, _ in pairs}
    r.matched = len(pairs)
    r.sim_sum = sum(s for _, _, s in pairs)
    for i, j, _ in pairs:
        if pred[i].get("label") != gold[j].get("label"):
            r.label_wrong += 1

    # a gold mistake is caught only by a prediction that also calls it a mistake
    for j, g in enumerate(gold):
        if g.get("label") not in MISTAKE:
            continue
        hit = any(gj == j and pred[pi].get("label") in MISTAKE for pi, gj, _ in pairs)
        if not hit:
            r.miss += 1
    # a predicted mistake matched to nothing is a false alarm
    for i, p in enumerate(pred):
        if p.get("label") in MISTAKE and i not in matched_p:
            r.false_alarm += 1
    # a benign/corrected gold event called a mistake
    for j, g in enumerate(gold):
        if g.get("label") in FORGIVEN and any(
                gj == j and pred[pi].get("label") in MISTAKE for pi, gj, _ in pairs):
            r.benign_flagged += 1
    r.clean_flagged = r.is_clean and bool(p_mist)
    return r


def summarize(results: list[ChunkResult]) -> dict[str, Any]:
    gm = sum(r.gold_mistakes for r in results)
    gf = sum(r.gold_forgiven for r in results)
    pm = sum(r.pred_mistakes for r in results)
    clean = [r for r in results if r.is_clean]
    miss = sum(r.miss for r in results) / gm if gm else 0.0
    fa = sum(r.false_alarm for r in results) / pm if pm else 0.0
    benign = sum(r.benign_flagged for r in results) / gf if gf else 0.0
    clean_err = sum(1 for r in clean if r.clean_flagged) / len(clean) if clean else 0.0
    matched = sum(r.matched for r in results)
    return {
        "study3_v19_score": round(2 * miss + fa + benign + clean_err, 6),
        "score_direction": "lower_is_better",
        "taxonomy_version": "0.19",
        "evaluator_version": "1.0",
        "miss": round(miss, 4),
        "false_alarm": round(fa, 4),
        "benign": round(benign, 4),
        "clean": round(clean_err, 4),
        "label_error": round(sum(r.label_wrong for r in results) / matched, 4) if matched else 0.0,
        "span_iou": round(sum(r.sim_sum for r in results) / matched, 4) if matched else 0.0,
        "counts": {
            "chunks": len(results), "clean_chunks": len(clean),
            "gold_mistakes": gm, "gold_benign_corrected": gf,
            "predicted_mistakes": pm, "matched_pairs": matched,
            "missed": sum(r.miss for r in results),
            "false_alarms": sum(r.false_alarm for r in results),
            "benign_flagged": sum(r.benign_flagged for r in results),
            "clean_flagged": sum(1 for r in clean if r.clean_flagged),
        },
    }


def per_label(gold_chunks: list[dict], results: list[ChunkResult]) -> dict[str, dict]:
    """Recall per gold label: how often an event of this label was matched at all."""
    out: dict[str, dict] = {}
    for gc, r in zip(gold_chunks, results):
        pairs = match_events(r.pred, list(gc.get("events") or []))
        hit = {j for _, j, _ in pairs}
        for j, g in enumerate(gc.get("events") or []):
            lab = g.get("label", "?")
            d = out.setdefault(lab, {"gold": 0, "matched": 0})
            d["gold"] += 1
            d["matched"] += 1 if j in hit else 0
    for d in out.values():
        d["recall"] = round(d["matched"] / d["gold"], 3) if d["gold"] else 0.0
    return dict(sorted(out.items()))


# ---------------------------------------------------------------- io
def load_gold(path: Path) -> list[tuple[str, dict]]:
    text = path.read_text(encoding="utf-8")
    recs = ([json.loads(l) for l in text.splitlines() if l.strip()]
            if path.suffix == ".jsonl" else json.loads(text))
    if isinstance(recs, dict):
        recs = recs.get("records") or recs.get("data") or []
    out = []
    for r in recs:
        rid = r.get("review_id")
        for c in r.get("chunks", []):
            out.append((f"{rid}:{c.get('chunk_idx')}", c))
    return out


def load_pred(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        out[f"{d.get('review_id')}:{d.get('chunk_idx')}"] = d.get("events") or []
    return out


def print_report(s: dict, labels: dict, results: list[ChunkResult]) -> None:
    c = s["counts"]
    print("---")
    print(f"study3_v19_score: {s['study3_v19_score']:.6f}")
    print(f"score_direction:  {s['score_direction']}")
    print()
    print(f"Task B scorecard, taxonomy v{s['taxonomy_version']}, evaluator v{s['evaluator_version']}")
    print(f"  Chunks: {c['chunks']} (clean {c['clean_chunks']}; gold mistakes {c['gold_mistakes']}, "
          f"gold benign/corrected {c['gold_benign_corrected']})")
    print(f"  miss:        {s['miss']:.3f}  ({c['missed']}/{c['gold_mistakes']})   x2 in score")
    print(f"  false_alarm: {s['false_alarm']:.3f}  ({c['false_alarms']}/{c['predicted_mistakes']} flags)")
    print(f"  benign:      {s['benign']:.3f}  ({c['benign_flagged']}/{c['gold_benign_corrected']})")
    print(f"  clean:       {s['clean']:.3f}  ({c['clean_flagged']}/{c['clean_chunks']})")
    print(f"  label_error: {s['label_error']:.3f}   span_iou: {s['span_iou']:.3f}   "
          f"matched pairs: {c['matched_pairs']}")
    print("  per gold label (recall of localization, any label):")
    for lab, d in labels.items():
        print(f"    {lab:<24} {d['matched']:>3}/{d['gold']:<3} {d['recall']:.2f}")
    crashes = [r for r in results if r.error]
    if crashes:
        print(f"  chunks with malformed predictions: {len(crashes)}")


def self_test(gold_path: Path) -> int:
    """Oracle checks: gold scores 0, empty scores 2, one broad flag cannot cover
    several gold events."""
    gold = load_gold(gold_path)
    ok = True

    res = [score_chunk(c, list(c.get("events") or []), k) for k, c in gold]
    s = summarize(res)
    print(f"gold-in            -> {s['study3_v19_score']:.4f} (expect 0.0), "
          f"label_error {s['label_error']:.3f}, span_iou {s['span_iou']:.3f}")
    ok &= abs(s["study3_v19_score"]) < 1e-9 and s["span_iou"] == 1.0

    res = [score_chunk(c, [], k) for k, c in gold]
    s = summarize(res)
    print(f"empty-in           -> {s['study3_v19_score']:.4f} (expect 2.0)")
    ok &= abs(s["study3_v19_score"] - 2.0) < 1e-9

    # flag the whole chunk once: must not collect credit for every gold event
    res = []
    for k, c in gold:
        n, m = len(c["transcript_tokens"]), len(c["reference_tokens"])
        res.append(score_chunk(c, [{"label": "substitution_mistake",
                                    "hyp_span": [0, n], "ref_span": [0, m]}], k))
    s = summarize(res)
    multi = [r for r in res if r.gold_mistakes > 1]
    leftover = sum(r.miss for r in multi)
    print(f"one-broad-flag     -> {s['study3_v19_score']:.4f} (expect > 1.0); "
          f"in multi-mistake chunks {leftover} of {sum(r.gold_mistakes for r in multi)} "
          f"gold mistakes still missed (expect > 0)")
    ok &= s["study3_v19_score"] > 1.0 and leftover > 0

    # a benign gold event called a mistake must be penalised
    res = []
    for k, c in gold:
        p = [{"label": "substitution_mistake", "hyp_span": g["hyp_span"], "ref_span": g["ref_span"]}
             for g in (c.get("events") or [])]
        res.append(score_chunk(c, p, k))
    s = summarize(res)
    print(f"all-called-mistake -> {s['study3_v19_score']:.4f}; benign {s['benign']:.3f} "
          f"(expect 1.0), miss {s['miss']:.3f} (expect 0.0)")
    ok &= abs(s["benign"] - 1.0) < 1e-9 and abs(s["miss"]) < 1e-9

    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Study 3 Task B scorecard (taxonomy v0.19).")
    ap.add_argument("--gold", type=Path, required=True, help="private gold .jsonl/.json")
    ap.add_argument("--pred", type=Path, help="predictions .jsonl")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test(a.gold)
    if not a.pred:
        ap.error("--pred is required unless --self-test")
    gold = load_gold(a.gold)
    pred = load_pred(a.pred)
    results = [score_chunk(c, pred.get(k, []), k) for k, c in gold]
    s = summarize(results)
    labels = per_label([c for _, c in gold], results)
    if a.json:
        print(json.dumps({"summary": s, "per_label": labels}, ensure_ascii=False, indent=1))
    else:
        print_report(s, labels, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
