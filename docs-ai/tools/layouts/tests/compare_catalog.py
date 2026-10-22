#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exact per-context native/Wasm parity with compact persistent survey evidence."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from survey_catalog import read, encoded, sha, run, status_for
from package_explorer import local_path


def load_cases(bundles, probes=True):
    manifest = read(bundles / 'manifest.json')
    cases = []
    for name, profile in manifest['profiles'].items():
        path = local_path(bundles, profile['directory'] + '/request.json')
        if sha(path.read_bytes()) != profile['request_sha256']:
            raise ValueError('Context request changed after survey')
        request = read(path)
        request['trace_dependencies'], request['trace_files'] = True, True
        cases.append((name, request))
    for name, failure in manifest['unsupported'].items():
        path = local_path(bundles, failure['directory'] + '/request.json')
        if sha(path.read_bytes()) != failure['request_sha256']:
            raise ValueError('Unsupported request changed after survey')
        cases.append((name, read(path)))
    if probes:
        base = next(((name, request) for name, request in cases if name == 'release-t8103--kernel'), None)
        if base:
            for suffix, overrides in [('no-cpi', {'CONFIG_PERVASIVE_CPI': '0'}), ('private-undefined', {'MACH_KERNEL_PRIVATE': None})]:
                request = copy.deepcopy(base[1]);request['macros'].update(overrides)
                cases.append((base[0] + '--' + suffix, request))
    if len({name for name, _ in cases}) != len(cases):
        raise ValueError('Duplicate comparison case ID')
    return cases


def requests_hash(cases):
    digest = hashlib.sha256()
    for name, request in cases:
        raw = encoded({'name': name, 'request': request})
        digest.update(len(raw).to_bytes(8, 'big'));digest.update(raw)
    return digest.hexdigest()


def compact(result):
    return {key: value for key, value in result.items() if key != 'dependency_trace'}


def result_hash(result):
    return sha(encoded(result) + b'\n')


def reuse_case(previous, directory, name, request):
    if name not in previous['cases']:
        return None
    evidence = previous['case_evidence'][name]
    if evidence['runtime_request_sha256'] != result_hash(request):
        return None
    result = copy.deepcopy(previous['results'][previous['cases'].index(name)])
    if result_hash(result) != evidence['compact_result_sha256']:
        raise ValueError('Reusable comparison result was changed: ' + name)
    if evidence['trace'] is not None:
        trace = evidence['trace']
        raw = local_path(directory, trace['path']).read_bytes()
        if len(raw) != trace['bytes'] or sha(raw) != trace['sha256']:
            raise ValueError('Reusable dependency trace was changed: ' + name)
        result['dependency_trace'] = json.loads(gzip.decompress(raw))
    if result_hash(result) != evidence['full_result_sha256']:
        raise ValueError('Reusable complete response was changed: ' + name)
    return result, previous['metrics'][name]


def validate_pac_context(request, result):
    """The supported iOS lane preserves real compiler features and their fields."""
    if request['target'] != 'arm64e-apple-ios' or request.get('ptrauth_calls') is not True or request.get('ptrauth_intrinsics') is not True:
        raise ValueError('Supported iOS context lost real PAC compiler features')
    macros = result['effective_macros']
    for name in ('__arm64e__', 'XNU_TARGET_OS_IOS', 'PLATYDOC_PTRAUTH_CALLS', 'PLATYDOC_PTRAUTH_INTRINSICS'):
        if (macros.get(name) or {}).get('replacement') != '1':
            raise ValueError('Supported iOS context lost effective feature: ' + name)
    qualifier = macros.get('__ptrauth')
    if macros.get('XNU_TARGET_OS_OSX') is not None or not qualifier or qualifier['function_like'] is not True or qualifier['replacement'] != '':
        raise ValueError('Supported iOS layout compatibility directive changed')
    if not request['files'][request['main']].startswith('#define __ptrauth(...)\n'):
        raise ValueError('Supported iOS compatibility directive is not explicit source input')
    for record in result['records']:
        if record['name'] == 'task' and not {'shared_region_auth_remapped', 'shared_region_id'}.issubset(field['name'] for field in record['fields']):
            raise ValueError('PAC-conditioned task fields were omitted')
        if record['name'] == 'machine_thread' and macros.get('HAS_APPLE_PAC') is not None and not {'rop_pid', 'jop_pid'}.issubset(field['name'] for field in record['fields']):
            raise ValueError('Source-enabled machine thread PAC fields were omitted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundles', 'native', 'wasm', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--reuse-report', type=Path,
                        help='Reuse exact request/compiler matches from an earlier local passing comparison')
    args = parser.parse_args()
    manifest = read(args.bundles / 'manifest.json')
    cases = load_cases(args.bundles)
    results, evidence, metrics = [], {}, {}
    previous, previous_sha, reused = None, None, []
    if args.reuse_report:
        raw = args.reuse_report.read_bytes()
        previous, previous_sha = json.loads(raw), sha(raw)
        if (previous.get('kind') != 'xnu-catalog-contexts' or previous.get('version') != 1 or
                previous.get('wasm_parity') != 'passed' or previous.get('dependency_tracing') is not True or
                previous.get('native_sha256') != sha(args.native.read_bytes()) or
                previous.get('wasm_factory_sha256') != sha(args.wasm.read_bytes()) or
                previous.get('wasm_sha256') != sha(args.wasm.with_suffix('.wasm').read_bytes()) or
                len(previous['cases']) != len(previous['results']) or len(set(previous['cases'])) != len(previous['cases'])):
            raise ValueError('Reuse requires a passing comparison from exactly the same native/Wasm compiler')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    trace_root = args.output.with_name(args.output.stem + '-traces')
    trace_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='layout-catalog-parity-') as temporary:
        root = Path(temporary)
        for name, request in cases:
            cached = reuse_case(previous, args.reuse_report.parent, name, request) if previous else None
            if cached is not None:
                native, metric = cached
                reused.append(name)
            else:
                native = run(args.native.resolve(), request)
                request_file, result_file, metric_file = root / 'request.json', root / 'wasm.json', root / 'metrics.json'
                request_file.write_bytes(encoded(request))
                subprocess.run(['node', str(HERE / 'run_catalog_wasm.cjs'), str(args.wasm.resolve()), str(request_file), str(result_file), str(metric_file)],
                               capture_output=True, check=True, timeout=120)
                wasm = read(result_file)
                if native != wasm:
                    raise ValueError('Full native/Wasm compiler response differs: ' + name)
                metric = read(metric_file)
            if name in manifest['profiles']:
                profile = manifest['profiles'][name]
                original = read(local_path(args.bundles, profile['directory'] + '/native.json'))
                if result_hash(original) != profile['native_result_sha256'] or compact(native) != original:
                    raise ValueError('Dependency tracing changed surveyed layout/diagnostic/context output: ' + name)
                if status_for(native)[0] != 'supported':
                    raise ValueError('Advertised runtime context failed parity: ' + name)
                validate_pac_context(request, native)
                directory, base_hash = profile['directory'], profile['request_sha256']
            elif name in manifest['unsupported']:
                original = manifest['unsupported'][name]
                if native != read(local_path(args.bundles, original['directory'] + '/native.json')):
                    raise ValueError('Unsupported survey boundary changed during parity')
                directory, base_hash = original['directory'], original['request_sha256']
            else:
                directory, base_hash = None, None
                if name.endswith('--no-cpi') and native['status'] != 'ok':
                    raise ValueError('Controlled CPI intervention failed')
                if name.endswith('--private-undefined') and native['status'] == 'ok':
                    raise ValueError('Source-private declaration boundary unexpectedly available')
            trace = native.get('dependency_trace')
            trace_identity = None
            if trace is not None:
                path = trace_root / (name + '.json.gz')
                raw = gzip.compress(encoded(trace) + b'\n', mtime=0)
                path.write_bytes(raw)
                trace_identity = {'path': path.relative_to(args.output.parent).as_posix(), 'sha256': sha(raw), 'bytes': len(raw)}
            reduced = compact(native)
            evidence[name] = {'directory': directory, 'base_request_sha256': base_hash,
                              'runtime_request_sha256': sha(encoded(request) + b'\n'), 'full_result_sha256': result_hash(native),
                              'compact_result_sha256': result_hash(reduced), 'trace': trace_identity}
            results.append(reduced);metrics[name] = metric
            print(name, native['status'], 'reused exact parity' if cached is not None else 'exact parity', flush=True)
    report = {'kind': 'xnu-catalog-contexts', 'version': 1, 'source': {'release': manifest['source_release'], 'revision': manifest['source_commit']},
              'target': manifest['target'], 'dependency_tracing': True, 'cases': [name for name, _ in cases], 'results': results,
              'case_evidence': evidence, 'requests_sha256': requests_hash(cases), 'requests_hash_algorithm': 'length-prefixed-canonical-json-v1',
              'bundle_manifest_sha256': sha((args.bundles / 'manifest.json').read_bytes()), 'coverage_sha256': manifest['coverage_sha256'],
              'native_sha256': sha(args.native.read_bytes()), 'wasm_factory_sha256': sha(args.wasm.read_bytes()),
              'wasm_sha256': sha(args.wasm.with_suffix('.wasm').read_bytes()), 'wasm_parity': 'passed', 'metrics': metrics}
    if previous is not None:
        report.update(reuse_report_sha256=previous_sha, reused_cases=reused)
    args.output.write_bytes(encoded(report) + b'\n')
    print('Catalog native/Wasm comparison:', args.output, flush=True)


if __name__ == '__main__':
    main()
