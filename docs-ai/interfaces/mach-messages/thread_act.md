# Mach messages: thread_act

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/thread_act.defs](../../../xnu/osfmk/mach/thread_act.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3600: thread_terminate_from_user

**Interface contract:**

> Destroy the target thread. JMM - For legacy reasons this consumes a reference to the target thread. This will have to change in the future because we want the interfaces to be able to be defined in more standard IDLs and transports, and most of them do not support the notion of reference ownership transfers (just sharing).

**Mechanism:** Rejects pthread-managed threads before reaching general termination. The internal path marks an active thread inactive under its mutex, posts the abort/APC work, interrupts an existing wait or starts a never-started thread so it can terminate, and unpins its control port. A successful remote request waits for the target to stop; the target still performs final termination itself. [thread_terminate_from_user](../../../xnu/osfmk/kern/thread_act.c#L285-L379).

**Declarations:** [`thread_terminate_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L102) (`server64`, `server32`, `local64`); [`thread_terminate`](../../../xnu/osfmk/mach/thread_act.defs#L102) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_terminate_from_user(
  target_act : thread_act_consume_ref_t);
```

**Local body:** [`thread_terminate_from_user`](../../../xnu/osfmk/kern/thread_act.c#L368).
Calls visible in this body include `thread_get_tag`, `thread_terminate`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L368-L380):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L368-L380 -->
```c
thread_terminate_from_user(
	thread_t                thread)
{
	if (thread == THREAD_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	if (thread_get_tag(thread) & THREAD_TAG_PTHREAD) {
		return KERN_DENIED;
	}

	return thread_terminate(thread);
}
```

### 3601: act_get_state_to_user

**Interface contract:**

> Return the selected state information for the target thr_act. If the thr_act is currently executing, the results may be stale. [Flavor THREAD_STATE_FLAVOR_LIST provides a list of valid flavors for the target thread.]

**Mechanism:** This compatibility activation entry rejects the current thread, then calls `thread_get_state_to_user`. Consequently its remaining behavior is the same stop/hold/read/translate protocol used for remote thread state, including inspection-state support and aborted/terminated failures. It is not a separate saved-state object or alternative register representation. [act_get_state_to_user](../../../xnu/osfmk/kern/thread_act.c#L1568-L1580).

**Declarations:** [`act_get_state_to_user`](../../../xnu/osfmk/mach/thread_act.defs#L112) (`server64`, `server32`, `local64`); [`act_get_state`](../../../xnu/osfmk/mach/thread_act.defs#L112) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
act_get_state_to_user(
  target_act : thread_read_t;
  flavor : int;
 out old_state : thread_state_t, CountInOut);
```

**Local body:** [`act_get_state_to_user`](../../../xnu/osfmk/kern/thread_act.c#L1568).
Calls visible in this body include `current_thread`, `thread_get_state_to_user`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L1568-L1579):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L1568-L1579 -->
```c
act_get_state_to_user(
	thread_t                                thread,
	int                                             flavor,
	thread_state_t                  state,
	mach_msg_type_number_t  *count)
{
	if (thread == current_thread()) {
		return KERN_INVALID_ARGUMENT;
	}

	return thread_get_state_to_user(thread, flavor, state, count);
}
```

### 3602: act_set_state_from_user

**Interface contract:**

> Set the selected state information for the target thread. If the thread is currently executing, the state change may be ill-defined.

**Mechanism:** Rejects a request targeting the current thread and forwards all other arguments to the ordinary user-state setter. This preserves that setter’s security checks, authenticated conversion, stop/hold protocol and cleanup. The activation name therefore adds a self-target restriction rather than providing a bypass around thread_set_state policy. [act_set_state_from_user](../../../xnu/osfmk/kern/thread_act.c#L1532-L1544).

**Declarations:** [`act_set_state_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L127) (`server64`, `server32`, `local64`); [`act_set_state`](../../../xnu/osfmk/mach/thread_act.defs#L127) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
act_set_state_from_user(
  target_act : thread_act_t;
  flavor : int;
  new_state : thread_state_t);
```

**Local body:** [`act_set_state_from_user`](../../../xnu/osfmk/kern/thread_act.c#L1532).
Calls visible in this body include `current_thread`, `thread_set_state_from_user`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L1532-L1543):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L1532-L1543 -->
```c
act_set_state_from_user(
	thread_t                                thread,
	int                                             flavor,
	thread_state_t                  state,
	mach_msg_type_number_t  count)
{
	if (thread == current_thread()) {
		return KERN_INVALID_ARGUMENT;
	}

	return thread_set_state_from_user(thread, flavor, state, count);
}
```

### 3603: thread_get_state_to_user

**Interface contract:**

> Backward compatible old-style thread routines. These have different semantics than the new activation versions. Return the selected state information for the target thread. If the thread is currently executing, the results may be stale. [Flavor THREAD_STATE_FLAVOR_LIST provides a list of valid flavors for the target thr_act.]

**Mechanism:** The helper holds the thread mutex and, for an active remote thread, places a hold, drops the mutex, and stops it before reading machine state. It un-stops and releases that hold afterward; interrupted stopping returns aborted. Inspection threads can still supply state after activity ends. A successful machine read is then translated to the user representation, including architecture-specific state authentication rules. [thread_get_state_to_user](../../../xnu/osfmk/kern/thread_act.c#L832-L914).

**Declarations:** [`thread_get_state_to_user`](../../../xnu/osfmk/mach/thread_act.defs#L146) (`server64`, `server32`, `local64`); [`thread_get_state`](../../../xnu/osfmk/mach/thread_act.defs#L146) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_get_state_to_user(
  target_act : thread_read_t;
  flavor : thread_state_flavor_t;
 out old_state : thread_state_t, CountInOut);
```

**Local body:** [`thread_get_state_to_user`](../../../xnu/osfmk/kern/thread_act.c#L906).
Calls visible in this body include `thread_get_state_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L906-L913):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L906-L913 -->
```c
thread_get_state_to_user(
	thread_t                thread,
	int                                             flavor,
	thread_state_t                  state,                  /* pointer to OUT array */
	mach_msg_type_number_t  *state_count)   /*IN/OUT*/
{
	return thread_get_state_internal(thread, flavor, state, state_count, TSSF_TRANSLATE_TO_USER);
}
```

### 3604: thread_set_state_from_user

**Interface contract:**

> Set the selected state information for the target thread. If the thread is currently executing, the state change may be ill-defined.

**Mechanism:** Requests entitlement-aware state conversion through the shared setter. Security policy is checked before taking the thread mutex and may arrange a guard violation; denied changes return no-access. User state is authenticated/translated before a remote thread is held and stopped, then the machine setter installs it. Every stop branch releases the hold, and external-modification statistics increment only after successful user-originated installation. [thread_set_state_from_user](../../../xnu/osfmk/kern/thread_act.c#L922-L1018).

**Declarations:** [`thread_set_state_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L161) (`server64`, `server32`, `local64`); [`thread_set_state`](../../../xnu/osfmk/mach/thread_act.defs#L161) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_set_state_from_user(
  target_act : thread_act_t;
  flavor : thread_state_flavor_t;
  new_state : thread_state_t);
```

**Local body:** [`thread_set_state_from_user`](../../../xnu/osfmk/kern/thread_act.c#L1009).
Calls visible in this body include `thread_set_state_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L1009-L1018):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L1009-L1018 -->
```c
thread_set_state_from_user(
	thread_t                thread,
	int                                             flavor,
	thread_state_t                  state,
	mach_msg_type_number_t  state_count)
{
	audit_token_t *audit = NULL;
	return thread_set_state_internal(thread, flavor, state, state_count, NULL,
	           0, TSSF_TRANSLATE_TO_USER | TSSF_CHECK_ENTITLEMENT, audit);
}
```

### 3605: thread_suspend

**Interface contract:**

> Increment the suspend count for the target thread. Once this call has completed, the thread will not execute any further user or meta- instructions. Once suspended, a thread may not execute again until its suspend count is zero, and the suspend count for its task is also zero.

**Mechanism:** Under the thread mutex, increments both total and legacy user stop counts; only transition from zero total user holds adds the underlying thread hold. It rejects kernel-task threads and inactive targets, and waits for a remote target to stop after unlocking. The body does not create a resume-port right despite the broader historical comment above it. [thread_suspend](../../../xnu/osfmk/kern/thread_act.c#L454-L476). [Public wait ordering](../../../xnu/osfmk/kern/thread_act.c#L550-L571).

**Declarations:** [`thread_suspend`](../../../xnu/osfmk/mach/thread_act.defs#L179) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_suspend(
  target_act : thread_read_t);
```

**Local body:** [`thread_suspend`](../../../xnu/osfmk/kern/thread_act.c#L550).
Calls visible in this body include `get_threadtask`, `thread_mtx_lock`, `thread_suspend_internal`, `thread_mtx_unlock`, `current_thread`, `thread_wait`.

### 3606: thread_resume

**Interface contract:**

> Decrement the suspend count for the target thread, if that count is not already zero.

**Mechanism:** Requires a live nonkernel thread and a nonzero legacy stop count, then decrements legacy and total user counts under the thread mutex. Only the last user count releases the underlying hold. That release starts an unstarted thread or wakes a thread parked for suspension. A normal token-based suspension alone cannot satisfy the legacy-resume check. [thread_resume](../../../xnu/osfmk/kern/thread_act.c#L430-L534). [Public wrapper](../../../xnu/osfmk/kern/thread_act.c#L574-L587).

**Declarations:** [`thread_resume`](../../../xnu/osfmk/mach/thread_act.defs#L186) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_resume(
  target_act : thread_read_t);
```

**Local body:** [`thread_resume`](../../../xnu/osfmk/kern/thread_act.c#L574).
Calls visible in this body include `get_threadtask`, `thread_mtx_lock`, `thread_resume_internal`, `thread_mtx_unlock`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread_act.c#L574-L587):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread_act.c#L574-L587 -->
```c
thread_resume(thread_t thread)
{
	kern_return_t kr = KERN_SUCCESS;

	if (thread == THREAD_NULL || get_threadtask(thread) == kernel_task) {
		return KERN_INVALID_ARGUMENT;
	}

	thread_mtx_lock(thread);
	kr = thread_resume_internal(thread, THREAD_SUSPEND_LEGACY);
	thread_mtx_unlock(thread);

	return kr;
}
```

### 3607: thread_abort

**Interface contract:**

> Cause any user or meta- instructions currently being executed by the target thread to be aborted. [Meta- instructions consist of the basic traps for IPC (e.g., msg_send, msg_receive) and self-identification (e.g., task_self, thread_self, thread_reply). Calls described by MiG interfaces are not meta-instructions themselves.]

**Mechanism:** Locks the thread mutex, rejects an inactive thread, marks abort/APC state through `act_abort`, and tries to clear the current wait with `THREAD_INTERRUPTED`. The helper uses the scheduler lock at raised interrupt level, ends priority depression, and upgrades an already pending safe abort to an ordinary abort. This asks the target to unwind at kernel-defined points; it does not directly edit user registers. [thread_abort](../../../xnu/osfmk/kern/thread_act.c#L721-L762).

**Declarations:** [`thread_abort`](../../../xnu/osfmk/mach/thread_act.defs#L198) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_abort(
  target_act : thread_act_t);
```

**Local body:** [`thread_abort`](../../../xnu/osfmk/kern/thread_act.c#L741).
Calls visible in this body include `thread_mtx_lock`, `act_abort`, `clear_wait`, `thread_mtx_unlock`.

### 3608: thread_abort_safely

**Interface contract:**

> Cause any user or meta- instructions currently being executed by the target thread to be aborted so that they are transparently restartable. This call fails if the abort would result in a non-restartable condition. Retry is the caller's responsibility. [Meta- instructions consist of the basic traps for IPC (e.g., msg_send, msg_receive) and self-identification (e.g., task_self, thread_self, thread_reply). Calls described by MiG interfaces are not meta-instructions themselves.]

**Mechanism:** Under the thread mutex and scheduler lock, first tries to interrupt a wait only if the thread is at a safe point. Otherwise it records abort-safe state and posts APC work if no abort is already pending, also ending depression. Inactive threads return terminated; success can mean deferred abort processing rather than immediate removal from a wait queue. [thread_abort_safely](../../../xnu/osfmk/kern/thread_act.c#L765-L798).

**Declarations:** [`thread_abort_safely`](../../../xnu/osfmk/mach/thread_act.defs#L213) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_abort_safely(
  target_act : thread_act_t);
```

**Local body:** [`thread_abort_safely`](../../../xnu/osfmk/kern/thread_act.c#L765).
Calls visible in this body include `thread_mtx_lock`, `splsched`, `thread_lock`, `clear_wait_internal`, `thread_set_apc_ast_locked`, `thread_depress_abort_locked`, `thread_unlock`, `splx`, `thread_mtx_unlock`.

### 3609: thread_depress_abort_from_user

Cancel priority depression for a thread under thread control serialization.

**Mechanism:** Holds the thread mutex and rejects inactive targets. The helper additionally takes the scheduler lock at raised interrupt level, refuses to cancel poll-depression, and returns `KERN_NOT_DEPRESSED` when no ordinary depression is eligible. Otherwise it clears depression flags, recomputes scheduling priority and cancels the depression timer, decrementing its active count only when cancellation succeeds. [Wrapper](../../../xnu/osfmk/kern/thread_act.c#L692-L712), [depression and timer handling](../../../xnu/osfmk/kern/syscall_subr.c#L507-L556).

**Declarations:** [`thread_depress_abort_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L217) (`server64`, `server32`, `local64`); [`thread_depress_abort`](../../../xnu/osfmk/mach/thread_act.defs#L217) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_depress_abort_from_user(
  thread : thread_act_t);
```

**Local body:** [`thread_depress_abort_from_user`](../../../xnu/osfmk/kern/thread_act.c#L692).
Calls visible in this body include `thread_mtx_lock`, `thread_depress_abort`, `thread_mtx_unlock`.

### 3610: thread_get_special_port_from_user

**Interface contract:**

> Returns the current value of the selected special port associated with the target thread.

**Mechanism:** Converts the destination to an inspectable thread, preserves its actual capability flavor, and applies the movable-self-control policy check for a thread of the current task. The selector allows a read capability to obtain read/inspect, while inspect permits inspect only. The internal helper checks activity under the thread mutex and copies/converts the selected capability; the wrapper drops its temporary thread reference. [thread_get_special_port_from_user](../../../xnu/osfmk/kern/ipc_tt.c#L1515-L1678).

**Declarations:** [`thread_get_special_port_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L230) (`server64`, `server32`, `local64`); [`thread_get_special_port`](../../../xnu/osfmk/mach/thread_act.defs#L230) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_get_special_port_from_user(
  port : mach_port_t;
  which_port : int;
 out special_port : mach_port_t);
```

**Local body:** [`thread_get_special_port_from_user`](../../../xnu/osfmk/kern/ipc_tt.c#L1590).
Calls visible in this body include `current_task`, `convert_port_to_thread_inspect_no_eval`, `get_thread_ro`, `ip_type`, `mac_task_check_get_movable_control_port`, `task_is_immovable`, `thread_get_special_port_internal`, `thread_deallocate`.

### 3611: thread_set_special_port

**Interface contract:**

> Set one of the special ports associated with the target thread.

**Mechanism:** Only THREAD_KERNEL_PORT is recognized. A permitted write requires CONFIG_CSR and a successful CSR kernel-debugger exception check; the configuration-disabled body returns KERN_NO_ACCESS as well. The body rejects un-stashable send rights and inactive targets; allowed writes store the supplied right under the thread mutex. Its local `old` variable remains null, so the apparent release block does not actually capture/release the prior settable-self right in this implementation. [thread_set_special_port](../../../xnu/osfmk/kern/ipc_tt.c#L1700-L1755).

**Declarations:** [`thread_set_special_port`](../../../xnu/osfmk/mach/thread_act.defs#L246) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_set_special_port(
  thr_act : thread_act_t;
  which_port : int;
  special_port : mach_port_t);
```

**Local body:** [`thread_set_special_port`](../../../xnu/osfmk/kern/ipc_tt.c#L1700).
Calls visible in this body include `ipc_can_stash_naked_send`, `csr_check`, `thread_mtx_lock`, `thread_mtx_unlock`, `IP_VALID`, `ipc_port_release_send`, `else`.

### 3612: thread_info

**Interface contract:**

> Returns information about the target thread.

**Mechanism:** Holds the thread mutex and admits either active or inspection threads, allowing corpse-style inspection after normal activity ends. Flavor-specific work takes the scheduler lock as needed: BASIC_INFO snapshots accounted state, IDENTIFIER_INFO returns thread ID/handle/dispatch address, and scheduler layouts validate the actual scheduling mode. FIFO_INFO is explicitly invalid-policy; count checks precede writing each supported layout. [thread_info](../../../xnu/osfmk/kern/thread_act.c#L805-L829). [Flavor implementation](../../../xnu/osfmk/kern/thread.c#L2036-L2185).

**Declarations:** [`thread_info`](../../../xnu/osfmk/mach/thread_act.defs#L254) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_info(
                target_act : thread_inspect_t;
                flavor : thread_flavor_t;
        out thread_info_out : thread_info_t, CountInOut);
```

**Local body:** [`thread_info`](../../../xnu/osfmk/kern/thread_act.c#L805).
Calls visible in this body include `thread_mtx_lock`, `thread_info_internal`, `thread_mtx_unlock`.

### 3613: thread_set_exception_ports

**Interface contract:**

> Set an exception handler for a thread on one or more exception types

**Mechanism:** Validates mask, port suitability, behavior and state flavor for a nonhardened update before applying MAC policy. Under the thread mutex it rejects inactive targets, lazily creates an exception-action array, and updates selected permitted entries with copied rights and metadata. Displaced rights and the incoming right are released after unlocking; per-action label policy can prevent individual changes. [thread_set_exception_ports](../../../xnu/osfmk/kern/ipc_tt.c#L4024-L4140).

**Declarations:** [`thread_set_exception_ports`](../../../xnu/osfmk/mach/thread_act.defs#L262) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_set_exception_ports(
   thread : thread_act_t;
   exception_mask : exception_mask_t;
   new_port : mach_port_t;
   behavior : exception_behavior_t;
   new_flavor : thread_state_flavor_t);
```

**Local body:** [`thread_set_exception_ports`](../../../xnu/osfmk/kern/ipc_tt.c#L4122).
Calls visible in this body include `set_exception_ports_validation`, `get_threadtask`, `thread_set_exception_ports_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/ipc_tt.c#L4122-L4140):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ipc_tt.c#L4122-L4140 -->
```c
thread_set_exception_ports(
	thread_t                thread,
	exception_mask_t        exception_mask,
	ipc_port_t              new_port,
	exception_behavior_t    new_behavior,
	thread_state_flavor_t   new_flavor)
{
	if (thread == THREAD_NULL) {
		return KERN_INVALID_ARGUMENT;
	}
	bool hardened_exception_flow = false;
	kern_return_t kr = set_exception_ports_validation(get_threadtask(thread),
	    exception_mask, new_port, new_behavior, new_flavor, hardened_exception_flow);
	if (kr != KERN_SUCCESS) {
		return kr;
	}

	return thread_set_exception_ports_internal(thread, exception_mask, new_port, new_behavior, new_flavor, false);
}
```

### 3614: thread_get_exception_ports_from_user

**Interface contract:**

> Lookup some of the old exception handlers for a thread

**Mechanism:** Requires thread-control conversion to return actual handler rights. The shared query validates activity and mask under the thread mutex; an unallocated action array yields zero groups. Otherwise identical port/behavior/flavor triples share a mask, with copied send rights returned up to capacity. Stored registrations remain owned by the thread, and the wrapper drops its temporary thread reference. [thread_get_exception_ports_from_user](../../../xnu/osfmk/kern/ipc_tt.c#L4492-L4589). [Control conversion](../../../xnu/osfmk/kern/ipc_tt.c#L4632-L4653).

**Declarations:** [`thread_get_exception_ports_from_user`](../../../xnu/osfmk/mach/thread_act.defs#L272) (`server64`, `server32`, `local64`); [`thread_get_exception_ports`](../../../xnu/osfmk/mach/thread_act.defs#L272) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_get_exception_ports_from_user(
   port : mach_port_t;
   exception_mask : exception_mask_t;
    out masks : exception_mask_array_t;
    out old_handlers : exception_handler_array_t, SameCount;
    out old_behaviors : exception_behavior_array_t, SameCount;
    out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`thread_get_exception_ports_from_user`](../../../xnu/osfmk/kern/ipc_tt.c#L4632).
Calls visible in this body include `convert_port_to_thread`, `thread_get_exception_ports`, `thread_deallocate`.

### 3615: thread_swap_exception_ports

**Interface contract:**

> Set an exception handler for a thread on one or more exception types. At the same time, return the previously defined exception handlers for those types.

**Mechanism:** After common validation/MAC checks, locks the thread, rejects inactivity, and lazily allocates its action array. It returns grouped old port/behavior/flavor triples while replacing selected actions with copied new rights. The loop stops when the supplied result capacity is reached, so later exceptions are not necessarily changed. Cleanup releases displaced references and the incoming right after unlocking. [thread_swap_exception_ports](../../../xnu/osfmk/kern/ipc_tt.c#L4253-L4362).

**Declarations:** [`thread_swap_exception_ports`](../../../xnu/osfmk/mach/thread_act.defs#L291) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_swap_exception_ports(
   thread : thread_act_t;
   exception_mask : exception_mask_t;
   new_port : mach_port_t;
   behavior : exception_behavior_t;
   new_flavor : thread_state_flavor_t;
    out masks : exception_mask_array_t;
    out old_handlers : exception_handler_array_t, SameCount;
    out old_behaviors : exception_behavior_array_t, SameCount;
    out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`thread_swap_exception_ports`](../../../xnu/osfmk/kern/ipc_tt.c#L4253).
Calls visible in this body include `task_is_privileged`, `current_task`, `set_exception_ports_validation`, `get_threadtask`, `mac_task_check_set_thread_exception_ports`, `mac_exc_create_label_for_current_proc`, `thread_mtx_lock`, `thread_mtx_unlock`, `mac_exc_free_label`, `get_thread_ro`, `ipc_thread_init_exc_actions`, `mac_exc_update_action_label`.

### 3616: thread_policy

Query/change the historical thread scheduling-policy representation according to this declaration.

**Mechanism:** Builds a historical policy-limit structure while holding the thread mutex. Without set_limit it rejects a base priority exceeding the thread’s current maximum; with set_limit it uses the supplied base as the proposed limit. It unlocks before calling `thread_set_policy`. The downstream implementation validates that limit but deliberately does not apply it, so this interface does not establish a new maximum priority. [thread_policy](../../../xnu/osfmk/kern/mk_sp.c#L181-L355).

**Declarations:** [`thread_policy`](../../../xnu/osfmk/mach/thread_act.defs#L305) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_thread_policy`](../../../xnu/osfmk/mach/thread_act.defs#L305) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine thread_policy(
 thr_act : thread_act_t;
 policy : policy_t;
 base : policy_base_t;
 set_limit : boolean_t);
```

**Local body:** [`thread_policy`](../../../xnu/osfmk/kern/mk_sp.c#L181).
Calls visible in this body include `thread_mtx_lock`, `invalid_policy`, `thread_mtx_unlock`, `thread_set_policy`.

**User wrapper:** [`thread_policy`](../../../xnu/libsyscall/mach/thread_act.c#L35).
Calls visible in this body include `_kernelrpc_thread_policy`, `_pthread_clear_qos_tsd`.

[Implementation excerpt](../../../xnu/libsyscall/mach/thread_act.c#L35-L47):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/thread_act.c#L35-L47 -->
```c
thread_policy(thread_act_t thr_act, policy_t policy, policy_base_t base, mach_msg_type_number_t baseCnt, boolean_t set_limit)
{
	kern_return_t kr;

	kr = _kernelrpc_thread_policy(thr_act, policy, base, baseCnt, set_limit);
	if (kr == KERN_SUCCESS) {
		_pthread_clear_qos_tsd(thr_act);
	} else if (kr == KERN_POLICY_STATIC) {
		kr = KERN_SUCCESS;
	}

	return kr;
}
```

### 3617: thread_policy_set

**Interface contract:**

> Set/get policy information for a thread. (Approved Mac OS X microkernel interface)

**Mechanism:** Rejects forbidden static/QoS changes and work-interval configurations that disallow realtime. Existing QoS is temporarily removed and restored if applying the replacement fails. The internal dispatcher holds the thread mutex, validates flavor/count, and uses scheduler locking for mode/priority changes; realtime computation is raised toward half the constraint and capped. Affinity drops the mutex before taking task-level locks; deferred policy effects complete after unlocking. [thread_policy_set](../../../xnu/osfmk/kern/thread_policy.c#L265-L623).

**Declarations:** [`thread_policy_set`](../../../xnu/osfmk/mach/thread_act.defs#L316) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_thread_policy_set`](../../../xnu/osfmk/mach/thread_act.defs#L316) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine thread_policy_set(
 thread : thread_act_t;
 flavor : thread_policy_flavor_t;
 policy_info : thread_policy_t);
```

**Local body:** [`thread_policy_set`](../../../xnu/osfmk/kern/thread_policy.c#L265).
Calls visible in this body include `thread_is_static_param`, `os_atomic_load`, `thread_remove_qos_policy`, `thread_policy_set_internal`.

**User wrapper:** [`thread_policy_set`](../../../xnu/libsyscall/mach/thread_act.c#L50).
Calls visible in this body include `_kernelrpc_thread_policy_set`, `_pthread_clear_qos_tsd`.

[Implementation excerpt](../../../xnu/libsyscall/mach/thread_act.c#L50-L62):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/thread_act.c#L50-L62 -->
```c
thread_policy_set(thread_act_t thread, thread_policy_flavor_t flavor, thread_policy_t policy_info, mach_msg_type_number_t policy_infoCnt)
{
	kern_return_t kr;

	kr = _kernelrpc_thread_policy_set(thread, flavor, policy_info, policy_infoCnt);
	if (kr == KERN_SUCCESS) {
		_pthread_clear_qos_tsd(thread);
	} else if (kr == KERN_POLICY_STATIC) {
		kr = KERN_SUCCESS;
	}

	return kr;
}
```

### 3618: thread_policy_get

Return the selected thread-policy flavor under thread/scheduler locking.

**Mechanism:** Locks the thread and rejects inactivity, then reads flavor-specific policy or returns requested defaults. Scheduler fields are additionally protected by the scheduler lock; demoted threads can report their saved mode. Asking realtime policy of a non-realtime thread switches the result to defaults. Detailed policy-state inspection is privileged, affinity is architecture-dependent, and unsupported/count-invalid flavors return errors. [thread_policy_get](../../../xnu/osfmk/kern/thread_policy.c#L1283-L1494).

**Declarations:** [`thread_policy_get`](../../../xnu/osfmk/mach/thread_act.defs#L321) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_policy_get(
 thread : thread_inspect_t;
 flavor : thread_policy_flavor_t;
out policy_info : thread_policy_t, CountInOut;
inout get_default : boolean_t);
```

**Local body:** [`thread_policy_get`](../../../xnu/osfmk/kern/thread_policy.c#L1283).
Calls visible in this body include `thread_mtx_lock`, `thread_mtx_unlock`, `splsched`, `thread_lock`, `thread_unlock`, `splx`, `thread_affinity_is_supported`, `thread_affinity_get`, `task_is_privileged`, `current_task`, `proc_get_thread_policy_bitfield`, `proc_get_thread_policy_locked`.

### 3619: thread_sample

**Interface contract:**

> thread_get_assignment

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [thread_sample](../../../xnu/osfmk/mach/thread_act.defs#L337).

**Declarations:** [`thread_sample`](../../../xnu/osfmk/mach/thread_act.defs#L337) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine thread_sample(
  thread : thread_act_t;
  reply : mach_port_make_send_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3620: etap_trace_thread

Historical event-tracing control for a thread.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [etap_trace_thread](../../../xnu/osfmk/mach/thread_act.defs#L341).

**Declarations:** [`etap_trace_thread`](../../../xnu/osfmk/mach/thread_act.defs#L341) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine etap_trace_thread(
  target_act : thread_act_t;
  trace_status : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3621: thread_assign

Historical thread-to-processor-set assignment.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [thread_assign](../../../xnu/osfmk/mach/thread_act.defs#L345).

**Declarations:** [`thread_assign`](../../../xnu/osfmk/mach/thread_act.defs#L345) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine thread_assign(
  thread : thread_act_t;
  new_set : processor_set_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3622: thread_assign_default

Historical assignment to the default processor set.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [thread_assign_default](../../../xnu/osfmk/mach/thread_act.defs#L349).

**Declarations:** [`thread_assign_default`](../../../xnu/osfmk/mach/thread_act.defs#L349) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine thread_assign_default(
  thread : thread_act_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3623: thread_get_assignment

Historical query of a thread's processor-set assignment.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [thread_get_assignment](../../../xnu/osfmk/mach/thread_act.defs#L352).

**Declarations:** [`thread_get_assignment`](../../../xnu/osfmk/mach/thread_act.defs#L352) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine thread_get_assignment(
  thread : thread_inspect_t;
 out assigned_set : processor_set_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3624: thread_set_policy

Apply the legacy thread scheduling mode and priority parameters through the current policy implementation.

**Mechanism:** Accepts only the boot compatibility processor set and recognized timeshare/RR/FIFO layouts with exact base/limit counts and valid priorities. It validates the supplied maximum but deliberately passes only policy and base priority to `thread_set_mode_and_absolute_pri`. RR and FIFO both map to fixed scheduling internally; neither the historical max-priority field nor an RR quantum is installed by this wrapper. [thread_set_policy](../../../xnu/osfmk/kern/mk_sp.c#L70-L170). [Mode mapping](../../../xnu/osfmk/kern/thread_policy.c#L631-L648).

**Declarations:** [`thread_set_policy`](../../../xnu/osfmk/mach/thread_act.defs#L360) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_thread_set_policy`](../../../xnu/osfmk/mach/thread_act.defs#L360) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine thread_set_policy(
  thr_act : thread_act_t;
  pset : processor_set_t;
  policy : policy_t;
  base : policy_base_t;
  limit : policy_limit_t);
```

**Local body:** [`thread_set_policy`](../../../xnu/osfmk/kern/mk_sp.c#L70).
Calls visible in this body include `invalid_policy`, `invalid_pri`, `thread_set_mode_and_absolute_pri`.

**User wrapper:** [`thread_set_policy`](../../../xnu/libsyscall/mach/thread_act.c#L65).
Calls visible in this body include `_kernelrpc_thread_set_policy`, `_pthread_clear_qos_tsd`.

[Implementation excerpt](../../../xnu/libsyscall/mach/thread_act.c#L65-L77):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/thread_act.c#L65-L77 -->
```c
thread_set_policy(thread_act_t thr_act, processor_set_t pset, policy_t policy, policy_base_t base, mach_msg_type_number_t baseCnt, policy_limit_t limit, mach_msg_type_number_t limitCnt)
{
	kern_return_t kr;

	kr = _kernelrpc_thread_set_policy(thr_act, pset, policy, base, baseCnt, limit, limitCnt);
	if (kr == KERN_SUCCESS) {
		_pthread_clear_qos_tsd(thr_act);
	} else if (kr == KERN_POLICY_STATIC) {
		kr = KERN_SUCCESS;
	}

	return kr;
}
```

### 3625: thread_get_mach_voucher

Return a referenced voucher associated with the thread.

**Mechanism:** Ignores the selector and reads `ith_voucher` under the thread mutex. If a voucher exists it takes an additional reference before unlocking; otherwise it returns null with success. This is a snapshot reference, so a later voucher replacement does not invalidate the object returned to the caller. No active-thread check is performed in this body. [thread_get_mach_voucher](../../../xnu/osfmk/kern/thread.c#L3422-L3446).

**Declarations:** [`thread_get_mach_voucher`](../../../xnu/osfmk/mach/thread_act.defs#L367) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_get_mach_voucher(
  thr_act : thread_read_t;
  which : mach_voucher_selector_t;
 out voucher : ipc_voucher_t);
```

**Local body:** [`thread_get_mach_voucher`](../../../xnu/osfmk/kern/thread.c#L3422).
Calls visible in this body include `thread_mtx_lock`, `ipc_voucher_reference`, `thread_mtx_unlock`.

### 3626: thread_set_mach_voucher

Adopt a voucher on a thread and update bank-ledger/thread-group/persona attribution as required.

**Mechanism:** Derives bank ledger, thread group and persona metadata before locking. Under the thread mutex it allows only the current thread or one not yet started, references the new voucher, replaces `ith_voucher`, and clears the cached voucher name. After unlocking it updates bank attribution/thread-group state and releases the old voucher. A started remote target fails before replacement. [thread_set_mach_voucher](../../../xnu/osfmk/kern/thread.c#L3460-L3509).

**Declarations:** [`thread_set_mach_voucher`](../../../xnu/osfmk/mach/thread_act.defs#L372) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_set_mach_voucher(
  thr_act : thread_act_t;
  voucher : ipc_voucher_t);
```

**Local body:** [`thread_set_mach_voucher`](../../../xnu/osfmk/kern/thread.c#L3460).
Calls visible in this body include `bank_get_bank_ledger_thread_group_and_persona`, `thread_mtx_lock`, `current_thread`, `thread_mtx_unlock`, `ipc_voucher_reference`, `bank_swap_thread_bank_ledger`, `thread_group_set_bank`, `KERNEL_DEBUG_CONSTANT_IST`, `MACHDBG_CODE`, `thread_tid`, `VM_KERNEL_ADDRPERM`, `ipc_voucher_release`.

### 3627: thread_swap_mach_voucher

Replace the thread voucher while following the input/output voucher reference-transfer contract.

**Mechanism:** The compare/swap operation is no longer supported. It still releases the in/out old-voucher reference to compensate for the generated MIG ownership convention, then returns `KERN_NOT_SUPPORTED`; neither thread state nor the supplied replacement is installed. [thread_swap_mach_voucher](../../../xnu/osfmk/kern/thread.c#L3521-L3534).

**Declarations:** [`thread_swap_mach_voucher`](../../../xnu/osfmk/mach/thread_act.defs#L376) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_swap_mach_voucher(
  thr_act : thread_act_t;
  new_voucher : ipc_voucher_t;
 inout old_voucher : ipc_voucher_t);
```

**Local body:** [`thread_swap_mach_voucher`](../../../xnu/osfmk/kern/thread.c#L3521).
Calls visible in this body include `ipc_voucher_release`, `OS_ANALYZER_SUPPRESS`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread.c#L3521-L3534):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread.c#L3521-L3534 -->
```c
thread_swap_mach_voucher(
	__unused thread_t               thread,
	__unused ipc_voucher_t          new_voucher,
	ipc_voucher_t                   *in_out_old_voucher)
{
	/*
	 * Currently this function is only called from a MIG generated
	 * routine which doesn't release the reference on the voucher
	 * addressed by in_out_old_voucher. To avoid leaking this reference,
	 * a call to release it has been added here.
	 */
	ipc_voucher_release(*in_out_old_voucher);
	OS_ANALYZER_SUPPRESS("81787115") return KERN_NOT_SUPPORTED;
}
```

### 3628: thread_convert_thread_state

Translate state between thread/self representations, validating direction, flavor and architecture-specific conversion.

**Mechanism:** Validates direction and output capacity, then chooses source/destination authentication contexts between the named thread and current thread. It converts input from the source’s user representation to kernel form and then into the destination’s user representation while preserving flags. Only successful conversion with adequate final capacity copies the result out. This transforms a supplied state blob; it does not install registers into either thread. [thread_convert_thread_state](../../../xnu/osfmk/kern/thread_act.c#L1021-L1083).

**Declarations:** [`thread_convert_thread_state`](../../../xnu/osfmk/mach/thread_act.defs#L381) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_convert_thread_state(
  thread : thread_act_t;
  direction : int;
  flavor : thread_state_flavor_t;
  in_state : thread_state_t;
 out out_state : thread_state_t, CountInOut);
```

**Local body:** [`thread_convert_thread_state`](../../../xnu/osfmk/kern/thread_act.c#L1021).
Calls visible in this body include `current_thread`, `machine_thread_state_convert_from_user`, `machine_thread_state_convert_to_user`, `memcpy`.

### 3629: thread_raise_exception

**Interface contract:**

> For userland binary translation to cause specific exceptions

**Mechanism:** The Rosetta implementation requires a thread in the current translated task and rejects EXC_CRASH. It constructs the code pair and delivers through host exception actions using the host lock; failure propagates without resuming. On successful delivery it calls ordinary `thread_resume`, so that final resume can itself fail if no eligible legacy suspension exists. [thread_raise_exception](../../../xnu/osfmk/kern/thread_act.c#L1443-L1480).

**Declarations:** [`thread_raise_exception`](../../../xnu/osfmk/mach/thread_act.defs#L393) (`server64`, `server32`, `local64`).
**Reserved instead in:** `client64`, `client32`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine thread_raise_exception(
    target_act : thread_act_t;
    exception : int;
    code_count : natural_t;
    code : int64_t;
    sub_code : int64_t);
```

**Local body:** [`thread_raise_exception`](../../../xnu/osfmk/kern/thread_act.c#L1443).
Calls visible in this body include `get_threadtask`, `current_task`, `task_is_translated`, `host_priv_self`, `exception_deliver`, `thread_resume`.

### 3630: thread_get_exception_ports_info

Return exception-action metadata after converting the supplied thread-read capability.

**Mechanism:** Uses thread-read conversion without evaluation and selects information-only enumeration. The locked query groups actions as usual but fills hashed port/receiver identities instead of granting handler send rights; invalid ports produce zero identities. It preallocates FP state before locking to keep address hashing from allocating under thread locks, then returns the grouped count and releases the converted thread reference. [thread_get_exception_ports_info](../../../xnu/osfmk/kern/ipc_tt.c#L4492-L4629).

**Declarations:** [`thread_get_exception_ports_info`](../../../xnu/osfmk/mach/thread_act.defs#L406) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_get_exception_ports_info(
  port : mach_port_t;
  exception_mask : exception_mask_t;
 out masks : exception_mask_array_t;
 out old_handlers_info : exception_handler_info_array_t, SameCount;
 out old_behaviors : exception_behavior_array_t, SameCount;
 out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`thread_get_exception_ports_info`](../../../xnu/osfmk/kern/ipc_tt.c#L4607).
Calls visible in this body include `convert_port_to_thread_read_no_eval`, `thread_get_exception_ports_internal`, `thread_deallocate`.

### 3631: thread_adopt_exception_handler

**Interface contract:**

> Calls thread_set_exception_ports on thread using a previously registered hardened exception handler. Only one hardened exception handler is allowed per task.

**Mechanism:** Only a thread of the current task may adopt, and the task’s exception ports must already be frozen. It snapshots the registered hardened action under the task IPC lock, accepts only that handler port or null, and rejects masks not contained in the allowed exception/behavior/flavor masks. The ordinary internal thread updater then installs selected actions with the hardened flag, including its activity/MAC checks and right cleanup. [thread_adopt_exception_handler](../../../xnu/osfmk/kern/ipc_tt.c#L4913-L4961).

**Declarations:** [`thread_adopt_exception_handler`](../../../xnu/osfmk/mach/thread_act.defs#L419) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_adopt_exception_handler(
  thread : thread_t;
  exc_port : mach_port_t;
  exc_mask : exception_mask_t;
  behavior_mask : exception_behavior_t;
  flavor_mask :thread_state_flavor_t);
```

**Local body:** [`thread_adopt_exception_handler`](../../../xnu/osfmk/kern/ipc_tt.c#L4913).
Calls visible in this body include `get_threadtask`, `current_task`, `exception_ports_frozen`, `itk_lock`, `itk_unlock`, `IP_VALID`, `ip_is_exception_port`, `thread_set_exception_ports_internal`.

### 3632: thread_suspend2

**Interface contract:**

> New thread suspend interface that returns a suspend token

**Mechanism:** Preallocates a resume kobject port before locking, places a normal hold, and installs the port if necessary. It makes a send right while holding the thread mutex, so the make-send count serializes against no-senders cleanup. Unused preallocated ports are deallocated; remote targets are waited for after unlocking. The implementation returns a send right shared by normal suspensions, not a unique send-once right per call. [thread_suspend2](../../../xnu/osfmk/kern/thread_act.c#L590-L652).

**Declarations:** [`thread_suspend2`](../../../xnu/osfmk/mach/thread_act.defs#L429) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_suspend2(
  target_act : thread_read_t;
 out suspend_token : mach_port_move_send_t);
```

**Local body:** [`thread_suspend2`](../../../xnu/osfmk/kern/thread_act.c#L590).
Calls visible in this body include `get_threadtask`, `ipc_kobject_alloc_port`, `thread_mtx_lock`, `thread_suspend_internal`, `thread_mtx_unlock`, `ipc_kobject_dealloc_port`, `ipc_kobject_require`, `ipc_kobject_make_send`, `IP_VALID`, `current_thread`, `thread_wait`.

### 3633: thread_resume2

**Interface contract:**

> New thread resume interface that takes a suspend token

**Mechanism:** Looks up the thread-resume kobject while holding the token port’s queue lock and acquires a thread reference before unlocking. Invalid/stale tokens fail. It releases a normal hold under the thread mutex, then drops the temporary thread reference. Port-right consumption is governed by the message declaration/IPC path, not an explicit release of the token port in this body. [thread_resume2](../../../xnu/osfmk/kern/thread_act.c#L655-L683).

**Declarations:** [`thread_resume2`](../../../xnu/osfmk/mach/thread_act.defs#L436) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_resume2(
  suspend_token : mach_port_move_send_t);
```

**Local body:** [`thread_resume2`](../../../xnu/osfmk/kern/thread_act.c#L655).
Calls visible in this body include `IP_VALID`, `ip_mq_lock`, `ipc_kobject_get_locked`, `thread_reference`, `ip_mq_unlock`, `get_threadtask`, `thread_mtx_lock`, `thread_resume_internal`, `thread_mtx_unlock`, `thread_deallocate`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
