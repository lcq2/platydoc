"""Build-time, offline Mermaid-to-SVG rendering.

API: render_diagrams([{key, source, label}, ...], output_dir, cache_dir,
                     strict=True) -> {key: "assets/diagrams/<key>.svg"}.

``output_dir`` is the HTML book root; keys must be lowercase SHA-256 hex strings.
The caller chooses deterministic keys; this module additionally hashes source,
label, pinned renderer assets, configuration and renderer implementation for cache
invalidation. Uncached diagrams require Node >= 20 and either Chromium or
Graphviz. Cached SVGs can be copied without invoking either renderer.
The vendored Mermaid runtime needs no npm installation or internet access.
If Chromium cannot launch, the same Mermaid parser feeds Graphviz for graph/state
diagrams and a native SVG sequence renderer. Unsupported fallback constructs fail
explicitly. DOCS_DIAGRAM_RENDERER=browser requires the browser backend;
DOCS_DIAGRAM_RENDERER=parsed-svg selects the fallback without attempting Chromium.

Failures raise DiagramRenderError by default. ``strict=False`` is explicitly
partial mode: failures are printed and omitted from the returned mapping.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor" / "mermaid"
SCRIPT = HERE / "render_diagrams.mjs"
CONFIG = {
    "startOnLoad": False,
    "securityLevel": "strict",
    "theme": "base",
    "htmlLabels": False,
    "deterministicIds": True,
    "fontFamily": "Arial, Helvetica, sans-serif",
    "maxTextSize": 100000,
    "themeVariables": {
        "fontSize": "16px", "fontFamily": "Arial, Helvetica, sans-serif",
        "primaryColor": "#e8f0fa", "primaryTextColor": "#172a46",
        "primaryBorderColor": "#516c91", "lineColor": "#516c91",
        "secondaryColor": "#edf5f0", "tertiaryColor": "#f6f2e8",
        "background": "#ffffff",
    },
    "flowchart": {"htmlLabels": False, "useMaxWidth": False, "curve": "basis"},
    "sequence": {"useMaxWidth": False, "mirrorActors": False},
}


class DiagramRenderError(RuntimeError):
    """A required diagram or its offline renderer could not be built."""


def _svg_ok(data: bytes) -> bool:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return False
    return (
        root.tag == "{http://www.w3.org/2000/svg}svg"
        and bool(root.get("viewBox"))
        and not any(n.tag.rsplit("}", 1)[-1] in {"foreignObject", "script"} for n in root.iter())
    )


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".diagram-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _run_renderer(request):
    """Bound the entire child process group, including browser/Graphviz children."""
    process = subprocess.Popen(
        ["node", str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, start_new_session=(os.name == "posix"),
    )
    try:
        stdout, stderr = process.communicate(json.dumps(request), timeout=180)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.communicate()
        raise
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def render_diagrams(diagrams, output_dir, cache_dir, strict=True):
    """Render all distinct keys and return paths relative to the book root."""
    output_dir, cache_dir = Path(output_dir), Path(cache_dir)
    backend = os.environ.get("DOCS_DIAGRAM_RENDERER", "auto")
    if backend not in {"auto", "browser", "parsed-svg"}:
        raise DiagramRenderError(f"Unknown DOCS_DIAGRAM_RENDERER: {backend}")
    manifest = json.loads((VENDOR / "manifest.json").read_text())
    # Verify bundled inputs, so accidental changes cannot masquerade as a cache hit.
    for name, expected in manifest["files"].items():
        path = VENDOR / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise DiagramRenderError(f"Vendored Mermaid integrity check failed: {path}")
    fingerprint = hashlib.sha256(json.dumps({
        "vendor": manifest["sha256"], "config": CONFIG, "backend": backend,
        "script": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "python": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, sort_keys=True).encode()).hexdigest()
    unique = {}
    for original in diagrams:
        item = {name: str(original.get(name, "")) for name in ("key", "source", "label")}
        key = item["key"]
        if not re.fullmatch(r"[0-9a-f]{64}", key):
            raise DiagramRenderError(f"Diagram key is not a SHA-256 hex string: {key!r}")
        if key in unique and unique[key]["source"] != item["source"]:
            raise DiagramRenderError(f"Diagram key collision for {key}")
        unique.setdefault(key, item)
    results, missing, errors, cache_paths = {}, [], [], {}
    for key, item in unique.items():
        cache_key = hashlib.sha256(json.dumps({
            "renderer": fingerprint, **item,
        }, sort_keys=True).encode()).hexdigest()
        cache_path = cache_dir / f"{cache_key}.svg"
        cache_paths[key] = cache_path
        if cache_path.is_file() and _svg_ok(data := cache_path.read_bytes()):
            relative = f"assets/diagrams/{key}.svg"
            _atomic_write(output_dir / relative, data)
            results[key] = relative
        else:
            missing.append(item)
    if missing and not shutil.which("node"):
        raise DiagramRenderError("Uncached diagrams require Node.js >= 20 on PATH.")
    chromium = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
    if missing and backend == "browser" and not shutil.which(chromium):
        raise DiagramRenderError(f"Uncached diagrams require Chromium; set CHROMIUM_PATH (tried {chromium}).")
    for start in range(0, len(missing), 25):
        batch = missing[start:start + 25]
        request = {
            "diagrams": batch, "config": CONFIG,
            "entry": str(VENDOR / manifest["entry"]), "version": manifest["version"],
            "render_timeout_ms": 30000, "backend": backend,
        }
        print(f"Rendering diagrams {start + 1}–{start + len(batch)} of {len(missing)} "
              f"({len(unique) - len(missing)} cached)", file=sys.stderr, flush=True)
        try:
            process = _run_renderer(request)
            if process.returncode:
                raise DiagramRenderError(process.stderr.strip()[-8000:] or f"Node exited {process.returncode}")
            if process.stderr.strip():
                print(process.stderr.strip()[-2000:], file=sys.stderr)
            records = json.loads(process.stdout)
            expected = {item["key"] for item in batch}
            if len(records) != len(expected) or {record["key"] for record in records} != expected:
                raise DiagramRenderError("Renderer returned an incomplete or mismatched batch.")
            for record in records:
                key = record["key"]
                if "error" in record:
                    errors.append(f"{unique[key]['label'] or key}: {record['error']}")
                    continue
                data = record["svg"].encode()
                if not _svg_ok(data):
                    errors.append(f"{unique[key]['label'] or key}: invalid/non-native SVG")
                    continue
                _atomic_write(cache_paths[key], data)
                relative = f"assets/diagrams/{key}.svg"
                _atomic_write(output_dir / relative, data)
                results[key] = relative
        except (OSError, subprocess.TimeoutExpired, ValueError, DiagramRenderError) as error:
            errors.append(f"Renderer batch beginning {batch[0]['label'] or batch[0]['key']}: {error}")
    if errors:
        message = f"{len(errors)} diagram rendering error(s):\n" + "\n".join(errors)
        if strict:
            raise DiagramRenderError(message)
        print(message, file=sys.stderr)
    return results
