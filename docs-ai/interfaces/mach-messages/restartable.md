# Mach messages: restartable

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/restartable.defs](../../../xnu/osfmk/mach/restartable.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 8000: task_restartable_ranges_register

Validate and register restartable instruction ranges for the current eligible task.

**Mechanism:** Only the current task may register. Validation precedes the task lock; translated tasks are rejected when Rosetta is configured. Installation requires a single-threaded task, and release kernels also reject replacing an existing registration. The creator installs the validated range representation while task creation is serialized by the task lock; failures leave the old registration intact. [task_restartable_ranges_register](../../../xnu/osfmk/kern/restartable.c#L535-L579).

**Declarations:** [`task_restartable_ranges_register`](../../../xnu/osfmk/mach/restartable.defs#L44) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_restartable_ranges_register(
  target_task : task_t;
  ranges : task_restartable_range_array_t);
```

**Local body:** [`task_restartable_ranges_register`](../../../xnu/osfmk/kern/restartable.c#L535).
Calls visible in this body include `current_task`, `task_is_translated`, `_ranges_validate`, `task_lock`, `_restartable_ranges_create`, `task_unlock`.

### 8001: task_restartable_ranges_synchronize

Request synchronization across the task's threads, using reset-PC AST/IPI acknowledgement where needed.

**Mechanism:** Only the current task is accepted; no registered ranges is a successful no-op. A priority floor bounds scheduler interference while the task lock serializes synchronization, with concurrent callers rejected as already waiting. A release fence precedes posting RESET_PCS ASTs to other threads. The caller waits for required acknowledgments/fault resolution, restarts enumeration after lock-dropping waits, then clears the in-flight flag and releases its priority floor. [task_restartable_ranges_synchronize](../../../xnu/osfmk/kern/restartable.c#L583-L685).

**Declarations:** [`task_restartable_ranges_synchronize`](../../../xnu/osfmk/mach/restartable.defs#L48) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_restartable_ranges_synchronize(
  target_task : task_t);
```

**Local body:** [`task_restartable_ranges_synchronize`](../../../xnu/osfmk/kern/restartable.c#L583).
Calls visible in this body include `current_task`, `thread_priority_floor_start`, `task_lock`, `os_atomic_thread_fence`, `queue_iterate`, `current_thread`, `act_set_ast_reset_pcs`, `thread_rr_wait_if_needed`, `task_unlock`, `thread_priority_floor_end`.
