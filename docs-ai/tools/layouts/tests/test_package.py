"""Focused producer/consumer boundary checks; no compiler is invoked."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from layouts import prepared
from layouts.catalog import source_records_by_layout_path
from paths import SOURCE_ROOT, PROJECT_ROOT

class PackageTests(unittest.TestCase):
    def test_producer_source_identity_links_to_nested_handbook_source(self):
        path = (SOURCE_ROOT / 'bsd/sys/proc_internal.h').relative_to(PROJECT_ROOT).as_posix()
        url = '_sources/' + path + '.html'
        record = {'path': path, 'sha256': 'source-bytes'}
        indexed = source_records_by_layout_path({url: record})
        self.assertEqual(indexed['xnu/bsd/sys/proc_internal.h'], (url, record))
        self.assertEqual(indexed[path], (url, record))

    def test_download_mismatch_preserves_existing_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); reference = root/'ref.json'; output = root/'data.tar.gz'
            digest = hashlib.sha256(b'expected').hexdigest()
            reference.write_text(json.dumps({'format':prepared.REFERENCE_FORMAT,'version':1,
                'repo':'owner/data','tag':'layouts-'+digest,'asset':prepared.ASSET,'sha256':digest,'bytes':8}))
            output.write_bytes(b'previous')
            def wrong_download(args): Path(args[-1]).write_bytes(b'corrupt!')
            with patch.object(prepared, 'gh', side_effect=wrong_download):
                with self.assertRaisesRegex(ValueError,'checksum'): prepared.download(reference,output)
            self.assertEqual(output.read_bytes(), b'previous')

    def test_unpack_rejects_escape_and_leaves_no_partial_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); archive=root/'bad.tar.gz'; output=root/'layouts'
            with tarfile.open(archive,'w:gz') as tar:
                member=tarfile.TarInfo('../escape');member.size=1
                tar.addfile(member,io.BytesIO(b'x'))
            with self.assertRaisesRegex(ValueError,'Unsafe'): prepared.unpack(archive,output)
            self.assertFalse(output.exists());self.assertFalse((root/'escape').exists())

    def test_missing_cache_does_not_start_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);reference=root/'ref.json';digest='a'*64
            reference.write_text(json.dumps({'format':prepared.REFERENCE_FORMAT,'version':1,
                'repo':'owner/data','tag':'layouts-'+digest,'asset':prepared.ASSET,'sha256':digest,'bytes':1}))
            with patch.object(prepared,'gh',side_effect=AssertionError('unexpected network')):
                with self.assertRaisesRegex(ValueError,'--update-data'): prepared.cached_archive(reference,root)

if __name__=='__main__':unittest.main()
