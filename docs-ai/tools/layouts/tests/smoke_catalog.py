#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Quick native/Wasm smoke check for explicitly selected surveyed contexts."""
import argparse
from pathlib import Path
import subprocess
import tempfile

from compare_catalog import (
    HERE, encoded, local_path, read, run, sha, validate_pac_context,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundles', 'native', 'wasm'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--context', action='append', required=True,
                        help='Exact supported context ID; repeat for affected families only')
    args = parser.parse_args()
    profiles = read(args.bundles / 'manifest.json')['profiles']
    contexts = list(dict.fromkeys(args.context))
    unknown = set(contexts) - profiles.keys()
    if unknown:
        parser.error('Unknown supported context(s): ' + ', '.join(sorted(unknown)))
    with tempfile.TemporaryDirectory(prefix='layout-smoke-') as temporary:
        root = Path(temporary)
        for name in contexts:
            profile = profiles[name]
            request_path = local_path(args.bundles, profile['directory'] + '/request.json')
            if sha(request_path.read_bytes()) != profile['request_sha256']:
                raise ValueError('Survey request changed: ' + name)
            request = read(request_path)
            native = run(args.native.resolve(), request)
            if native['status'] != 'ok' or not native['records']:
                raise ValueError('Selected context did not produce layouts: ' + name)
            validate_pac_context(request, native)
            expected_path = local_path(args.bundles, profile['directory'] + '/native.json')
            if sha(expected_path.read_bytes()) != profile['native_result_sha256']:
                raise ValueError('Survey result changed: ' + name)
            if native != read(expected_path):
                raise ValueError('Native result differs from survey: ' + name)
            request_file = root / 'request.json'
            request_file.write_bytes(encoded(request))
            result_file = root / 'wasm.json'
            subprocess.run(
                ['node', str(HERE / 'run_catalog_wasm.cjs'), str(args.wasm.resolve()),
                 str(request_file), str(result_file), str(root / 'metrics.json')],
                check=True, timeout=90,
            )
            if native != read(result_file):
                raise ValueError('Native/Wasm results differ: ' + name)
            print('PASS', name, '(survey, native/Wasm equality, iOS/PAC)', flush=True)
    print(f'{len(contexts)} context(s) checked; no release comparison report generated.')


if __name__ == '__main__':
    main()
