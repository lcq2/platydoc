"""Documentation notices persist through edits and standalone generators."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import build_mach_trap_catalog as traps
import build_toc
import doc_license as license


class DocumentationLicenseTests(unittest.TestCase):
    def test_notice_is_idempotent_and_preserves_exact_excerpt(self):
        body = (
            "# A chapter\n\n"
            "<!-- source-excerpt: ../platydoc-data/xnu/probe.c#L1-L3 -->\n"
            "```c\nint probe(void) {\n\treturn 1;  \n}\n```\n"
        )
        first = license.with_license_notice(body)
        self.assertIn(body, first)
        self.assertEqual(first, license.with_license_notice(first))
        self.assertEqual(first.count(license.BEGIN), 1)
        self.assertEqual(first.count(license.END), 1)
        self.assertIn("Quoted source code and third-party material", first)
        self.assertEqual(license.strip_license_notice(first).rstrip("\n"),
                         body.rstrip("\n"))

    def test_old_and_duplicate_marked_notices_are_replaced(self):
        old = f"{license.BEGIN}\nOld notice.\n{license.END}\n"
        text = "# Chapter\n\n" + old + "\n" + old
        updated = license.with_license_notice(text)
        self.assertEqual(updated.count(license.BEGIN), 1)
        self.assertNotIn("Old notice", updated)
        self.assertEqual(updated, license.with_license_notice("# Chapter\n"))

    def test_crlf_code_excerpt_bytes_are_preserved(self):
        excerpt = (
            "<!-- source-excerpt: ../platydoc-data/xnu/probe.c#L1-L3 -->\r\n"
            "```c\r\nint probe(void) {\r\n\treturn 1;  \r\n}\r\n```\r\n"
        )
        body = "# Chapter\r\n\r\n" + excerpt + "\r\nExplanation.\r\n"
        updated = license.with_license_notice(body)
        self.assertIn(excerpt, updated)
        self.assertIn(excerpt, license.strip_license_notice(updated))
        self.assertEqual(updated, license.with_license_notice(updated))

    def test_check_is_read_only_and_vendor_and_upstream_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            docs = project / "docs-ai"
            page = docs / "README.md"
            vendor = docs / "tools/book/vendor/dependency/README.md"
            upstream = project / "platydoc-data/xnu/README.md"
            for path in (page, vendor, upstream):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Original\n")
            linked = docs / "linked.md"
            linked.symlink_to(upstream)
            pages = license.handbook_paths(docs)
            self.assertEqual(pages, [page])
            self.assertEqual(license.sync_notices(pages, check=True), [page])
            self.assertEqual(page.read_text(), "# Original\n")
            self.assertEqual(license.sync_notices(pages), [page])
            self.assertEqual(license.sync_notices(pages, check=True), [])
            self.assertEqual(license.sync_notices(pages), [])
            self.assertEqual(vendor.read_text(), "# Original\n")
            self.assertEqual(upstream.read_text(), "# Original\n")

    def test_toc_generator_adds_notice_without_changing_heading_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            docs = Path(directory)
            page = docs / "README.md"
            page.write_text(license.with_license_notice("# Guide\n\n## Entry\n"))
            with patch.object(build_toc, "DOCS", docs), \
                    patch.object(build_toc, "GROUPS", [("Guide", ".", ["README"])]), \
                    redirect_stdout(io.StringIO()):
                build_toc.main()
            output = (docs / "table-of-contents.md").read_text()
            self.assertEqual(output.count(license.BEGIN), 1)
            self.assertIn("[Guide](README.md)", output)
            self.assertEqual(build_toc.headings(page), ("Guide", [("Entry", "entry")]))

    def test_mach_generator_keeps_notice_outside_generated_block_and_passes_check(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mach-traps.md"
            authored = "# Traps\n\nAuthored introduction.\n\n"
            original = f"{authored}{traps.START}\nOld rows.\n{traps.END}\n\nAfterword.\n"
            generated = f"{traps.START}\nNew rows.\n{traps.END}"
            output.write_text(original)
            with patch.object(traps, "OUT", output), \
                    patch.object(traps, "generate", return_value=generated), \
                    patch.object(traps, "require_source"), \
                    redirect_stdout(io.StringIO()):
                with patch.object(sys, "argv", ["catalog"]):
                    traps.main()
                first = output.read_text()
                with patch.object(sys, "argv", ["catalog", "--check"]):
                    traps.main()
                with patch.object(sys, "argv", ["catalog"]):
                    traps.main()
            self.assertEqual(output.read_text(), first)
            self.assertTrue(first.startswith(authored))
            self.assertIn("Afterword.\n", first)
            self.assertLess(first.index(traps.END), first.index(license.BEGIN))
            self.assertEqual(first.count(license.BEGIN), 1)


if __name__ == "__main__":
    unittest.main()
