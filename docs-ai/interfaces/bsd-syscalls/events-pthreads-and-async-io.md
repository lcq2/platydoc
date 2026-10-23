# BSD syscalls: Events pthreads and async io

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 93: select

`int select(int nd, u_int32_t *in, u_int32_t *ou, u_int32_t *ex, struct timeval *tv) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L151) · **Condition:** `always` · **Audit event:** `AUE_SELECT`.

Wait for descriptor readability/writability/exception conditions using fd bitsets and a timeval deadline.

**Implementation:** [select](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1128). The common body imports/converts the timeout and calls `select_internal`, which coordinates readiness scans and waits; the ordinary wrapper tests cancellation before entering it.

## 230: poll

`int poll(struct pollfd *fds, u_int nfds, int timeout);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L338) · **Condition:** `always` · **Audit event:** `AUE_POLL`.

Wait for readiness of an array of descriptor/event requests.

**Implementation:** [poll](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1684). The common body builds a temporary kqueue, registers per-fd interests, scans/waits, and copies revents out, releasing temporary knotes/queue storage; ordinary poll first tests cancellation.

## 297: psynch_rw_longrdlock

`uint32_t psynch_rw_longrdlock(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L449) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Enter the selected pthread reader/writer-lock slow-path operation.

**Implementation:** [psynch_rw_longrdlock](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L446). Each shim invokes its correspondingly named `pthread_functions` callback with rwlock address, lock/unlock generation, writer count and flags; provider code owns the actual wait/grant protocol.

## 298: psynch_rw_yieldwrlock

`uint32_t psynch_rw_yieldwrlock(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L450) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Enter the selected pthread reader/writer-lock slow-path operation.

**Implementation:** [psynch_rw_yieldwrlock](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L476). Each shim invokes its correspondingly named `pthread_functions` callback with rwlock address, lock/unlock generation, writer count and flags; provider code owns the actual wait/grant protocol.

## 299: psynch_rw_downgrade

`int psynch_rw_downgrade(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L451) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Retain historical rwlock upgrade/downgrade entry points as no-ops.

**Implementation:** [psynch_rw_downgrade](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L488). Both local bodies return zero and ignore their arguments. No lock conversion or provider callback occurs in these implementations.

## 300: psynch_rw_upgrade

`uint32_t psynch_rw_upgrade(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L452) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Retain historical rwlock upgrade/downgrade entry points as no-ops.

**Implementation:** [psynch_rw_upgrade](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L482). Both local bodies return zero and ignore their arguments. No lock conversion or provider callback occurs in these implementations.

## 301: psynch_mutexwait

`uint32_t psynch_mutexwait(user_addr_t mutex, uint32_t mgen, uint32_t ugen, uint64_t tid, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L453) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Enter the pthread provider's mutex-wait slow path with lock-generation and owner information.

**Implementation:** [psynch_mutexwait](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L410). The shim forwards mutex address, generation values, thread identity and flags to `pthread_functions->psynch_mutexwait`; queue and priority-inheritance algorithms are not implemented in this shim.

## 302: psynch_mutexdrop

`uint32_t psynch_mutexdrop(user_addr_t mutex, uint32_t mgen, uint32_t ugen, uint64_t tid, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L454) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Release/wake through the pthread provider's mutex slow path.

**Implementation:** [psynch_mutexdrop](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L416). Forwards the mutex address, generation/owner fields and flags to `pthread_functions->psynch_mutexdrop`; the returned generation/result comes from that provider.

## 303: psynch_cvbroad

`uint32_t psynch_cvbroad(user_addr_t cv, uint64_t cvlsgen, uint64_t cvudgen, uint32_t flags, user_addr_t mutex, uint64_t mugen, uint64_t tid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L455) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Broadcast a pthread condition variable using generation/prepost state.

**Implementation:** [psynch_cvbroad](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L422). The shim passes CV generations, associated mutex fields and thread identity to the registered `psynch_cvbroad` callback; userspace condition-variable state is coordinated by that external provider.

## 304: psynch_cvsignal

`uint32_t psynch_cvsignal(user_addr_t cv, uint64_t cvlsgen, uint32_t cvugen, int thread_port, user_addr_t mutex, uint64_t mugen, uint64_t tid, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L456) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Signal a pthread condition variable, optionally selecting a thread.

**Implementation:** [psynch_cvsignal](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L428). Forwards CV/mutex generations, target thread-port field and flags to `pthread_functions->psynch_cvsignal`; it is not a BSD signal-posting operation.

## 305: psynch_cvwait

`uint32_t psynch_cvwait(user_addr_t cv, uint64_t cvlsgen, uint32_t cvugen, user_addr_t mutex, uint64_t mugen, uint32_t flags, int64_t sec, uint32_t nsec) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L457) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Wait on a pthread condition variable with mutex/generation and timeout state.

**Implementation:** [psynch_cvwait](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L434). The local shim forwards CV/mutex generations, flags and seconds/nanoseconds to the provider callback; atomic mutex-release/wait semantics must be established in the provider implementation.

## 306: psynch_rw_rdlock

`uint32_t psynch_rw_rdlock(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L458) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Enter the selected pthread reader/writer-lock slow-path operation.

**Implementation:** [psynch_rw_rdlock](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L452). Each shim invokes its correspondingly named `pthread_functions` callback with rwlock address, lock/unlock generation, writer count and flags; provider code owns the actual wait/grant protocol.

## 307: psynch_rw_wrlock

`uint32_t psynch_rw_wrlock(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L459) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Enter the selected pthread reader/writer-lock slow-path operation.

**Implementation:** [psynch_rw_wrlock](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L470). Each shim invokes its correspondingly named `pthread_functions` callback with rwlock address, lock/unlock generation, writer count and flags; provider code owns the actual wait/grant protocol.

## 308: psynch_rw_unlock

`uint32_t psynch_rw_unlock(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L460) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Release a pthread rwlock through its registered provider.

**Implementation:** [psynch_rw_unlock](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L458). Forwards the rwlock address, generation/count and flags to `pthread_functions->psynch_rw_unlock`, returning that provider's result.

## 309: psynch_rw_unlock2

`uint32_t psynch_rw_unlock2(user_addr_t rwlock, uint32_t lgenval, uint32_t ugenval, uint32_t rw_wc, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L461) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Retain an unsupported historical rwlock entry point.

**Implementation:** [psynch_rw_unlock2](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L464). The local body returns `ENOTSUP` without invoking a provider callback.

## 312: psynch_cvclrprepost

`int psynch_cvclrprepost(user_addr_t cv, uint32_t cvgen, uint32_t cvugen, uint32_t cvsgen, uint32_t prepocnt, uint32_t preposeq, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L480) · **Condition:** `(PSYNCH)` · **Audit event:** `AUE_NULL`.

Clear pthread condition-variable prepost bookkeeping through the provider.

**Implementation:** [psynch_cvclrprepost](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L440). Forwards CV generations, prepost count/sequence and flags to `pthread_functions->psynch_cvclrprepost`; this local body adds no independent wait-queue algorithm.

## 313: aio_fsync

`int aio_fsync(int op, user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L484) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Enqueue an asynchronous read, write or synchronization request using a user aiocb identity.

**Implementation:** [aio_fsync](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L775). `aio_queue_async_request` copies/validates request state, registers completion policy and queues owned kernel work; execution/completion and later result consumption occur separately.

## 314: aio_return

`user_ssize_t aio_return(user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L485) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Consume the result of a completed asynchronous request.

**Implementation:** [aio_return](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L842). Finds the completed entry under the AIO process lock, removes it from the done list and drops its final result ownership with `aio_entry_unref` after extracting the result.

## 315: aio_suspend

`int aio_suspend(user_addr_t aiocblist, int nent, user_addr_t timeoutp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L486) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wait for completion among a list of asynchronous requests, optionally with a timeout.

**Implementation:** [aio_suspend](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L1144). The common body copies the aiocb-pointer list, searches protected AIO state and installs a bounded wait; the ordinary wrapper tests cancellation first.

## 316: aio_cancel

`int aio_cancel(int fd, user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L487) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Attempt to cancel eligible queued asynchronous work for a descriptor/request.

**Implementation:** [aio_cancel](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L562). Validates the file/request and races protected queue removal against worker admission; already running/completed requests produce different cancellation statuses and are not unconditionally aborted.

## 317: aio_error

`int aio_error(user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L488) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Query the completion/error state of an asynchronous request.

**Implementation:** [aio_error](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L715). Searches the process's protected AIO state by aiocb identity and reports its maintained error/in-progress status; it does not consume the completed request.

## 318: aio_read

`int aio_read(user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L489) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Enqueue an asynchronous read, write or synchronization request using a user aiocb identity.

**Implementation:** [aio_read](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L813). `aio_queue_async_request` copies/validates request state, registers completion policy and queues owned kernel work; execution/completion and later result consumption occur separately.

## 319: aio_write

`int aio_write(user_addr_t aiocbp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L490) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Enqueue an asynchronous read, write or synchronization request using a user aiocb identity.

**Implementation:** [aio_write](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L1289). `aio_queue_async_request` copies/validates request state, registers completion policy and queues owned kernel work; execution/completion and later result consumption occur separately.

## 320: lio_listio

`int lio_listio(int mode, user_addr_t aiocblist, int nent, user_addr_t sigp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L491) · **Condition:** `always` · **Audit event:** `AUE_LIOLISTIO`.

Submit a list of asynchronous I/O requests with wait/notification policy.

**Implementation:** [lio_listio](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L1604). Imports the list and optional sigevent, creates entries, registers kevents and enqueues eligible work under AIO protection; partial preparation/enqueue failures require per-entry cleanup rather than assuming one atomic batch.

## 360: bsdthread_create

`user_addr_t bsdthread_create(user_addr_t func, user_addr_t func_arg, user_addr_t stack, user_addr_t pthread, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L541) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Request creation of a pthread using registered start/stack/thread parameters.

**Implementation:** [bsdthread_create](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L338). The local shim forwards individual arguments to `pthread_functions->bsdthread_create`; the registered pthread provider supplies the creation implementation beyond this interface.

## 361: bsdthread_terminate

`int bsdthread_terminate(user_addr_t stackaddr, size_t freesize, uint32_t port, user_addr_t sema_or_ulock) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L542) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Terminate the current pthread and coordinate stack/join notification cleanup.

**Implementation:** [bsdthread_terminate](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L366). Locally removes workqueue membership or rejects AIO-worker termination, distinguishes a join ulock from a semaphore, records delayed port/ulock cleanup, then calls the provider's termination callback.

## 362: kqueue

`int kqueue(void);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L543) · **Condition:** `always` · **Audit event:** `AUE_KQUEUE`.

Create a file-descriptor-backed event queue, optionally guarded.

**Implementation:** [kqueue](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L3088). Both call `kqueue_internal`; the guarded entry imports guard identity/restrictions before allocation/publication. The resulting fd owns queue state until close and knote teardown complete.

## 363: kevent

`int kevent(int fd, const struct kevent *changelist, int nchanges, struct kevent *eventlist, int nevents, const struct timespec *timeout);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L544) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Apply changes and retrieve events using the legacy or fixed-width kevent ABI.

**Implementation:** [kevent](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L8549). `kevent_legacy_internal` imports change records, registers/modifies knotes and scans for output according to the selected record layout and timeout; event processing can mutate state before output copy succeeds.

## 366: bsdthread_register

`int bsdthread_register(user_addr_t threadstart, user_addr_t wqthread, uint32_t flags, user_addr_t stack_addr_hint, user_addr_t targetconc_ptr, uint32_t dispatchqueue_offset, uint32_t tsd_offset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L547) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Register pthread and workqueue user-entry information with the kernel pthread provider.

**Implementation:** [bsdthread_register](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L344). Converts user function pointers, checks provider version and calls `bsdthread_register2` or the older callback with the appropriate stack/TSD/dispatch offsets. Provider internals are external to this shim.

## 367: workq_open

`int workq_open(void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L548) · **Condition:** `always` · **Audit event:** `AUE_WORKQOPEN`.

Initialize a process workqueue if necessary.

**Implementation:** [workq_open](../../../platydoc-data/xnu/bsd/pthread/pthread_workqueue.c#L2081). Serializes workqueue publication, allocates state, establishes QoS/parallelism and turnstile/request machinery, and makes the queue available to subsequent worker-demand operations.

## 368: workq_kernreturn

`int workq_kernreturn(int options, user_addr_t item, int affinity, int prio) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L549) · **Condition:** `always` · **Audit event:** `AUE_WORKQOPS`.

Submit worker requests or return/park a workqueue thread through an operation selector.

**Implementation:** [workq_kernreturn](../../../platydoc-data/xnu/bsd/pthread/pthread_workqueue.c#L3750). Dispatches requests to `workq_reqthreads`, thread return, stack/event and related handlers while coordinating queue locks, thread tags and admission state; not every operation returns through the original user stack.

## 369: kevent64

`int kevent64(int fd, const struct kevent64_s *changelist, int nchanges, struct kevent64_s *eventlist, int nevents, unsigned int flags, const struct timespec *timeout);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L550) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Apply changes and retrieve events using the legacy or fixed-width kevent ABI.

**Implementation:** [kevent64](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L8570). `kevent_legacy_internal` imports change records, registers/modifies knotes and scans for output according to the selected record layout and timeout; event processing can mutate state before output copy succeeds.

## 372: thread_selfid

`uint64_t thread_selfid (void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L553) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Return the current thread's numeric ID through the pthread provider interface.

**Implementation:** [thread_selfid](../../../platydoc-data/xnu/bsd/pthread/pthread_shims.c#L402). The local shim invokes `pthread_functions->thread_selfid` and passes the 64-bit result pointer; it does not return a Mach thread port right.

## 374: kevent_qos

`int kevent_qos(int fd, const struct kevent_qos_s *changelist, int nchanges, struct kevent_qos_s *eventlist, int nevents, void *data_out, size_t *data_available, unsigned int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L555) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Apply/retrieve modern QoS-aware events for fd/workqueue-backed queues.

**Implementation:** [kevent_qos](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L8405). Adjusts caller flags, imports output-data sizing, selects `kevent_get_kqwq` or `kevent_get_kqfile`, and invokes `kevent_modern_internal` for registration and delivery.

## 375: kevent_id

`int kevent_id(uint64_t id, const struct kevent_qos_s *changelist, int nchanges, struct kevent_qos_s *eventlist, int nevents, void *data_out, size_t *data_available, unsigned int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L556) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Operate a dynamic workloop identified by a 64-bit ID.

**Implementation:** [kevent_id](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L8269). Gets/creates and retains the workloop, selects supported flags and enters `kevent_modern_internal`; the ID is a name for a reference-managed object, not permanent ownership.

## 394: pselect

`int pselect(int nd, u_int32_t *in, u_int32_t *ou, u_int32_t *ex, const struct timespec *ts, const struct sigset_t *mask) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L588) · **Condition:** `always` · **Audit event:** `AUE_SELECT`.

Wait for descriptor readiness with a timespec timeout and temporary signal-mask semantics.

**Implementation:** [pselect](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1170). Imports/validates timeout and mask state, then uses `select_internal` with uthread signal coordination; the ordinary wrapper first tests cancellation.

## 395: pselect_nocancel

`int pselect_nocancel(int nd, u_int32_t *in, u_int32_t *ou, u_int32_t *ex, const struct timespec *ts, const struct sigset_t *mask) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L589) · **Condition:** `always` · **Audit event:** `AUE_SELECT`.

Wait for descriptor readiness with a timespec timeout and temporary signal-mask semantics.

**Implementation:** [pselect_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1177). Imports/validates timeout and mask state, then uses `select_internal` with uthread signal coordination; the ordinary wrapper first tests cancellation.

## 407: select_nocancel

`int select_nocancel(int nd, u_int32_t *in, u_int32_t *ou, u_int32_t *ex, struct timeval *tv) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L608) · **Condition:** `always` · **Audit event:** `AUE_SELECT`.

Wait for descriptor readability/writability/exception conditions using fd bitsets and a timeval deadline.

**Implementation:** [select_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1135). The common body imports/converts the timeout and calls `select_internal`, which coordinates readiness scans and waits; the ordinary wrapper tests cancellation before entering it.

## 417: poll_nocancel

`int poll_nocancel(struct pollfd *fds, u_int nfds, int timeout) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L626) · **Condition:** `always` · **Audit event:** `AUE_POLL`.

Wait for readiness of an array of descriptor/event requests.

**Implementation:** [poll_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L1692). The common body builds a temporary kqueue, registers per-fd interests, scans/waits, and copies revents out, releasing temporary knotes/queue storage; ordinary poll first tests cancellation.

## 421: aio_suspend_nocancel

`int aio_suspend_nocancel(user_addr_t aiocblist, int nent, user_addr_t timeoutp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L635) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wait for completion among a list of asynchronous requests, optionally with a timeout.

**Implementation:** [aio_suspend_nocancel](../../../platydoc-data/xnu/bsd/kern/kern_aio.c#L1152). The common body copies the aiocb-pointer list, searches protected AIO state and installs a bounded wait; the ordinary wrapper tests cancellation first.

## 443: guarded_kqueue_np

`int guarded_kqueue_np(const guardid_t *guard, u_int guardflags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L673) · **Condition:** `always` · **Audit event:** `AUE_KQUEUE`.

Create a file-descriptor-backed event queue, optionally guarded.

**Implementation:** [guarded_kqueue_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L395). Both call `kqueue_internal`; the guarded entry imports guard identity/restrictions before allocation/publication. The resulting fd owns queue state until close and knote teardown complete.

## 478: bsdthread_ctl

`int bsdthread_ctl(user_addr_t cmd, user_addr_t arg1, user_addr_t arg2, user_addr_t arg3) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L732) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Control pthread/workqueue QoS overrides, self properties and related servicing policy.

**Implementation:** [bsdthread_ctl](../../../platydoc-data/xnu/bsd/pthread/pthread_workqueue.c#L2837). Operation dispatch selects explicit/dispatch override helpers, self-policy updates, parallelism queries, worker kill permission and supported apply/signal-mask controls with argument validation.

## 496: mach_eventlink_signal

`uint64_t mach_eventlink_signal(mach_port_name_t eventlink_port, uint64_t signal_count) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L779) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Signal a Mach eventlink endpoint through the BSD syscall namespace.

**Implementation:** [mach_eventlink_signal](../../../platydoc-data/xnu/bsd/kern/sys_eventlink.c#L59). Calls `mach_eventlink_signal_trap` and puts its packed 64-bit result into the BSD return-value slot while the wrapper itself returns errno zero; inner status is not a BSD errno conversion.

## 497: mach_eventlink_wait_until

`uint64_t mach_eventlink_wait_until(mach_port_name_t eventlink_port, uint64_t wait_count, uint64_t deadline, uint32_t clock_id, uint32_t option) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L780) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wait for an eventlink count with explicit clock/deadline/options.

**Implementation:** [mach_eventlink_wait_until](../../../platydoc-data/xnu/bsd/kern/sys_eventlink.c#L69). Invokes `mach_eventlink_wait_until_trap` and returns its packed 64-bit value with outer BSD success, preserving the eventlink result contract.

## 498: mach_eventlink_signal_wait_until

`uint64_t mach_eventlink_signal_wait_until(mach_port_name_t eventlink_port, uint64_t wait_count, uint64_t signal_count, uint64_t deadline, uint32_t clock_id, uint32_t option) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L781) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Signal an eventlink and wait for the paired count/deadline operation.

**Implementation:** [mach_eventlink_signal_wait_until](../../../platydoc-data/xnu/bsd/kern/sys_eventlink.c#L80). Passes both counts plus options/clock/deadline to the combined trap helper; the helper's packed result is the 64-bit syscall value, not the wrapper errno.

## 499: work_interval_ctl

`int work_interval_ctl(uint32_t operation, uint64_t work_interval_id, void *arg, size_t len) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L782) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Create, join/name/configure, notify or destroy a work interval through an operation selector.

**Implementation:** [work_interval_ctl](../../../platydoc-data/xnu/bsd/kern/sys_work_interval.c#L42). Imports command-specific arguments and calls `kern_work_interval_*` helpers, using work-interval IDs or Mach ports according to the operation; privileges and output cleanup are command-specific.

## 515: sys_ulock_wait

`int sys_ulock_wait(uint32_t operation, void *addr, uint64_t value, uint32_t timeout) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L818) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wait on a user-address lock using the older timeout ABI.

**Implementation:** [sys_ulock_wait](../../../platydoc-data/xnu/bsd/kern/sys_ulock.c#L505). Builds the extended wait arguments and calls `sys_ulock_wait2`, preserving operation/value semantics while translating the older timeout representation.

## 516: sys_ulock_wake

`int sys_ulock_wake(uint32_t operation, void *addr, uint64_t wake_value) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L819) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wake one or more waiters on a keyed user-address lock.

**Implementation:** [sys_ulock_wake](../../../platydoc-data/xnu/bsd/kern/sys_ulock.c#L889). Validates operation/debug modes and calls `ulock_wake` for the process/task address key, coordinating the matching wait queue and any owner/turnstile update.

## 530: kqueue_workloop_ctl

`int kqueue_workloop_ctl(user_addr_t cmd, uint64_t options, user_addr_t addr, size_t sz) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L838) · **Condition:** `always` · **Audit event:** `AUE_WORKLOOPCTL`.

Create/destroy or configure workloop attributes through a control request.

**Implementation:** [kqueue_workloop_ctl](../../../platydoc-data/xnu/bsd/kern/kern_event.c#L5047). Copies the size-bounded request and calls `kqueue_workloop_ctl_internal`; command/options determine which workloop policy or lifecycle operation is permitted.

## 544: sys_ulock_wait2

`int sys_ulock_wait2(uint32_t operation, void *addr, uint64_t value, uint64_t timeout, uint64_t value2) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L856) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Wait while a supported user lock/value condition holds, optionally using owner donation and an extended timeout/value.

**Implementation:** [sys_ulock_wait2](../../../platydoc-data/xnu/bsd/kern/sys_ulock.c#L519). Validates operation/address/value, performs atomic user reads, obtains keyed ulock state and prepares turnstile/wait state before blocking; changed values, timeout, cancellation and owner-resolution failure take explicit cleanup paths.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
