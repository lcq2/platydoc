# Platydoc

Platydoc is a source-based technical handbook for Apple XNU. It explains subsystem boundaries, key structures, execution paths, ownership, synchronization and failure handling, with links to the implementation, checked source excerpts and diagrams. The current handbook was researched against the `xnu-12377.121.6` snapshot.

Start with the [handbook](docs-ai/README.md), [architecture](docs-ai/architecture.md) or [complete contents](docs-ai/table-of-contents.md). The [coverage record](docs-ai/coverage.md) and [coverage audit](docs-ai/coverage-audit.md) distinguish examined mechanisms, remaining gaps and unavailable external implementations.

## Project layout

| Path | Purpose |
| --- | --- |
| `xnu/` | Apple XNU source input, kept separate as a checkout or submodule. Documentation work does not modify it. Its [upstream README](xnu/README.md) and [technical documentation](xnu/doc/) remain intact. |
| `docs-ai/` | Editable handbook, authored interface metadata, catalog generators, checks and HTML reader tools. |
| `make_docs.py` | Documentation build entry point. |
| `docs-ai-html/` | Generated standalone HTML book. |
| `.docs-cache/` | Reusable source-token and SVG caches. |
| [AGENTS.md](AGENTS.md) | Research, authoring, regeneration, verification and release-maintenance instructions. |

Kernel paths written in the handbook, such as `osfmk/vm/vm_map.c`, are normally relative to `xnu/`. Documentation commands run from the Platydoc root. The [shared path module](docs-ai/tools/paths.py) makes this distinction explicit for tools; generated output and caches belong outside the kernel source input.

## Build and read

Populate `xnu/` with the selected XNU source checkout before building. If it is configured as a Git submodule, initialize that submodule using the repository's Git configuration. Install the dependencies listed in the [build guide](docs-ai/development/building-html.md), then run from this directory:

```sh
python3 make_docs.py
```

Open `docs-ai-html/index.html`. The generated folder is self-contained and can be copied elsewhere for offline reading. It includes chapter navigation, full-documentation search, an alphabetical index, SVG diagrams and syntax-highlighted source previews. Search and source viewing use local JavaScript and work with `file://` URLs; no server or CDN is required.

After changing Markdown, rebuild the book. After selecting a new source release, review the affected explanations and authored metadata before regenerating the interface catalogs:

```sh
python3 make_docs.py --refresh-catalogs
```

The [maintenance instructions](AGENTS.md) explain source provenance, exact excerpts, catalog ownership, release migration and validation. Catalog generation checks declarations and metadata; it does not research changed implementation semantics or turn source analysis into a kernel runtime test.

## Attribution

XNU retains its original notices and [Apple license](xnu/APPLE_LICENSE). The documentation tools preserve source headers and include notices for bundled build dependencies in the generated book. See the [HTML build guide](docs-ai/development/building-html.md) for the build components and provenance records.
