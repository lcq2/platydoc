# SPDX-License-Identifier: GPL-2.0-only
"""Attach a prepared data package to the handbook; never run a compiler."""
import hashlib
import json
from html import escape
from pathlib import Path
import shutil
import subprocess
from urllib.parse import parse_qsl
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS
HERE = Path(__file__).resolve().parent
PAGE = "structures/layout-browser.html"
MARKER = "structure-layout-explorer"


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_bytes())

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value) + b"\n")

def validate_selection_query(query, catalog):
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
    if len(pairs) != 1 or pairs[0][0] != "declaration":
        raise ValueError("Unknown or ambiguous authored layout declaration selector")
    matches = [selection for selection in catalog["selections"] if selection["key"] == pairs[0][1]]
    if len(matches) != 1:
        raise ValueError("Unknown or ambiguous authored layout declaration selector")
    return matches[0]

def seal(output):
    """Seal data/assets only: native book HTML has its own ZIP transformations."""
    files = {}
    for path in sorted(output.rglob("*")):
        if path.is_symlink():
            raise ValueError("Generated layout assets cannot be symlinks")
        if path.is_file() and path.name != "manifest.json":
            raw = path.read_bytes()
            files[path.relative_to(output).as_posix()] = {"bytes": len(raw), "sha256": digest(raw)}
    value = {"contract": "platydoc.layout-package", "version": 1, "page": PAGE, "files": files}
    write_json(output / "manifest.json", value)
    notices = [{"name": path.name, "path": "layouts/licenses/" + path.name} for path in sorted((output / "licenses").iterdir()) if path.is_file()]
    return {"path": "layouts/manifest.json", "sha256": digest((output / "manifest.json").read_bytes()), "profiles": len(read_json(output / "runtime-manifest.json")["profiles"]), "notices": notices}

def coverage_table(coverage):
    """A readable finite matrix; unsupported cells never link to invented layouts."""
    heading = '<section id="layout-coverage"><h2>Documented structure coverage</h2><p>This finite survey covers the listed C roots in each generated iPhoneOS source profile. Available layouts use PAC-enabled arm64e analysis contexts. Returned embedded records do not expand the surveyed inventory. Unsupported cells retain their exact compiler diagnostics in <a href="../layouts/coverage.json">coverage data</a>.</p><div class="table-wrap"><table><thead><tr><th>Structure</th>'
    heading += ''.join('<th>' + escape(base) + '</th>' for base in coverage['base_profiles']) + '</tr></thead><tbody>'
    rows = []
    for entry in coverage['entries']:
        cells = []
        for base in coverage['base_profiles']:
            cell = entry['profiles'][base]
            text = 'Available' if cell['status'] == 'supported' else escape(cell['status'] + ': ' + cell['reason'])
            cells.append('<td data-coverage-root="' + escape(entry['key'], quote=True) + '" data-base-profile="' + escape(base, quote=True) + '">' + text + '</td>')
        name = '<a href="layout-browser.html?declaration=' + escape(entry['key'], quote=True) + '">' + escape(entry['key']) + '</a>'
        rows.append('<tr><th scope="row">' + name + '</th>' + ''.join(cells) + '</tr>')
    return heading + ''.join(rows) + '</tbody></table></div></section>'

def integrate(book, prepared):
    """Inject the approved workspace into the authored native-shell chapter."""
    import re
    page = book / PAGE
    text = page.read_text()
    marker = '<div id="' + MARKER + '"></div>'
    if text.count(marker) != 1:
        raise ValueError("Layout guide needs exactly one empty reserved explorer marker")
    for other in book.rglob("*.html"):
        if other != page and 'id="' + MARKER + '"' in other.read_text():
            raise ValueError("Reserved explorer marker occurs outside the layout guide")
    output = book / "layouts"
    from .prepared import unpack
    unpack(prepared, output)
    attach_reader(output, book)
    template = (HERE / "browser/layouts.html").read_text()
    workspace = '<section id="workspace"' + template.split('<section id="workspace"', 1)[1].split('</main>', 1)[0]
    workspace = re.sub(r'<footer class="mockup-footer">.*?</footer>', '', workspace, flags=re.S)
    workspace = workspace.replace('<kbd>/</kbd>', '')  # Global slash belongs to native handbook search.
    inspector = '<aside id="field-inspector"' + template.split('<aside id="field-inspector"', 1)[1].split('</aside>', 1)[0] + '</aside>'
    announce = '<div id="announce" class="visually-hidden" role="status" aria-live="polite"></div>'
    text = text.replace(marker, '<div id="' + MARKER + '">' + workspace + '</div>')
    coverage = output / 'coverage.json'
    if coverage.is_file():
        boundary = '<div id="' + MARKER + '">' + workspace + '</div>'
        text = text.replace(boundary, boundary + coverage_table(read_json(coverage)), 1)
    text = re.sub(r'<body class="[^"]*"', '<body class="layout-design layout-integrated"', text, count=1)
    text = text.replace('</head>', '<link rel="stylesheet" href="../layouts/layouts.css">\n</head>')
    scripts = ["runtime-manifest.js", "explorer-config.js", "catalog.js", "layout-codec.js", "layout-runtime.js",
               "contracts.js", "dependencies.js", "explorer-model.js", "book-layouts.js", "layouts.js"]
    text = text.replace('</body>', inspector + announce + ''.join('<script src="../layouts/' + name + '"></script>' for name in scripts) + '</body>')
    page.write_text(text)
    return seal(output)


def source_records_by_layout_path(records):
    """Map producer-relative XNU identities to this handbook's source wrappers."""
    prefix = SOURCE_ROOT.relative_to(PROJECT_ROOT).as_posix() + '/'
    indexed = {}
    for url, record in records.items():
        indexed[record['path']] = (url, record)
        if record['path'].startswith(prefix):
            indexed['xnu/' + record['path'][len(prefix):]] = (url, record)
    return indexed


def attach_reader(output, book):
    descriptor = output / 'data-package.json'
    if descriptor.is_file():
        data = read_json(descriptor)
        if data.get('format') != 'platydoc.layout-data' or data.get('version') != 1 or data.get('reader_api') != 1:
            raise ValueError('Unsupported layout data/reader API version')
    catalog = read_json(output / 'catalog.json')
    if catalog.get('contract') != 'platydoc.layout-catalog' or catalog.get('version') != 1:
        raise ValueError('Unsupported layout catalog format')
    revision = subprocess.run(['git', '-C', str(SOURCE_ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
    if catalog['source']['revision'] != revision:
        raise ValueError('Layout data and handbook XNU revisions differ; select matching data')
    # Presentation and chapter destinations belong to this handbook revision.
    mapping = read_json(DOCS / 'structures/layouts.json')
    if mapping['source'] != catalog['source']:
        raise ValueError('Chapter mapping and layout source revisions differ')
    chapters = {row['display_name']: row['chapters'] for row in mapping['entries']}
    mapped = {row['display_name']: row for row in mapping['entries']}
    declarations = {row['id']: row for row in catalog['declarations']}
    for selection in catalog['selections']:
        binding = mapped.get(selection['key'])
        if binding:
            for identity in selection['declarations'].values():
                declaration = declarations[identity]
                point = declaration['source']['spelling']
                if (binding['kind'], binding['source_path'], binding['source_sha256'], binding['offset_bytes']) != (declaration['kind'], point['source_path'], point['sha256'], point['offset_bytes']):
                    raise ValueError('Chapter binding differs from packaged declaration: ' + selection['key'])
        selection['chapters'] = chapters.get(selection['key'], [])
    for name in ('layouts.css', 'layouts.js', 'explorer-model.js', 'book-layouts.js'):
        shutil.copyfile(HERE / 'browser' / name, output / name)
    records = read_json(book / 'source-records.json')
    by_source = source_records_by_layout_path(records)
    headers = read_json(output / 'headers.json')
    links, seen, conflicts = {}, {}, set()
    for rows in headers['profiles'].values():
        for row in rows:
            for key in (row['path'], row.get('source_path')):
                if key is None: continue
                if key in seen and seen[key] != row['sha256']: conflicts.add(key)
                seen[key] = row['sha256']
            target = by_source.get(row.get('source_path'))
            if target and target[1]['sha256'] == row['sha256']:
                links[row['path']] = links[row['source_path']] = '../' + target[0]
    for key in conflicts: links.pop(key, None)
    config = {'bookRoot': '../', 'assetRoot': '../layouts/', 'integrated': True,
              'source': catalog['source'], 'sourceLinks': links, 'selections': catalog['selections']}
    coverage = output / 'coverage.json'
    if coverage.is_file():
        config['coverage'] = read_json(coverage)
        for row in config['coverage']['entries']:
            row['chapters'] = chapters.get(row['key'], [])
    write_json(output / 'catalog.json', catalog)
    write_json(output / 'layout-chapters.json', mapping)
    for name, variable, value in [('catalog.js', 'layoutCatalog', catalog),
                                   ('explorer-config.js', 'layoutExplorerConfig', config)]:
        (output / name).write_bytes(b'// SPDX-License-Identifier: GPL-2.0-only\nwindow.' + variable.encode() + b'=' + encoded(value) + b';\n')


def verify(book):
    """Verify assembled reader files locally, without any producer checkout."""
    output = book / 'layouts'
    manifest = read_json(output / 'manifest.json')
    if manifest.get('contract') != 'platydoc.layout-package' or manifest.get('version') != 1:
        raise ValueError('Unsupported reader layout package')
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    if actual != set(manifest['files']):
        raise ValueError('Layout package membership differs from manifest')
    for name, identity in manifest['files'].items():
        path = output / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
            raise ValueError('Unsafe layout package path')
        raw = path.read_bytes()
        if len(raw) != identity['bytes'] or digest(raw) != identity['sha256']:
            raise ValueError('Layout package file differs: ' + name)
    catalog = read_json(output / 'catalog.json')
    for selection in catalog['selections']:
        for chapter in selection['chapters']:
            page, fragment = chapter.split('#', 1)
            if Path(page).is_absolute() or '..' in Path(page).parts or not page.endswith('.md'):
                raise ValueError('Unsafe layout chapter destination')
            target = book / (page[:-3] + '.html')
            if ('id="' + fragment + '"') not in target.read_text():
                raise ValueError('Missing layout chapter heading: ' + chapter)
    headers = read_json(output / 'headers.json')
    return {'layout_profiles': len(catalog['profiles']), 'layout_declarations': len(catalog['declarations']),
            'layout_headers': sum(map(len, headers['profiles'].values()))}
