# Runtime, IPC, and platform documentation coverage audit

[Complete audit](../coverage-audit.md) · [Guide index](../README.md)

This is a documentation-scope audit of **all 34 baseline Markdown chapters** in runtime (12), IPC (10), and platform (12), followed by bounded verification of the source paths that support the recommendations below. It identifies work to do; it does not itself expand the technical chapters, assert that every source file was audited, or report kernel execution. Chapter structure, explanatory depth, reading routes, and stated limits were considered together: a citation alone does not count as coverage.

Requested follow-ups added alongside this audit are [ARM64 exception assembly walkthroughs](../subsystems/platform/arm64-assembly-walkthroughs.md) and [thread switching, entry and exit](../subsystems/platform/arm64-context-switching.md). They are additions to the baseline disposition table below.

**Priorities:** P1 closes a foundational gap needed to connect existing chapters; P2 adds useful implementation depth; P3 is specialized follow-on work. **Disposition:** retain means the current scope is coherent; deepen means an existing explanation needs a fuller mechanism; add-neighbor means preserve the current chapter and link a separate implementation chapter. Proposed filenames below are proposals, not existing links.

## Current strengths and boundaries

**Runtime:** The guides already explain runnable/waiting state, continuation and kernel-stack ownership, Clutch/Edge selection, priority/QoS, quantum expiration, realtime queues, SMT eligibility, mutex contention, turnstile donation, and timer/thread-call cancellation. Their selected paths include difficult retry and cleanup branches. The imbalance is between that depth and the short navigation-level treatment of clocks, Recount, ledgers, coalitions, work-interval accounting, and suspension. See the [runtime overview](../subsystems/runtime/README.md), [scheduler execution](../subsystems/runtime/scheduler-execution.md), and [time/accounting introduction](../subsystems/runtime/time-and-accounting.md).

**IPC:** Names, rights, user/kernel message layouts, message ownership on failure, notifications, port destruction, guards, kernel RPC, exception delivery, voucher caching, and selected importance inheritance already have substantial explanations. The remaining foundational links are synchronous-dependency state, the waitq membership implementation underlying port sets, table growth under concurrent users, and the bank manager behind voucher attribution. The [IPC overview](../subsystems/ipc/README.md) correctly distinguishes modern message paths from unexamined combinations; it should retain that qualification.

**Platform:** ARM64 exception entry/return, protected-domain boundaries, CPU startup/offline/idle, and hibernation creation/restore already have detailed guides. The x86 sleep guide is also substantial. Normal x86 syscall/trap/interrupt execution remains much shallower than ARM64, while cold-boot memory ownership and clock publication are presented mostly as boundaries. [Hardware mappings](../subsystems/platform/hardware-mappings.md) is intentionally an introduction to the existing VM pmap chapters; its brevity does not imply that pmap mechanisms are absent from the documentation tree.

## Every existing chapter: disposition

### Runtime — 12 chapters

| Existing chapter | Disposition | Reason and proposed connection |
|---|---|---|
| [README](../subsystems/runtime/README.md) | Retain | Good execution/policy/lifetime reading route and honest limits; add links after approved expansions. |
| [Objects and lifecycle](../subsystems/runtime/objects-and-lifecycle.md) | Add-neighbor | Creation and staged termination are present; suspension, stop/abort, and resume-token ownership need a separate control-state trace (R5). |
| [Scheduling](../subsystems/runtime/scheduling.md) | Retain | Useful short introduction linking the detailed policy and execution guides. |
| [Scheduler execution](../subsystems/runtime/scheduler-execution.md) | Retain | Covers wake-to-placement, keeping the current thread, stack shortage/handoff, switching, and final termination. |
| [Clutch and Edge](../subsystems/runtime/clutch-and-edge.md) | Retain | Selection hierarchy, starvation/warp, interactivity, cluster placement, and stealing are already concrete. |
| [Priority, QoS, and quanta](../subsystems/runtime/priority-qos-and-quanta.md) | Add-neighbor | Retain policy computation; connect its CPU-limit handoff to ledger execution and refill (R3), rather than repeating the quantum chapter. |
| [Realtime deadlines and runqueues](../subsystems/runtime/realtime-deadlines-and-runqueues.md) | Retain | Accepted parameters, queue ordering, conditional EDF, CPU placement, and shutdown are traced; no need for another generic realtime overview. |
| [CPU eligibility and scheduler variants](../subsystems/runtime/cpu-eligibility-and-scheduler-variants.md) | Retain | Already distinguishes dispatch configuration, recommendation, availability, binding, SMT, dualq, and alternate AMP. |
| [Waits and locks](../subsystems/runtime/waits-and-locks.md) | Add-neighbor | Mutex and wait introduction is supported by a deep guide; RW/ticket variants currently stop at contracts (R4). |
| [Wait and turnstile protocols](../subsystems/runtime/wait-and-turnstile-protocols.md) | Retain | Detailed registration, detach-before-runnable, inheritor references, and generation-checked propagation; IPC dependency state belongs beside it (I1). |
| [Time and accounting](../subsystems/runtime/time-and-accounting.md) | Deepen | Keep as the introduction, but its one-paragraph measurement/limit/attribution descriptions need neighboring clock, Recount, ledger, and bank traces (R1–R3, I4). |
| [Timer and thread-call lifetime](../subsystems/runtime/timer-and-thread-call-lifetime.md) | Retain | Selected cancellation/free/worker/ONCE/SIGNAL paths are deep; clock domains are the missing prerequisite (R1), not another cancellation explanation. |

### IPC — 10 chapters

| Existing chapter | Disposition | Reason and proposed connection |
|---|---|---|
| [README](../subsystems/ipc/README.md) | Retain | Strong names-to-message-to-dispatch route with explicit limits. |
| [Names and rights](../subsystems/ipc/names-and-rights.md) | Deepen | Entry/name/uref/SMR lookup is covered; table growth is a brief explanation without its concurrent rescan/publication protocol (I3). |
| [Ports and rights lifecycle](../subsystems/ipc/ports-and-rights-lifecycle.md) | Retain | Covers transfer, circularity, death, notifications, and space teardown; port-set internals should be an adjacent chapter (I2). |
| [Message path](../subsystems/ipc/message-path.md) | Retain | Explains ABI packing, layout changes, and trap entry before the deeper ownership trace. |
| [Message send/receive](../subsystems/ipc/message-send-receive.md) | Add-neighbor | Queue capacity, direct delivery, receive/copyout, and errors are substantive; connect port-set readiness and synchronous dependencies to their implementations (I1/I2). |
| [Kernel RPC and exceptions](../subsystems/ipc/kernel-rpc-and-exceptions.md) | Retain | Correct distinction between trap dispatch and MIG/kobject RPC; generated stub implementations require an actual build, not invented source. |
| [Exception delivery](../subsystems/ipc/exception-delivery.md) | Retain | Handler snapshot, fallback, behavior payload, kernel RPC, and reply-state validation are traced; specialized corpse/hardened cases remain explicit limits. |
| [Policies and attribution](../subsystems/ipc/policies-and-attribution.md) | Add-neighbor | Good orientation, but synchronous-link and bank mechanisms remain interface summaries (I1/I4). |
| [Guards and policy enforcement](../subsystems/ipc/guards-and-policy-enforcement.md) | Retain | Guard/context, movement/destruction, deferred exception, reply context, and notification policy are concrete; security policy expansion is separately coordinated. |
| [Vouchers and importance](../subsystems/ipc/vouchers-and-importance.md) | Add-neighbor | Recipe/cache/no-senders/release reconciliation and selected importance inheritance are already deep; add the bank implementation behind adoption (I4). |

### Platform — 12 chapters

| Existing chapter | Disposition | Reason and proposed connection |
|---|---|---|
| [README](../subsystems/platform/README.md) | Retain | Routes and source limits are useful; add x86 normal-entry and bootstrap-memory neighbors if approved. |
| [Boot](../subsystems/platform/boot.md) | Add-neighbor | STARTUP and boot-to-PID1 order are present; bootstrap allocations, temporary mappings/stacks, and release-to-VM require a narrower ownership chapter (P2). |
| [Execution](../subsystems/platform/execution.md) | Add-neighbor | Works as ARM-oriented orientation; needs a symmetric normal x86 entry/return route (P1). |
| [ARM64 exception entry](../subsystems/platform/arm64-exception-entry.md) | Retain | Vector/configuration, saved-state, stacks, SVC/fault, IRQ, and monitor-visible boundaries are already traced. |
| [ARM64 exception return](../subsystems/platform/arm64-exception-return.md) | Retain | Covers AST eligibility, continuations, PFZ, authenticated restore, and final trampoline/translation transitions. |
| [Exception levels and monitors](../subsystems/platform/exception-levels-and-monitors.md) | Retain | Explicitly separates architectural EL2 from Apple protected-domain interfaces and missing external implementations. |
| [Hardware mappings](../subsystems/platform/hardware-mappings.md) | Retain | Orientation and crosslinks are appropriate; evaluate pmap detail in the VM audit, not by this chapter's length. |
| [Platform services](../subsystems/platform/platform-services.md) | Add-neighbor | Device-tree borrowing and platform callback boundaries are covered; clock/commpage publication needs depth (R1), virtualization remains a specialized possible follow-on. |
| [CPU power lifecycle](../subsystems/platform/cpu-power-lifecycle.md) | Retain | CPU registration/start/offline/idle and sleep-time bridge are substantial; link the proposed clock chapter rather than repeat power ordering. |
| [Hibernation image creation](../subsystems/platform/hibernation-image-creation.md) | Retain | Selected resource ownership, VM bitmap/discard, image encoding, and polled-I/O boundaries are detailed. |
| [Hibernation restore](../subsystems/platform/hibernation-restore.md) | Retain | Separates early physical restore, temporary mappings, metadata reconstruction, late restore, and missing monitor internals. |
| [x86 sleep and resume](../subsystems/platform/x86-sleep-and-resume.md) | Retain | ACPI, wake page tables, assembly save/restore, clock rebase, and CPU restart are already traced; ordinary x86 execution remains separate (P1). |

## Prioritized expansion candidates

### R1 — P1: clocks, time domains, and publication to userspace

**Current gap:** [Time/accounting](../subsystems/runtime/time-and-accounting.md) discusses timer queues, while [platform services](../subsystems/platform/platform-services.md) briefly describes commpage publication. Neither follows a clock read through its source, conversion, consistency protocol, and relation to sleep or calendar adjustment. The existing timer and sleep chapters should remain the consumers of this explanation.

**Local evidence:** `mach_continuous_time()` has distinct continuous-hardware-clock and software sleep-offset paths; the latter retries when the offset changes around its absolute-time read. This is implemented, not just an API comment. Calendar reads and commpage updates are centralized separately in `clock_gettimeofday_and_absolute_time()`. See [clock.c:690–712](../../xnu/osfmk/kern/clock.c#L690-L712) and [clock.c:1727–1746](../../xnu/osfmk/kern/clock.c#L1727-L1746). The sleep test is explicitly gated by `MCT_SLEEP_TEST`; its presence is not evidence that sleep was tested here ([mach_continuous_time.c:161–183](../../xnu/tests/mach_continuous_time.c#L161-L183)).

**Proposed chapter:** `runtime/clocks-and-time-domains.md`. Answer: Which quantities include sleep? Which are clock-adjustable? How do scale/offset and hardware-counter readers differ by build? Which writer/reader barriers make commpage snapshots coherent? Where do deadline conversions saturate? How do calendar changes differ from continuous-time rebasing? Follow one kernel read and one available userspace read implementation, then link the existing power chapters. **Benefit/dependencies:** foundational to timers, scheduling measurements, trace timestamps, and wake behavior; separate externally supplied RTC/platform behavior from local conversion code.

### R2 — P1: Recount, exited usage, coalitions, and work-interval accounting

**Current gap:** [Time/accounting](../subsystems/runtime/time-and-accounting.md) identifies measurement versus attribution, but does not explain a snapshot delta or why exited-thread/task accounting remains visible. Scheduler policy chapters mention work intervals for eligibility and groups, which does not cover accounting ownership.

**Local evidence:** `recount_absorb_snap()` starts sequence-locked updates for thread, optional work interval, task, and processor; idle execution has a different attribution rule. `recount_switch_thread()` computes the difference from the prior processor snapshot before absorption ([recount.c:1026–1103](../../xnu/osfmk/kern/recount.c#L1026-L1103)). Separate rollups preserve task and coalition aggregates ([recount.c:556–569](../../xnu/osfmk/kern/recount.c#L556-L569)). A local regression test checks increasing `getrusage` across thread exit ([recount_tests.c:630–660](../../xnu/tests/recount/recount_tests.c#L630-L660)).

**Proposed chapter:** `runtime/recount-and-resource-attribution.md`. Answer: Who owns each track array? Which topology and execution-level index is chosen? How do sequence locks provide a consistent read without making all CPUs atomic together? Where are snapshots taken at switch/exception boundaries? How are terminated thread/task values transferred, and how are live coalition members combined with exited usage? What does joining or leaving a work interval change in accounting? Explain `RECOUNT_ENERGY`, PMC availability, and topology configuration rather than assuming every metric exists. **Benefit/dependencies:** ties scheduler activity to observable task/coalition statistics; provides the measurement prerequisite for R3 and I4. Existing [Recount design notes](../../xnu/doc/observability/recount.md) are useful prior documentation, not a replacement for the current call paths.

### R3 — P2: ledgers, scalable settlement, and enforcement

**Current gap:** The [time/accounting introduction](../subsystems/runtime/time-and-accounting.md) names limits/refill; the [priority guide](../subsystems/runtime/priority-qos-and-quanta.md) reaches CPU-limit effects. Neither follows ledger updates through settlement and AST enforcement.

**Local evidence:** The implementation contains distinct ordinary/scalable credit paths and an AST handler that reconciles task/thread CPU-limit requests, including `CONFIG_SCHED_RT_ALLOW` ([ledger.c:1179–1288](../../xnu/osfmk/kern/ledger.c#L1179-L1288), [ledger.c:1825–1905](../../xnu/osfmk/kern/ledger.c#L1825-L1905)). The unit test explicitly disables preemption, creates a scalable template, checks credit/debit, and shows that an open tab delays visible settlement ([test_ledgers.c:57–95](../../xnu/tests/unit/test_ledgers.c#L57-L95)).

**Proposed chapter:** `runtime/ledgers-limits-and-settlement.md`. Answer: What do entry balance, limits, maxima, warning state, and refill represent? What is temporarily held in per-CPU tabs? Which reads settle it, with what locking/preemption requirements? How does credit trigger AST work rather than execute all callbacks inline? When can an over-limit thread block, wake, or change its limit? Which task/coalition teardown references keep the ledger alive? **Benefit/dependencies:** explains CPU/memory accounting consumers without confusing a balance with a measurement snapshot; build on R2 and link memory-pressure enforcement rather than duplicate it.

### R4 — P2: RW, ticket, and pointer-lock variants

**Current gap:** [Waits and locks](../subsystems/runtime/waits-and-locks.md) correctly warns that the old RW implementation is the default and identifies the newer implementation. It does not trace upgrade failure, reader/writer admission, wake choice, destruction, or ticket invalidation. The mutex/turnstile chapter already covers its own mechanism.

**Local evidence:** The default selection is explicit in [lock_rw.h:40–48](../../xnu/osfmk/kern/lock_rw.h#L40-L48). The old writer path rechecks under an embedded interlock, sets waiter state, registers a wait, and then blocks ([lock_rw_old.c:589–611](../../xnu/osfmk/kern/lock_rw_old.c#L589-L611)). The new shared-to-exclusive path releases the shared hold and returns false when another upgrader is already present ([lock_rw.c:1763–1788](../../xnu/osfmk/kern/lock_rw.c#L1763-L1788)). Ticket locks separately expose allow-invalid acquisition and invalidation ([lock_ticket.c:910–938](../../xnu/osfmk/kern/lock_ticket.c#L910-L938)).

**Proposed chapter:** `runtime/rw-ticket-and-pointer-locks.md`. Answer: Which implementation does a declared type select? What ownership remains after failed upgrade? When is preemption disabled and when can an API sleep? How do waiter registration and unlock avoid lost wakeups? How can invalidation coexist with reserved tickets? Establish pointer-lock implementation and callers before adding that section; its full body was not traced in this audit. **Benefit/dependencies:** immediately useful for VM/map/VFS readers; requires the existing waitq introduction, not another scheduler overview. Test expansion should distinguish generic [locks tests](../../xnu/tests/locks.c#L1) from kernel-side variant-specific routines, rather than imply that one test covers all lock algorithms.

### R5 — P2: task/thread suspension and execution-control lifetime

**Current gap:** [Objects and lifecycle](../subsystems/runtime/objects-and-lifecycle.md) explains creation and termination; it leaves suspension, stopping, abort, and resumption mostly to neighboring references. A retained task is not thereby running, suspended, or terminated.

**Local evidence:** `task_suspend2_grp()` takes a task reference after placing the hold and returns a suspension token; `task_resume_internal()` changes hold state while its caller owns token management; `task_resume2_grp()` consumes the token reference even after the internal operation returns ([task.c:4276–4351](../../xnu/osfmk/kern/task.c#L4276-L4351)). Dedicated source tests examine suspension statistics and sources ([task_suspend_stats.c:279–318](../../xnu/tests/task_suspend_stats.c#L279-L318)).

**Proposed chapter:** `runtime/suspension-stop-and-abort.md`. Answer: How do nested user holds differ from scheduler wait/stop state? Which AST or wake path makes a target stop? What does a suspension token own, including port no-senders and task death? Which operations may stop the current thread, fail on an inactive target, or leave a hold outstanding? Trace thread abort/safe-abort separately from task resume. **Benefit/dependencies:** connects task objects to IPC tokens and debugger/process-control behavior; coordinate task-right authorization details with the security audit rather than duplicate them.

### I1 — P1: synchronous IPC dependencies and special-reply state

**Current gap:** [Policies/attribution](../subsystems/ipc/policies-and-attribution.md) and [exception delivery](../subsystems/ipc/exception-delivery.md) identify the special reply port and destination turnstile. They do not follow the full dependency-link state machine or the workloop handoff. Ordinary reply right ownership and strict reply policy are already covered elsewhere.

**Local evidence:** `ipc_port_link_special_reply_port()` prepares a destination send turnstile before locking the reply port, either installs a referenced destination in `PORT_SYNC_LINK_PORT` or drops the unused prepared reference ([ipc_port.c:1867–1913](../../xnu/osfmk/ipc/ipc_port.c#L1867-L1913)). Adjustment can replace port, knote, or stashed-turnstile state, and completes inherited-priority cleanup after dropping the message-queue lock ([ipc_port.c:2111–2188](../../xnu/osfmk/ipc/ipc_port.c#L2111-L2188)). The local regression test constructs a kqueue/port-descriptor scenario specifically for a stashed turnstile reference ([port_turnstile_stash.c:20–80](../../xnu/tests/ipc/port_turnstile_stash.c#L20-L80)).

**Proposed chapter:** `ipc/synchronous-dependencies-and-special-replies.md`. Answer: Who owns each state-dependent union member? When does client donation target a port, server thread, or workloop? Which lock serializes state changes? How do receive completion, interruption, port death, and link loss unwind references? How does a queued message change the dependency before the server runs? **Benefit/dependencies:** closes the central IPC-to-scheduler gap; build on runtime turnstiles and coordinate kqueue/workloop consumers with process/event documentation.

### I2 — P2: port-set membership and persistent readiness

**Current gap:** [Message send/receive](../subsystems/ipc/message-send-receive.md) explains the port-set receive consumer; [rights lifecycle](../subsystems/ipc/ports-and-rights-lifecycle.md) explains API membership and set destruction. The waitq link/prepost representation beneath those operations remains shallow.

**Local evidence:** `ipc_pset_destroy()` wakes waiters, invalidates the set, unlinks membership under the set lock, then drops its reference and frees detached links ([ipc_pset.c:236–264](../../xnu/osfmk/ipc/ipc_pset.c#L236-L264)). The waitq implementation maintains distinct member and preposted link lists and traverses both ([waitq.c:1871–1883](../../xnu/osfmk/kern/waitq.c#L1871-L1883)); its in-kernel test performs link/unlink with both locks and frees unused or detached storage afterward ([waitq.c:2544–2588](../../xnu/osfmk/kern/waitq.c#L2544-L2588)).

**Proposed section/chapter:** `ipc/port-sets-and-waitq-readiness.md`. Answer: How is an already-nonempty port remembered when no receiver is asleep? How does readiness move between membership/prepost lists, and when is it cleared? What are link allocation and locking contracts? How do remove-one, move-membership, and set destruction affect other members and blocked receivers? **Benefit/dependencies:** lets readers reason about multiplexing without confusing a set's readiness with a second copy of the message; reuse the existing receive and wait registration traces.

### I3 — P2: IPC namespace growth and resource exhaustion

**Current gap:** [Names and rights](../subsystems/ipc/names-and-rights.md) already explains generations and SMR lookup. Table growth is summarized, but the concurrent rescan and failure branches are not explained as a protocol.

**Local evidence:** `ipc_entry_grow_table()` waits for another grower, chooses a bounded target, marks modified-index bounds, drops the space lock, allocates and copies a table while rebuilding reverse hashes ([ipc_entry.c:624–748](../../xnu/osfmk/ipc/ipc_entry.c#L624-L748)). It then detects space death or modifications and rescans; only a stable table is published and the old table retired. Maximum size returns `KERN_NO_SPACE` ([ipc_entry.c:770–844](../../xnu/osfmk/ipc/ipc_entry.c#L770-L844)).

**Proposed section:** extend `names-and-rights.md` with “Growing a live namespace.” Answer: Why may unlocked snapshots be inconsistent without becoming authoritative? What precisely marks the rescan interval? Which caller lock state follows each failure? How do allocation failure, concurrent termination, and configured maximum differ? Why is publication not the point at which old readers disappear? **Benefit/dependencies:** a compact implementation case study in concurrent replacement and resource bounds; avoid repeating the already-covered SMR lookup and notification request-table growth algorithms.

### I4 — P2: bank accounts, voucher adoption, and charging

**Current gap:** [Vouchers and importance](../subsystems/ipc/vouchers-and-importance.md) follows voucher-manager ownership and adoption but explicitly leaves full bank account/ledger creation outside its scope. This is a local implementation gap, not missing external policy.

**Local evidence:** `bank_account_alloc_init()` allocates a bill, matches an existing account using merchant/originator/proximate process/group/persona, and links a new account into holder-pay and merchant-charge lists under their locks ([bank.c:1058–1130](../../xnu/osfmk/bank/bank.c#L1058-L1130)). Deallocation rejects a stale `ba_made` synchronization value before rollup/removal ([bank.c:1234–1295](../../xnu/osfmk/bank/bank.c#L1234-L1295)). `bank_swap_thread_bank_ledger()` computes elapsed quantum and energy deltas while holding the thread lock, switches the ledger pointer, and credits the previous bill afterward ([bank.c:1898–1963](../../xnu/osfmk/bank/bank.c#L1898-L1963)).

**Proposed chapter:** `ipc/bank-accounts-and-charging.md`. Answer: Which roles identify an account and which task owns each reference? How do voucher made/reference counts differ from account lifetime? How does thread adoption divide a quantum without double charging? How do live bills and task teardown produce final totals? How do group/persona data travel without being equivalent to a security authorization decision? **Benefit/dependencies:** concrete bridge from messages to resource attribution; depends on the existing voucher cache chapter and R2/R3. Coordinate persona authorization with security rather than infer it from billing roles.

### P1 — P1: ordinary x86 syscall, trap, and interrupt return

**Current gap:** [Execution](../subsystems/platform/execution.md) and the two ARM exception chapters have no equally detailed normal x86 counterpart. [x86 sleep/resume](../subsystems/platform/x86-sleep-and-resume.md) is a different path and should not be expanded into an entry chapter.

**Local evidence:** `idt64_syscall` performs GS transitions, temporarily preserves the syscall number, switches from the user stack to a per-CPU exception stack, and synthesizes an interrupt frame ([idt64.s:534–574](../../xnu/osfmk/x86_64/idt64.s#L534-L574)). `return_from_trap` obtains saved state, handles pending ASTs including PFZ deferral, and rechecks after possible continuation ([idt64.s:1542–1579](../../xnu/osfmk/x86_64/idt64.s#L1542-L1579)). Separate return branches include `iret` and `sysretq` ([idt64.s:782–852](../../xnu/osfmk/x86_64/idt64.s#L782-L852)).

**Proposed chapter:** `platform/x86-entry-and-return.md`. Answer: Which IDT/MSR entry is selected? Where do GS, CR3, stacks, and saved-state formats change? How are Mach and Unix calls classified? What differs for kernel-origin faults, IST/NMI, and recoverable faults during return? When is SYSRET eligible, and what forces IRET? Follow AST/preemption conditions without assuming the ARM rules carry over. **Benefit/dependencies:** foundational architecture parity for the existing IPC/process guides; configuration and 32-bit compatibility paths must be labeled rather than collapsed into a single x86 path.

### P2 — P2: cold-boot memory ownership and release to VM

**Current gap:** [Boot](../subsystems/platform/boot.md) traces initialization order, while [hardware mappings](../subsystems/platform/hardware-mappings.md) points to mature pmap machinery. The transition between temporary bootstrap storage and ordinary VM ownership is not a full narrative.

**Local evidence:** `arm_vm_prot_finalize()` releases pre-kernel regions to VM while retaining the physical mapping, tightens selected segment permissions, allocates/replaces the boot CPU stack, and releases BOOTDATA; monitor/configuration conditions further change cleanup ([arm_vm_init.c:1654–1703](../../xnu/osfmk/arm64/arm_vm_init.c#L1654-L1703)). The distinction between physical eligibility for allocation and the existence of an address translation is therefore visible in local code, not only architectural background.

**Proposed chapter:** `platform/bootstrap-memory-and-lockdown.md`. Answer: Which boot arguments and image segments establish physical reservations? Which allocator may run before general VM and zones exist? Which temporary tables/stacks remain usable until a specific handoff? When does protection tighten, and when does memory become reusable? Compare legacy and SPTM local preparation/handoff while leaving external monitor implementation opaque. **Benefit/dependencies:** joins boot order to the VM mapping guides; coordinate with the pmap fundamentals work and existing IOKit lockdown narrative to avoid duplicating them.

## Follow-on limits and what not to expand by assumption

The eleven candidates above are the recommended bounded backlog. P3 follow-ons could investigate long-term timer migration/coalescing, further importance-graph propagation, or local hypervisor-provider registration/VMX lifetime. Their complete paths were **not** verified for this audit, so they are not promoted to implementation-ready recommendations. Existing guides already declare these limits.

Missing provider bodies are a different category. Protected-monitor calls, some PPL crossings, firmware/SoC behavior, the external hypervisor provider, and generated MIG stubs must remain interface/build boundaries until the relevant implementation or generated artifact is available. The [monitor guide](../subsystems/platform/exception-levels-and-monitors.md), [platform services](../subsystems/platform/platform-services.md), and [kernel RPC guide](../subsystems/ipc/kernel-rpc-and-exceptions.md) already make those distinctions. More local documentation cannot honestly reconstruct those missing implementations.

Configuration and tests should be part of each approved expansion, not a detached list: inspect the selected definitions and branches, use tests to identify intended contracts and failure cases, and report whether they were actually run. This audit read representative test bodies and local implementation branches; it did not build or execute XNU or tests. Timekeeping's sleep-test gate, ledger tests' preemption requirement, Recount's exit monotonicity test, and IPC's stashed-turnstile reference test are concrete starting points, not claims of comprehensive test coverage.
