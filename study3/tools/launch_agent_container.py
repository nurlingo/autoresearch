#!/usr/bin/env python3
"""Launch a configured agent image with only the prepared train workspace mounted.

The image must contain the desired CLI plus Python 3. API credentials are passed
only by explicit environment-name allowlist. No host HOME, Docker socket, owner
manifest, gold or checkout is available inside the container.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import sys
import time
import uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--image', required=True)
    # CLAUDE_CODE_OAUTH_TOKEN carries a Claude subscription (`claude setup-token`)
    # instead of metered API billing; it is a credential like the rest, so it is
    # passed by explicit name and recorded in the launch record.
    ap.add_argument('--env', action='append', default=[], choices=[
        'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
        'CLAUDE_CODE_OAUTH_TOKEN', 'OPENAI_API_KEY', 'OPENAI_BASE_URL'])
    ap.add_argument('--seconds', type=int, required=True)
    ap.add_argument('--log', type=Path, help='transcript path (default: <manifest>.run.log)')
    ap.add_argument('command', nargs=argparse.REMAINDER)
    args = ap.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command: ap.error('provide the exact agent command after --')
    manifest = json.loads(args.manifest.read_text())
    workspace = Path(manifest['workspace']).resolve()
    if args.manifest.resolve().is_relative_to(workspace): ap.error('owner manifest must be outside the workspace')
    # Directories the tooling itself writes into a prepared workspace. They are
    # not part of what was prepared, so they neither have to match the manifest
    # nor may they be trusted; every file that IS in the manifest is still
    # re-hashed below. __pycache__ appears as soon as anyone runs score.py,
    # which the agent is expected to do.
    transient = {'.feedback', '__pycache__', '.scores.jsonl'}
    expected = manifest['workspace_file_sha256']
    actual = {str(p.relative_to(workspace)) for p in workspace.rglob('*')
              if p.is_file() and not transient & set(p.relative_to(workspace).parts)}
    if actual != set(expected): ap.error('workspace file allowlist changed before launch')
    for name, digest in expected.items():
        path = workspace / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            ap.error('prepared workspace bytes changed before launch; prepare a new run')
    if any(p.is_symlink() for p in workspace.rglob('*')):
        ap.error('workspace contains a symlink')
    inspection = subprocess.run(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}}'],
        capture_output=True, text=True, check=True)
    image = inspection.stdout.strip()
    name = 'study3-agent-' + uuid.uuid4().hex
    cmd = ['docker', 'run', '--rm', '--name', name, '--pull=never', '--read-only',
        '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL', '--security-opt=no-new-privileges',
        '--pids-limit=256', '--memory=2g', '--cpus=2', '--log-driver=none',
        '--tmpfs=/tmp:rw,nosuid,size=256m', '--env=HOME=/tmp/agent-home',
        '--mount', f'type=bind,source={workspace},target=/workspace', '--workdir=/workspace']
    for key in args.env:
        if key not in os.environ: ap.error(f'required environment variable is unset: {key}')
        cmd.extend(['--env', key])
    # Networking serves model APIs; this is not an internet-retrieval filter.
    cmd.extend([image, *command])
    # A measured run that leaves no trace cannot be audited afterwards: how long
    # the agent worked, how many passes it made, and whether it stopped early or
    # was cut off are all questions the transcript answers and mtimes do not.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    log_path = args.log or args.manifest.with_suffix(f'.{stamp}.run.log')
    record = {'image': image, 'command': command, 'seconds': args.seconds,
        'credential_names': args.env, 'network': 'enabled for model API',
        'mode': manifest['mode'], 'log': str(log_path),
        'started_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    launch_record = args.manifest.with_suffix('.launch.json')
    launch_record.write_text(json.dumps(record, indent=2) + '\n')

    started = time.monotonic()
    timed_out = interrupted = False
    with open(log_path, 'wb') as log:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        def pump():
            """Drain output on a thread. Reading inline would block until the
            agent closed its pipe, which is exactly the case the time budget
            exists to bound -- a hung run would never be cut off."""
            for line in process.stdout:
                sys.stdout.buffer.write(line); sys.stdout.buffer.flush()
                log.write(line); log.flush()

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        try:
            status = process.wait(timeout=args.seconds)
        except subprocess.TimeoutExpired:
            timed_out, status = True, 124
            print('\nAgent time budget reached; stop and freeze the saved solution.',
                  file=sys.stderr)
        except KeyboardInterrupt:
            # Stopping a run by hand is ordinary. Tear the container down, record
            # the run as interrupted, and report it -- not a traceback.
            interrupted, status = True, 130
            print('\nInterrupted; stopping the agent and recording the run.',
                  file=sys.stderr)
        finally:
            subprocess.run(['docker', 'rm', '-f', name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            if process.poll() is None: process.kill()
            process.wait(timeout=5)
            reader.join(timeout=5)

    elapsed = round(time.monotonic() - started, 1)
    ended = datetime.now(timezone.utc)
    # macOS monotonic time stops while the host sleeps; wall time does not. The
    # difference is time the agent was frozen but its in-container deadline was
    # still running, so a large value means the run did not get its budget.
    wall = (ended - datetime.fromisoformat(record['started_at'])).total_seconds()
    suspended = max(0, round(wall - elapsed))
    record['host_suspended_seconds'] = suspended
    if suspended > 60:
        print(f'\nWARNING: host was suspended for {suspended}s during this run; the '
              f'agent had about {elapsed:.0f}s of working time, not the budget. Do not '
              f'grade it as a measured run.', file=sys.stderr)
    record.update(ended_at=ended.isoformat(timespec='seconds'),
                  elapsed_seconds=elapsed, exit_code=status, hit_time_budget=timed_out,
                  interrupted=interrupted, budget_used=round(elapsed / args.seconds, 3))
    launch_record.write_text(json.dumps(record, indent=2) + '\n')
    # The launcher's own reporting goes to stderr: stdout is the agent's output
    # stream, and a caller piping it (the tests parse score.py's JSON straight
    # out of it) must not receive our summary mixed in.
    print(f'\nRan {elapsed:.0f}s of a {args.seconds}s budget '
          f'({record["budget_used"]:.0%}); exit {status}. Transcript: {log_path}',
          file=sys.stderr)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
