#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run synthetic cases, independent assertions, and native/Wasm equality."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from fixtures import cases, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--wasm", type=Path, help="Emscripten factory .js; required for final parity")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = cases()
    results = []
    start = time.monotonic()
    for name, request in inputs:
        process = subprocess.run([str(args.native.resolve())], input=json.dumps(request),
                                 text=True, capture_output=True, timeout=30, check=True)
        result = json.loads(process.stdout)
        validate(name, result)
        # A second request process must yield exactly the same protocol bytes.
        repeat = subprocess.run([str(args.native.resolve())], input=json.dumps(request),
                                text=True, capture_output=True, timeout=30, check=True)
        assert process.stdout == repeat.stdout, f"nondeterministic native output: {name}"
        results.append(result)
    report = {"cases": [name for name, _ in inputs], "native_assertions": "passed",
              "native_wall_ms": round((time.monotonic() - start) * 1000, 3),
              "wasm_parity": "not-run", "results": results}
    if args.wasm:
        with tempfile.TemporaryDirectory(prefix="layout-compare-") as temporary:
            requests_file = Path(temporary) / "requests.json"
            requests_file.write_text(json.dumps([r for _, r in inputs]))
            process = subprocess.run([
                "node", str(Path(__file__).with_name("run_wasm.cjs")),
                str(args.wasm.resolve()), str(requests_file),
            ], text=True, capture_output=True, timeout=180)
            if process.returncode:
                raise RuntimeError(f"Wasm comparison runner failed:\n{process.stderr}")
        wasm = json.loads(process.stdout)
        for (name, _), native_result, wasm_result in zip(inputs, results, wasm["results"], strict=True):
            validate(name, wasm_result)
            assert native_result == wasm_result, f"native/Wasm mismatch: {name}"
        report["wasm_parity"] = "passed"
        report["wasm_metrics"] = wasm["metrics"]
    report["native_sha256"] = hashlib.sha256(args.native.read_bytes()).hexdigest()
    if args.wasm:
        report["wasm_factory_sha256"] = hashlib.sha256(args.wasm.read_bytes()).hexdigest()
        report["wasm_sha256"] = hashlib.sha256(args.wasm.with_suffix(".wasm").read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"{len(inputs)} native cases passed; Wasm parity: {report['wasm_parity']}")


if __name__ == "__main__":
    main()
