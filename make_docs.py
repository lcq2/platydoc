#!/usr/bin/env python3
"""Build Platydoc's offline XNU handbook, reading xnu/ without modifying it.

Run from any working directory. Use --help for refresh and output options.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "docs-ai" / "tools"))
from book.build import main

if __name__ == "__main__":
    raise SystemExit(main())
