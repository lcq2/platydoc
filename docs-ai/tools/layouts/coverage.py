# SPDX-License-Identifier: GPL-2.0-only
"""Validate the finite documented structure/profile survey and its evidence."""
import hashlib
import json
import re
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(value, inventory, manifest, root=None):
    expected_keys = {'contract', 'version', 'source', 'platform', 'target', 'base_profiles', 'inventory_sha256', 'scope', 'entries'}
    if set(value) != expected_keys or value['contract'] != 'platydoc.layout-coverage' or value['version'] != 1:
        raise ValueError('Unsupported finite layout coverage schema')
    if value['source'] != inventory['source'] or value['platform'] != inventory['platform'] or value['scope'] != inventory['scope']:
        raise ValueError('Survey source/platform/scope differs from authored inventory')
    if value['target'] != manifest['target'] or value['base_profiles'] != manifest['base_profiles'] or len(set(value['base_profiles'])) != len(value['base_profiles']):
        raise ValueError('Survey target/profile matrix differs from bundle')
    if value['inventory_sha256'] != manifest['inventory_sha256'] or not re.fullmatch('[a-f0-9]{64}', value['inventory_sha256']):
        raise ValueError('Survey inventory identity differs')
    authored = {entry['key']: entry for entry in inventory['entries']}
    if len(authored) != len(inventory['entries']) or len(value['entries']) != len(authored):
        raise ValueError('Survey inventory membership differs')
    seen = set()
    for entry in value['entries']:
        key = entry.get('key')
        if key not in authored or key in seen or set(entry) != set(authored[key]) | {'profiles'}:
            raise ValueError('Unknown/duplicate surveyed structure')
        seen.add(key)
        if {name: item for name, item in entry.items() if name != 'profiles'} != authored[key]:
            raise ValueError('Survey source/declaration/chapter metadata differs')
        if set(entry['profiles']) != set(value['base_profiles']):
            raise ValueError('Survey must cover every declared base profile')
        for base, cell in entry['profiles'].items():
            if set(cell) != {'status', 'transport_status', 'reason', 'diagnostics', 'context_id', 'declaration_id', 'directory', 'request_sha256', 'native_result_sha256', 'full_input_equivalence'}:
                raise ValueError('Invalid survey cell schema')
            if cell['full_input_equivalence'] != 'passed' or any(not isinstance(cell[name], str) or not re.fullmatch('[a-f0-9]{64}', cell[name]) for name in ('request_sha256', 'native_result_sha256')):
                raise ValueError('Survey cell lacks complete equivalence/hash evidence')
            if not isinstance(cell['diagnostics'], list):
                raise ValueError('Invalid survey diagnostics')
            if cell['status'] == 'supported':
                if cell['transport_status'] != 'ok' or cell['reason'] is not None or cell['diagnostics'] or not isinstance(cell['declaration_id'], str) or not re.fullmatch('decl-v1:[a-f0-9]{64}', cell['declaration_id']):
                    raise ValueError('Supported survey cell has incomplete/failed evidence')
                context = manifest['profiles'].get(cell['context_id'])
                if not context or context['base_profile'] != base or entry['record'] not in context['records']:
                    raise ValueError('Supported cell references an unrelated runtime context')
            else:
                taxonomy = {'unsupported-layout': ('unsupported', 'engine-source-identity'), 'unavailable-type': ('unavailable', 'definition-not-in-header-context'),
                            'invalid-request': ('invalid-configuration', 'invalid-request')}
                if cell['transport_status'] == 'error':
                    missing = any('file not found' in diagnostic.get('message', '') for diagnostic in cell['diagnostics'])
                    expected = ('unavailable', 'missing-header') if missing else ('compilation-error', 'compiler-error')
                elif cell['transport_status'] == 'ok':
                    expected = ('unsupported', 'compiler-diagnostics')
                else:
                    expected = taxonomy.get(cell['transport_status'])
                if expected != (cell['status'], cell['reason']) or cell['context_id'] is not None or cell['declaration_id'] is not None or not cell['diagnostics']:
                    raise ValueError('Unsupported cell invents a layout or mislabels its boundary')
            directory = Path(cell['directory'])
            if directory.is_absolute() or '..' in directory.parts or directory.parts != ('survey', base + '--' + key):
                raise ValueError('Invalid survey evidence directory')
            if root is not None:
                source = root / directory
                for filename, identity in [('request.json', 'request_sha256'), ('native.json', 'native_result_sha256')]:
                    path = source / filename
                    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or digest(path.read_bytes()) != cell[identity]:
                        raise ValueError('Survey evidence changed: ' + key)
                result = json.loads((source / 'native.json').read_bytes())
                if result['status'] != cell['transport_status'] or result['diagnostics'] != cell['diagnostics']:
                    raise ValueError('Survey diagnostic/status evidence mismatch')
                if cell['status'] == 'supported':
                    context_result = json.loads((root / manifest['profiles'][cell['context_id']]['directory'] / 'native.json').read_bytes())
                    matches = [declaration for declaration in context_result['declarations'] if declaration['id'] == cell['declaration_id'] and declaration['name'] == entry['record']]
                    if len(matches) != 1:
                        raise ValueError('Survey declaration is missing from its runtime context')
                    point = matches[0]['source']['spelling']
                    candidate = {'source_path': point['source_path'], 'source_sha256': point['sha256'], 'offset_bytes': point['offset_bytes'], 'kind': matches[0]['kind']}
                    if candidate not in entry['source_candidates']:
                        raise ValueError('Survey declaration does not match authored physical source')
                elif result['status'] != 'ok' and result['records']:
                    raise ValueError('Unsupported survey result contains layouts')
    return {'structures': len(seen), 'profiles': len(value['base_profiles']), 'cells': len(seen) * len(value['base_profiles']),
            'supported': sum(cell['status'] == 'supported' for entry in value['entries'] for cell in entry['profiles'].values())}
