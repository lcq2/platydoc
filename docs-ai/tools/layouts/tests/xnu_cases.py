# SPDX-License-Identifier: GPL-2.0-only
"""Verified real-header requests plus clearly separated configuration probes."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bundle_xnu import json_bytes, validate_real_layouts  # noqa: E402


def load_cases(bundle):
    bundle = Path(bundle)
    manifest = json.loads((bundle / "manifest.json").read_bytes())
    result = []
    for name, profile in sorted(manifest["profiles"].items()):
        directory = bundle / profile["directory"]
        raw_manifest = (directory / "manifest.json").read_bytes()
        if hashlib.sha256(raw_manifest).hexdigest() != profile["manifest_sha256"]:
            raise ValueError("profile manifest changed: " + name)
        profile_manifest = json.loads(raw_manifest)
        raw_request = (directory / "request.json").read_bytes()
        if hashlib.sha256(raw_request).hexdigest() != profile_manifest["request_sha256"]:
            raise ValueError("profile request changed: " + name)
        request = json.loads(raw_request)
        for path, content in request["files"].items():
            expected = profile_manifest["files"][path]["sha256"]
            if hashlib.sha256(content.encode()).hexdigest() != expected:
                raise ValueError("header request bytes changed: " + path)
            if (directory / "files" / path.lstrip("/")).read_bytes() != content.encode():
                raise ValueError("raw header differs from request: " + path)
        result.append((name, request))
    baseline = next(request for name, request in result if name == "release-t8103")
    override = copy.deepcopy(baseline)
    override["macros"]["DEBUG"] = "1"
    result.append(("probe-header-redefinition", override))
    defined_zero = copy.deepcopy(baseline)
    defined_zero["macros"]["CONFIG_TASK_SUSPEND_STATS"] = "0"
    result.append(("probe-defined-zero-task-suspend", defined_zero))
    missing = copy.deepcopy(baseline)
    del missing["files"]["/inputs/clang-resource/stdbool.h"]
    missing.get("source_paths", {}).pop("/inputs/clang-resource/stdbool.h", None)
    result.append(("missing-resource-header", missing))
    incomplete = copy.deepcopy(baseline)
    incomplete["files"][incomplete["main"]] = "#include <kern/kern_types.h>\n"
    incomplete["records"] = ["task"]
    result.append(("incomplete-task", incomplete))
    return result


def validate(name, result):
    if name.startswith(("release-", "development-")):
        assert result["status"] == "ok" and not result["diagnostics"], (name, result["diagnostics"])
        return validate_real_layouts(result, name)
    if name in {"missing-resource-header", "incomplete-task"}:
        expected = "unavailable-type" if name == "incomplete-task" else "error"
        assert result["status"] == expected, (name, result)
        assert result["records"] == [] and result["diagnostics"]
        return {"kind": "expected-diagnostic", "status": expected}
    assert result["status"] == "ok", (name, result)
    task = next(r for r in result["records"] if r["name"] == "task")
    macros = result["effective_macros"]
    if name == "probe-header-redefinition":
        assert macros["DEBUG"]["replacement"] == "0"
        assert macros["DEBUG"]["location"]["file"] == "/inputs/generated/debug.h"
        assert task["size_bytes"] == 1632
        assert any(d["severity"] == "warning" and "redefined" in d["message"] for d in result["diagnostics"])
        return {"kind": "header-overrode-command-line", "effective_DEBUG": "0"}
    assert name == "probe-defined-zero-task-suspend"
    assert not result["diagnostics"]
    assert macros["CONFIG_TASK_SUSPEND_STATS"]["replacement"] == "0"
    fields = {f["name"]: f for f in task["fields"]}
    assert "t_suspend_stats" in fields and "t_suspend_sources" in fields
    assert task["size_bytes"] == 2016
    assert fields["t_suspend_stats"]["offset_bits"] == 132 * 8
    assert fields["user_stop_count"]["offset_bits"] == 516 * 8
    return {"kind": "what-if-source-layout-only", "task_size_bytes": 2016,
            "note": "Defined-zero triggers task.h #ifdef; this is not an advertised generated build profile."}


def requests_hash(cases):
    return hashlib.sha256(json_bytes([{ "name": name, "request": request } for name, request in cases])).hexdigest()
