#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""CI-only provisioning and reviewed semantic admission for the layout catalog.

The workflow never runs make-baseline. Runner-specific artifact hashes are
admitted only after comparing actual requests/results with reviewed evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = ROOT / 'docs-ai/tools/layouts'
DEFAULT_BASELINE = ROOT / '.github/layouts-semantic-baseline.json'
SEMANTIC_INPUTS = [
    'engine.cpp', 'CMakeLists.txt', 'toolchain.lock.json', 'build.py',
    'profiles/ios-catalog.json', 'profiles/structure-catalog.json',
    'generate_configs.py', 'survey_catalog.py', 'layout_exports.py', 'coverage.py',
    'bundle_xnu.py', 'catalog.py', 'package_catalog_runtime.py', 'package_xnu_proof.py',
    'browser/contracts.js', 'browser/dependencies.js', 'browser/layout-runtime.js',
    'browser/layout-worker.js', 'browser/layout-codec.js',
    'tests/compare_catalog.py', 'tests/compare_ipv6.py', 'tests/run_catalog_wasm.cjs',
]
RECEIPT = '.ci-compiler-receipt.json'


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value, pretty=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.ci-json-', delete=False) as stream:
        temporary = Path(stream.name)
        raw = json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2, allow_nan=False).encode() if pretty else encoded(value)
        stream.write(raw + b'\n')
    os.replace(temporary, path)


def modules():
    sys.path.insert(0, str(LAYOUTS))
    sys.path.insert(0, str(LAYOUTS / 'tests'))
    import build, catalog, compare_catalog
    return build, catalog, compare_catalog


def inputs():
    names = [LAYOUTS / name for name in SEMANTIC_INPUTS]
    names += [ROOT / 'docs-ai/tools/paths.py', ROOT / 'docs-ai/structures/layouts.json']
    return {path.relative_to(ROOT).as_posix(): file_sha(path) for path in names}


def result_rows(comparison, cases):
    names = [name for name, _ in cases]
    if comparison.get('kind') != 'xnu-catalog-contexts' or comparison.get('version') != 1 or comparison.get('wasm_parity') != 'passed' or comparison.get('dependency_tracing') is not True:
        raise ValueError('Passing full traced native/Wasm catalog comparison required')
    if comparison['cases'] != names or len(set(names)) != len(names) or set(comparison['case_evidence']) != set(names):
        raise ValueError('Missing, extra, reordered or duplicate comparison cases')
    if len(comparison['results']) != len(cases): raise ValueError('Incomplete actual comparison results')
    _, _, compare = modules()
    if comparison.get('requests_hash_algorithm') != 'length-prefixed-canonical-json-v1' or comparison['requests_sha256'] != compare.requests_hash(cases):
        raise ValueError('Complete comparison request identity differs')
    rows = []
    for (name, request), result in zip(cases, comparison['results'], strict=True):
        request_sha, result_sha = compare.result_hash(request), compare.result_hash(result)
        claim = comparison['case_evidence'][name]
        if claim['runtime_request_sha256'] != request_sha or claim['compact_result_sha256'] != result_sha:
            raise ValueError('Actual request/result bytes differ from claimed evidence: ' + name)
        rows.append({'name': name, 'request_sha256': request_sha, 'compact_result_sha256': result_sha, 'status': result['status']})
    return rows


def matrix_summary(bundle, coverage):
    """Finite membership comes from reviewed inventory, never a legacy count."""
    contexts, boundaries, statuses = set(), set(), {}
    roots = [entry['key'] for entry in coverage['entries']]
    bases = coverage['base_profiles']
    if not roots or len(set(roots)) != len(roots) or not bases or len(set(bases)) != len(bases):
        raise ValueError('Empty or duplicate finite review matrix')
    for entry in coverage['entries']:
        if set(entry['profiles']) != set(bases): raise ValueError('Incomplete finite review matrix')
        for base, cell in entry['profiles'].items():
            status = cell['status']; statuses[status] = statuses.get(status, 0) + 1
            if status == 'supported': contexts.add(cell['context_id'])
            else: boundaries.add(base + '--unsupported--' + entry['key'])
    if contexts != set(bundle['profiles']) or boundaries != set(bundle['unsupported']):
        raise ValueError('Context/boundary membership differs from finite review matrix')
    return {'roots': roots, 'base_profiles': bases, 'cells': len(roots) * len(bases),
            'statuses': statuses, 'contexts': len(contexts), 'boundaries': len(boundaries)}


def semantic_material(bundles, comparison_path):
    _, catalog, compare = modules()
    bundle, comparison = read(bundles / 'manifest.json'), read(comparison_path)
    cases = compare.load_cases(bundles)
    rows = result_rows(comparison, cases)
    if comparison['bundle_manifest_sha256'] != file_sha(bundles / 'manifest.json') or comparison['coverage_sha256'] != file_sha(bundles / 'coverage.json'):
        raise ValueError('Comparison does not bind current bundle/coverage bytes')
    coverage = read(bundles / 'coverage.json')
    from coverage import validate as validate_coverage
    validate_coverage(coverage, read(LAYOUTS / 'profiles/structure-catalog.json'), bundle)
    matrix = matrix_summary(bundle, coverage)
    source = {'release': bundle['source_release'], 'revision': bundle['source_commit']}
    if source != comparison['source'] or source != coverage['source'] or comparison['target'] != 'arm64e-apple-ios':
        raise ValueError('Catalog source/target differs')
    revision = subprocess.run(['git', '-C', str(ROOT / 'xnu'), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=30, check=True).stdout.strip()
    if revision != source['revision']: raise ValueError('Current XNU checkout revision differs from reviewed source')
    current = catalog.inventory(ROOT / 'xnu')
    if sha(encoded(current)) != bundle['source_inventory_sha256']:
        raise ValueError('Current complete XNU source inventory differs from survey')
    for (name, request), result in zip(cases, comparison['results'], strict=True):
        if name in bundle['profiles']:
            if result['status'] != 'ok' or result['diagnostics']: raise ValueError('Advertised context is not diagnostic-free')
            compare.validate_pac_context(request, result)
        elif name in bundle['unsupported'] and result['status'] == 'ok' and not result['diagnostics']:
            raise ValueError('Unsupported boundary silently became available')
    pins = read(LAYOUTS / 'toolchain.lock.json')
    return {'source': source, 'target': comparison['target'],
            'source_inventory': {'files': len(current), 'sha256': sha(encoded(current))},
            'toolchain': pins, 'inputs': inputs(), 'profiles': list(bundle['profiles']), 'matrix': matrix,
            'coverage_sha256': file_sha(bundles / 'coverage.json'), 'cases': rows}


def baseline_schema(value):
    if set(value) != {'contract', 'version', 'reviewed_evidence', 'semantics'} or value['contract'] != 'platydoc.ci-layout-semantic-baseline' or value['version'] != 1:
        raise ValueError('Unsupported reviewed CI semantic baseline')
    if not isinstance(value['reviewed_evidence'], dict) or not isinstance(value['semantics'], dict):
        raise ValueError('Malformed reviewed baseline')
    reviewed = value['reviewed_evidence']
    if set(reviewed) != {'comparison_sha256', 'note'} or not isinstance(reviewed['note'], str) or not isinstance(reviewed['comparison_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', reviewed['comparison_sha256']):
        raise ValueError('Malformed maintainer review evidence')


def check_semantics(baseline_path, bundles, comparison):
    baseline = read(baseline_path); baseline_schema(baseline)
    actual = semantic_material(bundles, comparison)
    expected = baseline['semantics']
    if actual != expected:
        changed = [key for key in sorted(set(actual) | set(expected)) if actual.get(key) != expected.get(key)]
        raise ValueError('Reviewed layout semantics changed (' + ', '.join(changed) + '); review locally and explicitly update the baseline, never regenerate it in CI')
    return actual


def reject_symlink_ancestors(path):
    for candidate in (path, *path.parents):
        if candidate.is_symlink(): raise ValueError('CI output/cache path contains a symlink: ' + str(candidate))


def download(url, target, expected):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'codeload.github.com' or parsed.query or parsed.fragment:
        raise ValueError('Only pinned official codeload archives are provisioned')
    reject_symlink_ancestors(target)
    if target.exists():
        if file_sha(target) != expected: raise ValueError('Cached archive SHA256 mismatch: ' + str(target))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.archive-', delete=False) as destination:
            temporary = Path(destination.name)
            with urllib.request.urlopen(url, timeout=120) as source: shutil.copyfileobj(source, destination)
        if file_sha(temporary) != expected: raise ValueError('Downloaded official archive SHA256 mismatch')
        os.replace(temporary, target)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)


def extract_sdk(archive, destination):
    reject_symlink_ancestors(destination)
    if destination.exists() and any(destination.iterdir()): raise ValueError('SDK extraction requires an empty CI directory')
    destination.mkdir(parents=True, exist_ok=True)
    top = None
    with tarfile.open(archive) as source:
        for member in source:
            parts = Path(member.name).parts
            if not parts or Path(member.name).is_absolute() or '..' in parts or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe SDK archive member')
            if top is None: top = parts[0]
            if parts[0] != top: raise ValueError('SDK archive has multiple roots')
            if len(parts) == 1: continue
            target = destination.joinpath(*parts[1:])
            if member.isdir(): target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as stream, target.open('wb') as output: shutil.copyfileobj(stream, output)
                target.chmod(member.mode & 0o777)


def host_context():
    versions = {}
    for name, command in [('cc', ['/usr/bin/clang', '--version']), ('cxx', ['/usr/bin/clang++', '--version']),
                          ('cmake', ['cmake', '--version']), ('ninja', ['ninja', '--version']), ('node', ['node', '--version'])]:
        versions[name] = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    return {'system': platform.platform(), 'machine': platform.machine(), 'python': platform.python_version(),
            'checkout': str(ROOT), 'image': os.environ.get('ImageVersion', ''), 'versions': versions,
            'helper_sha256': file_sha(Path(__file__)), 'semantic_inputs': inputs(),
            'baseline_sha256': file_sha(DEFAULT_BASELINE)}


def file_manifest(directory):
    files = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink(): raise ValueError('Compiler cache contains a symlink')
        if path.is_file() and path != directory / RECEIPT:
            files[path.relative_to(directory).as_posix()] = {'sha256': file_sha(path), 'bytes': path.stat().st_size, 'mode': path.stat().st_mode & 0o777}
        elif not path.is_dir() and path != directory / RECEIPT: raise ValueError('Compiler cache contains a special file')
    return files


def validate_compiler_cache(directory, context):
    reject_symlink_ancestors(directory)
    receipt = read(directory / RECEIPT)
    if set(receipt) != {'contract', 'version', 'context', 'files'} or receipt['contract'] != 'platydoc.ci-compiler-cache' or receipt['version'] != 1 or receipt['context'] != context:
        raise ValueError('Compiler cache context differs; discard this dedicated cache')
    if receipt['files'] != file_manifest(directory): raise ValueError('Compiler cache bytes/membership/modes changed')
    provenance = read(directory / 'toolchain-provenance.json')
    if provenance['pins'] != read(LAYOUTS / 'toolchain.lock.json'): raise ValueError('Cached compiler pins differ')
    for name in ('engine.cpp', 'CMakeLists.txt', 'toolchain.lock.json', 'build.py'):
        if provenance['inputs'][name] != file_sha(LAYOUTS / name): raise ValueError('Cached compiler build inputs differ')
    for name, identity in provenance['artifacts'].items():
        if receipt['files'].get(name, {}).get('sha256') != identity['sha256']: raise ValueError('Cached compiler artifact/provenance differs')
    required = {'build-native/bin/layout-engine', 'build-wasm/bin/layout-engine.js', 'build-wasm/bin/layout-engine.wasm'}
    if not required.issubset(provenance['artifacts']): raise ValueError('Cached compiler lacks native/Wasm artifacts')
    for name, identity in provenance['notices'].items():
        if receipt['files'].get('notices/' + name, {}).get('sha256') != identity: raise ValueError('Cached compiler notice differs')
    if not os.access(directory / 'build-native/bin/layout-engine', os.X_OK): raise ValueError('Cached native compiler is not executable')


def provision(downloads, cache, artifacts):
    for output in (downloads, cache, artifacts):
        reject_symlink_ancestors(output)
        for protected in (ROOT / 'docs-ai', ROOT / 'xnu', ROOT / '.git', ROOT / '.github'):
            if output == protected or output in protected.parents or protected in output.parents:
                raise ValueError('CI provisioning outputs must be dedicated and outside source trees')
    build, _, _ = modules(); pins = read(LAYOUTS / 'toolchain.lock.json'); context = host_context()
    llvm_archive = downloads / 'llvm-20.1.8.tar.gz'; sdk_archive = downloads / 'emsdk-6.0.13.tar.gz'
    download(pins['llvm']['archive_url'], llvm_archive, pins['llvm']['archive_sha256'])
    download(pins['emscripten']['emsdk_archive_url'], sdk_archive, pins['emscripten']['emsdk_archive_sha256'])
    if artifacts.exists() and any(artifacts.iterdir()):
        validate_compiler_cache(artifacts, context)
        build.extract(llvm_archive, cache / 'llvm-source', pins['llvm']['archive_sha256'])
        build.verify_source(cache / 'llvm-source')
        print('Verified compact compiler cache; LLVM resource source restored from pinned archive', flush=True)
        return
    if shutil.disk_usage(ROOT).free < 6 * 1024**3: raise ValueError('Cold layout build needs at least 6 GiB free disk space')
    sdk = cache / 'emsdk'
    extract_sdk(sdk_archive, sdk)
    build.verify_sdk(sdk_archive, sdk, pins['emscripten']['emsdk_archive_sha256'])
    release = read(sdk / 'emscripten-releases-tags.json')['releases'][pins['emscripten']['version']]
    if release != pins['emscripten']['sdk_release']: raise ValueError('Pinned SDK source release lookup differs')
    # The verified official installer uses release-addressed secondary binaries.
    # Do not claim those downloads have independent SHA pins in this repository.
    for action in ('install', 'activate'):
        subprocess.run([sys.executable, str(sdk / 'emsdk.py'), action, pins['emscripten']['version']], check=True, timeout=1800)
    subprocess.run([sys.executable, '-B', str(LAYOUTS / 'build.py'), '--llvm-archive', str(llvm_archive),
                    '--emsdk', str(sdk), '--emsdk-archive', str(sdk_archive), '--cache', str(cache),
                    '--artifact-output', str(artifacts), '--host-cc', '/usr/bin/clang', '--host-cxx', '/usr/bin/clang++', '--jobs', '2'],
                   check=True, timeout=8500)
    write(artifacts / RECEIPT, {'contract': 'platydoc.ci-compiler-cache', 'version': 1, 'context': context, 'files': file_manifest(artifacts)})
    validate_compiler_cache(artifacts, context)


def derive_pin(baseline_path, bundles, comparison, runtime, native, configs):
    semantics = check_semantics(baseline_path, bundles, comparison)
    _, catalog, _ = modules()
    package, manifest = read(runtime / 'manifest.json'), read(runtime / 'runtime-manifest.json')
    if package['kind'] != 'milestone-8-offline-structure-catalog-runtime' or package['source'] != semantics['source']:
        raise ValueError('Runner runtime package source/kind differs')
    if package['runtime_manifest_sha256'] != file_sha(runtime / 'runtime-manifest.json'):
        raise ValueError('Runtime manifest differs from packaged identity')
    actual = {p.relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file() and p != runtime / 'manifest.json'}
    if actual != set(package['files']): raise ValueError('Runtime package membership differs')
    for name, identity in package['files'].items():
        raw = catalog.checked_file(runtime, name, identity['sha256']).read_bytes()
        if len(raw) != identity['bytes']: raise ValueError('Runtime package size differs')
    report = read(comparison); reference = read(runtime / 'native-validation.json')
    if reference['comparison_sha256'] != file_sha(comparison) or reference['native_sha256'] != file_sha(native) or reference['requests_sha256'] != report['requests_sha256']:
        raise ValueError('Runner runtime is not bound to reviewed comparison/native bytes')
    if [profile['id'] for profile in manifest['profiles']] != semantics['profiles']:
        raise ValueError('Runner runtime profile matrix differs')
    catalog.validate_coverage_package(runtime, manifest, read(runtime / 'bundle-manifest.json'))
    if (runtime / 'config-provenance.json').read_bytes() != (configs / 'config-provenance.json').read_bytes():
        raise ValueError('Runner configuration provenance differs from runtime')
    return {'contract': 'platydoc.layout-artifact-lock', 'version': 2, 'source': semantics['source'],
            'source_inventory': {'algorithm': 'sha256-canonical-json-path-hashes-v1', **semantics['source_inventory']},
            'platform': 'iPhoneOS', 'profile_spec': 'profiles/ios-catalog.json', 'inventory': 'profiles/structure-catalog.json',
            'expected_profiles': semantics['profiles'], 'compiler': manifest['compiler'], 'native_sha256': file_sha(native),
            'runtime_manifest_sha256': file_sha(runtime / 'runtime-manifest.json'),
            'runtime_package_manifest_sha256': file_sha(runtime / 'manifest.json'),
            'config_provenance_sha256': file_sha(runtime / 'config-provenance.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('context')
    p = commands.add_parser('provision')
    p.add_argument('--downloads', type=Path, default=ROOT / '.docs-cache/layouts/ci-downloads')
    p.add_argument('--cache', type=Path, default=ROOT / '.docs-cache/layouts/ci-build')
    p.add_argument('--artifacts', type=Path, default=ROOT / '.docs-cache/layouts/milestone8-compiler')
    for command in ('make-baseline', 'check-semantics', 'pin'):
        p = commands.add_parser(command)
        p.add_argument('--baseline', type=Path, default=DEFAULT_BASELINE)
        p.add_argument('--bundles', type=Path, default=ROOT / '.docs-cache/layouts/structure-bundles')
        p.add_argument('--comparison', type=Path, default=ROOT / '.docs-cache/layouts/structure-comparison.json')
        if command == 'make-baseline': p.add_argument('--reviewed', action='store_true', required=True, help='Maintainer acknowledgement; never called by CI')
        if command == 'pin':
            p.add_argument('--runtime', type=Path, default=ROOT / '.docs-cache/layouts/structure-runtime')
            p.add_argument('--native', type=Path, default=ROOT / '.docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine')
            p.add_argument('--configs', type=Path, default=ROOT / '.docs-cache/layouts/milestone8-configs')
            p.add_argument('--output', type=Path, default=LAYOUTS / 'artifact-ios.lock.json')
    args = parser.parse_args()
    if args.command == 'context': print('cache_key=layouts-compiler-v1-' + sha(encoded(host_context())))
    elif args.command == 'provision': provision(args.downloads.absolute(), args.cache.absolute(), args.artifacts.absolute())
    elif args.command == 'make-baseline':
        if os.environ.get('GITHUB_ACTIONS') == 'true': raise ValueError('CI cannot author its own reviewed baseline')
        write(args.baseline, {'contract': 'platydoc.ci-layout-semantic-baseline', 'version': 1,
                             'reviewed_evidence': {'comparison_sha256': file_sha(args.comparison), 'note': 'Maintainer-reviewed native/Wasm structure matrix; update only after local review.'},
                             'semantics': semantic_material(args.bundles, args.comparison)}, pretty=True)
    elif args.command == 'check-semantics':
        semantics = check_semantics(args.baseline, args.bundles, args.comparison)
        print('All', len(semantics['cases']), 'cases match the reviewed semantic baseline')
    else:
        pin = derive_pin(args.baseline, args.bundles, args.comparison, args.runtime, args.native, args.configs)
        previous = args.output.read_bytes() if args.output.exists() else None
        write(args.output, pin)
        if args.output.resolve() == LAYOUTS / 'artifact-ios.lock.json':
            try: modules()[1].provisioned(args.runtime.resolve(), args.native.resolve(), args.configs.resolve())
            except BaseException:
                if previous is None: args.output.unlink(missing_ok=True)
                else: args.output.write_bytes(previous)
                raise
        print('Runner artifact pin admitted only after reviewed semantic equality:', args.output)


if __name__ == '__main__': main()
