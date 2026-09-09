import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import eval19 as e


def event(label='substitution_mistake', hyp=(1, 2), ref=(1, 2)):
    return {'label': label, 'hyp_span': list(hyp), 'ref_span': list(ref)}


def chunk(events=None):
    return {'transcript_tokens': ['A', 'X', 'C'], 'reference_tokens': ['A', 'B', 'C'],
            'events': [event()] if events is None else events}


class EvaluatorTests(unittest.TestCase):
    def score(self, pred, gold=None):
        return e.summarize([e.score_chunk(gold or chunk(), pred, 'synthetic')])

    def test_oracle_and_empty(self):
        self.assertEqual(self.score([event()])['strict_micro_f1'], 1)
        self.assertEqual(self.score([])['micro_f1'], 0)

    def test_empty_substitution_cannot_match(self):
        s = self.score([event(hyp=(1, 1), ref=(1, 1))])
        self.assertEqual(s['micro_f1'], 0)
        self.assertEqual(s['counts']['invalid_predictions'], 1)
        self.assertEqual(s['counts']['fp'], 1)
        self.assertEqual(s['counts']['fn'], 1)

    def test_malformed_events_count_as_false_positives(self):
        bad = [None, 'event', {'label': ['bad']}, event(hyp=(-1, 2)), event(ref=(1, 9)),
               event(hyp=(True, 2)), event(hyp=(1.0, 2)), event(ref=('1', 2)),
               event('insertion_mistake'), event('omission_mistake'), event('unknown')]
        s = self.score(bad, chunk([]))
        self.assertEqual(s['counts']['invalid_predictions'], len(bad))
        self.assertEqual(s['counts']['fp'], len(bad))
        self.assertEqual(s['loc_f1'], 0)

    def test_wrong_location_and_label_lose_credit(self):
        self.assertEqual(self.score([event(hyp=(0, 1))])['micro_f1'], 0)
        self.assertEqual(self.score([event('spelling_benign')])['micro_f1'], 0)

    def test_omission_anchor_tolerance_and_strict_score(self):
        g = chunk([event('omission_mistake', (1, 1), (1, 2))])
        s = self.score([event('omission_mistake', (2, 2), (1, 2))], g)
        self.assertEqual(s['micro_f1'], 1)
        self.assertEqual(s['strict_micro_f1'], 0)
        self.assertEqual(e.span_sim([1, 1], [1, 2]), 0)

    def test_one_attempt_loses_exact_credit(self):
        g = {'transcript_tokens': ['A', 'B', 'A', 'B'], 'reference_tokens': ['A', 'B'],
             'events': [event('repetition_benign', (0, 4), (0, 2))]}
        s = self.score([event('repetition_benign', (2, 4), (0, 2))], g)
        self.assertEqual(s['micro_f1'], 1)
        self.assertEqual(s['strict_micro_f1'], 0)

    def test_secondary_raw_count_ratio(self):
        missed = self.score([])['review_cost']
        extra = self.score([event()], chunk([]))['review_cost']
        self.assertEqual(missed, 2 * extra)

    def test_invalid_gold_is_rejected(self):
        with self.assertRaises(ValueError):
            self.score([], chunk([event(hyp=(1, 1))]))

    def test_duplicate_prediction_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'pred.jsonl'
            row = json.dumps({'review_id': 'toy', 'chunk_idx': 0, 'events': []})
            p.write_text(row + '\n' + row + '\n')
            with self.assertRaises(ValueError):
                e.load_pred(p)

    def test_unlabelled_opening_is_still_input(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'records.jsonl'
            out = Path(directory) / 'inputs.jsonl'
            p.write_text(json.dumps({'review_id': 'toy', 'preamble': {'text': 'Opening text'}, 'chunks': []}) + '\n')
            subprocess.run([sys.executable, str(Path(e.__file__).parent / 'tools/make_inputs.py'), '--gold', str(p), '--out', str(out)], check=True, capture_output=True)
            row = json.loads(out.read_text())
            self.assertEqual(row['chunk_idx'], -1)
            self.assertNotIn('events', row)
            self.assertNotIn('label', row)


if __name__ == '__main__':
    unittest.main()
