# A practical route through XNU

[Guide index](README.md) · [Architecture](architecture.md) · [Source map](source-map.md)

## Read an operation, then widen the boundary

For each operation, identify its entry point, the object it acts on, the lock/reference protecting that object, its normal path, its blocking or failure path, and its cleanup. Those six questions are a more manageable unit than “read the VM subsystem.” Keep a small call graph and add only the branches needed to answer your question.

The following passes build on one another. They are an order of study, not a claim that every listed file should be read in full.

## Pass 1: learn the identities

Read [architecture.md](architecture.md), then compare the definitions of [`proc`](../xnu/bsd/sys/proc_internal.h), [`task`](../xnu/osfmk/kern/task.h), [`thread`/`thread_ro`](../xnu/osfmk/kern/thread.h), and [`uthread`](../xnu/bsd/sys/user.h). Write down which layer owns PID identity, the address map, the IPC namespace, scheduling state, and BSD thread state.

Then read `proc_task()` in [kern_proc.c](../xnu/bsd/kern/kern_proc.c#L2003) and `get_threadtask()` in [bsd_kern.c](../xnu/osfmk/kern/bsd_kern.c#L834). The accessor implementations are useful precisely because current layout differs from older diagrams. Continue into the [runtime lifecycle guide](subsystems/runtime/objects-and-lifecycle.md) and [BSD lifecycle guide](subsystems/processes/README.md).

**Checkpoint:** explain how one process can have several schedulable threads, why a task is not a CPU execution context, and why a reference and a PID are not interchangeable ways to keep a process alive.

## Pass 2: follow one entry from user space

Pick a small syscall from [syscalls.master](../xnu/bsd/kern/syscalls.master), locate its implementation, and inspect an architecture dispatcher: [ARM](../xnu/bsd/dev/arm/systemcalls.c) or [x86](../xnu/bsd/dev/i386/systemcalls.c). Trace argument extraction and the return convention before following the operation itself. Use the [process interface guide](subsystems/processes/README.md) to connect dispatch, `uthread`, restart behavior, and signals.

Next compare a Mach trap in [syscall_sw.c](../xnu/osfmk/kern/syscall_sw.c) with an RPC declaration such as [mach_vm.defs](../xnu/osfmk/mach/mach_vm.defs). Read the [IPC guide](subsystems/ipc/README.md) to understand why a public function name can lead to a trap wrapper, generated MIG client, or kernel server implementation.

The [complete interface map](interfaces/README.md) gives a searchable route through [every BSD slot](interfaces/bsd-syscalls/number-index.md), [every Mach trap slot](interfaces/mach-traps.md), [machine-specific selectors](interfaces/machine-entry-points.md), and [all MIG subsystems](interfaces/mach-messages/subsystems.md). Use each entry's purpose, argument declaration and implementation path to choose the next function; preserve the distinction between a declaration, a registered receiver and an external service.

For the instructions before and after C dispatch, follow the [ARM64 assembly walkthroughs](subsystems/platform/arm64-assembly-walkthroughs.md). Track the active SP bank, saved-context address, handler arguments, AST loop and exact register values used by exception return.

Then follow [AST publication and consumption](subsystems/runtime/ast-mechanism.md) and the [complete flavor catalog](subsystems/runtime/ast-flavors.md). Trace a producer setting thread state, CPU propagation or a remote check, consumption with the required interrupt state, and any payload cleared before the callback. Compare urgent kernel preemption with work eligible only on return to userspace.

**Checkpoint:** distinguish a syscall number, a Mach trap number, a Mach message ID, a port name, and a kernel object pointer. None is a substitute for the others.

## Pass 3: understand blocking before scheduler policy

Read `assert_wait*()`, `thread_block_reason()`, and the wakeup-to-runnable path in [sched_prim.c](../xnu/osfmk/kern/sched_prim.c), with [waitq.c](../xnu/osfmk/kern/waitq.c) beside it. Follow the [waits and locks guide](subsystems/runtime/waits-and-locks.md). Notice where the condition's lock is released, where the thread is registered as waiting, and how a wakeup racing with the block is handled.

Only then read [scheduling.md](subsystems/runtime/scheduling.md). Separate common runnable/block/context-switch machinery from the selected scheduler's choice of thread and CPU. Study one Clutch bucket or one Edge placement decision at a time rather than trying to memorize the entire policy.

Read [ARM64 thread switching, entry and exit](subsystems/platform/arm64-context-switching.md) to connect that decision to `cswitch.s`. Trace a saved kernel call returning on another stack, a continuation starting on a reset stack, first user entry and the final off-CPU termination/reaping sequence.

Continue with [priority, QoS and quanta](subsystems/runtime/priority-qos-and-quanta.md), [realtime deadlines](subsystems/runtime/realtime-deadlines-and-runqueues.md), and [CPU eligibility and scheduler variants](subsystems/runtime/cpu-eligibility-and-scheduler-variants.md). Work through the numerical priority/deadline examples, then identify which lock protects a queued thread while its priority or eligible CPUs change.

**Checkpoint:** explain why waking a thread does not guarantee immediate execution and why a callback cannot always sleep just because its caller is written in C.

## Pass 4: translate a virtual address

Start with [maps and faults](subsystems/vm/maps-and-faults.md). Locate a map entry, calculate the object offset, and follow a resident-page fault before examining a slow pager fault. Keep map, object, page, and pmap roles distinct. Read the current range/entry locking rules; do not impose a historical single-map-lock model on this source.

Use the [mapping walkthroughs](subsystems/vm/mapping-walkthroughs.md) to follow anonymous memory, a mapped file, and COW. Read [virtual address maps](subsystems/vm/virtual-address-maps.md), [objects and pages](subsystems/vm/objects-and-pages.md), and [fault resolution](subsystems/vm/fault-resolution.md) for the structures and retry rules behind those examples.

Next follow the resulting physical frame into [ARM64 pmap](subsystems/vm/pmap-arm64.md), [mapping lifetimes](subsystems/vm/pmap-mapping-lifecycle.md), and [TLB/cache completion](subsystems/vm/pmap-tlb-and-cache.md), or the separate [x86_64 implementation](subsystems/vm/pmap-x86.md). Then connect [wiring and memory entries](subsystems/vm/wiring-and-memory-entries.md) and [pagers/UPL](subsystems/vm/pagers-and-upl.md) to page ownership during sharing and I/O. Finish with [reclamation](subsystems/vm/reclaim-and-pressure.md) and [kernel allocation](subsystems/vm/kernel-allocation.md).

**Checkpoint:** explain how a valid mapping can lack a resident physical page, why a resident page can still fault, how two mappings can share backing, and when an old translation stops being usable. Distinguish virtual size, resident size, compressed contents, and allocation-zone usage.

For allocator internals, continue from the [allocator overview](subsystems/vm/kernel-allocation.md) to [zones](subsystems/vm/zone-allocator.md), [kalloc routing](subsystems/vm/kalloc-heaps-and-routing.md) and [type isolation](subsystems/vm/typed-allocation.md). Follow one metadata record from its macro into startup assignment, then through allocation and compatible free. Finally trace a refill or large request into [guarded kernel VM allocation](subsystems/vm/kernel-virtual-allocation.md). Check which state is per call site, per type/signature group, per zone, per physical page, or per CPU.

For the protected-domain side of VM, follow [SPTM/TXM/Exclaves boundaries](subsystems/security/protected-execution.md). Trace one SPTM mapping/retype operation and one TXM signature association, then distinguish an Exclaves scheduling request from an RPC upcall. **Checkpoint:** identify what XNU retains across each call, how interrupt return selects the interrupted domain, and when a physical page becomes safe for XNU to reuse.

Use [pmap translation walkthroughs](subsystems/vm/pmap-translation-walkthroughs.md) to decompose concrete 4 KiB and 16 KiB addresses. Distinguish the physical location of a PTE from the physical page it names, then follow a mapping change through TLB completion and safe reuse.

## Pass 5: follow a file descriptor into VFS or networking

Read [`fileproc` and `fileglob`](../xnu/bsd/sys/file_internal.h) and the generic read/write code in [sys_generic.c](../xnu/bsd/kern/sys_generic.c). Then choose a vnode-backed file or a socket. For a file, continue into [VFS](subsystems/vfs/README.md): path lookup, authorization, vnode lifetime, operation dispatch, and cache/pager integration. For a socket, continue into [networking](subsystems/networking/README.md): socket buffers, protocol callbacks, packet representation, and interface input/output.

Follow [namespace mutations](subsystems/vfs/namespace-mutations.md) through a rename retry, then compare [device nodes and FIFOs](subsystems/vfs/device-nodes-and-fifos.md), [stacked filesystem aliases](subsystems/vfs/stacked-filesystems.md), and [an NFS request](subsystems/vfs/nfs-server-requests.md). Track exactly which layer owns the pathname, vnode identity, persistent reference, per-operation iocount and completion result.

For caching, compare [vnode identity and authorization caches](subsystems/vfs/vnode-cache-identity-and-reuse.md), [UBC resident/missing-page reads](subsystems/vfs/file-data-cache-and-read-path.md), and [buffer-cache ownership](subsystems/vfs/buffer-cache-and-block-io.md). Follow one read hit, one read miss, one truncate and one final close. Identify which of those operations changes file bytes, which releases an active owner, and which actually evicts cached state.

**Checkpoint:** explain why duplicating a descriptor can share an open-file offset, why a vnode is not just a pathname, and why socket readiness belongs to both networking state and the event/wakeup machinery.

## Pass 6: learn IPC ownership and service boundaries

Use the [IPC guide](subsystems/ipc/README.md) to follow a message from user-space port names through copyin, queueing or direct delivery, receive, and copyout. Track rights and out-of-line memory as well as inline bytes. Inspect the destination's right type and any kernel-object conversion.

Then use [drivers](subsystems/drivers/README.md) to follow a request from a user-client connection into an IOKit object. Compare a driver work loop with the BSD `kevent` workloop described in the process guide; the similar names do not imply a shared object type.

The driver index now provides a full reading route from [bootstrap](subsystems/drivers/bootstrap-and-bsd-integration.md) and [object runtime](subsystems/drivers/object-runtime-and-collections.md) through registry/matching, notifications, execution, user interfaces, memory and power. Compare a [shared queue notification](subsystems/drivers/shared-data-queues-and-notifications.md) with a [DriverKit action](subsystems/drivers/driverkit-dispatch-and-actions.md), and follow one buffer through [CPU mapping](subsystems/drivers/memory-descriptors-and-cpu-mappings.md) before [DMA preparation](subsystems/drivers/dma-preparation-and-mapping.md). Continue into [segment generation](subsystems/drivers/dma-segment-walkthrough.md) and explain which returned address is physical or IOVA, where a padded mapping introduces a gap, and how a second capacity-limited call resumes.

**Checkpoint:** explain why a port name is local to an IPC space, why sending a right changes ownership/accounting, and why possession of a connection does not mean every external driver method is authorized.

## Pass 7: connect policy and hardware

Read [security](subsystems/security/README.md) around an operation you already understand: file open, process execution, task-port access, or a driver request. Find which credential is used, where an operation invokes authorization or a MAC hook, and what implementation lies outside the public source.

For code signing, read [signature format](subsystems/security/signature-format-and-blob-validation.md) → [vnode attachment](subsystems/security/vnode-signature-lifecycle.md) → [exec/mapping policy](subsystems/security/executable-signature-policy.md) → [page validation](subsystems/security/page-signature-validation.md). Trace one slice-relative CodeDirectory slot to a file offset and then to a resident VM page. Explain why an accepted blob, `CS_VALID`, a page's validated mask and `csm_associated` do not mean the same thing, and what changes after a cached write, COW, page eviction or vnode reclaim.

For power transitions, follow [device power state selection](subsystems/drivers/device-power-state-machine.md) → [system sleep and wake](subsystems/drivers/system-sleep-and-wake.md) → [hibernation image construction](subsystems/platform/hibernation-image-creation.md) → [image restoration](subsystems/platform/hibernation-restore.md). Compare [x86 sleep/resume](subsystems/platform/x86-sleep-and-resume.md) with [ARM64 CPU lifecycle](subsystems/platform/cpu-power-lifecycle.md). Identify the last context that can use ordinary filesystem I/O, the switch to polled I/O, and the separate point at which normal scheduling and services resume.

Then read [platform](subsystems/platform/README.md) around a fault or syscall you already traced. Study boot order, interrupt context, exception entry/return, and the selected pmap backend. This gives machine code a concrete purpose instead of making assembly the first obstacle.

**Checkpoint:** distinguish a policy decision from a mechanism that enforces it, and identify which build guards change the path on the target you are studying.

## A repeatable source-reading worksheet

The [complete table of contents](table-of-contents.md) provides a section-level route through the whole handbook. For the newly expanded lifecycle and failure paths, use the [topic audit](expansion-audit.md), then compare [completion and cancellation](cross-cutting/completion-and-failure.md) across the relevant subsystems. The [SMR chapter](cross-cutting/smr-and-publication.md) supplies the shared reclamation protocol behind many lookup and teardown paths.

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

The [observability guide](development/observability.md) maps questions to traces, samples, counters, snapshots, and debugger macros. A macro that displays the fields you are studying can be a useful second explanation of their relationship. A subsystem test can provide a small scenario and expected result; see [build and tests](development/build-and-tests.md) for the different harnesses and their requirements.

Keep three claims separate in your notes: “this body performs this step,” “this configuration selects this body,” and “this happened in a running kernel.” Source reading can establish the first, selected build artifacts help establish the second, and runtime evidence is needed for the third.
