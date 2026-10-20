"""Behavior checks for the offline index and generated-book verifier.

Run with: python3 -B -m unittest discover -s docs-ai/tools/book/tests -v
"""

import contextlib
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from book.concepts import build_concept_index
from book.verify import verify_generated


class ConceptIndexTests(unittest.TestCase):
    def setUp(self):
        self.pages = [{
            "path": "interfaces/bsd-syscalls/sample.md",
            "title": "Sample",
            "url": "interfaces/sample.html",
            "chapter": "Interfaces",
            "sections": [
                {"id": "exact-1", "title": "97: socket", "level": 2,
                 "text": "Rendered source text: CodeDirectory."},
                {"id": "not-a-slug", "title": "Repeated", "level": 2, "text": ""},
                {"id": "not-a-slug-2", "title": "Repeated", "level": 2, "text": ""},
            ],
            "markdown": (
                "# Sample\n## 97: socket\n"
                "Socket uses `socket()` and `AST_BSD`.\n"
                "Ignore `x1`, `NULL`, `0xff`, `a/b.c`, `void`, `_64`.\n"
                "```c\n`fenced_symbol` CodeDirectory\n```\n"
                "## Repeated\n`first_symbol`\n## Repeated\n`second_symbol`\n"
            ),
        }, {
            "path": "glossary.md", "title": "Glossary", "url": "glossary.html",
            "chapter": "Basics",
            "sections": [{"id": "terms-exact", "title": "Terms", "level": 2, "text": ""}],
            "markdown": (
                "# Glossary\n## Terms\n| Term | Meaning |\n| --- | --- |\n"
                "| AST | Asynchronous system trap: deferred work. |\n"
                "| `vm_page` | Metadata for a page. |\n"
            ),
        }]

    def test_supplied_ids_and_duplicate_heading_destinations(self):
        index = {row["term"]: row for row in build_concept_index(self.pages)}
        self.assertEqual(index["first_symbol"]["entries"][0]["url"],
                         "interfaces/sample.html#not-a-slug")
        self.assertEqual(index["second_symbol"]["entries"][0]["url"],
                         "interfaces/sample.html#not-a-slug-2")
        self.assertEqual(index["AST"]["entries"][0]["url"],
                         "glossary.html#terms-exact")
        self.assertEqual(index["vm_page"]["kind"], "Symbols")

    def test_concepts_interfaces_and_code_exclusions(self):
        rows = build_concept_index(self.pages)
        index = {row["term"]: row for row in rows}
        self.assertEqual(index["Socket"]["kind"], "Concepts")
        self.assertEqual(index["socket"]["kind"], "Interfaces")
        self.assertIn("AST_BSD", index)
        self.assertIn("Asynchronous system trap", index)
        for junk in ("fenced_symbol", "CodeDirectory", "x1", "NULL", "0xff",
                     "a/b.c", "void", "_64"):
            self.assertNotIn(junk, index)
        self.assertEqual(rows, build_concept_index(self.pages))
        self.assertEqual(rows, sorted(rows, key=lambda row: (row["term"].casefold(), row["kind"])))

    def test_numbered_dispatch_class_is_not_a_callable_interface(self):
        page = {
            "path": "interfaces/machine-entry-points.md", "title": "Entry",
            "url": "entry.html", "chapter": "Interfaces", "sections": [],
            "markdown": "| Number | Class |\n| --- | --- |\n| 1 | `MACH` |\n",
        }
        self.assertFalse(any(row["kind"] == "Interfaces"
                             for row in build_concept_index([page])))


class GeneratedBookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="xnu-book-test-")
        self.root = Path(self.temporary.name) / "book"
        for directory in ("src", "assets", "download"):
            (self.root / directory).mkdir(parents=True)
        (self.root / "src/code.html").write_text(
            '<html><span id="L1">a</span><span id="L5">b</span></html>')
        (self.root / "assets/app.js").write_text("void 0;")
        (self.root / "assets/figure.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect id="shape" width="20" height="10"/></svg>')
        (self.root / "download/text.md").write_text("# Raw\n")
        self.html = (
            '<html><h1 id="top">Test</h1>'
            '<a href="src/code.html#L1-L5">Code</a><a href="#top">Top</a>'
            '<a href="download/text.md">Raw</a>'
            '<script src="assets/app.js"></script>'
            '<img src="assets/figure.svg#shape">'
            '<a href="https://example.com">External</a>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<path d="M0 0 L10 10"/></svg></html>'
        )
        (self.root / "index.html").write_text(self.html)

    def tearDown(self):
        self.temporary.cleanup()

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return verify_generated(self.root)

    def test_valid_links_source_range_downloads_scripts_and_svgs(self):
        counts = self.verify()
        self.assertEqual(counts["html_files"], 2)
        self.assertEqual(counts["svg_files"], 1)
        self.assertEqual(counts["inline_svgs"], 1)
        self.assertEqual(counts["anchors"], 3)
        self.assertEqual(counts["scripts"], 1)
        self.assertEqual(counts["errors"], 0)

    def test_broken_or_unsafe_generated_content_is_rejected(self):
        bad_cases = {
            "missing anchor": self.html.replace("#L1-L5", "#L1-L6"),
            "reversed range": self.html.replace("#L1-L5", "#L5-L1"),
            "encoded traversal": self.html.replace("download/text.md", "%2e%2e/outside.md"),
            "external script": self.html.replace("assets/app.js", "https://cdn.example.com/app.js"),
            "javascript URL": self.html.replace('href="#top"', 'href="javascript:alert(1)"'),
            "missing file": self.html.replace("assets/app.js", "assets/missing.js"),
            "empty SVG": self.html.replace(
                '<path d="M0 0 L10 10"/>', '<defs><rect width="20" height="10"/></defs>'),
            "invalid SVG": self.html.replace('<path d="M0 0 L10 10"/>', "<path>"),
            "duplicate ID": self.html.replace('<h1 id="top">', '<i id="top"></i><h1 id="top">'),
            "base redirect": self.html.replace("<html>", '<html><base href="https://example.com">'),
        }
        for name, content in bad_cases.items():
            with self.subTest(name=name):
                (self.root / "index.html").write_text(content)
                with self.assertRaises(ValueError):
                    self.verify()

    def test_file_and_directory_index_symlinks_cannot_escape(self):
        outside = Path(self.temporary.name) / "outside.html"
        outside.write_text("<html>Outside</html>")
        link = self.root / "escape.html"
        link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink escapes"):
            self.verify()
        link.unlink()
        (self.root / "linked").mkdir()
        (self.root / "linked/index.html").symlink_to(outside)
        (self.root / "index.html").write_text(self.html + '<a href="linked/">Link</a>')
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.verify()

    def test_svg_entity_declarations_are_rejected(self):
        (self.root / "assets/figure.svg").write_text(
            '<!DOCTYPE svg [<!ENTITY x "expanded">]>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect id="shape" width="20" height="10"/><text>&x;</text></svg>')
        with self.assertRaisesRegex(ValueError, "entity declaration"):
            self.verify()


class CompactSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="xnu-compact-test-")
        self.root = Path(self.temporary.name)
        self.source = "doc/example.md"
        self.url = "_sources/" + self.source + ".html"
        self.payload = "assets/sources/example.js"
        (self.root / self.url).parent.mkdir(parents=True)
        (self.root / self.payload).parent.mkdir(parents=True)
        text = "# Alpha\r\ntext\fform-feed stays on one line\n## Alpha\nend\n"
        self.data = {
            "schema": 2, "path": self.source, "url": self.url, "language": "md",
            "styles": ["", "k"], "tokens": [[0, text[:9]], [1, text[9:]]],
            "aliases": {"alpha": 1, "alpha-1": 3}, "line_count": 4,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        self.wrapper = (
            f'<html><body data-source-path="{self.source}" '
            f'data-source-payload="{self.payload}"><main id="main">'
            f'<pre data-source-full data-source="{self.source}" '
            f'data-source-payload="{self.payload}"><code></code></pre>'
            '</main></body></html>'
        )
        self.index = (
            f'<html><body><h1 id="top">Book</h1>'
            f'<a class="source-link" href="{self.url}#L1-L4" '
            f'data-source="{self.source}" data-source-payload="{self.payload}" '
            f'data-start="1" data-end="4">Source</a>'
            f'<a href="{self.url}#alpha-1">Heading</a></body></html>'
        )
        (self.root / self.url).write_text(self.wrapper)
        (self.root / "index.html").write_text(self.index)
        self.save_payload()

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def envelope(value):
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        return {"schema": 2, "encoding": "gzip-base64",
                "data": base64.b64encode(gzip.compress(raw, mtime=0)).decode()}

    def save_payload(self, *, record_updates=None, suffix=""):
        js = ("window.XNU_SOURCES=window.XNU_SOURCES||{};\n"
              f"window.XNU_SOURCES[{json.dumps(self.source)}]="
              + json.dumps(self.envelope(self.data)) + ";\n" + suffix)
        (self.root / self.payload).write_text(js)
        record = {key: self.data[key] for key in ("path", "sha256", "line_count", "aliases")}
        record.update(payload=self.payload, payload_sha256=hashlib.sha256(js.encode()).hexdigest())
        record.update(record_updates or {})
        (self.root / "source-records.json").write_text(json.dumps({self.url: record}))
        return record

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return verify_generated(self.root)

    def test_virtual_line_and_markdown_anchors_from_exact_source_bytes(self):
        result = self.verify()
        self.assertEqual(result["source_payloads"], 1)
        self.assertEqual(result["virtual_source_lines"], 4)
        self.assertEqual(result["errors"], 0)
        self.assertNotIn('id="L1"', (self.root / self.url).read_text())

    def test_invalid_source_data_is_rejected(self):
        original = json.loads(json.dumps(self.data))
        cases = {
            "token style": {"tokens": [[8, "bad"]]},
            "non-integer style": {"tokens": [[True, "bad"]]},
            "CSS injection": {"styles": ["", 'x" onclick="bad']},
            "source hash": {"sha256": "0" * 64},
            "line count": {"line_count": 5},
            "alias line": {"aliases": {"alpha": 2, "alpha-1": 3}},
            "alias invented": {"aliases": {"alpha": 1, "invented": 3}},
            "alias out of bounds": {"aliases": {"alpha": 100}},
            "alias in line namespace": {"aliases": {"L1": 1}},
            "source URL": {"url": "_sources/wrong.md.html"},
            "raw bytes": {"raw_base64": base64.b64encode(b"different").decode()},
        }
        for name, change in cases.items():
            with self.subTest(name=name):
                self.data = dict(original, **change)
                self.save_payload()
                with self.assertRaises(ValueError):
                    self.verify()
        self.data = original

    def test_payload_and_manifest_integrity(self):
        self.save_payload(record_updates={"payload_sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "payload SHA-256 mismatch"):
            self.verify()
        self.save_payload(suffix="window.unexpected=true;\n")
        with self.assertRaisesRegex(ValueError, "JSON-only"):
            self.verify()
        self.save_payload()
        manifest = self.root / "source-records.json"
        manifest.write_text(manifest.read_text().replace(
            '"alpha": 1', '"alpha": 1, "alpha": 1'))
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.verify()
        self.save_payload()
        (self.root / "build-manifest.json").write_text(
            json.dumps({"source_hashes": {self.source: "0" * 64}}))
        with self.assertRaisesRegex(ValueError, "build-manifest"):
            self.verify()

    def test_missing_records_and_wrapper_or_citation_mismatches(self):
        cases = [
            (self.url, self.wrapper.replace(self.source, "wrong.md")),
            (self.url, self.wrapper.replace('<main id="main">', '<main id="main"><i id="L1"></i>')),
            (self.url, self.wrapper.replace('<main id="main">', '<main id="main"><i id="alpha"></i>')),
            ("index.html", self.index.replace('data-end="4"', 'data-end="3"')),
            ("index.html", self.index.replace("#L1-L4", "#L1-L5")),
            ("index.html", self.index.replace("#alpha-1", "#invented")),
            ("index.html", self.index.replace('data-source="doc/example.md"', 'data-source="wrong.md"')),
        ]
        for path, content in cases:
            with self.subTest(path=path, content=content):
                (self.root / self.url).write_text(self.wrapper)
                (self.root / "index.html").write_text(self.index)
                (self.root / path).write_text(content)
                with self.assertRaises(ValueError):
                    self.verify()
        (self.root / self.url).write_text(self.wrapper)
        (self.root / "index.html").write_text(self.index)
        (self.root / "source-records.json").unlink()
        with self.assertRaises(ValueError):
            self.verify()

    def test_invalid_utf8_and_line_endings_remain_byte_exact(self):
        raw = b"\xff\r\nline\fform-feed\rend"
        self.data.update(
            tokens=[[0, raw.decode("utf-8", errors="replace")]], aliases={},
            line_count=3, sha256=hashlib.sha256(raw).hexdigest(),
            raw_base64=base64.b64encode(raw).decode())
        self.save_payload()
        (self.root / "index.html").write_text(f'<a href="{self.url}#L1-L3">Source</a>')
        self.assertEqual(self.verify()["virtual_source_lines"], 3)

    def test_empty_source_has_no_virtual_first_line(self):
        self.data.update(tokens=[], aliases={}, line_count=0,
                         sha256=hashlib.sha256(b"").hexdigest())
        self.save_payload()
        (self.root / "index.html").write_text(f'<a href="{self.url}">Source</a>')
        self.assertEqual(self.verify()["virtual_source_lines"], 0)
        (self.root / "index.html").write_text(f'<a href="{self.url}#L1">Source</a>')
        with self.assertRaises(ValueError):
            self.verify()

    def test_packed_indexes_and_navigation_preserve_link_checks(self):
        search = [{"url": self.url + "#L2", "title": "Source", "heading": "Line",
                   "chapter": "Test", "text": "Searchable text"}]
        (self.root / "assets/search-index.js").write_text(
            "window.XNU_SEARCH=" + json.dumps(self.envelope(search)) + ";")
        concept = f'<h2 id="letter-A">A</h2><a href="{self.url}#alpha">Alpha</a>'
        (self.root / "assets/concept-index.js").write_text(
            "window.XNU_CONCEPT_INDEX=" + json.dumps(self.envelope(concept)) + ";")
        (self.root / "assets/navigation.js").write_text("window.XNU_NAV=" + json.dumps([
            {"part": 1, "title": "Chapter", "pages": [
                {"url": "index.html", "title": "Book", "number": "1"}]}]) + ";")
        (self.root / "index.html").write_text(
            self.index + '<a href="#letter-A">A</a>'
            '<div id="concept-content" data-index-payload="assets/concept-index.js"></div>')
        self.assertEqual(self.verify()["compressed_assets"], 3)
        (self.root / "assets/concept-index.js").write_text(
            "window.XNU_CONCEPT_INDEX=" + json.dumps(self.envelope('<h2 id="top">Duplicate</h2>')) + ";")
        with self.assertRaisesRegex(ValueError, "duplicate id"):
            self.verify()
        (self.root / "assets/concept-index.js").write_text(
            "window.XNU_CONCEPT_INDEX=" + json.dumps(self.envelope(concept)) + ";")
        search[0]["url"] = self.url + "#L100"
        (self.root / "assets/search-index.js").write_text(
            "window.XNU_SEARCH=" + json.dumps(self.envelope(search)) + ";")
        with self.assertRaisesRegex(ValueError, "missing anchor"):
            self.verify()
        search[0]["url"] = "https://external.example/file"
        (self.root / "assets/search-index.js").write_text(
            "window.XNU_SEARCH=" + json.dumps(self.envelope(search)) + ";")
        with self.assertRaisesRegex(ValueError, "must stay inside"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
