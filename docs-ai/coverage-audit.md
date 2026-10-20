# Complete documentation coverage audit

The [first-release expansion record](audits/first-release-expansion.md) tracks the initial 30 companions across nine requested areas and the [audit-priority follow-up](audits/first-release-expansion.md#10-audit-priority-follow-up): Skywalk control/readiness, VM copy/remap, clocks/accounting, descriptor lifetime, task/thread capabilities and suspension. It preserves this audit's historical baseline and remaining backlog. New work excludes x86 and KDP.

The [netif, flow lookup, authorization and ARM64 memory batch](audits/first-release-expansion.md#11-netif-flow-lookup-authorization-and-arm64-memory) adds seven companions with separate state/lifetime explanations. The [packet transformations, filtering, IPC and logging batch](audits/first-release-expansion.md#12-packet-transformations-filtering-ipc-internals-and-logging) follows those gaps with six companions and an in-place namespace expansion. The [network policy, identity and shared lookup batch](audits/first-release-expansion.md#13-network-policy-identity-and-shared-lookup-lifetimes) adds seven companions for NECP, socket content filtering, personas, audit sessions, SMR hash algorithms and symbol interning. Remaining priorities include transport algorithms, Skywalk diagnostics/test matrices and paired-pipe/provider variants, transport overlays, trust controls, trace consumers and remaining lock and power-policy paths. Historical findings below are retained rather than relabeled as current gaps.

The [MTE mitigation follow-up](audits/first-release-expansion.md#14-mte-mitigation-from-boot-policy-to-allocation-and-fault) expands the existing tag-storage and bootstrap chapters in place. It connects boot/CPU policy, tagged objects and aliases, allocator reuse, page preservation and fault reporting; hardware/monitor/provider boundaries remain explicit. It does not replace the unrelated expansion backlog.

[Guide index](README.md) · [Contents](table-of-contents.md) · [Verification record](coverage.md) · [Earlier expansion history](expansion-audit.md)

The highest-value next work is to explain missing mechanisms and complete concrete operations across subsystem boundaries. Adding more detail uniformly would repeat substantial material in IPC, allocation, file caching, signing, scheduling and IOKit while leaving larger gaps elsewhere.

The requested **whole Skywalk surface** has a separate expansion program. Four companion chapters implement the additional requests for deeper **pmap**, **DMA/segment generation**, **ARM64 exception assembly**, and **thread switching/entry/exit**. Their reading routes appear below. Skywalk now has memory, packet-pool, controller/provider, readiness, namespace/lookup, default datapath, netif and scheduling companions. Packet-transformation, filter/reinjection, agent/rule and NECP companions extend that coverage. Its full program remains partial, especially diagnostics/test matrices, paired-pipe and remaining provider/configuration/policy combinations.

## Scope and method

The baseline is **143 Markdown pages**, including four coverage/generated-navigation pages. The review covers all **139 explanatory pages**: their section structure, actual explanations, source references and declared limits. Four area reports give a disposition for each explanatory page:

| Report | Baseline pages | Areas |
| --- | ---: | --- |
| [Runtime, IPC and platform](audits/runtime-ipc-platform.md) | 34 | Scheduling, synchronization, Mach IPC, boot, exceptions and power |
| [VM and drivers](audits/vm-and-drivers.md) | 42 | Maps, objects, pmaps, allocators, IOKit and kernel libraries |
| [Processes, VFS and networking](audits/processes-vfs-networking.md) | 34 | Process interfaces, filesystems, sockets, protocols and Skywalk |
| [Security, development and shared paths](audits/security-and-development.md) | 29 | Security, diagnostics, build/test tooling, cross-subsystem and orientation pages |

Source review was selective and evidence-driven: locate a missing or shallow explanation, inspect the relevant local structures and implementation bodies, identify callers and configuration boundaries, and determine what an expansion can actually explain. This is a complete **documentation-scope audit**, not a claim that every branch of the kernel was audited.

The remaining four baseline pages were assessed as maintenance artifacts:

| Page | Disposition |
| --- | --- |
| [Coverage and verification](coverage.md) | Update counts and reviewed paths; distinguish audit references from implemented explanations. |
| [Historical expansion audit](expansion-audit.md) | Preserve completed research history and identify this report as the current gap assessment. |
| [Complete contents](table-of-contents.md) | Regenerate with the four new implementation chapters and four area reports. |
| [Source index](source-index.md) | Regenerate; explicitly state that audit-only references identify proposed work. |

The per-page disposition tables were checked against the inventory: all 139 explanatory pages occur once, with no omissions or duplicates.

The [reproducible inventory](audits/inventory.json), produced by [audit_inventory.py](tools/audit_inventory.py), records page metrics, source-file references and uncited implementation files. Its baseline contains **4,641 source/header/interface files and 2,465,322 physical lines**, including tests, comments, bundled headers and conditional code. The counted suffixes are `.c`, `.h`, `.cpp`, `.s`, `.S`, `.defs`, `.m` and `.mm`; other interfaces such as `.iig`, scripts and build files remain part of the qualitative review.

The baseline explanatory guides cite **653 distinct files**. That is a navigation measure, not a coverage percentage. A single citation can point to a 10,000-line file while explaining one function. Conversely, a mechanism can be explained through callers without directly citing every implementation file. Audit reports are excluded from the inventory's explanatory-guide counts so that merely identifying a new source file does not count as documenting it.

## Source-tree inventory at the audit baseline

This is a file inventory, not a compiled-source or reviewed-line count. The final column counts direct citations from explanatory guides before audit findings and the requested new chapters were added.

| Directory | All files | Counted source/header/interface files | Files cited by baseline guides |
| --- | ---: | ---: | ---: |
| Repository root | 3 | 0 | 2 |
| `EXTERNAL_HEADERS` | 148 | 139 | 0 |
| `SETUP` | 25 | 13 | 0 |
| `bsd` | 1,708 | 1,267 | 201 |
| `config` | 79 | 0 | 2 |
| `doc` | 34 | 0 | 26 |
| `iokit` | 304 | 258 | 73 |
| `libkdd` | 18 | 12 | 2 |
| `libkern` | 304 | 264 | 33 |
| `libsa` | 14 | 4 | 2 |
| `libsyscall` | 257 | 232 | 6 |
| `makedefs` | 8 | 0 | 5 |
| `osfmk` | 1,502 | 1,188 | 266 |
| `pexpert` | 72 | 57 | 4 |
| `san` | 60 | 36 | 2 |
| `security` | 39 | 30 | 10 |
| `tests` | 1,298 | 1,086 | 7 |
| `tools` | 238 | 55 | 12 |

The inventory also lists large uncited implementation files as search leads. These were checked against existing prose and caller coverage before becoming recommendations; size or lack of a link alone did not determine priority. Supporting directories receive configuration, test, decoding or provider-boundary treatment where appropriate, rather than an assumed kernel-runtime chapter for every file.

## Depth at the audit baseline

| Area | What is already substantial | Most useful remaining work |
| --- | --- | --- |
| Runtime | Wake/selection/context paths, Clutch/Edge, priority/quantum, RT/SMT eligibility, waits/turnstiles and timer lifetimes | Clock domains/commpage, resource/accounting aggregation, task suspension and additional lock implementations |
| Mach IPC | Namespace/rights, message representation and transfer, port death, RPC/MIG, exceptions, guards, vouchers and importance | Special-reply/turnstile state, namespace growth and narrower synchronization-object lifetimes |
| VM/allocation | Map/object/fault/COW ownership, pmap backends, wiring/UPLs, reclaim, allocator routing and type isolation | Requested concrete pmap walkthrough; shared-region/dyld transformations, copy/remap, compressor internals, deferred reclamation, purgeable state and MTE |
| Processes | Exec/fork/exit/wait, signal delivery, kqueue/workloops, workqueue and AIO | Descriptor reservation/dup/close, pipes/UNIX rights, ulocks/POSIX/System V IPC and TTY/job control |
| VFS | Lookup/namespace mutations, vnode/name/file/buffer caches, mount/reclaim, writeback, special/stacked filesystems and NFS server | Attribute/xattr/ACL interfaces, advisory locking, filesystem events and selected durability/error semantics |
| Networking | Socket lifecycle, selected TCP connection/timer/data paths, packet/route/interface lifetimes and initial Skywalk paths | Whole Skywalk program; UDP/IPv6/neighbor protocols, network policy/filter engines, interface variants and remaining TCP algorithms |
| IOKit/libkern | Objects/registry/service lifetimes, notifications, DriverKit, workloops, CPU maps, DMA ownership, power and reporting | Requested segment-generation walkthrough; OSKext/kernel collections, serialization/parser ownership, symbol interning and PM assertions |
| Security | Credential/MAC lifetimes, signature pipeline, audit output, SPTM/TXM and Exclaves | Task/thread right flavors, personas/group resolution, audit-session capabilities, trust-cache/csops/CSR frontend |
| Platform | ARM64 entry/return, monitor boundaries, CPU lifecycle, hibernation and x86 sleep | Ordinary x86 trap/syscall paths, clock hardware/boot details and selected platform services |
| Development/diagnostics | Source-selection/test-harness orientation, selected tracing/accounting/sysctl entries | Crash artifacts, stackshot/kcdata, trace consumption, logging, DTrace and sanitizer/coverage lifetimes |
| Shared teaching paths | Ownership, SMR and completion comparisons; representative operation diagrams | Concrete address/object-state examples for pmap, DMA and Skywalk; SMR hash resizing and test-to-invariant maps |

“Substantial” applies to the named paths, not every API in that area. The detailed reports identify where an overview should stay short and gain a companion chapter.

## Requested expansion tracks

### 1. Whole Skywalk surface

Treat Skywalk as a substantial subsystem with its own chapter tree. The current [overview](subsystems/networking/skywalk.md) and [lifecycle chapter](subsystems/networking/skywalk-lifecycles.md) provide useful entry points, but they are not sufficient coverage of its interfaces and implementation.

The expansion must account for:

- Configuration, initialization, exported/user/kernel interfaces and syscall/ioctl admission.
- Channels, ring/slot schemas, synchronization, validation, readiness and event delivery.
- Nexus controllers, domains, providers, adapters, ports, bindings and their separate reference/close protocols.
- Packets, buflets, pools, regions, slabs, caches, arenas, mappings and ownership across user/kernel/device boundaries.
- Flow/protocol/port namespaces, flow-switch classification, routes, TX/RX, fragmentation, segmentation and checksum/offload paths.
- Netif native and compatibility paths, logical links, queues, scheduling, filters and agents.
- User/kernel pipe nexuses and their peer/ring lifetimes.
- Policy integration, traffic rules, statistics, diagnostic controls, tests and error/teardown paths.

The [networking audit's Skywalk program](audits/processes-vfs-networking.md#a12--p1-complete-skywalk-expansion-program) provides the directory/interface inventory and 13 proposed chapters. Each surface should include an interface/structure map, at least one normal operation, failure/partial progress, close/reclaim, configuration, and a worked ownership diagram. Concrete NIC drivers, external agents and userspace policy must remain explicitly bounded.

### 2. Pmap and the meaning of a hardware mapping

The existing [ARM64 structure guide](subsystems/vm/pmap-arm64.md), [mapping lifecycle](subsystems/vm/pmap-mapping-lifecycle.md), [TLB/cache guide](subsystems/vm/pmap-tlb-and-cache.md) and [x86 pmap](subsystems/vm/pmap-x86.md) contain substantial implementation detail. The remaining teaching gap is following concrete values and objects through those pieces.

The requested expansion should make a reader able to:

1. Separate a `vm_map_entry`, object offset, resident page, pmap, table page, PTE, physical address and TLB entry.
2. Decompose an example virtual address using the actual 4 KiB/16 KiB geometry and configured root level.
3. Locate each table and decode a valid leaf, absent entry, permission state and software marker.
4. Follow table allocation and `pmap_enter`, including reverse metadata and legacy/SPTM differences.
5. Explain a read fault, COW write, protection reduction, removal, TLB completion and safe page/table reuse.
6. Distinguish user/kernel/nested address spaces and CPU translations from device IOMMU mappings.

Numeric examples must state their configuration and be checked against local constants. Source-supported behavior must remain distinct from external SPTM implementation.

Added: [Pmap translation walkthroughs](subsystems/vm/pmap-translation-walkthroughs.md), including three source-checked address decompositions, PTE decoding, mapping/protection/removal, table ownership and reuse.

### 3. DMA descriptors and segment generation

The source API corresponding to the requested `genVMSegments` walkthrough is `IODMACommand::genIOVMSegments`, with typed wrappers. Existing [DMA preparation](subsystems/drivers/dma-preparation-and-mapping.md) explains ownership; the new walkthrough should show the actual values and descriptor transitions.

Required explanation: caller virtual ranges → descriptor backing and preparation → UPL/page information → command range/constraints → physical or mapper-backed DMA addresses → formatted output segments → device completion/synchronization → mapping and page release.

Include descriptor subclasses/composition, `IODMACommand` cursor state, `IOMapper` contracts, split/coalesced segments, alignment/address-width limits, bounce/copy paths, incremental calls and failure results. Diagrams must label CPU virtual, physical and device-address domains. An illustrative scatter/gather example must not be presented as an observed hardware transfer.

Added: [DMA segment walkthrough](subsystems/drivers/dma-segment-walkthrough.md), including the complete generator decisions, descriptor dispatch, padded mapper coordinates, sparse copying, real bounded-iteration code, error mutations and DriverKit completion.

### 4. Architecture-specific exception assembly

Added: [ARM64 assembly walkthroughs](subsystems/platform/arm64-assembly-walkthroughs.md). Read selected `locore.s` and related macro sequences instruction by instruction, with register and stack state at each boundary. The chapter connects hardware exception state, user PCB and kernel frames, C handler dispatch, AST processing, pointer authentication and final exception return.

The guide retains configuration guards and identifies uncertainty where source macros alone do not establish one universal compiled sequence. It does not reconstruct missing monitor or firmware bodies. Ordinary x86 entry/return remains a separate priority below.

### 5. Thread switching, first entry and exit

Added: [ARM64 thread switching](subsystems/platform/arm64-context-switching.md). This joins the scheduler's selection with `machine_switch_context`, `Switch_context`, pmap/extended-context changes, register and stack restoration, manufactured first-dispatch state, `thread_continue`, `Call_continuation`, stack handoff, user return, and termination/reaping.

The chapter distinguishes kernel function return from exception return, live stack from saved state area, user PCB from compact kernel context, and leaving the CPU from final object destruction. Idle/shutdown paths connect the same save/restore machinery to the existing power chapters.

## General expansion priorities

The ranking is based on explanatory value, missing local mechanisms and reuse across chapters. It is not a ranking of security risk, code quality, or source-file size.

| Priority | Expansion group | Why it matters | Detailed evidence |
| --- | --- | --- | --- |
| P1 | Descriptor allocation, duplication, close and local data transfer | Completes common user operations whose ownership rules differ from Mach rights | [Processes/VFS/networking](audits/processes-vfs-networking.md) |
| P1 | UDP and IPv6 socket-to-packet paths | The network explanation is currently much stronger for sockets and selected TCP paths | [Processes/VFS/networking](audits/processes-vfs-networking.md) |
| P1 | Shared-region/dyld mapping and VM copy/remap | Explains how executable sharing and actual mapping transformations use the VM abstractions | [VM/drivers](audits/vm-and-drivers.md) |
| P1 | Compressor segment and swapfile lifetimes | Extends slot-level explanations into memory/storage reclamation decisions | [VM/drivers](audits/vm-and-drivers.md) |
| P1 | OSKext/kernel-collection lifecycle and serialization | Major local implementation remains behind short runtime/interface descriptions | [VM/drivers](audits/vm-and-drivers.md) |
| P1 | Clock domains and accounting/resource aggregation | Connects scheduling, observed time and resource attribution | [Runtime/IPC/platform](audits/runtime-ipc-platform.md) |
| P1 | Synchronous IPC dependencies and special-reply state | Completes message transport with scheduler dependency and turnstile lifetime | [Runtime/IPC/platform](audits/runtime-ipc-platform.md) |
| P1 | Ordinary x86 trap, syscall and interrupt return | Provides an architecture counterpart to the deeper ARM64 execution paths | [Runtime/IPC/platform](audits/runtime-ipc-platform.md) |
| P1 | Task/thread right flavors and conversion | Connects BSD identity, Mach capabilities, policy checks and object lifetimes | [Security/development](audits/security-and-development.md#s1-task-and-thread-rights-as-an-end-to-end-capability-path--p1) |
| P1 | Corpse/core/panic paths and stackshot collection | Explains the artifacts used to investigate every other subsystem | [Security/development](audits/security-and-development.md) |
| P1 | Configuration/test-to-invariant references | Makes chapter claims easier to inspect and prevents accidental configuration generalization | [Security/development](audits/security-and-development.md#d6-configuration-and-test-evidence-attached-to-implementation-chapters--p1) |
| P2 | Neighbor/IP control paths, NECP/content filters and filesystem metadata/locks/events | Substantial local state machines remain survey-level | [Processes/VFS/networking](audits/processes-vfs-networking.md) |
| P2 | Deferred reclamation, purgeable memory, MTE storage and PM assertions | Adds important ownership protocols beyond the common VM/power paths | [VM/drivers](audits/vm-and-drivers.md) |
| P2 | Lock variants, suspension/control, ledgers and namespace growth | Completes important alternatives around already detailed common paths | [Runtime/IPC/platform](audits/runtime-ipc-platform.md) |
| P2 | Personas, audit sessions, trust-control interfaces, SMR hash resizing | Joins identity/capability/publication mechanisms with distinct lifetimes | [Security/development](audits/security-and-development.md) |
| P2 | Trace consumers, logging, DTrace and sanitizers | Turns diagnostics navigation into implementation explanations | [Security/development](audits/security-and-development.md) |
| P3 | PF/IPsec, specialized linker, resilience, hardware/provider and rare configuration branches | Valuable after foundational routes; expand where local implementation supports it | All area reports |

The requested tracks take precedence over this general queue; the four new walkthroughs address the immediate pmap, DMA, assembly and thread requests. Some P1 groups deserve multiple chapters rather than one very large page. The area reports contain the concrete questions and proposed boundaries.

## Improvements to apply across future chapters

- **Show values as well as names.** Use one concrete address, range, descriptor, ring index or reference transition through the whole operation.
- **Record branch conditions.** State what selects a backend, fast path, copy, retry or rejection; distinguish compile-time configuration from runtime policy.
- **Make ownership visible.** Diagrams should identify who owns data, metadata, mappings and completion responsibility at each stage.
- **Include failure after progress.** Explain output-copy failure, partial I/O, cursor advance, published objects and delayed cleanup.
- **Attach selected tests.** Name the invariant and test conditions; a test filename alone is not evidence that all paths are verified.
- **Keep exact source excerpts and honest boundaries.** A declaration or callback does not reveal an absent provider's implementation.

The current link/excerpt checks verify navigation and copied code, not the semantic truth of every sentence. Detailed new chapters still need an independent source review. No single “percentage of XNU documented” follows from word counts, file links or the audit inventory.

## Material that should remain bounded

APFS internals; absent NFS client operations; most concrete hardware drivers and IOMMU backends; full userspace pthread/DriverKit/dyld services; AMFI/CoreTrust/sandbox policy; secure-kernel/SPTM/TXM internals; and missing generated/imported bodies cannot be reconstructed from this checkout. Explain their local entry/exit contracts and distinguish genuinely missing code from local code not yet documented.

Tests, build scripts, library wrappers, external headers and upstream documentation are included in the inventory but serve different purposes. They should not all receive the same chapter depth as VM, IPC or the data path.

## Audit artifacts and maintenance

The baseline inventory is a snapshot before the four implementation chapters added during this audit. Re-running its generator updates the snapshot to the then-current explanatory guides; audit-only citations remain excluded. The four area reports are review records and expansion plans, not substitutes for the proposed chapters.

The historical [expansion audit](expansion-audit.md) remains the record of completed passes. This report supersedes its older gap list for prioritization. The generated TOC and source index include audit documents for navigation; their raw totals must not be interpreted as newly explained kernel behavior. HTML and SVG publication remain outside this Markdown work.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
