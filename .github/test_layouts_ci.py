#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""CI admission/cache/archive tests using only the standard library."""
import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import layouts_ci as C


class CITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='platydoc-ci-test-')
        self.root = Path(self.temporary.name)

    def tearDown(self): self.temporary.cleanup()

    def comparison(self):
        cases = [('first', {'target': 'test', 'main': '/inputs/a.c', 'files': {'/inputs/a.c': 'struct A {int x;};'}})]
        result = {'status': 'ok', 'records': [{'size_bytes': 4}]}
        compare = C.modules()[2]
        report = {'kind': 'xnu-catalog-contexts', 'version': 1, 'wasm_parity': 'passed', 'dependency_tracing': True,
                  'cases': ['first'], 'results': [result], 'case_evidence': {'first': {
                      'runtime_request_sha256': compare.result_hash(cases[0][1]), 'compact_result_sha256': compare.result_hash(result)}},
                  'requests_sha256': compare.requests_hash(cases), 'requests_hash_algorithm': 'length-prefixed-canonical-json-v1'}
        return report, cases

    def test_actual_request_result_rehash_and_case_membership(self):
        report, cases = self.comparison()
        self.assertEqual(C.result_rows(report, cases)[0]['status'], 'ok')
        changes = [lambda p: p['results'][0]['records'][0].update(size_bytes=8),
                   lambda p: p['case_evidence']['first'].update(runtime_request_sha256='0' * 64),
                   lambda p: p['cases'].append('extra'), lambda p: p['results'].append({}),
                   lambda p: p['case_evidence'].update(extra={})]
        for mutate in changes:
            bad = copy.deepcopy(report); mutate(bad)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): C.result_rows(bad, cases)
        altered = copy.deepcopy(cases); altered[0][1]['files']['/inputs/a.c'] += '\n'
        with self.assertRaises(ValueError): C.result_rows(report, altered)

    def test_rehashed_fresh_output_cannot_replace_reviewed_baseline(self):
        baseline = {'contract': 'platydoc.ci-layout-semantic-baseline', 'version': 1,
                    'reviewed_evidence': {'comparison_sha256': 'a' * 64, 'note': 'Reviewed local evidence'},
                    'semantics': {'cases': [{'name': 'first', 'compact_result_sha256': 'b' * 64}], 'inputs': {'engine': 'c' * 64}}}
        path = self.root / 'baseline.json'; C.write(path, baseline)
        with patch.object(C, 'semantic_material', return_value=copy.deepcopy(baseline['semantics'])):
            C.check_semantics(path, self.root, self.root)
        for key in ('cases', 'inputs'):
            changed = copy.deepcopy(baseline['semantics']); changed[key] = []
            with patch.object(C, 'semantic_material', return_value=changed), self.assertRaisesRegex(ValueError, 'Reviewed layout semantics changed'):
                C.check_semantics(path, self.root, self.root)

    def test_ci_cannot_author_its_own_baseline(self):
        with patch.dict(C.os.environ, {'GITHUB_ACTIONS': 'true'}), patch('sys.argv', ['layouts_ci.py', 'make-baseline', '--reviewed']), self.assertRaisesRegex(ValueError, 'cannot author'):
            C.main()

    def test_finite_matrix_membership_is_explicit_without_legacy_counts(self):
        coverage = {'base_profiles': ['release'], 'entries': [
            {'key': 'ipv6', 'profiles': {'release': {'status': 'supported', 'context_id': 'release--ipv6'}}},
            {'key': 'opaque', 'profiles': {'release': {'status': 'unavailable', 'context_id': None}}}]}
        bundle = {'profiles': {'release--ipv6': {}}, 'unsupported': {'release--unsupported--opaque': {}}}
        self.assertEqual(C.matrix_summary(bundle, coverage)['cells'], 2)
        for key in ('profiles', 'unsupported'):
            bad = copy.deepcopy(bundle); bad[key]['extra'] = {}
            with self.assertRaisesRegex(ValueError, 'membership'): C.matrix_summary(bad, coverage)
        bad = copy.deepcopy(coverage); bad['entries'][0]['profiles'] = {}
        with self.assertRaisesRegex(ValueError, 'Incomplete'): C.matrix_summary(bundle, bad)
        bad = copy.deepcopy(coverage); bad['entries'].append(copy.deepcopy(bad['entries'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): C.matrix_summary(bundle, bad)

    def compiler(self):
        folder = self.root / 'compiler'; folder.mkdir()
        artifacts = ['build-native/bin/layout-engine', 'build-wasm/bin/layout-engine.js', 'build-wasm/bin/layout-engine.wasm']
        for name in artifacts:
            path = folder / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'fixture bytes'); path.chmod(0o755)
        notices = folder / 'notices'; notices.mkdir(); (notices / 'license.txt').write_text('Original terms')
        provenance = {'pins': C.read(C.LAYOUTS / 'toolchain.lock.json'),
                      'inputs': {name: C.file_sha(C.LAYOUTS / name) for name in ('engine.cpp', 'CMakeLists.txt', 'toolchain.lock.json', 'build.py')},
                      'artifacts': {name: {'sha256': C.file_sha(folder / name)} for name in artifacts},
                      'notices': {'license.txt': C.file_sha(notices / 'license.txt')}}
        C.write(folder / 'toolchain-provenance.json', provenance)
        context = {'host': 'test'}
        C.write(folder / C.RECEIPT, {'contract': 'platydoc.ci-compiler-cache', 'version': 1, 'context': context, 'files': C.file_manifest(folder)})
        return folder, context

    def test_cache_checks_bytes_membership_context_and_notices(self):
        folder, context = self.compiler(); C.validate_compiler_cache(folder, context)
        with self.assertRaises(ValueError): C.validate_compiler_cache(folder, {'host': 'different'})
        path = folder / 'notices/license.txt'; old = path.read_bytes(); path.write_bytes(b'changed')
        with self.assertRaises(ValueError): C.validate_compiler_cache(folder, context)
        path.write_bytes(old); extra = folder / 'unexpected'; extra.write_bytes(b'extra')
        with self.assertRaises(ValueError): C.validate_compiler_cache(folder, context)
        extra.unlink(); (folder / 'bad-link').symlink_to(path)
        with self.assertRaises(ValueError): C.validate_compiler_cache(folder, context)

    def test_nested_receipt_name_is_not_hidden(self):
        folder, context = self.compiler(); path = folder / 'nested' / C.RECEIPT; path.parent.mkdir(); path.write_text('{}')
        with self.assertRaises(ValueError): C.validate_compiler_cache(folder, context)

    def archive(self, names):
        path = self.root / 'sdk.tar.gz'
        with tarfile.open(path, 'w:gz') as archive:
            for name, kind in names:
                member = tarfile.TarInfo(name)
                if kind == 'link': member.type = tarfile.SYMTYPE; member.linkname = '/tmp/outside'; archive.addfile(member)
                else:
                    raw = b'exact pinned source'; member.size = len(raw); member.mode = 0o644; archive.addfile(member, io.BytesIO(raw))
        return path

    def test_sdk_extraction_rejects_links_traversal_and_multiple_roots(self):
        cases = [[('../escape', 'file')], [('/absolute', 'file')], [('sdk/link', 'link')], [('one/a', 'file'), ('two/b', 'file')]]
        for index, names in enumerate(cases):
            with self.subTest(names=names), self.assertRaises(ValueError): C.extract_sdk(self.archive(names), self.root / ('out' + str(index)))
        good = self.root / 'good'; C.extract_sdk(self.archive([('sdk/emsdk.py', 'file')]), good)
        self.assertEqual((good / 'emsdk.py').read_bytes(), b'exact pinned source')

    def test_cached_archive_hash_checked_before_network_or_execution(self):
        archive = self.root / 'archive'; archive.write_bytes(b'corrupt')
        with patch.object(C.urllib.request, 'urlopen') as network, self.assertRaisesRegex(ValueError, 'SHA256'):
            C.download('https://codeload.github.com/llvm/llvm-project/tar.gz/pin', archive, '0' * 64)
        network.assert_not_called()

    def test_download_temporary_symlink_cannot_overwrite_another_file(self):
        archive = self.root / 'archive.tar.gz'; victim = self.root / 'victim'; victim.write_bytes(b'preserve')
        archive.with_suffix('.gz.partial').symlink_to(victim)
        with patch.object(C.urllib.request, 'urlopen', return_value=io.BytesIO(b'original')):
            C.download('https://codeload.github.com/llvm/llvm-project/tar.gz/pin', archive, C.sha(b'original'))
        self.assertEqual(victim.read_bytes(), b'preserve')
        linked = self.root / 'linked'; linked.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'): C.extract_sdk(self.archive([('sdk/a', 'file')]), linked / 'sdk')

    def test_provision_refuses_source_outputs(self):
        with self.assertRaisesRegex(ValueError, 'outside source'):
            C.provision(C.ROOT / 'xnu/downloads', self.root / 'cache', self.root / 'artifacts')

    def test_workflow_only_publishes_locally_prepared_layouts(self):
        workflow = (C.ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('--prepared-layouts runtime/prepared-layouts.tar.gz --publish-only', workflow)
        self.assertIn('actions/upload-pages-artifact@v4', workflow)
        self.assertIn('actions/deploy-pages@v4', workflow)
        for forbidden in ('layouts_ci.py', '--native', 'tests/', 'compare_catalog.py',
                          'survey_catalog.py', 'emsdk', 'cmake', 'ninja-build', '--check'):
            self.assertNotIn(forbidden, workflow)


if __name__ == '__main__': unittest.main()
