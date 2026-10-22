# Pages layout provisioning

`workflows/pages.yml` builds the complete handbook and layout explorer on an
Ubuntu 24.04 runner. A cold job installs normal distribution dependencies, then
downloads the official LLVM and emsdk source archives named in
[`toolchain.lock.json`](../docs-ai/tools/layouts/toolchain.lock.json). The helper
checks their SHA256 before extracting or running SDK source. It checks the
pinned emsdk release lookup and installs/activates **6.0.13**, never `latest`.
The verified official installer downloads release-addressed SDK binaries;
this repository does not claim independent SHA256 pins for those secondary
downloads. Build provenance records the resulting tools and compiler artifacts.

The native and Wasm frontends use the same pinned LLVM source and wrapper.
Two build jobs limit memory use; the workflow allows 180 minutes for a cold
build. It needs several GiB of disk space and fails clearly when insufficient.
It does not delete unrelated preinstalled runner software.

Only compact compiler artifacts, notices, provenance and an integrity receipt
are cached. The cache identity includes exact semantic/build inputs, the
reviewed baseline, the CI helper and host/tool/image versions. Restores require
matching context, complete file membership, hashes, executable modes and build
provenance. There are no broad fallback cache keys. Verified source archives
have a separate cache; the LLVM resource source is restored from its checked
archive even on a compiler-cache hit. Build trees and generated catalog results
are not reused as proof.

Every run generates fresh iPhoneOS configurations, surveys all 264 structure /
profile cells, and compares all 126 native/Wasm cases. Before admitting a
runner-specific artifact pin, `layouts_ci.py pin` compares the actual complete
request identities and actual compact results with
[`layouts-semantic-baseline.json`](layouts-semantic-baseline.json). The reviewed
matrix includes 64 supported header contexts, 60 boundary cases and two
intervention cases. The source inventory, profiles, declarations, engine,
contract and generation inputs are bound too. Missing/extra/reordered cases,
changed unsupported diagnostics, changed PAC fields or rehashed fresh results
cannot silently refresh the baseline. The exact 66-root inventory, four source
profiles, status totals and context/boundary membership are recorded in the
reviewed baseline. These are explicit reviewed inputs, rather than hardcoded
historical counts in the helper. This catalog parity is required build evidence
for the packaged artifacts and pin, rather than an optional regression suite.
The semantic gate runs once inside `pin`; there is no duplicate CI invocation.

The runtime packager additionally validates the full trace and header evidence.
Only after these checks does `layouts_ci.py pin` derive Ubuntu-specific binary,
configuration-provenance and runtime hashes for the ephemeral workspace copy of
`artifact-ios.lock.json`. It validates that pin through the production catalog
validator before the book build. No source change is committed by the job.
The normal Pages artifact includes the complete runtime, headers, catalog,
coverage, source viewers, licenses and offline ZIP; layout failures fail the job
rather than publishing a reduced book.

## Minimal default and optional regressions

Push builds and ordinary manual runs use the minimal path: two cheap local
layout-asset loading/recovery checks, production catalog generation/parity,
runtime packaging/pin validation, and the handbook build's normal integrity
checks. They do not run the broad geometry, PAC-guard, worker/runtime or
handbook unit suites.

To run those regression suites, manually dispatch the workflow and enable
**full_tests** (default **false**). This adds the fixed IPv6/thread geometry
checks, PAC override checks, runtime lifecycle tests, CI admission/cache/archive
fixtures, Python book unit tests and browser-asset JavaScript tests. It does
not change the produced artifact format or relax any production validation
when disabled.

## Local validation

The minimal local reader check does not run a compiler or build:

```sh
node docs-ai/tools/layouts/tests/book-layouts.test.cjs
```

For optional CI helper regressions, run `python3 -B .github/test_layouts_ci.py -v`.
Existing artifact admission can be checked separately without rebuilding LLVM
or downloading tools:

```sh
python3 -B .github/layouts_ci.py pin --output /tmp/platydoc-ci-artifact-pin.json
```

`pin` already checks semantics. Use `check-semantics` alone only when diagnosing
a baseline mismatch without deriving a pin; do not routinely run both.

Custom artifact locations can be supplied with `--bundles`, `--comparison`,
`--runtime`, `--native` and `--configs`. The temporary pin command leaves the
checked-in artifact pin unchanged. These tests establish local helper behavior;
they are not evidence that a fresh hosted Ubuntu run or Pages deployment passed.
Default catalog paths are `.docs-cache/layouts/structure-bundles`,
`structure-comparison.json` and `structure-runtime`; the existing pinned
compiler and generated configuration paths remain `milestone8-compiler` and
`milestone8-configs`. Local expansion validation may pass the preserved
`expansion-bundles` and `expansion-comparison.json` explicitly.

## Reviewed baseline updates

Ordinary chapter prose, CSS and book-shell edits do not change the semantic
baseline. Fresh book/runtime provenance still binds those inputs separately.
Changes to XNU, the compiler, source profiles, exports, contract semantics or
survey logic require review:

1. Update the affected source/configuration/inventory tooling through its normal
   maintenance workflow. Preserve previous proof artifacts.
2. Generate the survey and native/Wasm comparison required by the baseline
   format. Review changed declarations and representative geometry. Additional
   regression tests are needed only for the corresponding engine/runtime changes;
   catalog additions do not require independent whole-catalog or browser audits.
3. Explicitly regenerate the baseline from that reviewed local evidence:

   ```sh
   python3 -B .github/layouts_ci.py make-baseline --reviewed
   ```

4. Review the JSON diff: source/tool changes, every changed request/result hash,
   case membership and coverage. Do not rerun already passing smoke checks.

The workflow never calls `make-baseline`; that command refuses to run when
`GITHUB_ACTIONS=true`. A CI mismatch requires investigation and local review,
not an automatic baseline refresh.

The helper and tests use GPL-2.0-only ([LICENSE](../LICENSE)); this explanation
uses CC BY 4.0 ([LICENSE-DOCS](../LICENSE-DOCS)). Upstream compiler/SDK notices
retain their own terms.
