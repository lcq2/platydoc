# Time, deferred work, and resource attribution

[Runtime overview](README.md) · [Scheduling](scheduling.md)

For callback ownership and shutdown, continue with [timers and thread-call lifetime](timer-and-thread-call-lifetime.md), including the different ordinary-call and `ONCE` cancel-wait branches.

## Reading the time and accounting paths

1. [ARM64 clocks and time domains](clocks-and-time-domains.md): hardware/absolute/continuous ticks, calendar scaling, sleep adjustment, commpage publication and the local userspace read paths.
2. [Recount and resource attribution](recount-and-resource-attribution.md): execution snapshots, track topology/sequence reads, live and exited task/coalition totals, and work-interval ownership.
3. [Ledgers, limits and settlement](ledgers-limits-and-settlement.md): entry representation, per-CPU tabs, remote flushes, refill, callback publication and blocking at `AST_LEDGER`.
4. [Bank accounts and charging](../ipc/bank-accounts-and-charging.md): voucher-derived account roles, deduplication/references, adoption, quantum splitting, bill reporting and teardown.

A Recount snapshot measures execution; a ledger stores resource balances; a bank account attributes selected work to another holder. Their fields and aggregation rules should not be added together without following the relevant reporting contract.

## Timer calls and thread calls

| Mechanism | Structure and execution path | Main distinction |
|---|---|---|
| Timer call | `timer_call`: `tc_func`, parameters, soft deadline, deadline-queue links, queue pointer, lock. `timer_call_enter_internal()` → timer queue → `timer_queue_expire_with_options()`. | Low-level timed callback mechanism used by scheduler waits and other timing machinery. [`timer_call.h`](../../../platydoc-data/xnu/osfmk/kern/timer_call.h#L72), [`timer_call.c`](../../../platydoc-data/xnu/osfmk/kern/timer_call.c#L657). |
| Thread call | A `thread_call` belongs to a priority group with pending/delayed queues, timers, worker counts, and wait queues. `thread_call_thread()` consumes pending callbacks. | Normal work executes on managed kernel worker threads, after dropping the group lock and restoring interrupts. [`thread_call.c`, groups](../../../platydoc-data/xnu/osfmk/kern/thread_call.c#L71), [`thread_call.c`, worker](../../../platydoc-data/xnu/osfmk/kern/thread_call.c#L1711). |

`timer_call_enter_internal()` preserves the requested soft deadline, derives coalescing slack from urgency and, for the applicable user urgency classes, the current thread, optionally expands it using explicit leeway, and chooses a long-term or ordinary timer queue. The expiration path removes the timer and drops queue/call locks before invoking the callback. This lock release does not make the callback a worker-thread function: timer interrupt context still constrains what it may do. [`timer_call.c`, enqueue](../../../platydoc-data/xnu/osfmk/kern/timer_call.c#L657), [`timer_call.c`, callback](../../../platydoc-data/xnu/osfmk/kern/timer_call.c#L1010).

A delayed thread call is a useful bridge. The group's timer invokes `thread_call_delayed_timer()`, which moves expired ordinary entries onto the pending queue. Worker threads run them through `thread_call_invoke()`. `THREAD_CALL_SIGNAL` is an explicit exception: that path invokes the callback directly from delayed-timer processing. Consequently, determine the allocation/options flags before assuming a callback may block. The implementation separately tracks absolute and continuous-time delayed queues. [`thread_call.c`](../../../platydoc-data/xnu/osfmk/kern/thread_call.c#L1999), [`thread_call.c`, execution](../../../platydoc-data/xnu/osfmk/kern/thread_call.c#L1795).

Cancellation is a lifetime issue. A failed queue cancellation may mean an invocation is already in flight. `thread_call_cancel_wait()` handles waiting, checks for self-deadlock and interrupt context, and distinguishes `THREAD_CALL_ONCE` from normal calls; its comments also warn about concurrent resubmission. In particular, an ordinary non-`ONCE` call that successfully cancels pending work returns without waiting for an earlier concurrent invocation; an `ONCE` call cancels pending work and waits for the running invocation. See the [branch-by-branch treatment](timer-and-thread-call-lifetime.md#7-cancellation-api-behavior-is-branch-dependent). Thread teardown demonstrates the analogous timer problem by canceling the wait timer and waiting for the active-expiration count to drain. [`thread_call.c`](../../../platydoc-data/xnu/osfmk/kern/thread_call.c#L1391), [`thread.c`](../../../platydoc-data/xnu/osfmk/kern/thread.c#L642).

## Measurement, limits, and attribution are separate jobs

**Recount measures execution.** Its tracks hold time by execution level and, when configured, instruction/cycle counts and energy. Plans define aggregation topology: system, CPU, or CPU kind. `recount_switch_thread()` computes the difference from the CPU's previous counter snapshot, absorbs it into the outgoing thread/task/processor accounting, and saves the new snapshot. Some architecture configurations track user/kernel transitions more precisely than others; the header explicitly conditions thread-based level tracking on arm64. [`recount.h`](../../../platydoc-data/xnu/osfmk/kern/recount.h#L44), [`recount.c`](../../../platydoc-data/xnu/osfmk/kern/recount.c#L1083).

**Ledgers provide resource balances and limits.** Entry features include historical debit, maxima, refill intervals, and scalable backing, with incompatible combinations documented in the header. Task/thread creation instantiates ledgers; `ledger_credit()` and `ledger_debit()` update them, while `ledger_ast()` handles current-thread policy work and CPU-limit requests. Recount and ledgers are related accounting systems, but neither should be treated as merely another name for the other. [`ledger.h`](../../../platydoc-data/xnu/osfmk/kern/ledger.h#L119), [`ledger.c`, updates](../../../platydoc-data/xnu/osfmk/kern/ledger.c#L1179), [`ledger.c`, AST](../../../platydoc-data/xnu/osfmk/kern/ledger.c#L1825).

**Coalitions aggregate related tasks.** `struct coalition` has type, ID, reference count, active count, lifecycle flags, a lock, and resource/jetsam-specific state. Active count includes members and voucher references; storage references and logical activity therefore differ. `coalitions_adopt_task()` and `coalitions_remove_task()` connect membership to task lifetime. For resource reporting, continue at `coalition_resource_usage_internal()` and the original [coalitions guide](../../../platydoc-data/xnu/doc/observability/coalitions.md); jetsam policy belongs with [VM](../vm/README.md). [`coalition.c`, structure](../../../platydoc-data/xnu/osfmk/kern/coalition.c#L270), [`coalition.c`, membership](../../../platydoc-data/xnu/osfmk/kern/coalition.c#L2047).

## Work intervals and vouchers connect work to scheduling

`struct work_interval` represents identified work with creation flags, creator identity, a reference count, optional thread group, workload class/offset, and Recount storage. Work-interval-driven policy can supply a thread's priority, while auto-join paths propagate membership under configured conditions. The object comments specifically explain deferred destruction: the final release may occur in the scheduler while a thread lock is held, requiring another thread to free it. Start with `work_interval_set_policy()`, `work_interval_auto_join_propagate()`, and `work_interval_thread_terminate()`. [`work_interval.c`, structure](../../../platydoc-data/xnu/osfmk/kern/work_interval.c#L152), [`work_interval.c`, propagation](../../../platydoc-data/xnu/osfmk/kern/work_interval.c#L460), [`work_interval.c`, policy](../../../platydoc-data/xnu/osfmk/kern/work_interval.c#L765).

An `ipc_voucher` is an immutable-after-creation set of indices into resource-manager attribute values, with its own references and representing port. The bank manager supplies attribution metadata: `bank_task` links accounts payable/chargeable, while `bank_account` identifies merchant/holder and carries the temporary ledger and optional adopted thread group. These structures explain how work can be charged to a client while executing in another task. [`ipc_voucher.h`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.h#L68), [`bank_internal.h`](../../../platydoc-data/xnu/osfmk/bank/bank_internal.h#L68).

The connecting operation is concrete: `thread_set_voucher_name()` converts the port name to a voucher reference, asks `bank_get_bank_ledger_thread_group_and_persona()` for bank attributes, replaces `ith_voucher` under the thread mutex, swaps the bank ledger, updates bank-derived thread-group state, and releases the previous voucher. Follow [IPC](../ipc/README.md) for transport and redemption, and the bank functions for attribution rules. [`thread.c`](../../../platydoc-data/xnu/osfmk/kern/thread.c#L3364), [`bank.c`](../../../platydoc-data/xnu/osfmk/bank/bank.c#L1823).

The companion chapters above trace the measurement, balance, attribution and ownership paths behind this overview. Full workload-policy combinations, external runtime behavior and empirical accounting accuracy remain separate questions. The source's [Recount guide](../../../platydoc-data/xnu/doc/observability/recount.md) and [coalition guide](../../../platydoc-data/xnu/doc/observability/coalitions.md) provide additional design context.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
