# Vocabulary and object index

[Guide index](README.md) · [Architecture](architecture.md)

These definitions describe how to read the terms in this source tree. They are deliberately short; the linked guides explain the actual fields, ownership, and control paths.

## Execution and concurrency

| Term | Meaning in the guides |
| --- | --- |
| `proc` | BSD process object: Unix identity, relationships, descriptors, signals, and lifecycle state. [Process objects](subsystems/processes/lifecycle.md) |
| `task` | Mach resource container with a VM map, IPC space, threads, policy, and accounting. [Runtime objects](subsystems/runtime/objects-and-lifecycle.md) |
| `thread` / `uthread` | Schedulable Mach execution state and its associated BSD state; they do not represent two independently scheduled threads. [Process objects](subsystems/processes/lifecycle.md) |
| `processor_set` | A scheduler domain containing CPU state and queues; its relationship to hardware topology depends on configuration. [Scheduling](subsystems/runtime/scheduling.md) |
| QoS | Quality-of-service classification used by policy and work admission; it contributes to scheduling behavior but is not identical to one fixed numeric priority. [Scheduling](subsystems/runtime/scheduling.md) |
| Base priority / scheduled priority / quantum | Policy-derived priority, the priority currently used for scheduling, and the execution interval assigned by the scheduler. Decay, promotion and quantum accounting have separate update paths. [Priority and quanta](subsystems/runtime/priority-qos-and-quanta.md) |
| RT computation / constraint / deadline | Declared execution budget, permitted completion interval, and the absolute deadline used in real-time queue selection. Their local validation and ordering do not establish system-wide schedulability. [Real-time scheduling](subsystems/runtime/realtime-deadlines-and-runqueues.md) |
| Clutch bucket / bucket group | A scheduling tier within a processor-set hierarchy / shared thread-group accounting used by Clutch selection and interactivity. These are not simply one FIFO per priority. [Clutch and Edge](subsystems/runtime/clutch-and-edge.md) |
| AST | Asynchronous system trap: deferred work requested for an appropriate execution/return boundary, including scheduling and BSD attention. [Signals and exceptions](subsystems/processes/syscalls-signals.md) |
| EL0 / EL1 / EL2 | ARM exception levels: applications, the ordinary XNU kernel context, and a hypervisor context respectively in the paths described here. Hardware entry saves return PC/status in the target level's exception registers; software saves additional context. [ARM64 entry](subsystems/platform/arm64-exception-entry.md), [EL2 boundaries](subsystems/platform/exception-levels-and-monitors.md) |
| User PCB / `arm_context_t` | Persistent per-thread user register state used to resume after a syscall, fault, or continuation; distinct from a kernel stack frame and from a networking PCB. [Entry frames](subsystems/platform/arm64-exception-entry.md) |
| `ERET` | ARM exception-return instruction restoring PC and processor state from the target return registers; distinct from an ordinary function `ret`. [Return path](subsystems/platform/arm64-exception-return.md) |
| PPL / SPTM / GL | Page Protection Layer / Secure Page Table Monitor / Apple guarded-level terminology. Their caller-side interfaces and conditional paths are present, while protected transition bodies are incomplete or external. [Protected execution](subsystems/platform/exception-levels-and-monitors.md) |
| Wait queue | Registration and wakeup machinery for threads waiting on an event. [Waits](subsystems/runtime/waits-and-locks.md) |
| Turnstile | A dependency/priority-inheritance object connecting waiters to an inheritor that can unblock them. [Locks and turnstiles](subsystems/runtime/waits-and-locks.md) |
| SMR | Safe memory reclamation: read-side participation and deferred reclamation protect supported lockless-access patterns. A reader grace period and completion of queued reclamation callbacks are separate obligations. [SMR and publication](cross-cutting/smr-and-publication.md) |
| Workqueue / workloop | Context-dependent names. BSD workqueues supply servicing threads; BSD event workloops manage event/service relationships; IOKit work loops serialize participating driver event sources. [BSD events](subsystems/processes/events-threads.md), [drivers](subsystems/drivers/README.md) |
| Knote | A registered event/filter relationship with its own activation, processing and removal state; consuming or dropping it can precede delivery of the result to userspace. [Kqueue and workloops](subsystems/processes/kqueue-and-workloops.md) |
| Timer call / thread call | Deadline-triggered callback machinery / deferred execution on worker threads, with distinct enqueue, invocation and cancellation protocols. A successful cancellation does not universally mean no callback is running. [Call lifetimes](subsystems/runtime/timer-and-thread-call-lifetime.md) |

## Memory and IPC

| Term | Meaning in the guides |
| --- | --- |
| VM map / map entry | An address space and one of its virtual ranges, with protections and a backing-object or submap relationship. [Virtual address maps](subsystems/vm/virtual-address-maps.md) |
| VM object | Logical backing contents indexed by offset, including resident pages, shadow relationships, and pager state. [Objects and pages](subsystems/vm/objects-and-pages.md) |
| `vm_page` | Metadata for a physical-page representation and its VM/object/queue state; it is distinct from the page's bytes. [Objects and pages](subsystems/vm/objects-and-pages.md) |
| Pmap | The architecture-facing physical-map implementation that manages hardware address translations and related bookkeeping. [ARM64](subsystems/vm/pmap-arm64.md), [x86](subsystems/vm/pmap-x86.md) |
| COW | Copy-on-write: share contents until a write requires private backing, subject to the mapping/object copy strategy. [Fault resolution](subsystems/vm/fault-resolution.md) |
| PTE / table descriptor | A hardware translation-table entry; its level and type determine whether it points to another table or describes a physical mapping. [ARM64 geometry](subsystems/vm/pmap-arm64.md) |
| PV / reverse mapping | Physical-to-virtual metadata that lets pmap start with a physical page and find its installed aliases. [Mapping lifecycle](subsystems/vm/pmap-mapping-lifecycle.md) |
| PTD | ARM page-table descriptor: software metadata associating table storage with its owner and per-table state. Its counters differ between legacy and SPTM implementations. [ARM64 metadata](subsystems/vm/pmap-arm64.md) |
| Translation granule / VM page size | The hardware table-walk unit and the VM system's page unit; a map can also specify its own page shift. Check each layer before computing indices or offsets. [ARM64 geometry](subsystems/vm/pmap-arm64.md) |
| ASID / PCID | Address-space tags used to distinguish cached translations; allocating/reusing tags requires backend-specific coherency rules. [ARM64 activation](subsystems/vm/pmap-tlb-and-cache.md), [x86 activation](subsystems/vm/pmap-x86.md) |
| TLB / shootdown | Cached translations / the protocol that invalidates stale translations on affected CPUs and establishes required completion. [TLB operations](subsystems/vm/pmap-tlb-and-cache.md) |
| Wiring | Residency protection represented at map, physical-page and pmap layers; their counts and lifetimes are distinct. [Wiring](subsystems/vm/wiring-and-memory-entries.md) |
| Memory entry / map copy | A port-backed capability to memory and a kernel representation used for range transfer. A copy representation does not by itself imply an eager byte copy. [Memory entries](subsystems/vm/wiring-and-memory-entries.md) |
| Compressed marker / compressor slot | An invalid PTE's accounting marker and the pager's locator for compressed contents are separate state. [Reclaim and compression](subsystems/vm/reclaim-and-pressure.md) |
| Memorystatus / freezer | Process-level memory-pressure policy and selected task-memory freezing. Candidate selection, VM work, process accounting and later termination or thaw are separate stages. [Pressure and freezing](subsystems/vm/memorystatus-and-freezer.md) |
| Pager | An implementation that supplies or accepts backing contents through the memory-object interface; it need not be a user-space server. [Pagers](subsystems/vm/pagers-and-upl.md) |
| UBC / UPL | Unified buffer cache connects vnode contents to VM; a universal page list carries page-transfer and completion state during I/O. [Pagers and UPL](subsystems/vm/pagers-and-upl.md) |
| Zone / typed allocation | Kernel object-allocation mechanisms backed by VM; allocation placement does not replace C ownership/lifetime rules. [Allocation](subsystems/vm/kernel-allocation.md) |
| Zone magazine / depot | A batch of free elements / inventory holding such batches between CPU caches and a zone. [Zone allocator](subsystems/vm/zone-allocator.md) |
| Kalloc heap view | Routing and accounting information over existing size-class zones; a separate view name need not identify exclusive backing. [Kalloc routing](subsystems/vm/kalloc-heaps-and-routing.md) |
| Type signature / signature equivalence | Compiler-supplied allocation layout and startup compatibility classes used in assignment/free checks; neither is nominal C type identity. [Type isolation](subsystems/vm/typed-allocation.md) |
| Guard object / VA sequestering | VM allocation-slot/guard management and zone address-retention policy are distinct mechanisms with different reuse rules. [VM guards](subsystems/vm/kernel-virtual-allocation.md), [zones](subsystems/vm/zone-allocator.md) |
| Restricted frame / read-only zone | A kernel-private mapping category and storage requiring controlled writes; these enforce different contracts. [Mapping categories](subsystems/vm/allocator-interfaces.md), [RO allocator](subsystems/vm/read-only-and-special-zones.md) |
| IPC space / port name | A task-local namespace and an integer name interpreted through an entry in that namespace. [Names and rights](subsystems/ipc/names-and-rights.md) |
| Port / right | A kernel endpoint object and a capability such as receive, send, or send-once authority referring to it. [Names and rights](subsystems/ipc/names-and-rights.md) |
| Kmsg / OOL | Kernel message representation / out-of-line descriptor data. OOL does not by itself imply zero-copy transfer. [Messages](subsystems/ipc/message-path.md) |
| MIG | Mach Interface Generator: generates client/server boundary code from `.defs` interfaces. [Kernel RPC](subsystems/ipc/kernel-rpc-and-exceptions.md) |
| Kobject | A typed kernel object associated with a port, reached through validated conversions and dispatch. [Kernel RPC](subsystems/ipc/kernel-rpc-and-exceptions.md) |
| Urefs / send rights / object references | User-reference count in a space entry, kernel send-right instances, and allocation-lifetime references are different counts. [Rights model](subsystems/ipc/names-and-rights.md) |
| Mach exception / exception action | A kernel event delivered through an exception RPC, and its registered destination/behavior/state flavor. Hardware faults are one source of these events. [Exception delivery](subsystems/ipc/exception-delivery.md) |
| Voucher | An IPC object containing references to managed attribute values. Transporting a voucher in a message and adopting its attributes on a thread are separate operations. [Vouchers and importance](subsystems/ipc/vouchers-and-importance.md) |
| Port guard / construction policy | Guard-context checks and port-type restrictions applied to selected operations. A guard context is not a replacement for an IPC right. [Guards and policy](subsystems/ipc/guards-and-policy-enforcement.md) |

## Protected execution

| Term | Meaning in the guides |
| --- | --- |
| SPTM | Secure Page Table Monitor: external authority over typed physical frames and protected mapping operations; XNU retains VM, reverse-map and lifetime bookkeeping. [SPTM](subsystems/security/sptm.md) |
| TXM / CSM | Trusted Execution Monitor / common code-signing-monitor interface. CSM selects TXM in SPTM builds; registration, verification, region association and executable mapping are separate operations. [TXM](subsystems/security/txm.md) |
| Frame type / page ownership | Protected physical-frame classification and permitted uses; distinct from a single PTE's permissions or retaining a `vm_page` record. [Frame types](subsystems/security/sptm.md#frame-types-physical-page-policy-distinct-from-a-mappings-permissions) |
| Exclaves / conclave | Exclaves is the secure-execution integration; a conclave resource associates an external domain/manager and lifecycle state with an XNU task. [Resources and task lifecycle](subsystems/security/exclaves-resources-and-memory.md) |
| SCID / host ID | External scheduling-context identifier / XNU compact thread identifier, paired in scheduler messages. Neither is a Mach port name. [Execution context](subsystems/security/exclaves-execution.md#1-the-two-protocols-and-their-storage) |
| Ringgate / Tightbeam | Named secure-entry endpoints and status contract / generated service RPC interfaces and runtime. Their XNU call sites are visible, while substantial transport code is supplied externally. [Execution](subsystems/security/exclaves-execution.md), [services](subsystems/security/exclaves-services.md) |
| Epoch synchronization | Exclaves host wait/wake protocol using external epochs, hashed local wait objects and turnstiles; distinct from SPTM pmap epochs protecting mapping/table observations. [Exclaves waits](subsystems/security/exclaves-execution.md#7-waits-wakes-and-priority-donation), [pmap epochs](subsystems/security/sptm.md#why-an-epoch-is-needed-in-addition-to-a-pvh-lock) |

## Files, networks, drivers, and policy

| Term | Meaning in the guides |
| --- | --- |
| Fd / `fileproc` / `fileglob` | Process-local descriptor number, descriptor instance, and shared open-file object. [Descriptors](subsystems/processes/descriptors-ipc.md) |
| Vnode / mount | Generic filesystem-object state and a mounted filesystem instance. A vnode is not merely a pathname. [VFS objects](subsystems/vfs/vnodes-mounts-and-dispatch.md) |
| Vnode hold / I/O count / use count | Allocation protection, active-operation protection, and persistent-use accounting. Converting a cached pointer into usable vnode state also requires identity validation. [Vnode lifetime](subsystems/vfs/name-cache-and-vnode-reclaim.md) |
| Mount busy / cross-reference | Participation in the mount's operation-versus-unmount protocol / protection while crossing from a covered vnode. These coexist with ordinary and iteration references. [Mount lifetime](subsystems/vfs/mount-lifecycle.md) |
| Compound VNOP | Filesystem operation that combines lookup and a namespace mutation with explicit returned-vnode and retry ownership. It does not imply that every later VFS failure undoes the completed mutation. [Namespace mutations](subsystems/vfs/namespace-mutations.md) |
| Specfs / devfs / FIFO vnode | Device operation dispatch, device namespace construction, and named-pipe vnode operations backed by a socket pair. They provide different parts of the pathname-to-I/O path. [Devices and FIFOs](subsystems/vfs/device-nodes-and-fifos.md) |
| NFS duplicate-request cache | Bounded server-side request/reply state keyed by RPC identity and peer information. It reduces duplicate execution for selected requests without providing a universal exactly-once guarantee. [NFS server](subsystems/vfs/nfs-server-requests.md) |
| `namei` / name cache | Pathname-resolution machinery and cached name-to-vnode relationships, with identity/concurrency validation. [Lookup](subsystems/vfs/pathname-and-authorization.md) |
| `uio` / `buf` | A description of data-transfer buffers/progress and a block/transfer buffer descriptor. They play different roles from VM pages. [VFS I/O](subsystems/vfs/io-and-cache.md) |
| UBC / file-data cache | The vnode-to-VM association and file-object resident pages that can serve reads and mappings. A valid data page is not necessarily signature-checked or executable. [File-data caching](subsystems/vfs/file-data-cache-and-read-path.md) |
| Buffer-cache hit | A matching vnode/logical-block buffer header. Busy ownership, byte validity and metadata-versus-UPL backing remain separate decisions. [Buffer cache](subsystems/vfs/buffer-cache-and-block-io.md) |
| Vnode generation / hold | An identity check against recycling / protection of the vnode allocation's storage. A hold alone does not authorize operations on the filesystem object; the acquisition path must establish the required iocount and identity. [Vnode identity](subsystems/vfs/vnode-cache-identity-and-reuse.md) |
| `cl_writebehind` / DRT | Per-vnode clustered-write tracking / sparse dirty-region tracking. Removing a range from these structures does not itself clean its VM pages or complete storage I/O. [Clustered writeback](subsystems/vfs/clustered-writeback.md) |
| `VNOP_*` / `VFS_*` | Dispatch interfaces for per-vnode operations and filesystem-wide operations. [VFS dispatch](subsystems/vfs/vnodes-mounts-and-dispatch.md) |
| PCB | Protocol control block, such as `inpcb` for Internet endpoint state and `tcpcb` for TCP-specific connection state. [TCP/IP](subsystems/networking/tcp-ip-interfaces.md) |
| Mbuf | BSD packet/data storage unit with chain links, metadata, and optional external backing. [TCP/IP](subsystems/networking/tcp-ip-interfaces.md) |
| `ifnet` / DLIL | Network-interface state and the data-link interface layer connecting protocols, queues, and driver callbacks. [TCP/IP](subsystems/networking/tcp-ip-interfaces.md) |
| Interface I/O reference / data-movement reference | Separate participation counts used to quiesce interface users and data paths during detach; retaining the `ifnet` object alone is insufficient. [Packet and interface lifetimes](subsystems/networking/packets-routes-and-interfaces.md) |
| Skywalk channel / nexus | Shared-ring endpoint and provider-instance infrastructure for supported packet/data paths. [Skywalk](subsystems/networking/skywalk.md) |
| `IOService` / user client | An IOKit service/driver object and an interface object controlling operations from user space. [Drivers](subsystems/drivers/README.md) |
| `OSObject` / `OSMetaClass` | Reference-counted kernel C++ object and its class metadata. Collection-tagged ownership, module/class pins and class-instance tracking have distinct accounting rules. [Object runtime](subsystems/drivers/object-runtime-and-collections.md) |
| Registry plane | A named parent/child graph over I/O Registry entries. One entry can participate in several planes and has a separate property dictionary. [Registry planes](subsystems/drivers/registry-planes-and-properties.md) |
| Matching notifier / interest notifier | Registration for matching service lifecycle events / messages associated with a particular service. Removal includes an invocation-drain protocol with a self-callback exception. [Notifications and arbitration](subsystems/drivers/service-notifications-and-arbitration.md) |
| `OSAction` | DriverKit callback object holding a target, callback/target method IDs and optional private reference bytes. Its kernel aborted notification is separate from the externally implemented user-space cancellation/wait contract. [DriverKit actions](subsystems/drivers/driverkit-dispatch-and-actions.md) |
| Memory descriptor / DMA command | IOKit descriptions/preparation of memory and machinery for device-visible mappings/segments. CPU virtual addresses and DMA addresses are distinct. [Drivers](subsystems/drivers/README.md) |
| `IOMemoryMap` | An IOKit CPU mapping object, retained subset view, or static alias. Mapping ownership differs from descriptor preparation and device-address mappings. [CPU mappings](subsystems/drivers/memory-descriptors-and-cpu-mappings.md) |
| `IODataQueue` / `IOCircularDataQueue` | Shared-memory FIFO with producer/consumer offsets / overwriting queue with per-entry and reader-cursor validation. Their notification and failure-progress contracts differ. [Shared queues](subsystems/drivers/shared-data-queues-and-notifications.md) |
| `IOPMPowerState` / PM request | A driver's declared power-state capabilities and requirements / queued work used by the power state machine. State index, optional state order, parent power and outstanding acknowledgments are separate inputs. [Device power](subsystems/drivers/device-power-state-machine.md) |
| Root-domain capability transition | System-level change in available CPU, graphics, audio and network capabilities, coordinated with notifications, driver power and platform sleep/wake. [System sleep](subsystems/drivers/system-sleep-and-wake.md) |
| Hibernation image1 / image2 | Early-restored image portion and the remaining pageable image restored after kernel execution resumes. Selection bitmaps, scratch-page collision handling and VM cleanup connect the two stages. [Image creation](subsystems/platform/hibernation-image-creation.md), [restoration](subsystems/platform/hibernation-restore.md) |
| `IOReporter` / performance-control token | Channel/element sampling infrastructure / identity and retained state for a submitted unit of device work. Reporting samples and controller work lifetime are separate protocols. [Reporting and performance control](subsystems/drivers/reporting-and-performance-control.md) |
| Kauth / MAC | Authorization and mandatory-access-control framework mechanisms called by operation-specific code. Their interfaces do not contain every external policy implementation. [Security](subsystems/security/README.md) |
| `ucred` / `kaudit_record` | Shared credential identity and label state / an in-progress or queued audit event. Credential publication, operation authorization, audit commit and audit-file output have different completion points. [Credentials](subsystems/security/credential-and-policy-lifetimes.md), [audit](subsystems/security/audit-pipeline.md) |
| SuperBlob / CodeDirectory | An indexed serialized signature container / the selected signed description of code and special-slot hashes, geometry, identifiers and flags. Structural acceptance, certificate trust and page-byte matching are separate checks. [Signature format](subsystems/security/signature-format-and-blob-validation.md) |
| CDHash | The fixed 20-byte identity derived from hashing the selected CodeDirectory. It is not a hash of the entire file or SuperBlob; the cached identity survives selected in-memory signature transformations. [Hash identities](subsystems/security/signature-format-and-blob-validation.md) |
| `cs_blob` / signature attachment | A vnode-owned wrapper for signature coverage, retained bytes, accepted properties and optional monitor/entitlement state, published through UBC. Readers require the documented vnode/paging lifetime protection. [Attachment lifecycle](subsystems/security/vnode-signature-lifecycle.md) |
| Signing generation / `cs_mtime` | Cached policy-generation acceptance / a recorded first-attachment modification time. Neither is a per-page byte-integrity result. [Revalidation and invalidation](subsystems/security/vnode-signature-lifecycle.md) |
| `vmp_cs_validated` / tainted / NX | VM subpage masks recording checked, tainted, and non-executable state. A mismatch can set both validated and tainted; callers must interpret all applicable bits and policy. [Page integrity](subsystems/security/page-signature-validation.md) |
| `csm_associated` | VM-entry state recording successful code-signing-monitor region association. It does not by itself establish that every resident page has passed the eventual executable-mapping check. [Executable policy](subsystems/security/executable-signature-policy.md) |
| Kdebug / kperf / Recount | Event tracing, triggered sampling, and accumulated resource accounting. They answer different questions. [Observability](development/observability.md) |
| Stackshot / kcdata | Structured task/thread capture and the chunked record format used for diagnostic output. [Observability](development/observability.md) |

For a name not listed here, use the [source-reference index](source-index.md) or start from the subsystem's structure table. The definition and its nearby lock/lifetime comments are usually more informative than expanding the acronym alone.
