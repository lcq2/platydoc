#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fetch pinned layout data explicitly; ordinary book builds remain offline."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
ASSET = 'prepared-layouts.tar.gz'
REFERENCE_FORMAT = 'platydoc.prepared-layout-release'

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
        if target.stat().st_size != value['bytes'] or file_sha(target) != value['sha256']:
            raise ValueError('Downloaded data differs from the selected release checksum')
        target.replace(output)
    print('Downloaded prepared layouts:', output)


def cached_archive(reference, cache):
    value = reference_value(json.loads(reference.read_text()))
    archive = cache / 'layout-data' / (value['sha256'] + '.tar.gz')
    if not archive.is_file():
        raise ValueError('Layout package is not cached. Run: python3 make_docs.py --update-data ' + value['tag'] + ' --data-repo ' + value['repo'])
    if archive.stat().st_size != value['bytes'] or file_sha(archive) != value['sha256']:
        raise ValueError('Cached layout package checksum differs; download it again')
    return archive


def select_release(repo, tag, reference, cache):
    # Content-addressed release names bind the expected checksum before download.
    value = reference_value({'format': REFERENCE_FORMAT, 'version': 1, 'repo': repo,
        'tag': tag, 'asset': ASSET, 'sha256': tag.removeprefix('layouts-'), 'bytes': 1})
    remote = json.loads(gh(['release', 'view', tag, '--repo', repo, '--json', 'assets']))
    assets = [row for row in remote['assets'] if row['name'] == ASSET]
    if len(assets) != 1: raise ValueError('Release must contain exactly one layout data archive')
    value['bytes'] = assets[0]['size']
    reference_value(value)
    reference.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.layout-select-', dir=reference.parent) as temp:
        pending = Path(temp) / 'reference.json'
        pending.write_text(json.dumps(value, indent=2) + '\n')
        download(pending, cache / 'layout-data' / (value['sha256'] + '.tar.gz'))
        pending.replace(reference)
    print('Selected layout data:', tag)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['download'])
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    download(args.reference, args.output)

if __name__ == '__main__': main()
