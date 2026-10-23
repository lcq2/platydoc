# Handbook data and Pages publishing

`platydoc-data` owns compiler builds, generated headers, structure surveys,
validation and release publication. This repository renders the handbook using
one immutable data release. Pages never builds or runs a native compiler.

## Select a data release

In a local `platydoc-data` checkout:

```sh
python3 make_data.py build
python3 make_data.py publish --repo lcq2/platydoc-data
```

Publication prints a content-addressed `layouts-<sha256>` release tag. In this
repository, select that tag:

```sh
python3 make_docs.py --update-data layouts-<sha256> --data-repo lcq2/platydoc-data
python3 make_docs.py
```

Commit `runtime/prepared-layouts.release.json` with the relevant handbook edits.
The archive and `docs-ai-html/` remain ignored. Ordinary prose and reader UI edits
reuse the selected package and require no new data release.

The existing reference can continue pointing to an older release hosted in
`lcq2/platydoc` during migration. Selecting a new release changes the repository
and checksum together; never point the reference at an unpublished asset.

For an unpublished local package:

```sh
python3 make_docs.py --prepared-layouts platydoc-data/dist/prepared-layouts.tar.gz
```

## Pages

Actions downloads the exact archive from the committed reference, checks its
size/checksum, renders HTML and the offline ZIP, and deploys the result. There
are no compiler builds, native runs, header generators or validation suites.

The producer will be checked out as the root `platydoc-data/` submodule. Only
the selected package crosses the build boundary; Pages initializes that repository and only its `xnu` submodule for handbook
source previews. It does not initialize `bootstrap_cmds` or run producer tools.

GitHub CLI is required only for explicit release downloads/uploads. Install it
through your package manager and authenticate locally with `gh auth login`.

Original documentation: CC BY 4.0. Build tools: GPL-2.0-only. Bundled compiler,
headers and third-party assets retain their original notices.
