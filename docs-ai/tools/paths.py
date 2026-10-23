"""Paths shared by Platydoc tools; the XNU checkout is a read-only input.

Inventory and authored catalog metadata paths stay relative to SOURCE_ROOT.
Markdown destinations and generated book records are relative to the project.
Resolve from this module, never the caller's working directory.
"""
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DOCS.parent
SOURCE_ROOT = PROJECT_ROOT / "platydoc-data" / "xnu"


def require_source():
    """Fail early with a useful diagnostic when the checkout is not populated."""
    for relative in ("osfmk", "bsd", "iokit", "APPLE_LICENSE"):
        if not (SOURCE_ROOT / relative).exists():
            raise RuntimeError(
                f"XNU source tree is missing or incomplete at {SOURCE_ROOT}. "
                "Initialize platydoc-data, then run git -C platydoc-data submodule update --init xnu before building."
            )
