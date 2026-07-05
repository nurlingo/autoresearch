"""Adapter: the incumbent hand-built follow_my_reading production pipeline
(AyahDetector + alignment segmenter), wrapped in the autoresearch contract.

Usage: copy next to eval.py as solution.py (or symlink), set FMR_REPO if the
sibling checkout is elsewhere. Scored 2026-07-06 on dataset v1.1:
  held-out test: 0.760 (det 82.9%, split 91.1%, abstain 1/2)
  full 258:      0.785 (det 81.1%, split 90.4%, abstain 2/4)
Note: the incumbent was historically tuned on the 22-case manifest, which
overlaps ~20 of these rows — the comparison favors it, and it still loses ~10x
to the agent-built winner (production/solution.py, held-out 0.079)."""
import os, sys, json, re
F = os.getenv("FMR_REPO", str(__import__("pathlib").Path(__file__).resolve().parents[2] / "follow_my_reading"))
sys.path.insert(0, F); sys.path.insert(0, F + "/backend")
os.environ.setdefault("AYAH_JSON_PATH", F + "/backend/quran.json")
os.environ.setdefault("FMR_EVAL_LOG_LEVEL", "ERROR")
from worker.services.ayah_detector import AyahDetector
from worker.services.segmentation_strategies import get_segmenter

ISTIADHA_RE = re.compile(r"^[أا]عوذ\s+بالله\s+من\s+الشيطان\s+الرجيم\s*")
BASMALA_RE = re.compile(r"^بسم\s+الله\s+الرحمن\s+الرحيم\s*")

class Solution:
    def __init__(self):
        quran = json.load(open(os.environ["AYAH_JSON_PATH"], encoding="utf-8"))
        self.by_surah = {}
        ayahs = []
        for sid, rows in quran.items():
            lst = []
            for raw in rows:
                t = raw.get("titles", {})
                a = {"id": raw["id"], "text": t.get("ar",""), "text_clean": t.get("clean",""),
                     "text_uthmani": t.get("ar","")}
                lst.append(a); ayahs.append(a)
            self.by_surah[sid] = lst
        self.detector = AyahDetector(ayahs)
        self.segmenter = get_segmenter("alignment")
    def _range(self, s, e):
        sid = s[:3]; out=[]; on=False
        for a in self.by_surah.get(sid, []):
            if a["id"]==s: on=True
            if on: out.append(a)
            if a["id"]==e: break
        return out
    def process(self, transcript):
        det = self.detector.detect(transcript)
        if det is None: return {"abstain": True}
        rng = self._range(det["start_ayah_id"], det["end_ayah_id"])
        if not rng: return {"abstain": True}
        text = BASMALA_RE.sub("", ISTIADHA_RE.sub("", transcript)).strip()
        segs = self.segmenter.segment(text, rng)
        return {"ayahs": [{"id": a["id"], "text": t} for a, t in zip(rng, segs)]}
