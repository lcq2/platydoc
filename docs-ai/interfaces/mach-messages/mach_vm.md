# Mach messages: mach_vm

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_vm.defs](../../../xnu/osfmk/mach/mach_vm.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 4800: mach_vm_allocate_external

**Interface contract:**

> Allocate zero-filled memory in the address space of the target task, either at the specified address, or wherever space can be found (controlled by flags), of the specified size. The address at which the allocation actually took place is returned.

**Mechanism:** The receiver rejects flags outside `VM_FLAGS_USER_ALLOCATE`, then delegates to `mach_vm_allocate_kernel`. That helper validates the map and address/size, selects the placement range, and calls `vm_map_enter` with no backing object, default current protections, maximum `VM_PROT_ALL`, and default inheritance. This creates an anonymous mapping; physical pages can be supplied later by faults. Sanitization has a successful zero-size case that returns address zero; other failures leave allocation to the documented error path. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L144-L165), [allocation helper](../../../xnu/osfmk/vm/vm_kern.c#L1410-L1480).

**Declarations:** [`mach_vm_allocate_external`](../../../xnu/osfmk/mach/mach_vm.defs#L111) (`server64`, `server32`); [`_kernelrpc_mach_vm_allocate`](../../../xnu/osfmk/mach/mach_vm.defs#L111) (`client64`, `client32`); [`mach_vm_allocate`](../../../xnu/osfmk/mach/mach_vm.defs#L111) (`libsyscall64`, `sender64`); [`vm_allocate_external`](../../../xnu/osfmk/mach/mach_vm.defs#L122) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_allocate_external (
  target : vm_task_entry_t;
 inout address : mach_vm_address_t;
  size : mach_vm_size_t;
  flags : int);
```

**Local body:** [`mach_vm_allocate_external`](../../../xnu/osfmk/vm/vm_user.c#L144).
Calls visible in this body include `ktriage_record`, `thread_tid`, `current_thread`, `KDBG_TRIAGE_EVENTID`, `vm_map_kernel_flags_set_vmflags`, `mach_vm_allocate_kernel`.

**Local body:** [`vm_allocate_external`](../../../xnu/osfmk/vm/vm_user.c#L173).
Calls visible in this body include `mach_vm_allocate_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L173-L180):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L173-L180 -->
```c
vm_allocate_external(
	vm_map_t        map,
	vm_offset_ut   *addr,
	vm_size_ut      size,
	int             flags)
{
	return mach_vm_allocate_external(map, addr, size, flags);
}
```

### 4801: mach_vm_deallocate_external

**Interface contract:**

> Deallocate the specified range from the virtual address space of the target virtual memory map.

**Mechanism:** This removes mappings rather than directly freeing a userspace-supplied physical page. `mach_vm_deallocate_kernel` rejects a null map, sanitizes the address/size into a range, and invokes `vm_map_remove_guard` with no special removal flags and no kernel allocation guard. Removal must perform entry/object/pmap lifetime work; a VM object shared by another mapping can survive. The receiver itself does not implement a separate removal algorithm or translate failure into success. [Entry](../../../xnu/osfmk/vm/vm_user.c#L188-L194), [validated removal](../../../xnu/osfmk/vm/vm_kern.c#L1488-L1536).

**Declarations:** [`mach_vm_deallocate_external`](../../../xnu/osfmk/mach/mach_vm.defs#L138) (`server64`, `server32`); [`_kernelrpc_mach_vm_deallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L138) (`client64`, `client32`); [`mach_vm_deallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L138) (`libsyscall64`, `sender64`); [`vm_deallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L148) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_deallocate_external (
  target : vm_task_entry_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t);
```

**Local body:** [`mach_vm_deallocate_external`](../../../xnu/osfmk/vm/vm_user.c#L188).
Calls visible in this body include `mach_vm_deallocate_kernel`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L188-L194):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L188-L194 -->
```c
mach_vm_deallocate_external(
	vm_map_t                map,
	mach_vm_offset_ut       start_u,
	mach_vm_size_ut         size_u)
{
	return mach_vm_deallocate_kernel(map, start_u, size_u);
}
```

**Local body:** [`vm_deallocate`](../../../xnu/osfmk/vm/vm_user.c#L203).
Calls visible in this body include `mach_vm_deallocate_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L203-L209):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L203-L209 -->
```c
vm_deallocate(
	vm_map_t                map,
	vm_offset_ut            start,
	vm_size_ut              size)
{
	return mach_vm_deallocate_external(map, start, size);
}
```

**User wrapper:** [`vm_deallocate`](../../../xnu/libsyscall/mach/mach_vm.c#L135).
Calls visible in this body include `mach_vm_deallocate`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_vm.c#L135-L145):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_vm.c#L135-L145 -->
```c
vm_deallocate(
	mach_port_name_t task,
	vm_address_t address,
	vm_size_t size)
{
	kern_return_t rv;

	rv = mach_vm_deallocate(task, address, size);

	return rv;
}
```

### 4802: mach_vm_protect

**Interface contract:**

> Set the current or maximum protection attribute for the specified range of the virtual address space of the target virtual memory map. The current protection limits the memory access rights of threads within the map; the maximum protection limits the accesses that may be given in the current protection. Protections are specified as a set of {read, write, execute} *permissions*.

**Mechanism:** After rejecting a null map, the receiver treats zero size as success and passes a computed end plus the requested current/maximum mode to `vm_map_protect`. The lower layer sanitizes protections and ranges, applies map/entry policy, and coordinates protection changes with mapped translations. `VM_PROT_COPY` has a special copy-on-write remap path rather than being an ordinary hardware permission bit; execute/write policy can reject it with `KERN_PROTECTION_FAILURE`. Successful protection changes do not imply that pages were made resident. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L259-L279), [validation and COPY path](../../../xnu/osfmk/vm/vm_map.c#L5801-L5906).

**Declarations:** [`mach_vm_protect`](../../../xnu/osfmk/mach/mach_vm.defs#L167) (`server64`, `server32`, `libsyscall64`, `sender64`); [`_kernelrpc_mach_vm_protect`](../../../xnu/osfmk/mach/mach_vm.defs#L167) (`client64`, `client32`); [`vm_protect`](../../../xnu/osfmk/mach/mach_vm.defs#L181) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_protect (
  target_task : vm_task_entry_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  set_maximum : boolean_t;
  new_protection : vm_prot_t);
```

**Local body:** [`mach_vm_protect`](../../../xnu/osfmk/vm/vm_user.c#L259).
Calls visible in this body include `VM_SANITIZE_UNSAFE_IS_ZERO`, `vm_map_protect`, `vm_sanitize_compute_ut_end`.

**User wrapper:** [`mach_vm_protect`](../../../xnu/libsyscall/mach/mach_vm.c#L93).
Calls visible in this body include `_kernelrpc_mach_vm_protect_trap`, `_kernelrpc_mach_vm_protect`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_vm.c#L93-L111):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_vm.c#L93-L111 -->
```c
mach_vm_protect(
	mach_port_name_t task,
	mach_vm_address_t address,
	mach_vm_size_t size,
	boolean_t set_maximum,
	vm_prot_t new_protection)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_vm_protect_trap(task, address, size, set_maximum,
	    new_protection);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_vm_protect(task, address, size,
		    set_maximum, new_protection);
	}

	return rv;
}
```

**Local body:** [`vm_protect`](../../../xnu/osfmk/vm/vm_user.c#L289).
Calls visible in this body include `mach_vm_protect`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L289-L297):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L289-L297 -->
```c
vm_protect(
	vm_map_t                map,
	vm_offset_ut            start_u,
	vm_size_ut              size_u,
	boolean_t               set_maximum,
	vm_prot_ut              new_protection_u)
{
	return mach_vm_protect(map, start_u, size_u, set_maximum, new_protection_u);
}
```

**User wrapper:** [`vm_protect`](../../../xnu/libsyscall/mach/mach_vm.c#L148).
Calls visible in this body include `mach_vm_protect`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_vm.c#L148-L160):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_vm.c#L148-L160 -->
```c
vm_protect(
	mach_port_name_t task,
	vm_address_t address,
	vm_size_t size,
	boolean_t set_maximum,
	vm_prot_t new_protection)
{
	kern_return_t rv;

	rv = mach_vm_protect(task, address, size, set_maximum, new_protection);

	return rv;
}
```

### 4803: mach_vm_inherit

**Interface contract:**

> Set the inheritance attribute for the specified range of the virtual address space of the target address space. The inheritance value is one of {none, copy, share}, and specifies how the child address space should acquire this memory at the time of a task_create call.

**Mechanism:** The receiver validates the map, accepts a zero-size request, and calls `vm_map_inherit` with a computed range end. The helper sanitizes the inheritance value/range, clamps to map bounds, and installs entry-specific preflight checks before taking a streaming exclusive range lock. It updates inheritance on the entries it visits; an entirely unmapped range is explicitly normalized to success. The operation changes future fork inheritance policy, not an immediate copy of pages into a child task. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L217-L235), [entry walk](../../../xnu/osfmk/vm/vm_map.c#L6205-L6262).

**Declarations:** [`mach_vm_inherit`](../../../xnu/osfmk/mach/mach_vm.defs#L200) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_inherit`](../../../xnu/osfmk/mach/mach_vm.defs#L202) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_inherit(
  target_task : vm_task_entry_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  new_inheritance : vm_inherit_t);
```

**Local body:** [`mach_vm_inherit`](../../../xnu/osfmk/vm/vm_user.c#L217).
Calls visible in this body include `VM_SANITIZE_UNSAFE_IS_ZERO`, `vm_map_inherit`, `vm_sanitize_compute_ut_end`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L217-L235):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L217-L235 -->
```c
mach_vm_inherit(
	vm_map_t                map,
	mach_vm_offset_ut       start_u,
	mach_vm_size_ut         size_u,
	vm_inherit_ut           new_inheritance_u)
{
	if (map == VM_MAP_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	if (VM_SANITIZE_UNSAFE_IS_ZERO(size_u)) {
		return KERN_SUCCESS;
	}

	return vm_map_inherit(map,
	           start_u,
	           vm_sanitize_compute_ut_end(start_u, size_u),
	           new_inheritance_u);
}
```

**Local body:** [`vm_inherit`](../../../xnu/osfmk/vm/vm_user.c#L243).
Calls visible in this body include `mach_vm_inherit`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L243-L250):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L243-L250 -->
```c
vm_inherit(
	vm_map_t                map,
	vm_offset_ut            start_u,
	vm_size_ut              size_u,
	vm_inherit_ut           new_inheritance_u)
{
	return mach_vm_inherit(map, start_u, size_u, new_inheritance_u);
}
```

### 4804: mach_vm_read

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit reading.]

**Mechanism:** The receiver rejects a null map and sizes that cannot fit `mach_msg_type_number_t`, then calls `vm_map_copyin` without destroying the source. On success it returns a `vm_map_copy_t` and byte count to the MIG transport, not an already chosen destination address in the caller. Reply delivery performs the out-of-line copyout; a direct kernel caller must manage the copy representation itself. Range/protection/copy-on-write work belongs to VM copyin, so this is not a blind `memcpy` from another task. [Body and transport contract](../../../xnu/osfmk/vm/vm_user.c#L345-L389).

**Declarations:** [`mach_vm_read`](../../../xnu/osfmk/mach/mach_vm.defs#L217) (`server64`, `server32`, `libsyscall64`, `sender64`); [`_kernelrpc_mach_vm_read`](../../../xnu/osfmk/mach/mach_vm.defs#L217) (`client64`, `client32`); [`vm_read`](../../../xnu/osfmk/mach/mach_vm.defs#L219) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_read (
  target_task : vm_map_read_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
 out data : pointer_t);
```

**Local body:** [`mach_vm_read`](../../../xnu/osfmk/vm/vm_user.c#L358).
Calls visible in this body include `VM_SANITIZE_UNSAFE_FITS`, `vm_map_copyin`, `VM_SANITIZE_UT_SET`, `VM_SANITIZE_UNSAFE_UNWRAP`.

**User wrapper:** [`mach_vm_read`](../../../xnu/libsyscall/mach/mach_vm.c#L258).
Calls visible in this body include `_kernelrpc_mach_vm_read`, `__syscall_logger`, `mach_task_self`.

**Local body:** [`vm_read`](../../../xnu/osfmk/vm/vm_user.c#L402).
Calls visible in this body include `mach_vm_read`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L402-L410):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L402-L410 -->
```c
vm_read(
	vm_map_t                map,
	vm_address_ut           addr,
	vm_size_ut              size,
	pointer_ut             *data,
	mach_msg_type_number_t *data_size)
{
	return mach_vm_read(map, addr, size, data, data_size);
}
```

**User wrapper:** [`vm_read`](../../../xnu/libsyscall/mach/mach_vm.c#L367).
Calls visible in this body include `_kernelrpc_vm_read`, `__syscall_logger`, `mach_task_self`.

### 4805: mach_vm_read_list

**Interface contract:**

> List corrollary to vm_read, returns mapped contents of specified ranges within target address space.

**Mechanism:** The list operation bounds `count` by `VM_MAP_ENTRY_MAX` and manually copies each nonempty source range into the current task map because MIG does not return an array of VM-copy objects here. A failed copyout discards its copy; an empty or failed item is rewritten to address/size zero. Processing continues, preserving earlier successful mappings. The single returned `error` is overwritten by later attempted items, so it is not a first-error summary or an all-or-nothing transaction; inspect each result entry. [Loop and cleanup](../../../xnu/osfmk/vm/vm_user.c#L421-L465).

**Declarations:** [`mach_vm_read_list`](../../../xnu/osfmk/mach/mach_vm.defs#L231) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_read_list`](../../../xnu/osfmk/mach/mach_vm.defs#L233) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_read_list(
  target_task : vm_map_read_t;
 inout data_list : mach_vm_read_entry_t;
  count : natural_t);
```

**Local body:** [`mach_vm_read_list`](../../../xnu/osfmk/vm/vm_user.c#L421).
Calls visible in this body include `vm_map_copyin`, `vm_map_copyout`, `current_task`, `vm_map_copy_discard`.

**Local body:** [`vm_read_list`](../../../xnu/osfmk/vm/vm_user.c#L487).
Calls visible in this body include `vm_map_copyin`, `vm_map_copyout`, `current_task`, `CAST_DOWN`, `vm_map_copy_discard`.

### 4806: mach_vm_write

**Interface contract:**

> Writes the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit writing.]

**Mechanism:** The incoming data parameter is a VM-copy object constructed by the kernel MIG server from the sender's userspace buffer. After checking the destination map, the body unwraps that transport-created value and passes it to `vm_map_copy_overwrite` with the supplied byte count. It does not dereference the wire pointer as a raw kernel buffer or itself make a second source copy. MTE builds explicitly pass `sec_override=TRUE`; other protection/range decisions belong to the overwrite implementation and transport cleanup contract. [Body](../../../xnu/osfmk/vm/vm_user.c#L674-L698).

**Declarations:** [`mach_vm_write`](../../../xnu/osfmk/mach/mach_vm.defs#L247) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_write`](../../../xnu/osfmk/mach/mach_vm.defs#L249) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_write(
  target_task : vm_map_t;
  address : mach_vm_address_t;
  data : pointer_t);
```

**Local body:** [`mach_vm_write`](../../../xnu/osfmk/vm/vm_user.c#L674).
Calls visible in this body include `VM_SANITIZE_UNSAFE_UNWRAP`, `vm_map_copy_overwrite`.

**Local body:** [`vm_write`](../../../xnu/osfmk/vm/vm_user.c#L711).
Calls visible in this body include `mach_vm_write`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L711-L718):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L711-L718 -->
```c
vm_write(
	vm_map_t                map,
	vm_address_ut           address,
	pointer_ut              data,
	mach_msg_type_number_t  size)
{
	return mach_vm_write(map, address, data, size);
}
```

### 4807: mach_vm_copy

**Interface contract:**

> Copy the contents of the source range of the virtual address space of the target task to the destination range in that same address space. [Both of the ranges must be aligned on a virtual page boundary, and must be multiples of pages in extent. The protection on the source range must permit reading, and the protection on the destination range must permit writing.]

**Mechanism:** Both ranges belong to the specified map. The implementation first captures the source with nondestructive `vm_map_copyin`, checks the copy size when present, and then calls `vm_map_copy_overwrite` for the destination. A failed overwrite discards the retained copy; success consumes it through the overwrite path. Thus overlap and backing-object behavior are VM-copy operations rather than a driver or physical-address copy. A null map is rejected before either stage. [Two-stage operation and failure cleanup](../../../xnu/osfmk/vm/vm_user.c#L727-L761).

**Declarations:** [`mach_vm_copy`](../../../xnu/osfmk/mach/mach_vm.defs#L266) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_copy`](../../../xnu/osfmk/mach/mach_vm.defs#L268) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_copy(
  target_task : vm_map_t;
  source_address : mach_vm_address_t;
  size : mach_vm_size_t;
  dest_address : mach_vm_address_t);
```

**Local body:** [`mach_vm_copy`](../../../xnu/osfmk/vm/vm_user.c#L727).
Calls visible in this body include `vm_map_copyin`, `VM_SANITIZE_UNSAFE_IS_EQUAL`, `vm_map_copy_overwrite`, `vm_map_copy_discard`.

**Local body:** [`vm_copy`](../../../xnu/osfmk/vm/vm_user.c#L764).
Calls visible in this body include `mach_vm_copy`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L764-L771):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L764-L771 -->
```c
vm_copy(
	vm_map_t                map,
	vm_address_ut           source_address,
	vm_size_ut              size,
	vm_address_ut           dest_address)
{
	return mach_vm_copy(map, source_address, size, dest_address);
}
```

### 4808: mach_vm_read_overwrite

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [There are no alignment restrictions, and the results will overwrite the area pointed to by data - which must already exist. The protection on the specified range must permit reading.]

**Mechanism:** The source map supplies a nondestructive `vm_map_copyin`; the destination is an already specified address in `current_thread()->map`. `vm_map_copy_overwrite` applies that copy to the destination with interruption disabled for this call. Only success publishes the requested output byte count. If overwrite fails, this caller discards the remaining copy object. The separation between acquiring the copy and overwriting a destination is the important ownership boundary; the wrapper does not promise a general rollback of destination changes. [Complete entry body](../../../xnu/osfmk/vm/vm_user.c#L544-L580).

**Declarations:** [`mach_vm_read_overwrite`](../../../xnu/osfmk/mach/mach_vm.defs#L284) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_read_overwrite`](../../../xnu/osfmk/mach/mach_vm.defs#L286) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_read_overwrite(
  target_task : vm_map_read_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  data : mach_vm_address_t;
 out outsize : mach_vm_size_t);
```

**Local body:** [`mach_vm_read_overwrite`](../../../xnu/osfmk/vm/vm_user.c#L544).
Calls visible in this body include `vm_map_copyin`, `VM_SANITIZE_UNSAFE_IS_EQUAL`, `vm_map_copy_overwrite`, `current_thread`, `vm_map_copy_discard`.

**Local body:** [`vm_read_overwrite`](../../../xnu/osfmk/vm/vm_user.c#L595).
Calls visible in this body include `mach_vm_read_overwrite`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L595-L603):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L595-L603 -->
```c
vm_read_overwrite(
	vm_map_t                map,
	vm_address_ut           address,
	vm_size_ut              size,
	vm_address_ut           data,
	vm_size_ut             *data_size)
{
	return mach_vm_read_overwrite(map, address, size, data, data_size);
}
```

### 4809: mach_vm_msync

Request synchronization of the specified mapped range through vm_map_msync.

**Mechanism:** A null map returns `KERN_INVALID_TASK`; zero size succeeds. The map implementation rejects simultaneous synchronous/asynchronous flags, sanitizes the range, and uses a streaming range lock whose hole handling depends on CONTIGUOUS/KILLPAGES. Kill/deactivate requests operate on object pages. Ordinary sync skips absent, internal, private or pagerless objects; for an eligible external object it takes a reference, drops the streamed entry lock, calls `vm_object_sync`, and releases the reference. Success is not a universal storage-device durability guarantee. [Entry](../../../xnu/osfmk/vm/vm_user.c#L1208-L1223), [walk](../../../xnu/osfmk/vm/vm_map.c#L18955-L19165).

**Declarations:** [`mach_vm_msync`](../../../xnu/osfmk/mach/mach_vm.defs#L296) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_msync`](../../../xnu/osfmk/mach/mach_vm.defs#L298) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_msync(
  target_task : vm_map_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  sync_flags : vm_sync_t);
```

**Local body:** [`mach_vm_msync`](../../../xnu/osfmk/vm/vm_user.c#L1208).
Calls visible in this body include `VM_SANITIZE_UNSAFE_IS_ZERO`, `vm_map_msync`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1208-L1223):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1208-L1223 -->
```c
mach_vm_msync(
	vm_map_t                map,
	mach_vm_address_ut      address_u,
	mach_vm_size_ut         size_u,
	vm_sync_t               sync_flags)
{
	if (map == VM_MAP_NULL) {
		return KERN_INVALID_TASK;
	}

	if (VM_SANITIZE_UNSAFE_IS_ZERO(size_u)) {
		return KERN_SUCCESS;
	}

	return vm_map_msync(map, address_u, size_u, sync_flags);
}
```

**Local body:** [`vm_msync`](../../../xnu/osfmk/vm/vm_user.c#L1260).
Calls visible in this body include `mach_vm_msync`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1260-L1267):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1260-L1267 -->
```c
vm_msync(
	vm_map_t        map,
	vm_address_ut   address_u,
	vm_size_ut      size_u,
	vm_sync_t       sync_flags)
{
	return mach_vm_msync(map, address_u, size_u, sync_flags);
}
```

### 4810: mach_vm_behavior_set

**Interface contract:**

> Set the paging behavior attribute for the specified range of the virtual address space of the target task. The behavior value is one of {default, random, forward sequential, reverse sequential} and indicates the expected page reference pattern for the specified range.

**Mechanism:** The receiver sanitizes the range and behavior before dispatching. Persistent DEFAULT/RANDOM/SEQUENTIAL/REVERSE-SEQUENTIAL behaviors are recorded under an atomic exclusive range lock that excludes holes. ZERO_WIRED_PAGES additionally preflights write permission and disallows JIT/TPRO entries where configured. Other values initiate work immediately: WILLNEED requests paging, DONTNEED/FREE invoke msync deactivate/kill behavior, and REUSABLE/REUSE use their own page-accounting helpers. Consequently, this interface is not uniformly a harmless hint or a simple field assignment. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L1369-L1395), [behavior dispatch](../../../xnu/osfmk/vm/vm_map.c#L14589-L14695).

**Declarations:** [`mach_vm_behavior_set`](../../../xnu/osfmk/mach/mach_vm.defs#L313) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_behavior_set`](../../../xnu/osfmk/mach/mach_vm.defs#L315) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_behavior_set(
  target_task : vm_map_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  new_behavior : vm_behavior_t);
```

**Local body:** [`mach_vm_behavior_set`](../../../xnu/osfmk/vm/vm_user.c#L1369).
Calls visible in this body include `mach_vm_behavior_set_sanitize`, `vm_sanitize_get_kr`, `vm_map_behavior_set`.

**Local body:** [`vm_behavior_set`](../../../xnu/osfmk/vm/vm_user.c#L1411).
Calls visible in this body include `mach_vm_behavior_set`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1411-L1421):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1411-L1421 -->
```c
vm_behavior_set(
	vm_map_t                map,
	vm_offset_ut            start,
	vm_size_ut              size,
	vm_behavior_ut          new_behavior)
{
	return mach_vm_behavior_set(map,
	           start,
	           size,
	           new_behavior);
}
```

### 4811: mach_vm_map_external

**Interface contract:**

> Map a user-supplie memory object into the virtual address space of the target task. If desired (anywhere is TRUE), the kernel will find a suitable address range of the specified size; else, the specific address will be allocated. The beginning address of the range will be aligned on a virtual page boundary, be at or beyond the address specified, and meet the mask requirements (bits turned on in the mask must not be turned on in the result); the size of the range, in bytes, will be rounded up to an integral number of virtual pages. The memory in the resulting range will be associated with the specified memory object, with the beginning of the memory range referring to the specified offset into the memory object. The mapping will take the current and maximum protections and the inheritance attributes specified; see the vm_protect and vm_inherit calls for a description of these attributes. If desired (copy is TRUE), the memory range will be filled with a copy of the data from the memory object; this copy will be private to this mapping in this target task. Otherwise, the memory in this mapping will be shared with other mappings of the same memory object at the same offset (in this task or in other tasks). [The Mach kernel only enforces shared memory consistency among mappings on one host with similar page alignments. The user-defined memory manager for this object is responsible for further consistency.]

**Mechanism:** The external receiver first rejects kernel-only mapping flags, constructs `vm_map_kernel_flags_t`, and forwards all object/offset/copy/current/max/inheritance inputs to `mach_vm_map_kernel`. That helper enters `vm_map_enter_mem_object`, which interprets the supplied memory-entry/object capability and installs mappings subject to VM validation and placement policy. This full message interface can carry backing objects and protection/inheritance choices absent from the restricted current-task allocation trap. Returned addresses describe CPU virtual mappings; they are not DMA addresses. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L829-L855), [mapping handoff](../../../xnu/osfmk/vm/vm_kern.c#L2482-L2509).

**Declarations:** [`mach_vm_map_external`](../../../xnu/osfmk/mach/mach_vm.defs#L354) (`server64`, `server32`); [`_kernelrpc_mach_vm_map`](../../../xnu/osfmk/mach/mach_vm.defs#L354) (`client64`, `client32`); [`mach_vm_map`](../../../xnu/osfmk/mach/mach_vm.defs#L354) (`libsyscall64`, `sender64`); [`vm_map_external`](../../../xnu/osfmk/mach/mach_vm.defs#L356) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_map_external (
  target_task : vm_task_entry_t;
 inout address : mach_vm_address_t;
  size : mach_vm_size_t;
  mask : mach_vm_offset_t;
  flags : int;
  object : mem_entry_name_port_t;
  offset : memory_object_offset_t;
  copy : boolean_t;
  cur_protection : vm_prot_t;
  max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`mach_vm_map_external`](../../../xnu/osfmk/vm/vm_user.c#L829).
Calls visible in this body include `vm_map_kernel_flags_set_vmflags`, `mach_vm_map_kernel`.

**Local body:** [`vm_map_external`](../../../xnu/osfmk/vm/vm_user.c#L881).
Calls visible in this body include `mach_vm_map_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L881-L897):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L881-L897 -->
```c
vm_map_external(
	vm_map_t                target_map,
	vm_offset_ut           *address,
	vm_size_ut              size,
	vm_offset_ut            mask,
	int                     flags,
	ipc_port_t              port,
	vm_offset_ut            offset,
	boolean_t               copy,
	vm_prot_ut              cur_protection,
	vm_prot_ut              max_protection,
	vm_inherit_ut           inheritance)
{
	return mach_vm_map_external(target_map, address,
	           size, mask, flags, port, offset, copy,
	           cur_protection, max_protection, inheritance);
}
```

### 4812: mach_vm_machine_attribute

Request an architecture-specific mapping/cache attribute operation, subject to the local supported-result behavior.

**Mechanism:** A null map is invalid and zero size succeeds. The helper sanitizes the range, checks map bounds, and accepts only `MATTR_CACHE`; unsupported attributes deliberately return `KERN_INVALID_ADDRESS` for compatibility. It takes an atomic exclusive range lock to serialize pmap access, descends into constant submaps, and calls the per-entry machine-attribute operation only when an object exists. The loop continues even after an entry operation fails, so its final status is not transactional rollback across the range. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L305-L325), [helper](../../../xnu/osfmk/vm/vm_map.c#L14491-L14562).

**Declarations:** [`mach_vm_machine_attribute`](../../../xnu/osfmk/mach/mach_vm.defs#L376) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_machine_attribute`](../../../xnu/osfmk/mach/mach_vm.defs#L378) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_machine_attribute(
  target_task : vm_map_t;
  address : mach_vm_address_t;
  size : mach_vm_size_t;
  attribute : vm_machine_attribute_t;
 inout value : vm_machine_attribute_val_t);
```

**Local body:** [`mach_vm_machine_attribute`](../../../xnu/osfmk/vm/vm_user.c#L305).
Calls visible in this body include `VM_SANITIZE_UNSAFE_IS_ZERO`, `vm_map_machine_attribute`, `vm_sanitize_compute_ut_end`.

**Local body:** [`vm_machine_attribute`](../../../xnu/osfmk/vm/vm_user.c#L334).
Calls visible in this body include `mach_vm_machine_attribute`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L334-L342):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L334-L342 -->
```c
vm_machine_attribute(
	vm_map_t                map,
	vm_address_ut           addr_u,
	vm_size_ut              size_u,
	vm_machine_attribute_t  attribute,
	vm_machine_attribute_val_t *value) /* IN/OUT */
{
	return mach_vm_machine_attribute(map, addr_u, size_u, attribute, value);
}
```

### 4813: mach_vm_remap_external

**Interface contract:**

> Map portion of a task's address space.

**Mechanism:** The legacy remap receiver rejects flags outside `VM_FLAGS_USER_REMAP`, initializes both output protection values to NONE, and marks the request as legacy remap before calling `vm_map_remap`. The source is an already converted map capability. The underlying extraction/insertion path implements the copy-versus-share choice; protections returned to this legacy caller describe the resulting region rather than an input permission request. Unlike the newer interface, this wrapper does not force data-address offset preservation. [Legacy receiver](../../../xnu/osfmk/vm/vm_user.c#L1019-L1057), [map/COW mechanisms](../../subsystems/vm/virtual-address-maps.md).

**Declarations:** [`mach_vm_remap_external`](../../../xnu/osfmk/mach/mach_vm.defs#L390) (`server64`, `server32`); [`_kernelrpc_mach_vm_remap`](../../../xnu/osfmk/mach/mach_vm.defs#L390) (`client64`, `client32`); [`mach_vm_remap`](../../../xnu/osfmk/mach/mach_vm.defs#L390) (`libsyscall64`, `sender64`); [`vm_remap_external`](../../../xnu/osfmk/mach/mach_vm.defs#L392) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_remap_external (
  target_task : vm_map_t;
 inout target_address : mach_vm_address_t;
  size : mach_vm_size_t;
  mask : mach_vm_offset_t;
  flags : int;
  src_task : vm_map_t;
  src_address : mach_vm_address_t;
  copy : boolean_t;
 out cur_protection : vm_prot_t;
 out max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`mach_vm_remap_external`](../../../xnu/osfmk/vm/vm_user.c#L1019).
Calls visible in this body include `vm_map_kernel_flags_set_vmflags`, `vm_sanitize_wrap_prot`, `vm_map_remap`.

**Local body:** [`vm_remap_external`](../../../xnu/osfmk/vm/vm_user.c#L1095).
Calls visible in this body include `mach_vm_remap_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1095-L1111):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1095-L1111 -->
```c
vm_remap_external(
	vm_map_t                target_map,
	vm_offset_ut           *address,
	vm_size_ut              size,
	vm_offset_ut            mask,
	int                     flags,
	vm_map_t                src_map,
	vm_offset_ut            memory_address,
	boolean_t               copy,
	vm_prot_ut             *cur_protection,    /* OUT */
	vm_prot_ut             *max_protection,    /* OUT */
	vm_inherit_ut           inheritance)
{
	return mach_vm_remap_external(target_map, address,
	           size, mask, flags, src_map, memory_address, copy,
	           cur_protection, max_protection, inheritance);
}
```

### 4814: mach_vm_page_query

**Interface contract:**

> Give the caller information on the given location in a virtual address space. If a page is mapped return ref and dirty info.

**Mechanism:** The wrapper requests `VM_PAGE_INFO_BASIC` from `vm_map_page_info` and extracts only disposition and reference count. It sets both scalar outputs to zero if the helper fails, then returns that failure; zero outputs therefore do not establish that a page is valid and empty. The helper queries a one-byte interval expanded to the effective page boundary, rather than allocating/faulting a page for the caller. This is a state observation, not a retained page or mapping reference. [Wrapper](../../../xnu/osfmk/vm/vm_user.c#L1677-L1703), [query delegation](../../../xnu/osfmk/vm/vm_map.c#L18394-L18408).

**Declarations:** [`mach_vm_page_query`](../../../xnu/osfmk/mach/mach_vm.defs#L411) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_map_page_query`](../../../xnu/osfmk/mach/mach_vm.defs#L413) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_page_query(
  target_map : vm_map_read_t;
  offset : mach_vm_offset_t;
 out disposition : integer_t;
 out ref_count : integer_t);
```

**Local body:** [`mach_vm_page_query`](../../../xnu/osfmk/vm/vm_user.c#L1677).
Calls visible in this body include `vm_map_page_info`.

**Local body:** [`vm_map_page_query`](../../../xnu/osfmk/vm/vm_user.c#L1706).
Calls visible in this body include `mach_vm_page_query`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1706-L1713):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1706-L1713 -->
```c
vm_map_page_query(
	vm_map_t                map,
	vm_offset_ut            offset,
	int                    *disposition,
	int                    *ref_count)
{
	return mach_vm_page_query(map, offset, disposition, ref_count);
}
```

### 4815: mach_vm_region_recurse

Walk nested VM submaps and return the next region plus depth/flavor information.

**Mechanism:** This entry rejects a null map and passes the in/out address, size, nesting depth and record capacity to `vm_map_region_recurse_64`. The depth is part of the traversal contract: the operation can describe a submap or descend into its regions instead of treating the top-level entry as a leaf. It returns a snapshot record, not a retained map-entry object. Compatibility adapters may additionally narrow the address or translate the information layout, so their output and overflow behavior should be read separately. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L1534-L1548), [recursive helper](../../../xnu/osfmk/vm/vm_map.c#L13308).

**Declarations:** [`mach_vm_region_recurse`](../../../xnu/osfmk/mach/mach_vm.defs#L421) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_region_recurse_64`](../../../xnu/osfmk/mach/mach_vm.defs#L423) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_region_recurse(
  target_task : vm_map_read_t;
 inout address : mach_vm_address_t;
 out size : mach_vm_size_t;
 inout nesting_depth : natural_t;
 out info : vm_region_recurse_info_t,CountInOut);
```

**Local body:** [`mach_vm_region_recurse`](../../../xnu/osfmk/vm/vm_user.c#L1534).
Calls visible in this body include `vm_map_region_recurse_64`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1534-L1548):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1534-L1548 -->
```c
mach_vm_region_recurse(
	vm_map_t                map,
	mach_vm_address_ut     *address_u,
	mach_vm_size_ut        *size_u,
	uint32_t               *depth,
	vm_region_recurse_info_t info,
	mach_msg_type_number_t *infoCnt)
{
	if (VM_MAP_NULL == map) {
		return KERN_INVALID_ARGUMENT;
	}

	return vm_map_region_recurse_64(map, address_u, size_u, depth,
	           (vm_region_submap_info_64_t)info, infoCnt);
}
```

**Local body:** [`vm_region_recurse_64`](../../../xnu/osfmk/vm/vm_user.c#L1556).
Calls visible in this body include `mach_vm_region_recurse`, `vm_region_get_kern_return`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1556-L1570):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1556-L1570 -->
```c
vm_region_recurse_64(
	vm_map_t                map,
	vm_address_ut          *address_u,
	vm_size_ut             *size_u,
	uint32_t               *depth,
	vm_region_recurse_info_64_t info,
	mach_msg_type_number_t *infoCnt)
{
	kern_return_t kr;

	kr = mach_vm_region_recurse(map, address_u, size_u, depth,
	    (vm_region_recurse_info_t)info, infoCnt);

	return vm_region_get_kern_return(kr, *address_u, *size_u);
}
```

### 4816: mach_vm_region

Query VM region information using the compatibility VM address/flavor interface.

**Mechanism:** The wide entry converts the old BASIC flavor to BASIC_INFO_64 and delegates to `vm_map_region`. That routine validates flavor/count, resolves a region at or after the requested address under a find/range-lock context, and copies entry metadata such as permissions, inheritance, offset and extent. The basic branches explicitly return a null object-name port; the report is not a capability retaining the region. MTE-tagged address rejection and legacy end-of-address-space compatibility are implemented below the receiver. [Wrapper](../../../xnu/osfmk/vm/vm_user.c#L1438-L1458), [basic resolution](../../../xnu/osfmk/vm/vm_map.c#L13664-L13775).

**Declarations:** [`mach_vm_region`](../../../xnu/osfmk/mach/mach_vm.defs#L443) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`); [`vm_region_64`](../../../xnu/osfmk/mach/mach_vm.defs#L445) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_region(
  target_task : vm_map_read_t;
 inout address : mach_vm_address_t;
 out size : mach_vm_size_t;
  flavor : vm_region_flavor_t;
 out info : vm_region_info_t, CountInOut;
 out object_name : memory_object_name_t =
        MACH_MSG_TYPE_MOVE_SEND
        ctype: mach_port_t);
```

**Local body:** [`mach_vm_region`](../../../xnu/osfmk/vm/vm_user.c#L1438).
Calls visible in this body include `vm_map_region`.

**Local body:** [`vm_region_64`](../../../xnu/osfmk/vm/vm_user.c#L1489).
Calls visible in this body include `mach_vm_region`, `vm_region_get_kern_return`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1489-L1504):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1489-L1504 -->
```c
vm_region_64(
	vm_map_t                map,
	vm_offset_ut           *address_u,      /* IN/OUT */
	vm_size_ut             *size_u,         /* OUT */
	vm_region_flavor_t      flavor,         /* IN */
	vm_region_info_t        info,           /* OUT */
	mach_msg_type_number_t *count,          /* IN/OUT */
	mach_port_t            *object_name)    /* OUT */
{
	kern_return_t kr;

	kr = mach_vm_region(map, address_u, size_u, flavor, info, count,
	    object_name);

	return vm_region_get_kern_return(kr, *address_u, *size_u);
}
```

### 4817: _mach_make_memory_entry

Create a memory-entry capability for a map range with a wide offset/size representation.

**Mechanism:** The public variants converge on `mach_make_memory_entry_internal` with no trusted kernel flags. It sanitizes user permissions, rejects a copy-backed parent, then selects MEM_ONLY, new anonymous named object, VM-copy snapshot, sharing/reuse, or parent-relative derivation. These paths have different zero-size, alignment and protection checks. A named object is exposed through an `IKOT_NAMED_ENTRY` send right; a copy entry owns an entry-list copy, while a parent-derived entry cannot exceed its parent's allowed protections. Returned size can be adjusted for page/data offsets. [Dispatcher](../../../xnu/osfmk/vm/vm_memory_entry.c#L1188-L1285), [port creation](../../../xnu/osfmk/vm/vm_memory_entry.c#L1288-L1305).

**Declarations:** [`_mach_make_memory_entry`](../../../xnu/osfmk/mach/mach_vm.defs#L466) (`server64`, `server32`, `client32`, `libsyscall64`); [`mach_make_memory_entry`](../../../xnu/osfmk/mach/mach_vm.defs#L468) (`client64`, `sender64`); [`mach_make_memory_entry_64`](../../../xnu/osfmk/mach/mach_vm.defs#L471) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine _mach_make_memory_entry(
  target_task :vm_map_t;
 inout size :memory_object_size_t;
  offset :memory_object_offset_t;
  permission :vm_prot_t;
 out object_handle :mem_entry_name_port_move_send_t;
  parent_handle :mem_entry_name_port_t);
```

**Local body:** [`_mach_make_memory_entry`](../../../xnu/osfmk/vm/vm_memory_entry.c#L1259).
Calls visible in this body include `mach_make_memory_entry_64`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_memory_entry.c#L1259-L1269):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_memory_entry.c#L1259-L1269 -->
```c
_mach_make_memory_entry(
	vm_map_t                target_map,
	memory_object_size_ut  *size_u,
	memory_object_offset_ut offset_u,
	vm_prot_ut              permission_u,
	ipc_port_t              *object_handle,
	ipc_port_t              parent_entry)
{
	return mach_make_memory_entry_64(target_map, size_u,
	           offset_u, permission_u, object_handle, parent_entry);
}
```

**Local body:** [`mach_make_memory_entry_64`](../../../xnu/osfmk/vm/vm_memory_entry.c#L61).
Calls visible in this body include `mach_make_memory_entry_internal`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_memory_entry.c#L61-L76):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_memory_entry.c#L61-L76 -->
```c
mach_make_memory_entry_64(
	vm_map_t                target_map,
	memory_object_size_ut  *size_u,
	memory_object_offset_ut offset_u,
	vm_prot_ut              permission_u,
	ipc_port_t              *object_handle,
	ipc_port_t              parent_handle)
{
	return mach_make_memory_entry_internal(target_map,
	           size_u,
	           offset_u,
	           permission_u,
	           VM_NAMED_ENTRY_KERNEL_FLAGS_NONE,
	           object_handle,
	           parent_handle);
}
```

### 4818: mach_vm_purgable_control_external

**Interface contract:**

> Control behavior and investigate state of a "purgable" object in the virtual address space of the target task. A purgable object is created via a call to mach_vm_allocate() with VM_FLAGS_PURGABLE specified. See the routine implementation for a complete definition of the routine.

**Mechanism:** GET_STATE converts the destination capability with `convert_port_to_map_read`; mutations use map control. The wrapper always releases that converted map reference after calling the common control body. Userspace cannot select SET_STATE_FROM_KERNEL. The map helper validates states, requires an existing purgeable object, rejects submap addresses, and requires write permission for state changes; PURGE_ALL is a separate global purge branch. This object policy can discard contents, so changing volatility is distinct from removing the virtual mapping. [Capability selection](../../../xnu/osfmk/vm/vm_user.c#L1619-L1663), [object checks](../../../xnu/osfmk/vm/vm_map.c#L18078-L18175).

**Declarations:** [`mach_vm_purgable_control_external`](../../../xnu/osfmk/mach/mach_vm.defs#L488) (`server64`, `server32`); [`_kernelrpc_mach_vm_purgable_control`](../../../xnu/osfmk/mach/mach_vm.defs#L488) (`client64`, `client32`); [`mach_vm_purgable_control`](../../../xnu/osfmk/mach/mach_vm.defs#L488) (`libsyscall64`, `sender64`); [`vm_purgable_control_external`](../../../xnu/osfmk/mach/mach_vm.defs#L490) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_purgable_control_external (
  target_tport : mach_port_t;
  address : mach_vm_address_t;
  control : vm_purgable_t;
 inout state : int);
```

**Local body:** [`mach_vm_purgable_control_external`](../../../xnu/osfmk/vm/vm_user.c#L1644).
Calls visible in this body include `convert_port_to_map_read`, `convert_port_to_map`, `mach_vm_purgable_control`, `vm_map_deallocate`.

**Local body:** [`vm_purgable_control_external`](../../../xnu/osfmk/vm/vm_user.c#L1666).
Calls visible in this body include `mach_vm_purgable_control_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1666-L1673):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1666-L1673 -->
```c
vm_purgable_control_external(
	mach_port_t             target_tport,
	vm_offset_ut            address,
	vm_purgable_t           control,
	int                     *state)
{
	return mach_vm_purgable_control_external(target_tport, address, control, state);
}
```

### 4819: mach_vm_page_info

Query page-state information for a virtual address through the VM map.

**Mechanism:** After rejecting a null map, the receiver delegates the caller's flavor/count to `vm_map_page_info`. The lower helper expands an address-sized query to the effective page geometry and accepts BASIC count, including the historical one-word-short compatibility count; unknown flavors/counts fail. It returns disposition, object identity/offset, reference count and depth information through the supplied record. The query may consult mapping/object/footprint state; it does not pin the observed page against subsequent changes. [Entry](../../../xnu/osfmk/vm/vm_user.c#L1888-L1903), [count and page-size validation](../../../xnu/osfmk/vm/vm_map.c#L18485-L18564).

**Declarations:** [`mach_vm_page_info`](../../../xnu/osfmk/mach/mach_vm.defs#L503) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_page_info(
  target_task : vm_map_read_t;
  address : mach_vm_address_t;
  flavor : vm_page_info_flavor_t;
 out info : vm_page_info_t, CountInOut);
```

**Local body:** [`mach_vm_page_info`](../../../xnu/osfmk/vm/vm_user.c#L1888).
Calls visible in this body include `vm_map_page_info`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L1888-L1903):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L1888-L1903 -->
```c
mach_vm_page_info(
	vm_map_t                map,
	mach_vm_address_ut      address,
	vm_page_info_flavor_t   flavor,
	vm_page_info_t          info,
	mach_msg_type_number_t  *count)
{
	kern_return_t   kr;

	if (map == VM_MAP_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kr = vm_map_page_info(map, address, flavor, info, count);
	return kr;
}
```

### 4820: mach_vm_page_range_query

Validate the range and output capacity, collect per-page dispositions and copy the resulting array out.

**Mechanism:** This API writes disposition integers directly to a caller-supplied address. It checks output-count multiplication/address overflow and sanitizes the source range using the effective page size. It allocates bounded scratch arrays and queries at most `MAX_PAGE_RANGE_QUERY` bytes per iteration, stopping at output capacity or a copyout error. Earlier chunks can already be visible on failure. The reported count is advanced before checking that iteration's copyout status, so an error count is not proof that every counted integer reached userspace. Scratch buffers are freed on exit. [Complete path](../../../xnu/osfmk/vm/vm_user.c#L1716-L1885).

**Declarations:** [`mach_vm_page_range_query`](../../../xnu/osfmk/mach/mach_vm.defs#L513) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_page_range_query(
  target_map : vm_map_read_t;
  address : mach_vm_offset_t;
  size : mach_vm_size_t;
  dispositions : mach_vm_address_t;
 inout dispositions_count : mach_vm_size_t);
```

**Local body:** [`mach_vm_page_range_query`](../../../xnu/osfmk/vm/vm_user.c#L1762).
Calls visible in this body include `vm_self_region_page_shift_safely`, `mach_vm_page_range_query_sanitize`, `vm_sanitize_get_kr`, `MIN`, `kalloc_data`, `vm_map_page_range_info_internal`, `vm_map_round_page`, `copyout`, `VM_SANITIZE_UT_SET`, `kfree_data`.

### 4821: mach_vm_remap_new_external

Remap a source range using the newer remap semantics and return the resulting protections/address.

**Mechanism:** This receiver forces `VM_FLAGS_RETURN_DATA_ADDR`, validates in/out protections, and rejects maximum permissions containing both WRITE and EXECUTE. It converts the source port to a read map for copying or a maximum of exactly READ/NONE; other shared remaps require map control. It invokes `vm_map_remap`, releases the converted map reference on every return, and consumes the incoming source send right only on success. The output protections report what was actually installed, while the returned address preserves the source offset within a page. [Body](../../../xnu/osfmk/vm/vm_user.c#L929-L1006).

**Declarations:** [`mach_vm_remap_new_external`](../../../xnu/osfmk/mach/mach_vm.defs#L527) (`server64`, `server32`); [`_kernelrpc_mach_vm_remap_new`](../../../xnu/osfmk/mach/mach_vm.defs#L527) (`client64`, `client32`); [`mach_vm_remap_new`](../../../xnu/osfmk/mach/mach_vm.defs#L527) (`libsyscall64`, `sender64`); [`vm_remap_new_external`](../../../xnu/osfmk/mach/mach_vm.defs#L529) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_remap_new_external (
  target_task : vm_map_t;
 inout target_address : mach_vm_address_t;
  size : mach_vm_size_t;
  mask : mach_vm_offset_t;
  flags : int;
  src_tport : mach_port_t;
  src_address : mach_vm_address_t;
  copy : boolean_t;
 inout cur_protection : vm_prot_t;
 inout max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`mach_vm_remap_new_external`](../../../xnu/osfmk/vm/vm_user.c#L929).
Calls visible in this body include `vm_map_kernel_flags_set_vmflags`, `mach_vm_remap_new_external_sanitize`, `vm_sanitize_get_kr`, `convert_port_to_map_read`, `convert_port_to_map`, `vm_map_remap`, `vm_map_deallocate`, `ipc_port_release_send`.

**Local body:** [`vm_remap_new_external`](../../../xnu/osfmk/vm/vm_user.c#L1064).
Calls visible in this body include `mach_vm_remap_new_external`.

### 4822: mach_vm_deferred_reclamation_buffer_allocate

**Interface contract:**

> Mach VM deferred reclamation subsystem

**Mechanism:** With deferred reclamation enabled, allocation is limited to the current task and rejects simulated processes. The internal helper validates capacities/output pointers, global enablement and the maximum backing size, allocates a permanent tagged VM range, and verifies that initial busy/head/tail indices are zero. It publishes metadata under the global-buffer and task locks so termination sees the ring. This is ring metadata/backing allocation, not immediate reclamation of arbitrary user objects. Remote calls return `MACH_SEND_INVALID_DEST`; disabled builds return `KERN_NOT_SUPPORTED`. [Entry](../../../xnu/osfmk/vm/vm_user.c#L1953-L1978), [setup](../../../xnu/osfmk/vm/vm_reclaim.c#L347-L460).

**Declarations:** [`mach_vm_deferred_reclamation_buffer_allocate`](../../../xnu/osfmk/mach/mach_vm.defs#L552) (`server64`, `server32`, `client64`, `client32`, `sender64`).
**Reserved instead in:** `libsyscall64`, `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_deferred_reclamation_buffer_allocate(
  target_task : task_t;
 out address : mach_vm_address_t;
 out next_deadline : uint64_t;
  len : uint32_t;
  max_len : uint32_t);
```

**Local body:** [`mach_vm_deferred_reclamation_buffer_allocate`](../../../xnu/osfmk/vm/vm_user.c#L1953).
Calls visible in this body include `current_task`, `task_get_proc_raw`, `proc_is_simulated`, `vm_deferred_reclamation_buffer_allocate_internal`, `else`.

### 4823: mach_vm_deferred_reclamation_buffer_flush

Ask the current task's deferred-reclamation machinery to process its buffer.

**Mechanism:** The enabled wrapper requires the current task and both accounting outputs. The helper acquires and owns the task's ring metadata, reclaims bounded chunks until the requested count or stopping condition, and can relinquish/reacquire ownership after a qualifying lost race with userspace. It combines newly reclaimed bytes with outstanding kernel accounting, resets that counter, computes the next sample deadline, and releases ownership. Results describe incremental reclaim progress; errors do not undo already reclaimed entries. Disabled configurations return `KERN_NOT_SUPPORTED`. [Entry](../../../xnu/osfmk/vm/vm_user.c#L1981-L2009), [flush loop](../../../xnu/osfmk/vm/vm_reclaim.c#L1320-L1383).

**Declarations:** [`mach_vm_deferred_reclamation_buffer_flush`](../../../xnu/osfmk/mach/mach_vm.defs#L559) (`server64`, `server32`, `client64`, `client32`, `sender64`).
**Reserved instead in:** `libsyscall64`, `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_deferred_reclamation_buffer_flush(
  target_task : task_t;
  num_entries_to_reclaim : uint32_t;
 out bytes_reclaimed : uint64_t;
 out next_deadline : uint64_t);
```

**Local body:** [`mach_vm_deferred_reclamation_buffer_flush`](../../../xnu/osfmk/vm/vm_user.c#L1981).
Calls visible in this body include `current_task`, `vm_deferred_reclamation_buffer_flush_internal`, `else`.

### 4824: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/mach_vm.defs#L565).

### 4825: mach_vm_range_create

Validate a versioned range-recipe array and establish the requested map-range configuration.

**Mechanism:** Only the current map with user ranges enabled accepts recipes; zero byte size succeeds, and only integral V1 recipe arrays up to `VM_MAP_EXTRA_RANGES_MAX` are supported. The V1 helper sanitizes and sorts recipes, rejects flags, unsupported tags and overlap, then updates the extra-range table under the map interlock. Successful ranges receive fixed PROT_NONE placeholder mappings with their tags. This establishes placement policy and reserved ranges, not resident application data. Without `CONFIG_MAP_RANGES`, the entry returns `KERN_NOT_SUPPORTED`. [Validation/commit](../../../xnu/osfmk/vm/vm_user.c#L2178-L2368).

**Declarations:** [`mach_vm_range_create`](../../../xnu/osfmk/mach/mach_vm.defs#L573) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_range_create(
  target_task : vm_map_t;
  flavor : mach_vm_range_flavor_t;
  recipes : mach_vm_range_recipes_raw_t);
```

**Local body:** [`mach_vm_range_create`](../../../xnu/osfmk/vm/vm_user.c#L2320).
Calls visible in this body include `current_map`, `mach_vm_range_create_v1`.

**Local body:** [`mach_vm_range_create`](../../../xnu/osfmk/vm/vm_user.c#L2360).
Calls visible in this body include `unused`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L2360-L2368):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L2360-L2368 -->
```c
mach_vm_range_create(
	vm_map_t                map,
	mach_vm_range_flavor_t  flavor,
	mach_vm_range_recipes_raw_t recipe,
	natural_t               size)
{
#pragma unused(map, flavor, recipe, size)
	return KERN_NOT_SUPPORTED;
}
```

### 4826: mach_vm_deferred_reclamation_buffer_resize

Resize the current task's deferred-reclamation buffer through the configured implementation.

**Mechanism:** This is a current-task operation when deferred reclaim is configured. The helper validates a nonzero capacity that fits the ring's already allocated maximum range, then owns the metadata while draining old entries so old reclaim IDs cannot alias slots under the new capacity. The caller must also serialize its userspace threads. Success publishes the new logical capacity and accounting/deadline; failure can still report bytes reclaimed during the drain. It does not allocate a replacement range here. [Entry](../../../xnu/osfmk/vm/vm_user.c#L2012-L2039), [resize and cleanup](../../../xnu/osfmk/vm/vm_reclaim.c#L1386-L1484).

**Declarations:** [`mach_vm_deferred_reclamation_buffer_resize`](../../../xnu/osfmk/mach/mach_vm.defs#L582) (`server64`, `server32`, `client64`, `client32`, `sender64`).
**Reserved instead in:** `libsyscall64`, `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_deferred_reclamation_buffer_resize(
  target_task : task_t;
  new_len : uint32_t;
 out bytes_reclaimed : uint64_t;
 out next_deadline : uint64_t);
```

**Local body:** [`mach_vm_deferred_reclamation_buffer_resize`](../../../xnu/osfmk/vm/vm_user.c#L2012).
Calls visible in this body include `current_task`, `vm_deferred_reclamation_buffer_resize_internal`, `else`.

### 4827: mach_vm_update_pointers_with_remote_tags

Read remote allocation tags and update the supplied pointers under the map/debugging checks and MTE-specific path.

**Mechanism:** Input/output arrays must exist, counts must match and stay within `VM_OFFSET_LIST_MAX`, and the target needs a pmap. With `HAS_MTE`, the target address space must be debugged; the check reads its owning task under the map interlock. The implementation switches into that map, loads tags for each pointer, leaves a failed element unwritten, and switches back. Per-element failures do not fail the whole operation. Without MTE the validated call returns `KERN_FAILURE`, not fabricated tag data. [Body](../../../xnu/osfmk/vm/vm_user.c#L616-L666).

**Declarations:** [`mach_vm_update_pointers_with_remote_tags`](../../../xnu/osfmk/mach/mach_vm.defs#L592) (`server64`, `server32`, `libsyscall64`, `sender64`); [`_kernelrpc_mach_vm_update_pointers_with_remote_tags`](../../../xnu/osfmk/mach/mach_vm.defs#L592) (`client64`, `client32`).
**Reserved instead in:** `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_update_pointers_with_remote_tags (
   target : vm_map_t;
   in_pointer_list : mach_vm_offset_list_t;
   out out_pointer_list : mach_vm_offset_list_t, CountInOut);
```

**Local body:** [`mach_vm_update_pointers_with_remote_tags`](../../../xnu/osfmk/vm/vm_user.c#L616).
Calls visible in this body include `vm_map_ilk_lock`, `is_address_space_debugged`, `get_bsdtask_info`, `vm_map_ilk_unlock`, `vm_map_switch_to`, `copyin_mte_load_tag`, `vm_map_switch_back`.

**User wrapper:** [`mach_vm_update_pointers_with_remote_tags`](../../../xnu/libsyscall/mach/mach_vm.c#L420).
Calls visible in this body include `_kernelrpc_mach_vm_update_pointers_with_remote_tags`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_vm.c#L420-L428):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_vm.c#L420-L428 -->
```c
mach_vm_update_pointers_with_remote_tags(
	mach_port_name_t        target,
	mach_vm_offset_list_t in_pointer_list,
	mach_msg_type_number_t in_pointer_listCnt,
	mach_vm_offset_list_t out_pointer_list,
	mach_msg_type_number_t *out_pointer_listCnt)
{
	return _kernelrpc_mach_vm_update_pointers_with_remote_tags(target, in_pointer_list, in_pointer_listCnt, out_pointer_list, out_pointer_listCnt);
}
```

### 4828: mach_vm_deferred_reclamation_buffer_query

**Interface contract:**

> !defined(_MACH_VM_PUBLISH_AS_LOCAL_)

**Mechanism:** Unlike allocate/flush/resize, this wrapper has no explicit current-task restriction. The configured helper validates the task and output pointers, acquires its ring metadata, and reads ring address and reserved size under the metadata lock before dropping the reference. A task without a ring receives zero address and size with success. The result locates the existing reservation; it does not hand the caller ownership of the ring or guarantee that a later operation observes unchanged metadata. Disabled builds return `KERN_NOT_SUPPORTED`. [Entry](../../../xnu/osfmk/vm/vm_user.c#L2042-L2054), [query](../../../xnu/osfmk/vm/vm_reclaim.c#L2157-L2186).

**Declarations:** [`mach_vm_deferred_reclamation_buffer_query`](../../../xnu/osfmk/mach/mach_vm.defs#L601) (`server64`, `server32`, `client64`, `client32`, `sender64`).
**Reserved instead in:** `libsyscall64`, `local64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_deferred_reclamation_buffer_query(
  target : task_read_t;
  out addr : mach_vm_address_t;
  out size : mach_vm_size_t);
```

**Local body:** [`mach_vm_deferred_reclamation_buffer_query`](../../../xnu/osfmk/vm/vm_user.c#L2042).
Calls visible in this body include `vm_deferred_reclamation_buffer_query_internal`, `else`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L2042-L2054):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L2042-L2054 -->
```c
mach_vm_deferred_reclamation_buffer_query(task_t task,
    mach_vm_address_ut *addr_out_ut,
    mach_vm_size_ut *size_out_ut)
{
#if CONFIG_DEFERRED_RECLAIM
	return vm_deferred_reclamation_buffer_query_internal(task, addr_out_ut, size_out_ut);
#else /* CONFIG_DEFERRED_RECLAIM */
	(void) task;
	(void) addr_out_ut;
	(void) size_out_ut;
	return KERN_NOT_SUPPORTED;
#endif /* !CONFIG_DEFERRED_RECLAIM */
}
```

### 4829: mach_vm_reallocate

**Interface contract:**

> Relocate the pages of the source range of the specified map to a new range of the given size in bytes within the same map.

**Mechanism:** The receiver rejects a null map and forwards to `vm_map_reallocate`. Its sanitizer checks flag/option masks, nonzero page-aligned sizes, source alignment and fixed-destination alignment. The relocation implementation refuses non-native page-size maps, shrinking, and fixed-overwrite overlap with the source; equal-size aligned ANYWHERE requests can simply return the source address. Entry preflight excludes submaps, permanent mappings, JIT and configured MTE/TPRO cases. Sanitization or relocation failure clears the destination output rather than returning a stale proposed address. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L779-L794), [validation/relocation](../../../xnu/osfmk/vm/vm_map.c#L17326-L17535).

**Declarations:** [`mach_vm_reallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L614) (`server64`, `server32`, `libsyscall64`, `sender64`); [`_kernelrpc_mach_vm_reallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L614) (`client64`, `client32`); [`vm_reallocate`](../../../xnu/osfmk/mach/mach_vm.defs#L616) (`local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_reallocate (
   target_task : vm_map_t;
   src : mach_vm_address_t;
   src_size : mach_vm_size_t;
    inout dst : mach_vm_address_t;
     dst_size : mach_vm_size_t;
   align_mask : mach_vm_offset_t;
   options : int;
   flags : int);
```

**Local body:** [`mach_vm_reallocate`](../../../xnu/osfmk/vm/vm_user.c#L779).
Calls visible in this body include `vm_map_reallocate`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L779-L794):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L779-L794 -->
```c
mach_vm_reallocate(
	vm_map_t                map,
	mach_vm_address_ut      src,
	mach_vm_size_ut         src_size,
	mach_vm_address_ut     *dst_inout,
	mach_vm_size_ut         dst_size,
	mach_vm_offset_ut       align_mask,
	int                     options,
	int                     flags)
{
	if (map == VM_MAP_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return vm_map_reallocate(map, src, src_size, dst_inout, dst_size, align_mask, options, flags);
}
```

**User wrapper:** [`mach_vm_reallocate`](../../../xnu/libsyscall/mach/mach_vm.c#L732).
Calls visible in this body include `_kernelrpc_mach_vm_reallocate`, `__syscall_logger`.

**Local body:** [`vm_reallocate`](../../../xnu/osfmk/vm/vm_user.c#L797).
Calls visible in this body include `mach_vm_reallocate`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_user.c#L797-L815):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_user.c#L797-L815 -->
```c
vm_reallocate(
	vm_map_t                map,
	vm_address_ut           src,
	vm_size_ut              src_size,
	vm_address_ut          *dst_inout,
	vm_size_ut              dst_size,
	vm_offset_ut            align_mask,
	int                     options,
	int                     flags)
{
	kern_return_t kr;
	mach_vm_address_ut dst_inout_mach;

	dst_inout_mach = (mach_vm_address_ut)(*dst_inout);
	kr = mach_vm_reallocate(map, src, src_size, &dst_inout_mach, dst_size, align_mask, options, flags);
	*dst_inout = (vm_address_ut) dst_inout_mach;

	return kr;
}
```

**User wrapper:** [`vm_reallocate`](../../../xnu/libsyscall/mach/mach_vm.c#L754).
Calls visible in this body include `mach_vm_reallocate`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
