"""Verify a generated offline book without network access or third-party code."""

from __future__ import annotations

from collections import Counter
import base64
import binascii
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zlib


_SHAPES = {
    "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "image", "use",
}
_RANGE = re.compile(r"L([1-9]\d*)-L([1-9]\d*)$")
_LINE = re.compile(r"L([1-9]\d*)$")
_WEB_SCHEMES = {"http", "https", "mailto", "tel"}
_SHA256 = re.compile(r"[0-9a-f]{64}$")
_STYLE = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_-]*(?: [A-Za-z_][A-Za-z0-9_-]*)*)?$")
_DECODE_LIMIT = 128 * 1024 * 1024


def _valid_anchor(fragment, ids, virtual=None):
    interval = _RANGE.fullmatch(fragment)
    if virtual is not None:
        if interval:
            start, end = map(int, interval.groups())
            return 1 <= start <= end <= virtual["line_count"]
        line = _LINE.fullmatch(fragment)
        if line:
            return int(line[1]) <= virtual["line_count"]
        return fragment in ids or fragment in virtual["aliases"]
    if interval:
        start, end = map(int, interval.groups())
        return start <= end and f"L{start}" in ids and f"L{end}" in ids
    return fragment in ids


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(text):
    def invalid_constant(value):
        raise ValueError(f"invalid JSON constant: {value}")
    return json.loads(text, object_pairs_hook=_unique_object,
                      parse_constant=invalid_constant)


def _local_file(root, value):
    """Resolve a root-relative book asset, with no redirects or escapes."""
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError(f"invalid local asset path: {value!r}")
    url = urlsplit(value)
    if url.scheme or url.netloc or url.query or url.fragment or url.path.startswith("/"):
        raise ValueError(f"asset path must be book-relative: {value!r}")
    target = (root / unquote(url.path)).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"asset path escapes output: {value!r}")
    if not target.is_file():
        raise ValueError(f"missing local asset: {value!r}")
    return target


def _assignment(path, variable, key=None):
    """Read a fixed JSON-only classic-script assignment without executing JS."""
    text = path.read_text(encoding="utf-8")
    prefix = ""
    target = rf"window\.{re.escape(variable)}"
    if key is not None:
        prefix = rf"\s*{target}\s*=\s*{target}\s*\|\|\s*\{{\}}\s*;"
        target += r'\s*\[\s*("(?:\\.|[^"\\])*")\s*\]'
    match = re.fullmatch(prefix + rf"\s*{target}\s*=\s*(.*?)\s*;\s*", text, re.S)
    if not match:
        raise ValueError(f"not a JSON-only window.{variable} assignment")
    if key is not None:
        if _json(match[1]) != key:
            raise ValueError("source payload assignment key differs from manifest")
    try:
        return _json(match[2] if key is not None else match[1])
    except ValueError as exc:
        raise ValueError(f"invalid JSON-only window.{variable} assignment: {exc}") from exc


def _decode_envelope(envelope):
    if (not isinstance(envelope, dict) or type(envelope.get("schema")) is not int
            or envelope.get("schema") != 2
            or envelope.get("encoding") != "gzip-base64"
            or not isinstance(envelope.get("data"), str)):
        raise ValueError("invalid schema-2 gzip-base64 envelope")
    try:
        packed = base64.b64decode(envelope["data"], validate=True)
        inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
        decoded = inflater.decompress(packed, _DECODE_LIMIT + 1)
    except (binascii.Error, zlib.error) as exc:
        raise ValueError(f"invalid compressed payload: {exc}") from exc
    if len(decoded) > _DECODE_LIMIT or not inflater.eof:
        raise ValueError("compressed payload is truncated or exceeds decoded-size limit")
    if inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError("compressed payload has trailing data or concatenated streams")
    return _json(decoded.decode("utf-8"))


def _source_lines(text):
    if not text:
        return []
    lines = re.split(r"\r\n|\r|\n", text)
    return lines[:-1] if lines[-1] == "" else lines


def _markdown_aliases(text):
    """Reconstruct source-heading aliases, independently of the manifest."""
    result, seen, fence = {}, Counter(), None
    for number, line in enumerate(_source_lines(text), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", match[2])
        title = re.sub(r"<[^>]*>", "", title)
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        duplicate = seen[slug]
        seen[slug] += 1
        result[f"{slug}-{duplicate}" if duplicate else slug] = number
    return result


def _source_record(root, url, record):
    if not isinstance(record, dict):
        raise ValueError("source record must be an object")
    required = {"path", "payload", "sha256", "payload_sha256", "line_count", "aliases"}
    if not required <= record.keys():
        raise ValueError("source record missing fields: " + ", ".join(sorted(required - record.keys())))
    source = record["path"]
    if (not isinstance(source, str) or not source or "\\" in source or "\x00" in source
            or source.startswith("/") or any(p in {"", ".", ".."} for p in source.split("/"))):
        raise ValueError("invalid repository-relative source path")
    if url != "_sources/" + source + ".html":
        raise ValueError("source wrapper URL does not match its repository path")
    wrapper = _local_file(root, url)
    payload = _local_file(root, record["payload"])
    for field in ("sha256", "payload_sha256"):
        if not isinstance(record[field], str) or not _SHA256.fullmatch(record[field]):
            raise ValueError(f"invalid {field}")
    if hashlib.sha256(payload.read_bytes()).hexdigest() != record["payload_sha256"]:
        raise ValueError("source payload SHA-256 mismatch")
    data = _decode_envelope(_assignment(payload, "XNU_SOURCES", source))
    if (not isinstance(data, dict) or type(data.get("schema")) is not int
            or data.get("schema") != 2):
        raise ValueError("decoded source must be a schema-2 object")
    for field in ("path", "sha256", "line_count", "aliases"):
        if data.get(field) != record[field]:
            raise ValueError(f"decoded source {field} differs from manifest")
    if (type(data.get("line_count")) is not int
            or not isinstance(data.get("aliases"), dict)
            or any(type(n) is not int for n in data["aliases"].values())):
        raise ValueError("decoded source line count and alias lines must be integers")
    if data.get("url") != url:
        raise ValueError("decoded source URL differs from manifest")
    if not isinstance(data.get("language"), str):
        raise ValueError("decoded source language must be a string")
    styles = data.get("styles")
    if (not isinstance(styles, list) or not styles
            or any(not isinstance(style, str) or not _STYLE.fullmatch(style) for style in styles)):
        raise ValueError("invalid source CSS style table")
    if len(set(styles)) != len(styles):
        raise ValueError("duplicate source CSS style")
    tokens = data.get("tokens")
    if not isinstance(tokens, list):
        raise ValueError("source tokens must be an array")
    parts = []
    for token in tokens:
        if (not isinstance(token, list) or len(token) != 2
                or type(token[0]) is not int or not 0 <= token[0] < len(styles)
                or not isinstance(token[1], str)):
            raise ValueError("invalid source token or style index")
        parts.append(token[1])
    text = "".join(parts)
    if "raw_base64" in data:
        if not isinstance(data["raw_base64"], str):
            raise ValueError("raw_base64 must be a string")
        try:
            raw = base64.b64decode(data["raw_base64"], validate=True)
        except binascii.Error as exc:
            raise ValueError("invalid original source bytes") from exc
        if raw.decode("utf-8", errors="replace") != text:
            raise ValueError("source tokens differ from original replacement-decoded bytes")
    else:
        raw = text.encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError("reconstructed source SHA-256 mismatch")
    if type(record["line_count"]) is not int or record["line_count"] != len(_source_lines(text)):
        raise ValueError("reconstructed source line count differs from manifest")
    aliases = record["aliases"]
    if not isinstance(aliases, dict):
        raise ValueError("source aliases must be an object")
    for alias, line in aliases.items():
        if (not alias or re.search(r"[\s#\x00]", alias) or _LINE.fullmatch(alias)
                or _RANGE.fullmatch(alias) or type(line) is not int
                or not 1 <= line <= record["line_count"]):
            raise ValueError(f"invalid source alias: {alias!r}")
    expected = _markdown_aliases(text) if source.endswith(".md") else {}
    if aliases != expected:
        raise ValueError("source aliases differ from decoded Markdown headings")
    return wrapper, dict(record, url=url)


def _drawable(element):
    tag = element.tag.rsplit("}", 1)[-1]
    nonzero = lambda value: bool(value and not re.fullmatch(r"0+(?:\.0+)?(?:px|%)?", value.strip()))
    if tag == "path":
        return bool(element.get("d", "").strip())
    if tag == "rect":
        return nonzero(element.get("width")) and nonzero(element.get("height"))
    if tag == "circle":
        return nonzero(element.get("r"))
    if tag == "ellipse":
        return nonzero(element.get("rx")) and nonzero(element.get("ry"))
    if tag == "line":
        return ((element.get("x1", "0"), element.get("y1", "0")) !=
                (element.get("x2", "0"), element.get("y2", "0")))
    if tag in {"polyline", "polygon"}:
        return len(re.findall(r"-?\d+(?:\.\d+)?", element.get("points", ""))) >= 4
    if tag in {"image", "use"}:
        return any(key.rsplit("}", 1)[-1] == "href" and value
                   for key, value in element.attrib.items())
    return False


class _Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.inline_svgs = []
        self.duplicate_ids = set()
        self.base_hrefs = []
        self.body_attrs = {}
        self.source_citations = []
        self.source_viewers = []
        self.packed_html = []
        self._text = text
        self._offsets = [0]
        for match in re.finditer("\n", text):
            self._offsets.append(match.end())
        self._svg_depth = 0
        self._svg_start = 0
        self.feed(text)
        self.close()

    def _offset(self):
        line, column = self.getpos()
        return self._offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body":
            self.body_attrs = attrs
        if tag == "a" and "source-link" in attrs.get("class", "").split():
            self.source_citations.append((attrs, self.getpos()[0]))
        if "data-source-full" in attrs:
            self.source_viewers.append(attrs)
        if attrs.get("id") == "concept-content" and attrs.get("data-index-payload"):
            self.packed_html.append(attrs["data-index-payload"])
        for key in (("id", "name") if tag == "a" else ("id",)):
            identifier = attrs.get(key)
            if identifier:
                if identifier in self.ids and key == "id":
                    self.duplicate_ids.add(identifier)
                self.ids.add(identifier)
        if tag == "base" and attrs.get("href"):
            self.base_hrefs.append(attrs["href"])
        for key in ("href", "src", "xlink:href"):
            if key in attrs and attrs[key] is not None:
                self.links.append((tag, key, attrs[key], self.getpos()[0]))
        if tag == "svg":
            if self._svg_depth == 0:
                self._svg_start = self._offset()
            self._svg_depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "svg":
            self._svg_depth -= 1
            if self._svg_depth == 0:
                self.inline_svgs.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag == "svg" and self._svg_depth:
            self._svg_depth -= 1
            if self._svg_depth == 0:
                end = self._text.find(">", self._offset()) + 1
                self.inline_svgs.append(self._text[self._svg_start:end])


def _svg_validity(text):
    """Return (IDs, external references, problem); never resolve XML entities."""
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
        return set(), [], "SVG contains a DTD or entity declaration"
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        return set(), [], f"invalid SVG XML: {error}"
    if root.tag.rsplit("}", 1)[-1] != "svg":
        return set(), [], "SVG root element is not svg"
    ids, references = set(), []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if element.get("id"):
            ids.add(element.get("id"))
        for attribute, value in element.attrib.items():
            if attribute.rsplit("}", 1)[-1] in {"href", "src"}:
                references.append((tag, attribute, value, 0))
        if tag == "script":
            return ids, references, "SVG contains an executable script"
    def visible_shape(element):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"defs", "clipPath", "mask", "marker", "symbol"}:
            return False
        if tag in _SHAPES and _drawable(element):
            return True
        return any(visible_shape(child) for child in element)
    has_shape = visible_shape(root)
    if not has_shape:
        return ids, references, "SVG has no shape, image or use element"
    return ids, references, None


def verify_generated(output_dir):
    """Return verification counts, or raise ValueError with actionable errors.

    Checks files already under output_dir; it never fetches a URL. Root-relative
    local paths are interpreted within the generated book, and symlink targets
    must stay inside that root. Compact source anchors are accepted only after
    decoding and checking the corresponding manifest, source payload and bytes.
    Inline scripts are permitted; scripts with src must reference local files.
    """
    root = Path(output_dir).resolve()
    if not root.is_dir():
        raise ValueError(f"Generated output directory is missing: {root}")
    counts = Counter(html_files=0, svg_files=0, inline_svgs=0,
                     local_links=0, external_links=0, anchors=0, scripts=0,
                     source_payloads=0, virtual_source_lines=0, compressed_assets=0)
    errors = []
    documents = {}
    svg_ids = {}
    all_links = []
    sources = {}
    sources_by_path = {}
    manifest_path = root / "source-records.json"
    compact = manifest_path.exists()

    def error(path, message, line=None):
        label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        errors.append(f"{label}{':' + str(line) if line else ''}: {message}")

    def local_data_url(value):
        if not isinstance(value, str) or not value:
            raise ValueError("data URL must be a nonempty local URL string")
        url = urlsplit(value)
        if (url.scheme or url.netloc or url.path.startswith("/")
                or "\x00" in value or "\\" in value):
            raise ValueError(f"data URL must stay inside the book: {value!r}")
        return value

    if compact:
        try:
            manifest_path = _local_file(root, "source-records.json")
            records = _json(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(records, dict):
                raise ValueError("source-records.json must be keyed by wrapper URL")
            payloads = set()
            for url, record in records.items():
                try:
                    wrapper, validated = _source_record(root, url, record)
                    payload = _local_file(root, validated["payload"])
                    if wrapper in sources or validated["path"] in sources_by_path or payload in payloads:
                        raise ValueError("duplicate source wrapper, source path or payload")
                    sources[wrapper] = validated
                    sources_by_path[validated["path"]] = validated
                    payloads.add(payload)
                    counts["source_payloads"] += 1
                    counts["virtual_source_lines"] += validated["line_count"]
                    counts["compressed_assets"] += 1
                except (ValueError, UnicodeError, OSError) as exc:
                    error(manifest_path, f"{url}: {exc}")
            for payload in (root / "assets/sources").glob("*.js"):
                if payload.resolve() not in payloads:
                    error(payload, "source payload has no validated manifest record")
            provenance = root / "build-manifest.json"
            if provenance.exists():
                build = _json(_local_file(root, "build-manifest.json").read_text(encoding="utf-8"))
                hashes = build.get("source_hashes")
                if not isinstance(hashes, dict):
                    raise ValueError("build manifest has no source_hashes mapping")
                actual = {record["path"]: record["sha256"] for record in sources.values()}
                if hashes != actual:
                    raise ValueError("source records differ from build-manifest source hashes")
        except (ValueError, UnicodeError, OSError) as exc:
            error(manifest_path, str(exc))

    # Data consumed by local scripts contains navigation links too. Validate
    # those links even though they are not literal hrefs in static HTML.
    search_path = root / "assets/search-index.js"
    if search_path.exists():
        try:
            value = _assignment(_local_file(root, "assets/search-index.js"), "XNU_SEARCH")
            if isinstance(value, dict):
                value = _decode_envelope(value)
                counts["compressed_assets"] += 1
            if not isinstance(value, list):
                raise ValueError("search index must decode to an array")
            for row in value:
                if (not isinstance(row, dict)
                        or any(not isinstance(row.get(key), str)
                               for key in ("url", "title", "heading", "chapter", "text"))):
                    raise ValueError("invalid search record")
                all_links.append((root / "index.html", "a", "href",
                                  local_data_url(row["url"]), 0))
        except (ValueError, UnicodeError, OSError) as exc:
            error(search_path, str(exc))
    nav_path = root / "assets/navigation.js"
    if nav_path.exists():
        try:
            value = _assignment(_local_file(root, "assets/navigation.js"), "XNU_NAV")
            if not isinstance(value, list):
                raise ValueError("navigation must be an array")
            for group in value:
                if not isinstance(group, dict) or not isinstance(group.get("pages"), list):
                    raise ValueError("invalid navigation group")
                for page in group["pages"]:
                    if not isinstance(page, dict):
                        raise ValueError("invalid navigation page")
                    all_links.append((root / "index.html", "a", "href",
                                      local_data_url(page.get("url")), 0))
        except (ValueError, UnicodeError, OSError) as exc:
            error(nav_path, str(exc))

    # Parse each HTML file once. Source pages with thousands of line IDs are
    # represented as sets, making all later anchor lookups constant time.
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            error(path, "file symlink escapes the generated output")
            continue
        suffix = path.suffix.lower()
        if suffix in {".html", ".htm"}:
            counts["html_files"] += 1
            try:
                doc = _Document(path.read_text(encoding="utf-8"))
            except (UnicodeError, ValueError) as exc:
                error(path, f"cannot parse HTML: {exc}")
                continue
            for asset in doc.packed_html:
                try:
                    packed = _local_file(root, asset)
                    decoded = _decode_envelope(_assignment(packed, "XNU_CONCEPT_INDEX"))
                    if not isinstance(decoded, str):
                        raise ValueError("concept index must decode to HTML text")
                    fragment = _Document(decoded)
                    doc.duplicate_ids.update(doc.ids & fragment.ids)
                    doc.duplicate_ids.update(fragment.duplicate_ids)
                    doc.ids.update(fragment.ids)
                    doc.links.extend(fragment.links)
                    doc.inline_svgs.extend(fragment.inline_svgs)
                    doc.base_hrefs.extend(fragment.base_hrefs)
                    if fragment._svg_depth:
                        error(path, "unclosed SVG in decoded concept index")
                    counts["compressed_assets"] += 1
                except (ValueError, UnicodeError, OSError) as exc:
                    error(path, f"packed concept index: {exc}")
            documents[resolved] = doc
            virtual = sources.get(resolved)
            if virtual is not None:
                if (doc.body_attrs.get("data-source-path") != virtual["path"]
                        or doc.body_attrs.get("data-source-payload") != virtual["payload"]):
                    error(path, "source wrapper body does not match manifest")
                for viewer in doc.source_viewers:
                    if (viewer.get("data-source") != virtual["path"]
                            or viewer.get("data-source-payload") != virtual["payload"]):
                        error(path, "source viewer does not match manifest")
                for identifier in doc.ids:
                    if identifier in virtual["aliases"] or _LINE.fullmatch(identifier):
                        error(path, f"static ID conflicts with a virtual source anchor: {identifier}")
            elif "data-source-path" in doc.body_attrs or (
                    compact and path.relative_to(root).parts[0] == "_sources"):
                error(path, "source wrapper has no validated manifest record")
            if compact:
                for citation, line in doc.source_citations:
                    try:
                        record = sources_by_path.get(citation.get("data-source"))
                        if record is None:
                            raise ValueError("source citation has no validated record")
                        if citation.get("data-source-payload") != record["payload"]:
                            raise ValueError("source citation payload differs from manifest")
                        url = urlsplit(citation.get("href", ""))
                        if url.scheme or url.netloc:
                            raise ValueError("source citation is not local")
                        destination = (path.parent / unquote(url.path)).resolve()
                        if destination != (root / record["url"]).resolve():
                            raise ValueError("source citation href and payload identify different files")
                        start = int(citation.get("data-start", ""))
                        end = int(citation.get("data-end", ""))
                        # An uncited empty source file has no valid L1 anchor.
                        if record["line_count"]:
                            if not 1 <= start <= end:
                                raise ValueError("source citation has an invalid preview range")
                            fragment = unquote(url.fragment)
                            interval, single = _RANGE.fullmatch(fragment), _LINE.fullmatch(fragment)
                            if interval and (start, end) != tuple(map(int, interval.groups())):
                                raise ValueError("source citation preview differs from line range")
                            if single and (start != int(single[1]) or end != start):
                                raise ValueError("source citation preview differs from line anchor")
                            if fragment in record["aliases"] and start != record["aliases"][fragment]:
                                raise ValueError("source citation preview differs from Markdown heading")
                            if fragment and (start > record["line_count"] or
                                             ((interval or single) and end > record["line_count"])):
                                raise ValueError("source citation preview is outside source bounds")
                    except (ValueError, TypeError) as exc:
                        error(path, str(exc), line)
            for identifier in sorted(doc.duplicate_ids):
                error(path, f"duplicate id: {identifier}")
            if doc.base_hrefs:
                error(path, "base href changes local-link resolution")
            if doc._svg_depth:
                error(path, "unclosed inline svg element")
            for tag, attribute, raw, line in doc.links:
                # Source pages have one self-link for every source line.
                # Resolve those now instead of retaining millions of tuples.
                if raw.strip().startswith("#"):
                    counts["local_links"] += 1
                    if tag == "script" and attribute == "src":
                        counts["scripts"] += 1
                    fragment = unquote(raw.strip()[1:])
                    if fragment:
                        counts["anchors"] += 1
                        if not _valid_anchor(fragment, doc.ids, virtual):
                            error(path, f"missing anchor in local target: {raw}", line)
                else:
                    all_links.append((path, tag, attribute, raw, line))
            for index, svg in enumerate(doc.inline_svgs, 1):
                counts["inline_svgs"] += 1
                _, _, problem = _svg_validity(svg)
                if problem:
                    error(path, f"inline SVG {index}: {problem}")
            # Only the ID set is needed for cross-document lookups. Highlighted
            # source HTML can be much larger than the original source file.
            doc.links.clear()
            doc.inline_svgs.clear()
            doc._text = ""
            doc._offsets.clear()
        elif suffix == ".svg":
            counts["svg_files"] += 1
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError as exc:
                error(path, f"cannot read SVG: {exc}")
                continue
            ids, references, problem = _svg_validity(text)
            svg_ids[resolved] = ids
            all_links.extend((path, *link) for link in references)
            if problem:
                error(path, problem)

    for source, tag, attribute, raw, line in all_links:
        raw = raw.strip()
        if not raw:
            continue
        try:
            url = urlsplit(raw)
        except ValueError as exc:
            error(source, f"invalid URL {raw!r}: {exc}", line)
            continue
        scheme = url.scheme.lower()
        script = tag == "script" and attribute == "src"
        if script:
            counts["scripts"] += 1
        if scheme or url.netloc:
            if script:
                error(source, f"script src must be local: {raw}", line)
            elif scheme in _WEB_SCHEMES or (url.netloc and not scheme):
                counts["external_links"] += 1
            elif scheme == "data" and tag in {"img", "image", "source"}:
                # Embedded images have no filesystem target to resolve.
                pass
            else:
                error(source, f"unsupported or unsafe URL scheme: {raw}", line)
            continue
        local_path = unquote(url.path)
        if "\x00" in local_path or "\\" in local_path:
            error(source, f"unsafe local path: {raw}", line)
            continue
        if local_path.startswith("/"):
            target = root / local_path.lstrip("/")
        elif local_path:
            target = source.parent / local_path
        else:
            target = source
        target = target.resolve()
        counts["local_links"] += 1
        if not target.is_relative_to(root):
            error(source, f"local link escapes output directory: {raw}", line)
            continue
        if target.is_dir():
            target = (target / "index.html").resolve()
            if not target.is_relative_to(root):
                error(source, f"directory index escapes output directory: {raw}", line)
                continue
        if not target.is_file():
            error(source, f"missing local target: {raw}", line)
            continue
        if target == root / "structures/layout-browser.html" and url.query:
            try:
                catalog = _json(_local_file(root, "layouts/catalog.json").read_text(encoding="utf-8"))
                from layouts.catalog import validate_selection_query
                validate_selection_query(url.query, catalog)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                error(source, str(exc), line)
        fragment = unquote(url.fragment)
        if not fragment:
            continue
        counts["anchors"] += 1
        doc = documents.get(target)
        ids = doc.ids if doc else svg_ids.get(target)
        if ids is None:
            # Downloadable source/data files have no DOM; their fragments are
            # not assumed to be HTML heading anchors.
            continue
        if not _valid_anchor(fragment, ids, sources.get(target)):
            error(source, f"missing anchor in local target: {raw}", line)

    if not counts["html_files"]:
        errors.append("No generated HTML files were found.")
    layout_manifest = root / "layouts/manifest.json"
    build_manifest = root / "build-manifest.json"
    layout_reference = _json(build_manifest.read_text(encoding="utf-8")).get("layouts") if build_manifest.is_file() else None
    if layout_manifest.exists() or layout_reference is not None:
        try:
            if not layout_reference or layout_reference.get("path") != "layouts/manifest.json" or hashlib.sha256(_local_file(root, "layouts/manifest.json").read_bytes()).hexdigest() != layout_reference.get("sha256"):
                raise ValueError("Book layout manifest reference is missing or stale")
            from layouts.catalog import verify as verify_layouts
            counts.update(verify_layouts(root))
        except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            error(layout_manifest, str(exc))
    # The extracted copy omits the ZIP itself and replaces marked download
    # controls. Verify distributed archives against all remaining bytes.
    from .offline import ARCHIVE_NAME, verify_archive
    archive = root / ARCHIVE_NAME
    if archive.exists() or archive.is_symlink():
        try:
            counts.update(verify_archive(root))
        except (ValueError, OSError) as exc:
            error(archive, str(exc))
    counts["errors"] = len(errors)
    summary = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    if errors:
        shown = errors[:80]
        extra = f"\n... {len(errors) - len(shown)} more errors" if len(errors) > len(shown) else ""
        raise ValueError("Generated book verification failed (" + summary + "):\n"
                         + "\n".join(shown) + extra)
    print("Generated book verification passed: " + summary)
    return dict(counts)
