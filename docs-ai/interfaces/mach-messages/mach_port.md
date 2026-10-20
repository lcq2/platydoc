# Mach messages: mach_port

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_port.defs](../../../xnu/osfmk/mach/mach_port.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3200: mach_port_names

**Interface contract:**

> Returns the set of port and port set names to which the target task has access, along with the type (set or port) for each name.

**Mechanism:** Takes the IPC-space read lock, sizes two page-rounded output arrays against the current entry table, drops the lock to allocate, and retries if the table outgrows them. It walks nonempty entries with generation-bearing names and a port-death timestamp, then zeroes padding and converts the used buffers into `vm_map_copy` objects for out-of-line reply delivery. Empty results free the buffers and return null copies. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L220).

**Declarations:** [`mach_port_names`](../../../xnu/osfmk/mach/mach_port.defs#L87) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_names(
  task : ipc_space_t;
 out names : mach_port_name_array_t;
 out types : mach_port_type_array_t);
```

**Local body:** [`mach_port_names`](../../../xnu/osfmk/ipc/mach_port.c#L220).
Calls visible in this body include `static_assert`, `is_read_lock`, `is_active`, `is_read_unlock`, `kmem_free`, `ipc_entry_table_count`, `is_active_table`, `vm_map_round_page`, `VM_MAP_PAGE_MASK`, `kmem_alloc`, `ipc_port_timestamp`, `ipc_entry_table_get_nocheck`.

**User wrapper:** [`mach_port_names`](../../../xnu/libsyscall/mach/mach_port.c#L38).
Calls visible in this body include `_kernelrpc_mach_port_names`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L38-L51):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L38-L51 -->
```c
mach_port_names(
	ipc_space_t task,
	mach_port_name_array_t *names,
	mach_msg_type_number_t *namesCnt,
	mach_port_type_array_t *types,
	mach_msg_type_number_t *typesCnt)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_names(task, names, namesCnt, types,
	    typesCnt);

	return rv;
}
```

### 3201: mach_port_type

**Interface contract:**

> Returns the type (set or port) for the port name within the target task. Also indicates whether there is a dead-name request for the name.

**Mechanism:** Special-cases NULL and DEAD names, then obtains a writable namespace lookup because `ipc_right_info` may reconcile a dead port with the entry. Returns the combined right-type bits, with the send-possible notification bits explicitly masked for compatibility. The result describes this space's rights under that name, not a unique global port identity. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L402).

**Declarations:** [`mach_port_type`](../../../xnu/osfmk/mach/mach_port.defs#L98) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_type(
  task : ipc_space_t;
  name : mach_port_name_t;
 out ptype : mach_port_type_t);
```

**Local body:** [`mach_port_type`](../../../xnu/osfmk/ipc/mach_port.c#L402).
Calls visible in this body include `ipc_right_lookup_write`, `ipc_right_info`.

**User wrapper:** [`mach_port_type`](../../../xnu/libsyscall/mach/mach_port.c#L54).
Calls visible in this body include `_kernelrpc_mach_port_type_trap`, `_kernelrpc_mach_port_type`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L54-L68):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L54-L68 -->
```c
mach_port_type(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_type_t *ptype)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_type_trap(task, name, ptype);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_type(task, name, ptype);
	}

	return rv;
}
```

### 3202: mach_port_rename

Rename a right within an IPC namespace through the historical public interface.

**Mechanism:** This historical declaration is skipped by the kernel-server profile and has no same-symbol receiver in the indexed implementation. It must not be interpreted as a working rename operation in the current kobject dispatch table. Use the per-profile declaration and reserved-slot evidence below.

**Declarations:** [`mach_port_rename`](../../../xnu/osfmk/mach/mach_port.defs#L109) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_port_rename(
  task : ipc_space_t;
  old_name : mach_port_name_t;
  new_name : mach_port_name_t);
```

**User wrapper:** [`mach_port_rename`](../../../xnu/libsyscall/mach/mach_port.c#L71).
Calls visible in this body include `_kernelrpc_mach_port_rename`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L71-L81):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L71-L81 -->
```c
mach_port_rename(
	ipc_space_t task,
	mach_port_name_t old_name,
	mach_port_name_t new_name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_rename(task, old_name, new_name);

	return rv;
}
```

Only a user-library body was resolved here; that is not a kernel receiver implementation.

### 3203: mach_port_allocate_name

**Interface contract:**

> Allocates the specified kind of object, with the given name. The right must be one of MACH_PORT_RIGHT_RECEIVE MACH_PORT_RIGHT_PORT_SET MACH_PORT_RIGHT_DEAD_NAME New port sets are empty. New ports don't have any send/send-once rights or queued messages. The make-send count is zero and their queue limit is MACH_PORT_QLIMIT_DEFAULT. New sets, ports, and dead names have one user reference.

**Mechanism:** Sets `qos.name`, rejects invalid requested names, and delegates to `mach_port_allocate_full`. Receive-port and port-set cases use their named allocators. The DEAD_NAME case instead calls `ipc_object_alloc_dead`, whose `ipc_entry_alloc` chooses a fresh entry and overwrites the local name variable; this wrapper does not return that replacement name. Thus the historical requested-name contract does not describe that branch. [Wrapper](../../../xnu/osfmk/ipc/mach_port.c#L478), [dead-name allocator](../../../xnu/osfmk/ipc/ipc_object.c#L381).

**Declarations:** [`mach_port_allocate_name`](../../../xnu/osfmk/mach/mach_port.defs#L127) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_allocate_name(
  task : ipc_space_t;
  right : mach_port_right_t;
  name : mach_port_name_t);
```

**Local body:** [`mach_port_allocate_name`](../../../xnu/osfmk/ipc/mach_port.c#L478).
Calls visible in this body include `MACH_PORT_VALID`, `mach_port_allocate_full`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L478-L493):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L478-L493 -->
```c
mach_port_allocate_name(
	ipc_space_t             space,
	mach_port_right_t       right,
	mach_port_name_t        name)
{
	kern_return_t           kr;
	mach_port_qos_t         qos = { .name = TRUE };

	if (!MACH_PORT_VALID(name)) {
		return KERN_INVALID_VALUE;
	}

	kr = mach_port_allocate_full(space, right, MACH_PORT_NULL,
	    &qos, &name);
	return kr;
}
```

**User wrapper:** [`mach_port_allocate_name`](../../../xnu/libsyscall/mach/mach_port.c#L84).
Calls visible in this body include `_kernelrpc_mach_port_allocate_name`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L84-L94):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L84-L94 -->
```c
mach_port_allocate_name(
	ipc_space_t task,
	mach_port_right_t right,
	mach_port_name_t name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_allocate_name(task, right, name);

	return rv;
}
```

### 3204: mach_port_allocate

**Interface contract:**

> Allocates the specified kind of object. The right must be one of MACH_PORT_RIGHT_RECEIVE MACH_PORT_RIGHT_PORT_SET MACH_PORT_RIGHT_DEAD_NAME Like port_allocate_name, but the kernel picks a name. It can use any name not associated with a right.

**Mechanism:** Initializes an empty QoS request and invokes `mach_port_allocate_full` with a null prototype. The selected allocator chooses a free namespace entry/name; successful receive-port or port-set allocation returns a locked object which the common allocator unlocks before returning. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L514).

**Declarations:** [`mach_port_allocate`](../../../xnu/osfmk/mach/mach_port.defs#L142) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_allocate(
  task : ipc_space_t;
  right : mach_port_right_t;
 out name : mach_port_name_t);
```

**Local body:** [`mach_port_allocate`](../../../xnu/osfmk/ipc/mach_port.c#L514).
Calls visible in this body include `mach_port_allocate_full`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L514-L525):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L514-L525 -->
```c
mach_port_allocate(
	ipc_space_t             space,
	mach_port_right_t       right,
	mach_port_name_t        *namep)
{
	kern_return_t           kr;
	mach_port_qos_t         qos = { };

	kr = mach_port_allocate_full(space, right, MACH_PORT_NULL,
	    &qos, namep);
	return kr;
}
```

**User wrapper:** [`mach_port_allocate`](../../../xnu/libsyscall/mach/mach_port.c#L97).
Calls visible in this body include `_kernelrpc_mach_port_allocate_trap`, `_kernelrpc_mach_port_allocate`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L97-L111):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L97-L111 -->
```c
mach_port_allocate(
	ipc_space_t task,
	mach_port_right_t right,
	mach_port_name_t *name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_allocate_trap(task, right, name);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_allocate(task, right, name);
	}

	return rv;
}
```

### 3205: mach_port_destroy

**Interface contract:**

> Destroys all rights associated with the name and makes it available for recycling immediately. The name can be a port (possibly with multiple user refs), a port set, or a dead name (again, with multiple user refs).

**Mechanism:** Treats NULL/DEAD names as successful no-ops; otherwise looks up and write-locks the namespace entry and hands it to `ipc_right_destroy`, which unlocks the space. Destruction concerns all rights represented by that entry and can initiate port death/notifications when receive ownership is destroyed. Lookup failure can also record a guard exception. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L692).

**Declarations:** [`mach_port_destroy`](../../../xnu/osfmk/mach/mach_port.defs#L154) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_destroy(
  task : ipc_space_t;
  name : mach_port_name_t);
```

**Local body:** [`mach_port_destroy`](../../../xnu/osfmk/ipc/mach_port.c#L692).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_right_lookup_write`, `mach_port_guard_exception`, `ipc_right_destroy`.

**User wrapper:** [`mach_port_destroy`](../../../xnu/libsyscall/mach/mach_port.c#L114).
Calls visible in this body include `_kernelrpc_mach_port_destroy`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L114-L123):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L114-L123 -->
```c
mach_port_destroy(
	ipc_space_t task,
	mach_port_name_t name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_destroy(task, name);

	return rv;
}
```

### 3206: mach_port_deallocate

**Interface contract:**

> Releases one send/send-once/dead-name user ref. Just like mach_port_mod_refs -1, but deduces the correct type of right. This allows a user task to release a ref for a port without worrying about whether the port has died or not.

**Mechanism:** Calls `mach_port_deallocate_kernel` with `IOT_ANY`. After a writable entry lookup, `ipc_right_dealloc` removes one applicable user reference and performs final-right/name cleanup when required. This differs from destroying every right at the entry. NULL/DEAD names succeed without lookup; invalid live names can trigger a guard exception. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L728).

**Declarations:** [`mach_port_deallocate`](../../../xnu/osfmk/mach/mach_port.defs#L166) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_deallocate(
  task : ipc_space_t;
  name : mach_port_name_t);
```

**Local body:** [`mach_port_deallocate`](../../../xnu/osfmk/ipc/mach_port.c#L775).
Calls visible in this body include `mach_port_deallocate_kernel`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L775-L780):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L775-L780 -->
```c
mach_port_deallocate(
	ipc_space_t             space,
	mach_port_name_t        name)
{
	return mach_port_deallocate_kernel(space, name, IOT_ANY);
}
```

**User wrapper:** [`mach_port_deallocate`](../../../xnu/libsyscall/mach/mach_port.c#L126).
Calls visible in this body include `_kernelrpc_mach_port_deallocate_trap`, `_kernelrpc_mach_port_deallocate`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L126-L139):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L126-L139 -->
```c
mach_port_deallocate(
	ipc_space_t task,
	mach_port_name_t name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_deallocate_trap(task, name);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_deallocate(task, name);
	}

	return rv;
}
```

### 3207: mach_port_get_refs

**Interface contract:**

> A port set always has one user ref. A send-once right always has one user ref. A dead name always has one or more user refs. A send right always has one or more user refs. A receive right always has one user ref. The right must be one of MACH_PORT_RIGHT_RECEIVE MACH_PORT_RIGHT_PORT_SET MACH_PORT_RIGHT_DEAD_NAME MACH_PORT_RIGHT_SEND MACH_PORT_RIGHT_SEND_ONCE

**Mechanism:** Checks the requested right kind, resolves current type and user-reference count with `ipc_right_info`, and returns zero when the name exists but lacks that kind. Receive, port-set and send-once rights report one; send/dead-name rights use the stored urefs. Special NULL/DEAD send/send-once queries are handled before namespace lookup. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L800).

**Declarations:** [`mach_port_get_refs`](../../../xnu/osfmk/mach/mach_port.defs#L184) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_get_refs(
  task : ipc_space_t;
  name : mach_port_name_t;
  right : mach_port_right_t;
 out refs : mach_port_urefs_t);
```

**Local body:** [`mach_port_get_refs`](../../../xnu/osfmk/ipc/mach_port.c#L800).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_right_lookup_write`, `ipc_right_info`, `MACH_PORT_TYPE`.

**User wrapper:** [`mach_port_get_refs`](../../../xnu/libsyscall/mach/mach_port.c#L142).
Calls visible in this body include `_kernelrpc_mach_port_get_refs`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L142-L153):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L142-L153 -->
```c
mach_port_get_refs(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_right_t right,
	mach_port_urefs_t *refs)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_get_refs(task, name, right, refs);

	return rv;
}
```

### 3208: mach_port_mod_refs

**Interface contract:**

> The delta is a signed change to the task's user ref count for the right. Only dead names and send rights can have a positive delta. The resulting user ref count can't be negative. If it is zero, the right is deallocated. If the name isn't a composite right, it becomes available for recycling. The right must be one of MACH_PORT_RIGHT_RECEIVE MACH_PORT_RIGHT_PORT_SET MACH_PORT_RIGHT_DEAD_NAME MACH_PORT_RIGHT_SEND MACH_PORT_RIGHT_SEND_ONCE

**Mechanism:** Validates the requested right kind and special names, obtains a writable entry lookup and calls `ipc_right_delta`. The lower operation enforces right-specific delta, overflow, destruction and guard rules and releases the namespace lock. This changes urefs/right ownership, not the raw reference count of `ipc_port` storage. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L889).

**Declarations:** [`mach_port_mod_refs`](../../../xnu/osfmk/mach/mach_port.defs#L205) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_mod_refs(
  task : ipc_space_t;
  name : mach_port_name_t;
  right : mach_port_right_t;
  delta : mach_port_delta_t);
```

**Local body:** [`mach_port_mod_refs`](../../../xnu/osfmk/ipc/mach_port.c#L889).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_right_lookup_write`, `mach_port_guard_exception`, `ipc_right_delta`.

**User wrapper:** [`mach_port_mod_refs`](../../../xnu/libsyscall/mach/mach_port.c#L156).
Calls visible in this body include `_kernelrpc_mach_port_mod_refs_trap`, `_kernelrpc_mach_port_mod_refs`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L156-L171):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L156-L171 -->
```c
mach_port_mod_refs(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_right_t right,
	mach_port_delta_t delta)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_mod_refs_trap(task, name, right, delta);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_mod_refs(task, name, right, delta);
	}

	return rv;
}
```

### 3209: mach_port_peek

**Interface contract:**

> Peek at the message queue for the specified receive right and return info about the message with the sequence number matching the input. If zero is specified as the seqno, the first message in the queue will be peeked. Only the following trailer types are currently supported: MACH_RCV_TRAILER_TYPE(MACH_MSG_TRAILER_FORMAT_0) or'ed with one of these element types: MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_NULL) MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_SEQNO) MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_SENDER) MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_AUDIT)

**Mechanism:** Validates the requested trailer extent against the caller's capacity and refuses fields beyond the audit trailer, then translates the receive right. With the port queue locked, `ipc_mqueue_peek_locked` selects a queued message and reports its sequence, size, ID and trailer without receiving it. A missing matching message returns failure; no rights or message ownership transfer occurs. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L966).

**Declarations:** [`mach_port_peek`](../../../xnu/osfmk/mach/mach_port.defs#L227) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_peek(
  task : ipc_space_t;
  name : mach_port_name_t;
  trailer_type : mach_msg_trailer_type_t;
 inout request_seqnop : mach_port_seqno_t;
 out msg_sizep : mach_msg_size_t;
 out msg_idp : mach_msg_id_t;
 out trailer_infop : mach_msg_trailer_info_t, CountInOut);
```

**Local body:** [`mach_port_peek`](../../../xnu/osfmk/ipc/mach_port.c#L966).
Calls visible in this body include `MACH_PORT_VALID`, `GET_RCV_ELEMENTS`, `REQUESTED_TRAILER_SIZE`, `mach_port_guard_exception`, `MPG_PAYLOAD`, `ipc_port_translate_receive`, `ipc_mqueue_peek_locked`, `ip_mq_unlock`, `memcpy`.

**User wrapper:** [`mach_port_peek`](../../../xnu/libsyscall/mach/mach_port.c#L174).
Calls visible in this body include `_kernelrpc_mach_port_peek`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L174-L191):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L174-L191 -->
```c
mach_port_peek(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_msg_trailer_type_t trailer_type,
	mach_port_seqno_t       *seqnop,
	mach_msg_size_t         *msg_sizep,
	mach_msg_id_t           *msg_idp,
	mach_msg_trailer_info_t trailer_infop,
	mach_msg_type_number_t  *trailer_sizep)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_peek(task, name, trailer_type,
	    seqnop, msg_sizep, msg_idp,
	    trailer_infop, trailer_sizep);

	return rv;
}
```

### 3210: mach_port_set_mscount

**Interface contract:**

> Only valid for receive rights. Sets the make-send count for the port.

**Mechanism:** Translates the name as a receive right, writes `ip_mscount` under the port queue lock and unlocks. The value is the make-send generation used by notification semantics; this operation does not create send rights or change their user references. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1041).

**Declarations:** [`mach_port_set_mscount`](../../../xnu/osfmk/mach/mach_port.defs#L240) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_set_mscount(
  task : ipc_space_t;
  name : mach_port_name_t;
  mscount : mach_port_mscount_t);
```

**Local body:** [`mach_port_set_mscount`](../../../xnu/osfmk/ipc/mach_port.c#L1041).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_set_mscount`](../../../xnu/libsyscall/mach/mach_port.c#L194).
Calls visible in this body include `_kernelrpc_mach_port_set_mscount`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L194-L204):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L194-L204 -->
```c
mach_port_set_mscount(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_mscount_t mscount)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_set_mscount(task, name, mscount);

	return rv;
}
```

### 3211: mach_port_get_set_status_from_user

**Interface contract:**

> Only valid for port sets. Returns a list of the members.

**Mechanism:** Converts the destination to a referenced readable IPC space, then enumerates the selected port-set waitq membership. The helper allocates a buffer outside the object lock and retries if it is too small, sorts member names, zeroes padding, and returns a `vm_map_copy` array. The wrapper releases the space reference on return. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1361).

**Declarations:** [`mach_port_get_set_status_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L249) (`server64`, `server32`, `local64`); [`mach_port_get_set_status`](../../../xnu/osfmk/mach/mach_port.defs#L249) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_get_set_status_from_user(
  port : mach_port_t;
  name : mach_port_name_t;
 out members : mach_port_name_array_t);
```

**Local body:** [`mach_port_get_set_status_from_user`](../../../xnu/osfmk/ipc/mach_port.c#L1361).
Calls visible in this body include `convert_port_to_space_read_no_eval`, `mach_port_get_set_status`, `ipc_space_release`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L1361-L1379):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L1361-L1379 -->
```c
mach_port_get_set_status_from_user(
	mach_port_t                     port,
	mach_port_name_t                name,
	mach_port_name_t                **members,
	mach_msg_type_number_t          *membersCnt)
{
	kern_return_t kr;

	ipc_space_t space = convert_port_to_space_read_no_eval(port);

	if (space == IPC_SPACE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kr = mach_port_get_set_status(space, name, members, membersCnt);

	ipc_space_release(space);
	return kr;
}
```

### 3212: mach_port_move_member

**Interface contract:**

> Puts the member port (the task must have receive rights) into the after port set. If the port is already a member of any set(s), it is atomically removed from those sets as part of this operation. (If after is MACH_PORT_NULL, the port is still removed from all current sets).

**Mechanism:** For a nonnull destination, allocates a waitq link and jointly translates the receive port and port set, adds the selected set, then unlinks all other memberships while retaining that set. A null destination removes all memberships and reports `KERN_NOT_IN_SET` when none existed. Detached/unused links are freed after unlocking. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1403).

**Declarations:** [`mach_port_move_member`](../../../xnu/osfmk/mach/mach_port.defs#L268) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_move_member(
  task : ipc_space_t;
  member : mach_port_name_t;
  after : mach_port_name_t);
```

**Local body:** [`mach_port_move_member`](../../../xnu/osfmk/ipc/mach_port.c#L1403).
Calls visible in this body include `MACH_PORT_VALID`, `waitq_link_alloc`, `ipc_object_translate_port_pset`, `ipc_port_translate_receive`, `ipc_mqueue_add_locked`, `ips_mq_unlock`, `ip_in_pset`, `waitq_unlink_all_locked`, `ip_mq_unlock`, `waitq_link_free_list`, `waitq_link_free`.

**User wrapper:** [`mach_port_move_member`](../../../xnu/libsyscall/mach/mach_port.c#L222).
Calls visible in this body include `_kernelrpc_mach_port_move_member_trap`, `_kernelrpc_mach_port_move_member`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L222-L236):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L222-L236 -->
```c
mach_port_move_member(
	ipc_space_t task,
	mach_port_name_t member,
	mach_port_name_t after)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_move_member_trap(task, member, after);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_move_member(task, member, after);
	}

	return rv;
}
```

### 3213: mach_port_request_notification

**Interface contract:**

> Requests a notification from the kernel. The request must supply the send-once right which is used for the notification. If a send-once right was previously registered, it is returned. The msgid must be one of: MACH_NOTIFY_PORT_DESTROYED (receive rights) MACH_NOTIFY_DEAD_NAME (send/receive/send-once rights) MACH_NOTIFY_SEND_POSSIBLE (send/receive/send-once rights) MACH_NOTIFY_NO_SENDERS (receive rights) The sync value specifies whether a notification should get sent immediately, if appropriate. The exact meaning depends on the notification: MACH_NOTIFY_PORT_DESTROYED: must be zero. MACH_NOTIFY_DEAD_NAME: if non-zero, then name can be dead, and the notification gets sent immediately. If zero, then name can't be dead. MACH_NOTIFY_SEND_POSSIBLE: if non-zero, will generate a send- possible notification as soon as it is possible to send to the port. If zero, will generate a send-possible notification only after a subsequent failed send (with MACH_SEND_NOTIFY option to mach_msg call). Can generate a dead-name notification if name is already dead or becomes dead before a send-possible notification fires. MACH_NOTIFY_NO_SENDERS: the notification gets sent immediately if the current mscount is greater than or equal to the sync value and there are no extant send rights. If the name is deleted before a successfully registered notification is delivered, it is replaced with a port-deleted notification.

**Mechanism:** Validates the notification capability and whether its port type can receive notifications. The ID selects port-destroyed backup registration, no-senders registration/immediate delivery based on send count and make-send generation, or dead-name/send-possible request-table installation. Replacement rights and immediate delivery have distinct ownership paths; port policy can reject registration even when the receive right exists. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1514).

**Declarations:** [`mach_port_request_notification`](../../../xnu/osfmk/mach/mach_port.defs#L306) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_request_notification(
  task : ipc_space_t;
  name : mach_port_name_t;
  msgid : mach_msg_id_t;
  sync : mach_port_mscount_t;
  notify : mach_port_send_once_t;
 out previous : mach_port_move_send_once_t);
```

**Local body:** [`mach_port_request_notification`](../../../xnu/osfmk/ipc/mach_port.c#L1514).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_can_receive_notifications`, `ipc_port_translate_receive`, `ipc_allow_register_pd_notification`, `ip_mq_unlock`, `ip_label_get`, `ipc_policy`, `mach_port_guard_exception`, `ip_mq_unlock_label_put`, `IP_VALID`, `ipc_notify_no_senders_mqueue`, `ipc_right_request_alloc`.

**User wrapper:** [`mach_port_request_notification`](../../../xnu/libsyscall/mach/mach_port.c#L239).
Calls visible in this body include `_kernelrpc_mach_port_request_notification_trap`, `_kernelrpc_mach_port_request_notification`.

### 3214: mach_port_insert_right

**Interface contract:**

> Inserts the specified rights into the target task, using the specified name. If inserting send/receive rights and the task already has send/receive rights for the port, then the names must agree. In any case, the task gains a user ref for the port.

**Mechanism:** Validates a legal destination name, a port-right disposition and a live kernel port capability, then calls `ipc_object_copyout_name`. The lower copyout operation installs or merges the transferred right at the requested name subject to entry/right collisions and uref limits; the kernel port pointer is not itself a userspace name. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1659).

**Declarations:** [`mach_port_insert_right`](../../../xnu/osfmk/mach/mach_port.defs#L322) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_insert_right(
  task : ipc_space_t;
  name : mach_port_name_t;
  poly : mach_port_poly_t);
```

**Local body:** [`mach_port_insert_right`](../../../xnu/osfmk/ipc/mach_port.c#L1659).
Calls visible in this body include `MACH_PORT_VALID`, `MACH_MSG_TYPE_PORT_ANY_RIGHT`, `IP_VALID`, `ipc_object_copyout_name`.

**User wrapper:** [`mach_port_insert_right`](../../../xnu/libsyscall/mach/mach_port.c#L262).
Calls visible in this body include `_kernelrpc_mach_port_insert_right_trap`, `_kernelrpc_mach_port_insert_right`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L262-L278):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L262-L278 -->
```c
mach_port_insert_right(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_t poly,
	mach_msg_type_name_t polyPoly)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_insert_right_trap(task, name, poly, polyPoly);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_insert_right(task, name, poly,
		    polyPoly);
	}

	return rv;
}
```

### 3215: mach_port_extract_right

**Interface contract:**

> Returns the specified right for the named port in the target task, extracting that right from the target task. The target task loses a user ref and the name may be available for recycling. msgt_name must be one of MACH_MSG_TYPE_MOVE_RECEIVE MACH_MSG_TYPE_COPY_SEND MACH_MSG_TYPE_MAKE_SEND MACH_MSG_TYPE_MOVE_SEND MACH_MSG_TYPE_MAKE_SEND_ONCE MACH_MSG_TYPE_MOVE_SEND_ONCE

**Mechanism:** Checks the disposition and name, then uses `ipc_object_copyin` to extract the right as a kernel port plus resulting disposition. Only copying a send right from the current space passes the immovable-send allowance here. On success it reports `ipc_object_copyin_type`; invalid special names are errors rather than an exported dead name. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1698).

**Declarations:** [`mach_port_extract_right`](../../../xnu/osfmk/mach/mach_port.defs#L341) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_extract_right(
  task : ipc_space_t;
  name : mach_port_name_t;
  msgt_name : mach_msg_type_name_t;
 out poly : mach_port_poly_t);
```

**Local body:** [`mach_port_extract_right`](../../../xnu/osfmk/ipc/mach_port.c#L1698).
Calls visible in this body include `MACH_MSG_TYPE_PORT_ANY`, `MACH_PORT_VALID`, `ipc_object_copyin`, `current_space`, `ipc_object_copyin_type`.

**User wrapper:** [`mach_port_extract_right`](../../../xnu/libsyscall/mach/mach_port.c#L281).
Calls visible in this body include `_kernelrpc_mach_port_extract_right`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L281-L294):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L281-L294 -->
```c
mach_port_extract_right(
	ipc_space_t task,
	mach_port_name_t name,
	mach_msg_type_name_t msgt_name,
	mach_port_t *poly,
	mach_msg_type_name_t *polyPoly)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_extract_right(task, name, msgt_name,
	    poly, polyPoly);

	return rv;
}
```

### 3216: mach_port_set_seqno

**Interface contract:**

> Only valid for receive rights. Sets the sequence number for the port.

**Mechanism:** Requires a valid receive right and calls `ipc_mqueue_set_seqno_locked` while the port queue is locked. It changes receive sequencing metadata, then releases the lock; it neither dequeues nor reorders a message. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1083).

**Declarations:** [`mach_port_set_seqno`](../../../xnu/osfmk/mach/mach_port.defs#L352) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_set_seqno(
  task : ipc_space_t;
  name : mach_port_name_t;
  seqno : mach_port_seqno_t);
```

**Local body:** [`mach_port_set_seqno`](../../../xnu/osfmk/ipc/mach_port.c#L1083).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ipc_mqueue_set_seqno_locked`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_set_seqno`](../../../xnu/libsyscall/mach/mach_port.c#L297).
Calls visible in this body include `_kernelrpc_mach_port_set_seqno`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L297-L307):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L297-L307 -->
```c
mach_port_set_seqno(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_seqno_t seqno)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_set_seqno(task, name, seqno);

	return rv;
}
```

### 3217: mach_port_get_attributes_from_user

**Interface contract:**

> Returns information about a port.

**Mechanism:** Converts a readable space and dispatches the information flavor. The helper returns queue limits, receive status, request-table capacity, extended importance/guard status, or service throttle state, with flavor-specific count/name checks. Receive status exposes whether send rights exist and whether the port belongs to a set, not the set's kernel identity. The service-throttle branch requires a service port and has different count handling from the fixed-size branches. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1932).

**Declarations:** [`mach_port_get_attributes_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L360) (`server64`, `server32`, `local64`); [`mach_port_get_attributes`](../../../xnu/osfmk/mach/mach_port.defs#L360) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_get_attributes_from_user(
  port : mach_port_t;
  name : mach_port_name_t;
  flavor : mach_port_flavor_t;
 out port_info_out : mach_port_info_t, CountInOut);
```

**Local body:** [`mach_port_get_attributes_from_user`](../../../xnu/osfmk/ipc/mach_port.c#L1932).
Calls visible in this body include `convert_port_to_space_read_no_eval`, `mach_port_get_attributes`, `ipc_space_release`.

### 3218: mach_port_set_attributes

**Interface contract:**

> Set attributes of a port

**Mechanism:** Dispatches by flavor under a translated receive-port lock. Queue-limit updates enforce `MACH_PORT_QLIMIT_MAX`; the DNREQUESTS_SIZE branch currently validates/looks up but does not resize. Temporary-owner/importance flavors change donation state and release/drop associated importance assertions after unlocking. Service throttling updates the service label; unsupported flavors and unsuitable port types fail. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1954).

**Declarations:** [`mach_port_set_attributes`](../../../xnu/osfmk/mach/mach_port.defs#L376) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_set_attributes(
  task : ipc_space_t;
  name : mach_port_name_t;
  flavor : mach_port_flavor_t;
  port_info : mach_port_info_t);
```

**Local body:** [`mach_port_set_attributes`](../../../xnu/osfmk/ipc/mach_port.c#L1954).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ipc_mqueue_set_qlimit_locked`, `ip_mq_unlock`, `ip_is_kobject`, `ip_is_special_reply_port`, `ip_get_imp_task`, `ipc_importance_task_is_any_receiver_type`, `ipc_importance_task_drop_internal_assertion`, `ipc_importance_task_release`, `current_task`, `ip_label_get`.

**User wrapper:** [`mach_port_set_attributes`](../../../xnu/libsyscall/mach/mach_port.c#L343).
Calls visible in this body include `_kernelrpc_mach_port_set_attributes`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L343-L356):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L343-L356 -->
```c
mach_port_set_attributes(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_flavor_t flavor,
	mach_port_info_t port_info,
	mach_msg_type_number_t port_infoCnt)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_set_attributes(task, name, flavor,
	    port_info, port_infoCnt);

	return rv;
}
```

### 3219: mach_port_allocate_qos

**Interface contract:**

> Allocates the specified kind of object, qos version. The right must be MACH_PORT_RIGHT_RECEIVE Like port_allocate_name, but the kernel picks a name. It can use any name not associated with a right.

**Mechanism:** Rejects the `name` option because this entry chooses the name, then shares the full allocator. Historical preallocation flags undergo size/right checks but are cleared rather than creating preallocated messages. The effective behavior therefore follows the present implementation, not the older QoS description. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L547).

**Declarations:** [`mach_port_allocate_qos`](../../../xnu/osfmk/mach/mach_port.defs#L391) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_allocate_qos(
  task : ipc_space_t;
  right : mach_port_right_t;
 inout qos : mach_port_qos_t;
 out name : mach_port_name_t);
```

**Local body:** [`mach_port_allocate_qos`](../../../xnu/osfmk/ipc/mach_port.c#L547).
Calls visible in this body include `mach_port_allocate_full`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L547-L561):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L547-L561 -->
```c
mach_port_allocate_qos(
	ipc_space_t             space,
	mach_port_right_t       right,
	mach_port_qos_t         *qosp,
	mach_port_name_t        *namep)
{
	kern_return_t           kr;

	if (qosp->name) {
		return KERN_INVALID_ARGUMENT;
	}
	kr = mach_port_allocate_full(space, right, MACH_PORT_NULL,
	    qosp, namep);
	return kr;
}
```

**User wrapper:** [`mach_port_allocate_qos`](../../../xnu/libsyscall/mach/mach_port.c#L359).
Calls visible in this body include `_kernelrpc_mach_port_allocate_qos`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L359-L370):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L359-L370 -->
```c
mach_port_allocate_qos(
	ipc_space_t task,
	mach_port_right_t right,
	mach_port_qos_t *qos,
	mach_port_name_t *name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_allocate_qos(task, right, qos, name);

	return rv;
}
```

### 3220: mach_port_allocate_full

**Interface contract:**

> Generic interface to allocation various kinds of ports. Should never be called directly by users (at least not unless they are exceedingly masochistic).

**Mechanism:** Validates the space, null prototype and any explicit name; preserves old preallocation errors while clearing that request. RECEIVE and PORT_SET select named or unnamed allocators according to `qos.name`. DEAD_NAME always uses `ipc_object_alloc_dead`, which chooses a fresh namespace entry rather than honoring the supplied name. Other right kinds are invalid: this routine does not manufacture a send right without a receive endpoint. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L588).

**Declarations:** [`mach_port_allocate_full`](../../../xnu/osfmk/mach/mach_port.defs#L404) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_allocate_full(
  task : ipc_space_t;
  right : mach_port_right_t;
  proto : mach_port_t;
 inout qos : mach_port_qos_t;
 inout name : mach_port_name_t);
```

**Local body:** [`mach_port_allocate_full`](../../../xnu/osfmk/ipc/mach_port.c#L588).
Calls visible in this body include `MACH_PORT_VALID`, `IPC_OBJECT_LABEL`, `ipc_port_alloc_name`, `ipc_port_alloc`, `ip_mq_unlock`, `ipc_pset_alloc_name`, `ipc_pset_alloc`, `ips_mq_unlock`, `ipc_object_alloc_dead`.

**User wrapper:** [`mach_port_allocate_full`](../../../xnu/libsyscall/mach/mach_port.c#L373).
Calls visible in this body include `_kernelrpc_mach_port_allocate_full`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L373-L385):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L373-L385 -->
```c
mach_port_allocate_full(
	ipc_space_t task,
	mach_port_right_t right,
	mach_port_t proto,
	mach_port_qos_t *qos,
	mach_port_name_t *name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_allocate_full(task, right, proto, qos, name);

	return rv;
}
```

### 3221: task_set_port_space

**Interface contract:**

> Pre-expand task port name space. OBSOLETE. Do nothing and return success.

**Mechanism:** The `table_entries` parameter is unused. The body rejects a null space and otherwise returns success, without reserving, growing or resizing the entry table. Its historical name is not evidence of current table-sizing behavior. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2256).

**Declarations:** [`task_set_port_space`](../../../xnu/osfmk/mach/mach_port.defs#L417) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine task_set_port_space(
  task : ipc_space_t;
  table_entries : int);
```

**Local body:** [`task_set_port_space`](../../../xnu/osfmk/ipc/mach_port.c#L2256).

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L2256-L2265):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L2256-L2265 -->
```c
task_set_port_space(
	ipc_space_t     space,
	__unused int    table_entries)
{
	if (space == IS_NULL) {
		return KERN_INVALID_TASK;
	}

	return KERN_SUCCESS;
}
```

**User wrapper:** [`task_set_port_space`](../../../xnu/libsyscall/mach/mach_port.c#L388).
Calls visible in this body include `_kernelrpc_task_set_port_space`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L388-L397):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L388-L397 -->
```c
task_set_port_space(
	ipc_space_t task,
	int table_entries)
{
	kern_return_t rv;

	rv = _kernelrpc_task_set_port_space(task, table_entries);

	return rv;
}
```

### 3222: mach_port_get_srights

**Interface contract:**

> Returns the exact number of extant send rights for the given receive right.

**Mechanism:** Requires a receive right, reads `ip_srights` under the port lock, then publishes that count after unlocking. This is the port's send-right reference count rather than the urefs held under one namespace name. Compare the separate `mach_port_get_refs` interface. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L105).

**Declarations:** [`mach_port_get_srights`](../../../xnu/osfmk/mach/mach_port.defs#L426) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_get_srights(
  task : ipc_space_t;
  name : mach_port_name_t;
 out srights : mach_port_rights_t);
```

**Local body:** [`mach_port_get_srights`](../../../xnu/osfmk/ipc/mach_debug.c#L105).
Calls visible in this body include `ipc_port_translate_receive`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_get_srights`](../../../xnu/libsyscall/mach/mach_port.c#L400).
Calls visible in this body include `_kernelrpc_mach_port_get_srights`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L400-L410):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L400-L410 -->
```c
mach_port_get_srights(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_rights_t *srights)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_get_srights(task, name, srights);

	return rv;
}
```

### 3223: mach_port_space_info_from_user

**Interface contract:**

> Returns information about an IPC space.

**Mechanism:** Converts a readable space and collects namespace information plus an out-of-line entry array. Allocation occurs outside the space lock; the helper rechecks size and may drop/reacquire the lock between batches, so the entire array is not an atomic snapshot. It captures object pointer values without retaining the objects and hashes those values after unlocking; it does not dereference them then. Obsolete tree output is empty, and the wrapper releases the space reference. [Wrapper](../../../xnu/osfmk/ipc/mach_debug.c#L323), [collection/export](../../../xnu/osfmk/ipc/mach_debug.c#L218).

**Declarations:** [`mach_port_space_info_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L435) (`server64`, `server32`, `local64`); [`mach_port_space_info`](../../../xnu/osfmk/mach/mach_port.defs#L435) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_space_info_from_user(
  port : mach_port_t;
 out space_info : ipc_info_space_t;
 out table_info : ipc_info_name_array_t;
 out tree_info : ipc_info_tree_name_array_t);
```

**Local body:** [`mach_port_space_info_from_user`](../../../xnu/osfmk/ipc/mach_debug.c#L323).
Calls visible in this body include `convert_port_to_space_read_no_eval`, `mach_port_space_info`, `ipc_space_release`.

### 3224: mach_port_dnrequest_info

**Interface contract:**

> Returns information about the dead-name requests registered with the named receive right.

**Mechanism:** Translates a receive right and scans `ip_requests` while holding the port lock. Returns table capacity and the number of entries with a nonnull notification right, excluding the host-notify sentinel. An absent request table produces zero for both outputs. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L404).

**Declarations:** [`mach_port_dnrequest_info`](../../../xnu/osfmk/mach/mach_port.defs#L451) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_dnrequest_info(
  task : ipc_space_t;
  name : mach_port_name_t;
 out dnr_total : unsigned;
 out dnr_used : unsigned);
```

**Local body:** [`mach_port_dnrequest_info`](../../../xnu/osfmk/ipc/mach_debug.c#L404).
Calls visible in this body include `ipc_port_translate_receive`, `ipc_port_request_table_base`, `ipc_port_request_table_next_elem`, `ipc_port_request_table_count`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_dnrequest_info`](../../../xnu/libsyscall/mach/mach_port.c#L529).
Calls visible in this body include `_kernelrpc_mach_port_dnrequest_info`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L529-L541):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L529-L541 -->
```c
mach_port_dnrequest_info(
	ipc_space_t task,
	mach_port_name_t name,
	unsigned *dnr_total,
	unsigned *dnr_used)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_dnrequest_info(task, name, dnr_total,
	    dnr_used);

	return rv;
}
```

### 3225: mach_port_kernel_object

**Interface contract:**

> mach_port_kernel_object_from_user

**Mechanism:** The historical kernel-object query remains a client declaration but the corresponding server slot is skipped. Follow the newer kobject query/description entries for current local inspection behavior; do not interpret this declaration as a callable receiver.

**Declarations:** [`mach_port_kernel_object`](../../../xnu/osfmk/mach/mach_port.defs#L463) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_port_kernel_object(
  task : ipc_space_read_t;
  name : mach_port_name_t;
 out object_type : unsigned;
 out object_addr : unsigned);
```

**User wrapper:** [`mach_port_kernel_object`](../../../xnu/libsyscall/mach/mach_port.c#L544).
Calls visible in this body include `_kernelrpc_mach_port_kobject`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L544-L561):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L544-L561 -->
```c
mach_port_kernel_object(
	ipc_space_t task,
	mach_port_name_t name,
	unsigned *object_type,
	unsigned *object_addr)
{
	kern_return_t rv;
	mach_vm_address_t addr;

	rv = _kernelrpc_mach_port_kobject(task, name,
	    object_type, &addr);

	if (rv == KERN_SUCCESS && object_addr) {
		*object_addr = (unsigned)addr;
	}

	return rv;
}
```

Only a user-library body was resolved here; that is not a kernel receiver implementation.

### 3226: mach_port_insert_member

**Interface contract:**

> Inserts the specified rights into the portset identified by the <task, pset> pair. The results of passing in the Poly argument via the supplied disposition must yield a receive right. If the <task,pset> pair does not represent a valid portset KERN_INVALID_RIGHT is returned. If the passed in name argument does not represent a receive right, KERN_INVALID_CAPABILITY will be returned. If the port represented by the receive right is already in the portset, KERN_ALREADY_IN_SET is returned.

**Mechanism:** Preallocates a waitq link, jointly translates and locks the receive port and port set, then calls `ipc_mqueue_add_locked`. Unlocks both objects and frees a link that was not consumed. Existing membership and invalid rights are handled through the actual add/translation result, rather than replacing other memberships as `move_member` does. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2153).

**Declarations:** [`mach_port_insert_member`](../../../xnu/osfmk/mach/mach_port.defs#L486) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_insert_member(
  task : ipc_space_t;
  name : mach_port_name_t;
  pset : mach_port_name_t);
```

**Local body:** [`mach_port_insert_member`](../../../xnu/osfmk/ipc/mach_port.c#L2153).
Calls visible in this body include `MACH_PORT_VALID`, `waitq_link_alloc`, `ipc_object_translate_port_pset`, `ipc_mqueue_add_locked`, `ips_mq_unlock`, `ip_mq_unlock`, `waitq_link_free`.

**User wrapper:** [`mach_port_insert_member`](../../../xnu/libsyscall/mach/mach_port.c#L564).
Calls visible in this body include `_kernelrpc_mach_port_insert_member_trap`, `_kernelrpc_mach_port_insert_member`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L564-L578):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L564-L578 -->
```c
mach_port_insert_member(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_name_t pset)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_insert_member_trap(task, name, pset);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_insert_member(task, name, pset);
	}

	return rv;
}
```

### 3227: mach_port_extract_member

**Interface contract:**

> Extracts the specified right from the named portset in the target task. the target task. The target task loses a user ref and the name may be available for recycling. msgt_name must be one of MACH_MSG_TYPE_MOVE_RECEIVE MACH_MSG_TYPE_COPY_SEND MACH_MSG_TYPE_MAKE_SEND MACH_MSG_TYPE_MOVE_SEND MACH_MSG_TYPE_MAKE_SEND_ONCE MACH_MSG_TYPE_MOVE_SEND_ONCE

**Mechanism:** Jointly translates/locks the receive port and named set, unlinks that specific waitq membership, unlocks both, and frees the detached link. A missing link produces `KERN_NOT_IN_SET`; other memberships are not removed by this entry. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2212).

**Declarations:** [`mach_port_extract_member`](../../../xnu/osfmk/mach/mach_port.defs#L505) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_extract_member(
  task : ipc_space_t;
  name : mach_port_name_t;
  pset : mach_port_name_t);
```

**Local body:** [`mach_port_extract_member`](../../../xnu/osfmk/ipc/mach_port.c#L2212).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_object_translate_port_pset`, `waitq_unlink_locked`, `ips_mq_unlock`, `ip_mq_unlock`, `waitq_link_free`.

**User wrapper:** [`mach_port_extract_member`](../../../xnu/libsyscall/mach/mach_port.c#L581).
Calls visible in this body include `_kernelrpc_mach_port_extract_member_trap`, `_kernelrpc_mach_port_extract_member`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L581-L595):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L581-L595 -->
```c
mach_port_extract_member(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_name_t pset)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_extract_member_trap(task, name, pset);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_extract_member(task, name, pset);
	}

	return rv;
}
```

### 3228: mach_port_get_context_from_user

**Interface contract:**

> Only valid for receive rights. Gets the context pointer for the port.

**Mechanism:** Converts the destination with the readable-space converter and calls the receive-right context helper. The helper returns zero for strictly guarded ports because the context is also the guard value; otherwise it copies `ip_context` under the port lock. The space reference is released after the call. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1161).

**Declarations:** [`mach_port_get_context_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L514) (`server64`, `server32`, `local64`); [`mach_port_get_context`](../../../xnu/osfmk/mach/mach_port.defs#L514) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_get_context_from_user(
  port : mach_port_t;
  name : mach_port_name_t;
 out context : mach_vm_address_t
 );
```

**Local body:** [`mach_port_get_context_from_user`](../../../xnu/osfmk/ipc/mach_port.c#L1161).
Calls visible in this body include `convert_port_to_space_read_no_eval`, `mach_port_get_context`, `ipc_space_release`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L1161-L1178):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L1161-L1178 -->
```c
mach_port_get_context_from_user(
	mach_port_t             port,
	mach_port_name_t        name,
	mach_vm_address_t       *context)
{
	kern_return_t kr;

	ipc_space_t space = convert_port_to_space_read_no_eval(port);

	if (space == IPC_SPACE_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kr = mach_port_get_context(space, name, context);

	ipc_space_release(space);
	return kr;
}
```

### 3229: mach_port_set_context

**Interface contract:**

> Only valid for receive rights. Sets the context pointer for the port.

**Mechanism:** Translates a receive right and updates `ip_context` under the port lock. Strict guarding prevents this overwrite: the function unlocks, records `kGUARD_EXC_SET_CONTEXT` and returns an error. Context is application-associated metadata, but it also participates in guard enforcement. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L1195).

**Declarations:** [`mach_port_set_context`](../../../xnu/osfmk/mach/mach_port.defs#L535) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_set_context(
  task : ipc_space_t;
  name : mach_port_name_t;
  context : mach_vm_address_t
  );
```

**Local body:** [`mach_port_set_context`](../../../xnu/osfmk/ipc/mach_port.c#L1195).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ip_mq_unlock`, `mach_port_guard_exception`.

**User wrapper:** [`mach_port_set_context`](../../../xnu/libsyscall/mach/mach_port.c#L616).
Calls visible in this body include `_kernelrpc_mach_port_set_context`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L616-L626):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L616-L626 -->
```c
mach_port_set_context(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_context_t context)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_set_context(task, name, context);

	return rv;
}
```

### 3230: mach_port_kobject_from_user

**Interface contract:**

> Return the type and address of the kernel object that the given send/receive right represents.

**Mechanism:** Delegates to `mach_port_kobject_description_from_user` with no description buffer. The common helper converts a readable namespace, accepts send/receive rights, derives an exported object type, and returns address zero in release builds or a hashed kernel address in development/debug builds. It does not grant access to the associated object. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L651).

**Declarations:** [`mach_port_kobject_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L549) (`server64`, `server32`, `local64`); [`mach_port_kobject`](../../../xnu/osfmk/mach/mach_port.defs#L549) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_kobject_from_user(
  port : mach_port_t;
  name : mach_port_name_t;
 out object_type : ipc_info_object_type_t;
 out object_addr : mach_vm_address_t);
```

**Local body:** [`mach_port_kobject_from_user`](../../../xnu/osfmk/ipc/mach_debug.c#L651).
Calls visible in this body include `mach_port_kobject_description_from_user`.

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_debug.c#L651-L658):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_debug.c#L651-L658 -->
```c
mach_port_kobject_from_user(
	mach_port_t                     port,
	mach_port_name_t                name,
	ipc_info_object_type_t          *typep,
	mach_vm_address_t               *addrp)
{
	return mach_port_kobject_description_from_user(port, name, typep, addrp, NULL);
}
```

### 3231: mach_port_construct

**Interface contract:**

> Constructs a right based on the options passed in. Also allows guarding the port as one of the options if the requested right is a receive right.

**Mechanism:** Validates one port-type selection and unused flags, derives the label/type and entitlement/policy requirements, checks queue limits and optional render-server tracking, then allocates service/bootstrap/connection label state and the namespace port, passing any initial-send-right request as an allocation flag. After successful allocation the body enters its no-failure configuration phase: queue limit, donation/reply settings and guard/context are installed before unlocking. See [construction and policy](../../subsystems/ipc/guards-and-policy-enforcement.md). [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2420).

**Declarations:** [`mach_port_construct`](../../../xnu/osfmk/mach/mach_port.defs#L568) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_construct(
  task : ipc_space_t;
  options : mach_port_options_ptr_t;
  context : uint64_t;
 out name : mach_port_name_t);
```

**Local body:** [`mach_port_construct`](../../../xnu/osfmk/ipc/mach_port.c#L2420).
Calls visible in this body include `IPC_OBJECT_LABEL`, `ipc_space_policy`, `mach_port_construct_check_service_port`, `ipc_should_apply_policy`, `ipc_policy`, `IOCurrentTaskHasEntitlement`, `ipc_triage_policy_violation`, `mach_port_guard_exception`, `proc_get_effective_task_policy`, `current_task`, `work_interval_port_type_render_server`, `ip_is_any_service_port_type`.

**User wrapper:** [`mach_port_construct`](../../../xnu/libsyscall/mach/mach_port.c#L658).
Calls visible in this body include `_kernelrpc_mach_port_construct_trap`, `_kernelrpc_mach_port_construct`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L658-L673):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L658-L673 -->
```c
mach_port_construct(
	ipc_space_t             task,
	mach_port_options_t     *options,
	mach_port_context_t     context,
	mach_port_name_t        *name)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_construct_trap(task, options, (uint64_t) context, name);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_construct(task, options, (uint64_t) context, name);
	}

	return rv;
}
```

### 3232: mach_port_destruct

**Interface contract:**

> Destroys a mach port using the guard provided for guarded ports. Also reduces the user ref count for send rights as specified by srdelta.

**Mechanism:** Looks up the namespace entry with a write lock and delegates to `ipc_right_destruct`, which requires a receive right and a nonpositive send-right delta. The guard value is checked only when the port is guarded; unguarded receive rights can also be destructed. The helper adjusts send urefs, then removes receive ownership, potentially transferring it through a port-destroyed request rather than killing the endpoint. It releases the space lock and performs notification cleanup. [Wrapper](../../../xnu/osfmk/ipc/mach_port.c#L2698), [rights helper](../../../xnu/osfmk/ipc/ipc_right.c#L1664).

**Declarations:** [`mach_port_destruct`](../../../xnu/osfmk/mach/mach_port.defs#L583) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_destruct(
  task : ipc_space_t;
  name : mach_port_name_t;
  srdelta : mach_port_delta_t;
  guard : uint64_t
  );
```

**Local body:** [`mach_port_destruct`](../../../xnu/osfmk/ipc/mach_port.c#L2698).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_right_lookup_write`, `mach_port_guard_exception`, `ipc_right_destruct`.

**User wrapper:** [`mach_port_destruct`](../../../xnu/libsyscall/mach/mach_port.c#L676).
Calls visible in this body include `_kernelrpc_mach_port_destruct_trap`, `_kernelrpc_mach_port_destruct`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L676-L691):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L676-L691 -->
```c
mach_port_destruct(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_port_delta_t       srdelta,
	mach_port_context_t     guard)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_destruct_trap(task, name, srdelta, (uint64_t) guard);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_destruct(task, name, srdelta, (uint64_t) guard);
	}

	return rv;
}
```

### 3233: mach_port_guard

**Interface contract:**

> Guard an already existing port. Allows guarding receive rights only. Uses the context field in the port structure to store the guard.

**Mechanism:** Translates and locks the receive right, maps the boolean strict option to `MPG_STRICT`, and invokes the shared guard helper. A nonzero existing context causes a guard exception/error; otherwise the helper stores the guard in `ip_context` and sets guarded/strict state. The outer wrapper releases the queue lock. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2743).

**Declarations:** [`mach_port_guard`](../../../xnu/osfmk/mach/mach_port.defs#L599) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_guard(
  task : ipc_space_t;
  name : mach_port_name_t;
  guard : uint64_t;
  strict : boolean_t);
```

**Local body:** [`mach_port_guard`](../../../xnu/osfmk/ipc/mach_port.c#L2743).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `mach_port_guard_exception`, `mach_port_guard_locked`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_guard`](../../../xnu/libsyscall/mach/mach_port.c#L694).
Calls visible in this body include `_kernelrpc_mach_port_guard_trap`, `_kernelrpc_mach_port_guard`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L694-L709):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L694-L709 -->
```c
mach_port_guard(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_port_context_t     guard,
	boolean_t               strict)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_guard_trap(task, name, (uint64_t) guard, strict);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_guard(task, name, (uint64_t) guard, strict);
	}

	return rv;
}
```

### 3234: mach_port_unguard

**Interface contract:**

> Unguard a port guarded previously. For unguarded ports or incorrect guards passed in it raises an exception indicating guarding misbehavior.

**Mechanism:** Under a translated receive-port lock, checks that the port is guarded and the supplied value matches `ip_context`. Failure records the appropriate guard exception. Success clears the context and both guarded/strict flags; it does not destroy the name or remove any immovable-receive label state. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2796).

**Declarations:** [`mach_port_unguard`](../../../xnu/osfmk/mach/mach_port.defs#L614) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_unguard(
  task : ipc_space_t;
  name : mach_port_name_t;
  guard : uint64_t
  );
```

**Local body:** [`mach_port_unguard`](../../../xnu/osfmk/ipc/mach_port.c#L2796).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `mach_port_guard_exception`, `mach_port_unguard_locked`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_unguard`](../../../xnu/libsyscall/mach/mach_port.c#L712).
Calls visible in this body include `_kernelrpc_mach_port_unguard_trap`, `_kernelrpc_mach_port_unguard`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L712-L726):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L712-L726 -->
```c
mach_port_unguard(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_port_context_t     guard)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_unguard_trap(task, name, (uint64_t) guard);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_port_unguard(task, name, (uint64_t) guard);
	}

	return rv;
}
```

### 3235: mach_port_space_basic_info

**Interface contract:**

> Returns basic information about an IPC space.

**Mechanism:** Read-locks an active IPC space, obtains its entry-table size and computes used entries from the free count, excluding entry zero. Returns the generation-number mask and zeroed reserved fields without allocating the full per-name array. Dead/null spaces fail. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L358).

**Declarations:** [`mach_port_space_basic_info`](../../../xnu/osfmk/mach/mach_port.defs#L627) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_space_basic_info(
  task : ipc_space_inspect_t;
 out basic_info : ipc_info_space_basic_t);
```

**Local body:** [`mach_port_space_basic_info`](../../../xnu/osfmk/ipc/mach_debug.c#L358).
Calls visible in this body include `is_read_lock`, `is_active`, `is_read_unlock`, `ipc_entry_table_count`, `is_active_table`, `MACH_PORT_NGEN`.

**User wrapper:** [`mach_port_space_basic_info`](../../../xnu/libsyscall/mach/mach_port.c#L430).
Calls visible in this body include `_kernelrpc_mach_port_space_basic_info`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L430-L439):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L430-L439 -->
```c
mach_port_space_basic_info(
	ipc_space_t task,
	ipc_info_space_basic_t *space_basic_info)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_space_basic_info(task, space_basic_info);

	return rv;
}
```

### 3236: mach_port_special_reply_port_reset_link

**Interface contract:**

> Returns sync ipc turnstile link status for special reply ports.

**Mechanism:** Development/debug builds require the current IPC space and the calling thread's exact special-reply receive port. They return `ip_srp_lost_link` and clear that diagnostic flag under the port lock. Other builds return `KERN_NOT_SUPPORTED`; the operation does not reconstruct a lost synchronization link. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L662).

**Declarations:** [`mach_port_special_reply_port_reset_link`](../../../xnu/osfmk/mach/mach_port.defs#L636) (`server64`, `server32`, `client64`, `client32`, `sender64`, `local64`).
**Reserved instead in:** `libsyscall64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_port_special_reply_port_reset_link(
  task : ipc_space_t;
  name : mach_port_name_t;
 out srp_lost_link : boolean_t);
```

**Local body:** [`mach_port_special_reply_port_reset_link`](../../../xnu/osfmk/ipc/mach_debug.c#L662).
Calls visible in this body include `current_thread`, `current_space`, `MACH_PORT_VALID`, `IP_VALID`, `ipc_port_translate_receive`, `ip_mq_unlock`.

**Local body:** [`mach_port_special_reply_port_reset_link`](../../../xnu/osfmk/ipc/mach_debug.c#L701).

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_debug.c#L701-L707):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_debug.c#L701-L707 -->
```c
mach_port_special_reply_port_reset_link(
	__unused ipc_space_t            space,
	__unused mach_port_name_t       name,
	__unused boolean_t              *srp_lost_link)
{
	return KERN_NOT_SUPPORTED;
}
```

### 3237: mach_port_guard_with_flags

**Interface contract:**

> Guard an already existing port. Allows guarding receive rights only. Uses the context field in the port structure to store the guard.

**Mechanism:** Shares receive-right translation and the guard helper with the boolean API. The helper rejects a nonzero existing context, stores the guard/strict bit, and can transition the port label to immovable-receive state for `MPG_IMMOVABLE_RECEIVE`. Follow the actual helper rather than older comments about unsupported guard flag checks. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2845).

**Declarations:** [`mach_port_guard_with_flags`](../../../xnu/osfmk/mach/mach_port.defs#L649) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_guard_with_flags(
  task : ipc_space_t;
  name : mach_port_name_t;
  guard : uint64_t;
  flags : uint64_t);
```

**Local body:** [`mach_port_guard_with_flags`](../../../xnu/osfmk/ipc/mach_port.c#L2845).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `mach_port_guard_exception`, `mach_port_guard_locked`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_guard_with_flags`](../../../xnu/libsyscall/mach/mach_port.c#L775).
Calls visible in this body include `_kernelrpc_mach_port_guard_with_flags`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L775-L786):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L775-L786 -->
```c
mach_port_guard_with_flags(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_port_context_t     guard,
	uint64_t                flags)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_guard_with_flags(task, name, (uint64_t) guard, flags);

	return rv;
}
```

### 3238: mach_port_swap_guard

**Interface contract:**

> Swap guard value of an existing guarded port. Works only if it is not a strict guard.

**Mechanism:** Requires a guarded receive port, rejects strict guards, and compares the existing context with `old_guard`. Only after all three checks does it overwrite `ip_context` with `new_guard`. Each failed state check unlocks before recording the corresponding guard exception; this operation preserves guarded state. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2892).

**Declarations:** [`mach_port_swap_guard`](../../../xnu/osfmk/mach/mach_port.defs#L663) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_swap_guard(
  task : ipc_space_t;
  name : mach_port_name_t;
  old_guard : uint64_t;
  new_guard : uint64_t);
```

**Local body:** [`mach_port_swap_guard`](../../../xnu/osfmk/ipc/mach_port.c#L2892).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `mach_port_guard_exception`, `ip_mq_unlock`.

**User wrapper:** [`mach_port_swap_guard`](../../../xnu/libsyscall/mach/mach_port.c#L789).
Calls visible in this body include `_kernelrpc_mach_port_swap_guard`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L789-L800):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L789-L800 -->
```c
mach_port_swap_guard(
	ipc_space_t             task,
	mach_port_name_t        name,
	mach_port_context_t     old_guard,
	mach_port_context_t     new_guard)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_swap_guard(task, name, (uint64_t)old_guard, (uint64_t)new_guard);

	return rv;
}
```

### 3239: mach_port_kobject_description_from_user

**Interface contract:**

> Return the type and address of the kernel object that the given send/receive right represents.

**Mechanism:** Converts a readable space and looks up a send/receive right. The common body reports a public object-type classification and optionally formats IOKit object, task-identity-token, named-memory-entry or thread-resume details. IOKit objects are retained before dropping the port lock for description work. Raw addresses are not exposed: release builds return zero and development/debug builds return a hash. [`Implementation`](../../../xnu/osfmk/ipc/mach_debug.c#L629).

**Declarations:** [`mach_port_kobject_description_from_user`](../../../xnu/osfmk/mach/mach_port.defs#L682) (`server64`, `server32`, `local64`); [`mach_port_kobject_description`](../../../xnu/osfmk/mach/mach_port.defs#L682) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine
mach_port_kobject_description_from_user(
  port : mach_port_t;
  name : mach_port_name_t;
 out object_type : ipc_info_object_type_t;
 out object_addr : mach_vm_address_t;
 out description : kobject_description_t);
```

**Local body:** [`mach_port_kobject_description_from_user`](../../../xnu/osfmk/ipc/mach_debug.c#L629).
Calls visible in this body include `convert_port_to_space_read_no_eval`, `mach_port_kobject_description`, `ipc_space_release`.

### 3240: mach_port_is_connection_for_service

**Interface contract:**

> Verifies that connection port was created for this service port and returns the filter policy id for that connection port

**Mechanism:** Requires a supported message-filter callback version, translates the service receive right and retains its sandbox label before unlocking. With no service label it returns policy ID zero. Otherwise it translates the connection port, retains an applicable connection label, and passes both to the filter callback, whose contract consumes those references. The filter implementation is an external policy boundary. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L2947).

**Declarations:** [`mach_port_is_connection_for_service`](../../../xnu/osfmk/mach/mach_port.defs#L700) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_is_connection_for_service(
  task : ipc_space_t;
  connection_port : mach_port_name_t;
  service_port : mach_port_name_t;
 out filter_policy_id : uint64_t
);
```

**Local body:** [`mach_port_is_connection_for_service`](../../../xnu/osfmk/ipc/mach_port.c#L2947).
Calls visible in this body include `MACH_PORT_VALID`, `mach_msg_filter_at_least`, `ipc_port_translate_receive`, `ip_label_get`, `ip_is_any_service_port_type`, `ip_mq_unlock_label_put`, `mach_msg_filter_retain_sblabel_callback`, `mach_msg_filter_dealloc_service_port_sblabel_callback`, `mach_msg_filter_get_connection_port_filter_policy_callback`.

**User wrapper:** [`mach_port_is_connection_for_service`](../../../xnu/libsyscall/mach/mach_port.c#L803).
Calls visible in this body include `_kernelrpc_mach_port_is_connection_for_service`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L803-L814):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L803-L814 -->
```c
mach_port_is_connection_for_service(
	ipc_space_t task,
	mach_port_name_t connection_port_name,
	mach_port_name_t service_port_name,
	uint64_t *filter_policy_id)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_is_connection_for_service(task, connection_port_name, service_port_name, filter_policy_id);

	return rv;
}
```

### 3241: mach_port_get_service_port_info

**Interface contract:**

> Get information about service ports. Supported only on development/debug builds

**Mechanism:** With `CONFIG_SERVICE_PORT_INFO`, translates a receive right and accepts service or bootstrap labels, copying their recorded information while protected. Other types fail with invalid capability. The configuration-disabled body always returns `KERN_NOT_SUPPORTED`. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L3024).

**Declarations:** [`mach_port_get_service_port_info`](../../../xnu/osfmk/mach/mach_port.defs#L711) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_get_service_port_info(
  task : ipc_space_read_t;
  name : mach_port_name_t;
 out sp_info_out : mach_service_port_info_data_t
);
```

**Local body:** [`mach_port_get_service_port_info`](../../../xnu/osfmk/ipc/mach_port.c#L3024).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ip_label_get`, `ip_is_any_service_port_type`, `ipc_service_port_label_get_info`, `ip_is_bootstrap_port_type`, `ipc_bootstrap_port_label_get_info`, `ip_mq_unlock_label_put`.

**Local body:** [`mach_port_get_service_port_info`](../../../xnu/osfmk/ipc/mach_port.c#L3068).

[Implementation excerpt](../../../xnu/osfmk/ipc/mach_port.c#L3068-L3074):
<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_port.c#L3068-L3074 -->
```c
mach_port_get_service_port_info(
	__unused ipc_space_read_t           space,
	__unused mach_port_name_t           name,
	__unused mach_service_port_info_t   sp_info)
{
	return KERN_NOT_SUPPORTED;
}
```

**User wrapper:** [`mach_port_get_service_port_info`](../../../xnu/libsyscall/mach/mach_port.c#L817).
Calls visible in this body include `_kernelrpc_mach_port_get_service_port_info`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L817-L827):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L817-L827 -->
```c
mach_port_get_service_port_info(
	ipc_space_read_t task,
	mach_port_name_t name,
	mach_service_port_info_data_t *sp_info_out)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_get_service_port_info(task, name, sp_info_out);

	return rv;
}
```

### 3242: mach_port_assert_attributes

Check the receive port's asserted attributes and invoke guard-exception handling when the assertion fails.

**Mechanism:** Currently accepts only `MACH_PORT_GUARD_INFO`, checks the input count and receive right, then requires guarded state, strict guarding and the matching context value. Mismatch records a guard exception and returns invalid argument; success only verifies state and does not modify it. [`Implementation`](../../../xnu/osfmk/ipc/mach_port.c#L3078).

**Declarations:** [`mach_port_assert_attributes`](../../../xnu/osfmk/mach/mach_port.defs#L717) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_port_assert_attributes(
  task : ipc_space_t;
  name : mach_port_name_t;
  flavor : mach_port_flavor_t;
  info : mach_port_info_t
);
```

**Local body:** [`mach_port_assert_attributes`](../../../xnu/osfmk/ipc/mach_port.c#L3078).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_receive`, `ip_mq_unlock`, `mach_port_guard_exception`.

**User wrapper:** [`mach_port_assert_attributes`](../../../xnu/libsyscall/mach/mach_port.c#L830).
Calls visible in this body include `_kernelrpc_mach_port_assert_attributes`.

[Implementation excerpt](../../../xnu/libsyscall/mach/mach_port.c#L830-L843):
<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_port.c#L830-L843 -->
```c
mach_port_assert_attributes(
	ipc_space_t task,
	mach_port_name_t name,
	mach_port_flavor_t flavor,
	mach_port_info_t info,
	mach_msg_type_number_t infoCnt)
{
	kern_return_t rv;

	rv = _kernelrpc_mach_port_assert_attributes(task, name, flavor,
	    info, infoCnt);

	return rv;
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
