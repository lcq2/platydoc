#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build pinned cross-platform Apple MIG and generate local profile headers.

Download the pinned source archive separately; this command never downloads
binaries or source. Host compatibility headers compile migcom only and are never
added to the kernel layout input universe. XNU remains read-only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS, require_source
sys.path.insert(0, str(HERE))
from bundle_xnu import exports
from layout_exports import exported_headers

COMMIT = 'f337e600741638896fb6056ce87c6479f74b89a3'
ARCHIVE_SHA256 = 'aba7ae76ecfc18e895f6f40c39d2b0bdd330aa535bb8bf9703d08b13772be6d0'
URL = 'https://github.com/markmentovai/bootstrap_cmds/archive/' + COMMIT + '.tar.gz'
HEADERS = ('host_priv', 'thread_act', 'upl', 'vm_map')
MARKER = '.layout-generated-mig'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_output(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Output must not traverse symlinks')
    path = path.resolve()
    for protected in (SOURCE_ROOT, DOCS, PROJECT_ROOT / '.git'):
        if path == protected or path in protected.parents or protected in path.parents:
            raise ValueError('Generated output must remain outside source/documentation trees')
    return path


def run(argv, cwd=None, data=None):
    result = subprocess.run([str(a) for a in argv], cwd=cwd, input=data,
                            capture_output=True, timeout=180, check=False)
    if result.returncode:
        raise RuntimeError('Command failed: ' + str(argv[0]) + '\n' + result.stderr.decode(errors='replace'))
    return result


def build_tool(archive, tools):
    if sha(archive) != ARCHIVE_SHA256:
        raise ValueError('MIG source archive does not match pinned SHA-256')
    tools = safe_output(tools)
    source = tools / ('bootstrap_cmds-' + COMMIT)
    binary = source / 'migcom.tproj/migcom'
    identity = tools / 'build.json'
    recipe = {'commit': COMMIT, 'archive_sha256': ARCHIVE_SHA256,
              'recipe': ['autoreconf --install', 'sh configure', 'make -j4']}
    if binary.is_file() and identity.is_file():
        saved = json.loads(identity.read_bytes())
        if all(saved.get(k) == v for k, v in recipe.items()) and saved.get('binary_sha256') == sha(binary):
            return binary, saved
        raise ValueError('Cached MIG build identity changed; choose a fresh tools directory')
    if tools.exists() and any(tools.iterdir()):
        raise ValueError('Refusing to overwrite a nonempty unverified MIG tools directory')
    tools.mkdir(parents=True, exist_ok=True)
    # Only regular files/directories under the pinned archive root are admitted.
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar.getmembers():
            name = Path(member.name)
            if (name.is_absolute() or '..' in name.parts or not name.parts or
                    name.parts[0] != source.name or not (member.isfile() or member.isdir())):
                raise ValueError('Unexpected MIG source archive member')
        tar.extractall(tools)
    host = {}
    for name in ('autoreconf', 'sh', 'make', 'gcc', 'flex', 'bison'):
        found = shutil.which(name)
        if not found: raise RuntimeError('Missing installed host tool: ' + name)
        host[name] = {'path': str(Path(found).resolve()), 'sha256': sha(Path(found).resolve())}
    for command in ([host['autoreconf']['path'], '--install'], [host['sh']['path'], 'configure'],
                    [host['make']['path'], '-j4']):
        run(command, cwd=source)
    recipe.update(binary_sha256=sha(binary), host_tools=host,
                  licenses={str(p.relative_to(source)): sha(p) for p in [source / 'APPLE_LICENSE']})
    identity.write_text(json.dumps(recipe, indent=2) + '\n')
    return binary, recipe


def validate_manifest(manifest, spec, spec_sha, config_sha, source_inputs, generator_sha):
    """Validate provenance offline; no host generator or compiler is required."""
    expected_source = {'repository': 'https://github.com/markmentovai/bootstrap_cmds',
                       'commit': COMMIT, 'archive_url': URL, 'archive_sha256': ARCHIVE_SHA256}
    if (manifest.get('contract'), manifest.get('version')) != ('platydoc.generated-mig', 1):
        raise ValueError('Unsupported MIG generation provenance')
    if (manifest.get('source_commit') != spec['source_commit'] or
            manifest.get('generator_sha256') != generator_sha or
            manifest.get('spec_sha256') != spec_sha or
            manifest.get('config_provenance_sha256') != config_sha or
            manifest.get('tool_source') != expected_source or
            manifest.get('license_sha256') != '212846e0145aa50fb3a5aef254a370311a93acf6c1e792e47e0068d64c8c3885'):
        raise ValueError('MIG recipe/source/spec/config identity changed')
    tool = manifest.get('tool', {})
    if tool.get('commit') != COMMIT or tool.get('archive_sha256') != ARCHIVE_SHA256:
        raise ValueError('MIG tool source identity changed')
    inputs = manifest.get('source_inputs', {})
    required = {'osfmk/mach/Makefile', 'makedefs/MakeInc.def'} | {'osfmk/mach/' + name + '.defs' for name in HEADERS}
    if not required.issubset(inputs) or any(source_inputs.get(name) != value for name, value in inputs.items()):
        raise ValueError('MIG source/preprocessor inputs changed')
    profiles = manifest.get('profiles', {})
    if len(profiles) != 4 or set(profiles) != set(spec['configurations']):
        raise ValueError('Unexpected MIG profile set')
    import re
    for base, profile in profiles.items():
        board = profile.get('board')
        matches = [(soc, value) for soc, value in spec['boards'].items() if base.endswith('-' + soc)]
        if len(matches) != 1 or board != matches[0][1]:
            raise ValueError('MIG board does not match profile')
        if board not in spec['boards'].values() or profile.get('directory') != 'profiles/' + base:
            raise ValueError('Invalid MIG profile path/board')
        files = profile.get('files', {})
        if set(files) != {'mach/' + name + '.h' for name in HEADERS} or any(
                not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value) for value in files.values()):
            raise ValueError('Invalid MIG generated header identities')
        macros = profile.get('macros', {})
        expected = {**spec['base_macros'], board['board_macro']: '1', 'CURRENT_MACHINE_CONFIG_LC': matches[0][0]}
        if any(macros.get(name, object()) != value for name, value in expected.items()):
            raise ValueError('MIG base macro identity changed')
        if len(profile.get('commands', [])) != len(HEADERS) or [c.get('interface') for c in profile['commands']] != list(HEADERS):
            raise ValueError('MIG command provenance missing')


def load(spec, configs):
    selected = spec.get('generated_mig')
    if selected is None: return None, None
    if selected != {'directory': '.docs-cache/layouts/generated-mig', 'includes': ['vm/bsd_vm.c']}:
        raise ValueError('Unsupported generated MIG context')
    root = safe_output(PROJECT_ROOT / selected['directory'])
    manifest = json.loads((root / 'generation.json').read_bytes())
    spec_path = HERE / 'profiles/ios-catalog.json'
    if json.loads(spec_path.read_bytes()) != spec:
        raise ValueError('MIG profile spec differs from selected local recipe')
    config_path = Path(configs) / 'config-provenance.json'
    config = json.loads(config_path.read_bytes())
    if any(Path(name).is_absolute() or '..' in Path(name).parts for name in manifest['source_inputs']):
        raise ValueError('Invalid MIG source input path')
    source_inputs = {name: sha(SOURCE_ROOT / name) for name in manifest['source_inputs']}
    validate_manifest(manifest, spec, sha(spec_path), sha(config_path), source_inputs, sha(Path(__file__)))
    for base, profile in manifest['profiles'].items():
        source = config['profiles'][base]
        board = spec['boards'][source['soc']]
        macros = {**source['macros'], **spec['base_macros'], board['board_macro']: '1',
                  'CURRENT_MACHINE_CONFIG_LC': source['soc']}
        if profile['macros'] != macros or profile['board'] != board:
            raise ValueError('Generated MIG configuration macros changed')
        for name, digest in profile['files'].items():
            path = root / profile['directory'] / name
            if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or sha(path) != digest:
                raise ValueError('Generated MIG header changed: ' + name)
    license_path = root / 'MIG-APPLE_LICENSE.txt'
    if license_path.is_symlink() or sha(license_path) != manifest['license_sha256']:
        raise ValueError('MIG license notice changed')
    return root, manifest


def generate(spec_path, configs, archive, tools, output):
    require_source()
    spec = json.loads(spec_path.read_bytes())
    config = json.loads((configs / 'config-provenance.json').read_bytes())
    if config['source_commit'] != spec['source_commit']:
        raise ValueError('Configuration source revision mismatch')
    actual = run(['git', '-C', SOURCE_ROOT, 'rev-parse', 'HEAD']).stdout.decode().strip()
    if actual != spec['source_commit']: raise ValueError('Wrong selected XNU revision')
    binary, tool = build_tool(archive, tools)
    clang = Path(shutil.which('clang') or '')
    if not clang.is_file(): raise RuntimeError('Missing installed clang preprocessor')
    output = safe_output(output)
    if output.exists() and (not (output / MARKER).is_file() or any(p.is_symlink() for p in output.rglob('*'))):
        raise ValueError('Refusing unmarked or symlink-containing MIG output')
    output.parent.mkdir(parents=True, exist_ok=True)
    source_inputs = {name: sha(SOURCE_ROOT / name) for name in
                     ('osfmk/mach/Makefile', 'makedefs/MakeInc.def')}
    manifest = {'contract': 'platydoc.generated-mig', 'version': 1,
                'generator_sha256': sha(Path(__file__)), 'spec_sha256': sha(spec_path),
                'config_provenance_sha256': sha(configs / 'config-provenance.json'),
                'source_commit': actual, 'tool': tool,
                'tool_source': {'repository': 'https://github.com/markmentovai/bootstrap_cmds',
                                'commit': COMMIT, 'archive_url': URL, 'archive_sha256': ARCHIVE_SHA256},
                'preprocessor': {'path': str(clang.resolve()), 'sha256': sha(clang.resolve())},
                'source_inputs': source_inputs, 'profiles': {}}
    with tempfile.TemporaryDirectory(prefix='.mig-stage-', dir=output.parent) as temporary:
        stage = Path(temporary)
        license_source = binary.parent.parent / 'APPLE_LICENSE'
        (stage / 'MIG-APPLE_LICENSE.txt').write_bytes(license_source.read_bytes())
        manifest['license_sha256'] = sha(license_source)
        aliases = {**exports(spec), **exported_headers(SOURCE_ROOT, spec['additional_exports'])}
        export_root = stage / 'exports'
        for virtual, (path, makefile) in aliases.items():
            dest = export_root / virtual.removeprefix('/inputs/exports/')
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(path.read_bytes())
            source_inputs[path.relative_to(SOURCE_ROOT).as_posix()] = sha(path)
            recipe_path = SOURCE_ROOT / makefile
            if recipe_path.is_file(): source_inputs[recipe_path.relative_to(SOURCE_ROOT).as_posix()] = sha(recipe_path)
        for base in spec['configurations']:
            selected = config['profiles'][base]
            if selected['platform'] != spec['platform']: raise ValueError('Configuration platform mismatch')
            cfg = configs / selected['directory']
            for name, digest in selected['files'].items():
                if sha(cfg / name) != digest: raise ValueError('Changed configuration file: ' + name)
            board = spec['boards'][selected['soc']]
            macros = {**selected['macros'], **spec['base_macros'], board['board_macro']: '1',
                      'CURRENT_MACHINE_CONFIG_LC': selected['soc']}
            cpp = [str(clang), '-E', '-x', 'c', '-target', spec['target'], '-nostdinc',
                   '-std=' + spec['language'], '-ffreestanding']
            if spec['blocks']: cpp += ['-fblocks']
            if spec['kernel_mode']:
                cpp += ['-fno-builtin', '-fgnuc-version=4.2.1', '-fmax-type-align=16']
            if spec['ptrauth_intrinsics']: cpp += ['-fptrauth-intrinsics']
            if spec['ptrauth_calls']: cpp += ['-fptrauth-calls']
            for feature in board['target_features']:
                cpp += ['-Xclang', '-target-feature', '-Xclang', feature]
            if 'target_cpu' in board: cpp += ['-mcpu=' + board['target_cpu']]
            if 'target_arch' in board: cpp += ['-march=' + board['target_arch']]
            for virtual in spec['include_dirs']:
                if virtual.startswith('/inputs/generated/'): path = cfg
                elif virtual.startswith('/inputs/xnu/'): path = SOURCE_ROOT / virtual.removeprefix('/inputs/xnu/')
                elif virtual.startswith('/inputs/exports/'): path = export_root / virtual.removeprefix('/inputs/exports/')
                elif virtual == '/inputs/clang-resource/': continue # .defs use no compiler resource headers
                else: raise ValueError('Unexpected profile include directory')
                cpp += ['-I' + str(path)]
            cpp += [('-U' + k) if v is None else ('-D' + k + '=' + v) for k, v in macros.items()]
            cpp += ['-D__MIG__=1']
            for forced in spec['forced_includes']:
                if not forced.startswith('/inputs/generated/'):
                    raise ValueError('Unexpected forced include in MIG profile')
                cpp += ['-include', str(cfg / forced.removeprefix('/inputs/generated/'))]
            generated = stage / 'profiles' / base
            (generated / 'mach').mkdir(parents=True)
            records = {}
            commands = []
            for name in HEADERS:
                mode = ['-DKERNEL_USER=1', '-DEXC_SERVER_AUDITTOKEN=1', '-DMACH_EXC_SERVER_AUDITTOKEN=1'] if name in ('upl', 'vm_map') else []
                defs = SOURCE_ROOT / ('osfmk/mach/' + name + '.defs')
                dependency = generated / (name + '.d')
                command = cpp + mode + ['-MD', '-MF', str(dependency), '-MT', name, str(defs)]
                preprocessed = run(command).stdout
                (generated / (name + '.preprocessed.defs')).write_bytes(preprocessed)
                header = generated / ('mach/' + name + '.h')
                migflags = ['-novouchers'] + (['-maxonstack', '1024'] if mode else [])
                migcommand = [str(binary), *migflags, '-server', '/dev/null', '-user', '/dev/null', '-header', str(header)]
                run(migcommand, data=preprocessed)
                commands.append({'interface': name, 'cpp_argv': command, 'mig_argv': migcommand,
                                 'preprocessed_sha256': hashlib.sha256(preprocessed).hexdigest()})
                # Hash every actual source preprocessor input, in addition to recipe Makefiles.
                dependencies = dependency.read_text().replace('\\\n', '').split(':', 1)[1].split()
                for raw in dependencies:
                    path = Path(raw)
                    if path.is_relative_to(SOURCE_ROOT): source_inputs[path.relative_to(SOURCE_ROOT).as_posix()] = sha(path)
                records['mach/' + name + '.h'] = sha(header)
            manifest['profiles'][base] = {'directory': 'profiles/' + base, 'files': records,
                                          'macros': macros, 'board': board, 'commands': commands}
        (stage / MARKER).write_text('Local generated MIG headers; see generation.json\n')
        (stage / 'generation.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        # Output is explicitly marked derived data; staging succeeded before replacement.
        if output.exists(): shutil.rmtree(output)
        shutil.move(str(stage), str(output))
    print('Generated genuine MIG headers for ' + str(len(manifest['profiles'])) + ' profiles: ' + str(output))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', type=Path, default=HERE / 'profiles/ios-catalog.json')
    p.add_argument('--configs', type=Path, default=PROJECT_ROOT / '.docs-cache/layouts/milestone8-configs')
    p.add_argument('--archive', type=Path, default=PROJECT_ROOT / '.docs-cache/layouts/mig-tools/port.tar.gz')
    p.add_argument('--tools', type=Path, default=PROJECT_ROOT / '.docs-cache/layouts/mig-tools/pinned-build')
    p.add_argument('--output', type=Path, default=PROJECT_ROOT / '.docs-cache/layouts/generated-mig')
    args = p.parse_args()
    generate(args.spec.resolve(), args.configs.resolve(), args.archive.resolve(), args.tools, args.output)


if __name__ == '__main__': main()
