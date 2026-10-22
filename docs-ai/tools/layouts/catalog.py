#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Generate the handbook layout catalog from provisioned, pinned offline inputs.

This module never downloads dependencies or builds LLVM. The common-profile
cache supplies catalog/binding generation; reader analyses still use the worker.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
from html import escape
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import parse_qsl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS
sys.path.insert(0, str(HERE))
from package_explorer import decoded_asset, local_path
from package_xnu_proof import validate_chapter_mapping

PAGE = "structures/layout-browser.html"
MARKER = "structure-layout-explorer"
PURPOSE = "Searchable pilot declarations and common-profile source bindings; live views compile in the worker."
CATALOG_PURPOSE = "Finite documented C structure survey and validated source bindings; live views compile in the worker."


def expanded(lock):
    return lock.get("version") == 2


def profile_ids(lock):
    return lock["expected_profiles"] if expanded(lock) else ["release-t8103", "development-t8103", "release-vmapple", "development-vmapple"]


def lock_path(runtime):
    package = read_json(runtime / "manifest.json")
    return HERE / ("artifact-ios.lock.json" if package.get("kind") == "milestone-8-offline-structure-catalog-runtime" else "artifact.lock.json")


def coverage_summary(lock, selections):
    return {"status": "finite-documented-survey" if expanded(lock) else "pilot", "roots": [row["key"] for row in selections],
            "dependencies": "not-computed-in-common-cache"}


def selections_for(mapping, entries, coverage=None):
    """Bind source anchors, never a same-name AST fallback across definitions."""
    selections = []
    if coverage is not None:
        mapped_keys = set()
        for entry in coverage["entries"]:
            matches = {cell["context_id"]: cell["declaration_id"] for cell in entry["profiles"].values() if cell["status"] == "supported"}
            if matches:
                mapped = [row for row in mapping['entries'] if row['display_name'] == entry['key']]
                if len(mapped) != 1 or mapped[0]['chapters'] != entry['chapters'] or {key: value for key, value in mapped[0].items() if key not in {'display_name', 'chapters'}} not in entry['source_candidates']:
                    raise ValueError('Supported survey root lacks its exact authored chapter/source binding')
                mapped_keys.add(entry['key'])
            for context, identity in matches.items():
                document = next(item["document"] for item in entries if item["profile"] == context)
                found = [declaration for declaration in document["declarations"]["entries"] if declaration["id"] == identity]
                if len(found) != 1:
                    raise ValueError("Survey binding missing from validated common-profile contract")
                point = found[0]["source"]["spelling"]
                if {"kind": found[0]["kind"], "source_path": point["source_path"], "source_sha256": point["sha256"], "offset_bytes": point["offset_bytes"]} not in entry["source_candidates"]:
                    raise ValueError("Survey binding does not match authored physical source")
            selections.append({"key": entry["key"], "declarations": matches, "chapters": entry["chapters"]})
        if {row['display_name'] for row in mapping['entries']} != mapped_keys or len(mapping['entries']) != len(mapped_keys):
            raise ValueError('Authored bindings exceed or omit supported finite survey roots')
    else:
        for mapped in mapping["entries"]:
            matches = {}
            for entry in entries:
                found = [d for d in entry["document"]["declarations"]["entries"] if d["kind"] == mapped["kind"] and d["source"]["spelling"]["source_path"] == mapped["source_path"] and d["source"]["spelling"]["sha256"] == mapped["source_sha256"] and d["source"]["spelling"]["offset_bytes"] == mapped["offset_bytes"]]
                if len(found) != 1:
                    raise ValueError("Mapped catalog source anchor is unavailable/ambiguous")
                matches[entry["profile"]] = found[0]["id"]
            selections.append({"key": mapped["display_name"], "declarations": matches, "chapters": mapped["chapters"]})
    if len({row["key"] for row in selections}) != len(selections):
        raise ValueError("Duplicate authored layout selection key")
    return selections


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


def runtime_files(package):
    return ["layout-codec.js", "layout-runtime.js", "contracts.js", "dependencies.js", "runtime-manifest.json",
            "runtime-manifest.js", "runtime-provenance.json", "toolchain-provenance.json", "config-provenance.json", "bundle-manifest.json", "native-validation.json"] + (["coverage.json", "coverage-evidence.json", "profile-spec.json", "structure-inventory.json"] if package.get("kind") == "milestone-8-offline-structure-catalog-runtime" else []) + [name for name in package["files"] if name.startswith(("assets/", "licenses/", "generated-syscalls/", "generated-mig/", "ubc-inputs/"))]


def declaration_rows(entries):
    declarations = {}
    for entry in entries:
        for declaration in entry["document"]["declarations"]["entries"]:
            if declaration["kind"] not in {"struct", "union"}:
                continue
            row = declarations.setdefault(declaration["id"], {"id": declaration["id"], "name": declaration["name"], "kind": declaration["kind"], "source": declaration["source"], "profiles": [], "fields": []})
            row["profiles"].append(entry["profile"])
            fields = [d["name"] for d in entry["document"]["declarations"]["entries"] if d.get("owner_id") == declaration["id"] and d["kind"] == "field"]
            row["fields"] = sorted(set(row["fields"] + fields))
    return sorted(declarations.values(), key=lambda row: row["id"])


def inventory(root):
    """Include membership, ignored/untracked files and bytes; omit Git metadata."""
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            raise ValueError("Layout source inventory cannot contain symlinks: " + str(path))
        if path.is_file():
            result[relative.as_posix()] = digest(path.read_bytes())
        elif not path.is_dir():
            raise ValueError("Layout source inventory contains a nonregular entry")
    return result


def checked_file(root, relative, sha):
    path = local_path(root, relative)
    if digest(path.read_bytes()) != sha:
        raise ValueError("Pinned layout input changed: " + str(path))
    return path


def tool_inputs():
    names = ["catalog.py", "catalog_contracts.cjs", "artifact.lock.json", "profiles/arm64-xnu.json",
             "browser/contracts.js", "browser/dependencies.js", "browser/explorer-model.js",
             "browser/layouts.js", "browser/layouts.css", "browser/layouts.html",
             "browser/book-layouts.js", "generate_configs.py", "bundle_xnu.py", "package_explorer.py", "package_xnu_proof.py"]
    names += ["coverage.py", "layout_exports.py", "survey_catalog.py", "generate_sysproto.py", "generate_mig.py", "ubc_inputs.py", "compatibility/CoreEntitlements/V2/API.h", "compatibility/CoreEntitlements/V2/Kernel.h", "profiles/ios-catalog.json", "profiles/structure-catalog.json"]
    if (HERE / "artifact-ios.lock.json").is_file():
        names.append("artifact-ios.lock.json")
    paths = [HERE / name for name in names] + [HERE.parent / "paths.py", HERE.parent / "check_links.py", HERE.parent / "book/source_codec.py",
                                            HERE.parent / "book/build.py", HERE.parent / "book/verify.py", HERE.parent / "book/assets/book.js"]
    return {path.relative_to(PROJECT_ROOT).as_posix(): digest(path.read_bytes()) for path in paths}


def generation_provenance(identities, lock, snapshot, mapping):
    return {"contract": "platydoc.layout-generation-provenance", "version": 1, "identity": identities,
            "runtime_package_sha256": lock["runtime_package_manifest_sha256"], "source_inventory_sha256": digest(encoded(snapshot)),
            "mapping_sha256": digest(encoded(mapping)), "configuration_sha256": lock["config_provenance_sha256"],
            "native_sha256": lock["native_sha256"], "runtime_manifest_sha256": lock["runtime_manifest_sha256"],
            "cache_purpose": "Catalog/contracts/bindings only; no prewarmed browser worker or cached override results."}


def generated_sources(runtime, bundle, snapshot=None):
    """Check generated headers against their preserved original-generator evidence."""
    generated = bundle.get('generated_syscalls')
    sources = snapshot if snapshot is not None else bundle['source_evidence']
    if generated is not None:
        from generate_sysproto import validate_manifest
        validate_manifest(generated, sources, bundle['tool_inputs']['generate_sysproto.py'])
        if read_json(runtime / 'generated-syscalls/generation.json') != generated:
            raise ValueError('Generated syscall provenance differs from surveyed input')
        for name, sha in generated['files'].items():
            checked_file(runtime / 'generated-syscalls', name, sha)
    mig = bundle.get('generated_mig')
    if mig is not None:
        from generate_mig import validate_manifest as validate_mig
        spec = read_json(runtime / 'profile-spec.json')
        validate_mig(mig, spec, bundle['profile_spec_sha256'], bundle['config_manifest_sha256'],
                     sources, bundle['tool_inputs']['generate_mig.py'])
        if read_json(runtime / 'generated-mig/generation.json') != mig:
            raise ValueError('Generated MIG provenance differs from surveyed input')
        for profile in mig['profiles'].values():
            for name, sha in profile['files'].items():
                checked_file(runtime / 'generated-mig', profile['directory'] + '/' + name, sha)
        checked_file(runtime / 'generated-mig', 'MIG-APPLE_LICENSE.txt', mig['license_sha256'])
    ubc = bundle.get('ubc_layout_inputs')
    if ubc is not None:
        from ubc_inputs import validate_manifest
        validate_manifest(ubc, read_json(runtime / 'profile-spec.json'))
        if read_json(runtime / 'ubc-inputs/provenance.json') != ubc:
            raise ValueError('UBC dependency provenance differs from surveyed input')
        for name, origin in ubc['files'].items():
            checked_file(runtime / 'ubc-inputs', name, origin['sha256'])
        checked_file(runtime / 'ubc-inputs', 'TRUSTCACHE-APPLE_LICENSE.txt', ubc['license_sha256'])
    return generated


def validate_coverage_package(runtime, manifest, bundle):
    """Recheck the finite survey offline, without trusting coverage labels alone."""
    from coverage import validate as validate_coverage
    from survey_catalog import root_meaning
    coverage = read_json(runtime / "coverage.json")
    authored = read_json(runtime / "structure-inventory.json")
    spec = read_json(runtime / "profile-spec.json")
    generated_sources(runtime, bundle)
    if digest((runtime / "structure-inventory.json").read_bytes()) != bundle["inventory_sha256"] or digest((runtime / "profile-spec.json").read_bytes()) != bundle["profile_spec_sha256"]:
        raise ValueError("Packaged survey inventory/profile identity differs from bundle")
    result = validate_coverage(coverage, authored, bundle)
    if spec["platform"] != "iPhoneOS" or spec["target"] != "arm64e-apple-ios" or spec.get("ptrauth_calls") is not True or spec.get("ptrauth_intrinsics") is not True:
        raise ValueError("Expanded iOS contexts lost required arm64e/PAC features")
    evidence = read_json(runtime / "coverage-evidence.json")
    if set(evidence) != {"contract", "version", "comparison", "surveys"} or evidence["contract"] != "platydoc.layout-coverage-evidence" or evidence["version"] != 1:
        raise ValueError("Unsupported offline survey evidence schema")
    comparison, reference = evidence["comparison"], read_json(runtime / "native-validation.json")
    if comparison.get('kind') != 'xnu-catalog-contexts' or comparison.get('version') != 1 or comparison.get('dependency_tracing') is not True or comparison.get('requests_hash_algorithm') != 'length-prefixed-canonical-json-v1':
        raise ValueError('Unsupported finite survey comparison schema')
    if reference["status"] != "passed" or reference["comparison_sha256"] != digest(encoded(comparison) + b"\n") or comparison["wasm_parity"] != "passed" or comparison["target"] != spec["target"] or comparison["source"] != authored["source"]:
        raise ValueError("Survey comparison is not the packaged native/Wasm evidence")
    if reference["coverage_sha256"] != digest((runtime / "coverage.json").read_bytes()) or comparison['coverage_sha256'] != reference['coverage_sha256'] or comparison['bundle_manifest_sha256'] != digest((runtime / 'bundle-manifest.json').read_bytes()):
        raise ValueError("Survey coverage differs from native/Wasm validation")
    for comparison_name, manifest_name in [('wasm_sha256', 'wasm_sha256'), ('wasm_factory_sha256', 'factory_sha256')]:
        if comparison[comparison_name] != manifest['compiler'][manifest_name]:
            raise ValueError('Survey compiler artifact differs from runtime')
    if comparison['native_sha256'] != reference['native_sha256'] or comparison['wasm_sha256'] != reference['wasm_sha256']:
        raise ValueError('Survey compiler artifacts differ from validation reference')
    expected_cases = list(bundle["profiles"]) + list(bundle["unsupported"])
    if 'release-t8103--kernel' in bundle['profiles']:
        expected_cases += ['release-t8103--kernel--no-cpi', 'release-t8103--kernel--private-undefined']
    cases = dict(zip(comparison["cases"], comparison["results"], strict=True))
    if comparison["cases"] != expected_cases or len(cases) != len(expected_cases) or set(comparison['case_evidence']) != set(expected_cases):
        raise ValueError("Missing/duplicate/unexpected native/Wasm context or boundary evidence")
    expected_reference = [{'name': name, 'status': cases[name]['status'], **comparison['case_evidence'][name]} for name in expected_cases]
    if reference['cases'] != expected_reference or reference['requests_sha256'] != comparison['requests_sha256']:
        raise ValueError('Native/Wasm reference differs from comparison case evidence')
    for name, compiled in cases.items():
        if digest(encoded(compiled) + b'\n') != comparison['case_evidence'][name]['compact_result_sha256']:
            raise ValueError('Comparison compact result hash differs: ' + name)
        if not isinstance(compiled.get('compiler'), dict) or any(compiled['compiler'].get(key) != manifest['compiler'][key] for key in ('revision', 'engine_sha256')):
            raise ValueError('Comparison case compiler identity differs: ' + name)
    profiles = {profile["id"]: profile for profile in manifest["profiles"]}
    if set(profiles) != set(bundle["profiles"]):
        raise ValueError("Survey runtime contexts differ from validated comparison")
    for name in bundle["profiles"]:
        compiled = cases[name]
        request = json.loads(decoded_asset(runtime, profiles[name]["asset"]))["request"]
        if request["target"] != spec["target"] or request.get("ptrauth_intrinsics") is not True or request.get("ptrauth_calls") is not True or compiled["status"] != "ok" or compiled["diagnostics"]:
            raise ValueError("Runtime survey context failed required compiler/PAC invariants")
        identity = comparison["case_evidence"][name]
        if digest(encoded(request) + b"\n") != identity["runtime_request_sha256"] or digest(encoded(compiled) + b"\n") != identity["compact_result_sha256"]:
            raise ValueError("Runtime request/layout differs from comparison")
    surveys = {}
    for row in evidence["surveys"]:
        if set(row) != {"key", "base_profile", "request_sha256", "native_result_sha256", "transport_status", "diagnostics", "layout_meaning_sha256"}:
            raise ValueError("Invalid offline survey cell evidence")
        key = (row["key"], row["base_profile"])
        if key in surveys:
            raise ValueError("Duplicate offline survey cell evidence")
        surveys[key] = row
    expected = set()
    for entry in coverage["entries"]:
        for base, cell in entry["profiles"].items():
            key = (entry["key"], base); expected.add(key)
            row = surveys.get(key)
            if row is None or any(row[name] != cell[name] for name in ("request_sha256", "native_result_sha256", "transport_status", "diagnostics")):
                raise ValueError("Offline survey cell evidence differs from coverage")
            if cell["status"] == "supported":
                compiled = cases[cell["context_id"]]
                meaning = digest(encoded(root_meaning(compiled, entry["record"])) + b"\n")
                matching = [record for record in compiled["records"] if record["id"] == cell["declaration_id"] and record["name"] == entry["record"]]
                if row["layout_meaning_sha256"] != meaning or len(matching) != 1:
                    raise ValueError("Offline survey geometry differs from validated merged context")
                declarations = [declaration for declaration in compiled['declarations'] if declaration['id'] == cell['declaration_id']]
                if len(declarations) != 1:
                    raise ValueError('Offline survey source declaration is unavailable/ambiguous')
                point = declarations[0]['source']['spelling']
                if {'kind': declarations[0]['kind'], 'source_path': point['source_path'], 'source_sha256': point['sha256'], 'offset_bytes': point['offset_bytes']} not in entry['source_candidates']:
                    raise ValueError('Offline survey source declaration differs from authored candidate')
            elif row["layout_meaning_sha256"] is not None:
                raise ValueError("Unsupported survey cell claims trusted geometry")
            else:
                boundary = base + '--unsupported--' + entry['key']
                if boundary not in bundle['unsupported'] or boundary not in cases:
                    raise ValueError('Unsupported survey cell lacks native/Wasm boundary case')
                failed, identity = cases[boundary], comparison['case_evidence'][boundary]
                if failed['status'] != cell['transport_status'] or failed['diagnostics'] != cell['diagnostics'] or identity['base_request_sha256'] != cell['request_sha256'] or identity['full_result_sha256'] != cell['native_result_sha256']:
                    raise ValueError('Unsupported survey native/Wasm evidence differs from cell')
    if set(surveys) != expected:
        raise ValueError("Offline survey evidence matrix membership differs")
    return result


def provisioned(runtime, native, configs):
    """Validate the entire provisioning boundary before writing generated output."""
    if not runtime.is_dir() or not native.is_file() or not configs.is_dir():
        raise ValueError("Layout artifacts are not provisioned. Supply --layout-runtime, --layout-native and "
                         "--layout-configs from the pinned offline layout workflow (see layouts/README.txt). "
                         "Ordinary book generation does not download or build the compiler.")
    pin = lock_path(runtime)
    if not pin.is_file():
        raise ValueError("Reviewed layout artifact pin is missing: " + pin.name)
    lock = read_json(pin)
    if lock.get("contract") != "platydoc.layout-artifact-lock" or lock.get("version") not in {1, 2}:
        raise ValueError("Unsupported layout artifact lock")
    package_bytes = (runtime / "manifest.json").read_bytes()
    if digest(package_bytes) != lock["runtime_package_manifest_sha256"]:
        raise ValueError("Layout runtime package differs from artifact.lock.json")
    package = json.loads(package_bytes)
    if package.get("kind") != ("milestone-8-offline-structure-catalog-runtime" if expanded(lock) else "milestone-5-offline-worker-runtime-proof") or package["source"] != lock["source"]:
        raise ValueError("Unrecognized pinned layout runtime")
    for name, identity in package["files"].items():
        raw = checked_file(runtime, name, identity["sha256"]).read_bytes()
        if len(raw) != identity["bytes"]:
            raise ValueError("Runtime file length differs: " + name)
    checked_file(runtime, "runtime-manifest.json", lock["runtime_manifest_sha256"])
    manifest = read_json(runtime / "runtime-manifest.json")
    expected_profiles = profile_ids(lock)
    if len(set(expected_profiles)) != len(expected_profiles) or len(manifest["profiles"]) != len(expected_profiles) or {profile["id"] for profile in manifest["profiles"]} != set(expected_profiles):
        raise ValueError("Pinned runtime profile membership differs from reviewed artifact")
    if manifest["compiler"] != lock["compiler"] or digest(native.read_bytes()) != lock["native_sha256"]:
        raise ValueError("Pinned native/Wasm compiler identity changed")
    provenance = read_json(runtime / "toolchain-provenance.json")
    for name in ("engine.cpp", "CMakeLists.txt", "toolchain.lock.json", "build.py"):
        checked_file(HERE, name, provenance["inputs"][name])
    if provenance["artifacts"]["build-native/bin/layout-engine"]["sha256"] != lock["native_sha256"]:
        raise ValueError("Native compiler is not bound to packaged build provenance")
    for key, artifact in (("wasm", "build-wasm/bin/layout-engine.wasm"), ("factory", "build-wasm/bin/layout-engine.js")):
        raw = decoded_asset(runtime, manifest["assets"][key])
        if digest(raw) != provenance["artifacts"][artifact]["sha256"]:
            raise ValueError("Packaged compiler/build provenance mismatch")
    for name in ("layout-codec.js", "layout-runtime.js", "contracts.js", "dependencies.js"):
        if (HERE / "browser" / name).read_bytes() != (runtime / name).read_bytes():
            raise ValueError("Runtime helper changed; provision a reviewed artifact: " + name)
    if digest((HERE / "browser/layout-worker.js").read_bytes()) != manifest["assets"]["worker"]["sha256"]:
        raise ValueError("Worker helper differs from pinned artifact")
    snapshot = inventory(SOURCE_ROOT)
    expected = lock["source_inventory"]
    if len(snapshot) != expected["files"] or digest(encoded(snapshot)) != expected["sha256"]:
        raise ValueError("XNU source snapshot changed (including file membership); regenerate/review layout bundles and artifact pin")
    bundle = read_json(runtime / "bundle-manifest.json")
    if bundle["source_commit"] != lock["source"]["revision"] or bundle["source_release"] != lock["source"]["release"]:
        raise ValueError("Bundle source identity differs from artifact lock")
    for origin in bundle["discovery_universe"].values():
        if origin["kind"] in {"xnu", "xnu-export"} and snapshot.get(origin["path"]) != origin["sha256"]:
            raise ValueError("Header discovery universe changed: " + origin["path"])
    checked_file(HERE, lock.get("profile_spec", "profiles/arm64-xnu.json"), bundle["profile_spec_sha256"])
    if expanded(lock):
        if lock.get("platform") != "iPhoneOS" or (HERE / lock["profile_spec"]).read_bytes() != (runtime / "profile-spec.json").read_bytes() or (HERE / lock["inventory"]).read_bytes() != (runtime / "structure-inventory.json").read_bytes():
            raise ValueError("Expanded source profile/inventory differs from reviewed local inputs")
        validate_coverage_package(runtime, manifest, bundle)
    config_bytes = (runtime / "config-provenance.json").read_bytes()
    if digest(config_bytes) != lock["config_provenance_sha256"] or digest(config_bytes) != bundle["config_manifest_sha256"]:
        raise ValueError("Generated configuration provenance changed")
    if (configs / "config-provenance.json").read_bytes() != config_bytes:
        raise ValueError("Current generated configuration provenance differs from pinned bundle")
    config = json.loads(config_bytes)
    generated = generated_sources(runtime, bundle, snapshot)
    if generated is not None:
        from generate_sysproto import load
        if load(read_json(runtime / 'profile-spec.json'), snapshot)[1] != generated:
            raise ValueError('Current generated syscall header differs from packaged input')
    if bundle.get('generated_mig') is not None:
        from generate_mig import load as load_mig
        if load_mig(read_json(runtime / 'profile-spec.json'), configs)[1] != bundle['generated_mig']:
            raise ValueError('Current generated MIG headers differ from packaged input')
    if bundle.get('ubc_layout_inputs') is not None:
        from ubc_inputs import load
        if load(read_json(runtime / 'profile-spec.json'))[0] != bundle['ubc_layout_inputs']:
            raise ValueError('Current UBC dependency input differs from packaged input')
    checked_file(HERE, "generate_configs.py", config["generator_sha256"])
    for name, sha in config["source_inputs"].items():
        checked_file(SOURCE_ROOT, name, sha)
    for profile in config["profiles"].values():
        for name, sha in profile["files"].items():
            checked_file(configs, profile["directory"] + "/" + name, sha)
    return lock, package, manifest, bundle, config, snapshot


def bridge(entries, source, mapping, partial=False):
    if len(entries) > 1:
        combined = {"documents": [], "bindings": []}
        for entry in entries:
            checked = bridge([entry], source, mapping, partial)
            for key in combined:
                combined[key].extend(checked[key])
        return combined
    with tempfile.TemporaryFile() as stream:
        stream.write(encoded({"entries": entries, "source": source, "mapping": mapping, "partial": partial}))
        stream.seek(0)
        result = subprocess.run(["node", str(HERE / "catalog_contracts.cjs")], stdin=stream,
                                capture_output=True, timeout=180, check=False)
    if result.returncode:
        raise ValueError("Layout catalog contract validation failed: " + result.stderr.decode())
    return json.loads(result.stdout)


def request_for(runtime, profile, snapshot, configs, config, bundle):
    payload = json.loads(decoded_asset(runtime, profile["asset"]))
    if payload["source"] != profile["source"]:
        raise ValueError("Profile source identity mismatch")
    request = copy.deepcopy(payload["request"])
    request["trace_dependencies"], request["trace_files"] = False, True
    for virtual, text in request["files"].items():
        physical = request.get("source_paths", {}).get(virtual, "")
        sha = digest(text.encode())
        if physical.startswith("xnu/"):
            if snapshot.get(physical[4:]) != sha:
                raise ValueError("Bundled XNU header differs from current source: " + virtual)
        elif physical.startswith("generated-config/"):
            checked_file(configs, physical.removeprefix("generated-config/"), sha)
        elif physical.startswith('generated-syscalls/'):
            generated = bundle.get('generated_syscalls', {})
            name = physical.removeprefix('generated-syscalls/')
            if generated.get('files', {}).get(name) != sha:
                raise ValueError('Bundled syscall header lacks original-generator provenance')
            checked_file(runtime / 'generated-syscalls', name, sha)
        elif physical.startswith('generated-mig/'):
            name = physical.removeprefix('generated-mig/')
            selected = bundle.get('generated_mig', {}).get('profiles', {}).get(profile['base_profile'], {})
            expected = {selected.get('directory', '') + '/' + key: value for key, value in selected.get('files', {}).items()}
            if expected.get(name) != sha:
                raise ValueError('Bundled MIG header lacks matching profile provenance')
            checked_file(runtime / 'generated-mig', name, sha)
        elif physical.startswith(('external-header/', 'layout-compatibility/')):
            kind, name = physical.split('/', 1)
            origin = bundle.get('ubc_layout_inputs', {}).get('files', {}).get(name, {})
            if origin.get('kind') != kind or origin.get('sha256') != sha:
                raise ValueError('Unrecognized UBC dependency origin')
            checked_file(runtime / 'ubc-inputs', name, sha)
        elif virtual.startswith("/inputs/clang-resource/"):
            if bundle["discovery_universe"].get(virtual, {}).get("sha256") != sha:
                raise ValueError("Bundled Clang resource header lacks pinned provenance")
        elif virtual != request["main"]:
            raise ValueError("Unrecognized bundled header origin: " + virtual)
    return request


def common_profiles(runtime, native, configs, manifest, lock, config, snapshot, bundle, mapping, cache):
    identities = {"artifact_lock": digest(encoded(lock)), "tools": tool_inputs(),
                  "mapping": digest(encoded(mapping)), "schema": 1}
    entries, keys, bindings = [], [], []
    for profile in manifest["profiles"]:
        request = request_for(runtime, profile, snapshot, configs, config, bundle)
        key = digest(encoded({"context": identities, "profile": profile["id"], "request": request}))
        keys.append(key)
        cached = cache / (key + ".json")
        value = None
        if cached.is_file() and not cached.is_symlink():
            try:
                envelope = read_json(cached)
                candidate = envelope["value"]
                if set(envelope) != {"key", "sha256", "value"} or envelope["key"] != key or digest(encoded(candidate)) != envelope["sha256"]:
                    raise ValueError("Cache checksum mismatch")
                if set(candidate) != {"contract", "version", "identity", "profile", "request_sha256", "result", "document"} or candidate["contract"] != "platydoc.common-profile-layout" or candidate["version"] != 1 or candidate["identity"] != key or candidate["profile"] != profile["id"] or candidate["request_sha256"] != digest(encoded(request)):
                    raise ValueError("Cache context mismatch")
                if candidate["result"].get("status") != "ok" or candidate["result"].get("diagnostics") or candidate["result"]["compiler"]["engine_sha256"] != manifest["compiler"]["engine_sha256"] or candidate["result"]["compiler"]["revision"] != manifest["compiler"]["revision"]:
                    raise ValueError("Cache compiler/status mismatch")
                validated = bridge([{ "profile": profile["id"], "request": request, "result": candidate["result"], "document": candidate["document"]}], lock["source"], mapping, expanded(lock))
                value = candidate
            except (ValueError, KeyError, TypeError, OSError):
                value = None
        if value is None:
            process = subprocess.run([str(native)], input=encoded(request), capture_output=True, timeout=120, check=True)
            result = json.loads(process.stdout)
            if result.get("status") != "ok" or result.get("diagnostics") or result["compiler"]["engine_sha256"] != manifest["compiler"]["engine_sha256"] or result["compiler"]["revision"] != manifest["compiler"]["revision"]:
                raise ValueError("Pinned common-profile compiler context failed: " + profile["id"])
            validated = bridge([{ "profile": profile["id"], "request": request, "result": result}], lock["source"], mapping, expanded(lock))
            document = validated["documents"][0]
            value = {"contract": "platydoc.common-profile-layout", "version": 1, "identity": key,
                     "profile": profile["id"], "request_sha256": digest(encoded(request)), "result": result, "document": document}
            cache.mkdir(parents=True, exist_ok=True)
            if cache.is_symlink() or cached.is_symlink():
                raise ValueError("Refusing symlinks in layout cache")
            write_json(cached, {"key": key, "sha256": digest(encoded(value)), "value": value})
        entries.append({**value, "profile": profile["id"], "request": request})
        bindings.append(validated["bindings"][0])
    # Each profile was already validated above. Combining the entire catalog
    # duplicates that work and can exceed Node's maximum JSON string length.
    return entries, bindings, identities


def generate(output, book, cache, runtime, native, configs):
    """Write only inside a new book staging directory owned by its caller."""
    lock, package, manifest, bundle, config, snapshot = provisioned(runtime, native, configs)
    mapping = read_json(DOCS / "structures/layouts.json")
    validate_chapter_mapping(mapping, lock["source"])
    entries, bindings, identities = common_profiles(runtime, native, configs, manifest, lock, config, snapshot, bundle, mapping, cache)
    if output.exists():
        raise ValueError("Layout generation needs a fresh staging subdirectory")
    output.mkdir(parents=True)
    copied = runtime_files(package)
    for name in copied:
        destination = local_path(output, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_path(runtime, name), destination)
        if digest(destination.read_bytes()) != package["files"][name]["sha256"] or destination.stat().st_size != package["files"][name]["bytes"]:
            raise ValueError("Runtime file changed while copying: " + name)
    shutil.copyfile(runtime / "manifest.json", output / "runtime-package-manifest.json")
    for name in ("layouts.css", "layouts.js", "explorer-model.js", "book-layouts.js"):
        shutil.copyfile(HERE / "browser" / name, output / name)
    write_json(output / "artifact.lock.json", lock)
    write_json(output / "source-inventory.json", snapshot)
    write_json(output / "layout-chapters.json", mapping)
    write_json(output / "chapter-bindings.json", bindings)
    profile_rows, headers, links, observed, conflicts = [], {}, {}, {}, set()
    records = read_json(book / "source-records.json")
    by_source = {record["path"]: (url, record) for url, record in records.items()}
    for entry, profile in zip(entries, manifest["profiles"], strict=True):
        name, document = entry["profile"], entry["document"]
        value = {key: entry[key] for key in ("contract", "version", "identity", "profile", "request_sha256", "result", "document")}
        relative = "common-profiles/" + name + ".json"
        write_json(output / relative, value)
        raw = (output / relative).read_bytes()
        profile_rows.append({"id": name, "configuration_id": document["configuration"]["id"], "request_sha256": entry["request_sha256"],
                             "header_asset": profile["asset"], "cache": {"path": relative, "bytes": len(raw), "sha256": digest(raw)}})
        headers[name] = []
        for path, text in entry["request"]["files"].items():
            physical = entry["request"].get("source_paths", {}).get(path)
            sha = digest(text.encode())
            for key in (path, physical):
                if key is not None:
                    if key in observed and observed[key] != sha:
                        conflicts.add(key)
                    observed[key] = sha
            headers[name].append({"path": path, "source_path": physical, "bytes": len(text.encode()), "sha256": sha})
            if physical in by_source:
                url, record = by_source[physical]
                if record["sha256"] == sha and digest(local_path(book, record["payload"]).read_bytes()) == record["payload_sha256"]:
                    links[path] = links[physical] = "../" + url
    coverage = read_json(output / "coverage.json") if expanded(lock) else None
    selections = selections_for(mapping, entries, coverage)
    catalog = {"contract": "platydoc.layout-catalog", "version": 1, "source": lock["source"], "compiler": manifest["compiler"],
               "purpose": CATALOG_PURPOSE if expanded(lock) else PURPOSE,
               "profiles": profile_rows, "declarations": declaration_rows(entries), "selections": selections,
               "coverage": coverage_summary(lock, selections)}
    write_json(output / "catalog.json", catalog)
    write_json(output / "headers.json", {"contract": "platydoc.layout-header-bundles", "version": 1, "profiles": headers})
    for key in conflicts:
        links.pop(key, None)
    explorer = {"bookRoot": "../", "assetRoot": "../layouts/", "integrated": True, "source": lock["source"], "sourceLinks": links, "selections": selections}
    if coverage is not None:
        explorer["coverage"] = coverage
    (output / "explorer-config.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutExplorerConfig=" + encoded(explorer) + b";\n")
    (output / "catalog.js").write_bytes(b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutCatalog=" + encoded(catalog) + b";\n")
    provenance = generation_provenance(identities, lock, snapshot, mapping)
    write_json(output / "generation-provenance.json", provenance)
    provisioned(runtime, native, configs)
    if tool_inputs() != identities["tools"] or digest(encoded(read_json(DOCS / "structures/layouts.json"))) != identities["mapping"]:
        raise ValueError("Layout generation tools or authored mapping changed during generation")
    return catalog


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


def integrate(book, cache, runtime, native, configs, prepared=None):
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
    if prepared is None:
        generate(output, book, cache / "layout-common-profiles", runtime, native, configs)
    else:
        from prepared import unpack
        unpack(prepared, output)
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


def verify(book):
    """Verify a packaged/extracted book without original cache or compiler files."""
    output = book / "layouts"
    package = read_json(local_path(output, "manifest.json"))
    if set(package) != {"contract", "version", "page", "files"} or package["contract"] != "platydoc.layout-package" or package["version"] != 1 or package["page"] != PAGE:
        raise ValueError("Unsupported handbook layout package")
    actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"}
    if actual != set(package["files"]):
        raise ValueError("Layout package membership differs from manifest")
    for name, identity in package["files"].items():
        if set(identity) != {"sha256", "bytes"} or type(identity["bytes"]) is not int or identity["bytes"] < 0:
            raise ValueError("Invalid layout file identity")
        if len(checked_file(output, name, identity["sha256"]).read_bytes()) != identity["bytes"]:
            raise ValueError("Layout file length differs from manifest")
    lock = read_json(output / "artifact.lock.json")
    if lock != read_json(HERE / ("artifact-ios.lock.json" if expanded(lock) else "artifact.lock.json")):
        raise ValueError("Packaged layout artifact differs from current reviewed pin")
    original = read_json(checked_file(output, "runtime-package-manifest.json", lock["runtime_package_manifest_sha256"]))
    for name in runtime_files(original):
        if package["files"].get(name) != original["files"][name]:
            raise ValueError("Pinned runtime asset identity changed: " + name)
    runtime = read_json(checked_file(output, "runtime-manifest.json", lock["runtime_manifest_sha256"]))
    expected_profiles = profile_ids(lock)
    if runtime["compiler"] != lock["compiler"] or len(runtime["profiles"]) != len(expected_profiles) or {p["id"] for p in runtime["profiles"]} != set(expected_profiles):
        raise ValueError("Invalid packaged compiler/profile identities")
    for asset in list(runtime["assets"].values()) + [p["asset"] for p in runtime["profiles"]]:
        decoded_asset(output, asset)
    if (output / "runtime-manifest.js").read_bytes() != b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutRuntimeManifest=" + encoded(runtime) + b";\n":
        raise ValueError("Runtime classic script differs from JSON manifest")
    snapshot = read_json(output / "source-inventory.json")
    if len(snapshot) != lock["source_inventory"]["files"] or digest(encoded(snapshot)) != lock["source_inventory"]["sha256"]:
        raise ValueError("Packaged source inventory differs from reviewed source snapshot")
    config = read_json(checked_file(output, "config-provenance.json", lock["config_provenance_sha256"]))
    for name, sha in config["source_inputs"].items():
        if snapshot.get(name) != sha:
            raise ValueError("Configuration recipe inputs differ from source inventory")
    bundle = read_json(output / "bundle-manifest.json")
    generated_sources(output, bundle, snapshot)
    if bundle["config_manifest_sha256"] != lock["config_provenance_sha256"]:
        raise ValueError("Bundle/config provenance mismatch")
    for origin in bundle["discovery_universe"].values():
        if origin["kind"] in {"xnu", "xnu-export"} and snapshot.get(origin["path"]) != origin["sha256"]:
            raise ValueError("Packaged discovery universe differs from source inventory")
    if expanded(lock):
        validate_coverage_package(output, runtime, bundle)
    mapping = read_json(output / "layout-chapters.json")
    catalog = read_json(output / "catalog.json")
    if set(catalog) != {"contract", "version", "source", "compiler", "purpose", "profiles", "declarations", "selections", "coverage"} or catalog["contract"] != "platydoc.layout-catalog" or catalog["version"] != 1:
        raise ValueError("Unsupported layout catalog schema")
    if catalog["source"] != lock["source"] or catalog["compiler"] != runtime["compiler"]:
        raise ValueError("Catalog source/compiler provenance mismatch")
    if catalog["purpose"] != (CATALOG_PURPOSE if expanded(lock) else PURPOSE) or catalog["coverage"] != coverage_summary(lock, catalog["selections"]):
        raise ValueError("Catalog coverage/purpose exceeds the validated finite survey")
    if (output / "catalog.js").read_bytes() != b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutCatalog=" + encoded(catalog) + b";\n":
        raise ValueError("Catalog classic script differs from JSON")
    if len(catalog["profiles"]) != len(expected_profiles) or [p["id"] for p in catalog["profiles"]] != [p["id"] for p in runtime["profiles"]]:
        raise ValueError("Catalog must cover exactly the pinned runtime contexts")
    provenance = read_json(output / "generation-provenance.json")
    expected_identity = {"artifact_lock": digest(encoded(lock)), "tools": tool_inputs(), "mapping": digest(encoded(mapping)), "schema": 1}
    if provenance != generation_provenance(expected_identity, lock, snapshot, mapping):
        raise ValueError("Layout generation provenance/tool/schema identity changed")
    for name in ("layouts.css", "layouts.js", "explorer-model.js", "book-layouts.js"):
        expected_sha = expected_identity["tools"][(HERE / "browser" / name).relative_to(PROJECT_ROOT).as_posix()]
        if digest((output / name).read_bytes()) != expected_sha:
            raise ValueError("Packaged explorer helper differs from generation inputs")
    if provenance["source_inventory_sha256"] != digest(encoded(snapshot)) or provenance["mapping_sha256"] != digest(encoded(mapping)) or provenance["runtime_manifest_sha256"] != lock["runtime_manifest_sha256"] or provenance["native_sha256"] != lock["native_sha256"]:
        raise ValueError("Layout generation provenance mismatch")
    headers = read_json(output / "headers.json")
    if set(headers) != {"contract", "version", "profiles"} or headers["contract"] != "platydoc.layout-header-bundles" or headers["version"] != 1 or set(headers["profiles"]) != {p["id"] for p in runtime["profiles"]}:
        raise ValueError("Unsupported header bundle index")
    entries, source_links, source_seen, conflicts = [], {}, {}, set()
    source_records = read_json(book / "source-records.json")
    by_source = {record["path"]: (url, record) for url, record in source_records.items()}
    for profile, summary in zip(runtime["profiles"], catalog["profiles"], strict=True):
        payload = json.loads(decoded_asset(output, profile["asset"]))
        request = payload["request"]
        request["trace_dependencies"], request["trace_files"] = False, True
        if summary["header_asset"] != profile["asset"] or summary["request_sha256"] != digest(encoded(request)):
            raise ValueError("Catalog header/request context mismatch")
        observed = []
        for virtual, content in request["files"].items():
            physical = request.get("source_paths", {}).get(virtual)
            sha = digest(content.encode())
            observed.append({"path": virtual, "source_path": physical, "bytes": len(content.encode()), "sha256": sha})
            for key in (virtual, physical):
                if key is not None:
                    if key in source_seen and source_seen[key] != sha:
                        conflicts.add(key)
                    source_seen[key] = sha
            if physical in by_source:
                url, record = by_source[physical]
                if record["sha256"] == sha and digest(local_path(book, record["payload"]).read_bytes()) == record["payload_sha256"]:
                    source_links[virtual] = source_links[physical] = "../" + url
            if physical and physical.startswith("xnu/") and snapshot.get(physical[4:]) != sha:
                raise ValueError("Bundled header differs from pinned source")
            if physical and physical.startswith("generated-config/"):
                parts = physical.removeprefix("generated-config/").split("/")
                if len(parts) != 3 or parts[0] != "profiles" or config["profiles"][parts[1]]["files"].get(parts[2]) != sha:
                    raise ValueError("Bundled generated header differs from configuration recipe")
            if physical and physical.startswith('generated-syscalls/'):
                if bundle.get('generated_syscalls', {}).get('files', {}).get(physical.removeprefix('generated-syscalls/')) != sha:
                    raise ValueError('Bundled syscall header differs from original generator output')
            if physical and physical.startswith('generated-mig/'):
                selected = bundle.get('generated_mig', {}).get('profiles', {}).get(profile['base_profile'], {})
                expected = {'generated-mig/' + selected.get('directory', '') + '/' + name: value for name, value in selected.get('files', {}).items()}
                if expected.get(physical) != sha:
                    raise ValueError('Bundled MIG header differs from profile generator output')
            if physical and physical.startswith(('external-header/', 'layout-compatibility/')):
                kind, name = physical.split('/', 1)
                origin = bundle.get('ubc_layout_inputs', {}).get('files', {}).get(name, {})
                if origin.get('kind') != kind or origin.get('sha256') != sha:
                    raise ValueError('Bundled UBC dependency differs from reviewed source')
            if virtual.startswith("/inputs/clang-resource/") and bundle["discovery_universe"].get(virtual, {}).get("sha256") != sha:
                raise ValueError("Unpinned compiler resource header")
        if observed != headers["profiles"][profile["id"]]:
            raise ValueError("Header index does not describe complete profile bytes")
        identity = summary["cache"]
        raw = checked_file(output, identity["path"], identity["sha256"]).read_bytes()
        if len(raw) != identity["bytes"]:
            raise ValueError("Common-profile cache length mismatch")
        cached = json.loads(raw)
        if set(cached) != {"contract", "version", "identity", "profile", "request_sha256", "result", "document"} or cached["contract"] != "platydoc.common-profile-layout" or cached["version"] != 1 or cached["result"].get("status") != "ok" or cached["result"].get("diagnostics"):
            raise ValueError("Invalid common-profile cache schema/status")
        expected_key = digest(encoded({"context": provenance["identity"], "profile": profile["id"], "request": request}))
        if cached["identity"] != expected_key or cached["profile"] != profile["id"] or cached["request_sha256"] != digest(encoded(request)) or cached["document"]["configuration"]["id"] != summary["configuration_id"]:
            raise ValueError("Common-profile cache has a stale context identity")
        if cached["result"]["compiler"]["revision"] != lock["compiler"]["revision"] or cached["result"]["compiler"]["engine_sha256"] != lock["compiler"]["engine_sha256"]:
            raise ValueError("Cached compiler provenance differs")
        entries.append({"profile": profile["id"], "request": request, "result": cached["result"], "document": cached["document"]})
    validated = bridge(entries, lock["source"], mapping, expanded(lock))
    if catalog["declarations"] != declaration_rows(entries):
        raise ValueError("Searchable catalog declarations differ from validated contracts")
    if validated["bindings"] != read_json(output / "chapter-bindings.json"):
        raise ValueError("Chapter bindings do not resolve against common-profile contracts")
    coverage = read_json(output / "coverage.json") if expanded(lock) else None
    if catalog["selections"] != selections_for(mapping, entries, coverage):
        raise ValueError("Catalog selection keys do not match explicit authored bindings")
    for key in conflicts:
        source_links.pop(key, None)
    expected_config = {"bookRoot": "../", "assetRoot": "../layouts/", "integrated": True, "source": lock["source"], "sourceLinks": source_links, "selections": catalog["selections"]}
    if coverage is not None:
        expected_config["coverage"] = coverage
    if (output / "explorer-config.js").read_bytes() != b"// SPDX-License-Identifier: GPL-2.0-only\nwindow.layoutExplorerConfig=" + encoded(expected_config) + b";\n":
        raise ValueError("Explorer source links or declaration selection config changed")
    # Existing source verifier checks payload bytes and headings independently.
    # Validate here that every mapped chapter/anchor is a real generated target.
    for mapped in mapping["entries"]:
        for chapter in mapped["chapters"]:
            page, fragment = chapter.split("#", 1)
            target = local_path(book, page.removesuffix(".md") + ".html")
            if ('id="' + fragment + '"') not in target.read_text():
                raise ValueError("Mapped chapter heading is absent from generated book")
    return {"layout_profiles": len(entries), "layout_declarations": len(catalog["declarations"]), "layout_headers": sum(map(len, headers["profiles"].values()))}
