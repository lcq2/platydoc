# First-release expansion: networking, memory, IPC and system services

[Handbook home](../README.md) · [Complete contents](../table-of-contents.md) · [Coverage and verification](../coverage.md) · [Historical coverage audit](../coverage-audit.md)

The initial pass expanded all nine areas requested after the independent review. It added **30 implementation companions**, deepened related existing chapters, and connected them through subsystem reading routes. The [audit-priority follow-up](#10-audit-priority-follow-up) adds nine companions and extends descriptor/Skywalk lifecycle coverage after reconciling the older audits against those additions. The [netif, flow lookup, authorization and ARM64 memory batch](#11-netif-flow-lookup-authorization-and-arm64-memory) adds seven further companions. The [packet-transformation, filtering, IPC and logging batch](#12-packet-transformations-filtering-ipc-internals-and-logging) adds six companions and expands live namespace growth in place. The source target remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`, under the read-only `xnu/` directory. New architecture-specific work covers ARM64; x86 and KDP are excluded.

The purpose is broad, useful first-release coverage. Each companion follows concrete operations, state, ownership, decisions and failure/cleanup, with source citations, exact excerpts and editable diagrams. The remaining scopes below identify further depth and unavailable providers; they do not replace the new explanations with a planning survey.

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

## Integration and verification scope

The subsystem READMEs and existing companion chapters link the new routes. The TOC generator places the chapters beside their prerequisites; the source-reference index and searchable HTML derive from the Markdown. Original text/diagrams retain the handbook's CC BY 4.0 notice, while quoted source retains its upstream terms.

The initial pass included local link/anchor and source-line bounds, exact source-excerpt comparison, strict diagram rendering and the normal book verifier. Selected independent cross-reviews covered diagnostic ownership/publication, module/parser/NVRAM boundaries, synchronous IPC dependencies and shared-region installation. The follow-up batches validate Markdown and standalone SVG without rebuilding HTML, at the user's request. The earlier follow-up reviewed descriptor/capability/suspension lifetime, copy/remap failure and geometry, Skywalk publication/readiness, and clock/accounting ownership; the later batches add the mechanisms in sections 11–14. These are source reviews, not kernel execution or a whole-file concurrency proof. Current counts and completed check results are recorded in [coverage and verification](../coverage.md).

The historical audit inventory was preserved. No citation ratio is presented as a percentage of XNU understood, and no source file under `xnu/` was modified.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
