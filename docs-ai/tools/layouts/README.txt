Platydoc layout engine — compiler and XNU context proofs
======================================================

These tools are GPL-2.0-only; see the project-root LICENSE. LLVM, Clang,
Emscripten and their runtime components retain their upstream terms. This
directory contains original wrapper/build/test code, not vendored compiler
source or generated artifacts.

Routine validation (start here)
-------------------------------
Use a small smoke suite for ordinary catalog changes; aim to finish a batch
within 20 minutes. Reuse the pinned compiler. Review new source declarations,
check one representative size/nested offset, and compare native/Wasm output
only for affected header contexts. Add a second configuration when conditional
fields change. For example, against already generated current bundles:

  python3 -B docs-ai/tools/layouts/tests/smoke_catalog.py \
    --bundles .docs-cache/layouts/structure-bundles \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/milestone8-compiler/build-wasm/bin/layout-engine.js \
    --context release-t8103--ipv6-wire
  node docs-ai/tools/layouts/tests/book-layouts.test.cjs

Choose exact context IDs from the bundle manifest; repeat --context only for
other affected families. Smoke compares complete returned layouts and checks
iOS/PAC state, but does not create a release comparison or admit an artifact
pin. It consumes existing survey requests: regenerate affected input evidence
before using it to validate changed catalog declarations. It does not discover
new roots merely from an edited inventory.

Run one focused file:// browser interaction only for changed UI/binding code or
a concrete integration concern. Do not routinely rerun the historical milestone
commands below, all profiles, external-compiler geometry audits, ZIP audits,
HTTPS/fallback matrices or whole-book regressions. The milestone sections are
reference procedures for targeted investigation and explicit full validation;
their old acceptance requirements are not a cumulative maintenance checklist.

Local preparation and Pages publication are separate. After generating and
validating the handbook locally, export/upload its completed layout assets:

  python3 docs-ai/tools/layouts/prepared.py publish \
    --book docs-ai-html --repo lcq2/platydoc

This uses an authenticated GitHub CLI and saves only the small
runtime/prepared-layouts.release.json reference for Git. The archive is a
versioned release asset, containing the layout catalog, headers, compiled Wasm,
browser assets and notices, with no native compiler, SDK or LLVM build tree.
Pages downloads the specified release asset and renders HTML:

  python3 docs-ai/tools/layouts/prepared.py download \
    --reference runtime/prepared-layouts.release.json \
    --output .docs-cache/layouts/prepared-layouts.tar.gz
  python3 make_docs.py --prepared-layouts .docs-cache/layouts/prepared-layouts.tar.gz --publish-only

For the first migration, upload the existing archive using publish --archive,
then stop tracking it with git rm --cached. See .github/README.md for exact
commands. Upload must succeed before committing the workflow/reference change.
The helper never commits, pushes, untracks files or rewrites history itself.

GitHub runs no layout generation, native compiler, comparisons, tests or
validation. The published browser uses Wasm for interactive analysis and flag
changes. Default local builds keep their preparation/validation behavior.
Stop after focused local checks pass unless a concrete failure justifies more
work; the historical native proof commands below are offline maintenance only.

Scope
-----
This provides the compiler proof, conservative configuration-dependency
discovery, offline worker runtime and live handbook explorer. The historical
four-profile proof analyzes complete, unmodified recount.h/task.h closures for
RELEASE/DEVELOPMENT and T8103/VMAPPLE. The documented-structure survey described
below expands the finite root inventory using separate source-header families.
The normal book build consumes reviewed offline artifacts and never downloads
or builds LLVM.

engine.cpp is compiled unchanged for the native host and WebAssembly. It uses
Clang CompilerInstance, ASTFrontendAction, ASTContext and ASTRecordLayout, not
text parsing of compiler layout dumps. Each call owns a complete in-memory
filesystem, compiler instance and AST. Destruction releases all per-request
compiler objects. The returned UTF-8 JSON allocation must be released with
layout_free; the caller separately owns its request allocation. No AST or
mutable file registry survives a call. Loading files is part of each request.

Compiler transport (schema 2)
-------------------------------
Native executable: one JSON request on stdin, one JSON response on stdout.
Analysis failure is a JSON status, not a nonzero process exit. Allocation
failure can produce process exit 2. Callers must impose a finite timeout.

Wasm exports:
  char *layout_analyze(const char *NUL_terminated_UTF8_JSON);
  void layout_free(char *response);
  malloc/free plus UTF8ToString/stringToUTF8/lengthBytesUTF8 runtime helpers.

Request:
  {
    "target": "aarch64-apple-darwin",
    "main": "/inputs/main.c",
    "files": {"/inputs/main.c": "#include \"types.h\"\nstruct S { long x; };",
              "/inputs/types.h": "/* supplied header */"},
    "macros": {"UNDEFINED": null, "ZERO": "0", "ENABLED": "1"},
    "records": ["S"]
  }

target/main/files are required. macros/records are optional. With records,
each selected tag must have a complete definition; output contains selected
records and all records embedded through fields/arrays. Unrelated declarations
and pointer referents are excluded from layouts. Referenced declarations and
typedef aliases remain in the declaration catalog. Without records, all defined
records, including function-local records, are returned. Typedef-name selection
is unsupported; ambiguous tag-name selections fail closed.

Source paths must be below /inputs/. Defaults are GNU C11, freestanding mode,
an explicit target, /inputs include search and disabled builtin/system include
directories. It never overlays the host filesystem. Optional typed inputs are:

  source_paths: optional virtual-to-physical source identity mapping
  language: gnu11 or gnu17
  include_dirs: ordered supplied /inputs/ directories
  forced_includes: ordered supplied /inputs/ header filenames
  target_cpu: upstream CPU selection expanded by the pinned Clang driver
  target_arch: source architecture selection armv8.5a+sme2 (exclusive with CPU)
  target_features: explicit +/-v8.5a and +/-sme2 overrides only
  blocks: enable the actual Clang blocks extension
  kernel_mode: disabled builtins, GNU compatibility 4.2.1, maximum type alignment 16
  ptrauth_intrinsics/ptrauth_calls: actual Clang language feature switches;
                  absent means false for historical requests, not inferred
                  from a CPU name or target macro
  observe_macros: final replacement tokens/definition locations; request macro
                  names are included whenever observation or tracing is enabled
  trace_files: return every supplied file's exact SHA256, consumed/probed paths,
               and successful/failed __has_include/__has_include_next outcomes

Unknown feature overrides fail closed: Clang's AST-only ARM64 path otherwise
accepts unknown names silently. XNU profiles explicitly use GNU17 and kernel
semantics, including GNU compatibility 4.2.1, __BLOCKS__=1 and __STDC_HOSTED__=0. GNU17 is an
analysis choice matching pinned Clang's C default, not an explicit XNU -std flag.
The profile JSON records source evidence and included/excluded compiler options.
Builtin target macros come from the pinned frontend. The synthetic cases need
no resource headers; real contexts supply exact pinned Clang resource headers.
All additional headers must be explicitly supplied.
Arbitrary compiler flags, plugins, modules, PCH and code generation are absent.

Response status is ok, invalid-request, error, unavailable-type, or
unsupported-layout. Any error returns an empty records array; recovered or
partial ASTs never supply trusted layouts. diagnostics include severity,
message, Clang ID when applicable, and available physical file/line/column.
Records expose byte size/alignment and field bit offsets; field types expose
bit sizes/alignment, nested record references, array element types/counts and
flexible-array status. Flexible arrays have null fixed size/count and a known
element stride. Pointer type size describes the pointer, not its referent.
Unnamed and zero-width bitfields remain explicit fields. Union offsets overlap.

Transport schema 2 replaces the prototype location IDs with source-based IDs.
They hash declaration kind, UTF-8 physical path/byte length, exact file SHA256,
byte anchor, lexical scopes, complete macro frames and every point's include-site
chain. Names, field indices, configurations, raw SourceLocation/FileID encodings
and scratch-buffer offsets do not define identity. Fields and aliases have their
own IDs. Type/layout variants are separate from declaration identity. IDs are
stable across configurations of identical source inputs, not arbitrary source
edits or moves. Token-pasted names use a physical macro-invocation anchor,
physical expansion/include frames and an explicit generated_token discriminator;
scratch-buffer positions and hashes never enter their IDs. Nonphysical command-line
spelling and implicit compiler-only aliases still fail closed as unsupported; no
partial catalog/layout is published. Distinct physical definitions never merge
by name. Values outside JavaScript's exact integer range are
rejected, not silently rounded. Request JSON is capped at 64 MiB. This is not
a hostile-source sandbox: run untrusted input inside a disposable process or
worker with time/memory limits. Runtime recovery/cancellation belongs to the
later browser-runtime milestone.

Build
-----
toolchain.lock.json pins LLVM 20.1.8 and Emscripten SDK 6.0.13. Provision
those explicit dependencies first; build.py performs no downloads. Build output,
compiler sources, notices and provenance belong outside docs-ai/ and xnu/.

From the project root:

  python3 docs-ai/tools/layouts/build.py \
    --llvm-archive /path/to/pinned-llvm.tar.gz \
    --emsdk .docs-cache/layouts/emsdk-6 \
    --emsdk-archive /path/to/pinned-emsdk.tar.gz \
    --host-cc clang --host-cxx clang++ --jobs 2

Native frontend and native table generators are built first; the Wasm frontend
then uses those table generators. Both use the same extracted source and wrapper.
Build commands are logged under .docs-cache/layouts/. Each command has a finite
timeout; invoke --phase native or --phase wasm to resume an interrupted build.
No source patches are currently applied. toolchain-provenance.json records pins,
compiler identities, options, tool inputs and artifact hashes. The build cache
is not a security boundary; use a fresh cache when independently reproducing.

Synthetic regression and offline proof
--------------------------------------
  python3 docs-ai/tools/layouts/tests/compare.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/milestone2-synthetic-comparison.json

  python3 docs-ai/tools/layouts/package_proof.py \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --native-report .docs-cache/layouts/milestone2-synthetic-comparison.json \
    --notices .docs-cache/layouts/notices \
    --provenance .docs-cache/layouts/toolchain-provenance.json \
    --output .docs-cache/layouts/proof-synthetic

  node docs-ai/tools/layouts/tests/browser_check.mjs \
    .docs-cache/layouts/proof-synthetic/index.html \
    .docs-cache/layouts/browser-synthetic-comparison.json \
    .docs-cache/layouts/milestone2-synthetic-comparison.json

The test checks independent ARM64 expected sizes, alignments and bit offsets,
then compares the complete native and Wasm protocol results. It tests defined
zero versus undefined macros, nested/multidimensional arrays, anonymous records,
unions, packed/aligned/pragma-packed records, unnamed/zero-width bitfields and a
flexible-array tail. Error cases include partial parse failure, unavailable
headers, host header denial, incomplete/unknown selected types, unsafe JSON
numbers, macro identity collisions and invalid request options. Successful
selected-root closure and unknown-target-feature rejection are included in the
current 13-case suite. Thirty repeated
Wasm requests exercise teardown and detect stale state. Node parity is separate
from the required direct-file browser check.

Open the generated index.html directly through file:// in a fresh browser profile with
networking disabled. It uses classic scripts and embedded Wasm bytes; no fetch,
server, browser cache, installed compiler or remote dependency is required.
The browser_check.mjs command automates this with Chromium; no extra browser
flags are needed. Its real mode requires the independent passing native/Wasm
report and compares the complete actual browser results against that report.
The --harness-smoke option is only for internal automation fixtures and does
not establish compiler parity or pass this milestone.
window.layoutProofMetrics exposes the actual startup, per-request parsing,
linear-memory capacity and parity results for browser automation. A failed
comparison leaves data-result=failed on the document element. The proof contains
native expected outputs and full fixture inputs, not precomputed browser results.
The Wasm frontend runs every fixture in the browser. This minimal proof runs on
the main thread; worker isolation is explicitly a later milestone.

Bundle bytes come from manifest.json, including base64 and all notices. Startup
includes local script loading, Wasm decoding, compilation and instantiation.
Parse time includes request/result serialization and diagnostic formatting.
peak_linear_memory_bytes is Wasm buffer capacity; it is not live heap usage or
browser process RSS. Emscripten memory growth does not shrink that buffer after
freed AST allocations. Browser process peak memory requires separate browser
instrumentation and must be reported with the measurement method/browser version.

A native-only --native run is useful for development but does not pass milestone
one. Final acceptance requires matching pinned source revisions, native/Wasm
and native/browser equality, a fresh offline browser run, and measured artifact
size/startup/parsing/memory. Report the evidence and actual limitations with the
acceptance results.

Reproducible real XNU contexts
-----------------------------
The pinned source is xnu-12377.121.6, commit
ac9718fb1af618d5ce8678d0dc6e8a58f252216f. xnu/ stays read-only.

Configuration generation uses original XNU SETUP/config/doconf and the config
utility built from unchanged local source. Dependencies must already be installed;
none of these tools download or install anything. On Arch Linux, install missing
system dependencies using the normal package manager:

  sudo pacman -S --needed tcsh unifdef bison flex clang

generate_configs.py records installed executable paths, versions and hashes,
source hashes, generation commands and every output hash. It invokes system
tcsh/unifdef, not manually extracted executable packages. It builds only the
configuration utility, never the kernel. From the project root:

  python3 docs-ai/tools/layouts/generate_configs.py

  python3 docs-ai/tools/layouts/bundle_xnu.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine

  python3 docs-ai/tools/layouts/tests/compare_xnu.py \
    --bundles .docs-cache/layouts/xnu-bundles \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/xnu-comparison.json

bundle_xnu.py verifies the configuration generator/source/output hashes and
parses CONFIG_DEFINES back from the actual generated Makefile before using
manifest macros. It verifies the pinned LLVM source manifest for resource
headers. Export aliases come from the original Makefile EXPORT_MI_LIST/DIR
assignments: libsa/string.h at the osfmk component root and sanitizer headers
under san/. The export rule copies original bytes; no types, declarations,
attributes or source headers are invented, stripped or rewritten.

Discovery initially supplies the complete tracked XNU header/include-file
universe and pinned resource headers to the same in-memory frontend. The
reduced bundle retains opened includes and successful probe-only headers.
Records, final macros, include probes, diagnostics and consumed paths must
match between full and reduced input sets. All supplied bytes have SHA256
records. Exact raw files and their original license headers are saved alongside
each request, with source/config/compiler provenance and export mapping.

The supported matrix is profiles/arm64-xnu.json:

Source -mcpu=apple-a14 and -march=armv8.5a+sme2 are expanded by the same pinned
upstream Clang driver, using the isolated virtual filesystem and never executing
driver jobs. Only the resulting CPU and target features feed the frontend.
VMAPPLE selects upstream Darwin's default apple-m1 CPU with the specified
architecture features. Independent driver/preprocessor probes establish exact
feature lists and meaningful builtins such as NEON, AES, atomics and SME2.
These are upstream compiler semantics; no Apple-private feature parity is claimed.
All request macro names and generated option-header macro names are observed,
including undefined values and final definition locations after headers run.

  Context                  recount_track   task     alignment
  RELEASE T8103            64 bytes        1632 B   8 bytes
  DEVELOPMENT T8103        64 bytes        2072 B   8 bytes
  RELEASE VMAPPLE          24 bytes        1632 B   8 bytes
  DEVELOPMENT VMAPPLE      24 bytes        2072 B   8 bytes

Physical T8103 configurations select CPI/energy counters in MASTER; VMAPPLE
does not. DEVELOPMENT adds actual task reference-group and suspend-statistic
fields. Tests assert independent sizes/offsets, record-reference resolution,
effective macros and exact native/Wasm output equality. Accepted generated
contexts must have zero diagnostics, so ignored ABI attributes cannot pass.
The actual header/configuration inputs are complete for this declared matrix;
they are not an exhaustive SDK, arbitrary header environment or kernel build.

Four additional probes are explicitly outside the supported build matrix:
DEBUG=1 supplied on the command line is redefined to 0 by the generated RELEASE
header, with its real warning/definition location exposed; defining
CONFIG_TASK_SUSPEND_STATS as 0 still adds fields under task.h's #ifdef (2016-byte
what-if task); removing a required resource header and selecting an incomplete
task produce diagnostics and no layouts. These probes verify configuration and
failure semantics; they do not advertise additional valid product profiles.

Package and test the independent XNU proof:

  python3 docs-ai/tools/layouts/package_xnu_proof.py \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --native-report .docs-cache/layouts/xnu-comparison.json \
    --bundles .docs-cache/layouts/xnu-bundles \
    --config-root .docs-cache/layouts/xnu-configs \
    --notices .docs-cache/layouts/notices \
    --provenance .docs-cache/layouts/toolchain-provenance.json \
    --output .docs-cache/layouts/proof-xnu

  node docs-ai/tools/layouts/tests/browser_check.mjs \
    .docs-cache/layouts/proof-xnu/index.html \
    .docs-cache/layouts/xnu-browser-comparison.json \
    .docs-cache/layouts/xnu-comparison.json

The XNU proof executes all eight requests and 30 repeats in the browser, displays
actual root structure sizes/field offsets and exposes diagnostics. Compiler
bytes and exact header contents are local. Deduplicated runtime header strings
and raw header downloads retain virtual-path mappings and upstream notices.

Its small layout browser selects a verified profile and root record, filters
field paths, expands embedded records/unions and selects array indices. It shows
a C-style declaration view with hexadecimal size/alignment and root-offset
gutters (+0x...), with local offsets and decimal values in field details, keeps
pointers terminal and links exact source-header downloads. The object-like
#define/#undef editor runs the actual local Wasm compiler; manual analyses are
labeled what-if, not native-validated profiles. Requested directives, effective
tokens, definition locations and frontend options stay inspectable. Editing or
failing a request clears stale layouts; Reset restores the verified profile.
The Chromium harness additionally checks manual configuration changes, nested
offsets, array bounds, filtering, invalid directives and compiler errors/reset.

These are ordinary ARM64 GNU C header-analysis contexts using exact XNU source
configurations. They do not establish an identified shipped kernel's ABI.
Arm64e pointer authentication, Apple bounds-safety compiler modes, C++ layouts,
SPTM profiles and other releases remain unvalidated. Source-supported compiler
feature fallbacks are used without overriding feature tests or attributes.
Current effective __has_ptrcheck is 0; BOUND_CHECKS and __arm64e__ are undefined.
The source/configuration snapshot, target, CPU/features, language and options
travel with every result. Worker runtime, cancellation and handbook integration
remain later milestones. Dependency discovery is described separately below.

Versioned consumable contracts
-----------------------------
The compiler transport is schema 2. Historical milestone 1/2 schema 1 evidence
and its archived binaries remain readable as historical artifacts. The current
contract API rejects schema 1 rather than inventing absent source identities.
No historical evidence is silently upgraded.

browser/contracts.js is the shared classic-script/CommonJS implementation. It
creates and validates platydoc.layout-set version 1 documents, containing
version 1 declarations, configuration, layouts and diagnostics, plus the
dependencies version1 relation schema or version2 shared-analysis reference.
Node tooling and the file:// browser use the same code. canonical() sorts object
keys by JavaScript string order, preserves ordered arrays, emits compact JSON and
rejects undefined/sparse values, floating point and unsafe integers. All sizes,
counts and offsets are exact nonnegative integers at most 2^53-1. Record size/alignment
use explicit byte keys; type size/alignment, field/path offsets and bitfield
widths use bit keys.
Source offsets are UTF-8 byte offsets. IDs hash canonical JSON except source IDs,
whose explicit source-key encoding is independently recomputed by the validator.

The public API is create(), validate(), canonical(), createPolicy(),
resolveConfiguration(), resolvePath(), mergePresence() and mapChapters().
Creation/validation/hash functions are asynchronous; layout navigation and
configuration resolution are synchronous. tests/contracts_cli.cjs provides
bounded JSON create/validate/map commands for Python tooling. The package emits
contracts.json and chapter-bindings.json; window.layoutContractSets contains
contracts made from actual browser Wasm results, validated and compared with the
packaged native expectations before layouts publish. Current manual results also
expose their contract through window.layoutCustomResult.contract.

A declaration entry stores immutable identity/source/scope metadata; a distinct
variant binds its type/completeness to a configuration ID. Alias declarations
have separate identities and typed underlying relations, preserving pointer and
array boundaries and alias chains. Fields have owner IDs. Layout entries bind
record/field IDs, present fields, exact sizes, alignment, bit offsets and types
to one configuration. The validator checks IDs, hashes, units, references,
owner relations, numeric bounds, embedded cycles and type/array storage sizes.
Attributed typedef alignment is preserved even when it differs from the base
record or array-element alignment. Type bound_kind distinguishes constant and
incomplete arrays; the transport flexible flag describes an incomplete bound,
while field flexible_tail explicitly marks a trailing storage member.

mergePresence() compares observed fields only after their owning source-defined
record was successfully laid out in the same identity domain: present/absent
are then meaningful. Failed, unselected, incomplete or differently defined
owners remain unknown. It rejects conflicting immutable metadata for one ID.
These presence contracts do not invent inactive AST declarations. The separate
dependency analyzer below indexes inactive source regions.
Source-identical struct/union kind variants are a current merge boundary:
individual layouts remain valid, but conflicting immutable kind metadata makes
mergePresence fail closed instead of combining them.

A configuration binds every supplied header hash/byte count/physical mapping,
ordered include/forced-include inputs, macro directives, language, kernel mode,
target CPU/architecture/overrides, expanded driver features, frontend options,
compiler revision/version and wrapper-source hash. Requested macros distinguish
undefined, defined-empty and defined-zero. Effective observed replacement tokens
and definition locations are separate; a missing observation means unknown,
not undefined. The inline hash-bound policy stores baseline context, editable
names, derived names, compiler-reserved prefixes and allowed-value constraints.
Policy baselines and resolved values are validated. Protected or derived edits
require explicit what-if analysis and cannot become validated profiles. Explicit
what-if reserved-macro directives remain possible; defining a feature macro does
not change the separately recorded compiler CPU/features. The macro editor cannot
change compiler/source context through its policy.

Normalized statuses are success, invalid-configuration, compilation-error,
incomplete-type and unsupported. Every failure has diagnostics and zero trusted
layouts/declarations. Early malformed requests retain honest partial/null
compiler context. Warnings remain visible; the four supported real contexts must
still have zero diagnostics independently of schema validation.

The dependency schema defines macro/declaration origins, target declarations,
relationship kinds, source/comparison evidence, configuration references and
coverage states. Status/coverage pairs are exactly not-computed/unknown,
partial/partial and complete/declared-complete. The real milestone 3 outputs say
not-computed/unknown with no
relations. A manually constructed schema fixture validates potential dependency
evidence; this version1 relation fixture is distinct from the version2 shared-analysis
reference described below.

resolvePath() accepts declaration IDs (or unambiguous local field names), then
array {index} steps. It adds bit offsets through embedded storage; union members
share the same base. It never follows a pointer into another object. Fixed arrays
are bounds checked. Flexible indices require supplied runtime lengths or an
explicit runtime-unchecked preview; no allocation length is inferred. Returned
root/local bit offsets, pointer boundary, union path and bounds status are
explicit. The existing C-style browser uses this resolver without visual changes.

Authored docs-ai/structures/layouts.json maps physical source/hash/byte anchors
to real handbook chapters. Package generation checks current header bytes and
actual heading anchors, then the shared mapper binds declaration IDs. It does
not rebuild the handbook or add a new chapter.

Run the integrated contract checks (native/Wasm equality includes the identity,
alias, anonymous, scoped, Unicode, macro/include and failure fixtures):

  python3 docs-ai/tools/layouts/tests/compare_contracts.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --bundles .docs-cache/layouts/xnu-bundles \
    --output .docs-cache/layouts/milestone3-contracts.json

Configuration dependencies (analysis schema 1, document reference schema 2)
-----------------------------------------------------------------------
trace_dependencies:true adds compiler-dependency-evidence version1 to the
compiler transport. dependency_files optionally limits macro-expansion capture
to supplied virtual files; bundle_xnu derives this set from selected declaration
anchors and their include chains. Conditions, definitions and helper expression
sources remain in the selected source/macro-origin closure. The trace records
its filtering rule, original/retained event counts and a 40000-event ceiling.
Truncation is explicit; omitted observations remain unknown. PP sequence numbers
remain original, potentially sparse, and are not array indices.

Clang PPCallbacks record event-time macro definitions/replacements, conditional
evaluations, expansions, skipped ranges, pragmas and include occurrence context.
Final effective macro values remain separate. AST evidence records field/alias
relationships, array bounds, bit widths, explicit alignment, enum expressions
and implicit predecessor values. Unary sizeof/_Alignof record operands can
supply type-query edges; arbitrary non-value type-expression discovery remains
partial. All source intervals are half-open UTF-8 byte ranges. Spelling and
expansion ranges are distinct, and raw inactive branches are source regions,
not invented declaration IDs.

browser/dependencies.js is the shared classic-script/CommonJS analyzer. It
indexes continued/CRLF directives while masking comments and literals, preserves
physical UTF-8 offsets, indexes inactive branches and replacement definitions,
and joins them with the compiler's observed events and typed storage edges.
Macro replacement origins use event-time definitions, including later undef or
redefinition. Compiler queries such as __has_feature(ptrauth_calls) and
__has_include("header") are query evidence; their argument tokens are not
editable macro names. Structurally recognized include guards are preconditions,
not ordinary layout controls. Pointer referents do not propagate storage
influence. Embedded records, arrays and typedefs do; pointer-to-array bounds
retain non-storage evidence. Only a path applicable within one observed
configuration establishes a control; edges from incompatible configurations
cannot be joined into an apparently observed path.

Packing evidence models the simple unnamed push/pop/numeric stack. Named or
combined pop syntax is explicitly marked unsupported and does not claim an
exact active packing state. Other extraction limits are listed in each
analysis's partial coverage. Source and graph pruning retain reverse-reachable
layout evidence, with omitted node/edge counts. This is not exhaustive C
preprocessor evaluation or a claim of all possible XNU build variants.

API:
  analysis = await LayoutDependencies.discover(entries, {space_id});
  // entries: {name,request,result,document}; all bytes/context are verified.
  await LayoutDependencies.validate(analysis, documents);
  await LayoutContracts.registerDependencyAnalysis(analysis);
  document = await LayoutDependencies.attach(document, analysis);
  controls = LayoutDependencies.controlsFor(analysis, declaration_id);

One shared platydoc.dependency-analysis document contains source hashes/origins,
source regions, typed graph edges, event-time observations, reason paths,
controlled comparisons, finite-space enumeration and partial discovery coverage.
Each attached layout-set keeps a small dependencies version2 reference with the
analysis ID, its configuration ID and roots. Validation requires the referenced
registered/provided analysis and binds the complete original base contract.
Existing dependencies version1 documents remain readable. The CLI bridge's
'discover' command accepts entries with the same create metadata and returns
{analysis,documents}; 'validate' and 'map' accept the separate analysis object.

A single-macro intervention requires identical supplied bytes and other compiler
context, while preserving missing directive versus explicit #undef. Joint profile
differences are never attributed to one flag: RELEASE/DEVELOPMENT and board
profiles change multiple inputs/options. Observed components separately cover
record size/alignment and field presence/type/offset/bit width. Equal-width alias
changes can change field type without changing bytes. Potential controls can
have controlled no-change observations; an untested branch is unknown, and a
failed configuration supplies no layouts. Interacting flags are evidenced by
comparisons in their actual other-flag context, not independent-effect claims.

Finite synthetic discovery regression:
  python3 docs-ai/tools/layouts/tests/compare_dependencies.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/milestone4-dependencies.json

Real 13-case dependency matrix (four profiles plus nine diagnostic/what-if cases):
  python3 docs-ai/tools/layouts/tests/compare_xnu.py --dependencies \
    --bundles .docs-cache/layouts/xnu-bundles \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/milestone4-xnu-comparison.json

Pass that report to the existing package_xnu_proof.py --native-report option;
the packager selects dependency mode automatically and emits dependencies.json
once. The file:// browser independently recomputes window.layoutDependencyAnalysis
from actual Wasm results, validates/references it in window.layoutContractSets,
and exposes potential/demonstrated controls with source reason paths in the
existing layout details. Manual edits remain explicit what-if analyses and have
a separate window.layoutCustomDependencyAnalysis. No worker or handbook build
is involved. Full result text is materialized only when its details are opened.

Offline worker runtime (manifest/protocol version 1)
--------------------------------------------------
The separate milestone 5 runtime proof uses layout-runtime.js, layout-worker.js,
layout-codec.js and proof_runtime.js. It does not load the 13-case native golden
matrix or run it during normal startup. The accepted milestone 4 artifact and
proof_xnu.js remain separate. The compiler binary is unchanged.

The main page loads local classic scripts. Asset scripts register deterministic
schema2 gzip-base64 envelopes through LayoutRuntimeAssets.deliver(id,envelope).
The runtime checks the manifest's exact decompressed SHA256 and byte size before
using any compiler, script or profile asset. layout-codec.js reuses the book's
GPL-2.0-only gzip/DEFLATE fallback and verifies CRC/size; the native streaming
DecompressionStream path checks its byte ceiling while reading and verifies the
same SHA/length. No fetch, module imports, CDN, server, cross-origin isolation
headers, persistent storage or installed browser-side compiler is required.

The compiler factory, shared contracts/dependency code and worker code form one
classic Blob worker. Wasm bytes are transferred once to that worker; the asset
cache never retains a detached transferred buffer. Blob URLs, script elements,
listeners and timers are cleaned up on readiness, failure, cancellation and
shutdown. Only the selected profile's complete header bundle is loaded lazily.
Source downloads use exact bytes from the current request on demand.

The worker owns all synchronous Clang calls, contract creation and dependency
analysis. It returns the compact compiler result without dependency_trace, its
normalized contract and separate shared analysis. Temporary trace data stays in
the worker's bounded cache/analysis lifetime. The main page validates reply
bindings and re-creates the contract as a trust check before rendering; the
C-style view uses the existing shared offset resolver. No global analysis
registry accumulates manual reports. Macro overrides remain explicit what-if
analyses, compared only with the selected baseline.

LayoutRuntime.Client(manifest,options) exposes analyze(profile,{overrides,
dependencies,timeout_ms}), cancel() and dispose(). analyze allocates its request
ID synchronously and snapshots directives before loading/hashing. A new request
supersedes an active request. Cancellation, a startup/request deadline, worker
failure or invalid reply terminates the worker, including synchronous Wasm;
the next request constructs a fresh worker. Generation and worker-instance
checks suppress callbacks from old loaders/workers and late async validation.
Every request promise settles once. A 'compiling' progress event is posted just
before entering the synchronous compiler, allowing cancellation tests to target
actual compiler work. This is a dedicated worker, not an interruptible compiler.

The cache key binds runtime/compiler/worker/contract/dependency asset identities,
the complete baseline request bytes/options/physical-source mappings, selected
profile/source metadata, overrides and analysis mode. Dependency inference never
narrows this key. An identical manual request reached from a different baseline
cannot reuse the former baseline's policy/comparison. Cache hits validate the
stored contract/report; main replies also bind the current verified profile and
requested directives. Invalid or stale values cannot become visible layouts.

Defaults: three worker cache entries with 64 MiB of serialized JSON accounting,
16 MiB of decoded main-thread assets, and a 256 MiB Wasm capacity retirement
threshold. Entries larger than the budget are not cached. LRU eviction bounds
retained entries/serialized bytes; it is not an exact JavaScript heap bound.
The Wasm threshold is a post-request retirement rule, not a hard peak-memory
limit: the worker may grow beyond it while analyzing, returns the result, and
is then discarded. A warm worker is reused until failure/cancellation/retirement.
Persistence is deliberately disabled; correctness and recovery do not depend on
IndexedDB/localStorage availability, cache restoration or browser cache state.

The lightweight proof exposes window.layoutRuntimeClient,
window.layoutRuntimeState and window.layoutRuntimeCurrent. The current value
contains {id,generation,profile,request,result,contract,analysis,metrics}; it is
cleared as soon as inputs change or analysis is cancelled. Client metrics count
worker starts/terminations, stale messages and cache hits; response metrics
report compiler calls, serialized cache bytes and Wasm buffer capacity. These
are separate from browser process RSS and live allocation measurements.

Focused bounded tests:
  python3 docs-ai/tools/layouts/tests/compare_runtime.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --output .docs-cache/layouts/milestone5-runtime-tests.json

The worker test consumes entries from the dependency fixtures and uses a
native-evidence compiler adapter with the real shared contracts/dependency code;
it verifies cache identity/eviction and allocation cleanup, not browser compiler
parity. A fresh offline file:// Chromium check against real native expectations
is required separately for runtime acceptance. No handbook HTML build is used.

Package and verify the separate real worker proof (compiler artifacts are reused):
  python3 docs-ai/tools/layouts/package_runtime_proof.py \
    --wasm .docs-cache/layouts/build-wasm/bin/layout-engine.js \
    --native-report .docs-cache/layouts/milestone4-xnu-comparison.json \
    --bundles .docs-cache/layouts/xnu-bundles \
    --config-root .docs-cache/layouts/xnu-configs \
    --notices .docs-cache/layouts/notices \
    --provenance .docs-cache/layouts/toolchain-provenance.json \
    --output .docs-cache/layouts/proof-runtime

  node docs-ai/tools/layouts/tests/browser_runtime_check.mjs \
    .docs-cache/layouts/proof-runtime/index.html \
    .docs-cache/layouts/milestone5-browser-runtime.json \
    .docs-cache/layouts/milestone4-xnu-comparison.json

  node docs-ai/tools/layouts/tests/browser_runtime_check.mjs \
    .docs-cache/layouts/proof-runtime/index.html \
    .docs-cache/layouts/milestone5-browser-runtime-fallback.json \
    .docs-cache/layouts/milestone4-xnu-comparison.json --fallback

The browser checks use fresh offline Chromium profiles. --fallback disables
DecompressionStream to exercise the bundled gzip decoder. --smoke is only a
short development check; full acceptance uses the commands above. Runtime
provenance binds the new JS/package helpers separately from the unchanged
compiler provenance; no LLVM rebuild is required for JavaScript-only changes.

Live structure explorer (milestone 6)
------------------------------------
layouts.html/css/js preserve the approved handbook-style design while using the
same offline LayoutRuntime worker. This is a dedicated standalone explorer;
book generation/integration is a separate milestone. The recorded mockup and
accepted runtime proof remain separate artifacts. No compiler changes are needed.

Structure and field search, profile selection, CPI/energy shortcuts, relevant
macro controls and raw object-like directives all use complete runtime requests.
Manual edits are what-if analyses. Requested and effective macro definitions,
actual compiler/target settings and partial dependency evidence are inspectable.
Custom non-boolean effective replacements are shown as indeterminate switches,
not guessed true/false values. Upstream Clang features do not establish support
for Apple-private features or an identified shipping-kernel ABI.

explorer-model.js uses LayoutContracts.resolvePath for field/array arithmetic.
It distinguishes immediate-parent and object-root offsets, union overlap,
zero-width/unnamed bitfields, embedded records and pointer boundaries. Padding
unions occupied bit intervals per record; it does not add overlapping union
alternatives or invent flexible-tail storage. Padding stops at the flexible-tail
offset because tail elements can overlap the fixed sizeof area. Flexible array
indices require a supplied runtime length or an explicit unchecked preview;
zero-length arrays have no element offsets. A pointer may open a new root only
when its complete referent layout is already available in the returned context.
The new object starts at zero; unavailable referents remain explicit boundaries.

Comparison defaults to the selected live profile baseline. A pinned successful
result can instead serve as the comparison while changing flags/profiles. At
most the current result, current profile baseline and one pinned result are
retained. Added/removed source fields, changed types/widths, local offsets and
root-relative shifts (including changed array stride) are distinguished. A
removed field has no current offsets or size. Absence requires successful
coverage of the same owning source definition; different/unselected/error
contexts remain unknown. Never-observed inactive source regions do not acquire
invented field IDs. Evidence paths are source dependencies, not a conjunction
of conditions asserted currently true.

The bounded version1 URL fragment records the source root, selected source-ID
field steps, array indices/lengths, profile, exact overrides, number format,
search and expansion state. Restoration validates selectors/bounds after live
results arrive, including collapsed arrays. Unknown IDs, malformed keys and
out-of-range indices fail visibly without retaining old geometry. Root-only
selections are valid bookmarks. Semantic navigation supports Back/Forward.
Pinned comparisons are session-local and are not serialized in the URL. A
selection known only from a pinned result may be unavailable after reopening;
restoration reports that boundary rather than inventing a current layout.
Reset clears invalid view state and restores a usable profile/root. Returning
from a source page via the browser cache reloads the same bookmark to recreate
the disposed worker. Every asynchronous pipeline phase checks its UI generation
before launching manual work or publishing results. Loading, edits, cancellation
and errors clear visible geometry immediately.

Source links use exact-byte-verified existing handbook wrappers when the package
can resolve them. Otherwise Download exact source creates a local Blob from the
current request, with no server or fabricated line viewer. All assets are local;
persistent storage is not required. Keyboard buttons, field-row arrow navigation,
slash-to-search, accessible status/diagnostics and narrow-screen navigation are
included. Worker memory/cache/cancellation semantics remain as documented above.

Focused model checks use actual native-generated synthetic geometry:
  python3 docs-ai/tools/layouts/tests/compare_explorer.py \
    --native .docs-cache/layouts/build-native/bin/layout-engine \
    --output .docs-cache/layouts/milestone6-model-tests.json

After generating the accepted runtime package, create the standalone explorer:
  python3 docs-ai/tools/layouts/package_explorer.py \
    --runtime .docs-cache/layouts/proof-runtime \
    --book docs-ai-html \
    --output .docs-cache/layouts/explorer

Open .docs-cache/layouts/explorer/index.html directly through file://. The
packager reuses verified runtime assets and copies the handbook CSS; it does
not rebuild the handbook. A fresh offline browser run with real native
expectations remains required for acceptance.

Full fresh-profile offline explorer checks (normal and gzip fallback):
  node docs-ai/tools/layouts/tests/browser_explorer_check.mjs \
    .docs-cache/layouts/explorer/index.html \
    .docs-cache/layouts/milestone6-browser.json \
    .docs-cache/layouts/milestone4-xnu-comparison.json

  node docs-ai/tools/layouts/tests/browser_explorer_check.mjs \
    .docs-cache/layouts/explorer/index.html \
    .docs-cache/layouts/milestone6-browser-fallback.json \
    .docs-cache/layouts/milestone4-xnu-comparison.json --fallback

The --smoke mode is only an early integration check. Full checks exercise the
live compiler, controls, nested arithmetic, comparisons, source downloads,
URL restoration, errors/cancellation and responsive presentation. Screenshots
are captured alongside their reports; no handbook rebuild is performed.

Handbook generation and offline packaging (milestone 7)
-----------------------------------------------------
Ordinary make_docs.py builds include the live explorer in the authored
structures/layout-browser.md guide. Its unique structure-layout-explorer div
is replaced inside the native book shell; navigation, global search, theme,
source dialogs, footer and offline-download controls remain the book's own.
The approved standalone explorer and historical proof packages stay separate.

The historical milestone-7 provisioned inputs were:
  --layout-runtime .docs-cache/layouts/proof-runtime
  --layout-native .docs-cache/layouts/build-native/bin/layout-engine
  --layout-configs .docs-cache/layouts/xnu-configs
They came from the explicit compiler/configuration/bundle/runtime workflows
above; current iOS defaults are listed in the milestone-8 section. A normal book build never downloads dependencies, builds LLVM, installs
tools or silently omits the explorer. Missing or stale inputs stop the build
before rendering. Paths can change; their content must match artifact.lock.json.

The lock binds native/Wasm/factory/compiler identity, the accepted runtime
manifest and package, generated configuration provenance and the full selected
XNU file inventory. Inventory identity includes paths and exact bytes of all
6113 regular source files, including ignored/untracked additions; only .git
metadata is excluded. Symlinks are rejected. The existing tracked header
discovery universe and exact supplied Clang resource bytes are also checked.
New include candidates therefore invalidate reduced header bundles rather than
silently changing __has_include or include-shadowing behavior.

catalog.py validates the configuration generator and its source inputs, every
generated profile file, current profile/export rules, compiler build inputs and
runtime helpers. Changed source/compiler/configuration inputs require explicitly
regenerating and reviewing the affected upstream workflow, native/Wasm parity
evidence and artifact lock; editing a cached result cannot refresh provenance.
Do not update the lock merely to suppress a mismatch.

The generated layouts/ directory includes:
  catalog.json/catalog.js: searchable source-ID declarations, field names,
    supported profiles and explicit authored selection keys;
  assets/: lazy full exact-byte header/resource/configuration requests and the
    compressed local compiler/worker assets, preserving their pinned manifest;
  headers.json: every profile's supplied paths, original paths, lengths and SHA;
  common-profiles/: successful native-generated normalized contracts and
    compiler responses, with full request/compiler/source/tool cache identities;
  chapter-bindings.json/layout-chapters.json: shared-contract source-anchor
    bindings to actual chapter headings, checked without name-only fallback;
  generation-provenance.json/source-inventory.json/artifact.lock.json and
    original compiler/runtime/configuration provenance and all license notices.

The common-profile cache is used for catalog and binding generation only.
It does not prewarm the browser worker or replace live baseline/override
analysis. Cache hits verify checksums, exact context/schema/compiler identity
and reconstructed shared contracts; malformed entries are rebuilt. The cache
key changes with source, compiler, configuration, request, mapping or consumed
generation/helper code. Build/check verifies the distributed assets independently
of the original native executable and working cache.

Authored links use ordinary Markdown queries, for example
layout-browser.md?declaration=task. Only explicit layouts.json binding keys are
accepted (the expanded finite survey also retains known unavailable keys and
their diagnostics). The integrated explorer resolves the selected context's physical
source ID; unknown/duplicate keys show an error with no old geometry. A valid
#layout bookmark takes precedence over the initial query. Native global slash
search remains the handbook shortcut. Existing source wrappers are linked only
when their original header and payload hashes match; exact-source downloads
remain available when no wrapper exists.

The existing offline ZIP includes all layouts/ assets and notices automatically.
The layout manifest seals data/assets, while the book verifier and ZIP verifier
own HTML and its offline-download rewrites. Extracted ZIPs can therefore be
checked without special hash exceptions for mutated HTML.

Focused checks:
  python3 -B docs-ai/tools/layouts/tests/catalog.test.py -v
  node docs-ai/tools/layouts/tests/book-layouts.test.cjs
  python3 -B -m unittest discover -s docs-ai/tools/book/tests -v
  node docs-ai/tools/book/tests/assets.test.mjs

Build a separate handbook without replacing an existing book:
  python3 make_docs.py --output .private/milestone7-book --cache .docs-cache
  python3 make_docs.py --output .private/milestone7-book --check
Output and cache must remain separate dedicated directories. The book's normal
source/link/license/diagram/ZIP checks and actual fresh offline browser acceptance
still apply; these focused checks do not replace end-to-end validation.

Integrated fresh-profile browser checks:
  node docs-ai/tools/layouts/tests/browser_book_check.mjs \
    .private/milestone7-book .docs-cache/layouts/milestone7-browser.json \
    .docs-cache/layouts/milestone4-xnu-comparison.json
Repeat with --fallback for the local gzip decoder. After extracting the normal
xnu-source-handbook.zip, pass its extracted xnu-source-handbook directory and
--extracted to check the distributed copy. --https-project-path serves only the
local package under a nested HTTPS project path for URL-resolution acceptance;
it is a test route, not a reader hosting requirement.

Documented C structure survey and maintenance (milestone 8 and expansions)
--------------------------------------------------------
profiles/structure-catalog.json is an authored finite inventory of primary C
objects and direct companions explained by the existing chapters. It is not
an exhaustive list of every type mentioned in prose or returned by Clang.
Each entry binds physical header bytes, a declaration-token byte anchor and
real chapter headings. A same-name declaration elsewhere cannot replace it.

The new source profiles are generated for iPhoneOS, with XNU_TARGET_OS_IOS=1
and XNU_TARGET_OS_OSX undefined. Defined zero is not equivalent to undefined
for source #ifdef branches. profiles/ios-catalog.json records component flags,
board CPU/architecture selection, original export rules and all deliberately
excluded build details. arm64e-apple-ios with both real pointer-authentication
feature switches enabled is required for every advertised supported iOS
context. No SDK or deployment version is fabricated. Upstream compiler feature
support and XNU's compatibility macros are distinct from Apple-private compiler
behavior; diagnostics or missing compiler capabilities remain explicit
boundaries, never a reason to skip fields or rewrite original headers.

The authorized layout-only compatibility directive is exactly
  #define __ptrauth(...)
at the beginning of the supplied analysis-entry source. This empty variadic
function macro removes qualifier annotations that LLVM20 cannot parse; it does
not replace __has_feature, disable either real PAC feature switch or remove
PAC-conditioned fields. The exact directive is visible in configuration
details, the effective function macro and its source location are observed,
and its bytes are bound into request/policy/provenance identity. A command-line
#undef cannot remove this later source definition. It does not implement pointer
signing or validate executable pointer-authentication behavior. Independent
compiler geometry and explicit PAC-field preservation checks remain required.
The shared runtime rejects attempts to disable __arm64e__ in this mandatory PAC
lane before compilation. The lane is bound by the catalog analysis-entry source
identity and required feature observations, including its persisted baseline
policy; generic arm64e API inputs do not require these project-specific probes.
Successful imported/cached contracts must retain the
effective architecture/feature probes and actual compiler switches; baseline
source-defined PAC capabilities remain required where observed. Other manual
macros retain their explicit what-if behavior. This guards layout publication,
not the generic engine's ability to analyze deliberately different inputs.

The survey separates kernel, thread, VM, BSD, uthread, credentials, file objects,
security labels, IPC, socket-buffer, mbuf-companion and IPv6 wire/options/
address/neighbor/multicast header contexts. BSD's component defines differ from osfmk's. It evaluates each
inventoried root independently before merging compatible successful roots into
a lazy family context. Complete field/type/layout semantics must match the
individual translation unit; effective macro differences are retained in the
context manifest. Export aliases copy exact source bytes using the literal
Makefile rules. Unsupported assignment/conditional syntax stops generation
instead of approximating make execution.

Reproduce in dedicated caches, preserving historical packages:
  python3 docs-ai/tools/layouts/generate_configs.py --platform iPhoneOS \
    --output .docs-cache/layouts/milestone8-configs
  python3 docs-ai/tools/layouts/generate_sysproto.py
  python3 docs-ai/tools/layouts/generate_mig.py
  python3 docs-ai/tools/layouts/survey_catalog.py \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --config-root .docs-cache/layouts/milestone8-configs \
    --output .docs-cache/layouts/structure-bundles
  python3 docs-ai/tools/layouts/tests/compare_catalog.py \
    --bundles .docs-cache/layouts/structure-bundles \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/milestone8-compiler/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/structure-comparison.json

The config helper requires installed tcsh, unifdef, clang, bison and flex.
On Arch Linux install missing tools through pacman; these scripts never
download or execute an extracted package. Compiler provisioning remains the
separate pinned build workflow. A survey with genuine unsupported compiler
features records failures; it does not authorize a compatibility definition.

generate_sysproto.py uses XNU's unmodified syscall generator with explicit
SEED_DEFINES (empty by default). generate_mig.py builds the pinned Linux-compatible
Apple MIG source using installed autoconf/automake, gcc, make, flex and bison,
then generates four Mach headers from this XNU checkout for each base profile.
It requires the source archive already present at
.docs-cache/layouts/mig-tools/port.tar.gz; it performs no download. The exact
archive URL, revision and SHA-256 are pinned in generate_mig.py. Generated
headers, source hashes and actual commands accompany the prepared runtime;
neither browser readers nor GitHub Actions run these generators.

For incremental preparation, pass --reuse-report PATH to compare_catalog.py
with a previous passing comparison. It reuses results only when all compiler
artifact hashes and the complete request match, verifies the stored result and
trace hashes, and checks them against the new survey. Changed contexts run
normally. Reused case timings describe their original run.

coverage.json contains every root x declared base-profile cell, with distinct
supported, unavailable, compilation-error, unsupported and invalid-configuration
states. Failed/incomplete/identity-unsupported requests advertise no layout.
Warning-only compiler evidence is retained but not admitted as a supported
zero-diagnostic profile. Every cell retains exact status, diagnostics and
request/result hashes. Successful cells bind the family context and actual
source declaration ID. Reduced header closures must reproduce the entire
full-universe result, including include probes; file additions invalidate the
full source snapshot rather than silently changing __has_include behavior.

compare_catalog.py checks the complete native/Wasm response before storing a
compact result with only dependency_trace removed. Exact traces remain as
separately hashed gzip files, preventing one huge JSON report. The runtime
package retains the finite coverage, authored inventory/profile specification,
compact comparison and per-cell semantic evidence. Offline book verification
rechecks geometry digests, source candidates, all supported/boundary/probe case
membership, context/header identities and the independent compiler evidence.
The generated guide renders the finite matrix; a known unavailable declaration
shows its retained boundary without starting a compiler or inventing offsets.

Native/Wasm renderer geometry regression, including packed bitfields, anonymous
unions, aligned array stride, zero arrays and flexible tails inside fixed sizeof:
  python3 docs-ai/tools/layouts/tests/compare_explorer.py \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/milestone8-compiler/build-wasm/bin/layout-engine.js \
    --output .docs-cache/layouts/milestone8-model-tests.json
  python3 docs-ai/tools/layouts/tests/coverage.test.py
  python3 docs-ai/tools/layouts/tests/compare_pac_guard.py \
    --bundles .docs-cache/layouts/structure-bundles \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --output .docs-cache/layouts/milestone8-pac-guard.json

Package the reviewed expanded runtime without replacing the historical proof:
  python3 docs-ai/tools/layouts/package_catalog_runtime.py \
    --native .docs-cache/layouts/milestone8-compiler/build-native/bin/layout-engine \
    --wasm .docs-cache/layouts/milestone8-compiler/build-wasm/bin/layout-engine.js \
    --native-report .docs-cache/layouts/structure-comparison.json \
    --bundles .docs-cache/layouts/structure-bundles \
    --config-root .docs-cache/layouts/milestone8-configs \
    --notices .docs-cache/layouts/milestone8-compiler/notices \
    --provenance .docs-cache/layouts/milestone8-compiler/toolchain-provenance.json \
    --output .docs-cache/layouts/structure-runtime

Current normal-book defaults are --layout-runtime pointing to that new runtime,
--layout-native pointing to milestone8-compiler/build-native/bin/layout-engine,
and --layout-configs pointing to milestone8-configs. The reviewed separate
artifact-ios.lock.json binds these artifacts. A stale or missing pin/input fails
closed; normal generation does not provision it. The family include sets
remain separate because mixing task/thread and unrelated BSD headers can change
source-bound forward-declaration identities even when byte sizes match.

The inventory contains 66 roots with supported layouts in all four base
profiles (264 successful cells). The 88
runtime contexts include ARM64 machine/saved state,
IPv6 address and wire headers, packet options, fragment queues, routes, neighbor
discovery and multicast. Token-pasted aliases retain physical macro provenance,
enabling proc, ipc_space, ipc_port, fileproc, vnode, socket, inpcb, tcpcb, mbuf and
in6_ifaddr. thread_group uses its complete original C source, explicitly listed
in source_files; include_diagnostics narrowly suppresses its -Wstatic-in-inline
warnings without altering declarations. ucred_rw includes original kern_credential.c
with genuine sysproto.h and approved include-local allocator metadata placeholders
(__builtin_xnu_type_summary becomes 0, __builtin_xnu_type_signature becomes an empty
string). Directives shows their exact scope and layout-only meaning. vnode_pager
includes original bsd_vm.c with genuine per-profile MIG headers. ubc_info and
cs_blob share a dedicated context with unchanged original headers, older
Apple-published TrustCache dependencies and independently authored layout-only
CoreEntitlements declarations. No original KDK headers are packaged. ubc_inputs.py
pins the public provider source/hash/license and compatibility inputs. The context
requires both original roots and rejects exposed placeholder-dependent types;
CoreEntitlements and unrelated pmap metadata layouts are not supported. Directives
shows the exact compatibility declarations. Changing placeholder storage from
1 byte to 1024 bytes aligned to 64 bytes left every returned record and declaration
identical in the focused independence probe.

Local UBC preparation reads the five unmodified TrustCache headers, APPLE_LICENSE
and source.json from .docs-cache/layouts/trustcache-source. The provider is Apple's
xnu-8796.101.5 release, commit aca3beaa3dfbd42498b42c5e5ce20a938e6554e5,
EXTERNAL_HEADERS/TrustCache; source.json records individual file hashes and the
profile pins that manifest. A prepared runtime preserves those exact inputs and
notices. The CE compatibility headers are authored under compatibility/ and need
no SDK or KDK. No KDK archive or extracted KDK content is used in preparation or
publication. Macro type-query expressions (sizeof/alignof/typeof/offsetof) are rejected in
this context so custom flags cannot use placeholder storage indirectly.

Generate and verify a separate book, then exercise the current bindings:
  python3 make_docs.py --output .private/structure-expansion-book --cache .docs-cache
  python3 make_docs.py --output .private/structure-expansion-book --check
  node docs-ai/tools/layouts/tests/browser_expansion_check.mjs \
    .private/structure-expansion-book .docs-cache/layouts/structure-browser.json \
    .docs-cache/layouts/structure-comparison.json
Repeat with a separate output report and --https-project-path. This portable
mode exercises every current runtime context and requires no private archives.
For the original expansion audit, all three optional arguments can bind the
retained M8 evidence: --baseline-book .private/milestone8-book,
--baseline-native .docs-cache/layouts/milestone8-comparison.json and
--baseline-browser .docs-cache/layouts/milestone8-browser.json. That archived
mode requires the exact accepted historical proof, verifies preservation of
earlier layouts and exercises new/changed bindings. The historical
browser_validation_check.mjs proof retains its file/ZIP/fallback/HTTPS reader
and failure-recovery evidence. Both modes check actual chapter links and new
unavailable selections. Independently verify the new offline ZIP members and
layout assets. These test servers are not required by an offline reader.

When changing a release/profile, update the authored inventory only after
reading its new declarations and chapters; regenerate upstream configuration
headers, survey all cells, review exact unsupported diagnostics, independently
check representative geometry and run native/Wasm parity. Then package the
new runtime, review its separate artifact-ios.lock.json pin and regenerate the
book. The M7 artifact.lock.json and accepted historical proof bytes remain
separate. Cache checksums and changed pins do not substitute for this review.
