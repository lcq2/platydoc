#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build matching native/Wasm frontends from the pinned LLVM source archive.

Dependencies are provisioned explicitly. This script never downloads, updates a
checkout, or installs a compiler into the user's environment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
EXCLUDED_SOURCE_PATHS = {"clang/test"}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command, *, env, log, timeout=3600):
    print("Running:", " ".join(map(str, command)), flush=True)
    with log.open("a") as output:
        output.write("\n" + " ".join(map(str, command)) + "\n")
        output.flush()
        process = subprocess.Popen(list(map(str, command)), env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
            if code:
                raise subprocess.CalledProcessError(code, command)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Killing only CMake/Ninja leaves their compiler children running.
            # This session belongs solely to this build command.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # The parent may exit while a child ignores TERM. Kill the group
            # even when waiting for the direct parent already succeeded.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
            print("\n".join(log.read_text(errors="replace").splitlines()[-60:]), flush=True)
            raise
        except subprocess.CalledProcessError:
            print("\n".join(log.read_text(errors="replace").splitlines()[-60:]), flush=True)
            raise


def extract(archive, destination, expected_hash):
    if sha256(archive) != expected_hash:
        raise SystemExit("LLVM source archive SHA256 differs from toolchain.lock.json")
    marker = destination / ".source-archive-sha256"
    if marker.exists():
        if marker.read_text().strip() != expected_hash:
            raise SystemExit("existing source extraction is from a different archive")
        return
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit("refusing nonempty, unmarked source extraction directory")
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    with tarfile.open(archive) as source:
        for member in source:
            parts = Path(member.name).parts
            # The tarball root component is the tagged repository name. Keep
            # only the frontend, LLVM support, and their CMake dependencies.
            if len(parts) < 2 or parts[1] not in {"llvm", "clang", "cmake", "third-party"}:
                continue
            relative = Path(*parts[1:])
            if any(relative == Path(prefix) or Path(prefix) in relative.parents
                   for prefix in EXCLUDED_SOURCE_PATHS):
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit("unsafe archive path")
            if not (member.isfile() or member.isdir()):
                raise SystemExit("source archive contains a link or special file")
            target = destination / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as content, target.open("wb") as output:
                    shutil.copyfileobj(content, output)
                target.chmod(member.mode & 0o777)
                hashes[relative.as_posix()] = sha256(target)
    (destination / ".source-files.json").write_text(json.dumps(hashes, sort_keys=True) + "\n")
    marker.write_text(expected_hash + "\n")


def verify_source(source):
    """Reject modified, missing and added files in the selected source input."""
    manifest = source / ".source-files.json"
    expected = json.loads(manifest.read_text())
    observed = {}
    for path in source.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"source input acquired a symlink: {path}")
        if path.is_file() and path.relative_to(source).as_posix() not in {".source-files.json", ".source-archive-sha256"}:
            observed[path.relative_to(source).as_posix()] = sha256(path)
    if observed != expected:
        raise SystemExit("extracted LLVM source changed; restore or use a fresh cache")
    return hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()


def verify_sdk(archive, sdk, expected_hash):
    if sha256(archive) != expected_hash:
        raise SystemExit("emsdk source archive differs from toolchain.lock.json")
    # Installation adds upstream/, node/, downloads/ and local configuration.
    # Check every original SDK source file against the immutable input archive.
    hashes = {}
    with tarfile.open(archive) as source:
        for member in source:
            parts = Path(member.name).parts
            if len(parts) < 2 or member.isdir():
                continue
            relative = Path(*parts[1:])
            if ".." in relative.parts or relative.is_absolute() or not member.isfile():
                raise SystemExit("unsafe SDK source archive member")
            expected = hashlib.sha256(source.extractfile(member).read()).hexdigest()
            path = sdk / relative
            if not path.is_file() or path.is_symlink() or sha256(path) != expected:
                raise SystemExit(f"installed SDK source differs from pinned archive: {relative}")
            hashes[relative.as_posix()] = expected
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-archive", type=Path, required=True)
    parser.add_argument("--emsdk", type=Path, required=True)
    parser.add_argument("--emsdk-archive", type=Path, help="pinned emsdk source archive; required for Wasm")
    parser.add_argument("--cache", type=Path, default=PROJECT / ".docs-cache/layouts")
    parser.add_argument("--artifact-output", type=Path,
                        help="Separate compiler artifacts/notices/provenance from reusable build directories")
    parser.add_argument("--host-cc", default="clang")
    parser.add_argument("--host-cxx", default="clang++")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--phase", choices=("all", "native", "wasm"), default="all")
    args = parser.parse_args()
    cache = args.cache.resolve()
    artifacts = (args.artifact_output or cache).resolve()
    for directory in (cache, artifacts):
        if any(directory == PROJECT / forbidden or directory.is_relative_to(PROJECT / forbidden)
               or (PROJECT / forbidden).is_relative_to(directory) for forbidden in ("docs-ai", "xnu")):
            raise SystemExit("build/cache output must be outside docs-ai/, xnu/ and their ancestors")
    if args.jobs < 1:
        raise SystemExit("jobs must be positive")
    if artifacts != cache and artifacts.exists():
        if not artifacts.is_dir() or (any(artifacts.iterdir()) and
                not (artifacts / ".layout-compiler-artifacts").is_file()):
            raise SystemExit("refusing nonempty unmarked compiler artifact directory")
        if any(path.is_symlink() for path in artifacts.rglob("*")):
            raise SystemExit("refusing symlinks inside compiler artifact directory")
    cache.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    if artifacts != cache:
        (artifacts / ".layout-compiler-artifacts").write_text("Platydoc compiler artifacts, notices and provenance\n")
    lock = json.loads((ROOT / "toolchain.lock.json").read_text())
    source = cache / "llvm-source"
    extract(args.llvm_archive.resolve(), source, lock["llvm"]["archive_sha256"])
    source_identity = verify_source(source)
    sdk = args.emsdk.resolve()
    env = os.environ.copy()
    env["EM_CONFIG"] = str(sdk / ".emscripten")
    env["EMSDK"] = str(sdk)
    version = None
    sdk_source_identity = None
    if args.phase in {"all", "wasm"}:
        if not args.emsdk_archive:
            raise SystemExit("--emsdk-archive is required for Wasm")
        sdk_source_identity = verify_sdk(args.emsdk_archive, sdk, lock["emscripten"]["emsdk_archive_sha256"])
        emcc = sdk / "upstream/emscripten/emcc"
        version = subprocess.run([str(emcc), "--version"], env=env, text=True,
                                 capture_output=True, timeout=30, check=True).stdout
        if f" {lock['emscripten']['version']} " not in version.splitlines()[0]:
            raise SystemExit("Emscripten version differs from toolchain.lock.json")
        emscripten_version_file = sdk / "upstream/emscripten/emscripten-version.txt"
        if emscripten_version_file.read_text().strip().strip('"') != lock["emscripten"]["version"]:
            raise SystemExit("installed Emscripten version file differs from pin")
    native = cache / "build-native"
    wasm = cache / "build-wasm"
    native_output = artifacts / "build-native/bin"
    wasm_output = artifacts / "build-wasm/bin"
    common = [
        "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DLLVM_ENABLE_PROJECTS=clang",
        "-DLLVM_TARGETS_TO_BUILD=AArch64", "-DLLVM_ENABLE_THREADS=OFF",
        "-DLLVM_ENABLE_ZLIB=OFF", "-DLLVM_ENABLE_ZSTD=OFF", "-DLLVM_ENABLE_LIBXML2=OFF",
        "-DLLVM_ENABLE_LIBEDIT=OFF", "-DLLVM_ENABLE_CURL=OFF", "-DLLVM_ENABLE_TERMINFO=OFF",
        "-DLLVM_ENABLE_BACKTRACES=OFF", "-DLLVM_ENABLE_CRASH_OVERRIDES=OFF",
        "-DLLVM_INCLUDE_TESTS=OFF", "-DLLVM_INCLUDE_EXAMPLES=OFF", "-DLLVM_INCLUDE_BENCHMARKS=OFF",
        "-DLLVM_BUILD_TOOLS=OFF", "-DLLVM_BUILD_UTILS=OFF", "-DCLANG_BUILD_TOOLS=OFF",
        "-DCLANG_INCLUDE_TESTS=OFF", "-DCLANG_ENABLE_ARCMT=OFF", "-DCLANG_ENABLE_STATIC_ANALYZER=OFF",
        "-DLLVM_ENABLE_ASSERTIONS=OFF", "-DLLVM_EXTERNAL_PROJECTS=platydoc_layout",
        "-DLLVM_APPEND_VC_REV=OFF",
        f"-DLLVM_FORCE_VC_REVISION={lock['llvm']['revision']}",
        "-DLLVM_FORCE_VC_REPOSITORY=https://github.com/llvm/llvm-project",
        f"-DLLVM_EXTERNAL_PLATYDOC_LAYOUT_SOURCE_DIR={ROOT}",
        f"-DLAYOUT_LLVM_REVISION={lock['llvm']['revision']}",
    ]
    started = time.monotonic()
    build_identity = {
        "source_tree_manifest_sha256": source_identity,
        "wrapper_sha256": sha256(ROOT / "engine.cpp"),
        "cmake_sha256": sha256(ROOT / "CMakeLists.txt"),
        "lock_sha256": sha256(ROOT / "toolchain.lock.json"),
        "common_cmake_options": common,
        "artifact_output": str(artifacts),
    }
    native_identity = native / "layout-build-inputs.json"
    def verify_build_inputs():
        actual = {
            "wrapper_sha256": sha256(ROOT / "engine.cpp"),
            "cmake_sha256": sha256(ROOT / "CMakeLists.txt"),
            "lock_sha256": sha256(ROOT / "toolchain.lock.json"),
        }
        if verify_source(source) != source_identity or any(
                actual[key] != build_identity[key] for key in actual):
            raise SystemExit("inputs changed during the build; rerun the affected phases")

    if args.phase in {"all", "native"}:
        run(["cmake", "-S", source / "llvm", "-B", native, *common,
             f"-DLAYOUT_RUNTIME_OUTPUT_DIRECTORY={native_output}",
             f"-DCMAKE_C_COMPILER={args.host_cc}", f"-DCMAKE_CXX_COMPILER={args.host_cxx}"],
            env=env, log=artifacts / "native-build.log", timeout=300)
        run(["cmake", "--build", native, "--target", "layout-engine", "llvm-tblgen", "clang-tblgen",
             "-j", args.jobs], env=env, log=artifacts / "native-build.log")
        verify_build_inputs()
        native_identity.write_text(json.dumps(build_identity, sort_keys=True) + "\n")
    if args.phase in {"all", "wasm"}:
        if not native_identity.is_file() or json.loads(native_identity.read_text()) != build_identity:
            raise SystemExit("native build inputs differ; rebuild native before Wasm")
        if verify_source(source) != source_identity:
            raise SystemExit("source changed between native and Wasm builds")
        for tool in ("llvm-tblgen", "clang-tblgen"):
            if not (native / "bin" / tool).is_file():
                raise SystemExit("build the native tablegen tools before the Wasm phase")
        run([sdk / "upstream/emscripten/emcmake", "cmake", "-S", source / "llvm", "-B", wasm,
             *common, f"-DLLVM_NATIVE_TOOL_DIR={native / 'bin'}",
             f"-DLAYOUT_RUNTIME_OUTPUT_DIRECTORY={wasm_output}",
             f"-DLLVM_TABLEGEN={native / 'bin/llvm-tblgen'}",
             f"-DCLANG_TABLEGEN={native / 'bin/clang-tblgen'}",
             "-DLLVM_HOST_TRIPLE=wasm32-unknown-emscripten", "-DCMAKE_C_FLAGS_RELEASE=-Oz -DNDEBUG",
             "-DCMAKE_CXX_FLAGS_RELEASE=-Oz -DNDEBUG"],
            env=env, log=artifacts / "wasm-build.log", timeout=300)
        run(["cmake", "--build", wasm, "--target", "layout-engine", "-j", args.jobs],
            env=env, log=artifacts / "wasm-build.log")
        verify_build_inputs()
    notices = artifacts / "notices"
    notices.mkdir(exist_ok=True)
    notice_paths = {
        "LLVM-LICENSE.txt": source / "llvm/LICENSE.TXT",
        "Clang-LICENSE.txt": source / "clang/LICENSE.TXT",
        "LLVM-Support-regex-COPYRIGHT.txt": source / "llvm/lib/Support/COPYRIGHT.regex",
        "LLVM-Support-BLAKE3-LICENSE.txt": source / "llvm/lib/Support/BLAKE3/LICENSE",
    }
    if version:
        notice_paths.update({"Emscripten-LICENSE.txt": sdk / "upstream/emscripten/LICENSE",
                             "Emscripten-AUTHORS.txt": sdk / "upstream/emscripten/AUTHORS",
                             "emsdk-LICENSE.txt": sdk / "LICENSE"})
        for name, relative in {
            "musl-COPYRIGHT.txt": "libc/musl/COPYRIGHT",
            "libcxx-LICENSE.txt": "libcxx/LICENSE.TXT",
            "libcxxabi-LICENSE.txt": "libcxxabi/LICENSE.TXT",
            "compiler-rt-LICENSE.txt": "compiler-rt/LICENSE.TXT",
            "llvm-libc-LICENSE.txt": "llvm-libc/LICENSE.TXT",
            "libunwind-LICENSE.txt": "libunwind/LICENSE.TXT",
        }.items():
            notice_paths[name] = sdk / "upstream/emscripten/system/lib" / relative
    for name, path in notice_paths.items():
        shutil.copyfile(path, notices / name)
    # Preserve additional file-level terms (e.g. xxHash BSD and Unicode's
    # ConvertUTF permission) rather than implying the LLVM umbrella covers all.
    preambles = []
    roots = [source / p for p in ("llvm/lib/Support", "llvm/lib/Demangle",
                                 "llvm/include/llvm/Support", "llvm/include/llvm/ADT",
                                 "llvm/include/llvm/Demangle")]
    if version:
        roots.append(sdk / "upstream/emscripten/system/lib")
    for directory in roots:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in {".cpp", ".c", ".h"}:
                text = path.read_text(errors="replace")
                if "#include" in text:
                    prefix = text.split("#include", 1)[0]
                    if "copyright" in prefix.lower() or "license" in prefix.lower():
                        base = source if path.is_relative_to(source) else sdk
                        preambles.append(str(path.relative_to(base)) + "\n" + prefix + "\n")
    preamble_notice = notices / "Embedded-source-notices.txt"
    preamble_notice.write_text("File-level source notices; original source paths are shown.\n\n" + "\n".join(preambles))
    notice_paths[preamble_notice.name] = preamble_notice
    manifest = {
        "pins": lock, "source_archive_sha256": sha256(args.llvm_archive),
        "build_identity": build_identity,
        "emsdk_source_manifest_sha256": sdk_source_identity, "emcc_version": version,
        "host_cc": subprocess.run([args.host_cc, "--version"], capture_output=True,
                                   text=True, timeout=30, check=True).stdout,
        "host_cxx": subprocess.run([args.host_cxx, "--version"], capture_output=True,
                                    text=True, timeout=30, check=True).stdout,
        "common_cmake_options": common, "phase": args.phase,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "patches": [], "inputs": {}, "artifacts": {},
        "source_extraction_excludes": sorted(EXCLUDED_SOURCE_PATHS),
        "notices": {name: sha256(path) for name, path in notice_paths.items()},
    }
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            manifest["inputs"][path.relative_to(ROOT).as_posix()] = sha256(path)
    for path in (native_output / "layout-engine", wasm_output / "layout-engine.js", wasm_output / "layout-engine.wasm"):
        if path.is_file():
            manifest["artifacts"][path.relative_to(artifacts).as_posix()] = {
                "bytes": path.stat().st_size, "sha256": sha256(path)}
    (artifacts / "toolchain-provenance.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Build provenance: {artifacts / 'toolchain-provenance.json'}", flush=True)


if __name__ == "__main__":
    main()
