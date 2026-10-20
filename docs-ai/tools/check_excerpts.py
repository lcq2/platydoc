#!/usr/bin/env python3
"""Verify annotated Markdown excerpts against exact checkout line ranges."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from paths import DOCS, PROJECT_ROOT, require_source


ROOT = PROJECT_ROOT
MARKER = re.compile(r"^<!-- source-excerpt: (.+) -->$")
RANGE = re.compile(r"L([1-9][0-9]*)-L([1-9][0-9]*)$")


def check_excerpts(path, root=None):
    """Return (excerpt count, errors); compare text including indentation."""
    root = Path(root if root is not None else ROOT).resolve()
    lines = path.read_text().splitlines()
    errors = []
    count = 0
    for index, line in enumerate(lines):
        marker = MARKER.fullmatch(line)
        if marker is None:
            if line.startswith("<!-- source-excerpt:"):
                errors.append(f"{path}:{index + 1}: malformed excerpt marker")
            continue
        count += 1
        location = f"{path}:{index + 1}"
        url = urlsplit(marker.group(1))
        bounds = RANGE.fullmatch(url.fragment)
        if url.scheme or url.netloc or not url.path or not bounds:
            errors.append(f"{location}: excerpt needs a local path and #Lstart-Lend")
            continue
        source = (path.parent / unquote(url.path)).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            errors.append(f"{location}: invalid excerpt source: {marker.group(1)}")
            continue
        start, end = map(int, bounds.groups())
        source_lines = source.read_text().splitlines()
        if not 1 <= start <= end <= len(source_lines):
            errors.append(f"{location}: excerpt range outside source")
            continue
        if index + 1 >= len(lines) or not re.fullmatch(r"```[\w+-]*", lines[index + 1]):
            errors.append(f"{location}: marker must immediately precede a code fence")
            continue
        finish = next((n for n in range(index + 2, len(lines)) if lines[n] == "```"), None)
        if finish is None:
            errors.append(f"{location}: excerpt fence is not closed")
            continue
        actual = lines[index + 2:finish]
        expected = source_lines[start - 1:end]
        if actual != expected:
            mismatch = next((n for n, (a, e) in enumerate(zip(actual, expected)) if a != e),
                            min(len(actual), len(expected)))
            errors.append(f"{location}: excerpt differs at source line {start + mismatch} "
                          f"({len(actual)} displayed lines, {len(expected)} expected)")
    return count, errors


def main():
    require_source()
    count = 0
    errors = []
    for page in sorted(DOCS.rglob("*.md")):
        number, failures = check_excerpts(page)
        count += number
        errors.extend(failures)
    for error in errors:
        print(error)
    print(f"{count} source excerpts; {len(errors)} errors")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
