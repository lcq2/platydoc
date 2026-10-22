#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Finite native/Wasm evidence parity and shared dependency semantics."""
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
    parser.add_argument('--wasm', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    entries = []
    for name, request in cases():
        raw = subprocess.run([str(args.native.resolve())], input=json.dumps(request), capture_output=True, text=True, timeout=30, check=True)
        result = json.loads(raw.stdout)
        validate(name, result)
        entries.append(dict(name=name, request=request, result=result))
    with tempfile.TemporaryDirectory(prefix='layout-dependencies-') as temporary:
        requests = Path(temporary) / 'requests.json'
        requests.write_text(json.dumps([entry['request'] for entry in entries]))
        raw = subprocess.run(['node', str(Path(__file__).with_name('run_wasm.cjs')), str(args.wasm.resolve()), str(requests)], capture_output=True, text=True, timeout=240, check=True)
        wasm = json.loads(raw.stdout)
        for entry, actual in zip(entries, wasm['results'], strict=True):
            assert entry['result'] == actual, 'Native/Wasm evidence differs: ' + entry['name']
        evidence = Path(temporary) / 'evidence.json'
        evidence.write_text(json.dumps(dict(entries=entries)))
        with evidence.open() as stream:
            raw = subprocess.run(['node', str(Path(__file__).with_name('dependencies.test.cjs'))], stdin=stream, capture_output=True, text=True, timeout=180, check=True)
        report = json.loads(raw.stdout)
    report.update(wasm_parity='passed', wasm_metrics=wasm['metrics'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True) + '\n')
    print('Dependency discovery checks passed: ' + str(args.output))


if __name__ == '__main__':
    main()
