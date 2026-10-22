#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Create the review-only handbook layout mockup from verified saved layouts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from paths import PROJECT_ROOT, SOURCE_ROOT, DOCS
sys.path.insert(0, str(HERE / "tests"))
from xnu_dependency_cases import load_cases, requests_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/milestone4-xnu-comparison.json")
    parser.add_argument("--bundles", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/xnu-bundles")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / ".docs-cache/layouts/mockup-handbook")
    args = parser.parse_args()
    output = args.output.resolve()
    for protected in (SOURCE_ROOT.resolve(), DOCS.resolve()):
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError("Mockup output must be outside handbook and XNU sources")
    if output.exists() and (not output.is_dir() or (any(output.iterdir()) and not (output / ".layout-mockup").is_file())):
        raise ValueError("Refusing nonempty unmarked output")
    if output.exists() and any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("Refusing symlinks in mockup output")
    raw = args.report.read_bytes()
    report = json.loads(raw)
    cases = load_cases(args.bundles)
    if report.get("wasm_parity") != "passed" or report.get("requests_sha256") != requests_hash(cases):
        raise ValueError("Mockup requires passing evidence for these exact saved requests")
    bundle = json.loads((args.bundles / "manifest.json").read_bytes())
    wanted = {"release-t8103", "development-t8103", "release-vmapple", "development-vmapple", "probe-no-cpi", "probe-no-energy", "probe-neither-counter"}
    profiles = []
    for name, request in cases:
        if name not in wanted:
            continue
        result = report["results"][report["cases"].index(name)]
        if result["status"] != "ok":
            raise ValueError("Saved mockup case did not succeed: " + name)
        profiles.append({"id": name, "label": name,
                         "request": {k: v for k, v in request.items() if k != "files"},
                         "result": {k: result[k] for k in ("records", "effective_macros", "target", "status")}})
    data = {"source": {"release": bundle["source_release"], "revision": bundle["source_commit"]},
            "bookRoot": Path(os.path.relpath(PROJECT_ROOT / "docs-ai-html", output)).as_posix() + "/",
            "defaultProfile": "release-t8103", "profiles": profiles,
            "note": "Design mockup using recorded native/Wasm-verified layouts; no live analysis."}
    output.mkdir(parents=True, exist_ok=True)
    (output / ".layout-mockup").write_text("Platydoc layout browser design preview\n")
    for name in ("index.html", "mockup.css", "mockup.js"):
        shutil.copyfile(HERE / "mockup" / name, output / name)
    shutil.copyfile(HERE.parent / "book/assets/book.css", output / "book.css")
    (output / "recorded-data.js").write_text("// Recorded layout metadata; upstream terms remain applicable.\nwindow.LayoutMockupData=" + json.dumps(data, separators=(",", ":"), ensure_ascii=True) + ";\n")
    for source, name in ((PROJECT_ROOT / "LICENSE", "LICENSE-software.txt"),
                         (PROJECT_ROOT / "LICENSE-DOCS", "LICENSE-docs.txt"),
                         (SOURCE_ROOT / "APPLE_LICENSE", "LICENSE-xnu.txt")):
        shutil.copyfile(source, output / name)
    manifest = {"kind": "design-mockup", "native_wasm_report_sha256": hashlib.sha256(raw).hexdigest(),
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file() and p.name not in {"manifest.json", "preview-report.json"} and p.suffix != ".png"}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(output / "index.html")


if __name__ == "__main__":
    main()
