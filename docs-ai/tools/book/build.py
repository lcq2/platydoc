"""Convert the Markdown handbook to a self-contained technical book."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import html
from html.parser import HTMLParser
import json
import multiprocessing
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import quote, unquote, urlsplit
import xml.etree.ElementTree as ET

from build_toc import GROUPS
from check_links import DOCS, ROOT, prose_lines
from doc_license import LICENSE_URL, handbook_paths, strip_license_notice, sync_notices
from paths import SOURCE_ROOT, require_source
from .offline import (
    ARCHIVE_NAME, ARCHIVE_ROOT, DOWNLOAD_PAGE, DOWNLOAD_START, DOWNLOAD_END,
    HEADER_START, HEADER_END, HEADER_LABEL, create_archive,
)

HERE = Path(__file__).resolve().parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def log(message):
    print(message, flush=True)


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def relative(url, current):
    """Root-relative book URL -> link relative to the current HTML file."""
    return os.path.relpath(url, str(Path(current).parent)).replace(os.sep, "/")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def packed_json(value):
    """Lossless classic-script data: usable on file:// without a fetch request."""
    from .source_codec import pack
    return pack(value)


def script_data(path, name, value, *, compress=True):
    write(path, f"window.{name}=" + json.dumps(
        packed_json(value) if compress else value, ensure_ascii=False,
        separators=(",", ":")) + ";\n")


class Node:
    def __init__(self, tag="", attrs=None, children=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), children or []

    def text(self):
        return "".join(c.text() if isinstance(c, Node) else str(c)
                       for c in self.children)

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def render(self):
        content = "".join(c.render() if isinstance(c, Node) else
                          html.escape(str(c), quote=False) for c in self.children)
        if not self.tag:
            return content
        attrs = "".join(f' {k}="{html.escape(str(v), quote=True)}"'
                        for k, v in self.attrs.items() if v is not None)
        return f"<{self.tag}{attrs}>" + ("" if self.tag in VOID
                                       else content + f"</{self.tag}>")


class Raw(Node):
    def __init__(self, content):
        super().__init__()
        self.content = content

    def render(self):
        return self.content

    def text(self):
        return ""


class DOM(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def markdown(source):
    result = subprocess.run(
        ["cmark-gfm", "--unsafe", "--extension", "table", "--extension",
         "strikethrough", "--extension", "autolink", "--extension", "tasklist"],
        input=source, text=True, capture_output=True, timeout=20, check=True)
    return DOM(result.stdout).root


def source_headings(path):
    seen = Counter()
    rows = []
    for line_number, line in prose_lines(path):
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", match[2])
        title = re.sub(r"<[^>]*>", "", title)
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        n = seen[slug]
        seen[slug] += 1
        rows.append({"id": f"{slug}-{n}" if n else slug,
                     "title": title.replace("`", ""), "level": len(match[1]),
                     "line": line_number, "text": ""})
    return rows


def collect_pages():
    paths = set(DOCS.rglob("*.md"))
    ordered = []
    assigned = set()
    for part, (label, directory, preferred) in enumerate(GROUPS, 1):
        rank = {name: i for i, name in enumerate(preferred)}
        group = sorted((p for p in paths if p.parent == DOCS / directory),
                       key=lambda p: (rank.get(p.stem, len(rank)), p.name))
        for number, path in enumerate(group, 1):
            rel = path.relative_to(DOCS).as_posix()
            url = "index.html" if rel == "README.md" else str(Path(rel).with_suffix(".html"))
            sections = source_headings(path)
            if not sections or sections[0]["level"] != 1:
                raise ValueError(f"Missing title: {rel}")
            ordered.append({"path": rel, "file": path, "url": url,
                            "title": sections[0]["title"], "chapter": label,
                            "part": part, "number": f"{part:02d}.{number:02d}",
                            "sections": sections, "markdown": path.read_text()})
            assigned.add(path)
    if paths != assigned:
        raise ValueError("Unclassified Markdown pages: " +
                         ", ".join(str(p) for p in paths-assigned))
    return ordered


def highlight_code(code, language="", filename=None, trim=True):
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, TextLexer
    from pygments.util import ClassNotFound
    try:
        lexer = (get_lexer_for_filename(filename, stripnl=False, ensurenl=False)
                 if filename else get_lexer_by_name(language or "text",
                                                   stripnl=False, ensurenl=False))
    except ClassNotFound:
        lexer = TextLexer(stripnl=False, ensurenl=False)
    result = highlight(code, lexer, HtmlFormatter(nowrap=True))
    return result.rstrip("\n") if trim else result


def nav_html(pages, current):
    return (f'<div class="nav-fallback"><a href="{relative("table-of-contents.html", current)}">'
            'Complete table of contents</a></div>')


def nav_data(pages):
    groups = defaultdict(list)
    for p in pages:
        groups[(p["part"], p["chapter"])].append(p)
    return [{"part": part, "title": title,
             "pages": [{key: p[key] for key in ("url", "title", "number")} for p in group]}
            for (part, title), group in groups.items()]


def shell(title, content, current, *, nav="", toc="", chapter="", breadcrumb="",
          page_navigation="", body_class="", body_attrs=None):
    prefix = relative("assets", current).removesuffix("assets")
    if not prefix:
        prefix = "./"
    e = html.escape
    attributes = "".join(f' {key}="{e(str(value),quote=True)}"'
                         for key, value in (body_attrs or {}).items())
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(title)} · XNU Source Handbook</title>
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/book.css">
<link rel="stylesheet" href="{prefix}assets/highlight.css">
<script src="{prefix}assets/navigation.js" defer></script>
<script src="{prefix}assets/book.js" defer></script>
</head>
<body class="{body_class}" data-root="{prefix}" data-page="{e(current,quote=True)}"
 data-search-index="{prefix}assets/search-index.js"{attributes}>
<a class="skip-link" href="#main">Skip to content</a>
<header class="book-header">
 <button id="menu-toggle" type="button" aria-label="Toggle chapter navigation" aria-controls="chapter-nav" aria-expanded="false">☰</button>
 <a class="book-brand" href="{prefix}index.html"><span class="brand-mark">X</span><span>XNU <strong>Source Handbook</strong></span></a>
 <nav class="header-links" aria-label="Book tools"><a href="{prefix}table-of-contents.html">Contents</a><a href="{prefix}concept-index.html">A–Z index</a></nav>
 <button id="search-open" type="button" aria-label="Search the handbook">Search <kbd>/</kbd></button>
 <button id="theme-toggle" type="button" aria-label="Toggle color theme">◐</button>
 {HEADER_START}<a class="offline-download" href="{prefix}{ARCHIVE_NAME}" download="{ARCHIVE_NAME}">{HEADER_LABEL}</a>{HEADER_END}
</header>
<aside id="chapter-nav" class="chapter-nav" aria-label="Chapters"{" data-shared-nav" if nav else ""}>{nav}</aside>
<main id="main" class="book-main">
 <div class="breadcrumbs">{breadcrumb}</div>
 <div class="chapter-label">{e(chapter)}</div>
 <article id="content">{content}</article>
 <nav class="page-navigation" aria-label="Adjacent chapters">{page_navigation}</nav>
 <footer class="book-footer">
  <p>XNU 12377.121.6 · Source-based technical documentation · <a href="{prefix}build-info.html">Build &amp; provenance</a> · <a href="{prefix}{DOWNLOAD_PAGE}">Offline handbook</a></p>
  <p>Original Platydoc documentation and diagrams: <a href="{LICENSE_URL}" rel="license">CC BY 4.0</a>
  (<a href="{prefix}licenses/CC-BY-4.0.txt">license text</a>). Platydoc software:
  <a href="{prefix}licenses/GPL-2.0.txt">GPLv2</a>. XNU source, quoted code and third-party materials
  retain their original licenses. <a href="{prefix}build-info.html#licenses">License notices</a>.</p>
 </footer>
</main>
<aside id="page-toc" class="page-toc" aria-label="On this page">{toc}</aside>
<dialog id="search-dialog" aria-labelledby="search-heading">
 <div class="dialog-heading"><h2 id="search-heading">Search the handbook</h2><button type="button" data-close-search aria-label="Close search">×</button></div>
 <label class="visually-hidden" for="search-input">Terms, symbols or interfaces</label>
 <input id="search-input" type="search" placeholder="Search pmap_enter, AST, vnode…" autocomplete="off" spellcheck="false">
 <div id="search-status" role="status" aria-live="polite">Search every chapter, interface and code excerpt.</div>
 <ol id="search-results"></ol>
</dialog>
<dialog id="diagram-dialog" aria-labelledby="diagram-caption">
 <div class="dialog-heading"><h2 id="diagram-caption">Diagram</h2><button type="button" data-close-diagram aria-label="Close diagram">×</button></div>
 <img id="diagram-image" alt="">
</dialog>
<dialog id="source-dialog" aria-labelledby="source-title">
 <div class="dialog-heading"><h2 id="source-title">Source preview</h2><button type="button" data-close-source aria-label="Close source preview">×</button></div>
 <div class="source-toolbar"><span id="source-meta"></span><a id="source-full-link" href="{prefix}source-index.html">Open full file</a>
 <button id="source-prev" type="button">Earlier lines</button><button id="source-next" type="button">Later lines</button></div>
 <div id="source-code" class="source-preview-code" tabindex="0"></div>
</dialog>
</body></html>
"""


def download_page(pages):
    content = (
        '<h1 id="download">Download the offline handbook</h1>'
        '<p>Take the complete HTML handbook with you: every chapter, search, the A–Z index, '
        'SVG diagrams, cited source files, Markdown sources and license notices.</p>'
        f'{DOWNLOAD_START}\n'
        f'<p><a class="start-reading" href="{ARCHIVE_NAME}" download="{ARCHIVE_NAME}">Download ZIP</a></p>'
        '<ol><li>Download and extract the ZIP file completely.</li>'
        f'<li>Open <code>{ARCHIVE_ROOT}/index.html</code> in your browser.</li>'
        '<li>Keep the extracted folder together so its links and reading tools continue to work.</li></ol>\n'
        f'{DOWNLOAD_END}'
        '<p>No web server, installation or network connection is needed. '
        'Enable JavaScript for search, the A–Z index and source previews/downloads. '
        'Chapters and diagrams can also be read without JavaScript.</p>'
        '<p><a href="index.html">Read the handbook</a> · '
        '<a href="build-info.html#licenses">Licenses and attribution</a></p>'
    )
    return shell("Offline handbook", content, DOWNLOAD_PAGE,
                 nav=nav_html(pages, DOWNLOAD_PAGE), chapter="OFFLINE READING",
                 breadcrumb='<a href="index.html">Handbook</a> / Offline reading')


class Book:
    def __init__(self, pages, output, cache):
        self.pages, self.output, self.cache = pages, output, cache
        self.by_path = {p["file"].resolve(): p for p in pages}
        self.sources = {}
        self.downloads = set()
        self.directories = set()
        self.diagrams = {}
        self.search = []

    def source_record(self, target, page):
        rel = target.relative_to(ROOT).as_posix()
        if rel not in self.sources:
            self.sources[rel] = {"path": rel, "file": target,
                                 "url": "_sources/" + rel + ".html",
                                 "payload": "assets/sources/" + digest(rel)[:24] + ".js",
                                 "backlinks": {}}
        self.sources[rel]["backlinks"][page["url"]] = page["title"]
        return self.sources[rel]

    def convert_link(self, node, page):
        attribute = "src" if node.tag == "img" else "href"
        raw = node.attrs.get(attribute, "")
        url = urlsplit(raw)
        if url.scheme or url.netloc:
            if url.scheme.lower() in {"javascript", "data"}:
                raise ValueError(f"Unsafe authored URL in {page['path']}: {raw}")
            return
        if not url.path:
            return
        target = (page["file"].parent / unquote(url.path)).resolve()
        if not target.is_relative_to(ROOT) or not target.exists():
            raise ValueError(f"Invalid local target in {page['path']}: {raw}")
        fragment = ("#" + url.fragment) if url.fragment else ""
        if target in self.by_path:
            dest = self.by_path[target]["url"]
        elif target.is_dir():
            rel = target.relative_to(ROOT).as_posix()
            dest = "_directories/" + (rel if rel != "." else "root") + ".html"
            self.directories.add(target)
        elif target.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf"}:
            dest = "_downloads/" + target.relative_to(ROOT).as_posix()
            self.downloads.add(target)
        else:
            record = self.source_record(target, page)
            dest = record["url"]
            line = re.fullmatch(r"L(\d+)(?:-L(\d+))?", unquote(url.fragment))
            start = int(line[1]) if line else 1
            end = int(line[2] or start) if line else 30
            if not line and url.fragment and target.suffix == ".md":
                headings = source_headings(target)
                for index, heading in enumerate(headings):
                    if heading["id"] == unquote(url.fragment):
                        start = heading["line"]
                        following = (headings[index+1]["line"]-1 if index+1 < len(headings)
                                     else len(target.read_text().splitlines()))
                        end = min(start+29, following)
                        break
            node.attrs.update({"class": (node.attrs.get("class", "") + " source-link").strip(),
                               "data-source": record["path"], "data-start": str(start),
                               "data-end": str(end), "data-source-payload": record["payload"],
                               "title": f"Preview {record['path']}, line {start}"})
        node.attrs[attribute] = relative(dest, page["url"]) + (("?" + url.query) if url.query else "") + fragment

    def prepare(self):
        for page in self.pages:
            # Every Markdown download carries its own notice. The shared footer
            # presents that notice once in HTML, outside chapter/search content.
            dom = markdown(strip_license_notice(page["markdown"]))
            heading_nodes = [n for n in dom.walk() if re.fullmatch(r"h[1-6]", n.tag)]
            if len(heading_nodes) != len(page["sections"]):
                raise ValueError(f"Heading parser mismatch: {page['path']}")
            for node, heading in zip(heading_nodes, page["sections"]):
                node.attrs["id"] = heading["id"]
                heading["title"] = node.text()
            for node in list(dom.walk()):
                if node.tag in {"a", "img"}:
                    self.convert_link(node, page)
            # Section records include prose, tables and code, preserving every term.
            section = page["sections"][0]
            collected = []
            for child in dom.children:
                if isinstance(child, Node) and re.fullmatch(r"h[1-6]", child.tag):
                    if collected:
                        section["text"] = "\n".join(collected)
                    section = next(s for s in page["sections"] if s["id"] == child.attrs["id"])
                    collected = []
                else:
                    text = child.text() if isinstance(child, Node) else str(child)
                    collected.append(text)
            section["text"] = "\n".join(collected)
            for s in page["sections"]:
                content = s["text"].strip()
                chunks = [content[i:i+12000] for i in range(0, max(1, len(content)), 11700)]
                for chunk in chunks:
                    self.search.append({"title": page["title"], "chapter": page["chapter"],
                                        "heading": s["title"],
                                        "url": page["url"] + "#" + s["id"], "text": chunk})
            for node in dom.walk():
                if node.tag != "pre" or not node.children:
                    continue
                code = node.children[0]
                if not isinstance(code, Node) or code.tag != "code":
                    continue
                language = code.attrs.get("class", "").removeprefix("language-")
                if language == "mermaid":
                    source = code.text()
                    key = digest(source)
                    self.diagrams.setdefault(key, {"key": key, "source": source,
                                                   "label": f"{page['title']} diagram"})
                    node.attrs["data-diagram-key"] = key
                else:
                    node.attrs["class"] = "code-block"
                    node.attrs["data-language"] = language or "text"
                    code.children = [Raw(highlight_code(code.text(), language))]
            page["dom"] = dom

    def render_chapters(self, svg_paths):
        for i, page in enumerate(self.pages):
            for node in list(page["dom"].walk()):
                key = node.attrs.get("data-diagram-key")
                if not key:
                    continue
                url = relative(svg_paths[key], page["url"])
                src = html.escape(self.diagrams[key]["source"])
                label = html.escape(self.diagrams[key]["label"], quote=True)
                node.tag = "figure"
                node.attrs = {"class": "diagram"}
                node.children = [Raw(f'<a class="diagram-link" href="{url}" title="Enlarge diagram">'
                    f'<img src="{url}" alt="{label}" loading="lazy"></a>'
                    f'<figcaption>{label} · <a href="{url}">Open SVG</a></figcaption>'
                    f'<details class="diagram-source"><summary>Mermaid source</summary>'
                    f'<pre><code class="language-mermaid">{src}</code></pre></details>')]
            sections = [s for s in page["sections"] if 2 <= s["level"] <= 3]
            toc = "<h2>On this page</h2><ol>" + "".join(
                f'<li class="toc-level-{s["level"]}"><a href="#{s["id"]}">'
                f'{html.escape(s["title"])}</a></li>' for s in sections) + "</ol>"
            adjacent = []
            for index, label in ((i-1, "Previous"), (i+1, "Next")):
                if 0 <= index < len(self.pages):
                    other = self.pages[index]
                    adjacent.append(f'<a class="page-{label.lower()}" href="{relative(other["url"],page["url"])}">'
                                    f'<span>{label}</span><strong>{html.escape(other["title"])}</strong></a>')
            authored = self.source_record(page["file"], page)
            raw = relative(authored["url"], page["url"])
            breadcrumb = f'<a href="{relative("index.html",page["url"])}">Handbook</a> / ' + html.escape(page["chapter"])
            breadcrumb += f' <a class="markdown-link" href="{raw}">Markdown source</a>'
            lead = ""
            if page["path"] == "README.md":
                lead = (f'<section class="book-intro"><p class="eyebrow">SOURCE EDITION · 12377.121.6</p>'
                        f'<p class="book-deck">Read the kernel as a connected system.</p>'
                        f'<div class="book-stats"><span><strong>{len(self.pages)}</strong> chapters &amp; guides</span>'
                        f'<span><strong>{len(self.diagrams)}</strong> SVG diagrams</span>'
                        f'<span><strong>Offline</strong> search &amp; source previews</span></div>'
                        f'<a class="start-reading" href="architecture.html">Start with the architecture →</a> '
                        f'<a href="concept-index.html">Browse the A–Z index</a> '
                        f'<a href="{DOWNLOAD_PAGE}">Download offline ZIP</a></section>')
            content = lead + page["dom"].render()
            write(self.output/page["url"], shell(page["title"], content, page["url"],
                nav=nav_html(self.pages,page["url"]), toc=toc,
                chapter=f'Part {page["part"]:02d} · Chapter {page["number"]}',
                breadcrumb=breadcrumb, page_navigation="".join(adjacent)))

    def render_indexes(self):
        from .concepts import build_concept_index
        terms = build_concept_index([
            dict(page, markdown=strip_license_notice(page["markdown"]))
            for page in self.pages])
        letters = defaultdict(list)
        for term in terms:
            initial = term["term"].lstrip("_")[0].upper()
            letters[initial if initial in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "#"].append(term)
        alphabet = "".join(f'<a href="#letter-{letter if letter != "#" else "other"}">{letter}</a>'
                           for letter in ["#"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") if letter in letters)
        blocks = [f'<h1 id="concept-index">Concept and symbol index</h1>'
                  f'<p>{len(terms):,} concepts, structures, symbols and interfaces. '
                  f'Entries link to the sections where they are explained or used.</p>'
                  '<label for="index-filter">Filter the index</label>'
                  '<input id="index-filter" type="search" placeholder="Type a concept or symbol…" autocomplete="off">'
                  f'<nav class="alphabet-nav" aria-label="Index letters">{alphabet}</nav>']
        for letter in ["#"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            if letter not in letters:
                continue
            anchor = "other" if letter == "#" else letter
            blocks.append(f'<section class="index-group"><h2 id="letter-{anchor}">{letter}</h2><dl>')
            for term in letters[letter]:
                blocks.append(f'<div class="index-entry" data-term="{html.escape(term["term"],quote=True)}">'
                              f'<dt>{html.escape(term["term"])} <span class="index-kind">{term["kind"]}</span></dt><dd>')
                for occurrence, entry in enumerate(term["entries"]):
                    if occurrence == 4:
                        blocks.append(f'<details><summary>{len(term["entries"])-4} more references</summary>')
                    label = entry["title"]
                    if entry.get("heading") and entry["heading"] != label:
                        label += " — " + entry["heading"]
                    blocks.append(f'<a href="{html.escape(entry["url"],quote=True)}">{html.escape(label)}</a>')
                if len(term["entries"]) > 4:
                    blocks.append("</details>")
                blocks.append("</dd></div>")
            blocks.append("</dl></section>")
        script_data(self.output/"assets"/"concept-index.js", "XNU_CONCEPT_INDEX", "".join(blocks))
        content = ('<div id="concept-content" data-index-payload="assets/concept-index.js">'
                   '<h1>Concept and symbol index</h1><p>Loading the alphabetical index…</p>'
                   '<noscript><p>The searchable index requires JavaScript. Browse the '
                   '<a href="glossary.html">glossary</a> or '
                   '<a href="source-index.html">source-reference index</a>.</p></noscript></div>')
        write(self.output/"concept-index.html", shell("Concept and symbol index",
              content, "concept-index.html", nav=nav_html(self.pages,"concept-index.html"),
              chapter="REFERENCE · ALPHABETICAL INDEX", body_class="index-page"))
        return len(terms)

    def render_sources(self, jobs):
        records = list(self.sources.values())
        log(f"Preparing {len(records)} source files and highlighted previews…")
        work = [(r, str(self.output), str(self.cache)) for r in records]
        count = 0
        source_records = {}
        # Bounded worker pool; each external dependency has its own timeout.
        # fork avoids the forkserver's local socket on restricted POSIX hosts.
        context = multiprocessing.get_context("fork" if os.name == "posix" else "spawn")
        pool = ProcessPoolExecutor(max_workers=jobs, mp_context=context)
        try:
            futures = [pool.submit(render_source, item) for item in work]
            last = time.monotonic()
            for future in as_completed(futures, timeout=300):
                result = future.result()
                source_records[result.pop("url")] = result
                count += 1
                if count % 100 == 0 or time.monotonic()-last > 15:
                    log(f"  Sources: {count}/{len(records)}")
                    last = time.monotonic()
        except BaseException:
            # A timeout must stop the workers, not wait indefinitely in __exit__.
            workers = list(pool._processes.values())
            for worker in workers:
                worker.terminate()
            pool.shutdown(wait=False, cancel_futures=True)
            for worker in workers:
                worker.join(timeout=2)
                if worker.is_alive():
                    worker.kill()
            raise
        else:
            pool.shutdown()
        write(self.output/"source-records.json", json.dumps(
            dict(sorted(source_records.items())), ensure_ascii=False, separators=(",", ":")) + "\n")
        for directory in sorted(self.directories):
            rel = directory.relative_to(ROOT).as_posix()
            current = "_directories/" + (rel if rel != "." else "root") + ".html"
            records = [r for r in self.sources.values() if r["file"].is_relative_to(directory)]
            items = "".join(f'<li><a href="{relative(r["url"],current)}">{html.escape(r["path"])}</a></li>'
                            for r in sorted(records, key=lambda r:r["path"]))
            content = f'<h1 id="directory">{html.escape(rel)}/</h1><p>Files referenced by this handbook.</p><ul>{items}</ul>'
            write(self.output/current, shell(rel + "/",content,current, chapter="SOURCE DIRECTORY"))

    def copy_downloads(self):
        for path in sorted(self.downloads):
            dest = self.output/"_downloads"/path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path,dest)


def render_source(work):
    from .source_codec import encode_source
    record, output, cache = work
    output, cache = Path(output), Path(cache)
    target = Path(record["file"])
    current = record["url"]
    aliases = {h["id"]: h["line"] for h in source_headings(target)} if target.suffix == ".md" else {}
    payload = encode_source(target, cache)
    payload.update({"path": record["path"], "url": current, "aliases": aliases})
    packed = "window.XNU_SOURCES=window.XNU_SOURCES||{};\n"
    packed += f"window.XNU_SOURCES[{json.dumps(record['path'])}]={json.dumps(packed_json(payload), separators=(',', ':'))};\n"
    write(output/record["payload"], packed)
    backlinks = "".join(f'<li><a href="{relative(url,current)}">{html.escape(title)}</a></li>'
                        for url,title in record["backlinks"].items())
    attrs = (f'data-source="{html.escape(record["path"],quote=True)}" '
             f'data-source-payload="{record["payload"]}"')
    content = (f'<h1 id="source-file">{html.escape(record["path"])}</h1>'
               f'<p class="source-info">{payload["line_count"]:,} lines · '
               f'<button type="button" class="source-download" {attrs}>Download raw file</button> · '
               f'<a href="{relative("source-index.html",current)}">Source index</a></p>'
               f'<details class="source-backlinks"><summary>Referenced in {len(record["backlinks"])} chapters</summary>'
               f'<ul>{backlinks}</ul></details><p id="source-load-status" role="status">Loading source…</p>'
               f'<noscript><p>The source viewer and download controls require JavaScript.</p></noscript>'
               f'<pre class="source-code" data-source-full {attrs}><code></code></pre>')
    write(output/current,shell(record["path"],content,current,
        chapter="SOURCE REFERENCE",body_class="source-page",
        body_attrs={"data-source-path": record["path"], "data-source-payload": record["payload"]}))
    return {"url": current, "path": record["path"], "payload": record["payload"],
            "sha256": payload["sha256"], "payload_sha256": digest(packed),
            "line_count": payload["line_count"], "aliases": aliases}


def register_license_notices(book):
    """Keep project licenses readable offline and preserve upstream notices."""
    project = {"CC-BY-4.0.txt": ROOT/"LICENSE-DOCS",
               "GPL-2.0.txt": ROOT/"LICENSE"}
    notices = dict(project)
    notices["APPLE_LICENSE.txt"] = SOURCE_ROOT/"APPLE_LICENSE"
    for name in ("LICENSE.txt", "THIRD_PARTY_NOTICES.txt", "PROVENANCE.txt"):
        notices["mermaid-" + name] = HERE/"vendor"/"mermaid"/name
    for name, path in project.items():
        destination = book.output/"licenses"/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        # These plain-text copies also work without the JavaScript source viewer.
        shutil.copyfile(path, destination)
    return {name: book.source_record(path, {
        "url": "build-info.html", "title": "Build and provenance"})["url"]
        for name, path in notices.items()}


def check_dependencies():
    missing = [name for name in ("cmark-gfm","node") if not shutil.which(name)]
    if not shutil.which(os.environ.get("CHROMIUM_PATH", "chromium")) and not shutil.which("dot"):
        missing.append("Chromium or Graphviz (dot) for SVG rendering")
    try:
        import pygments
    except ImportError:
        missing.append("Pygments (python3 -m pip install -r docs-ai/tools/book/requirements.txt)")
    if missing:
        raise RuntimeError("Missing documentation build tools: " + ", ".join(missing))


def run_tool(name, timeout=60, args=()):
    subprocess.run([sys.executable,str(DOCS/"tools"/name),*args],
                   cwd=ROOT,check=True,timeout=timeout)


def validate_output_paths(output, cache):
    """Keep generated files outside the read-only XNU input and authored docs."""
    if output == ROOT or output.is_relative_to(DOCS) or ROOT.is_relative_to(output):
        raise ValueError("--output must be a dedicated directory outside docs-ai and not an ancestor of the project")
    if output.is_relative_to(SOURCE_ROOT.resolve()) or cache.is_relative_to(SOURCE_ROOT.resolve()):
        raise ValueError("--output and --cache must be outside the read-only xnu source tree")
    if cache.is_relative_to(output) or output.is_relative_to(cache) or cache.is_relative_to(DOCS):
        raise ValueError("--cache must be separate from the output and Markdown source directories")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"docs-ai-html",
                        help="Generated book directory (default: docs-ai-html)")
    parser.add_argument("--cache",type=Path,default=ROOT/".docs-cache",
                        help="Reusable diagram and source-highlighting cache")
    parser.add_argument("--refresh-catalogs",action="store_true",
                        help="Re-extract syscall/trap/MIG catalogs before building")
    parser.add_argument("--jobs",type=int,default=min(4,os.cpu_count() or 1),
                        help="Source-highlighting workers (default: up to 4)")
    parser.add_argument("--check",action="store_true",
                        help="Validate an already generated book without rebuilding")
    parser.add_argument("--layout-runtime", type=Path, default=ROOT/".docs-cache/layouts/structure-runtime",
                        help="Provisioned pinned offline layout runtime (never downloaded by book generation)")
    parser.add_argument("--layout-native", type=Path, default=ROOT/".docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine",
                        help="Provisioned pinned native layout frontend")
    parser.add_argument("--layout-configs", type=Path, default=ROOT/".docs-cache/layouts/milestone8-configs",
                        help="Generated XNU configuration files matching the pinned runtime provenance")
    args = parser.parse_args()
    output,cache = args.output.resolve(),args.cache.resolve()
    if args.check:
        missing = sync_notices(handbook_paths(), check=True)
        if missing:
            parser.error(f"{len(missing)} Markdown files have missing or stale license notices; rebuild the book")
        from .verify import verify_generated
        log(json.dumps(verify_generated(output),indent=2))
        return 0
    try:
        validate_output_paths(output, cache)
    except ValueError as error:
        parser.error(str(error))
    if not 1<=args.jobs<=32:
        parser.error("--jobs must be between 1 and 32")
    marker = output/".xnu-book"
    if output.exists() and any(output.iterdir()) and not marker.exists():
        parser.error("Refusing to replace an unmarked, nonempty output directory")
    require_source()
    check_dependencies()
    from layouts.catalog import provisioned as check_layout_inputs
    check_layout_inputs(args.layout_runtime.resolve(), args.layout_native.resolve(), args.layout_configs.resolve())
    started=time.monotonic()
    if args.refresh_catalogs:
        log("Refreshing declaration catalogs against local XNU source…")
        run_tool("build_bsd_syscall_catalog.py")
        run_tool("build_mach_trap_catalog.py")
        run_tool("build_mig_catalog.py",timeout=120)
    log("Refreshing navigation and checking Markdown/source excerpts…")
    run_tool("build_toc.py")
    run_tool("build_source_index.py")
    updated = sync_notices(handbook_paths())
    if updated:
        log(f"Updated CC BY 4.0 notices in {len(updated)} Markdown files.")
    run_tool("check_links.py")
    pages=collect_pages()
    # A staging directory prevents a failed build from destroying the last book.
    staging=output.with_name(output.name+".building")
    if staging.exists():
        if not (staging/".xnu-book").exists():
            raise RuntimeError(f"Unmarked build directory exists: {staging}")
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    write(staging/".xnu-book","Generated by make_docs.py\n")
    cache.mkdir(parents=True,exist_ok=True)
    book=Book(pages,staging,cache)
    log(f"Converting {len(pages)} Markdown chapters…")
    book.prepare()
    from .diagrams import render_diagrams
    log(f"Rendering {len(book.diagrams)} SVG diagrams…")
    svg_paths=render_diagrams(list(book.diagrams.values()),staging,cache,strict=True)
    shutil.copytree(HERE/"assets",staging/"assets",dirs_exist_ok=True)
    script_data(staging/"assets"/"navigation.js", "XNU_NAV", nav_data(pages), compress=False)
    notice_links = register_license_notices(book)
    from pygments.formatters import HtmlFormatter
    selectors = [".code-block", ".source-code", ".source-preview-code"]
    highlight_css=HtmlFormatter(style="friendly").get_style_defs(selectors)
    highlight_css+="\n"+HtmlFormatter(style="github-dark").get_style_defs(
        ["html[data-theme=dark] " + selector for selector in selectors])
    write(staging/"assets"/"highlight.css",highlight_css)
    write(staging/"assets"/"favicon.svg",'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="#102f40"/><path d="m11 10 18 20M29 10 11 30" stroke="#9fdcc4" stroke-width="4"/></svg>')
    book.render_chapters(svg_paths)
    count=book.render_indexes()
    log(f"Built alphabetical index: {count:,} terms.")
    script_data(staging/"assets"/"search-index.js", "XNU_SEARCH", book.search)
    book.render_sources(args.jobs)
    book.copy_downloads()
    from layouts.catalog import integrate as integrate_layouts
    log("Generating the pinned layout catalog, header bundles and explorer…")
    layouts = integrate_layouts(staging, cache, args.layout_runtime.resolve(), args.layout_native.resolve(), args.layout_configs.resolve())
    write(staging/DOWNLOAD_PAGE, download_page(pages))
    import pygments
    renderers = Counter(ET.parse(staging/path).getroot().get("data-renderer","unknown")
                        for path in svg_paths.values())
    tool_paths = {path for path in HERE.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts}
    tool_paths.add(DOCS/"tools"/"doc_license.py")
    manifest={"schema":2,"snapshot":"xnu-12377.121.6",
              "documentation_license":"CC-BY-4.0",
              "software_license":"GPL-2.0-only",
              "source_root":SOURCE_ROOT.relative_to(ROOT).as_posix(),"pages":len(pages),
              "diagrams":len(book.diagrams),"sources":len(book.sources),
              "concepts":count,"search_sections":len(book.search),
              "source_format":"gzip-base64-pygments-tokens-v2",
              "layouts":layouts,
              "offline_archive":{"file":ARCHIVE_NAME,"root":ARCHIVE_ROOT},
              "diagram_renderers":dict(sorted(renderers.items())),
              "pygments_version":pygments.__version__,
              "book_tool_hashes":{path.relative_to(ROOT).as_posix():digest(path.read_bytes())
                                 for path in sorted(tool_paths)},
              "markdown":{p["path"]:digest(p["markdown"]) for p in pages},
              "source_hashes":{r["path"]:digest(r["file"].read_bytes()) for r in book.sources.values()}}
    write(staging/"build-manifest.json",json.dumps(manifest,indent=2)+"\n")
    content=(f'<h1 id="build">Build and provenance</h1><p>Generated from the local XNU Markdown handbook with <code>python3 make_docs.py</code>.</p>'
             f'<ul><li>{len(pages)} Markdown pages</li><li>{len(book.diagrams)} standalone SVG diagrams</li>'
             f'<li>{len(book.sources)} source, Markdown and notice files with line anchors and highlighted previews</li>'
             f'<li>{count:,} alphabetical entries; {len(book.search):,} searchable sections/chunks</li></ul>'
             '<p>Search indexes the complete documentation, including inline code. Source files are available through citations and the source index.</p>'
             '<p>All browsing assets are local. No server, account, analytics, CDN or network connection is required to read this book. '
             'Source files, search and index data are stored losslessly compressed. The browser creates highlighting and exact-byte downloads from the shared data.</p>'
             '<p><a href="build-manifest.json">Content hashes and build manifest</a> · '
             '<a href="development/building-html.html">Build and maintenance instructions</a> · '
             f'<a href="{DOWNLOAD_PAGE}">Download the offline handbook</a></p>'
             '<h2 id="licenses">Documentation, software and source licenses</h2>'
             f'<p>Original Platydoc documentation and diagrams, including the Markdown and generated HTML, '
             f'are licensed under <a href="{LICENSE_URL}" rel="license">Creative Commons Attribution 4.0 International</a> '
             '(<a href="licenses/CC-BY-4.0.txt">local license text</a>). When sharing or adapting them, '
             'credit Platydoc and its contributors, retain attribution and the license link, and identify changes.</p>'
             '<p>Platydoc build tools and browser software are licensed under '
             '<a href="licenses/GPL-2.0.txt">GNU GPL version 2</a>. '
             'The documentation license does not relicense XNU, copied source excerpts, source-viewer contents '
             'or bundled third-party materials: those retain their respective licenses and notices. '
             'Original Platydoc Markdown shown in the source viewer remains CC BY 4.0.</p><ul>' +
             "".join(f'<li><a href="{url}">{name}</a></li>' for name,url in notice_links.items()) +
             "".join(f'<li><a href="{html.escape(notice["path"],quote=True)}">Layout runtime: {html.escape(notice["name"])}</a></li>' for notice in layouts["notices"]) + '</ul>')
    write(staging/"build-info.html",shell("Build and provenance",content,"build-info.html",
          nav=nav_html(pages,"build-info.html"),chapter="BUILD REFERENCE"))
    log("Packaging the complete offline handbook ZIP…")
    create_archive(staging)
    from .verify import verify_generated
    log("Checking generated HTML, anchors, assets, SVG and offline ZIP…")
    checks=verify_generated(staging)
    log(json.dumps(checks,indent=2))
    backup=output.with_name(output.name+".previous")
    if backup.exists():
        if not (backup/".xnu-book").exists():
            raise RuntimeError(f"Unmarked backup directory exists: {backup}")
        shutil.rmtree(backup)
    if output.exists():
        output.rename(backup)
    staging.rename(output)
    if backup.exists():
        shutil.rmtree(backup)
    log(f"Built in {time.monotonic()-started:.1f}s. Open {output/'index.html'}")
    log(f"Offline download: {output/ARCHIVE_NAME}")
    return 0
