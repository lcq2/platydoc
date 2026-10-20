# Reclamation, compression, swap, and process memory policy

[VM index](README.md) · [Pagers](pagers-and-upl.md) · [Kernel allocation](kernel-allocation.md)

## Several forms of memory shortage

Free physical pages, reclaimable file cache, compressor capacity, swap capacity, and kernel-zone capacity are related resources with different failure modes. Pageout tries to supply pages while preserving useful contents. BSD memorystatus can notify or terminate processes and can select processes for freezing. These are cooperating mechanisms rather than one replacement algorithm.

[`vm_page_grab_options`](../../../xnu/osfmk/vm/vm_resident.c#L5261) first checks per-CPU free-page magazines, with separate handling for tagged pages when configured, then enters refill/slower paths. VM-privileged threads receive special access needed to keep reclamation moving. The scanner aims above the emergency reserve: the original [pageout document](../../../xnu/doc/vm/pageout_scan.md) explains the free target, minimum and reserved-page relationship. Exact thresholds are tuned by platform and configuration.

## Replacement queues and decisions

The queue-state enumeration in [`vm_page.h`](../../../xnu/osfmk/vm/vm_page.h#L238) includes active, inactive internal, inactive external, inactive cleaned, speculative, pageout, free, wired and compressor-owned states. There are per-CPU states and optional secluded/tagged-memory behavior too. “Inactive” means a replacement candidate; it does not mean the page is unowned or contains no useful data.

[`vm_pageout_scan`](../../../xnu/osfmk/vm/vm_pageout.c#L3509) asks pmap to release cheaply recoverable pages, balances active/inactive queues, checks targets and worker throttles, selects pages, and inspects object/page state. The main decisions include:

| Observation | Typical action |
|---|---|
| Page is busy, being cleaned, or otherwise temporarily unavailable | Skip or requeue according to state |
| Backing object is dead, page absent/error, or external backing lost | Reclaim after necessary mapping cleanup |
| Purgeable object is empty and no copy object needs the contents | Reclaim even dirty contents |
| Page was referenced recently | Reactivate, subject to limits and policy exceptions |
| Contents can be discarded safely | Remove mappings and object membership; return physical storage |
| Dirty external contents | Queue filesystem writeback |
| Anonymous contents requiring preservation | Queue compression when available |

The implementation reads pmap reference/modified state before deciding that a page is clean. [`pmap_disconnect_options`](../../../xnu/osfmk/vm/vm_pageout.c#L4293) prevents continuing CPU access while contents are reclaimed or handed onward. Local free batches reduce repeated queue operations. The scanner controls outstanding “laundry” work so too many pages are not trapped in I/O that itself needs memory.

This is not a precise least-recently-used stack. Reactivation limits, speculative aging, background/special queues, realtime/shared-cache treatment and worker pressure affect ordering. A queue label alone cannot predict a page's fate. The scanner also yields locks and uses object-lock try/retry cooperation to avoid deadlocking with threads that acquire object and queue locks in other phases.

### The final dirty-state check must disconnect CPU mappings

The earlier `pmap_get_refmod` sample can become stale while the page is still mapped. A CPU may write between that observation and reclamation. The scanner therefore calls `pmap_disconnect_options` and incorporates its returned modified state before deciding that the contents are discardable. This is a physical-page operation: the backend uses reverse mappings to remove aliases across pmaps, rather than finding one process and removing its map entry. [`last-access race and option selection`](../../../xnu/osfmk/vm/vm_pageout.c#L4247-L4292), [ARM mapping lifecycle](pmap-mapping-lifecycle.md), [x86 disconnect](pmap-x86.md#6-reverse-mappings-support-operations-starting-from-a-physical-page).

[Source: vm_pageout.c, lines 4293–4298](../../../xnu/osfmk/vm/vm_pageout.c#L4293-L4298)

<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_pageout.c#L4293-L4298 -->
```c
			refmod_state = pmap_disconnect_options(VM_PAGE_GET_PHYS_PAGE(m),
			    pmap_options,
			    NULL);
			if (refmod_state & VM_MEM_MODIFIED) {
				SET_PAGE_DIRTY(m, FALSE);
			}
```

The scanner passes `PMAP_OPTIONS_COMPRESSOR` when it knows anonymous contents need preserving, and `PMAP_OPTIONS_COMPRESSOR_IFF_MODIFIED` when the pmap's final dirty observation must decide. File pages or an inactive compressor use a different option path. The pmap can preserve compressed accounting in software PTE markers while removing CPU access; the actual compressed contents are stored by the later compressor operation. A clean-looking page can still need preservation because of shadow/copy relationships; the scanner checks those after disconnect. [`post-disconnect decisions`](../../../xnu/osfmk/vm/vm_pageout.c#L4307-L4341).

Do not infer current translation presence from `vmp_pmapped` alone. The scanner's comment treats a false value as evidence that the page has not been mapped, permitting it to skip the expensive disconnect; true causes a conservative query/cleanup. The current PTEs and reverse mappings supply the actual mapping state. [`pmapped contract at reclamation`](../../../xnu/osfmk/vm/vm_pageout.c#L4257-L4264).

### Scanner-to-worker ownership

The scanner separates candidate selection from blocking content preservation. `vm_pageout_cluster_to_queue` requires the object and page-queue locks, verifies a dirty/precious unwired page, and takes an **activity** hold on the object. It marks the page as laundry, increments queue accounting, and puts it on the pending queue. For internal objects it also sets the page busy before waking compression work:

[Source: vm_pageout.c, lines 753–770](../../../xnu/osfmk/vm/vm_pageout.c#L753-L770)

<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_pageout.c#L753-L770 -->
```c
	/*
	 * protect the object from collapse or termination
	 */
	vm_object_activity_begin(object);


	/*
	 * pgo_laundry count is tied to the laundry bit
	 */
	m->vmp_laundry = TRUE;
	q->pgo_laundry++;

	m->vmp_q_state = VM_PAGE_ON_PAGEOUT_Q;
	vm_page_queue_enter(&q->pgo_pending, m, vmp_pageq);

	if (object->internal == TRUE) {
		assert(VM_CONFIG_COMPRESSOR_IS_PRESENT);
		m->vmp_busy = TRUE;
```

The internal worker takes a batch from the queue, clears queue/laundry membership, adjusts throttling, and drops the queue lock before compression. The busy page plus activity hold preserve the necessary lifetime while the worker no longer holds the scanner's locks. `vm_pageout_compress_page` asserts both obligations. On successful compression it removes the page from the object and ends activity; the caller batches those now-disposable physical pages into `vm_page_free_list`. On failure the function clears busy, reactivates the original page, ends activity, and returns failure rather than discarding the only contents. [`worker batch`](../../../xnu/osfmk/vm/vm_pageout.c#L4773-L4844), [`compressor preconditions`](../../../xnu/osfmk/vm/vm_pageout.c#L4962-L4986), [`success/failure cleanup`](../../../xnu/osfmk/vm/vm_pageout.c#L5068-L5118).

The separate external worker reaches vnode/pager writeback and UPL completion. Its pages can have cleaning/free-when-done state while I/O is underway; the scanner deliberately leaves such pages to their owner. `upl_commit_range` can subsequently put a cleaned page on the cleaned queue. Reclaiming the page again just because it is absent from the ordinary active queue would violate that I/O ownership. [`scanner cleaning cases`](../../../xnu/osfmk/vm/vm_pageout.c#L3883-L3910), [UPL ownership](pagers-and-upl.md).

## Anonymous contents become compressor slots

The internal worker reaches [`vm_pageout_compress_page`](../../../xnu/osfmk/vm/vm_pageout.c#L4973). It verifies a busy page and ongoing object activity, creates an object's compressor pager if necessary, then calls `vm_compressor_pager_put` with object offset plus `paging_offset`. On success it removes the resident page from the object and updates compressed ownership/accounting. Compression can release the source page while consuming fewer bytes in other physical pages; it does not make the contents cost zero memory.

[`struct compressor_pager`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L143) associates object page offsets with slots using embedded, direct or indirect slot arrays. [`vm_compressor_pager_put`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L751) obtains a slot and calls `vm_compressor_put`; replacing an existing slot releases its older contents. [`vm_compressor_pager_get`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L820) translates the slot back into a physical destination page and returns compressed-count changes to the object layer.

The ordinary slot encodes a segment number and index. [`struct c_segment`](../../../xnu/osfmk/vm/vm_compressor_xnu.h#L211) has its own lock, queue links, byte/slot occupancy, a busy state and storage that can be a resident buffer or a swap handle. [`c_slot_mapping`](../../../xnu/osfmk/vm/vm_compressor_xnu.h#L296) also reserves a special representation for single-value pages. The corresponding [`vm_compressor_get`](../../../xnu/osfmk/vm/vm_compressor.c#L6100) can reconstruct those pages from a value table without conventional decompression.

```mermaid
flowchart LR
    O[Object offset] --> S[Compressor pager slot]
    S --> C[Segment and slot index]
    C --> R[Resident compressed buffer]
    C --> D[Swap handle]
    D --> I[Read segment]
    I --> R
    R --> P[Decompress into a physical page]
    P --> F[Fault installs CPU mapping]
```

Compaction packs segment contents and recovers holes; swap can move eligible segments to storage. Faults can therefore be satisfied from RAM compression or require segment swap-in first. `C_DONT_BLOCK` lets a fast path fail back to a blocking path; `C_KEEP` can retain the original compressed contents, useful for copying. Configuration `CONFIG_TRACK_UNMODIFIED_ANON_PAGES` additionally supports uncompressed swap-backed slots; the diagram represents the ordinary compressed case.

### Follow one compressed offset and its ownership

`vm_pageout_compress_page` passes `m->vmp_offset + object->paging_offset` and the physical page number to the compressor pager. That sum is a pager coordinate, distinct from the faulting process's virtual address:

[Source: vm_pageout.c, lines 5048–5055](../../../xnu/osfmk/vm/vm_pageout.c#L5048-L5055)

<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_pageout.c#L5048-L5055 -->
```c
	retval = vm_compressor_pager_put(
		pager,
		m->vmp_offset + object->paging_offset,
		VM_PAGE_GET_PHYS_PAGE(m),
		current_chead,
		scratch_buf,
		&compressed_count_delta,
		flags);
```

The pager maps the offset to `compressor_slot_t`, a 32-bit representation interpreted as `c_slot_mapping`. In the ordinary configuration it contains a segment number plus slot index; the unmodified-anonymous configuration reserves another bit for uncompressed swap state. The single-value sentinel instead identifies an entry in the repeated-value table. These encodings are defined in [`c_slot_mapping`](../../../xnu/osfmk/vm/vm_compressor_xnu.h#L296-L320); they are unrelated to a pmap's invalid compressed PTE bits.

| Structure or field | What it owns/describes |
| --- | --- |
| `compressor_pager.cpgr_slots` | Per-object-offset embedded/direct/indirect slot lookup |
| `cpgr_num_slots_occupied` | Occupied backing slots; adjusted by operation deltas |
| `c_slot_mapping` | Locator or special encoding for one page's contents |
| `c_segment.c_slot_*` | Slot metadata locating contents within a compressed segment |
| `c_segment.c_store` | Resident buffer or swap handle, interpreted according to segment state |
| `c_lock`, `c_busy`, `c_wanted`, `c_busy_swapping` | Segment synchronization, exclusive work, waiting, and I/O state |
| `c_bytes_used`, `c_bytes_unused`, `c_slots_used` | Occupancy/fragmentation, separate from original uncompressed page count |

Definitions: [`compressor_pager`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L143-L162), [`c_segment`](../../../xnu/osfmk/vm/vm_compressor_xnu.h#L211-L289). Several segment fields have special busy-versus-lock rules; the structure's comment explicitly keeps `c_swappedin` out of a lock-protected bitfield because it may be modified under busy-state protection instead.

`vm_compressor_pager_put` obtains or creates the offset's slot. If the slot already contains compressed backing, it releases that backing and reports a negative count adjustment before inserting the new contents. A successful insertion adds one. The caller applies the resulting delta to the object/pager accounting rather than assuming every put adds a new occupied slot. [`put`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L751-L816).

On get, `vm_compressor_get` maps the **destination physical page** through `pmap_map_compressor_page`, fills it by repeated-value reconstruction or decompression, then unmaps that temporary compressor access. This is separate from the later user pmap insertion. `C_KEEP` retains the source compressed slot for COW; otherwise successful consumption can clear it and decrement the pager's occupied count. [`get and temporary mapping`](../../../xnu/osfmk/vm/vm_compressor.c#L6100-L6177), [`count delta`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L880-L891).

Segment synchronization can require a wait even if the logical contents are already compressed in memory. The nonblocking case preserves the slot and asks the caller to retry when the segment is busy or needs swap-in:

[Source: vm_compressor.c, lines 5650–5657](../../../xnu/osfmk/vm/vm_compressor.c#L5650-L5657)

<!-- source-excerpt: ../../../xnu/osfmk/vm/vm_compressor.c#L5650-L5657 -->
```c
	if (flags & C_DONT_BLOCK) {
		if (c_seg->c_busy || (C_SEG_IS_ONDISK(c_seg) && dst)) {
			*zeroslot = 0;

			retval = DECOMPRESS_NEED_BLOCK;
			goto done;
		}
	}
```

The pager converts that `DECOMPRESS_NEED_BLOCK` result into a retryable failure for a `C_DONT_BLOCK` request; genuine decompression/swap errors take different result paths. A fast-fault miss is therefore not proof of corrupted or absent backing. [`pager get result handling`](../../../xnu/osfmk/vm/vm_compressor_pager.c#L858-L877), [fault fast/slow transitions](fault-resolution.md).

## Swap stores compressor backing through VFS

[`vm_swap_put`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1767) locates a free slot in a ready swapfile, updates bitmap and I/O counts under `vm_swap_data_lock`, then issues I/O outside that lock. [`vm_swap_get`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1702) resolves a handle, acquires a vnode reference, reads into segment backing via `vm_swapfile_io`, and releases the swap slot. The following section traces completion ownership; swapfile creation, garbage collection and trimming have additional state machines beyond this trace.

[`VM_CONFIG_COMPRESSOR_IS_ACTIVE`, `VM_CONFIG_SWAP_IS_ACTIVE`, and `VM_CONFIG_FREEZER_SWAP_IS_ACTIVE`](../../../xnu/osfmk/vm/vm_pageout.h#L227) are distinct checks. Avoid assuming that every target swaps anonymous memory, that all freezer operation writes to disk, or that compressor exhaustion is identical to exhausted free disk space.

### Reservation, I/O, and completion are different swap states

`vm_swap_put` reserves a segment-sized slot under `vm_swap_data_lock`: it sets the bitmap bit, increments segment/I/O counts, associates the compressed segment, and records the swapfile identity and byte offset. After releasing that lock, `issue_io` forms the returned handle, acquires the vnode and issues `vm_swapfile_io`. The segment must be busy and busy-swapping at this boundary. Merely obtaining a swap handle does not establish that the write completed. [`reservation`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1788-L1827), [`I/O submission`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1875-L1907).

With an asynchronous completion structure, the routine records segment, size, swapfile, and completion state for the later callback. Without it, or on immediate error, it calls `vm_swap_put_finish` directly. That function releases the vnode I/O reference when applicable, decrements outstanding I/O accounting, wakes teardown waiters, and frees the reserved slot on error. [`completion`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1911-L1934).

`vm_swap_get` similarly increments I/O protection while the swapfile is locked, drops the lock for the read into an already allocated segment buffer, releases the disk slot, and completes accounting. The fault still needs to extract/decompress its page from the segment and revalidate/install the user mapping. This explains the distinct levels: swap handle → segment contents → physical destination page → pmap translation. [`swap-in`](../../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1702-L1763).

## BSD memorystatus: process-level decisions

Continue with [memorystatus and the freezer](memorystatus-and-freezer.md) for health/action selection, candidate references and retries, task/map/object freeze execution, completion units, budgets, and resume/demotion state.

[`memorystatus_update_available_page_count`](../../../xnu/bsd/kern/kern_memorystatus.c#L6045) publishes available-page information, asks the pressure-notification path to reevaluate, considers a freezer wakeup when configured, and considers waking jetsam. Its comment explains why this path cannot take `freezer_mutex`: callers may hold page-queue locks with preemption disabled. Wakeups defer policy work to suitable threads.

[`memorystatus_thread_internal`](../../../xnu/bsd/kern/kern_memorystatus.c#L4963) repeatedly calls `memorystatus_pick_action` and `memorystatus_do_action`. Inputs include pressure, high-water violations, eligible swappable processes and subsystem shortage signals. After a successful kill it revisits candidates and acknowledges relevant compressor, zone or pageout shortages. It also collects and posts diagnostic snapshots. Priority bands and per-process state belong to BSD's process policy; VM provides the page and footprint accounting underlying those decisions.

Memory pressure notifications are another route: they allow clients to release caches before or alongside stronger actions. They should not be equated with a guaranteed grace period before termination. Consult the original [memorystatus](../../../xnu/doc/vm/memorystatus.md), [notifications](../../../xnu/doc/vm/memorystatus_notify.md), and [kill-policy](../../../xnu/doc/vm/memorystatus_kills.md) documents for the broader policy surface.

## Freezing preserves selected process contents

[`memorystatus_freeze_process`](../../../xnu/bsd/kern/kern_memorystatus_freeze.c#L1816) checks eligibility, slots and budget, marks a process temporarily locked against competing policy, retains it and releases the process-list lock before calling `task_freeze`. This is a clear example of BSD selecting a process while Mach VM performs the memory work.

[`task_freeze`](../../../xnu/osfmk/kern/task.c#L5042) serializes freeze-state changes, optionally drains deferred reclamation, and invokes [`vm_map_freeze`](../../../xnu/osfmk/vm/vm_map.c#L20322). The map routine takes an exclusive range lock over the whole map to block concurrent faults, scans eligible anonymous objects, and tracks purgeable, wired, clean, dirty and shared pages. With freezer swap enabled it performs an evaluation phase and observes budgets; in-memory-only compression has different behavior. Wired pages are not magically made pageable by freezing.

On success the task's frozen state and accounting are updated, and compactor/swapper work is awakened as appropriate. This preserves memory for later use; process termination instead tears down resources. The original [freezer document](../../../xnu/doc/vm/freezer.md) covers selection and product policy beyond this call path.
