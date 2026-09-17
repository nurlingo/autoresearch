#!/usr/bin/env python3
"""Owner-side preparation of answer-free train inputs and a private run manifest."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21
from predict_isolated import input_records, IMAGE


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def train_records(corpus):
    """Annotation payload only -- an allowlist, never the raw record.

    The stored records carry the review workflow around the annotation: absolute
    paths into the private corpus, production recording ids, dates, reviewer
    names, and deliberation notes that name held-out cases by id. None of that
    teaches the task and some of it must not leave the owner's machine, so the
    export is built field by field rather than filtered after the fact.
    """
    for rec in corpus:
        units = [{"chunk_idx": u["chunk_idx"], "ayah_id": u.get("ayah_id"),
                  "transcript": u["transcript"],
                  "transcript_tokens": list(u["transcript_tokens"]),
                  "reference_text": u["reference_text"],
                  "reference_tokens": list(u["reference_tokens"]),
                  "event_ids": list(u.get("event_ids", []))}
                 for u in rec["units"]]
        def location(loc):
            # `words` is redundant with span+tokens but the evaluator checks the
            # two agree, so carry it only when the source actually has it.
            out = {"chunk_idx": loc.get("chunk_idx"), "span": list(loc.get("span", []))}
            if "words" in loc:
                out["words"] = loc["words"]
            return out

        events = []
        for e in rec.get("events", []):
            ref = e.get("reference") or {}
            reference = {"ayah_id": ref.get("ayah_id"), "span": list(ref.get("span", []))}
            if "words" in ref:
                reference["words"] = ref["words"]
            event = {"label": e["label"], "anchor_chunk_idx": e.get("anchor_chunk_idx"),
                     "hyp_locations": [location(l) for l in e.get("hyp_locations", [])],
                     "reference": reference}
            if e.get("event_id"):
                event["event_id"] = e["event_id"]
            events.append(event)
        yield {"case_id": rec["case_id"], "units": units, "events": events}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True, help="split-train.jsonl only")
    ap.add_argument("--gold", type=Path, required=True, help="owner-only split audit; never exported")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--quran", type=Path, default=HERE / "quran-reference.json")
    ap.add_argument("--budget", required=True)
    ap.add_argument("--preflight", action="store_true", help="allow incomplete/unapproved splits for setup tests")
    a = ap.parse_args()
    if a.out.exists() or a.out.with_name(a.out.name + ".owner.json").exists():
        ap.error("output workspace/owner manifest already exists; choose a fresh path")
    train, gold = eval21.load_corpus(a.corpus), eval21.load_corpus(a.gold)
    for corpus in (train, gold): eval21.validate_corpus(corpus)
    for key in ("case_id", "recording_id"):
        x, y = {r[key] for r in train}, {r[key] for r in gold}
        if len(x) != len(train) or len(y) != len(gold) or x & y:
            ap.error("split contains duplicate or shared recording/case identities")
    if not a.preflight and (len(train) != 100 or len(gold) != 100 or
            any(r.get("review_status") != "approved" for r in train + gold)):
        ap.error("measured run requires 100 approved train and 100 approved gold cases; use --preflight for setup checks")
    indexed = {}
    for r in gold:
        for u in r["units"]:
            if u.get("ayah_id"):
                k = (u["ayah_id"], u["transcript"])
                indexed[k] = indexed.get(k, False) or bool(u.get("event_ids"))
    for r in train:
        for u in r["units"]:
            k = (u.get("ayah_id"), u["transcript"])
            if k in indexed and (indexed[k] or u.get("event_ids")):
                ap.error("event-bearing ayah transcript shared across splits")
    reference = json.loads(a.quran.read_text())
    if any(u["reference_text"] != reference.get(u["ayah_id"])
           for r in train + gold for u in r["units"] if u.get("ayah_id")):
        ap.error("supplied Quran reference does not match the corpus")
    (a.out / "data").mkdir(parents=True)
    rows = list(input_records(train))
    (a.out / "data/corpus-inputs.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    # The annotated train split. Answers for the train half are the agent's to
    # learn from; the held-back half is never written here, and the graded
    # inference container is staged separately from this workspace, so a
    # solution cannot read these at scoring time -- see predict_isolated.
    annotated = list(train_records(train))
    # The export is what the agent learns from; hold it to the same schema the
    # evaluator enforces, so an allowlist bug fails here and not mid-run.
    eval21.validate_corpus(annotated)
    if sum(len(r["events"]) for r in annotated) != sum(len(r.get("events", [])) for r in train):
        ap.error("train export lost events")
    (a.out / "data/corpus-train.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in annotated))
    # Hard stop: no held-out case may be named anywhere in the exported bytes.
    exported = (a.out / "data/corpus-train.jsonl").read_text()
    named = sorted(g["case_id"] for g in gold
                   if re.search(rf"\b{re.escape(g['case_id'])}\b", exported))
    if named:
        ap.error(f"held-out case ids appear in the train export: {named[:5]}")
    shutil.copyfile(a.quran, a.out / "data/quran-reference.json")
    shutil.copyfile(HERE / "eval21.py", a.out / "eval21.py")
    guide = (HERE / "ANNOTATION-GUIDE.md").read_text()
    policy = (HERE / "annotation-review/HAMZA-POLICY.md").read_text().split("## Completed audit")[0]
    # Inline the public policy; no linked private review/history bundle.
    guide += "\n\n## Hamza policy (included in full for use offline)\n\n" + policy
    guide = re.sub(r"\[([^]]+)\]\((?!https?://)[^)]+\)", r"\1", guide)
    (a.out / "ANNOTATION-GUIDE.md").write_text(guide)
    task = (HERE / "agent-run/TASK.md").read_text()
    task = (task.replace("{BUDGET}", a.budget).replace("{N_CASES}", str(len(train)))
                .replace("{N_UNITS}", str(sum(len(r["units"]) for r in train)))
                .replace("{N_EVENTS}", str(sum(len(r.get("events", [])) for r in train)))
                .replace("{N_HOLDOUT}", str(len(gold))))
    if a.preflight: task = "PREFLIGHT WORKSPACE: not a measured experiment.\n\n" + task
    (a.out / "TASK.md").write_text(task)
    shutil.copyfile(HERE / "agent-run/score_agent.py", a.out / "score.py")
    (a.out / "solution.py").write_text("class Solution:\n    def detect_events(self, chunk):\n        return []\n")
    manifest = {"mode": "preflight" if a.preflight else "measured", "budget": a.budget,
        "workspace": str(a.out.resolve()), "train_path": str(a.corpus.resolve()),
        "train_sha256": sha(a.corpus), "gold_sha256": sha(a.gold),
        "reference_path": str(a.quran.resolve()), "reference_sha256": sha(a.quran),
        "evaluator_sha256": sha(HERE / "eval21.py"), "evaluator_version": "2.3",
        "inference_image": IMAGE, "train_cases": len(train), "gold_cases": len(gold),
        "workspace_file_sha256": {str(p.relative_to(a.out)): sha(p) for p in a.out.rglob("*") if p.is_file()}}
    owner = a.out.with_name(a.out.name + ".owner.json")
    owner.write_text(json.dumps(manifest, indent=2) + "\n"); owner.chmod(0o600)
    print(f"Prepared {len(train)} train cases; private owner manifest: {owner}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
