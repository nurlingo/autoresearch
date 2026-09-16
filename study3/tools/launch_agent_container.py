#!/usr/bin/env python3
"""Launch a configured agent image with only the prepared train workspace mounted.

The image must contain the desired CLI plus Python 3. API credentials are passed
only by explicit environment-name allowlist. No host HOME, Docker socket, owner
manifest, gold or checkout is available inside the container.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
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
    transient = {'.feedback', '__pycache__'}
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
    record = {'image': image, 'command': command, 'seconds': args.seconds,
        'credential_names': args.env, 'network': 'enabled for model API', 'mode': manifest['mode']}
    args.manifest.with_suffix('.launch.json').write_text(json.dumps(record, indent=2) + '\n')
    process = subprocess.Popen(cmd)
    try:
        return process.wait(timeout=args.seconds)
    except subprocess.TimeoutExpired:
        print('Agent time budget reached; stop and freeze the saved solution.')
        return 124
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if process.poll() is None: process.kill()
        process.wait(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
