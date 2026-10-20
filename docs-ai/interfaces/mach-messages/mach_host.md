# Mach messages: mach_host

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_host.defs](../../../xnu/osfmk/mach/mach_host.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 200: host_info

**Interface contract:**

> Return information about this host.

**Mechanism:** Dispatches each host flavor with layout-specific capacity checks, rather than returning one fixed snapshot. BASIC_INFO accepts the older short layout, conditionally reports the extended layout, and adjusts available CPUs for SMT policy. Scheduler info converts the active scheduler’s initial quantum into milliseconds; trap-availability flavors return zero words. Resource-size information remains an explicit invalid-argument branch. [host_info](../../../xnu/osfmk/kern/host.c#L204-L337).

**Declarations:** [`host_info`](../../../xnu/osfmk/mach/mach_host.defs#L94) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_info(
  host : host_t;
  flavor : host_flavor_t;
 out host_info_out : host_info_t, CountInOut);
```

**Local body:** [`host_info`](../../../xnu/osfmk/kern/host.c#L204).
Calls visible in this body include `slot_type`, `slot_subtype`, `current_task`, `slot_threadtype`, `SCHED`, `absolutetime_to_nanoseconds`, `PE_i_can_has_debugger`, `vm_purgeable_stats`, `bzero`, `PE_get_default`.

### 201: host_kernel_version

**Interface contract:**

> Get string describing current kernel version.

**Mechanism:** Requires a non-null host, then copies the global kernel version string into the fixed-size `kernel_version_t` result with bounded `strncpy`. It does not allocate an OOL buffer or query a separately running service. [host_kernel_version](../../../xnu/osfmk/kern/host.c#L1203-L1213).

**Declarations:** [`host_kernel_version`](../../../xnu/osfmk/mach/mach_host.defs#L102) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_kernel_version(
  host : host_t;
 out kernel_version : kernel_version_t);
```

**Local body:** [`host_kernel_version`](../../../xnu/osfmk/kern/host.c#L1203).
Calls visible in this body include `strncpy`.

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1203-L1212):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1203-L1212 -->
```c
host_kernel_version(host_t host, kernel_version_t out_version)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	(void)strncpy(out_version, version, sizeof(kernel_version_t));

	return KERN_SUCCESS;
}
```

### 202: host_page_size

**Interface contract:**

> Get host page size (compatibility for running old libraries on new kernels - host_page_size() is now a library routine based on constants)

**Mechanism:** Requires a non-null host and returns the kernel’s `PAGE_SIZE`. This is not a query of an arbitrary task map’s page mask or the hardware geometry selected by that map’s pmap. [host_page_size](../../../xnu/osfmk/kern/host.c#L1185-L1194).

**Declarations:** [`host_page_size`](../../../xnu/osfmk/mach/mach_host.defs#L112) (`server64`, `server32`, `sender64`, `local64`); [`_host_page_size`](../../../xnu/osfmk/mach/mach_host.defs#L114) (`client64`, `client32`, `libsyscall64`).

**Fields after preprocessing (`server64`):**

```text
routine host_page_size(
  host : host_t;
 out out_page_size : vm_size_t);
```

**Local body:** [`host_page_size`](../../../xnu/osfmk/kern/host.c#L1185).

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1185-L1194):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1185-L1194 -->
```c
host_page_size(host_t host, vm_size_t * out_page_size)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	*out_page_size = PAGE_SIZE;

	return KERN_SUCCESS;
}
```

**User wrapper:** [`host_page_size`](../../../xnu/libsyscall/mach/mach_init.c#L89).

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_init.c#L89-L93):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_init.c#L89-L93 -->
```c
host_page_size(__unused host_t host, vm_size_t *out_page_size)
{
	*out_page_size = vm_kernel_page_size;
	return KERN_SUCCESS;
}
```

### 203: mach_memory_object_memory_entry

**Interface contract:**

> Allow pagers to create named entries that point to un-mapped abstract memory object. The named entries are generally mappable and can be subsetted through the mach_make_memory_entry call

**Mechanism:** The common 64-bit implementation validates host, size and permissions, then either allocates an internal VM object when no pager was supplied or references the VM object represented by the pager. It creates a named entry, stores size/protection/access, associates the object range, and records internal/ownership attributes. A missing backing object is invalid-argument. The older-sized routine only forwards into this implementation. [mach_memory_object_memory_entry](../../../xnu/osfmk/vm/vm_memory_entry.c#L1340-L1405).

**Declarations:** [`mach_memory_object_memory_entry`](../../../xnu/osfmk/mach/mach_host.defs#L124) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_object_memory_entry(
  host :host_t;
  internal :boolean_t;
  size :vm_size_t;
  permission :vm_prot_t;
  pager :memory_object_t;
 out entry_handle :mach_port_move_send_t);
```

**Local body:** [`mach_memory_object_memory_entry`](../../../xnu/osfmk/vm/vm_memory_entry.c#L1461).
Calls visible in this body include `mach_memory_object_memory_entry_64`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_memory_entry.c#L1461-L1471):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_memory_entry.c#L1461-L1471 -->
```c
mach_memory_object_memory_entry(
	host_t          host,
	boolean_t       internal,
	vm_size_ut      size_u,
	vm_prot_ut      permission_u,
	memory_object_t pager,
	ipc_port_t      *entry_handle)
{
	return mach_memory_object_memory_entry_64( host, internal,
	           size_u, permission_u, pager, entry_handle);
}
```

### 204: host_processor_info

**Interface contract:**

> Get processor info for all the processors on this host. The returned data is an OOL array of processor info.

**Mechanism:** Obtains the per-CPU record size for the requested flavor, allocates a rounded IPC-kernel-map buffer, and fills each slot by calling `processor_info`. A per-CPU failure frees the allocation. Success zeroes trailing page padding, unwires the buffer, and turns the used bytes into a source-destroying VM copy for the OOL reply. Processor count and total word count describe that packed array. [host_processor_info](../../../xnu/osfmk/kern/host.c#L1271-L1335).

**Declarations:** [`host_processor_info`](../../../xnu/osfmk/mach/mach_host.defs#L137) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_processor_info(
  host : host_t;
                flavor : processor_flavor_t;
 out out_processor_count : natural_t;
        out out_processor_info : processor_info_array_t);
```

**Local body:** [`host_processor_info`](../../../xnu/osfmk/kern/host.c#L1271).
Calls visible in this body include `processor_info_count`, `vm_map_round_page`, `VM_MAP_PAGE_MASK`, `kmem_alloc`, `processor_info`, `kmem_free`, `bzero`, `vm_map_unwire`, `vm_map_trunc_page`, `vm_map_copyin`.

### 205: host_get_io_main

**Interface contract:**

> Return host IO main access port

**Mechanism:** Rejects a null ordinary host, then obtains the IO main special port through the privileged-host helper using the kernel’s real host object. The returned right names the existing IOKit service endpoint; no driver or registry object is instantiated by this call. [host_get_io_main](../../../xnu/osfmk/kern/host.c#L1516-L1523).

**Declarations:** [`host_get_io_main`](../../../xnu/osfmk/mach/mach_host.defs#L146) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine
host_get_io_main(
                host : host_t;
        out io_main : io_main_t);
```

**Local body:** [`host_get_io_main`](../../../xnu/osfmk/kern/host.c#L1516).
Calls visible in this body include `host_get_io_main_port`, `host_priv_self`.

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1516-L1523):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1516-L1523 -->
```c
host_get_io_main(host_t host, io_main_t * io_mainp)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return host_get_io_main_port(host_priv_self(), io_mainp);
}
```

### 206: host_get_clock_service

**Interface contract:**

> Get service port for a processor set. Available to all.

**Mechanism:** Checks the host and bounds of the clock ID, selects the static `clock_list` entry, and rejects an entry lacking operations. The output is the clock service object converted by MIG into its capability; this operation neither allocates a new clock nor grants a clock-control implementation. [host_get_clock_service](../../../xnu/osfmk/kern/clock_oldops.c#L253-L268).

**Declarations:** [`host_get_clock_service`](../../../xnu/osfmk/mach/mach_host.defs#L159) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_get_clock_service(
  host : host_t;
  clock_id : clock_id_t;
 out clock_serv : clock_serv_t);
```

**Local body:** [`host_get_clock_service`](../../../xnu/osfmk/kern/clock_oldops.c#L253).

[Implementation excerpt](../../../xnu/osfmk/kern/clock_oldops.c#L253-L268):
<!-- source-excerpt: ../../../xnu/osfmk/kern/clock_oldops.c#L253-L268 -->
```c
host_get_clock_service(
	host_t                  host,
	clock_id_t              clock_id,
	clock_t                 *clock)         /* OUT */
{
	if (host == HOST_NULL || clock_id < 0 || clock_id >= clock_count) {
		*clock = CLOCK_NULL;
		return KERN_INVALID_ARGUMENT;
	}

	*clock = &clock_list[clock_id];
	if ((*clock)->cl_ops == 0) {
		return KERN_FAILURE;
	}
	return KERN_SUCCESS;
}
```

### 207: kmod_get_info

**Interface contract:**

> kmod_ MIG calls now return KERN_NOT_SUPPORTED on PPC/i386/x86_64.

**Mechanism:** This body only logs that the operation is unsupported on the kernel architecture, including the caller’s process name, and returns `KERN_NOT_SUPPORTED`. It does not enumerate OSKext objects despite the retained OOL result declaration. [kmod_get_info](../../../xnu/osfmk/kern/kmod.c#L98-L105).

**Declarations:** [`kmod_get_info`](../../../xnu/osfmk/mach/mach_host.defs#L169) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine kmod_get_info(
  host : host_t;
 out modules : kmod_args_t);
```

**Local body:** [`kmod_get_info`](../../../xnu/osfmk/kern/kmod.c#L98).
Calls visible in this body include `NOT_SUPPORTED_KERNEL`.

[Implementation excerpt](../../../xnu/osfmk/kern/kmod.c#L98-L105):
<!-- source-excerpt: ../../../xnu/osfmk/kern/kmod.c#L98-L105 -->
```c
kmod_get_info(
	host_t host __unused,
	kmod_info_array_t * kmod_list KMOD_MIG_UNUSED,
	mach_msg_type_number_t * kmodCount KMOD_MIG_UNUSED)
{
	NOT_SUPPORTED_KERNEL();
	return KERN_NOT_SUPPORTED;
}
```

### 208: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/mach_host.defs#L174).

### 209: host_virtual_physical_table_info

**Interface contract:**

> Returns information about the global VP table. Only supported in MACH_VM_DEBUG kernels, otherwise returns KERN_FAILURE.

**Mechanism:** The local routine unconditionally returns `KERN_FAILURE`; it does not fill the historical physical-hash-bucket array. The retained interface should not be used as evidence of a supported pmap introspection mechanism. [host_virtual_physical_table_info](../../../xnu/osfmk/vm/vm_debug.c#L152-L158).

**Declarations:** [`host_virtual_physical_table_info`](../../../xnu/osfmk/mach/mach_host.defs#L181) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_virtual_physical_table_info(
  host : host_t;
 out info : hash_info_bucket_array_t,
     Dealloc);
```

**Local body:** [`host_virtual_physical_table_info`](../../../xnu/osfmk/vm/vm_debug.c#L152).

[Implementation excerpt](../../../xnu/osfmk/vm/vm_debug.c#L152-L158):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_debug.c#L152-L158 -->
```c
host_virtual_physical_table_info(
	__DEBUG_ONLY host_t                     host,
	__DEBUG_ONLY hash_info_bucket_array_t   *infop,
	__DEBUG_ONLY mach_msg_type_number_t     *countp)
{
	return KERN_FAILURE;
}
```

### 210: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/mach_host.defs#L187).

### 211: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/mach_host.defs#L188).

### 212: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/mach_host.defs#L189).

### 213: processor_set_default

**Interface contract:**

> Get default processor set for host.

**Mechanism:** A non-null host returns `sched_boot_pset`. No set is created and no scheduler state is changed; MIG converts this existing compatibility-set object into the requested processor-set capability. A null host fails before publishing an output object. [processor_set_default](../../../xnu/osfmk/kern/ipc_host.c#L221-L233).

**Declarations:** [`processor_set_default`](../../../xnu/osfmk/mach/mach_host.defs#L194) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_set_default(
  host : host_t;
 out default_set : processor_set_name_t);
```

**Local body:** [`processor_set_default`](../../../xnu/osfmk/kern/ipc_host.c#L221).

[Implementation excerpt](../../../xnu/osfmk/kern/ipc_host.c#L221-L232):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ipc_host.c#L221-L232 -->
```c
processor_set_default(
	host_t                  host,
	processor_set_t         *pset)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	*pset = sched_boot_pset;

	return KERN_SUCCESS;
}
```

### 214: processor_set_create

Request creation of a processor set through the historical host interface.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_create](../../../xnu/osfmk/mach/mach_host.defs#L204).

**Declarations:** [`processor_set_create`](../../../xnu/osfmk/mach/mach_host.defs#L204) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_create(
  host : host_t;
 out new_set : processor_set_t;
 out new_name : processor_set_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 215: mach_memory_object_memory_entry_64

Create a named memory-entry capability for the supplied memory object/size/permissions.

**Mechanism:** The common 64-bit implementation validates host, size and permissions, then either allocates an internal VM object when no pager was supplied or references the VM object represented by the pager. It creates a named entry, stores size/protection/access, associates the object range, and records internal/ownership attributes. A missing backing object is invalid-argument. The older-sized routine only forwards into this implementation. [mach_memory_object_memory_entry_64](../../../xnu/osfmk/vm/vm_memory_entry.c#L1340-L1405).

**Declarations:** [`mach_memory_object_memory_entry_64`](../../../xnu/osfmk/mach/mach_host.defs#L210) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_object_memory_entry_64(
  host :host_t;
  internal :boolean_t;
  size :memory_object_size_t;
  permission :vm_prot_t;
  pager :memory_object_t;
 out entry_handle :mach_port_move_send_t);
```

**Local body:** [`mach_memory_object_memory_entry_64`](../../../xnu/osfmk/vm/vm_memory_entry.c#L1340).
Calls visible in this body include `mach_memory_object_memory_entry_64_sanitize`, `vm_sanitize_get_kr`, `vm_object_allocate`, `memory_object_to_vm_object`, `vm_object_reference`, `mach_memory_entry_allocate`, `GET_MAP_MEM`, `vm_named_entry_associate_vm_object`, `VM_OBJECT_OWNER`.

### 216: host_statistics_from_user

**Interface contract:**

> Return statistics from this host.

**Mechanism:** The user wrapper validates the host, then invokes the rate-limiter/cache helper before reading statistics. A cached reply or rate-limit error returns immediately. Otherwise it calls the corresponding statistics dispatcher and caches only a successful result. The 64-bit dispatcher handles its extended flavors and can fall back to the ordinary dispatcher; these wrappers therefore have different freshness semantics from direct kernel calls. [host_statistics_from_user](../../../xnu/osfmk/kern/host.c#L1061-L1111).

**Declarations:** [`host_statistics_from_user`](../../../xnu/osfmk/mach/mach_host.defs#L221) (`server64`, `server32`, `local64`); [`host_statistics`](../../../xnu/osfmk/mach/mach_host.defs#L221) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
host_statistics_from_user(
  host_priv : host_t;
  flavor : host_flavor_t;
 out host_info_out : host_info_t, CountInOut);
```

**Local body:** [`host_statistics_from_user`](../../../xnu/osfmk/kern/host.c#L1088).
Calls visible in this body include `rate_limit_host_statistics`, `host_statistics`, `cache_host_statistics`.

### 217: host_request_notification

Register a notification request on the host, retaining its reply capability according to the host-notification lifetime.

**Mechanism:** Validates the host, send-once reply capability and notification selector, then allocates a host-notify record. Under the global notify lock and port queue lock it registers a port request and queues the record; successful registration also makes an ordinary in-space receive right immovable. A full request table is grown after dropping locks and retried; other errors free the record without installing it. [host_request_notification](../../../xnu/osfmk/kern/host_notify.c#L65-L130).

**Declarations:** [`host_request_notification`](../../../xnu/osfmk/mach/mach_host.defs#L231) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_request_notification(
  host : host_t;
  notify_type : host_flavor_t;
  notify_port : mach_port_make_send_once_t);
```

**Local body:** [`host_request_notification`](../../../xnu/osfmk/kern/host_notify.c#L65).
Calls visible in this body include `IP_VALID`, `zalloc_flags`, `lck_mtx_lock`, `ip_mq_lock`, `ip_active`, `ipc_port_request_hnotify_alloc`, `ip_is_immovable_receive`, `ip_label_get`, `ipc_release_assert`, `io_label_set_and_put`, `enqueue_tail`, `lck_mtx_unlock`.

### 218: host_lockgroup_info

Snapshot lock-group statistics into an allocated output array.

**Mechanism:** Allocates a zeroed IPC-map buffer with modest growth slack, then enumerates lock groups and copies counters/names until capacity is reached. DTrace counters are configuration-dependent and the fields are not a globally atomic snapshot. Unused trailing pages are freed; the used pages are unwired and converted to a source-destroying VM copy for the OOL result. [host_lockgroup_info](../../../xnu/osfmk/kern/lock_group.c#L331-L410).

**Declarations:** [`host_lockgroup_info`](../../../xnu/osfmk/mach/mach_host.defs#L236) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_lockgroup_info(
  host : host_t;
 out lockgroup_info : lockgroup_info_array_t,
     Dealloc);
```

**Local body:** [`host_lockgroup_info`](../../../xnu/osfmk/kern/lock_group.c#L331).
Calls visible in this body include `os_atomic_load`, `vm_map_round_page`, `VM_MAP_PAGE_MASK`, `kmem_alloc`, `lck_grp_foreach`, `bool`, `memcpy`, `kmem_free`, `vm_map_unwire`, `vm_map_copyin`.

### 219: host_statistics64_from_user

**Interface contract:**

> Return 64-bit statistics from this host.

**Mechanism:** The user wrapper validates the host, then invokes the rate-limiter/cache helper before reading statistics. A cached reply or rate-limit error returns immediately. Otherwise it calls the corresponding statistics dispatcher and caches only a successful result. The 64-bit dispatcher handles its extended flavors and can fall back to the ordinary dispatcher; these wrappers therefore have different freshness semantics from direct kernel calls. [host_statistics64_from_user](../../../xnu/osfmk/kern/host.c#L1061-L1111).

**Declarations:** [`host_statistics64_from_user`](../../../xnu/osfmk/mach/mach_host.defs#L244) (`server64`, `server32`, `local64`); [`host_statistics64`](../../../xnu/osfmk/mach/mach_host.defs#L244) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
host_statistics64_from_user(
  host_priv : host_t;
  flavor : host_flavor_t;
 out host_info64_out : host_info64_t, CountInOut);
```

**Local body:** [`host_statistics64_from_user`](../../../xnu/osfmk/kern/host.c#L1061).
Calls visible in this body include `rate_limit_host_statistics`, `host_statistics64`, `cache_host_statistics`.

### 220: mach_zone_info

**Interface contract:**

> Returns information about the memory allocation zones. Data returned is compatible with various caller and kernel address space sizes.

**Mechanism:** Delegates to `mach_memory_info` without requesting the auxiliary memory-information array. That entry first attempts privileged-host conversion; ordinary-host conversion selects redacted output. The shared implementation applies memory-information security checks and packages zone names/statistics into OOL VM copies, so this older call inherits redaction, coalescing and admission behavior. [mach_zone_info](../../../xnu/osfmk/kern/zalloc.c#L8194-L8224).

**Declarations:** [`mach_zone_info`](../../../xnu/osfmk/mach/mach_host.defs#L259) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_zone_info(
  host : mach_port_t;
 out names : mach_zone_name_array_t,
     Dealloc;
 out info : mach_zone_info_array_t,
     Dealloc);
```

**Local body:** [`mach_zone_info`](../../../xnu/osfmk/kern/zalloc.c#L8194).
Calls visible in this body include `mach_memory_info`.

[Implementation excerpt](../../../xnu/osfmk/kern/zalloc.c#L8194-L8202):
<!-- source-excerpt: ../../../xnu/osfmk/kern/zalloc.c#L8194-L8202 -->
```c
mach_zone_info(
	mach_port_t             host_port,
	mach_zone_name_array_t  *namesp,
	mach_msg_type_number_t  *namesCntp,
	mach_zone_info_array_t  *infop,
	mach_msg_type_number_t  *infoCntp)
{
	return mach_memory_info(host_port, namesp, namesCntp, infop, infoCntp, NULL, NULL);
}
```

### 221: mach_zone_force_gc

**Interface contract:**

> Forces a zone allocator garbage collections pass. Pages with no in-use allocations are returned to the VM system for re-use.

**Mechanism:** Validates the host. Only DEBUG/DEVELOPMENT builds call the optional buffer-cache collector followed by `zone_gc(ZONE_GC_DRAIN)`; other builds return success without performing that collection. A successful return therefore does not universally demonstrate that any zone pages were reclaimed. [mach_zone_force_gc](../../../xnu/osfmk/kern/zalloc.c#L8722-L8739).

**Declarations:** [`mach_zone_force_gc`](../../../xnu/osfmk/mach/mach_host.defs#L272) (`client64`, `client32`, `libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `sender64`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_zone_force_gc(
  host : host_t);
```

**Local body:** [`mach_zone_force_gc`](../../../xnu/osfmk/kern/zalloc.c#L8722).
Calls visible in this body include `boolean_t`, `zone_gc`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/osfmk/kern/zalloc.c#L8722-L8738):
<!-- source-excerpt: ../../../xnu/osfmk/kern/zalloc.c#L8722-L8738 -->
```c
mach_zone_force_gc(
	host_t host)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_HOST;
	}

#if DEBUG || DEVELOPMENT
	extern boolean_t(*volatile consider_buffer_cache_collect)(int);
	/* Callout to buffer cache GC to drop elements in the apfs zones */
	if (consider_buffer_cache_collect != NULL) {
		(void)(*consider_buffer_cache_collect)(0);
	}
	zone_gc(ZONE_GC_DRAIN);
#endif /* DEBUG || DEVELOPMENT */
	return KERN_SUCCESS;
}
```

### 222: host_create_mach_voucher

Create a voucher by interpreting the supplied recipes through the registered voucher managers.

**Mechanism:** Validates the host then invokes the common voucher creator without an attribute-control capability and with user-data recipe conversion enabled. The creator allocates an initially empty voucher, walks bounded recipes, resolves previous-voucher names, applies attribute-manager commands, and releases partially built state on failure. Successful construction deduplicates the voucher’s attribute set before publishing a reference. [host_create_mach_voucher](../../../xnu/osfmk/ipc/ipc_voucher.c#L1407-L1559).

**Declarations:** [`host_create_mach_voucher`](../../../xnu/osfmk/mach/mach_host.defs#L285) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_host_create_mach_voucher`](../../../xnu/osfmk/mach/mach_host.defs#L283) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine host_create_mach_voucher(
  host : host_t;
  recipes : mach_voucher_attr_raw_recipe_array_t;
 out voucher : ipc_voucher_t);
```

**Local body:** [`host_create_mach_voucher`](../../../xnu/osfmk/ipc/ipc_voucher.c#L2070).
Calls visible in this body include `ipc_create_mach_voucher_internal`.

[Implementation excerpt](../../../xnu/osfmk/ipc/ipc_voucher.c#L2070-L2082):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_voucher.c#L2070-L2082 -->
```c
host_create_mach_voucher(
	host_t host,
	mach_voucher_attr_raw_recipe_array_t recipes,
	mach_voucher_attr_raw_recipe_size_t recipe_size,
	ipc_voucher_t *new_voucher)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return ipc_create_mach_voucher_internal(IPC_VOUCHER_ATTR_CONTROL_NULL,
	           recipes, recipe_size, true, new_voucher);
}
```

**User wrapper:** [`host_create_mach_voucher`](../../../xnu/libsyscall/mach/host.c#L84).
Calls visible in this body include `host_create_mach_voucher_trap`, `_kernelrpc_host_create_mach_voucher`.

### 223: host_register_mach_voucher_attr_manager

**Interface contract:**

> was host_register_well_known_mach_voucher_attr_manager

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_register_mach_voucher_attr_manager](../../../xnu/osfmk/mach/mach_host.defs#L296).

**Declarations:** [`host_register_mach_voucher_attr_manager`](../../../xnu/osfmk/mach/mach_host.defs#L296) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine host_register_mach_voucher_attr_manager(
  host : host_t;
  attr_manager : mach_voucher_attr_manager_t;
  default_value : mach_voucher_attr_value_handle_t;
 out new_key : mach_voucher_attr_key_t;
 out new_attr_control: ipc_voucher_attr_control_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 224: host_register_well_known_mach_voucher_attr_manager

Register a well-known voucher attribute manager and return its control capability; distinguish kernel registration from public message availability.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_register_well_known_mach_voucher_attr_manager](../../../xnu/osfmk/mach/mach_host.defs#L303).

**Declarations:** [`host_register_well_known_mach_voucher_attr_manager`](../../../xnu/osfmk/mach/mach_host.defs#L303) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine host_register_well_known_mach_voucher_attr_manager(
  host : host_t;
  attr_manager : mach_voucher_attr_manager_t;
  default_value : mach_voucher_attr_value_handle_t;
  key : mach_voucher_attr_key_t;
 out new_attr_control: ipc_voucher_attr_control_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 225: host_set_atm_diagnostic_flag

**Interface contract:**

> Update the global ATM diagnostic flag, readable from the commpage

**Mechanism:** Requires a valid host and the private set-atm-diagnostic-flag entitlement. With ATM configured it delegates to `atm_set_diagnostic_config`; otherwise it returns `KERN_NOT_SUPPORTED` after those admission checks. Possession of the ordinary host port alone is insufficient to change the setting. [host_set_atm_diagnostic_flag](../../../xnu/osfmk/kern/host.c#L1538-L1553).

**Declarations:** [`host_set_atm_diagnostic_flag`](../../../xnu/osfmk/mach/mach_host.defs#L314) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_set_atm_diagnostic_flag(
  host : host_t;
 in diagnostic_flag : uint32_t);
```

**Local body:** [`host_set_atm_diagnostic_flag`](../../../xnu/osfmk/kern/host.c#L1538).
Calls visible in this body include `IOCurrentTaskHasEntitlement`, `atm_set_diagnostic_config`, `else`.

[Implementation excerpt](../../../xnu/osfmk/kern/host.c#L1538-L1554):
<!-- source-excerpt: ../../../xnu/osfmk/kern/host.c#L1538-L1554 -->
```c
host_set_atm_diagnostic_flag(host_t host, uint32_t diagnostic_flag)
{
	if (host == HOST_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	if (!IOCurrentTaskHasEntitlement("com.apple.private.set-atm-diagnostic-flag")) {
		return KERN_NO_ACCESS;
	}

#if CONFIG_ATM
	return atm_set_diagnostic_config(diagnostic_flag);
#else
	(void)diagnostic_flag;
	return KERN_NOT_SUPPORTED;
#endif
}
```

### 226: host_get_atm_diagnostic_flag

Read the ATM diagnostic flag through the libsyscall/commpage interface declaration.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_get_atm_diagnostic_flag](../../../xnu/osfmk/mach/mach_host.defs#L319).

**Declarations:** [`host_get_atm_diagnostic_flag`](../../../xnu/osfmk/mach/mach_host.defs#L319) (`libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `client64`, `client32`, `sender64`, `local64`.

**Fields after preprocessing (`libsyscall64`):**

```text
routine host_get_atm_diagnostic_flag(
  host : host_t;
 out diagnostic_flag : uint32_t);
```

**User wrapper:** [`host_get_atm_diagnostic_flag`](../../../xnu/libsyscall/mach/host.c#L37).
Calls visible in this body include `COMM_PAGE_READ`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/libsyscall/mach/host.c#L37-L42):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/host.c#L37-L42 -->
```c
host_get_atm_diagnostic_flag(host_t host __unused,
    uint32_t *diagnostic_flag)
{
	*diagnostic_flag = COMM_PAGE_READ(uint32_t, ATM_DIAGNOSTIC_CONFIG);
	return KERN_SUCCESS;
}
```

Only a user-library body was resolved here; that is not a kernel receiver implementation.

### 227: mach_memory_info

Collect memory/zone accounting information after converting the supplied host capability to the permitted flavor.

**Mechanism:** Uses the raw destination port to distinguish a privileged host from an ordinary host, selecting redaction for the latter. Shared sampling performs root/entitlement/rate-limit checks as configured. Redacted samples zero sensitive size fields and coalesce typed-allocation zones by element size; full samples also accumulate collectable bytes. Results are returned as VM-copy arrays, not pointers into live zone metadata. [mach_memory_info](../../../xnu/osfmk/kern/zalloc.c#L8100-L8144). [Port conversion and sampling](../../../xnu/osfmk/kern/zalloc.c#L8205-L8370).

**Declarations:** [`mach_memory_info`](../../../xnu/osfmk/mach/mach_host.defs#L326) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_info(
  host : mach_port_t;
 out names : mach_zone_name_array_t,
     Dealloc;
 out info : mach_zone_info_array_t,
     Dealloc;
 out memory_info : mach_memory_info_array_t,
     Dealloc);
```

**Local body:** [`mach_memory_info`](../../../xnu/osfmk/kern/zalloc.c#L8205).
Calls visible in this body include `convert_port_to_host_priv`, `convert_port_to_host`, `mach_memory_info_internal`.

### 228: host_set_multiuser_config_flags

**Interface contract:**

> Update the global multiuser flags, readable from the commpage

**Mechanism:** On non-macOS targets, validates the privileged-host object and directly updates the commpage multiuser configuration. On macOS the body ignores both arguments and returns `KERN_NOT_SUPPORTED`. This call updates the published bit configuration, not a set of user accounts or per-process credentials. [host_set_multiuser_config_flags](../../../xnu/osfmk/kern/host.c#L1557-L1576).

**Declarations:** [`host_set_multiuser_config_flags`](../../../xnu/osfmk/mach/mach_host.defs#L338) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_set_multiuser_config_flags(
  host_priv : host_priv_t;
 in multiuser_flags : uint32_t);
```

**Local body:** [`host_set_multiuser_config_flags`](../../../xnu/osfmk/kern/host.c#L1557).
Calls visible in this body include `commpage_update_multiuser_config`, `else`.

### 229: host_get_multiuser_config_flags

Read the multiuser configuration flags through the libsyscall/commpage interface declaration.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_get_multiuser_config_flags](../../../xnu/osfmk/mach/mach_host.defs#L343).

**Declarations:** [`host_get_multiuser_config_flags`](../../../xnu/osfmk/mach/mach_host.defs#L343) (`libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `client64`, `client32`, `sender64`, `local64`.

**Fields after preprocessing (`libsyscall64`):**

```text
routine host_get_multiuser_config_flags(
  host : host_t;
 out multiuser_flags : uint32_t);
```

**User wrapper:** [`host_get_multiuser_config_flags`](../../../xnu/libsyscall/mach/host.c#L45).
Calls visible in this body include `COMM_PAGE_READ`, `else`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/libsyscall/mach/host.c#L45-L55):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/host.c#L45-L55 -->
```c
host_get_multiuser_config_flags(host_t host __unused,
    uint32_t *multiuser_flags)
{
#if (TARGET_OS_IPHONE && !TARGET_OS_SIMULATOR)
	*multiuser_flags = COMM_PAGE_READ(uint32_t, MULTIUSER_CONFIG);
	return KERN_SUCCESS;
#else
	(void)multiuser_flags;
	return KERN_NOT_SUPPORTED;
#endif
}
```

Only a user-library body was resolved here; that is not a kernel receiver implementation.

### 230: host_check_multiuser_mode

Test multiuser mode using the shared configuration flags.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [host_check_multiuser_mode](../../../xnu/osfmk/mach/mach_host.defs#L351).

**Declarations:** [`host_check_multiuser_mode`](../../../xnu/osfmk/mach/mach_host.defs#L351) (`libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `client64`, `client32`, `sender64`, `local64`.

**Fields after preprocessing (`libsyscall64`):**

```text
routine host_check_multiuser_mode(
  host : host_t;
 out multiuser_mode : uint32_t);
```

**User wrapper:** [`host_check_multiuser_mode`](../../../xnu/libsyscall/mach/host.c#L58).
Calls visible in this body include `host_get_multiuser_config_flags`, `else`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/libsyscall/mach/host.c#L58-L75):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/host.c#L58-L75 -->
```c
host_check_multiuser_mode(host_t host __unused,
    uint32_t *multiuser_mode)
{
#if (TARGET_OS_IPHONE && !TARGET_OS_SIMULATOR)
	uint32_t multiuser_flags;
	kern_return_t kr;

	kr = host_get_multiuser_config_flags(host, &multiuser_flags);
	if (kr != KERN_SUCCESS) {
		return kr;
	}
	*multiuser_mode = (multiuser_flags & kIsMultiUserDevice) == kIsMultiUserDevice;
	return KERN_SUCCESS;
#else
	(void)multiuser_mode;
	return KERN_NOT_SUPPORTED;
#endif
}
```

Only a user-library body was resolved here; that is not a kernel receiver implementation.

### 231: mach_zone_info_for_zone

**Interface contract:**

> Returns information about a specific zone. The zone name is passed in via the argument name, info returns the zone info.

**Mechanism:** Requires a valid host and output pointer, with an additional debugger-availability gate in protected zone-info configurations. It builds each zone’s heap-prefixed name and uses `track_this_zone` to find a match, then snapshots that zone through `get_zone_info`. Missing names return invalid-argument; a failed snapshot returns failure. [mach_zone_info_for_zone](../../../xnu/osfmk/kern/zalloc.c#L8505-L8551).

**Declarations:** [`mach_zone_info_for_zone`](../../../xnu/osfmk/mach/mach_host.defs#L363) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_zone_info_for_zone(
  host : host_priv_t;
  name : mach_zone_name_t;
 out info : mach_zone_info_t);
```

**Local body:** [`mach_zone_info_for_zone`](../../../xnu/osfmk/kern/zalloc.c#L8505).
Calls visible in this body include `PE_i_can_has_debugger`, `zone_foreach`, `snprintf`, `zone_heap_name`, `track_this_zone`, `get_zone_info`.

### 232: mach_zone_info_for_largest_zone

**Interface contract:**

> Returns information about the largest zone. name returns the zone name, info returns the zone info.

**Mechanism:** Applies the host/debugger gate and validates both output pointers, then asks `zone_find_largest` for the current largest zone and snapshots its name/statistics with `get_zone_info`. It does not reclaim that zone or pin its population against later changes. Snapshot failure is reported as `KERN_FAILURE`. [mach_zone_info_for_largest_zone](../../../xnu/osfmk/kern/zalloc.c#L8554-L8577).

**Declarations:** [`mach_zone_info_for_largest_zone`](../../../xnu/osfmk/mach/mach_host.defs#L373) (`client64`, `client32`, `libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `sender64`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_zone_info_for_largest_zone(
  host : host_priv_t;
 out name : mach_zone_name_t;
 out info : mach_zone_info_t);
```

**Local body:** [`mach_zone_info_for_largest_zone`](../../../xnu/osfmk/kern/zalloc.c#L8554).
Calls visible in this body include `PE_i_can_has_debugger`, `get_zone_info`, `zone_find_largest`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

### 233: mach_zone_get_zlog_zones

**Interface contract:**

> Returns names of zones that have zlog enabled.

**Mechanism:** When zone logging is compiled in, validates the host and outputs, allocates a pageable IPC-map name buffer sized to the current zone count, and includes only zones with a `z_btlog`. The used names become a VM-copy result. Without `ZALLOC_ENABLE_LOGGING`, the routine simply returns `KERN_FAILURE`. [mach_zone_get_zlog_zones](../../../xnu/osfmk/kern/zalloc.c#L8596-L8649).

**Declarations:** [`mach_zone_get_zlog_zones`](../../../xnu/osfmk/mach/mach_host.defs#L385) (`client64`, `client32`, `libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `sender64`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_zone_get_zlog_zones(
  host : host_priv_t;
 out names : mach_zone_name_array_t,
     Dealloc);
```

**Local body:** [`mach_zone_get_zlog_zones`](../../../xnu/osfmk/kern/zalloc.c#L8596).
Calls visible in this body include `os_atomic_load`, `round_page`, `kmem_alloc`, `get_zone_info`, `create_vm_map_copy`, `unused`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

### 234: mach_zone_get_btlog_records

**Interface contract:**

> Returns BTLog records for a specific zone. The zone name is passed in via the argument name, recs returns an array of zone_btrecord_t's.

**Mechanism:** With zone logging enabled, finds the heap-prefixed zone name, rejects an absent zone or missing log, then obtains a record snapshot from `btlog_get_records`. It converts that allocated snapshot into a source-destroying VM copy for reply ownership. Allocation/helper errors propagate; a build without logging returns failure rather than an empty successful snapshot. [mach_zone_get_btlog_records](../../../xnu/osfmk/kern/zalloc.c#L8652-L8717).

**Declarations:** [`mach_zone_get_btlog_records`](../../../xnu/osfmk/mach/mach_host.defs#L399) (`client64`, `client32`, `libsyscall64`).
**Reserved instead in:** `server64`, `server32`, `sender64`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_zone_get_btlog_records(
  host : host_priv_t;
  name : mach_zone_name_t;
 out recs : zone_btrecord_array_t,
     Dealloc);
```

**Local body:** [`mach_zone_get_btlog_records`](../../../xnu/osfmk/kern/zalloc.c#L8652).
Calls visible in this body include `zone_foreach`, `snprintf`, `zone_heap_name`, `track_this_zone`, `btlog_get_records`, `vm_map_copyin`, `unused`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

### 235: mach_memory_info_redacted

**Interface contract:**

> Always returns the redacted version of the mach_memory_info output

**Mechanism:** Forces redaction even when a more powerful destination capability was supplied, converting it through the host interface. The common security check permits non-root redacted requests but can still require the memory-information entitlement. Sampling removes sensitive size information and combines same-sized typed-zone statistics before producing independent OOL output arrays. [mach_memory_info_redacted](../../../xnu/osfmk/kern/zalloc.c#L8227-L8370).

**Declarations:** [`mach_memory_info_redacted`](../../../xnu/osfmk/mach/mach_host.defs#L411) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_info_redacted(
  host : mach_port_t;
 out names : mach_zone_name_array_t,
     Dealloc;
 out info : mach_zone_info_array_t,
     Dealloc;
 out memory_info : mach_memory_info_array_t,
     Dealloc);
```

**Local body:** [`mach_memory_info_redacted`](../../../xnu/osfmk/kern/zalloc.c#L8227).
Calls visible in this body include `convert_port_to_host`, `mach_memory_info_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/zalloc.c#L8227-L8240):
<!-- source-excerpt: ../../../xnu/osfmk/kern/zalloc.c#L8227-L8240 -->
```c
mach_memory_info_redacted(
	mach_port_t             host_port,
	mach_zone_name_array_t  *namesp,
	mach_msg_type_number_t  *namesCntp,
	mach_zone_info_array_t  *infop,
	mach_msg_type_number_t  *infoCntp,
	mach_memory_info_array_t *memoryInfop,
	mach_msg_type_number_t   *memoryInfoCntp)
{
	bool redact_info = true;
	host_t host = convert_port_to_host(host_port);

	return mach_memory_info_internal(host, namesp, namesCntp, infop, infoCntp, memoryInfop, memoryInfoCntp, redact_info);
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
