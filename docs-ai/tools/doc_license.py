#!/usr/bin/env python3
"""Keep the CC BY 4.0 notice in original handbook Markdown.

The notice covers original Platydoc text and diagrams. It does not relicense
quoted source, vendored files or the documentation software. Markdown writers
use with_license_notice(); the HTML reader strips this block before rendering
because its shared page footer supplies the visible notice.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from collections.abc import Iterable

from paths import DOCS


LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
BEGIN = "<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->"
END = "<!-- END PLATYDOC DOCUMENTATION LICENSE -->"
NOTICE = (
    "Original Platydoc text and diagrams are licensed under "
    f"[CC BY 4.0]({LICENSE_URL}). "
    "Quoted source code and third-party material retain their respective licenses."
)
BLOCK = f"{BEGIN}\n{NOTICE}\n{END}\n"
_BLOCK_RE = re.compile(
    r"^" + re.escape(BEGIN) + r"\r?\n.*?^" + re.escape(END) + r"(?:\r?\n|$)",
    re.MULTILINE | re.DOTALL,
)


def strip_license_notice(text: str) -> str:
    """Remove marked notices without altering any other lines or code fences."""
    return _BLOCK_RE.sub("", text)


def with_license_notice(text: str) -> str:
    """Append one current notice, replacing any previous marked notices."""
    body = strip_license_notice(text).rstrip("\r\n")
    return (body + "\n\n" if body else "") + BLOCK


def handbook_paths(root: Path = DOCS) -> list[Path]:
    """Find original handbook pages, excluding vendors and linked input files."""
    root = Path(root).resolve()
    return [
        path for path in sorted(root.rglob("*.md"))
        if "vendor" not in path.relative_to(root).parts
        and not path.is_symlink()
        and path.resolve().is_relative_to(root)
    ]


def sync_notices(paths: Iterable[Path], *, check: bool = False) -> list[Path]:
    """Return stale paths; update their notices unless this is a read-only check."""
    changed = []
    for path in paths:
        old = path.read_bytes().decode("utf-8")
        new = with_license_notice(old)
        if old != new:
            changed.append(path)
            if not check:
                path.write_bytes(new.encode("utf-8"))
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report missing/stale notices without writing files")
    parser.add_argument("--root", type=Path, default=DOCS,
                        help="handbook directory (default: docs-ai)")
    args = parser.parse_args()
    pages = handbook_paths(args.root)
    changed = sync_notices(pages, check=args.check)
    if args.check and changed:
        for path in changed:
            print(f"Missing or stale documentation license: {path}")
        raise SystemExit(1)
    action = "Checked" if args.check else "Updated"
    print(f"{action} documentation licenses: {len(pages)} pages, "
          f"{len(changed)} changed.")


if __name__ == "__main__":
    main()
