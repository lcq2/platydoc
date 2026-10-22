#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded codec/lifecycle/cache checks with native fixture evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from dependency_cases import cases, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    entries = []
    for name, request in cases():
        if name not in {'dep-base', 'dep-leaf'}:
            continue
        result = subprocess.run([str(args.native.resolve())], input=json.dumps(request), text=True, capture_output=True, check=True, timeout=30)
        result = json.loads(result.stdout)
        validate(name, result)
        entries.append(dict(name=name, request=request, result=result))
    directory = Path(__file__).parent
    lifecycle = subprocess.run(['node', str(directory / 'runtime.test.cjs')], capture_output=True, text=True, check=True, timeout=30)
    with tempfile.TemporaryDirectory(prefix='layout-runtime-') as temporary:
        evidence = Path(temporary) / 'evidence.json'
        evidence.write_text(json.dumps(dict(entries=entries)))
        with evidence.open() as stream:
            worker = subprocess.run(['node', str(directory / 'worker.test.cjs')], stdin=stream, capture_output=True, text=True, check=True, timeout=60)
    report = {'status': 'passed', 'lifecycle': json.loads(lifecycle.stdout), 'worker': json.loads(worker.stdout), 'native_cases': len(entries)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True) + '\n')
    print('Runtime checks passed: ' + str(args.output))


if __name__ == '__main__':
    main()
