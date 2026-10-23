# XNU source guide

This guide explains the `xnu-12377.121.6` source snapshot stored in Platydoc's `platydoc-data/xnu/` input: which subsystem owns which state, how operations cross subsystem boundaries, and where to read the implementation. Start with the architecture, then choose a concrete operation. Reading the tree alphabetically is much less useful.

The [complete table of contents](table-of-contents.md) lists every chapter and its main sections.

The [key-structures section](structures/README.md) follows allocation, access, updates and reclamation, starting with [`proc` and its protected data](structures/proc-and-proc-ro.md), [`task` and the shared RO record](structures/task-and-shared-ro.md), and [how writes to protected fields reach memory](structures/read-only-object-updates.md). It connects concrete process/task callers to the existing zone and SMR explanations.

Continue through [`thread`, `uthread` and `thread_ro`](structures/thread-and-thread-ro.md), [credential storage and replacement](structures/credentials-and-credential-storage.md), and [MAC label ownership](structures/mac-label-storage.md). Then follow a Mach capability through [IPC spaces and entries](structures/ipc-spaces-and-entries.md) into [ports and kernel-object associations](structures/ipc-ports-and-kobjects.md). These companions connect field maps and exact source excerpts to construction, lookup, protected writes, references, synchronization, failure and final release; the [reading exercises](structures/README.md#worked-reading-routes) join them into complete paths.

Continue into [VM maps and entries](structures/vm-maps-and-entries.md), [objects and backing](structures/vm-objects-and-backing.md), [page descriptors and resident storage](structures/vm-pages-and-resident-storage.md), and [ARM64 pmap/table storage](structures/pmap-and-translation-storage.md). Finish with [named memory entries and VM copy containers](structures/memory-entries-and-vm-copies.md), which connect memory ownership to Mach capabilities. The [VM structure route](structures/README.md#follow-virtual-memory-into-backing-and-translation-storage) separates metadata, physical bytes, translations and transferred references.

The [file and signature structure route](structures/README.md#follow-descriptors-into-file-and-signature-storage) follows [descriptor tables](structures/file-descriptor-tables.md), [fileprocs and shared fileglobs](structures/fileprocs-and-fileglobs.md), [vnode storage and identity](structures/vnodes-and-vnode-identity.md), [UBC and vnode pagers](structures/ubc-and-vnode-pagers.md), and [protected code-signature blobs](structures/code-signature-blob-storage.md). It connects descriptor reuse and shared offsets to cached backing, signed-byte views and staged reclamation.

The [message and network structure route](structures/README.md#follow-messages-and-packets-into-their-storage) follows [IPC kmsg buffers](structures/ipc-kmsgs-and-message-storage.md), [socket attachments](structures/sockets-and-protocol-attachments.md), [socket-buffer records](structures/socket-buffers-and-record-queues.md), [Internet PCB and TCP storage](structures/internet-pcbs-and-transport-storage.md), and [mbuf views and shared clusters](structures/mbufs-and-external-storage.md). It connects representation changes and queue publication to references, capacity accounting, partial failures and final release.

The [IPsec, MPTCP and process-inspection route](reading-guide.md#ipsec-interfaces-mptcp-and-process-inspection) connects [IPsec virtual-interface lifetime](subsystems/networking/ipsec-interface-lifecycle.md), [multipath sessions and TCP subflows](subsystems/networking/mptcp-sessions-and-subflows.md), and [`proc_info` queries and snapshots](subsystems/processes/process-inspection-and-snapshots.md) to the existing packet, transport and process chapters.

The [exec-stack, executable-I/O and scheduler-placement route](reading-guide.md#exec-stacks-executable-io-and-scheduler-placement) continues three existing topics through their next operations: [argument bytes into an ARM64 user stack](subsystems/processes/exec-arguments-and-user-stack.md), [executable pages into UPL backing](subsystems/vm/executable-pages-and-upl-io.md), and [thread-group changes into accounting and cluster placement](subsystems/runtime/thread-group-accounting-and-cluster-migration.md).

The [executable-memory, synchronization and packet-policy route](reading-guide.md#executable-memory-synchronization-and-packet-policy) connects [JIT/protection changes](subsystems/vm/executable-memory-policy.md), [semaphores/eventlinks](subsystems/ipc/semaphores-and-eventlinks.md), [work intervals/thread groups](subsystems/runtime/work-interval-policy-and-thread-groups.md), [flow diversion](subsystems/networking/flow-diversion-and-provider-lifetime.md), deeper [PF TCP/NAT](subsystems/networking/pf-rules-states-and-packet-ownership.md) and [IPsec IPv6/chains](subsystems/networking/ipsec-policy-associations-and-transforms.md), and a worked [ARM64 build/MIG trace](development/arm64-build-and-mig-walkthrough.md).

For a source-focused route through argument handling, authority and object lifetime, follow [the eight-part implementation reading route](reading-guide.md#argument-identity-and-lifetime-paths). It connects command dispatch, VM validation, concurrent operations, IOKit calls, exec identity, message/register integrity, instrumentation and packet processing.

The [Platydoc project layout](../README.md#project-layout) separates the handbook and its tools from the read-only XNU input.

Build the local HTML book with `python3 make_docs.py` from the Platydoc project root (the directory containing `platydoc-data/`), then open `docs-ai-html/index.html`. The [build guide](development/building-html.md) covers offline search, the alphabetical index, SVG diagrams, highlighted source previews and regeneration after Markdown or source changes.

## Start here

1. [Architecture and object relationships](architecture.md): the kernel's main components and their interfaces.
2. [Source map](source-map.md): directories, supporting components, and where to look for a feature.
3. [Reading guide](reading-guide.md): a staged route through structures and execution paths.
4. [Operations across subsystem boundaries](cross-cutting/execution-paths.md): file access, mapped memory, IPC, networking, process creation, and driver requests.
5. [Executable loading](cross-cutting/executable-loading.md): how Mach-O commands become mappings and initial execution state.
6. [Ownership and synchronization](cross-cutting/ownership-and-locking.md): how to reason about references, locks, deferred work, and teardown.
7. [SMR and pointer publication](cross-cutting/smr-and-publication.md): read-side protection, grace periods, sleepable readers, callback queues and barriers.
8. [Completion, cancellation and partial failure](cross-cutting/completion-and-failure.md): where ownership moves, what errors preserve, and when teardown can release storage.

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

Markdown links resolve relative to each chapter and reach the separate kernel input through `platydoc-data/xnu/`. Kernel paths written in prose, such as `osfmk/vm/vm_map.c`, and source-inventory metadata are XNU-relative unless stated otherwise; kernel build/debug commands run from `platydoc-data/xnu/` unless their instructions say otherwise, and documentation commands run from the Platydoc project root. Platydoc files and generated artifacts remain outside the kernel checkout. A link ending in `#L123` identifies a line in the inspected snapshot; renderers without source-line navigation can still open the file and search for the named symbol. Names and source paths are the durable navigation keys. Diagrams use Mermaid and describe selected relationships or paths; they do not imply every branch or lock operation is shown.

Copied source excerpts carry their original file and line range. The [documentation checker](tools/check_links.py) compares marked excerpts against those exact lines, including indentation; explanatory examples are identified separately. Rerun it after changing the checkout or extending a guide.

This is source analysis, not a report of running or booting the kernel. Architecture, platform, build variant, and feature configuration change compiled behavior. The original supplied folder identified the snapshot as `xnu-12377.121.6`; no usable Git history was available during that source analysis for pinning it to a commit. Moving the input to `platydoc-data/xnu/` does not itself revalidate the handbook against a different release. The build can obtain its version from an SDK/KDK or an override, as explained in the repository's [version documentation](../platydoc-data/xnu/doc/building/xnu_version.md).

The tree contains kernel mechanisms and many interfaces to components built elsewhere. It does not contain the complete macOS or iOS system, every hardware driver, or every security policy implementation. The guides identify those boundaries instead of filling them with assumed implementations. Existing [Apple-authored documentation](../platydoc-data/xnu/doc/) remains useful alongside this guide.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
