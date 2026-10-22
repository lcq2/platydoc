#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package lazy local assets for the worker-based offline layout runtime."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from paths import DOCS, PROJECT_ROOT, SOURCE_ROOT
from book.source_codec import _gzip
sys.path.insert(0, str(ROOT / "tests"))
from xnu_dependency_cases import load_cases, requests_hash, validate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_json(path, value):
    path.write_bytes(json_bytes(value) + b"\n")


def asset(stage, name, raw):
    sha = digest(raw)
    key = name + "-" + sha
    url = "assets/" + key + ".js"
    envelope = {"schema": 2, "encoding": "gzip-base64", "data": base64.b64encode(_gzip(raw)).decode("ascii")}
    (stage / url).write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\n// Encapsulated upstream bytes retain notices; see licenses/.\nLayoutRuntimeAssets.deliver(" + json_bytes(key) + b"," + json_bytes(envelope) + b");\n")
    return {"id": key, "url": url, "sha256": sha, "bytes": len(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("wasm", "native-report", "bundles", "config-root", "notices", "provenance", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    for protected in (DOCS.resolve(), SOURCE_ROOT.resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError("Runtime proof must be outside source and handbook trees")
    if output.exists():
        if not output.is_dir() or (any(output.iterdir()) and not (output / ".layout-runtime-proof").is_file()):
            raise ValueError("Refusing nonempty unmarked runtime proof output")
        if any(path.is_symlink() for path in output.rglob("*")):
            raise ValueError("Refusing symlinks within runtime proof output")

    report_bytes = args.native_report.read_bytes()
    comparison = json.loads(report_bytes)
    if comparison.get("kind") != "xnu-contexts" or comparison.get("wasm_parity") != "passed" or comparison.get("dependency_tracing") is not True:
        raise ValueError("Passing traced native/Wasm XNU report required")
    cases = load_cases(args.bundles)
    if comparison["cases"] != [name for name, _ in cases] or comparison["requests_sha256"] != requests_hash(cases):
        raise ValueError("Comparison does not describe current requests")
    for (name, _), result in zip(cases, comparison["results"], strict=True):
        validate(name, result)
    bundle_bytes = (args.bundles / "manifest.json").read_bytes()
    bundle = json.loads(bundle_bytes)
    if comparison["bundle_manifest_sha256"] != digest(bundle_bytes):
        raise ValueError("Header bundle changed after verification")
    config_bytes = (args.config_root / "config-provenance.json").read_bytes()
    if bundle["config_manifest_sha256"] != digest(config_bytes) or bundle["profile_spec_sha256"] != digest((ROOT / "profiles/arm64-xnu.json").read_bytes()):
        raise ValueError("Configuration provenance changed after bundling")
    provenance_bytes = args.provenance.read_bytes()
    provenance = json.loads(provenance_bytes)
    factory, wasm = args.wasm.read_bytes(), args.wasm.with_suffix(".wasm").read_bytes()
    for raw, comparison_key, artifact in ((factory, "wasm_factory_sha256", "build-wasm/bin/layout-engine.js"), (wasm, "wasm_sha256", "build-wasm/bin/layout-engine.wasm")):
        if digest(raw) != comparison[comparison_key] or digest(raw) != provenance["artifacts"][artifact]["sha256"]:
            raise ValueError("Compiler artifact differs from verification: " + artifact)
    if provenance["artifacts"]["build-native/bin/layout-engine"]["sha256"] != comparison["native_sha256"]:
        raise ValueError("Native compiler differs from verification")
    if provenance["pins"]["llvm"]["revision"] != comparison["results"][0]["compiler"]["revision"]:
        raise ValueError("Compiler revision differs from pin")
    # Compiler provenance describes the accepted compiler build. JavaScript-only
    # changes get a separate runtime snapshot; they do not rebuild LLVM.
    for name in ("engine.cpp", "CMakeLists.txt", "toolchain.lock.json", "build.py"):
        if digest((ROOT / name).read_bytes()) != provenance["inputs"].get(name):
            raise ValueError("Compiler build input changed: " + name)
    required = {"package_runtime_proof.py", "browser/layout-codec.js", "browser/layout-runtime.js", "browser/layout-worker.js", "browser/proof_runtime.js", "browser/runtime-proof.html", "browser/layout-proof.css", "browser/contracts.js", "browser/dependencies.js", "tests/xnu_cases.py", "tests/xnu_dependency_cases.py", "bundle_xnu.py", "profiles/arm64-xnu.json"}
    runtime_inputs = {str((ROOT / name).relative_to(PROJECT_ROOT)): digest((ROOT / name).read_bytes()) for name in sorted(required)}
    for path in (ROOT.parent / "paths.py", ROOT.parent / "book/source_codec.py"):
        runtime_inputs[str(path.relative_to(PROJECT_ROOT))] = digest(path.read_bytes())
    required_notices = {"LLVM-LICENSE.txt", "Clang-LICENSE.txt", "Emscripten-LICENSE.txt", "emsdk-LICENSE.txt"}
    if not required_notices.issubset(provenance["notices"]):
        raise ValueError("Missing compiler/runtime license provenance")
    for name, sha in provenance["notices"].items():
        if digest((args.notices / name).read_bytes()) != sha:
            raise ValueError("Upstream license changed: " + name)
    if (args.bundles / "notices/XNU-APPLE_LICENSE.txt").read_bytes() != (SOURCE_ROOT / "APPLE_LICENSE").read_bytes():
        raise ValueError("XNU license differs from selected source")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".layout-runtime-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "proof"
        stage.mkdir()
        (stage / ".layout-runtime-proof").write_text("Platydoc offline worker runtime proof\n")
        (stage / "assets").mkdir()
        shutil.copytree(args.notices, stage / "licenses")
        shutil.copyfile(SOURCE_ROOT / "APPLE_LICENSE", stage / "licenses/XNU-APPLE_LICENSE.txt")
        shutil.copyfile(PROJECT_ROOT / "LICENSE", stage / "licenses/Platydoc-GPL-2.0-only.txt")
        shutil.copyfile(PROJECT_ROOT / "LICENSE-DOCS", stage / "licenses/Platydoc-CC-BY-4.0.txt")
        plain = ["layout-codec.js", "layout-runtime.js", "contracts.js", "dependencies.js", "proof_runtime.js", "layout-proof.css"]
        for name in plain:
            shutil.copyfile(ROOT / "browser" / name, stage / name)
        shutil.copyfile(ROOT / "browser/runtime-proof.html", stage / "index.html")
        source = {"release": bundle["source_release"], "revision": bundle["source_commit"]}
        assets = {"factory": asset(stage, "factory", factory), "wasm": asset(stage, "wasm", wasm)}
        for key, name in [("contracts", "contracts.js"), ("dependencies", "dependencies.js"), ("worker", "layout-worker.js")]:
            assets[key] = asset(stage, key, (ROOT / "browser" / name).read_bytes())
        profiles = []
        for name, request in cases:
            if name not in bundle["profiles"]:
                continue
            profiles.append({"id": name, "label": name, "source": source,
                             "asset": asset(stage, "profile-" + name, json_bytes({"request": request, "source": source}))})
        compiler = comparison["results"][0]["compiler"]
        runtime = {"contract": "platydoc.layout-runtime-manifest", "version": 1,
                   "compiler": {"revision": compiler["revision"], "engine_sha256": compiler["engine_sha256"],
                                "wasm_sha256": digest(wasm), "factory_sha256": digest(factory)},
                   "assets": assets, "profiles": profiles}
        write_json(stage / "runtime-manifest.json", runtime)
        (stage / "runtime-manifest.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutRuntimeManifest=" + json_bytes(runtime) + b";\n")
        (stage / "toolchain-provenance.json").write_bytes(provenance_bytes)
        runtime_provenance = {"kind": "platydoc-layout-runtime-provenance", "version": 1,
                              "compiler_provenance_sha256": digest(provenance_bytes),
                              "inputs": runtime_inputs,
                              "note": "Compiler build provenance is historical; these hashes identify the current runtime and packaging sources."}
        write_json(stage / "runtime-provenance.json", runtime_provenance)
        (stage / "bundle-manifest.json").write_bytes(bundle_bytes)
        (stage / "config-provenance.json").write_bytes(config_bytes)
        write_json(stage / "native-validation.json", {"kind": "native-wasm-validation-reference", "status": "passed",
                   "comparison_sha256": digest(report_bytes), "requests_sha256": comparison["requests_sha256"],
                   "native_sha256": comparison["native_sha256"], "wasm_sha256": digest(wasm),
                   "cases": [{"name": name, "status": result["status"]} for name, result in zip(comparison["cases"], comparison["results"], strict=True)],
                   "note": "Complete native evidence is retained in the build workspace; no validation matrix runs on reader startup."})
        manifest = {"kind": "milestone-5-offline-worker-runtime-proof", "source": source, "scope": bundle["scope"],
                    "runtime_manifest_sha256": digest(json_bytes(runtime) + b"\n"), "wasm_bytes": len(wasm),
                    "compiler_provenance_sha256": digest(provenance_bytes),
                    "runtime_provenance_sha256": digest(json_bytes(runtime_provenance) + b"\n"),
                    "files": {}}
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                raw = path.read_bytes()
                manifest["files"][path.relative_to(stage).as_posix()] = {"bytes": len(raw), "sha256": digest(raw)}
        manifest["total_bytes"] = sum(entry["bytes"] for entry in manifest["files"].values())
        write_json(stage / "manifest.json", manifest)
        # Catch concurrent source edits before replacing the last generated proof.
        for name, sha in runtime_inputs.items():
            if digest((PROJECT_ROOT / name).read_bytes()) != sha:
                raise ValueError("Tool source changed during packaging: " + name)
        previous = Path(temporary) / "previous"
        if output.exists():
            output.rename(previous)
        try:
            stage.rename(output)
        except BaseException:
            if previous.exists():
                previous.rename(output)
            raise
    print(f"Offline runtime proof: {output / 'index.html'} ({manifest['total_bytes']:,} bytes excluding manifest)")


if __name__ == "__main__":
    main()
