from pathlib import Path
import os
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'baselines'))


@unittest.skipUnless(os.environ.get('FMR_REPO'), 'Set FMR_REPO to test production component adapter')
class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import incumbent19
        cls.adapter = incumbent19
        cls.sol = incumbent19.Solution()

    def predict(self, hyp, ref):
        return self.sol.detect_events({'ayah_id': '090001', 'transcript': hyp,
                                      'transcript_tokens': hyp.split(), 'reference_text': ref,
                                      'reference_tokens': ref.split()})

    def test_repeat_spans_both_copies(self):
        ref = 'لا اقسم بهذا البلد'
        events = self.predict(ref + ' ' + ref, ref)
        self.assertEqual(events, [{'label': 'repetition_benign', 'hyp_span': [0, 8], 'ref_span': [0, 4]}])

    def test_surviving_repeat_keeps_its_original_identity(self):
        ref = 'لا اقسم بهذا البلد'
        events = self.predict(ref + ' ' + ref + ' شيء', ref + ' حق')
        self.assertIn({'label': 'substitution_mistake', 'hyp_span': [8, 9], 'ref_span': [4, 5]}, events)

    def test_partial_reference_offset_is_preserved(self):
        events = self.predict('الانسان في راحة', 'لقد خلقنا الانسان في كبد')
        self.assertIn({'label': 'substitution_mistake', 'hyp_span': [2, 3], 'ref_span': [4, 5]}, events)

    def test_cleaner_note_tracks_kept_copy(self):
        from types import SimpleNamespace
        note = SimpleNamespace(position=0, text='A B')
        kept, removed = self.adapter._removed_tokens(['A','B','A','B'], 'A B', [note])
        self.assertEqual(kept, [2,3])
        self.assertEqual(removed, [[0,1]])

    def test_matching_words_separate_events(self):
        events = [{'label': 'substitution_mistake', 'hyp_span': [0,1], 'ref_span': [0,1]},
                  {'label': 'substitution_mistake', 'hyp_span': [2,3], 'ref_span': [2,3]}]
        self.assertEqual(self.adapter._merge(events), events)


if __name__ == '__main__':
    unittest.main()
