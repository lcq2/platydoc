Platydoc layout reader (GPL-2.0-only)
===================================

This directory consumes standalone packages produced by platydoc-data.
It contains no compiler, source-header generators or native validation tools.

catalog.py attaches the package to the handbook, supplies presentation assets
from browser/, and binds current chapter/source links. prepared.py downloads
an explicitly selected content-addressed release and verifies its checksum.

Select/update data explicitly:
  python3 make_docs.py --update-data layouts-<sha256> --data-repo lcq2/platydoc-data

Render offline using the cached, locked package:
  python3 make_docs.py

Use a local producer output without publishing:
  python3 make_docs.py --prepared-layouts platydoc-data/dist/prepared-layouts.tar.gz

The producer owns tools/layouts/, including all original compiler build,
configuration/header generation, survey, comparison and packaging scripts.
See its README.md and make_data.py. Reader UI edits do not require repackaging.
