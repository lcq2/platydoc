# Mach messages: host_priv

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/host_priv.defs](../../../xnu/osfmk/mach/host_priv.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 400: host_get_boot_info

**Interface contract:**

> Get boot configuration information from kernel.

**Mechanism:** Requires a privileged-host object, then asks the machine boot-info helper to fill or return a string. If the helper returned a different buffer, the wrapper copies it into the bounded output array. The machine backend determines the actual boot-information contents; this is not a direct export of all firmware or device-tree state. [host_get_boot_info](../../../xnu/osfmk/kern/machine.c#L587-L607).

**Declarations:** [`host_get_boot_info`](../../../xnu/osfmk/mach/host_priv.defs#L94) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_get_boot_info(
  host_priv : host_priv_t;
 out boot_info : kernel_boot_info_t);
```

**Local body:** [`host_get_boot_info`](../../../xnu/osfmk/kern/machine.c#L587).
Calls visible in this body include `machine_boot_info`, `strncpy`.

### 401: host_reboot

**Interface contract:**

> Reboot this host. Only available to privileged users.

**Mechanism:** Rejects a null privileged host. Development/debug builds honor the debugger option by entering `Debugger` and returning. The UPS-delay option calls the platform halt/restart hook; other requests call `halt_all_cpus`, with the HALT bit selecting halt versus restart. The RPC is therefore a thin privileged entry into machine/platform shutdown, not a BSD filesystem-sync transaction. [host_reboot](../../../xnu/osfmk/kern/machine.c#L198-L221).

**Declarations:** [`host_reboot`](../../../xnu/osfmk/mach/host_priv.defs#L102) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_reboot(
  host_priv : host_priv_t;
  options : int);
```

**Local body:** [`host_reboot`](../../../xnu/osfmk/kern/machine.c#L198).
Calls visible in this body include `Debugger`, `PEHaltRestart`, `halt_all_cpus`.

### 402: host_priv_statistics

**Interface contract:**

> Return privileged statistics from this host.

**Mechanism:** Forwards directly to `host_statistics` with the privileged-host object cast to a host. The body adds no privileged statistics flavor and bypasses the separate user statistics wrapper’s rate-limiter/cache path; flavor validation and output sizing belong to the ordinary dispatcher. [host_priv_statistics](../../../xnu/osfmk/kern/host.c#L1119-L1122).

**Declarations:** [`host_priv_statistics`](../../../xnu/osfmk/mach/host_priv.defs#L110) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_priv_statistics(
  host_priv : host_priv_t;
  flavor : host_flavor_t;
 out host_info_out : host_info_t, CountInOut);
```

**Local body:** [`host_priv_statistics`](../../../xnu/osfmk/kern/host.c#L1119).
Calls visible in this body include `host_statistics`.

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1119-L1122):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1119-L1122 -->
```c
host_priv_statistics(host_priv_t host_priv, host_flavor_t flavor, host_info_t info, mach_msg_type_number_t * count)
{
	return host_statistics((host_t)host_priv, flavor, info, count);
}
```

### 403: host_default_memory_manager

**Interface contract:**

> Sets the default memory manager, the port to which newly-created temporary memory objects are delivered. [See (memory_object_default)memory_object_create.] Also sets the default cluster size used for pagein/pageout to this port. The old memory manager port is returned.

**Mechanism:** Serializes access with `memory_manager_default_lock`. A null incoming manager queries the current manager by making a send right. Replacement is restricted to the kernel task even with a privileged host, starts internal pager support for the first manager, and on success returns the old reference while making a send right for the new stored manager. Startup errors leave the stored manager unchanged. [host_default_memory_manager](../../../xnu/osfmk/vm/memory_object.c#L1413-L1485).

**Declarations:** [`host_default_memory_manager`](../../../xnu/osfmk/mach/host_priv.defs#L123) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_default_memory_manager(
  host_priv : host_priv_t;
 inout default_manager : memory_object_default_t =
     MACH_MSG_TYPE_MAKE_SEND;
  cluster_size : memory_object_cluster_size_t);
```

**Local body:** [`host_default_memory_manager`](../../../xnu/osfmk/vm/memory_object.c#L1413).
Calls visible in this body include `lck_mtx_lock`, `ipc_port_make_send_mqueue`, `current_task`, `vm_pageout_internal_start`, `thread_wakeup`, `vm_page_reactivate_all_throttled`, `lck_mtx_unlock`.

### 404: vm_wire

**Interface contract:**

> Specify that the range of the virtual address space of the target task must not cause page faults for the indicated accesses. [ To unwire the pages, specify VM_PROT_NONE. ]

**Mechanism:** The common implementation requires a privileged host and target map, computes the unsafe end address for the sanitizing map helpers, and interprets zero protection as unwire. Nonzero protection requests user-accounted wiring with the MLOCK tag; zero requests user unwiring. Validation, range walking and partial-work cleanup belong to `vm_map_wire_impl`/`vm_map_unwire_impl`; the older-sized entry simply forwards. [vm_wire](../../../xnu/osfmk/vm/vm_user.c#L1127-L1175).

**Declarations:** [`vm_wire`](../../../xnu/osfmk/mach/host_priv.defs#L137) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_wire(
  host_priv : host_priv_t;
  task : vm_map_t;
  address : vm_address_t;
  size : vm_size_t;
  desired_access : vm_prot_t);
```

**Local body:** [`vm_wire`](../../../xnu/osfmk/vm/vm_user.c#L1166).
Calls visible in this body include `mach_vm_wire_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1166-L1174):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1166-L1174 -->
```c
vm_wire(
	host_priv_t             host_priv,
	vm_map_t                map,
	vm_offset_ut            start,
	vm_size_ut              size,
	vm_prot_ut              access)
{
	return mach_vm_wire_external(host_priv, map, start, size, access);
}
```

### 405: thread_wire

**Interface contract:**

> Specify that the target thread must always be able to run and to allocate memory.

**Mechanism:** The current body ignores every argument and returns `KERN_NOT_SUPPORTED`. It does not set the thread’s VM-privilege option; the separately implemented kernel privilege helpers nearby are not the behavior of this MIG operation. [thread_wire](../../../xnu/osfmk/kern/thread.c#L2310-L2316).

**Declarations:** [`thread_wire`](../../../xnu/osfmk/mach/host_priv.defs#L148) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine thread_wire(
  host_priv : host_priv_t;
  thread : thread_act_t;
  wired : boolean_t);
```

**Local body:** [`thread_wire`](../../../xnu/osfmk/kern/thread.c#L2310).

[Implementation excerpt](../../../xnu/osfmk/kern/thread.c#L2310-L2316):
<!-- source-excerpt: ../../../xnu/osfmk/kern/thread.c#L2310-L2316 -->
```c
thread_wire(
	host_priv_t     host_priv __unused,
	thread_t        thread __unused,
	boolean_t       wired __unused)
{
	return KERN_NOT_SUPPORTED;
}
```

### 406: vm_allocate_cpm

Request physically contiguous memory through the historical privileged-host interface.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [vm_allocate_cpm](../../../xnu/osfmk/mach/host_priv.defs#L159).

**Declarations:** [`vm_allocate_cpm`](../../../xnu/osfmk/mach/host_priv.defs#L159) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine vm_allocate_cpm(
  host_priv : host_priv_t;
  task : vm_map_t;
 inout address : vm_address_t;
  size : vm_size_t;
  flags : int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 407: host_processors

**Interface contract:**

> Get list of processors on this host.

**Mechanism:** Requires a privileged-host object and allocates an array sized to the global processor count. Each `processor_array` object is converted to a processor send right before the array is published. Allocation failure returns resource-shortage; this enumerates registered processor objects, rather than filtering to currently running CPUs. [host_processors](../../../xnu/osfmk/kern/host.c#L171-L199).

**Declarations:** [`host_processors`](../../../xnu/osfmk/mach/host_priv.defs#L170) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_processors(
  host_priv : host_priv_t;
 out out_processor_list : processor_array_t);
```

**Local body:** [`host_processors`](../../../xnu/osfmk/kern/host.c#L171).
Calls visible in this body include `static_assert`, `mach_port_array_alloc`, `convert_processor_to_port`.

### 408: host_get_clock_control

Request a control capability for the selected clock.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_get_clock_control](../../../xnu/osfmk/mach/host_priv.defs#L184).

**Declarations:** [`host_get_clock_control`](../../../xnu/osfmk/mach/host_priv.defs#L184) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine host_get_clock_control(
  host_priv : host_priv_t;
  clock_id : clock_id_t;
 out clock_ctrl : clock_ctrl_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 409: kmod_create

Historical module-creation interface; inspect the local implementation status before assuming modern kext loading uses it.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [kmod_create](../../../xnu/osfmk/mach/host_priv.defs#L189).

**Declarations:** [`kmod_create`](../../../xnu/osfmk/mach/host_priv.defs#L189) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine kmod_create(
  host_priv : host_priv_t;
  info : vm_address_t;
 out module : kmod_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 410: kmod_destroy

Historical module-destruction interface.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [kmod_destroy](../../../xnu/osfmk/mach/host_priv.defs#L194).

**Declarations:** [`kmod_destroy`](../../../xnu/osfmk/mach/host_priv.defs#L194) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine kmod_destroy(
  host_priv : host_priv_t;
  module : kmod_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 411: kmod_control

Historical module-control interface.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [kmod_control](../../../xnu/osfmk/mach/host_priv.defs#L198).

**Declarations:** [`kmod_control`](../../../xnu/osfmk/mach/host_priv.defs#L198) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine kmod_control(
  host_priv : host_priv_t;
  module : kmod_t;
  flavor : kmod_control_flavor_t;
 inout data : kmod_args_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 412: host_get_special_port_from_user

**Interface contract:**

> Get a given special port for a given node. Special ports are defined in host_special_ports.h; examples include the master device port. There are a limited number of slots available for system servers.

**Mechanism:** Rejects invalid IDs and the security port. Driver tasks cannot obtain user-owned special ports except the entitled HID sysdiagnose exception. Under the host lock, the helper clones the appropriate right: host kobjects use typed copies, IO main uses its dedicated endpoint, and other slots use mqueue send-right copying. The node argument is ignored locally. [host_get_special_port_from_user](../../../xnu/osfmk/kern/host.c#L1461-L1507).

**Declarations:** [`host_get_special_port_from_user`](../../../xnu/osfmk/mach/host_priv.defs#L211) (`server64`, `server32`, `local64`); [`host_get_special_port`](../../../xnu/osfmk/mach/host_priv.defs#L211) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
host_get_special_port_from_user(
                host_priv : host_priv_t;
                node : int;
                which : int;
        out port : mach_port_t);
```

**Local body:** [`host_get_special_port_from_user`](../../../xnu/osfmk/kern/host.c#L1461).
Calls visible in this body include `current_task`, `task_is_driver`, `IOCurrentTaskHasEntitlement`, `host_get_special_port`.

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1461-L1478):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1461-L1478 -->
```c
host_get_special_port_from_user(host_priv_t host_priv, __unused int node, int id, ipc_port_t * portp)
{
	if (host_priv == HOST_PRIV_NULL || id == HOST_SECURITY_PORT || id > HOST_MAX_SPECIAL_PORT || id < HOST_MIN_SPECIAL_PORT) {
		return KERN_INVALID_ARGUMENT;
	}

	task_t task = current_task();
	if (task && task_is_driver(task) && id > HOST_MAX_SPECIAL_KERNEL_PORT) {
		/* allow HID drivers to get the sysdiagnose port for keychord handling */
		if (id == HOST_SYSDIAGNOSE_PORT &&
		    IOCurrentTaskHasEntitlement(kIODriverKitHIDFamilyEventServiceEntitlementKey)) {
			goto get_special_port;
		}
		return KERN_NO_ACCESS;
	}
get_special_port:
	return host_get_special_port(host_priv, node, id, portp);
}
```

### 413: host_set_special_port_from_user

**Interface contract:**

> Set a given special port for the local node. See host_get_special_port.

**Mechanism:** Rejects kernel-owned slots, DriverKit callers, and send rights that cannot safely be stashed. The downstream setter permits kernel/init callers or the applicable entitlement/CSR exception, applies MAC policy, then swaps the host slot under its lock. The old send right is released afterward. Success transfers ownership of the new right to the host slot. [host_set_special_port_from_user](../../../xnu/osfmk/kern/host.c#L1347-L1451).

**Declarations:** [`host_set_special_port_from_user`](../../../xnu/osfmk/mach/host_priv.defs#L226) (`server64`, `server32`, `local64`); [`host_set_special_port`](../../../xnu/osfmk/mach/host_priv.defs#L226) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
host_set_special_port_from_user(
                host_priv : host_priv_t;
                which : int;
                port : mach_port_t);
```

**Local body:** [`host_set_special_port_from_user`](../../../xnu/osfmk/kern/host.c#L1401).
Calls visible in this body include `task_is_driver`, `current_task`, `ipc_can_stash_naked_send`, `host_set_special_port`.

### 414: host_set_exception_ports

**Interface contract:**

> Set an exception handler for a host on one or more exception types. These handlers are invoked for all threads on the host if there are no task or thread-specific exception handlers or those handlers returned an error.

**Mechanism:** Validates mask/behavior/flavor and MAC permission before taking the host lock. Selected exception actions receive copies of the new right and updated behavior/flavor, subject to per-action label updates. Lazy MAC labels are prepared outside the lock; displaced rights and unused labels are released afterward. Success consumes the supplied send right, rather than storing that one reference in every action. [host_set_exception_ports](../../../xnu/osfmk/kern/ipc_host.c#L492-L588).

**Declarations:** [`host_set_exception_ports`](../../../xnu/osfmk/mach/host_priv.defs#L242) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_set_exception_ports(
  host_priv : host_priv_t;
  exception_mask : exception_mask_t;
  new_port : mach_port_t;
  behavior : exception_behavior_t;
  new_flavor : thread_state_flavor_t);
```

**Local body:** [`host_set_exception_ports`](../../../xnu/osfmk/kern/ipc_host.c#L492).
Calls visible in this body include `set_exception_ports_validation`, `mac_task_check_set_host_exception_ports`, `current_task`, `mac_exc_create_label_for_current_proc`, `mac_exc_label`, `mac_exc_create_label`, `host_lock`, `mac_exc_associate_action_label`, `mac_exc_update_action_label`, `exception_port_copy_send`, `host_unlock`, `mac_exc_free_label`.

### 415: host_get_exception_ports

**Interface contract:**

> Lookup some of the old exception handlers for a host

**Mechanism:** Under the host lock, groups selected exception actions with identical port, behavior and state flavor into one result mask. Each newly represented group gets a copied send right, up to the caller’s supplied capacity. The output count is the groups actually returned; this query does not clear registrations or transfer their stored rights. [host_get_exception_ports](../../../xnu/osfmk/kern/ipc_host.c#L606-L657).

**Declarations:** [`host_get_exception_ports`](../../../xnu/osfmk/mach/host_priv.defs#L253) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_get_exception_ports(
  host_priv : host_priv_t;
  exception_mask : exception_mask_t;
   out masks : exception_mask_array_t;
   out old_handlers : exception_handler_array_t, SameCount;
   out old_behaviors : exception_behavior_array_t, SameCount;
   out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`host_get_exception_ports`](../../../xnu/osfmk/kern/ipc_host.c#L606).
Calls visible in this body include `host_lock`, `exception_port_copy_send`, `host_unlock`.

### 416: host_swap_exception_ports

**Interface contract:**

> Set an exception handler for a host on one or more exception types. At the same time, return the previously defined exception handlers for those types.

**Mechanism:** After validating the replacement and MAC permission, snapshots grouped old actions while installing copied replacement rights under the host lock. The loop is bounded by the supplied output capacity, so insufficient capacity limits which later exception types are processed rather than merely truncating a separately completed full swap. Old stored rights and the supplied replacement right are released after unlocking. [host_swap_exception_ports](../../../xnu/osfmk/kern/ipc_host.c#L660-L780).

**Declarations:** [`host_swap_exception_ports`](../../../xnu/osfmk/mach/host_priv.defs#L267) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_swap_exception_ports(
  host_priv : host_priv_t;
  exception_mask : exception_mask_t;
  new_port : mach_port_t;
  behavior : exception_behavior_t;
  new_flavor : thread_state_flavor_t;
   out masks : exception_mask_array_t;
   out old_handlerss : exception_handler_array_t, SameCount;
   out old_behaviors : exception_behavior_array_t, SameCount;
   out old_flavors : exception_flavor_array_t, SameCount);
```

**Local body:** [`host_swap_exception_ports`](../../../xnu/osfmk/kern/ipc_host.c#L660).
Calls visible in this body include `set_exception_ports_validation`, `mac_task_check_set_host_exception_ports`, `current_task`, `mac_exc_create_label_for_current_proc`, `mac_exc_label`, `mac_exc_create_label`, `host_lock`, `mac_exc_associate_action_label`, `mac_exc_update_action_label`, `exception_port_copy_send`, `host_unlock`, `mac_exc_free_label`.

### 417: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/host_priv.defs#L278).

### 418: mach_vm_wire_external

**Interface contract:**

> Specify that the range of the virtual address space of the target task must not cause page faults for the indicated accesses. [ To unwire the pages, specify VM_PROT_NONE. ]

**Mechanism:** The common implementation requires a privileged host and target map, computes the unsafe end address for the sanitizing map helpers, and interprets zero protection as unwire. Nonzero protection requests user-accounted wiring with the MLOCK tag; zero requests user unwiring. Validation, range walking and partial-work cleanup belong to `vm_map_wire_impl`/`vm_map_unwire_impl`; the older-sized entry simply forwards. [mach_vm_wire_external](../../../xnu/osfmk/vm/vm_user.c#L1127-L1175).

**Declarations:** [`mach_vm_wire_external`](../../../xnu/osfmk/mach/host_priv.defs#L287) (`server64`, `server32`, `local64`); [`mach_vm_wire`](../../../xnu/osfmk/mach/host_priv.defs#L287) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_wire_external(
  host_priv : host_priv_t;
  task : vm_map_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  desired_access : vm_prot_t);
```

**Local body:** [`mach_vm_wire_external`](../../../xnu/osfmk/vm/vm_user.c#L1127).
Calls visible in this body include `vm_sanitize_compute_ut_end`, `VM_SANITIZE_UNSAFE_IS_ZERO`, `vm_map_unwire_impl`, `vm_map_wire_impl`.

### 419: host_processor_sets

**Interface contract:**

> List all processor sets on host.

**Mechanism:** Allocates exactly one port-array element and returns a name capability for `sched_boot_pset`. Internal cluster processor sets are not enumerated through this compatibility interface. Null host is rejected; allocation uses the waiting, no-fail path. [host_processor_sets](../../../xnu/osfmk/kern/host.c#L1220-L1243).

**Declarations:** [`host_processor_sets`](../../../xnu/osfmk/mach/host_priv.defs#L301) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_processor_sets(
  host_priv : host_priv_t;
 out processor_sets : processor_set_name_array_t);
```

**Local body:** [`host_processor_sets`](../../../xnu/osfmk/kern/host.c#L1220).
Calls visible in this body include `mach_port_array_alloc`, `convert_pset_name_to_port`.

### 420: host_processor_set_priv

**Interface contract:**

> Get control port for a processor set.

**Mechanism:** Requires both a privileged host and an existing processor-set-name object. It returns that same set object for control-port conversion, rather than allocating another set or modifying membership. Invalid arguments explicitly clear the output set before returning failure. [host_processor_set_priv](../../../xnu/osfmk/kern/host.c#L1250-L1262).

**Declarations:** [`host_processor_set_priv`](../../../xnu/osfmk/mach/host_priv.defs#L308) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_processor_set_priv(
  host_priv : host_priv_t;
  set_name : processor_set_name_t;
 out set : processor_set_t);
```

**Local body:** [`host_processor_set_priv`](../../../xnu/osfmk/kern/host.c#L1250).

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1250-L1261):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1250-L1261 -->
```c
host_processor_set_priv(host_priv_t host_priv, processor_set_t pset_name, processor_set_t * pset)
{
	if (host_priv == HOST_PRIV_NULL || pset_name == PROCESSOR_SET_NULL) {
		*pset = PROCESSOR_SET_NULL;

		return KERN_INVALID_ARGUMENT;
	}

	*pset = pset_name;

	return KERN_SUCCESS;
}
```

### 421: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/host_priv.defs#L318).

### 422: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/host_priv.defs#L319).

### 423: host_set_UNDServer

**Interface contract:**

> Set the UserNotification daemon access port for this host. If this value is already set, the kernel will discard its reference to the previously registered port.

**Mechanism:** With user notifications configured, this is a wrapper around the host user-notification special-port helper, so its authorization and right ownership follow the host special-port operation. Without `CONFIG_USER_NOTIFICATION` it ignores the arguments and returns `KERN_NOT_SUPPORTED`; the interface declaration does not guarantee a notification-daemon backend. [host_set_UNDServer](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L364-L376).

**Declarations:** [`host_set_UNDServer`](../../../xnu/osfmk/mach/host_priv.defs#L326) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_set_UNDServer(
  host : host_priv_t;
 in server : UNDServerRef);
```

**Local body:** [`host_set_UNDServer`](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L364).
Calls visible in this body include `host_set_user_notification_port`, `unused`.

[Implementation excerpt](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L364-L374):
<!-- source-excerpt: ../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L364-L374 -->
```c
host_set_UNDServer(
	host_priv_t     host_priv,
	UNDServerRef    server)
{
#if CONFIG_USER_NOTIFICATION
	return host_set_user_notification_port(host_priv, server);
#else
#pragma unused(host_priv, server)
	return KERN_NOT_SUPPORTED;
#endif
}
```

### 424: host_get_UNDServer

**Interface contract:**

> Get the UserNotification daemon access port for this host. This can then be used to communicate with that daemon, which in turn communicates with the User through whatever means available (pop-up-menus for GUI systems, text for non-GUI, etc..). Access to this port is restricted to privileged clients because it is a special purpose port intended for kernel clients. User level clients should go directly to the CFUserNotifcation services.

**Mechanism:** With user notifications configured, this is a wrapper around the host user-notification special-port helper, so its authorization and right ownership follow the host special-port operation. Without `CONFIG_USER_NOTIFICATION` it ignores the arguments and returns `KERN_NOT_SUPPORTED`; the interface declaration does not guarantee a notification-daemon backend. [host_get_UNDServer](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L381-L391).

**Declarations:** [`host_get_UNDServer`](../../../xnu/osfmk/mach/host_priv.defs#L340) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_get_UNDServer(
  host : host_priv_t;
 out server : UNDServerRef);
```

**Local body:** [`host_get_UNDServer`](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L381).
Calls visible in this body include `host_get_user_notification_port`, `unused`.

[Implementation excerpt](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L381-L391):
<!-- source-excerpt: ../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L381-L391 -->
```c
host_get_UNDServer(
	host_priv_t     host_priv,
	UNDServerRef    *serverp)
{
#if CONFIG_USER_NOTIFICATION
	return host_get_user_notification_port(host_priv, serverp);
#else
#pragma unused(host_priv, serverp)
	return KERN_NOT_SUPPORTED;
#endif
}
```

### 425: kext_request

**Interface contract:**

> Perform an operation with a kernel extension, on the kext loading system, or request information about loaded kexts or the state of the kext loading system. Active operations (load, unload, disable/enable) require host_priv/root access. Info retrieval does not. WARNING: THIS ROUTINE IS PRIVATE TO THE KEXT-MANAGEMENT STACK AND IS SUBJECT TO CHANGE AT ANY TIME.

**Mechanism:** Clears all reply outputs before consuming the incoming VM-copy request into kernel-map memory. It distinguishes mkext binary loading from XML requests: secure/no-KXLD builds reject mkext, and loading requires the privileged host. OSKext operations report a separate `op_result`; response/log buffers become OOL copies. Copyout failure leaves input-copy cleanup to MIG, whereas a successfully mapped input is deallocated by the finish path. [kext_request](../../../xnu/libkern/OSKextLib.cpp#L218-L394).

**Declarations:** [`kext_request`](../../../xnu/osfmk/mach/host_priv.defs#L354) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine kext_request(
        host_priv : host_priv_t;
    in user_log_flags : uint32_t;
    in request_data : pointer_t;
    out response_data : pointer_t;
    out log_data : pointer_t;
    out op_result : kern_return_t);
```

**Local body:** [`kext_request`](../../../xnu/libkern/OSKextLib.cpp#L218).
Calls visible in this body include `OSKextLog`, `space`, `vm_map_copyout_size`, `vm_map_copyout`, `CAST_DOWN`, `MKEXT_GET_MAGIC`, `MKEXT_GET_SIGNATURE`, `loadFromMkext`, `handleRequest`, `vm_map_copyin`, `CAST_USER_ADDR_T`, `vm_deallocate`.
