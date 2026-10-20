# Mach messages: task

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/task.defs](../../../xnu/osfmk/mach/task.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3400: task_create

Historical task-creation message declaration; the kernel-server profile reserves this slot instead of exposing it.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_create](../../../xnu/osfmk/mach/task.defs#L100).

**Declarations:** [`task_create`](../../../xnu/osfmk/mach/task.defs#L100) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_create(
  target_task : task_t;
  ledgers : ledger_array_t;
  inherit_memory : boolean_t;
 out child_task : task_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3401: task_terminate

**Interface contract:**

> Destroy the target task, causing all of its threads to be destroyed, all of its IPC rights to be deallocated, and all of its address space to be deallocated.

**Mechanism:** The public body rejects a null task and refuses any task with BSD process information, so it is not the ordinary process-exit entry. The accepted Mach-only path serializes task state, holds threads, marks the task inactive and disables task IPC before requesting thread termination. It subsequently destroys owned synchronizers, terminates the IPC space and VM map, and moves the task to the terminated-task list; storage remains reference-counted. [Public admission](../../../xnu/osfmk/kern/task.c#L2445-L2457), [ordered termination](../../../xnu/osfmk/kern/task.c#L2982-L3210).

**Declarations:** [`task_terminate`](../../../xnu/osfmk/mach/task.defs#L112) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_terminate(
  target_task : task_t);
```

**Local body:** [`task_terminate`](../../../xnu/osfmk/kern/task.c#L2445).
Calls visible in this body include `get_bsdtask_info`, `task_terminate_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L2445-L2457):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L2445-L2457 -->
```c
task_terminate(
	task_t          task)
{
	if (task == TASK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	if (get_bsdtask_info(task)) {
		return KERN_FAILURE;
	}

	return task_terminate_internal(task);
}
```

### 3402: task_threads_from_user

**Interface contract:**

> Returns the set of threads belonging to the target task. [Polymorphic] This routine returns thread port with the same flavor as that of the task port passed in.

**Mechanism:** Converts the destination to an inspectable task without the usual conversion evaluation, then uses its actual CONTROL/READ/INSPECT kobject type to choose the corresponding thread-port flavor. The helper retries allocation outside the task lock, references the active task’s threads under that lock, and converts them into ports afterward. Failed resizing drops all collected references; the wrapper always drops its temporary task reference. [task_threads_from_user](../../../xnu/osfmk/kern/task.c#L3852-L3985).

**Declarations:** [`task_threads_from_user`](../../../xnu/osfmk/mach/task.defs#L120) (`server64`, `server32`, `local64`); [`task_threads`](../../../xnu/osfmk/mach/task.defs#L120) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
task_threads_from_user(
  port : mach_port_t;
 out act_list : thread_act_array_t);
```

**Local body:** [`task_threads_from_user`](../../../xnu/osfmk/kern/task.c#L3949).
Calls visible in this body include `convert_port_to_task_inspect_no_eval`, `ip_type`, `task_threads_internal`, `task_deallocate`.

### 3403: _kernelrpc_mach_ports_register3

Store the three inherited task ports used by this kernel interface.

**Mechanism:** Checks all three incoming rights for stashability before taking the task IPC lock. If IPC is inactive it fails without replacing slots. Otherwise it exchanges the complete registered-port array while locked and releases the displaced send rights after unlocking. Success transfers the supplied rights into inheritable task slots; no OOL array allocation occurs in this three-port server form. [_kernelrpc_mach_ports_register3](../../../xnu/osfmk/kern/ipc_tt.c#L2184-L2235).

**Declarations:** [`_kernelrpc_mach_ports_register3`](../../../xnu/osfmk/mach/task.defs#L141) (`server64`, `server32`, `client64`, `client32`, `sender64`, `local64`); [`mach_ports_register`](../../../xnu/osfmk/mach/task.defs#L136) (`libsyscall64`).

**Fields after preprocessing (`server64`):**

```text
routine _kernelrpc_mach_ports_register3(
  target_task : task_t;
  port1 : mach_port_t;
  port2 : mach_port_t;
  port3 : mach_port_t);
```

**Local body:** [`_kernelrpc_mach_ports_register3`](../../../xnu/osfmk/kern/ipc_tt.c#L2184).
Calls visible in this body include `ipc_can_stash_naked_send`, `itk_lock`, `itk_unlock`, `ipc_port_release_send`.

### 3404: _kernelrpc_mach_ports_lookup3

Return the three inherited task ports stored by the kernel interface.

**Mechanism:** Under the task IPC lock, rejects an inactive task and clones each of its three registered send rights into separate outputs. Stored references remain in the task; the caller receives additional rights. This fixed-arity server form avoids the older client API’s apparent variable-length array contract, which is handled outside this body. [_kernelrpc_mach_ports_lookup3](../../../xnu/osfmk/kern/ipc_tt.c#L2251-L2275).

**Declarations:** [`_kernelrpc_mach_ports_lookup3`](../../../xnu/osfmk/mach/task.defs#L157) (`server64`, `server32`, `client64`, `client32`, `sender64`, `local64`); [`mach_ports_lookup`](../../../xnu/osfmk/mach/task.defs#L152) (`libsyscall64`).

**Fields after preprocessing (`server64`):**

```text
routine _kernelrpc_mach_ports_lookup3(
  target_task : task_t;
 out port1 : mach_port_t;
 out port2 : mach_port_t;
 out port3 : mach_port_t);
```

**Local body:** [`_kernelrpc_mach_ports_lookup3`](../../../xnu/osfmk/kern/ipc_tt.c#L2251).
Calls visible in this body include `itk_lock`, `itk_unlock`, `ipc_port_copy_send_any`.

### 3405: task_info_from_user

**Interface contract:**

> Returns information about the target task.

**Mechanism:** Chooses the capability conversion by information flavor: DYLD_INFO requires task-read access, while other flavors use task-name conversion. The common dispatcher locks the task, rejects an inactive foreign task, checks the requested layout count, and collects flavor-specific map, ledger, accounting or policy data. The wrapper drops its converted task reference on every return; passing a null conversion through the dispatcher yields invalid-argument. [task_info_from_user](../../../xnu/osfmk/kern/task.c#L5291-L5330). [Flavor-dependent conversion](../../../xnu/osfmk/kern/task.c#L6417-L6437).

**Declarations:** [`task_info_from_user`](../../../xnu/osfmk/mach/task.defs#L168) (`server64`, `server32`, `local64`); [`task_info`](../../../xnu/osfmk/mach/task.defs#L173) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine task_info_from_user(
                target_task : mach_port_t;
                flavor : task_flavor_t;
        out task_info_out : task_info_t, CountInOut);
```

**Local body:** [`task_info_from_user`](../../../xnu/osfmk/kern/task.c#L6417).
Calls visible in this body include `convert_port_to_task_read`, `convert_port_to_task_name`, `task_info`, `task_deallocate`.

### 3406: task_set_info

**Interface contract:**

> Set task information.

**Mechanism:** After checking that the task is non-null, this dispatcher supports no mutable information flavor. With ATM configured, TASK_TRACE_MEMORY_INFO explicitly returns `KERN_NOT_SUPPORTED`; all other flavors return `KERN_INVALID_ARGUMENT`. It neither copies an arbitrary information block into the task nor changes the data returned by task_info. [task_set_info](../../../xnu/osfmk/kern/task.c#L5251-L5269).

**Declarations:** [`task_set_info`](../../../xnu/osfmk/mach/task.defs#L183) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_info(
  target_task : task_t;
  flavor : task_flavor_t;
  task_info_in : task_info_t);
```

**Local body:** [`task_set_info`](../../../xnu/osfmk/kern/task.c#L5251).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L5251-L5268):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L5251-L5268 -->
```c
task_set_info(
	task_t          task,
	task_flavor_t   flavor,
	__unused task_info_t    task_info_in,           /* pointer to IN array */
	__unused mach_msg_type_number_t task_info_count)
{
	if (task == TASK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}
	switch (flavor) {
#if CONFIG_ATM
	case TASK_TRACE_MEMORY_INFO:
		return KERN_NOT_SUPPORTED;
#endif // CONFIG_ATM
	default:
		return KERN_INVALID_ARGUMENT;
	}
}
```

### 3407: task_suspend

**Interface contract:**

> Increment the suspend count for the target task. No threads within a task may run when the suspend count for that task is non-zero.

**Mechanism:** Places a legacy hold under the task lock, rejecting null/kernel targets and failing for a dead noncorpse task. The first user hold suspends constituent threads and waits for user execution to stop. It then makes a send right to the task resume kobject and copies that hidden token into the caller’s IPC space; abandoning rights enables no-senders cleanup. Copyout errors are reported after the hold was placed. [task_suspend](../../../xnu/osfmk/kern/task.c#L3987-L4071). [Legacy token publication](../../../xnu/osfmk/kern/task.c#L4141-L4197).

**Declarations:** [`task_suspend`](../../../xnu/osfmk/mach/task.defs#L193) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_suspend(
  target_task : task_read_t);
```

**Local body:** [`task_suspend`](../../../xnu/osfmk/kern/task.c#L4141).
Calls visible in this body include `task_lock`, `place_task_hold`, `task_unlock`, `itk_lock`, `ipc_kobject_alloc_port`, `ipc_kobject_make_send`, `itk_unlock`, `IP_VALID`, `ipc_object_copyout`, `current_space`, `printf`, `s`.

### 3408: task_resume

**Interface contract:**

> Decrement the suspend count for the target task, if the count is currently non-zero. If the resulting suspend count is zero, then threads within the task that also have non-zero suspend counts may execute.

**Mechanism:** Releases a legacy hold under the task lock, then searches the caller’s IPC space for the task’s resume-port token. It deallocates one right after a successful release or destroys the found entry when release failed. Missing tokens do not undo an otherwise successful resume; they only trigger an out-of-band warning. Final hold release is what resumes constituent threads. [task_resume](../../../xnu/osfmk/kern/task.c#L4207-L4259).

**Declarations:** [`task_resume`](../../../xnu/osfmk/mach/task.defs#L203) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_resume(
  target_task : task_read_t);
```

**Local body:** [`task_resume`](../../../xnu/osfmk/kern/task.c#L4207).
Calls visible in this body include `current_task`, `task_lock`, `release_task_hold`, `task_unlock`, `itk_lock`, `is_write_lock`, `is_active`, `IP_VALID`, `ipc_hash_lookup`, `ip_to_object`, `itk_unlock`, `ipc_right_dealloc`.

### 3409: task_get_special_port_from_user

**Interface contract:**

> Returns the current value of the selected special port associated with the target task.

**Mechanism:** Converts the incoming task capability to an inspectable object, applies MAC policy, and separately checks requests for a movable self-control port. It preserves the destination’s CONTROL/READ/INSPECT strength when calling the internal selector: read access can obtain read/inspect/name, while inspect permits inspect/name only. The temporary task reference is released regardless of selector or policy failure. [task_get_special_port_from_user](../../../xnu/osfmk/kern/ipc_tt.c#L1887-L1985).

**Declarations:** [`task_get_special_port_from_user`](../../../xnu/osfmk/mach/task.defs#L210) (`server64`, `server32`, `local64`); [`task_get_special_port`](../../../xnu/osfmk/mach/task.defs#L210) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
task_get_special_port_from_user(
  port : mach_port_t;
  which_port : int;
 out special_port : mach_port_t);
```

**Local body:** [`task_get_special_port_from_user`](../../../xnu/osfmk/kern/ipc_tt.c#L1887).
Calls visible in this body include `current_task`, `convert_port_to_task_inspect_no_eval`, `ip_type`, `mac_task_check_get_task_special_port`, `mac_task_check_get_movable_control_port`, `task_is_immovable`, `task_get_special_port_internal`, `task_deallocate`.

### 3410: task_set_special_port_from_user

**Interface contract:**

> Set one of the special ports associated with the target task.

**Mechanism:** Applies MAC policy before the kernel setter’s DriverKit, stashability and CSR checks. The internal operation takes the task IPC lock, requires an existing control-port object, and swaps only supported slots; TASK_ACCESS_PORT cannot be overwritten once valid. Unlike an IPC-active check, the control-port existence check permits spawn-time setup before task IPC publication. Displaced send rights are released after unlocking. [task_set_special_port_from_user](../../../xnu/osfmk/kern/ipc_tt.c#L2004-L2161).

**Declarations:** [`task_set_special_port_from_user`](../../../xnu/osfmk/mach/task.defs#L226) (`server64`, `server32`, `local64`); [`task_set_special_port`](../../../xnu/osfmk/mach/task.defs#L226) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
task_set_special_port_from_user(
  task : task_t;
  which_port : int;
  special_port : mach_port_t);
```

**Local body:** [`task_set_special_port_from_user`](../../../xnu/osfmk/kern/ipc_tt.c#L2004).
Calls visible in this body include `mac_task_check_set_task_special_port`, `current_task`, `task_set_special_port`.

[Implementation excerpt](../../../xnu/osfmk/kern/ipc_tt.c#L2004-L2020):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ipc_tt.c#L2004-L2020 -->
```c
task_set_special_port_from_user(
	task_t          task,
	int             which,
	ipc_port_t      port)
{
	if (task == TASK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

#if CONFIG_MACF
	if (mac_task_check_set_task_special_port(current_task(), task, which, port)) {
		return KERN_DENIED;
	}
#endif

	return task_set_special_port(task, which, port);
}
```

### 3411: thread_create_from_user

**Interface contract:**

> Create a new thread within the target task, returning the port representing the first thr_act in that new thread. The initial execution state of the thread is undefined.

**Mechanism:** Uses the user creation helper, which rejects kernel/null tasks and applies MAC checks to foreign-task creation. The new thread starts with one legacy user stop count and a corresponding hold, plus another hold if its task is suspended. Creation statistics are updated, then task/global thread-list locks are released before the thread reference is returned. The initial continuation is the user bootstrap-return path. [thread_create_from_user](../../../xnu/osfmk/kern/thread.c#L1587-L1648).

**Declarations:** [`thread_create_from_user`](../../../xnu/osfmk/mach/task.defs#L241) (`server64`, `server32`, `local64`); [`thread_create`](../../../xnu/osfmk/mach/task.defs#L241) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_create_from_user(
  parent_task : task_t;
 out child_act : thread_act_t);
```

**Local body:** [`thread_create_from_user`](../../../xnu/osfmk/kern/thread.c#L1642).
Calls visible in this body include `thread_create_with_options_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread.c#L1642-L1649):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread.c#L1642-L1649 -->
```c
thread_create_from_user(
	task_t                          task,
	thread_t                        *new_thread)
{
	/* All thread ports are created immovable by default */
	return thread_create_with_options_internal(task, new_thread, TRUE, TH_OPTION_NONE,
	           (thread_continue_t)thread_bootstrap_return);
}
```

### 3412: thread_create_running_from_user

**Interface contract:**

> Create a new thread within the target task, returning the port representing that new thread. The new thread is not suspended; its initial execution state is given by flavor and new_state. Returns the port representing the new thread.

**Mechanism:** After target/MAC checks, creates a thread with the user bootstrap continuation, preserves any task-wide hold, and translates the supplied user register state before installing it. State conversion or installation failure unlocks the task/global lists, terminates the new thread, and drops its reference. Only successful state setup reaches `thread_start`; creation accounting and output publication follow. [thread_create_running_from_user](../../../xnu/osfmk/kern/thread.c#L1736-L1800).

**Declarations:** [`thread_create_running_from_user`](../../../xnu/osfmk/mach/task.defs#L257) (`server64`, `server32`, `local64`); [`thread_create_running`](../../../xnu/osfmk/mach/task.defs#L257) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
thread_create_running_from_user(
                parent_task : task_t;
                flavor : thread_state_flavor_t;
                new_state : thread_state_t;
        out child_act : thread_act_t);
```

**Local body:** [`thread_create_running_from_user`](../../../xnu/osfmk/kern/thread.c#L1826).
Calls visible in this body include `thread_create_running_internal2`.

[Implementation excerpt](../../../xnu/osfmk/kern/thread.c#L1826-L1836):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread.c#L1826-L1836 -->
```c
thread_create_running_from_user(
	task_t         task,
	int                     flavor,
	thread_state_t          new_state,
	mach_msg_type_number_t  new_state_count,
	thread_t                                *new_thread)
{
	return thread_create_running_internal2(
		task, flavor, new_state, new_state_count,
		new_thread, TRUE);
}
```

### 3413: task_set_exception_ports

**Interface contract:**

> Set an exception handler for a task on one or more exception types. These handlers are invoked for all threads in the task if there are no thread-specific exception handlers or those handlers returned an error.

**Mechanism:** Validates exception semantics and MAC permission, then updates selected action entries under the task IPC lock with copied rights and behavior/flavor/privilege metadata. It requires the control-port object to exist, allowing setup before `ipc_active` during spawn. Per-action label checks can exclude updates. After unlocking it releases displaced rights and consumes the incoming right; invalid validation leaves registrations untouched. [task_set_exception_ports](../../../xnu/osfmk/kern/ipc_tt.c#L4143-L4223).

**Declarations:** [`task_set_exception_ports`](../../../xnu/osfmk/mach/task.defs#L274) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_exception_ports(
  task : task_t;
  exception_mask : exception_mask_t;
  new_port : mach_port_t;
  behavior : exception_behavior_t;
  new_flavor : thread_state_flavor_t);
```

**Local body:** [`task_set_exception_ports`](../../../xnu/osfmk/kern/ipc_tt.c#L4143).
Calls visible in this body include `task_is_privileged`, `current_task`, `set_exception_ports_validation`, `mac_task_check_set_task_exception_ports`, `mac_exc_create_label_for_current_proc`, `itk_lock`, `itk_unlock`, `mac_exc_free_label`, `mac_exc_update_action_label`, `exception_port_copy_send`, `IP_VALID`, `ipc_port_release_send`.

### 3414: task_get_exception_ports_from_user

**Interface contract:**

> Lookup some of the old exception handlers for a task

**Mechanism:** Requires conversion to a task-control object because it returns usable handler send rights. The internal query validates the mask and IPC activity, groups matching action triples under the task IPC lock, and copies one right per returned group up to capacity. Registrations remain unchanged. The wrapper releases its temporary task reference after both success and failure. [task_get_exception_ports_from_user](../../../xnu/osfmk/kern/ipc_tt.c#L4655-L4743). [Control-port wrapper](../../../xnu/osfmk/kern/ipc_tt.c#L4787-L4810).

**Declarations:** [`task_get_exception_ports_from_user`](../../../xnu/osfmk/mach/task.defs#L285) (`server64`, `server32`, `local64`); [`task_get_exception_ports`](../../../xnu/osfmk/mach/task.defs#L285) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
task_get_exception_ports_from_user(
  port : mach_port_t;
  exception_mask : exception_mask_t;
   out masks : exception_mask_array_t;
   out old_handlers : exception_handler_array_t, SameCount;
   out old_behaviors : exception_behavior_array_t, SameCount;
   out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`task_get_exception_ports_from_user`](../../../xnu/osfmk/kern/ipc_tt.c#L4787).
Calls visible in this body include `convert_port_to_task`, `task_get_exception_ports`, `task_deallocate`.

### 3415: task_swap_exception_ports

**Interface contract:**

> Set an exception handler for a thread on one or more exception types. At the same time, return the previously defined exception handlers for those types.

**Mechanism:** Validates the replacement and MAC policy, then requires `ipc_active` under the task IPC lock. For selected actions it groups identical old port/behavior/flavor triples into output masks and installs copies of the new right. The loop stops when output-group capacity is reached, limiting later changes as well as results. Stored old references and the supplied replacement right are released after unlocking. [task_swap_exception_ports](../../../xnu/osfmk/kern/ipc_tt.c#L4366-L4470).

**Declarations:** [`task_swap_exception_ports`](../../../xnu/osfmk/mach/task.defs#L305) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_swap_exception_ports(
  task : task_t;
  exception_mask : exception_mask_t;
  new_port : mach_port_t;
  behavior : exception_behavior_t;
  new_flavor : thread_state_flavor_t;
   out masks : exception_mask_array_t;
   out old_handlers : exception_handler_array_t, SameCount;
   out old_behaviors : exception_behavior_array_t, SameCount;
   out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`task_swap_exception_ports`](../../../xnu/osfmk/kern/ipc_tt.c#L4366).
Calls visible in this body include `task_is_privileged`, `current_task`, `set_exception_ports_validation`, `mac_task_check_set_task_exception_ports`, `mac_exc_create_label_for_current_proc`, `itk_lock`, `itk_unlock`, `mac_exc_free_label`, `mac_exc_update_action_label`, `exception_port_copy_send`, `IP_VALID`, `ipc_port_release_send`.

### 3416: lock_set_create

Historical task-owned lock-set creation declaration.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [lock_set_create](../../../xnu/osfmk/mach/task.defs#L323).

**Declarations:** [`lock_set_create`](../../../xnu/osfmk/mach/task.defs#L323) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine lock_set_create(
  task : task_t;
 out new_lock_set : lock_set_t;
  n_ulocks : int;
  policy : int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3417: lock_set_destroy

Historical lock-set destruction declaration.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [lock_set_destroy](../../../xnu/osfmk/mach/task.defs#L329).

**Declarations:** [`lock_set_destroy`](../../../xnu/osfmk/mach/task.defs#L329) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine lock_set_destroy(
  task : task_t;
  lock_set : lock_set_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3418: semaphore_create

**Interface contract:**

> Create and destroy semaphore synchronizers on a per-task basis (i.e. the task owns them).

**Mechanism:** Validates the task, nonnegative initial value and user policy mask before allocating a zeroed semaphore. Under the task lock it rechecks task activity, initializes a locked wait queue and reference count, and links the semaphore into the owner’s list. A termination race frees the new object and returns `KERN_INVALID_TASK`; success publishes the initialized semaphore after releasing both locks. [semaphore_create](../../../xnu/osfmk/kern/sync_sema.c#L94-L145).

**Declarations:** [`semaphore_create`](../../../xnu/osfmk/mach/task.defs#L339) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_create(
  task : task_t;
 out semaphore : semaphore_t;
  policy : int;
  value : int);
```

**Local body:** [`semaphore_create`](../../../xnu/osfmk/kern/sync_sema.c#L94).
Calls visible in this body include `zalloc_id`, `task_lock`, `task_unlock`, `zfree_id`, `waitq_init`, `os_ref_init_raw`, `enqueue_head`, `semaphore_unlock`.

### 3419: semaphore_destroy

Destroy a task-owned semaphore under task/semaphore lifetime rules.

**Mechanism:** Consumes the supplied semaphore reference even when the task argument is invalid. If the task owns the semaphore, it rechecks ownership under the task lock, unlinks the object, clears its owner/count under the semaphore lock, and wakes waiters with `THREAD_RESTART`. A valid non-owner task does not destroy the semaphore but still returns success after dropping the reference; waiters translate destruction into `KERN_TERMINATED`. [semaphore_destroy](../../../xnu/osfmk/kern/sync_sema.c#L158-L194). [Ownership check and reference consumption](../../../xnu/osfmk/kern/sync_sema.c#L285-L311).

**Declarations:** [`semaphore_destroy`](../../../xnu/osfmk/mach/task.defs#L345) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine semaphore_destroy(
  task : task_t;
  semaphore : semaphore_consume_ref_t);
```

**Local body:** [`semaphore_destroy`](../../../xnu/osfmk/kern/sync_sema.c#L285).
Calls visible in this body include `semaphore_dereference`, `task_lock`, `semaphore_destroy_internal`, `task_unlock`.

### 3420: task_policy_set

**Interface contract:**

> Set/get policy information for a task. (Approved Mac OS X microkernel interface)

**Mechanism:** Dispatches category, latency/throughput QoS and platform-specific suppression policy after validating layout and values. Control/graphics roles require privileged self requests, and embedded systems reject self category changes. Suppression updates requested-policy fields under the task lock, recomputes effective policy, then performs deferred completion outside the lock. A configured suppression-disable switch can return success without applying an active suppression request. [task_policy_set](../../../xnu/osfmk/kern/task_policy.c#L347-L529).

**Declarations:** [`task_policy_set`](../../../xnu/osfmk/mach/task.defs#L354) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_policy_set(
 task : task_policy_set_t;
 flavor : task_policy_flavor_t;
 policy_info : task_policy_t);
```

**Local body:** [`task_policy_set`](../../../xnu/osfmk/kern/task_policy.c#L347).
Calls visible in this body include `current_task`, `proc_set_task_policy`, `task_is_privileged`, `task_qos_policy_validate`, `qos_extract`, `proc_set_task_policy2`, `task_lock`, `KERNEL_DEBUG_CONSTANT_IST`, `IMPORTANCE_CODE`, `proc_selfpid`, `task_pid`, `trequested_0`.

### 3421: task_policy_get

Query the selected task-policy flavor and indicate whether default values were requested/returned.

**Mechanism:** Returns flavor-specific requested policy or defaults, with count checks before writing each layout. Category defaults are unspecified; QoS defaults use unspecified tiers, while actual values are repackaged from policy fields. The detailed TASK_POLICY_STATE flavor requires a privileged caller and locks the task to snapshot requested/effective and importance state. Unsupported flavors fail rather than returning a generic policy record. [task_policy_get](../../../xnu/osfmk/kern/task_policy.c#L575-L690).

**Declarations:** [`task_policy_get`](../../../xnu/osfmk/mach/task.defs#L359) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_policy_get(
 task : task_policy_get_t;
 flavor : task_policy_flavor_t;
out policy_info : task_policy_t, CountInOut;
inout get_default : boolean_t);
```

**Local body:** [`task_policy_get`](../../../xnu/osfmk/kern/task_policy.c#L575).
Calls visible in this body include `proc_get_task_policy`, `proc_get_task_policy2`, `qos_latency_policy_package`, `qos_throughput_policy_package`, `task_is_privileged`, `current_task`, `task_lock`, `task_requested_bitfield`, `task_effective_bitfield`, `IIT_EXTERN`, `task_is_marked_importance_receiver`, `task_is_marked_importance_denap_receiver`.

### 3422: task_sample

Historical sampling registration for a task.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_sample](../../../xnu/osfmk/mach/task.defs#L381).

**Declarations:** [`task_sample`](../../../xnu/osfmk/mach/task.defs#L381) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_sample(
  task : task_t;
  reply : mach_port_make_send_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3423: task_policy

Historical scheduling-policy assignment for a task.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_policy](../../../xnu/osfmk/mach/task.defs#L385).

**Declarations:** [`task_policy`](../../../xnu/osfmk/mach/task.defs#L385) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_policy(
 task : task_t;
 policy : policy_t;
 base : policy_base_t;
 set_limit : boolean_t;
 change : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3424: task_set_emulation

Historical syscall-emulation dispatch entry assignment.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_set_emulation](../../../xnu/osfmk/mach/task.defs#L392).

**Declarations:** [`task_set_emulation`](../../../xnu/osfmk/mach/task.defs#L392) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_set_emulation(
  target_port : task_t;
  routine_entry_pt: vm_address_t;
  routine_number : int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3425: task_get_emulation_vector

Historical retrieval of a task's syscall-emulation vector.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_get_emulation_vector](../../../xnu/osfmk/mach/task.defs#L397).

**Declarations:** [`task_get_emulation_vector`](../../../xnu/osfmk/mach/task.defs#L397) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_get_emulation_vector(
  task : task_t;
 out vector_start : int;
 out emulation_vector: emulation_vector_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3426: task_set_emulation_vector

Historical installation of a task's syscall-emulation vector.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_set_emulation_vector](../../../xnu/osfmk/mach/task.defs#L402).

**Declarations:** [`task_set_emulation_vector`](../../../xnu/osfmk/mach/task.defs#L402) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_set_emulation_vector(
  task : task_t;
  vector_start : int;
  emulation_vector: emulation_vector_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3427: task_set_ras_pc

Historical restartable-atomic-sequence program-counter registration.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_set_ras_pc](../../../xnu/osfmk/mach/task.defs#L408).

**Declarations:** [`task_set_ras_pc`](../../../xnu/osfmk/mach/task.defs#L408) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_set_ras_pc(
  target_task : task_t;
  basepc : vm_address_t;
  boundspc : vm_address_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3428: task_zone_info

Historical per-task zone-information query.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_zone_info](../../../xnu/osfmk/mach/task.defs#L413).

**Declarations:** [`task_zone_info`](../../../xnu/osfmk/mach/task.defs#L413) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_zone_info(
  target_task : task_inspect_t;
 out names : mach_zone_name_array_t,
     Dealloc;
 out info : task_zone_info_array_t,
     Dealloc);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3429: task_assign

Historical assignment of a task to a processor set.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_assign](../../../xnu/osfmk/mach/task.defs#L420).

**Declarations:** [`task_assign`](../../../xnu/osfmk/mach/task.defs#L420) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_assign(
  task : task_t;
  new_set : processor_set_t;
  assign_threads : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3430: task_assign_default

Historical assignment of a task to the default processor set.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_assign_default](../../../xnu/osfmk/mach/task.defs#L425).

**Declarations:** [`task_assign_default`](../../../xnu/osfmk/mach/task.defs#L425) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_assign_default(
  task : task_t;
  assign_threads : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3431: task_get_assignment

Historical query of a task's processor-set assignment.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_get_assignment](../../../xnu/osfmk/mach/task.defs#L429).

**Declarations:** [`task_get_assignment`](../../../xnu/osfmk/mach/task.defs#L429) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_get_assignment(
  task : task_inspect_t;
 out assigned_set : processor_set_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3432: task_set_policy

Historical task scheduling-policy parameter update.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [task_set_policy](../../../xnu/osfmk/mach/task.defs#L433).

**Declarations:** [`task_set_policy`](../../../xnu/osfmk/mach/task.defs#L433) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine task_set_policy(
 task : task_t;
 pset : processor_set_t;
 policy : policy_t;
 base : policy_base_t;
 limit : policy_limit_t;
 change : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3433: task_get_state

**Interface contract:**

> Read the selected state which is to be installed on new threads in the task as they are created.

**Mechanism:** This operates on the task’s default machine state inherited by subsequently created threads, not the live register state of every existing thread. It validates the task, holds its mutex across an activity check and the machine-task get/set callback, then returns that callback’s flavor/count result. An inactive task fails before the architecture callback. [task_get_state](../../../xnu/osfmk/kern/task.c#L7100-L7127).

**Declarations:** [`task_get_state`](../../../xnu/osfmk/mach/task.defs#L446) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_get_state(
  task : task_read_t;
  flavor : thread_state_flavor_t;
 out old_state : thread_state_t, CountInOut);
```

**Local body:** [`task_get_state`](../../../xnu/osfmk/kern/task.c#L7100).
Calls visible in this body include `task_lock`, `task_unlock`, `machine_task_get_state`.

### 3434: task_set_state

**Interface contract:**

> Set the selected state information to be installed on all subsequently created threads in the task.

**Mechanism:** This operates on the task’s default machine state inherited by subsequently created threads, not the live register state of every existing thread. It validates the task, holds its mutex across an activity check and the machine-task get/set callback, then returns that callback’s flavor/count result. An inactive task fails before the architecture callback. [task_set_state](../../../xnu/osfmk/kern/task.c#L7069-L7096).

**Declarations:** [`task_set_state`](../../../xnu/osfmk/mach/task.defs#L455) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_state(
  task : task_t;
  flavor : thread_state_flavor_t;
  new_state : thread_state_t);
```

**Local body:** [`task_set_state`](../../../xnu/osfmk/kern/task.c#L7069).
Calls visible in this body include `task_lock`, `task_unlock`, `machine_task_set_state`.

### 3435: task_set_phys_footprint_limit

**Interface contract:**

> Change the task's physical footprint limit (in MB).

**Mechanism:** With memorystatus enabled, requires footprint-management privilege and preserves the task’s existing active/fatal policy while changing the physical-footprint ledger limit. The helper reports the old limit, treats `-1` as the configured global maximum or infinity, and checks a current task’s new balance after an actual update. CONFIG_NOMONITORS bypasses ordinary new-limit enforcement; without CONFIG_MEMORYSTATUS the RPC is a failure stub. [task_set_phys_footprint_limit](../../../xnu/osfmk/kern/task.c#L7533-L7555). [Ledger updates](../../../xnu/osfmk/kern/task.c#L7600-L7716), [disabled configuration](../../../xnu/osfmk/kern/task.c#L7826-L7832).

**Declarations:** [`task_set_phys_footprint_limit`](../../../xnu/osfmk/mach/task.defs#L463) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_phys_footprint_limit(
  task : task_t;
  new_limit : int;
 out old_limit : int);
```

**Local body:** [`task_set_phys_footprint_limit`](../../../xnu/osfmk/kern/task.c#L7533).
Calls visible in this body include `proc_check_footprint_priv`, `task_get_memlimit_is_active`, `task_get_memlimit_is_fatal`, `task_set_phys_footprint_limit_internal`.

**Local body:** [`task_set_phys_footprint_limit`](../../../xnu/osfmk/kern/task.c#L7826).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L7826-L7832):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L7826-L7832 -->
```c
task_set_phys_footprint_limit(
	__unused task_t task,
	__unused int new_limit_mb,
	__unused int *old_limit_mb)
{
	return KERN_FAILURE;
}
```

### 3436: task_suspend2_mig

Suspend a task using a resumable task-suspension token/capability.

**Mechanism:** Calls the normal task-hold path, then acquires a TASK_GRP_MIG reference and returns the task as a suspension-token object. MIG converts that reference into the token capability. Each successful call represents its own normal hold; a failed suspension clears the output token. It shares task/null/kernel/activity checks and first-hold thread waiting with the common hold machinery. [task_suspend2_mig](../../../xnu/osfmk/kern/task.c#L4266-L4309).

**Declarations:** [`task_suspend2_mig`](../../../xnu/osfmk/mach/task.defs#L468) (`server64`, `server32`, `local64`); [`task_suspend2`](../../../xnu/osfmk/mach/task.defs#L468) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine task_suspend2_mig(
  target_task : task_read_t;
 out suspend_token : task_suspension_token_t);
```

**Local body:** [`task_suspend2_mig`](../../../xnu/osfmk/kern/task.c#L4303).
Calls visible in this body include `task_suspend2_grp`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L4303-L4308):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L4303-L4308 -->
```c
task_suspend2_mig(
	task_t                  task,
	task_suspension_token_t *suspend_token)
{
	return task_suspend2_grp(task, suspend_token, TASK_GRP_MIG);
}
```

### 3437: task_resume2_mig

Consume/use the task-suspension token to release its corresponding suspension.

**Mechanism:** Uses the supplied suspension token to release a normal task hold under the task lock, then unconditionally deallocates the token’s grouped task reference. The cleanup occurs even if resuming fails. Null/kernel targets and missing eligible holds fail through the common resume path; the final successful hold release wakes the task’s threads. [task_resume2_mig](../../../xnu/osfmk/kern/task.c#L4324-L4360).

**Declarations:** [`task_resume2_mig`](../../../xnu/osfmk/mach/task.defs#L472) (`server64`, `server32`, `local64`); [`task_resume2`](../../../xnu/osfmk/mach/task.defs#L472) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine task_resume2_mig(
  suspend_token : task_suspension_token_t);
```

**Local body:** [`task_resume2_mig`](../../../xnu/osfmk/kern/task.c#L4355).
Calls visible in this body include `task_resume2_grp`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L4355-L4359):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L4355-L4359 -->
```c
task_resume2_mig(
	task_suspension_token_t         task)
{
	return task_resume2_grp(task, TASK_GRP_MIG);
}
```

### 3438: task_purgable_info

Snapshot the target task's purgeable-object statistics while retaining the task.

**Mechanism:** Validates both the task and output pointer, takes an additional task reference around `vm_purgeable_stats`, and drops it before returning success. The helper supplies per-task purgeable-object statistics; this operation does not change purgeability or force a purge, despite sharing the purgeable-memory subsystem. [task_purgable_info](../../../xnu/osfmk/kern/task.c#L6917-L6931).

**Declarations:** [`task_purgable_info`](../../../xnu/osfmk/mach/task.defs#L475) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_purgable_info(
  task : task_inspect_t;
 out stats : task_purgable_info_t);
```

**Local body:** [`task_purgable_info`](../../../xnu/osfmk/kern/task.c#L6917).
Calls visible in this body include `task_reference`, `vm_purgeable_stats`, `task_deallocate`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L6917-L6930):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L6917-L6930 -->
```c
task_purgable_info(
	task_t                  task,
	task_purgable_info_t    *stats)
{
	if (task == TASK_NULL || stats == NULL) {
		return KERN_INVALID_ARGUMENT;
	}
	/* Take task reference */
	task_reference(task);
	vm_purgeable_stats((vm_purgeable_info_t)stats, task);
	/* Drop task reference */
	task_deallocate(task);
	return KERN_SUCCESS;
}
```

### 3439: task_get_mach_voucher

The local placeholder validates the task and returns a null voucher; it does not retrieve a task-wide adopted voucher.

**Mechanism:** For a non-null task, always returns a null voucher and success; the selector is unused. A null task returns `KERN_INVALID_TASK`. This compatibility body does not read the task’s bank context or synthesize a default voucher from it. [task_get_mach_voucher](../../../xnu/osfmk/kern/task.c#L8822-L8833).

**Declarations:** [`task_get_mach_voucher`](../../../xnu/osfmk/mach/task.defs#L479) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_get_mach_voucher(
  task : task_read_t;
  which : mach_voucher_selector_t;
 out voucher : ipc_voucher_t);
```

**Local body:** [`task_get_mach_voucher`](../../../xnu/osfmk/kern/task.c#L8822).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L8822-L8833):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L8822-L8833 -->
```c
task_get_mach_voucher(
	task_t                  task,
	mach_voucher_selector_t __unused which,
	ipc_voucher_t           *voucher)
{
	if (TASK_NULL == task) {
		return KERN_INVALID_TASK;
	}

	*voucher = NULL;
	return KERN_SUCCESS;
}
```

### 3440: task_set_mach_voucher

The local placeholder validates the task and succeeds without establishing a task-wide adopted voucher.

**Mechanism:** Only validates that the task is non-null, then returns success while ignoring the supplied voucher. It does not store a voucher, update accounting attribution or alter thread vouchers. The separate thread-level setter contains the actual voucher/bank update mechanism. [task_set_mach_voucher](../../../xnu/osfmk/kern/task.c#L8836-L8845).

**Declarations:** [`task_set_mach_voucher`](../../../xnu/osfmk/mach/task.defs#L484) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_mach_voucher(
  task : task_t;
  voucher : ipc_voucher_t);
```

**Local body:** [`task_set_mach_voucher`](../../../xnu/osfmk/kern/task.c#L8836).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L8836-L8845):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L8836-L8845 -->
```c
task_set_mach_voucher(
	task_t                  task,
	ipc_voucher_t           __unused voucher)
{
	if (TASK_NULL == task) {
		return KERN_INVALID_TASK;
	}

	return KERN_SUCCESS;
}
```

### 3441: task_swap_mach_voucher

The local placeholder consumes the supplied voucher reference as coded; do not infer a functional task-wide voucher swap.

**Mechanism:** Always returns `KERN_NOT_SUPPORTED`, but first releases the voucher reference in the in/out old-voucher argument because the generated MIG path does not release that reference itself. The task and replacement voucher are unused; no compare-and-swap or task state update occurs. [task_swap_mach_voucher](../../../xnu/osfmk/kern/task.c#L8848-L8861).

**Declarations:** [`task_swap_mach_voucher`](../../../xnu/osfmk/mach/task.defs#L488) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_swap_mach_voucher(
  task : task_t;
  new_voucher : ipc_voucher_t;
 inout old_voucher : ipc_voucher_t);
```

**Local body:** [`task_swap_mach_voucher`](../../../xnu/osfmk/kern/task.c#L8848).
Calls visible in this body include `ipc_voucher_release`, `OS_ANALYZER_SUPPRESS`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L8848-L8861):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L8848-L8861 -->
```c
task_swap_mach_voucher(
	__unused task_t         task,
	__unused ipc_voucher_t  new_voucher,
	ipc_voucher_t          *in_out_old_voucher)
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

### 3442: task_generate_corpse

Create a corpse task and preserve inspection data through the task/corpse implementation.

**Mechanism:** Rejects null/kernel targets and an existing corpse fork. It temporarily promotes the caller while the internal generator creates the corpse, then drops the returned thread reference, waits under the new task’s lock for thread termination, and resets eligible thread ports. Finally it transfers the corpse task reference into a control port with no-senders tracking, tying subsequent corpse lifetime to that capability. [task_generate_corpse](../../../xnu/osfmk/corpses/corpse.c#L440-L490).

**Declarations:** [`task_generate_corpse`](../../../xnu/osfmk/mach/task.defs#L493) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_generate_corpse(
  task :task_read_t;
 out corpse_task_port:mach_port_t);
```

**Local body:** [`task_generate_corpse`](../../../xnu/osfmk/corpses/corpse.c#L440).
Calls visible in this body include `task_lock`, `task_is_a_corpse_fork`, `task_unlock`, `thread_set_exec_promotion`, `current_thread`, `task_generate_corpse_internal`, `thread_clear_exec_promotion`, `thread_deallocate`, `task_wait_till_threads_terminate_locked`, `queue_iterate`, `ipc_thread_reset`, `convert_corpse_to_port_and_nsrequest`.

### 3443: task_map_corpse_info

Map corpse diagnostic data into the requesting task using the compatibility-width output.

**Mechanism:** The 64-bit path requires a noncorpse destination and a corpse source with a valid kcdata buffer. It maps the fixed-size corpse-info allocation through `task_map_kcdata_64` and publishes address/size only after mapping succeeds. The older entry invokes that path and narrows successful address and size outputs to its legacy types; it does not create a second mapping implementation. [task_map_corpse_info](../../../xnu/osfmk/corpses/corpse.c#L888-L950). The common mapper allocates in `task->map` but uses ordinary `copyout` and ignores its return value, so allocation success is not proof that copying the buffer succeeded. [Mapper body](../../../xnu/osfmk/corpses/corpse.c#L855-L873).

**Declarations:** [`task_map_corpse_info`](../../../xnu/osfmk/mach/task.defs#L497) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_map_corpse_info(
  task :task_t;
  corspe_task :task_read_t;
 out kcd_addr_begin :vm_address_t;
 out kcd_size :uint32_t);
```

**Local body:** [`task_map_corpse_info`](../../../xnu/osfmk/corpses/corpse.c#L888).
Calls visible in this body include `task_map_corpse_info_64`.

[Implementation excerpt](../../../xnu/osfmk/corpses/corpse.c#L888-L906):
<!-- source-excerpt: ../../../xnu/osfmk/corpses/corpse.c#L888-L906 -->
```c
task_map_corpse_info(
	task_t task,
	task_t corpse_task,
	vm_address_t *kcd_addr_begin,
	uint32_t *kcd_size)
{
	kern_return_t kr;
	mach_vm_address_t kcd_addr_begin_64;
	mach_vm_size_t size_64;

	kr = task_map_corpse_info_64(task, corpse_task, &kcd_addr_begin_64, &size_64);
	if (kr != KERN_SUCCESS) {
		return kr;
	}

	*kcd_addr_begin = (vm_address_t)kcd_addr_begin_64;
	*kcd_size = (uint32_t) size_64;
	return KERN_SUCCESS;
}
```

### 3444: task_register_dyld_image_infos

Record a batch of image-load information through the dyld tracing path.

**Mechanism:** Emits dyld UUID map trace events through `kdebug_trace_dyld`; it does not maintain a queryable kernel image registry. If tracing is disabled, the helper discards the incoming VM copy and succeeds before checking task identity. Otherwise only the current task is accepted, the copy is mapped into the IPC kernel map, each image is traced, and the mapped input is deallocated afterward. [task_register_dyld_image_infos](../../../xnu/osfmk/kern/task.c#L9055-L9109).

**Declarations:** [`task_register_dyld_image_infos`](../../../xnu/osfmk/mach/task.defs#L503) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_register_dyld_image_infos(
        task :task_t;
        dyld_images :dyld_kernel_image_info_array_t);
```

**Local body:** [`task_register_dyld_image_infos`](../../../xnu/osfmk/kern/task.c#L9094).
Calls visible in this body include `kdebug_trace_dyld`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9094-L9100):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9094-L9100 -->
```c
task_register_dyld_image_infos(task_t task,
    dyld_kernel_image_info_array_t infos_copy,
    mach_msg_type_number_t infos_len)
{
	return kdebug_trace_dyld(task, DBG_DYLD_UUID_MAP_A,
	           (vm_map_copy_t)infos_copy, infos_len);
}
```

### 3445: task_unregister_dyld_image_infos

Record a batch of image-unload information through the dyld tracing path.

**Mechanism:** Emits dyld UUID unmap trace events through `kdebug_trace_dyld`; it does not maintain a queryable kernel image registry. If tracing is disabled, the helper discards the incoming VM copy and succeeds before checking task identity. Otherwise only the current task is accepted, the copy is mapped into the IPC kernel map, each image is traced, and the mapped input is deallocated afterward. [task_unregister_dyld_image_infos](../../../xnu/osfmk/kern/task.c#L9055-L9109).

**Declarations:** [`task_unregister_dyld_image_infos`](../../../xnu/osfmk/mach/task.defs#L507) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_unregister_dyld_image_infos(
        task :task_t;
        dyld_images :dyld_kernel_image_info_array_t);
```

**Local body:** [`task_unregister_dyld_image_infos`](../../../xnu/osfmk/kern/task.c#L9103).
Calls visible in this body include `kdebug_trace_dyld`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9103-L9109):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9103-L9109 -->
```c
task_unregister_dyld_image_infos(task_t task,
    dyld_kernel_image_info_array_t infos_copy,
    mach_msg_type_number_t infos_len)
{
	return kdebug_trace_dyld(task, DBG_DYLD_UUID_UNMAP_A,
	           (vm_map_copy_t)infos_copy, infos_len);
}
```

### 3446: task_get_dyld_image_infos

Request dyld image information; check the local implementation's supported/unsupported result.

**Mechanism:** The body ignores its arguments and returns `KERN_NOT_SUPPORTED`. Registration RPCs nearby emit tracing events rather than populating an image list that this operation can retrieve. [task_get_dyld_image_infos](../../../xnu/osfmk/kern/task.c#L9112-L9117).

**Declarations:** [`task_get_dyld_image_infos`](../../../xnu/osfmk/mach/task.defs#L511) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_get_dyld_image_infos(
        task :task_read_t;
    out dyld_images :dyld_kernel_image_info_array_t);
```

**Local body:** [`task_get_dyld_image_infos`](../../../xnu/osfmk/kern/task.c#L9112).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9112-L9117):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9112-L9117 -->
```c
task_get_dyld_image_infos(__unused task_t task,
    __unused dyld_kernel_image_info_array_t * dyld_images,
    __unused mach_msg_type_number_t * dyld_imagesCnt)
{
	return KERN_NOT_SUPPORTED;
}
```

### 3447: task_register_dyld_shared_cache_image_info

Record the current task's shared-cache image information for dyld tracing.

**Mechanism:** Accepts only the current task, then emits one shared-cache UUID trace record. The no-cache and private-cache flags are explicitly unused. Success indicates acceptance by this tracing entry, not registration of a new VM shared region or validation of a cache mapping. [task_register_dyld_shared_cache_image_info](../../../xnu/osfmk/kern/task.c#L9120-L9131).

**Declarations:** [`task_register_dyld_shared_cache_image_info`](../../../xnu/osfmk/mach/task.defs#L515) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_register_dyld_shared_cache_image_info(
        task :task_t;
        dyld_cache_image :dyld_kernel_image_info_t;
        no_cache :boolean_t;
        private_cache :boolean_t);
```

**Local body:** [`task_register_dyld_shared_cache_image_info`](../../../xnu/osfmk/kern/task.c#L9120).
Calls visible in this body include `current_task`, `kdebug_trace_dyld_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9120-L9131):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9120-L9131 -->
```c
task_register_dyld_shared_cache_image_info(task_t task,
    dyld_kernel_image_info_t cache_img,
    __unused boolean_t no_cache,
    __unused boolean_t private_cache)
{
	if (task == NULL || task != current_task()) {
		return KERN_INVALID_TASK;
	}

	kdebug_trace_dyld_internal(DBG_DYLD_UUID_SHARED_CACHE_A, &cache_img);
	return KERN_SUCCESS;
}
```

### 3448: task_register_dyld_set_dyld_state

The local compatibility entry returns KERN_NOT_SUPPORTED rather than recording a dyld state.

**Mechanism:** The local body ignores the declared state arguments and returns `KERN_NOT_SUPPORTED`. It neither stores nor retrieves dyld process state; the retained MIG layout provides compatibility, not an active state service. [task_register_dyld_set_dyld_state](../../../xnu/osfmk/kern/task.c#L9134-L9139).

**Declarations:** [`task_register_dyld_set_dyld_state`](../../../xnu/osfmk/mach/task.defs#L521) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_register_dyld_set_dyld_state(
        task :task_t;
        dyld_state :uint8_t);
```

**Local body:** [`task_register_dyld_set_dyld_state`](../../../xnu/osfmk/kern/task.c#L9134).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9134-L9138):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9134-L9138 -->
```c
task_register_dyld_set_dyld_state(__unused task_t task,
    __unused uint8_t dyld_state)
{
	return KERN_NOT_SUPPORTED;
}
```

### 3449: task_register_dyld_get_process_state

The local compatibility entry returns KERN_NOT_SUPPORTED rather than returning a dyld process state.

**Mechanism:** The local body ignores the declared state arguments and returns `KERN_NOT_SUPPORTED`. It neither stores nor retrieves dyld process state; the retained MIG layout provides compatibility, not an active state service. [task_register_dyld_get_process_state](../../../xnu/osfmk/kern/task.c#L9141-L9146).

**Declarations:** [`task_register_dyld_get_process_state`](../../../xnu/osfmk/mach/task.defs#L525) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_register_dyld_get_process_state(
        task :task_t;
    out dyld_process_state :dyld_kernel_process_info_t);
```

**Local body:** [`task_register_dyld_get_process_state`](../../../xnu/osfmk/kern/task.c#L9141).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9141-L9145):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9141-L9145 -->
```c
task_register_dyld_get_process_state(__unused task_t task,
    __unused dyld_kernel_process_info_t * dyld_process_state)
{
	return KERN_NOT_SUPPORTED;
}
```

### 3450: task_map_corpse_info_64

Map the corpse's kcdata diagnostic buffer into the requesting task using wide output addresses.

**Mechanism:** The 64-bit path requires a noncorpse destination and a corpse source with a valid kcdata buffer. It maps the fixed-size corpse-info allocation through `task_map_kcdata_64` and publishes address/size only after mapping succeeds. The older entry invokes that path and narrows successful address and size outputs to its legacy types; it does not create a second mapping implementation. [task_map_corpse_info_64](../../../xnu/osfmk/corpses/corpse.c#L888-L950). The common mapper allocates in `task->map` but uses ordinary `copyout` and ignores its return value, so allocation success is not proof that copying the buffer succeeded. [Mapper body](../../../xnu/osfmk/corpses/corpse.c#L855-L873).

**Declarations:** [`task_map_corpse_info_64`](../../../xnu/osfmk/mach/task.defs#L529) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_map_corpse_info_64(
  task :task_t;
  corspe_task :task_read_t;
 out kcd_addr_begin :mach_vm_address_t;
 out kcd_size :mach_vm_size_t);
```

**Local body:** [`task_map_corpse_info_64`](../../../xnu/osfmk/corpses/corpse.c#L919).
Calls visible in this body include `task_is_a_corpse`, `kcdata_memory_get_begin_addr`, `task_map_kcdata_64`.

### 3451: task_inspect

Return the selected task-inspection information, including configured accounting/performance data.

**Mechanism:** When pervasive CPI accounting is enabled, accepts BASIC_COUNTS with a sufficiently large output and sums the task’s lifetime recount usage into instruction and cycle totals. It writes the resulting count only on success; unknown flavors fail. Without CONFIG_PERVASIVE_CPI the entire implementation returns `KERN_NOT_SUPPORTED`, independently of the declared inspection capability. [task_inspect](../../../xnu/osfmk/kern/task.c#L9148-L9194).

**Declarations:** [`task_inspect`](../../../xnu/osfmk/mach/task.defs#L535) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_inspect(
     task : task_inspect_t;
     flavor : task_inspect_flavor_t;
 out info_out : task_inspect_info_t, CountInOut);
```

**Local body:** [`task_inspect`](../../../xnu/osfmk/kern/task.c#L9148).
Calls visible in this body include `recount_sum`, `recount_usage_instructions`, `recount_usage_cycles`, `unused`.

### 3452: task_get_exc_guard_behavior

Read the task's exception-guard behavior flags.

**Mechanism:** Rejects a null task, otherwise returns its current `task_exc_guard` flags directly. The getter performs no mutation or policy relaxation and does not promise a mutex-protected multi-field snapshot; it reads this one behavior field. [task_get_exc_guard_behavior](../../../xnu/osfmk/kern/task.c#L9464-L9473).

**Declarations:** [`task_get_exc_guard_behavior`](../../../xnu/osfmk/mach/task.defs#L540) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_get_exc_guard_behavior(
  task : task_inspect_t;
 out behavior : task_exc_guard_behavior_t);
```

**Local body:** [`task_get_exc_guard_behavior`](../../../xnu/osfmk/kern/task.c#L9464).

[Implementation excerpt](../../../xnu/osfmk/kern/task.c#L9464-L9473):
<!-- source-excerpt: ../../../xnu/osfmk/kern/task.c#L9464-L9473 -->
```c
task_get_exc_guard_behavior(
	task_t task,
	task_exc_guard_behavior_t *behaviorp)
{
	if (task == TASK_NULL) {
		return KERN_INVALID_TASK;
	}
	*behaviorp = task->task_exc_guard;
	return KERN_SUCCESS;
}
```

### 3453: task_set_exc_guard_behavior

Update the task's exception-guard behavior with the local atomic policy checks.

**Mechanism:** Rejects unknown flags, masks requested behavior to the configuration’s supported set, and updates the guard field. Release builds use an atomic compare/update loop that forbids changes covered by the no-unset/no-set masks while allowing corpse-bit changes; DEBUG/DEVELOPMENT builds assign the masked value directly. A disallowed downgrade/upgrade returns `KERN_DENIED` without installing that attempted value. [task_set_exc_guard_behavior](../../../xnu/osfmk/kern/task.c#L9476-L9509).

**Declarations:** [`task_set_exc_guard_behavior`](../../../xnu/osfmk/mach/task.defs#L544) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_exc_guard_behavior(
  task : task_t;
  behavior : task_exc_guard_behavior_t);
```

**Local body:** [`task_set_exc_guard_behavior`](../../../xnu/osfmk/kern/task.c#L9476).
Calls visible in this body include `os_atomic_rmw_loop`, `os_atomic_rmw_loop_give_up`.

### 3454: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/task.defs#L548).

### 3455: mach_task_is_self

Test whether the converted target task is the current task.

**Mechanism:** After rejecting a null converted task, compares object identity with `current_task()` and writes the boolean result. It does not compare PID values, task-port names or right counts; different capability flavors resolving to the same task therefore identify the same self task. [mach_task_is_self](../../../xnu/osfmk/kern/ipc_tt.c#L1210-L1221).

**Declarations:** [`mach_task_is_self`](../../../xnu/osfmk/mach/task.defs#L551) (`server64`, `server32`, `sender64`, `local64`); [`_kernelrpc_mach_task_is_self`](../../../xnu/osfmk/mach/task.defs#L551) (`client64`, `client32`).
**Reserved instead in:** `libsyscall64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_task_is_self(
  task : task_name_t;
 out is_self : boolean_t);
```

**Local body:** [`mach_task_is_self`](../../../xnu/osfmk/kern/ipc_tt.c#L1210).
Calls visible in this body include `current_task`.

[Implementation excerpt](../../../xnu/osfmk/kern/ipc_tt.c#L1210-L1221):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ipc_tt.c#L1210-L1221 -->
```c
mach_task_is_self(
	task_t         task,
	boolean_t     *is_self)
{
	if (task == TASK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	*is_self = (task == current_task());

	return KERN_SUCCESS;
}
```

**User wrapper:** [`mach_task_is_self`](../../../xnu/libsyscall/mach/task.c#L44).
Calls visible in this body include `_kernelrpc_mach_task_is_self`.

[Implementation excerpt](../../../xnu/libsyscall/mach/task.c#L44-L56):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/task.c#L44-L56 -->
```c
mach_task_is_self(task_name_t task)
{
	boolean_t is_self;
	kern_return_t kr;

	if (task == mach_task_self_) {
		return TRUE;
	}

	kr = _kernelrpc_mach_task_is_self(task, &is_self);

	return kr == KERN_SUCCESS && is_self;
}
```

### 3456: task_dyld_process_info_notify_register

Register a dyld process-info notification destination with task/port policy and ownership checks.

**Mechanism:** Validates a stashable live send right and MAC policy, obtains the target’s dyld info address, then serializes notifier-array changes with the global dyld mutex and task IPC lock. It clears dead entries, rejects duplicates, and inserts into a free slot or returns no-space. The helper updates userspace’s notification magic with copyout errors ignored and releases removed rights after unlocking; success consumes the new right. [task_dyld_process_info_notify_register](../../../xnu/osfmk/kern/task.c#L6512-L6626).

**Declarations:** [`task_dyld_process_info_notify_register`](../../../xnu/osfmk/mach/task.defs#L559) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_dyld_process_info_notify_register(
  target_task : task_read_t;
  notify : mach_port_make_send_t);
```

**Local body:** [`task_dyld_process_info_notify_register`](../../../xnu/osfmk/kern/task.c#L6512).
Calls visible in this body include `ipc_can_stash_naked_send`, `IP_VALID`, `mac_task_check_dyld_process_info_notify_register`, `task_info`, `offsetof`, `kalloc_type`, `lck_mtx_lock`, `itk_lock`, `itk_unlock`, `lck_mtx_unlock`, `ip_active`, `task_dyld_process_info_update_helper`.

### 3457: task_create_identity_token

Create a task-identity token that can later be converted under flavor/policy constraints.

**Mechanism:** Allocates a token, then validates the target under its task lock. A corpse is identified by task unique ID; a live BSD task uses an exact-process identity, while inactive or non-BSD ordinary tasks fail and free the allocation. The initialized token reference is intended for no-senders ownership, avoiding a permanently retained ordinary task reference merely to represent identity. [task_create_identity_token](../../../xnu/osfmk/kern/task_ident.c#L127-L162).

**Declarations:** [`task_create_identity_token`](../../../xnu/osfmk/mach/task.defs#L563) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_create_identity_token(
     task : task_t;
 out token : task_id_token_t);
```

**Local body:** [`task_create_identity_token`](../../../xnu/osfmk/kern/task_ident.c#L127).
Calls visible in this body include `zalloc_flags`, `task_lock`, `get_bsdtask_info`, `task_is_a_corpse`, `proc_ident_with_policy`, `task_unlock`, `zfree`, `os_ref_init_count`.

### 3458: task_identity_token_get_task_port

Resolve a task-identity token and return a permitted task-port flavor after conversion and policy checks.

**Mechanism:** Resolves the recorded exact process/corpse identity to a referenced task, so exit or identity mismatch can produce not-found. Corpses only support CONTROL conversion. Self CONTROL takes a fast path; other strong flavors undergo task-conversion policy, and foreign tasks also undergo MAC checks. Successful flavor conversion consumes the task reference; denial releases it without publishing a capability. [task_identity_token_get_task_port](../../../xnu/osfmk/kern/task_ident.c#L165-L264).

**Declarations:** [`task_identity_token_get_task_port`](../../../xnu/osfmk/mach/task.defs#L567) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_identity_token_get_task_port(
     token : task_id_token_t;
  flavor : task_flavor_t;
 out task_port: mach_port_t);
```

**Local body:** [`task_identity_token_get_task_port`](../../../xnu/osfmk/kern/task_ident.c#L202).
Calls visible in this body include `task_identity_token_get_task_grp`, `current_task`, `convert_task_to_port`, `task_conversion_eval`, `task_deallocate`, `mac_task_check_task_id_token_get_task`, `convert_task_to_port_with_flavor`.

### 3459: task_dyld_process_info_notify_deregister

Remove a dyld process-info notification registration with receive-right and task policy validation.

**Mechanism:** Resolves a receive-right name in the caller’s space and temporarily references that port. Under the dyld global/task IPC locks it removes matching notifier rights and stale dead entries, then frees an empty array or refreshes the userspace magic through the shared helper. Removed send rights and the temporary port reference are released; absence of the requested registration returns failure. [task_dyld_process_info_notify_deregister](../../../xnu/osfmk/kern/task.c#L6651-L6735).

**Declarations:** [`task_dyld_process_info_notify_deregister`](../../../xnu/osfmk/mach/task.defs#L572) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_dyld_process_info_notify_deregister(
  target_task : task_read_t;
  notify : mach_port_name_t);
```

**Local body:** [`task_dyld_process_info_notify_deregister`](../../../xnu/osfmk/kern/task.c#L6651).
Calls visible in this body include `MACH_PORT_VALID`, `mac_task_check_dyld_process_info_notify_register`, `task_info`, `offsetof`, `ipc_port_translate_receive`, `current_space`, `ip_reference`, `ip_mq_unlock`, `lck_mtx_lock`, `itk_lock`, `itk_unlock`, `lck_mtx_unlock`.

### 3460: task_get_exception_ports_info

Return exception-action metadata using the permitted task-read conversion.

**Mechanism:** Uses task-read conversion without evaluation and calls the same locked action enumerator in information-only mode. Instead of send rights, it returns hashed port and receiver-object identities, with zeros for invalid ports; matching actions are still merged into masks. This exposes handler metadata without granting the capability to message the handlers. The temporary task reference is released afterward. [task_get_exception_ports_info](../../../xnu/osfmk/kern/ipc_tt.c#L4655-L4784).

**Declarations:** [`task_get_exception_ports_info`](../../../xnu/osfmk/mach/task.defs#L576) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_get_exception_ports_info(
  port : mach_port_t;
  exception_mask : exception_mask_t;
 out masks : exception_mask_array_t;
 out old_handlers_info : exception_handler_info_array_t, SameCount;
 out old_behaviors : exception_behavior_array_t, SameCount;
 out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`task_get_exception_ports_info`](../../../xnu/osfmk/kern/ipc_tt.c#L4762).
Calls visible in this body include `convert_port_to_task_read_no_eval`, `task_get_exception_ports_internal`, `task_deallocate`.

### 3461: task_test_sync_upcall

Invoke the supplied synchronous test upcall port from the configured kernel test path.

**Mechanism:** Only DEBUG/DEVELOPMENT builds implement this test hook. It requires the current task and a valid send port, performs the synchronous kernel upcall, then releases the supplied send right and returns success. Other builds return `KERN_NOT_SUPPORTED`; the test path is not a general arbitrary-target task callback facility. [task_test_sync_upcall](../../../xnu/osfmk/kern/task.c#L10224-L10242).

**Declarations:** [`task_test_sync_upcall`](../../../xnu/osfmk/mach/task.defs#L584) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_test_sync_upcall(
 task : task_t;
 port : mach_port_t);
```

**Local body:** [`task_test_sync_upcall`](../../../xnu/osfmk/kern/task.c#L10224).
Calls visible in this body include `current_task`, `IPC_PORT_VALID`, `mach_test_sync_upcall`, `ipc_port_release_send`, `else`.

### 3462: task_set_corpse_forking_behavior

Set the configured corpse-forking behavior under the task lock.

**Mechanism:** In DEBUG/DEVELOPMENT builds, validates the task and updates TF_NO_CORPSE_FORKING under its lock according to the diagnostic-disable bit. Other bits are not separately rejected by this body. Production builds ignore the arguments and return `KERN_NOT_SUPPORTED`; this is not a universal control over production corpse generation. [task_set_corpse_forking_behavior](../../../xnu/osfmk/kern/task.c#L9512-L9534).

**Declarations:** [`task_set_corpse_forking_behavior`](../../../xnu/osfmk/mach/task.defs#L588) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_corpse_forking_behavior(
  task : task_t;
  behavior : task_corpse_forking_behavior_t);
```

**Local body:** [`task_set_corpse_forking_behavior`](../../../xnu/osfmk/kern/task.c#L9512).
Calls visible in this body include `task_lock`, `task_unlock`, `else`.

### 3463: task_test_async_upcall_propagation

Issue a test asynchronous upcall with thread-attribute/importance propagation.

**Mechanism:** The development/debug hook validates self task, send port, QoS and IO-tier bounds before propagating attributes to the port. Attribute-propagation failure returns before the upcall. Success temporarily enables send importance for the current thread, makes the async upcall, disables importance again, and consumes the send right. Release builds return not-supported. [task_test_async_upcall_propagation](../../../xnu/osfmk/kern/task.c#L10246-L10287).

**Declarations:** [`task_test_async_upcall_propagation`](../../../xnu/osfmk/mach/task.defs#L592) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_test_async_upcall_propagation(
 task : task_t;
 port : mach_port_t;
 qos : int;
 iotier : int);
```

**Local body:** [`task_test_async_upcall_propagation`](../../../xnu/osfmk/kern/task.c#L10246).
Calls visible in this body include `current_task`, `IPC_PORT_VALID`, `ipc_port_propagate_thread_attr`, `thread_enable_send_importance`, `current_thread`, `mach_test_async_upcall`, `ipc_port_release_send`, `else`.

### 3464: task_map_kcdata_object_64

Map the selected kcdata object into the requesting task using wide addresses.

**Mechanism:** Requires a noncorpse destination task and a valid kcdata object with a backing buffer. It maps the fixed backtrace-info allocation into the target through the common kcdata mapper using the BTINFO memory tag. Output address and size are written only after success; an absent buffer or invalid object fails without publishing a mapping result. [task_map_kcdata_object_64](../../../xnu/osfmk/corpses/corpse.c#L962-L993). The common mapper allocates in `task->map` but uses ordinary `copyout` and ignores its return value, so allocation success is not proof that copying the buffer succeeded. [Mapper body](../../../xnu/osfmk/corpses/corpse.c#L855-L873).

**Declarations:** [`task_map_kcdata_object_64`](../../../xnu/osfmk/mach/task.defs#L598) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_map_kcdata_object_64(
  task :task_t;
  kcdata_object :kcdata_object_t;
 out kcd_addr_begin :mach_vm_address_t;
 out kcd_size :mach_vm_size_t);
```

**Local body:** [`task_map_kcdata_object_64`](../../../xnu/osfmk/corpses/corpse.c#L962).
Calls visible in this body include `task_is_a_corpse`, `kcdata_memory_get_begin_addr`, `task_map_kcdata_64`.

### 3465: task_register_hardened_exception_handler

**Interface contract:**

> When used in conjunction with thread_adopt_exception_handler, we call this a hardened mach exception handler, and it adds additional security guarantees to this exception port: 1. Enforces only a subset of exceptions, behaviours, and flavors may be used with this port 2. The `new_exception_port` must be created using MPO_EXCEPTION_PORT (implicitly immovable) 3. When using *STATE* behaviors of exception handling, only the PC is allowed to be set. 4. Setting the PC in an exception handler must be signed using a diversifier of signed_pc_key (if non-zero). You can pre-sign your PC state and then throw away the key to ensure that only a limited set of PC's may be used with this exception handler 5. Calling `[task,thread,host]_set_exception_ports` if you have the IPC_ONLY_ONE_EXCEPTION_PORT entitlement is disallowed, and you must use this hardened exception flow. If used with the traditional set_exception_ports functions, these security guarantees do not apply. You can only call this once per task. See tests/ipc/hardened_exceptions.c for examples.

**Mechanism:** Requires an exception-compatible port and validates the allowed exception/behavior/flavor combination through the hardened path. It refuses an already-frozen task, sets the freeze flag, then takes the IPC lock and rejects a preexisting valid hardened handler. Success donates the incoming right into the task’s hardened action along with the signed-PC key and allowed masks; ordinary per-exception action arrays are not installed here. [task_register_hardened_exception_handler](../../../xnu/osfmk/kern/ipc_tt.c#L4842-L4898).

**Declarations:** [`task_register_hardened_exception_handler`](../../../xnu/osfmk/mach/task.defs#L623) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_register_hardened_exception_handler(
   task : task_t;
   signed_pc_key : uint32_t;
   exceptions_allowed : exception_mask_t;
   behaviors_allowed : exception_behavior_t;
   flavors_allowed : thread_state_flavor_t;
   new_exception_port : mach_port_t);
```

**Local body:** [`task_register_hardened_exception_handler`](../../../xnu/osfmk/kern/ipc_tt.c#L4842).
Calls visible in this body include `IP_VALID`, `ip_is_exception_port`, `set_exception_ports_validation`, `exception_ports_frozen`, `task_ro_flags_set`, `itk_lock`, `itk_unlock`.
