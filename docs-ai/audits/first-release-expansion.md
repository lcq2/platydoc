# First-release expansion: networking, memory, IPC and system services

[Handbook home](../README.md) · [Complete contents](../table-of-contents.md) · [Coverage and verification](../coverage.md) · [Historical coverage audit](../coverage-audit.md)

The initial pass expanded all nine areas requested after the independent review. It added **30 implementation companions**, deepened related existing chapters, and connected them through subsystem reading routes. The [audit-priority follow-up](#10-audit-priority-follow-up) adds nine companions and extends descriptor/Skywalk lifecycle coverage after reconciling the older audits against those additions. The [netif, flow lookup, authorization and ARM64 memory batch](#11-netif-flow-lookup-authorization-and-arm64-memory) adds seven further companions. The [packet-transformation, filtering, IPC and logging batch](#12-packet-transformations-filtering-ipc-internals-and-logging) adds six companions and expands live namespace growth in place. The source target remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`, under the read-only `xnu/` directory. New architecture-specific work covers ARM64; x86 and KDP are excluded.

The purpose is broad, useful first-release coverage. Each companion follows concrete operations, state, ownership, decisions and failure/cleanup, with source citations, exact excerpts and editable diagrams. The remaining scopes below identify further depth and unavailable providers; they do not replace the new explanations with a planning survey.

The latest [two-batch expansion](#22-executable-memory-synchronization-packet-policy-and-build-selection) adds executable-memory, semaphore/eventlink, work-interval, flow-diversion and ARM64 build/MIG companions, and deepens PF/IPsec in place. Further debugger and kperf expansion is deferred by request.

## 1. Network layer below TCP

| Chapter | Mechanisms expanded |
| --- | --- |
| [Internet PCBs, port allocation and lifetime](../subsystems/networking/internet-pcbs-ports-and-lifetime.md) | Socket/PCB identity, hash lookup, bind/connect and ephemeral ports, wanted references, stop-using and reclamation |
| [UDP send, receive and errors](../subsystems/networking/udp-send-receive-and-errors.md) | Datagram construction, endpoint selection, protocol output, input demultiplexing, receive-buffer ownership, errors and teardown |
| [IPv6 output and neighbor discovery](../subsystems/networking/ipv6-output-and-neighbor-discovery.md) | Output decisions, route/interface handoff, neighbor state and held packets, resolution and transmission |
| [Mbuf allocation caches and pressure](../subsystems/networking/mbuf-allocation-caches-and-pressure.md) | Allocator configuration, storage classes, caches, packet/external storage ownership and pressure/reclamation |
| [Kernel control sockets and network statistics](../subsystems/networking/kernel-control-sockets-and-network-statistics.md) | Controller registration, connection/callback lifetimes, data queues, statistics providers, sources and asynchronous reporting |

The TCP and socket chapters remain prerequisites for transport/socket relationships. Follow-up depth includes every TCP loss/congestion algorithm, multicast and routing variant, packet filter, control provider and driver backend. The new chapters explain the selected common protocols without claiming all network algorithms have been audited.

## 2. Skywalk memory and packets

| Chapter | Mechanisms expanded |
| --- | --- |
| [Memory arenas, regions, caches and mappings](../subsystems/networking/skywalk-memory-arenas-and-mapping.md) | Region geometry, allocation caches, segment backing, memory descriptors, arenas, per-task mapping and redirected/revoked backing |
| [Packets, buflets and packet pools](../subsystems/networking/skywalk-packets-buflets-and-pools.md) | Packet/quantum metadata, buflet and buffer relationships, pool allocation, cloning/freeing, user/kernel ownership validation and device-facing mappings |

These extend [Skywalk lifecycle](../subsystems/networking/skywalk-lifecycles.md) and start with the memory/packet foundation of the existing [whole-Skywalk program](processes-vfs-networking.md). Local `IOSkywalkSupport` mapping bodies are included. The original 13-track program remains active: these two companions do not establish complete coverage of every flowswitch policy, netif adapter, scheduler, filter, protocol and provider.

## 3. Synchronous Mach IPC

The new [synchronous dependencies and special reply ports](../subsystems/ipc/synchronous-dependencies-and-special-replies.md) companion traces reply-port binding, destination and workloop inheritance, knote stashing, reset, interruption and death. It separates scheduler dependencies from request routing and reply capability ownership.

Existing chapters now expand [strict reply contexts and port-label substitution](../subsystems/ipc/guards-and-policy-enforcement.md), [trailers and delayed message reaping](../subsystems/ipc/message-path.md), and [send/receive completion](../subsystems/ipc/message-send-receive.md). These are connected mechanisms with distinct entry points; general copyout policy and destruction are not confined to synchronous RPC.

Further work can follow additional workloop races and external client-library behavior. Missing generated stubs or userspace dispatch implementation are not reconstructed.

## 4. Compressor, shared cache and reclamation

| Chapter | Mechanisms expanded |
| --- | --- |
| [Compressor segments and swapfiles](../subsystems/vm/compressor-segments-and-swapfiles.md) | Segment allocation/state, slot relocation, minor/major compaction, worker continuations, swapfile creation, trimming and GC |
| [Shared regions and transforming pagers](../subsystems/vm/shared-regions-and-transforming-pagers.md) | Region identity, exec placeholder, submap installation, file/slide mapping, dyld/shared-region pager faults, validation provenance and lifetime |
| [Deferred reclamation](../subsystems/vm/deferred-reclamation.md) | Shared-ring producer/consumer protocol, cancellation, range actions, accounting, drains and task lifetime |
| [Purgeable memory](../subsystems/vm/purgeable-memory.md) | Object states, old-state results, queues/tokens, aging and purge/reclamation |
| [Phantom cache and refault history](../subsystems/vm/phantom-cache-and-refaults.md) | Eviction-history records, refault matching, pressure sampling and configuration-specific policy use |

[Object/page lifetime](../subsystems/vm/objects-and-pages.md) also expands termination and reaping details. The source's configuration boundaries matter: phantom-cache pressure participation is not universal on macOS ARM64; shared-cache transformation does not expose all userspace dyld policy; compressor algorithms and every freezer/product combination remain additional depth.

## 5. Diagnostic artifacts

| Chapter | Mechanisms expanded |
| --- | --- |
| [Stackshot and kcdata](../development/stackshot-and-kcdata.md) | Admission, buffer estimation/retry, stopped-CPU parallel work, typed/padded records, assembly and publication |
| [Corpses and process core files](../development/corpses-and-process-core-dumps.md) | Admission slots, full/lightweight artifacts, task/port lifetime, process-map selection, Mach-O file layout, partial writes and cleanup |
| [ARM64 panic coordination and records](../development/panic-coordination-and-records.md) | Per-CPU state, owner selection, SPTM boundary, CPU acknowledgments/fallback, bounded panic region, extensible data and checksum/platform synchronization |

KDP protocol and kernel-core transport are outside scope. Common stackshot/panic helper names can contain historical `kdp_` identifiers; their appearance does not add a debugger-transport expansion. Crash reporting, symbolication, firmware retrieval and concrete hardware persistence remain external or separate.

## 6. Process-local IPC and terminals

| Chapter | Mechanisms expanded |
| --- | --- |
| [Pipes and UNIX-socket rights](../subsystems/processes/pipes-and-unix-socket-rights.md) | Circular buffers, atomic/partial writes, blocking/readiness, close and unreachable descriptor-right cycles |
| [User-lock wait and wake](../subsystems/processes/user-lock-wait-and-wake.md) | Keys, expected values, owners, turnstile waits, wake selection, interruption and final cleanup |
| [POSIX named IPC](../subsystems/processes/posix-named-ipc.md) | Semaphore and shared-memory names, descriptors, underlying objects, mappings, unlink and final release |
| [System V IPC](../subsystems/processes/system-v-ipc.md) | Message queues, semaphore operation arrays/undo and shared-memory attachments/exit |
| [TTY and PTY lifetime](../subsystems/processes/tty-and-pty-lifecycle.md) | Master/slave and line discipline, input/output queues, canonical and timed reads, job control, hangup and close |

Configuration guards select facilities. Userspace pthread/libc policy and serial-device hardware are separate from the local syscall/TTY machinery.

## 7. VFS metadata and associated state

| Chapter | Mechanisms expanded |
| --- | --- |
| [Metadata and extended attributes](../subsystems/vfs/metadata-and-extended-attributes.md) | Attribute masks, vnode attributes, variable result offsets, setters/bulk enumeration, xattr dispatch and default-provider handoff |
| [Advisory locks and leases](../subsystems/vfs/advisory-locks-and-leases.md) | Range/owner models, conflicts, splitting/merging, waits, deadlock checks, close and lease breaks |
| [Filesystem event queues](../subsystems/vfs/filesystem-event-queues.md) | Event production/coalescing, watcher rings, references, overflow/drop markers, reads and close |
| [Compressed file data](../subsystems/vfs/compressed-file-data.md) | decmpfs headers/cnodes, provider selection, read/pagein, conversion and UPL completion |
| [Quota cache and filesystem boundaries](../subsystems/vfs/quota-cache-and-filesystem-boundaries.md) | Quota-file/dquot identity, cache references, dirty/free queues, synchronization and dispatch |

Concrete APFS metadata and quota accounting are not present. The default AppleDouble route in this snapshot includes an external `doubleagentd` handoff; decmpfs has local infrastructure and some local handling but separate format providers. Those boundaries are explained where the calls occur.

## 8. ARM64 platform fundamentals

[ARM64 user-memory access](../subsystems/platform/arm64-user-memory-copy.md) connects `copyin`, `copyout`, strings and atomic values to map/range validation, PAN/MTE access selection, assembly recovery tables, VM fault resolution, saved-register changes and error epilogues. Worked partial-copy reasoning explains why an error does not imply that the destination is unchanged.

The chapter builds on existing exception entry/return and pmap material. No x86 expansion was performed.

## 9. Loading, serialization and NVRAM

| Chapter | Mechanisms expanded |
| --- | --- |
| [Kernel collections and OSKext lifetime](../subsystems/drivers/kext-loading-and-unloading.md) | ARM64 boot/deferred collection ingestion, dependencies, load/start/matching, class pins, stop/unload and autounload |
| [Serialization and property transport](../subsystems/drivers/serialization-and-property-transport.md) | Legacy/XML/binary parser families, graph identity, temporary ownership, indexed-format boundaries and registry receiver policy |
| [NVRAM variables and persistence](../subsystems/drivers/nvram-variables-and-persistence.md) | GUID/name/type/permission handling, V3/CHRP representations, pending updates, append/invalidate, bank rebuild, sync and controller boundary |

The explanations distinguish parser acceptance from authorization, module metadata from executable availability, and a successful property update from durable hardware storage. Collection construction, boot authentication, external load policy and concrete firmware/controller behavior remain separate.

## 10. Audit-priority follow-up

The next batch follows mechanisms still shallow after the initial expansion. Chapter boundaries follow the operation being explained: descriptor races stay in the existing descriptor chapter, and channel synchronization stays in the Skywalk lifecycle chapter. Control-plane lifetime, readiness, memory transfer, clock publication, measurement, settlement, billing and suspension each have distinct state and completion rules, so they receive companions linked from the introductions.

| Reading route | Expanded mechanism |
| --- | --- |
| [Skywalk controllers, providers and ports](../subsystems/networking/skywalk-controller-provider-and-port-lifetime.md) | Controller file lifetime, provider/domain-provider identities, registration/removal, nexus-port binding/admission and publication/cleanup |
| [Channel ABI and readiness](../subsystems/networking/skywalk-channel-abi-and-readiness.md) plus [lifecycle](../subsystems/networking/skywalk-lifecycles.md) | Request conversion, channel/schema/slot coordinates, publication, synchronization, low-water checks, select/kqueue notification, event ownership and defunct teardown |
| [VM copy-overwrite and remap](../subsystems/vm/copy-overwrite-and-remap.md) | Entry streaming, substitution versus page copying, fault/COW revalidation, changed prefixes on failure, remap extraction/reservation and worked mixed-granule adjustment |
| [ARM64 clocks and commpage](../subsystems/runtime/clocks-and-time-domains.md) | Counter/base reads, tick conversion, absolute/continuous/calendar domains, sleep reconciliation and userspace snapshot publication |
| [Recount and resource attribution](../subsystems/runtime/recount-and-resource-attribution.md) | Counter deltas, per-owner track topology, execution levels, sequence readers, work intervals, task exit and coalition aggregation |
| [Ledger limits and settlement](../subsystems/runtime/ledgers-limits-and-settlement.md) | Template/entry state, credits/debits, balance limits, refill, AST callbacks and blocking/wakeup |
| [Bank accounts and charging](../subsystems/ipc/bank-accounts-and-charging.md) | Voucher-derived payer/worker roles, made counts, adoption, scheduler billing, account settlement and detached-task lifetime |
| [Descriptor allocation, replacement and close](../subsystems/processes/descriptors-ipc.md), expanded in place | Slot reservation/growth, construction/publication, `dup2` restart and replacement, I/O reference drain, guard predicates and fileport cleanup |
| [Task and thread capabilities](../subsystems/security/task-and-thread-capabilities.md) | PID acquisition, flavor compatibility, policy gates, MIG input/output ownership, lazy ports, reset/no-senders and identity tokens |
| [Suspension, stopping and abort](../subsystems/runtime/suspension-stop-and-abort.md) | Nested holds, legacy versus token-based suspension, abandoned-token notifications, PID suspension, stop waits and safe abort |

At the end of that follow-up, netif scheduling, namespace/datapath algorithms, ACL evaluation and ARM64 MTE/bootstrap remained priorities. The next batch below addresses those selected paths. Network policy/transport algorithms, Skywalk filters/offloads, logging and remaining SMR/symbol-table and power-policy details still need expansion. The older reports retain their baseline findings; current reading routes identify which proposed mechanisms now have explanations.

## 11. Netif, flow lookup, authorization and ARM64 memory

This parallel batch adds seven implementation companions. Existing lifecycle chapters remain the source for channel synchronization and flow teardown; the new network chapters explain registration identities, lookup, packet processing, netif servicing and interface scheduling as distinct operations. ACL decisions build on pathname and credential explanations. MTE tag backing and boot-time memory allocation have separate state models from ordinary object/page lifetime and pmap translation, so they receive companions linked from those chapters.

| Companion | Paths and decisions added |
| --- | --- |
| [Skywalk namespaces and flow lookup](../subsystems/networking/skywalk-namespaces-and-flow-lookup.md) | Flow-request preparation; BSD/Skywalk address/port conflict accounting, ephemeral allocation, withdrawal/half-close; protocol reservations and flow IDs; normalized/masked keys, cuckoo lookup/publication, parent-child demux, retained-entry lifetime and installation unwind. |
| [Flowswitch classification, routes and packet delivery](../subsystems/networking/skywalk-flowswitch-classification-routes-and-datapaths.md) | Header/buflet bounds, RX fallback versus TX rejection, shared route cache and event references, source choice, ARP/ND ownership, partial pool allocation/copy, per-flow RX worker ownership, ring publication, host fallback and route reaping. |
| [Netif logical links, queues and servicing](../subsystems/networking/skywalk-netif-links-queues-and-scheduling.md) | Link/qset/queue identities and references, initialization unwind, selection, native/compat host/device paths, provider enqueue/dequeue, ring refill, doorbells, polling/mitigation, low-latency servicing and teardown boundaries. |
| [Interface packet scheduling and FQ-CoDel](../subsystems/networking/interface-packet-scheduling-and-fq-codel.md) | Shared mbuf/Skywalk representation, new/legacy scheduler selection, service classes/groups, per-flow queues, deficit scheduling, delay/drop/ECN decisions, pacing/TBR eligibility, ACK compression, return/drop ownership and deferred flow-control feedback. |
| [VFS permissions and ACL evaluation](../subsystems/vfs/permissions-and-acl-evaluation.md) | Action expansion, provider-opaque authorization, mount restrictions, ordered ACE evaluation, GUID/group matching, residual POSIX rights, delete/sticky-directory rules, creation inheritance, filesec copying, partial metadata fallback and cleanup. |
| [MTE tag storage and page lifetime](../subsystems/vm/mte-tag-storage-and-page-lifecycle.md) | Cell/page geometry, activation publication, tagged free-page accounting, same-CPU deactivation barriers, claimed-page relocation, lock revalidation, PINNED retries, compressor borrowing and page-tag preservation. |
| [ARM64 bootstrap memory and lockdown](../subsystems/platform/bootstrap-memory-and-lockdown.md) | Legacy-built versus SPTM-adopted roots, VA/PA cursors and stolen pages, descriptor/bootstrap publication, initial mappings, stack replacement, aliases/static frees, deferred reuse and integrity/monitor finalization. |

Independent reviews compared packet ownership, resolver results, queue return/drop conventions, route registration order and cache retention to source. ACL review checked ordered decisions, delete semantics and inheritance. VM/platform review checked activation/retype/publication, deactivation barriers, claimed-page relocation/retries, bootstrap descriptors and deferred release. Exact excerpts and worked examples expose the consequential branches: an accepted packet can return congestion feedback; pending neighbor resolution can have no buffered mbuf; a failed flow registration can leave a tree-held route; retained tagged state does not mean available taggable capacity.

At the end of that batch, fragment/reassembly and aggregation algorithms, tracking/GSO, netif filter/agent/reinjection machinery, logging and IPC namespace/readiness remained gaps. Section 12 addresses those selected paths; broad diagnostics/test matrices, full network policy engines and remaining provider combinations still need work. APFS ACL persistence, external identity policy, device DMA/firmware behavior and monitor-internal enforcement are explicit implementation boundaries. Source tests were inspected where relevant; no kernel was built or executed.

## 12. Packet transformations, filtering, IPC internals and logging

This batch continues the whole-Skywalk plan and fills two remaining Mach IPC foundations and the logging mechanism gap. Four packet companions distinguish retaining fragments, observing transport state, combining or splitting packet representations, filtering and control-rule publication. Port-set readiness has its own link/wait protocol; live namespace growth extends the existing names-and-rights chapter. Logging receives one companion that connects its locally implemented producer and buffer paths while marking the missing central Firehose manager.

| Chapter | Added mechanisms |
| --- | --- |
| [Skywalk fragments, reassembly and flow tracking](../subsystems/networking/skywalk-fragments-reassembly-and-flow-tracking.md) | Fragment keys/queues, ordering and overlap checks, original-packet chain completion, limits/timeouts, passive TCP/UDP tracking, close/linger and abort construction. |
| [TCP aggregation, segmentation and offloads](../subsystems/networking/skywalk-tcp-aggregation-segmentation-and-offloads.md) | Aggregation eligibility, retained payload/header/checksum representation, default versus accelerated receive, flowswitch/native-netif segmentation, copied output ownership, metadata/QoS and steering-install rollback. |
| [Netif filters and reinjection](../subsystems/networking/skywalk-netif-filters-and-reinjection.md) | Native/compat admission, read-only views retaining originals, filter traversal/progress, kernel callback versus virtual-port ownership, reinjection, disabled/drop paths and removal reference drains. |
| [Netif agents and traffic rules](../subsystems/networking/skywalk-netif-agents-and-traffic-rules.md) | Agent lifecycle and flow/port identities, request admission, INET/Ethernet rule objects, UUID/descriptor ownership, publication/matching, provider notifications and cleanup. |
| [Port sets and persistent readiness](../subsystems/ipc/port-sets-and-waitq-readiness.md) | Two-way membership links, ordinary/preposted lists, direct waiter selection, lazy readiness clearing, set-to-port lock ordering/revalidation, knote notification and invalidation/unlink. |
| [Names and rights](../subsystems/ipc/names-and-rights.md), expanded in place | Hold/claim capacity, pure-send reverse hashing, live-table unlocked copy and changed-index rescans, free-list repair, publication/SMR retirement, termination, lock-state contracts and deferred resource reports. |
| [Kernel logging and Firehose](../development/kernel-logging-and-firehose.md) | Text/binary/live fanout, identity/format encoding, logmem allocation, per-CPU copied retry entries, publication and deferred cleanup, chunk inline operations, read-only mapping/feedback, stream reservation/cache/read, msgbuf replay and dmesg. |

The chapters use worked state/representation examples and distinguish accepted work from completed delivery: a set prepost is not another message queue; reassembly can preserve separate original packet headers; a filter view can retain an original packet whose bytes are reinjected; rule publication can precede a failed provider notification; logging retry acceptance is not persistence. Comments that disagree with the inspected body are identified at the relevant branch rather than repeated as implementation facts.

Independent cross-reviews checked fragment ownership, queue limits and transport observation; aggregation/segmentation allocation, checksums and copied output; filter callback references, original-packet retention, processed queues and rule publication; logging retry ownership, stream reservations and reader lifetime. Coordinating source review checked port-set preposts, set-to-port lock revalidation, live-table rescans and resource-limit reporting. The logging review also distinguished the visible chunk helpers and device integration from imported Firehose manager bodies that are absent here. These are selected source-path checks, not exhaustive concurrency proofs.

At the end of this batch, remaining candidates included NECP client/policy and socket content-filter machinery, BSD transport recovery/congestion algorithms, route/multicast control, the complete Skywalk diagnostics/configuration/test matrix, remaining provider variants, lock/SMR-hash internals, personas/audit sessions and power-policy assertions. Section 13 follows the policy, identity and hash-table candidates. The local Firehose integration does not supply its imported buffer manager or userspace decoders/persistence. Hardware/AOP/firmware, secure-domain services and userspace policy providers remain explicit external boundaries. No kernel or daemon tests were executed.

## 13. Network policy, identity and shared lookup lifetimes

This batch adds seven companions. NECP rule compilation and matching have a different ownership model from the client/result/flow objects that consume policy, so they have separate chapters. Socket content filtering follows original mbufs, inspection copies and pass offsets through its own control protocol. Persona membership, external group resolution and audit-session capabilities extend the credential reading route. Generic SMR hash algorithms and the concrete `OSSymbol` pool also remain separate: array publication and grace periods do not establish a client's reference or string-storage lifetime.

| Chapter | Added mechanisms |
| --- | --- |
| [NECP policy compilation and evaluation](../subsystems/networking/necp-policy-evaluation.md) | Policy-session admission, staged TLV ownership, ordering and derived socket/IP rules, incremental apply/removal, lookup maps, accumulated versus terminal results, cache generations and packet policy tags. |
| [NECP clients and flow registration](../subsystems/networking/necp-clients-and-flow-registration.md) | FD/client/registration/flow identities, creation and claim, result reevaluation and notification, socket/nexus assignment, observer copies, action-specific partial progress and close ownership. |
| [Socket content filtering](../subsystems/networking/socket-content-filtering.md) | Filter attachment/control messages, byte coordinates and record queues, pass/peek decisions, inspection copies, reinjection/backpressure, stream versus datagram lifetime, disconnect, close waits and garbage collection. |
| [Personas and membership resolution](../subsystems/security/personas-and-membership-resolution.md) | Persona registry publication and invalidation, spawn adoption/drop, process accounting versus credentials, voucher identity boundaries, positive/negative membership caches, identity translation and external-resolver queues/results/timeouts. |
| [Audit-session capabilities](../subsystems/security/audit-session-capabilities.md) | Session identity and credential/process accounting, lazy port export, send epochs and no-senders, self/join/spawn inheritance, masks, reference release and distinct session END/CLOSE events. |
| [SMR hash tables](../cross-cutting/smr-hash-tables.md) | Traits and reference acquisition, duplicate insertion, serialized-writer growth/shrink and chain repair, scalable stop markers and bucket migration, resize/reseed triggers, grace periods and table versus object teardown. |
| [Symbol interning](../subsystems/drivers/symbol-interning.md) | Ordinary hash versus huge-symbol lookup, candidate publication and loser cleanup, copied/borrowed/permanent backing, final-release unlink and deferred cleanup, module-unload string replacement and dictionary integration. |

Worked examples follow a policy change into cached socket state, byte offsets through content-filter queues, persona identity alongside process credentials, an audit-session capability across join, a hash chain through a bucket split, and symbol acquisition across concurrent creation. The chapters identify implementation limits at the branch concerned: failed output copying need not undo an earlier registration or publication; inspected filter data is not thereby permitted to pass; a dead symbol can remain allocated for SMR readers.

Independent source reviews checked content-filter whole-record pass/peek, consumed reinjection, retry/accounting and close/GC predicates; serialized/scalable hash migration and grace-period ordering; symbol acquisition, duplicate cleanup, backing replacement and final release. Coordinating review checked persona publication/adoption/drop and resolver responses, audit-session masks/counts/lazy-port reference transfer and join/removal, and NECP apply/publication/result-copy failure paths. Review refined the datagram GC shortcut to include its cached-entry predicate and clarified that SMR-safe symbol destruction can occur synchronously in a rare allocator fallback. These checks cover named paths, not every interleaving or configuration.

Remaining expansion candidates include BSD transport recovery/congestion algorithms, route/multicast control, the complete Skywalk diagnostics/configuration/test matrix and paired-pipe/provider variants, flow-divert/MPTCP and deeper PF/IPsec state, trust-cache/csops/CSR controls, trace consumers, DTrace/sanitizers, remaining lock internals and power-policy assertions. The new policy chapters cover selected local mechanisms, not every policy condition/action composition or external policy daemon. Resolver databases, filter agents, protected policy providers and hardware remain external. Configuration and concurrency limits are stated in each companion.

The next bounded batch should prioritize these distinct mechanisms. These are proposals, not completed coverage:

| Priority | Proposed scope and chapter placement |
| --- | --- |
| 1 | TCP ACK/SACK holes, RACK loss timing and a worked congestion-recovery algorithm: a companion to [TCP connection/timer lifetime](../subsystems/networking/tcp-connections-and-timers.md), retaining that chapter's existing role. |
| 2 | Skywalk user/kernel pipes: a paired-ring ownership and teardown companion to [controller/provider lifetime](../subsystems/networking/skywalk-controller-provider-and-port-lifetime.md), separate from BSD pipes and flowswitch transport. |
| 3 | Kdebug storage and consumer readout: a companion to [observability](../development/observability.md) for publication, timestamp merging, loss markers, recycling and partial output. |
| 4 | Trust-cache frontends, `csops` and CSR: a signing-control companion to [code signing](../subsystems/security/code-signing.md), reusing the existing protected TXM path rather than repeating it. |
| 5 | RW, ticket and pointer locks: a mechanism companion to [waits and locks](../subsystems/runtime/waits-and-locks.md), preserving the actual old/new RW build selection and distinct invalidation/wakeup contracts. |
| 6 | Skywalk inspection, guard failures and configuration/test evidence: a focused diagnostics companion under the [whole-surface program](processes-vfs-networking.md#a12--p1-complete-skywalk-expansion-program), with test-to-mechanism mappings and no claim that tests ran. |

Power assertions, preventer sets and idle-policy propagation are the strongest following driver candidate. They need a separate policy-state explanation linked to [system sleep/wake](../subsystems/drivers/system-sleep-and-wake.md), whose transition machinery is already developed.

## 14. MTE mitigation from boot policy to allocation and fault

This requested expansion deepens two existing chapters rather than splitting the same mitigation across more pages. The source target remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`. The earlier physical-tag-storage and bootstrap ownership explanations remain intact, with their major numbered anchors preserved.

| Existing chapter | Added mechanisms |
| --- | --- |
| [MTE tag storage and page lifetime](../subsystems/vm/mte-tag-storage-and-page-lifecycle.md) | Pointer versus allocation tags and finite-granule limits; exec/fork and pmap root policy; tagged object admission, first fault and zeroing; provenance and checked/unchecked aliases; virtual-copy restrictions and physical tag preservation; compressor restoration; zone tag initialization, free/reuse and SMR delay; large allocation/free/realloc differences; packed pointers, trusted bypasses and KASAN distinctions; EL0/EL1 hard/soft faults, copyio recovery, map/IOMD attribution and AST consumption. |
| [ARM64 bootstrap memory and lockdown](../subsystems/platform/bootstrap-memory-and-lockdown.md) | Compile-time capability, release/debug/KASAN policy and static-if patch timing; visible SCTLR/TCR/MAIR controls versus absent monitor programming; per-CPU tag generation and privilege-boundary reseeding; early tagged-zone stealing/relocation; stack coverage limits; secondary, idle-reset and full-resume paths; mutable tag state after lockdown; TCO handling across exception entry and context switching. |

Two writers researched the existing chapter domains while a third agent traced allocator behavior and independently reviewed both drafts. Coordinating research followed process admission, root configuration, synchronous aborts, soft-mode retry and delayed task attribution, then checked their integration with the VM paths. Worked examples distinguish a reused tagged zone element from a reused physical page, a foreign untagged alias from loss of physical tags, and saved compressor tags from tag-storage frames borrowed for compressed bytes.

Review exposed several consequential qualifications. The zone exclusion-mask bits forbid tag values; initial alternating tag sets do not guarantee permanent differences between neighboring elements. Ordinary zone frees retag before reuse, while SMR frees wait for readers. Large shared-data allocation retains `KMA_TAG` in the inspected local branch despite a broader exclusion comment; [the allocation-routing chapter](../subsystems/vm/kalloc-heaps-and-routing.md) was corrected accordingly. The local legacy SCTLR default does not incorporate the separately defined MTE control bundle, so that write cannot establish MTE enablement; SPTM's protected-register setup remains external. Inspected CPU/thread stack allocations omit `KMA_TAG`. Soft mode disables enforcement without discarding stored tags or the task feature, and async guard names describe software-delayed notification of a synchronous hardware tag fault.

The expansion does not establish every shipped configuration, full allocation coverage, a numerical detection probability or a passing hardware test. Production userspace allocators, AMFI decisions supplied by external providers, SPTM internals, firmware and physical tag-array implementation remain explicit boundaries. Selected test bodies were inspected, including disabled and development/SOC-restricted cases; none was executed. The previously proposed TCP, paired-pipe, tracing, trust-control, lock and Skywalk-diagnostic work remains a separate backlog.

## 15. TCP recovery, Skywalk pipes and Kdebug readout

This batch implements the first three priorities listed in section 13, after the requested MTE follow-up. It adds three companions rather than overloading the connection/timer, controller/provider and observability chapters: recovery algorithms have separate state from connection lifetime, pipe transports have separate ownership from flowswitch delivery, and consuming trace readout differs from log buffering.

| Companion | Mechanisms explained |
| --- | --- |
| [TCP loss recovery and congestion control](../subsystems/networking/tcp-loss-recovery-and-congestion-control.md) | Cumulative ACK and send-buffer release, legacy SACK-hole updates and allocation failure, RACK sequence/time indexes and loss evidence, reordering/probe/retransmission timer decisions, recovery entry/output/exit, congestion callbacks and a worked NewReno recovery. |
| [Skywalk user and kernel pipes](../subsystems/networking/skywalk-user-and-kernel-pipes.md) | Endpoint and adapter construction, paired rings and packet-attachment transfer, available capacity and RX-assisted progress, peer references across close/reopen, defunct teardown, kernel-pipe callback dispatch and protected slot-storage lifetime. |
| [Kdebug storage and readout](../development/kdebug-storage-and-readout.md) | Session ownership/configuration, per-CPU storage and record reservation, producer filtering, wrap/steal and loss reporting, coprocessor timestamps, merge barriers, consuming cursor advancement, partial output, recycling and reset. |

Three parallel writers traced the implementations and their local test/configuration evidence, then cross-reviewed another writer's chapter. Coordinating review followed pipe transfer and peer-reference transitions, Kdebug reservation/merge/output failure, and RACK/NewReno decision branches. Review clarified per-ring teardown ordering, successful-provider reference balancing, the Kdebug read horizon's update at successful read completion, and the temporal ordering in its two-CPU example. The TCP worked example distinguishes receipt of out-of-order bytes from delivery to the receiving application. The new chapters link existing explanations for socket/PCB lifetime, generic channel and packet memory, clocks and tracing controls. Source tests are reading evidence; no kernel, network workload, pipe harness or tracing session was executed.

The explanations preserve distinctions that affect failure reasoning. SACK delivery evidence does not release the sender's stream bytes as a cumulative ACK does. RACK transmission records are not the legacy SACK-hole list, and resource exhaustion can change the recovery implementation. User-pipe synchronization swaps descriptors and packet attachments between separate rings; kernel pipes dispatch provider operations. A Kdebug read advances source cursors before output, so a copyout error is not a rollback and the returned count need not report earlier successful output.

At this point the next batch was **trust-cache/`csops`/CSR controls, RW/ticket/pointer locks, and Skywalk diagnostics/configuration/test mapping**, implemented in section 16. Power assertions/idle policy, IP control paths and DTrace follow. Remaining TCP algorithms and ECN/option combinations, all external kernel-pipe providers, trace-consumer tooling and the whole Skywalk failure/configuration matrix remain bounded rather than marked complete by these three companions. x86 and KDP remain excluded.

## 16. Trust controls, lock implementations and Skywalk diagnostics

This batch follows the remaining three priorities in section 13. Five companions preserve useful subject boundaries: trust-cache loading and query storage differ from process signing controls, while RW admission differs from ticket reservation and pointer publication. Skywalk diagnostics spans existing transport and memory mechanisms, so its exporter and test explanation has its own route rather than repeating the datapaths.

| Companion | Mechanisms explained |
| --- | --- |
| [Trust-cache control](../subsystems/security/trust-cache-control.md) | Typed frontend admission, Image4 extraction versus verification, ordinary/PPL/TXM backend selection, retained payloads, runtime locking, duplicate results, query tokens and unload boundaries. |
| [Code-signing process controls and CSR](../subsystems/security/code-signing-process-controls.md) | `csops`/audit-token process identity, command-specific authority and data formats, partial copyout and mutation, process/VM flag effects, ARM64 Device Tree CSR derivation, check semantics and consumers. |
| [Reader/writer locks](../subsystems/runtime/reader-writer-locks.md) | Default legacy versus explicit newer types, state fields, reader/writer/upgrader admission, spin and sleep, waiter publication, wake selection, failed upgrades, downgrade, scheduler accounting and destruction. |
| [Ticket and pointer locks](../subsystems/runtime/ticket-and-pointer-locks.md) | ARM64 ticket reservation and acquisition, preemption, timeouts and invalidation; packed pointer/lock state, queued contention, release publication, value observation and concrete caller lifetime rules. |
| [Skywalk diagnostics, configuration and tests](../subsystems/networking/skywalk-diagnostics-configuration-and-tests.md) | Build/runtime branch selection, diagnostic authority, snapshot sizing and copying, object/counter lifetime, channel failure reporting, trace/log evidence, injection controls and selected harness assertions. |

Three parallel writers traced these areas against the same `xnu-12377.121.6` source. Coordinating research independently followed `csops_internal`, the ordinary trust-cache backend and common frontend, ARM64 CSR initialization, legacy RW upgrade/release, ticket reservation/invalidation, pointer release, and Skywalk nexus/flow exporters. The paths retain distinctions that determine caller behavior: identity validation is not authorization; an error can follow a state change or partial output; a failed RW upgrade can drop ownership; a timed-out ticket reservation cannot simply be abandoned; snapshot storage can be stable while copied counters remain mutually inconsistent.

Each writer also reviewed another area against source. The lock review checked legacy/new selection, waiter publication, upgrade failure, ticket invalidation and pointer/MCS publication. The Skywalk review checked collection/export differences, counter rollover, retained flow statistics, mapped settings and test injection/result policy. The security review checked backend ownership and token handling, process command gates and partial mutation, output formats and ARM64 CSR derivation. Corrections clarify `CLEARPLATFORM`'s early return when no signature blob exists, counter-extrema rollover, separate drop-observation headers and the exact abort-signal helper. Seventeen new diagrams were rendered strictly to standalone SVG and visually inspected; one crowded lock diagram was replaced with a sequence diagram.

Imported TrustCache layouts/type-policy tables, Image4/AMFI validation and protected-monitor behavior remain external boundaries. The local ARM64 CSR body assumes the boot-policy Device Tree node is available for its later property read; its missing-node behavior is not reconstructed as a safe fallback. Skywalk inspection is a source-based map of selected exporter/configuration/test mechanisms, not a completed test campaign or every combination in the whole-surface program. No kernel tests, formal lock model, transport workload or diagnostic session was executed.

The next priorities are **power assertions, preventer sets and idle policy; IP control paths such as routing/ARP/ICMP/multicast; and DTrace instrumentation lifecycle**. Deeper PF/IPsec state, MPTCP/flow-divert transports, sanitizer internals and remaining provider/configuration variants follow. x86 and KDP remain excluded.

## 17. IOKit queue and service protocols and worked operations

This requested batch expands three existing IOKit chapters and adds three cross-subsystem operations. Queue variants belong beside their existing data layouts; catalogue rescans, matching deferrals and notification lifetime belong beside service matching and teardown. The worked operations have separate chapters because they carry one set of addresses, objects or packet slots across several subsystem explanations.

| Chapter | Added mechanisms |
| --- | --- |
| [Shared queues and notifications](../subsystems/drivers/shared-data-queues-and-notifications.md) | Classic byte-ring wrap/full and exact-end cases; payload publication versus wakeup; circular reset scope, generation/cursor mutation and slot identity; DriverKit layout, callback coalescing, backpressure, capacity queries, handler lifetime and cancellation boundaries; concrete test assertions and unchecked failures. |
| [Service matching and termination](../subsystems/drivers/service-matching-and-termination.md) | Partial catalogue insertion, generation/rescan and lock handoff; registration coalescing and late callbacks; module, daemon, power and DriverKit deferrals; category reservations during rematch, replacement predicates, probe/start cleanup and finalization tokens. |
| [Service notifications and arbitration](../subsystems/drivers/service-notifications-and-arbitration.md) | Notification event meanings, replay versus live ordering, concurrent invocation records, self-removal, disable/removal distinctions, ownership across callbacks and the limits of selected concurrency tests. |
| [Mapped file to ARM64 fault](../cross-cutting/mapped-file-to-arm64-fault.md) | A numeric 16 KiB private-file mapping through fd/vnode/UBC ownership, delayed-copy objects, ARM64 entry, pager/UPL completion, map revalidation, pmap/SPTM insertion, private write faults and unmapping. |
| [User buffer to DMA completion](../cross-cutting/user-buffer-to-dma-completion.md) | A client-task range through DriverKit descriptor construction, VM sharing/COW and I/O UPLs, whole-descriptor preparation versus a smaller command interval, mapper/segment coordinates, external device completion, partial failure and final release. |
| [Skywalk channel operation](../cross-cutting/skywalk-channel-operation.md) | Guarded-fd creation and schema publication, arena mappings through IOKit, user versus validated ring cursors, packet attachment transfer, two batches through a full user pipe, readiness-driven progress and close/map/peer lifetime. |

Three parallel writers traced the IOKit variants and two memory operations. Coordinating research followed the Skywalk operation, integrated reading routes and independently checked matching/notifier and mapped-file branches. Cross-reviews checked queue publication/reset/error behavior, file-offset rebasing through delayed-copy and private shadow objects, DMA geometry and cleanup, and channel mapping/publication/readiness/teardown.

The reviews retain several consequential distinctions. Catalogue insertion can make partial progress before an error. Disabling a notifier does not unlink it; removal and callback waiting have separate reference rules. Circular reset can change generation before a later failure. A classic queue regression test ignores failures and therefore does not exercise the wrap case its comment describes. DMA command clearing discards command-completion errors, while outstanding DMA references at final descriptor completion trigger a panic. Channel open reserves its guarded fd before optional key copying, and the inspected wrapper close and mapper-free paths discard particular cleanup results.

The worked examples separate source-observed sequences from illustrative values and adjacent paths. The file example selects ordinary untagged ARM64 memory and the SPTM backend. The DMA example selects 16 KiB VM and device pages without asserting that all mappers use that geometry; returned segments do not submit hardware work or establish device quiescence. The Skywalk example derives its two-batch slot counts from `skt_fullupipe`; readiness is an additional source trace, not an operation executed by that test. Concrete filesystem/mapper/device providers, generated DriverKit dispatch bodies and monitor implementations remain boundaries.

The batch adds **14 diagrams and 19 exact excerpts**. Diagrams were rendered strictly to standalone SVG and visually inspected; source tests were read but not executed. This completes the selected IOKit variants and worked-operation follow-up, not every test/configuration/interleaving or the entire older audit backlog. **Power assertions/preventer sets/idle policy, IP control paths and DTrace instrumentation lifecycle remain the next distinct mechanisms**; deeper KXLD relocation and remaining provider/configuration variants also remain candidates. x86 and KDP stay excluded.

## 18. VM fault, UPL and complex IPC state transitions

This requested expansion follows the most involved ownership and retry paths that remained compressed in the existing VM and IPC explanations. It deepens object/fault and port-lifetime chapters in place, while three companions separate UPL completion, complex-message conversion and importance propagation from their introductory routes. The source target remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`; research covers common code and selected ARM64 paths.

| Chapter | Added depth |
| --- | --- |
| [Objects and pages](../subsystems/vm/objects-and-pages.md) | Delayed-copy reuse/growth/insertion, reverse-lock retry, preservation before source writes, copy-version changes, resident/compressed contents, collapse eligibility and exclusive rewalk, pager/slot transfer, bypass coverage proof and reference handoff. |
| [Fault resolution](../subsystems/vm/fault-resolution.md) | Busy-page/paging/reference ownership through unlocked page-in, top-object/offset and copy-version revalidation, concurrent remap/copy growth examples, resilient-media versus signing admission, COW preparation, private zero-fill and saved-reference transfer. |
| [UPL gathering and completion](../subsystems/vm/upl-gather-and-completion.md) | Whole-object and general IOPL gathering, absent/busy versus wired pages, delayed page work and executable-page admission, direction and fault protection, access-blocking callers, processed-prefix unwind, range commit/abort, vector coordinates, child retirement and failure after partial completion. |
| [Complex message conversion](../subsystems/ipc/complex-message-copyin-and-copyout.md) | Inflation before acquisition, same-name header dispositions, finite-uref examples, OOL VM representation and 16 KiB receive alignment, port-array memory/right ownership, header death ordering, body/final-byte failures and pseudo-receive restoration limits. |
| [Importance propagation and delayed drops](../subsystems/ipc/importance-propagation-and-delayed-drops.md) | Queued-message and inherited-value graph edges, raised bits and assertion counts, port-chain migration, task-policy second-chance locking, delayed request-time cutoff, external-drop commands and task disconnect. |
| [Port and right lifecycle](../subsystems/ipc/ports-and-rights-lifecycle.md) | Fast versus serialized circularity checks, inactive-tail references, circular-message destruction with successful send status, consumed backup registration and old/new transit-destination lifetimes. |

Three parallel researchers traced VM object/fault machinery, UPL acquisition/completion and IPC dependency lifetime. Coordinating work traced complex message/header/descriptor conversions and integrated the reading routes. Independent review checked delayed-copy versioning and lock order, collapse/bypass geometry, resilience recovery identity, UPL gather/unwind/vector ownership, IPC alias/death/pseudo semantics and OOL VM geometry. Coordinating source review separately checked importance counters, delayed-scan comparisons, second-chance locking and transit/backup lifetime.

Several qualifications materially change how to read these flows. Growing a delayed-copy object can require new write preservation without changing its pointer. A page-in result is insufficient to install a translation after the address is remapped. Resilient-media recovery retains the failed top-object/offset pair and revalidates it before private zero-fill; signing resilience is a different flag. An I/O UPL can retain absent/busy pages without ordinary wires, and a vector error can follow retirement of an earlier child. The UPL fast gather visits resident-list order while error cleanup scans a processed offset prefix; the chapter records the unresolved coverage of earlier high-offset fast-path holds without claiming a verified runtime bug.

On the IPC side, header move coordination is not a globally atomic snapshot of independent port deaths. OOL array memory deallocation can precede failure on a later right; receiver rights/mappings can precede a failed final buffer write. Pseudo-receive's wrapper discards that final byte-copy status. Importance graph accounting changes before delayed policy withdrawal, and the delayed scanner compares request timestamps to a shared scheduled cutoff rather than guaranteeing a separate full delay for each task. The port-destroyed backup registration is detached before attempting the recovery message.

The batch adds **15 diagrams and 22 exact excerpts**. Strict standalone SVG rendering and visual inspection cover the new diagrams. Selected source tests identify intended scenarios and limits, including a resilient-media COW signal-helper/comment mismatch; none was executed. Historical audit V7 now has a mechanism explanation. Remaining VM/IPC work includes unreviewed security/configuration combinations, all map/copy aliases and races, complete pager/transpose variants, legacy/watchport paths, external policy/runtime and generated MIG implementations. This is selected deep source review, not a whole-component correctness or concurrency proof. The separate power/IP-control/DTrace backlog remains unchanged; x86 and KDP remain excluded.

## 19. Prioritized review: IP control, power policy and instrumentation

This pass reviewed current subsystem reading routes, existing chapters' stated limits and the residual audit proposals, then inspected selected implementation bodies to choose the next work. It did not reread every line in all 299 starting Markdown pages or certify every cited source file. VM/IPC, pmap, allocation, signing, scheduling, DMA and the main Skywalk paths already have substantial mechanism explanations; repeating those routes uniformly would leave more distinct common operations unexplained. The selected input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`.

### Ranked gaps and chapter placement

| Rank | Gap and reason for priority | Placement and result |
| --- | --- | --- |
| 1 | Routing sockets mutate state used by almost every IP path, but the packet/interface chapter deliberately stopped at cached-route lifetime. IPv4 ARP pending packets, retries and deletion had no complete common-stack explanation. | Added [routing control and IPv4 ARP](../subsystems/networking/routing-control-and-ipv4-arp.md). Kept the existing packet/interface chapter focused and added a bridge. |
| 2 | UDP/TCP depend on receiving complete datagrams and on asynchronous ICMP feedback. Common IP reassembly ownership, IPv4/IPv6 overlap differences and PMTU validation order were not explained by the separate Skywalk reassembly chapter. | Added [IP fragment reassembly and ICMP feedback](../subsystems/networking/ip-fragment-reassembly-and-icmp.md), with UDP/IPv6 links. A single companion compares the two address-family implementations and their error boundary. |
| 3 | Sleep-transition machinery already exists, but readers could not trace the assertion/preventer/settings state that permits or delays a transition. | Added [power assertions, sleep preventers and idle policy](../subsystems/drivers/power-assertions-and-idle-policy.md). The existing sleep/wake chapter links policy inputs without duplicating transition/CPU/hibernate mechanics. |
| 4 | Observability named DTrace without following a consumer from admitted program through an installed provider hook, recording and teardown. Its local implementation provides substantially more evidence than the overview exposed. | Added [DTrace provider and action lifecycle](../development/dtrace-provider-and-action-lifecycle.md), using a concrete ARM64 syscall provider. The observability survey remains the mechanism-selection guide. |
| 5 | Multicast socket state, IGMP/MLD reports and IPv6 router/prefix lifetimes remain distinct from unicast neighbor resolution and route mutation. | The subsequent IPv6 batch in section 20 implements MLD/membership and router/prefix companions plus their configuration, socket and packet-path prerequisites. IPv4 multicast/IGMP remains open. |
| 6 | PF state/NAT and IPsec security-policy/security-association lifetimes remain a dispatch survey; NECP and socket-content filtering do not explain them. | Next security/network batch: separate PF and IPsec mechanism chapters linked from policy extensions. Keep userspace key/policy providers explicit. |
| 7 | Compiler-inserted sanitizer/coverage hooks, runtime metadata and consumer teardown have different ownership from tracing probes. | Next instrumentation batch: sanitizer/coverage companions, linked to allocation/MTE where useful. Distinguish classic/shadow/tagged/configured implementations. |
| 8 | MPTCP and flow-divert add session/subflow or delegated-transport state above ordinary TCP/socket behavior. | Later transport companions after their common prerequisites; avoid duplicating TCP recovery. |
| 9 | kperf action/sampler/buffer completion and remaining power/Skywalk provider/configuration matrices still have untraced combinations. | Extend current chapters when the state holder is already explained; add a companion only for an independent lifecycle. |
| 10 | KXLD relocation/vtable linking is still partial, but runtime applicability depends on `CONFIG_KXLD` and target selection. | Lower-priority source-bound loading companion; do not present configuration-specific legacy linking as every ARM64 kernel's loading path. |

The source-backed residual proposals remain in [networking A8–A11](processes-vfs-networking.md), [driver D4/D5](vm-and-drivers.md), and [diagnostics D4–D6](security-and-development.md). This ranking weighs missing operation coverage, availability of local bodies and usefulness to the current ARM64/common reading route. Missing firmware, external policy/runtime providers and generated artifacts cannot be filled by inventing their internals. x86 and KDP remain excluded.

### What the first four priorities now explain

Routing/ARP follows routing-socket parsing and authority, scoped route creation/deletion/change, notification and reference ownership, pending packet queues, arrival-driven ARP retry, reply completion and separate aging/deadline paths. It distinguishes a failed report from a failed mutation: route state can already have changed when a later allocation or metric operation fails.

IP reassembly follows hash/queue identity, packet versus fragment-descriptor ownership, header and byte-offset transformations, admission, checksum/ECN state, overlap, reconstruction, limits and expiry. It compares IPv4 trimming with IPv6 duplicate handling and retained dirty identities. The ICMP section traces quote validation, borrowed callback parameters, PCB/socket handoff and PMTU side effects. IPv6 route-MTU changes occur before the transport's own quoted-sequence checks. Source tests are classified by their actual operations: the ICMP “fragmented payload” test supplies a truncated quotation, while the HBH regression exercises outbound fragmentation.

Power policy follows kernel assertion IDs before asynchronous installation, manual description/service ownership, combined masks, the separate userspace mask and DriverKit's immediate exclusion counts. It connects those objects to service preventer sets, idle timer/stimulus decisions and coalesced aggressiveness callbacks, with ordering and return-value limitations. A published setting, issued ID or canceled timer is not itself proof of a finished power transition.

DTrace follows registered providers/probes, admitted DOF/DIF, enablings and ECBs, the distinction between ENABLE and GO, ARM64 syscall entry/return, per-CPU action recording, faults/drops, consuming buffer output, STOP and final disable/cleanup. Consumer state and output copying can make progress before an error return; local hooks do not imply that userspace compilers/consumers or every provider implementation were audited.

Three parallel researchers handled routing/ARP, power policy and DTrace; coordinating work handled common IP reassembly/ICMP and integration. Independent cross-reviews check the newly written mechanisms against their source, rather than treating valid links as semantic proof. The four companions add **15 diagrams and 24 exact excerpts**. Exact excerpts, source links and standalone SVG are validated without rebuilding HTML. Final measured additions and check results are in [coverage and verification](../coverage.md#documentation-checks). No kernel/network/power/tracing test is claimed as executed, and the historical inventory remains unchanged.

## 20. IPv6 configuration, packet paths and lifetime

The requested IPv6 batch extends the existing output/ND and common reassembly/ICMP explanations into a connected family reading route. It adds **eight pages**: an overview plus seven mechanism companions. The selected source remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`. No source update or kernel change was performed.

| Placement | What the expanded explanation follows |
| --- | --- |
| [IPv6 guide](../subsystems/networking/ipv6.md) | Reading order, object distinctions, source map, one host operation across configuration/send/receive/teardown, and external/configuration limits. |
| [Addresses, autoconfiguration and DAD](../subsystems/networking/ipv6-addresses-autoconfiguration-and-dad.md) | Interface/address entry points, publication versus unwind, link-local/stable/CGA/temporary generation, tentative/optimistic state, DAD nonce/counters/timers, duplicate regeneration, deadlines, expiry and purge. |
| [Router advertisements and prefixes](../subsystems/networking/ipv6-router-advertisements-and-prefix-lifetime.md) | RA admission and partial option processing, default routers and zero-lifetime distinctions, RIO lists, route installation, L/A bits, advertiser associations, two-hour address rules, on-link/detached transitions and independent deletion. |
| [Scopes and source selection](../subsystems/networking/ipv6-source-selection-and-scopes.md) | External/embedded/separate zones, explicit/bound/ranked source paths, ordered preferences, prefix/router lock-drop restart, policy labels, cache invalidation, borrowed routes and retained address/interface results. |
| [Sockets and packet options](../subsystems/networking/ipv6-sockets-and-packet-options.md) | Native/mapped dispatch, scoped bind/connect and ephemeral port publication, option allocation/copy/validation, unlocked UDP output and receive controls, wanted holds, raw and datagram ICMPv6 admission. |
| [Input and forwarding](../subsystems/networking/ipv6-input-extension-headers-and-forwarding.md) | Family/protocol registration, mbuf/offset representation, local/forward decision, Hop-by-Hop and extension dispatch, supported routing-header boundary, quoted errors, scopes, hop limit, MTU and ownership. |
| Existing [output/ND chapter](../subsystems/networking/ipv6-output-and-neighbor-discovery.md), expanded in place | Header-copy/merge ownership, PMTU/link-MTU distinction, checksum and offload predicates, numeric three-fragment example, packet-list replacement and cleanup. Retains the end-to-end ND hold/resubmit primer. |
| [Neighbor messages and reachability](../subsystems/networking/ipv6-neighbor-messages-and-reachability.md) | Kernel/raw ICMP audiences, NS/NA validation and cache learning, flags/override matrix, generated messages, NUD/passive reachability, route/timer ownership and redirects. |
| [Multicast membership and MLD](../subsystems/networking/ipv6-multicast-membership-and-mld.md) | Socket versus aggregate filter state, INCLUDE/EXCLUDE counters, join/leave and partial failure, MLDv1/v2 queries/compatibility, report construction, timers, output commit/queues, receive fanout, loopback and delayed leave release. |

These boundaries were chosen by state owner and operation. Address publication/DAD and received router/prefix lifetime use related objects but different admission and teardown; they justify separate chapters. Source/scope selection and socket-option interpretation deserve companions because output callers depend on their references and representation choices. The original output chapter remains the home of packet construction/fragmentation, and the existing shared reassembly chapter remains the home of fragment queues and PMTU feedback. No parallel replacement of those explanations was added.

### Source-specific findings retained in the text

The chapters distinguish setter acceptance from working output: this tree can store a validated type-0 routing-header option but rejects packets containing a routing header. Policy-table add/delete ioctls end in `ENOTSUP`. Ancillary option copying omits two initialized scalar policy fields, and later parse errors do not establish a universal cleanup guarantee in the inspected UDP caller. These are bounded observations of the bodies, not runtime bug reproductions.

Address lifetime macros use absolute uptime deadlines despite historical duration-oriented comments. RA zero-lifetime behavior differs for eligible default routers, ineligible bookkeeping and RIO entries. Router associations, prefix objects, routes and derived addresses have independent lifetime rules. The ND option-count limit can stop parsing with success; it is not automatically malformed-input rejection. Neighbor admission failures can still reach raw observers in selected paths, while failure to copy for both consumers can favor kernel handling over observation.

MLD socket filters and interface aggregates have separate commit clocks. The literal receive EXCLUDE predicate, full-state copyin error labels, leave-result handling and delayed final-report reference path are described without replacing them with a generic idealized transaction. Report state can commit without successful packet transmission. Final-leave retention is conditional on reporting state and a nonzero retransmission budget.

Three parallel researchers handled configuration/RA, input/forwarding/neighbor messages, and multicast/MLD. Coordinating work handled source selection, sockets/options, output and the family guide. Independent cross-reviews checked the other authors' state, locks, ownership, failure labels and numeric examples. The batch adds **25 diagrams and 40 exact source excerpts**. Standalone SVG rendering and visual inspection cover the new diagrams without rebuilding the HTML; global link/excerpt/license results and measured counts are recorded in [coverage](../coverage.md#documentation-checks).

### Remaining scope

IPv4 multicast/IGMP remains the unexpanded portion of the prior multicast proposal. PF and IPsec rule/state/SA lifecycle, MPTCP/flow-divert transport overlays, and deeper tunnel/translation/proxy/configuration variants remain distinct follow-up work. DHCPv6/resolver/router software, concrete NIC/firmware behavior and external providers are not reconstructed from their kernel hooks. This expansion does not claim every IPv6 branch, every standards requirement or concurrent network behavior was tested. In-tree tests were read for their actual assertions; none was executed.

## Integration and verification scope

The subsystem READMEs and existing companion chapters link the new routes. The TOC generator places the chapters beside their prerequisites; the source-reference index and searchable HTML derive from the Markdown. Original text/diagrams retain the handbook's CC BY 4.0 notice, while quoted source retains its upstream terms.

The initial pass included local link/anchor and source-line bounds, exact source-excerpt comparison, strict diagram rendering and the normal book verifier. Selected independent cross-reviews covered diagnostic ownership/publication, module/parser/NVRAM boundaries, synchronous IPC dependencies and shared-region installation. The follow-up batches validate Markdown and standalone SVG without rebuilding HTML, at the user's request. The earlier follow-up reviewed descriptor/capability/suspension lifetime, copy/remap failure and geometry, Skywalk publication/readiness, and clock/accounting ownership; the later batches add the mechanisms in sections 11–22. These are source reviews, not kernel execution or a whole-file concurrency proof. Current counts and completed check results are recorded in [coverage and verification](../coverage.md).

The historical audit inventory was preserved. No citation ratio is presented as a percentage of XNU understood, and no source file under `xnu/` was modified.

## 21. Arguments, identity, integrity, instrumentation and packet state

This source-documentation expansion follows the eight requested priorities in order. It adds twelve implementation companions, retains the existing introductions, and connects them through an [ordered reading route](../reading-guide.md#argument-identity-and-lifetime-paths). The input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`. No kernel implementation changes, vulnerability research, HTML generation or kernel/runtime tests are part of this pass.

| Priority | Companion | Reviewed mechanism |
| --- | --- | --- |
| 1 | [Command dispatch and validation](../interfaces/command-dispatch-and-validation.md) | Outer/nested ioctl copying and BPF dispatch, descriptor retention, selected fcntl state changes, sysctl OID/handler lifetime and output cursors |
| 2 | [VM API argument validation](../subsystems/vm/api-argument-validation.md) | Unsafe wrappers, tag/range/page-size decisions, zero-length control returns, protection compatibility and named-entry admission |
| 3 | [Concurrent-operation walkthroughs](../cross-cutting/concurrent-operation-walkthroughs.md) | VM copy/revalidation after mapping changes, IPC grower/terminator ordering, workqueue callback rearm versus exit/cancel |
| 4 | [External-method call lifecycle](../subsystems/drivers/external-method-call-lifecycle.md) | A real local user-client service, opener/current-caller/memory-owner identities, scalar/structure arguments, selector checks, output, async references and close |
| 5 | [Exec identity and inherited state](../subsystems/processes/exec-identity-and-inherited-state.md) | Set-ID and group predicates, MAC transition/disjointness, IPC inheritance/reset, credential publication, stdio repair and task tokens |
| 6 | [Message integrity and descriptors](../subsystems/ipc/message-integrity-and-descriptor-authentication.md) | Exact signature inputs, early header signing, acquired-prefix cleanup, saved descriptor count, qualified pointers and native/extension relocation |
| 6 | [ARM64 thread-state conversion](../subsystems/security/arm64-thread-state-conversion.md) | Kernel import flags versus user metadata, diversifier choice, pointer replacement/authentication, exception and sigreturn restoration, saved-state signing |
| 7 | [Sanitizer runtime and reporting](../development/sanitizer-runtime-and-reporting.md) | Classic/TBI selection and metadata geometry, allocator hooks, quarantine/fake stacks, suppression and KASAN/UBSAN report disposition |
| 7 | [Coverage instrumentation lifecycle](../development/coverage-instrumentation-lifecycle.md) | Compiler/runtime gates, device/mode/mapping state, per-thread attachment, record reservation, enable flags, detach and close |
| 8 | [BPF capture and filter lifetime](../subsystems/networking/bpf-capture-and-filter-lifecycle.md) | Program validation/replacement, interface/listener lifetime, interpreter capture lengths, buffer rotation, reads and teardown |
| 8 | [PF rules and packet state](../subsystems/networking/pf-rules-states-and-packet-ownership.md) | Rule tickets/staging/swap, retained rule/key/state objects, UDP progression, selected translation, packet ownership and expiry/unlink/free |
| 8 | [IPsec policy and associations](../subsystems/networking/ipsec-policy-associations-and-transforms.md) | PF_KEY admission/status, policy/request/association identities, publication/expiry/reclamation, missing-SA packet ownership, IPv4 ESP transformation and authentication/replay ordering |

### Findings that shape the explanations

- Argument transport and operation validation are separate. The ioctl outer copy precedes fd lookup; BPF copies its pointed-to program separately. Sysctl rejects an oversized next output chunk before copying that chunk, while earlier output can remain visible. Selected fcntl callbacks run after flags have already changed.
- VM zero-length and compatibility paths do not have one universal meaning. A sanitizer can return a control sentinel, normalize a protection request, or record telemetry about an alternative result without replacing the actual error.
- Concurrency is documented through concrete schedules and retained state. A held object/page reference does not prove that the same map entry still exists; waking a namespace waiter does not mean all temporary storage has already been freed; cancel return values and callback quiescence answer different questions.
- Identity and integrity depend on representation and caller-selected policy. IOKit opener identity differs from the current caller; exec's credential and inherited-IPC decisions differ; kmsg signing precedes descriptor acquisition; ARM64 conversion can replace a proposed pointer or retain an unusable authenticated result without reporting the same error as an explicit policy rejection.
- Instrumentation has several enable and lifetime boundaries. A runtime, compiler callback, attached thread and enabled shared buffer are separate prerequisites. Coverage head reservation precedes writing its record. Report-function names and nearby comments are checked against the actual KASAN/UBSAN disposition bodies.
- Packet control publication and lifetime continue beyond an individual call. BPF can retain a listener after tap-enable failure and recycle captured data after a copy error; PF rules can outlive active-list membership through state references, and stopped PF still uses the actual expiry predicate during purge. IPsec has distinct policy and association ownership rather than one generic packet-policy object.

### Scope and verification boundaries

The companions document selected source paths, exact branches, object layouts, synchronization, partial progress and cleanup. The new route does not claim every interface selector, descriptor/layout, concurrency schedule, register flavor, sanitizer compiler transformation, packet protocol/helper or product configuration is covered. Generated MIG output, AMFI/MAC providers, SPTM implementation, concrete DriverKit services, userspace packet-policy/key-management tools and hardware behavior remain external where their bodies are absent.

The generic classic sanitizer backend is compared with ARM64 software TBI; this is not a new x86 exception or platform walkthrough. IPv4 UDP is the worked PF state path, classic BPF is the capture interpreter, and IPsec's selected ESP path is distinct from a proof of every cryptographic transform. Historical A11 and D5 now have concrete companions at this bounded depth; the remaining variants retain their backlog status.

The twelve companions add **35 diagrams and 69 exact source excerpts**. Validation counts and final checks for this batch are recorded in [coverage and verification](../coverage.md#documentation-checks). The historical audit inventory is preserved.

## 22. Executable memory, synchronization, packet policy and build selection

This follow-up addresses the remaining six recommended areas after the reader deprioritized debugger attach/stop/resume and kperf. Two batches split independent mechanisms among three specialist authors and coordinating work. Five new companions and two existing chapters form the [reading route](../reading-guide.md#executable-memory-synchronization-and-packet-policy). The selected input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`.

| Batch | Deliverable | Reviewed source path |
| --- | --- | --- |
| A | New [executable-memory policy](../subsystems/vm/executable-memory-policy.md) | MAP_JIT admission, common/mobile and macOS W+X branches, current/maximum permission, association outcomes, ARM64 faults, SPTM frame types and copy/inheritance boundaries |
| A | New [semaphores and eventlinks](../subsystems/ipc/semaphores-and-eventlinks.md) | Credits versus paired counters, typed capability/reference lifetime, association, combined signal/wait ordering, timeout results, handoff and destruction |
| A | New [work-interval policy and groups](../subsystems/runtime/work-interval-policy-and-thread-groups.md) | Workload loading/default-phase copies, assignment/join ordering, class and effective priority, group resolution, two-thread auto-join and unwind/deferred release |
| A | New [flow diversion](../subsystems/networking/flow-diversion-and-provider-lifetime.md) | NECP protocol replacement, provider/token admission, PCB/group ownership, connect/results, flow credit versus control queues, receive, fallback and teardown |
| B | Expanded [PF rules and state](../subsystems/networking/pf-rules-states-and-packet-ownership.md) | TCP directional peers, sequence/ACK/window arithmetic, worked handshake/data/close, selected loose/proxy branches, same-family NAT/checksum changes and partial progress |
| B | Expanded [IPsec policy and associations](../subsystems/networking/ipsec-policy-associations-and-transforms.md) | IPv6 transport/tunnel stages, given request-chain ordering, packet handoff, old/new association selection and retirement, with parser/ownership boundaries |
| B | New [ARM64 build/MIG walkthrough](../development/arm64-build-and-mig-walkthrough.md) | Illustrative target selection, MASTER/doconf/source/header decisions, Mach VM declaration and build outputs, typed conversion, local read receiver and sanitizer-check limits |

The source distinctions drive the explanations. A successful VM operation need not retain its requested execute bit after association. A semaphore credit differs from an eventlink counter, and combined operations have different lock and result contracts. Workload assignment, effective scheduling policy and the resolved thread group are separate state. Flow-diversion control-queue admission differs from provider receipt or remote delivery. PF can update peer state before packet copyback fails, while an IPsec request-chain error can follow a packet handoff. Build declarations establish inputs and generation contracts without supplying missing generated bytes or external SDK tools.

Independent and coordinating reviews checked each deliverable against its source, including numeric examples, mutation/error ordering and cleanup. Existing introductory routes and exact excerpts were retained. The new diagrams are editable Mermaid with strict standalone-SVG rendering and visual inspection; final navigation, link, excerpt, license and preservation checks are recorded in [coverage and verification](../coverage.md#documentation-checks).

These batches add **20 diagrams and 42 exact source excerpts**.

The focus remains common code and selected ARM64 paths. Deferring debugger and kperf work is a scope choice, not a universal macOS-only availability claim. External MAC/monitor/JIT-runtime policy, performance-controller behavior, flow-diversion providers, key management/crypto providers, complete SYN-proxy reachability, every configuration/interleaving and a shipping product build remain outside the reviewed paths. Tests are inspected as source evidence; no kernel build, runtime/network tests, vulnerability research or HTML generation is part of these batches. The historical audit inventory remains unchanged.

## 23. Exec stacks, executable I/O and scheduler placement

The reader selected the first three follow-ups from the next-depth recommendations. Three authors worked in parallel on separate companions, extending existing subjects through their next operations. The input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`. The [reading route](../reading-guide.md#exec-stacks-executable-io-and-scheduler-placement) connects each companion to its prerequisites.

| Companion | Reviewed operation | Boundary retained |
| --- | --- | --- |
| [Exec arguments and the initial user stack](../subsystems/processes/exec-arguments-and-user-stack.md) | Incoming pointers and argument budgets, interpreter rewriting, kernel string storage, Apple entries, stack allocation/copyout and ARM64 startup state | The worked layout selects a concrete path; optional entries, other ABIs, every exec failure and dyld consumption are not exhaustively covered |
| [Executable pages and UPL I/O](../subsystems/vm/executable-pages-and-upl-io.md) | Read/write direction, executable/debug mapping predicates, temporary copying and padding, recursive gathering, returned data offsets and deferred backing release | The example selects 16 KiB pages and ordinary I/O wiring; monitor/device enforcement and every UPL mode remain separate |
| [Thread-group accounting and cluster migration](../subsystems/runtime/thread-group-accounting-and-cluster-migration.md) | Resolved-group counters and old-group CPU charging, preference publication, running-thread preemption requests, queued-thread draining and requeueing | External performance-controller policy, all topology/binding combinations and complete scheduler interleavings remain outside the selected paths |

The chapters distinguish representations that the earlier introductions only connected briefly. Exec's caller-pointer width and new-image pointer width serve different steps. A temporary kernel mapping can disappear while a UPL activity hold still protects backing. Resolving a thread group changes accounting without queue surgery at that point; an Edge preference change separately publishes placement inputs and can request action for existing work. Source comments, local executable bodies and external contracts are kept distinct.

The batch adds **eight diagrams and thirteen exact source excerpts**. Shared navigation and related chapters link to the new explanations. Documentation verification, source cross-review and diagram results are recorded in [coverage and verification](../coverage.md#documentation-checks). Historical audit measurements and the source inventory are retained.

IPsec virtual-interface lifecycle, MPTCP sessions/subflows and `proc_info` inspection remain future candidates from the recommendation list. The prior debugger and kperf priorities remain deferred. This batch documents source behavior; it does not add vulnerability research, kernel changes, target runtime tests or an HTML rebuild.

## 24. IPsec interfaces, MPTCP and process inspection

This batch addresses the three remaining candidates from the recommendation list following section 23. Separate authors developed three companions in parallel; the [reading route](../reading-guide.md#ipsec-interfaces-mptcp-and-process-inspection) connects them to the existing interface, packet, TCP, process and descriptor explanations. The selected input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`.

| Companion | Reviewed operation | Boundary retained |
| --- | --- | --- |
| [IPsec interface lifecycle](../subsystems/networking/ipsec-interface-lifecycle.md) | Privileged control setup, PCB/interface publication, legacy mbuf and Skywalk paths, interface-selected transforms, inbound delivery and staged disconnect | External key negotiation and service/device providers, every packet/configuration branch and all teardown interleavings remain outside the selected operation |
| [MPTCP sessions and subflows](../subsystems/networking/mptcp-sessions-and-subflows.md) | Session/subflow publication, connection and TCP sequence spaces, data buffering and selection, reinjection, receive ordering, fallback and staged close | Peer behavior, every service-policy/option combination and actual network performance are not inferred from local source |
| [Process inspection and snapshots](../subsystems/processes/process-inspection-and-snapshots.md) | `proc_info` selector dispatch, process identity and access checks, descriptor enumeration, typed detail lookup, references, sizing and copyout | Separate queries are not one atomic snapshot; unreviewed selectors and external MAC policy remain bounded |

The explanations keep several independent events separate. Connecting an IPsec control socket establishes control/interface state rather than a generic packet-injection stream. MPTCP's connection data numbering and retained bytes have a lifetime above individual TCP subflows. A process identity comparison and a descriptor lookup stabilize different objects, and a copied list does not retain those objects for a later query.

The batch adds **nine diagrams and sixteen exact source excerpts**. Shared indexes and related chapters link to the companions. Source cross-review, worked-example verification, standalone diagram inspection and final navigation/excerpt/license checks are recorded in [coverage and verification](../coverage.md#documentation-checks). Earlier measurements and the historical audit inventory are preserved.

These are selected source paths, not exhaustive IPsec, multipath or process-introspection coverage. IPv4 multicast/IGMP, additional protocol/helper/configuration combinations, and external implementations remain separate backlog. Debugger attach/stop/resume and kperf retain their earlier deferred priority. No kernel changes, vulnerability research, kernel/network experiments or HTML rebuild are part of this batch.

## 25. Key structures: proc, task and protected updates

The reader requested a dedicated structure-oriented section, beginning with process/task allocation, access, read-only-zone usage and the writes that update protected state. The [key-structures overview](../structures/README.md) and three companions establish this route separately from the larger syscall and lifecycle walkthroughs. The input remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`.

| Companion | Source operations followed | Boundary retained |
| --- | --- | --- |
| [The process and its protected data](../structures/proc-and-proc-ro.md) | Writable/protected field groups, combined allocation, RO template publication, current-thread and PID access, identity writes, exec replacement and BSD retirement | Selected fields and lifecycle paths; a reference, an allocation hold and a transition wait reference have distinct contracts |
| [The task and its shared RO data](../structures/task-and-shared-ro.md) | Allocation geometry, resource initialization, task/thread/port access, RO attachment and updates, termination and final allocation-hold release | Kernel bootstrap and corpse construction differ from the ordinary shared-RO path; task references alone do not establish a live BSD process |
| [Writing protected object fields](../structures/read-only-object-updates.md) | Concrete copy and atomic setters, macro offsets/sizes, source/destination validation, physical-aperture writes and protected clearing/free | PPL entry, non-PPL legacy ARM, SPTM and disabled enforcement remain distinct; external monitor implementation is not reconstructed |

The structure study distinguishes the writable `proc_task` zone element from the separate `proc_ro` element, and named field groups from independent allocations. Ordinary `proc_get_ro()` and `task_get_ro()` access validates zone identity and a backreference without acquiring a new reference or serializing all field reads. A checked copy remains a copy; an atomic field update protects that operation rather than a whole structure transaction. Final object death, association clearing, SMR retirement and allocator-slot release occur at different points.

The overview and three companions add **nine diagrams and seventeen exact source excerpts**. The new group is registered in the shared TOC/book order and linked from the handbook, architecture, reading guide, process/runtime guides and RO-zone material. Parallel authors and coordinating review trace the selected source paths; final cross-review, diagram inspection and documentation checks are recorded in [coverage and verification](../coverage.md#documentation-checks). Historical measurements and the coverage inventory remain preserved.

This first study does not claim complete structural coverage of threads, credentials, VM, IPC or every process/task field. It adds no kernel changes, runtime tests, vulnerability investigation or HTML build. Further debugger/kperf expansion retains its earlier deferred priority.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
