# AST flavor reference: every bit and its consumer

This is the complete top-level AST namespace in this checkout, paired with concrete producers and consumers. The [mechanism chapter](ast-mechanism.md) explains propagation, interrupt levels, remote IPIs, continuation behavior, PFZ deferral, and the difference between a pending bit and an acknowledged operation. The definition contains **22 active individual bits**, **5 named retired positions**, **4 public composite masks**, and the NONE/ALL constants. These counts describe the source namespace, not which features a particular kernel configuration enables. [Authoritative definitions](../../../platydoc-data/xnu/osfmk/kern/ast.h#L105-L152).

## 1. Active bits and service contracts

In the tables, **T** means membership in `AST_PER_THREAD`; **C** means a CPU-pending request outside that mask; **R** means a scheduling reason used by blocking/dispatch code. KPERF is deliberately marked **T-storage/C-mask**: its producer sets `thread->ast`, but the mask excludes it. “User dispatch” means the ordered, enabled-interrupt handler called from `ast_taken_user()`; MACH_EXCEPTION, DTRACE, TELEMETRY, KPERF, and DEBUG_ASSERT also belong to the restricted asynchronous-worker subset. [Membership](../../../platydoc-data/xnu/osfmk/kern/ast.h#L142-L152), [dispatcher](../../../platydoc-data/xnu/osfmk/kern/ast.c#L307-L410), [asynchronous subset](../../../platydoc-data/xnu/osfmk/kern/ast.c#L429-L458).

### Scheduling reasons

| Bit | State and trigger | Consumer and effect |
|---|---|---|
| `AST_PREEMPT` `0x00000001` | C/R. Scheduler checks identify work that should replace the current thread; `ast_check()` transfers the result to CPU pending state. | Kernel service requires URGENT too; user service rechecks `csw_check()` before a nonurgent switch. It is a request to reconsider execution, not a stored pointer to the next thread. [Check](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L5855-L5897), [service](../../../platydoc-data/xnu/osfmk/kern/ast.c#L228-L287). |
| `AST_QUANTUM` `0x00000002` | C/R. Quantum expiration passes QUANTUM to the scheduler's check. | Accompanies the preemption reason and affects dispatch/requeue accounting; user recheck carries this bit forward. It is not a timer callback run by the flavor dispatcher. [Expiry](../../../platydoc-data/xnu/osfmk/kern/priority.c#L228-L245), [dispatch](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L3610-L3660), [recheck](../../../platydoc-data/xnu/osfmk/kern/ast.c#L249-L268). |
| `AST_URGENT` `0x00000004` | C/R. Scheduler requests urgent rescheduling; quantum expiry adds it for `kernel_task`. The nonurgent-preemption timer can upgrade a still-required request. | Makes eligible kernel return/preemption-enable paths service PREEMPT immediately; user handler also prioritizes it before subsystem callbacks. URGENT alone is not a valid request at the assertions requiring PREEMPT. [Quantum](../../../platydoc-data/xnu/osfmk/kern/priority.c#L228-L236), [timer](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L5924-L5958), [kernel/user handling](../../../platydoc-data/xnu/osfmk/kern/ast.c#L119-L192). |
| `AST_HANDOFF` `0x00000008` | R. `thread_run()` supplies HANDOFF when switching directly to a selected thread. | Dispatch can donate the old thread's remaining quantum and convert its reason to QUANTUM. There is no separate HANDOFF user-return callback. [Handoff call](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L3950-L3975), [donation](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L3610-L3634). |
| `AST_YIELD` `0x00000010` | R. Explicit yield/block paths pass YIELD into `thread_block_reason()` or `csw_check()`. | Influences selection and timeslice treatment; not an independently dispatched user AST. [Yield syscall path](../../../platydoc-data/xnu/osfmk/kern/syscall_subr.c#L315-L337), [yield checks](../../../platydoc-data/xnu/osfmk/kern/syscall_subr.c#L620-L660), [blocking setup](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L3874-L3900). |
| `AST_REBALANCE` `0x00100000` | R. `thread_select()` adds this reason when policy requires movement away from the current CPU. | Dispatch selects requeue options based on the reason. It is defined outside `AST_SCHEDULING`, and there is no corresponding user-return callback. [Selection branches](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L2688-L2710), [later selection](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L2857-L2873), [requeue](../../../platydoc-data/xnu/osfmk/kern/sched_prim.c#L3635-L3655). |

The shared namespace is explicit technical debt in the header's “split the context switch and return-to-user AST namespaces” comment. A numeric reason in a scheduler trace therefore does not establish that the same bit was posted to `cpu_pending_ast` or dispatched as a callback. [Namespace comment](../../../platydoc-data/xnu/osfmk/kern/ast.h#L104-L108). See [priority, QoS, and quanta](priority-qos-and-quanta.md) and [selection and context switching](scheduler-execution.md) for the scheduler policies behind these reasons.

### Thread control and policy callbacks

| Bit | State and trigger | Consumer, configuration, and outcome |
|---|---|---|
| `AST_APC` `0x00000020` | T. Suspension/termination code sets it while holding the thread mutex and scheduling lock, propagating locally or requesting an IPI for a running remote target. | `thread_apc_ast()` clears abort flags, terminates an inactive thread, or parks a suspended thread with `thread_suspended` as continuation. The enum's “migration APC hook” comment does not describe this current body. [Producer](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1308-L1351), [consumer](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1390-L1430). |
| `AST_BSD` `0x00000080` | T. `act_set_astbsd()` is used by signal paths; machine/BSD paths also request deferred BSD processing. | Under `MACH_BSD`, `bsd_ast()` accounts process interval timers/CPU limit, handles deferred DTrace process actions when configured, delivers pending signals, and performs the first `bsdinit_task()` call. It can suspend or enter signal/exit handling. [Setter](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1642-L1647), [signal trigger](../../../platydoc-data/xnu/bsd/kern/kern_sig.c#L2428-L2447), [full callback](../../../platydoc-data/xnu/bsd/kern/kern_sig.c#L3361-L3471). |
| `AST_MACF` `0x00000200` | T. `mac_schedule_userret()` requests it for the current thread through `act_set_astmacf()`. | `CONFIG_MACF`: `mac_thread_userret()` invokes the MAC policy `thread_userret` hooks. AST code supplies the safe call site; the hook implementations determine policy, additional references, and outcomes. [Request](../../../platydoc-data/xnu/security/mac_base.c#L1678-L1682), [setter](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1742-L1749), [dispatch to policies](../../../platydoc-data/xnu/security/mac_mach.c#L349-L352). |
| `AST_RESET_PCS` `0x00000400` | T. Restartable-range synchronization or signal handling requests saved-PC correction. Remote synchronization has extra IPI/fault acknowledgment state. | `thread_reset_pcs_ast()` looks up the saved PC in immutable registered ranges and changes it to the registered restart target if appropriate. Setting/clearing this bit alone is not the lifetime barrier for memory a synchronizer will free. [Producer](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1672-L1726), [consumer](../../../platydoc-data/xnu/osfmk/kern/restartable.c#L490-L522), [acknowledgment/wait](../../../platydoc-data/xnu/osfmk/kern/restartable.c#L383-L487). |
| `AST_ARCADE` `0x00000800` | T. The configured prepare path marks non-platform processes with the subscription entitlement. | `CONFIG_ARCADE`: `arcade_ast()` obtains a service send right, prepares a path copy, makes a validation upcall, retries selected dead-server cases, and can terminate the task. The validation service's policy/UI are external to this source. [Trigger](../../../platydoc-data/xnu/osfmk/kern/arcade.c#L82-L100), [callback](../../../platydoc-data/xnu/osfmk/kern/arcade.c#L270-L353). |

### Accounting, exceptions, and resource pressure

| Bit | State and trigger | Consumer, configuration, and outcome |
|---|---|---|
| `AST_LEDGER` `0x00000040` | T. Ledger refill/callback thresholds and CPU-limit policy request service. `le_set_ast()` may use a no-IPI path because the caller already holds the thread lock; PPL dispatch initially records a per-CPU ledger-tab flag. | `ledger_ast()` reconciles configured CPU limits, checks thread/task/coalition ledger entries, invokes eligible callbacks, and can sleep for resources. It resnapshots/rechecks after blocking requests that require a restart, and exits when the task/thread is dying. [Producers](../../../platydoc-data/xnu/osfmk/kern/ledger.c#L730-L805), [consumer](../../../platydoc-data/xnu/osfmk/kern/ledger.c#L1824-L1962). |
| `AST_SFI` `0x00010000` | C/R. Global off-phase timer activity and scheduler classification request selective forced-idle evaluation; remote targets receive AST-check IPIs. | `CONFIG_SCHED_SFI`: serviced after ordinary user callbacks and again if the scheduling recheck returns SFI. `sfi_ast()` reclassifies under locks, enters the class wait queue if still in an off phase, and blocks with its class continuation. It is not in PER_THREAD or SCHEDULING. [Timer](../../../platydoc-data/xnu/osfmk/kern/sfi.c#L320-L343), [classification](../../../platydoc-data/xnu/osfmk/kern/sfi.c#L830-L879), [wait](../../../platydoc-data/xnu/osfmk/kern/sfi.c#L939-L1005), [AST order](../../../platydoc-data/xnu/osfmk/kern/ast.c#L228-L275). |
| `AST_MACH_EXCEPTION` `0x00001000` | T. `thread_ast_mach_exception()` writes one current-thread exception slot; guard violation helpers use it. Existing sticky records cannot be overwritten. | `mach_exception_ast()` snapshots and zeros that slot before guard-specific or fatal handling. An empty lingering request is harmless. This mechanism is not the route for every Mach exception. [Producer](../../../platydoc-data/xnu/osfmk/kern/thread.c#L2425-L2484), [consumer](../../../platydoc-data/xnu/osfmk/kern/thread.c#L2490-L2578), [exception IPC guide](../ipc/exception-delivery.md). |
| `AST_SYNTHESIZE_MACH` `0x02000000` | T. `task_set_ast_synthesize_async_fault_mach_exception()` requests handling across the threads of an active task, with local propagation or a remote IPI when necessary. | `vm_map_synthesize_guard_exception()` claims the map's asynchronous fault record with compare/exchange; losing threads return. It reports the guard fault, with a `HAS_MTE` soft-mode branch. Its payload belongs to the map, distinct from `thread->mach_exc_info`. [Fan-out](../../../platydoc-data/xnu/osfmk/kern/task.c#L10845-L10883), [claim and delivery](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L7760-L7800). |
| `AST_KEVENT` `0x00080000` | T. Kqueue/workqueue code ORs `kevent_ast_bits`, then uses the asynchronous setter. | The dispatcher clears the top-level bit and exchanges the subsidiary bits to zero; `kevent_ast()` redrives work requests, updates return-to-kernel TSD, and/or reevaluates workqueue quantum expiry. These are coalesced reasons, not one callback per event. [Producer](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1650-L1669), [snapshot](../../../platydoc-data/xnu/osfmk/kern/ast.c#L379-L385), [consumer](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L9748-L9764). |
| `AST_PROC_RESOURCE` `0x00400000` | T. IPC-space growth, descriptor allocation, and workloop counts can request deferred limit handling. | `task_port_space_ast()` checks IPC-space limits, followed under `MACH_BSD` by `proc_filedesc_ast()`. The latter's actual work is conditional on `CONFIG_PROC_RESOURCE_LIMITS`; it evaluates descriptor limits first and otherwise workloop limits. Limit state suppresses duplicate reporting; outcomes can include fatal resource reporting. [Port producers](../../../platydoc-data/xnu/osfmk/ipc/ipc_space.c#L510-L536), [FD producers](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L1184-L1200), [workloop producers](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L3515-L3538), [consumers](../../../platydoc-data/xnu/osfmk/kern/task.c#L8600-L8609), [FD/workloop selection](../../../platydoc-data/xnu/bsd/kern/kern_proc.c#L5546-L5578). |

### Profiling, telemetry, and assertions

| Bit | State and trigger | Consumer, configuration, and outcome |
|---|---|---|
| `AST_KPERF` `0x00000100` | T-storage/C-mask. `kperf_ast_pend()` merges sampling flags/action information and calls `act_set_kperf()`; KPC can request buffer allocation. | Dispatcher clears the thread bit, calls KPC handling under `CONFIG_CPU_COUNTERS`, calls Kperf handling, then zeros `kperf_ast`. The sampling handler skips tasks that already exec'd or are exec copies. Unlike most thread-set bits, it is outside PER_THREAD; source comments question that classification. [Pend](../../../platydoc-data/xnu/osfmk/kperf/action.c#L581-L605), [KPC request](../../../platydoc-data/xnu/osfmk/kern/kpc_thread.c#L130-L149), [dispatch](../../../platydoc-data/xnu/osfmk/kern/ast.c#L362-L371), [sampling](../../../platydoc-data/xnu/osfmk/kperf/action.c#L501-L539). |
| `AST_TELEMETRY` `0x00002000` | T. `act_set_telemetry_ast()` ORs `t_telemetry_ast` then posts asynchronously. Sampling, logical writes, MAC hooks, and memory events have different trigger conditions. | `CONFIG_TELEMETRY`: the handler clears the top-level bit and exchanges subsidiary reasons; `telemetry_handle_ast()` builds record flags and chooses generic and/or MACF sampling. It is neither an event count nor a guarantee that sampling succeeds. [Posting/clear](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1757-L1769), [consumer](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L471-L504), [buffer failures](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L1355-L1430). |
| `AST_DTRACE` `0x00020000` | C. A buffer-limit condition sets a bit in global `dtrace_wake_clients` and requests a local AST. | `CONFIG_DTRACE`: `dtrace_ast()` exchanges the global client mask to zero and wakes extant clients with preemption disabled. This defers wakeups out of probe context. It does not consume a `thread->ast` bit. DTrace's deferred signal/stop/resume actions instead run through BSD. [Producer](../../../platydoc-data/xnu/bsd/dev/dtrace/dtrace.c#L12178-L12202), [consumer](../../../platydoc-data/xnu/bsd/dev/dtrace/dtrace.c#L19228-L19252), [BSD actions](../../../platydoc-data/xnu/bsd/kern/kern_sig.c#L3425-L3457). |
| `AST_DEBUG_ASSERT` `0x00800000` | T. Debug paths arm a return invariant check, including lock/promotion/fault-disable conditions; `act_set_debug_assert()` avoids redundant local posting. | `MACH_ASSERT`: verifies no prohibited rwlock/promotion/fault-disable state, and checks Exclaves state when configured. This is also the sole member of AST_LAZY; no use of that composite was found in executable paths. [Setter](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1630-L1640), [checks](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1481-L1506), [LAZY definition](../../../platydoc-data/xnu/osfmk/kern/ast.h#L151-L152). |
| `AST_LARGE_ENTER_TELEMETRY` `0x04000000` | T. `CONFIG_LARGE_SIZE_TELEMETRY`: qualifying large, non-fixed user allocations in guard-object tasks atomically claim `large_allocation_size` from its not-sent sentinel. Several VM tags and opt-out mappings are excluded. | Sends an analytics event with process name and size. DEVELOPMENT/DEBUG can additionally attempt simulated guard reporting. The shown path records telemetry; it does not implement the future denial mentioned in its comment. [Trigger predicate](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L3113-L3134), [consumer](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L2983-L3013). |

## 2. Composite masks, zero, and historical holes

The composites select different work; none should be treated as an interchangeable “all valid ASTs” mask:

[ast.h, lines 139–152](../../../platydoc-data/xnu/osfmk/kern/ast.h#L139-L152)

<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/kern/ast.h#L139-L152 -->
```c
#define AST_NONE                (UINT32_C(0))
#define AST_ALL                 (~AST_NONE)

#define AST_PREEMPTION  (AST_PREEMPT | AST_QUANTUM | AST_URGENT)
#define AST_SCHEDULING  (AST_PREEMPTION | AST_YIELD | AST_HANDOFF)

/* Per-thread ASTs follow the thread at context-switch time. */
#define AST_PER_THREAD  (AST_APC | AST_BSD | AST_MACF | AST_RESET_PCS | \
	AST_ARCADE | AST_LEDGER | AST_MACH_EXCEPTION | AST_SYNTHESIZE_MACH | \
	AST_LARGE_ENTER_TELEMETRY | AST_TELEMETRY | AST_KEVENT | \
	AST_PROC_RESOURCE | AST_DEBUG_ASSERT)

/* ASTs that can be skipped when checking if there's a reason to return to userspace */
#define AST_LAZY (AST_DEBUG_ASSERT)
```

- `AST_PREEMPTION` selects three scheduling bits: PREEMPT, QUANTUM, URGENT.
- `AST_SCHEDULING` adds HANDOFF and YIELD. It excludes REBALANCE and SFI even though scheduler code uses those reasons.
- `AST_PER_THREAD` lists 13 members, defining what `ast_context()` replaces on a CPU switch. It does not filter the incoming thread mask before ORing it into CPU state.
- `AST_LAZY` contains only DEBUG_ASSERT; a source search found no executable use beyond the definition.
- `AST_NONE` is zero. `AST_ALL` is the 32-bit complement of zero, including holes and unnamed bits; it is not an enumeration of supported callbacks.

These are direct readings of the [definitions](../../../platydoc-data/xnu/osfmk/kern/ast.h#L139-L152) and [context propagation](../../../platydoc-data/xnu/osfmk/kern/ast.c#L515-L535). `ASYNC_THREAD_ASTS_HANDLED`, private to `ast.c`, is an additional five-member service subset, not another individual flavor or public header mask. [Definition and use](../../../platydoc-data/xnu/osfmk/kern/ast.c#L429-L458).

| Retired position | Header's former name | Current meaning |
|---|---|---|
| `0x00004000` | `AST_TELEMETRY_KERNEL` | Historical comment; current privilege classification is a telemetry payload bit. |
| `0x00008000` | `AST_TELEMETRY_PMI` | Historical comment; current PMI request is a telemetry payload bit. |
| `0x00040000` | `AST_TELEMETRY_IO` | Historical comment; current IO sampling request is a telemetry payload bit. |
| `0x00200000` | `AST_UNQUIESCE` | Historical comment; no active flavor under this name. |
| `0x01000000` | `AST_TELEMETRY_MACF` | Historical comment; current MACF request is a telemetry payload bit. |

The comments are in [ast.h:124–134](../../../platydoc-data/xnu/osfmk/kern/ast.h#L124-L134). Bits 27–31 also have no named active member in this enum. A debugger decoding a raw mask must preserve unknown bits rather than assigning them one of these retired meanings. The statement concerns the displayed source definition, not a promise that every past or future XNU version shares it. [Complete enum](../../../platydoc-data/xnu/osfmk/kern/ast.h#L109-L137).

## 3. Kevent payload: three reasons under one top-level bit

The `uint16_t` payload is defined identically in the Mach and BSD AST headers. Producers merge reasons before posting the top-level bit; the consumer atomically detaches that reason set before executing it. Multiple posts of the same reason therefore need not produce multiple callback invocations. [Definitions](../../../platydoc-data/xnu/osfmk/kern/ast.h#L216-L221), [BSD mirror](../../../platydoc-data/xnu/bsd/kern/ast.h#L43-L46), [posting](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1650-L1669), [exchange](../../../platydoc-data/xnu/osfmk/kern/ast.c#L379-L385).

| Subsidiary bit | Producer example | Consumer action |
|---|---|---|
| `AST_KEVENT_RETURN_TO_KERNEL` `0x0001` | Kqueue return-to-kernel request ([kern_event.c:5816–5832](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L5816-L5832)). | Writes return-to-kernel flags into registered userspace TSD. No registered address returns without copying; a copyout error is printed, with no rearm in that helper ([kern_event.c:9687–9697](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L9687-L9697)). |
| `AST_KEVENT_REDRIVE_THREADREQ` `0x0002` | A failed deferred workqueue request can post to the current thread ([pthread_workqueue.c:4555–4580](../../../platydoc-data/xnu/bsd/pthread/pthread_workqueue.c#L4555-L4580)). | `workq_kern_threadreq_redrive()` with `WORKQ_THREADREQ_CAN_CREATE_THREADS` ([kern_event.c:9754–9756](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L9754-L9756)). |
| `AST_KEVENT_WORKQ_QUANTUM_EXPIRED` `0x0004` | Thread workqueue-quantum expiration logic ([thread.c:3750–3778](../../../platydoc-data/xnu/osfmk/kern/thread.c#L3750-L3778)). | `workq_kern_quantum_expiry_reevaluate()`; associated TSD flags communicate responsibility to userspace, with atomic 32/64-bit copyout paths ([kern_event.c:9700–9763](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L9700-L9763)). |

Dispatch order is REDRIVE, RETURN_TO_KERNEL, QUANTUM_EXPIRED, not bit order. `act_clear_astkevent()` can clear selected subsidiary reasons separately. This is a reason-set protocol, so callers must use the workqueue/kqueue state machine to decide whether useful work remains. [Consumer](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L9748-L9764), [selective clear](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1660-L1669).

## 4. Telemetry payload: five triggers and two context flags

`telemetry_ast_t` has seven active bits. USER/KERNEL describe the context that caused a request; they are not independent top-level AST flavors or sample-count fields. [Payload definition](../../../platydoc-data/xnu/osfmk/kern/thread.h#L1766-L1818).

| Subsidiary bit | Meaning and producer conditions |
|---|---|
| `TELEMETRY_AST_PMI` `0x0001` | Performance-monitor-triggered sample. The producer is under `HAS_PMI_MICROSTACKSHOTS`, checks `telemetry_sample_pmis`, and counts a skipped request if sampling is disabled. It adds USER or KERNEL ([telemetry.c:438–460](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L438-L460)). |
| `TELEMETRY_AST_IO` `0x0002` | Logical-write sampling request from task accounting ([task.c:8488–8509](../../../platydoc-data/xnu/osfmk/kern/task.c#L8488-L8509)). |
| `TELEMETRY_AST_MACF` `0x0004` | MAC-related sampling hook; handled through the MACF sample path ([telemetry.c:1645–1665](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L1645-L1665), [dispatch](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L490-L502)). |
| `TELEMETRY_AST_VM_FAULT` `0x0008` | The setter writes a 48-bit VA, fault type, and flags, then posts telemetry. The implementation uses `CONFIG_MEMORY_MICROSTACKSHOT` singular ([thread_act.c:1771–1787](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1771-L1787)). |
| `TELEMETRY_AST_PAGE_GRAB` `0x0010` | Setter increments IOPL or UPL count and records a tag before posting; same singular configuration guard ([thread_act.c:1789–1806](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1789-L1806)). |
| `TELEMETRY_AST_USER` `0x1000` | Producer observed userspace; consumer adds the user-mode sample flag ([PMI producer](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L459-L460), [record flags](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L486-L495)). |
| `TELEMETRY_AST_KERNEL` `0x2000` | Producer observed kernel execution; participates in interrupt/PMI record classification ([same producer](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L459-L460), [classification](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L486-L488)). |

The generic sample call requires one of PMI/IO/VM_FAULT/PAGE_GRAB; MACF invokes its own sample path. USER/KERNEL alone do not reach either sampling call. A combined reason set can cause both paths. This is important when interpreting coalesced reasons: the payload describes requested work, not a queue of separate interrupt records. [Exact consumer predicates](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L494-L503).

[telemetry.c, lines 494–503](../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L494-L503)

<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/kern/telemetry.c#L494-L503 -->
```c
	enum micro_snapshot_flags user_telemetry = (reasons & TELEMETRY_AST_USER) ? kUserMode : 0;
	enum micro_snapshot_flags microsnapshot_flags = record_type | user_telemetry;

	if ((reasons & TELEMETRY_AST_MACF) != 0) {
		telemetry_macf_take_sample(thread, microsnapshot_flags);
	}

	if ((reasons & (TELEMETRY_AST_PMI | TELEMETRY_AST_IO | TELEMETRY_AST_VM_FAULT | TELEMETRY_AST_PAGE_GRAB)) != 0) {
		telemetry_take_sample(thread, microsnapshot_flags);
	}
```

The header's VM/page-grab comments use `CONFIG_MEMORY_MICROSTACKSHOTS` and misspell the setter names; the implementation uses singular `CONFIG_MEMORY_MICROSTACKSHOT` and `act_set_telemetry_ast_*`. Follow the body when checking compilation or setting breakpoints. [Header comments](../../../platydoc-data/xnu/osfmk/kern/thread.h#L1789-L1803), [actual functions](../../../platydoc-data/xnu/osfmk/kern/thread_act.c#L1771-L1806).

## 5. Kperf payload and unrelated uses of the word AST

The low Kperf payload flags are `T_KPERF_AST_CALLSTACK=1`, `T_KPERF_AST_DISPATCH=2`, and `T_KPC_ALLOC=4`; `T_KPERF_AST_ALL` combines them. The field also carries action-ID and callstack-depth information using macros at offsets 18 and 24. Those macros are shift operations; this guide does not substitute an inferred packed-field mask for the actual code. `kperf_ast_pend()` merges flags and changes the action information only for the current thread, panicking for a remote target. [Definitions](../../../platydoc-data/xnu/osfmk/kern/thread.h#L863-L882), [merge](../../../platydoc-data/xnu/osfmk/kperf/action.c#L581-L605).

The KPC handler allocates a counter buffer if ALLOC is set; Kperf turns CALLSTACK/DISPATCH into sampler selections. Common dispatch then zeros the entire Kperf payload. Task-exec checks can skip sampling, and this dispatcher does not automatically retry a skipped sample. KPC buffer destruction has its own lifecycle. [KPC handler and destruction](../../../platydoc-data/xnu/osfmk/kern/kpc_thread.c#L208-L232), [Kperf sampling](../../../platydoc-data/xnu/osfmk/kperf/action.c#L501-L539), [payload clear](../../../platydoc-data/xnu/osfmk/kern/ast.c#L362-L371).

Names such as `SCHED_AST_URGENT_SET_REASON_*` are instrumentation reason constants for scheduler request bookkeeping; they are not additional AST bits. Similarly, `kperf_exclaves_ast` and its inspection callback do not add members to `ast_t`: the callback is invoked by Exclave inspection work and has its own payload/context. [Scheduler reason enums](../../../platydoc-data/xnu/osfmk/kern/sched_prim.h#L410-L435), [Exclaves callback](../../../platydoc-data/xnu/osfmk/kperf/action.c#L542-L579). This reference exhausts the top-level enum and the specified sub-bit namespaces, not every symbol whose name contains the substring `AST`.

## 6. Inspection limits

All 22 active top-level bits were matched to their current consumer or scheduler-reason use, with representative producer bodies read for each. The three kevent bits, seven telemetry bits, three Kperf flag bits, public composites, private asynchronous subset, retired comments, and configuration guards were compared against the definitions above. The [mechanism chapter's source table](ast-mechanism.md#sources-inspected-and-limits) records the deeper paths reviewed.

This is a source walkthrough, not execution of a kernel configuration matrix. MAC policy providers, the Arcade validation service, and generated/user-side RPC behavior beyond visible call sites are not reconstructed. Feature guards in a shared enum do not establish that the corresponding feature is active on a particular machine, and an AST request does not promise successful external reporting or a retained reference to every object mentioned by its payload.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
