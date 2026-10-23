# Mach messages: device

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/device/device.defs](../../../platydoc-data/xnu/osfmk/device/device.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 2800: io_object_get_class

Copy the object's runtime metaclass name into the bounded output string.

**Mechanism:** Rejects a null object, asks the retained runtime object for its metaclass, and returns `kIOReturnNotFound` if that lookup is absent. Otherwise `strlcpy` copies the class name into the fixed `io_name_t` result. This reports the dynamic metaclass of the supplied object rather than searching the class registry by string. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2441).

**Declarations:** [`io_object_get_class`](../../../platydoc-data/xnu/osfmk/device/device.defs#L151) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_object_get_class(
     object : io_object_t;
 out className : io_name_t
 );
```

**Local body:** [`is_io_object_get_class`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2441).
Calls visible in this body include `getMetaClass`, `strlcpy`, `getClassName`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2441-L2459):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2441-L2459 -->
```c
is_io_object_get_class(
	io_object_t object,
	io_name_t className )
{
	const OSMetaClass* my_obj = NULL;

	if (!object) {
		return kIOReturnBadArgument;
	}

	my_obj = object->getMetaClass();
	if (!my_obj) {
		return kIOReturnNotFound;
	}

	strlcpy( className, my_obj->getClassName(), sizeof(io_name_t));

	return kIOReturnSuccess;
}
```

### 2801: io_object_conforms_to

Test whether the object can be cast to the named runtime class.

**Mechanism:** Rejects a null input object and evaluates `object->metaCast(className)`. The Boolean result reports whether the runtime object conforms to the named class; a false result is still a successful RPC. The wrapper neither allocates a new instance nor returns a second object capability. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2565).

**Declarations:** [`io_object_conforms_to`](../../../platydoc-data/xnu/osfmk/device/device.defs#L156) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_object_conforms_to(
     object : io_object_t;
 in className : io_name_t;
 out conforms : boolean_t
 );
```

**Local body:** [`is_io_object_conforms_to`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2565).
Calls visible in this body include `metaCast`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2565-L2577):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2565-L2577 -->
```c
is_io_object_conforms_to(
	io_object_t object,
	io_name_t className,
	boolean_t *conforms )
{
	if (!object) {
		return kIOReturnBadArgument;
	}

	*conforms = (NULL != object->metaCast( className ));

	return kIOReturnSuccess;
}
```

### 2802: io_iterator_next

Return the next retained object from an exported IOKit iterator.

**Mechanism:** Distinguishes an `IOUserIterator`, whose `copyNextObject` already returns a retained object, from a plain `OSIterator`, whose borrowed `getNextObject` result is explicitly retained. Other objects yield `kIOReturnBadArgument`. A present result is handed to the output translation with success; exhaustion returns `kIOReturnNoDevice` rather than an unretained object. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2595).

**Declarations:** [`io_iterator_next`](../../../platydoc-data/xnu/osfmk/device/device.defs#L162) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_iterator_next(
     iterator : io_object_t;
 out object : io_object_t
 );
```

**Local body:** [`is_io_iterator_next`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2595).
Calls visible in this body include `OSDynamicCast`, `copyNextObject`, `getNextObject`, `retain`.

### 2803: io_iterator_reset

Reset an exported iterator's traversal position.

**Mechanism:** The `CHECK` macro requires an `OSIterator`; otherwise the RPC fails with a bad argument. The wrapper calls the iterator's virtual `reset` and returns success. Iterator-specific traversal invalidation, locking and retained collection behavior belong to that implementation rather than being independently reconstructed by this wrapper. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2627).

**Declarations:** [`io_iterator_reset`](../../../platydoc-data/xnu/osfmk/device/device.defs#L167) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_iterator_reset(
     iterator : io_object_t
 );
```

**Local body:** [`is_io_iterator_reset`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2627).
Calls visible in this body include `CHECK`, `reset`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2627-L2635):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2627-L2635 -->
```c
is_io_iterator_reset(
	io_object_t iterator )
{
	CHECK( OSIterator, iterator, iter );

	iter->reset();

	return kIOReturnSuccess;
}
```

### 2804: io_service_get_matching_services

Request an iterator over services matching a serialized property dictionary.

**Mechanism:** This exact legacy string-form body immediately returns `kIOReturnUnsupported`. The existence of similarly named binary or out-of-line forms does not make this declaration operational; no dictionary is parsed and no matching or notification registration is performed here. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2766).

**Declarations:** [`io_service_get_matching_services`](../../../platydoc-data/xnu/osfmk/device/device.defs#L171) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_services(
     main_port : mach_port_t;
 in matching : io_string_t;
 out existing : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_services`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2766).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2766-L2772):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2766-L2772 -->
```c
is_io_service_get_matching_services(
	mach_port_t main_port,
	io_string_t matching,
	io_iterator_t *existing )
{
	return kIOReturnUnsupported;
}
```

### 2805: io_registry_entry_get_property

Request a serialized value for one registry property, subject to property-access policy.

**Mechanism:** Requires a registry entry and passes the configured MAC property-read check. `IOCopyPropertyCompatible` returns a retained ordinary property or allowed compatibility-overlay value. The wrapper serializes it into `OSSerialize`, converts the serialized bytes to outgoing VM-copy data with `copyoutkdata`, and releases both objects. Missing properties, allocation failure and unsupported serialization have distinct errors. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3758).

**Declarations:** [`io_registry_entry_get_property`](../../../platydoc-data/xnu/osfmk/device/device.defs#L177) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_property(
     registry_entry : io_object_t;
 in property_name : io_name_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_property`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3758).
Calls visible in this body include `CHECK`, `mac_iokit_check_get_property`, `kauth_cred_get`, `IOCopyPropertyCompatible`, `withCapacity`, `release`, `serialize`, `getLength`, `copyoutkdata`, `text`.

### 2806: io_registry_create_iterator

Create a registry traversal iterator for the requested plane and options.

**Mechanism:** Requires the main-device port, resolves the named registry plane, and invokes `IORegistryIterator::iterateOver` with the requested options. The registry iterator is wrapped in `IOUserIterator` for export. A null result returns `kIOReturnBadArgument`; the wrapper does not itself walk the graph or return a snapshot array of all entries. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3342).

**Declarations:** [`io_registry_create_iterator`](../../../platydoc-data/xnu/osfmk/device/device.defs#L183) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_create_iterator(
     main_port : mach_port_t;
 in plane : io_name_t;
 in options : uint32_t;
 out iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_create_iterator`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3342).
Calls visible in this body include `withIterator`, `iterateOver`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3342-L3357):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3342-L3357 -->
```c
is_io_registry_create_iterator(
	mach_port_t main_port,
	io_name_t plane,
	uint32_t options,
	io_object_t *iterator )
{
	if (main_port != main_device_port) {
		return kIOReturnNotPrivileged;
	}

	*iterator = IOUserIterator::withIterator(
		IORegistryIterator::iterateOver(
			IORegistryEntry::getPlane( plane ), options ));

	return *iterator ? kIOReturnSuccess : kIOReturnBadArgument;
}
```

### 2807: io_registry_iterator_enter_entry

Descend into the current entry while holding the iterator's serialization lock.

**Mechanism:** The `CHECKLOCKED` path obtains an `IORegistryIterator` from the exported user iterator. The wrapper holds the enclosing iterator lock while calling `enterEntry`, then unlocks and returns success. This mutates traversal position; it does not attach the entry to a new registry plane. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3378).

**Declarations:** [`io_registry_iterator_enter_entry`](../../../platydoc-data/xnu/osfmk/device/device.defs#L190) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_iterator_enter_entry(
     iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_iterator_enter_entry`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3378).
Calls visible in this body include `CHECKLOCKED`, `IOLockLock`, `enterEntry`, `IOLockUnlock`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3378-L3388):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3378-L3388 -->
```c
is_io_registry_iterator_enter_entry(
	io_object_t iterator )
{
	CHECKLOCKED( IORegistryIterator, iterator, iter );

	IOLockLock(&oIter->lock);
	iter->enterEntry();
	IOLockUnlock(&oIter->lock);

	return kIOReturnSuccess;
}
```

### 2808: io_registry_iterator_exit_entry

Leave the current nested iterator traversal level.

**Mechanism:** After validating the wrapped registry iterator, it holds the user iterator lock around `exitEntry`. A successful ascent returns success; inability to exit the current traversal level returns `kIOReturnNoDevice`. Lock release occurs before either result is returned. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3392).

**Declarations:** [`io_registry_iterator_exit_entry`](../../../platydoc-data/xnu/osfmk/device/device.defs#L194) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_iterator_exit_entry(
     iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_iterator_exit_entry`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3392).
Calls visible in this body include `CHECKLOCKED`, `IOLockLock`, `exitEntry`, `IOLockUnlock`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3392-L3404):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3392-L3404 -->
```c
is_io_registry_iterator_exit_entry(
	io_object_t iterator )
{
	bool        didIt;

	CHECKLOCKED( IORegistryIterator, iterator, iter );

	IOLockLock(&oIter->lock);
	didIt = iter->exitEntry();
	IOLockUnlock(&oIter->lock);

	return didIt ? kIOReturnSuccess : kIOReturnNoDevice;
}
```

### 2809: io_registry_entry_from_path

Resolve a registry path to an exported entry, including the local compatibility lookup rules.

**Mechanism:** Requires `main_device_port` and calls `IORegistryEntry::fromPath`. If that fails and task registry compatibility is active, it builds a dictionary containing compatibility and path-match keys and asks `copyMatchingService` for a fallback. Temporary dictionary/string objects are released. The output may remain null while the wrapper still returns success. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3408).

**Declarations:** [`io_registry_entry_from_path`](../../../platydoc-data/xnu/osfmk/device/device.defs#L198) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_from_path(
     main_port : mach_port_t;
 in path : io_string_t;
 out registry_entry : io_object_t
 );
```

**Local body:** [`is_io_registry_entry_from_path`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3408).
Calls visible in this body include `fromPath`, `IOTaskRegistryCompatibility`, `current_task`, `withCStringNoCopy`, `withObjects`, `copyMatchingService`, `OSSafeReleaseNULL`.

### 2810: io_registry_entry_get_name

Copy the registry entry's name into the bounded output.

**Mechanism:** Requires an `IORegistryEntry` and copies `getName()` into the fixed `io_name_t` array using the body’s `strncpy`. It returns success without allocating or exporting another object. The result is a bounded name field; it is not a full path or an independently retained registry name object. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3579).

**Declarations:** [`io_registry_entry_get_name`](../../../platydoc-data/xnu/osfmk/device/device.defs#L204) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_name(
     registry_entry : io_object_t;
 out name : io_name_t
 );
```

**Local body:** [`is_io_registry_entry_get_name`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3579).
Calls visible in this body include `CHECK`, `strncpy`, `getName`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3579-L3588):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3579-L3588 -->
```c
is_io_registry_entry_get_name(
	io_object_t registry_entry,
	io_name_t name )
{
	CHECK( IORegistryEntry, registry_entry, entry );

	strncpy( name, entry->getName(), sizeof(io_name_t));

	return kIOReturnSuccess;
}
```

### 2811: io_registry_entry_get_properties

Request a serialized property dictionary for a registry entry.

**Mechanism:** This exact legacy body returns `kIOReturnUnsupported` immediately. It does not serialize the entry's dictionary. The binary variants below implement property-table export and filtering, so their behavior must not be attributed to this retained compatibility slot. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3851).

**Declarations:** [`io_registry_entry_get_properties`](../../../platydoc-data/xnu/osfmk/device/device.defs#L209) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_properties(
     registry_entry : io_object_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_properties`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3851).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3851-L3857):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3851-L3857 -->
```c
is_io_registry_entry_get_properties(
	io_object_t registry_entry,
	io_buf_ptr_t *properties,
	mach_msg_type_number_t *propertiesCnt )
{
	return kIOReturnUnsupported;
}
```

### 2812: io_registry_entry_get_property_bytes

Copy the bytes of an OSData property after property-access checks.

**Mechanism:** After entry/MAC validation, obtains a retained compatible property and exports only supported scalar/data forms: serializable `OSData`, string including null, Boolean as `Yes`/`No`, or the number's bounded byte width. Other object types return a bad argument. A too-small output buffer returns `kIOReturnIPCError`; the retained property is always released after conversion. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3684).

**Declarations:** [`io_registry_entry_get_property_bytes`](../../../platydoc-data/xnu/osfmk/device/device.defs#L214) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_property_bytes(
     registry_entry : io_object_t;
 in property_name : io_name_t;
 out data : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_registry_entry_get_property_bytes`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3684).
Calls visible in this body include `CHECK`, `mac_iokit_check_get_property`, `kauth_cred_get`, `IOCopyPropertyCompatible`, `OSDynamicCast`, `getLength`, `getBytesNoCopy`, `isSerializable`, `getCStringNoCopy`, `isTrue`, `unsigned64BitValue`, `numberOfBytes`.

### 2813: io_registry_entry_get_child_iterator

Create an iterator over the entry's children in the requested registry plane.

**Mechanism:** Requires an `IORegistryEntry`, resolves the requested plane, obtains the corresponding child or parent iterator, and wraps it with `IOUserIterator::withIterator` for export. The visible wrapper returns success without an explicit null-result test. Plane graph ownership and iterator invalidation remain in the registry/iterator implementations. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4220).

**Declarations:** [`io_registry_entry_get_child_iterator`](../../../platydoc-data/xnu/osfmk/device/device.defs#L220) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_child_iterator(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_entry_get_child_iterator`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4220).
Calls visible in this body include `CHECK`, `withIterator`, `getChildIterator`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4220-L4231):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4220-L4231 -->
```c
is_io_registry_entry_get_child_iterator(
	io_object_t registry_entry,
	io_name_t plane,
	io_object_t *iterator )
{
	CHECK( IORegistryEntry, registry_entry, entry );

	*iterator = IOUserIterator::withIterator(entry->getChildIterator(
		    IORegistryEntry::getPlane( plane )));

	return kIOReturnSuccess;
}
```

### 2814: io_registry_entry_get_parent_iterator

Create an iterator over the entry's parents in the requested registry plane.

**Mechanism:** Requires an `IORegistryEntry`, resolves the requested plane, obtains the corresponding child or parent iterator, and wraps it with `IOUserIterator::withIterator` for export. The visible wrapper returns success without an explicit null-result test. Plane graph ownership and iterator invalidation remain in the registry/iterator implementations. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4235).

**Declarations:** [`io_registry_entry_get_parent_iterator`](../../../platydoc-data/xnu/osfmk/device/device.defs#L226) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_parent_iterator(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_entry_get_parent_iterator`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4235).
Calls visible in this body include `CHECK`, `withIterator`, `getParentIterator`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4235-L4246):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4235-L4246 -->
```c
is_io_registry_entry_get_parent_iterator(
	io_object_t registry_entry,
	io_name_t plane,
	io_object_t *iterator)
{
	CHECK( IORegistryEntry, registry_entry, entry );

	*iterator = IOUserIterator::withIterator(entry->getParentIterator(
		    IORegistryEntry::getPlane( plane )));

	return kIOReturnSuccess;
}
```

### 2815: io_connect_map_shared_memory

**Interface contract:**

> >was< routine io_service_open

**Mechanism:** Requires a nonshared user client and the current task as target. Under the configured IPC gate, it gets `clientMemoryForType`, requires an `OSData` sharing context, checks writable-sharing entitlement and output-description capacity, then creates an anywhere mapping with permitted user options. Success exports address/size and stores the mapping in the client's set under `gIOObjectPortLock`, releasing the temporary mapping reference. Sharing-description copy and mapping creation are separate failure points. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4706).

**Declarations:** [`io_connect_map_shared_memory`](../../../platydoc-data/xnu/osfmk/device/device.defs#L233) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_map_shared_memory(
     connection : io_connect_t;
 in memory_type : uint32_t;
 in into_task : task_t;
 inout address : mach_vm_address_t;
 inout size : mach_vm_size_t;
 in flags : uint32_t;
 in property_name : io_name_t;
 out inband_output : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_connect_map_shared_memory`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4706).
Calls visible in this body include `CHECK`, `current_task`, `IOStatisticsClientCall`, `ipcEnter`, `clientMemoryForType`, `copySharingContext`, `OSDynamicCast`, `IOCurrentTaskHasEntitlement`, `getLength`, `memcpy`, `getBytesNoCopy`, `OSSafeReleaseNULL`.

### 2816: io_service_close

Close a user-client connection through its IPC admission and clientClose protocol.

**Mechanism:** An `OSSet` mapping capability is accepted as a compatibility no-op. Otherwise the object must be an `IOUserClient`. A shared instance or successful atomic closed-bit transition enters the write IPC gate and calls `clientClose`; repeated nonshared closes are logged and ignored. The wrapper returns success rather than propagating `clientClose`'s result. Closing the logical connection is distinct from deallocating its Mach send-right name. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4613).

**Declarations:** [`io_service_close`](../../../platydoc-data/xnu/osfmk/device/device.defs#L244) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_close(
     connection : io_connect_t
 );
```

**Local body:** [`is_io_service_close`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4613).
Calls visible in this body include `OSDynamicCast`, `CHECK`, `IOStatisticsClientCall`, `OSCompareAndSwap8`, `ipcEnter`, `clientClose`, `ipcExit`, `IOLog`, `is_io_service_close`, `getRegistryEntryID`, `getName`.

### 2817: io_connect_get_service

Obtain a retained service object associated with a user-client connection.

**Mechanism:** Requires an `IOUserClient`, enters its IPC lifetime gate with no client lock request and obtains `getService`. It retains a nonnull service before leaving the gate and assigning the output capability. Missing backing service returns unsupported; an existing service returns success with a reference suitable for outgoing object translation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4639).

**Declarations:** [`io_connect_get_service`](../../../platydoc-data/xnu/osfmk/device/device.defs#L248) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_get_service(
     connection : io_connect_t;
 out service : io_object_t
 );
```

**Local body:** [`is_io_connect_get_service`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4639).
Calls visible in this body include `CHECK`, `ipcEnter`, `getService`, `retain`, `ipcExit`.

### 2818: io_connect_set_notification_port

Register a notification port and reference value with a user client.

**Mechanism:** Requires an `IOUserClient`, records call statistics, enters the write IPC gate and invokes the driver's `registerNotificationPort` with notification type, port and reference. The older form widens its 32-bit reference; the 64-bit form passes the user reference directly. Gate exit precedes return of the driver's result. This registers a callback destination rather than immediately sending a notification. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4663).

**Declarations:** [`io_connect_set_notification_port`](../../../platydoc-data/xnu/osfmk/device/device.defs#L254) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_set_notification_port(
     connection : io_connect_t;
 in notification_type : uint32_t;
 in port : mach_port_make_send_t;
 in reference : uint32_t
 );
```

**Local body:** [`is_io_connect_set_notification_port`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4663).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `registerNotificationPort`, `ipcExit`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4663-L4680):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4663-L4680 -->
```c
is_io_connect_set_notification_port(
	io_connect_t connection,
	uint32_t notification_type,
	mach_port_t port,
	uint32_t reference)
{
	kern_return_t ret;
	CHECK( IOUserClient, connection, client );

	IOStatisticsClientCall();

	client->ipcEnter(kIPCLockWrite);
	ret = client->registerNotificationPort( port, notification_type,
	    (io_user_reference_t) reference );
	client->ipcExit(kIPCLockWrite);

	return ret;
}
```

### 2819: io_connect_map_memory

Map a user client's selected memory type into a task and return address and size using this ABI's widths.

**Mechanism:** Widens the input 32-bit address and size using `SCALAR64`, delegates to `is_io_connect_map_memory_into_task`, and narrows the resulting values using `SCALAR32` before returning the delegated status. Thus mapping ownership, target-task admission and IPC gating are inherited from the wide implementation; this compatibility wrapper does not implement an independent physical-memory mapping path or explicit overflow-result branch. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4859).

**Declarations:** [`io_connect_map_memory`](../../../platydoc-data/xnu/osfmk/device/device.defs#L261) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_map_memory(
     connection : io_connect_t;
 in memory_type : uint32_t;
 in into_task : task_t;
 inout address : uint32_t;
 inout size : uint32_t;
 in flags : uint32_t
 );
```

**Local body:** [`is_io_connect_map_memory`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4859).
Calls visible in this body include `SCALAR64`, `is_io_connect_map_memory_into_task`, `SCALAR32`.

### 2820: io_connect_add_client

Ask one user client to connect another client object.

**Mechanism:** Requires both capabilities to identify `IOUserClient` objects. The initiating client enters its configured write-or-none IPC gate, calls its virtual `connectClient` with the second client, exits the gate and returns the method's status. The wrapper does not itself merge the clients' mappings or owners; any connection-specific relationship is implemented by that virtual method. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4994).

**Declarations:** [`io_connect_add_client`](../../../platydoc-data/xnu/osfmk/device/device.defs#L279) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_add_client(
     connection : io_connect_t;
 in connect_to : io_connect_t
 );
```

**Local body:** [`is_io_connect_add_client`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4994).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `connectClient`, `ipcExit`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4994-L5010):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4994-L5010 -->
```c
is_io_connect_add_client(
	io_connect_t connection,
	io_object_t connect_to)
{
	CHECK( IOUserClient, connection, client );
	CHECK( IOUserClient, connect_to, to );

	IOReturn ret;

	IOStatisticsClientCall();

	client->ipcEnter(client->defaultLocking ? kIPCLockWrite : kIPCLockNone);
	ret = client->connectClient( to );
	client->ipcExit(client->defaultLocking ? kIPCLockWrite : kIPCLockNone);

	return ret;
}
```

### 2821: io_connect_set_properties

Apply serialized properties to a connection through the registry-property setter.

**Mechanism:** Directly delegates the connection capability and OOL property payload to `is_io_registry_entry_set_properties`. That shared path handles VM-copy consumption, object parsing, MAC/allowable-key policy, locking and `setProperties`/DriverKit forwarding. Consequently operation failure can be reported through the separate `result` after successful consumption rather than by failing the outer RPC. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5015).

**Declarations:** [`io_connect_set_properties`](../../../platydoc-data/xnu/osfmk/device/device.defs#L284) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_set_properties(
     connection : io_connect_t;
 in properties : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t
 );
```

**Local body:** [`is_io_connect_set_properties`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5015).
Calls visible in this body include `is_io_registry_entry_set_properties`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5015-L5022):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5015-L5022 -->
```c
is_io_connect_set_properties(
	io_connect_t connection,
	io_buf_ptr_t properties,
	mach_msg_type_number_t propertiesCnt,
	kern_return_t * result)
{
	return is_io_registry_entry_set_properties( connection, properties, propertiesCnt, result );
}
```

### 2822: io_connect_method_scalarI_scalarO

Adapt legacy scalar input/scalar output arrays to the common synchronous user-client method path.

**Mechanism:** Widens the legacy scalar input array to 64-bit words and zeroes a temporary wide output array. It delegates to `is_io_connect_method` with no structure or OOL buffers, then narrows the returned scalar words using the updated output count, returning the shared method status. Selector validation, policy and IPC gating remain in the shared dispatch path rather than this ABI adapter. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5350).

**Declarations:** [`io_connect_method_scalarI_scalarO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L291) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method_scalarI_scalarO(
     connection : io_connect_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 out output : io_scalar_inband_t, CountInOut
 );
```

**Local body:** [`is_io_connect_method_scalarI_scalarO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5350).
Calls visible in this body include `bzero`, `SCALAR64`, `is_io_connect_method`, `SCALAR32`.

### 2823: io_connect_method_scalarI_structureO

Adapt legacy scalar inputs and structure output to the common synchronous method path.

**Mechanism:** Widens legacy scalar inputs and calls the unified synchronous method path with the in-band structure output and its capacity/count pointer. Scalar output and OOL sizes are explicitly zero. The driver-updated structure size comes back through the original count pointer; policy and selector behavior are inherited from `is_io_connect_method` and the selected client's implementation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5733).

**Declarations:** [`io_connect_method_scalarI_structureO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L298) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method_scalarI_structureO(
     connection : io_connect_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 out output : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_connect_method_scalarI_structureO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5733).
Calls visible in this body include `SCALAR64`, `is_io_connect_method`.

### 2824: io_connect_method_scalarI_structureI

Adapt legacy scalar and structure inputs to the common synchronous method path.

**Mechanism:** Widens legacy scalar input words, forwards the supplied in-band input structure, and initializes all output counts to zero before calling `is_io_connect_method`. This form has no scalar, structure or OOL output payload. It still uses the shared external-method filter, client gate and driver selector dispatch; a successful RPC need not imply any generic kernel-side state change beyond the driver's chosen operation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5906).

**Declarations:** [`io_connect_method_scalarI_structureI`](../../../platydoc-data/xnu/osfmk/device/device.defs#L305) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method_scalarI_structureI(
     connection : io_connect_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 in inputStruct : io_struct_inband_t
 );
```

**Local body:** [`is_io_connect_method_scalarI_structureI`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5906).
Calls visible in this body include `SCALAR64`, `is_io_connect_method`.

### 2825: io_connect_method_structureI_structureO

Adapt legacy structure input/output to the common synchronous method path.

**Mechanism:** Adapts the legacy in-band structure-input/structure-output form to `is_io_connect_method`, with scalar input absent and scalar/OOL output counts zero. The shared dispatcher receives the actual structure buffers and sizes and updates the output count. Any legacy target-method shape validation occurs below that common path, not in a new independent implementation of the selector. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6083).

**Declarations:** [`io_connect_method_structureI_structureO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L312) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method_structureI_structureO(
     connection : io_connect_t;
 in selector : uint32_t;
 in input : io_struct_inband_t;
 out output : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_connect_method_structureI_structureO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6083).
Calls visible in this body include `is_io_connect_method`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6083-L6101):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6083-L6101 -->
```c
is_io_connect_method_structureI_structureO(
	io_object_t     connect,
	uint32_t        index,
	io_struct_inband_t              input,
	mach_msg_type_number_t  inputCount,
	io_struct_inband_t              output,
	mach_msg_type_number_t *        outputCount )
{
	mach_msg_type_number_t scalar_outputCnt = 0;
	mach_vm_size_t ool_output_size = 0;

	return is_io_connect_method(connect, index,
	           NULL, 0,
	           input, inputCount,
	           0, 0,
	           output, outputCount,
	           NULL, &scalar_outputCnt,
	           0, &ool_output_size);
}
```

### 2826: io_registry_entry_get_path

Copy an entry's path in a specified registry plane into the bounded output buffer.

**Mechanism:** Requires an `IORegistryEntry` and supplies the fixed `io_string_t` capacity to `getPath` for the named plane. Successful formatting returns success; failure returns `kIOReturnBadArgument`. No second larger buffer or partial-path recovery is attempted by this legacy fixed-size form. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3520).

**Declarations:** [`io_registry_entry_get_path`](../../../platydoc-data/xnu/osfmk/device/device.defs#L325) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_path(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out path : io_string_t
 );
```

**Local body:** [`is_io_registry_entry_get_path`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3520).
Calls visible in this body include `CHECK`, `getPath`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3520-L3534):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3520-L3534 -->
```c
is_io_registry_entry_get_path(
	io_object_t registry_entry,
	io_name_t plane,
	io_string_t path )
{
	int         length;
	CHECK( IORegistryEntry, registry_entry, entry );

	length = sizeof(io_string_t);
	if (entry->getPath( path, &length, IORegistryEntry::getPlane( plane ))) {
		return kIOReturnSuccess;
	} else {
		return kIOReturnBadArgument;
	}
}
```

### 2827: io_registry_get_root_entry

Return a retained registry root object.

**Mechanism:** Requires `main_device_port`, obtains the registry root and explicitly retains it if present before assigning the object output. The wrapper returns success even if the root pointer is null. The retained nonnull object is supplied to the outgoing object/capability translation rather than exposed as a raw kernel pointer. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3321).

**Declarations:** [`io_registry_get_root_entry`](../../../platydoc-data/xnu/osfmk/device/device.defs#L331) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_get_root_entry(
     main_port : mach_port_t;
 out root : io_object_t
 );
```

**Local body:** [`is_io_registry_get_root_entry`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3321).
Calls visible in this body include `getRegistryRoot`, `retain`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3321-L3338):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3321-L3338 -->
```c
is_io_registry_get_root_entry(
	mach_port_t main_port,
	io_object_t *root )
{
	IORegistryEntry *   entry;

	if (main_port != main_device_port) {
		return kIOReturnNotPrivileged;
	}

	entry = IORegistryEntry::getRegistryRoot();
	if (entry) {
		entry->retain();
	}
	*root = entry;

	return kIOReturnSuccess;
}
```

### 2828: io_registry_entry_set_properties

Copy in and deserialize the supplied property representation, apply policy, and invoke the entry's property setter.

**Mechanism:** Bounds and consumes the OOL VM copy, unserializes it and deallocates mapped bytes. It checks MAC policy and any allowable-key array before dispatching `setProperties`, with user-client or property-action locking selected by the entry's settings. DriverKit services can then invoke `UserSetProperties`. Parsed objects and allowable-key references are released. Once the input copy is consumed, operation status goes in `result`, while the outer return reflects copy consumption. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4106).

**Declarations:** [`io_registry_entry_set_properties`](../../../platydoc-data/xnu/osfmk/device/device.defs#L336) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_set_properties(
     registry_entry : io_object_t;
 in properties : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t
 );
```

**Local body:** [`is_io_registry_entry_set_properties`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4106).
Calls visible in this body include `CHECK`, `vm_map_copyout`, `CAST_DOWN`, `FAKE_STACK_FRAME`, `getMetaClass`, `OSUnserializeXML`, `vm_deallocate`, `mac_iokit_check_set_properties`, `kauth_cred_get`, `OSDynamicCast`, `copyProperty`, `iterateObjects`.

### 2829: io_registry_entry_in_plane

Test whether the entry belongs to the named registry plane.

**Mechanism:** Requires an `IORegistryEntry`, resolves the named plane and calls `inPlane` on that entry. The output Boolean reports membership with RPC success. The wrapper neither traverses parents nor rewrites graph relationships; interpretation of a missing plane is delegated to the registry operation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3505).

**Declarations:** [`io_registry_entry_in_plane`](../../../platydoc-data/xnu/osfmk/device/device.defs#L342) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_in_plane(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out inPlane : boolean_t
 );
```

**Local body:** [`is_io_registry_entry_in_plane`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3505).
Calls visible in this body include `CHECK`, `inPlane`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3505-L3515):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3505-L3515 -->
```c
is_io_registry_entry_in_plane(
	io_object_t registry_entry,
	io_name_t plane,
	boolean_t *inPlane )
{
	CHECK( IORegistryEntry, registry_entry, entry );

	*inPlane = entry->inPlane( IORegistryEntry::getPlane( plane ));

	return kIOReturnSuccess;
}
```

### 2830: io_object_get_retain_count

Report the object's reference count at the point of inspection; this value does not confer ownership.

**Mechanism:** Rejects a null input and reads `getRetainCount` into the scalar result. This is a diagnostic snapshot of the runtime object's reference count while the call holds its input object; it is not a Mach send-right user-reference count and does not itself change ownership. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2581).

**Declarations:** [`io_object_get_retain_count`](../../../platydoc-data/xnu/osfmk/device/device.defs#L348) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_object_get_retain_count(
     object : io_object_t;
 out retainCount : uint32_t
 );
```

**Local body:** [`is_io_object_get_retain_count`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2581).
Calls visible in this body include `getRetainCount`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2581-L2591):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2581-L2591 -->
```c
is_io_object_get_retain_count(
	io_object_t object,
	uint32_t *retainCount )
{
	if (!object) {
		return kIOReturnBadArgument;
	}

	*retainCount = object->getRetainCount();
	return kIOReturnSuccess;
}
```

### 2831: io_service_get_busy_state

Read the service's current busy count/state.

**Mechanism:** Requires an `IOService` and exports `getBusyState` as a scalar. This reads the service's busy accounting; it does not wait for matching/configuration to complete and does not itself acquire a termination claim. The wrapper returns success with whatever value the service method supplies. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4250).

**Declarations:** [`io_service_get_busy_state`](../../../platydoc-data/xnu/osfmk/device/device.defs#L353) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_busy_state(
     service : io_object_t;
 out busyState : uint32_t
 );
```

**Local body:** [`is_io_service_get_busy_state`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4250).
Calls visible in this body include `CHECK`, `getBusyState`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4250-L4259):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4250-L4259 -->
```c
is_io_service_get_busy_state(
	io_object_t _service,
	uint32_t *busyState )
{
	CHECK( IOService, _service, service );

	*busyState = service->getBusyState();

	return kIOReturnSuccess;
}
```

### 2832: io_service_wait_quiet

Wait for a service to become quiet, using the supplied timeout.

**Mechanism:** Requires an `IOService`, converts the supplied seconds/nanoseconds pair to a 64-bit nanosecond timeout, then returns `service->waitQuiet(timeoutNS)`. Busy-state waiting and timeout handling occur in that service method. The wrapper does not drain a specific workloop or independently acknowledge power notifications. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4280).

**Declarations:** [`io_service_wait_quiet`](../../../platydoc-data/xnu/osfmk/device/device.defs#L358) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_wait_quiet(
     service : io_object_t;
     wait_time : mach_timespec_t
 );
```

**Local body:** [`is_io_service_wait_quiet`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4280).
Calls visible in this body include `CHECK`, `waitQuiet`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4280-L4293):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4280-L4293 -->
```c
is_io_service_wait_quiet(
	io_object_t _service,
	mach_timespec_t wait_time )
{
	uint64_t    timeoutNS;

	CHECK( IOService, _service, service );

	timeoutNS = wait_time.tv_sec;
	timeoutNS *= kSecondScale;
	timeoutNS += wait_time.tv_nsec;

	return service->waitQuiet(timeoutNS);
}
```

### 2833: io_registry_entry_create_iterator

Create a traversal iterator rooted at this entry in the requested plane.

**Mechanism:** Requires an `IORegistryEntry` capability and constructs traversal from that entry in the named plane with the caller's options. `IOUserIterator::withIterator` supplies the exported wrapper; failure yields `kIOReturnBadArgument`. This anchors iteration at an already authorized object rather than requiring the global main-device port. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3361).

**Declarations:** [`io_registry_entry_create_iterator`](../../../platydoc-data/xnu/osfmk/device/device.defs#L363) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_create_iterator(
     registry_entry : io_object_t;
 in plane : io_name_t;
 in options : uint32_t;
 out iterator : io_object_t
 );
```

**Local body:** [`is_io_registry_entry_create_iterator`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3361).
Calls visible in this body include `CHECK`, `withIterator`, `iterateOver`, `getPlane`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3361-L3374):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3361-L3374 -->
```c
is_io_registry_entry_create_iterator(
	io_object_t registry_entry,
	io_name_t plane,
	uint32_t options,
	io_object_t *iterator )
{
	CHECK( IORegistryEntry, registry_entry, entry );

	*iterator = IOUserIterator::withIterator(
		IORegistryIterator::iterateOver( entry,
		IORegistryEntry::getPlane( plane ), options ));

	return *iterator ? kIOReturnSuccess : kIOReturnBadArgument;
}
```

### 2834: io_iterator_is_valid

Test whether registry mutation has invalidated the iterator.

**Mechanism:** Requires an `OSIterator`, reads its virtual `isValid` result and returns that Boolean with RPC success. Invalid traversal state is therefore represented in the output value, not as a generic transport failure; callers can decide whether to reset or discard the iterator. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2639).

**Declarations:** [`io_iterator_is_valid`](../../../platydoc-data/xnu/osfmk/device/device.defs#L370) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_iterator_is_valid(
     iterator : io_object_t;
 out is_valid : boolean_t
 );
```

**Local body:** [`is_io_iterator_is_valid`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2639).
Calls visible in this body include `CHECK`, `isValid`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2639-L2648):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2639-L2648 -->
```c
is_io_iterator_is_valid(
	io_object_t iterator,
	boolean_t *is_valid )
{
	CHECK( OSIterator, iterator, iter );

	*is_valid = iter->isValid();

	return kIOReturnSuccess;
}
```

### 2835: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/device/device.defs#L375).

### 2836: io_catalog_send_data

**Interface contract:**

> was routine io_make_matching( main_port : mach_port_t; in of_type : uint32_t; in options : uint32_t; in input : io_struct_inband_t; out matching : io_string_t );

**Mechanism:** Under production `NO_KEXTD`, returns not-privileged. Otherwise it requires the main port and command-appropriate data; missing management entitlement intentionally returns outer success without applying changes. Input VM-copy data is bounded, consumed, parsed and unmapped. The command switch calls catalogue reset/add/remove-driver operations, optionally starting matching; removed/kextd-state commands return unsupported. After copy consumption, operation status is returned through `result` and the parsed object is released. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6205).

**Declarations:** [`io_catalog_send_data`](../../../platydoc-data/xnu/osfmk/device/device.defs#L385) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_send_data(
     main_port : mach_port_t;
        in flag : uint32_t;
 in inData : io_buf_ptr_t;
        out result : kern_return_t
 );
```

**Local body:** [`is_io_catalog_send_data`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6205).
Calls visible in this body include `IOCurrentTaskHasEntitlement`, `IOCopyLogNameForPID`, `proc_selfpid`, `IOLog`, `IOCatalogueSendData`, `getCStringNoCopy`, `OSSafeReleaseNULL`, `vm_map_copyout`, `CAST_DOWN`, `OSUnserializeXML`, `vm_deallocate`, `OSDynamicCast`.

### 2837: io_catalog_terminate

Request termination of matching drivers or a module after privilege checks.

**Mechanism:** Requires the main-device port and administrator privilege. Outside `SECURE_KERNEL`, the flag selects `terminateDrivers` for a named service or `terminateDriversForModule`, with module-unload determining whether unloading is requested. Unsupported flags, including the excluded commands in secure builds, return bad argument. Termination coordination is delegated to the catalogue rather than completed by merely decoding the request. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6340).

**Declarations:** [`io_catalog_terminate`](../../../platydoc-data/xnu/osfmk/device/device.defs#L392) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_terminate(
     main_port : mach_port_t;
        in flag : uint32_t;
 in name : io_name_t
 );
```

**Local body:** [`is_io_catalog_terminate`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6340).
Calls visible in this body include `clientHasPrivilege`, `current_task`, `terminateDrivers`, `terminateDriversForModule`.

### 2838: io_catalog_get_data

Serialize selected driver-catalogue data and return it through VM-backed output memory.

**Mechanism:** Requires the main-device port, creates a serializer and invokes `gIOCatalogue->serializeData(flag, ...)`. On success it allocates tagged kernel VM, copies serialized bytes there and uses `vm_map_copyin` with source destruction to construct the outgoing OOL result. Serializer allocation, catalogue selection, VM allocation and VM-copy conversion can fail separately; the serializer is released before return. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6380).

**Declarations:** [`io_catalog_get_data`](../../../platydoc-data/xnu/osfmk/device/device.defs#L398) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_get_data(
     main_port : mach_port_t;
        in flag : uint32_t;
 out outData : io_buf_ptr_t
 );
```

**Local body:** [`is_io_catalog_get_data`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6380).
Calls visible in this body include `withCapacity`, `serializeData`, `getLength`, `mach_vm_allocate_kernel`, `VM_MAP_KERNEL_FLAGS_ANYWHERE`, `bcopy`, `text`, `vm_map_copyin`, `release`.

### 2839: io_catalog_get_gen_count

Return the matching catalogue's generation counter.

**Mechanism:** Requires the main-device port and a nonnull output pointer, then reads `gIOCatalogue->getGenerationCount` into the result. This reports catalogue generation rather than returning matching services or a versioned property snapshot. The wrapper does not hold a collection iterator or trigger driver matching as a side effect. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6425).

**Declarations:** [`io_catalog_get_gen_count`](../../../platydoc-data/xnu/osfmk/device/device.defs#L404) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_get_gen_count(
     main_port : mach_port_t;
        out genCount : uint32_t
 );
```

**Local body:** [`is_io_catalog_get_gen_count`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6425).
Calls visible in this body include `getGenerationCount`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6425-L6442):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6425-L6442 -->
```c
is_io_catalog_get_gen_count(
	mach_port_t             main_port,
	uint32_t                *genCount)
{
	if (main_port != main_device_port) {
		return kIOReturnNotPrivileged;
	}

	//printf("io_catalog_get_gen_count called.\n");

	if (!genCount) {
		return kIOReturnBadArgument;
	}

	*genCount = gIOCatalogue->getGenerationCount();

	return kIOReturnSuccess;
}
```

### 2840: io_catalog_module_loaded

Notify the catalogue that a named module has loaded.

**Mechanism:** Requires the main-device port and a nonnull module name, calls `gIOCatalogue->moduleHasLoaded(name)` and returns success. The wrapper is a notification to catalogue matching machinery; it does not load module bytes, validate a code signature, or prove a requested module actually became executable. Those actions belong to other paths. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6448).

**Declarations:** [`io_catalog_module_loaded`](../../../platydoc-data/xnu/osfmk/device/device.defs#L409) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_module_loaded(
     main_port : mach_port_t;
 in name : io_name_t
 );
```

**Local body:** [`is_io_catalog_module_loaded`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6448).
Calls visible in this body include `moduleHasLoaded`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6448-L6465):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6448-L6465 -->
```c
is_io_catalog_module_loaded(
	mach_port_t             main_port,
	io_name_t               name)
{
	if (main_port != main_device_port) {
		return kIOReturnNotPrivileged;
	}

	//printf("io_catalog_module_loaded called. name %s\n", name);

	if (!name) {
		return kIOReturnBadArgument;
	}

	gIOCatalogue->moduleHasLoaded(name);

	return kIOReturnSuccess;
}
```

### 2841: io_catalog_reset

Reset or restart catalogue matching according to the supplied flag.

**Mechanism:** Requires the main-device port and recognizes only `kIOCatalogResetDefault`. That selector calls `gIOCatalogue->reset` and the wrapper returns success; all other flags yield bad argument. Unlike adjacent catalogue operations, this visible wrapper contains no separate administrator or management-entitlement check, so its actual admission must be read with the capability boundary rather than inferred from neighboring handlers. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6468).

**Declarations:** [`io_catalog_reset`](../../../platydoc-data/xnu/osfmk/device/device.defs#L414) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_catalog_reset(
     main_port : mach_port_t;
 in flag : uint32_t
 );
```

**Local body:** [`is_io_catalog_reset`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6468).
Calls visible in this body include `reset`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6468-L6486):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6468-L6486 -->
```c
is_io_catalog_reset(
	mach_port_t             main_port,
	uint32_t                flag)
{
	if (main_port != main_device_port) {
		return kIOReturnNotPrivileged;
	}

	switch (flag) {
	case kIOCatalogResetDefault:
		gIOCatalogue->reset();
		break;

	default:
		return kIOReturnBadArgument;
	}

	return kIOReturnSuccess;
}
```

### 2842: io_service_request_probe

Invoke the service's probe request operation with the supplied options.

**Mechanism:** Requires an `IOService` and forwards the option bits to its virtual `requestProbe`, returning the result directly. This is a driver/service probe request, not a direct instruction to instantiate every matching personality. Supported options and effects depend on the selected service implementation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4325).

**Declarations:** [`io_service_request_probe`](../../../platydoc-data/xnu/osfmk/device/device.defs#L419) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_request_probe(
     service : io_object_t;
 in options : uint32_t
 );
```

**Local body:** [`is_io_service_request_probe`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4325).
Calls visible in this body include `CHECK`, `requestProbe`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4325-L4332):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4325-L4332 -->
```c
is_io_service_request_probe(
	io_object_t _service,
	uint32_t options )
{
	CHECK( IOService, _service, service );

	return service->requestProbe( options );
}
```

### 2843: io_registry_entry_get_name_in_plane

Copy the entry's name as represented in a selected registry plane.

**Mechanism:** Requires an `IORegistryEntry`; a nonempty plane name is resolved, while an empty name passes a null plane. It copies the selected `getName(plane)` into the fixed output with `strncpy`. This asks for the registry entry's name in that context without traversing or changing its plane membership. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3592).

**Declarations:** [`io_registry_entry_get_name_in_plane`](../../../platydoc-data/xnu/osfmk/device/device.defs#L424) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_name_in_plane(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out name : io_name_t
 );
```

**Local body:** [`is_io_registry_entry_get_name_in_plane`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3592).
Calls visible in this body include `CHECK`, `getPlane`, `strncpy`, `getName`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3592-L3609):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3592-L3609 -->
```c
is_io_registry_entry_get_name_in_plane(
	io_object_t registry_entry,
	io_name_t planeName,
	io_name_t name )
{
	const IORegistryPlane * plane;
	CHECK( IORegistryEntry, registry_entry, entry );

	if (planeName[0]) {
		plane = IORegistryEntry::getPlane( planeName );
	} else {
		plane = NULL;
	}

	strncpy( name, entry->getName( plane), sizeof(io_name_t));

	return kIOReturnSuccess;
}
```

### 2844: io_service_match_property_table

Test a service against a serialized matching dictionary.

**Mechanism:** This exact legacy string-form body immediately returns `kIOReturnUnsupported`. The existence of similarly named binary or out-of-line forms does not make this declaration operational; no dictionary is parsed and no matching or notification registration is performed here. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2685).

**Declarations:** [`io_service_match_property_table`](../../../platydoc-data/xnu/osfmk/device/device.defs#L430) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_match_property_table(
     service : io_object_t;
 in matching : io_string_t;
 out matches : boolean_t
 );
```

**Local body:** [`is_io_service_match_property_table`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2685).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2685-L2691):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2685-L2691 -->
```c
is_io_service_match_property_table(
	io_service_t service,
	io_string_t matching,
	boolean_t *matches )
{
	return kIOReturnUnsupported;
}
```

### 2845: io_async_method_scalarI_scalarO

Adapt legacy scalar arguments and asynchronous reference values to the common asynchronous user-client method path.

**Mechanism:** Checks the legacy async-reference count, widens supplied reference words and zero-pads unused slots. It widens scalar inputs, zeroes a wide output array and calls the unified async method with no structure/OOL buffers. Returned scalar words are narrowed using the updated count. The common async path rewrites reference word zero with the wake port and performs policy/dispatch; later notification lifetime remains a separate concern. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5464).

**Declarations:** [`io_async_method_scalarI_scalarO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L437) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_async_method_scalarI_scalarO(
     connection : io_connect_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 out output : io_scalar_inband_t, CountInOut
 );
```

**Local body:** [`is_io_async_method_scalarI_scalarO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5464).
Calls visible in this body include `bzero`, `REF64`, `SCALAR64`, `is_io_connect_async_method`, `SCALAR32`.

### 2846: io_async_method_scalarI_structureO

Adapt legacy scalar inputs and structure output to asynchronous user-client dispatch.

**Mechanism:** Bounds and widens/zero-pads the legacy async references, widens scalar inputs and delegates to `is_io_connect_async_method` with an in-band structure output. Scalar output and OOL counts start at zero. The shared path records the wake port, applies async policy and invokes the client's method, while the caller's structure output count carries the synchronous reply size. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5515).

**Declarations:** [`io_async_method_scalarI_structureO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L445) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_async_method_scalarI_structureO(
     connection : io_connect_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 out output : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_async_method_scalarI_structureO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5515).
Calls visible in this body include `REF64`, `bzero`, `SCALAR64`, `is_io_connect_async_method`.

### 2847: io_async_method_scalarI_structureI

Adapt legacy scalar and structure inputs to asynchronous user-client dispatch.

**Mechanism:** Bounds, widens and zero-pads the async-reference array, widens scalar inputs and forwards the in-band input structure. It initializes all output counts to zero and calls the shared async method. This wrapper packages a legacy input-only method call; it does not itself send an asynchronous completion or retain an arbitrary userspace buffer after return. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5558).

**Declarations:** [`io_async_method_scalarI_structureI`](../../../platydoc-data/xnu/osfmk/device/device.defs#L453) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_async_method_scalarI_structureI(
     connection : io_connect_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 in selector : uint32_t;
 in input : io_scalar_inband_t;
 in inputStruct : io_struct_inband_t
 );
```

**Local body:** [`is_io_async_method_scalarI_structureI`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5558).
Calls visible in this body include `REF64`, `bzero`, `SCALAR64`, `is_io_connect_async_method`.

### 2848: io_async_method_structureI_structureO

Adapt legacy structure inputs/output and notification references to asynchronous user-client dispatch.

**Mechanism:** Validates and widens/zero-pads the legacy async references, then supplies in-band structure input/output to the unified async method with no scalar buffers and no OOL output. The output count is passed through to receive the driver's synchronous structure length. Wake-port encoding, filtering, client gating and any later asynchronous notification use the shared implementation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5602).

**Declarations:** [`io_async_method_structureI_structureO`](../../../platydoc-data/xnu/osfmk/device/device.defs#L461) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_async_method_structureI_structureO(
     connection : io_connect_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 in selector : uint32_t;
 in input : io_struct_inband_t;
 out output : io_struct_inband_t, CountInOut
 );
```

**Local body:** [`is_io_async_method_structureI_structureO`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5602).
Calls visible in this body include `REF64`, `bzero`, `is_io_connect_async_method`.

### 2849: io_service_add_notification

Register a matching notification and return its exported notification/iterator object.

**Mechanism:** This exact legacy string-form body immediately returns `kIOReturnUnsupported`. The existence of similarly named binary or out-of-line forms does not make this declaration operational; no dictionary is parsed and no matching or notification registration is performed here. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2995).

**Declarations:** [`io_service_add_notification`](../../../platydoc-data/xnu/osfmk/device/device.defs#L477) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_string_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2995).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2995-L3005):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2995-L3005 -->
```c
is_io_service_add_notification(
	mach_port_t main_port,
	io_name_t notification_type,
	io_string_t matching,
	mach_port_t port,
	io_async_ref_t reference,
	mach_msg_type_number_t referenceCnt,
	io_object_t * notification )
{
	return kIOReturnUnsupported;
}
```

### 2850: io_service_add_interest_notification

Register a service-interest callback using a notification port and asynchronous references.

**Mechanism:** Validates and zero-pads the appropriate async-reference width, requires an `IOService`, interns the interest name, and builds an `IOServiceMessageUserNotification` around the supplied port. `registerInterest` supplies the notifier retained by that wrapper; failure invalidates the port and releases it. The common body also contains WatchOS power-interest entitlement checking, with enforcement controlled by `gEnforcePowerEntitlement`. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3244).

**Declarations:** [`io_service_add_interest_notification`](../../../platydoc-data/xnu/osfmk/device/device.defs#L485) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_interest_notification(
     service : io_object_t;
 in type_of_interest : io_name_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 out notification : io_object_t
        );
```

**Local body:** [`is_io_service_add_interest_notification`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3244).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_interest_notification`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3244-L3262):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3244-L3262 -->
```c
is_io_service_add_interest_notification(
	io_object_t service,
	io_name_t type_of_interest,
	mach_port_t port,
	io_async_ref_t reference,
	mach_msg_type_number_t referenceCnt,
	io_object_t * notification )
{
	io_async_ref_t zreference;

	if (referenceCnt > ASYNC_REF_COUNT) {
		return kIOReturnBadArgument;
	}
	bcopy(&reference[0], &zreference[0], referenceCnt * sizeof(zreference[0]));
	bzero(&zreference[referenceCnt], (ASYNC_REF_COUNT - referenceCnt) * sizeof(zreference[0]));

	return internal_io_service_add_interest_notification(service, type_of_interest,
	           port, &zreference[0], sizeof(io_async_ref_t), false, notification);
}
```

### 2851: io_service_acknowledge_notification

Acknowledge a notification through the target service's callback.

**Mechanism:** Requires an `IOService`, converts the numeric notification reference into `IONotificationRef` and passes the response bits to the service's virtual `acknowledgeNotification`. The wrapper returns that operation's result directly. It does not validate acknowledgement state itself or treat the reference as a Mach port name. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3289).

**Declarations:** [`io_service_acknowledge_notification`](../../../platydoc-data/xnu/osfmk/device/device.defs#L492) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_acknowledge_notification(
           service : io_object_t;
       in notify_ref : natural_t;
       in response : natural_t
        );
```

**Local body:** [`is_io_service_acknowledge_notification`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3289).
Calls visible in this body include `CHECK`, `acknowledgeNotification`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3289-L3298):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3289-L3298 -->
```c
is_io_service_acknowledge_notification(
	io_object_t _service,
	natural_t notify_ref,
	natural_t response )
{
	CHECK( IOService, _service, service );

	return service->acknowledgeNotification((IONotificationRef)(uintptr_t) notify_ref,
	           (IOOptionBits) response );
}
```

### 2852: io_connect_get_notification_semaphore

Obtain a user-client notification semaphore for the selected notification type.

**Mechanism:** Requires an `IOUserClient`, records client-call statistics and enters its write IPC gate. It delegates the requested notification type to `getNotificationSemaphore`, exits the gate and returns the driver's result. The output semaphore is a separate kernel object translated by MIG; the wrapper does not create a generic semaphore for every notification type. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3302).

**Declarations:** [`io_connect_get_notification_semaphore`](../../../platydoc-data/xnu/osfmk/device/device.defs#L503) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_get_notification_semaphore(
     connection : io_connect_t;
 in notification_type : natural_t;
 out semaphore : semaphore_t
 );
```

**Local body:** [`is_io_connect_get_notification_semaphore`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3302).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `getNotificationSemaphore`, `ipcExit`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3302-L3317):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3302-L3317 -->
```c
is_io_connect_get_notification_semaphore(
	io_connect_t connection,
	natural_t notification_type,
	semaphore_t *semaphore )
{
	IOReturn ret;
	CHECK( IOUserClient, connection, client );

	IOStatisticsClientCall();
	client->ipcEnter(kIPCLockWrite);
	ret = client->getNotificationSemaphore((UInt32) notification_type,
	    semaphore );
	client->ipcExit(kIPCLockWrite);

	return ret;
}
```

### 2853: io_connect_unmap_memory

Unmap a selected user-client memory mapping from a task using the legacy-width adapter.

**Mechanism:** This compatibility wrapper forwards the supplied 32-bit address, task and memory type to `is_io_connect_unmap_memory_from_task`. The wide routine performs descriptor lookup, reference-mapping lookup, client-set removal and exported-port cleanup. The local temporary widened address does not create another mapping or change the argument actually passed to the wide helper. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4975).

**Declarations:** [`io_connect_unmap_memory`](../../../platydoc-data/xnu/osfmk/device/device.defs#L510) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_unmap_memory(
     connection : io_connect_t;
 in memory_type : uint32_t;
 in into_task : task_t;
 in address : uint32_t
 );
```

**Local body:** [`is_io_connect_unmap_memory`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4975).
Calls visible in this body include `SCALAR64`, `is_io_connect_unmap_memory_from_task`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4975-L4989):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4975-L4989 -->
```c
is_io_connect_unmap_memory(
	io_object_t     connect,
	uint32_t        type,
	task_t          task,
	uint32_t        mapAddr )
{
	IOReturn            err;
	mach_vm_address_t   address;

	address = SCALAR64(mapAddr);

	err = is_io_connect_unmap_memory_from_task(connect, type, task, mapAddr);

	return err;
}
```

### 2854: io_registry_entry_get_location_in_plane

Copy the entry's location string in the specified plane.

**Mechanism:** Requires an `IORegistryEntry`, resolves a nonempty plane name or uses null for an empty name, then reads `getLocation`. A present location is copied into the fixed output; absence yields `kIOReturnNotFound`. Location and entry name are distinct registry properties and this call does not synthesize a path from them. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3613).

**Declarations:** [`io_registry_entry_get_location_in_plane`](../../../platydoc-data/xnu/osfmk/device/device.defs#L524) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_location_in_plane(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out location : io_name_t
 );
```

**Local body:** [`is_io_registry_entry_get_location_in_plane`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3613).
Calls visible in this body include `CHECK`, `getPlane`, `getLocation`, `strncpy`.

### 2855: io_registry_entry_get_property_recursively

Search/copy a property through the selected plane according to recursive-search options.

**Mechanism:** Requires the entry and MAC approval, then calls `copyProperty(name, plane, options)` to obtain a retained property through registry traversal. It serializes the found object into the outgoing VM-copy representation, releasing serializer and property afterward. Missing property is `kIOReturnNotFound`; this older wrapper has one initial MAC check rather than the per-candidate checks visible in the newer binary-buffer routine. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3803).

**Declarations:** [`io_registry_entry_get_property_recursively`](../../../platydoc-data/xnu/osfmk/device/device.defs#L530) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_property_recursively(
     registry_entry : io_object_t;
 in plane : io_name_t;
 in property_name : io_name_t;
 in options : uint32_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_property_recursively`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3803).
Calls visible in this body include `CHECK`, `mac_iokit_check_get_property`, `kauth_cred_get`, `copyProperty`, `getPlane`, `withCapacity`, `release`, `serialize`, `getLength`, `copyoutkdata`, `text`.

### 2856: io_service_get_state

Return service state, busy count and accumulated busy time.

**Mechanism:** Requires an `IOService` and reads `getState`, `getBusyState` and `getAccumulatedBusyTime` into separate outputs. The body performs three method calls without wrapping them in a common snapshot lock, so the outputs should not be described as an atomic multi-field state snapshot. No waiting or state transition is requested. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4263).

**Declarations:** [`io_service_get_state`](../../../platydoc-data/xnu/osfmk/device/device.defs#L538) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_state(
     service : io_object_t;
 out state : uint64_t;
 out busy_state : uint32_t;
 out accumulated_busy_time : uint64_t
 );
```

**Local body:** [`is_io_service_get_state`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4263).
Calls visible in this body include `CHECK`, `getState`, `getBusyState`, `getAccumulatedBusyTime`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4263-L4276):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4263-L4276 -->
```c
is_io_service_get_state(
	io_object_t _service,
	uint64_t *state,
	uint32_t *busy_state,
	uint64_t *accumulated_busy_time )
{
	CHECK( IOService, _service, service );

	*state                 = service->getState();
	*busy_state            = service->getBusyState();
	*accumulated_busy_time = service->getAccumulatedBusyTime();

	return kIOReturnSuccess;
}
```

### 2857: io_service_get_matching_services_ool

Request an iterator over services matching a serialized property dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** First consumes the incoming VM copy with `vm_map_copyout(kernel_map, ...)`. After successful consumption it initializes the object output to null, puts dictionary/matching errors in the separate `result` output, and preserves RPC success so MIG handles outputs correctly. The common helper validates the main port, builds a compatibility-adjusted matching dictionary and iterator; temporary kernel mapping storage is then deallocated. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2776).

**Declarations:** [`io_service_get_matching_services_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L545) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_services_ool(
     main_port : mach_port_t;
 in matching : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t;
 out existing : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_services_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2776).
Calls visible in this body include `vm_map_copyout`, `CAST_DOWN`, `internal_io_service_get_matching_services`, `vm_deallocate`.

### 2858: io_service_match_property_table_ool

Test a service against a serialized matching dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Consumes the OOL matching-data VM copy into `kernel_map`; after that succeeds, it invokes the common dictionary/compatibility/`passiveMatch` path and stores its status in `result`. Temporary mapped bytes are deallocated. Keeping the outer return successful after consuming the copy distinguishes operation errors from transport cleanup ownership. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2696).

**Declarations:** [`io_service_match_property_table_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L552) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_match_property_table_ool(
     service : io_object_t;
 in matching : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t;
 out matches : boolean_t
 );
```

**Local body:** [`is_io_service_match_property_table_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2696).
Calls visible in this body include `vm_map_copyout`, `CAST_DOWN`, `internal_io_service_match_property_table`, `vm_deallocate`.

### 2859: io_service_add_notification_ool

Register a matching notification and return its exported notification/iterator object. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Validates and zero-pads the width-specific async reference array, then enters the OOL helper. Successful `vm_map_copyout` consumes the input copy, so the helper keeps transport success and reports matching/registration errors through `result`, with the notification output initially null. It deallocates the mapped dictionary bytes after the common notifier-construction path, whose failure cleanup invalidates the port and releases the wrapper. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3107).

**Declarations:** [`io_service_add_notification_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L560) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification_ool(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_buf_ptr_t, physicalcopy;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
        out result : kern_return_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3107).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_notification_ool`.

### 2860: io_object_get_superclass

Resolve a named runtime class and return its superclass name.

**Mechanism:** Requires the main-device port and nonnull input/output arrays, interns the requested class name, and uses `copyMetaClassWithName` to hold the metaclass during lookup. It copies the superclass name only if both superclass and name exist. The temporary symbol and metaclass hold are released on all exits; unresolved classes or root classes return `kIOReturnNotFound`. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2463).

**Declarations:** [`io_object_get_superclass`](../../../platydoc-data/xnu/osfmk/device/device.defs#L573) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_object_get_superclass(
     main_port : mach_port_t;
 in obj_name : io_name_t;
 out class_name : io_name_t
        );
```

**Local body:** [`is_io_object_get_superclass`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2463).
Calls visible in this body include `withCString`, `copyMetaClassWithName`, `getSuperClass`, `getClassName`, `strlcpy`, `OSSafeReleaseNULL`, `releaseMetaClass`.

### 2861: io_object_get_bundle_identifier

Return the owning module/bundle identifier associated with a named metaclass.

**Mechanism:** Requires the main-device port, interns the class name and acquires its metaclass. It obtains `getKmodName`, copies that symbol's string into the bounded output and returns success only when all lookups succeed. The temporary symbol and metaclass reference are released afterward. This answers the runtime class's kmod association, not a filesystem bundle search. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2514).

**Declarations:** [`io_object_get_bundle_identifier`](../../../platydoc-data/xnu/osfmk/device/device.defs#L579) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_object_get_bundle_identifier(
     main_port : mach_port_t;
 in obj_name : io_name_t;
 out class_name : io_name_t
        );
```

**Local body:** [`is_io_object_get_bundle_identifier`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2514).
Calls visible in this body include `withCString`, `copyMetaClassWithName`, `getKmodName`, `getCStringNoCopy`, `strlcpy`, `OSSafeReleaseNULL`, `releaseMetaClass`.

### 2862: io_service_open_extended

Create a user client for a service/task/type, applying open policy, property decoding and client initialization.

**Mechanism:** Requires an `IOService`, the current task as owner and MAC approval; nonnull properties are unsupported in the active body. `newUserClient` constructs the client, after which the wrapper initializes locking/shared-instance settings, enforces IOUserClient2022 property requirements and entitlement/MAC/filter policy, then registers ownership. Later failure calls `clientClose`, clears termination deferral and releases the client. Successful transport returns the client and a separate operation `result`; early validation errors return directly. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4377).

**Declarations:** [`io_service_open_extended`](../../../platydoc-data/xnu/osfmk/device/device.defs#L585) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_open_extended(
     service : io_object_t;
 in owningTask : task_t;
 in connect_type : uint32_t;
 in ndr : NDR_record_t;
 in properties : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t;
 out connection : io_connect_t
 );
```

**Local body:** [`is_io_service_open_extended`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4377).
Calls visible in this body include `CHECK`, `current_task`, `mac_iokit_check_open_service`, `kauth_cred_get`, `vm_map_copyout`, `CAST_DOWN`, `OSUnserializeXML`, `vm_deallocate`, `OSDynamicCast`, `release`, `newUserClient`, `reserve`.

### 2863: io_connect_map_memory_into_task

**Interface contract:**

> * * * * * * * * * * * * * * * * * * * * * * * * * * * *

**Mechanism:** Requires a user client and target task, then calls `mapClientMemory64` under the configured IPC gate. A mapping exports address/size. Shared instances or another target task attempt to create a mapping-object send right in that task. An ordinary current-task mapping is inserted into `client->mappings` when its set exists or can be allocated, under `gIOObjectPortLock`. The temporary map reference is released. The wrapper returns success when a map was obtained without separately checking port creation, set allocation or set insertion; absence of a map returns bad argument. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4797-L4855).

**Declarations:** [`io_connect_map_memory_into_task`](../../../platydoc-data/xnu/osfmk/device/device.defs#L598) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_map_memory_into_task(
     connection : io_connect_t;
 in memory_type : uint32_t;
 in into_task : task_t;
 inout address : mach_vm_address_t;
 inout size : mach_vm_size_t;
 in flags : uint32_t
 );
```

**Local body:** [`is_io_connect_map_memory_into_task`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4797).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `mapClientMemory64`, `getAddress`, `getSize`, `current_task`, `makeSendRightForTask`, `release`, `IOLockLock`, `withCapacity`, `setObject`.

### 2864: io_connect_unmap_memory_from_task

Find and remove a user-client mapping in the specified task using the wide address ABI.

**Mechanism:** Requires a client and task, obtains the descriptor for the memory type, and uses `kIOMapReference` to locate a mapping at the address. It removes that map from the client set under the object-port lock. Shared/other-task mappings attempt to create a temporary send right; only a nonzero returned name selects `userClientUnmap` and the two-send-reference decrement, whose result is overwritten by success. Otherwise it releases the exported object port. Temporary map-reference release depends on the shared/other-task branch. Missing referenced mapping returns bad argument. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4911-L4971).

**Declarations:** [`io_connect_unmap_memory_from_task`](../../../platydoc-data/xnu/osfmk/device/device.defs#L607) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_unmap_memory_from_task(
     connection : io_connect_t;
 in memory_type : uint32_t;
 in from_task : task_t;
 in address : mach_vm_address_t
 );
```

**Local body:** [`is_io_connect_unmap_memory_from_task`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4911).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `clientMemoryForType`, `createMappingInTask`, `release`, `IOLockLock`, `removeObject`, `IOLockUnlock`, `current_task`, `makeSendRightForTask`, `userClientUnmap`.

### 2865: io_connect_method

Validate scalar/structure buffers, construct IOExternalMethodArguments, apply connection filtering and invoke the user's selected external method.

**Mechanism:** Builds `IOExternalMethodArguments`, clears reserved/output-scalar storage and represents large user buffers with task memory descriptors: input uses copy-on-write plus `kIODirectionOut`, output uses `kIODirectionIn`. It rejects OOL lengths that belong in-band and oversized output lengths, applies the per-task external-method filter, then calls `callExternalMethod`. Updated output counts are copied back and temporary descriptors released. [Call gating](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6583) selects client locking and legacy versus 2022 dispatch; driver selectors define the operation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5133).

**Declarations:** [`io_connect_method`](../../../platydoc-data/xnu/osfmk/device/device.defs#L614) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method(
     connection : io_connect_t;
 in selector : uint32_t;
 in scalar_input : io_scalar_inband64_t;
 in inband_input : io_struct_inband_t;
 in ool_input : mach_vm_address_t;
 in ool_input_size : mach_vm_size_t;
 out inband_output : io_struct_inband_t, CountInOut;
 out scalar_output : io_scalar_inband64_t, CountInOut;
 in ool_output : mach_vm_address_t;
 inout ool_output_size : mach_vm_size_t
 );
```

**Local body:** [`is_io_connect_method`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5133).
Calls visible in this body include `CHECK`, `bzero`, `withAddressRange`, `current_task`, `typeof`, `IOStatisticsClientCall`, `filterForTask`, `io_filter_applier`, `callExternalMethod`, `release`.

### 2866: io_connect_async_method

Construct asynchronous external-method arguments, retain notification references as required, and dispatch the selected user-client method.

**Mechanism:** Requires at least one reference word, replaces word zero with the wake port and marks 64-bit userspace references when appropriate. It constructs the same scalar/structure/descriptor arguments as the synchronous form, but applies the async-method filter and supplies the async reference and port to `callExternalMethod`. Output counts and temporary descriptor cleanup are synchronous; a later completion notification is a separate driver operation, not automatic completion of the MIG request. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5236).

**Declarations:** [`io_connect_async_method`](../../../platydoc-data/xnu/osfmk/device/device.defs#L629) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_async_method(
     connection : io_connect_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref64_t;
 in selector : uint32_t;
 in scalar_input : io_scalar_inband64_t;
 in inband_input : io_struct_inband_t;
 in ool_input : mach_vm_address_t;
 in ool_input_size : mach_vm_size_t;
 out inband_output : io_struct_inband_t, CountInOut;
 out scalar_output : io_scalar_inband64_t, CountInOut;
 in ool_output : mach_vm_address_t;
 inout ool_output_size : mach_vm_size_t
 );
```

**Local body:** [`is_io_connect_async_method`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5236).
Calls visible in this body include `CHECK`, `bzero`, `vm_map_is_64bit`, `get_task_map`, `current_task`, `withAddressRange`, `typeof`, `IOStatisticsClientCall`, `filterForTask`, `io_filter_applier`, `callExternalMethod`, `release`.

### 2867: io_connect_set_notification_port_64

Register a notification port and reference value with a user client.

**Mechanism:** Requires an `IOUserClient`, records call statistics, enters the write IPC gate and invokes the driver's `registerNotificationPort` with notification type, port and reference. The older form widens its 32-bit reference; the 64-bit form passes the user reference directly. Gate exit precedes return of the driver's result. This registers a callback destination rather than immediately sending a notification. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4684).

**Declarations:** [`io_connect_set_notification_port_64`](../../../platydoc-data/xnu/osfmk/device/device.defs#L655) (`server64`, `server32`, `local64`); [`io_connect_set_notification_port`](../../../platydoc-data/xnu/osfmk/device/device.defs#L655) (`client64`, `libsyscall64`, `sender64`).
**Reserved instead in:** `client32`.

**Fields after preprocessing (`server64`):**

```text
routine io_connect_set_notification_port_64(
     connection : io_connect_t;
 in notification_type : uint32_t;
 in port : mach_port_make_send_t;
 in reference : io_user_reference_t
 );
```

**Local body:** [`is_io_connect_set_notification_port_64`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4684).
Calls visible in this body include `CHECK`, `IOStatisticsClientCall`, `ipcEnter`, `registerNotificationPort`, `ipcExit`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4684-L4701):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4684-L4701 -->
```c
is_io_connect_set_notification_port_64(
	io_connect_t connection,
	uint32_t notification_type,
	mach_port_t port,
	io_user_reference_t reference)
{
	kern_return_t ret;
	CHECK( IOUserClient, connection, client );

	IOStatisticsClientCall();

	client->ipcEnter(kIPCLockWrite);
	ret = client->registerNotificationPort( port, notification_type,
	    reference );
	client->ipcExit(kIPCLockWrite);

	return ret;
}
```

### 2868: io_service_add_notification_64

Register a matching notification and return its exported notification/iterator object.

**Mechanism:** This exact legacy string-form body immediately returns `kIOReturnUnsupported`. The existence of similarly named binary or out-of-line forms does not make this declaration operational; no dictionary is parsed and no matching or notification registration is performed here. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3009).

**Declarations:** [`io_service_add_notification_64`](../../../platydoc-data/xnu/osfmk/device/device.defs#L662) (`server64`, `server32`, `local64`); [`io_service_add_notification`](../../../platydoc-data/xnu/osfmk/device/device.defs#L662) (`client64`, `libsyscall64`, `sender64`).
**Reserved instead in:** `client32`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification_64(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_string_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref64_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification_64`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3009).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3009-L3019):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3009-L3019 -->
```c
is_io_service_add_notification_64(
	mach_port_t main_port,
	io_name_t notification_type,
	io_string_t matching,
	mach_port_t wake_port,
	io_async_ref64_t reference,
	mach_msg_type_number_t referenceCnt,
	io_object_t *notification )
{
	return kIOReturnUnsupported;
}
```

### 2869: io_service_add_interest_notification_64

Register a service-interest callback using a notification port and asynchronous references.

**Mechanism:** Validates and zero-pads the appropriate async-reference width, requires an `IOService`, interns the interest name, and builds an `IOServiceMessageUserNotification` around the supplied port. `registerInterest` supplies the notifier retained by that wrapper; failure invalidates the port and releases it. The common body also contains WatchOS power-interest entitlement checking, with enforcement controlled by `gEnforcePowerEntitlement`. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3266).

**Declarations:** [`io_service_add_interest_notification_64`](../../../platydoc-data/xnu/osfmk/device/device.defs#L671) (`server64`, `server32`, `local64`); [`io_service_add_interest_notification`](../../../platydoc-data/xnu/osfmk/device/device.defs#L671) (`client64`, `libsyscall64`, `sender64`).
**Reserved instead in:** `client32`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_interest_notification_64(
     service : io_object_t;
 in type_of_interest : io_name_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref64_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_interest_notification_64`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3266).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_interest_notification`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3266-L3284):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3266-L3284 -->
```c
is_io_service_add_interest_notification_64(
	io_object_t service,
	io_name_t type_of_interest,
	mach_port_t wake_port,
	io_async_ref64_t reference,
	mach_msg_type_number_t referenceCnt,
	io_object_t *notification )
{
	io_async_ref64_t zreference;

	if (referenceCnt > ASYNC_REF64_COUNT) {
		return kIOReturnBadArgument;
	}
	bcopy(&reference[0], &zreference[0], referenceCnt * sizeof(zreference[0]));
	bzero(&zreference[referenceCnt], (ASYNC_REF64_COUNT - referenceCnt) * sizeof(zreference[0]));

	return internal_io_service_add_interest_notification(service, type_of_interest,
	           wake_port, &zreference[0], sizeof(io_async_ref64_t), true, notification);
}
```

### 2870: io_service_add_notification_ool_64

Register a matching notification and return its exported notification/iterator object. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Validates and zero-pads the width-specific async reference array, then enters the OOL helper. Successful `vm_map_copyout` consumes the input copy, so the helper keeps transport success and reports matching/registration errors through `result`, with the notification output initially null. It deallocates the mapped dictionary bytes after the common notifier-construction path, whose failure cleanup invalidates the port and releases the wrapper. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3133).

**Declarations:** [`io_service_add_notification_ool_64`](../../../platydoc-data/xnu/osfmk/device/device.defs#L679) (`server64`, `server32`, `local64`); [`io_service_add_notification_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L679) (`client64`, `libsyscall64`, `sender64`).
**Reserved instead in:** `client32`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification_ool_64(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_buf_ptr_t, physicalcopy;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref64_t;
        out result : kern_return_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification_ool_64`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3133).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_notification_ool`.

### 2871: io_registry_entry_get_registry_entry_id

**Interface contract:**

> IOKIT_ALL_IPC || __LP64__

**Mechanism:** Requires an `IORegistryEntry` and copies `getRegistryEntryID()` into the 64-bit result. This returns the registry's identity value for the current object, not a memory address, process ID, or Mach port name. It neither searches by ID nor extends lifetime beyond the ordinary object-call reference. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3639).

**Declarations:** [`io_registry_entry_get_registry_entry_id`](../../../platydoc-data/xnu/osfmk/device/device.defs#L698) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_registry_entry_id(
     registry_entry : io_object_t;
 out entry_id : uint64_t
 );
```

**Local body:** [`is_io_registry_entry_get_registry_entry_id`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3639).
Calls visible in this body include `CHECK`, `getRegistryEntryID`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3639-L3648):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3639-L3648 -->
```c
is_io_registry_entry_get_registry_entry_id(
	io_object_t registry_entry,
	uint64_t *entry_id )
{
	CHECK( IORegistryEntry, registry_entry, entry );

	*entry_id = entry->getRegistryEntryID();

	return kIOReturnSuccess;
}
```

### 2872: io_connect_method_var_output

Invoke an external method whose structure output is returned through a variable-size memory representation.

**Mechanism:** Builds synchronous external-method arguments with a pointer for driver-produced variable-output ownership, optionally representing large input with a copy-on-write descriptor. After filtering and dispatch, success requires the output object to be `OSSerialize` or `OSData`; data is clipped for copyout and converted into outgoing VM-copy bytes. Other output types yield underrun. Input descriptor and returned object are released, including after serialization/copy failure; scalar/in-band counts are propagated separately. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5026).

**Declarations:** [`io_connect_method_var_output`](../../../platydoc-data/xnu/osfmk/device/device.defs#L703) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_connect_method_var_output(
     connection : io_connect_t;
 in selector : uint32_t;
 in scalar_input : io_scalar_inband64_t;
 in inband_input : io_struct_inband_t;
 in ool_input : mach_vm_address_t;
 in ool_input_size : mach_vm_size_t;
 out inband_output : io_struct_inband_t, CountInOut;
 out scalar_output : io_scalar_inband64_t, CountInOut;
 out var_output : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_connect_method_var_output`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L5026).
Calls visible in this body include `CHECK`, `bzero`, `withAddressRange`, `current_task`, `IOStatisticsClientCall`, `filterForTask`, `io_filter_applier`, `callExternalMethod`, `OSDynamicCast`, `getLength`, `copyoutkdata`, `text`.

### 2873: io_service_get_matching_service

Request a single retained service matching a serialized property dictionary.

**Mechanism:** This exact legacy string-form body immediately returns `kIOReturnUnsupported`. The existence of similarly named binary or out-of-line forms does not make this declaration operational; no dictionary is parsed and no matching or notification registration is performed here. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2849).

**Declarations:** [`io_service_get_matching_service`](../../../platydoc-data/xnu/osfmk/device/device.defs#L717) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_service(
     main_port : mach_port_t;
 in matching : io_string_t;
 out service : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_service`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2849).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2849-L2855):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2849-L2855 -->
```c
is_io_service_get_matching_service(
	mach_port_t main_port,
	io_string_t matching,
	io_service_t *service )
{
	return kIOReturnUnsupported;
}
```

### 2874: io_service_get_matching_service_ool

Request a single retained service matching a serialized property dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Maps/consumes the incoming VM-copy payload into `kernel_map`, initializes the service result to null, and calls the same dictionary/compatibility/`copyMatchingService` helper as the binary form. Once VM-copy consumption succeeds, operation failure is reported in the separate `result` field while the RPC return remains successful. The temporary mapping is deallocated after matching. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2859).

**Declarations:** [`io_service_get_matching_service_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L723) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_service_ool(
     main_port : mach_port_t;
 in matching : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t;
 out service : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_service_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2859).
Calls visible in this body include `vm_map_copyout`, `CAST_DOWN`, `internal_io_service_get_matching_service`, `vm_deallocate`.

### 2875: io_service_get_authorization_id

Read the service authorization identifier after the applicable privilege checks.

**Mechanism:** Requires an `IOService` and first checks administrator privilege through `IOUserClient::clientHasPrivilege`. On macOS it exports the service's authorization ID; on other targets it writes zero and returns unsupported. The ID query therefore has its own explicit privilege check independent of the object-capability lookup. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4336).

**Declarations:** [`io_service_get_authorization_id`](../../../platydoc-data/xnu/osfmk/device/device.defs#L730) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_authorization_id(
     service : io_object_t;
 out authorization_id : uint64_t
 );
```

**Local body:** [`is_io_service_get_authorization_id`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4336).
Calls visible in this body include `CHECK`, `clientHasPrivilege`, `current_task`, `getAuthorizationID`.

### 2876: io_service_set_authorization_id

Set the service authorization identifier through the local setter.

**Mechanism:** Requires an `IOService`; on macOS it delegates to `setAuthorizationID`, while other targets return unsupported. Unlike the adjacent getter wrapper, this body contains no separate administrator-privilege check, so admission and any additional authorization must be understood from capability translation and the called service method rather than copied from the getter's contract. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4362).

**Declarations:** [`io_service_set_authorization_id`](../../../platydoc-data/xnu/osfmk/device/device.defs#L735) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_set_authorization_id(
     service : io_object_t;
 in authorization_id : uint64_t
 );
```

**Local body:** [`is_io_service_set_authorization_id`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4362).
Calls visible in this body include `CHECK`, `setAuthorizationID`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4362-L4373):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4362-L4373 -->
```c
is_io_service_set_authorization_id(
	io_object_t _service,
	uint64_t authorization_id )
{
	CHECK( IOService, _service, service );

#if defined(XNU_TARGET_OS_OSX)
	return service->setAuthorizationID( authorization_id );
#else /* defined(XNU_TARGET_OS_OSX) */
	return kIOReturnUnsupported;
#endif /* defined(XNU_TARGET_OS_OSX) */
}
```

### 2877: io_server_version

Query the IOKit IPC server version.

**Mechanism:** Writes the compile-time `IOKIT_SERVER_VERSION` constant and returns success. The visible body does not validate `main_port` or negotiate features; admission by the surrounding MIG/kobject transport is distinct from this wrapper's implementation. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2431).

**Declarations:** [`io_server_version`](../../../platydoc-data/xnu/osfmk/device/device.defs#L742) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_server_version(
     main_port : mach_port_t;
 out version : uint64_t
 );
```

**Local body:** [`is_io_server_version`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2431).

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2431-L2437):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2431-L2437 -->
```c
is_io_server_version(
	mach_port_t main_port,
	uint64_t *version)
{
	*version = IOKIT_SERVER_VERSION;
	return kIOReturnSuccess;
}
```

### 2878: io_registry_entry_get_properties_bin

Request a serialized property dictionary for a registry entry. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Delegates to the buffer-capable binary implementation with a null direct destination and no size pointer, forcing the outgoing VM-copy representation. The common implementation applies optional MAC filtering during serialization and merges allowed compatibility overlays into a temporary property dictionary. It releases serializer and temporary property objects after producing output; this wrapper adds no independent property snapshot. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3979).

**Declarations:** [`io_registry_entry_get_properties_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L747) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_properties_bin(
     registry_entry : io_object_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_properties_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3979).
Calls visible in this body include `is_io_registry_entry_get_properties_bin_buf`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3979-L3986):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3979-L3986 -->
```c
is_io_registry_entry_get_properties_bin(
	io_object_t registry_entry,
	io_buf_ptr_t *properties,
	mach_msg_type_number_t *propertiesCnt)
{
	return is_io_registry_entry_get_properties_bin_buf(registry_entry,
	           0, NULL, properties, propertiesCnt);
}
```

### 2879: io_registry_entry_get_property_bin

Request a serialized value for one registry property, subject to property-access policy. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Calls the binary-buffer implementation with no direct output buffer, so successful serialization returns OOL VM-copy data. The common path handles property-key enumeration, compatibility lookup, optional recursive traversal and remove-on-read properties, with configured MAC checks. It releases the retained property after serialization; the wrapper does not bypass those checks merely because its result is OOL. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4091).

**Declarations:** [`io_registry_entry_get_property_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L752) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_property_bin(
     registry_entry : io_object_t;
 in plane : io_name_t;
 in property_name : io_name_t;
 in options : uint32_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_property_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4091).
Calls visible in this body include `is_io_registry_entry_get_property_bin_buf`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4091-L4101):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4091-L4101 -->
```c
is_io_registry_entry_get_property_bin(
	io_object_t registry_entry,
	io_name_t plane,
	io_name_t property_name,
	uint32_t options,
	io_buf_ptr_t *properties,
	mach_msg_type_number_t *propertiesCnt )
{
	return is_io_registry_entry_get_property_bin_buf(registry_entry, plane,
	           property_name, options, 0, NULL, properties, propertiesCnt);
}
```

### 2880: io_service_get_matching_service_bin

Request a single retained service matching a serialized property dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** The common helper validates the main-device port, parses an `OSDictionary`, and applies the current task's compatibility rules. `IOService::copyMatchingService` returns a retained first matching service; absence is reported as `kIOReturnNotFound`, unlike the iterator-producing form. The parsed object is released regardless of matching outcome. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2887).

**Declarations:** [`io_service_get_matching_service_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L760) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_service_bin(
     main_port : mach_port_t;
 in matching : io_struct_inband_t;
 out service : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_service_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2887).
Calls visible in this body include `internal_io_service_get_matching_service`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2887-L2894):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2887-L2894 -->
```c
is_io_service_get_matching_service_bin(
	mach_port_t main_port,
	io_struct_inband_t matching,
	mach_msg_type_number_t matchingCnt,
	io_object_t *service)
{
	return internal_io_service_get_matching_service(main_port, matching, matchingCnt, service);
}
```

### 2881: io_service_get_matching_services_bin

Request an iterator over services matching a serialized property dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** The common helper requires `main_device_port`, unserializes the supplied bounded buffer, and requires an `OSDictionary`. It applies task compatibility matching, calls `IOService::getMatchingServices`, wraps the resulting iterator with `IOUserIterator::withIterator`, and releases the parsed object. The helper returns success after that construction without a separate null-output check; malformed dictionaries return `kIOReturnBadArgument`. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2804).

**Declarations:** [`io_service_get_matching_services_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L766) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_get_matching_services_bin(
     main_port : mach_port_t;
 in matching : io_struct_inband_t;
 out existing : io_object_t
 );
```

**Local body:** [`is_io_service_get_matching_services_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2804).
Calls visible in this body include `internal_io_service_get_matching_services`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2804-L2811):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2804-L2811 -->
```c
is_io_service_get_matching_services_bin(
	mach_port_t main_port,
	io_struct_inband_t matching,
	mach_msg_type_number_t matchingCnt,
	io_object_t *existing)
{
	return internal_io_service_get_matching_services(main_port, matching, matchingCnt, existing);
}
```

### 2882: io_service_match_property_table_bin

Test a service against a serialized matching dictionary. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** The common helper first requires an `IOService`, then unserializes a dictionary, adjusts task compatibility matching and calls `service->passiveMatch`. It releases the dictionary after use. A well-formed dictionary can produce `matches = false` with success; failure to obtain a dictionary is a bad argument. This checks the supplied service rather than returning a global matching iterator. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2722).

**Declarations:** [`io_service_match_property_table_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L772) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_match_property_table_bin(
     service : io_object_t;
 in matching : io_struct_inband_t;
 out matches : boolean_t
 );
```

**Local body:** [`is_io_service_match_property_table_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2722).
Calls visible in this body include `internal_io_service_match_property_table`.

[Implementation excerpt](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2722-L2729):
<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L2722-L2729 -->
```c
is_io_service_match_property_table_bin(
	io_object_t service,
	io_struct_inband_t matching,
	mach_msg_type_number_t matchingCnt,
	boolean_t *matches)
{
	return internal_io_service_match_property_table(service, matching, matchingCnt, matches);
}
```

### 2883: io_service_add_notification_bin

Register a matching notification and return its exported notification/iterator object. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Checks the reference-word count against the corresponding 32-bit or 64-bit limit, copies supplied words into a zero-padded reference array, and passes its width to the common helper. That helper requires the main-device port and a bounded matching dictionary, chooses a notification message type, constructs `IOServiceUserNotification`, and registers a matching notifier. Failure invalidates the retained notification port and releases the wrapper; success attaches the notifier to the exported object. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3023).

**Declarations:** [`io_service_add_notification_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L779) (`server64`, `server32`, `client32`, `local64`).
**Reserved instead in:** `client64`, `libsyscall64`, `sender64`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification_bin(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_struct_inband_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification_bin`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3023).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_notification`.

### 2884: io_service_add_notification_bin_64

Register a matching notification and return its exported notification/iterator object. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Checks the reference-word count against the corresponding 32-bit or 64-bit limit, copies supplied words into a zero-padded reference array, and passes its width to the common helper. That helper requires the main-device port and a bounded matching dictionary, chooses a notification message type, constructs `IOServiceUserNotification`, and registers a matching notifier. Failure invalidates the retained notification port and releases the wrapper; success attaches the notifier to the exported object. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3049).

**Declarations:** [`io_service_add_notification_bin_64`](../../../platydoc-data/xnu/osfmk/device/device.defs#L792) (`server64`, `server32`, `local64`); [`io_service_add_notification_bin`](../../../platydoc-data/xnu/osfmk/device/device.defs#L792) (`client64`, `libsyscall64`, `sender64`).
**Reserved instead in:** `client32`.

**Fields after preprocessing (`server64`):**

```text
routine io_service_add_notification_bin_64(
     main_port : mach_port_t;
 in notification_type : io_name_t;
 in matching : io_struct_inband_t;
 in wake_port : mach_port_make_send_t;
 in reference : io_async_ref64_t;
 out notification : io_object_t
 );
```

**Local body:** [`is_io_service_add_notification_bin_64`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3049).
Calls visible in this body include `bcopy`, `bzero`, `internal_io_service_add_notification`.

### 2885: io_registry_entry_get_path_ool

Copy an entry's path in a specified registry plane into the bounded output buffer. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Attempts `getPath` in the small in-band buffer first, with OOL output initialized empty. If that fails, it allocates a 16-KiB temporary buffer and retries, returning no-memory or formatting error as appropriate. Success converts those bytes to outgoing VM-copy data through `copyoutkdata`; temporary allocation is freed in all fallback cases. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3538).

**Declarations:** [`io_registry_entry_get_path_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L806) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_path_ool(
     registry_entry : io_object_t;
 in plane : io_name_t;
 out path : io_string_inband_t;
 out path_ool : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_path_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3538).
Calls visible in this body include `CHECK`, `getPath`, `getPlane`, `IONewData`, `copyoutkdata`, `IODeleteData`.

### 2886: io_registry_entry_from_path_ool

Resolve a registry path to an exported entry, including the local compatibility lookup rules. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Requires the main-device port and prefers the nonempty in-band path. Otherwise it requires a bounded nonempty OOL payload, consumes its VM copy and checks the final byte is null. It calls `fromPath`, reports not-found or malformed-path status in `result`, and deallocates mapped bytes. After consuming the VM copy, transport success is preserved even when lookup fails; this body lacks the legacy wrapper's compatibility fallback. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3443).

**Declarations:** [`io_registry_entry_from_path_ool`](../../../platydoc-data/xnu/osfmk/device/device.defs#L813) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_from_path_ool(
     main_port : mach_port_t;
 in path : io_string_inband_t;
 in path_ool : io_buf_ptr_t, physicalcopy;
        out result : kern_return_t;
 out registry_entry : io_object_t
 );
```

**Local body:** [`is_io_registry_entry_from_path_ool`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3443).
Calls visible in this body include `vm_map_copyout`, `CAST_DOWN`, `fromPath`, `vm_deallocate`.

### 2887: io_device_tree_entry_exists_with_name

Search the device tree for an entry/property matching the supplied name.

**Mechanism:** Requires the main-device port and interprets an optional colon as an entry-name/property-name separator. It recursively searches device-tree entries with `IODTFindMatchingEntries`, examines only the first matching entry, and returns true when that entry exists and the requested property, if any, exists. The iterator is released; absence is a false Boolean with successful RPC, not a lookup error. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6547).

**Declarations:** [`io_device_tree_entry_exists_with_name`](../../../platydoc-data/xnu/osfmk/device/device.defs#L823) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_device_tree_entry_exists_with_name(
     main_port : mach_port_t;
 in name : io_name_t;
 out exists : boolean_t
 );
```

**Local body:** [`is_io_device_tree_entry_exists_with_name`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L6547).
Calls visible in this body include `strchr`, `strlcpy`, `IODTFindMatchingEntries`, `getRegistryRoot`, `getNextObject`, `propertyExists`, `OSSafeReleaseNULL`.

### 2888: io_registry_entry_get_properties_bin_buf

Request a serialized property dictionary for a registry entry. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Builds a binary serializer, optionally installing a MAC editor that filters top-level properties. Compatibility overlays are merged into a temporary property dictionary with overlay-container keys removed; otherwise `serializeProperties` supplies the table. If the caller's direct buffer fits, copyout fills it and OOL output is empty. Otherwise it returns VM-copy data and clears the direct-buffer size. Serialization/copy errors are returned after releasing temporary objects. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3894).

**Declarations:** [`io_registry_entry_get_properties_bin_buf`](../../../platydoc-data/xnu/osfmk/device/device.defs#L829) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_properties_bin_buf(
     registry_entry : io_object_t;
 in buf : mach_vm_address_t;
 inout bufsize : mach_vm_size_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_properties_bin_buf`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3894).
Calls visible in this body include `CHECK`, `mac_iokit_check_filter_properties`, `kauth_cred_get`, `binaryWithCapacity`, `copyProperty`, `IOTaskRegistryCompatibility`, `current_task`, `dictionaryWithProperties`, `removeObject`, `merge`, `OSDynamicCast`, `serialize`.

### 2889: io_registry_entry_get_property_bin_buf

Request a serialized value for one registry property, subject to property-access policy. This declaration uses the buffer/serialization/address-width variant shown in its fields.

**Mechanism:** Checks the entry/property MAC rule, interns the key, then either obtains property keys or performs compatible lookup, including optional recursive traversal and per-candidate MAC checks. A found remove-on-read property is removed before serialization/output. It returns binary bytes through a sufficiently large direct user buffer or OOL copy, releasing symbol, iterator, serializer and property references. A later copy failure does not restore a removed property. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3990).

**Declarations:** [`io_registry_entry_get_property_bin_buf`](../../../platydoc-data/xnu/osfmk/device/device.defs#L836) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_registry_entry_get_property_bin_buf(
     registry_entry : io_object_t;
 in plane : io_name_t;
 in property_name : io_name_t;
 in options : uint32_t;
 in buf : mach_vm_address_t;
 inout bufsize : mach_vm_size_t;
 out properties : io_buf_ptr_t, physicalcopy
 );
```

**Local body:** [`is_io_registry_entry_get_property_bin_buf`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L3990).
Calls visible in this body include `CHECK`, `mac_iokit_check_get_property`, `kauth_cred_get`, `withCString`, `copyPropertyKeys`, `IOCopyPropertyCompatible`, `iterateOver`, `getPlane`, `getNextObject`, `OSSafeReleaseNULL`, `release`, `containsObject`.

### 2890: io_service_wait_quiet_with_options

Wait for quiet with the additional options and entitlement checks implemented by this entry.

**Mechanism:** Requires an `IOService` and converts the timeout to nanoseconds. If the caller requests `kIOWaitQuietPanicOnFailure` without its entitlement, the wrapper logs and removes that option rather than rejecting the entire wait. It then calls `waitQuietWithOptions` with the resulting flags and returns the service's outcome. [Local implementation](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4297).

**Declarations:** [`io_service_wait_quiet_with_options`](../../../platydoc-data/xnu/osfmk/device/device.defs#L846) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine io_service_wait_quiet_with_options(
            service : io_object_t;
 in wait_time : mach_timespec_t;
 in options : uint32_t
 );
```

**Local body:** [`is_io_service_wait_quiet_with_options`](../../../platydoc-data/xnu/iokit/Kernel/IOUserClient.cpp#L4297).
Calls visible in this body include `CHECK`, `IOCurrentTaskHasEntitlement`, `IOCopyLogNameForPID`, `proc_selfpid`, `IOLog`, `IOServiceWaitQuietWithOptions`, `getCStringNoCopy`, `OSSafeReleaseNULL`, `waitQuietWithOptions`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
