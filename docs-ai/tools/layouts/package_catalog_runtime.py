#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package validated catalog contexts for the offline handbook layout worker."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / 'tests'))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS
from package_runtime_proof import asset, digest, json_bytes, write_json
from package_explorer import local_path
from compare_catalog import load_cases, requests_hash, result_hash
from survey_catalog import root_meaning, status_for, inputs as survey_inputs, request_for, dependency_files, encoded
from coverage import validate as validate_coverage
from build import verify_source
from catalog import inventory as source_inventory, validate_coverage_package
from ubc_inputs import load as load_ubc, guard as guard_ubc


def validate_request(request, spec, base, component, headers, records,
                     universe, origins, config, configs, result, runtime=False):
    """Reconstruct every context option and byte from its authored inputs."""
    guard_ubc(request, result)
    expected, mapped = request_for(spec, base, component, headers, records,
                                   universe, origins, config, configs)
    if not set(request['files']).issubset(expected['files']):
        raise ValueError('Request has files outside the authored input universe')
    for key in ('files', 'source_paths'):
        expected[key] = {name: expected[key][name] for name in request['files']}
    if runtime:
        expected['trace_dependencies'] = True
        expected['dependency_files'] = dependency_files(result)
    # JSON identity distinguishes booleans from numeric values (Python's == does not).
    if result_hash(request) != result_hash(expected):
        changed = sorted(key for key in set(request) | set(expected)
                         if key not in request or key not in expected or
                         result_hash(request[key]) != result_hash(expected[key]))
        raise ValueError('Request differs from authored configuration: ' + ', '.join(changed))
    return {name: mapped[name] for name in request['files']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('native', 'wasm', 'native-report', 'bundles', 'config-root', 'notices', 'provenance', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--llvm-source', type=Path, default=PROJECT_ROOT / '.docs-cache/layouts/llvm-source')
    args = parser.parse_args()
    consumed = {}
    def read_input(path):
        path = path.resolve()
        raw = path.read_bytes()
        consumed[path] = digest(raw)
        return raw
    def checked(root, name, expected):
        path = local_path(root, name)
        raw = read_input(path)
        if digest(raw) != expected:
            raise ValueError('Changed input: ' + str(path))
        return raw
    output = args.output.resolve()
    for protected in (SOURCE_ROOT.resolve(), DOCS.resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError('Runtime package must be outside source/handbook trees and their ancestors')
    marker = '.layout-catalog-runtime'
    if output.exists() and (not output.is_dir() or
            (any(output.iterdir()) and not (output / marker).is_file()) or
            any(path.is_symlink() for path in output.rglob('*'))):
        raise ValueError('Refusing nonempty unmarked or symlink-containing runtime output')

    report_raw = read_input(args.native_report)
    report = json.loads(report_raw)
    if (report.get('kind'), report.get('version'), report.get('wasm_parity'), report.get('dependency_tracing')) != (
            'xnu-catalog-contexts', 1, 'passed', True):
        raise ValueError('Passing traced native/Wasm catalog comparison required')
    if report.get('requests_hash_algorithm') != 'length-prefixed-canonical-json-v1':
        raise ValueError('Unknown request identity algorithm')
    bundle_raw = checked(args.bundles, 'manifest.json', report['bundle_manifest_sha256'])
    bundle = json.loads(bundle_raw)
    coverage_raw = checked(args.bundles, 'coverage.json', bundle['coverage_sha256'])
    coverage = json.loads(coverage_raw)
    if report['coverage_sha256'] != bundle['coverage_sha256']:
        raise ValueError('Coverage changed after comparison')
    source = {'release': bundle['source_release'], 'revision': bundle['source_commit']}
    if report['source'] != source or coverage['source'] != source or report['target'] != bundle['target']:
        raise ValueError('Comparison source/target mismatch')
    spec_raw = checked(HERE, bundle['profile_spec_path'], bundle['profile_spec_sha256'])
    spec = json.loads(spec_raw)
    inventory_raw = checked(HERE, bundle['inventory_path'], bundle['inventory_sha256'])
    declared = json.loads(inventory_raw)
    validate_coverage(coverage, declared, bundle, args.bundles)
    snapshot = source_inventory(SOURCE_ROOT)
    if digest(json_bytes(snapshot)) != bundle['source_inventory_sha256']:
        raise ValueError('XNU source membership/content changed')
    if (spec['target'] != 'arm64e-apple-ios' or spec.get('platform') != 'iPhoneOS' or
            spec.get('ptrauth_intrinsics') is not True or spec.get('ptrauth_calls') is not True):
        raise ValueError('Supported iOS contexts require arm64e and both PAC compiler features')
    config_raw = checked(args.config_root, 'config-provenance.json', bundle['config_manifest_sha256'])
    config = json.loads(config_raw)
    checked(HERE, 'generate_configs.py', config['generator_sha256'])
    for name, sha in config['source_inputs'].items():
        checked(SOURCE_ROOT, name, sha)
    for profile in config['profiles'].values():
        if profile['platform'] != 'iPhoneOS':
            raise ValueError('Mixed configuration platforms')
        for name, sha in profile['files'].items():
            checked(args.config_root, profile['directory'] + '/' + name, sha)

    provenance_raw = read_input(args.provenance)
    provenance = json.loads(provenance_raw)
    source_identity = verify_source(args.llvm_source)
    if source_identity != bundle['llvm_source_manifest_sha256'] or source_identity != provenance['build_identity']['source_tree_manifest_sha256']:
        raise ValueError('Compiler resource source identity differs from build/survey')
    llvm_files = json.loads(read_input(args.llvm_source / '.source-files.json'))
    universe, origins, rebuilt_config, rebuilt_snapshot, rebuilt_llvm = survey_inputs(
        spec, args.llvm_source, args.config_root)
    from generate_sysproto import load as load_syscalls
    generated_root, generated = load_syscalls(spec, snapshot)
    if generated != bundle.get('generated_syscalls'):
        raise ValueError('Generated syscall header provenance differs from survey')
    generated_files = {}
    if generated is not None:
        generated_files = {name: checked(generated_root, name, sha) for name, sha in generated['files'].items()}
        generated_files['generation.json'] = read_input(generated_root / 'generation.json')
    from generate_mig import load as load_mig
    mig_root, mig = load_mig(spec, args.config_root)
    if mig != bundle.get('generated_mig'):
        raise ValueError('Generated MIG header provenance differs from survey')
    mig_files = {}
    if mig is not None:
        for profile in mig['profiles'].values():
            for name, sha in profile['files'].items():
                name = profile['directory'] + '/' + name
                mig_files[name] = checked(mig_root, name, sha)
        mig_files['generation.json'] = read_input(mig_root / 'generation.json')
        mig_files['MIG-APPLE_LICENSE.txt'] = checked(mig_root, 'MIG-APPLE_LICENSE.txt', mig['license_sha256'])
    ubc, ubc_files, ubc_root = load_ubc(spec)
    if ubc != bundle.get('ubc_layout_inputs'):
        raise ValueError('UBC dependency provenance differs from survey')
    if ubc is not None:
        checked(ubc_root, 'source.json', spec['ubc_layout_inputs']['trustcache_provenance_sha256'])
        for name in ubc['files']:
            origin = ubc['files'][name]
            origin_root, original = ((HERE / 'compatibility', name) if origin['kind'] == 'layout-compatibility' else (ubc_root, Path(name).name))
            checked(origin_root, original, origin['sha256'])
        checked(ubc_root, 'APPLE_LICENSE', ubc['license_sha256'])
    if (rebuilt_config != config or rebuilt_snapshot != snapshot or rebuilt_llvm != source_identity or
            origins != bundle['discovery_universe']):
        raise ValueError('Survey input universe differs from original source/export rules')
    for name, sha in bundle['tool_inputs'].items():
        checked(HERE, name, sha)
    factory, wasm = read_input(args.wasm), read_input(args.wasm.with_suffix('.wasm'))
    native_sha = digest(read_input(args.native))
    for raw, report_key, artifact_path in (
            (factory, 'wasm_factory_sha256', 'build-wasm/bin/layout-engine.js'),
            (wasm, 'wasm_sha256', 'build-wasm/bin/layout-engine.wasm')):
        if digest(raw) != report[report_key] or digest(raw) != provenance['artifacts'][artifact_path]['sha256']:
            raise ValueError('Compiler artifact differs from comparison/build provenance')
    if native_sha != report['native_sha256'] or native_sha != provenance['artifacts']['build-native/bin/layout-engine']['sha256']:
        raise ValueError('Native compiler identity mismatch')
    for name in ('engine.cpp', 'CMakeLists.txt', 'toolchain.lock.json', 'build.py'):
        checked(HERE, name, provenance['inputs'][name])
    for name, sha in provenance['notices'].items():
        checked(args.notices, name, sha)
    for path in (SOURCE_ROOT / 'APPLE_LICENSE', PROJECT_ROOT / 'LICENSE', PROJECT_ROOT / 'LICENSE-DOCS'):
        read_input(path)
    if not {'LLVM-LICENSE.txt', 'Clang-LICENSE.txt', 'Emscripten-LICENSE.txt', 'emsdk-LICENSE.txt'}.issubset(provenance['notices']):
        raise ValueError('Required compiler notices missing')

    cases = load_cases(args.bundles)
    if report['cases'] != [name for name, _ in cases] or report['requests_sha256'] != requests_hash(cases):
        raise ValueError('Comparison does not describe current requests')
    if set(report['case_evidence']) != set(report['cases']):
        raise ValueError('Incomplete comparison evidence')
    compiler = None
    by_case = dict(zip(report['cases'], report['results'], strict=True))
    for (name, request), result in zip(cases, report['results'], strict=True):
        evidence = report['case_evidence'][name]
        if result_hash(request) != evidence['runtime_request_sha256'] or result_hash(result) != evidence['compact_result_sha256']:
            raise ValueError('Changed comparison request/result: ' + name)
        full = dict(result)
        trace = evidence['trace']
        if trace is not None:
            raw = checked(args.native_report.parent, trace['path'], trace['sha256'])
            if len(raw) != trace['bytes']:
                raise ValueError('Trace size mismatch')
            full['dependency_trace'] = json.loads(gzip.decompress(raw))
        if result_hash(full) != evidence['full_result_sha256']:
            raise ValueError('Full compiler evidence mismatch: ' + name)
        current = result.get('compiler')
        if current:
            if compiler is not None and current != compiler:
                raise ValueError('Mixed compiler identities')
            compiler = current
        if name in bundle['profiles']:
            profile = bundle['profiles'][name]
            info = json.loads(checked(args.bundles, profile['directory'] + '/manifest.json', profile['manifest_sha256']))
            checked(args.bundles, profile['directory'] + '/request.json', profile['request_sha256'])
            checked(args.bundles, profile['directory'] + '/native.json', profile['native_result_sha256'])
            if result['status'] != 'ok' or result['diagnostics'] or trace is None:
                raise ValueError('Advertised runtime context failed: ' + name)
            if (request['target'] != spec['target'] or request.get('ptrauth_intrinsics') is not True or
                    request.get('ptrauth_calls') is not True):
                raise ValueError('Runtime context lost required target/PAC features')
            if evidence['base_request_sha256'] != profile['request_sha256']:
                raise ValueError('Survey request identity mismatch')
            if set(info['files']) != set(request['files']):
                raise ValueError('Header manifest membership differs from supplied files')
            context = spec['contexts'][profile['family']]
            selected_records = [entry['record'] for entry in coverage['entries']
                                if entry['record'] in context['records'] and
                                entry['profiles'][profile['base_profile']]['status'] == 'supported']
            if profile['records'] != selected_records:
                raise ValueError('Context root selection differs from the finite survey')
            expected_origins = validate_request(request, spec, profile['base_profile'], context['component'],
                context['headers'], selected_records, universe, origins, config, args.config_root, result, runtime=True)
            if info['files'] != expected_origins:
                raise ValueError('Header origins differ from source/export rules')
            # validate_request above reconstructs the entire entry, including
            # any include-local diagnostic push/pop, from the authored spec.
            if profile['component'] != context['component']:
                raise ValueError('Analysis entry/component differs from authored context')
            for virtual, content in request['files'].items():
                origin = info['files'][virtual]
                if digest(content.encode()) != origin['sha256']:
                    raise ValueError('Header identity mismatch: ' + virtual)
                if origin['kind'] in ('xnu', 'xnu-export'):
                    checked(SOURCE_ROOT, origin['path'], origin['sha256'])
                elif origin['kind'] == 'generated-config':
                    selected = config['profiles'][profile['base_profile']]
                    basename = virtual.removeprefix('/inputs/generated/')
                    if (origin['path'] != selected['directory'] + '/' + basename or
                            selected['files'].get(basename) != origin['sha256']):
                        raise ValueError('Generated header comes from wrong configuration')
                    checked(args.config_root, origin['path'], origin['sha256'])
                elif origin['kind'] == 'clang-resource':
                    if llvm_files.get(origin['path']) != origin['sha256']:
                        raise ValueError('Resource header lacks compiler-source provenance')
                    checked(args.llvm_source, origin['path'], origin['sha256'])
                elif origin['kind'] == 'generated-syscalls':
                    if generated is None or generated['files'].get(origin['path']) != origin['sha256']:
                        raise ValueError('Generated syscall header lacks original recipe provenance')
                    checked(generated_root, origin['path'], origin['sha256'])
                elif origin['kind'] == 'generated-mig':
                    if mig is None or origin['path'] not in mig_files or digest(mig_files[origin['path']]) != origin['sha256']:
                        raise ValueError('Generated MIG header lacks original recipe provenance')
                    checked(mig_root, origin['path'], origin['sha256'])
                elif origin['kind'] in ('external-header', 'layout-compatibility'):
                    if ubc is None or ubc['files'].get(origin['path'], {}).get('sha256') != origin['sha256'] or ubc['files'][origin['path']]['kind'] != origin['kind']:
                        raise ValueError('UBC dependency header lacks reviewed source provenance')
                elif origin['kind'] != 'analysis-entry' or virtual != request['main']:
                    raise ValueError('Unknown header origin')
        elif name in bundle['unsupported'] and status_for(result)[0] == 'supported':
            raise ValueError('Unsupported context unexpectedly passes admission')
    if not compiler or not bundle['profiles']:
        raise ValueError('No validated runtime contexts')
    if compiler['revision'] != provenance['pins']['llvm']['revision'] or compiler['engine_sha256'] != digest((HERE / 'engine.cpp').read_bytes()):
        raise ValueError('Compiler source identity mismatch')

    surveys = []
    if (coverage['base_profiles'] != spec['configurations'] or
            [entry['key'] for entry in coverage['entries']] != [entry['key'] for entry in declared['entries']]):
        raise ValueError('Coverage does not match finite authored inventory/profile space')
    for entry in coverage['entries']:
        if set(entry['profiles']) != set(spec['configurations']):
            raise ValueError('Incomplete root/profile coverage')
        for base, cell in entry['profiles'].items():
            original = json.loads(checked(args.bundles, cell['directory'] + '/native.json', cell['native_result_sha256']))
            original_request = json.loads(checked(args.bundles, cell['directory'] + '/request.json', cell['request_sha256']))
            validate_request(original_request, spec, base, entry['component'], entry['headers'],
                [entry['record']], universe, origins, config, args.config_root, original)
            if (status_for(original) != (cell['status'], cell['reason']) or
                    original['status'] != cell['transport_status'] or original['diagnostics'] != cell['diagnostics']):
                raise ValueError('Survey cell differs from compiler evidence')
            meaning = None
            if cell['status'] == 'supported':
                context_id = cell['context_id']
                if context_id not in bundle['profiles'] or bundle['profiles'][context_id]['base_profile'] != base:
                    raise ValueError('Supported cell has wrong runtime context')
                meaning = root_meaning(original, entry['record'])
                if meaning != root_meaning(by_case[context_id], entry['record']):
                    raise ValueError('Merged runtime context changed root semantics')
                matching = [record for record in by_case[context_id]['records'] if record['name'] == entry['record']]
                if len(matching) != 1 or matching[0]['id'] != cell['declaration_id']:
                    raise ValueError('Coverage declaration identity differs from runtime result')
            elif original['status'] != 'ok' and original['records']:
                raise ValueError('Unsupported survey cell contains geometry')
            surveys.append({'key': entry['key'], 'base_profile': base,
                            'request_sha256': cell['request_sha256'], 'native_result_sha256': cell['native_result_sha256'],
                            'transport_status': original['status'], 'diagnostics': original['diagnostics'],
                            'layout_meaning_sha256': result_hash(meaning) if meaning is not None else None})

    names = ['package_catalog_runtime.py', 'package_runtime_proof.py', 'package_explorer.py',
             'survey_catalog.py', 'generate_sysproto.py', 'generate_mig.py', 'ubc_inputs.py', 'compatibility/CoreEntitlements/V2/API.h', 'compatibility/CoreEntitlements/V2/Kernel.h', 'layout_exports.py', 'coverage.py', 'bundle_xnu.py', 'catalog.py',
             'tests/compare_catalog.py', 'tests/run_catalog_wasm.cjs',
             bundle['profile_spec_path'], bundle['inventory_path']]
    names += ['browser/' + name for name in ('layout-codec.js', 'layout-runtime.js', 'layout-worker.js', 'contracts.js', 'dependencies.js')]
    inputs = {str((HERE / name).relative_to(PROJECT_ROOT)): digest((HERE / name).read_bytes()) for name in names}
    for path in (HERE.parent / 'paths.py', HERE.parent / 'book/source_codec.py', HERE.parent / 'check_links.py'):
        inputs[str(path.relative_to(PROJECT_ROOT))] = digest(path.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.catalog-runtime-stage-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'runtime'; stage.mkdir()
        (stage / marker).write_text('Platydoc validated offline catalog runtime\n')
        (stage / 'assets').mkdir()
        for name, raw in generated_files.items():
            path = stage / 'generated-syscalls' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for name, raw in mig_files.items():
            path = stage / 'generated-mig' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        for name, raw in ubc_files.items():
            path = stage / 'ubc-inputs' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if ubc is not None:
            write_json(stage / 'ubc-inputs/provenance.json', ubc)
        shutil.copytree(args.notices, stage / 'licenses')
        if mig_files:
            (stage / 'licenses/MIG-APPLE_LICENSE.txt').write_bytes(mig_files['MIG-APPLE_LICENSE.txt'])
        if ubc is not None:
            (stage / 'licenses/TrustCache-APPLE_LICENSE.txt').write_bytes(ubc_files['TRUSTCACHE-APPLE_LICENSE.txt'])
        for path, name in ((SOURCE_ROOT / 'APPLE_LICENSE', 'XNU-APPLE_LICENSE.txt'),
                           (PROJECT_ROOT / 'LICENSE', 'Platydoc-GPL-2.0-only.txt'),
                           (PROJECT_ROOT / 'LICENSE-DOCS', 'Platydoc-CC-BY-4.0.txt')):
            shutil.copyfile(path, stage / 'licenses' / name)
        for name in ('layout-codec.js', 'layout-runtime.js', 'contracts.js', 'dependencies.js'):
            shutil.copyfile(HERE / 'browser' / name, stage / name)
        assets = {'factory': asset(stage, 'factory', factory), 'wasm': asset(stage, 'wasm', wasm)}
        for key, name in [('contracts', 'contracts.js'), ('dependencies', 'dependencies.js'), ('worker', 'layout-worker.js')]:
            assets[key] = asset(stage, key, (HERE / 'browser' / name).read_bytes())
        profiles = []
        for name, request in cases:
            if name in bundle['profiles']:
                profile = bundle['profiles'][name]
                profiles.append({'id': name, 'label': profile['label'], 'source': source,
                                 'base_profile': profile['base_profile'], 'family': profile['family'],
                                 'component': profile['component'], 'platform': 'iPhoneOS',
                                 'asset': asset(stage, 'profile-' + name, json_bytes({'request': request, 'source': source}))})
        runtime = {'contract': 'platydoc.layout-runtime-manifest', 'version': 1,
                   'compiler': {**compiler, 'wasm_sha256': digest(wasm), 'factory_sha256': digest(factory)},
                   'assets': assets, 'profiles': profiles}
        # The runtime identity schema uses just these compiler fields.
        runtime['compiler'] = {key: runtime['compiler'][key] for key in ('revision', 'engine_sha256', 'wasm_sha256', 'factory_sha256')}
        write_json(stage / 'runtime-manifest.json', runtime)
        (stage / 'runtime-manifest.js').write_bytes(b'// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutRuntimeManifest=' + encoded(runtime) + b';\n')
        for name, raw in [('toolchain-provenance.json', provenance_raw), ('bundle-manifest.json', bundle_raw),
                          ('config-provenance.json', config_raw), ('coverage.json', coverage_raw),
                          ('profile-spec.json', spec_raw), ('structure-inventory.json', inventory_raw)]:
            (stage / name).write_bytes(raw)
        write_json(stage / 'coverage-evidence.json', {'contract': 'platydoc.layout-coverage-evidence', 'version': 1,
                   'comparison': report, 'surveys': surveys})
        write_json(stage / 'runtime-provenance.json', {'kind': 'platydoc-layout-runtime-provenance', 'version': 1,
                   'compiler_provenance_sha256': digest(provenance_raw), 'inputs': inputs,
                   'note': 'Exact compiler/header contexts and full native/Wasm responses validated before packaging.'})
        write_json(stage / 'native-validation.json', {'kind': 'native-wasm-validation-reference', 'status': 'passed',
                   'comparison_sha256': digest(report_raw), 'requests_sha256': report['requests_sha256'],
                   'native_sha256': native_sha, 'wasm_sha256': digest(wasm), 'coverage_sha256': digest(coverage_raw),
                   'cases': [{'name': name, 'status': result['status'], **report['case_evidence'][name]}
                             for name, result in zip(report['cases'], report['results'], strict=True)],
                   'note': 'Full comparison and trace evidence remain in the build workspace; reader startup runs no validation matrix.'})
        validate_coverage_package(stage, runtime, bundle)
        manifest = {'kind': 'milestone-8-offline-structure-catalog-runtime', 'source': source, 'scope': bundle['scope'],
                    'runtime_manifest_sha256': digest((stage / 'runtime-manifest.json').read_bytes()), 'wasm_bytes': len(wasm),
                    'compiler_provenance_sha256': digest(provenance_raw),
                    'runtime_provenance_sha256': digest((stage / 'runtime-provenance.json').read_bytes()), 'files': {}}
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                raw = path.read_bytes()
                manifest['files'][path.relative_to(stage).as_posix()] = {'bytes': len(raw), 'sha256': digest(raw)}
        manifest['total_bytes'] = sum(entry['bytes'] for entry in manifest['files'].values())
        write_json(stage / 'manifest.json', manifest)
        for name, sha in inputs.items():
            checked(PROJECT_ROOT, name, sha)
        for name, sha in provenance['notices'].items():
            if digest((stage / 'licenses' / name).read_bytes()) != sha:
                raise ValueError('Notice changed while copying')
        for source_path, name in ((SOURCE_ROOT / 'APPLE_LICENSE', 'XNU-APPLE_LICENSE.txt'),
                                 (PROJECT_ROOT / 'LICENSE', 'Platydoc-GPL-2.0-only.txt'),
                                 (PROJECT_ROOT / 'LICENSE-DOCS', 'Platydoc-CC-BY-4.0.txt')):
            if digest((stage / 'licenses' / name).read_bytes()) != consumed[source_path.resolve()]:
                raise ValueError('Project/source license changed while copying')
        for path, sha in consumed.items():
            if digest(path.read_bytes()) != sha:
                raise ValueError('Input changed during packaging: ' + str(path))
        if source_inventory(SOURCE_ROOT) != snapshot:
            raise ValueError('Source inventory changed during packaging')
        previous = Path(temporary) / 'previous'
        if output.exists(): output.rename(previous)
        try: stage.rename(output)
        except BaseException:
            if previous.exists(): previous.rename(output)
            raise
    print(f'Offline catalog runtime: {output} ({len(profiles)} contexts, {manifest["total_bytes"]:,} bytes)')


if __name__ == '__main__':
    main()
