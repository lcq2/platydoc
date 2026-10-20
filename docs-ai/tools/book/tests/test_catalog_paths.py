"""Catalog input isolation and source-link identity after the XNU move.

Run with: python3 -B -m unittest discover -s docs-ai/tools/book/tests -v
These fixtures never regenerate the real catalogs or write the XNU checkout.
"""

from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import build_bsd_syscall_catalog as bsd
import build_mach_trap_catalog as traps
import build_mig_catalog as mig
import doc_license
import paths


class CatalogPathsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="platydoc-catalog-")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.source = self.project / "xnu"
        self.docs = self.project / "docs-ai"
        self.bsd_out = self.docs / "interfaces/bsd-syscalls"
        self.mig_out = self.docs / "interfaces/mach-messages"
        self.body = "int\nprobe(void)\n{\n\treturn helper();\n}\n"
        self.write(self.source / "bsd/kern/probe.c", self.body)
        self.write(self.source / "osfmk/probe.defs",
                   "subsystem probe 1000;\nroutine probe();\n")
        # A generated book and an old checkout must not become source inputs.
        self.write(self.project / "bsd/kern/decoy.c", self.body)
        self.write(self.project / "osfmk/decoy.c", self.body)
        for relative in (
            "docs-ai-html/_downloads/osfmk/copied.defs",
            "archive/osfmk/old.defs",
            "docs-ai/scratch.defs",
        ):
            self.write(self.project / relative,
                       "subsystem decoy 9000;\nroutine decoy();\n")
        self.write(self.source / "tests/test.defs",
                   "subsystem test 8000;\nroutine test();\n")

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def data(self):
        item = {
            "id": 1000, "kind": "routine", "name": "probe",
            "server_symbol": "probe", "sender_symbol": "probe",
            "line": 2, "end_line": 2, "signature": "routine probe();",
            "comment": "",
        }
        return {
            "interfaces": [{
                "path": "osfmk/probe.defs",
                "profiles": {"server64": {
                    "subsystem": "probe", "base": 1000,
                    "serverprefix": "", "userprefix": "", "items": [item],
                }},
                "raw_routine_lines": [2], "uncovered_routine_lines": [],
            }],
            "include_wrappers": [], "type_definitions": [],
        }

    def snapshot(self):
        return {p.relative_to(self.source): p.read_bytes()
                for p in self.source.rglob("*") if p.is_file()}

    def assert_source_links(self, text, directory):
        targets = re.findall(r"\]\(([^)]+#L\d+(?:-L\d+)?)\)", text)
        self.assertTrue(targets)
        for url in targets:
            path = (directory / url.split("#", 1)[0]).resolve()
            self.assertTrue(path.is_relative_to(self.source), url)
            self.assertTrue(path.is_file(), url)

    def test_shared_layout_and_all_link_helpers(self):
        self.assertEqual(paths.SOURCE_ROOT, paths.PROJECT_ROOT / "xnu")
        self.assertEqual(bsd.MASTER, paths.SOURCE_ROOT / "bsd/kern/syscalls.master")
        self.assertEqual(bsd.DEST, paths.DOCS / "interfaces/bsd-syscalls")
        self.assertEqual(mig.OUT, paths.DOCS / "interfaces/mach-messages")
        self.assertEqual(traps.OUT, paths.DOCS / "interfaces/mach-traps.md")
        relative = "bsd/kern/probe.c"
        for text, parent in (
            (bsd.link_source(relative, 2, "probe"), self.bsd_out),
            (mig.source_link(relative, 2, "probe"), self.mig_out),
            (traps.link("probe", relative, 2), self.docs / "interfaces"),
        ):
            self.assert_source_links(text, parent)

    def test_definition_scanners_ignore_project_copies_and_keep_relative_paths(self):
        before = self.snapshot()
        with patch.object(bsd, "SOURCE_ROOT", self.source):
            candidates = bsd.index_implementations({"probe"})["probe"]
        self.assertEqual([entry["path"] for entry in candidates],
                         ["bsd/kern/probe.c"])
        with patch.object(mig, "SOURCE_ROOT", self.source):
            index = mig.index_code(self.data())
        for collection in ("definitions", "occurrences"):
            self.assertEqual([entry["path"] for entry in index[collection]["probe"]],
                             ["bsd/kern/probe.c"])
        self.assertEqual(before, self.snapshot())

    def test_defs_discovery_ignores_book_archives_and_test_interfaces(self):
        self.write(self.source / "osfmk/types.defs", "type integer_t = int;\n")
        self.write(self.source / "libsyscall/mach/wrapper.defs",
                   "#include <osfmk/probe.defs>\n")
        expected_profile = self.data()["interfaces"][0]["profiles"]["server64"]
        with patch.object(mig, "SOURCE_ROOT", self.source), \
                patch.object(mig, "parse", return_value=expected_profile) as parse:
            data = mig.collect()
        self.assertEqual([row["path"] for row in data["interfaces"]],
                         ["osfmk/probe.defs"])
        self.assertEqual(data["interfaces"][0]["uncovered_routine_lines"], [])
        self.assertEqual([row["path"] for row in data["include_wrappers"]],
                         ["libsyscall/mach/wrapper.defs"])
        self.assertEqual([row["path"] for row in data["type_definitions"]],
                         ["osfmk/types.defs"])
        self.assertEqual(parse.call_count, len(mig.PROFILES))
        self.assertTrue(all(call.args[0] == self.source / "osfmk/probe.defs"
                            for call in parse.call_args_list))

    def test_bsd_renderer_reads_source_checkout_and_links_same_files(self):
        self.write(self.source / "bsd/kern/syscalls.master",
                   "0 AUE_NULL ALL { int probe(void); }\n")
        master = self.source / "bsd/kern/syscalls.master"
        metadata = {"probe": {
            "family": "test-family", "purpose": "Exercise the fixture operation.",
            "mechanism": "The fixture calls helper and returns its result.",
            "implementation": [{"path": "bsd/kern/probe.c", "line": 2}],
        }}
        before = self.snapshot()
        with patch.object(bsd, "SOURCE_ROOT", self.source), \
                patch.object(bsd, "MASTER", master):
            rows = bsd.parse_master()
            families, outputs = bsd.render(rows, metadata)
        self.assertEqual(families, {"test-family": 1})
        for text in outputs.values():
            self.assert_source_links(text, self.bsd_out)
            self.assertEqual(text.count(doc_license.BEGIN), 1)
            self.assertEqual(text, doc_license.with_license_notice(text))
        self.assertEqual(before, self.snapshot())

    def test_mig_renderer_registration_excerpt_and_test_links_match_checkout(self):
        self.write(self.source / "osfmk/kern/ipc_kobject.c", "\n" * 200)
        self.write(self.mig_out / "descriptions.tsv",
                   "probe\tExercise the fixture operation.\n")
        self.write(self.mig_out / "mechanisms-fixture.json",
                   json.dumps({"probe": "Calls helper and returns its result."}))
        before = self.snapshot()
        with patch.object(mig, "SOURCE_ROOT", self.source), \
                patch.object(mig, "OUT", self.mig_out):
            data = self.data()
            index = mig.index_code(data)
            summary = mig.render(data, index)
        self.assertEqual(summary[0]["file"], "osfmk/probe.defs")
        self.assertEqual(summary[0]["mechanism_slots"], 1)
        text = (self.mig_out / "probe.md").read_text()
        self.assertIn("../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197", text)
        excerpt = re.search(
            r"<!-- source-excerpt: ([^ ]+) -->\n```c\n(.*?)\n```", text, re.S)
        self.assertIsNotNone(excerpt)
        url, body = excerpt.groups()
        relative, first, last = re.fullmatch(r"(.+)#L(\d+)-L(\d+)", url).groups()
        target = (self.mig_out / relative).resolve()
        self.assertEqual(target, self.source / "bsd/kern/probe.c")
        self.assertEqual(body.splitlines(),
                         target.read_text().splitlines()[int(first)-1:int(last)])
        for name in ("probe.md", "subsystems.md"):
            page = (self.mig_out / name).read_text()
            self.assert_source_links(page, self.mig_out)
            self.assertEqual(page.count(doc_license.BEGIN), 1)
            self.assertEqual(page, doc_license.with_license_notice(page))
        self.assertEqual(before, self.snapshot())

    def test_mach_trap_generation_uses_source_table_header_and_bodies(self):
        table = []
        for number in range(128):
            if number == 47:
                table.extend([
                    "#if defined(__LP64__) || defined(__arm64__)",
                    "/* 47 */ MACH_TRAP(trap_probe, 1, 1, NULL)",
                    "#else", "/* 47 */ MACH_TRAP(kern_invalid, 0, 0, NULL)",
                    "#endif",
                ])
            elif number == 63:
                table.extend([
                    "#if __LP64__", "/* 63 */ MACH_TRAP(kern_invalid, 0, 0, NULL)",
                    "#else", "/* 63 */ MACH_TRAP(kern_invalid, 0, 0, NULL)",
                    "#endif",
                ])
            else:
                table.append(f"/* {number} */ MACH_TRAP(kern_invalid, 0, 0, NULL)")
        self.write(self.source / "osfmk/kern/syscall_sw.c", "\n".join(table))
        self.write(self.source / "osfmk/mach/mach_traps.h",
                   "struct probe_args {\n PAD_ARG_(uint32_t, value);\n};\n"
                   "int trap_probe(struct probe_args *args);\n")
        self.write(self.source / "osfmk/kern/probe.c",
                   "int\ntrap_probe(struct probe_args *args)\n{\n return 0;\n}\n")
        self.write(self.project / "osfmk/decoy_trap.c",
                   "int\ntrap_probe(void)\n{\n return 1;\n}\n")
        before = self.snapshot()
        with patch.object(traps, "SOURCE_ROOT", self.source), \
                patch.object(traps, "PURPOSE", {47: "Exercise the fixture trap."}):
            text = traps.generate()
        self.assertIn("`uint32_t value`", text)
        self.assertIn("Exercise the fixture trap.", text)
        self.assert_source_links(text, self.docs / "interfaces")
        self.assertEqual(before, self.snapshot())

    def test_all_entry_points_require_checkout_before_outputs_or_scans(self):
        # A missing submodule must fail before creating catalog directories or
        # trusting saved inventories, including MIG's render-only entry point.
        for module, arguments, output_name in (
            (bsd, [], "DEST"), (mig, [], "OUT"),
            (mig, ["--render-only"], "OUT"), (traps, [], "OUT"),
        ):
            with self.subTest(module=module.__name__, arguments=arguments):
                destination = self.project / "must-not-be-created"
                with ExitStack() as stack:
                    stack.enter_context(patch.object(module, output_name, destination))
                    stack.enter_context(patch.object(
                        module, "require_source", side_effect=RuntimeError("missing checkout")))
                    stack.enter_context(patch.object(sys, "argv", ["catalog", *arguments]))
                    stack.enter_context(redirect_stdout(io.StringIO()))
                    with self.assertRaisesRegex(RuntimeError, "missing checkout"):
                        module.main()
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
