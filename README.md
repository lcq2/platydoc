# Platydoc

Platydoc is a technical handbook for Apple's XNU kernel, researched against `xnu-12377.121.6`. It explains subsystems, data structures and execution paths through source references, code excerpts and diagrams.

Read the [handbook](docs-ai/README.md) or browse the [table of contents](docs-ai/table-of-contents.md).

## Project layout

- `docs-ai/` — Markdown documentation and build tools.
- `platydoc-data/xnu/` — upstream kernel source, kept separate from documentation.
- `platydoc-data/` — shared XNU source and data-preparation tools; its build tools run only when changing prepared data.
- `docs-ai-html/` — generated static book, excluded from Git.
- `runtime/prepared-layouts.release.json` — pinned data release from the separate `platydoc-data` producer.

## Build and read

Populate `platydoc-data/xnu/` with the documented source release and install the dependencies in the [build guide](docs-ai/development/building-html.md). Download the selected layout package once using the command reported by the builder, or select a new release with `python3 make_docs.py --update-data layouts-<sha256> --data-repo lcq2/platydoc-data`. Then build offline from the project root:

```sh
python3 make_docs.py
```

Open `docs-ai-html/index.html` in a browser. The book works offline and on static hosts such as GitHub Pages, with full-text search, an alphabetical index, SVG diagrams and syntax-highlighted source previews.

Each build also creates `docs-ai-html/xnu-source-handbook.zip`. Use **Download offline version from here** in any page's header to download it directly. Extract the ZIP completely, then open `xnu-source-handbook/index.html`; keep the whole folder together. The archive includes all reading assets and license notices, so no server or network connection is needed.

Edit the Markdown or reader UI and rerun the build to update the book. Compiler builds, header generation and structure surveys belong to `platydoc-data`; handbook builds consume its package without a native compiler. See [AGENTS.md](AGENTS.md) for research, validation and release-update instructions.

## License

Platydoc's original text and diagrams, in Markdown and generated HTML, are licensed under [Creative Commons Attribution 4.0 International](LICENSE-DOCS) (`CC-BY-4.0`). Credit Platydoc and its contributors, link the license and indicate changes when reusing the documentation.

Build tools and browser software remain under [GNU GPL version 2](LICENSE) (`GPL-2.0-only`). XNU, reproduced source excerpts and bundled third-party dependencies retain their respective licenses and notices.
