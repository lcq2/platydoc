# Building and maintaining the HTML handbook

[Guide index](../README.md) · [Complete contents](../table-of-contents.md)

Platydoc keeps the editable Markdown in `docs-ai/`, Apple XNU as a separate read-only input in `xnu/`, generated HTML in `docs-ai-html/`, and reusable caches in `.docs-cache/`. Documentation tools and output remain outside the XNU checkout or submodule. It includes chapter navigation, a page outline, previous/next links, full-documentation search, an alphabetical concept/symbol index, standalone SVG diagrams, and source files with highlighted line previews.

## Build and open

From the Platydoc project root, the directory containing `make_docs.py` and `xnu/`:

```sh
python3 make_docs.py
```

Open `docs-ai-html/index.html` in a browser. The whole output folder can be copied elsewhere and browsed without the checkout. A web server is optional: search and source previews use local classic-script assets and work with `file://` URLs. No CDN, account, analytics service or network connection is needed for reading.

The builder uses Python 3.10 or newer, `cmark-gfm` for GitHub-flavored Markdown, Node.js 20 or newer for the bundled Mermaid parser, and Pygments for syntax highlighting. Chromium can render Mermaid directly where the environment permits; Graphviz supplies the browserless graph layout. Install the Python dependency with:

```sh
python3 -m pip install -r docs-ai/tools/book/requirements.txt
```

Use your platform's package manager for `cmark-gfm`, Node.js, Chromium and Graphviz. The checked-in diagram runtime and license notices make a normal build independent of npm or a CDN. The entry script reports missing build tools before generating the book.

The default `DOCS_DIAGRAM_RENDERER=auto` first tries Chromium. If Chromium is unavailable, it uses the same bundled Mermaid parser with Graphviz for flow/state diagrams and a native SVG sequence renderer. Select `DOCS_DIAGRAM_RENDERER=parsed-svg` to use that backend directly, or `DOCS_DIAGRAM_RENDERER=browser` to require Chromium. `CHROMIUM_PATH` selects a browser executable. Unsupported diagram syntax or fallback constructs fail the build with an error rather than silently dropping a diagram. All 190 current diagrams render with the browserless backend, which was used for this environment's initial build.

The first build highlights referenced source files and renders diagrams. Later builds reuse content-addressed caches in `.docs-cache`. The builder writes to a staging directory and validates the result before replacing the previous successful book. It refuses to overwrite an unmarked, nonempty output directory.

## Reading tools

- Open **Contents** for the complete chapter list; the left sidebar follows the same reading order.
- Press `/` or `Ctrl+K` to search every documentation section, including inline source excerpts and interface catalogs. The search index contains documentation, not every line of the kernel.
- Open **A–Z index** to browse concepts, structures, symbols and interfaces alphabetically. Its filter narrows entries without a server.
- Click a source citation to preview the referenced lines with nearby context and syntax highlighting. Earlier/later controls move through the file; **Open full file** preserves the referenced range. Modified clicks still open the ordinary source link.
- The full-file viewer renders every line, so browser Find, selection and printing work across the file. **Download raw file** recreates its exact original bytes, including tabs, line endings and final-newline state. The chapter's **Markdown source** link opens the same viewer for the editable input.
- Click a diagram to enlarge it. The original Mermaid source remains available below it; the SVG is also a standalone file.
- Use the theme button for light/dark reading and the browser's print command for a print-oriented chapter layout.

## Updating Markdown and source

Edit the Markdown and rebuild. Chapter titles, section outlines, search records, concept occurrences, source references and SVG assets are regenerated automatically. The builder refreshes the Markdown table of contents and source-reference index before conversion, then checks links and exact copied excerpts.

Every handbook Markdown page carries a visible CC BY 4.0 notice for original Platydoc text and diagrams. The build synchronizes these notices before validation, and the standalone catalog/navigation generators preserve them. Check notice coverage without editing files with `python3 docs-ai/tools/doc_license.py --check`.

After updating the XNU checkout or adding interfaces, refresh the source-derived syscall and MIG catalogs as well:

```sh
python3 make_docs.py --refresh-catalogs
```

This reruns the existing BSD syscall, Mach trap and MIG inventory generators. New declarations can require authored purposes/mechanisms in their metadata files; source changes can invalidate copied snippets or line anchors. The generators/checkers deliberately report those gaps. They do not invent updated technical explanations.

The preserved coverage-audit baseline is not regenerated by this option.

Catalog and source-inventory discovery is restricted to `xnu/` through the [shared path definitions](../tools/paths.py). Populating that checkout or initializing its submodule is required before a build; generated books and documentation elsewhere in Platydoc are not source inputs. Keep archives and outputs outside `xnu/`; see the [source-discovery contract](../../AGENTS.md#keep-source-discovery-clean).

To validate an existing generated book without rebuilding:

```sh
python3 make_docs.py --check
```

Additional options select an output directory, a cache directory and the number of source-highlighting workers:

```sh
python3 make_docs.py --output /tmp/xnu-book --cache /tmp/xnu-book-cache --jobs 4
```

## Build components

| File | Responsibility |
| --- | --- |
| [make_docs.py](../../make_docs.py) | Stable command-line entry point. |
| [tools/paths.py](../tools/paths.py) | Shared project, documentation and read-only XNU roots; detects an absent or incomplete source checkout. |
| [tools/doc_license.py](../tools/doc_license.py) | Shared Markdown documentation-license notice, idempotent updates and notice coverage checks. |
| [book/build.py](../tools/book/build.py) | Markdown conversion, chapter ordering, heading preservation, link rewriting, search records, source highlighting/previews, output staging and build manifest. |
| [book/source_codec.py](../tools/book/source_codec.py) | Exact source tokenization, deterministic compression, byte preservation and versioned source cache. |
| [book/concepts.py](../tools/book/concepts.py) | Alphabetical concept/symbol/interface extraction and occurrence links. |
| [book/diagrams.py](../tools/book/diagrams.py) | Diagram rendering, content-addressed cache and renderer selection. |
| [book/verify.py](../tools/book/verify.py) | Generated local links, HTML anchors, assets and SVG verification. |
| [book.css](../tools/book/assets/book.css), [book.js](../tools/book/assets/book.js) | Responsive book layout, themes, search, source/diagram dialogs and reading controls. |
| [build_toc.py](../tools/build_toc.py) | Reading-area and chapter order shared by the Markdown TOC and HTML sidebar. |

Path conventions distinguish evidence from project infrastructure. `PROJECT_ROOT` is the Platydoc directory, `SOURCE_ROOT` is its `xnu/` child, and `DOCS` is `docs-ai/`. Kernel paths in inventory records and implementation-location metadata remain XNU-relative (`osfmk/...`); Markdown destinations and generated source-record paths are project-relative where appropriate (`xnu/osfmk/...`). Embedded Markdown links in authored catalog text resolve from the generated chapter, just like links in ordinary Markdown.

The generated `build-manifest.json` records input/tool content hashes, diagram renderers, the highlighter version and artifact counts. `build-info.html` describes the build's scope and links to source/build-tool license notices. Generated HTML and caches should not be edited manually; rebuild them from Markdown and the book tools.

## Documentation license

Original Platydoc text and diagrams, including the Markdown and generated HTML, are licensed under [Creative Commons Attribution 4.0 International](../../LICENSE-DOCS) (`CC-BY-4.0`). Credit Platydoc and its contributors, link the license and indicate changes when reusing this material. The build tools and browser software remain under [GNU GPL version 2](../../LICENSE) (`GPL-2.0-only`).

Every HTML page displays this distinction in its footer. Both project license texts are included as plain-text files for offline reading and linked from the build-information page. The Markdown notice is omitted from rendered chapter/search content to avoid duplication with the HTML footer; the downloadable Markdown retains it.

XNU, reproduced source excerpts and third-party dependencies retain their respective licenses and notices. A source-view page's documentation footer does not change the license of the displayed source. The book includes `xnu/APPLE_LICENSE`, preserves full-file source headers and retains the bundled dependency notices.

## Compact static storage

The output keeps one compressed token record for each referenced file. Both the popup and the full-file viewer consume that record; there are no duplicate raw source downloads or full highlighted HTML copies. Pygments selects the syntax classes during the build. The browser creates text nodes and styled spans from those tokens, without interpreting source text as HTML.

Each `assets/sources/*.js` file assigns a JSON envelope to `window.XNU_SOURCES[path]`. The envelope has `schema: 2`, `encoding: "gzip-base64"` and a `data` field containing gzip-compressed UTF-8 JSON encoded as base64. Its decoded record contains:

| Field | Meaning |
| --- | --- |
| `path`, `url` | Platydoc-project-relative file path (for example `xnu/osfmk/kern/thread.c` or `docs-ai/README.md`) and book-root-relative source viewer URL. |
| `styles`, `tokens` | Pygments CSS class table and ordered `[class_index, exact_text]` runs. Concatenating the run text reconstructs the file's decoded text. |
| `line_count`, `aliases` | Physical line count and Markdown heading-to-line map. CRLF, CR and LF are line separators; a terminal newline does not create an extra line. |
| `sha256` | Hash of the original file bytes. |
| `raw_base64` | Present only when invalid UTF-8 prevents an exact text-to-byte round trip; it preserves the original download bytes. |

The small `_sources/<path>.html` pages retain stable file and line URLs. Their browser code loads the shared record, adds line anchors and heading aliases, and renders the complete file in batches. JavaScript is required for source viewing/downloads, search and the alphabetical index. Authored chapters, the complete contents and SVG diagrams remain directly readable without it.

Search records and the complete alphabetical index use the same lossless gzip/base64 envelope in `assets/search-index.js` and `assets/concept-index.js`. The chapter sidebar is stored once in `assets/navigation.js`. All are local classic scripts: this also works when the static book is hosted below a path such as `/xnu-handbook/`. No server decompression, HTTP rewrite rules or build-time URL prefix is needed. Browsers use `DecompressionStream` when available and the bundled JavaScript decoder otherwise.

`source-records.json` maps viewer URLs to their paths, payload filenames, original-byte hashes, payload-file hashes, line counts and heading aliases. The verifier decodes each payload, checks its reconstructed bytes and line map, and validates source citations against that map. It also decodes the search/index data to check their destinations; compression does not exempt these links from validation.

Original Markdown and complete license notices use this same source viewer and exact-byte download path. Project licenses also have small plain-text copies under `licenses/` for reading without JavaScript. Compression changes storage, not their contents. `_downloads/` is reserved for linked binary assets such as images or PDFs.

The source cache is `.docs-cache/source-codec/`, keyed by file content, basename, Pygments version and `source_codec.py`'s `CODEC_VERSION`. Bump that version when changing tokenization or record semantics. The obsolete `.docs-cache/highlight/` directory from older builds may be removed after a successful compact build; retain the cached SVG files elsewhere in `.docs-cache/` to reuse rendered diagrams. Do not copy caches or vendored build tools to a static host—only the generated output directory is needed.

## Verification limits

The build validates original Markdown links/excerpts and generated local links, heading/source anchors, local assets and SVG structure. Catalog reconciliation remains separate from runtime behavior. Static checks do not establish that every explanation is correct or replace browser interaction checks, source review, or kernel testing.

Run the generator and browser-logic regression checks with:

```sh
python3 -B -m unittest discover -s docs-ai/tools/book/tests -v
node docs-ai/tools/book/tests/assets.test.mjs
```

These include source ranges and Markdown heading previews, exact token/download byte preservation, compressed payload integrity, both gzip decoding paths, concept destinations, invalid links/SVGs, search matching/pagination and bounded preview context. The JavaScript tests execute the implementation helpers with a small DOM fixture; they do not substitute for a visual browser check.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
