#!/usr/bin/env python3
"""
eval19.py - scorecard for Study 3 Task B, taxonomy v0.19. Evaluator v2.1.

    python3 study3/eval19.py --gold <private gold.jsonl> --pred <predictions.jsonl>
    python3 study3/eval19.py --gold <gold.jsonl> --self-test

This file contains NO gold data. It reads a private gold file by path; the
reviewer bundle stays outside this repository and outside agent runtimes.

--------------------------------------------------------------------------
Why v2.0 replaces v1.0
--------------------------------------------------------------------------
v1.0 scored only mistake-flagging, so three separate faults were free: giving a
mistake the wrong mistake label, omitting benign and corrected annotations
entirely, and inventing benign annotations on clean chunks. All three, together,
still scored a perfect 0. Its match test also averaged the two span
similarities, so an exact reference span carried a match on its own and a
completely wrong hypothesis span cost nothing.

v2.1 additionally validates labels, bounds and empty-span shapes, counts invalid
predictions as false positives, and reports exact-span F1.

v2.0 makes label-aware event F1 the primary measure, requires BOTH spans to
overlap before a pair can match, and prices the application cost in raw event
counts so the stated exchange rate is the one actually implemented.

--------------------------------------------------------------------------
Contract
--------------------------------------------------------------------------
Per chunk the system receives `transcript_tokens`, `reference_tokens`,
`ayah_id`, `chunk_idx`, `n_chunks`, and returns events:

    {"label": <one of the v0.19 labels>, "hyp_span": [i, j], "ref_span": [a, b]}

Spans are half-open indices into those token arrays. An empty hypothesis span
is an omission anchor; an empty reference span is an insertion point. A chunk
with no events is clean. Reviewed ayah splits, IDs and references are supplied,
so ayah detection is not scored.

Opening formulas ARE scored: each record's isti'adhah or basmala is presented
as a chunk with `chunk_idx = -1`, its text as the transcript and an empty
reference, carrying one or two gold events. Deciding that an opening formula is benign
rather than an insertion is part of the task.

Predictions file: one JSON object per line,
    {"review_id": ..., "chunk_idx": ..., "events": [...]}
Chunks in gold but absent from predictions count as predicted-clean.

--------------------------------------------------------------------------
Matching
--------------------------------------------------------------------------
Within a chunk, predictions and gold events are paired one-to-one by maximum
total similarity, so one broad prediction can be credited with at most one gold
event. A pair is eligible only when BOTH spans overlap:

    sim(pred, gold) = min(span_sim(hyp), span_sim(ref)) >= MIN_SPAN

span_sim treats an empty span as an anchor: two anchors score 1.0 when they
coincide and 0.5 within ANCHOR_SLACK tokens. Empty spans never match
nonempty spans; two nonempty spans use intersection over union. Corrected and repetition events span all
attempts, so a prediction covering one attempt loses IoU but can still match.

Pairing itself ignores labels, which lets localization be reported separately
from naming.

--------------------------------------------------------------------------
Scores
--------------------------------------------------------------------------
PRIMARY - label-aware event F1. A paired prediction is a true positive only if
its label also matches. A pair with the wrong label counts once as a false
positive and once as a false negative, as does an unpaired prediction or gold
event.

    micro_f1     over all events               -> headline
    macro_f1     mean of per-label F1          -> protects rare labels
    event_error  = 1 - micro_f1                -> lower-is-better loop scalar
    loc_f1       same matching, labels ignored -> localization on its own
    span_iou     mean IoU over matched pairs

SECONDARY - application cost, in raw event counts so the exchange rate is real:

    missed       gold mistake events no mistake prediction matched
    false_flags  predicted mistake events matching no gold mistake
    review_cost  = (2*missed + false_flags) / chunks * 100

One missed mistake is priced at two unnecessary flags. Both terms are event
counts in the same unit, so that ratio is what the formula implements.
Reported beside it: `clean_flag_rate`, the share of no-event chunks carrying
any predicted mistake.

Reference points: predicting nothing gives micro_f1 0.0 and event_error 1.0;
returning the gold annotation gives micro_f1 1.0 and event_error 0.0.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from itertools import permutations
from pathlib import Path
from typing import Any

MIN_SPAN = 0.30      # BOTH spans must reach this before a pair can match
ANCHOR_SLACK = 1     # tokens of tolerance for omission/insertion anchors
FORMULA_IDX = -1     # chunk index used for a record's opening formula

LABELS = (
    "substitution_mistake", "omission_mistake", "insertion_mistake",
    "substitution_corrected", "omission_corrected",
    "repetition_benign", "letters_benign", "spelling_benign",
    "basmala_benign", "isti3adha_benign",
)
MISTAKE = {l for l in LABELS if l.endswith("_mistake")}


# ---------------------------------------------------------------- similarity
def event_error(event: Any, n_hyp: int, n_ref: int) -> str | None:
    """Validate original-token coordinates and label-specific empty spans."""
    if not isinstance(event, dict) or event.get("label") not in LABELS:
        return "unknown or missing event label"
    spans = []
    for name, limit in (("hyp_span", n_hyp), ("ref_span", n_ref)):
        span = event.get(name)
        if (not isinstance(span, list) or len(span) != 2
                or any(type(i) is not int for i in span)
                or not 0 <= span[0] <= span[1] <= limit):
            return "invalid " + name
        spans.append(span)
    h_empty, r_empty = (a == b for a, b in spans)
    label = event["label"]
    expected = ((True, False) if label == "omission_mistake" else
                (False, True) if label in {"insertion_mistake", "basmala_benign", "isti3adha_benign"}
                else (False, False))
    if (h_empty, r_empty) != expected:
        return "empty spans incompatible with label"
    return None


def span_sim(a: list[int], b: list[int]) -> float:
    """IoU for token spans; empty spans match only other empty anchors."""
    a0, a1 = a
    b0, b1 = b
    a_empty, b_empty = a0 == a1, b0 == b1
    if a_empty and b_empty:
        d = abs(a0 - b0)
        return 1.0 if d == 0 else (0.5 if d <= ANCHOR_SLACK else 0.0)
    if a_empty or b_empty:
        return 0.0
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union else 0.0


def event_sim(pred: dict, gold: dict) -> float:
    """Both spans must overlap: the weaker of the two decides."""
    return min(span_sim(pred.get("hyp_span"), gold.get("hyp_span")),
               span_sim(pred.get("ref_span"), gold.get("ref_span")))


def match_events(pred: list[dict], gold: list[dict], *, strict: bool = False) -> list[tuple[int, int, float]]:
    """One-to-one maximum-similarity pairing, labels ignored."""
    if not pred or not gold:
        return []
    sim = [[(float(p["hyp_span"] == g["hyp_span"] and p["ref_span"] == g["ref_span"])
             if strict else event_sim(p, g)) for g in gold] for p in pred]
    n, m = len(pred), len(gold)
    if n <= 7 and m <= 7:                       # exact; chunks hold few events
        rows = range(n) if n <= m else range(m)
        cols = range(m) if n <= m else range(n)
        best: tuple[float, list[tuple[int, int, float]]] = (-1.0, [])
        for perm in permutations(cols, len(list(rows))):
            pairs, total = [], 0.0
            for r, c in zip(rows, perm):
                i, j = (r, c) if n <= m else (c, r)
                if sim[i][j] >= MIN_SPAN:
                    pairs.append((i, j, sim[i][j]))
                    total += sim[i][j]
            if total > best[0]:
                best = (total, pairs)
        return sorted(best[1])
    order = sorted(((sim[i][j], i, j) for i in range(n) for j in range(m)), reverse=True)
    used_p: set[int] = set()
    used_g: set[int] = set()
    pairs = []
    for s, i, j in order:
        if s < MIN_SPAN or i in used_p or j in used_g:
            continue
        used_p.add(i); used_g.add(j); pairs.append((i, j, s))
    return sorted(pairs)


# ---------------------------------------------------------------- scoring
@dataclass
class ChunkResult:
    key: str
    is_clean: bool = False
    tp: list[str] = field(default_factory=list)          # gold labels correctly named
    fp: list[str] = field(default_factory=list)          # predicted labels that are wrong
    fn: list[str] = field(default_factory=list)          # gold labels not correctly named
    loc_hit: int = 0                                     # gold events paired at all
    n_gold: int = 0
    n_pred: int = 0
    sim_sum: float = 0.0
    missed: int = 0
    false_flags: int = 0
    clean_flagged: bool = False
    invalid_predictions: int = 0
    strict_tp: int = 0


def score_chunk(gold_chunk: dict, pred_events: list[dict], key: str) -> ChunkResult:
    r = ChunkResult(key)
    gold = list(gold_chunk.get("events") or [])
    if not isinstance(pred_events, list):
        raise ValueError("events must be a list: " + key)
    n, m = len(gold_chunk["transcript_tokens"]), len(gold_chunk["reference_tokens"])
    for event in gold:
        error = event_error(event, n, m)
        if error:
            raise ValueError("Invalid gold event in " + key + ": " + error)
    pred, invalid = [], []
    for event in pred_events:
        if event_error(event, n, m):
            invalid.append(event)
        else:
            pred.append(event)
    r.invalid_predictions = len(invalid)
    # Invalid predictions count as false positives, never as localization hits.
    for event in invalid:
        label = event.get("label") if isinstance(event, dict) else None
        r.fp.append(label if label in LABELS else "invalid_prediction")
        if isinstance(label, str) and label in MISTAKE:
            r.false_flags += 1
    r.is_clean, r.n_gold, r.n_pred = not gold, len(gold), len(pred_events)
    pairs = match_events(pred, gold)
    r.strict_tp = sum(pred[i]["label"] == gold[j]["label"]
                      for i, j, _ in match_events(pred, gold, strict=True))
    r.loc_hit = len(pairs)
    r.sim_sum = sum(s for _, _, s in pairs)
    paired_p = {i: j for i, j, _ in pairs}
    paired_g = {j: i for i, j, _ in pairs}

    for j, g in enumerate(gold):
        i = paired_g.get(j)
        if i is not None and pred[i].get("label") == g.get("label"):
            r.tp.append(g.get("label"))
        else:
            r.fn.append(g.get("label"))          # unpaired, or paired but misnamed
    for i, p in enumerate(pred):
        j = paired_p.get(i)
        if j is None or gold[j].get("label") != p.get("label"):
            r.fp.append(p.get("label"))

    # application cost, mistake events only
    gold_mist = [j for j, g in enumerate(gold) if g.get("label") in MISTAKE]
    for j in gold_mist:
        i = paired_g.get(j)
        if i is None or pred[i].get("label") not in MISTAKE:
            r.missed += 1
    for i, p in enumerate(pred):
        if p.get("label") not in MISTAKE:
            continue
        j = paired_p.get(i)
        if j is None or gold[j].get("label") not in MISTAKE:
            r.false_flags += 1
    r.clean_flagged = r.is_clean and any(isinstance(p, dict) and isinstance(p.get("label"), str) and p.get("label") in MISTAKE for p in pred_events)
    return r


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * rc / (p + rc) if p + rc else 0.0
    return p, rc, f


def summarize(results: list[ChunkResult]) -> dict[str, Any]:
    TP = sum(len(r.tp) for r in results)
    FP = sum(len(r.fp) for r in results)
    FN = sum(len(r.fn) for r in results)
    p, rc, micro = _prf(TP, FP, FN)

    per: dict[str, dict[str, int]] = {}
    for r in results:
        for lab in r.tp:
            per.setdefault(lab, {"tp": 0, "fp": 0, "fn": 0})["tp"] += 1
        for lab in r.fp:
            per.setdefault(lab, {"tp": 0, "fp": 0, "fn": 0})["fp"] += 1
        for lab in r.fn:
            per.setdefault(lab, {"tp": 0, "fp": 0, "fn": 0})["fn"] += 1
    gold_labels = {
        lab for lab, d in per.items() if d["tp"] + d["fn"] > 0}
    for lab, d in per.items():
        d["precision"], d["recall"], d["f1"] = (round(x, 4) for x in _prf(d["tp"], d["fp"], d["fn"]))
    macro = sum(per[l]["f1"] for l in gold_labels) / len(gold_labels) if gold_labels else 0.0

    loc_tp = sum(r.loc_hit for r in results)
    n_gold = sum(r.n_gold for r in results)
    n_pred = sum(r.n_pred for r in results)
    loc_p, loc_r, loc_f1 = _prf(loc_tp, n_pred - loc_tp, n_gold - loc_tp)
    strict_tp = sum(r.strict_tp for r in results)
    _, _, strict_f1 = _prf(strict_tp, n_pred - strict_tp, n_gold - strict_tp)

    chunks = len(results) or 1
    missed = sum(r.missed for r in results)
    flags = sum(r.false_flags for r in results)
    clean = [r for r in results if r.is_clean]
    return {
        "event_error": round(1 - micro, 6),
        "score_direction": "lower_is_better",
        "taxonomy_version": "0.19",
        "evaluator_version": "2.1",
        "micro_f1": round(micro, 4), "precision": round(p, 4), "recall": round(rc, 4),
        "macro_f1": round(macro, 4),
        "loc_f1": round(loc_f1, 4),
        "loc_precision": round(loc_p, 4), "loc_recall": round(loc_r, 4),
        "strict_micro_f1": round(strict_f1, 4),
        "span_iou": round(sum(r.sim_sum for r in results) / loc_tp, 4) if loc_tp else 0.0,
        "review_cost": round((2 * missed + flags) / chunks * 100, 2),
        "clean_flag_rate": round(sum(1 for r in clean if r.clean_flagged) / len(clean), 4) if clean else 0.0,
        "counts": {
            "chunks": len(results), "clean_chunks": len(clean),
            "gold_events": n_gold, "predicted_events": n_pred,
            "tp": TP, "fp": FP, "fn": FN, "located": loc_tp,
            "missed_mistakes": missed, "false_flags": flags,
            "invalid_predictions": sum(r.invalid_predictions for r in results),
        },
        "per_label": dict(sorted(per.items())),
    }


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
        pre = r.get("preamble") or {}
        segs = [s for s in (pre.get("segments") or []) if s.get("label")]
        if not segs and pre.get("label"):
            segs = [{"text": pre.get("text", ""), "label": pre["label"]}]
        if segs:
            toks = (pre.get("text") or "").split()
            events, cur = [], 0
            for seg in segs:                       # segments follow the text in order
                n = len(str(seg.get("text") or "").split())
                events.append({"label": seg["label"],
                               "hyp_span": [cur, min(cur + n, len(toks))], "ref_span": [0, 0]})
                cur += n
            out.append((f"{rid}:{FORMULA_IDX}", {
                "chunk_idx": FORMULA_IDX, "ayah_id": None,
                "transcript": pre.get("text", ""), "transcript_tokens": toks,
                "reference_text": "", "reference_tokens": [],
                "events": events,
            }))
        for c in r.get("chunks", []):
            out.append((f"{rid}:{c.get('chunk_idx')}", c))
    if len({key for key, _ in out}) != len(out):
        raise ValueError("Duplicate gold unit identifiers")
    return out


def load_pred(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            if (not isinstance(d, dict) or not isinstance(d.get("review_id"), str)
                    or type(d.get("chunk_idx")) is not int or not isinstance(d.get("events"), list)):
                raise ValueError("Each prediction row requires review_id, integer chunk_idx and an events list")
            key = f"{d['review_id']}:{d['chunk_idx']}"
            if key in out:
                raise ValueError("Duplicate prediction unit: " + key)
            out[key] = d["events"]
    return out


def print_report(s: dict) -> None:
    c = s["counts"]
    print("---")
    print(f"event_error:      {s['event_error']:.6f}")
    print(f"score_direction:  {s['score_direction']}")
    print()
    print(f"Task B scorecard, taxonomy v{s['taxonomy_version']}, evaluator v{s['evaluator_version']}")
    print(f"  Chunks: {c['chunks']} ({c['clean_chunks']} clean); gold events {c['gold_events']}, "
          f"predicted {c['predicted_events']}")
    print(f"  micro F1:   {s['micro_f1']:.3f}   (P {s['precision']:.3f} / R {s['recall']:.3f}; "
          f"tp {c['tp']}, fp {c['fp']}, fn {c['fn']})")
    print(f"  strict F1:  {s['strict_micro_f1']:.3f}   exact spans and labels")
    print(f"  macro F1:   {s['macro_f1']:.3f}   over the labels present in gold")
    print(f"  loc F1:     {s['loc_f1']:.3f}   labels ignored; span IoU {s['span_iou']:.3f}")
    print(f"  review_cost {s['review_cost']:.2f} per 100 chunks "
          f"({c['missed_mistakes']} missed x2 + {c['false_flags']} false flags)")
    print(f"  clean_flag_rate {s['clean_flag_rate']:.3f}")
    print(f"  invalid predictions: {c['invalid_predictions']}")
    print("  per label   gold  pred    P     R    F1")
    for lab, d in s["per_label"].items():
        print(f"    {lab:<24} {d['tp'] + d['fn']:>4}  {d['tp'] + d['fp']:>4}  "
              f"{d['precision']:.2f}  {d['recall']:.2f}  {d['f1']:.2f}")


def self_test(gold_path: Path) -> int:
    """Every case the v1.0 evaluator let through must now cost something."""
    gold = load_gold(gold_path)
    ok = True
    WRONG = {"substitution_mistake": "omission_mistake",
             "omission_mistake": "insertion_mistake",
             "insertion_mistake": "substitution_mistake",
             "repetition_benign": "spelling_benign",
             "spelling_benign": "repetition_benign"}

    def run(mut) -> dict:
        return summarize([score_chunk(c, mut(c), k) for k, c in gold])

    def check(name, s, want, cond):
        nonlocal ok
        good = cond(s)
        ok &= good
        print(f"  {'ok ' if good else 'FAIL'} {name:<46} micro_f1 {s['micro_f1']:.3f}  "
              f"error {s['event_error']:.3f}   (expect {want})")

    print("evaluator v2.1 oracle tests")
    check("gold in", run(lambda c: list(c.get("events") or [])), "f1 1.0",
          lambda s: abs(s["micro_f1"] - 1.0) < 1e-9 and abs(s["span_iou"] - 1.0) < 1e-9)
    check("empty in", run(lambda c: []), "f1 0.0",
          lambda s: s["micro_f1"] == 0.0 and s["event_error"] == 1.0)
    print("  regressions the v1.0 evaluator scored as perfect:")
    check("wrong mistake label everywhere",
          run(lambda c: [{**e, "label": WRONG.get(e["label"], e["label"])} for e in (c.get("events") or [])]),
          "f1 < 1", lambda s: s["micro_f1"] < 1.0)
    check("benign and corrected annotations omitted",
          run(lambda c: [e for e in (c.get("events") or []) if e["label"].endswith("_mistake")]),
          "f1 < 1", lambda s: s["micro_f1"] < 1.0)
    check("fabricated benign event on every clean chunk",
          run(lambda c: (c.get("events") or []) or [{"label": "repetition_benign",
                                                     "hyp_span": [0, 1], "ref_span": [0, 1]}]),
          "f1 < 1", lambda s: s["micro_f1"] < 1.0)
    check("exact ref span, hypothesis span misplaced",
          run(lambda c: [{**e, "hyp_span": [max(0, len(c["transcript_tokens"]) - 1),
                                           len(c["transcript_tokens"])]}
                         for e in (c.get("events") or [])]),
          "f1 < 1", lambda s: s["micro_f1"] < 1.0)

    # one broad flag must not harvest several gold events
    res = []
    for k, c in gold:
        n, m = len(c["transcript_tokens"]), len(c["reference_tokens"])
        res.append(score_chunk(c, [{"label": "substitution_mistake",
                                    "hyp_span": [0, n], "ref_span": [0, m]}], k))
    multi = [r for r in res if r.n_gold > 1]
    left = sum(len(r.fn) for r in multi)
    s = summarize(res)
    good = s["micro_f1"] < 0.2 and left > 0
    ok &= good
    print(f"  {'ok ' if good else 'FAIL'} {'one chunk-wide flag':<46} micro_f1 {s['micro_f1']:.3f}  "
          f"({left} gold events in multi-event chunks unrecovered)")

    synthetic = {"transcript_tokens": ["A", "X", "C"], "reference_tokens": ["A", "B", "C"],
                 "events": [{"label": "substitution_mistake", "hyp_span": [1, 2], "ref_span": [1, 2]}]}
    empty_sub = [{"label": "substitution_mistake", "hyp_span": [1, 1], "ref_span": [1, 1]}]
    s = summarize([score_chunk(synthetic, empty_sub, "synthetic")])
    check("zero-word substitution rejected", s, "f1 0, invalid 1",
          lambda s: s["micro_f1"] == 0 and s["counts"]["invalid_predictions"] == 1)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Study 3 Task B scorecard (taxonomy v0.19).")
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--pred", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test(a.gold)
    if not a.pred:
        ap.error("--pred is required unless --self-test")
    gold = load_gold(a.gold)
    pred = load_pred(a.pred)
    if set(pred) - {k for k, _ in gold}:
        raise ValueError("Predictions contain unknown unit identifiers")
    s = summarize([score_chunk(c, pred.get(k, []), k) for k, c in gold])
    print(json.dumps(s, ensure_ascii=False, indent=1) if a.json else "", end="")
    if not a.json:
        print_report(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
