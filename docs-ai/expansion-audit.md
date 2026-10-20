# Documentation expansion: topic audit and research record

The latest [first-release expansion](audits/first-release-expansion.md) records the initial nine requested areas and the [audit-priority follow-up](audits/first-release-expansion.md#10-audit-priority-follow-up) through Skywalk control/readiness, VM copy/remap, clocks/accounting, descriptors, capabilities and suspension. Scope remains ARM64/common code, with no new x86 or KDP coverage. The earlier passes below remain historical records.

The [netif, flow lookup, authorization and ARM64 memory batch](audits/first-release-expansion.md#11-netif-flow-lookup-authorization-and-arm64-memory) adds seven companions with separate state/lifetime explanations. The [packet transformations, filtering, IPC and logging batch](audits/first-release-expansion.md#12-packet-transformations-filtering-ipc-internals-and-logging) follows those gaps with six companions and an in-place namespace expansion. The [network policy, identity and shared lookup batch](audits/first-release-expansion.md#13-network-policy-identity-and-shared-lookup-lifetimes) adds seven companions for NECP, socket content filtering, personas, audit sessions, SMR hash algorithms and symbol interning. Remaining priorities include transport algorithms, Skywalk diagnostics/test matrices and paired-pipe/provider variants, transport overlays, trust controls, trace consumers and remaining lock and power-policy paths. Historical findings below are retained rather than relabeled as current gaps.

The [MTE mitigation follow-up](audits/first-release-expansion.md#14-mte-mitigation-from-boot-policy-to-allocation-and-fault) expands the existing tag-storage and bootstrap chapters in place. It follows MTE from boot-policy and CPU setup through tagged mappings, allocation lifetimes and fault handling, retaining the earlier physical-backing explanation and the separate expansion backlog.

[Guide index](README.md) · [Complete contents](table-of-contents.md) · [Coverage and verification](coverage.md)

This audit records the Markdown expansion requested before building an HTML handbook. The existing chapters are the starting explanation, not a fixed limit on topics or depth. The unit of review is a mechanism and its execution paths: its state, inputs, decisions, synchronization, ownership, completion, and failure handling.

For the latest chapter-by-chapter gap assessment and priorities, use the [complete coverage audit](coverage-audit.md). This page preserves the history of earlier research and expansion passes; its starting gaps are not claims about the current tree.

## Baseline and review categories

The pre-handbook-expansion baseline had 86 Markdown pages, 88 Mermaid diagrams, and 280 checked source excerpts. Its depth was uneven. IPC, VM, allocation, ARM64 exceptions, and protected execution already had substantial implementation chapters. Runtime, BSD processes, networking, VFS, and drivers mostly had shorter orientation guides. Page length alone does not establish depth; the starting findings below came from those chapters' explanations and recorded inspection limits.

| Category | Meaning |
| --- | --- |
| Detailed path | Important structures, decisions, concurrency and cleanup are explained for a named source path. This is not a whole-file audit. |
| Partial | An entry point or success path is described, but consequential decisions, state transitions or teardown need expansion. |
| Navigation only | The guide identifies source locations or an external interface without explaining the implementation path. |
| External boundary | The relevant implementation is not supplied here. Expansion can explain the local contract, callers and outcomes, but cannot reconstruct absent code. |

Each expansion should answer:

1. Which objects and fields carry the operation, and who keeps them alive?
2. Which public, internal, callback or machine entry point starts the path?
3. Which conditions select branches, backends, fast paths and fallback?
4. What must remain locked, referenced, pinned or non-preemptible?
5. Where can execution sleep, retry, migrate, or call another subsystem?
6. Which state changes are committed before a failure, and how is it unwound?
7. What constitutes completion, and when can objects or memory be reused?
8. Which configuration and external implementation limits apply?

## Topic audit

| Area | Starting coverage | Expansion selected from the gaps | Boundaries that must remain explicit |
| --- | --- | --- | --- |
| Runtime | Common wake-to-run route, scheduler structures, wait/mutex introduction, timer/worker distinction | Scheduler eligibility and selection; context/stack handoff; Clutch/Edge decisions; turnstile ownership/propagation; expiry/cancel/requeue and worker-call lifetime | Selected scheduling paths are not a proof of every policy, topology or priority-chain race |
| BSD processes | Process/task model; fork/exec/exit overview; signal and event entry points; AIO worker overview | Process transition/exit coordination, signal delivery/return, kqueue/knote/workloop state, workqueue servicing and cancellation | External pthread callbacks and all POSIX variants cannot be inferred from shims |
| Networking | Socket/TCP established-data route; callback families; selected Skywalk TX; policy survey | Connection and teardown state, socket buffer ownership, TCP loss/timers, interface/routing lifetime, deeper flow/ring/policy ownership | Hardware providers, complete transport heuristics and every filter/protocol variant remain separate |
| VFS/storage | Lookup, vnode counts, cached reads, operation vectors and filesystem survey | Cache validation/publication, vnode drain/reclaim, mount busy/crossing/unmount, clustered writeback and UPL/buffer completion | APFS, complete storage drivers and absent NFS client code remain external |
| IOKit/libkern | Matching, user-client dispatch, workloops, memory/DMA and power overview | Matching/termination coordination, connection/RPC teardown, event-source and power acknowledgments, DMA completion and resource release | Concrete drivers, IOMMU hardware and userspace DriverKit implementations remain external |
| IPC | Detailed names/rights, message transport, MIG and exception paths | Audit less-developed guard, notification, voucher and importance mechanisms; extend selected missing lifetimes | Generated stubs and policy-provider bodies may be absent |
| VM and allocation | Detailed maps, objects, faults, pagers, pmaps, reclaim and allocator/type isolation | Review existing limits and cross-subsystem completion gaps; add focused material where the source supports an untraced mechanism | Whole-VM concurrency, every allocator option and external monitor enforcement are not implied |
| Security | Detailed monitor integration; shorter credentials/MAC/audit guides | Review credential publication, MAC dispatch/lifecycle and audit completion gaps | External authorization policy and cryptography remain boundaries |
| Platform | Detailed ARM64 exception paths; shorter boot, CPU/power and platform-service guides | Review boot ordering, CPU lifecycle, idle/sleep/resume and hibernation handoffs | Firmware, protected transition bodies and hardware/platform policy remain external |
| Cross-subsystem paths | Representative open/read, mapped fault, fork/exec, IPC, receive, driver and pressure routes | Connect the expanded paths through ownership, partial failure, cancellation and completion | A source trace records selected paths, not observed execution on a live kernel |
| Development/observation | Build/test navigation and representative instrumentation entry points | Preserve source selection, generated-interface provenance and diagnostics needed to inspect expanded paths | No kernel build, boot, benchmark or hardware test is part of this phase |

## Research and integration record

Work is divided by subsystem so each researcher can follow adjacent structures, callers, locks and cleanup without overlapping edits. The coordinating work maintains this audit, expands VFS/storage, connects the new material, and checks references and excerpts. Subsequent reviews compare independently authored chapters with the source and related guides.

The initial phases 1–3 completed the topic audit, selected source research, and Markdown expansion/integration. That pass added 27 implementation chapters plus this audit and the generated TOC, bringing the tree at that point to 115 Markdown pages, 123 Mermaid diagrams and 405 checked source excerpts. Existing guides were retained and cross-linked, with additional AIO and glossary coverage. Subsequent requested expansions are recorded below; [coverage and verification](coverage.md) records the current counts and checks. Phase 4 now has a [scripted local HTML build](development/building-html.md).

The expansion adds the following implementation chapters while retaining the original introductions. Each chapter records its source route and limits; an interface name or source link alone is not counted as an expanded mechanism.

| Area | Implementation chapters | Decisions and lifetimes expanded |
| --- | --- | --- |
| Runtime | [Scheduler execution](subsystems/runtime/scheduler-execution.md), [Clutch/Edge](subsystems/runtime/clutch-and-edge.md), [wait/turnstile protocols](subsystems/runtime/wait-and-turnstile-protocols.md), [timers/thread calls](subsystems/runtime/timer-and-thread-call-lifetime.md) | Eligibility and current-thread comparison, hierarchy/warp/starvation windows, stack handoff and allocation retry, departure/reaping, wait registration and inheritor propagation, timer dequeue races and branch-specific cancellation |
| Processes | [Process transitions](subsystems/processes/process-transitions.md), [signals/return](subsystems/processes/signal-delivery-and-return.md), [kqueue/workloops](subsystems/processes/kqueue-and-workloops.md), [pthread/workqueue lifecycle](subsystems/processes/pthread-workqueue-lifecycle.md); expanded [AIO](subsystems/processes/async-io.md) | Shadow-proc publication and return gates, irreversible exec failure, exit/wait/reap, signal target/frame/token/state import, knote registration/post/drop/copyout, worker admission/bind/park, cancellation and ordered drains |
| Networking | [Socket lifecycle/I/O](subsystems/networking/socket-lifecycle-and-io.md), [TCP connections/timers](subsystems/networking/tcp-connections-and-timers.md), [packets/routes/interfaces](subsystems/networking/packets-routes-and-interfaces.md), [Skywalk lifecycles](subsystems/networking/skywalk-lifecycles.md) | Queue ownership and ancillary rights, accept visibility and handshake state, retransmission/timer ownership, close deferral, route cache validity and final-reference locking, ifnet quiescence, packet-pool ownership and flow removal/linger |
| VFS | [Name cache/vnode reclaim](subsystems/vfs/name-cache-and-vnode-reclaim.md), [mount lifecycle](subsystems/vfs/mount-lifecycle.md), [clustered writeback](subsystems/vfs/clustered-writeback.md) | SMR snapshot/reference conversion, publication/invalidation generations, drain variants, filesystem cleanup and vnode reuse, mount admission/reference domains, failed unmount, packed/sparse dirty tracking, UPL reacquisition, direct-write coherence and transaction completion |
| Drivers | [Matching/termination](subsystems/drivers/service-matching-and-termination.md), [user-client/DriverKit lifetime](subsystems/drivers/user-client-and-driverkit-lifetime.md), [workloop/power protocols](subsystems/drivers/workloop-and-power-protocols.md), [DMA preparation/mapping](subsystems/drivers/dma-preparation-and-mapping.md) | Candidate/probe/start ownership, deferred termination phases, exported-object and connection cleanup, RPC object/message ownership, event/timer/gate execution, power acknowledgments, descriptor versus command preparation and failure unwind |
| IPC | [Guards/policy enforcement](subsystems/ipc/guards-and-policy-enforcement.md), [vouchers/importance](subsystems/ipc/vouchers-and-importance.md) | Construction policy and guard context, deferred guard handling, reply constraints, voucher uniquing/manager references and port lifetime, message processing versus thread adoption, importance donation and release |
| VM | [Memorystatus and freezer](subsystems/vm/memorystatus-and-freezer.md) | Pressure-policy action, candidate selection/reference/revalidation, termination outcomes, task/map freezing and process/budget accounting |
| Security | [Credential/policy lifetimes](subsystems/security/credential-and-policy-lifetimes.md), [audit pipeline](subsystems/security/audit-pipeline.md) | Credential uniquing/publication/retry and thread cache refresh, kauth unlisten contract, dynamic MAC iteration/unload and label ownership, audit preselection/commit/backpressure/worker/output/rotation/failure |
| Platform | [CPU and power lifecycle](subsystems/platform/cpu-power-lifecycle.md) | Startup ordering, CPU start/offline admission, idle versus system sleep, warm resume and hibernation handoffs |
| Shared mechanisms | [SMR/publication](cross-cutting/smr-and-publication.md), [completion/partial failure](cross-cutting/completion-and-failure.md) | Reader sequences, sleepable tracker transfer and turnstiles, deferred callbacks and barriers; contrasts between resource transfer, result publication, copyout, cancellation, quiescence and final release |

Several research choices avoid repeating already detailed material:

* Port-death, no-senders and backup-port notifications already have a substantial [port-lifecycle chapter](subsystems/ipc/ports-and-rights-lifecycle.md). The new IPC work connects policy/voucher/importance lifetimes to it.
* Compressor slots, swap submission/completion, allocator isolation and pmap backends already have implementation chapters. The VM addition concentrates on the previously short process-level pressure/freezer discussion.
* ARM64 exception entry/return and SPTM/TXM/Exclaves remain in their existing detailed chapters. The platform/security additions address CPU lifecycle, credentials, policy dispatch and audit.
* Build and observation guides retain their existing role: identify selected code, generated interfaces and instrumentation. This phase does not imply a build, a boot or runtime evidence.

## Filesystem, scheduler, sleep and IOKit expansion

The next requested pass expands the filesystem, scheduler, hibernation/resume/sleep, and IOKit implementation. Three researchers first followed filesystem, scheduler and hibernation paths, then continued into distinct IOKit mechanisms. Coordinating work connected system sleep, bootstrap/BSD integration, shared queues and reporting/performance accounting, reviewed the filesystem claims, and integrated navigation. The new material extends the earlier chapters rather than replacing their introductions or repeating the already detailed DMA, service termination and common scheduler paths.

| Area | New chapters | Principal decisions and lifetimes |
| --- | --- | --- |
| Filesystem mutation | [Namespace mutations](subsystems/vfs/namespace-mutations.md) | Compound final lookup/authorization/continuation; create postprocessing failure; link/unlink ownership; rename lock acquisition after dropping references, relookup, dataless materialization and bounded retries |
| In-tree filesystem implementations | [Device nodes and FIFOs](subsystems/vfs/device-nodes-and-fifos.md), [stacked filesystems](subsystems/vfs/stacked-filesystems.md) | Devfs registration/clone/removal, specfs device-switch and alias open accounting, FIFO socket pairs; bindfs/nullfs upper/lower identity, publication races, credential context, page-in and unmount |
| Network filesystem server | [NFS requests](subsystems/vfs/nfs-server-requests.md) | Socket upcalls/framing, worker/request ownership, bounded duplicate cache, export/file-handle/credential conversion, READ/WRITE/gather/COMMIT, reply and shutdown |
| Scheduler policy | [Priority/QoS/quanta](subsystems/runtime/priority-qos-and-quanta.md), [realtime deadlines/runqueues](subsystems/runtime/realtime-deadlines-and-runqueues.md), [CPU eligibility/variants](subsystems/runtime/cpu-eligibility-and-scheduler-variants.md) | Effective policy and usage decay, priority reinsertion, quantum accounting, stacked mode demotions, realtime parameter adjustment and conditional priority/EDF choice, SMT/AMP placement, recommendations and CPU availability |
| Hibernation and machine return | [Image creation](subsystems/platform/hibernation-image-creation.md), [restore](subsystems/platform/hibernation-restore.md), [x86 sleep/resume](subsystems/platform/x86-sleep-and-resume.md) | File/resource publication and timeout, inverted page-list bits and volatile exclusions, image streams/compression/encryption, polling, early collision handling, late reads, VM metadata rebuild, SPTM warm handoff and x86 saved context |
| System power policy | [System sleep and wake](subsystems/drivers/system-sleep-and-wake.md) | Capability state/generations, event submission, notification filtering, reply cookies/cancellation, bounded sync, task suspension, hibernation preparation, scheduler/CPU handoff and wake completion |
| IOKit bootstrap and runtime | [Bootstrap/BSD integration](subsystems/drivers/bootstrap-and-bsd-integration.md), [objects and collections](subsystems/drivers/object-runtime-and-collections.md) | Constructors and lockdown ordering, device-tree backing, resources and root-device matching; class registration, refcounts, allocation, casts, instance accounting and collection mutation/copy |
| Registry and notifications | [Planes/properties](subsystems/drivers/registry-planes-and-properties.md), [notifications/arbitration](subsystems/drivers/service-notifications-and-arbitration.md) | Reciprocal graph links, property ownership, traversal validity, paths/serialization; registration and existing-instance replay, callback removal, notifier references and arbitration lock conflicts |
| Driver execution and device power | [Interrupts/command queues](subsystems/drivers/interrupt-routing-and-command-queues.md), [device power machine](subsystems/drivers/device-power-state-machine.md) | Provider/controller routing, shared vectors and filters, command-pool transfer, legacy queue configuration; state order versus index, parent/child admission, queued requests, driver calls, acknowledgments, settle behavior and stop |
| Driver interfaces and memory | [DriverKit dispatch/actions](subsystems/drivers/driverkit-dispatch-and-actions.md), [descriptors/CPU mappings](subsystems/drivers/memory-descriptors-and-cpu-mappings.md) | IIG metadata, local routing and actions, dispatch-source ownership and missing runtime boundaries; buffer/composite backing, named entries, map reuse/submaps/static mappings, redirects, pager/cache behavior and unmap |
| Shared data and completion | [Shared queues/notifications](subsystems/drivers/shared-data-queues-and-notifications.md) | SPSC ring publication/wrap, notification races, dequeue failure, circular overwrite/sequence/generation validation, cursor progress, mapping lifetime and asynchronous Mach results |
| Observation and device-work accounting | [Reporting/performance control](subsystems/drivers/reporting-and-performance-control.md) | Reporter configuration/data locks, buffer swap/rollback, sample partial progress, state residency/histograms, controller registration, work tokens/contexts and retained submitter identities |

This pass adds 21 chapters, including 11 in the driver section. Source-visible qualifications are part of the explanations: the realtime `preemptible` field is ignored; time-constraint acceptance is not global admission control; sleep sync is not a universal stable-storage barrier; polling does not enforce the computed timeout in its disabled branch; NFS replay history is bounded; classic and circular shared queues have different loss behavior; and several DriverKit timer/queue bodies are absent. The chapters identify these boundaries at the relevant code rather than treating interface names as proof of implementation.

## File caches and executable-signature expansion

This pass adds seven chapters that connect filesystem identity, cached bytes, signature ownership and executable-page policy. It keeps the existing overviews and writeback/pager guides, with links to the new implementation paths.

| Area | New chapters | Questions traced |
| --- | --- | --- |
| Vnode identity and cached authorization | [Vnode cache and reuse](subsystems/vfs/vnode-cache-identity-and-reuse.md) | Allocation versus recycling, free/dead/asynchronous lists, vid/count rechecks, holds and SMR, devfs association, credential/action TTL, inactive/reclaim and UBC destruction |
| File-data pages | [File-data cache and reads](subsystems/vfs/file-data-cache-and-read-path.md) | Read dispatch, resident busy-page batches, mixed-validity UPLs, demand versus advisory completion, read-ahead, direct-I/O coherence, mapping lifetime, truncation and flush |
| Block and metadata buffers | [Buffer cache and block I/O](subsystems/vfs/buffer-cache-and-block-io.md) | Hash identity, busy waits and miss rechecks, storage versus headers, validity and resize, strategy/biodone callbacks, dirty writeback, release/invalidation and metadata reclaim |
| Serialized signatures | [Signature format and validation](subsystems/security/signature-format-and-blob-validation.md) | SuperBlob/CD offsets and slots, algorithms and CDHash, parser bounds and explicit gaps, auxiliary hashes, reconstitution and multilevel conversion |
| Vnode signature ownership | [Attachment lifecycle](subsystems/security/vnode-signature-lifecycle.md) | Loader/fcntl acquisition and reuse, address consumption, MAC/monitor checks, protected publication, duplicates, generation refresh, invalidation, supplemental signatures and teardown |
| Image and mapping admission | [Executable signature policy](subsystems/security/executable-signature-policy.md) | Exec/Mach-O ordering, command-buffer checks, process/map flags, launch constraints, detached lookup, library validation, shadow/backing offsets and monitor association |
| Cached integrity and faults | [Page-signature validation](subsystems/security/page-signature-validation.md) | File-offset/hash translation, checked/tainted/NX masks, result reuse, bitmap scope, busy/paging ownership, violation decisions, monitor deferral, writes/COW/UPL and transforming pagers |

The source distinguishes successful storage I/O, valid cache bytes, accepted signature metadata, checked page bytes, and permission to execute. The chapters preserve differences between loader and fcntl short-read handling, publication and later copyout failure, global generation and page masks, whole-page and subpage predicates, and ordinary versus supplemental attachments. Missing APFS, AMFI/CoreTrust, task-access-service and trusted-monitor implementations remain identified at their local interfaces.

## Complete coverage audit and concrete machine/DMA walkthroughs

The [complete coverage audit](coverage-audit.md) assesses all 139 explanatory pages at the 143-page baseline, plus the four coverage/navigation records. Four area reports provide a disposition for each explanatory page and source-backed expansion candidates. A preserved [inventory](audits/inventory.json) records the baseline page and citation metrics; it is not a reviewed-code percentage. The [whole-Skywalk program](audits/processes-vfs-networking.md#a12--p1-complete-skywalk-expansion-program) adds a directory/interface inventory and 13 proposed implementation chapters.

Four requested implementation chapters were completed during that audit:

| Chapter | Added explanation |
| --- | --- |
| [Pmap translation walkthroughs](subsystems/vm/pmap-translation-walkthroughs.md) | Three checked address decompositions, table-entry versus output physical addresses, decoded PTE values, root selection, enter/protect/remove/disconnect, table pins and reuse. |
| [DMA segment generation](subsystems/drivers/dma-segment-walkthrough.md) | Descriptor dispatch and UPL backing, physical/IOVA coordinates, padded mapper intervals, split/coalesce constraints, bounce copies, incremental generation and nontransactional errors. |
| [ARM64 exception assembly](subsystems/platform/arm64-assembly-walkthroughs.md) | Five instruction walkthroughs, active stack banks, user/kernel context storage, synthetic frames, C dispatch, AST retry, checked restore candidates and final `eret`. |
| [ARM64 thread switching, entry and exit](subsystems/platform/arm64-context-switching.md) | Compact kernel state, nonlocal C returns, pmap/CPU identity changes, first dispatch, continuations, stack handoff, user return, termination/reaping and idle/shutdown context. |

Independent reviews checked pmap arithmetic/lifetimes and thread switching against source; coordinating review checked the complete DMA generator decisions and selected exception assembly/register transitions. The four chapters add 19 Mermaid diagrams and 38 exact source excerpts. Audit reports identify future work and do not count as completed implementation explanations. HTML generation remains deferred.

## AST mechanism and complete entry-interface catalogs

This pass adds 72 Markdown pages and keeps the earlier subsystem chapters as the implementation reading routes. Separate agents traced AST dispatch and every flavor, the BSD syscall master and handlers, and Mach/machine-specific traps. The coordinator enumerated MIG interfaces and connected generated dispatch, capability conversions and outbound service boundaries. A second division of work added per-operation VM, runtime/host, IOKit, IPC and service/callback mechanisms.

| Area | Added documentation | Reconciliation and depth |
| --- | --- | --- |
| AST machinery | [Publication, propagation and dispatch](subsystems/runtime/ast-mechanism.md), [all flavors](subsystems/runtime/ast-flavors.md) | All 22 active bits, retired positions, composite masks, kevent/telemetry/kperf sub-flags; CPU/thread storage, remote check IPIs, interrupt state, payload clearing, PFZ, preemption, blocking and recheck. |
| Architecture entry | [Interface map](interfaces/README.md), [machine entry points](interfaces/machine-entry-points.md) | ARM SVC/platform/time selection, x86 syscall classes, machine-dependent and diagnostic tables, packed argument conventions and return results; Exclaves secondary operations. |
| BSD syscalls | [Dispatch and family catalog](interfaces/bsd-syscalls/README.md), [complete number index](interfaces/bsd-syscalls/number-index.md) | All 558 numbers, 669 conditional alternatives and 455 distinct non-placeholder declarations. Each active declaration has an authored purpose/mechanism; 454 resolve local handlers and the configured `vfork` declaration has an explicit missing-body boundary. |
| Mach traps | [Complete trap catalog](interfaces/mach-traps.md) | All 128 slots, 60 unconditional named operations and two conditional names. Records invalid entries, argument/munger metadata, implemented versus unsupported bodies, library fallback and special selectors outside the table. |
| MIG messages | [Dispatch guide](interfaces/mach-messages/README.md), [all subsystem catalogs](interfaces/mach-messages/subsystems.md) | All 49 subsystem-bearing non-test definition files and 541 raw routine sites represented in seven inspection profiles. All 510 per-file routine slots have a purpose/contract and mechanism or explicit implementation boundary; 23 always-skipped slots remain visible. |

The catalogs preserve different forms of evidence: a library declaration, a kernel-server `skip`, a generated stub contract, a local implementation and a registration in `mig_e` do not establish the same thing. Outbound notification and external-service interfaces have their local sender/ownership path where present. Compatibility placeholders, unsupported methods, missing generated code and absent receivers are identified beside the operation.

The added material contains 11 Mermaid diagrams and 289 exact source excerpts. Independent reviews checked all AST bits and trap rows, selected BSD socket/Skywalk/filesystem operations, VM and IOKit mechanisms, IPC rights/vouchers/eventlinks, and callback/service boundaries; coordinating review checked representative runtime mechanisms and catalog reconciliation. Corrections include conditional preemption escalation, narrow-ABI byte counts, post-operation output failures, dead-name allocation behavior, non-atomic namespace snapshots, manager-specific voucher handling, conditional mapping retention and no-op compatibility bodies.

This is complete entry enumeration within the stated local declaration/profile scope, not exhaustive analysis of all downstream `ioctl`, `fcntl`, `sysctl`, information/state flavors, driver selectors, provider implementations or concurrent paths. The whole-Skywalk audit program remains a separate expansion target; covering its numbered syscalls does not complete every Skywalk internal subsystem. HTML and rendered SVG generation remain deferred.

## Suggested review routes

| Review question | Reading route |
| --- | --- |
| Why does return to userspace run more kernel work? | [AST mechanism](subsystems/runtime/ast-mechanism.md) → [all flavors](subsystems/runtime/ast-flavors.md) → [ARM64 return assembly](subsystems/platform/arm64-assembly-walkthroughs.md) |
| Which interface does a library operation actually use? | [Entry map](interfaces/README.md) → [BSD dispatch](interfaces/bsd-syscalls/README.md), [Mach traps](interfaces/mach-traps.md) or [MIG receiver catalog](interfaces/mach-messages/README.md) |
| What really runs after a wakeup? | [Wait/turnstile state](subsystems/runtime/wait-and-turnstile-protocols.md) → [scheduler selection and context installation](subsystems/runtime/scheduler-execution.md) → [Clutch/Edge policy](subsystems/runtime/clutch-and-edge.md) |
| What survives a syscall failure? | [Cross-subsystem completion/failure](cross-cutting/completion-and-failure.md) → [exec/wait](subsystems/processes/process-transitions.md) → [socket send/receive](subsystems/networking/socket-lifecycle-and-io.md) → [Mach transfer](subsystems/ipc/message-send-receive.md) |
| When is a cached pointer safe to use or free? | [SMR](cross-cutting/smr-and-publication.md) → [vnode cache/reference conversion](subsystems/vfs/name-cache-and-vnode-reclaim.md) → [credential publication](subsystems/security/credential-and-policy-lifetimes.md) → [route/interface lifetime](subsystems/networking/packets-routes-and-interfaces.md) |
| How does asynchronous work shut down? | [Thread calls](subsystems/runtime/timer-and-thread-call-lifetime.md) → [AIO](subsystems/processes/async-io.md) → [workqueue/knote teardown](subsystems/processes/kqueue-and-workloops.md) → [driver event/power protocols](subsystems/drivers/workloop-and-power-protocols.md) |
| When can file or device memory be reused? | [Clustered writeback](subsystems/vfs/clustered-writeback.md) → [UPL ownership](subsystems/vm/pagers-and-upl.md) → [DMA preparation/completion](subsystems/drivers/dma-preparation-and-mapping.md) → [mount teardown](subsystems/vfs/mount-lifecycle.md) |
| What does a file-cache hit actually establish? | [Vnode identity/reuse](subsystems/vfs/vnode-cache-identity-and-reuse.md) → [resident file bytes](subsystems/vfs/file-data-cache-and-read-path.md) → [buffer ownership](subsystems/vfs/buffer-cache-and-block-io.md) |
| How does a file signature constrain execution? | [Signature format](subsystems/security/signature-format-and-blob-validation.md) → [vnode attachment](subsystems/security/vnode-signature-lifecycle.md) → [exec/map policy](subsystems/security/executable-signature-policy.md) → [page validation](subsystems/security/page-signature-validation.md) |

## Remaining depth and unavailable implementations

The selected mechanisms now have implementation-level routes. This is not an exhaustive audit of XNU or a claim that every function and race has been explained. Remaining narrower areas include every realtime/SMT placement and Edge policy combination; every turnstile client; all spawn/ptrace and event-filter variants; complete congestion-control/SACK/RACK, neighbor, multicast and fragmentation algorithms; every Skywalk arena/provider path; all vnode trigger/firmlink and specialized filesystem paths; every DriverKit generated method, hardware mapping provider and IOKit utility; every voucher manager, policy flag and memory-pressure action combination; and all hibernation image/configuration/error combinations. Common hibernation construction/restoration, selected realtime/SMT policy and the major IOKit mechanisms now have the dedicated chapters above.

APFS, absent NFS client operations, external pthread and DriverKit components, concrete hardware drivers, firmware, trusted monitors/secure-kernel bodies, external policy modules and missing generated/imported implementation remain explicit boundaries. The local caller, argument/result contract and cleanup are described where present; absent code is not reconstructed by inference.

The [coverage record](coverage.md) describes source review, independent checks and artifact verification. The [complete TOC](table-of-contents.md) is generated from the Markdown headings, and the [source index](source-index.md) is regenerated from direct local citations.

## Publication boundary

Markdown, source excerpts and editable Mermaid diagrams remain the authoring sources. The subsequently requested HTML book is generated locally with `python3 make_docs.py`, including rendered SVG assets, offline search and source previews. It requires no hosted service; see [build and reading instructions](development/building-html.md).

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
