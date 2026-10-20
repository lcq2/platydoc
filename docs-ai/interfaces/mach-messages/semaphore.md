# Mach messages: semaphore

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/semaphore.defs](../../../xnu/osfmk/mach/semaphore.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 617200: semaphore_signal

**Interface contract:**

> a semaphore_t is created and destroyed through the task object. semaphore_create(task_t,&semaphore_t,...); semaphore_destroy(task_t,semaphore_t);

**Mechanism:** Takes the semaphore lock at scheduler interrupt level and rejects an inactive object. It wakes one queued waiter when possible; otherwise the PREPOST option increments the available count. The public wrapper converts the internal `KERN_NOT_WAITING` result into success, so callers cannot distinguish a wakeup from a stored permit through the return value. [semaphore_signal](../../../xnu/osfmk/kern/sync_sema.c#L338-L415). [Public result conversion](../../../xnu/osfmk/kern/sync_sema.c#L495-L515).

**Declarations:** [`semaphore_signal`](../../../xnu/osfmk/mach/semaphore.defs#L56) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_signal(
  semaphore : semaphore_t);
```

**Local body:** [`semaphore_signal`](../../../xnu/osfmk/kern/sync_sema.c#L495).
Calls visible in this body include `semaphore_signal_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/sync_sema.c#L495-L511):
<!-- source-excerpt: ../../../xnu/osfmk/kern/sync_sema.c#L495-L511 -->
```c
semaphore_signal(
	semaphore_t             semaphore)
{
	kern_return_t           kr;

	if (semaphore == SEMAPHORE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kr = semaphore_signal_internal(semaphore,
	    THREAD_NULL,
	    SEMAPHORE_SIGNAL_PREPOST);
	if (kr == KERN_NOT_WAITING) {
		return KERN_SUCCESS;
	}
	return kr;
}
```

**User wrapper:** [`semaphore_signal`](../../../xnu/libsyscall/mach/semaphore.c#L37).
Calls visible in this body include `semaphore_signal_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L37-L40):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L37-L40 -->
```c
semaphore_signal(mach_port_t signal_semaphore)
{
	return semaphore_signal_trap(signal_semaphore);
}
```

### 617201: semaphore_signal_all

Wake all eligible semaphore waiters through the semaphore signal primitive.

**Mechanism:** Uses the shared signal helper with ALL but without PREPOST. When waiters exist, it sets the count to zero and wakes every waiter while releasing the wait-queue lock and restoring interrupt state. With a nonnegative count, it leaves that count unchanged: the implementation is narrower than the nearby comment that says the count always returns to zero. Inactive semaphores fail with `KERN_TERMINATED`. [semaphore_signal_all](../../../xnu/osfmk/kern/sync_sema.c#L338-L388).

**Declarations:** [`semaphore_signal_all`](../../../xnu/osfmk/mach/semaphore.defs#L59) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_signal_all(
  semaphore : semaphore_t);
```

**Local body:** [`semaphore_signal_all`](../../../xnu/osfmk/kern/sync_sema.c#L553).
Calls visible in this body include `semaphore_signal_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/sync_sema.c#L553-L569):
<!-- source-excerpt: ../../../xnu/osfmk/kern/sync_sema.c#L553-L569 -->
```c
semaphore_signal_all(
	semaphore_t             semaphore)
{
	kern_return_t kr;

	if (semaphore == SEMAPHORE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kr = semaphore_signal_internal(semaphore,
	    THREAD_NULL,
	    SEMAPHORE_SIGNAL_ALL);
	if (kr == KERN_NOT_WAITING) {
		return KERN_SUCCESS;
	}
	return kr;
}
```

**User wrapper:** [`semaphore_signal_all`](../../../xnu/libsyscall/mach/semaphore.c#L43).
Calls visible in this body include `semaphore_signal_all_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L43-L46):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L43-L46 -->
```c
semaphore_signal_all(mach_port_t signal_semaphore)
{
	return semaphore_signal_all_trap(signal_semaphore);
}
```

### 617202: semaphore_wait

Consume a semaphore count or register/block as a waiter.

**Mechanism:** Under the semaphore lock, consumes an available permit or records the presence of waiters with count `-1` and asserts an abort-safe wait. The count is a waiter-present marker, not a negative waiter total. After unlocking, the non-continuation MIG body blocks through the handoff helper and translates wakeup, timeout, interruption and destruction into success, timed-out, aborted and terminated results. [semaphore_wait](../../../xnu/osfmk/kern/sync_sema.c#L605-L623). [Wait registration and blocking](../../../xnu/osfmk/kern/sync_sema.c#L659-L801).

**Declarations:** [`semaphore_wait`](../../../xnu/osfmk/mach/semaphore.defs#L62) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_wait(
  semaphore : semaphore_t);
```

**Local body:** [`semaphore_wait`](../../../xnu/osfmk/kern/sync_sema.c#L789).
Calls visible in this body include `semaphore_wait_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/sync_sema.c#L789-L798):
<!-- source-excerpt: ../../../xnu/osfmk/kern/sync_sema.c#L789-L798 -->
```c
semaphore_wait(
	semaphore_t             semaphore)
{
	if (semaphore == SEMAPHORE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return semaphore_wait_internal(semaphore, SEMAPHORE_NULL,
	           0ULL, SEMAPHORE_OPTION_NONE, SEMAPHORE_CONT_NULL);
}
```

**User wrapper:** [`semaphore_wait`](../../../xnu/libsyscall/mach/semaphore.c#L55).
Calls visible in this body include `semaphore_wait_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L55-L58):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L55-L58 -->
```c
semaphore_wait(mach_port_t wait_semaphore)
{
	return semaphore_wait_trap(wait_semaphore);
}
```

### 617203: semaphore_signal_thread

Signal the specified thread waiting on a semaphore.

**Mechanism:** A non-null thread restricts the wakeup to that thread on this semaphore’s wait queue; absence of that waiter returns `KERN_NOT_WAITING`. A null thread selects any existing waiter. Unlike ordinary signal, this call does not prepost a permit when nobody is waiting. The semaphore lock and scheduler interrupt level protect the active/count check and wakeup selection. [semaphore_signal_thread](../../../xnu/osfmk/kern/sync_sema.c#L338-L415).

**Declarations:** [`semaphore_signal_thread`](../../../xnu/osfmk/mach/semaphore.defs#L66) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_signal_thread(
  semaphore : semaphore_t;
  thread : thread_act_t);
```

**Local body:** [`semaphore_signal_thread`](../../../xnu/osfmk/kern/sync_sema.c#L427).
Calls visible in this body include `semaphore_signal_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/sync_sema.c#L427-L437):
<!-- source-excerpt: ../../../xnu/osfmk/kern/sync_sema.c#L427-L437 -->
```c
semaphore_signal_thread(
	semaphore_t     semaphore,
	thread_t        thread)
{
	if (semaphore == SEMAPHORE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return semaphore_signal_internal(semaphore, thread,
	           SEMAPHORE_OPTION_NONE);
}
```

**User wrapper:** [`semaphore_signal_thread`](../../../xnu/libsyscall/mach/semaphore.c#L49).
Calls visible in this body include `semaphore_signal_thread_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L49-L52):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L49-L52 -->
```c
semaphore_signal_thread(mach_port_t signal_semaphore, mach_port_t thread_act)
{
	return semaphore_signal_thread_trap(signal_semaphore, thread_act);
}
```

### 617204: semaphore_timedwait

Validate the relative timeout, calculate a deadline and wait for the semaphore until completion or timeout.

**Mechanism:** Rejects an invalid timespec before touching the wait queue. `{0,0}` selects a nonblocking attempt; a positive interval becomes an absolute deadline. The shared locked wait path first consumes an existing permit, so a zero timeout can succeed; otherwise it returns timed-out or installs an abort-safe timed wait. The MIG wrapper uses the stack-preserving, non-continuation form. [semaphore_timedwait](../../../xnu/osfmk/kern/sync_sema.c#L867-L892).

**Declarations:** [`semaphore_timedwait`](../../../xnu/osfmk/mach/semaphore.defs#L70) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_timedwait(
  semaphore : semaphore_t;
  wait_time : mach_timespec_t);
```

**Local body:** [`semaphore_timedwait`](../../../xnu/osfmk/kern/sync_sema.c#L867).
Calls visible in this body include `BAD_MACH_TIMESPEC`, `semaphore_deadline`, `semaphore_wait_internal`.

**User wrapper:** [`semaphore_timedwait`](../../../xnu/libsyscall/mach/semaphore.c#L61).
Calls visible in this body include `semaphore_timedwait_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L61-L66):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L61-L66 -->
```c
semaphore_timedwait(mach_port_t wait_semaphore, mach_timespec_t wait_time)
{
	return semaphore_timedwait_trap(wait_semaphore,
	           wait_time.tv_sec,
	           wait_time.tv_nsec);
}
```

### 617205: semaphore_wait_signal

Combine signaling one semaphore with waiting on another through the semaphore wait implementation.

**Mechanism:** Registers the wait, or resolves an immediately available permit/error, before signaling the second semaphore. The wait lock is released before the signal lock is acquired. A waiting caller can hand execution directly to the awakened signal waiter. If the signal semaphore has died, it clears its own wait; an already-delivered wakeup wins, otherwise interruption is converted to `KERN_TERMINATED`. [semaphore_wait_signal](../../../xnu/osfmk/kern/sync_sema.c#L659-L778).

**Declarations:** [`semaphore_wait_signal`](../../../xnu/osfmk/mach/semaphore.defs#L74) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_wait_signal(
  wait_semaphore : semaphore_t;
  signal_semaphore: semaphore_t);
```

**Local body:** [`semaphore_wait_signal`](../../../xnu/osfmk/kern/sync_sema.c#L958).
Calls visible in this body include `semaphore_wait_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/sync_sema.c#L958-L968):
<!-- source-excerpt: ../../../xnu/osfmk/kern/sync_sema.c#L958-L968 -->
```c
semaphore_wait_signal(
	semaphore_t             wait_semaphore,
	semaphore_t             signal_semaphore)
{
	if (wait_semaphore == SEMAPHORE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return semaphore_wait_internal(wait_semaphore, signal_semaphore,
	           0ULL, SEMAPHORE_OPTION_NONE, SEMAPHORE_CONT_NULL);
}
```

**User wrapper:** [`semaphore_wait_signal`](../../../xnu/libsyscall/mach/semaphore.c#L69).
Calls visible in this body include `semaphore_wait_signal_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L69-L72):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L69-L72 -->
```c
semaphore_wait_signal(mach_port_t wait_semaphore, mach_port_t signal_semaphore)
{
	return semaphore_wait_signal_trap(wait_semaphore, signal_semaphore);
}
```

### 617206: semaphore_timedwait_signal

Combine signal and timed wait after validating and converting the timeout.

**Mechanism:** Validates the wait timespec, selects a nonblocking attempt for zero or computes an absolute deadline, then uses the same wait-before-signal protocol. Even when waiting resolves immediately, the helper still signals the second semaphore before returning. Invalid timespecs are rejected before that side effect. Signal-semaphore destruction explicitly cancels the pending wait rather than leaving the caller stranded. [semaphore_timedwait_signal](../../../xnu/osfmk/kern/sync_sema.c#L1020-L1047). [Signal and cancellation ordering](../../../xnu/osfmk/kern/sync_sema.c#L704-L752).

**Declarations:** [`semaphore_timedwait_signal`](../../../xnu/osfmk/mach/semaphore.defs#L78) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_timedwait_signal(
  wait_semaphore : semaphore_t;
  signal_semaphore: semaphore_t;
  wait_time : mach_timespec_t);
```

**Local body:** [`semaphore_timedwait_signal`](../../../xnu/osfmk/kern/sync_sema.c#L1020).
Calls visible in this body include `BAD_MACH_TIMESPEC`, `semaphore_deadline`, `semaphore_wait_internal`.

**User wrapper:** [`semaphore_timedwait_signal`](../../../xnu/libsyscall/mach/semaphore.c#L75).
Calls visible in this body include `semaphore_timedwait_signal_trap`.

[Implementation excerpt](../../../xnu/libsyscall/mach/semaphore.c#L75-L83):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/semaphore.c#L75-L83 -->
```c
semaphore_timedwait_signal(mach_port_t wait_semaphore,
    mach_port_t signal_semaphore,
    mach_timespec_t wait_time)
{
	return semaphore_timedwait_signal_trap(wait_semaphore,
	           signal_semaphore,
	           wait_time.tv_sec,
	           wait_time.tv_nsec);
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
