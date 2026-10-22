#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real pinned-input catalog/cache and corruption tests; no XNU writes."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from layouts import catalog as C


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="platydoc-layout-catalog-tests-")
        cls.root = Path(cls.temporary.name)
        cls.runtime = C.PROJECT_ROOT / ".docs-cache/layouts/proof-runtime"
        cls.native = C.PROJECT_ROOT / ".docs-cache/layouts/build-native/bin/layout-engine"
        cls.configs = C.PROJECT_ROOT / ".docs-cache/layouts/xnu-configs"
        cls.cache = cls.root / "cache"
        cls.book = cls.root / "book"
        cls.seed_book(cls.book)
        C.generate(cls.book / "layouts", cls.book, cls.cache, cls.runtime, cls.native, cls.configs)
        C.seal(cls.book / "layouts")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @staticmethod
    def seed_book(book):
        book.mkdir(parents=True)
        C.write_json(book / "source-records.json", {})
        mapping = C.read_json(C.DOCS / "structures/layouts.json")
        for entry in mapping["entries"]:
            for chapter in entry["chapters"]:
                page, anchor = chapter.split("#")
                path = book / (page.removesuffix(".md") + ".html")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('<h2 id="' + anchor + '">Existing mapped chapter</h2>')

    def copy_book(self, name):
        path = self.root / name
        shutil.copytree(self.book, path)
        return path

    def test_real_four_profile_package(self):
        result = C.verify(self.book)
        self.assertEqual(result["layout_profiles"], 4)
        self.assertGreater(result["layout_declarations"], 20)
        self.assertGreater(result["layout_headers"], 1300)
        catalog = C.read_json(self.book / "layouts/catalog.json")
        self.assertEqual([s["key"] for s in catalog["selections"]], ["task", "recount_track"])
        for profile in catalog["profiles"]:
            cached = C.read_json(self.book / "layouts" / profile["cache"]["path"])
            sizes = {r["name"]: r["size_bytes"] for r in cached["result"]["records"]}
            self.assertEqual(sizes["task"], 2072 if profile["id"].startswith("development") else 1632)
            self.assertEqual(sizes["recount_track"], 24 if profile["id"].endswith("vmapple") else 64)
            self.assertEqual(cached["document"]["dependencies"]["status"], "not-computed")

    def test_explicit_query_keys_and_reserved_integration_marker(self):
        catalog = C.read_json(self.book / "layouts/catalog.json")
        self.assertEqual(C.validate_selection_query('declaration=task', catalog)["key"], "task")
        for query in ('declaration=', 'declaration=unknown', 'declaration=task&declaration=task', 'other=task', 'declaration=task&other=1'):
            with self.subTest(query=query), self.assertRaises(ValueError):
                C.validate_selection_query(query, catalog)
        from book.build import shell
        book = self.root / "integrated-book"
        self.seed_book(book)
        page = book / C.PAGE
        page.write_text(shell('Structure layouts', '<h1 id="layouts">Structure layouts</h1><div id="structure-layout-explorer"></div><h2 id="usage">Usage</h2>', C.PAGE, nav='<a href="../index.html">Handbook</a>'))
        reference = C.integrate(book, self.cache.parent, self.runtime, self.native, self.configs)
        html = page.read_text()
        self.assertEqual(html.count('<h1 '), 1)
        self.assertIn('id="search-dialog"', html)
        self.assertIn('id="source-dialog"', html)
        self.assertIn('../layouts/book-layouts.js', html)
        self.assertNotIn('class="mockup-footer"', html)
        self.assertNotIn('href="licenses/Platydoc-', html)
        self.assertEqual(reference["profiles"], 4)
        self.assertTrue(any(notice["name"] == 'LLVM-LICENSE.txt' for notice in reference["notices"]))
        self.assertEqual(C.verify(book)["layout_profiles"], 4)
        invalid = self.root / "bad-marker"
        self.seed_book(invalid)
        (invalid / C.PAGE).write_text('<div id="structure-layout-explorer"></div>' * 2)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            C.integrate(invalid, self.cache.parent, self.runtime, self.native, self.configs)
        self.assertFalse((invalid / 'layouts').exists())

    def test_cache_hit_and_malformed_context_rebuild(self):
        cache = self.root / "cache-test"
        shutil.copytree(self.cache, cache)
        original_run, calls = C.subprocess.run, []

        def run(argv, *args, **kwargs):
            if argv[0] == str(self.native):
                calls.append(argv)
            return original_run(argv, *args, **kwargs)

        first = self.root / "cached-book"
        self.seed_book(first)
        with patch.object(C.subprocess, "run", side_effect=run):
            C.generate(first / "layouts", first, cache, self.runtime, self.native, self.configs)
        self.assertEqual(calls, [], "Valid full-context hits must not launch native compiler")
        path = next(cache.glob("*.json"))
        envelope = C.read_json(path)
        envelope["value"]["request"] = {"files": {"invented": "unsafe override"}}
        envelope["sha256"] = C.digest(C.encoded(envelope["value"]))
        C.write_json(path, envelope)
        second = self.root / "rebuilt-book"
        self.seed_book(second)
        with patch.object(C.subprocess, "run", side_effect=run):
            C.generate(second / "layouts", second, cache, self.runtime, self.native, self.configs)
        self.assertEqual(len(calls), 1, "Malformed cache is rebuilt rather than overriding request context")

    def test_native_bytes_and_source_membership_invalidate(self):
        altered = self.root / "altered-native"
        altered.write_bytes(self.native.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "compiler identity changed"):
            C.provisioned(self.runtime, altered, self.configs)
        snapshot = C.inventory(C.SOURCE_ROOT)
        snapshot["new-shadowing-header.h"] = "0" * 64
        with patch.object(C, "inventory", return_value=snapshot), self.assertRaisesRegex(ValueError, "snapshot changed"):
            C.provisioned(self.runtime, self.native, self.configs)

    def test_generated_config_bytes_invalidate(self):
        configs = self.root / "configs"
        shutil.copytree(self.configs, configs)
        provenance = C.read_json(configs / "config-provenance.json")
        profile = next(iter(provenance["profiles"].values()))
        path = configs / profile["directory"] / next(iter(profile["files"]))
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
        with self.assertRaisesRegex(ValueError, "input changed"):
            C.provisioned(self.runtime, self.native, configs)

    def test_rehashed_catalog_and_config_corruption_rejected(self):
        book = self.copy_book("bad-catalog")
        path = book / "layouts/catalog.json"
        value = C.read_json(path)
        value["declarations"][0]["name"] = "fabricated"
        C.write_json(path, value)
        (book / "layouts/catalog.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutCatalog=" + C.encoded(value) + b";\n")
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "declarations differ"):
            C.verify(book)
        book = self.copy_book("bad-config")
        with (book / "layouts/explorer-config.js").open("ab") as stream:
            stream.write(b"window.layoutExplorerConfig.sourceLinks={};\n")
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "source links"):
            C.verify(book)

    def test_rehashed_provenance_and_coverage_claims_rejected(self):
        book = self.copy_book("bad-coverage")
        path = book / "layouts/catalog.json"
        value = C.read_json(path)
        value["coverage"]["status"] = "complete"
        C.write_json(path, value)
        (book / "layouts/catalog.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutCatalog=" + C.encoded(value) + b";\n")
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "coverage/purpose"):
            C.verify(book)
        book = self.copy_book("bad-provenance")
        path = book / "layouts/generation-provenance.json"
        value = C.read_json(path)
        value["configuration_sha256"] = "0" * 64
        C.write_json(path, value)
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "generation provenance"):
            C.verify(book)

    def test_omitted_license_and_rehashed_numeric_corruption_rejected(self):
        book = self.copy_book("missing-license")
        (book / "layouts/licenses/LLVM-LICENSE.txt").unlink()
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "runtime asset identity"):
            C.verify(book)
        book = self.copy_book("bad-number")
        catalog = C.read_json(book / "layouts/catalog.json")
        summary = catalog["profiles"][0]["cache"]
        path = book / "layouts" / summary["path"]
        value = C.read_json(path)
        value["document"]["layouts"]["entries"][0]["size_bytes"] = 9007199254740992
        C.write_json(path, value)
        summary.update(bytes=path.stat().st_size, sha256=C.digest(path.read_bytes()))
        C.write_json(book / "layouts/catalog.json", catalog)
        (book / "layouts/catalog.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutCatalog=" + C.encoded(catalog) + b";\n")
        C.seal(book / "layouts")
        with self.assertRaisesRegex(ValueError, "contract validation failed"):
            C.verify(book)


if __name__ == "__main__":
    unittest.main()
