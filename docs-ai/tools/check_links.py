#!/usr/bin/env python3
"""Check local links, source-line bounds, Markdown fences, and source excerpts.

Run from any directory: python3 /path/to/platydoc/docs-ai/tools/check_links.py
This checks documentation structure, not kernel behavior or Mermaid rendering.
"""

from collections import Counter
import re
import sys
from urllib.parse import unquote, urlsplit

from check_excerpts import check_excerpts
from paths import DOCS, PROJECT_ROOT, require_source


# The HTML builder imports ROOT for project-relative documents and source records.
ROOT = PROJECT_ROOT
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\n]+)\)")
SOURCE_LINE = re.compile(r"L([1-9][0-9]*)(?:-L([1-9][0-9]*))?$")


def prose_lines(path):
    """Yield lines outside fenced blocks and report unterminated blocks."""
    fence = None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token), number)
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            continue
        if fence is None:
            yield number, line
    if fence:
        raise ValueError(f"unclosed code fence at line {fence[2]}")


def heading_ids(path):
    seen = Counter()
    result = set()
    for _, line in prose_lines(path):
        heading = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if not heading:
            continue
        text = heading.group(1).lower()
        text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"<[^>]*>", "", text)
        slug = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
        duplicate = seen[slug]
        seen[slug] += 1
        result.add(f"{slug}-{duplicate}" if duplicate else slug)
    return result


def main():
    require_source()
    files = sorted(DOCS.rglob("*.md"))
    errors = []
    links = 0
    excerpts = 0
    source_files = set()
    graphs = {}
    heading_cache = {}
    line_counts = {}
    for path in files:
        graphs[path] = set()
        excerpt_count, excerpt_errors = check_excerpts(path)
        excerpts += excerpt_count
        errors.extend(excerpt_errors)
        try:
            lines = list(prose_lines(path))
        except ValueError as error:
            errors.append(f"{path.relative_to(ROOT)}: {error}")
            continue
        if not any(line.startswith("# ") for _, line in lines):
            errors.append(f"{path.relative_to(ROOT)}: missing document title")
        for number, line in lines:
            for match in LINK.finditer(line):
                raw = match.group(1).strip()
                url = urlsplit(raw.removeprefix("<").removesuffix(">"))
                if url.scheme or url.netloc:
                    continue
                links += 1
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                location = f"{path.relative_to(ROOT)}:{number}"
                if not target.is_relative_to(ROOT):
                    errors.append(f"{location}: link escapes project tree: {raw}")
                    continue
                if not target.exists():
                    errors.append(f"{location}: missing target: {raw}")
                    continue
                if target.is_file() and not target.is_relative_to(DOCS):
                    source_files.add(target)
                if target.is_relative_to(DOCS) and target.suffix == ".md":
                    graphs[path].add(target)
                anchor = unquote(url.fragment)
                line_anchor = SOURCE_LINE.fullmatch(anchor)
                if line_anchor and target.is_file():
                    if target not in line_counts:
                        line_counts[target] = len(target.read_bytes().splitlines())
                    start = int(line_anchor.group(1))
                    end = int(line_anchor.group(2) or start)
                    if not 1 <= start <= end <= line_counts[target]:
                        errors.append(f"{location}: line anchor out of bounds: {raw}")
                elif anchor and target.suffix == ".md":
                    if target not in heading_cache:
                        try:
                            heading_cache[target] = heading_ids(target)
                        except ValueError as error:
                            errors.append(f"{location}: target {target.name}: {error}")
                            heading_cache[target] = set()
                    if anchor not in heading_cache[target]:
                        errors.append(f"{location}: missing heading: {raw}")
    reached = set()
    pending = [DOCS / "README.md"]
    while pending:
        node = pending.pop()
        if node in reached:
            continue
        reached.add(node)
        pending.extend(graphs.get(node, ()))
    for path in files:
        if path not in reached:
            errors.append(f"{path.relative_to(ROOT)}: not reachable from README.md")
    for error in errors:
        print(error)
    print(f"{len(files)} Markdown files; {links} local links; "
          f"{len(source_files)} distinct linked files outside docs-ai; "
          f"{excerpts} checked source excerpts; "
          f"{len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
