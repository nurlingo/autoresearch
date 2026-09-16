"""Opt-in Docker integration checks using synthetic data and private canaries."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
from predict_isolated import predict_isolated, IsolationError, IMAGE

CORPUS = [{'case_id': 'synthetic', 'units': [{'chunk_idx': 0, 'ayah_id': 'A',
    'transcript': 'wrong', 'transcript_tokens': ['wrong'],
    'reference_text': 'right', 'reference_tokens': ['right']}]}]


@unittest.skipUnless(os.environ.get('STUDY3_DOCKER_TESTS') == '1', 'set STUDY3_DOCKER_TESTS=1')
class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'solution.py'

    def run_source(self, source, **kwargs):
        self.path.write_text(source)
        return predict_isolated(self.path, CORPUS, **kwargs)

    def test_prediction_contract_and_stdout_suppression(self):
        result = self.run_source('''print('do not relay solution text')
class Solution:
 def detect_events(self, chunk):
  print('not a metric')
  return [{'label':'substitution_mistake', 'hyp_span':[0,1], 'ref_span':[0,1]}]
''')
        self.assertEqual(result['predictions']['synthetic'][0]['label'], 'substitution_mistake')
        self.assertEqual(result['crashes'], 0)

    def test_private_files_environment_and_network_unavailable(self):
        secret = Path(self.tmp.name) / 'private-answer.txt'
        secret.write_text('synthetic secret')
        os.environ['STUDY3_PRIVATE_CANARY'] = 'must not cross'
        self.addCleanup(os.environ.pop, 'STUDY3_PRIVATE_CANARY')
        source = '''import os, socket
from pathlib import Path
class Solution:
 def detect_events(self, chunk):
  assert 'STUDY3_PRIVATE_CANARY' not in os.environ
  assert not Path(PRIVATE_PATH).exists()
  assert not Path('/var/run/docker.sock').exists()
  assert set(Path('/workspace/data').iterdir()) == {Path('/workspace/data/corpus-inputs.jsonl'), Path('/workspace/data/quran-reference.json')}
  import json
  row = json.loads(Path('/workspace/data/corpus-inputs.jsonl').read_text())
  assert set(row) == {'case_id', 'units'}
  assert 'events' not in row['units'][0]
  try:
   socket.create_connection(('1.1.1.1',443), timeout=0.2)
  except OSError:
   pass
  else:
   raise AssertionError('network unexpectedly available')
  return []
'''.replace('PRIVATE_PATH', repr(str(secret)))
        result = self.run_source(source)
        self.assertEqual(result['crashes'], 0)
        self.assertEqual(result['predictions'], {'synthetic': []})

    def test_nonlist_and_exception_are_not_silently_clean(self):
        result = self.run_source('class Solution:\n def detect_events(self,c):\n  return None\n')
        self.assertEqual(result['predictions'], {'synthetic': [None]})
        result = self.run_source('class Solution:\n def detect_events(self,c):\n  raise RuntimeError("private detail")\n')
        self.assertEqual(result['predictions'], {'synthetic': [None]})
        self.assertEqual(result['crashes'], 1)

    def test_hanging_solution_times_out(self):
        with self.assertRaises(IsolationError):
            self.run_source('while True: pass\n', timeout=1)

    def test_symlink_solution_rejected(self):
        target = Path(self.tmp.name) / 'other.py'; target.write_text('')
        self.path.symlink_to(target)
        with self.assertRaises(OSError): predict_isolated(self.path, CORPUS)

    def test_prepare_feedback_freeze_and_integrity_gate(self):
        base = Path(self.tmp.name)
        quran = base / 'reference.json'; quran.write_text('{"A":"right"}')
        def record(name):
            return {'case_id': name, 'recording_id': 'recording-' + name,
                'review_status': 'approved', 'units': [{'chunk_idx': 0, 'ayah_id': 'A',
                    'transcript': name, 'transcript_tokens': [name], 'reference_text': 'right',
                    'reference_tokens': ['right'], 'event_ids': ['e']}],
                'events': [{'label': 'substitution_mistake', 'hyp_locations': [
                    {'chunk_idx': 0, 'span': [0, 1]}], 'reference': {'ayah_id': 'A', 'span': [0, 1]}}]}
        train, gold = base / 'train.jsonl', base / 'gold.jsonl'
        train.write_text(json.dumps(record('synthetic-train')) + '\n')
        gold.write_text(json.dumps(record('synthetic-holdout')) + '\n')
        run = base / 'run'
        prepare = [sys.executable, str(TOOLS / 'prepare_agent_run.py'), '--corpus', str(train),
            '--gold', str(gold), '--quran', str(quran), '--out', str(run), '--budget', 'setup']
        rejected = subprocess.run(prepare, capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('100 approved', rejected.stderr)
        subprocess.run(prepare + ['--preflight'], check=True, capture_output=True)
        manifest = base / 'run.owner.json'
        self.assertFalse(manifest.is_relative_to(run))
        inputs = json.loads((run / 'data/corpus-inputs.jsonl').read_text())
        self.assertEqual(inputs['case_id'], 'synthetic-train')
        self.assertNotIn('events', inputs['units'][0])
        # Train answers ship for development; the export is an allowlist, so the
        # review workflow around the annotation must not travel with it.
        annotated = json.loads((run / 'data/corpus-train.jsonl').read_text())
        self.assertEqual(set(annotated), {'case_id', 'units', 'events'})
        self.assertEqual(annotated['events'][0]['label'], 'substitution_mistake')
        exported = (run / 'data/corpus-train.jsonl').read_text()
        self.assertNotIn('synthetic-holdout', exported)
        for owner_only in ('recording_id', 'reviewed_by', 'review_date', 'source_review_status'):
            self.assertNotIn(owner_only, exported)
        # Scoring is local: the workspace carries answers and the evaluator, so
        # no owner-side service stands between the agent and its own metrics.
        launch = [sys.executable, str(TOOLS / 'launch_agent_container.py'), '--manifest',
            str(manifest), '--image', IMAGE, '--seconds', '30', '--',
            'python', 'score.py', '--json']
        answer = subprocess.run(launch, capture_output=True, text=True, timeout=35)
        self.assertEqual(answer.returncode, 0, answer.stderr)
        response = json.loads(answer.stdout)
        self.assertEqual(response['split'], 'train')
        self.assertEqual(response['metrics']['counts']['cases'], 1)
        self.assertEqual(response['crashes'], 0)
        frozen = base / 'frozen'
        digest = subprocess.run([sys.executable, str(TOOLS / 'freeze_solution.py'),
            '--workspace', str(run), '--manifest', str(manifest), '--out', str(frozen)],
            capture_output=True, text=True, check=True).stdout.strip()
        grade = [sys.executable, str(TOOLS / 'grade_workspace.py'), '--workspace', str(frozen),
            '--corpus', str(train), '--split', 'train', '--expected-solution-sha256', digest,
            '--preflight', '--json']
        answer = subprocess.run(grade, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(answer.stdout)['micro_f1'], 0)
        # A same-size replacement dataset must not silently inherit the freeze.
        train.write_text(json.dumps(record('different-synthetic-train')) + '\n')
        rejected = subprocess.run(grade, capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('hash mismatch', rejected.stderr)


if __name__ == '__main__':
    unittest.main()
