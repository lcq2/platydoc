# SPDX-License-Identifier: GPL-2.0-only
"""Narrow, explicitly non-ABI CoreEntitlements aid plus original OSS TrustCache."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
TC_COMMIT = 'aca3beaa3dfbd42498b42c5e5ce20a938e6554e5'
TC_HEADERS = ('API.h', 'RawTypes.h', 'Return.h', 'Types.h', 'TypesConfig.h')
COMPAT_HEADERS = ('CoreEntitlements/V2/API.h', 'CoreEntitlements/V2/Kernel.h')
ROOTS = ['ubc_info', 'cs_blob']
TOKENS = re.compile(r'\b(?:PlatydocUnavailableCEContext|PlatydocOpaqueCEKernelAPI|CEContext_t|CEKernelAPI_t)\b')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(root, name, digest=None):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Unsafe/missing UBC dependency input: ' + name)
    raw = path.read_bytes()
    if digest is not None and sha(raw) != digest:
        raise ValueError('UBC dependency input changed: ' + name)
    return raw


def validate_manifest(manifest, spec):
    selected = spec['ubc_layout_inputs']
    tc = manifest['trustcache']
    if (manifest.get('contract'), manifest.get('version')) != ('platydoc.ubc-layout-inputs', 1):
        raise ValueError('Unsupported UBC dependency provenance')
    if (sha(manifest['trustcache_source_json'].encode()) != selected['trustcache_provenance_sha256'] or
            json.loads(manifest['trustcache_source_json']) != tc):
        raise ValueError('TrustCache provenance differs from reviewed source')
    if tc['commit'] != TC_COMMIT or tc['repository'] != 'https://github.com/apple-oss-distributions/xnu' or set(tc['files']) != {*TC_HEADERS, 'APPLE_LICENSE'}:
        raise ValueError('Unexpected TrustCache source/header set')
    expected = {'TrustCache/' + name: {'kind': 'external-header', 'source_path': tc['files'][name]['source_path'], 'sha256': tc['files'][name]['sha256']} for name in TC_HEADERS}
    for name in COMPAT_HEADERS:
        expected[name] = {'kind': 'layout-compatibility', 'source_path': 'docs-ai/tools/layouts/compatibility/' + name, 'sha256': selected['compatibility_sha256'][name]}
    if manifest['files'] != expected or manifest['license_sha256'] != tc['files']['APPLE_LICENSE']['sha256']:
        raise ValueError('UBC header identities differ from authored provider contract')


def load(spec):
    selected = spec.get('ubc_layout_inputs')
    if selected is None: return None, {}, None
    if (selected['directory'], selected['includes']) != ('.docs-cache/layouts/trustcache-source', ['sys/ubc_internal.h']):
        raise ValueError('Unsupported UBC dependency context')
    root = PROJECT / selected['directory']
    tc_raw = checked(root, 'source.json', selected['trustcache_provenance_sha256'])
    tc = json.loads(tc_raw)
    files, origins = {}, {}
    for name in TC_HEADERS:
        relative = 'TrustCache/' + name
        files[relative] = checked(root, name, tc['files'][name]['sha256'])
        origins[relative] = {'kind': 'external-header', 'source_path': tc['files'][name]['source_path'], 'sha256': sha(files[relative])}
    for name in COMPAT_HEADERS:
        files[name] = checked(HERE / 'compatibility', name, selected['compatibility_sha256'][name])
        origins[name] = {'kind': 'layout-compatibility', 'source_path': 'docs-ai/tools/layouts/compatibility/' + name, 'sha256': sha(files[name])}
    files['TRUSTCACHE-APPLE_LICENSE.txt'] = checked(root, 'APPLE_LICENSE', tc['files']['APPLE_LICENSE']['sha256'])
    manifest = {'contract': 'platydoc.ubc-layout-inputs', 'version': 1, 'trustcache': tc, 'trustcache_source_json': tc_raw.decode(), 'files': origins,
                'license_sha256': sha(files['TRUSTCACHE-APPLE_LICENSE.txt']),
                'limitation': 'CE stand-ins have no real ABI; only original ubc_info/cs_blob and unaffected returned closure may be exposed.'}
    validate_manifest(manifest, spec)
    return manifest, files, root


def guard(request, result=None):
    if not any(name.startswith('/inputs/layout-compat/') for name in request['files']): return
    query = re.compile(r'\b(?:sizeof|_Alignof|__alignof|__alignof__|alignof|typeof|__typeof|__typeof__|offsetof|__builtin_offsetof)\b')
    if request.get('records') != ROOTS or any(TOKENS.search(v or '') or query.search(v or '') for v in request.get('macros', {}).values()):
        raise ValueError('Layout-only CE context permits only ubc_info/cs_blob and forbids stand-in-dependent requests')
    if result is not None and result['status'] == 'ok':
        text = json.dumps({'records': result['records'], 'declarations': result['declarations']})
        if TOKENS.search(text) or '/inputs/layout-compat/' in text or 'layout-compatibility/' in text:
            raise ValueError('Layout-only CE stand-in-dependent output cannot be published')
