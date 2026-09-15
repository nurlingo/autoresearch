#!/usr/bin/env python3
"""Evaluator v2.2 — scores the granular multi-location corpus.

v2.1 assumed one hypothesis span per event. The working corpus annotates a
recording-level event with every place it occurs: all occurrences of a repeat,
both attempts of a repair, and occasionally spans in two adjacent ayahs. 71 of
458 events have more than one location and three cross a chunk boundary, so
v2.1 cannot score this corpus at all.

Contract kept from v2.1: solutions still return per-unit events
{label, hyp_span, ref_span}, half-open over that unit's original whitespace
tokens. Nothing a solution emits has to change.

What generalizes is the credit rule. Gold says "this event happened, in these
places". A prediction that names the event and lands on ANY of those places is
right about the event, so it matches — once. It cannot then match a second
gold event, and a second prediction cannot match the same one. Extra
predictions are false positives, unmatched gold events false negatives.

Thresholds are v2.1's, unchanged: MIN_SPAN on both sides, anchor slack 1.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

MIN_SPAN = 0.50
ANCHOR_SLACK = 1

LABELS = (
    "substitution_mistake", "omission_mistake", "insertion_mistake",
    "substitution_corrected", "omission_corrected",
    "repetition_benign", "letters_benign", "spelling_benign",
    "basmala_benign", "isti3adha_benign",
)
MISTAKE = {l for l in LABELS if l.endswith("_mistake")}


def span_sim(a, b) -> float:
    """IoU for token spans; an empty span is an anchor and matches only anchors."""
    a0, a1 = a
    b0, b1 = b
    if a0 == a1 or b0 == b1:
        if a0 != a1 or b0 != b1:
            return 0.0
        d = abs(a0 - b0)
        return 1.0 if d == 0 else (0.5 if d <= ANCHOR_SLACK else 0.0)
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union else 0.0


def pair_sim(pred, gold_loc, gold_ref) -> float:
    """Both sides must overlap: one accurate side cannot carry a wrong one."""
    if pred["chunk_idx"] != gold_loc["chunk_idx"]:
        return 0.0
    h = span_sim(pred["hyp_span"], gold_loc["span"])
    r = span_sim(pred["ref_span"], gold_ref["span"])
    return min(h, r)


def best_sim(pred, gold_event) -> float:
    """A gold event is where it occurs — the closest of its locations counts."""
    ref = gold_event.get("reference") or {}
    ref_span = ref.get("span") or [0, 0]
    best = 0.0
    for loc in (gold_event.get("hyp_locations") or []):
        s = pair_sim(pred, loc, {"span": ref_span})
        if s > best:
            best = s
    return best


def match(preds, gold_events, *, strict=False):
    """Greedy one-to-one by descending similarity. Deterministic on ties."""
    cand = []
    for i, p in enumerate(preds):
        for j, g in enumerate(gold_events):
            s = best_sim(p, g)
            if s >= (1.0 if strict else MIN_SPAN):
                cand.append((-s, i, j, s))
    cand.sort()
    used_p, used_g, out = set(), set(), []
    for _, i, j, s in cand:
        if i in used_p or j in used_g:
            continue
        used_p.add(i)
        used_g.add(j)
        out.append((i, j, s))
    return out


def score(corpus, predictions):
    """predictions: {case_id: [ {chunk_idx,label,hyp_span,ref_span}, ... ]}"""
    TP = FP = FN = 0
    loc_tp = strict_tp = 0
    n_pred = n_gold = 0
    per = {l: Counter() for l in LABELS}
    invalid = 0
    clean_units = clean_flagged = 0

    for rec in corpus:
        gold = list(rec.get("events") or [])
        preds = list(predictions.get(rec["case_id"], []))
        sizes = {u["chunk_idx"]: (len(u["transcript_tokens"]), len(u["reference_tokens"]))
                 for u in rec["units"]}
        ok = []
        for p in preds:
            if (p.get("label") not in LABELS or p.get("chunk_idx") not in sizes
                    or not isinstance(p.get("hyp_span"), list)
                    or not isinstance(p.get("ref_span"), list)):
                invalid += 1
                continue
            nh, nr = sizes[p["chunk_idx"]]
            h, r = p["hyp_span"], p["ref_span"]
            if not (0 <= h[0] <= h[1] <= nh and 0 <= r[0] <= r[1] <= nr):
                invalid += 1
                continue
            ok.append(p)

        n_pred += len(ok) + (len(preds) - len(ok))
        n_gold += len(gold)

        pairs = match(ok, gold)
        loc_tp += len(pairs)
        strict_tp += len(match(ok, gold, strict=True))
        matched_p = {i for i, _, _ in pairs}
        matched_g = {j for _, j, _ in pairs}

        for i, j, _ in pairs:
            gl, pl = gold[j]["label"], ok[i]["label"]
            if gl == pl:
                TP += 1
                per[gl]["tp"] += 1
            else:
                FP += 1
                FN += 1
                per[pl]["fp"] += 1
                per[gl]["fn"] += 1
        for i, p in enumerate(ok):
            if i not in matched_p:
                FP += 1
                per[p["label"]]["fp"] += 1
        FP += len(preds) - len(ok)          # invalid predictions are false positives
        for j, g in enumerate(gold):
            if j not in matched_g:
                FN += 1
                per[g["label"]]["fn"] += 1

        # a unit gold marks clean must not be flagged with a mistake
        flagged = {p["chunk_idx"] for p in ok if p["label"] in MISTAKE}
        for u in rec["units"]:
            if not (u.get("event_ids") or []):
                clean_units += 1
                if u["chunk_idx"] in flagged:
                    clean_flagged += 1

    def prf(tp, fp, fn):
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return p, r, (2 * p * r / (p + r) if p + r else 0.0)

    p, r, micro = prf(TP, FP, FN)
    _, _, loc_f1 = prf(loc_tp, n_pred - loc_tp, n_gold - loc_tp)
    _, _, strict_f1 = prf(strict_tp, n_pred - strict_tp, n_gold - strict_tp)
    f1s = []
    for l in LABELS:
        c = per[l]
        if c["tp"] + c["fn"]:
            f1s.append(prf(c["tp"], c["fp"], c["fn"])[2])
    missed = sum(per[l]["fn"] for l in MISTAKE)
    flags = sum(per[l]["fp"] for l in MISTAKE)
    units = sum(len(rec["units"]) for rec in corpus) or 1
    return {
        "evaluator_version": "2.2",
        "micro_f1": round(micro, 4), "precision": round(p, 4), "recall": round(r, 4),
        "macro_f1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
        "strict_micro_f1": round(strict_f1, 4),
        "loc_f1": round(loc_f1, 4),
        "review_cost": round((2 * missed + flags) / units * 100, 2),
        "review_cost_1to1": round((missed + flags) / units * 100, 2),
        "clean_flag_rate": round(clean_flagged / clean_units, 4) if clean_units else 0.0,
        "counts": {"cases": len(corpus), "units": units, "gold_events": n_gold,
                   "predicted_events": n_pred, "tp": TP, "fp": FP, "fn": FN,
                   "located": loc_tp, "invalid_predictions": invalid,
                   "missed_mistakes": missed, "false_flags": flags},
        "per_label": {l: {"gold": per[l]["tp"] + per[l]["fn"],
                          "pred": per[l]["tp"] + per[l]["fp"],
                          "f1": round(prf(per[l]["tp"], per[l]["fp"], per[l]["fn"])[2], 3)}
                      for l in LABELS},
    }


def load_corpus(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def gold_as_predictions(corpus):
    """The oracle: every gold event, expressed the way a solution could express it.

    A solution sees one unit at a time, so its reference span is always in that
    unit. Three gold events name a reference in a neighbouring ayah; for those
    the oracle emits at whichever location shares the reference's ayah, which is
    the closest a per-unit prediction can come.
    """
    out = {}
    for rec in corpus:
        by_chunk = {u["chunk_idx"]: u for u in rec["units"]}
        rows = []
        for e in (rec.get("events") or []):
            locs = e.get("hyp_locations") or []
            if not locs:
                continue
            ref = e.get("reference") or {}
            ref_span = list(ref.get("span") or [0, 0])
            pick = next((l for l in locs
                         if by_chunk.get(l["chunk_idx"], {}).get("ayah_id") == ref.get("ayah_id")),
                        None)
            if pick is None:
                pick = next((l for l in locs
                             if ref_span[1] <= len(by_chunk.get(l["chunk_idx"], {})
                                                   .get("reference_tokens", []))), locs[0])
            rows.append({"chunk_idx": pick["chunk_idx"], "label": e["label"],
                         "hyp_span": list(pick["span"]), "ref_span": ref_span})
        out[rec["case_id"]] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--pred", type=Path, help="JSON {case_id: [events]}; omit for the empty baseline")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    corpus = load_corpus(a.corpus)

    if a.self_test:
        o = score(corpus, gold_as_predictions(corpus))
        e = score(corpus, {})
        print(f"gold in : micro {o['micro_f1']:.3f}  (expect 1.000)")
        print(f"empty in: micro {e['micro_f1']:.3f}  (expect 0.000)")
        return 0 if o["micro_f1"] == 1.0 and e["micro_f1"] == 0.0 else 1

    preds = json.loads(a.pred.read_text(encoding="utf-8")) if a.pred else {}
    s = score(corpus, preds)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        c = s["counts"]
        print(f"  micro F1   {s['micro_f1']:.3f}   (P {s['precision']:.3f} / R {s['recall']:.3f})")
        print(f"  exact F1   {s['strict_micro_f1']:.3f}")
        print(f"  macro F1   {s['macro_f1']:.3f}")
        print(f"  loc F1     {s['loc_f1']:.3f}")
        print(f"  cost       {s['review_cost']:.1f} (2:1) / {s['review_cost_1to1']:.1f} (1:1) per 100 units")
        print(f"  clean flag {s['clean_flag_rate']:.4f}   invalid {c['invalid_predictions']}")
        print(f"  gold {c['gold_events']}  pred {c['predicted_events']}  tp {c['tp']} fp {c['fp']} fn {c['fn']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
