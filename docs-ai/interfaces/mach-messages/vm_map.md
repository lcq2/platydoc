# Mach messages: vm_map

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/vm_map.defs](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3800: vm_region

**Interface contract:**

> Returns information about the contents of the virtual address space of the target task at the specified address. The returned protection, inheritance, sharing and memory object values apply to the entire range described by the address range returned; the memory object offset corresponds to the beginning of the address range. [If the specified address is not allocated, the next highest address range is described. If no addresses beyond the one specified are allocated, the call returns KERN_NO_SPACE.]

**Mechanism:** This older receiver calls `vm_map_region` with the requested flavor unchanged, unlike `mach_vm_region` which rewrites BASIC to BASIC_INFO_64. After a successful query, `vm_region_get_kern_return` rejects an extent whose computed end exceeds `VM_MAX_ADDRESS`. Thus the local region output may already have been filled before the wrapper returns an addressability error. Its BASIC layout contains a narrowed offset; this is a snapshot format, not an object capability. [Wrapper/end check](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1461-L1526), [basic record](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L13704-L13752).

**Declarations:** [`vm_region`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L109) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_region(
                target_task : vm_map_read_t;
 inout address : vm_address_t;
        out size : vm_size_t;
  flavor : vm_region_flavor_t;
 out info : vm_region_info_t, CountInOut;
        out object_name : memory_object_name_t =
                                        MACH_MSG_TYPE_MOVE_SEND
                                        ctype: mach_port_t);
```

**Local body:** [`vm_region`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1507).
Calls visible in this body include `vm_map_region`, `vm_region_get_kern_return`.

### 3801: vm_allocate_external

**Interface contract:**

> Allocate zero-filled memory in the address space of the target task, either at the specified address, or wherever space can be found (controlled by flags), of the specified size. The address at which the allocation actually took place is returned.

**Mechanism:** This native-width compatibility name forwards to `mach_vm_allocate_external`, preserving the restricted user flag mask and anonymous allocation semantics. It is not the explicit vm32 conversion wrapper. Profile-selected library/MIG names can differ, while the local receiver still reaches `mach_vm_allocate_kernel` and deferred page faults. [Compatibility receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L173-L180), [wide implementation](../../../platydoc-data/xnu/osfmk/vm/vm_kern.c#L1410-L1480).

**Declarations:** [`vm_allocate_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L130) (`server64`, `server32`, `local64`); [`vm_allocate`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L130) (`libsyscall64`, `sender64`).
**Reserved instead in:** `client64`, `client32`.

**Fields after preprocessing (`server64`):**

```text
routine vm_allocate_external(
  target_task : vm_task_entry_t;
 inout address : vm_address_t;
  size : vm_size_t;
  flags : int);
```

**Local body:** [`vm_allocate_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L173).
Calls visible in this body include `mach_vm_allocate_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L173-L180):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L173-L180 -->
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

### 3802: vm_deallocate

**Interface contract:**

> Deallocate the specified range from the virtual address space of the target virtual memory map.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_deallocate_external`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L203-L209). This removes mappings rather than directly freeing a userspace-supplied physical page. `mach_vm_deallocate_kernel` rejects a null map, sanitizes the address/size into a range, and invokes `vm_map_remove_guard` with no special removal flags and no kernel allocation guard. Removal must perform entry/object/pmap lifetime work; a VM object shared by another mapping can survive. The receiver itself does not implement a separate removal algorithm or translate failure into success. [Entry](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L188-L194), [validated removal](../../../platydoc-data/xnu/osfmk/vm/vm_kern.c#L1488-L1536).

**Declarations:** [`vm_deallocate`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L146) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`).
**Reserved instead in:** `client64`, `client32`.

**Fields after preprocessing (`server64`):**

```text
routine vm_deallocate(
  target_task : vm_task_entry_t;
  address : vm_address_t;
  size : vm_size_t);
```

**Local body:** [`vm_deallocate`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L203).
Calls visible in this body include `mach_vm_deallocate_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L203-L209):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L203-L209 -->
```c
vm_deallocate(
	vm_map_t                map,
	vm_offset_ut            start,
	vm_size_ut              size)
{
	return mach_vm_deallocate_external(map, start, size);
}
```

**User wrapper:** [`vm_deallocate`](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L135).
Calls visible in this body include `mach_vm_deallocate`.

[Implementation excerpt](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L135-L145):
<!-- source-excerpt: ../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L135-L145 -->
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

### 3803: vm_protect

**Interface contract:**

> Set the current or maximum protection attribute for the specified range of the virtual address space of the target virtual memory map. The current protection limits the memory access rights of threads within the map; the maximum protection limits the accesses that may be given in the current protection. Protections are specified as a set of {read, write, execute} *permissions*.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_protect`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L289-L297). After rejecting a null map, the receiver treats zero size as success and passes a computed end plus the requested current/maximum mode to `vm_map_protect`. The lower layer sanitizes protections and ranges, applies map/entry policy, and coordinates protection changes with mapped translations. `VM_PROT_COPY` has a special copy-on-write remap path rather than being an ordinary hardware permission bit; execute/write policy can reject it with `KERN_PROTECTION_FAILURE`. Successful protection changes do not imply that pages were made resident. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L259-L279), [validation and COPY path](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L5801-L5906).

**Declarations:** [`vm_protect`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L167) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`).
**Reserved instead in:** `client64`, `client32`.

**Fields after preprocessing (`server64`):**

```text
routine vm_protect(
  target_task : vm_task_entry_t;
  address : vm_address_t;
  size : vm_size_t;
  set_maximum : boolean_t;
  new_protection : vm_prot_t);
```

**Local body:** [`vm_protect`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L289).
Calls visible in this body include `mach_vm_protect`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L289-L297):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L289-L297 -->
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

**User wrapper:** [`vm_protect`](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L148).
Calls visible in this body include `mach_vm_protect`.

[Implementation excerpt](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L148-L160):
<!-- source-excerpt: ../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L148-L160 -->
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

### 3804: vm_inherit

**Interface contract:**

> Set the inheritance attribute for the specified range of the virtual address space of the target task. The inheritance value is one of {none, copy, share}, and specifies how the child address space should acquire this memory at the time of a task_create call.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_inherit`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L243-L250). The receiver validates the map, accepts a zero-size request, and calls `vm_map_inherit` with a computed range end. The helper sanitizes the inheritance value/range, clamps to map bounds, and installs entry-specific preflight checks before taking a streaming exclusive range lock. It updates inheritance on the entries it visits; an entirely unmapped range is explicitly normalized to success. The operation changes future fork inheritance policy, not an immediate copy of pages into a child task. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L217-L235), [entry walk](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L6205-L6262).

**Declarations:** [`vm_inherit`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L182) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_inherit(
  target_task : vm_task_entry_t;
  address : vm_address_t;
  size : vm_size_t;
  new_inheritance : vm_inherit_t);
```

**Local body:** [`vm_inherit`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L243).
Calls visible in this body include `mach_vm_inherit`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L243-L250):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L243-L250 -->
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

### 3805: vm_read

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit reading.]

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_read`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L402-L410). The receiver rejects a null map and sizes that cannot fit `mach_msg_type_number_t`, then calls `vm_map_copyin` without destroying the source. On success it returns a `vm_map_copy_t` and byte count to the MIG transport, not an already chosen destination address in the caller. Reply delivery performs the out-of-line copyout; a direct kernel caller must manage the copy representation itself. Range/protection/copy-on-write work belongs to VM copyin, so this is not a blind `memcpy` from another task. [Body and transport contract](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L345-L389).

**Declarations:** [`vm_read`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L195) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_vm_read`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L195) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine vm_read (
  target_task : vm_map_read_t;
  address : vm_address_t;
  size : vm_size_t;
 out data : pointer_t);
```

**Local body:** [`vm_read`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L402).
Calls visible in this body include `mach_vm_read`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L402-L410):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L402-L410 -->
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

**User wrapper:** [`vm_read`](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L367).
Calls visible in this body include `_kernelrpc_vm_read`, `__syscall_logger`, `mach_task_self`.

### 3806: vm_read_list

**Interface contract:**

> List corrollary to vm_read, returns mapped contents of specified ranges within target address space.

**Mechanism:** This native-width list implementation uses the same per-item copyin/current-task-copyout loop as the wide interface, but casts each successful returned address to `vm_offset_t`. It bounds the count, zeros failed/empty entries, discards a copy after copyout failure and continues rather than undoing earlier mappings. The final status reflects the last attempted operation that assigned it, so inspect every result entry. This is distinct from the vm32 adapter, which widens and narrows a fixed-size array. [Body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L487-L531).

**Declarations:** [`vm_read_list`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L205) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_read_list(
  target_task : vm_map_read_t;
 inout data_list : vm_read_entry_t;
  count : natural_t);
```

**Local body:** [`vm_read_list`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L487).
Calls visible in this body include `vm_map_copyin`, `vm_map_copyout`, `current_task`, `CAST_DOWN`, `vm_map_copy_discard`.

### 3807: vm_write

**Interface contract:**

> Writes the contents of the specified range of the virtual address space of the target task. [The range must be aligned on a virtual page boundary, and must be a multiple of pages in extent. The protection on the specified range must permit writing.]

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_write`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L711-L718). The incoming data parameter is a VM-copy object constructed by the kernel MIG server from the sender's userspace buffer. After checking the destination map, the body unwraps that transport-created value and passes it to `vm_map_copy_overwrite` with the supplied byte count. It does not dereference the wire pointer as a raw kernel buffer or itself make a second source copy. MTE builds explicitly pass `sec_override=TRUE`; other protection/range decisions belong to the overwrite implementation and transport cleanup contract. [Body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L674-L698).

**Declarations:** [`vm_write`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L217) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_write(
  target_task : vm_map_t;
  address : vm_address_t;
  data : pointer_t);
```

**Local body:** [`vm_write`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L711).
Calls visible in this body include `mach_vm_write`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L711-L718):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L711-L718 -->
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

### 3808: vm_copy

**Interface contract:**

> Copy the contents of the source range of the virtual address space of the target task to the destination range in that same address space. [Both of the ranges must be aligned on a virtual page boundary, and must be multiples of pages in extent. The protection on the source range must permit reading, and the protection on the destination range must permit writing.]

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_copy`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L764-L771). Both ranges belong to the specified map. The implementation first captures the source with nondestructive `vm_map_copyin`, checks the copy size when present, and then calls `vm_map_copy_overwrite` for the destination. A failed overwrite discards the retained copy; success consumes it through the overwrite path. Thus overlap and backing-object behavior are VM-copy operations rather than a driver or physical-address copy. A null map is rejected before either stage. [Two-stage operation and failure cleanup](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L727-L761).

**Declarations:** [`vm_copy`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L232) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_copy(
  target_task : vm_map_t;
  source_address : vm_address_t;
  size : vm_size_t;
  dest_address : vm_address_t);
```

**Local body:** [`vm_copy`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L764).
Calls visible in this body include `mach_vm_copy`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L764-L771):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L764-L771 -->
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

### 3809: vm_read_overwrite

**Interface contract:**

> Returns the contents of the specified range of the virtual address space of the target task. [There are no alignment restrictions, and the results will overwrite the area pointed to by data - which must already exist. The protection on the specified range must permit reading.]

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_read_overwrite`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L595-L603). The source map supplies a nondestructive `vm_map_copyin`; the destination is an already specified address in `current_thread()->map`. `vm_map_copy_overwrite` applies that copy to the destination with interruption disabled for this call. Only success publishes the requested output byte count. If overwrite fails, this caller discards the remaining copy object. The separation between acquiring the copy and overwriting a destination is the important ownership boundary; the wrapper does not promise a general rollback of destination changes. [Complete entry body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L544-L580).

**Declarations:** [`vm_read_overwrite`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L246) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_read_overwrite(
  target_task : vm_map_read_t;
  address : vm_address_t;
  size : vm_size_t;
  data : vm_address_t;
 out outsize : vm_size_t);
```

**Local body:** [`vm_read_overwrite`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L595).
Calls visible in this body include `mach_vm_read_overwrite`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L595-L603):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L595-L603 -->
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

### 3810: vm_msync

Request synchronization of the specified mapped range through vm_map_msync.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_msync`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1260-L1267). A null map returns `KERN_INVALID_TASK`; zero size succeeds. The map implementation rejects simultaneous synchronous/asynchronous flags, sanitizes the range, and uses a streaming range lock whose hole handling depends on CONTIGUOUS/KILLPAGES. Kill/deactivate requests operate on object pages. Ordinary sync skips absent, internal, private or pagerless objects; for an eligible external object it takes a reference, drops the streamed entry lock, calls `vm_object_sync`, and releases the reference. Success is not a universal storage-device durability guarantee. [Entry](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1208-L1223), [walk](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L18955-L19165).

**Declarations:** [`vm_msync`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L254) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_msync(
  target_task : vm_map_t;
  address : vm_address_t;
  size : vm_size_t;
  sync_flags : vm_sync_t);
```

**Local body:** [`vm_msync`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1260).
Calls visible in this body include `mach_vm_msync`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1260-L1267):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1260-L1267 -->
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

### 3811: vm_behavior_set

**Interface contract:**

> Set the paging behavior attribute for the specified range of the virtual address space of the target task. The behavior value is one of {default, random, forward sequential, reverse sequential} and indicates the expected page reference pattern for the specified range.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_behavior_set`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1411-L1421). The receiver sanitizes the range and behavior before dispatching. Persistent DEFAULT/RANDOM/SEQUENTIAL/REVERSE-SEQUENTIAL behaviors are recorded under an atomic exclusive range lock that excludes holes. ZERO_WIRED_PAGES additionally preflights write permission and disallows JIT/TPRO entries where configured. Other values initiate work immediately: WILLNEED requests paging, DONTNEED/FREE invoke msync deactivate/kill behavior, and REUSABLE/REUSE use their own page-accounting helpers. Consequently, this interface is not uniformly a harmless hint or a simple field assignment. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1369-L1395), [behavior dispatch](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L14589-L14695).

**Declarations:** [`vm_behavior_set`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L267) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_behavior_set(
  target_task : vm_map_t;
  address : vm_address_t;
  size : vm_size_t;
  new_behavior : vm_behavior_t);
```

**Local body:** [`vm_behavior_set`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1411).
Calls visible in this body include `mach_vm_behavior_set`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1411-L1421):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1411-L1421 -->
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

### 3812: vm_map_external

**Interface contract:**

> Map a user-defined memory object into the virtual address space of the target task. If desired (anywhere is TRUE), the kernel will find a suitable address range of the specified size; else, the specific address will be allocated. The beginning address of the range will be aligned on a virtual page boundary, be at or beyond the address specified, and meet the mask requirements (bits turned on in the mask must not be turned on in the result); the size of the range, in bytes, will be rounded up to an integral number of virtual pages. The memory in the resulting range will be associated with the specified memory object, with the beginning of the memory range referring to the specified offset into the memory object. The mapping will take the current and maximum protections and the inheritance attributes specified; see the vm_protect and vm_inherit calls for a description of these attributes. If desired (copy is TRUE), the memory range will be filled with a copy of the data from the memory object; this copy will be private to this mapping in this target task. Otherwise, the memory in this mapping will be shared with other mappings of the same memory object at the same offset (in this task or in other tasks). [The Mach kernel only enforces shared memory consistency among mappings on one host with similar page alignments. The user-defined memory manager for this object is responsible for further consistency.]

**Mechanism:** These compatibility mapping names converge on `mach_vm_map_external`. The `_64` form preserves a `memory_object_offset_ut` backing offset while the older native-width form uses `vm_offset_ut`; both retain address/size/mask widths from their declaration. They forward object, copy and protection/inheritance arguments rather than implementing independent mapping policy. [Adapters](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L860-L897). The external receiver first rejects kernel-only mapping flags, constructs `vm_map_kernel_flags_t`, and forwards all object/offset/copy/current/max/inheritance inputs to `mach_vm_map_kernel`. That helper enters `vm_map_enter_mem_object`, which interprets the supplied memory-entry/object capability and installs mappings subject to VM validation and placement policy. This full message interface can carry backing objects and protection/inheritance choices absent from the restricted current-task allocation trap. Returned addresses describe CPU virtual mappings; they are not DMA addresses. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L829-L855), [mapping handoff](../../../platydoc-data/xnu/osfmk/vm/vm_kern.c#L2482-L2509).

**Declarations:** [`vm_map_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L304) (`server64`, `server32`, `local64`); [`_kernelrpc_vm_map`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L304) (`client64`, `client32`); [`vm_map`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L304) (`libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_map_external (
  target_task : vm_task_entry_t;
 inout address : vm_address_t;
  size : vm_size_t;
  mask : vm_address_t;
  flags : int;
  object : mem_entry_name_port_t;
  offset : vm_offset_t;
  copy : boolean_t;
  cur_protection : vm_prot_t;
  max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm_map_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L881).
Calls visible in this body include `mach_vm_map_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L881-L897):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L881-L897 -->
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

### 3813: vm_machine_attribute

Request an architecture-specific mapping/cache attribute operation, subject to the local supported-result behavior.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_machine_attribute`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L334-L342). A null map is invalid and zero size succeeds. The helper sanitizes the range, checks map bounds, and accepts only `MATTR_CACHE`; unsupported attributes deliberately return `KERN_INVALID_ADDRESS` for compatibility. It takes an atomic exclusive range lock to serialize pmap access, descends into constant submaps, and calls the per-entry machine-attribute operation only when an object exists. The loop continues even after an entry operation fails, so its final status is not transactional rollback across the range. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L305-L325), [helper](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L14491-L14562).

**Declarations:** [`vm_machine_attribute`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L322) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_machine_attribute(
  target_task : vm_map_t;
  address : vm_address_t;
  size : vm_size_t;
  attribute : vm_machine_attribute_t;
 inout value : vm_machine_attribute_val_t);
```

**Local body:** [`vm_machine_attribute`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L334).
Calls visible in this body include `mach_vm_machine_attribute`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L334-L342):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L334-L342 -->
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

### 3814: vm_remap_external

**Interface contract:**

> Map portion of a task's address space.

**Mechanism:** The native-width remap adapter delegates to the legacy wide receiver; the source argument is an already converted map and protections are outputs. It does not introduce the newer source-port capability-selection or data-offset policy. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1095-L1111). The legacy remap receiver rejects flags outside `VM_FLAGS_USER_REMAP`, initializes both output protection values to NONE, and marks the request as legacy remap before calling `vm_map_remap`. The source is an already converted map capability. The underlying extraction/insertion path implements the copy-versus-share choice; protections returned to this legacy caller describe the resulting region rather than an input permission request. Unlike the newer interface, this wrapper does not force data-address offset preservation. [Legacy receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1019-L1057), [map/COW mechanisms](../../subsystems/vm/virtual-address-maps.md).

**Declarations:** [`vm_remap_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L332) (`server64`, `server32`, `local64`); [`_kernelrpc_vm_remap`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L332) (`client64`, `client32`); [`vm_remap`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L332) (`libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_remap_external (
  target_task : vm_map_t;
 inout target_address : vm_address_t;
  size : vm_size_t;
  mask : vm_address_t;
  flags : int;
  src_task : vm_map_t;
  src_address : vm_address_t;
  copy : boolean_t;
 out cur_protection : vm_prot_t;
 out max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm_remap_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1095).
Calls visible in this body include `mach_vm_remap_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1095-L1111):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1095-L1111 -->
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

### 3815: task_wire

Historical task-wide wiring control.

**Mechanism:** This obsolete interface performs no wiring. A null map returns `KERN_INVALID_ARGUMENT`; every other call returns `KERN_NOT_SUPPORTED`, irrespective of `must_wire`. Actual range/object wiring uses other VM entry points and UPL protocols, so the historical declaration must not be described as a current task-wide pinning service. [Complete body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1909-L1918).

**Declarations:** [`task_wire`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L350) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_wire(
  target_task : vm_map_t;
  must_wire : boolean_t);
```

**Local body:** [`task_wire`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1909).

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1909-L1918):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1909-L1918 -->
```c
task_wire(
	vm_map_t        map,
	boolean_t       must_wire __unused)
{
	if (map == VM_MAP_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return KERN_NOT_SUPPORTED;
}
```

### 3816: mach_make_memory_entry

**Interface contract:**

> Allow application level processes to create named entries which correspond to mapped portions of their address space. These named entries can then be manipulated, shared with other processes in other address spaces and ultimately mapped in ohter address spaces

**Mechanism:** The public variants converge on `mach_make_memory_entry_internal` with no trusted kernel flags. It sanitizes user permissions, rejects a copy-backed parent, then selects MEM_ONLY, new anonymous named object, VM-copy snapshot, sharing/reuse, or parent-relative derivation. These paths have different zero-size, alignment and protection checks. A named object is exposed through an `IKOT_NAMED_ENTRY` send right; a copy entry owns an entry-list copy, while a parent-derived entry cannot exceed its parent's allowed protections. Returned size can be adjusted for page/data offsets. [Dispatcher](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1188-L1285), [port creation](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1288-L1305).

**Declarations:** [`mach_make_memory_entry`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L362) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_make_memory_entry(
  target_task :vm_map_t;
 inout size :vm_size_t;
  offset :vm_offset_t;
  permission :vm_prot_t;
 out object_handle :mem_entry_name_port_move_send_t;
  parent_entry :mem_entry_name_port_t);
```

**Local body:** [`mach_make_memory_entry`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1272).
Calls visible in this body include `mach_make_memory_entry_64`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1272-L1285):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1272-L1285 -->
```c
mach_make_memory_entry(
	vm_map_t                target_map,
	vm_size_ut             *size_u,
	vm_offset_ut            offset_u,
	vm_prot_ut              permission_u,
	ipc_port_t              *object_handle,
	ipc_port_t              parent_entry)
{
	kern_return_t           kr;

	kr = mach_make_memory_entry_64(target_map, size_u,
	    offset_u, permission_u, object_handle, parent_entry);
	return kr;
}
```

### 3817: vm_map_page_query

**Interface contract:**

> Give the caller information on the given location in a virtual address space. If a page is mapped return ref and dirty info.

**Mechanism:** The native-width compatibility receiver delegates directly to `mach_vm_page_query`; the underlying decisions below still apply. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1706-L1713). The wrapper requests `VM_PAGE_INFO_BASIC` from `vm_map_page_info` and extracts only disposition and reference count. It sets both scalar outputs to zero if the helper fails, then returns that failure; zero outputs therefore do not establish that a page is valid and empty. The helper queries a one-byte interval expanded to the effective page boundary, rather than allocating/faulting a page for the caller. This is a state observation, not a retained page or mapping reference. [Wrapper](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1677-L1703), [query delegation](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L18394-L18408).

**Declarations:** [`vm_map_page_query`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L374) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_map_page_query(
                target_map :vm_map_read_t;
                offset :vm_offset_t;
        out disposition :integer_t;
        out ref_count :integer_t);
```

**Local body:** [`vm_map_page_query`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1706).
Calls visible in this body include `mach_vm_page_query`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1706-L1713):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1706-L1713 -->
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

### 3818: mach_vm_region_info

Historical VM region/object debugging-information query.

**Mechanism:** The locally resolved vm32 debug-region implementation unconditionally returns `KERN_FAILURE` after its VM lock-policy instrumentation. Historical declaration comments about returning object arrays do not describe a working receiver here. Unprefixed profile names refer to the compatibility declaration and do not establish a separate active wide implementation. [Actual stub](../../../platydoc-data/xnu/osfmk/vm/vm_debug.c#L95-L106).

**Declarations:** [`mach_vm_region_info`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L386) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_region_info(
  task : vm_map_read_t;
  address : vm_address_t;
 out region : vm_info_region_t;
 out objects : vm_info_object_array_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3819: vm_mapped_pages_info

Historical query of mapped physical-page information.

**Mechanism:** The local vm32 mapped-pages-info body immediately returns `KERN_FAILURE`. It does not allocate or return a page-address array, despite the interface's historical description. The unprefixed client/profile alias does not supply a missing local implementation. [Complete stub](../../../platydoc-data/xnu/osfmk/vm/vm_debug.c#L129-L135).

**Declarations:** [`vm_mapped_pages_info`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L392) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_mapped_pages_info(
  task : vm_map_read_t;
 out pages : page_address_array_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3820: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L396).

### 3821: vm_region_recurse

**Interface contract:**

> A recursive form of vm_region which probes submaps withint the address space.

**Mechanism:** The legacy record adapter requires at least `VM_REGION_SUBMAP_INFO_COUNT`, requests a 64-bit submap record internally, and translates the individual fields back, explicitly truncating the object offset to 32 bits. It restores the old output count and applies the native addressability end check. The body copies those temporary fields before returning the underlying status; callers must honor that status rather than assuming every output is meaningful after failure. [Translation body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1573-L1616).

**Declarations:** [`vm_region_recurse`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L402) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_region_recurse(
                target_task : vm_map_read_t;
 inout address : vm_address_t;
        out size : vm_size_t;
 inout nesting_depth : natural_t;
 out info : vm_region_recurse_info_t,CountInOut);
```

**Local body:** [`vm_region_recurse`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1573).
Calls visible in this body include `vm_map_region_recurse_64`, `vm_region_get_kern_return`.

### 3822: vm_region_recurse_64

**Interface contract:**

> The routines below are temporary, meant for transitional use as their counterparts are moved from 32 to 64 bit data path

**Mechanism:** The native-width wrapper delegates to `mach_vm_region_recurse` using the 64-bit information layout, then applies `vm_region_get_kern_return` to the returned address/extent. Submap depth and record capacity remain in/out parameters. This preserves recursive traversal while imposing the wrapper's legacy addressability check; it does not retain a submap on behalf of the user. [Wrapper](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1556-L1570), [extent check](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1461-L1475).

**Declarations:** [`vm_region_recurse_64`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L416) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_region_recurse_64(
                target_task : vm_map_read_t;
 inout address : vm_address_t;
        out size : vm_size_t;
 inout nesting_depth : natural_t;
 out info : vm_region_recurse_info_t,CountInOut);
```

**Local body:** [`vm_region_recurse_64`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1556).
Calls visible in this body include `mach_vm_region_recurse`, `vm_region_get_kern_return`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1556-L1570):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1556-L1570 -->
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

### 3823: mach_vm_region_info_64

Historical wide VM region/object debugging-information query.

**Mechanism:** This retained debug-region-info variant also unconditionally returns `KERN_FAILURE`; its wider record type does not make object-array enumeration functional. Treat the declaration as compatibility surface and inspect the stub rather than interpreting the older contract comment as implementation. [Actual stub](../../../platydoc-data/xnu/osfmk/vm/vm_debug.c#L113-L124).

**Declarations:** [`mach_vm_region_info_64`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L423) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_vm_region_info_64(
  task : vm_map_read_t;
  address : vm_address_t;
 out region : vm_info_region_64_t;
 out objects : vm_info_object_array_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 3824: vm_region_64

Query VM region information using the compatibility VM address/flavor interface.

**Mechanism:** This native-width address adapter calls `mach_vm_region`, thereby inheriting its BASIC-to-BASIC_INFO_64 flavor conversion, then checks the returned extent against `VM_MAX_ADDRESS`. The `_64` suffix here does not remove all legacy addressability limits. Failure of the final extent check is reported after the lower query has run. [Wrapper and extent check](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1461-L1504).

**Declarations:** [`vm_region_64`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L429) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_region_64(
                target_task : vm_map_read_t;
 inout address : vm_address_t;
        out size : vm_size_t;
  flavor : vm_region_flavor_t;
 out info : vm_region_info_t, CountInOut;
        out object_name : memory_object_name_t =
                                        MACH_MSG_TYPE_MOVE_SEND
                                        ctype: mach_port_t);
```

**Local body:** [`vm_region_64`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1489).
Calls visible in this body include `mach_vm_region`, `vm_region_get_kern_return`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1489-L1504):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1489-L1504 -->
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

### 3825: mach_make_memory_entry_64

Create a memory-entry capability for a map range with a wide offset/size representation.

**Mechanism:** The public variants converge on `mach_make_memory_entry_internal` with no trusted kernel flags. It sanitizes user permissions, rejects a copy-backed parent, then selects MEM_ONLY, new anonymous named object, VM-copy snapshot, sharing/reuse, or parent-relative derivation. These paths have different zero-size, alignment and protection checks. A named object is exposed through an `IKOT_NAMED_ENTRY` send right; a copy entry owns an entry-list copy, while a parent-derived entry cannot exceed its parent's allowed protections. Returned size can be adjusted for page/data offsets. [Dispatcher](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1188-L1285), [port creation](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1288-L1305).

**Declarations:** [`mach_make_memory_entry_64`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L439) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_make_memory_entry_64(
  target_task :vm_map_t;
 inout size :memory_object_size_t;
  offset :memory_object_offset_t;
  permission :vm_prot_t;
 out object_handle :mach_port_move_send_t;
  parent_entry :mem_entry_name_port_t);
```

**Local body:** [`mach_make_memory_entry_64`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L61).
Calls visible in this body include `mach_make_memory_entry_internal`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L61-L76):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L61-L76 -->
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

### 3826: vm_map_64_external

Map a memory-entry/object range using a wide object offset through the compatibility VM interface.

**Mechanism:** These compatibility mapping names converge on `mach_vm_map_external`. The `_64` form preserves a `memory_object_offset_ut` backing offset while the older native-width form uses `vm_offset_ut`; both retain address/size/mask widths from their declaration. They forward object, copy and protection/inheritance arguments rather than implementing independent mapping policy. [Adapters](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L860-L897). The external receiver first rejects kernel-only mapping flags, constructs `vm_map_kernel_flags_t`, and forwards all object/offset/copy/current/max/inheritance inputs to `mach_vm_map_kernel`. That helper enters `vm_map_enter_mem_object`, which interprets the supplied memory-entry/object capability and installs mappings subject to VM validation and placement policy. This full message interface can carry backing objects and protection/inheritance choices absent from the restricted current-task allocation trap. Returned addresses describe CPU virtual mappings; they are not DMA addresses. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L829-L855), [mapping handoff](../../../platydoc-data/xnu/osfmk/vm/vm_kern.c#L2482-L2509).

**Declarations:** [`vm_map_64_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L449) (`server64`, `server32`, `local64`); [`vm_map_64`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L449) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_map_64_external(
  target_task : vm_task_entry_t;
 inout address : vm_address_t;
  size : vm_size_t;
  mask : vm_address_t;
  flags : int;
  object : mem_entry_name_port_t;
  offset : memory_object_offset_t;
  copy : boolean_t;
  cur_protection : vm_prot_t;
  max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm_map_64_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L860).
Calls visible in this body include `mach_vm_map_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L860-L876):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L860-L876 -->
```c
vm_map_64_external(
	vm_map_t                target_map,
	vm_offset_ut           *address,
	vm_size_ut              size,
	vm_offset_ut            mask,
	int                     flags,
	ipc_port_t              port,
	memory_object_offset_ut offset,
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

### 3827: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L462).

### 3828: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L463).

### 3829: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L464).

### 3830: vm_purgable_control_external

**Interface contract:**

> Control behavior and investigate state of a "purgable" object in the virtual address space of the target task. A purgable object is created via a call to vm_allocate() with VM_FLAGS_PURGABLE specified. See the routine implementation for a complete definition of the routine.

**Mechanism:** The external native-width receiver forwards the destination port and address to the wide external control path; it retains GET_STATE's read-capability distinction. A client-side alias does not imply a separate object policy. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1666-L1673). GET_STATE converts the destination capability with `convert_port_to_map_read`; mutations use map control. The wrapper always releases that converted map reference after calling the common control body. Userspace cannot select SET_STATE_FROM_KERNEL. The map helper validates states, requires an existing purgeable object, rejects submap addresses, and requires write permission for state changes; PURGE_ALL is a separate global purge branch. This object policy can discard contents, so changing volatility is distinct from removing the virtual mapping. [Capability selection](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1619-L1663), [object checks](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L18078-L18175).

**Declarations:** [`vm_purgable_control_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L473) (`server64`, `server32`, `local64`); [`_kernelrpc_vm_purgable_control`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L473) (`client64`, `client32`); [`vm_purgable_control`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L473) (`libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_purgable_control_external (
  target_tport: mach_port_t;
  address : vm_address_t;
  control : vm_purgable_t;
 inout state : int);
```

**Local body:** [`vm_purgable_control_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1666).
Calls visible in this body include `mach_vm_purgable_control_external`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1666-L1673):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1666-L1673 -->
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

### 3831: vm_map_exec_lockdown

Establish the map's executable-mapping lockdown policy under its interlock.

**Mechanism:** The operation rejects a null map, takes the map interlock, sets `map_disallow_new_exec`, and releases the interlock. It records a future mapping/protection restriction; this body does not walk the map and remove existing executable permissions. Its success therefore means the policy bit was installed, not that every executable translation was torn down. [Complete receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1921-L1937).

**Declarations:** [`vm_map_exec_lockdown`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L484) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_map_exec_lockdown(
  target_task : vm_map_t);
```

**Local body:** [`vm_map_exec_lockdown`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1921).
Calls visible in this body include `vmlp_api_start`, `vmlp_api_end`, `vm_map_ilk_lock`, `vm_map_ilk_unlock`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1921-L1937):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1921-L1937 -->
```c
vm_map_exec_lockdown(
	vm_map_t        map)
{
	vmlp_api_start(VM_MAP_EXEC_LOCKDOWN);

	if (map == VM_MAP_NULL) {
		vmlp_api_end(VM_MAP_EXEC_LOCKDOWN, KERN_INVALID_ARGUMENT);
		return KERN_INVALID_ARGUMENT;
	}

	vm_map_ilk_lock(map);
	map->map_disallow_new_exec = TRUE;
	vm_map_ilk_unlock(map);

	vmlp_api_end(VM_MAP_EXEC_LOCKDOWN, KERN_SUCCESS);
	return KERN_SUCCESS;
}
```

### 3832: vm_remap_new_external

Remap a source range using the newer remap semantics and return the resulting protections/address.

**Mechanism:** The native-width adapter preserves the newer source-port and in/out protection contract while forwarding to `mach_vm_remap_new_external`. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1064-L1088). This receiver forces `VM_FLAGS_RETURN_DATA_ADDR`, validates in/out protections, and rejects maximum permissions containing both WRITE and EXECUTE. It converts the source port to a read map for copying or a maximum of exactly READ/NONE; other shared remaps require map control. It invokes `vm_map_remap`, releases the converted map reference on every return, and consumes the incoming source send right only on success. The output protections report what was actually installed, while the returned address preserves the source offset within a page. [Body](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L929-L1006).

**Declarations:** [`vm_remap_new_external`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L487) (`server64`, `server32`, `local64`); [`_kernelrpc_vm_remap_new`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L487) (`client64`, `client32`); [`vm_remap_new`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L487) (`libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine vm_remap_new_external (
  target_task : vm_map_t;
 inout target_address : vm_address_t;
  size : vm_size_t;
  mask : vm_address_t;
  flags : int;
  src_tport : mach_port_t;
  src_address : vm_address_t;
  copy : boolean_t;
 inout cur_protection : vm_prot_t;
 inout max_protection : vm_prot_t;
  inheritance : vm_inherit_t);
```

**Local body:** [`vm_remap_new_external`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L1064).
Calls visible in this body include `mach_vm_remap_new_external`.

### 3833: vm_reallocate

**Interface contract:**

> Relocate the pages of the source range of the specified map to a new range of the given size in bytes within the same map.

**Mechanism:** The native-width wrapper widens the destination temporary, invokes `mach_vm_reallocate`, then casts the returned destination back before returning the helper's status. Validation and relocation are shared, not a second allocator implementation. [Adapter](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L797-L815). The receiver rejects a null map and forwards to `vm_map_reallocate`. Its sanitizer checks flag/option masks, nonzero page-aligned sizes, source alignment and fixed-destination alignment. The relocation implementation refuses non-native page-size maps, shrinking, and fixed-overwrite overlap with the source; equal-size aligned ANYWHERE requests can simply return the source address. Entry preflight excludes submaps, permanent mappings, JIT and configured MTE/TPRO cases. Sanitization or relocation failure clears the destination output rather than returning a stale proposed address. [Receiver](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L779-L794), [validation/relocation](../../../platydoc-data/xnu/osfmk/vm/vm_map.c#L17326-L17535).

**Declarations:** [`vm_reallocate`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L508) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_vm_reallocate`](../../../platydoc-data/xnu/osfmk/mach/vm_map.defs#L508) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine vm_reallocate (
   target_task : vm_map_t;
   src : vm_address_t;
   src_size : vm_size_t;
 inout dst : vm_address_t;
     dst_size : vm_size_t;
   align_mask : vm_offset_t;
   options : int;
   flags : int);
```

**Local body:** [`vm_reallocate`](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L797).
Calls visible in this body include `mach_vm_reallocate`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L797-L815):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_user.c#L797-L815 -->
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

**User wrapper:** [`vm_reallocate`](../../../platydoc-data/xnu/libsyscall/mach/mach_vm.c#L754).
Calls visible in this body include `mach_vm_reallocate`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
