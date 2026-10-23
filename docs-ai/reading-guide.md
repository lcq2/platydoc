# A practical route through XNU

[Guide index](README.md) · [Architecture](architecture.md) · [Source map](source-map.md)

## Read an operation, then widen the boundary

For each operation, identify its entry point, the object it acts on, the lock/reference protecting that object, its normal path, its blocking or failure path, and its cleanup. Those six questions are a more manageable unit than “read the VM subsystem.” Keep a small call graph and add only the branches needed to answer your question.

The following passes build on one another. They are an order of study, not a claim that every listed file should be read in full.

## Pass 1: learn the identities

Read [architecture.md](architecture.md), then compare the definitions of [`proc`](../platydoc-data/xnu/bsd/sys/proc_internal.h), [`task`](../platydoc-data/xnu/osfmk/kern/task.h), [`thread`/`thread_ro`](../platydoc-data/xnu/osfmk/kern/thread.h), and [`uthread`](../platydoc-data/xnu/bsd/sys/user.h). Write down which layer owns PID identity, the address map, the IPC namespace, scheduling state, and BSD thread state.

Then read `proc_task()` in [kern_proc.c](../platydoc-data/xnu/bsd/kern/kern_proc.c#L2003) and `get_threadtask()` in [bsd_kern.c](../platydoc-data/xnu/osfmk/kern/bsd_kern.c#L834). The accessor implementations are useful precisely because current layout differs from older diagrams. Continue into the [runtime lifecycle guide](subsystems/runtime/objects-and-lifecycle.md) and [BSD lifecycle guide](subsystems/processes/README.md).

**Checkpoint:** explain how one process can have several schedulable threads, why a task is not a CPU execution context, and why a reference and a PID are not interchangeable ways to keep a process alive.

For a deeper structure study, continue through [key structures](structures/README.md), [the process and its protected data](structures/proc-and-proc-ro.md), [the task and its shared RO data](structures/task-and-shared-ro.md), then [writing protected object fields](structures/read-only-object-updates.md). Follow one selected field from its initialization template through an accessor and an update into final cleanup. Compare the combined writable allocation with the separate RO record, and keep backend write permission, object lifetime and field synchronization distinct.

Next follow [thread, BSD state and `thread_ro`](structures/thread-and-thread-ro.md). Compare the combined thread/uthread allocation with its separate protected companion, then identify which references survive the final off-CPU transition. Read [credential storage](structures/credentials-and-credential-storage.md) and [MAC labels](structures/mac-label-storage.md) alongside it: trace one identity replacement through hash uniquing, process publication, thread-cache refresh and final retirement. **Checkpoint:** distinguish process identity, an assumed thread identity, a borrowed credential pointer, an owned credential reference and a long-term stored holding.

## Pass 2: follow one entry from user space

Pick a small syscall from [syscalls.master](../platydoc-data/xnu/bsd/kern/syscalls.master), locate its implementation, and inspect an architecture dispatcher: [ARM](../platydoc-data/xnu/bsd/dev/arm/systemcalls.c) or [x86](../platydoc-data/xnu/bsd/dev/i386/systemcalls.c). Trace argument extraction and the return convention before following the operation itself. Use the [process interface guide](subsystems/processes/README.md) to connect dispatch, `uthread`, restart behavior, and signals.

Next compare a Mach trap in [syscall_sw.c](../platydoc-data/xnu/osfmk/kern/syscall_sw.c) with an RPC declaration such as [mach_vm.defs](../platydoc-data/xnu/osfmk/mach/mach_vm.defs). Read the [IPC guide](subsystems/ipc/README.md) to understand why a public function name can lead to a trap wrapper, generated MIG client, or kernel server implementation.

The [complete interface map](interfaces/README.md) gives a searchable route through [every BSD slot](interfaces/bsd-syscalls/number-index.md), [every Mach trap slot](interfaces/mach-traps.md), [machine-specific selectors](interfaces/machine-entry-points.md), and [all MIG subsystems](interfaces/mach-messages/subsystems.md). Use each entry's purpose, argument declaration and implementation path to choose the next function; preserve the distinction between a declaration, a registered receiver and an external service.

For the instructions before and after C dispatch, follow the [ARM64 assembly walkthroughs](subsystems/platform/arm64-assembly-walkthroughs.md). Track the active SP bank, saved-context address, handler arguments, AST loop and exact register values used by exception return.

Then follow [AST publication and consumption](subsystems/runtime/ast-mechanism.md) and the [complete flavor catalog](subsystems/runtime/ast-flavors.md). Trace a producer setting thread state, CPU propagation or a remote check, consumption with the required interrupt state, and any payload cleared before the callback. Compare urgent kernel preemption with work eligible only on return to userspace.

**Checkpoint:** distinguish a syscall number, a Mach trap number, a Mach message ID, a port name, and a kernel object pointer. None is a substitute for the others.

For a harder IPC exercise, use [complex message conversion](subsystems/ipc/complex-message-copyin-and-copyout.md). Give one header name two dispositions, then add memory and port-array descriptors. Predict which sender resources move and which receiver resources exist after each failure stage. Follow [importance propagation](subsystems/ipc/importance-propagation-and-delayed-drops.md) separately: a task can stop contributing to the dependency graph while an applied boost remains pending delayed withdrawal.

## Pass 3: understand blocking before scheduler policy

Read `assert_wait*()`, `thread_block_reason()`, and the wakeup-to-runnable path in [sched_prim.c](../platydoc-data/xnu/osfmk/kern/sched_prim.c), with [waitq.c](../platydoc-data/xnu/osfmk/kern/waitq.c) beside it. Follow the [waits and locks guide](subsystems/runtime/waits-and-locks.md). Notice where the condition's lock is released, where the thread is registered as waiting, and how a wakeup racing with the block is handled.

Only then read [scheduling.md](subsystems/runtime/scheduling.md). Separate common runnable/block/context-switch machinery from the selected scheduler's choice of thread and CPU. Study one Clutch bucket or one Edge placement decision at a time rather than trying to memorize the entire policy.

For primitive state transitions, follow [reader/writer locks](subsystems/runtime/reader-writer-locks.md) and [ticket and pointer locks](subsystems/runtime/ticket-and-pointer-locks.md). Check the selected RW type, whether a failed upgrade retains any ownership, and whether a ticket has already been reserved. Keep a pointer returned under a lock distinct from a pointer value merely observed by a waiter.

Read [ARM64 thread switching, entry and exit](subsystems/platform/arm64-context-switching.md) to connect that decision to `cswitch.s`. Trace a saved kernel call returning on another stack, a continuation starting on a reset stack, first user entry and the final off-CPU termination/reaping sequence.

Continue with [priority, QoS and quanta](subsystems/runtime/priority-qos-and-quanta.md), [realtime deadlines](subsystems/runtime/realtime-deadlines-and-runqueues.md), and [CPU eligibility and scheduler variants](subsystems/runtime/cpu-eligibility-and-scheduler-variants.md). Work through the numerical priority/deadline examples, then identify which lock protects a queued thread while its priority or eligible CPUs change.

**Checkpoint:** explain why waking a thread does not guarantee immediate execution and why a callback cannot always sleep just because its caller is written in C.

## Pass 4: translate a virtual address

Start with [maps and faults](subsystems/vm/maps-and-faults.md). Locate a map entry, calculate the object offset, and follow a resident-page fault before examining a slow pager fault. Keep map, object, page, and pmap roles distinct. Read the current range/entry locking rules; do not impose a historical single-map-lock model on this source.

Use the [mapping walkthroughs](subsystems/vm/mapping-walkthroughs.md) to follow anonymous memory, a mapped file, and COW. Read [virtual address maps](subsystems/vm/virtual-address-maps.md), [objects and pages](subsystems/vm/objects-and-pages.md), and [fault resolution](subsystems/vm/fault-resolution.md) for the structures and retry rules behind those examples.

Keep the five [VM structure companions](structures/README.md#follow-virtual-memory-into-backing-and-translation-storage) open beside those operations. Trace map/header/entry allocation, decode the backing and offset, distinguish object references from paging/activity holds, and identify the descriptor corresponding to a physical frame. Then compare pmap-object allocation with root/table/PTD/PV allocation in each ARM64 backend. Finish with a named memory entry: unwrap its single-object copy representation and account for the additional reference acquired by a destination mapping.

Next follow the resulting physical frame into [ARM64 pmap](subsystems/vm/pmap-arm64.md), [mapping lifetimes](subsystems/vm/pmap-mapping-lifecycle.md), and [TLB/cache completion](subsystems/vm/pmap-tlb-and-cache.md), or the separate [x86_64 implementation](subsystems/vm/pmap-x86.md). Then connect [wiring and memory entries](subsystems/vm/wiring-and-memory-entries.md) and [pagers/UPL](subsystems/vm/pagers-and-upl.md) to page ownership during sharing and I/O. Finish with [reclamation](subsystems/vm/reclaim-and-pressure.md) and [kernel allocation](subsystems/vm/kernel-allocation.md).

**Checkpoint:** explain how a valid mapping can lack a resident physical page, why a resident page can still fault, how two mappings can share backing, and when an old translation stops being usable. Distinguish virtual size, resident size, compressed contents, and allocation-zone usage.

Then follow the harder retry and reclamation paths: [delayed-copy preservation and collapse/bypass](subsystems/vm/objects-and-pages.md), [copy-version revalidation and resilient faults](subsystems/vm/fault-resolution.md), and [UPL gathering/partial completion](subsystems/vm/upl-gather-and-completion.md). Explain why an unchanged copy pointer can require new preservation work, why a page-in result does not authorize a PTE at an address that was remapped, and why a failed vector completion can have already retired an earlier child.

Then work through [one mapped file and ARM64 fault](cross-cutting/mapped-file-to-arm64-fault.md). Keep a ledger of the vnode, pager, private VM objects, file/object offsets and physical frame across read, private write and unmap. Use the concrete address calculation to test the distinctions above.

For allocator internals, continue from the [allocator overview](subsystems/vm/kernel-allocation.md) to [zones](subsystems/vm/zone-allocator.md), [kalloc routing](subsystems/vm/kalloc-heaps-and-routing.md) and [type isolation](subsystems/vm/typed-allocation.md). Follow one metadata record from its macro into startup assignment, then through allocation and compatible free. Finally trace a refill or large request into [guarded kernel VM allocation](subsystems/vm/kernel-virtual-allocation.md). Check which state is per call site, per type/signature group, per zone, per physical page, or per CPU.

For the protected-domain side of VM, follow [SPTM/TXM/Exclaves boundaries](subsystems/security/protected-execution.md). Trace one SPTM mapping/retype operation and one TXM signature association, then distinguish an Exclaves scheduling request from an RPC upcall. **Checkpoint:** identify what XNU retains across each call, how interrupt return selects the interrupted domain, and when a physical page becomes safe for XNU to reuse.

Use [pmap translation walkthroughs](subsystems/vm/pmap-translation-walkthroughs.md) to decompose concrete 4 KiB and 16 KiB addresses. Distinguish the physical location of a PTE from the physical page it names, then follow a mapping change through TLB completion and safe reuse.

Continue with [MTE tagging and page lifetime](subsystems/vm/mte-tag-storage-and-page-lifecycle.md) to follow the mitigation from pointer tags and process opt-in through first faults, mapping provenance, allocator reuse and fault reporting. Distinguish data-page tags, allocator cells and physical tag backing; follow the zone free example to see when a stale pointer becomes invalid. [Bootstrap memory and lockdown](subsystems/platform/bootstrap-memory-and-lockdown.md) supplies the prerequisites: boot-policy selection, CPU controls, tag-generator state, early tagged zones and final protection. Then use [ARM64 user-memory copying](subsystems/platform/arm64-user-memory-copy.md) and [AST handling](subsystems/runtime/ast-mechanism.md) to follow a kernel access to a user buffer through recovery and delayed notification. Track when an address becomes usable separately from when its storage becomes reusable or its tag checks are disabled.

## Pass 5: follow a file descriptor into VFS or networking

Read [`fileproc` and `fileglob`](../platydoc-data/xnu/bsd/sys/file_internal.h) and the generic read/write code in [sys_generic.c](../platydoc-data/xnu/bsd/kern/sys_generic.c). Then choose a vnode-backed file or a socket. For a file, continue into [VFS](subsystems/vfs/README.md): path lookup, authorization, vnode lifetime, operation dispatch, and cache/pager integration. For a socket, continue into [networking](subsystems/networking/README.md): socket buffers, protocol callbacks, packet representation, and interface input/output.

Keep the [file structure route](structures/README.md#follow-descriptors-into-file-and-signature-storage) open beside those operations. Trace the embedded filedesc header and movable arrays, reserve and publish one slot, then duplicate it and account for separate fileproc I/O holds and shared fileglob ownership. Continue through vnode generation/iocount/usecount/hold distinctions into UBC, the vnode pager and the named VM association. Compare descriptor close with vnode reclaim and final pager release.

For a socket, keep the [network structure route](structures/README.md#follow-messages-and-packets-into-their-storage) beside the operation. Distinguish the socket from its protocol attachment, the embedded sockbuf from its mbuf records, and one packet descriptor from shared external bytes. Work through the PCB reference and mbuf capacity examples, then compare a failed copy, a queue flush, protocol detach and final storage release.

Follow [namespace mutations](subsystems/vfs/namespace-mutations.md) through a rename retry, then compare [device nodes and FIFOs](subsystems/vfs/device-nodes-and-fifos.md), [stacked filesystem aliases](subsystems/vfs/stacked-filesystems.md), and [an NFS request](subsystems/vfs/nfs-server-requests.md). Track exactly which layer owns the pathname, vnode identity, persistent reference, per-operation iocount and completion result.

Trace the decision itself through [permissions and ACL evaluation](subsystems/vfs/permissions-and-acl-evaluation.md): requested actions, ordered ACEs, unresolved rights, POSIX fallback, deletion checks and inheritance are distinct steps. For Skywalk, follow [namespace reservation and lookup](subsystems/networking/skywalk-namespaces-and-flow-lookup.md) → [classification and delivery](subsystems/networking/skywalk-flowswitch-classification-routes-and-datapaths.md) → [netif queues](subsystems/networking/skywalk-netif-links-queues-and-scheduling.md) → [FQ-CoDel scheduling](subsystems/networking/interface-packet-scheduling-and-fq-codel.md). Explain who owns a packet after each conversion, enqueue, pending-neighbor result and drop.

For caching, compare [vnode identity and authorization caches](subsystems/vfs/vnode-cache-identity-and-reuse.md), [UBC resident/missing-page reads](subsystems/vfs/file-data-cache-and-read-path.md), and [buffer-cache ownership](subsystems/vfs/buffer-cache-and-block-io.md). Follow one read hit, one read miss, one truncate and one final close. Identify which of those operations changes file bytes, which releases an active owner, and which actually evicts cached state.

**Checkpoint:** explain why duplicating a descriptor can share an open-file offset, why a vnode is not just a pathname, and why socket readiness belongs to both networking state and the event/wakeup machinery.

For networking policy, follow [NECP rule evaluation](subsystems/networking/necp-policy-evaluation.md) into [client and flow-registration lifetime](subsystems/networking/necp-clients-and-flow-registration.md). Then trace [socket content filtering](subsystems/networking/socket-content-filtering.md), keeping pass permission, peek permission and actual reinjection separate. These byte-offset queues differ from Skywalk netif packet-filter channels.

For TCP, first follow [connection and timer lifetime](subsystems/networking/tcp-connections-and-timers.md), then [loss recovery and congestion control](subsystems/networking/tcp-loss-recovery-and-congestion-control.md). Keep acknowledged stream bytes, SACK delivery evidence and transmission timestamps separate. For a channel transport with different ownership, use [Skywalk user and kernel pipes](subsystems/networking/skywalk-user-and-kernel-pipes.md) after the packet-pool and channel guides: follow one packet attachment through transfer and distinguish an endpoint close from final ring storage release.

The [worked Skywalk operation](cross-cutting/skywalk-channel-operation.md) joins those mechanisms to guarded descriptors, IOKit task mappings and readiness. Explain each row of its two-batch backpressure table: which state changed in userspace, which was validated by the kernel, and which completion view is still stale.

## Pass 6: learn IPC ownership and service boundaries

Use the [IPC guide](subsystems/ipc/README.md) to follow a message from user-space port names through copyin, queueing or direct delivery, receive, and copyout. Track rights and out-of-line memory as well as inline bytes. Inspect the destination's right type and any kernel-object conversion.

Keep [IPC spaces and entries](structures/ipc-spaces-and-entries.md) beside [ports and kobjects](structures/ipc-ports-and-kobjects.md) while reading the implementation. Trace the name's index and generation, the entry's right type and user-reference count, the port's lifetime and state, and the target object reference acquired by conversion. Then repeat the lookup across a table growth or receive-right destruction: locate the exact point where the implementation retries or rejects stale state.

Continue with [IPC kmsg storage](structures/ipc-kmsgs-and-message-storage.md). Compute one inline/external layout boundary, follow the accessor selected by each representation, and maintain a resource ledger through copyin, queue transfer, copyout and destruction. Compare ordinary messages with the reusable `mk_timer` allocation: message-resource cleanup and final storage release follow different ownership transitions.

Then use [drivers](subsystems/drivers/README.md) to follow a request from a user-client connection into an IOKit object. Compare a driver work loop with the BSD `kevent` workloop described in the process guide; the similar names do not imply a shared object type.

The driver index now provides a full reading route from [bootstrap](subsystems/drivers/bootstrap-and-bsd-integration.md) and [object runtime](subsystems/drivers/object-runtime-and-collections.md) through registry/matching, notifications, execution, user interfaces, memory and power. Compare a [shared queue notification](subsystems/drivers/shared-data-queues-and-notifications.md) with a [DriverKit action](subsystems/drivers/driverkit-dispatch-and-actions.md), and follow one buffer through [CPU mapping](subsystems/drivers/memory-descriptors-and-cpu-mappings.md) before [DMA preparation](subsystems/drivers/dma-preparation-and-mapping.md). Continue into [segment generation](subsystems/drivers/dma-segment-walkthrough.md) and explain which returned address is physical or IOVA, where a padded mapping introduces a gap, and how a second capacity-limited call resumes.

Use the [complete user-buffer DMA example](cross-cutting/user-buffer-to-dma-completion.md) to connect client-task selection, VM COW/wiring, descriptor ranges, command preparation, segment output and release. Then compare [matching rescans and deferred starts](subsystems/drivers/service-matching-and-termination.md) with [notifier selection, replay and removal](subsystems/drivers/service-notifications-and-arbitration.md). Explain why a matched event need not imply a successfully started child, and why callback self-removal does not end that callback's use of its context.

**Checkpoint:** explain why a port name is local to an IPC space, why sending a right changes ownership/accounting, and why possession of a connection does not mean every external driver method is authorized.

For receive multiplexing, follow [port-set membership and persistent readiness](subsystems/ipc/port-sets-and-waitq-readiness.md) and explain how a stale prepost differs from a queued message. Then follow [live namespace growth](subsystems/ipc/names-and-rights.md#5-growing-a-live-namespace): private copies can be inconsistent until changed entries are rescanned and the locked publication check succeeds.

## Pass 7: connect policy and hardware

For signed-file storage, use the [cs_blob companion](structures/code-signature-blob-storage.md) alongside the signature operation chapters below. Follow one RO wrapper through its temporary template, byte-buffer relocation, PAC field preparation, publication, selected protected updates and cleanup. Distinguish a borrowed CodeDirectory/team string from a retained entitlement object and from an inline CDHash.

Read [security](subsystems/security/README.md) around an operation you already understand: file open, process execution, task-port access, or a driver request. Find which credential is used, where an operation invokes authorization or a MAC hook, and what implementation lies outside the public source.

For identity changes, compare [personas and membership resolution](subsystems/security/personas-and-membership-resolution.md) with [audit-session capabilities](subsystems/security/audit-session-capabilities.md). Explain which fields affect authorization, which identify an audit session, and which references survive process detachment or port-right release.

For code signing, read [signature format](subsystems/security/signature-format-and-blob-validation.md) → [vnode attachment](subsystems/security/vnode-signature-lifecycle.md) → [exec/mapping policy](subsystems/security/executable-signature-policy.md) → [page validation](subsystems/security/page-signature-validation.md). Trace one slice-relative CodeDirectory slot to a file offset and then to a resident VM page. Explain why an accepted blob, `CS_VALID`, a page's validated mask and `csm_associated` do not mean the same thing, and what changes after a cached write, COW, page eviction or vnode reclaim.

Then compare [trust-cache control](subsystems/security/trust-cache-control.md) with [process signing controls and CSR](subsystems/security/code-signing-process-controls.md). Follow one load through admission and payload retention, one `csops` request through PID/version and command-specific gates, and one boot-derived CSR allowance to its consumer. A trusted code identity, process policy and resident-page integrity answer different questions.

For power transitions, follow [device power state selection](subsystems/drivers/device-power-state-machine.md) → [system sleep and wake](subsystems/drivers/system-sleep-and-wake.md) → [hibernation image construction](subsystems/platform/hibernation-image-creation.md) → [image restoration](subsystems/platform/hibernation-restore.md). Compare [x86 sleep/resume](subsystems/platform/x86-sleep-and-resume.md) with [ARM64 CPU lifecycle](subsystems/platform/cpu-power-lifecycle.md). Identify the last context that can use ordinary filesystem I/O, the switch to polled I/O, and the separate point at which normal scheduling and services resume.

Then read [platform](subsystems/platform/README.md) around a fault or syscall you already traced. Study boot order, interrupt context, exception entry/return, and the selected pmap backend. This gives machine code a concrete purpose instead of making assembly the first obstacle.

**Checkpoint:** distinguish a policy decision from a mechanism that enforces it, and identify which build guards change the path on the target you are studying.

## A repeatable source-reading worksheet

The [complete table of contents](table-of-contents.md) provides a section-level route through the whole handbook. For lifecycle and failure paths, compare [completion and cancellation](cross-cutting/completion-and-failure.md) across the relevant subsystems. The [SMR chapter](cross-cutting/smr-and-publication.md) supplies the shared reclamation protocol behind many lookup and teardown paths.

For a concrete concurrent lookup, continue from SMR into [hash resizing and migration](cross-cutting/smr-hash-tables.md), then [symbol interning](subsystems/drivers/symbol-interning.md). Track the borrowed hash match, successful object acquisition, unlink, old-array retirement and eventual backing release separately.

For a function worth understanding, record:

| Item | What to write down |
| --- | --- |
| Caller and execution context | Syscall thread, worker thread, interrupt, boot phase, or debugger context |
| Inputs | User addresses, kernel pointers, names/handles, flags, and required object state |
| Protection | Entry locks, references, interrupt/preemption constraints, and assertions |
| Transition | The exact state changed and the point at which another thread can observe it |
| External call | Callback, operation vector, generated server stub, or architecture hook |
| Blocking/retry | What can release protection, sleep, allocate, fail, or require relookup |
| Exit | Which references/locks/resources are returned, consumed, or dropped |

For example, the returned-lock contract of `thread_create_internal()` is essential to understanding its callers. The VM fault slow path deliberately drops locks and must revalidate the mapping. A vnode lookup must distinguish object lifetime from recycled identity. These are the details that turn a call graph into an explanation.

## Efficient searches

Run these read-only searches from the XNU source root, `xnu/` inside Platydoc (`cd xnu` first when starting at the project root). Documentation build/check commands instead run from the parent Platydoc directory:

```sh
# Find declarations, implementation entries, and callers together.
rg -n 'thread_block_reason\(' osfmk bsd iokit

# Follow a dispatched operation rather than looking for a direct call.
rg -n 'fo_read|soo_read|vn_read' bsd

# Discover an implementation's build guards and selection lists.
rg -n 'CONFIG_SKYWALK|config_skywalk' config bsd/conf bsd/skywalk

# Look for ownership contracts and nearby invariants in one file.
rg -n 'assert|LCK_MTX_ASSERT|reference|release|deallocate' osfmk/ipc/ipc_port.c

# Find interface definitions and possible generated-code origins.
rg --files osfmk libsyscall iokit | rg '\.(defs|iig)$'
```

Search output is a starting point. Read enough surrounding code to see the preprocessor branch, error labels, and the success/cleanup contracts. For a function pointer, locate both the table definition and its registration; for a macro, read its expansion; for a generated name, inspect the declarative interface and build rule.

## Use diagnostics and tests to check your model

[Skywalk diagnostics, configuration and tests](subsystems/networking/skywalk-diagnostics-configuration-and-tests.md) connects inspected objects and counters to their exporters and local regression cases. Use its sizing and partial-output examples before treating a successful read as a complete, simultaneous snapshot.

[Kdebug storage and readout](development/kdebug-storage-and-readout.md) follows instrumentation records through reservation, timestamp merging, loss markers and consuming output. Use its two-CPU example to distinguish event time from read order, and its output-failure path to see why an error does not restore already-consumed records.

[Kernel logging](development/kernel-logging-and-firehose.md) follows one record through encoding, live streaming and Firehose retry, then compares those results with msgbuf text. Use its loss/publication examples before treating an absent log as evidence that an operation never ran.

The [observability guide](development/observability.md) maps questions to traces, samples, counters, snapshots, and debugger macros. A macro that displays the fields you are studying can be a useful second explanation of their relationship. A subsystem test can provide a small scenario and expected result; see [build and tests](development/build-and-tests.md) for the different harnesses and their requirements.

Keep three claims separate in your notes: “this body performs this step,” “this configuration selects this body,” and “this happened in a running kernel.” Source reading can establish the first, selected build artifacts help establish the second, and runtime evidence is needed for the third.

## Argument, identity and lifetime paths

This route builds a source-level understanding of concrete operations. Read it in the following order, using each companion's object definitions, exact branches, diagrams and failure/cleanup paths. Test references describe available source evidence, not runtime results.

| Order | Reading | What the implementation explains |
| --- | --- | --- |
| 1 | [Command dispatch and validation](interfaces/command-dispatch-and-validation.md) | `ioctl`, `fcntl` and `sysctl` transport, object lookup, caller checks, nested arguments, handler publication and partial output |
| 2 | [VM API argument validation](subsystems/vm/api-argument-validation.md) | Unsafe argument wrappers, range arithmetic, page-size geometry, zero-length conventions, compatibility policy and object admission |
| 3 | [Concurrent-operation walkthroughs](cross-cutting/concurrent-operation-walkthroughs.md) | Concrete VM copy/revalidation, IPC growth/termination and workqueue callback/cancellation schedules |
| 4 | [IOKit external-method call lifecycle](subsystems/drivers/external-method-call-lifecycle.md) | Opener versus current caller, connection and memory owners, dispatch tables, buffer representations, async completion and close |
| 5 | [Exec identity and inherited state](subsystems/processes/exec-identity-and-inherited-state.md) | Credential changes, group-membership exceptions, MAC transitions, inherited Mach state, descriptor repair and token publication |
| 6 | [Message integrity](subsystems/ipc/message-integrity-and-descriptor-authentication.md), then [ARM64 thread-state conversion](subsystems/security/arm64-thread-state-conversion.md) | Signed representations, conversion policy, pointer relocation/authentication, exception replies, sigreturn and installed saved state |
| 7 | [Sanitizer runtime and reporting](development/sanitizer-runtime-and-reporting.md), then [coverage instrumentation lifecycle](development/coverage-instrumentation-lifecycle.md) | Instrumentation selection, metadata lifetime, report disposition, per-thread coverage buffers and detach/close |
| 8 | [BPF capture/filter lifetime](subsystems/networking/bpf-capture-and-filter-lifecycle.md), [PF rules and state](subsystems/networking/pf-rules-states-and-packet-ownership.md), then [IPsec policy and associations](subsystems/networking/ipsec-policy-associations-and-transforms.md) | Capture program/buffer lifetime, published packet rules and retained state, policy/SA lookup, transforms and packet ownership |

This route documents the selected XNU snapshot; it does not prescribe vulnerability research.

## Executable memory, synchronization and packet policy

These companions continue the operation-based route above, concentrating on common code and selected ARM64 configurations. Each states the feature/platform guards that matter.

| Batch | Reading | Operation and state to follow |
| --- | --- | --- |
| A | [Executable-memory policy](subsystems/vm/executable-memory-policy.md) | MAP_JIT and RW→RX admission, current/maximum protection, monitor association, executable faults and SPTM frame types |
| A | [Mach semaphores and eventlinks](subsystems/ipc/semaphores-and-eventlinks.md) | Credits versus paired counters, association, signal/wait ordering, timeout results, handoff and destruction |
| A | [Work-interval policy and thread groups](subsystems/runtime/work-interval-policy-and-thread-groups.md) | Workload configuration, class and effective priority, group resolution, semaphore-triggered auto-join and unwind |
| A | [Flow diversion and provider lifetime](subsystems/networking/flow-diversion-and-provider-lifetime.md) | Socket protocol replacement, provider admission, CONNECT, per-flow credit/control queues, fallback and teardown |
| B | [PF rules, states and packet ownership](subsystems/networking/pf-rules-states-and-packet-ownership.md) | Continue from UDP into TCP peer windows, sequence/ACK decisions, selected loose/proxy handling and NAT/checksum changes |
| B | [IPsec policy, associations and transforms](subsystems/networking/ipsec-policy-associations-and-transforms.md) | Continue from IPv4 into IPv6 transport/tunnel stages, ordered requests, packet handoff and association replacement/retirement |
| B | [ARM64 build and MIG walkthrough](development/arm64-build-and-mig-walkthrough.md) | Concrete target selection, configuration/source/header generation, then a Mach VM request's declared conversion and local implementation |

No kernel build or target runtime test is implied by the worked examples.

## Exec stacks, executable I/O and scheduler placement

These three companions extend mechanisms already introduced above. Follow each representation change through the operation, including failures and ownership after the initiating call returns.

| Start from | Continue with | Concrete operation |
| --- | --- | --- |
| [Executable loading](cross-cutting/executable-loading.md) and [exec identity](subsystems/processes/exec-identity-and-inherited-state.md) | [Exec arguments and the initial user stack](subsystems/processes/exec-arguments-and-user-stack.md) | Incoming argument pointers become kernel strings, rewritten interpreter arguments, Apple entries and a new ARM64 stack with initial SP/PC |
| [Executable-memory policy](subsystems/vm/executable-memory-policy.md) and [UPL gathering](subsystems/vm/upl-gather-and-completion.md) | [Executable pages and UPL I/O](subsystems/vm/executable-pages-and-upl-io.md) | Direction and mapping policy select rejection, direct gathering or temporary copying; the UPL retains backing after the kernel mapping is removed |
| [Work-interval groups](subsystems/runtime/work-interval-policy-and-thread-groups.md) and [Clutch/Edge](subsystems/runtime/clutch-and-edge.md) | [Thread-group accounting and cluster migration](subsystems/runtime/thread-group-accounting-and-cluster-migration.md) | A group switch transfers accounting; a separate preference change updates future placement and requests action for running or queued threads |

The worked layouts and schedules are illustrative; no product configuration or runtime result is inferred from them.

## IPsec interfaces, MPTCP and process inspection

This route connects the packet, transport and process mechanisms with three operations whose state outlives an individual call or packet. Read the prerequisites first, then use the worked examples to follow ownership and identity through changes.

| Start from | Continue with | Operation to follow |
| --- | --- | --- |
| [IPsec policy and transforms](subsystems/networking/ipsec-policy-associations-and-transforms.md), [interface lifetime](subsystems/networking/packets-routes-and-interfaces.md) and [Skywalk pipes](subsystems/networking/skywalk-user-and-kernel-pipes.md) | [IPsec interface lifecycle](subsystems/networking/ipsec-interface-lifecycle.md) | Control setup publishes interface state; mbuf and Skywalk paths transform/deliver packets; disconnect drains distinct users before reclamation |
| [TCP connections](subsystems/networking/tcp-connections-and-timers.md) and [loss recovery](subsystems/networking/tcp-loss-recovery-and-congestion-control.md) | [MPTCP sessions and subflows](subsystems/networking/mptcp-sessions-and-subflows.md) | A session coordinates TCP subflows using connection-level numbering, path selection, reinjection, receive ordering and staged close |
| [Process lifetime](subsystems/processes/lifecycle.md), [descriptor ownership](subsystems/processes/descriptors-ipc.md) and [command dispatch](interfaces/command-dispatch-and-validation.md) | [Process inspection and snapshots](subsystems/processes/process-inspection-and-snapshots.md) | Selector and identity checks admit queries; descriptor enumeration and later typed lookup retain different state while the target can change |

These chapters explain source behavior and illustrative schedules; they do not report a kernel or network experiment.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
