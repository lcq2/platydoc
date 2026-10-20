"""Regression checks for source previews, heading links and code preservation."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from book.build import Book, DOCS, ROOT, SOURCE_ROOT, Node, source_headings, validate_output_paths


class SourcePreviewTests(unittest.TestCase):
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
        self.assertEqual(citation.attrs["data-source"], "xnu/doc/allocators/api-basics.md")

    def test_line_ranges_keep_exact_endpoints_and_nested_relative_links(self):
        page = {"file": DOCS / "subsystems/runtime/README.md",
                "path": "subsystems/runtime/README.md",
                "url": "subsystems/runtime/README.html", "title": "Runtime"}
        target = SOURCE_ROOT / "osfmk/kern/ast.c"
        citation = Node("a", {"href": os.path.relpath(target, page["file"].parent)
                             + "#L40-L50"})
        Book([], Path("/unused-output"), Path("/unused-cache")).convert_link(citation, page)
        self.assertEqual(citation.attrs["href"], "../../_sources/xnu/osfmk/kern/ast.c.html#L40-L50")
        self.assertEqual((citation.attrs["data-start"], citation.attrs["data-end"]), ("40", "50"))

    def test_project_tools_and_upstream_files_have_distinct_source_identities(self):
        page = {"file": DOCS / "development/building-html.md",
                "path": "development/building-html.md",
                "url": "development/building-html.html", "title": "Building"}
        book = Book([], Path("/unused-output"), Path("/unused-cache"))
        for target, expected in ((ROOT / "make_docs.py", "make_docs.py"),
                                 (SOURCE_ROOT / "README.md", "xnu/README.md")):
            with self.subTest(target=target):
                citation = Node("a", {"href": os.path.relpath(target, page["file"].parent)})
                book.convert_link(citation, page)
                self.assertEqual(citation.attrs["data-source"], expected)
                self.assertEqual(citation.attrs["href"], "../_sources/" + expected + ".html")
        self.assertEqual(set(book.sources), {"make_docs.py", "xnu/README.md"})

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

if __name__ == "__main__":
    unittest.main()
