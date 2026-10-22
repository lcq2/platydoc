# Local preparation and Pages publishing

There are two flows.

**Local preparation:** edit the handbook, add structures, generate their layout
artifacts with the local native LLVM compiler, and run the relevant checks.
Build the handbook locally with `python3 make_docs.py`, then export its prepared
layouts, headers, compiled Wasm runtime and notices:

```sh
python3 docs-ai/tools/layouts/prepared.py export --book docs-ai-html --output runtime/prepared-layouts.tar.gz
```

Include that archive with the changes you push. Refresh it when the structure
catalog, layout UI, compiler or bundled inputs change. Ordinary prose edits do
not require rebuilding LLVM. The supplied archive contains completed layout
outputs and browser assets; it contains no native executable, LLVM source tree,
Emscripten SDK or compiler build directory.

**Pages publishing:** Actions consumes the prepared archive, renders the HTML
handbook and offline ZIP, and publishes them. It runs:

```sh
python make_docs.py --prepared-layouts runtime/prepared-layouts.tar.gz --publish-only
```

Actions does not build or run a layout compiler, regenerate structure layouts,
run tests, compare native/Wasm results or perform validation. All validation
belongs to local preparation before pushing. Node is installed for diagram
rendering, not for compiling layouts. The published browser uses the supplied
Wasm compiler for interactive layout calculations, including flag changes.

The existing local compiler and comparison tools remain available for offline
maintenance. Pages does not invoke them. `--publish-only` is the rendering and
publication path; ordinary local builds keep their existing validation.

Build software uses GPL-2.0-only ([LICENSE](../LICENSE)); this explanation uses
CC BY 4.0 ([LICENSE-DOCS](../LICENSE-DOCS)). Compiler and runtime assets retain
their upstream notices.
