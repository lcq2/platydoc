"""Source/project boundary checks after moving the handbook outside xnu/.

Run: python3 -B -m unittest discover -s docs-ai/tools/book/tests -v
These fixtures never invoke the audit inventory writer or modify the checkout.
"""

import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import audit_inventory
import build_source_index
import check_excerpts
import check_links
import doc_license
import paths


class RelocatedToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.docs = self.project / "docs-ai"
        self.source = self.project / "xnu"
        self.page = self.docs / "subsystems/runtime/entry.md"
        self.write("xnu/osfmk/kern/entry.c", "int entry(void) {\n\treturn 1;\n}\n")
        self.write("xnu/bsd/kern/helper.c", "int helper;\n")
        self.write("xnu/iokit/present.h", "/* fixture */\n")
        self.write("xnu/APPLE_LICENSE", "Source license.\n")
        self.write("xnu/doc/guide.md", "# Upstream entry\n\nSource documentation.\n")
        self.write("make_docs.py", "# project entry point\n")
        self.write("docs-ai/README.md", "# Handbook\n\n[Entry](subsystems/runtime/entry.md#entry)\n")
        self.write("docs-ai/subsystems/runtime/entry.md", self.chapter())
        self.write("docs-ai/audits/inventory.json", '{"historical": true}\n')
        self.patches = contextlib.ExitStack()
        self.addCleanup(self.patches.close)
        for module in (paths, check_links, check_excerpts, build_source_index, audit_inventory):
            for name, value in (("ROOT", self.project), ("PROJECT_ROOT", self.project),
                                ("DOCS", self.docs), ("SOURCE_ROOT", self.source)):
                if hasattr(module, name):
                    self.patches.enter_context(patch.object(module, name, value))

    def write(self, relative, text):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def chapter(self):
        return (
            "# Entry\n\n"
            "[Kernel](../../../xnu/osfmk/kern/entry.c#L1-L3)\n"
            "[Project tool](../../../make_docs.py#L1)\n"
            "[Upstream docs](../../../xnu/doc/guide.md#upstream-entry)\n\n"
            "<!-- source-excerpt: ../../../xnu/osfmk/kern/entry.c#L1-L3 -->\n"
            "```c\nint entry(void) {\n\treturn 1;\n}\n```\n"
        )

    def link_check(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            result = check_links.main()
        return result, stream.getvalue()

    def test_project_root_contract_and_relocated_links_from_another_cwd(self):
        self.assertEqual(check_links.ROOT, paths.PROJECT_ROOT)
        self.assertEqual(check_links.DOCS.parent, check_links.ROOT)
        previous = Path.cwd()
        try:
            os.chdir(self.base)
            result, output = self.link_check()
        finally:
            os.chdir(previous)
        self.assertEqual(result, 0, output)
        self.assertIn("1 checked source excerpts; 0 errors", output)

    def test_old_checkout_relative_links_and_project_escapes_are_rejected(self):
        (self.base / "outside.c").write_text("outside\n")
        with self.page.open("a") as stream:
            stream.write("\n[Old path](../../../osfmk/kern/entry.c)\n")
            stream.write("[Outside](../../../../outside.c)\n")
        result, output = self.link_check()
        self.assertEqual(result, 1)
        self.assertIn("missing target: ../../../osfmk/kern/entry.c", output)
        self.assertIn("link escapes project tree: ../../../../outside.c", output)

    def test_relocated_excerpt_keeps_exact_indentation_and_line_bounds(self):
        self.assertEqual(check_excerpts.check_excerpts(self.page, self.project), (1, []))
        self.page.write_text(self.chapter().replace("\treturn 1;", "    return 1;"))
        count, errors = check_excerpts.check_excerpts(self.page, self.project)
        self.assertEqual(count, 1)
        self.assertIn("differs at source line 2", errors[0])
        self.page.write_text(self.chapter().replace("entry.c#L1-L3 -->", "entry.c#L1-L4 -->"))
        self.assertIn("range outside source", check_excerpts.check_excerpts(self.page, self.project)[1][0])

    def test_excerpt_cannot_follow_a_symlink_outside_the_project(self):
        outside = self.base / "outside.c"
        outside.write_text("outside\n")
        (self.source / "osfmk/kern/escape.c").symlink_to(outside)
        self.page.write_text(
            "# Entry\n<!-- source-excerpt: ../../../xnu/osfmk/kern/escape.c#L1-L1 -->\n"
            "```c\noutside\n```\n")
        self.assertIn("invalid excerpt source", check_excerpts.check_excerpts(self.page, self.project)[1][0])

    def test_audit_citations_are_only_xnu_relative_not_project_or_output_paths(self):
        generated = self.write("docs-ai-html/_downloads/osfmk/copied.c", "copy\n")
        self.write("old-xnu/osfmk/archived.c", "archive\n")
        self.write("xnu/osfmk/kern/space name.c", "space\n")
        (self.source / "osfmk/kern/escaped.c").symlink_to(generated)
        with self.page.open("a") as stream:
            stream.write("\n[Output](../../../docs-ai-html/_downloads/osfmk/copied.c)\n"
                         "[Archive](../../../old-xnu/osfmk/archived.c)\n"
                         "[Symlink](../../../xnu/osfmk/kern/escaped.c)\n"
                         "[Encoded](../../../xnu/osfmk/kern/space%20name.c#L1)\n")
        self.assertEqual(audit_inventory.source_links(self.page),
                         {"osfmk/kern/entry.c", "doc/guide.md", "osfmk/kern/space name.c"})

    def test_audit_discovery_scans_only_the_xnu_checkout_without_writing_baseline(self):
        baseline = self.docs / "audits/inventory.json"
        before = baseline.read_bytes()
        self.write("docs-ai-html/_downloads/osfmk/copied.c", "copy\n")
        self.write("old-xnu/osfmk/archived.c", "archive\n")
        self.write("docs-ai/tools/not_kernel.c", "tool fixture\n")
        discovered = {path.as_posix() for path in audit_inventory.source_paths()}
        self.assertIn("osfmk/kern/entry.c", discovered)
        self.assertIn("APPLE_LICENSE", discovered)
        self.assertEqual(discovered, {
            "osfmk/kern/entry.c", "bsd/kern/helper.c", "iokit/present.h",
            "APPLE_LICENSE", "doc/guide.md",
        })
        self.assertEqual(baseline.read_bytes(), before)

    def test_index_groups_upstream_directories_but_links_project_relative_targets(self):
        with self.page.open("a") as stream:
            stream.write("\n[BSD](../../../xnu/bsd/kern/helper.c#L1)\n"
                         "[License](../../../xnu/APPLE_LICENSE)\n")
        self.write("docs-ai/source-index.md", "# Old generated index\n\n[Stale](../xnu/iokit/present.h)\n")
        references = build_source_index.collect_references()
        self.assertIn(Path("xnu/osfmk/kern/entry.c"), references)
        self.assertIn(Path("make_docs.py"), references)
        self.assertNotIn(Path("xnu/iokit/present.h"), references)
        with contextlib.redirect_stdout(io.StringIO()):
            build_source_index.main()
        index = (self.docs / "source-index.md").read_text()
        for group in ("bsd", "osfmk", "doc", "XNU root files", "Project files"):
            self.assertIn("\n## " + group + "\n", index)
        self.assertNotIn("\n## xnu\n", index)
        self.assertIn("(../xnu/osfmk/kern/entry.c)", index)
        self.assertIn("(../make_docs.py)", index)
        self.assertEqual(index.count(doc_license.BEGIN), 1)
        self.assertEqual(index, doc_license.with_license_notice(index))

    def test_missing_checkout_fails_with_the_checkout_diagnostic(self):
        (self.source / "APPLE_LICENSE").unlink()
        with self.assertRaisesRegex(RuntimeError, "XNU source tree is missing or incomplete"):
            check_links.main()
        with self.assertRaisesRegex(RuntimeError, "Populate the xnu/ checkout"):
            audit_inventory.source_paths()


if __name__ == "__main__":
    unittest.main()
