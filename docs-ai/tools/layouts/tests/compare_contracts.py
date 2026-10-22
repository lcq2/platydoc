#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run bounded native evidence then shared JavaScript contract/semantic checks."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from fixtures import cases as synthetic_cases
from contract_cases import cases as identity_cases
from xnu_cases import load_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--wasm', type=Path, required=True)
    parser.add_argument('--bundles', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    entries = []
    for name, request in synthetic_cases() + identity_cases() + load_cases(args.bundles):
        native = subprocess.run([str(args.native.resolve())], input=json.dumps(request), text=True,
                                capture_output=True, check=True, timeout=90)
        entries.append({'name': name, 'request': request, 'result': json.loads(native.stdout)})
    with tempfile.TemporaryDirectory(prefix='layout-contracts-') as directory:
        source = Path(directory) / 'evidence.json'
        source.write_text(json.dumps(entries))
        requests = Path(directory) / 'requests.json'
        requests.write_text(json.dumps([entry['request'] for entry in entries]))
        wasm = subprocess.run(['node', str(Path(__file__).with_name('run_wasm.cjs')), str(args.wasm.resolve()), str(requests)],
                              text=True, capture_output=True, timeout=240)
        if wasm.returncode:
            raise RuntimeError(wasm.stderr)
        actual = json.loads(wasm.stdout)
        for entry, result in zip(entries, actual['results'], strict=True):
            assert entry['result'] == result, 'Native/Wasm contract transport differs: ' + entry['name']
        # File-fed Node avoids platform-specific inherited stdin pipe behavior.
        with source.open() as stream:
            result = subprocess.run(['node', str(Path(__file__).with_name('contracts.test.cjs'))],
                                    stdin=stream, capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(result.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = json.loads(result.stdout)
    report['wasm_parity'] = 'passed'
    report['wasm_metrics'] = actual['metrics']
    args.output.write_text(json.dumps(report, sort_keys=True) + '\n')
    print('Contract/identity/semantic checks passed: ' + str(args.output))


if __name__ == '__main__':
    main()
