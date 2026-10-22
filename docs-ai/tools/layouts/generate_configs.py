#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run XNU's original configuration generators using installed host tools.

This builds only the configuration utility, never the kernel. All generated
files stay outside the read-only source checkout. No dependencies are downloaded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DOCS, PROJECT_ROOT, SOURCE_ROOT, require_source


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(name):
    found = shutil.which(name)
    if not found:
        raise RuntimeError(
            f"Missing installed tool: {name}. On Arch Linux, install missing "
            "dependencies with pacman (tcsh, unifdef, bison, flex, clang). "
            "This script never downloads or installs tools."
        )
    return str(Path(found).resolve())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("iPhoneOS", "MacOSX"), default="iPhoneOS",
                        help="Source configuration platform (default: iPhoneOS)")
    parser.add_argument("--output", type=Path,
                        help="Generated directory; defaults to a platform-specific cache")
    parser.add_argument("--cc", default="clang")
    parser.add_argument("--sptm", action="store_true",
                        help="Also generate explicitly named SPTM contexts")
    args = parser.parse_args()
    require_source()
    output = (args.output or PROJECT_ROOT / ".docs-cache/layouts" /
              ("ios-configs" if args.platform == "iPhoneOS" else "macos-configs")).resolve()
    for protected in (SOURCE_ROOT.resolve(), DOCS.resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise RuntimeError("Configuration output must be outside source and handbook trees")
    tools = {name: executable(name) for name in ("tcsh", "unifdef", "bison", "flex")}
    tools["cc"] = executable(args.cc)
    marker = output / ".layout-config-output"
    if output.exists() and any(output.iterdir()) and not marker.is_file():
        raise RuntimeError(f"Refusing nonempty unmarked output directory: {output}")
    manifest_path = output / "config-provenance.json"
    if manifest_path.is_file():
        previous = json.loads(manifest_path.read_text())
        platforms = {profile.get("platform") for profile in previous.get("profiles", {}).values()}
        if platforms != {args.platform}:
            raise RuntimeError("Configuration platform differs from existing output; use a separate --output directory")
    output.mkdir(parents=True, exist_ok=True)
    for path in output.rglob("*"):
        if path.is_symlink() and path != output / "host-bin/unifdef":
            raise RuntimeError(f"Refusing symlink inside generated output: {path}")
    marker.write_text("Platydoc generated XNU configuration files\n")
    manifest_path.unlink(missing_ok=True)
    source = SOURCE_ROOT.resolve()
    utility_source = source / "SETUP/config"
    # Capture inputs before compiling or generating anything. Include every
    # candidate MASTER so a newly added earlier selection is represented.
    inputs = list(utility_source.glob("*"))
    inputs += list((source / "config").glob("MASTER*"))
    inputs += list((source / "osfmk/conf").glob("files*"))
    inputs += list((source / "osfmk/conf").glob("Makefile*"))
    input_hashes = {p.relative_to(source).as_posix(): sha256(p)
                    for p in sorted(inputs) if p.is_file()}
    build = output / "objects/SETUP/config"
    build.mkdir(parents=True, exist_ok=True)
    # Use the resolved installed executable even when the caller's PATH has a
    # different unifdef. doconf invokes unifdef by name.
    host_bin = output / "host-bin"
    host_bin.mkdir(exist_ok=True)
    unifdef_link = host_bin / "unifdef"
    if unifdef_link.is_symlink():
        unifdef_link.unlink()
    elif unifdef_link.exists():
        raise RuntimeError("Refusing to replace non-symlink host-bin/unifdef")
    unifdef_link.symlink_to(tools["unifdef"])
    env = os.environ.copy()
    env.pop("VPATH", None)
    env.update(OBJROOT=str(output / "objects"), SRCROOT=str(source),
               SOURCE=str(source / "osfmk/conf"),
               PATH=str(host_bin) + os.pathsep + env.get("PATH", ""), LC_ALL="C")
    commands = []

    def run(command, cwd=build):
        command = list(map(str, command))
        commands.append({"argv": command, "cwd": str(cwd)})
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=120)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # A child may outlive the parent even after TERM succeeds.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)
            raise
        if process.returncode:
            raise RuntimeError(f"Command failed: {shlex.join(command)}\n"
                               f"{stdout}\n{stderr}")

    run([tools["bison"], "-y", "-d", "-o", "parser.c", utility_source / "parser.y"])
    run([tools["flex"], "--header-file=lexer.yy.h", "-o", "lexer.yy.c",
         utility_source / "lexer.l"])
    sources = ["externs.c", "main.c", "mkheaders.c", "mkioconf.c", "mkmakefile.c",
               "openp.c", "searchp.c"]
    run([tools["cc"], "-g", "-O0", "-DYY_NO_INPUT", "-I" + str(utility_source),
         "-I.", "-o", "config", *[utility_source / name for name in sources],
         "parser.c", "lexer.yy.c"])
    profiles = {}
    for sptm in ([False, True] if args.sptm else [False]):
        for soc in ("t8103", "vmapple"):
            for kernel in ("RELEASE", "DEVELOPMENT"):
                name = f"{kernel.lower()}-{soc}" + ("-sptm" if sptm else "")
                directory = output / "profiles" / name
                directory.mkdir(parents=True, exist_ok=True)
                # Recreate generated headers so meta_features cannot retain
                # includes from a previous configuration generation.
                for old in directory.glob("*.h"):
                    old.unlink()
                (directory / "Makefile").unlink(missing_ok=True)
                (directory / f"config.{kernel}_ARM64").unlink(missing_ok=True)
                command = [tools["tcsh"], "-f", source / "SETUP/config/doconf",
                           "-c", "-cpu", "arm64", "-soc", soc, "-platform", args.platform,
                           "-d", directory, "-s", source / "osfmk/conf",
                           "-m", source / "config"]
                if sptm:
                    command += ["-sptm"]
                command += [kernel]
                run(command)
                makefile = (directory / "Makefile").read_text()
                lines = [line for line in makefile.splitlines()
                         if line.startswith("export CONFIG_DEFINES =")]
                if len(lines) != 1:
                    raise RuntimeError(f"Unexpected CONFIG_DEFINES in {name}")
                definitions = shlex.split(lines[0].split("=", 1)[1])
                macros = {}
                for definition in definitions:
                    if not definition.startswith("-D"):
                        raise RuntimeError(f"Unexpected config definition: {definition}")
                    key, separator, value = definition[2:].partition("=")
                    if key in macros:
                        raise RuntimeError(f"Duplicate config definition: {key}")
                    macros[key] = value if separator else "1"
                files = sorted(directory.glob("*.h"))
                files += [directory / "Makefile", directory / f"config.{kernel}_ARM64"]
                profiles[name] = {
                    "kernel": kernel, "cpu": "arm64", "soc": soc,
                    "platform": args.platform, "sptm": sptm,
                    "directory": directory.relative_to(output).as_posix(),
                    "config_defines": definitions, "macros": macros,
                    "files": {p.name: sha256(p) for p in files},
                    "command": commands[-1],
                }
    for relative, expected in input_hashes.items():
        if sha256(source / relative) != expected:
            raise RuntimeError("XNU configuration source changed during generation")
    host_tools = {}
    for name, path in tools.items():
        flag = "-V" if name == "unifdef" else "--version"
        result = subprocess.run([path, flag], text=True, capture_output=True, timeout=15)
        host_tools[name] = {"path": path, "sha256": sha256(Path(path)),
                            "version": (result.stdout + result.stderr).strip()}
    commit = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                            text=True, capture_output=True, timeout=15)
    manifest = {
        "schema": 1,
        "description": "Original XNU doconf/config outputs; source-derived analysis contexts, not captured product builds",
        "source_commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "source_root": str(source), "source_inputs": input_hashes,
        "generator_sha256": sha256(Path(__file__)), "tools": host_tools,
        "config_binary_sha256": sha256(build / "config"), "commands": commands,
        "environment": {k: env[k] for k in ("OBJROOT", "SRCROOT", "SOURCE", "LC_ALL")},
        "profiles": profiles,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(manifest_path)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error)) from error
