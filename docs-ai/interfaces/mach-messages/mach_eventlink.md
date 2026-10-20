# Mach messages: mach_eventlink

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_eventlink.defs](../../../xnu/osfmk/mach/mach_eventlink.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 716200: mach_eventlink_create

Create an eventlink pair for count-based synchronization and return endpoint capabilities.

**Mechanism:** Accepts only the current task and `MELC_OPTION_NO_COPYIN`. Allocation creates one shared base, two `IKOT_EVENTLINK` ports with send rights, two endpoint counters/association fields and a FIFO waitq. Returns both ports as the endpoint pair. Counter wait/signal operations use the separate BSD entries described in the syscall catalog. [`Implementation`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L155).

**Declarations:** [`mach_eventlink_create`](../../../xnu/osfmk/mach/mach_eventlink.defs#L39) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_eventlink_create(
  task : task_t;
  option : mach_eventlink_create_option_t;
 out eventlink_pair : eventlink_port_pair_t);
```

**Local body:** [`mach_eventlink_create`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L205).
Calls visible in this body include `current_task`, `ipc_eventlink_alloc`.

### 716201: mach_eventlink_destroy

Destroy an eventlink endpoint/pair according to its active-state protocol.

**Mechanism:** Calls internal pair teardown and returns success unconditionally, including when teardown reports termination. Under the shared base lock at scheduler priority, teardown clears both associations/port pointers, forces wakeups and invalidates the waitq. After unlocking it deallocates only the local endpoint port, disables the remote port's kobject without destroying that port, releases associated thread references and drops both port-owned base references. [Wrapper and teardown](../../../xnu/osfmk/ipc/ipc_eventlink.c#L239).

**Declarations:** [`mach_eventlink_destroy`](../../../xnu/osfmk/mach/mach_eventlink.defs#L44) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_eventlink_destroy(
  eventlink : eventlink_consume_ref_t);
```

**Local body:** [`mach_eventlink_destroy`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L239).
Calls visible in this body include `ipc_eventlink_destroy_internal`.

[Implementation excerpt](../../../xnu/osfmk/ipc/ipc_eventlink.c#L239-L246):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_eventlink.c#L239-L246 -->
```c
mach_eventlink_destroy(
	struct ipc_eventlink *ipc_eventlink)
{
	ipc_eventlink_destroy_internal(ipc_eventlink);

	/* mach_eventlink_destroy should succeed for terminated eventlink */
	return KERN_SUCCESS;
}
```

### 716202: mach_eventlink_associate

Associate a thread with an eventlink endpoint, retaining the thread and validating endpoint state under the eventlink lock.

**Mechanism:** Rejects nonzero copyin addresses/masks and incompatible thread/associate-on-wait combinations. Under the shared eventlink lock at scheduler priority, requires an active unassociated endpoint and stores either a retained thread or the wildcard sentinel consumed on wait. Reassociation returns `KERN_NAME_EXISTS`. [`Implementation`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L361).

**Declarations:** [`mach_eventlink_associate`](../../../xnu/osfmk/mach/mach_eventlink.defs#L48) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_eventlink_associate(
  eventlink : eventlink_t;
  thread : thread_t;
  copyin_addr_wait : mach_vm_address_t;
  copyin_mask_wait : uint64_t;
  copyin_addr_signal : mach_vm_address_t;
  copyin_mask_signal : uint64_t;
  option : mach_eventlink_associate_option_t);
```

**Local body:** [`mach_eventlink_associate`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L361).
Calls visible in this body include `splsched`, `ipc_eventlink_lock`, `ipc_eventlink_active`, `ipc_eventlink_unlock`, `splx`, `thread_reference`.

### 716203: mach_eventlink_disassociate

Remove an endpoint's thread association and wake/adjust wait state as required.

**Mechanism:** Requires `MELD_OPTION_NONE` and an active associated endpoint. Clears `el_thread` and forces a wake while holding the base lock, then restores priority and releases the retained thread unless it was the wildcard sentinel. Disassociation therefore also affects an already waiting caller. [`Implementation`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L428).

**Declarations:** [`mach_eventlink_disassociate`](../../../xnu/osfmk/mach/mach_eventlink.defs#L57) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_eventlink_disassociate(
  eventlink : eventlink_t;
  option : mach_eventlink_disassociate_option_t);
```

**Local body:** [`mach_eventlink_disassociate`](../../../xnu/osfmk/ipc/ipc_eventlink.c#L428).
Calls visible in this body include `splsched`, `ipc_eventlink_lock`, `ipc_eventlink_active`, `ipc_eventlink_unlock`, `splx`, `ipc_eventlink_signal_internal_locked`, `thread_deallocate`.
