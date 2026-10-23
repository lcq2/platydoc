"""Regression checks for source previews, heading links and code preservation."""
import os
from pathlib import Path
import posixpath
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from book.build import (
    Book, DOCS, ROOT, SOURCE_ROOT, DOM, Node, register_license_notices,
    shell, source_headings, validate_output_paths,
)
from doc_license import LICENSE_URL, NOTICE, with_license_notice


class SourcePreviewTests(unittest.TestCase):
    def test_nested_authored_layout_query_and_fragment_survive_conversion(self):
        target = {"file": DOCS / "structures/layout-browser.md", "url": "structures/layout-browser.html"}
        page = {"file": DOCS / "subsystems/runtime/recount-and-resource-attribution.md",
                "path": "subsystems/runtime/recount-and-resource-attribution.md",
                "url": "subsystems/runtime/recount-and-resource-attribution.html", "title": "Recount"}
        citation = Node("a", {"href": "../../structures/layout-browser.md?declaration=recount_track#workspace"})
        Book([target], Path("/unused-output"), Path("/unused-cache")).convert_link(citation, page)
        self.assertEqual(citation.attrs["href"], "../../structures/layout-browser.html?declaration=recount_track#workspace")
        self.assertNotIn("data-source", citation.attrs)

    def test_markdown_heading_citation_previews_that_section(self):
        target = SOURCE_ROOT / "doc/allocators/api-basics.md"
        page = {"file": DOCS / "subsystems/vm/kernel-allocation.md",
                "path": "subsystems/vm/kernel-allocation.md",
                "url": "subsystems/vm/kernel-allocation.html",
                "title": "Kernel allocation"}
        citation = Node("a", {"href": os.path.relpath(target, page["file"].parent)
                             + "#allocation-flags"})
        book = Book([], Path("/unused-output"), Path("/unused-cache"))
        book.convert_link(citation, page)
        heading = next(h for h in source_headings(target)
                       if h["id"] == "allocation-flags")
        self.assertEqual(int(citation.attrs["data-start"]), heading["line"])
        self.assertGreaterEqual(int(citation.attrs["data-end"]), heading["line"])
        self.assertTrue(citation.attrs["href"].endswith("#allocation-flags"))
        self.assertTrue(citation.attrs["data-source-payload"].startswith("assets/sources/"))
        self.assertEqual(citation.attrs["data-source"], "platydoc-data/xnu/doc/allocators/api-basics.md")

    def test_line_ranges_keep_exact_endpoints_and_nested_relative_links(self):
        page = {"file": DOCS / "subsystems/runtime/README.md",
                "path": "subsystems/runtime/README.md",
                "url": "subsystems/runtime/README.html", "title": "Runtime"}
        target = SOURCE_ROOT / "osfmk/kern/ast.c"
        citation = Node("a", {"href": os.path.relpath(target, page["file"].parent)
                             + "#L40-L50"})
        Book([], Path("/unused-output"), Path("/unused-cache")).convert_link(citation, page)
        self.assertEqual(citation.attrs["href"], "../../_sources/platydoc-data/xnu/osfmk/kern/ast.c.html#L40-L50")
        self.assertEqual((citation.attrs["data-start"], citation.attrs["data-end"]), ("40", "50"))

    def test_project_tools_and_upstream_files_have_distinct_source_identities(self):
        page = {"file": DOCS / "development/building-html.md",
                "path": "development/building-html.md",
                "url": "development/building-html.html", "title": "Building"}
        book = Book([], Path("/unused-output"), Path("/unused-cache"))
        for target, expected in ((ROOT / "make_docs.py", "make_docs.py"),
                                 (SOURCE_ROOT / "README.md", "platydoc-data/xnu/README.md")):
            with self.subTest(target=target):
                citation = Node("a", {"href": os.path.relpath(target, page["file"].parent)})
                book.convert_link(citation, page)
                self.assertEqual(citation.attrs["data-source"], expected)
                self.assertEqual(citation.attrs["href"], "../_sources/" + expected + ".html")
        self.assertEqual(set(book.sources), {"make_docs.py", "platydoc-data/xnu/README.md"})

    def test_generated_output_and_cache_cannot_write_inside_xnu(self):
        validate_output_paths(ROOT / "docs-ai-html", ROOT / ".docs-cache")
        for output, cache in (
            (SOURCE_ROOT, ROOT / ".docs-cache"),
            (SOURCE_ROOT / "generated", ROOT / ".docs-cache"),
            (ROOT / "docs-ai-html", SOURCE_ROOT / ".docs-cache"),
        ):
            with self.subTest(output=output, cache=cache):
                with self.assertRaisesRegex(ValueError, "read-only xnu"):
                    validate_output_paths(output, cache)


class LicenseTests(unittest.TestCase):
    def test_shared_footer_scopes_license_and_keeps_nested_offline_links(self):
        for current in (
            "index.html", "concept-index.html", "build-info.html",
            "subsystems/vm/pmap.html", "_sources/platydoc-data/xnu/osfmk/vm/vm_map.c.html",
            "_directories/platydoc-data/xnu/osfmk.html",
        ):
            with self.subTest(page=current):
                dom = DOM(shell("Example", "<h1>Example</h1>", current)).root
                footer = next(n for n in dom.walk() if n.tag == "footer")
                links = [n for n in footer.walk() if n.tag == "a"]
                license_link = next(n for n in links if n.attrs.get("rel") == "license")
                self.assertEqual(license_link.attrs["href"], LICENSE_URL)
                self.assertEqual(license_link.text(), "CC BY 4.0")
                local = {
                    posixpath.normpath(posixpath.join(
                        posixpath.dirname(current), n.attrs["href"]))
                    for n in links if "://" not in n.attrs["href"]
                }
                self.assertIn("licenses/CC-BY-4.0.txt", local)
                self.assertIn("licenses/GPL-2.0.txt", local)
                self.assertIn("build-info.html#licenses", local)
                self.assertIn("Original Platydoc documentation and diagrams", footer.text())
                self.assertIn("XNU source, quoted code and third-party materials", footer.text())
                self.assertIn("retain their original licenses", footer.text())

    def test_license_files_are_copied_exactly_and_registered_as_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = {
                "LICENSE-DOCS": b"CC license text\r\n",
                "LICENSE": b"GPL license text\n",
                "platydoc-data/xnu/APPLE_LICENSE": b"Apple license text\n",
                "book/vendor/mermaid/LICENSE.txt": b"Mermaid license\n",
                "book/vendor/mermaid/THIRD_PARTY_NOTICES.txt": b"Other notices\n",
                "book/vendor/mermaid/PROVENANCE.txt": b"Provenance\n",
            }
            for path, data in original.items():
                file = root/path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
            book = Book([], root/"output", root/"cache")
            with patch("book.build.ROOT", root), \
                    patch("book.build.SOURCE_ROOT", root/"platydoc-data" / "xnu"), \
                    patch("book.build.HERE", root/"book"):
                links = register_license_notices(book)
            for filename, source in (
                ("CC-BY-4.0.txt", "LICENSE-DOCS"), ("GPL-2.0.txt", "LICENSE"),
            ):
                self.assertEqual((book.output/"licenses"/filename).read_bytes(), original[source])
                self.assertEqual(links[filename], "_sources/" + source + ".html")
            self.assertEqual(set(book.sources), set(original))
            self.assertEqual(links["APPLE_LICENSE.txt"], "_sources/platydoc-data/xnu/APPLE_LICENSE.html")
            for path, data in original.items():
                self.assertEqual((root/path).read_bytes(), data)

    @unittest.skipUnless(shutil.which("cmark-gfm"), "cmark-gfm is not installed")
    def test_markdown_notice_is_preserved_but_not_duplicated_in_content_or_search(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = with_license_notice("# Example\n\nExplains virtual memory.\n")
            path = root/"example.md"
            path.write_text(original)
            page = {
                "file": path, "path": "example.md", "url": "example.html",
                "title": "Example", "chapter": "Example",
                "sections": source_headings(path), "markdown": original,
            }
            book = Book([page], root/"output", root/"cache")
            book.prepare()
            self.assertNotIn("CC BY", page["dom"].text())
            self.assertIn("virtual memory", page["dom"].text())
            self.assertTrue(all("CC BY" not in item["text"] for item in book.search))
            self.assertEqual(page["markdown"], original)
            self.assertEqual(path.read_text(), original)
            self.assertIn(NOTICE, original)

if __name__ == "__main__":
    unittest.main()
