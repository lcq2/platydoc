# First-release expansion: networking, memory, IPC and system services

[Handbook home](../README.md) · [Complete contents](../table-of-contents.md) · [Coverage and verification](../coverage.md) · [Historical coverage audit](../coverage-audit.md)

The initial pass expanded all nine areas requested after the independent review. It added **30 implementation companions**, deepened related existing chapters, and connected them through subsystem reading routes. The [audit-priority follow-up](#10-audit-priority-follow-up) adds nine companions and extends descriptor/Skywalk lifecycle coverage after reconciling the older audits against those additions. The source target remains `xnu-12377.121.6`, commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f`, under the read-only `xnu/` directory. New architecture-specific work covers ARM64; x86 and KDP are excluded.

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

These additions close the selected audit requests, not the full backlog. Skywalk still needs deeper netif/adapter scheduling, flowswitch policy/protocol paths, filtering and remaining provider combinations. Further independent subjects include ACL algorithms, network policy engines and transport algorithms, ARM64 MTE/bootstrap, logging, and remaining SMR/symbol-table and power-policy details. The older reports retain their baseline findings; current reading routes identify which proposed mechanisms now have explanations.

## Integration and verification scope

The subsystem READMEs and existing companion chapters link the new routes. The TOC generator places the chapters beside their prerequisites; the source-reference index and searchable HTML derive from the Markdown. Original text/diagrams retain the handbook's CC BY 4.0 notice, while quoted source retains its upstream terms.

The initial pass included local link/anchor and source-line bounds, exact source-excerpt comparison, strict diagram rendering and the normal book verifier. Selected independent cross-reviews covered diagnostic ownership/publication, module/parser/NVRAM boundaries, synchronous IPC dependencies and shared-region installation. The follow-up validates Markdown and standalone SVG without rebuilding HTML, at the user's request. Its source reviews cover descriptor/capability/suspension lifetime, copy/remap failure and geometry, Skywalk publication/readiness, and clock/accounting ownership. These are source reviews, not kernel execution or a whole-file concurrency proof. Current counts and completed check results are recorded in [coverage and verification](../coverage.md).

The historical audit inventory was preserved. No citation ratio is presented as a percentage of XNU understood, and no source file under `xnu/` was modified.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
