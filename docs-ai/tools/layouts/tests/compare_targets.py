#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Verify explicit target/PAC options, field presence and native/Wasm parity."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

SOURCE = '''
#if __has_feature(ptrauth_intrinsics)
#define FEATURE_INTRINSICS 1
#else
#define FEATURE_INTRINSICS 0
#endif
#if __has_feature(ptrauth_calls)
#define FEATURE_CALLS 1
#else
#define FEATURE_CALLS 0
#endif
struct PointerFields {
    void *ordinary;
#if __has_feature(ptrauth_calls)
    void (*authenticated_call)(void);
#endif
#if __has_feature(ptrauth_intrinsics)
    void *authenticated_data;
#endif
    char tail;
};
'''
OBSERVE = ['__arm64e__', '__ENVIRONMENT_IPHONE_OS_VERSION_MIN_REQUIRED__',
           '__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__', 'FEATURE_INTRINSICS', 'FEATURE_CALLS']


def request(target='arm64e-apple-ios', **options):
    return dict(target=target, main='/inputs/targets.c', files={'/inputs/targets.c': SOURCE},
                records=['PointerFields'], observe_macros=OBSERVE, **options)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--wasm', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = [('omitted', request()), ('ordinary-ios', request('aarch64-apple-ios')),
             ('historical-darwin', request('aarch64-apple-darwin'))]
    for intrinsics in (False, True):
        for calls in (False, True):
            cases.append((f'pac-{int(intrinsics)}-{int(calls)}', request(
                ptrauth_intrinsics=intrinsics, ptrauth_calls=calls)))
    for key in ('ptrauth_intrinsics', 'ptrauth_calls'):
        for value in (None, 0, 1, 'true', []):
            cases.append(('invalid-' + key + '-' + json.dumps(value), request(**{key: value})))
    for target in ('arm64e-apple-ios18.0', 'x86_64-apple-ios', 'aarch64-linux-gnu'):
        cases.append(('invalid-target-' + target, request(target)))
    results = []
    for name, req in cases:
        process = subprocess.run([str(args.native.resolve())], input=json.dumps(req),
                                 capture_output=True, text=True, check=True, timeout=30)
        result = json.loads(process.stdout)
        if name.startswith('invalid-'):
            assert result['status'] == 'invalid-request' and not result['records'], (name, result)
        else:
            assert result['status'] == 'ok' and not result['diagnostics'], (name, result)
            fields = ['ordinary']
            if req.get('ptrauth_calls'):
                fields.append('authenticated_call')
            if req.get('ptrauth_intrinsics'):
                fields.append('authenticated_data')
            fields.append('tail')
            record = result['records'][0]
            assert [f['name'] for f in record['fields']] == fields, (name, record)
            assert record['size_bytes'] == len(fields) * 8 and record['alignment_bytes'] == 8
            assert [f['offset_bits'] for f in record['fields']] == list(range(0, len(fields) * 64, 64))
            macro = lambda key: result['effective_macros'][key]
            for key, option in [('FEATURE_CALLS', 'ptrauth_calls'), ('FEATURE_INTRINSICS', 'ptrauth_intrinsics')]:
                assert macro(key)['replacement'] == str(int(req.get(option, False))), (name, key)
            assert (macro('__arm64e__') is not None) == req['target'].startswith('arm64e-')
            if req['target'].endswith('-ios'):
                assert macro('__ENVIRONMENT_IPHONE_OS_VERSION_MIN_REQUIRED__')['replacement'] == '00000'
                assert macro('__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__') is None
            else:
                assert macro('__ENVIRONMENT_IPHONE_OS_VERSION_MIN_REQUIRED__') is None
                assert macro('__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__')['replacement'] == '1040'
        results.append(result)
    with tempfile.TemporaryDirectory(prefix='layout-targets-') as temporary:
        inputs = Path(temporary) / 'requests.json'
        inputs.write_text(json.dumps([req for _, req in cases]))
        output = subprocess.run(['node', str(Path(__file__).with_name('run_wasm.cjs')),
                                 str(args.wasm.resolve()), str(inputs)], capture_output=True,
                                text=True, check=True, timeout=180)
        wasm = json.loads(output.stdout)
    assert wasm['results'] == results, 'Target/PAC native/Wasm mismatch'
    report = {'kind': 'target-pac-verification', 'cases': [name for name, _ in cases],
              'wasm_parity': 'passed', 'results': results, 'metrics': wasm['metrics'],
              'note': 'PAC-disabled cases test compiler options only; all supported iOS profiles require both options enabled.',
              'artifacts': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in (args.native, args.wasm, args.wasm.with_suffix('.wasm'))}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(cases)} target/PAC cases passed with native/Wasm parity')


if __name__ == '__main__':
    main()
