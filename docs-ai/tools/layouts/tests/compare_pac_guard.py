#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Demonstrate the real lost-field override and reject it at the shared boundary."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundles', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_bytes())
    evidence = {}
    for key, profile in [('baseline', 'release-t8103--kernel'), ('narrow', 'release-t8103--security')]:
        folder = args.bundles / profile
        evidence[key] = {'request': read(folder / 'request.json'), 'result': read(folder / 'native.json')}
    request = copy.deepcopy(evidence['baseline']['request']); request['macros']['__arm64e__'] = None
    raw = subprocess.run([str(args.native.resolve())], input=json.dumps(request).encode(), capture_output=True, check=True, timeout=60)
    disabled = json.loads(raw.stdout)
    if disabled['status'] != 'ok' or disabled['diagnostics']:
        raise ValueError('Lost-field probe no longer matches its successful raw compiler boundary')
    task = lambda result: next(record for record in result['records'] if record['name'] == 'task')
    before, after = task(evidence['baseline']['result']), task(disabled)
    removed = set(field['name'] for field in before['fields']) - set(field['name'] for field in after['fields'])
    if not {'rop_pid', 'jop_pid', 'disable_user_jop'}.issubset(removed) or after['size_bytes'] >= before['size_bytes']:
        raise ValueError('Raw compiler evidence does not demonstrate omitted PAC fields')
    evidence['disabled'] = {'request': request, 'result': disabled}
    generic = {'target': 'arm64e-apple-ios', 'ptrauth_calls': True, 'ptrauth_intrinsics': True,
               'main': '/inputs/generic.c', 'files': {'/inputs/generic.c': 'struct Generic { int value; };'}}
    raw_generic = subprocess.run([str(args.native.resolve())], input=json.dumps(generic).encode(), capture_output=True, check=True, timeout=60)
    evidence['generic'] = {'request': generic, 'result': json.loads(raw_generic.stdout)}
    with tempfile.TemporaryFile() as stream:
        stream.write(json.dumps(evidence).encode()); stream.seek(0)
        node = subprocess.run(['node', str(HERE / 'pac_guard.test.cjs')], stdin=stream, capture_output=True, timeout=120)
    if node.returncode:
        raise ValueError(node.stderr.decode())
    report = {**json.loads(node.stdout), 'native_sha256': hashlib.sha256(args.native.read_bytes()).hexdigest(),
              'raw_compiler_status': disabled['status'], 'baseline_task_bytes': before['size_bytes'],
              'disabled_task_bytes': after['size_bytes'], 'raw_removed_fields': sorted(removed),
              'note': 'Raw compiler omission is evidence of the boundary; shared contracts refuse publication.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('PAC publication guard checks passed:', args.output)


if __name__ == '__main__': main()
