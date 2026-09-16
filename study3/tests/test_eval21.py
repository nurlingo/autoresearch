"""Synthetic regression cases; no private transcripts or answers."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("eval21", Path(__file__).parents[1] / "eval21.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def fixture(label="substitution_mistake"):
    return [{"case_id": "synthetic", "units": [
        {"chunk_idx": 0, "ayah_id": "A", "transcript_tokens": ["wrong", "right"],
         "reference_tokens": ["right"], "event_ids": ["event"]}],
        "events": [{"label": label, "hyp_locations": [{"chunk_idx": 0, "span": [0, 1]}],
                    "reference": {"ayah_id": "A", "span": [0, 1]}}]}]


def pred(label="substitution_mistake", h=None, r=None):
    return {"chunk_idx": 0, "label": label, "hyp_span": [0, 1] if h is None else h,
            "ref_span": [0, 1] if r is None else r}


class EvaluationTests(unittest.TestCase):
    def score(self, predictions, corpus=None):
        return ev.score(corpus or fixture(), {"synthetic": predictions})

    def test_wrong_label_fails_both_label_metrics(self):
        s = self.score([pred("spelling_benign")])
        self.assertEqual((s["micro_f1"], s["strict_micro_f1"], s["loc_f1"]), (0, 0, 1))

    def test_invalid_outputs_are_false_positives_not_crashes(self):
        bad = [None, 4, [], {"label": []}]
        for span in ([], [0], [0, 1, 2], [False, 1], [0.0, 1], ["0", 1],
                     [-1, 1], [1, 0], [0, 99], None, "0,1"):
            p = pred(); p["hyp_span"] = span; bad.append(p)
        for idx in (True, 0.0, [], "0", 99):
            p = pred(); p["chunk_idx"] = idx; bad.append(p)
        s = self.score(bad)
        self.assertEqual(s["counts"]["invalid_predictions"], len(bad))
        self.assertEqual(s["counts"]["fp"], len(bad))
        self.assertEqual(s["counts"]["fn"], 1)

    def test_event_shape_checks(self):
        for p in (pred(h=[0, 0]), pred(r=[0, 0]), pred("omission_mistake"),
                  pred("insertion_mistake"), pred("basmala_benign")):
            self.assertEqual(self.score([p])["counts"]["invalid_predictions"], 1)

    def test_same_event_cannot_be_counted_twice(self):
        corpus = fixture("repetition_benign")
        corpus[0]["events"][0]["hyp_locations"].append({"chunk_idx": 0, "span": [1, 2]})
        one = self.score([pred("repetition_benign", h=[1, 2])], corpus)
        both = self.score([pred("repetition_benign"), pred("repetition_benign", h=[1, 2])], corpus)
        self.assertEqual(one["micro_f1"], 1)
        self.assertEqual((both["counts"]["tp"], both["counts"]["fp"]), (1, 1))

    def test_cross_ayah_wrong_reference_does_not_match(self):
        corpus = fixture("omission_corrected")
        corpus[0]["units"].append({"chunk_idx": 1, "ayah_id": "B",
            "transcript_tokens": ["right"], "reference_tokens": ["right"], "event_ids": ["event"]})
        corpus[0]["events"][0].update(hyp_locations=[{"chunk_idx": 0, "span": [0, 0]},
            {"chunk_idx": 1, "span": [0, 1]}], reference={"ayah_id": "B", "span": [0, 1]})
        wrong = pred("omission_corrected", h=[0, 0]); wrong["reference_ayah_id"] = "B"
        self.assertEqual(self.score([wrong], corpus)["micro_f1"], 0)
        right = pred("omission_corrected"); right["chunk_idx"] = 1
        self.assertEqual(self.score([right], corpus)["micro_f1"], 1)

    def test_tolerant_and_exact_are_distinct(self):
        s = self.score([pred(h=[0, 2])])
        self.assertEqual((s["micro_f1"], s["strict_micro_f1"]), (1, 0))

    def test_unknown_cases_and_bad_envelopes_rejected(self):
        for predictions in ({"other": []}, {"synthetic": {}}, []):
            with self.assertRaises(ValueError): ev.score(fixture(), predictions)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "pred.json"; p.write_text('{"synthetic": [], "synthetic": []}')
            with self.assertRaises(ValueError): ev.load_predictions(p)

    def test_invalid_gold_rejected(self):
        c = fixture(); c[0]["events"][0]["reference"]["span"] = [0, 8]
        with self.assertRaises(ValueError): ev.score(c, {})
        c = fixture(); c.append(copy.deepcopy(c[0]))
        with self.assertRaises(ValueError): ev.score(c, {})

    def test_oracle_empty_and_cost_ratio(self):
        corpus = fixture()
        self.assertEqual(ev.score(corpus, ev.gold_as_predictions(corpus))["micro_f1"], 1)
        s = ev.score(corpus, {})
        self.assertEqual(s["micro_f1"], 0)
        self.assertEqual(s["review_cost"], 2 * s["review_cost_1to1"])


if __name__ == "__main__":
    unittest.main()
