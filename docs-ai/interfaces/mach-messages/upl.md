# Mach messages: upl

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/upl.defs](../../../platydoc-data/xnu/osfmk/mach/upl.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 2050: upl_abort

Abort the full UPL and delegate page-state cleanup to the range operation.

**Mechanism:** The whole-UPL wrapper rejects a null handle and calls `upl_abort_range` over `0..u_size`, discarding the local empty-result variable. It does not itself deallocate the UPL or perform storage I/O. The range routine resolves page ownership/error state and wakes page waiters; an I/O-wired UPL without DUMP_PAGES takes a commit/free-absent path instead of ordinary abort. These local kernel bodies exist even though the UPL `.defs` subsystem is not registered in the ordinary kobject table. [Wrapper](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L582-L593), [wired special case](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L193-L201).

**Declarations:** [`upl_abort`](../../../platydoc-data/xnu/osfmk/mach/upl.defs#L77) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine upl_abort(
  upl_object : upl_t;
 in abort_cond : integer_t);
```

**Local body:** [`upl_abort`](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L582).
Calls visible in this body include `upl_abort_range`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L582-L593):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L582-L593 -->
```c
upl_abort(
	upl_t   upl,
	int     error)
{
	boolean_t       empty;

	if (upl == UPL_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return upl_abort_range(upl, 0, upl->u_size, error, &empty);
}
```

### 2051: upl_abort_range

Abort a UPL subrange, applying abort/error options to its VM pages and completion state.

**Mechanism:** The range routine locks the UPL/vector and backing/shadow object, checks range extent, and translates abort conditions into page restart, unavailable or error state. Unneeded speculative absent pages can be freed; cleanup clears busy/overwriting state, unwires when required and wakes waiters through delayed work. Empty detection uses the lite bitmap or page queue; an empty ordinary UPL is reported only when notification was requested, while vector sub-UPLs can be removed/deallocated internally. The top-level UPL lifetime is not automatically ended by every successful abort. [Entry/checks](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L165-L300), [page errors](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L340-L410), [empty cleanup](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L500-L579).

**Declarations:** [`upl_abort_range`](../../../platydoc-data/xnu/osfmk/mach/upl.defs#L81) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine upl_abort_range(
  upl_object : upl_t;
  offset : upl_offset_t;
  size : upl_size_t;
 in abort_cond : integer_t;
 out empty : boolean_t);
```

**Local body:** [`upl_abort_range`](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L165).
Calls visible in this body include `upl_commit_range`, `DELAYED_WORK_LIMIT`, `vm_page_delayed_work_get_ctx`, `vector_upl_is_valid`, `upl_lock`, `upl_unlock`, `vector_upl_subupl_byoffset`, `btref_get`, `__builtin_frame_address`, `upl_adjusted_size`, `DEBUG4K_ERROR`, `p`.

### 2052: upl_commit

Commit the full UPL through the range completion implementation.

**Mechanism:** The whole-UPL wrapper rejects a null handle and invokes `upl_commit_range` for the complete `u_size` with control flags zero and the supplied page list/count. It ignores the local empty result and does not itself free the top-level UPL. Zero control flags still permit effects inherited from the UPL's own SET_DIRTY/CLEAR_DIRTY and wiring state. Commit records completion of VM page ownership/state work; it is not a filesystem COMMIT or a promise that a storage device has persisted the bytes. [Wrapper](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L1400-L1413), [inherited controls](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L712-L718).

**Declarations:** [`upl_commit`](../../../platydoc-data/xnu/osfmk/mach/upl.defs#L88) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine upl_commit(
  upl_object : upl_t;
 in page_list : upl_page_info_array_t);
```

**Local body:** [`upl_commit`](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L1400).
Calls visible in this body include `upl_commit_range`.

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L1400-L1413):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L1400-L1413 -->
```c
upl_commit(
	upl_t                   upl,
	upl_page_info_t         *page_list,
	mach_msg_type_number_t  count)
{
	boolean_t       empty;

	if (upl == UPL_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return upl_commit_range(upl, 0, upl->u_size, 0,
	           page_list, count, &empty);
}
```

### 2053: upl_commit_range

Commit a UPL subrange, update page state and release the applicable busy/wire/activity ownership.

**Mechanism:** Commit validates the range, locks the UPL/vector and backing object, merges UPL dirty controls, and resolves busy/cleaning/wiring/page-queue state with batched delayed work. A zero page-list count suppresses the page list. Code-signed backing explicitly strips COMMIT_CS_VALIDATED, forcing normal VM validation instead of trusting supplied signing bits. Empty non-kernel direct-object UPLs end object activity; vector sub-UPLs may be removed and deallocated internally. The `empty` output is conditional notification state, not unconditional destruction of the caller's UPL handle. [Entry](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L596-L718), [signing policy](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L760-L779), [completion](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L1316-L1396).

**Declarations:** [`upl_commit_range`](../../../platydoc-data/xnu/osfmk/mach/upl.defs#L92) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine upl_commit_range(
  upl_object : upl_t;
  offset : upl_offset_t;
  size : upl_size_t;
 in cntrl_flags : integer_t;
 in page_list : upl_page_info_array_t;
 out empty : boolean_t);
```

**Local body:** [`upl_commit_range`](../../../platydoc-data/xnu/osfmk/vm/vm_upl.c#L596).
Calls visible in this body include `DELAYED_WORK_LIMIT`, `vm_page_delayed_work_get_ctx`, `vector_upl_is_valid`, `upl_lock`, `upl_unlock`, `vector_upl_subupl_byoffset`, `btref_get`, `__builtin_frame_address`, `upl_adjusted_size`, `DEBUG4K_ERROR`, `p`, `vm_object_lock`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
