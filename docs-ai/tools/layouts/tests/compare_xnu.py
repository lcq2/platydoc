#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compare exact real XNU contexts in native and WebAssembly frontends."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from xnu_cases import load_cases, requests_hash, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundles", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--wasm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dependencies", action="store_true", help="Include traced dependency interventions")
    args = parser.parse_args()
    case_loader, validate_result = load_cases, validate
    if args.dependencies:
        from xnu_dependency_cases import load_cases as case_loader, validate as validate_result
    inputs = case_loader(args.bundles)
    results = []
    facts = {}
    for name, request in inputs:
        process = subprocess.run([str(args.native.resolve())], input=json.dumps(request),
                                 text=True, capture_output=True, timeout=90, check=True)
        result = json.loads(process.stdout)
        facts[name] = validate_result(name, result)
        if result["status"] == "ok":
            assert result["input_sha256"] == {path: hashlib.sha256(content.encode()).hexdigest()
                                               for path, content in request["files"].items()}
        results.append(result)
        print(f"Native {name}: {result['status']}", flush=True)
    with tempfile.TemporaryDirectory(prefix="layout-xnu-compare-") as temporary:
        requests = Path(temporary) / "requests.json"
        requests.write_text(json.dumps([request for _, request in inputs]))
        process = subprocess.run(["node", str(Path(__file__).with_name("run_wasm.cjs")),
                                  str(args.wasm.resolve()), str(requests)],
                                 capture_output=True, text=True, timeout=180)
        if process.returncode:
            raise RuntimeError(process.stderr)
        wasm = json.loads(process.stdout)
    for (name, _), native, actual in zip(inputs, results, wasm["results"], strict=True):
        validate_result(name, actual)
        assert native == actual, "native/Wasm XNU mismatch: " + name
    report = {"kind": "xnu-contexts", "cases": [name for name, _ in inputs], "results": results,
              "dependency_tracing": args.dependencies,
              "facts": facts, "native_assertions": "passed", "wasm_parity": "passed",
              "requests_sha256": requests_hash(inputs), "wasm_metrics": wasm["metrics"],
              "bundle_manifest_sha256": hashlib.sha256((args.bundles / "manifest.json").read_bytes()).hexdigest(),
              "native_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest(),
              "wasm_factory_sha256": hashlib.sha256(args.wasm.read_bytes()).hexdigest(),
              "wasm_sha256": hashlib.sha256(args.wasm.with_suffix(".wasm").read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"{len(inputs)} XNU contexts/probes passed native/Wasm parity; report {args.output}")


if __name__ == "__main__":
    main()
