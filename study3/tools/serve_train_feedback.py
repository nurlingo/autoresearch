#!/usr/bin/env python3
"""Trusted owner process. Fixed, hash-checked train annotations; no gold access.

NOT USED BY THE CURRENT PIPELINE. It serves the inputs-only regime, where the
workspace carried no answers and an agent could only learn from a scalar. Since
the train split ships annotated, `score.py` scores locally and nothing needs to
stand between the agent and its own metrics. Kept because the inputs-only regime
is a legitimate comparison -- an agent given the rubric and a score against one
given labelled data -- and prepare_agent_run.py would need only to stop writing
data/corpus-train.jsonl to restore it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import uuid
import subprocess

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import eval21
from predict_isolated import predict_isolated, IsolationError


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--max-requests', type=int, default=100)
    ap.add_argument('--timeout', type=float, default=60)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    for path, expected in [(manifest['train_path'], manifest['train_sha256']),
            (manifest['reference_path'], manifest['reference_sha256']),
            (HERE / 'eval21.py', manifest['evaluator_sha256'])]:
        if digest(path) != expected:
            ap.error('frozen train/reference/evaluator hash changed; prepare a new run')
    corpus = eval21.load_corpus(Path(manifest['train_path']))
    eval21.validate_corpus(corpus)
    workspace = Path(manifest['workspace'])
    directory = os.open(workspace / '.feedback', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    seen = set()
    try:
        while len(seen) < args.max_requests:
            try:
                fd = os.open('request.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(fd) as f:
                    info = os.fstat(f.fileno())
                    request = json.loads(f.read(1024)) if stat.S_ISREG(info.st_mode) and info.st_size <= 1024 else {}
            except (OSError, ValueError):
                time.sleep(0.2); continue
            rid = request.get('request_id') if isinstance(request, dict) else None
            if not isinstance(rid, str) or not re.fullmatch(r'[0-9a-f]{32}', rid) or rid in seen:
                time.sleep(0.2); continue
            seen.add(rid)
            try:
                result = predict_isolated(workspace / 'solution.py', corpus,
                    Path(manifest['reference_path']), timeout=args.timeout)
                metrics = eval21.score(corpus, result['predictions'])
                response = {'ok': True, 'split': 'train', 'metrics': metrics,
                    'crashes': result['crashes'], 'solution_sha256': result['provenance']['solution_sha256']}
            except (IsolationError, OSError, ValueError, subprocess.SubprocessError):
                response = {'ok': False, 'split': 'train', 'error': 'Prediction execution or validation failed.'}
            name = uuid.uuid4().hex + '.tmp-owner'
            try:
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=directory)
                with os.fdopen(fd, 'w') as f: json.dump(response, f)
                os.replace(name, rid + '.json', src_dir_fd=directory, dst_dir_fd=directory)
            except OSError:
                print('feedback queue unavailable', flush=True)
                return 1
            print(f"train request {len(seen)}: {'scored' if response['ok'] else 'failed'}", flush=True)
            if args.once: break
    finally:
        os.close(directory)


if __name__ == '__main__':
    main()
