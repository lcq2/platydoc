"""Package and verify the complete generated handbook for offline reading."""

from __future__ import annotations

from pathlib import Path
import io
import os
import shutil
import stat
import tempfile
import zipfile
import zlib


ARCHIVE_NAME = "xnu-source-handbook.zip"
ARCHIVE_ROOT = "xnu-source-handbook"
DOWNLOAD_PAGE = "download.html"
DOWNLOAD_START = "<!-- BEGIN PLATYDOC OFFLINE DOWNLOAD -->"
DOWNLOAD_END = "<!-- END PLATYDOC OFFLINE DOWNLOAD -->"
HEADER_START = "<!-- BEGIN PLATYDOC HEADER DOWNLOAD -->"
HEADER_END = "<!-- END PLATYDOC HEADER DOWNLOAD -->"
HEADER_LABEL = "Download offline version from here"
_CHUNK_SIZE = 1024 * 1024

_OFFLINE_CONTENT = b"""
<p>This is the offline copy of the XNU Source Handbook.
<a href="index.html">Open the handbook</a> to start reading.</p>
<p>Keep the whole extracted folder together; search, source previews, diagrams
and license notices use its local files. No web server or network connection
is required.</p>
"""


def offline_page(data: bytes) -> bytes:
    """Replace the download control without changing the rest of its page."""
    start, end = DOWNLOAD_START.encode("ascii"), DOWNLOAD_END.encode("ascii")
    if data.count(start) != 1 or data.count(end) != 1:
        raise ValueError(f"{DOWNLOAD_PAGE} needs exactly one offline-download block")
    first = data.index(start) + len(start)
    last = data.index(end)
    if last < first:
        raise ValueError(f"{DOWNLOAD_PAGE} has reversed offline-download markers")
    return data[:first] + _OFFLINE_CONTENT + data[last:]


def offline_html(relative: str, data: bytes) -> bytes:
    """Keep header links useful after extracting the ZIP, which omits itself."""
    if relative == DOWNLOAD_PAGE:
        data = offline_page(data)
    start, end = HEADER_START.encode("ascii"), HEADER_END.encode("ascii")
    if start not in data and end not in data:
        return data
    if data.count(start) != 1 or data.count(end) != 1:
        raise ValueError(f"{relative} needs exactly one header-download block")
    first, last = data.index(start) + len(start), data.index(end)
    if last < first:
        raise ValueError(f"{relative} has reversed header-download markers")
    block = data[first:last].replace(f' download="{ARCHIVE_NAME}"'.encode(), b"")
    block = block.replace(ARCHIVE_NAME.encode(), DOWNLOAD_PAGE.encode())
    block = block.replace(HEADER_LABEL.encode(), b"Offline reading instructions")
    return data[:first] + block + data[last:]


def _book_files(root: Path) -> dict[str, Path]:
    """Inventory this output only, rejecting links and nonregular entries."""
    if not root.is_dir():
        raise ValueError(f"Generated output directory is missing: {root}")
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Offline archive cannot include a symlink: {path.relative_to(root)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Offline archive needs a regular file: {path.relative_to(root)}")
        relative = path.relative_to(root).as_posix()
        if relative != ARCHIVE_NAME:
            files[relative] = path
    for required in ("index.html", DOWNLOAD_PAGE):
        if required not in files:
            raise ValueError(f"Offline archive is missing its entry page: {required}")
    return files


def create_archive(root: Path) -> Path:
    """Write a compressed snapshot, atomically replacing any previous ZIP.

    The download page in the extracted copy has local reading instructions in
    place of the ZIP link. The ZIP itself is excluded, avoiding self-inclusion.
    Fixed member ordering, timestamps and permissions make packaging repeatable.
    """
    root = Path(root).resolve()
    files = _book_files(root)
    # Check the download-page instruction markers before opening the archive.
    offline_page(files[DOWNLOAD_PAGE].read_bytes())
    descriptor, name = tempfile.mkstemp(prefix=f".{ARCHIVE_NAME}.", suffix=".tmp", dir=root)
    os.close(descriptor)
    temporary = Path(name)
    destination = root / ARCHIVE_NAME
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative, path in files.items():
                info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                if path.suffix == ".html":
                    archive.writestr(info, offline_html(relative, path.read_bytes()))
                else:
                    info.file_size = path.stat().st_size
                    with path.open("rb") as source, archive.open(info, "w") as member:
                        shutil.copyfileobj(source, member, length=_CHUNK_SIZE)
        # mkstemp starts private; the published download must be readable by
        # the static web server just like the rest of the generated book.
        temporary.chmod(0o644)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def verify_archive(root: Path) -> dict[str, int]:
    """Check complete, unique and byte-exact membership without extraction.

    Comparing with the validated output also covers its nested links, local
    scripts, compressed source records, diagrams and notices. Only marked
    download controls change to local offline-reading links and instructions.
    """
    root = Path(root).resolve()
    files = _book_files(root)
    expected = {f"{ARCHIVE_ROOT}/{relative}": (relative, path)
                for relative, path in files.items()}
    destination = root / ARCHIVE_NAME
    try:
        with zipfile.ZipFile(destination) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise ValueError("Offline ZIP contains duplicate members")
            missing, extra = set(expected) - set(names), set(names) - set(expected)
            if missing or extra:
                details = []
                if missing:
                    details.append("missing: " + ", ".join(sorted(missing)[:8]))
                if extra:
                    details.append("unexpected: " + ", ".join(sorted(extra)[:8]))
                raise ValueError("Offline ZIP membership differs from the book (" + "; ".join(details) + ")")
            for entry in entries:
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError(f"Offline ZIP contains a symlink: {entry.filename}")
                if entry.compress_type != zipfile.ZIP_DEFLATED:
                    raise ValueError(f"Offline ZIP member is not DEFLATE-compressed: {entry.filename}")
                if entry.flag_bits & 1:
                    raise ValueError(f"Offline ZIP member is encrypted: {entry.filename}")
                relative, path = expected[entry.filename]
                data = offline_html(relative, path.read_bytes()) if path.suffix == ".html" else None
                expected_size = len(data) if data is not None else path.stat().st_size
                if entry.file_size != expected_size:
                    raise ValueError(f"Offline ZIP member size differs from the book: {entry.filename}")
                # Reading each complete member validates its CRC as well as the
                # content comparison, without trusting CRC alone for identity.
                with (io.BytesIO(data) if data is not None else path.open("rb")) as source, \
                        archive.open(entry) as member:
                    while True:
                        chunk = source.read(_CHUNK_SIZE)
                        if member.read(_CHUNK_SIZE) != chunk:
                            raise ValueError(f"Offline ZIP member differs from the book: {entry.filename}")
                        if not chunk:
                            break
    except (OSError, EOFError, zipfile.BadZipFile, RuntimeError, zlib.error) as exc:
        raise ValueError(f"Cannot verify offline ZIP: {exc}") from exc
    return {"archive_files": len(expected), "archive_bytes": destination.stat().st_size}
