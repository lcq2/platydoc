"""Compact, exact source records for the offline book's classic-script payloads.

encode_source(path, cache_dir, aliases=None) returns a decoded base record. The
builder adds path, URL and backlinks before calling pack(record). pack() also
accepts arbitrary JSON values for search and index payloads.

Token strings concatenate to raw.decode("utf-8", errors="replace"), preserving
BOMs, CRLFs, tabs and final-newline state. The optional raw_base64 field preserves
bytes that cannot round-trip through UTF-8. Token indexes address CSS class names,
not character offsets, so JavaScript UTF-16 indexing never changes token bounds.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.util import ClassNotFound


SCHEMA = 2
# Bump whenever tokenization, CSS class mapping or source-record semantics change.
CODEC_VERSION = "1"
_NEWLINE = re.compile(r"\r\n|\r|\n")


def line_count(text: str) -> int:
    """Count editor lines: CRLF/CR/LF delimiters, no extra terminal empty line."""
    if not text:
        return 0
    count = sum(1 for _ in _NEWLINE.finditer(text))
    return count + (0 if text.endswith(("\n", "\r")) else 1)


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _gzip(data: bytes) -> bytes:
    compressed = gzip.compress(data, compresslevel=9, mtime=0)
    # Python 3.11/3.12 may expose zlib's platform-specific OS byte for mtime=0.
    # Fix that harmless metadata byte for the same framing on every platform.
    return compressed[:9] + b"\xff" + compressed[10:]


def pack(value) -> dict:
    """Return an ASCII-safe deterministic gzip/base64 envelope for any JSON value."""
    return {
        "schema": SCHEMA,
        "encoding": "gzip-base64",
        "data": base64.b64encode(_gzip(_json_bytes(value))).decode("ascii"),
    }


def unpack(envelope):
    """Decode an envelope for build-side tests and tools; never executes JavaScript."""
    if envelope.get("schema") != SCHEMA or envelope.get("encoding") != "gzip-base64":
        raise ValueError("Unsupported compact payload envelope")
    compressed = base64.b64decode(envelope["data"], validate=True)
    return json.loads(gzip.decompress(compressed).decode("utf-8"))


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".source-codec-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _tokenize(text: str, filename: str) -> tuple[list[str], list[list]]:
    try:
        lexer = get_lexer_for_filename(filename, stripnl=False, ensurenl=False, tabsize=0)
    except ClassNotFound:
        lexer = TextLexer(stripnl=False, ensurenl=False, tabsize=0)
    formatter = HtmlFormatter()
    styles, indexes, tokens = [""], {"": 0}, []
    cursor = 0
    # Do not use lex()/get_tokens(): their input preprocessing normalizes CRLF,
    # removes an initial BOM and may strip/add newlines. Full-file unprocessed
    # lexing still carries the lexer's multiline state across every token.
    for position, token_type, value in lexer.get_tokens_unprocessed(text):
        if not value:
            continue
        end = cursor + len(value)
        if position != cursor or text[cursor:end] != value:
            raise ValueError(f"Pygments changed source text at character {cursor} in {filename}")
        cursor = end
        # Use the same class selection as the existing HtmlFormatter, including
        # inherited token subtypes that can require multiple CSS classes.
        style = formatter._get_css_classes(token_type)
        if style not in indexes:
            indexes[style] = len(styles)
            styles.append(style)
        index = indexes[style]
        if tokens and tokens[-1][0] == index:
            tokens[-1][1] += value
        else:
            tokens.append([index, value])
    if cursor != len(text):
        raise ValueError(f"Pygments omitted source text at character {cursor} in {filename}")
    return styles, tokens


def encode_source(path, cache_dir, aliases=None) -> dict:
    """Tokenize/cache a file, leaving path/URL/backlinks for the caller to enrich.

    Cache entries contain only content-dependent base fields; caller aliases are
    inserted after decoding. The caller can mutate its returned record freely.
    """
    path, cache_dir = Path(path), Path(cache_dir)
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    identity = [CODEC_VERSION, pygments.__version__, path.name, sha256]
    key = hashlib.sha256(_json_bytes(identity)).hexdigest()
    cached = cache_dir / "source-codec" / f"{key}.json.gz"
    try:
        record = json.loads(gzip.decompress(cached.read_bytes()).decode("utf-8"))
    except FileNotFoundError:
        text = raw.decode("utf-8", errors="replace")
        styles, tokens = _tokenize(text, path.name)
        record = {
            "schema": SCHEMA,
            "language": path.suffix.lstrip("."),
            "styles": styles,
            "tokens": tokens,
            "sha256": sha256,
            "line_count": line_count(text),
        }
        if text.encode("utf-8") != raw:
            record["raw_base64"] = base64.b64encode(raw).decode("ascii")
        _atomic_write(cached, _gzip(_json_bytes(record)))
    if record.get("schema") != SCHEMA or record.get("sha256") != sha256:
        raise ValueError(f"Invalid compact source cache entry: {cached}")
    record["aliases"] = dict(aliases or {})
    return record
