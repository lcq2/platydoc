#!/usr/bin/env python3
"""Regenerate source-index.md from direct local file links in this guide."""

from collections import defaultdict
from urllib.parse import unquote, urlsplit

from check_links import DOCS, ROOT, LINK, prose_lines
from paths import SOURCE_ROOT, require_source


def collect_references(docs=None, root=None):
    """Return project-relative destinations of direct local citations."""
    docs = (docs if docs is not None else DOCS).resolve()
    root = (root if root is not None else ROOT).resolve()
    output = docs / "source-index.md"
    references = defaultdict(set)
    for page in sorted(docs.rglob("*.md")):
        if page == output:
            continue
        for _, line in prose_lines(page):
            for match in LINK.finditer(line):
                raw = match.group(1).strip().removeprefix("<").removesuffix(">")
                url = urlsplit(raw)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (page.parent / unquote(url.path)).resolve()
                if (target.is_relative_to(root)
                        and not target.is_relative_to(docs)
                        and target.is_file()):
                    references[target.relative_to(root)].add(page.relative_to(docs))
    return references


def source_group(source, source_root=None, root=None):
    """Group XNU citations by upstream directories; keep project inputs separate."""
    source_root = source_root if source_root is not None else SOURCE_ROOT
    root = root if root is not None else ROOT
    prefix = source_root.resolve().relative_to(root.resolve())
    if source.is_relative_to(prefix):
        relative = source.relative_to(prefix)
        return relative.parts[0] if len(relative.parts) > 1 else "XNU root files"
    return "Project files"


def main():
    require_source()
    output = DOCS / "source-index.md"
    references = collect_references()

    lines = [
        "# Source-reference index", "",
        "[Guide index](README.md) · [Coverage](coverage.md)", "",
        "This index maps directly cited local source, interface, build, test, "
        "and upstream documentation files to the guides that cite them. "
        "It does not imply whole-file review; see each subsystem's coverage "
        "table. Directory links are excluded.", "",
        "Audit reports also cite files to identify future expansion work. Those "
        "references are navigation evidence, not completed explanations. The "
        "[coverage audit](coverage-audit.md) and its inventory keep explanatory-guide "
        "citations separate from audit-only discoveries.", "",
        "Regenerate with `python3 docs-ai/tools/build_source_index.py`.", "",
    ]
    previous_group = None
    for source, pages in sorted(references.items(), key=lambda item: (source_group(item[0]), item[0])):
        group = source_group(source)
        if group != previous_group:
            lines.extend([
                "", "## " + group, "",
                "| Cited file | Guides |", "| --- | --- |",
            ])
            previous_group = group
        links = []
        for page in sorted(pages):
            label = page.with_suffix("").as_posix().replace("/README", " / overview")
            links.append(f"[{label}]({page.as_posix()})")
        lines.append(f"| [{source.as_posix()}](../{source.as_posix()}) | "
                     + ", ".join(links) + " |")
    lines.extend(["", f"Total: {len(references)} distinct directly cited files.", ""])
    output.write_text("\n".join(lines))
    print(f"Indexed {len(references)} files in {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
