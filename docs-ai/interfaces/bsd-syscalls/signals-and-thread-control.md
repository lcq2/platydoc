# BSD syscalls: Signals and thread control

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 37: kill

`int kill(int pid, int signum, int posix) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L91) · **Condition:** `always` · **Audit event:** `AUE_KILL`.

Send a signal to a selected process or process group.

**Implementation:** [kill](../../../xnu/bsd/kern/kern_sig.c#L1381). Finds/refers to the target, applies `cansignal`, and calls `psignal` or `killpg1`; posting selects pending/action state and is separate from building a user signal frame.

## 46: sigaction

`int sigaction(int signum, struct __sigaction *nsa, struct sigaction *osa) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L100) · **Condition:** `always` · **Audit event:** `AUE_SIGACTION`.

Query or replace a process signal disposition.

**Implementation:** [sigaction](../../../xnu/bsd/kern/kern_sig.c#L440). Imports/converts the caller ABI, validates signal/restriction flags, copies old state out and updates handler/mask/action state used by posting and delivery.

## 48: sigprocmask

`int sigprocmask(int how, user_addr_t mask, user_addr_t omask);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L102) · **Condition:** `always` · **Audit event:** `AUE_SIGPROCMASK`.

Change the calling thread's blocked-signal mask and optionally return the previous mask.

**Implementation:** [sigprocmask](../../../xnu/bsd/kern/kern_sig.c#L793). Imports the mask, uses block/unblock/set helpers, requests an AST when newly deliverable work appears, and copies old mask state out.

## 52: sigpending

`int sigpending(struct sigvec *osv);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L106) · **Condition:** `always` · **Audit event:** `AUE_SIGPENDING`.

Read the calling thread's pending-signal set.

**Implementation:** [sigpending](../../../xnu/bsd/kern/kern_sig.c#L840). Copies the maintained uthread pending-signal mask to the supplied user address; it does not deliver or consume those signals.

## 53: sigaltstack

`int sigaltstack(struct sigaltstack *nss, struct sigaltstack *oss) NO_SYSCALL_STUB ;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L107) · **Condition:** `always` · **Audit event:** `AUE_SIGALTSTACK`.

Query or change the calling thread's alternate signal-stack configuration.

**Implementation:** [sigaltstack](../../../xnu/bsd/kern/kern_sig.c#L1310). Converts 32/64-bit stack descriptors, validates current/on-stack restrictions and updates uthread state used by later signal delivery.

## 111: sigsuspend

`int sigsuspend(sigset_t mask) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L180) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Temporarily replace the signal mask and sleep for signal handling.

**Implementation:** [sigsuspend](../../../xnu/bsd/kern/kern_sig.c#L869). The nocancel body records restoration state and enters interruptible `tsleep0`; signal delivery/return restores the appropriate mask. The ordinary entry first tests cancellation.

## 184: sigreturn

`int sigreturn(struct ucontext *uctx, int infostyle, user_addr_t token) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L280) · **Condition:** `always` · **Audit event:** `AUE_SIGRETURN`.

Restore user execution and signal-mask/alternate-stack state after a handler.

**Implementation:** [sigreturn](../../../xnu/bsd/dev/arm/unix_signal.c#L800), [sigreturn](../../../xnu/bsd/dev/i386/unix_signal.c#L772). Architecture-specific ARM and x86 bodies import the user context, validate tokens/machine state and install the saved state, using `EJUSTRETURN` so normal syscall result encoding does not overwrite it. Failure ordering is not an all-or-nothing memory transaction.

## 328: __pthread_kill

`int __pthread_kill(int thread_port, int sig);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L499) · **Condition:** `always` · **Audit event:** `AUE_PTHREADKILL`.

Send a signal to a pthread identified by a Mach thread port name.

**Implementation:** [__pthread_kill](../../../xnu/bsd/kern/kern_sig.c#L1104). Converts the port to a referenced thread, checks pthread/task association and posts through `psignal_uthread`, then drops the thread reference.

## 329: __pthread_sigmask

`int __pthread_sigmask(int how, user_addr_t set, user_addr_t oset);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L500) · **Condition:** `always` · **Audit event:** `AUE_PTHREADSIGMASK`.

Change/query the current pthread's signal mask.

**Implementation:** [__pthread_sigmask](../../../xnu/bsd/kern/kern_sig.c#L1151). Operates on uthread mask state after user copyin, requests a signal AST as appropriate and copies the previous mask out; it bypasses process-wide disposition changes.

## 330: __sigwait

`int __sigwait(user_addr_t set, user_addr_t sig);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L501) · **Condition:** `always` · **Audit event:** `AUE_SIGWAIT`.

Synchronously wait for and consume a signal from a supplied set.

**Implementation:** [__sigwait](../../../xnu/bsd/kern/kern_sig.c#L1207). The common body coordinates process signal state, waits when no matching pending bit exists and copies the selected signal number out. The ordinary entry first tests cancellation.

## 331: __disable_threadsignal

`int __disable_threadsignal(int value);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L502) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Mark the current thread as excluded from ordinary process-directed signal selection.

**Implementation:** [__disable_threadsignal](../../../xnu/bsd/kern/kern_sig.c#L899). Sets `UT_NO_SIGMASK | UT_CANCELDISABLE` in the current uthread, excluding ordinary signal selection and disabling cancellation handling. It does not alter every process signal disposition or the hardware interrupt mask.

## 332: __pthread_markcancel

`int __pthread_markcancel(int thread_port);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L503) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Mark a target pthread as having cancellation pending.

**Implementation:** [__pthread_markcancel](../../../xnu/bsd/kern/kern_sig.c#L937). Converts and checks the thread port, updates uthread cancellation flags and calls `thread_abort_safely` when the current cancellation state permits interruption, then releases the thread reference.

## 333: __pthread_canceled

`int __pthread_canceled(int action);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L504) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Query or modify the current pthread's kernel cancellation bookkeeping.

**Implementation:** [__pthread_canceled](../../../xnu/bsd/kern/kern_sig.c#L971). Dispatches actions over uthread flags/state used by cancellation-point checks; userspace pthread cleanup handlers are not implemented by this syscall body.

## 334: __semwait_signal

`int __semwait_signal(int cond_sem, int mutex_sem, int timeout, int relative, int64_t tv_sec, int32_t tv_nsec);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L509) · **Condition:** `always` · **Audit event:** `AUE_SEMWAITSIGNAL`.

Wait on a Mach semaphore, optionally signaling another and applying a timeout.

**Implementation:** [__semwait_signal](../../../xnu/bsd/kern/kern_sig.c#L1027). The common body converts timeout form and selects semaphore wait/timed-wait or wait-signal trap helpers; the ordinary wrapper performs its cancellation-point test.

## 410: sigsuspend_nocancel

`int sigsuspend_nocancel(sigset_t mask) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L615) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Temporarily replace the signal mask and sleep for signal handling.

**Implementation:** [sigsuspend_nocancel](../../../xnu/bsd/kern/kern_sig.c#L876). The nocancel body records restoration state and enters interruptible `tsleep0`; signal delivery/return restores the appropriate mask. The ordinary entry first tests cancellation.

## 422: __sigwait_nocancel

`int __sigwait_nocancel(user_addr_t set, user_addr_t sig) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L636) · **Condition:** `always` · **Audit event:** `AUE_SIGWAIT`.

Synchronously wait for and consume a signal from a supplied set.

**Implementation:** [__sigwait_nocancel](../../../xnu/bsd/kern/kern_sig.c#L1214). The common body coordinates process signal state, waits when no matching pending bit exists and copies the selected signal number out. The ordinary entry first tests cancellation.

## 423: __semwait_signal_nocancel

`int __semwait_signal_nocancel(int cond_sem, int mutex_sem, int timeout, int relative, int64_t tv_sec, int32_t tv_nsec);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L637) · **Condition:** `always` · **Audit event:** `AUE_SEMWAITSIGNAL`.

Wait on a Mach semaphore, optionally signaling another and applying a timeout.

**Implementation:** [__semwait_signal_nocancel](../../../xnu/bsd/kern/kern_sig.c#L1035). The common body converts timeout form and selects semaphore wait/timed-wait or wait-signal trap helpers; the ordinary wrapper performs its cancellation-point test.

## 520: terminate_with_payload

`int terminate_with_payload(int pid, uint32_t reason_namespace, uint64_t reason_code, void *payload, uint32_t payload_size, const char *reason_string, uint64_t reason_flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L823) · **Condition:** `always` · **Audit event:** `AUE_KILL`.

Terminate an authorized target process with a structured reason/payload.

**Implementation:** [terminate_with_payload](../../../xnu/bsd/kern/kern_sig.c#L1622). `terminate_with_payload_internal` validates and constructs reason state, checks the target and posts the fatal termination action; userspace strings/data are copied rather than retained as raw user pointers.

## 521: abort_with_payload

`void abort_with_payload(uint32_t reason_namespace, uint64_t reason_code, void *payload, uint32_t payload_size, const char *reason_string, uint64_t reason_flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L824) · **Condition:** `always` · **Audit event:** `AUE_EXIT`.

Abort the caller with a structured termination reason.

**Implementation:** [abort_with_payload](../../../xnu/bsd/kern/kern_exit.c#L1580). `abort_with_payload_internal` constructs the reason object and follows fatal exit/notification behavior for the current process.

## 529: os_fault_with_payload

`int os_fault_with_payload(uint32_t reason_namespace, uint64_t reason_code, void *payload, uint32_t payload_size, const char *reason_string, uint64_t reason_flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L837) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Report a structured process fault through the reason/payload interface.

**Implementation:** [os_fault_with_payload](../../../xnu/bsd/kern/kern_exit.c#L1591). Calls `abort_with_payload_internal` with `OS_REASON_IFLAG_USER_FAULT`, enabling throttling and a user-fault branch. Security soft traps send an analytics event; other namespaces construct a user guard exception and invoke `task_violated_guard`, then free the reason and translate its result. This differs from the abort entry's `SIGABRT` delivery.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
