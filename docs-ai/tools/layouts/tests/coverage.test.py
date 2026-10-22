#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Finite survey schema and source-export guards, without compiler execution."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coverage as C
import catalog
from layout_exports import exported_headers


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.entry = {'key': 'Root', 'record': 'Root', 'group': 'test', 'component': 'osfmk',
                      'headers': ['root.h'], 'source_candidates': [{'source_path': 'xnu/root.h', 'source_sha256': 'a' * 64, 'offset_bytes': 7, 'kind': 'struct'}],
                      'chapters': ['structures/root.md#root']}
        self.inventory = {'source': {'release': 'test', 'revision': 'test'}, 'platform': 'iPhoneOS', 'scope': 'finite test roots', 'entries': [self.entry]}
        self.manifest = {'target': 'arm64e-apple-ios', 'base_profiles': ['release'], 'inventory_sha256': 'b' * 64,
                         'profiles': {'release--kernel': {'base_profile': 'release', 'records': ['Root']}}}
        self.cell = {'status': 'supported', 'transport_status': 'ok', 'reason': None, 'diagnostics': [],
                     'context_id': 'release--kernel', 'declaration_id': 'decl-v1:' + 'c' * 64, 'directory': 'survey/release--Root',
                     'request_sha256': 'd' * 64, 'native_result_sha256': 'e' * 64, 'full_input_equivalence': 'passed'}
        self.value = {'contract': 'platydoc.layout-coverage', 'version': 1, 'source': self.inventory['source'],
                      'platform': 'iPhoneOS', 'target': 'arm64e-apple-ios', 'base_profiles': ['release'],
                      'inventory_sha256': 'b' * 64, 'scope': self.inventory['scope'],
                      'entries': [{**self.entry, 'profiles': {'release': self.cell}}]}

    def validate(self, value=None):
        return C.validate(value or self.value, self.inventory, self.manifest)

    def test_finite_success(self):
        self.assertEqual(self.validate(), {'structures': 1, 'profiles': 1, 'cells': 1, 'supported': 1})

    def test_missing_duplicate_or_extra_cells_fail(self):
        for mutate in (lambda v: v['entries'].clear(), lambda v: v['entries'].append(copy.deepcopy(v['entries'][0])),
                       lambda v: v['entries'][0]['profiles'].clear(), lambda v: v.update(complete=True),
                       lambda v: v['entries'][0]['profiles']['release'].update(context_id='release--unrelated')):
            value = copy.deepcopy(self.value); mutate(value)
            with self.assertRaises(ValueError): self.validate(value)

    def test_supported_cannot_hide_warning_or_unknown_layout(self):
        for change in ({'diagnostics': [{'message': 'warning'}]}, {'declaration_id': None}, {'reason': 'guess'}, {'transport_status': 'error'}):
            value = copy.deepcopy(self.value); value['entries'][0]['profiles']['release'].update(change)
            with self.assertRaises(ValueError): self.validate(value)

    def test_unavailable_preserves_precise_diagnostics(self):
        self.cell.update(status='unavailable', transport_status='error', reason='missing-header', context_id=None,
                         declaration_id=None, diagnostics=[{'message': "'external.h' file not found"}])
        self.assertEqual(self.validate()['supported'], 0)
        self.cell['reason'] = 'compiler-error'
        with self.assertRaises(ValueError): self.validate()

    def test_warning_only_evidence_never_advertises_layout(self):
        self.cell.update(status='unsupported', transport_status='ok', reason='compiler-diagnostics', context_id=None,
                         declaration_id=None, diagnostics=[{'message': 'warning'}])
        self.assertEqual(self.validate()['supported'], 0)
        self.cell['declaration_id'] = 'decl-v1:' + 'c' * 64
        with self.assertRaises(ValueError): self.validate()

    def test_export_expansion_and_unsupported_rules(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); (root / 'one.h').write_text('/* exact original bytes */\n')
            makefile = root / 'Makefile'
            valid = 'HEADERS = one.h\nEXPORT_MI_LIST = ${HEADERS}\nEXPORT_MI_DIR = sys\n'
            makefile.write_text(valid)
            aliases = exported_headers(root, ['Makefile'])
            self.assertEqual(aliases['/inputs/exports/bsd/sys/one.h'][0].read_bytes(), (root / 'one.h').read_bytes())
            for extra in ('HEADERS += other.h\n', 'override HEADERS = other.h\n', '  ifdef FLAG\nendif\n', 'EXPORT_MI_LIST := one.h\n'):
                makefile.write_text(valid + extra)
                with self.subTest(extra=extra), self.assertRaises(ValueError): exported_headers(root, ['Makefile'])

    def test_catalog_selection_uses_physical_anchor_and_keeps_boundaries(self):
        point = {'source_path': 'xnu/root.h', 'sha256': 'a' * 64, 'offset_bytes': 7}
        declaration = {'id': self.cell['declaration_id'], 'kind': 'struct', 'source': {'spelling': point}}
        entries = [{'profile': 'release--kernel', 'document': {'declarations': {'entries': [declaration]}}}]
        mapping = {'entries': [{**self.entry['source_candidates'][0], 'display_name': 'Root', 'chapters': self.entry['chapters']}]}
        selected = catalog.selections_for(mapping, entries, self.value)
        self.assertEqual(selected[0]['declarations'], {'release--kernel': self.cell['declaration_id']})
        declaration['source']['spelling']['offset_bytes'] = 8
        with self.assertRaisesRegex(ValueError, 'physical source'): catalog.selections_for(mapping, entries, self.value)
        self.cell.update(status='unsupported', context_id=None, declaration_id=None)
        self.assertEqual(catalog.selections_for({'entries': []}, [], self.value)[0]['declarations'], {})

    def test_coverage_table_has_finite_cell_hooks(self):
        html = catalog.coverage_table(self.value)
        self.assertIn('data-coverage-root="Root" data-base-profile="release"', html)
        self.assertIn('layout-browser.html?declaration=Root', html)
        self.assertIn('Available', html)


if __name__ == '__main__': unittest.main()
