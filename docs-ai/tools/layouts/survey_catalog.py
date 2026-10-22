#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Survey documented C roots, preserving exact successes and failure boundaries."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS
from check_links import heading_ids
sys.path.insert(0, str(HERE))
from bundle_xnu import exports, comparable
from build import verify_source
from catalog import inventory as source_inventory, local_path
from layout_exports import exported_headers
from coverage import validate as validate_coverage
from generate_sysproto import load as generated_syscalls
from generate_mig import load as generated_mig
from ubc_inputs import load as ubc_inputs, guard as guard_ubc


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value) + b"\n")


def run(native, request):
    guard_ubc(request)
    process = subprocess.run([str(native)], input=encoded(request), capture_output=True, timeout=90, check=True)
    result = json.loads(process.stdout)
    guard_ubc(request, result)
    if result.get("status") not in {"ok", "error", "invalid-request", "unsupported-layout", "unavailable-type"}:
        raise ValueError("Unexpected compiler response")
    if result["status"] != "ok" and result.get("records"):
        raise ValueError("Failed compiler request returned trusted layouts")
    return result


def validate_inventory(value, spec):
    if set(value) != {"contract", "version", "source", "platform", "scope", "entries"} or value["contract"] != "platydoc.structure-survey-inventory" or value["version"] != 1:
        raise ValueError("Unsupported surveyed inventory schema")
    if value["source"] != {"release": spec["source_release"], "revision": spec["source_commit"]} or value["platform"] != spec["platform"]:
        raise ValueError("Inventory source/platform mismatch")
    keys = set()
    for entry in value["entries"]:
        if set(entry) != {"key", "record", "group", "component", "headers", "source_candidates", "chapters"} or entry["key"] in keys:
            raise ValueError("Invalid/duplicate inventory entry")
        keys.add(entry["key"])
        if entry["component"] not in {"bsd", "osfmk"} or not re.fullmatch(r"[A-Za-z_]\w*", entry["record"]):
            raise ValueError("Invalid inventoried context")
        if not entry["source_candidates"] or not entry["chapters"]:
            raise ValueError("Inventoried roots require source and documentation anchors")
        for candidate in entry["source_candidates"]:
            if set(candidate) != {"source_path", "source_sha256", "offset_bytes", "kind"} or candidate["kind"] != "struct":
                raise ValueError("Invalid inventoried source candidate")
            path = local_path(PROJECT_ROOT, candidate["source_path"])
            if not path.resolve().is_relative_to(SOURCE_ROOT.resolve()):
                raise ValueError("Inventory source outside XNU")
            data = path.read_bytes()
            at = candidate["offset_bytes"]
            if type(at) is not int or at < 0 or sha(data) != candidate["source_sha256"] or data[at:at + len(entry["record"])] != entry["record"].encode():
                raise ValueError("Stale inventoried source anchor: " + entry["key"])
        for chapter in entry["chapters"]:
            page, fragment = chapter.split("#")
            if fragment not in heading_ids(local_path(DOCS, page)):
                raise ValueError("Stale inventoried chapter heading")


def inputs(spec, llvm, configs):
    """Construct original whole input universe; no fabricated includes or types."""
    if subprocess.run(["git", "-C", str(SOURCE_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip() != spec["source_commit"]:
        raise ValueError("Wrong XNU revision")
    snapshot = source_inventory(SOURCE_ROOT)
    old_pin = read(HERE / "artifact.lock.json")["source_inventory"]
    if len(snapshot) != old_pin["files"] or sha(encoded(snapshot)) != old_pin["sha256"]:
        raise ValueError("Selected source inventory changed; review source before surveying")
    source_manifest_sha = verify_source(llvm)
    generated_syscalls(spec, snapshot)
    llvm_files = read(llvm / ".source-files.json")
    config = read(configs / "config-provenance.json")
    generated_mig(spec, configs)
    ubc_inputs(spec)
    if config["source_commit"] != spec["source_commit"] or config["generator_sha256"] != sha((HERE / "generate_configs.py").read_bytes()):
        raise ValueError("Generated configuration recipe changed")
    for path, digest in config["source_inputs"].items():
        if snapshot.get(path) != digest:
            raise ValueError("Configuration source changed")
    files, origins = {}, {}
    source_files = spec.get("source_files", [])
    if len(set(source_files)) != len(source_files) or any(name not in snapshot or Path(name).suffix != ".c" for name in source_files):
        raise ValueError("Additional source inputs must name original inventoried C files")
    for relative, digest in snapshot.items():
        path = SOURCE_ROOT / relative
        if path.suffix.lower() in {".h", ".inc", ".def", ".defs", ".hpp"} or relative in source_files:
            virtual = "/inputs/xnu/" + relative
            files[virtual] = path.read_bytes().decode("utf-8")
            origins[virtual] = {"kind": "xnu", "path": relative, "sha256": digest}
    resources = llvm / "clang/lib/Headers"
    for path in sorted(resources.rglob("*.h")):
        raw = path.read_bytes()
        relative = path.relative_to(llvm).as_posix()
        if llvm_files[relative] != sha(raw):
            raise ValueError("Compiler resource differs from source pin")
        virtual = "/inputs/clang-resource/" + path.relative_to(resources).as_posix()
        files[virtual] = raw.decode("utf-8")
        origins[virtual] = {"kind": "clang-resource", "path": relative, "sha256": sha(raw)}
    aliases = {**exports(spec), **exported_headers(SOURCE_ROOT, spec["additional_exports"])}
    for virtual, (path, makefile) in aliases.items():
        raw = path.read_bytes()
        files[virtual] = raw.decode("utf-8")
        origins[virtual] = {"kind": "xnu-export", "path": path.relative_to(SOURCE_ROOT).as_posix(), "makefile": makefile, "sha256": sha(raw)}
    for profile in spec["configurations"]:
        selected = config["profiles"][profile]
        if selected["platform"] != spec["platform"]:
            raise ValueError("Generated configuration has wrong platform")
        for name, digest in selected["files"].items():
            if sha(local_path(configs, selected["directory"] + "/" + name).read_bytes()) != digest:
                raise ValueError("Generated configuration file changed")
        lines = [line for line in local_path(configs, selected["directory"] + "/Makefile").read_text().splitlines() if line.startswith("export CONFIG_DEFINES =")]
        import shlex
        options = shlex.split(lines[0].split("=", 1)[1]) if len(lines) == 1 else None
        if options != selected["config_defines"]:
            raise ValueError("Generated CONFIG_DEFINES changed")
        observed = {definition[2:].partition("=")[0]: definition[2:].partition("=")[2] or "1" for definition in options}
        if observed != selected["macros"]:
            raise ValueError("Generated configuration macros changed")
    return files, origins, config, snapshot, source_manifest_sha


def request_for(spec, base, component, headers, records, files, origins, config, configs):
    selected = config["profiles"][base]
    board = spec["boards"][selected["soc"]]
    supplied, mapped = dict(files), copy.deepcopy(origins)
    observed = set(spec["observe_macros"])
    generated_root = None
    if set(headers) & set(spec.get("generated_syscalls", {}).get("includes", [])):
        generated_root, generated = generated_syscalls(spec)
        virtual = '/inputs/generated-syscalls/sys/sysproto.h'
        supplied[virtual] = (generated_root / 'sys/sysproto.h').read_text()
        mapped[virtual] = {'kind': 'generated-syscalls', 'path': 'sys/sysproto.h',
                           'sha256': generated['files']['sys/sysproto.h']}
    mig_root = None
    if set(headers) & set(spec.get('generated_mig', {}).get('includes', [])):
        mig_root, mig = generated_mig(spec, configs)
        profile = mig['profiles'][base]
        for name, digest in profile['files'].items():
            virtual = '/inputs/generated-mig/' + name
            supplied[virtual] = (mig_root / profile['directory'] / name).read_text()
            mapped[virtual] = {'kind': 'generated-mig', 'path': profile['directory'] + '/' + name, 'sha256': digest}
    ubc = None
    if set(headers) & set(spec.get('ubc_layout_inputs', {}).get('includes', [])):
        ubc, external, _ = ubc_inputs(spec)
        records = ['ubc_info', 'cs_blob']
        for name, origin in ubc['files'].items():
            prefix = '/inputs/layout-compat/' if origin['kind'] == 'layout-compatibility' else '/inputs/external-trustcache/'
            virtual = prefix + name
            supplied[virtual] = external[name].decode()
            mapped[virtual] = {'kind': origin['kind'], 'path': name, 'sha256': origin['sha256']}
    for name, digest in selected["files"].items():
        if name.endswith(".h"):
            virtual = "/inputs/generated/" + name
            supplied[virtual] = local_path(configs, selected["directory"] + "/" + name).read_text()
            mapped[virtual] = {"kind": "generated-config", "path": selected["directory"] + "/" + name, "sha256": digest}
            observed.update(re.findall(r"^\s*#\s*define\s+([A-Za-z_]\w*)", supplied[virtual], re.M))
    main = spec["diagnostic_preamble"]
    if ubc is not None:
        main += '#define PLATYDOC_COREENTITLEMENTS_LAYOUT_ONLY 1\n'
        observed.add('PLATYDOC_COREENTITLEMENTS_LAYOUT_ONLY')
    for name in headers:
        compatibility = spec.get('include_compatibility', {}).get(name, {})
        if compatibility and (name != 'kern/kern_credential.c' or compatibility != {
                '__builtin_xnu_type_summary': '0', '__builtin_xnu_type_signature': '""'}):
            raise ValueError('Unsupported include-local compiler builtin compatibility')
        for builtin, replacement in compatibility.items():
            main += '#pragma push_macro("' + builtin + '")\n#undef ' + builtin + '\n'
            main += '#define ' + builtin + '(...) ' + replacement + '\n'
        warnings = spec.get("include_diagnostics", {}).get(name, [])
        if any(not re.fullmatch(r"-W[a-z0-9-]+", warning) for warning in warnings):
            raise ValueError("Invalid include-specific diagnostic option")
        if warnings:
            main += "#pragma clang diagnostic push\n"
            main += "".join('#pragma clang diagnostic ignored "' + warning + '"\n' for warning in warnings)
        main += "#include <" + name + ">\n"
        if warnings:
            main += "#pragma clang diagnostic pop\n"
        for builtin in reversed(compatibility):
            main += '#pragma pop_macro("' + builtin + '")\n'
    supplied["/inputs/request.c"] = main
    mapped["/inputs/request.c"] = {"kind": "analysis-entry", "path": "inputs/request.c", "sha256": sha(main.encode())}
    macros = {**selected["macros"], **spec["base_macros"], board["board_macro"]: "1", "CURRENT_MACHINE_CONFIG_LC": selected["soc"]}
    if component == "bsd":
        macros.update(spec["bsd_macros"])
    request = {key: copy.deepcopy(spec[key]) for key in ("target", "language", "blocks", "kernel_mode", "ptrauth_intrinsics", "ptrauth_calls", "include_dirs", "forced_includes")}
    if generated_root is not None:
        request['include_dirs'].insert(0, '/inputs/generated-syscalls/')
    if mig_root is not None:
        request['include_dirs'].insert(0, '/inputs/generated-mig/')
    if ubc is not None:
        request['include_dirs'][:0] = ['/inputs/layout-compat/', '/inputs/external-trustcache/']
    request.update({"main": "/inputs/request.c", "files": supplied, "records": list(records), "macros": macros,
                    "target_features": board["target_features"], "trace_files": True, "trace_dependencies": False,
                    "observe_macros": sorted(observed | set(macros))})
    request.update({key: board[key] for key in ("target_cpu", "target_arch") if key in board})
    request["source_paths"] = {name: ("xnu/" if origin["kind"].startswith("xnu") else origin["kind"] + "/") + origin["path"] for name, origin in mapped.items()}
    return request, mapped


def reduce_request(native, request, full):
    selected = set(full["consumed_files"]) | {probe["resolved"] for probe in full.get("include_probes", []) if probe["resolved"]}
    selected.add(request["main"])
    reduced = copy.deepcopy({key: value for key, value in request.items() if key not in {"files", "source_paths"}})
    reduced["files"] = {name: request["files"][name] for name in sorted(selected)}
    reduced["source_paths"] = {name: request["source_paths"][name] for name in sorted(selected)}
    result = run(native, reduced)
    if comparable(full) != comparable(result):
        raise ValueError("Reduced header closure changed preprocessing, status or complete layout output")
    return reduced, result


def physical_identity(declaration):
    point = declaration["source"]["spelling"]
    return [declaration["kind"], point["source_path"], point["sha256"], point["offset_bytes"]]


def root_meaning(result, tag):
    """Compare actual type/layout semantics across TUs, not TU-specific IDs."""
    declarations = {d["id"]: d for d in result["declarations"]}
    records = {r["id"]: r for r in result["records"]}
    matching = [r for r in result["records"] if r["name"] == tag]
    if len(matching) != 1:
        raise ValueError("Requested root missing or ambiguous")
    visited = set()
    def normalize(value, storage=True):
        if isinstance(value, list):
            return [normalize(item, storage) for item in value]
        if isinstance(value, dict):
            normalized = {key: normalize(item, storage and not (value.get("kind") == "pointer" and key == "pointee")) for key, item in value.items() if key not in {"id", "location", "scope", "source"}}
            if value.get("id") in declarations:
                normalized["declaration_source"] = physical_identity(declarations[value["id"]])
            return normalized
        if isinstance(value, str) and value in declarations:
            declaration = declarations[value]
            identity = physical_identity(declaration)
            if value in visited:
                return {"declaration": identity, "recursive": True}
            visited.add(value)
            if declaration["kind"] in {"struct", "union"} and not storage:
                body = None
            elif value in records:
                body = normalize(records[value], storage)
            else:
                body = normalize(declaration, storage)
            visited.remove(value)
            return {"declaration": identity, "body": body}
        return value
    record = matching[0]
    return {"source": physical_identity(declarations[record["id"]]), "layout": normalize(record)}


def status_for(result):
    if result["status"] == "ok" and not result["diagnostics"]:
        return "supported", None
    if result["status"] == "unsupported-layout":
        return "unsupported", "engine-source-identity"
    if result["status"] == "unavailable-type":
        return "unavailable", "definition-not-in-header-context"
    if result["status"] == "error":
        missing = any("file not found" in d["message"] for d in result["diagnostics"])
        return "unavailable" if missing else "compilation-error", "missing-header" if missing else "compiler-error"
    if result["status"] == "ok":
        return "unsupported", "compiler-diagnostics"
    return "invalid-configuration", "invalid-request"


def dependency_files(result):
    names = set()
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get("file"), str) and value["file"]:
                names.add(value["file"])
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    for declaration in result["declarations"]:
        visit(declaration["source"]); visit(declaration["scope"])
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--spec", type=Path, default=HERE / "profiles/ios-catalog.json")
    parser.add_argument("--config-root", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/milestone8-configs")
    parser.add_argument("--llvm-source", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/llvm-source")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/milestone8-bundles")
    args = parser.parse_args()
    args.spec = args.spec.resolve()
    output, native = args.output.resolve(), args.native.resolve()
    for protected in (PROJECT_ROOT, DOCS.resolve(), SOURCE_ROOT.resolve()):
        if output == protected or output in protected.parents or (protected != PROJECT_ROOT and protected in output.parents):
            raise ValueError("Survey output must be dedicated and outside source/documentation trees")
    if output.exists() and (not (output / ".layout-structure-survey").is_file() or any(p.is_symlink() for p in output.rglob("*"))):
        raise ValueError("Refusing unmarked or symlink-containing survey output")
    spec = read(args.spec)
    inventory_path = HERE / spec["inventory"]
    declared = read(inventory_path)
    validate_inventory(declared, spec)
    files, origins, config, snapshot, llvm_sha = inputs(spec, args.llvm_source, args.config_root)
    compiler_pin = read(HERE / "toolchain.lock.json")["llvm"]
    snapshot_sha = sha(encoded(snapshot))
    helper_names = ["survey_catalog.py", "layout_exports.py", "coverage.py", "bundle_xnu.py", "catalog.py", "build.py", "generate_configs.py", "generate_sysproto.py", "generate_mig.py", "ubc_inputs.py", "compatibility/CoreEntitlements/V2/API.h", "compatibility/CoreEntitlements/V2/Kernel.h", "engine.cpp", "toolchain.lock.json"]
    helper_inputs = {name: sha((HERE / name).read_bytes()) for name in helper_names}
    native_sha = sha(native.read_bytes())
    config_sha = sha((args.config_root / "config-provenance.json").read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".structure-survey-stage-", dir=output.parent) as temporary:
        stage = Path(temporary) / "bundles"; stage.mkdir()
        (stage / ".layout-structure-survey").write_text("Platydoc validated structure survey\n")
        coverage = {"contract": "platydoc.layout-coverage", "version": 1, "source": declared["source"], "platform": spec["platform"],
                    "target": spec["target"], "base_profiles": spec["configurations"], "inventory_sha256": sha(inventory_path.read_bytes()),
                    "scope": declared["scope"], "entries": []}
        by_key = {entry["key"]: {**entry, "profiles": {}} for entry in declared["entries"]}
        root_results = {}
        summary = {"schema": 1, "kind": "xnu-structure-survey", "source_release": spec["source_release"], "source_commit": spec["source_commit"],
                   "platform": spec["platform"], "target": spec["target"], "scope": spec["scope"], "compiler": compiler_pin,
                   "source_inventory_sha256": snapshot_sha, "llvm_source_manifest_sha256": llvm_sha,
                   "config_manifest_sha256": sha((args.config_root / "config-provenance.json").read_bytes()),
                   "profile_spec_path": args.spec.relative_to(HERE).as_posix(), "profile_spec_sha256": sha(args.spec.read_bytes()),
                   "inventory_path": spec["inventory"], "inventory_sha256": sha(inventory_path.read_bytes()),
                   "native_sha256": native_sha, "tool_inputs": helper_inputs,
                   "flag_policy": spec["flag_policy"], "base_profiles": spec["configurations"], "profiles": {}, "unsupported": {},
                   "source_evidence": {path: snapshot[path] for path in spec["evidence"]}, "discovery_universe": origins}
        _, generated = generated_syscalls(spec, snapshot)
        if generated is not None:
            summary['generated_syscalls'] = generated
        _, mig = generated_mig(spec, args.config_root)
        if mig is not None:
            summary['generated_mig'] = mig
            summary['source_evidence'].update(mig['source_inputs'])
        ubc, _, _ = ubc_inputs(spec)
        if ubc is not None:
            summary['ubc_layout_inputs'] = ubc
        for base in spec["configurations"]:
            for entry in declared["entries"]:
                request, mapped = request_for(spec, base, entry["component"], entry["headers"], [entry["record"]], files, origins, config, args.config_root)
                full = run(native, request)
                if full["compiler"]["revision"] != compiler_pin["revision"] or full["compiler"]["engine_sha256"] != sha((HERE / "engine.cpp").read_bytes()):
                    raise ValueError("Survey compiler differs from current pinned wrapper/source")
                status, reason = status_for(full)
                if status == "supported":
                    matches = [declaration for declaration in full["declarations"] if declaration["name"] == entry["record"] and declaration["kind"] == "struct"]
                    if len(matches) != 1:
                        raise ValueError("Requested inventoried declaration is ambiguous")
                    point = matches[0]["source"]["spelling"]
                    candidate = {"source_path": point["source_path"], "source_sha256": point["sha256"], "offset_bytes": point["offset_bytes"], "kind": "struct"}
                    if candidate not in entry["source_candidates"]:
                        raise ValueError("Selected declaration differs from authored physical inventory")
                reduced, result = reduce_request(native, request, full)
                root_results[(base, entry["record"])] = result
                directory = "survey/" + base + "--" + entry["key"]
                write(stage / directory / "request.json", reduced); write(stage / directory / "native.json", result)
                cell = {"status": status, "transport_status": result["status"], "reason": reason, "diagnostics": result["diagnostics"],
                        "context_id": None, "declaration_id": None, "directory": directory,
                        "request_sha256": sha(encoded(reduced) + b"\n"), "native_result_sha256": sha(encoded(result) + b"\n"),
                        "full_input_equivalence": "passed"}
                by_key[entry["key"]]["profiles"][base] = cell
                if status != "supported":
                    summary["unsupported"][base + "--unsupported--" + entry["key"]] = {"directory": directory, "base_profile": base, "root": entry["key"], **cell}
                print(base, entry["key"], status, reason or "", flush=True)
            for family, context in spec["contexts"].items():
                selected = [entry for entry in declared["entries"] if entry["record"] in context["records"] and by_key[entry["key"]]["profiles"][base]["status"] == "supported"]
                if not selected:
                    continue
                context_id = base + "--" + family
                request, mapped = request_for(spec, base, context["component"], context["headers"], [entry["record"] for entry in selected], files, origins, config, args.config_root)
                full = run(native, request)
                if status_for(full)[0] != "supported":
                    raise ValueError("Merged family context failed: " + context_id + " " + str(full["diagnostics"]))
                for entry in selected:
                    if root_meaning(full, entry["record"]) != root_meaning(root_results[(base, entry["record"])], entry["record"]):
                        raise ValueError("Merged family changes original type/layout semantics: " + context_id + " " + entry["key"])
                macro_differences = {}
                macro_value = lambda value: None if value is None else {key: value[key] for key in ("replacement", "function_like")}
                for entry in selected:
                    original_macros = root_results[(base, entry["record"])]["effective_macros"]
                    differences = {name: {"individual": original_macros.get(name), "context": full["effective_macros"].get(name)}
                                   for name in sorted(set(original_macros) | set(full["effective_macros"]))
                                   if macro_value(original_macros.get(name)) != macro_value(full["effective_macros"].get(name))}
                    if differences: macro_differences[entry["key"]] = differences
                reduced, result = reduce_request(native, request, full)
                reduced["dependency_files"] = dependency_files(result)
                result = run(native, reduced)
                destination = stage / context_id
                write(destination / "request.json", reduced); write(destination / "native.json", result)
                info = {"profile": context_id, "base_profile": base, "family": family, "component": context["component"],
                        "context": {key: value for key, value in reduced.items() if key != "files"},
                        "files": {name: mapped[name] for name in reduced["files"]}, "full_input_equivalence": "passed", "individual_root_equivalence": "passed",
                        "individual_effective_macro_differences": macro_differences,
                        "request_sha256": sha(encoded(reduced) + b"\n"), "native_result_sha256": sha(encoded(result) + b"\n")}
                write(destination / "manifest.json", info)
                for virtual, content in reduced["files"].items():
                    path = destination / "files" / virtual.lstrip("/"); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content.encode())
                summary["profiles"][context_id] = {"directory": context_id, "base_profile": base, "family": family, "component": context["component"],
                    "label": "iOS · " + base.replace("-", " · ") + " · " + family, "files": len(reduced["files"]),
                    "input_bytes": sum(len(text.encode()) for text in reduced["files"].values()), "manifest_sha256": sha(encoded(info) + b"\n"),
                    "request_sha256": info["request_sha256"], "native_result_sha256": info["native_result_sha256"], "records": [entry["record"] for entry in selected]}
                for entry in selected:
                    record = next(record for record in result["records"] if record["name"] == entry["record"])
                    by_key[entry["key"]]["profiles"][base].update(context_id=context_id, declaration_id=record["id"])
                print(context_id, "merged/reduced equivalence passed", flush=True)
        coverage["entries"] = list(by_key.values())
        for entry in coverage["entries"]:
            for cell in entry["profiles"].values():
                if cell["status"] == "supported" and cell["context_id"] is None:
                    raise ValueError("Supported root was not assigned to a validated runtime context")
        write(stage / "coverage.json", coverage)
        summary["coverage_sha256"] = sha((stage / "coverage.json").read_bytes())
        validate_coverage(coverage, declared, summary, stage)
        notices = stage / "notices"; notices.mkdir()
        shutil.copyfile(SOURCE_ROOT / "APPLE_LICENSE", notices / "XNU-APPLE_LICENSE.txt")
        shutil.copyfile(args.llvm_source / "clang/LICENSE.TXT", notices / "Clang-LICENSE.txt")
        write(stage / "manifest.json", summary)
        if sha(encoded(source_inventory(SOURCE_ROOT))) != snapshot_sha or sha(args.spec.read_bytes()) != summary["profile_spec_sha256"] or sha(inventory_path.read_bytes()) != summary["inventory_sha256"]:
            raise ValueError("Survey source/spec changed during generation")
        if sha(native.read_bytes()) != native_sha or any(sha((HERE / name).read_bytes()) != digest for name, digest in helper_inputs.items()):
            raise ValueError("Survey compiler/helper changed during generation")
        if sha((args.config_root / "config-provenance.json").read_bytes()) != config_sha:
            raise ValueError("Survey configuration provenance changed during generation")
        if generated_syscalls(spec, snapshot)[1] != generated:
            raise ValueError('Generated syscall inputs changed during survey')
        if generated_mig(spec, args.config_root)[1] != mig:
            raise ValueError('Generated MIG inputs changed during survey')
        if ubc_inputs(spec)[0] != ubc:
            raise ValueError('UBC dependency inputs changed during survey')
        for selected in config["profiles"].values():
            for name, digest in selected["files"].items():
                if sha(local_path(args.config_root, selected["directory"] + "/" + name).read_bytes()) != digest:
                    raise ValueError("Generated configuration changed during survey")
        for origin in origins.values():
            if origin["kind"] == "clang-resource" and sha(local_path(args.llvm_source, origin["path"]).read_bytes()) != origin["sha256"]:
                raise ValueError("Compiler resource changed during survey")
        previous = Path(temporary) / "previous"
        if output.exists(): output.rename(previous)
        try: stage.rename(output)
        except BaseException:
            if previous.exists(): previous.rename(output)
            raise
    print("Survey bundles:", output, flush=True)


if __name__ == "__main__":
    main()
