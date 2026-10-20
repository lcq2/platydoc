# Port policy and work attribution

[IPC overview](README.md) · [Kernel interfaces and exceptions](kernel-rpc-and-exceptions.md)

This introduction continues in [guards and policy enforcement](guards-and-policy-enforcement.md) and [vouchers, attribute caches, and importance inheritance](vouchers-and-importance.md), which trace the locking, reference counts, failure paths, and deferred completion behind these interfaces.

## Several independent properties constrain a right

A port's object type, its receive-right location/state, a space entry's send-right flags, and a guard context answer different questions. `mach_port_construct()` validates the requested port type, derives an object label from options and space policy, checks construction restrictions, and initializes the port. `ipc_policy_array` supplies type-specific receive movability, send movability, notification support, and reply semantics. Its initial values can be adjusted by policy tunables, so read the initialization and enforcement together. [`mach_port.c`](../../../xnu/osfmk/ipc/mach_port.c#L2420), [`ipc_policy.c`](../../../xnu/osfmk/ipc/ipc_policy.c#L1614).

| Property | Implementation meaning |
|---|---|
| Object type | Ordinary, service, connection, reply, special reply, exception, and kobject ports have different policy. This is distinct from a task kobject's control/read/inspect/name capability flavor. |
| Immovable receive right | Object state/policy prevents an otherwise valid receive-right transfer. Some types allow one transfer or transfer after a port-destroyed notification. |
| Immovable send right | Copyin policy restricts transferring the send capability out of its space. Entry flags and port policy participate. |
| Pinned send entry | The last user reference cannot be consumed through ordinary deallocation/move paths that enforce pinning. |
| Guard | A caller-supplied context protects selected receive-right operations against mismatched or unintended use. |

The representations and enforcement points are [`ipc_object.h`](../../../xnu/osfmk/ipc/ipc_object.h#L179), [`ipc_entry.h`](../../../xnu/osfmk/ipc/ipc_entry.h#L109), [`ipc_right_copyin()`](../../../xnu/osfmk/ipc/ipc_right.c#L2112), and [`mach_port_guard_locked()`](../../../xnu/osfmk/ipc/mach_port.c#L2278). For example, a `MOVE_SEND` of the final user reference checks pinning before taking the ordinary ownership-transfer path; a receive transfer checks the port's move policy and any supplied guard descriptor.

`mach_port_guard_locked()` records `ip_context`, sets `ip_guarded` and optionally `ip_strict_guard`, and can mark the receive right immovable. Unguarding requires an existing guard and matching context. Guard failures can be reported through `mach_port_guard_exception()`, which encodes the reason and target for the thread guard-violation path. Delivery/enforcement depends on the reason and configured policy; a guard report is not uniformly equivalent to immediate termination. [`mach_port.c`](../../../xnu/osfmk/ipc/mach_port.c#L2278), [`ipc_policy.c`, guard generation](../../../xnu/osfmk/ipc/ipc_policy.c#L1123), [`ipc_policy.c`, guard AST handling](../../../xnu/osfmk/ipc/ipc_policy.c#L1326).

## Reply ports and special ports

Three names are easy to conflate. A **task special port** is a capability stored in a designated task slot, retrieved through `task_get_special_port_internal()` with flavor and active-state checks. Examples include bootstrap, host, and task access ports. A **reply port** is a port type intended for reply semantics. A **thread special reply port** additionally links a synchronous IPC dependency to the waiting thread. [`ipc_tt.c`, task slots](../../../xnu/osfmk/kern/ipc_tt.c#L1787), [`ipc_tt.c`, thread reply allocation](../../../xnu/osfmk/kern/ipc_tt.c#L1349).

The legacy `mach_reply_port()` trap allocates an ordinary `IOT_PORT` in this checkout. Its name alone does not imply the stronger constructed reply-port type. `thread_get_special_reply_port()` instead allocates `IOT_SPECIAL_REPLY_PORT`, gives the caller send and receive rights, and binds it to the thread after unbinding any prior port. [`ipc_tt.c`](../../../xnu/osfmk/kern/ipc_tt.c#L1319).

`ipc_validate_local_port()` examines a request's reply port according to the destination's reply semantics and the sender's space policy. Kobject, bootstrap, and service destinations have different enhanced-policy thresholds and permitted reply types; compatibility exceptions are explicit. Other validation checks the selected `MACH64_SEND_*_CALL` class against destination type and bounds descriptor counts, port counts, and aggregate VM data. Follow these checks alongside copyin, rather than assuming any syntactically valid header is permitted. [`ipc_policy.c`, reply checks](../../../xnu/osfmk/ipc/ipc_policy.c#L567), [`schema validation`](../../../xnu/osfmk/ipc/ipc_policy.c#L632), [`destination validation`](../../../xnu/osfmk/ipc/ipc_policy.c#L787).

Synchronous receive setup can link the thread's special reply port to the destination port's send turnstile; receive completion unwinds or adjusts that linkage. This carries a scheduling dependency through IPC. It is separate from the mere presence of a reply send-once right in a message. [`mach_msg.c`, link setup](../../../xnu/osfmk/ipc/mach_msg.c#L1053), [`mach_msg_receive_results_complete()`](../../../xnu/osfmk/ipc/mach_msg.c#L1111), [`ipc_port.h`, sync-link states](../../../xnu/osfmk/ipc/ipc_port.h#L266).

## Vouchers carry managed attributes

An `ipc_voucher` is an immutable, reference-counted collection of attribute-value indices managed by registered resource managers. A voucher port represents the object as a capability. The kmsg keeps its voucher separately from ordinary body descriptors, with its own disposition/ownership. The immutability matters: preprocessing and redemption construct replacement vouchers rather than editing shared attributes in place. [`ipc_voucher.h`](../../../xnu/osfmk/ipc/ipc_voucher.h#L68), [`ipc_kmsg.h`](../../../xnu/osfmk/ipc/ipc_kmsg.h#L145).

`ipc_voucher_send_preprocessing()` gathers `SEND_PREPROCESS` recipes for managers supporting that operation and replaces the message voucher while preserving its disposition. `ipc_voucher_receive_postprocessing()` performs supported `AUTO_REDEEM` recipes only when `MACH_RCV_VOUCHER` was requested, a valid voucher exists, and the receiver is not the kernel task. Both release the superseded voucher port right. [`ipc_voucher.c`](../../../xnu/osfmk/ipc/ipc_voucher.c#L2172), [`receive processing`](../../../xnu/osfmk/ipc/ipc_voucher.c#L2222).

Transporting or redeeming a voucher is distinct from adopting it on a thread. `thread_set_voucher_name()` converts the name to a voucher reference, obtains its bank ledger/thread-group/persona attribution, swaps the thread's voucher under its mutex, applies ledger and thread-group changes, and releases the old voucher. Bank attributes connect IPC work to resource accounting; see [runtime accounting](../runtime/time-and-accounting.md). [`thread.c`](../../../xnu/osfmk/kern/thread.c#L3364), [`bank.c`](../../../xnu/osfmk/bank/bank.c#L1823), [`bank_internal.h`](../../../xnu/osfmk/bank/bank_internal.h#L68).

Strict reply context can record the voucher's persona on a reply port. When the send path enables this check for a send-once reply, `ipc_kmsg_validate_reply_context_locked()` requires a valid adopted voucher with the matching persona, then clears the recorded context even on failure. This is an additional reply-origin check, distinct from port guards and type validation. [`ipc_kmsg.c`, context recording/check](../../../xnu/osfmk/ipc/ipc_kmsg.c#L1471), [`send-path gating`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5180).

## Importance and turnstiles have different jobs

IPC importance tracks donation between tasks across messages. `ipc_importance_elem` links outstanding messages and boost counts; task and inheritance records represent the source/recipient relationships. `ipc_importance_send()` checks destination donation support, send options, donor state, and voucher attributes. Its lock acquisition may temporarily drop the port lock, which is why `ipc_kmsg_send()` explicitly rechecks/retries destination state around this stage. [`ipc_importance.h`](../../../xnu/osfmk/ipc/ipc_importance.h#L62), [`ipc_importance_send()`](../../../xnu/osfmk/ipc/ipc_importance.c#L2502), [`ipc_kmsg_send()`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5129).

Receive processing can turn the message's importance relationship into an inherited voucher attribute; cleanup detaches the relationship and withdraws associated accounting when necessary. This is not the same mechanism as the turnstile used when a thread blocks on a full queue or synchronous reply: those turnstiles propagate priority along a live waiting dependency. Follow both when investigating a priority change, and track bank attribution separately when investigating CPU charges. [`ipc_importance_receive()`](../../../xnu/osfmk/ipc/ipc_importance.c#L3139), [`ipc_importance_clean()`](../../../xnu/osfmk/ipc/ipc_importance.c#L3323), [`ipc_mqueue_send_locked()`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L432), [runtime wait/turnstile guide](../runtime/waits-and-locks.md).
