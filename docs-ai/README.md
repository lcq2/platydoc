# XNU source guide

This guide explains the `xnu-12377.121.6` source snapshot stored in Platydoc's `xnu/` input: which subsystem owns which state, how operations cross subsystem boundaries, and where to read the implementation. Start with the architecture, then choose a concrete operation. Reading the tree alphabetically is much less useful.

The [complete table of contents](table-of-contents.md) lists every chapter and its main sections. The [expansion audit](expansion-audit.md) records the topics deepened for the Markdown review before HTML generation.

The [Platydoc project layout](../README.md#project-layout) separates the handbook and its tools from the read-only XNU input.

Build the local HTML book with `python3 make_docs.py` from the Platydoc project root (the parent of `xnu/`), then open `docs-ai-html/index.html`. The [build guide](development/building-html.md) covers offline search, the alphabetical index, SVG diagrams, highlighted source previews and regeneration after Markdown or source changes.

The [first-release expansion](audits/first-release-expansion.md) adds detailed routes through networking below TCP, Skywalk memory and packets, synchronous Mach IPC, compressor/shared-region/reclamation internals, diagnostics, process-local IPC and TTY, VFS metadata, ARM64 user-memory access, and kernel loading/serialization/NVRAM. This pass focuses on ARM64 and common code; x86 and KDP are outside its scope.

Its [audit-priority follow-up](audits/first-release-expansion.md#10-audit-priority-follow-up) adds Skywalk controller/provider and readiness mechanisms, VM copy-overwrite/remap, clocks/commpage, Recount, ledger settlement, bank charging, task/thread capabilities and suspension. Descriptor reservation, publication, replacement and close are expanded in the existing [descriptor chapter](subsystems/processes/descriptors-ipc.md).

The [next parallel batch](audits/first-release-expansion.md#11-netif-flow-lookup-authorization-and-arm64-memory) adds [Skywalk namespace reservation and flow lookup](subsystems/networking/skywalk-namespaces-and-flow-lookup.md), [classification, routes and packet delivery](subsystems/networking/skywalk-flowswitch-classification-routes-and-datapaths.md), [netif links and queues](subsystems/networking/skywalk-netif-links-queues-and-scheduling.md), and [interface scheduling/FQ-CoDel](subsystems/networking/interface-packet-scheduling-and-fq-codel.md). It also follows [VFS permission and ACL decisions](subsystems/vfs/permissions-and-acl-evaluation.md), [MTE tag-storage lifetime](subsystems/vm/mte-tag-storage-and-page-lifecycle.md), and [ARM64 bootstrap memory and lockdown](subsystems/platform/bootstrap-memory-and-lockdown.md).

The following batch connects [Skywalk fragments and flow tracking](subsystems/networking/skywalk-fragments-reassembly-and-flow-tracking.md), [aggregation/segmentation/offloads](subsystems/networking/skywalk-tcp-aggregation-segmentation-and-offloads.md), [netif filters/reinjection](subsystems/networking/skywalk-netif-filters-and-reinjection.md) and [agents/traffic rules](subsystems/networking/skywalk-netif-agents-and-traffic-rules.md). It adds [Mach port-set readiness](subsystems/ipc/port-sets-and-waitq-readiness.md), expands [live IPC namespace growth](subsystems/ipc/names-and-rights.md), and traces [kernel logging, buffering and readout](development/kernel-logging-and-firehose.md).

Earlier expansions explain the [AST mechanism](subsystems/runtime/ast-mechanism.md) and [every AST flavor](subsystems/runtime/ast-flavors.md), map the [system-call and Mach interfaces](interfaces/README.md), and cover file caches/signatures, pmap, DMA, exception assembly, thread switching, scheduler policy, hibernation/resume and IOKit internals.

## Start here

For the current gaps and next expansion priorities, read the [complete coverage audit](coverage-audit.md). It includes an assessment of every baseline page and a whole-Skywalk expansion program. New detailed walkthroughs cover [pmap translations](subsystems/vm/pmap-translation-walkthroughs.md), [DMA segment generation](subsystems/drivers/dma-segment-walkthrough.md), [ARM64 exception assembly](subsystems/platform/arm64-assembly-walkthroughs.md), and [thread switching, entry and exit](subsystems/platform/arm64-context-switching.md).

1. [Architecture and object relationships](architecture.md): the kernel's main components and their interfaces.
2. [Source map](source-map.md): directories, supporting components, and where to look for a feature.
3. [Reading guide](reading-guide.md): a staged route through structures and execution paths.
4. [Operations across subsystem boundaries](cross-cutting/execution-paths.md): file access, mapped memory, IPC, networking, process creation, and driver requests.
5. [Executable loading](cross-cutting/executable-loading.md): how Mach-O commands become mappings and initial execution state.
6. [Ownership and synchronization](cross-cutting/ownership-and-locking.md): how to reason about references, locks, deferred work, and teardown.
7. [Topic expansion audit](expansion-audit.md): the coverage gaps, research scope and Markdown expansion preceding the HTML handbook.
8. [SMR and pointer publication](cross-cutting/smr-and-publication.md): read-side protection, grace periods, sleepable readers, callback queues and barriers.
9. [Completion, cancellation and partial failure](cross-cutting/completion-and-failure.md): where ownership moves, what errors preserve, and when teardown can release storage.

## Subsystem guides

Each subsystem index links to focused implementation guides, names the principal structures and entry points, and records what was inspected and what remains outside the analysis.

| Subsystem | What it explains |
| --- | --- |
| [Mach execution and scheduling](subsystems/runtime/README.md) | Tasks, threads, processors, scheduling policies, wait queues, locks, priority inheritance, timers, and accounting relationships |
| [Virtual memory and allocation](subsystems/vm/README.md) | Maps and range locks, objects/pages, faults and COW, ARM64/SPTM/x86 pmaps, page tables, reverse mappings, TLBs, wiring, pagers, compression, reclaim, and kernel allocation |
| [BSD processes and interfaces](subsystems/processes/README.md) | Process lifecycle, executable loading, syscalls, descriptors, signals, pthread integration, workqueues, kqueue, and asynchronous file I/O |
| [Mach IPC](subsystems/ipc/README.md) | Port names and rights, message transfer, message queues, MIG, kernel objects, exceptions, vouchers, and importance |
| [VFS and storage](subsystems/vfs/README.md) | Lookup and namespace mutation, mounts, vnode/cache lifetime, writeback, devfs/specfs/FIFOs, nullfs/bindfs and NFS server request/replay/I/O |
| [Networking](subsystems/networking/README.md) | Sockets, protocol dispatch, TCP/IP, packet buffers, interfaces, routing, policy, and Skywalk |
| [IOKit and kernel libraries](subsystems/drivers/README.md) | Bootstrap, objects/collections, registry and matching, notifications/arbitration, workloops/interrupts, user clients and DriverKit actions, shared queues, memory/DMA, device/system power and reporting |
| [Security](subsystems/security/README.md) | Credentials, authorization, MAC hooks, code signing, trust boundaries, auditing, and Exclaves integration |
| [Platform, boot, and machine execution](subsystems/platform/README.md) | Startup, architecture entry/exit, interrupts, CPU lifecycle, page-table backends, hibernation image creation/restoration and ARM64/x86 sleep/resume |

## Development and observation

- [Build, configuration, and tests](development/build-and-tests.md) explains how files and interfaces are selected or generated, and which test environments exist.
- [Tracing, accounting, debugging, and diagnostics](development/observability.md) connects kdebug, kperf, Recount, stackshot, kcdata, LLDB, and sanitizers to the objects they inspect.
- [Stackshot and kcdata](development/stackshot-and-kcdata.md), [corpses and process core dumps](development/corpses-and-process-core-dumps.md), and [ARM64 panic records](development/panic-coordination-and-records.md) explain diagnostic artifact creation, ownership and publication.
- [Vocabulary and object index](glossary.md) gives short definitions of the terms used throughout the code.
- [Source-reference index](source-index.md) maps each cited source file back to the guides that use it.
- [Coverage and verification](coverage.md) records the scope and how the documentation was checked.

## Detailed IPC and exception paths

For Mach IPC, follow [names and rights](subsystems/ipc/names-and-rights.md) → [port lifecycle](subsystems/ipc/ports-and-rights-lifecycle.md) → [message representation](subsystems/ipc/message-path.md) → [send and receive](subsystems/ipc/message-send-receive.md) → [kernel RPC/MIG](subsystems/ipc/kernel-rpc-and-exceptions.md). These pages track the same objects across namespace lookup, rights transfer, message delivery, reply, and cleanup, with inline source excerpts.

For ARM64 exceptions, follow [EL0 → EL1 entry](subsystems/platform/arm64-exception-entry.md) → [Mach exception delivery](subsystems/ipc/exception-delivery.md) → [EL1 → EL0 return](subsystems/platform/arm64-exception-return.md). The separate [EL2 and protected-execution guide](subsystems/platform/exception-levels-and-monitors.md) traces guest hypercalls, SPTM entry/exit hooks, protected-domain interrupt resumption, and legacy PPL boundaries.

## ASTs and the system-call surface

Start with [AST publication and dispatch](subsystems/runtime/ast-mechanism.md), then use the [flavor catalog](subsystems/runtime/ast-flavors.md) to find each bit's producers, consumer, execution context, clearing rules and configuration. The chapters connect CPU and thread masks to preemption, signals, suspension, guards, accounting, tracing and safe return to userspace.

The [entry-point map](interfaces/README.md) separates instruction entry, BSD syscall numbers, Mach trap numbers and Mach message IDs. Follow its [machine dispatch chapter](interfaces/machine-entry-points.md), [BSD catalog](interfaces/bsd-syscalls/README.md), [Mach trap catalog](interfaces/mach-traps.md), and [MIG message catalog](interfaces/mach-messages/README.md). Each catalog retains holes and conditional alternatives and links declared interfaces to local implementations or an explicit missing receiver. Dispatcher selectors and downstream driver, protocol and policy namespaces are identified separately.

## Detailed VM and hardware-mapping paths

Start with [mapping walkthroughs](subsystems/vm/mapping-walkthroughs.md), then follow [virtual address maps](subsystems/vm/virtual-address-maps.md) → [objects and pages](subsystems/vm/objects-and-pages.md) → [fault resolution](subsystems/vm/fault-resolution.md). These track anonymous allocation, mapped files, shared/private backing, COW, protection changes, and unmapping from API to physical-page ownership.

For hardware translation, follow [ARM64 pmap structures and table geometry](subsystems/vm/pmap-arm64.md) → [mapping and table lifetimes](subsystems/vm/pmap-mapping-lifecycle.md) → [ASIDs, TLBs, and caches](subsystems/vm/pmap-tlb-and-cache.md). The [x86_64 pmap guide](subsystems/vm/pmap-x86.md) covers its separate roots, PV lists, PCIDs, and shootdown protocol. Continue with [wiring and memory entries](subsystems/vm/wiring-and-memory-entries.md), [pagers and UPLs](subsystems/vm/pagers-and-upl.md), [reclaim/compression/swap](subsystems/vm/reclaim-and-pressure.md), and [kernel allocation](subsystems/vm/kernel-allocation.md). Each path names its structures, synchronization, cleanup, and source-visible limits.

## Detailed kernel allocation and type isolation

The [allocator overview](subsystems/vm/kernel-allocation.md) connects [zone elements/caches/reclaim](subsystems/vm/zone-allocator.md), [kalloc size/heap routing](subsystems/vm/kalloc-heaps-and-routing.md), and [kernel VM allocation/guards](subsystems/vm/kernel-virtual-allocation.md). For type isolation, read the dedicated [compiler metadata and assignment guide](subsystems/vm/typed-allocation.md): it traces fixed signature groups and zone budgets, variable heaps, initial shared allocations, and what matching frees actually validate. [Read-only and special zones](subsystems/vm/read-only-and-special-zones.md) and [IOKit/C++/BSD interfaces](subsystems/vm/allocator-interfaces.md) cover the additional protection and lifetime contracts.

## Detailed SPTM, TXM, and Exclaves boundaries

For protected execution, start with the [SPTM, TXM, and Exclaves entry/exit map](subsystems/security/protected-execution.md). Continue into [SPTM](subsystems/security/sptm.md), [TXM](subsystems/security/txm.md), and [Exclaves execution](subsystems/security/exclaves-execution.md), then [resources and physical ownership](subsystems/security/exclaves-resources-and-memory.md) and [service integration](subsystems/security/exclaves-services.md). These chapters distinguish normal calls, upcalls and interrupted-domain resumption, with explicit boundaries around code supplied outside this checkout.

## Conventions and limits

Markdown links resolve relative to each chapter and reach the separate kernel input through `xnu/`. Kernel paths written in prose, such as `osfmk/vm/vm_map.c`, and source-inventory metadata are XNU-relative unless stated otherwise; kernel build/debug commands run from `xnu/` unless their instructions say otherwise, and documentation commands run from the Platydoc project root. Platydoc files and generated artifacts remain outside the kernel checkout. A link ending in `#L123` identifies a line in the inspected snapshot; renderers without source-line navigation can still open the file and search for the named symbol. Names and source paths are the durable navigation keys. Diagrams use Mermaid and describe selected relationships or paths; they do not imply every branch or lock operation is shown.

Copied source excerpts carry their original file and line range. The [documentation checker](tools/check_links.py) compares marked excerpts against those exact lines, including indentation; explanatory examples are identified separately. Rerun it after changing the checkout or extending a guide.

This is source analysis, not a report of running or booting the kernel. Architecture, platform, build variant, and feature configuration change compiled behavior. The original supplied folder identified the snapshot as `xnu-12377.121.6`; no usable Git history was available during that source analysis for pinning it to a commit. Moving the input to `xnu/` does not itself revalidate the handbook against a different release. The build can obtain its version from an SDK/KDK or an override, as explained in the repository's [version documentation](../xnu/doc/building/xnu_version.md).

The tree contains kernel mechanisms and many interfaces to components built elsewhere. It does not contain the complete macOS or iOS system, every hardware driver, or every security policy implementation. The guides identify those boundaries instead of filling them with assumed implementations. Existing [Apple-authored documentation](../xnu/doc/) remains useful alongside this guide.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
