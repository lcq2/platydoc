# BSD syscalls: Local ipc

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 251: semsys

`int semsys(u_int which, int a2, int a3, int a4, int a5) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L366) · **Condition:** `(SYSV_SEM)` · **Audit event:** `AUE_SEMSYS`.

Dispatch the historical SysV semaphore multiplexor.

**Implementation:** [semsys](../../../xnu/bsd/kern/sysv_sem.c#L229). Bounds-checks `which` against `semcalls` and calls the selected handler with the packed trailing arguments; individual semctl/semget/semop handlers own locking and validation.

## 252: msgsys

`int msgsys(u_int which, int a2, int a3, int a4, int a5) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L371) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGSYS`.

Dispatch the historical SysV message-queue multiplexor.

**Implementation:** [msgsys](../../../xnu/bsd/kern/sysv_msg.c#L330). Bounds-checks `which` against `msgcalls`, then invokes the selected message operation with packed trailing arguments; invalid selectors return `EINVAL`.

## 253: shmsys

`int shmsys(u_int which, int a2, int a3, int a4) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L376) · **Condition:** `(SYSV_SHM)` · **Audit event:** `AUE_SHMSYS`.

Dispatch the historical SysV shared-memory multiplexor.

**Implementation:** [shmsys](../../../xnu/bsd/kern/sysv_shm.c#L950). Bounds-checks `which` against `shmcalls` and invokes the attachment/control/detachment/get handler; the selected operation performs its own locking.

## 254: semctl

`int semctl(int semid, int semnum, int cmd, semun_t arg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L381) · **Condition:** `(SYSV_SEM)` · **Audit event:** `AUE_SEMCTL`.

Control a SysV semaphore set, including metadata, values and removal.

**Implementation:** [semctl](../../../xnu/bsd/kern/sysv_sem.c#L578). Under SysV semaphore protection, validates ID/sequence and IPC/MAC permission, then executes the command; removal also clears relevant undo state and wakes affected waiters.

## 255: semget

`int semget(key_t key, int nsems, int semflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L382) · **Condition:** `(SYSV_SEM)` · **Audit event:** `AUE_SEMGET`.

Find or allocate a SysV semaphore set by key.

**Implementation:** [semget](../../../xnu/bsd/kern/sysv_sem.c#L831). Looks up existing identifiers/permissions or grows and initializes set/semaphore storage under subsystem protection, returning an ID with sequence identity.

## 256: semop

`int semop(int semid, struct sembuf *sops, int nsops);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L383) · **Condition:** `(SYSV_SEM)` · **Audit event:** `AUE_SEMOP`.

Apply a vector of SysV semaphore operations with wait and undo semantics.

**Implementation:** [semop](../../../xnu/bsd/kern/sysv_sem.c#L973). Imports operation records, validates set identity/permissions, evaluates the vector under subsystem locking and blocks/retries when values disallow progress; undo bookkeeping is tied to process exit.

## 258: msgctl

`int msgctl(int msqid, int cmd, struct msqid_ds *buf) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L392) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGCTL`.

Control a SysV message queue's metadata, limits or removal.

**Implementation:** [msgctl](../../../xnu/bsd/kern/sysv_msg.c#L373). Validates queue index/sequence and command-specific IPC/MAC permission under the message-subsystem lock, then copies status, changes attributes or removes/wakes queue users.

## 259: msgget

`int msgget(key_t key, int msgflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L393) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGGET`.

Find or create a SysV message queue by key.

**Implementation:** [msgget](../../../xnu/bsd/kern/sysv_msg.c#L576). Initializes the subsystem as needed, searches/authorizes an existing queue or allocates an unused slot with ownership and sequence metadata.

## 260: msgsnd

`int msgsnd(int msqid, void *msgp, size_t msgsz, int msgflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L394) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGSND`.

Append a typed message to a SysV queue, waiting for capacity when allowed.

**Implementation:** [msgsnd](../../../xnu/bsd/kern/sysv_msg.c#L699). The common body validates queue identity/permissions, imports message segments and coordinates capacity waits/enqueue under subsystem protection; ordinary msgsnd first tests cancellation.

## 261: msgrcv

`user_ssize_t msgrcv(int msqid, void *msgp, size_t msgsz, long msgtyp, int msgflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L395) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGRCV`.

Receive a SysV message selected by type and flags.

**Implementation:** [msgrcv](../../../xnu/bsd/kern/sysv_msg.c#L1127). The common body searches the protected queue, waits when no eligible message exists, handles size/truncation policy and copies out/reclaims message storage; ordinary msgrcv first tests cancellation.

## 262: shmat

`user_addr_t shmat(int shmid, void *shmaddr, int shmflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L403) · **Condition:** `(SYSV_SHM)` · **Audit event:** `AUE_SHMAT`.

Attach a SysV shared-memory segment into the calling process map.

**Implementation:** [shmat](../../../xnu/bsd/kern/sysv_shm.c#L378). Validates segment ID/permission, chooses address/protection, installs the VM mapping and records per-process attachment state; failures unwind mapping/reference work.

## 263: shmctl

`int shmctl(int shmid, int cmd, struct shmid_ds *buf) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L404) · **Condition:** `(SYSV_SHM)` · **Audit event:** `AUE_SHMCTL`.

Control SysV shared-memory metadata, permissions or removal.

**Implementation:** [shmctl](../../../xnu/bsd/kern/sysv_shm.c#L590). Validates segment identity and command authorization under subsystem protection, converts the user ABI and changes/query state; removal can defer backing destruction until attachments disappear.

## 264: shmdt

`int shmdt(void *shmaddr);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L405) · **Condition:** `(SYSV_SHM)` · **Audit event:** `AUE_SHMDT`.

Detach a previously attached SysV shared-memory mapping.

**Implementation:** [shmdt](../../../xnu/bsd/kern/sysv_shm.c#L320). Finds the caller's matching attachment, applies MAC checks and calls `shm_delete_mapping`, updating attachment counts and any pending segment-deletion lifetime.

## 265: shmget

`int shmget(key_t key, size_t size, int shmflg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L406) · **Condition:** `(SYSV_SHM)` · **Audit event:** `AUE_SHMGET`.

Find or create a SysV shared-memory segment by key and size.

**Implementation:** [shmget](../../../xnu/bsd/kern/sysv_shm.c#L892). Under subsystem protection, chooses `shmget_existing` or `shmget_allocate_segment`, enforcing size/permission/ID sequence rules and creating memory backing for new segments.

## 266: shm_open

`int shm_open(const char *name, int oflag, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L413) · **Condition:** `always` · **Audit event:** `AUE_SHMOPEN`.

Open or create a named POSIX shared-memory object as a descriptor.

**Implementation:** [shm_open](../../../xnu/bsd/kern/posix_shm.c#L383). Imports the name, reserves fileproc state, searches/publishes a protected namespace entry and assigns typed descriptor operations; truncation and mapping later manage memory-entry-backed storage.

## 267: shm_unlink

`int shm_unlink(const char *name);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L414) · **Condition:** `always` · **Audit event:** `AUE_SHMUNLINK`.

Remove a POSIX shared-memory name from its namespace.

**Implementation:** [shm_unlink](../../../xnu/bsd/kern/posix_shm.c#L1017). Looks up the name under the SHM lock, checks access/MAC and calls `pshm_unlink_internal`; existing descriptors/mappings can keep object storage alive after the name disappears.

## 268: sem_open

`user_addr_t sem_open(const char *name, int oflag, int mode, int value) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L415) · **Condition:** `always` · **Audit event:** `AUE_SEMOPEN`.

Open or create a named POSIX semaphore.

**Implementation:** [sem_open](../../../xnu/bsd/kern/posix_sem.c#L535). Imports/normalizes the name and team namespace, reserves descriptor state, creates a Mach semaphore when needed and publishes/reuses the protected POSIX object with ownership checks.

## 269: sem_close

`int sem_close(sem_t *sem);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L416) · **Condition:** `always` · **Audit event:** `AUE_SEMCLOSE`.

Close a POSIX semaphore descriptor.

**Implementation:** [sem_close](../../../xnu/bsd/kern/posix_sem.c#L951). Checks descriptor type under the fd lock and calls `fp_close_and_unlock`; namespace unlink and last backing-semaphore reference are separate events.

## 270: sem_unlink

`int sem_unlink(const char *name);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L417) · **Condition:** `always` · **Audit event:** `AUE_SEMUNLINK`.

Remove a POSIX semaphore name from the protected namespace.

**Implementation:** [sem_unlink](../../../xnu/bsd/kern/posix_sem.c#L872). Uses the team/name key, checks access/MAC and calls `psem_unlink_internal`; open descriptors retain their object references.

## 271: sem_wait

`int sem_wait(sem_t *sem);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L418) · **Condition:** `always` · **Audit event:** `AUE_SEMWAIT`.

Wait for a POSIX semaphore count.

**Implementation:** [sem_wait](../../../xnu/bsd/kern/posix_sem.c#L974). The common body pins a typed descriptor, checks object/MAC state and calls Mach `semaphore_wait`, translating its result before dropping the fileproc. Ordinary sem_wait tests cancellation.

## 272: sem_trywait

`int sem_trywait(sem_t *sem);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L419) · **Condition:** `always` · **Audit event:** `AUE_SEMTRYWAIT`.

Attempt a POSIX semaphore decrement without waiting.

**Implementation:** [sem_trywait](../../../xnu/bsd/kern/posix_sem.c#L1039). Pins/checks the typed semaphore object and calls `semaphore_timedwait` with the immediate timeout policy, translating failure/status and releasing the fd reference.

## 273: sem_post

`int sem_post(sem_t *sem);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L420) · **Condition:** `always` · **Audit event:** `AUE_SEMPOST`.

Increment/wake a POSIX semaphore.

**Implementation:** [sem_post](../../../xnu/bsd/kern/posix_sem.c#L1103). Pins/checks the typed object and invokes Mach `semaphore_signal`, then translates status and drops the fileproc reference.

## 418: msgsnd_nocancel

`int msgsnd_nocancel(int msqid, void *msgp, size_t msgsz, int msgflg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L628) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGSND`.

Append a typed message to a SysV queue, waiting for capacity when allowed.

**Implementation:** [msgsnd_nocancel](../../../xnu/bsd/kern/sysv_msg.c#L706). The common body validates queue identity/permissions, imports message segments and coordinates capacity waits/enqueue under subsystem protection; ordinary msgsnd first tests cancellation.

## 419: msgrcv_nocancel

`user_ssize_t msgrcv_nocancel(int msqid, void *msgp, size_t msgsz, long msgtyp, int msgflg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L629) · **Condition:** `(SYSV_MSG)` · **Audit event:** `AUE_MSGRCV`.

Receive a SysV message selected by type and flags.

**Implementation:** [msgrcv_nocancel](../../../xnu/bsd/kern/sysv_msg.c#L1134). The common body searches the protected queue, waits when no eligible message exists, handles size/truncation policy and copies out/reclaims message storage; ordinary msgrcv first tests cancellation.

## 420: sem_wait_nocancel

`int sem_wait_nocancel(sem_t *sem) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L634) · **Condition:** `always` · **Audit event:** `AUE_SEMWAIT`.

Wait for a POSIX semaphore count.

**Implementation:** [sem_wait_nocancel](../../../xnu/bsd/kern/posix_sem.c#L981). The common body pins a typed descriptor, checks object/MAC state and calls Mach `semaphore_wait`, translating its result before dropping the fileproc. Ordinary sem_wait tests cancellation.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
