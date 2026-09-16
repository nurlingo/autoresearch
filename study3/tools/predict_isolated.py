#!/usr/bin/env python3
"""Execute solution.py in Docker with input-only data, never annotation answers.

The parent is trusted. The container receives a copied solution, explicit input
fields and a Quran reference. No host HOME, repository, socket or credentials
are mounted. Resource and output limits fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import tempfile
import time
import uuid

IMAGE = "python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea"
MAX_OUTPUT = 16 * 1024 * 1024
HERE = Path(__file__).resolve().parents[1]

DRIVER = '''import contextlib, importlib.util, json, os, sys
with open('/dev/null', 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
    spec = importlib.util.spec_from_file_location('solution', '/workspace/solution.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    solution = module.Solution()
    predictions, crashes = {}, 0
    with open('/workspace/data/corpus-inputs.jsonl') as source:
        records = [json.loads(line) for line in source if line.strip()]
    for record in records:
        rows = []
        for original in record['units']:
            chunk = dict(original)
            chunk['transcript_tokens'] = list(original['transcript_tokens'])
            chunk['reference_tokens'] = list(original['reference_tokens'])
            try:
                events = solution.detect_events(chunk)
            except Exception:
                crashes += 1
                rows.append(None)
                continue
            if not isinstance(events, list):
                rows.append(None)
                continue
            for event in events:
                if isinstance(event, dict):
                    rows.append({'chunk_idx': original['chunk_idx'], 'label': event.get('label'),
                                 'hyp_span': event.get('hyp_span'), 'ref_span': event.get('ref_span')})
                else:
                    rows.append(None)
        predictions[record['case_id']] = rows
json.dump({'predictions': predictions, 'crashes': crashes}, sys.stdout, allow_nan=False)
'''


class IsolationError(RuntimeError):
    pass


def input_records(corpus):
    """One allowlist shared by preparation, feedback and final inference."""
    for rec in corpus:
        units = []
        for u in rec["units"]:
            units.append({"case_id": rec["case_id"], "chunk_idx": u["chunk_idx"],
                "n_chunks": sum(x["chunk_idx"] >= 0 for x in rec["units"]),
                "ayah_id": u.get("ayah_id"), "transcript": u["transcript"],
                "transcript_tokens": list(u["transcript_tokens"]),
                "reference_text": u["reference_text"],
                "reference_tokens": list(u["reference_tokens"])})
        yield {"case_id": rec["case_id"], "units": units}


def read_solution(path):
    """Reject symlinks/special files and bound source size before copying."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
            raise IsolationError("solution.py must be a regular file under 1 MiB")
        with os.fdopen(os.dup(fd), "rb") as f:
            source = f.read(1024 * 1024 + 1)
        if len(source) > 1024 * 1024:
            raise IsolationError("solution.py exceeds source size limit")
        return source
    finally:
        os.close(fd)


def predict_isolated(solution_path, corpus, quran_path=None, *, timeout=60, source=None):
    source = read_solution(solution_path) if source is None else source
    quran_path = quran_path or HERE / "quran-reference.json"
    image_check = subprocess.run(["docker", "image", "inspect", IMAGE],
                                capture_output=True, timeout=15)
    if image_check.returncode:
        raise IsolationError("Pinned inference image unavailable; start Docker and pull the documented image")
    with tempfile.TemporaryDirectory(prefix="study3-inference-") as tmp:
        stage = Path(tmp); stage.chmod(0o755)
        (stage / "data").mkdir(mode=0o755)
        (stage / "solution.py").write_bytes(source)
        (stage / "runner.py").write_text(DRIVER)
        (stage / "data/quran-reference.json").write_bytes(Path(quran_path).read_bytes())
        inputs = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in input_records(corpus))
        (stage / "data/corpus-inputs.jsonl").write_text(inputs)
        for path in stage.rglob("*"):
            if path.is_file(): path.chmod(0o644)
        name = "study3-predict-" + uuid.uuid4().hex
        cmd = ["docker", "run", "--rm", "--name", name, "--pull=never", "--network=none",
               "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
               "--pids-limit=64", "--memory=256m", "--cpus=1", "--user=65534:65534",
               "--tmpfs=/tmp:rw,noexec,nosuid,size=32m", "--log-driver=none",
               "--mount", f"type=bind,source={stage},target=/workspace,readonly",
               "--workdir=/workspace", "--env=PYTHONHASHSEED=0", IMAGE,
               "python", "-I", "-B", "/workspace/runner.py"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        selector = selectors.DefaultSelector(); selector.register(process.stdout, selectors.EVENT_READ)
        output = bytearray(); deadline = time.monotonic() + timeout
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise IsolationError("prediction execution exceeded time limit")
                for key, _ in selector.select(timeout=min(0.2, max(0, deadline-time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output.extend(chunk)
                        if len(output) > MAX_OUTPUT:
                            raise IsolationError("prediction output exceeded size limit")
            if process.wait(timeout=max(0.1, deadline-time.monotonic())):
                raise IsolationError("isolated prediction process failed")
            try:
                result = json.loads(output)
            except (ValueError, UnicodeError):
                raise IsolationError("isolated process returned invalid JSON") from None
            if (not isinstance(result, dict) or set(result) != {"predictions", "crashes"}
                    or not isinstance(result["predictions"], dict)
                    or type(result["crashes"]) is not int or result["crashes"] < 0):
                raise IsolationError("invalid prediction envelope")
            result["provenance"] = {"image": IMAGE, "solution_sha256": hashlib.sha256(source).hexdigest(),
                "inputs_sha256": hashlib.sha256(inputs.encode()).hexdigest(),
                "reference_sha256": hashlib.sha256(Path(quran_path).read_bytes()).hexdigest()}
            return result
        finally:
            selector.close(); process.stdout.close()
            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
            if process.poll() is None: process.kill()
            process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True, help="answer-free recording JSONL")
    parser.add_argument("--solution", type=Path, required=True)
    parser.add_argument("--quran", type=Path, default=HERE / "quran-reference.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.inputs.read_text().splitlines() if line.strip()]
    result = predict_isolated(args.solution, records, args.quran, timeout=args.timeout)
    args.out.write_text(json.dumps(result["predictions"], ensure_ascii=False) + "\n")
    args.out.with_suffix(args.out.suffix + ".metadata.json").write_text(json.dumps(
        {"crashes": result["crashes"], **result["provenance"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
