#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package the live explorer using a verified offline runtime package."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()


def local_path(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in {"..", "."} for part in path.parts):
        raise ValueError("Invalid package path: " + name)
    candidate = root.joinpath(*path.parts)
    if not candidate.resolve().is_relative_to(root.resolve()) or candidate.is_symlink():
        raise ValueError("Package path escapes its root: " + name)
    return candidate


def decoded_asset(package, asset):
    script = local_path(package, asset["url"]).read_bytes()
    prefix = b"LayoutRuntimeAssets.deliver(" + encoded(asset["id"]) + b","
    at = script.find(prefix)
    if at < 0 or not script.endswith(b");\n"):
        raise ValueError("Invalid local asset registration")
    envelope = json.loads(script[at + len(prefix):-3])
    if envelope.get("schema") != 2 or envelope.get("encoding") != "gzip-base64":
        raise ValueError("Invalid asset codec")
    raw = gzip.decompress(base64.b64decode(envelope["data"], validate=True))
    if len(raw) != asset["bytes"] or digest(raw) != asset["sha256"]:
        raise ValueError("Decoded runtime asset changed: " + asset["id"])
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/proof-runtime")
    parser.add_argument("--book", type=Path, default=PROJECT_ROOT / "docs-ai-html")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/explorer")
    args = parser.parse_args()
    package, output, book = args.runtime.resolve(), args.output.resolve(), args.book.resolve()
    for protected in (DOCS.resolve(), SOURCE_ROOT.resolve(), package, book):
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError("Explorer output must be separate from sources, book and runtime proof")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()) and not (output / ".layout-explorer").is_file():
            raise ValueError("Refusing nonempty unmarked explorer output")
        if any(path.is_symlink() for path in output.rglob("*")):
            raise ValueError("Refusing symlinks in explorer output")
    original_bytes = (package / "manifest.json").read_bytes()
    original = json.loads(original_bytes)
    if original.get("kind") != "milestone-5-offline-worker-runtime-proof":
        raise ValueError("Expected accepted offline runtime package")
    for name, identity in original["files"].items():
        raw = local_path(package, name).read_bytes()
        if len(raw) != identity["bytes"] or digest(raw) != identity["sha256"]:
            raise ValueError("Runtime package changed: " + name)
    runtime_bytes = (package / "runtime-manifest.json").read_bytes()
    if digest(runtime_bytes) != original["runtime_manifest_sha256"]:
        raise ValueError("Runtime manifest identity mismatch")
    runtime = json.loads(runtime_bytes)
    for asset in runtime["assets"].values():
        decoded_asset(package, asset)
    # M6 consumes the accepted compiler/runtime unchanged. Any future runtime
    # edit must first be packaged and verified by the runtime workflow.
    core = ["layout-codec.js", "layout-runtime.js", "contracts.js", "dependencies.js"]
    for name in core:
        if (ROOT / "browser" / name).read_bytes() != (package / name).read_bytes():
            raise ValueError("Runtime source differs from accepted package: " + name)
    for key, name in (("worker", "layout-worker.js"), ("contracts", "contracts.js"), ("dependencies", "dependencies.js")):
        if digest((ROOT / "browser" / name).read_bytes()) != runtime["assets"][key]["sha256"]:
            raise ValueError("Worker source differs from accepted package: " + name)

    # Optional handbook links are included only when source bytes and packaged
    # payload hashes match. Downloads from the active request remain available
    # when a source wrapper is missing or the handbook is not alongside us.
    records_path = book / "source-records.json"
    records_bytes = records_path.read_bytes() if records_path.is_file() else None
    book_records = json.loads(records_bytes) if records_bytes is not None else {}
    by_source = {value["path"]: (url, value) for url, value in book_records.items()}
    book_root = Path(os.path.relpath(book, output)).as_posix() + "/"
    links, conflicts, observed, payloads = {}, set(), {}, {}
    for profile in runtime["profiles"]:
        data = json.loads(decoded_asset(package, profile["asset"]))
        if data["source"] != original["source"]:
            raise ValueError("Profile source mismatch")
        request = data["request"]
        for path, content in request["files"].items():
            physical = request.get("source_paths", {}).get(path)
            sha = digest(content.encode())
            for key in (path, physical):
                if key is None:
                    continue
                if key in observed and observed[key] != sha:
                    conflicts.add(key)
                observed[key] = sha
            if not physical or not physical.startswith("xnu/") or physical not in by_source:
                continue
            url, record = by_source[physical]
            if sha != record["sha256"] or not local_path(book, url).is_file():
                continue
            payload = local_path(book, record["payload"])
            if record["payload"] not in payloads:
                payloads[record["payload"]] = digest(payload.read_bytes()) if payload.is_file() else None
            if payloads[record["payload"]] != record["payload_sha256"]:
                continue
            for key in (path, physical):
                links[key] = book_root + url
    for key in conflicts:
        links.pop(key, None)
    config = {"bookRoot": book_root, "source": original["source"], "sourceLinks": links}
    sources = {name: ROOT / "browser" / name for name in ("layouts.html", "layouts.css", "layouts.js", "explorer-model.js")}
    sources["book.css"] = ROOT.parent / "book/assets/book.css"
    input_paths = [*sources.values(), Path(__file__).resolve(), ROOT.parent / "paths.py"]
    inputs = {str(path.relative_to(PROJECT_ROOT)): digest(path.read_bytes()) for path in input_paths}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".layout-explorer-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "explorer"
        stage.mkdir()
        (stage / ".layout-explorer").write_text("Platydoc live structure explorer\n")
        copied = [*core, "runtime-manifest.js", "runtime-manifest.json", "runtime-provenance.json", "toolchain-provenance.json", "native-validation.json", "bundle-manifest.json", "config-provenance.json"]
        copied.extend(name for name in original["files"] if name.startswith(("assets/", "licenses/")))
        for name in copied:
            destination = local_path(stage, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local_path(package, name), destination)
            raw = destination.read_bytes()
            identity = original["files"][name]
            if len(raw) != identity["bytes"] or digest(raw) != identity["sha256"]:
                raise ValueError("Runtime file changed during packaging: " + name)
        for name, path in sources.items():
            shutil.copyfile(path, stage / ("index.html" if name == "layouts.html" else name))
        (stage / "explorer-config.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutExplorerConfig=" + encoded(config) + b";\n")
        provenance = {"kind": "platydoc-layout-explorer-provenance", "version": 1, "inputs": inputs,
                      "runtime_package_manifest_sha256": digest(original_bytes),
                      "book_source_records_sha256": digest(records_bytes) if records_bytes is not None else None,
                      "note": "Explorer sources and standalone packaging; compiler/runtime provenance remains unchanged."}
        (stage / "explorer-provenance.json").write_bytes(encoded(provenance) + b"\n")
        (stage / "runtime-package-manifest.json").write_bytes(original_bytes)
        manifest = {"kind": "milestone-6-live-layout-explorer", "source": original["source"],
                    "runtime_manifest_sha256": digest(runtime_bytes), "runtime_package_manifest_sha256": digest(original_bytes),
                    "files": {}}
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                raw = path.read_bytes()
                manifest["files"][path.relative_to(stage).as_posix()] = {"bytes": len(raw), "sha256": digest(raw)}
        manifest["total_bytes"] = sum(value["bytes"] for value in manifest["files"].values())
        (stage / "manifest.json").write_bytes(encoded(manifest) + b"\n")
        for path, sha in inputs.items():
            if digest((PROJECT_ROOT / path).read_bytes()) != sha:
                raise ValueError("Explorer source changed during packaging: " + path)
        previous = Path(temporary) / "previous"
        if output.exists():
            output.rename(previous)
        try:
            stage.rename(output)
        except BaseException:
            if previous.exists():
                previous.rename(output)
            raise
    print(f"Live explorer: {output / 'index.html'} ({manifest['total_bytes']:,} bytes excluding manifest)")


if __name__ == "__main__":
    main()
