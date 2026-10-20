# Mach messages: vm32_map

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/vm32_map.defs](../../../xnu/osfmk/mach/vm32_map.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3800: vm32_vm_region

**Interface contract:**

> See vm_map.defs for more information

**Mechanism:** This form widens input address/size, calls `vm_map_region` with the original information flavor, narrows outputs, and then rejects a successful result whose untruncated end exceeds `VM32_MAX_ADDRESS`. The result-field assignments precede the final error decision. This explicit end check distinguishes it from vm32_vm_region_64; do not assume identical overflow behavior based on similar names. [Wrapper and end check](../../../xnu/osfmk/vm/vm32_user.c#L437-L502).

**Declarations:** [`vm32_vm_region`](../../../xnu/osfmk/mach/vm32_map.defs#L85) (`server64`, `server32`, `local64`); [`vm_region`](../../../xnu/osfmk/mach/vm32_map.defs#L85) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_region(
                target_task : vm_map_read_t;
 inout address : vm32_address_t;
        out size : vm32_size_t;
  flavor : vm_region_flavor_t;
 out info : vm_region_info_t, CountInOut;
        out object_name : memory_object_name_t =
                                        MACH_MSG_TYPE_MOVE_SEND
                                        ctype: mach_port_t);
```

**Local body:** [`vm32_vm_region`](../../../xnu/osfmk/vm/vm32_user.c#L476).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `vm_map_region`, `vm_sanitize_trunc_addr_to_32`, `vm_sanitize_trunc_size_to_32`, `vm32_region_get_kern_return`.

### 3801: vm32_vm_allocate

**Interface contract:**

> Allocate zero-filled memory in the address space of the target task, either at the specified address, or wherever space can be found (controlled by flags), of the specified size. The address at which the allocation actually took place is returned.

**Mechanism:** The vm32 receiver expands the 32-bit hint and size into sanitized 64-bit wrapper types, invokes `mach_vm_allocate_external`, and truncates the address result back to the vm32 ABI before returning the status. Placement and allocation failures remain decisions of the wide allocator; this adapter does not independently reserve a low-address arena or prove the returned address fits by a separate test. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L109-L125). The receiver rejects flags outside `VM_FLAGS_USER_ALLOCATE`, then delegates to `mach_vm_allocate_kernel`. That helper validates the map and address/size, selects the placement range, and calls `vm_map_enter` with no backing object, default current protections, maximum `VM_PROT_ALL`, and default inheritance. This creates an anonymous mapping; physical pages can be supplied later by faults. Sanitization has a successful zero-size case that returns address zero; other failures leave allocation to the documented error path. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L144-L165), [allocation helper](../../../xnu/osfmk/vm/vm_kern.c#L1410-L1480).

**Declarations:** [`vm32_vm_allocate`](../../../xnu/osfmk/mach/vm32_map.defs#L95) (`server64`, `server32`, `local64`); [`vm_allocate`](../../../xnu/osfmk/mach/vm32_map.defs#L95) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_allocate(
  target_task : vm_task_entry_t;
 inout address : vm32_address_t;
  size : vm32_size_t;
  flags : int);
```

**Local body:** [`vm32_vm_allocate`](../../../xnu/osfmk/vm/vm32_user.c#L109).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_allocate_external`, `vm_sanitize_trunc_addr_to_32`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L109-L125):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L109-L125 -->
```c
vm32_vm_allocate(
	vm_map_t                map,
	vm32_address_ut        *addr32,
	vm32_size_ut            size32,
	int                     flags)
{
	mach_vm_address_ut      addr;
	mach_vm_size_ut         size;
	kern_return_t           kr;

	addr    = vm_sanitize_expand_addr_to_64(*addr32);
	size    = vm_sanitize_expand_size_to_64(size32);
	kr      = mach_vm_allocate_external(map, &addr, size, flags);
	*addr32 = vm_sanitize_trunc_addr_to_32(addr);

	return kr;
}
```

### 3802: vm32_vm_deallocate

**Interface contract:**

> Deallocate the specified range from the virtual address space of the target virtual memory map.

**Mechanism:** This vm32 adapter checks addition overflow in the original 32-bit start/size representation before widening them. Overflow returns `KERN_INVALID_ARGUMENT`; the wide `mach_vm_deallocate_external` implementation performs the remaining range and operation-specific checks. This prevents a wrapped 32-bit end from becoming an apparently valid wider interval. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L128-L145). This removes mappings rather than directly freeing a userspace-supplied physical page. `mach_vm_deallocate_kernel` rejects a null map, sanitizes the address/size into a range, and invokes `vm_map_remove_guard` with no special removal flags and no kernel allocation guard. Removal must perform entry/object/pmap lifetime work; a VM object shared by another mapping can survive. The receiver itself does not implement a separate removal algorithm or translate failure into success. [Entry](../../../xnu/osfmk/vm/vm_user.c#L188-L194), [validated removal](../../../xnu/osfmk/vm/vm_kern.c#L1488-L1536).

**Declarations:** [`vm32_vm_deallocate`](../../../xnu/osfmk/mach/vm32_map.defs#L101) (`server64`, `server32`, `local64`); [`vm_deallocate`](../../../xnu/osfmk/mach/vm32_map.defs#L101) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_deallocate(
  target_task : vm_task_entry_t;
  address : vm32_address_t;
  size : vm32_size_t);
```

**Local body:** [`vm32_vm_deallocate`](../../../xnu/osfmk/vm/vm32_user.c#L128).
Calls visible in this body include `vm_sanitize_add_overflow`, `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_deallocate_external`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L128-L145):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L128-L145 -->
```c
vm32_vm_deallocate(
	vm_map_t                map,
	vm32_offset_ut          start32,
	vm32_size_ut            size32)
{
	mach_vm_offset_ut start;
	mach_vm_size_ut   size;
	vm32_address_ut   discard;

	if (vm_sanitize_add_overflow(start32, size32, &discard)) {
		return KERN_INVALID_ARGUMENT;
	}

	start = vm_sanitize_expand_addr_to_64(start32);
	size = vm_sanitize_expand_size_to_64(size32);

	return mach_vm_deallocate_external(map, start, size);
}
```

### 3803: vm32_vm_protect

**Interface contract:**

> Set the current or maximum protection attribute for the specified range of the virtual address space of the target virtual memory map. The current protection limits the memory access rights of threads within the map; the maximum protection limits the accesses that may be given in the current protection. Protections are specified as a set of {read, write, execute} *permissions*.

**Mechanism:** This vm32 adapter checks addition overflow in the original 32-bit start/size representation before widening them. Overflow returns `KERN_INVALID_ARGUMENT`; the wide `mach_vm_protect` implementation performs the remaining range and operation-specific checks. This prevents a wrapped 32-bit end from becoming an apparently valid wider interval. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L173-L196). After rejecting a null map, the receiver treats zero size as success and passes a computed end plus the requested current/maximum mode to `vm_map_protect`. The lower layer sanitizes protections and ranges, applies map/entry policy, and coordinates protection changes with mapped translations. `VM_PROT_COPY` has a special copy-on-write remap path rather than being an ordinary hardware permission bit; execute/write policy can reject it with `KERN_PROTECTION_FAILURE`. Successful protection changes do not imply that pages were made resident. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L259-L279), [validation and COPY path](../../../xnu/osfmk/vm/vm_map.c#L5801-L5906).

**Declarations:** [`vm32_vm_protect`](../../../xnu/osfmk/mach/vm32_map.defs#L106) (`server64`, `server32`, `local64`); [`vm_protect`](../../../xnu/osfmk/mach/vm32_map.defs#L106) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_protect(
  target_task : vm_task_entry_t;
  address : vm32_address_t;
  size : vm32_size_t;
  set_maximum : boolean_t;
  new_protection : vm_prot_t);
```

**Local body:** [`vm32_vm_protect`](../../../xnu/osfmk/vm/vm32_user.c#L173).
Calls visible in this body include `vm_sanitize_add_overflow`, `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_protect`.

### 3804: vm32_vm_inherit

**Interface contract:**

> Set the inheritance attribute for the specified range of the virtual address space of the target task. The inheritance value is one of {none, copy, share}, and specifies how the child address space should acquire this memory at the time of a task_create call.

**Mechanism:** This vm32 adapter checks addition overflow in the original 32-bit start/size representation before widening them. Overflow returns `KERN_INVALID_ARGUMENT`; the wide `mach_vm_inherit` implementation performs the remaining range and operation-specific checks. This prevents a wrapped 32-bit end from becoming an apparently valid wider interval. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L148-L170). The receiver validates the map, accepts a zero-size request, and calls `vm_map_inherit` with a computed range end. The helper sanitizes the inheritance value/range, clamps to map bounds, and installs entry-specific preflight checks before taking a streaming exclusive range lock. It updates inheritance on the entries it visits; an entirely unmapped range is explicitly normalized to success. The operation changes future fork inheritance policy, not an immediate copy of pages into a child task. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L217-L235), [entry walk](../../../xnu/osfmk/vm/vm_map.c#L6205-L6262).

**Declarations:** [`vm32_vm_inherit`](../../../xnu/osfmk/mach/vm32_map.defs#L113) (`server64`, `server32`, `local64`); [`vm_inherit`](../../../xnu/osfmk/mach/vm32_map.defs#L113) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_inherit(
  target_task : vm_task_entry_t;
  address : vm32_address_t;
  size : vm32_size_t;
  new_inheritance : vm_inherit_t);
```

**Local body:** [`vm32_vm_inherit`](../../../xnu/osfmk/vm/vm32_user.c#L148).
Calls visible in this body include `vm_sanitize_add_overflow`, `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_inherit`.

### 3805: vm32_vm_read

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit reading.]

**Mechanism:** This receiver expands the vm32 address/size fields used by the operation and calls `mach_vm_read`. It does not supply the explicit start-plus-size overflow branch present in several other vm32 wrappers; the wide VM operation remains responsible for its range validation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L222-L236). The receiver rejects a null map and sizes that cannot fit `mach_msg_type_number_t`, then calls `vm_map_copyin` without destroying the source. On success it returns a `vm_map_copy_t` and byte count to the MIG transport, not an already chosen destination address in the caller. Reply delivery performs the out-of-line copyout; a direct kernel caller must manage the copy representation itself. Range/protection/copy-on-write work belongs to VM copyin, so this is not a blind `memcpy` from another task. [Body and transport contract](../../../xnu/osfmk/vm/vm_user.c#L345-L389).

**Declarations:** [`vm32_vm_read`](../../../xnu/osfmk/mach/vm32_map.defs#L119) (`server64`, `server32`, `local64`); [`vm_read`](../../../xnu/osfmk/mach/vm32_map.defs#L119) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_read(
  target_task : vm_map_read_t;
  address : vm32_address_t;
  size : vm32_size_t;
 out data : pointer_t);
```

**Local body:** [`vm32_vm_read`](../../../xnu/osfmk/vm/vm32_user.c#L222).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_read`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L222-L236):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L222-L236 -->
```c
vm32_vm_read(
	vm_map_t                map,
	vm32_address_ut         addr32,
	vm32_size_ut            size32,
	pointer_ut             *data,
	mach_msg_type_number_t *data_size)
{
	mach_vm_offset_ut addr;
	mach_vm_size_ut   size;

	addr = vm_sanitize_expand_addr_to_64(addr32);
	size = vm_sanitize_expand_size_to_64(size32);

	return mach_vm_read(map, addr, size, data, data_size);
}
```

### 3806: vm32_vm_read_list

**Interface contract:**

> List corrollary to vm_read, returns mapped contents of specified ranges within target address space.

**Mechanism:** The adapter copies every element of the fixed `VM_MAP_ENTRY_MAX` array into a wide temporary, calls `mach_vm_read_list` with the supplied count, then casts every result element back to vm32 address/size. The wide routine validates count and processes requested entries independently; successful items stay mapped even when another item fails. This wrapper's result conversion runs before returning the wide status and is not proof that all items succeeded. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L239-L261), [per-item semantics](../../../xnu/osfmk/vm/vm_user.c#L421-L465).

**Declarations:** [`vm32_vm_read_list`](../../../xnu/osfmk/mach/vm32_map.defs#L125) (`server64`, `server32`, `local64`); [`vm_read_list`](../../../xnu/osfmk/mach/vm32_map.defs#L125) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_read_list(
  target_task : vm_map_read_t;
 inout data_list : vm32_read_entry_t;
  count : natural_t);
```

**Local body:** [`vm32_vm_read_list`](../../../xnu/osfmk/vm/vm32_user.c#L239).
Calls visible in this body include `mach_vm_read_list`, `CAST_DOWN_EXPLICIT`.

### 3807: vm32_vm_write

**Interface contract:**

> Writes the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit writing.]

**Mechanism:** This receiver expands the vm32 address/size fields used by the operation and calls `mach_vm_write`. It does not supply the explicit start-plus-size overflow branch present in several other vm32 wrappers; the wide VM operation remains responsible for its range validation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L287-L297). The incoming data parameter is a VM-copy object constructed by the kernel MIG server from the sender's userspace buffer. After checking the destination map, the body unwraps that transport-created value and passes it to `vm_map_copy_overwrite` with the supplied byte count. It does not dereference the wire pointer as a raw kernel buffer or itself make a second source copy. MTE builds explicitly pass `sec_override=TRUE`; other protection/range decisions belong to the overwrite implementation and transport cleanup contract. [Body](../../../xnu/osfmk/vm/vm_user.c#L674-L698).

**Declarations:** [`vm32_vm_write`](../../../xnu/osfmk/mach/vm32_map.defs#L130) (`server64`, `server32`, `local64`); [`vm_write`](../../../xnu/osfmk/mach/vm32_map.defs#L130) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_write(
  target_task : vm_map_t;
  address : vm32_address_t;
  data : pointer_t);
```

**Local body:** [`vm32_vm_write`](../../../xnu/osfmk/vm/vm32_user.c#L287).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `mach_vm_write`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L287-L297):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L287-L297 -->
```c
vm32_vm_write(
	vm_map_t                map,
	vm32_address_ut         addr32,
	pointer_ut              data,
	mach_msg_type_number_t  size)
{
	mach_vm_offset_ut addr;

	addr = vm_sanitize_expand_addr_to_64(addr32);
	return mach_vm_write(map, addr, data, size);
}
```

### 3808: vm32_vm_copy

**Interface contract:**

> Copy the contents of the source range of the virtual address space of the target task to the destination range in that same address space. [Both of the ranges must be aligned on a virtual page boundary, and must be multiples of pages in extent. The protection on the source range must permit reading, and the protection on the destination range must permit writing.]

**Mechanism:** This receiver expands the vm32 address/size fields used by the operation and calls `mach_vm_copy`. It does not supply the explicit start-plus-size overflow branch present in several other vm32 wrappers; the wide VM operation remains responsible for its range validation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L300-L314). Both ranges belong to the specified map. The implementation first captures the source with nondestructive `vm_map_copyin`, checks the copy size when present, and then calls `vm_map_copy_overwrite` for the destination. A failed overwrite discards the retained copy; success consumes it through the overwrite path. Thus overlap and backing-object behavior are VM-copy operations rather than a driver or physical-address copy. A null map is rejected before either stage. [Two-stage operation and failure cleanup](../../../xnu/osfmk/vm/vm_user.c#L727-L761).

**Declarations:** [`vm32_vm_copy`](../../../xnu/osfmk/mach/vm32_map.defs#L135) (`server64`, `server32`, `local64`); [`vm_copy`](../../../xnu/osfmk/mach/vm32_map.defs#L135) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_copy(
  target_task : vm_map_t;
  source_address : vm32_address_t;
  size : vm32_size_t;
  dest_address : vm32_address_t);
```

**Local body:** [`vm32_vm_copy`](../../../xnu/osfmk/vm/vm32_user.c#L300).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_copy`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L300-L314):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L300-L314 -->
```c
vm32_vm_copy(
	vm_map_t                map,
	vm32_address_ut         src_addr32,
	vm32_size_ut            size32,
	vm32_address_ut         dst_addr32)
{
	mach_vm_offset_ut src_addr, dst_addr;
	mach_vm_size_ut   size;

	src_addr = vm_sanitize_expand_addr_to_64(src_addr32);
	size     = vm_sanitize_expand_size_to_64(size32);
	dst_addr = vm_sanitize_expand_addr_to_64(dst_addr32);

	return mach_vm_copy(map, src_addr, size, dst_addr);
}
```

### 3809: vm32_vm_read_overwrite

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [There are no alignment restrictions, and the results will overwrite the area pointed to by data - which must already exist. The protection on the specified range must permit reading.]

**Mechanism:** Source address, size, destination and initial output-size temporary are widened, then the adapter calls `mach_vm_read_overwrite` and truncates its size result back. The source copy is applied to the caller's current map, not the source task's map. Only the wide helper's success publishes a completed byte count; errors preserve its copy-discard contract and are returned unchanged by this adapter. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L264-L284), [copy/overwrite cleanup](../../../xnu/osfmk/vm/vm_user.c#L544-L580).

**Declarations:** [`vm32_vm_read_overwrite`](../../../xnu/osfmk/mach/vm32_map.defs#L141) (`server64`, `server32`, `local64`); [`vm_read_overwrite`](../../../xnu/osfmk/mach/vm32_map.defs#L141) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_read_overwrite(
  target_task : vm_map_read_t;
  address : vm32_address_t;
  size : vm32_size_t;
  data : vm32_address_t;
 out outsize : vm32_size_t);
```

**Local body:** [`vm32_vm_read_overwrite`](../../../xnu/osfmk/vm/vm32_user.c#L264).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_read_overwrite`, `vm_sanitize_trunc_size_to_32`.

### 3810: vm32_vm_msync

Request synchronization of the specified mapped range through vm_map_msync.

**Mechanism:** This receiver expands the vm32 address/size fields used by the operation and calls `mach_vm_msync`. It does not supply the explicit start-plus-size overflow branch present in several other vm32 wrappers; the wide VM operation remains responsible for its range validation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L401-L413). A null map returns `KERN_INVALID_TASK`; zero size succeeds. The map implementation rejects simultaneous synchronous/asynchronous flags, sanitizes the range, and uses a streaming range lock whose hole handling depends on CONTIGUOUS/KILLPAGES. Kill/deactivate requests operate on object pages. Ordinary sync skips absent, internal, private or pagerless objects; for an eligible external object it takes a reference, drops the streamed entry lock, calls `vm_object_sync`, and releases the reference. Success is not a universal storage-device durability guarantee. [Entry](../../../xnu/osfmk/vm/vm_user.c#L1208-L1223), [walk](../../../xnu/osfmk/vm/vm_map.c#L18955-L19165).

**Declarations:** [`vm32_vm_msync`](../../../xnu/osfmk/mach/vm32_map.defs#L149) (`server64`, `server32`, `local64`); [`vm_msync`](../../../xnu/osfmk/mach/vm32_map.defs#L149) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_msync(
  target_task : vm_map_t;
  address : vm32_address_t;
  size : vm32_size_t;
  sync_flags : vm_sync_t);
```

**Local body:** [`vm32_vm_msync`](../../../xnu/osfmk/vm/vm32_user.c#L401).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_msync`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L401-L413):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L401-L413 -->
```c
vm32_vm_msync(
	vm_map_t                map,
	vm32_address_ut         addr32,
	vm32_size_ut            size32,
	vm_sync_t               sync_flags)
{
	mach_vm_offset_ut addr;
	mach_vm_size_ut   size;

	addr = vm_sanitize_expand_addr_to_64(addr32);
	size = vm_sanitize_expand_size_to_64(size32);
	return mach_vm_msync(map, addr, size, sync_flags);
}
```

### 3811: vm32_vm_behavior_set

**Interface contract:**

> Set the paging behavior attribute for the specified range of the virtual address space of the target task. The behavior value is one of {default, random, forward sequential, reverse sequential} and indicates the expected page reference pattern for the specified range.

**Mechanism:** This vm32 adapter checks addition overflow in the original 32-bit start/size representation before widening them. Overflow returns `KERN_INVALID_ARGUMENT`; the wide `mach_vm_behavior_set` implementation performs the remaining range and operation-specific checks. This prevents a wrapped 32-bit end from becoming an apparently valid wider interval. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L416-L434). The receiver sanitizes the range and behavior before dispatching. Persistent DEFAULT/RANDOM/SEQUENTIAL/REVERSE-SEQUENTIAL behaviors are recorded under an atomic exclusive range lock that excludes holes. ZERO_WIRED_PAGES additionally preflights write permission and disallows JIT/TPRO entries where configured. Other values initiate work immediately: WILLNEED requests paging, DONTNEED/FREE invoke msync deactivate/kill behavior, and REUSABLE/REUSE use their own page-accounting helpers. Consequently, this interface is not uniformly a harmless hint or a simple field assignment. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L1369-L1395), [behavior dispatch](../../../xnu/osfmk/vm/vm_map.c#L14589-L14695).

**Declarations:** [`vm32_vm_behavior_set`](../../../xnu/osfmk/mach/vm32_map.defs#L155) (`server64`, `server32`, `local64`); [`vm_behavior_set`](../../../xnu/osfmk/mach/vm32_map.defs#L155) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_behavior_set(
  target_task : vm_map_t;
  address : vm32_address_t;
  size : vm32_size_t;
  new_behavior : vm_behavior_t);
```

**Local body:** [`vm32_vm_behavior_set`](../../../xnu/osfmk/vm/vm32_user.c#L416).
Calls visible in this body include `vm_sanitize_add_overflow`, `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_behavior_set`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L416-L434):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L416-L434 -->
```c
vm32_vm_behavior_set(
	vm_map_t                map,
	vm32_offset_ut           start32,
	vm32_size_ut             size32,
	vm_behavior_ut           new_behavior)
{
	vm_address_ut     start;
	vm_size_ut        size;
	vm32_address_ut   discard;

	if (vm_sanitize_add_overflow(start32, size32, &discard)) {
		return KERN_INVALID_ARGUMENT;
	}

	start = vm_sanitize_expand_addr_to_64(start32);
	size = vm_sanitize_expand_size_to_64(size32);

	return mach_vm_behavior_set(map, start, size, new_behavior);
}
```

### 3812: vm32_vm_map

**Interface contract:**

> Map a user-defined memory object into the virtual address space of the target task. If desired (anywhere is TRUE), the kernel will find a suitable address range of the specified size; else, the specific address will be allocated. The beginning address of the range will be aligned on a virtual page boundary, be at or beyond the address specified, and meet the mask requirements (bits turned on in the mask must not be turned on in the result); the size of the range, in bytes, will be rounded up to an integral number of virtual pages. The memory in the resulting range will be associated with the specified memory object, with the beginning of the memory range referring to the specified offset into the memory object. The mapping will take the current and maximum protections and the inheritance attributes specified; see the vm_protect and vm_inherit calls for a description of these attributes. If desired (copy is TRUE), the memory range will be filled with a copy of the data from the memory object; this copy will be private to this mapping in this target task. Otherwise, the memory in this mapping will be shared with other mappings of the same memory object at the same offset (in this task or in other tasks). [The Mach kernel only enforces shared memory consistency among mappings on one host with similar page alignments. The user-defined memory manager for this object is responsible for further consistency.]

**Mechanism:** The older vm32 map form additionally expands its 32-bit backing offset and delegates to `vm32_vm_map_64`, which widens destination fields, invokes the wide external mapping implementation and truncates the returned address. This is an ABI conversion chain, not a separate memory-object or page-table implementation. Failure status is returned from the underlying map operation after the adapter's output assignment. [Adapters](../../../xnu/osfmk/vm/vm32_user.c#L317-L366).

**Declarations:** [`vm32_vm_map`](../../../xnu/osfmk/mach/vm32_map.defs#L161) (`server64`, `server32`, `local64`); [`vm_map`](../../../xnu/osfmk/mach/vm32_map.defs#L161) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_map(
  target_task : vm_task_entry_t;
 inout address : vm32_address_t;
  size : vm32_size_t;
  mask : vm32_address_t;
  flags : int;
  object : mem_entry_name_port_t;
  offset : vm32_offset_t;
  copy : boolean_t;
  cur_protection : vm_prot_t;
  max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm32_vm_map`](../../../xnu/osfmk/vm/vm32_user.c#L347).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm32_vm_map_64`.

### 3813: vm32_vm_machine_attribute

Request an architecture-specific mapping/cache attribute operation, subject to the local supported-result behavior.

**Mechanism:** This vm32 adapter checks addition overflow in the original 32-bit start/size representation before widening them. Overflow returns `KERN_INVALID_ARGUMENT`; the wide `mach_vm_machine_attribute` implementation performs the remaining range and operation-specific checks. This prevents a wrapped 32-bit end from becoming an apparently valid wider interval. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L199-L219). A null map is invalid and zero size succeeds. The helper sanitizes the range, checks map bounds, and accepts only `MATTR_CACHE`; unsupported attributes deliberately return `KERN_INVALID_ADDRESS` for compatibility. It takes an atomic exclusive range lock to serialize pmap access, descends into constant submaps, and calls the per-entry machine-attribute operation only when an object exists. The loop continues even after an entry operation fails, so its final status is not transactional rollback across the range. [Receiver](../../../xnu/osfmk/vm/vm_user.c#L305-L325), [helper](../../../xnu/osfmk/vm/vm_map.c#L14491-L14562).

**Declarations:** [`vm32_vm_machine_attribute`](../../../xnu/osfmk/mach/vm32_map.defs#L174) (`server64`, `server32`, `local64`); [`vm_machine_attribute`](../../../xnu/osfmk/mach/vm32_map.defs#L174) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_machine_attribute(
  target_task : vm_map_t;
  address : vm32_address_t;
  size : vm32_size_t;
  attribute : vm_machine_attribute_t;
 inout value : vm_machine_attribute_val_t);
```

**Local body:** [`vm32_vm_machine_attribute`](../../../xnu/osfmk/vm/vm32_user.c#L199).
Calls visible in this body include `vm_sanitize_add_overflow`, `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_machine_attribute`.

### 3814: vm32_vm_remap

**Interface contract:**

> Map portion of a task's address space.

**Mechanism:** The adapter widens source/destination addresses, size and alignment mask, then calls legacy `mach_vm_remap_external` and truncates the destination output. The parameter named `anywhere` is passed in the wide receiver's flags position; the wide path applies its user-remap mask and initializes protection outputs. It does not use remap_new's input protection or read-capability rules. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L369-L398), [legacy wide body](../../../xnu/osfmk/vm/vm_user.c#L1019-L1057).

**Declarations:** [`vm32_vm_remap`](../../../xnu/osfmk/mach/vm32_map.defs#L181) (`server64`, `server32`, `local64`); [`vm_remap`](../../../xnu/osfmk/mach/vm32_map.defs#L181) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_remap(
  target_task : vm_map_t;
 inout target_address : vm32_address_t;
  size : vm32_size_t;
  mask : vm32_address_t;
  anywhere : boolean_t;
  src_task : vm_map_t;
  src_address : vm32_address_t;
  copy : boolean_t;
 out cur_protection : vm_prot_t;
 out max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm32_vm_remap`](../../../xnu/osfmk/vm/vm32_user.c#L369).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_remap_external`, `vm_sanitize_trunc_addr_to_32`.

### 3815: vm32_task_wire

Historical task-wide wiring control.

**Mechanism:** The vm32 task-wide wiring body is an obsolete stub: null map returns `KERN_INVALID_ARGUMENT`, otherwise it returns `KERN_NOT_SUPPORTED`. It neither delegates to a range-wiring implementation nor inspects the requested wire/unwire boolean. [Complete body](../../../xnu/osfmk/vm/vm32_user.c#L639-L648).

**Declarations:** [`vm32_task_wire`](../../../xnu/osfmk/mach/vm32_map.defs#L194) (`server64`, `server32`, `local64`); [`task_wire`](../../../xnu/osfmk/mach/vm32_map.defs#L194) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_task_wire(
  target_task : vm_map_t;
  must_wire : boolean_t);
```

**Local body:** [`vm32_task_wire`](../../../xnu/osfmk/vm/vm32_user.c#L639).

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L639-L648):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L639-L648 -->
```c
vm32_task_wire(
	vm_map_t        map,
	boolean_t       must_wire __unused)
{
	if (map == VM_MAP_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return KERN_NOT_SUPPORTED;
}
```

### 3816: vm32_mach_make_memory_entry

**Interface contract:**

> Allow application level processes to create named entries which correspond to mapped portions of their address space. These named entries can then be manipulated, shared with other processes in other address spaces and ultimately mapped in ohter address spaces

**Mechanism:** The legacy vm32 named-entry form widens size and offset, calls `_mach_make_memory_entry`, and truncates the adjusted output size. Its common implementation can return a page/data-offset-adjusted extent and named-entry capability; it does not copy bytes directly into the caller's address space. Check the returned status before using either the handle or adjusted size. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L620-L636), [common dispatch](../../../xnu/osfmk/vm/vm_memory_entry.c#L1188-L1269).

**Declarations:** [`vm32_mach_make_memory_entry`](../../../xnu/osfmk/mach/vm32_map.defs#L198) (`server64`, `server32`, `local64`); [`mach_make_memory_entry`](../../../xnu/osfmk/mach/vm32_map.defs#L198) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_mach_make_memory_entry(
  target_task :vm_map_t;
 inout size :vm32_size_t;
  offset :vm32_offset_t;
  permission :vm_prot_t;
 out object_handle :mem_entry_name_port_move_send_t;
  parent_entry :mem_entry_name_port_t);
```

**Local body:** [`vm32_mach_make_memory_entry`](../../../xnu/osfmk/vm/vm32_user.c#L620).
Calls visible in this body include `vm_sanitize_expand_size_to_64`, `vm_sanitize_expand_addr_to_64`, `_mach_make_memory_entry`, `vm_sanitize_trunc_size_to_32`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L620-L636):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L620-L636 -->
```c
vm32_mach_make_memory_entry(
	vm_map_t                target_map,
	vm32_size_ut           *size,
	vm32_offset_ut          offset,
	vm_prot_ut              permission,
	ipc_port_t              *object_handle,
	ipc_port_t              parent_entry)
{
	memory_object_size_ut   mo_size = vm_sanitize_expand_size_to_64(*size);
	memory_object_offset_ut mo_offset = vm_sanitize_expand_addr_to_64(offset);
	kern_return_t           kr;

	kr = _mach_make_memory_entry(target_map, &mo_size,
	    mo_offset, permission, object_handle, parent_entry);
	*size = vm_sanitize_trunc_size_to_32(mo_size);
	return kr;
}
```

### 3817: vm32_vm_map_page_query

**Interface contract:**

> Give the caller information on the given location in a virtual address space. If a page is mapped return ref and dirty info.

**Mechanism:** This receiver expands the vm32 address/size fields used by the operation and calls `mach_vm_page_query`. It does not supply the explicit start-plus-size overflow branch present in several other vm32 wrappers; the wide VM operation remains responsible for its range validation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L595-L604). The wrapper requests `VM_PAGE_INFO_BASIC` from `vm_map_page_info` and extracts only disposition and reference count. It sets both scalar outputs to zero if the helper fails, then returns that failure; zero outputs therefore do not establish that a page is valid and empty. The helper queries a one-byte interval expanded to the effective page boundary, rather than allocating/faulting a page for the caller. This is a state observation, not a retained page or mapping reference. [Wrapper](../../../xnu/osfmk/vm/vm_user.c#L1677-L1703), [query delegation](../../../xnu/osfmk/vm/vm_map.c#L18394-L18408).

**Declarations:** [`vm32_vm_map_page_query`](../../../xnu/osfmk/mach/vm32_map.defs#L206) (`server64`, `server32`, `local64`); [`vm_map_page_query`](../../../xnu/osfmk/mach/vm32_map.defs#L206) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_map_page_query(
                target_map :vm_map_read_t;
                offset :vm32_offset_t;
        out disposition :integer_t;
        out ref_count :integer_t);
```

**Local body:** [`vm32_vm_map_page_query`](../../../xnu/osfmk/vm/vm32_user.c#L595).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `mach_vm_page_query`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L595-L604):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L595-L604 -->
```c
vm32_vm_map_page_query(
	vm_map_t                map,
	vm32_offset_t           offset32,
	int                     *disposition,
	int                     *ref_count)
{
	vm_offset_ut offset = vm_sanitize_expand_addr_to_64(offset32);

	return mach_vm_page_query(map, offset, disposition, ref_count);
}
```

### 3818: vm32_mach_vm_region_info

Historical VM region/object debugging-information query.

**Mechanism:** The locally resolved vm32 debug-region implementation unconditionally returns `KERN_FAILURE` after its VM lock-policy instrumentation. Historical declaration comments about returning object arrays do not describe a working receiver here. Unprefixed profile names refer to the compatibility declaration and do not establish a separate active wide implementation. [Actual stub](../../../xnu/osfmk/vm/vm_debug.c#L95-L106).

**Declarations:** [`vm32_mach_vm_region_info`](../../../xnu/osfmk/mach/vm32_map.defs#L212) (`server64`, `server32`, `local64`); [`mach_vm_region_info`](../../../xnu/osfmk/mach/vm32_map.defs#L212) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_mach_vm_region_info(
  task : vm_map_read_t;
  address : vm32_address_t;
 out region : vm_info_region_t;
 out objects : vm_info_object_array_t);
```

**Local body:** [`vm32_mach_vm_region_info`](../../../xnu/osfmk/vm/vm_debug.c#L95).
Calls visible in this body include `vmlp_api_start`, `vmlp_api_end`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_debug.c#L95-L106):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_debug.c#L95-L106 -->
```c
vm32_mach_vm_region_info(
	__DEBUG_ONLY vm_map_t                   map,
	__DEBUG_ONLY vm32_offset_ut             address_u,
	__DEBUG_ONLY vm_info_region_t           *regionp,
	__DEBUG_ONLY vm_info_object_array_t     *objectsp,
	__DEBUG_ONLY mach_msg_type_number_t     *objectsCntp)
{
	vmlp_api_start(VM32_REGION_INFO);

	vmlp_api_end(VM32_REGION_INFO, KERN_FAILURE);
	return KERN_FAILURE;
}
```

### 3819: vm32_vm_mapped_pages_info

Historical query of mapped physical-page information.

**Mechanism:** The local vm32 mapped-pages-info body immediately returns `KERN_FAILURE`. It does not allocate or return a page-address array, despite the interface's historical description. The unprefixed client/profile alias does not supply a missing local implementation. [Complete stub](../../../xnu/osfmk/vm/vm_debug.c#L129-L135).

**Declarations:** [`vm32_vm_mapped_pages_info`](../../../xnu/osfmk/mach/vm32_map.defs#L218) (`server64`, `server32`, `local64`); [`vm_mapped_pages_info`](../../../xnu/osfmk/mach/vm32_map.defs#L218) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_mapped_pages_info(
  task : vm_map_read_t;
 out pages : page_address_array_t);
```

**Local body:** [`vm32_vm_mapped_pages_info`](../../../xnu/osfmk/vm/vm_debug.c#L129).

[Implementation excerpt](../../../xnu/osfmk/vm/vm_debug.c#L129-L135):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_debug.c#L129-L135 -->
```c
vm32_vm_mapped_pages_info(
	__DEBUG_ONLY vm_map_t                   map,
	__DEBUG_ONLY page_address_array_t       *pages,
	__DEBUG_ONLY mach_msg_type_number_t     *pages_count)
{
	return KERN_FAILURE;
}
```

### 3820: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/vm32_map.defs#L222).

### 3821: vm32_vm_region_recurse

**Interface contract:**

> was vm_region_object_create

**Mechanism:** This old-layout adapter validates map/count, widens address/size, requests a 64-bit submap record, and copies fields back into the vm32 record, including an explicit 32-bit object-offset truncation. It restores the legacy count, narrows address/size, and checks the untruncated successful extent against `VM32_MAX_ADDRESS`. Field assignment is not gated on helper success, so outputs must not be treated as valid when the result reports an error. [Complete translation](../../../xnu/osfmk/vm/vm32_user.c#L529-L579).

**Declarations:** [`vm32_vm_region_recurse`](../../../xnu/osfmk/mach/vm32_map.defs#L224) (`server64`, `server32`, `local64`); [`vm_region_recurse`](../../../xnu/osfmk/mach/vm32_map.defs#L224) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_region_recurse(
                target_task : vm_map_read_t;
 inout address : vm32_address_t;
        out size : vm32_size_t;
 inout nesting_depth : natural_t;
 out info : vm_region_recurse_info_t,CountInOut);
```

**Local body:** [`vm32_vm_region_recurse`](../../../xnu/osfmk/vm/vm32_user.c#L529).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_region_recurse`, `vm_sanitize_trunc_addr_to_32`, `vm_sanitize_trunc_size_to_32`, `vm32_region_get_kern_return`.

### 3822: vm32_vm_region_recurse_64

**Interface contract:**

> The routines below are temporary, meant for transitional use as their counterparts are moved from 32 to 64 bit data path

**Mechanism:** The vm32 address and size are widened while the recursive information buffer uses the wide layout. The helper traverses according to the caller's depth/count, after which address/size are truncated and the helper status is returned. This body has no additional `vm32_region_get_kern_return` check, unlike the old-layout recurse adapter. The returned record remains an observation rather than ownership of the encountered submap or objects. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L505-L526).

**Declarations:** [`vm32_vm_region_recurse_64`](../../../xnu/osfmk/mach/vm32_map.defs#L231) (`server64`, `server32`, `local64`); [`vm_region_recurse_64`](../../../xnu/osfmk/mach/vm32_map.defs#L231) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_region_recurse_64(
                target_task : vm_map_read_t;
 inout address : vm32_address_t;
        out size : vm32_size_t;
 inout nesting_depth : natural_t;
 out info : vm_region_recurse_info_t,CountInOut);
```

**Local body:** [`vm32_vm_region_recurse_64`](../../../xnu/osfmk/vm/vm32_user.c#L505).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_region_recurse`, `vm_sanitize_trunc_addr_to_32`, `vm_sanitize_trunc_size_to_32`.

### 3823: vm32_mach_vm_region_info_64

Historical wide VM region/object debugging-information query.

**Mechanism:** This retained debug-region-info variant also unconditionally returns `KERN_FAILURE`; its wider record type does not make object-array enumeration functional. Treat the declaration as compatibility surface and inspect the stub rather than interpreting the older contract comment as implementation. [Actual stub](../../../xnu/osfmk/vm/vm_debug.c#L113-L124).

**Declarations:** [`vm32_mach_vm_region_info_64`](../../../xnu/osfmk/mach/vm32_map.defs#L238) (`server64`, `server32`, `local64`); [`mach_vm_region_info_64`](../../../xnu/osfmk/mach/vm32_map.defs#L238) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_mach_vm_region_info_64(
  task : vm_map_read_t;
  address : vm32_address_t;
 out region : vm_info_region_64_t;
 out objects : vm_info_object_array_t);
```

**Local body:** [`vm32_mach_vm_region_info_64`](../../../xnu/osfmk/vm/vm_debug.c#L113).
Calls visible in this body include `vmlp_api_start`, `vmlp_api_end`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm_debug.c#L113-L124):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_debug.c#L113-L124 -->
```c
vm32_mach_vm_region_info_64(
	__DEBUG_ONLY vm_map_t                   map,
	__DEBUG_ONLY vm32_offset_ut             address_u,
	__DEBUG_ONLY vm_info_region_64_t        *regionp,
	__DEBUG_ONLY vm_info_object_array_t     *objectsp,
	__DEBUG_ONLY mach_msg_type_number_t     *objectsCntp)
{
	vmlp_api_start(VM32_REGION_INFO_64);

	vmlp_api_end(VM32_REGION_INFO_64, KERN_FAILURE);
	return KERN_FAILURE;
}
```

### 3824: vm32_vm_region_64

Query VM region information using the compatibility VM address/flavor interface.

**Mechanism:** The wrapper widens address/size, calls `mach_vm_region` (including BASIC flavor conversion), and truncates outputs to vm32 before returning its status. Unlike `vm32_vm_region`, this body does not call `vm32_region_get_kern_return` to validate the returned extent against `VM32_MAX_ADDRESS`. Its `_64` information/offset form therefore should not be documented by copying the older wrapper's extra end check. [Exact body](../../../xnu/osfmk/vm/vm32_user.c#L451-L473), [wide flavor selection](../../../xnu/osfmk/vm/vm_user.c#L1438-L1458).

**Declarations:** [`vm32_vm_region_64`](../../../xnu/osfmk/mach/vm32_map.defs#L244) (`server64`, `server32`, `local64`); [`vm_region_64`](../../../xnu/osfmk/mach/vm32_map.defs#L244) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_region_64(
                target_task : vm_map_read_t;
 inout address : vm32_address_t;
        out size : vm32_size_t;
  flavor : vm_region_flavor_t;
 out info : vm_region_info_t, CountInOut;
        out object_name : memory_object_name_t =
                                        MACH_MSG_TYPE_MOVE_SEND
                                        ctype: mach_port_t);
```

**Local body:** [`vm32_vm_region_64`](../../../xnu/osfmk/vm/vm32_user.c#L451).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_region`, `vm_sanitize_trunc_addr_to_32`, `vm_sanitize_trunc_size_to_32`.

### 3825: vm32_mach_make_memory_entry_64

Create a memory-entry capability for a map range with a wide offset/size representation.

**Mechanism:** The vm32 message variant with wide size/offset simply delegates to `_mach_make_memory_entry`; it introduces no address narrowing of those fields. Permission-driven object/share/copy/parent selection and output capability creation remain in the common named-entry implementation. A vm32 client declaration does not mean the underlying VM object is limited to a 32-bit offset. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L607-L617), [common dispatch](../../../xnu/osfmk/vm/vm_memory_entry.c#L1188-L1269).

**Declarations:** [`vm32_mach_make_memory_entry_64`](../../../xnu/osfmk/mach/vm32_map.defs#L254) (`server64`, `server32`, `local64`); [`mach_make_memory_entry_64`](../../../xnu/osfmk/mach/vm32_map.defs#L254) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_mach_make_memory_entry_64(
  target_task :vm_map_t;
 inout size :memory_object_size_t;
  offset :memory_object_offset_t;
  permission :vm_prot_t;
 out object_handle :mach_port_move_send_t;
  parent_entry :mem_entry_name_port_t);
```

**Local body:** [`vm32_mach_make_memory_entry_64`](../../../xnu/osfmk/vm/vm32_user.c#L607).
Calls visible in this body include `_mach_make_memory_entry`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L607-L617):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L607-L617 -->
```c
vm32_mach_make_memory_entry_64(
	vm_map_t                target_map,
	memory_object_size_ut  *size,
	memory_object_offset_ut offset,
	vm_prot_ut              permission,
	ipc_port_t              *object_handle,
	ipc_port_t              parent_handle)
{
	// use the existing entrypoint
	return _mach_make_memory_entry(target_map, size, offset, permission, object_handle, parent_handle);
}
```

### 3826: vm32_vm_map_64

Map a memory-entry/object range using a wide object offset through the compatibility VM interface.

**Mechanism:** This compatibility form widens the vm32 destination address/size/alignment mask but preserves the already-wide backing-object offset. It invokes `mach_vm_map_external` with the object/copy/protection/inheritance fields intact, then narrows the returned destination address. The 64 suffix refers to the object offset contract, not a wholly 64-bit virtual-address ABI. Flag and mapping policy validation occurs in the shared external map implementation. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L317-L344), [shared receiver](../../../xnu/osfmk/vm/vm_user.c#L829-L855).

**Declarations:** [`vm32_vm_map_64`](../../../xnu/osfmk/mach/vm32_map.defs#L264) (`server64`, `server32`, `local64`); [`vm_map_64`](../../../xnu/osfmk/mach/vm32_map.defs#L264) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_map_64(
  target_task : vm_task_entry_t;
 inout address : vm32_address_t;
  size : vm32_size_t;
  mask : vm32_address_t;
  flags : int;
  object : mem_entry_name_port_t;
  offset : memory_object_offset_t;
  copy : boolean_t;
  cur_protection : vm_prot_t;
  max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm32_vm_map_64`](../../../xnu/osfmk/vm/vm32_user.c#L317).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_map_external`, `vm_sanitize_trunc_addr_to_32`.

### 3827: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/vm32_map.defs#L277).

### 3828: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/vm32_map.defs#L278).

### 3829: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/vm32_map.defs#L279).

### 3830: vm32_vm_purgable_control

**Interface contract:**

> Control behavior and investigate state of a "purgable" object in the virtual address space of the target task. A purgable object is created via a call to vm_allocate() with VM_FLAGS_PURGABLE specified. See the routine implementation for a complete definition of the routine.

**Mechanism:** This vm32 receiver already receives a converted map. It expands only the address and calls the local `mach_vm_purgable_control`, whose control allowlist excludes the kernel-only setter. Unlike the modern external port-taking wrapper, this body itself does not choose read-versus-control port conversion based on GET_STATE; that distinction cannot be inferred from an address-width adapter. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L582-L592), [local control validation](../../../xnu/osfmk/vm/vm_user.c#L1619-L1641).

**Declarations:** [`vm32_vm_purgable_control`](../../../xnu/osfmk/mach/vm32_map.defs#L281) (`server64`, `server32`, `local64`); [`vm_purgable_control`](../../../xnu/osfmk/mach/vm32_map.defs#L281) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_purgable_control(
  target_task : vm_map_t;
  address : vm32_address_t;
  control : vm_purgable_t;
 inout state : int);
```

**Local body:** [`vm32_vm_purgable_control`](../../../xnu/osfmk/vm/vm32_user.c#L582).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `mach_vm_purgable_control`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L582-L592):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L582-L592 -->
```c
vm32_vm_purgable_control(
	vm_map_t                map,
	vm32_offset_ut          addr32,
	vm_purgable_t           control,
	int                    *state)
{
	mach_vm_offset_ut addr;

	addr = vm_sanitize_expand_addr_to_64(addr32);
	return mach_vm_purgable_control(map, addr, control, state);
}
```

### 3831: vm32_vm_map_exec_lockdown

Establish the map's executable-mapping lockdown policy under its interlock.

**Mechanism:** The vm32 version performs the same state change directly: reject a null map, acquire its interlock, set `map_disallow_new_exec`, unlock and return success. There are no virtual-address arguments to widen and no scan revoking already executable mappings. This operation installs future execution-map policy rather than returning a new region or modifying data pages. [Complete body](../../../xnu/osfmk/vm/vm32_user.c#L651-L668).

**Declarations:** [`vm32_vm_map_exec_lockdown`](../../../xnu/osfmk/mach/vm32_map.defs#L288) (`server64`, `server32`, `local64`); [`vm_map_exec_lockdown`](../../../xnu/osfmk/mach/vm32_map.defs#L288) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_map_exec_lockdown(
  target_task : vm_map_t);
```

**Local body:** [`vm32_vm_map_exec_lockdown`](../../../xnu/osfmk/vm/vm32_user.c#L651).
Calls visible in this body include `vmlp_api_start`, `vmlp_range_event_none`, `vmlp_api_end`, `vm_map_ilk_lock`, `vm_map_ilk_unlock`.

[Implementation excerpt](../../../xnu/osfmk/vm/vm32_user.c#L651-L668):
<!-- source-excerpt: ../../../xnu/osfmk/vm/vm32_user.c#L651-L668 -->
```c
vm32_vm_map_exec_lockdown(
	vm_map_t        map)
{
	vmlp_api_start(VM32__MAP_EXEC_LOCKDOWN);
	vmlp_range_event_none(map);

	if (map == VM_MAP_NULL) {
		vmlp_api_end(VM32__MAP_EXEC_LOCKDOWN, KERN_INVALID_ARGUMENT);
		return KERN_INVALID_ARGUMENT;
	}

	vm_map_ilk_lock(map);
	map->map_disallow_new_exec = TRUE;
	vm_map_ilk_unlock(map);

	vmlp_api_end(VM32__MAP_EXEC_LOCKDOWN, KERN_SUCCESS);
	return KERN_SUCCESS;
}
```

### 3832: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/mach/vm32_map.defs#L291).

### 3833: vm32_vm_reallocate

**Interface contract:**

> !defined(_MACH_VM_PUBLISH_AS_LOCAL_)

**Mechanism:** The adapter expands source address/size, destination address/size and alignment mask, delegates to `mach_vm_reallocate`, and truncates its destination result before returning status. The shared sanitizer/relocation implementation rejects shrinking and unsupported map/entry configurations; the vm32 wrapper does not add a separate relocation implementation or recovery transaction. A failure-cleared wide destination therefore becomes zero in this output too. [Adapter](../../../xnu/osfmk/vm/vm32_user.c#L671-L692), [shared validation](../../../xnu/osfmk/vm/vm_map.c#L17326-L17535).

**Declarations:** [`vm32_vm_reallocate`](../../../xnu/osfmk/mach/vm32_map.defs#L293) (`server64`, `server32`, `local64`); [`vm_reallocate`](../../../xnu/osfmk/mach/vm32_map.defs#L293) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm32_vm_reallocate (
   target_task : vm_map_t;
   src : vm32_address_t;
   src_size : vm32_size_t;
 inout dst : vm32_address_t;
     dst_size : vm32_size_t;
   align_mask : vm32_offset_t;
   options : int;
   flags : int);
```

**Local body:** [`vm32_vm_reallocate`](../../../xnu/osfmk/vm/vm32_user.c#L671).
Calls visible in this body include `vm_sanitize_expand_addr_to_64`, `vm_sanitize_expand_size_to_64`, `mach_vm_reallocate`, `vm_sanitize_trunc_addr_to_32`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
