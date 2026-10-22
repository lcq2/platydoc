#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package the verified real-XNU comparison for offline, direct-file browsing."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from paths import DOCS, PROJECT_ROOT, SOURCE_ROOT
from check_links import heading_ids
sys.path.insert(0, str(ROOT / "tests"))
from xnu_cases import load_cases, requests_hash, validate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def validate_chapter_mapping(mapping, source):
    """Check source bytes and real handbook headings before shared resolution."""
    if set(mapping) != {"contract", "version", "source", "entries"} or mapping["contract"] != "platydoc.layout-chapters" or mapping["version"] != 1:
        raise ValueError("Unsupported chapter mapping contract")
    if mapping["source"] != source or not isinstance(mapping["entries"], list) or not mapping["entries"]:
        raise ValueError("Chapter mapping does not describe the selected source")
    seen = set()
    for entry in mapping["entries"]:
        if set(entry) != {"source_path", "source_sha256", "offset_bytes", "kind", "display_name", "chapters"}:
            raise ValueError("Invalid chapter mapping entry")
        if entry["kind"] not in {"struct", "union", "alias"} or not isinstance(entry["display_name"], str):
            raise ValueError("Invalid mapped declaration kind/name")
        if type(entry["offset_bytes"]) is not int or not 0 <= entry["offset_bytes"] <= 9007199254740991:
            raise ValueError("Invalid declaration byte anchor")
        if not isinstance(entry["source_path"], str):
            raise ValueError("Invalid source path")
        path = (PROJECT_ROOT / entry["source_path"]).resolve()
        if not path.is_relative_to(SOURCE_ROOT.resolve()):
            raise ValueError("Mapped declaration must belong to XNU input")
        data = path.read_bytes()
        if digest(data) != entry["source_sha256"] or entry["offset_bytes"] >= len(data):
            raise ValueError("Mapped source changed; review its declaration anchor")
        anchor = (entry["source_path"], entry["offset_bytes"], entry["kind"])
        if anchor in seen:
            raise ValueError("Duplicate mapped declaration")
        seen.add(anchor)
        if not isinstance(entry["chapters"], list) or not entry["chapters"]:
            raise ValueError("Mapped declaration needs a chapter destination")
        for target in entry["chapters"]:
            if not isinstance(target, str) or target.count("#") != 1:
                raise ValueError("Chapter destination requires a heading anchor")
            page, heading = target.split("#")
            destination = (DOCS / page).resolve()
            if Path(page).is_absolute() or not destination.is_relative_to(DOCS.resolve()) or destination.suffix != ".md":
                raise ValueError("Chapter destination must be inside the handbook")
            if heading not in heading_ids(destination):
                raise ValueError("Missing chapter heading: " + target)


def contract_command(payload):
    with tempfile.TemporaryFile(mode="w+") as stream:
        json.dump(payload, stream)
        stream.seek(0)
        result = subprocess.run(["node", str(ROOT / "tests/contracts_cli.cjs")], stdin=stream,
                                capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise ValueError("Contract validation failed: " + result.stderr)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("wasm", "native-report", "bundles", "config-root", "notices", "provenance", "output"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    for protected in (DOCS.resolve(), SOURCE_ROOT.resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError("Proof output must be outside source and handbook trees")
    if output.exists():
        if any(output.iterdir()) and not (output / ".layout-xnu-proof").is_file():
            raise ValueError("Refusing nonempty unmarked proof output")
        if any(path.is_symlink() for path in output.rglob("*")):
            raise ValueError("Refusing symlinks within proof output")
    comparison = json.loads(args.native_report.read_bytes())
    dependency_mode = comparison.get("dependency_tracing", False)
    case_loader, validate_result = load_cases, validate
    if dependency_mode:
        from xnu_dependency_cases import load_cases as case_loader, validate as validate_result
    cases = case_loader(args.bundles)
    if comparison.get("kind") != "xnu-contexts" or comparison.get("wasm_parity") != "passed":
        raise ValueError("Passing real-XNU native/Wasm comparison required")
    if comparison["cases"] != [name for name, _ in cases] or comparison["requests_sha256"] != requests_hash(cases):
        raise ValueError("Comparison does not describe the current requests")
    for (name, _), result in zip(cases, comparison["results"], strict=True):
        validate_result(name, result)
    bundle_bytes = (args.bundles / "manifest.json").read_bytes()
    bundle = json.loads(bundle_bytes)
    if comparison["bundle_manifest_sha256"] != digest(bundle_bytes):
        raise ValueError("Bundle manifest changed after comparison")
    config_bytes = (args.config_root / "config-provenance.json").read_bytes()
    if bundle["config_manifest_sha256"] != digest(config_bytes):
        raise ValueError("Configuration provenance differs from bundle")
    if bundle["profile_spec_sha256"] != digest((ROOT / "profiles/arm64-xnu.json").read_bytes()):
        raise ValueError("Profile specification changed after bundling")
    provenance = json.loads(args.provenance.read_bytes())
    factory = args.wasm.read_bytes()
    binary = args.wasm.with_suffix(".wasm").read_bytes()
    for data, key, artifact in (
        (factory, "wasm_factory_sha256", "build-wasm/bin/layout-engine.js"),
        (binary, "wasm_sha256", "build-wasm/bin/layout-engine.wasm"),
    ):
        if digest(data) != comparison[key] or provenance["artifacts"][artifact]["sha256"] != digest(data):
            raise ValueError("Compiler artifact differs from comparison/provenance: " + artifact)
    if provenance["artifacts"]["build-native/bin/layout-engine"]["sha256"] != comparison["native_sha256"]:
        raise ValueError("Native compiler provenance differs from comparison")
    if provenance["pins"]["llvm"]["revision"] != comparison["results"][0]["compiler"]["revision"]:
        raise ValueError("Compiler revision mismatch")
    # Packaging must follow the final provenance refresh, including these files.
    inputs = provenance.get("inputs", {})
    required_inputs = ["package_xnu_proof.py", "browser/proof_xnu.js", "browser/contracts.js",
                       "tests/contracts_cli.cjs", "tests/xnu_cases.py", "tests/compare_xnu.py"]
    if dependency_mode:
        required_inputs.extend(["browser/dependencies.js", "tests/xnu_dependency_cases.py"])
    for required in required_inputs:
        if required not in inputs:
            raise ValueError("Refresh build provenance before packaging: missing " + required)
    for name, expected in inputs.items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError("Tool source changed after provenance refresh: " + name)
    required_notices = {"LLVM-LICENSE.txt", "Clang-LICENSE.txt", "Emscripten-LICENSE.txt", "emsdk-LICENSE.txt"}
    if not required_notices.issubset(provenance["notices"]):
        raise ValueError("Missing upstream license provenance")
    for name, expected in provenance["notices"].items():
        if digest((args.notices / name).read_bytes()) != expected:
            raise ValueError("Upstream notice changed: " + name)
    if (args.bundles / "notices/XNU-APPLE_LICENSE.txt").read_bytes() != (SOURCE_ROOT / "APPLE_LICENSE").read_bytes():
        raise ValueError("XNU license differs from source")

    source = {"release": bundle["source_release"], "revision": bundle["source_commit"]}
    entries = []
    for (name, request), result in zip(cases, comparison["results"], strict=True):
        metadata = {"source": source, "whatIf": name.startswith("probe-")}
        if metadata["whatIf"]:
            metadata["base_profile"] = "release-t8103"
        if name.startswith(("release-", "development-")):
            metadata["profile"] = name
        entries.append({"name": name, "request": request, "result": result, "metadata": metadata})
    analysis = None
    if dependency_mode:
        discovered = json.loads(contract_command({"command": "discover", "entries": entries, "space_id": "xnu-pilot"}))
        documents, analysis = discovered["documents"], discovered["analysis"]
        normalized = json.dumps(documents, separators=(",", ":"), sort_keys=True) + "\n"
    else:
        normalized = contract_command({"command": "create", "entries": entries})
        documents = json.loads(normalized)
    mapping_bytes = (DOCS / "structures/layouts.json").read_bytes()
    mapping = json.loads(mapping_bytes)
    validate_chapter_mapping(mapping, source)
    bindings = contract_command({"command": "map", "mapping": mapping, "analysis": analysis,
                                 "documents": [document for document in documents
                                               if document["configuration"]["classification"] == "validated-profile"]})

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".layout-xnu-proof-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "proof"
        stage.mkdir()
        (stage / ".layout-xnu-proof").write_text("Platydoc standalone real-XNU proof\n")
        (stage / "layout-engine.js").write_bytes(factory)
        shutil.copyfile(ROOT / "browser/proof_xnu.js", stage / "proof.js")
        shutil.copyfile(ROOT / "browser/contracts.js", stage / "contracts.js")
        if dependency_mode:
            shutil.copyfile(ROOT / "browser/dependencies.js", stage / "dependencies.js")
            (stage / "dependencies.json").write_text(json.dumps(analysis, separators=(",", ":"), sort_keys=True) + "\n")
        (stage / "contracts.json").write_text(normalized)
        (stage / "layout-chapters.json").write_bytes(mapping_bytes)
        (stage / "chapter-bindings.json").write_text(bindings)
        shutil.copytree(args.notices, stage / "licenses")
        shutil.copyfile(args.bundles / "notices/XNU-APPLE_LICENSE.txt", stage / "licenses/XNU-APPLE_LICENSE.txt")
        shutil.copyfile(PROJECT_ROOT / "LICENSE", stage / "licenses/Platydoc-GPL-2.0-only.txt")
        shutil.copyfile(PROJECT_ROOT / "LICENSE-DOCS", stage / "licenses/Platydoc-CC-BY-4.0.txt")
        shutil.copyfile(args.provenance, stage / "toolchain-provenance.json")
        shutil.copyfile(args.native_report, stage / "comparison.json")
        (stage / "bundle-manifest.json").write_bytes(bundle_bytes)
        (stage / "config-provenance.json").write_bytes(config_bytes)
        shutil.copyfile(ROOT / "profiles/arm64-xnu.json", stage / "profiles.json")
        (stage / "profile-manifests").mkdir()
        for name, profile in bundle["profiles"].items():
            shutil.copyfile(args.bundles / profile["directory"] / "manifest.json",
                            stage / "profile-manifests" / (name + ".json"))

        # Shared strings keep identical headers from being embedded per case.
        # Virtual paths remain per-request; raw exact bytes are downloadable once.
        headers = {}
        descriptors = []
        (stage / "headers").mkdir()
        for name, request in cases:
            descriptor = {key: value for key, value in request.items() if key != "files"}
            references = {}
            for path, content in request["files"].items():
                key = digest(content.encode("utf-8"))
                if key not in headers:
                    headers[key] = content
                    (stage / "headers" / (key + ".txt")).write_bytes(content.encode("utf-8"))
                references[path] = key
            descriptors.append({"name": name, "request": descriptor, "file_refs": references})
        write_json(stage / "header-map.json", {entry["name"]: entry["file_refs"] for entry in descriptors})
        chunks = [base64.b64encode(binary[i:i + 49152]).decode("ascii") for i in range(0, len(binary), 49152)]
        payload = (
            "// Original headers/compiler bytes retain notices; see licenses/ and manifests.\n"
            "function decodeLayoutWasm(){const chunks=" + json.dumps(chunks) + ";\n"
            f"const bytes=new Uint8Array({len(binary)});let offset=0;\n"
            "for(const chunk of chunks){const raw=atob(chunk);for(let i=0;i<raw.length;++i)bytes[offset++]=raw.charCodeAt(i);}return bytes;}\n"
            "(()=>{const headers=" + json.dumps(headers) + ";\n"
            "const descriptions=" + json.dumps(descriptors) + ";\n"
            "window.layoutHeaderMaps=Object.fromEntries(descriptions.map(entry=>[entry.name,entry.file_refs]));\n"
            "window.layoutCases=descriptions.map(entry=>({name:entry.name,request:{...entry.request,files:Object.fromEntries(Object.entries(entry.file_refs).map(([path,key])=>[path,headers[key]]))}}));})();\n"
            "window.layoutExpected=" + json.dumps(comparison["results"]) + ";\n"
            "window.layoutExpectedContracts=" + normalized.strip() + ";\n"
        )
        if dependency_mode:
            payload += "window.layoutExpectedDependencyAnalysis=" + json.dumps(analysis, separators=(",", ":"), sort_keys=True) + ";\n"
        (stage / "payload.js").write_text(payload)
        html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Offline XNU structure layouts</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>window.layoutProofStart=performance.now();</script>
<style>body{font:16px system-ui;max-width:110ch;margin:2em auto;padding:0 1em;color:#20242a;background:#f8fafc}table{border-collapse:collapse;width:100%;margin:1em 0}th,td{border:1px solid #ccd1d6;padding:.45em;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:1em 0}code{overflow-wrap:anywhere}caption{text-align:left;font-weight:bold}section{border-top:1px solid #ccd1d6;margin-top:2em}a{color:#0645ad}label{display:inline-block;margin:.5em 1em .5em 0}select,input,textarea,button{font:inherit;padding:.4em;max-width:100%;box-sizing:border-box}textarea{display:block;width:100%;font-family:monospace}button{cursor:pointer}#explorer{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:1.2em;margin:1.5em 0}#layout-meta{font:600 .9em ui-monospace,SFMono-Regular,Consolas,monospace;padding:.8em;background:#eaf1f8;border-radius:5px;margin:.8em 0}#layout-tree{font:14px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-x:auto;padding:.7em 0;color:#24344b}.record-brace{font-weight:600;padding:.15em .5em}.field-node{position:relative;margin:0;padding:0 0 0 1.25em;min-width:35em}.declaration-row{display:grid;grid-template-columns:7.5em minmax(15em,1fr) 4em;gap:.7em;align-items:baseline;padding:.12em 2em .12em .25em;cursor:default;border-radius:3px}.declaration-row:hover{background:#f0f5fa}details.field-node>summary{cursor:pointer;list-style:none}details.field-node>summary::-webkit-details-marker{display:none}details.field-node>summary:before{content:'▸';position:absolute;left:.15em;color:#64748b}details.field-node[open]>summary:before{content:'▾'}.field-offset{color:#64748b;white-space:nowrap;font-variant-numeric:tabular-nums}.field-declaration{color:#123e64;white-space:pre-wrap;overflow-wrap:normal}.field-size{color:#718198;text-align:right;font-size:.85em}.declaration-open{display:none}details.field-node[open]>summary .declaration-closed{display:none}details.field-node[open]>summary .declaration-open{display:inline}.field-children{margin-left:1.25em;border-left:1px solid #e3eaf2}.record-close{padding:.1em 0 .2em 8.75em;color:#123e64}.field-info{position:absolute;right:.1em;top:.05em;margin:0;font:12px/1.6 system-ui;color:#45556b;z-index:1}.field-info>summary{list-style:none;cursor:pointer;color:#718198;padding:0 .35em}.field-info>summary::-webkit-details-marker{display:none}.field-info[open]{background:#fff;border:1px solid #cbd5e1;box-shadow:0 3px 12px #24344b18;padding:.35em .6em;max-width:38em}.field-info[open]>div{overflow-wrap:anywhere}.field-info a{display:block}.array-preview{margin:.25em .3em .4em 8.75em;border-left:2px solid #c6d6e6;padding:.2em .6em;background:#f8fafc}.array-preview>small{display:block}.array-preview label{font:12px system-ui;margin:.3em 0}.array-preview input{width:6em;margin-left:.5em;padding:.2em .4em}.array-preview>.field-children{margin-left:0;border:0}.array-preview .field-node{min-width:25em}.array-preview .declaration-row{grid-template-columns:7.5em minmax(10em,1fr) 3em}.array-preview .field-info{right:0}.array-preview .array-preview{margin-left:1.25em}.element-preview{border-top:1px dashed #d9e2ec}.offset{font-variant-numeric:tabular-nums}.layout-columns{display:grid;grid-template-columns:7.5em minmax(15em,1fr) 6em;gap:.7em;font:12px ui-monospace,monospace;color:#64748b;padding:.6em 1em .25em 2em;border-bottom:1px solid #e3eaf2}#layout-error{color:#9a2020}.controls{display:flex;flex-wrap:wrap;align-items:end;gap:.3em}small{color:#45556b}[hidden]{display:none!important}</style>
</head><body><h1>Offline XNU structure layouts</h1>
<p>Clang runs locally in WebAssembly and analyzes complete, unmodified XNU headers. This proof checks results against the native compiler and validates the shared layout contracts.</p>
<p>Source: <strong>xnu-12377.121.6</strong>. Four explicit ARM64 Darwin analysis profiles cover release/development and T8103/VMAPPLE. These are not identified shipping-kernel ABIs. The compiler is upstream Clang 20.1.8; a CPU name does not imply support for Apple-private compiler features. Arm64e and Apple bounds-safety modes are not enabled.</p>
<section id="explorer" aria-labelledby="explorer-title"><h2 id="explorer-title">Layout browser preview</h2>
<p>C-style layout view. Offsets in the left gutter are hexadecimal bytes from the root structure; bit-fields retain their bit remainder. Hover or open ⓘ for local offsets and source. Expanded types and selected array elements are layout previews, not verbatim C source.</p>
<div class="controls"><label>Profile<br><select id="layout-profile" disabled></select></label><label>Structure<br><select id="layout-record" disabled><option value="task">task</option><option value="recount_track">recount_track</option></select></label></div>
<details><summary>Preprocessor configuration</summary>
<p>Enter object-like <code>#define NAME value</code> or <code>#undef NAME</code> directives, one per line. Headers can redefine these values; inspect the effective configuration below. Manual changes are what-if analyses, outside the verified profile matrix. Newly enabled branches may need headers absent from the selected bundle.</p>
<label for="layout-directives">Overrides (optional)</label><textarea id="layout-directives" rows="4" spellcheck="false" placeholder="#define CONFIG_TASK_SUSPEND_STATS 0" disabled></textarea>
<button id="layout-apply" type="button" disabled>Apply configuration</button> <button id="layout-reset" type="button" disabled>Reset to profile</button>
<details><summary>Requested directives, effective values and target features</summary><div id="layout-config"></div></details></details>
<p id="layout-status" role="status">Waiting for compiler checks…</p><pre id="layout-error" role="alert"></pre><div id="layout-meta" hidden></div>
<label for="layout-search">Find a field or field path</label><input id="layout-search" type="search" placeholder="task.ref_count" disabled>
<div class="layout-columns" aria-hidden="true">Root offset <span>Declaration</span><span>Size (bytes)</span></div><div id="layout-tree"></div></section>
<p id="status" role="status">Loading compiler…</p>
<table><caption>Supported profiles — size and alignment in bytes</caption><thead><tr><th>Profile</th><th>recount_track size</th><th>task size</th><th>Alignment (both)</th><th>Native comparison</th></tr></thead><tbody id="summary"></tbody></table>
<div id="results"></div>
<h2>Measurements</h2><p>Parsing runs on the main thread in this prototype. Linear memory is Wasm buffer capacity, not live allocation or browser process memory. Times include request/result serialization.</p>
<pre id="metrics"></pre><pre id="stderr"></pre>
<p><a href="manifest.json">Package manifest</a> · <a href="profiles.json">Profile definitions</a> · <a href="header-map.json">Virtual paths to exact header bytes</a> (files in <code>headers/&lt;SHA-256&gt;.txt</code>) · <a href="comparison.json">Native/Wasm results</a></p>
<p><a href="contracts.json">Versioned layout contracts</a> · <a href="layout-chapters.json">Authored chapter mapping</a> · <a href="chapter-bindings.json">Resolved chapter bindings</a>. The chapter mapping uses <a href="licenses/Platydoc-CC-BY-4.0.txt">CC BY 4.0</a>.</p>
<p>Platydoc software: <a href="licenses/Platydoc-GPL-2.0-only.txt">GPL-2.0-only</a>. Copied headers retain their original notices. See the <a href="licenses/XNU-APPLE_LICENSE.txt">XNU license</a>. Compiler/runtime notices include <a href="licenses/LLVM-LICENSE.txt">LLVM</a> and <a href="licenses/Emscripten-LICENSE.txt">Emscripten</a>.</p>
<script src="layout-engine.js"></script><script src="payload.js"></script><script src="contracts.js"></script><script src="proof.js"></script>
</body></html>
'''
        if dependency_mode:
            html = html.replace('<script src="proof.js"></script>', '<script src="dependencies.js"></script><script src="proof.js"></script>')
            html = html.replace('<a href="contracts.json">Versioned layout contracts</a>', '<a href="dependencies.json">Configuration-dependency evidence</a> · <a href="contracts.json">Versioned layout contracts</a>')
        (stage / "index.html").write_text(html)
        manifest = {"kind": "milestone-4-real-xnu-dependency-proof" if dependency_mode else "milestone-3-real-xnu-contract-proof", "scope": bundle["scope"],
                    "source_commit": bundle["source_commit"], "requests_sha256": comparison["requests_sha256"],
                    "chapter_mapping_sha256": digest(mapping_bytes),
                    "compiler": comparison["results"][0]["compiler"], "wasm_bytes": len(binary),
                    "unique_header_files": len(headers), "files": {}}
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                manifest["files"][path.relative_to(stage).as_posix()] = {"bytes": len(data), "sha256": digest(data)}
        manifest["total_bytes"] = sum(value["bytes"] for value in manifest["files"].values())
        write_json(stage / "manifest.json", manifest)
        previous = Path(temporary) / "previous"
        if output.exists():
            output.rename(previous)
        try:
            stage.rename(output)
        except BaseException:
            if previous.exists():
                previous.rename(output)
            raise
    print(f"Offline XNU proof: {output / 'index.html'} ({manifest['total_bytes']:,} bytes excluding manifest)")


if __name__ == "__main__":
    main()
