#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Transport locally prepared layout assets; publishing never runs a compiler."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
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


ASSET = 'prepared-layouts.tar.gz'
REFERENCE_FORMAT = 'platydoc.prepared-layout-release'


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()


def gh(arguments, missing_release=False):
    try:
        result = subprocess.run(['gh', *arguments], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=600)
    except FileNotFoundError as error:
        raise RuntimeError('GitHub CLI is missing; install github-cli through your package manager and run gh auth login.') from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError('GitHub CLI timed out; check connectivity and retry.') from error
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or 'unknown GitHub CLI error'
        if missing_release and ('release not found' in message.lower() or 'HTTP 404' in message): return None
        raise RuntimeError('GitHub release command failed; check gh authentication/network access: ' + message)
    return result.stdout


def reference_value(value):
    if (set(value) != {'format','version','repo','tag','asset','sha256','bytes'}
            or value['format'] != REFERENCE_FORMAT or value['version'] != 1
            or not isinstance(value['repo'], str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value['repo'])
            or not isinstance(value['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', value['sha256'])
            or value['tag'] != 'layouts-' + value['sha256'] or value['asset'] != ASSET
            or type(value['bytes']) is not int or value['bytes'] <= 0):
        raise ValueError('Invalid prepared-layout release reference')
    return value


def download(reference: Path, output: Path):
    value = reference_value(json.loads(reference.read_text()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.layout-download-', dir=output.parent) as temporary:
        target = Path(temporary) / ASSET
        gh(['release','download',value['tag'],'--repo',value['repo'],'--pattern',ASSET,'--output',str(target)])
        target.replace(output)
    print('Downloaded prepared layouts:', output)


def publish(repo: str, reference: Path, archive: Path | None = None, book: Path | None = None):
    if (archive is None) == (book is None): raise ValueError('Supply exactly one of --book or --archive')
    if book is not None:
        archive = Path(__file__).resolve().parents[3] / '.docs-cache/layouts/prepared-release' / ASSET
        export(book, archive)
    sha = file_sha(archive)
    value = reference_value({'format':REFERENCE_FORMAT,'version':1,'repo':repo,
        'tag':'layouts-' + sha,'asset':ASSET,'sha256':sha,'bytes':archive.stat().st_size})
    existing = gh(['release','view',value['tag'],'--repo',repo,'--json','assets'], missing_release=True)
    reference.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.layout-release-', dir=archive.parent) as temporary:
        upload = Path(temporary) / ASSET
        try: os.link(archive, upload)
        except OSError: shutil.copyfile(archive, upload)
        if existing is None:
            gh(['release','create',value['tag'],str(upload),'--repo',repo,'--target','main',
                '--title','Prepared layouts ' + value['sha256'][:12],
                '--notes','Locally prepared layout assets. No compiler build runs during publication.', '--latest=false'])
        elif any(asset['name'] == ASSET for asset in json.loads(existing)['assets']):
            # Verify the existing remote bytes; never replace an immutable asset.
            candidate = Path(temporary) / 'existing.tar.gz'
            gh(['release','download',value['tag'],'--repo',repo,'--pattern',ASSET,'--output',str(candidate)])
            if candidate.stat().st_size != value['bytes'] or file_sha(candidate) != value['sha256']:
                raise ValueError('Existing release asset differs; refusing to overwrite it')
        else:
            gh(['release','upload',value['tag'],str(upload),'--repo',repo])
        if archive.stat().st_size != value['bytes'] or file_sha(archive) != value['sha256']:
            raise ValueError('Local archive changed during upload; release reference not written')
        pending = Path(temporary) / 'reference.json'; pending.write_text(json.dumps(value, indent=2) + '\n')
        # Reference may live on another filesystem; replace a temporary sibling.
        with tempfile.NamedTemporaryFile(prefix='.layout-reference-', dir=reference.parent, delete=False) as stream:
            replacement = Path(stream.name); stream.write(pending.read_bytes())
        try: replacement.replace(reference)
        finally: replacement.unlink(missing_ok=True)
    print('Prepared layout release reference:', reference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('export'); p.add_argument('--book', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('unpack'); p.add_argument('--archive', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('publish'); source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--book', type=Path); source.add_argument('--archive', type=Path)
    p.add_argument('--repo', required=True); p.add_argument('--reference', type=Path, default=Path('runtime/prepared-layouts.release.json'))
    p = commands.add_parser('download'); p.add_argument('--reference', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'export': export(args.book, args.output)
        elif args.command == 'unpack': unpack(args.archive, args.output)
        elif args.command == 'publish': publish(args.repo, args.reference, archive=args.archive, book=args.book)
        else: download(args.reference, args.output)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__': main()
