#!/usr/bin/env python3
"""Copy the completed solution into a fresh owner-only directory and hash it."""
import argparse
import hashlib
import json
from pathlib import Path
from predict_isolated import read_solution, IMAGE

p=argparse.ArgumentParser()
p.add_argument('--workspace',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.out.exists():p.error('freeze destination exists; never overwrite a prior result')
manifest=json.loads(a.manifest.read_text())
if a.workspace.resolve()!=Path(manifest['workspace']).resolve():p.error('workspace does not match the owner manifest')
source=read_solution(a.workspace/'solution.py')
a.out.mkdir(parents=True,mode=0o700)
(a.out/'solution.py').write_bytes(source)
(a.out/'solution.py').chmod(0o444)
manifest.update(solution_sha256=hashlib.sha256(source).hexdigest(), inference_image=IMAGE)
(a.out/'frozen-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(manifest['solution_sha256'])
