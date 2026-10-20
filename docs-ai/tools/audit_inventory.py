#!/usr/bin/env python3
"""Inventory documentation and source citations; these are not review coverage.

Audit reports are deliberately excluded from explanatory-guide citation counts.
No source is modified. Run from any directory to regenerate audits/inventory.json.
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

from check_links import DOCS, ROOT, LINK, prose_lines
from paths import SOURCE_ROOT, require_source


SOURCE_SUFFIXES = {".c", ".h", ".cpp", ".s", ".S", ".defs", ".m", ".mm"}
IMPLEMENTATION_SUFFIXES = {".c", ".cpp", ".s", ".S", ".m", ".mm"}
REPORT_PAGES = {
    "coverage.md", "expansion-audit.md", "coverage-audit.md",
    "table-of-contents.md", "source-index.md",
}


def explanatory(page):
    relative = page.relative_to(DOCS)
    return relative.parts[0] != "audits" and relative.as_posix() not in REPORT_PAGES


def source_links(page):
    result = set()
    for _, line in prose_lines(page):
        for match in LINK.finditer(line):
            url = urlsplit(match[1].strip().removeprefix("<").removesuffix(">"))
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if target.is_relative_to(SOURCE_ROOT) and target.is_file():
                result.add(target.relative_to(SOURCE_ROOT).as_posix())
    return result


def source_paths():
    """Discover only XNU files, independent of nearby generated/archived trees."""
    require_source()
    return sorted(Path(p) for p in subprocess.check_output(
        ["rg", "--files"], cwd=SOURCE_ROOT, text=True, timeout=15).splitlines()
        if (SOURCE_ROOT / p).resolve().is_relative_to(SOURCE_ROOT))


def main():
    paths = source_paths()
    pages = sorted(p for p in DOCS.rglob("*.md") if explanatory(p))
    references = defaultdict(set)
    page_rows = []
    areas = defaultdict(Counter)
    for page in pages:
        text = page.read_text()
        relative = page.relative_to(DOCS).as_posix()
        linked = source_links(page)
        for path in linked:
            references[path].add(relative)
        area = str(page.parent.relative_to(DOCS))
        row = {
            "path": relative,
            "words_including_code": len(text.split()),
            "sections": sum(bool(re.match(r"^## ", line))
                            for _, line in prose_lines(page)),
            "mermaid_diagrams": text.count("```mermaid"),
            "marked_source_excerpts": text.count("<!-- source-excerpt:"),
            "distinct_cited_files": len(linked),
        }
        page_rows.append(row)
        areas[area]["pages"] += 1
        for key in ("words_including_code", "mermaid_diagrams", "marked_source_excerpts"):
            areas[area][key] += row[key]

    directories = defaultdict(Counter)
    subdirectories = defaultdict(Counter)
    unlinked = []
    for path in paths:
        keys = [directories[path.parts[0] if len(path.parts) > 1 else "(root)"]]
        if len(path.parts) > 2:
            keys.append(subdirectories["/".join(path.parts[:2])])
        source = path.suffix in SOURCE_SUFFIXES
        implementation = path.suffix in IMPLEMENTATION_SUFFIXES
        line_count = len((SOURCE_ROOT / path).read_bytes().splitlines()) if source else 0
        cited = path.as_posix() in references
        for counts in keys:
            counts["all_files"] += 1
            counts["source_header_interface_files"] += int(source)
            counts["source_header_interface_lines"] += line_count
            counts["implementation_files"] += int(implementation)
            counts["cited_files"] += int(cited)
            counts["cited_source_header_interface_files"] += int(cited and source)
            counts["cited_implementation_files"] += int(cited and implementation)
        if implementation and not cited:
            unlinked.append({"path": path.as_posix(), "lines": line_count})

    output = {
        "method": {
            "source_suffixes": sorted(SOURCE_SUFFIXES),
            "implementation_suffixes": sorted(IMPLEMENTATION_SUFFIXES),
            "guide_scope": "All Markdown except audits/, coverage, expansion-audit, "
                           "coverage-audit, table-of-contents and source-index.",
            "source_scope": "Files returned by rg --files within the xnu/ checkout; "
                            "includes tests, bundled headers and conditional code.",
            "interpretation": "A citation identifies a file, not reviewed lines or "
                              "explained behavior. No citation is a search lead, "
                              "not proof that a mechanism is absent from the guides.",
            "lines": "Physical lines including comments and blank lines.",
        },
        "totals": {
            "explanatory_pages": len(pages),
            "distinct_guide_cited_files": len(references),
            "source_header_interface_files": sum(
                c["source_header_interface_files"] for c in directories.values()),
            "source_header_interface_lines": sum(
                c["source_header_interface_lines"] for c in directories.values()),
        },
        "documentation_areas": dict(sorted(areas.items())),
        "directories": dict(sorted(directories.items())),
        "subdirectories": dict(sorted(subdirectories.items())),
        "pages": page_rows,
        "source_references": {p: sorted(v) for p, v in sorted(references.items())},
        "uncited_implementation_files_by_size": sorted(
            unlinked, key=lambda row: (-row["lines"], row["path"])),
    }
    destination = DOCS / "audits" / "inventory.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["totals"]))
    print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
