# Local preparation and Pages publishing

There are two flows. All compilation and validation stay local. Pages downloads
our prepared output, renders the HTML handbook/offline ZIP and publishes them.
The browser uses the supplied Wasm compiler for interactive layouts.

## One-time migration to release assets

Install GitHub CLI through your package manager (`sudo pacman -S --needed github-cli`
on Arch), then authenticate locally. Upload the existing prepared archive before
removing it from Git tracking:

```sh
gh auth login
python3 docs-ai/tools/layouts/prepared.py publish \
  --archive runtime/prepared-layouts.tar.gz --repo lcq2/platydoc
git rm --cached -- runtime/prepared-layouts.tar.gz runtime/prepared-layouts.tar.json
git add -- .gitignore .github docs-ai runtime/prepared-layouts.release.json
git commit -m "Store prepared layout assets in GitHub Releases"
git push origin main
```

`publish` writes `runtime/prepared-layouts.release.json` only after the upload
succeeds. It does not commit, push, stage files or rewrite history. Stop if the
upload fails; do not commit the new workflow without its release reference.
The archive remains on disk after `git rm --cached`, and is ignored thereafter.
The old pushed copy remains in Git history; these commands prevent future growth
without rewriting that history.

## Normal local preparation

After editing pages or adding structures, use the existing local preparation
workflow to regenerate layouts as needed. Build/validate locally, then export
and upload in one command:

```sh
DOCS_DIAGRAM_RENDERER=parsed-svg python3 make_docs.py
python3 docs-ai/tools/layouts/prepared.py publish --book docs-ai-html --repo lcq2/platydoc
git add -- docs-ai runtime/prepared-layouts.release.json
git commit -m "Update handbook and prepared layouts"
git push origin main
```

The archive is exported under `.docs-cache/layouts/`. Its content hash identifies
a versioned release; unchanged content reuses that release and existing assets
are not overwritten. Only the small release reference enters Git. Refresh the
prepared assets when structures, layout UI, compiler or bundled inputs change;
ordinary prose edits can reuse the existing release reference.

The upload uses [GitHub CLI releases](https://cli.github.com/manual/gh_release_create).
Authentication remains in your local GitHub CLI configuration; no token enters
Git. Use your own `owner/repo` in `--repo` for a fork.

## Pages publication

Actions downloads the exact release asset identified by the committed reference
using its read-only repository token, then runs:

```sh
python docs-ai/tools/layouts/prepared.py download \
  --reference runtime/prepared-layouts.release.json \
  --output .docs-cache/layouts/prepared-layouts.tar.gz
python make_docs.py --prepared-layouts .docs-cache/layouts/prepared-layouts.tar.gz --publish-only
```

Actions does not build/run a layout compiler, generate structure layouts, run
tests, compare native/Wasm outputs or perform validation. Node is only used for
diagram rendering. Default local builds retain their preparation and validation.
The reference must point to a release asset accessible to the workflow token;
for forks, upload the archive to that fork before publishing.

Build software uses GPL-2.0-only ([LICENSE](../LICENSE)); this explanation uses
CC BY 4.0 ([LICENSE-DOCS](../LICENSE-DOCS)). Compiler and runtime assets retain
their upstream notices.
