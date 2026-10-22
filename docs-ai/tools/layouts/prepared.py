#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Transport locally prepared layout assets; publishing never runs a compiler."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile


def export(book: Path, output: Path):
    source = book / 'layouts'
    if not (book / '.xnu-book').is_file() or not (source / 'catalog.json').is_file():
        raise ValueError('Export requires an existing generated book with prepared layouts')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.prepared-layouts-', dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            with gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|') as archive:
                    for path in sorted(source.rglob('*')):
                        if path.is_symlink(): raise ValueError('Prepared assets cannot contain symlinks')
                        if not path.is_file(): continue
                        member = tarfile.TarInfo(path.relative_to(source).as_posix())
                        member.size = path.stat().st_size; member.mode = 0o644
                        with path.open('rb') as content: archive.addfile(member, content)
            stream.flush()
            if temporary.stat().st_size >= 100_000_000:
                raise ValueError('Prepared archive exceeds the 100 MB repository file limit')
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
    # This records the original producer, not a fresh validation or generation.
    origin = {'format': 'platydoc.prepared-layouts', 'version': 1,
              'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'archive_bytes': output.stat().st_size,
              'producer_manifest_sha256': hashlib.sha256((source / 'manifest.json').read_bytes()).hexdigest(),
              'note': 'Exact files exported from a previously prepared book. Embedded producer provenance is preserved unchanged.'}
    output.with_suffix('.json').write_text(json.dumps(origin, indent=2) + '\n')
    print('Exported prepared layouts:', output, f'({output.stat().st_size:,} bytes)')


def unpack(archive: Path, output: Path):
    """Extract regular files into a fresh staging directory; no content audits."""
    if output.exists(): raise ValueError('Prepared layouts require a fresh staging directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Fail safely without leaving a partly populated book/layouts directory.
    with tempfile.TemporaryDirectory(prefix='.prepared-layouts-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'layouts'; stage.mkdir()
        seen = set()
        with tarfile.open(archive, 'r:gz') as source:
            for member in source:
                relative = Path(member.name)
                if (not member.isfile() or relative.is_absolute() or '..' in relative.parts
                        or relative.as_posix() in seen or not relative.parts):
                    raise ValueError('Unsafe prepared layout archive member: ' + member.name)
                seen.add(relative.as_posix())
                target = stage / relative; target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as content, target.open('wb') as stream:
                    shutil.copyfileobj(content, stream)
                target.chmod(0o644)
        stage.rename(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('export'); p.add_argument('--book', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('unpack'); p.add_argument('--archive', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export': export(args.book, args.output)
    else: unpack(args.archive, args.output)


if __name__ == '__main__': main()
