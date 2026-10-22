#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build exact XNU header closures and prove they preserve full-input analysis."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, require_source  # noqa: E402
sys.path.insert(0, str(ROOT))
from build import verify_source  # noqa: E402


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode()


def git(*args):
    return subprocess.run(["git", "-C", str(SOURCE_ROOT), *args], capture_output=True,
                          text=True, timeout=30, check=True).stdout.strip()


def exports(spec):
    """Read the literal/variable-only EXPORT_MI lists used by these Makefiles."""
    aliases = {}
    for export in spec["exports"]:
        path = SOURCE_ROOT / export["makefile"]
        text = path.read_text().replace("\\\n", " ")
        variables = {}
        for line in text.splitlines():
            match = re.fullmatch(r"([A-Z_]+)\s*=\s*(.*?)\s*", line)
            if match:
                variables[match[1]] = match[2].split("#", 1)[0].strip()

        def expand(name, stack=()):
            if name in stack or name not in variables:
                raise ValueError(f"unsupported export variable {name} in {path}")
            return re.sub(r"\$\{([A-Z_]+)\}|\$\(([A-Z_]+)\)",
                          lambda m: expand(m[1] or m[2], (*stack, name)), variables[name])

        names = expand("EXPORT_MI_LIST").split()
        directory = expand("EXPORT_MI_DIR")
        for name in names:
            relative = Path(directory) / name
            if "$" in name or relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsupported exported header name: {name}")
            virtual = f"/inputs/exports/{export['component']}/{relative.as_posix()}"
            source = SOURCE_ROOT / export["directory"] / name
            aliases[virtual] = (source, export["makefile"])
    return aliases


def analyze(native, request):
    data = json_bytes(request)
    process = subprocess.run([str(native)], input=data, capture_output=True, timeout=90, check=True)
    result = json.loads(process.stdout)
    if result.get("status") != "ok":
        messages = "\n".join(d["message"] for d in result.get("diagnostics", []))
        raise RuntimeError(f"XNU header context failed ({result.get('status')}):\n{messages}")
    if result.get("diagnostics"):
        raise RuntimeError("XNU profile produced diagnostics; no ignored attributes/warnings are accepted:\n" +
                           "\n".join(d["message"] for d in result["diagnostics"]))
    return result


def comparable(result):
    result = copy.deepcopy(result)
    result.pop("input_sha256", None)
    return result


def validate_real_layouts(result, profile):
    records = {r["name"]: r for r in result["records"] if r["name"]}
    macro = result["effective_macros"]
    spec = json.loads((ROOT / "profiles/arm64-xnu.json").read_bytes())
    board = spec["boards"][profile.split("-", 1)[1]]
    # Independent pinned driver -### / -E -dM probes of the source -mcpu or
    # -march option established these expectations; __ARM_ARCH alone is only
    # the major architecture number and cannot detect missing feature expansion.
    assert result["driver_target"] == board["expected_driver"], (profile, result["driver_target"])
    for name, value in board["expected_target_builtins"].items():
        actual = macro[name]["replacement"] if macro[name] is not None else None
        assert actual == value, (profile, name, actual, value)
    cpi = int(macro["CONFIG_PERVASIVE_CPI"]["replacement"]) if macro["CONFIG_PERVASIVE_CPI"] else 0
    energy = int(macro["CONFIG_PERVASIVE_ENERGY"]["replacement"]) if macro["CONFIG_PERVASIVE_ENERGY"] else 0
    secure = int(macro["RECOUNT_SECURE_METRICS"]["replacement"])
    track = records["recount_track"]
    expected = 8 + 8 * (1 + 2 * cpi) * (2 + secure) + 8 * energy
    assert track["alignment_bytes"] == 8 and track["size_bytes"] == expected, track
    assert [field["offset_bits"] for field in track["fields"]] == [0, 32, 64], track
    task = records["task"]
    names = {field["name"] for field in task["fields"]}
    development = profile.startswith("development-")
    assert ("ref_group" in names) == development, (profile, names)
    assert ("ref_group_lock" in names) == development, (profile, names)
    assert ("t_suspend_stats" in names) == (macro["CONFIG_TASK_SUSPEND_STATS"] is not None)
    assert ("t_suspend_sources" in names) == (macro["CONFIG_TASK_SUSPEND_STATS"] is not None)
    assert task["size_bytes"] > 0 and task["alignment_bytes"] >= 8
    # Independent Clang-driver/LLVM-constant checks established these values
    # from the complete physical source context, not from this wrapper output.
    assert task["size_bytes"] == (2072 if development else 1632), (profile, task["size_bytes"])
    fields = {field["name"]: field for field in task["fields"]}
    expected_offsets = {"lock": 0, "ref_count": 16,
        "active": 56 if development else 20,
        "task_uniqueid": 72 if development else 32,
        "suspend_count": 168 if development else 128,
        "user_stop_count": 556 if development else 132}
    if development:
        expected_offsets.update(ref_group=32, ref_group_lock=40, t_suspend_stats=172, t_suspend_sources=204,
                                suspends_outstanding=1466 if profile.endswith("vmapple") else 1467)
    for name, offset in expected_offsets.items():
        assert fields[name]["offset_bits"] == offset * 8, (profile, name, fields[name])
    assert macro["__arm64__"]["replacement"] == "1"
    assert macro["__GNUC__"]["replacement"] == "4"
    assert macro["__BLOCKS__"]["replacement"] == "1"
    assert macro["__STDC_HOSTED__"]["replacement"] == "0"
    return {"recount_track_size_bytes": expected, "task_size_bytes": task["size_bytes"],
            "task_alignment_bytes": task["alignment_bytes"], "cpi": cpi, "energy": energy,
            "secure": secure, "development_fields": development}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--config-root", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/xnu-configs")
    parser.add_argument("--llvm-source", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/llvm-source")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/xnu-bundles")
    args = parser.parse_args()
    args.native = args.native.resolve()
    output = args.output.resolve()
    for protected in (SOURCE_ROOT.resolve(), (PROJECT_ROOT / "docs-ai").resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise SystemExit("header bundles must be outside source/handbook trees and their ancestors")
    if output.exists() and any(output.iterdir()) and not (output / ".layout-xnu-bundles").is_file():
        raise SystemExit("refusing nonempty unmarked bundle output")
    if output.exists():
        for path in output.rglob("*"):
            if path.is_symlink():
                raise SystemExit(f"refusing symlink in bundle output: {path}")
    require_source()
    spec = json.loads((ROOT / "profiles/arm64-xnu.json").read_text())
    if git("rev-parse", "HEAD") != spec["source_commit"] or git("status", "--porcelain"):
        raise SystemExit("XNU source must be the clean pinned checkout")
    lock = json.loads((ROOT / "toolchain.lock.json").read_text())
    source_manifest_sha = verify_source(args.llvm_source)
    source_manifest = json.loads((args.llvm_source / ".source-files.json").read_text())
    config_manifest = json.loads((args.config_root / "config-provenance.json").read_text())
    if config_manifest["generator_sha256"] != digest((ROOT / "generate_configs.py").read_bytes()):
        raise SystemExit("configuration generator changed; regenerate configurations first")
    if config_manifest["source_commit"] != spec["source_commit"]:
        raise SystemExit("generated configuration belongs to a different XNU source")
    for relative, expected in config_manifest["source_inputs"].items():
        if digest((SOURCE_ROOT / relative).read_bytes()) != expected:
            raise SystemExit(f"configuration source changed: {relative}")
    for profile_id in spec["configurations"]:
        config = config_manifest["profiles"][profile_id]
        config_dir = args.config_root / config["directory"]
        if not config_dir.resolve().is_relative_to(args.config_root.resolve()):
            raise SystemExit("configuration path escapes its generated root")
        for name, expected in config["files"].items():
            if Path(name).name != name or digest((config_dir / name).read_bytes()) != expected:
                raise SystemExit(f"configuration output changed: {profile_id}/{name}")
        lines = [line for line in (config_dir / "Makefile").read_text().splitlines()
                 if line.startswith("export CONFIG_DEFINES =")]
        if len(lines) != 1:
            raise SystemExit("missing/ambiguous generated CONFIG_DEFINES")
        definitions = shlex.split(lines[0].split("=", 1)[1])
        observed = {}
        for definition in definitions:
            if not definition.startswith("-D"):
                raise SystemExit("unsupported generated config option")
            name, separator, value = definition[2:].partition("=")
            if name in observed:
                raise SystemExit("duplicate generated config macro")
            observed[name] = value if separator else "1"
        if definitions != config["config_defines"] or observed != config["macros"]:
            raise SystemExit("configuration manifest macros disagree with generated Makefile")
    # Supply the entire tracked header/include-file universe for discovery,
    # including files seen only by __has_include. Host headers never participate.
    universe = {}
    origins = {}
    tracked = git("ls-files").splitlines()
    for relative in tracked:
        path = SOURCE_ROOT / relative
        if path.suffix.lower() in {".h", ".inc", ".def", ".defs", ".hpp"}:
            data = path.read_bytes()
            virtual = "/inputs/xnu/" + relative
            universe[virtual] = data.decode("utf-8")
            origins[virtual] = {"kind": "xnu", "path": relative, "sha256": digest(data)}
    for path in sorted((args.llvm_source / "clang/lib/Headers").rglob("*.h")):
        relative = path.relative_to(args.llvm_source).as_posix()
        data = path.read_bytes()
        if source_manifest.get(relative) != digest(data):
            raise SystemExit(f"Clang resource differs from pinned source: {relative}")
        virtual = "/inputs/clang-resource/" + path.relative_to(args.llvm_source / "clang/lib/Headers").as_posix()
        universe[virtual] = data.decode("utf-8")
        origins[virtual] = {"kind": "clang-resource", "path": relative, "sha256": digest(data)}
    for virtual, (path, makefile) in exports(spec).items():
        data = path.read_bytes()
        universe[virtual] = data.decode("utf-8")
        origins[virtual] = {"kind": "xnu-export", "path": path.relative_to(SOURCE_ROOT).as_posix(),
                            "makefile": makefile, "sha256": digest(data)}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix=".layout-xnu-stage-", dir=output.parent)
    args.output = Path(temporary.name) / "bundles"
    args.output.mkdir()
    (args.output / ".layout-xnu-bundles").write_text("Platydoc generated XNU header bundles\n")
    summary = {"schema": 1, "source_release": spec["source_release"], "source_commit": spec["source_commit"],
               "scope": spec["scope"], "compiler": lock["llvm"], "llvm_source_manifest_sha256": source_manifest_sha,
               "flag_policy": spec["flag_policy"],
               "config_manifest_sha256": digest((args.config_root / "config-provenance.json").read_bytes()),
               "profile_spec_sha256": digest((ROOT / "profiles/arm64-xnu.json").read_bytes()),
               "source_evidence": {p: digest((SOURCE_ROOT / p).read_bytes()) for p in spec["evidence"]},
               "discovery_universe": origins, "profiles": {}}
    for profile_id in spec["configurations"]:
        config = config_manifest["profiles"][profile_id]
        config_dir = args.config_root / config["directory"]
        board = spec["boards"][config["soc"]]
        files = dict(universe)
        profile_origins = dict(origins)
        generated_macro_names = set()
        for name, expected in config["files"].items():
            if not name.endswith(".h"):
                continue
            data = (config_dir / name).read_bytes()
            if digest(data) != expected:
                raise SystemExit(f"generated configuration changed: {profile_id}/{name}")
            virtual = "/inputs/generated/" + name
            files[virtual] = data.decode("utf-8")
            generated_macro_names.update(re.findall(r"^\s*#\s*define\s+([A-Za-z_]\w*)", files[virtual], re.MULTILINE))
            profile_origins[virtual] = {"kind": "generated-config", "path": f"{config['directory']}/{name}", "sha256": expected}
        files["/inputs/request.c"] = spec["main"]
        profile_origins["/inputs/request.c"] = {"kind": "analysis-entry", "sha256": digest(spec["main"].encode())}
        macros = {**config["macros"], **spec["base_macros"], board["board_macro"]: "1",
                  "CURRENT_MACHINE_CONFIG_LC": config["soc"]}
        request = {key: copy.deepcopy(spec[key]) for key in (
            "target", "language", "blocks", "kernel_mode", "records", "include_dirs", "forced_includes", "observe_macros")}
        request.update({"main": "/inputs/request.c", "files": files, "macros": macros,
                        "target_features": board["target_features"], "trace_files": True})
        request.update({key: board[key] for key in ("target_cpu", "target_arch") if key in board})
        request["observe_macros"] = sorted(set(request["observe_macros"]) | generated_macro_names | set(macros))
        request["source_paths"] = {name: ("xnu/" if origin["kind"].startswith("xnu") else origin["kind"] + "/") + origin.get("path", name.lstrip("/"))
                                   for name, origin in profile_origins.items()}
        print(f"Discovering {profile_id}: {len(files)} complete input files", flush=True)
        full = analyze(args.native, request)
        if full["compiler"]["revision"] != lock["llvm"]["revision"]:
            raise SystemExit("native engine compiler differs from pin")
        # Expansion events are scoped to exact selected-declaration provenance;
        # conditions/definitions/pragmas remain traced across consumed headers.
        dependency_files = set()
        def source_files(value):
            if isinstance(value, dict):
                if isinstance(value.get("file"), str) and value["file"] in files:
                    dependency_files.add(value["file"])
                for child in value.values():
                    source_files(child)
            elif isinstance(value, list):
                for child in value:
                    source_files(child)
        for declaration in full["declarations"]:
            source_files(declaration["source"])
            source_files(declaration["scope"])
        request["dependency_files"] = sorted(dependency_files)
        selected = set(full["consumed_files"])
        if "/inputs/request.c" not in selected:
            raise SystemExit("preprocessor trace omitted the main input")
        request["files"] = {name: files[name] for name in sorted(selected)}
        request["source_paths"] = {name: request["source_paths"][name] for name in sorted(selected)}
        reduced = analyze(args.native, request)
        if comparable(full) != comparable(reduced):
            raise SystemExit(f"reduced header bundle changed preprocessing/layouts: {profile_id}")
        for name, value in reduced["input_sha256"].items():
            if value != profile_origins[name]["sha256"]:
                raise SystemExit(f"engine did not consume original bytes: {name}")
        facts = validate_real_layouts(reduced, profile_id)
        destination = args.output / profile_id
        destination.mkdir(exist_ok=True)
        (destination / "request.json").write_bytes(json_bytes(request))
        (destination / "native.json").write_bytes(json_bytes(reduced))
        manifest = {"profile": profile_id, "context": {key: value for key, value in request.items() if key != "files"},
                    "facts": facts, "full_input_equivalence": "passed",
                    "files": {name: profile_origins[name] for name in sorted(selected)},
                    "request_sha256": digest(json_bytes(request)),
                    "native_result_sha256": digest(json_bytes(reduced))}
        (destination / "manifest.json").write_bytes(json_bytes(manifest))
        for virtual, content in request["files"].items():
            raw = destination / "files" / virtual.lstrip("/")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(content.encode("utf-8"))
        summary["profiles"][profile_id] = {"directory": profile_id, "files": len(selected),
            "input_bytes": sum(len(content.encode()) for content in request["files"].values()),
            "manifest_sha256": digest(json_bytes(manifest)), **facts}
        print(f"  reduced to {len(selected)} exact files; recount={facts['recount_track_size_bytes']}B task={facts['task_size_bytes']}B", flush=True)
    # Original notices and exact copied header bytes retain upstream terms.
    notices = args.output / "notices"
    notices.mkdir(exist_ok=True)
    shutil.copyfile(SOURCE_ROOT / "APPLE_LICENSE", notices / "XNU-APPLE_LICENSE.txt")
    shutil.copyfile(args.llvm_source / "clang/LICENSE.TXT", notices / "Clang-LICENSE.txt")
    (args.output / "manifest.json").write_bytes(json_bytes(summary))
    previous = Path(temporary.name) / "previous"
    if output.exists():
        output.rename(previous)
    try:
        args.output.rename(output)
    except BaseException:
        if previous.exists():
            previous.rename(output)
        raise
    temporary.cleanup()
    print(f"XNU bundle manifest: {output / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    main()
