# Mach messages: memory_entry

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/memory_entry.defs](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 4900: mach_memory_entry_purgable_control

Query or change purgeable state through a named memory entry.

**Mechanism:** The user entry rejects SET_STATE_FROM_KERNEL before common processing. The helper resolves the named entry, checks the control/state mask, locks the entry, and requires an object-backed entry rather than a submap or copy. It then locks the object and verifies that the entry covers the entire object at offset zero. Only after establishing that ownership/extent does it release the entry lock and invoke `vm_object_purgable_control`, finally unlocking the object. Invalid partial entries cannot change whole-object purgeability through this API. [Bodies](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1474-L1546).

**Declarations:** [`mach_memory_entry_purgable_control`](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L39) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_entry_purgable_control(
  mem_entry : mem_entry_name_port_t;
  control : vm_purgable_t;
 inout state : int);
```

**Local body:** [`mach_memory_entry_purgable_control`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1474).
Calls visible in this body include `memory_entry_purgeable_control_internal`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1474-L1485):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1474-L1485 -->
```c
mach_memory_entry_purgable_control(
	ipc_port_t      entry_port,
	vm_purgable_t   control,
	int             *state)
{
	if (control == VM_PURGABLE_SET_STATE_FROM_KERNEL) {
		/* not allowed from user-space */
		return KERN_INVALID_ARGUMENT;
	}

	return memory_entry_purgeable_control_internal(entry_port, control, state);
}
```

### 4901: mach_memory_entry_access_tracking

Query/change the entry's access-tracking state and return accumulated reads/writes.

**Mechanism:** The helper translates the named-entry port and holds its lock while checking that it is object-backed, not a submap or copy, with a nonnull object. Only `VM_OBJECT_ACCESS_TRACKING` builds call `vm_object_access_tracking` to update/read tracking and read/write counters. Otherwise the validated operation returns `KERN_NOT_SUPPORTED`. The receiver does not silently fabricate zero access counts or claim that a named-entry capability always enables tracking. Entry unlocking is shared by the configured and unsupported paths. [Implementation](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1549-L1608).

**Declarations:** [`mach_memory_entry_access_tracking`](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L44) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_entry_access_tracking(
  mem_entry : mem_entry_name_port_t;
 inout access_tracking : int;
 out access_tracking_reads : uint32_t;
 out access_tracking_writes : uint32_t);
```

**Local body:** [`mach_memory_entry_access_tracking`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1598).
Calls visible in this body include `memory_entry_access_tracking_internal`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1598-L1608):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1598-L1608 -->
```c
mach_memory_entry_access_tracking(
	ipc_port_t      entry_port,
	int             *access_tracking,
	uint32_t        *access_tracking_reads,
	uint32_t        *access_tracking_writes)
{
	return memory_entry_access_tracking_internal(entry_port,
	           access_tracking,
	           access_tracking_reads,
	           access_tracking_writes);
}
```

### 4902: mach_memory_entry_ownership_from_user

Assign memory-entry ownership and ledger charging after converting the supplied task capability or identity token.

**Mechanism:** The MIG receiver first limits flags to `VM_LEDGER_FLAGS_USER`. It accepts either a task identity token or task port, retains the resolved owner, and discards a corpse owner rather than transferring to it. The ownership helper applies entitlement/tag/object checks; a null owner means leave ownership unchanged. The wrapper releases the task reference afterward and consumes the incoming owner send right only on success, following its MIG convention. Failure is not a transfer of that argument right. [Receiver and cleanup](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1818-L1862), [policy/backend](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1618-L1814).

**Declarations:** [`mach_memory_entry_ownership_from_user`](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L51) (`server64`, `server32`, `local64`); [`mach_memory_entry_ownership`](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L55) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_entry_ownership_from_user(
  mem_entry : mem_entry_name_port_t;
  owner : mach_port_t;
  ledger_tag : int;
  ledger_flags : int);
```

**Local body:** [`mach_memory_entry_ownership_from_user`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1818).
Calls visible in this body include `IP_VALID`, `ip_type`, `convert_port_to_task_id_token`, `task_identity_token_get_task_grp`, `task_id_token_release`, `convert_port_to_task_mig`, `task_is_a_corpse`, `task_deallocate_mig`, `mach_memory_entry_ownership`, `ipc_port_release_send`.

### 4903: mach_memory_entry_get_page_counts

Return resident, dirty and swapped-page counts for an eligible named memory entry.

**Mechanism:** The receiver resolves and locks the named entry, rejects submaps/copies, and requires an object. It locks the object before reading the entry's offset/size, expands that extent to object page boundaries, releases the entry lock, and calls `vm_object_get_page_counts` for resident, dirty and swapped counts. The object remains locked until counting finishes. These outputs measure the named extent under that protocol; they neither make pages resident nor transfer a reference to any individual page. [Body](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1865-L1911).

**Declarations:** [`mach_memory_entry_get_page_counts`](../../../platydoc-data/xnu/osfmk/mach/memory_entry.defs#L73) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_memory_entry_get_page_counts(
  mem_entry : mem_entry_name_port_t;
 out resident_cnt : uint64_t;
 out dirty_cnt : uint64_t;
 out swapped_cnt : uint64_t);
```

**Local body:** [`mach_memory_entry_get_page_counts`](../../../platydoc-data/xnu/osfmk/vm/vm_memory_entry.c#L1865).
Calls visible in this body include `mach_memory_entry_from_port`, `named_entry_lock`, `named_entry_unlock`, `vm_named_entry_to_vm_object`, `vm_object_lock`, `vm_object_round_page`, `vm_object_trunc_page`, `vm_object_get_page_counts`, `vm_object_unlock`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
