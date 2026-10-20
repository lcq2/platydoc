# ARM64 TLB, cache, and root-switch completion

For concrete 4 KiB/16 KiB address walks, descriptor locations, and decoded PTE values, start with [pmap translation walkthroughs](pmap-translation-walkthroughs.md).

Changing a PTE, preventing stale translations, finishing earlier memory accesses, and making newly written instructions visible are separate operations. The pmap paths coordinate them, but a call named “flush” can refer to only one part. This page follows the actual helpers in this checkout and distinguishes XNU's visible instructions from operations delegated to SPTM. Read [ARM64 structures](pmap-arm64.md) and [mapping lifecycle](pmap-mapping-lifecycle.md) first; [exception return](../platform/arm64-exception-return.md) covers the EL1-to-EL0 transition after the address space is prepared.

## Publication, invalidation, and completion are different boundaries

For a representative legacy change to an already valid PTE, `pmap_enter_pte()` performs the PTE store, `FLUSH_PTE_STRONG()`, then `PMAP_UPDATE_TLBS()`. The latter issues the selected asynchronous invalidation and calls `arm64_sync_tlb()`. A new mapping replacing an invalid PTE instead uses `FLUSH_PTE()` and an ISB. This source explicitly distinguishes entries that could already be cached from entries for which an invalidation is unnecessary. [Legacy enter commit](../../../xnu/osfmk/arm/pmap/pmap.c#L5928).

| Step/helper | Concrete operation | Purpose in the visible implementation |
| --- | --- | --- |
| `write_pte_fast()` or successful PTE compare-exchange | PTE memory update, without the complete translation-maintenance sequence | Change the table representation. |
| `FLUSH_PTE()` | `dmb ish` | Store/load ordering for updates such as invalid-entry insertion or AF restoration that do not require TLBI on that path. |
| `FLUSH_PTE_STRONG()` | `dsb ishst` | Complete prior PTE stores before an ensuing invalidation. |
| `flush_*_async()` | Selected `tlbi` instruction(s) | Issue invalidation at the requested VA/ASID/scope. |
| `sync_tlb_flush()` | `dsb ish` or `dsb ishnxs`, then `isb` | Complete the appropriate broadcast maintenance and synchronize subsequent execution. |
| `sync_tlb_flush_local()` | `dsb nsh` or `dsb nshnxs`, then `isb` | Complete the corresponding local-core maintenance. |

Definitions: [PTE update macros](../../../xnu/osfmk/arm/pmap/pmap.c#L629), [write helpers](../../../xnu/osfmk/arm/pmap/pmap.c#L675), [TLB barriers](../../../xnu/osfmk/arm64/tlb.h#L51). The C atomic ordering on a PTE does not replace the ARM translation-maintenance sequence. Nor does a completed TLB invalidation by itself release a software reader's pointer into a page table: SPTM epochs and table pins address that separate lifetime problem.

[tlb.h, lines 51–61](../../../xnu/osfmk/arm64/tlb.h#L51-L61)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/tlb.h#L51-L61 -->
```c
static inline void
sync_tlb_flush(void)
{
#if HAS_FEAT_XS
	asm volatile ("dsb ishnxs":::"memory");
#else
	__builtin_arm_dsb(DSB_ISH);
#endif /* HAS_FEAT_XS */
	__builtin_arm_isb(ISB_SY);
}

```

`HAS_FEAT_XS` changes the instruction/barrier variants. A subtle source detail matters: the `strong` argument to `arm64_sync_tlb()` is marked unused here and the body always calls `sync_tlb_flush()`. Some issuing helpers select ordinary versus `nxs` TLBIs based on `strong`, and the full-flush wrapper explicitly uses `sync_tlb_flush_strong()` when XS exists. It would be inaccurate to describe the generic `arm64_sync_tlb(true)` wrapper as itself selecting a stronger DSB in this release. [Wrapper and full flush](../../../xnu/osfmk/arm64/tlb.h#L76).

[tlb.h, lines 85–89](../../../xnu/osfmk/arm64/tlb.h#L85-L89)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/tlb.h#L85-L89 -->
```c
static inline void
arm64_sync_tlb(bool strong __unused)
{
	sync_tlb_flush();
}
```

“Asynchronous” here means that the caller may issue several invalidations before the completion barrier. It does not inherently mean an IPI, background thread, or deferred scheduling operation. The `...is` instructions shown below provide the inner-shareable broadcast form directly. [Asynchronous helper bodies](../../../xnu/osfmk/arm64/tlb.h#L96).

## Choosing the translation entries to invalidate

There are several independent dimensions: one VA/range versus all VAs; one address-space identity versus all identities; leaf-only versus all table levels; and local core versus broadcast. The helper selection reflects those dimensions rather than one universal flush primitive. [TLB helper family](../../../xnu/osfmk/arm64/tlb.h#L128).

| Intent | Representative non-XS instruction | Detail that affects correctness |
| --- | --- | --- |
| VA, ASID, leaf only, broadcast | `tlbi vale1is` | Targets leaf translations; helper also handles kernel-protection ASID pairing. |
| VA, ASID, all levels, broadcast | `tlbi vae1is` | Used when invalidation must cover intermediate translation state too. |
| VA, all ASIDs, leaf only / all levels | `tlbi vaale1is` / `tlbi vaae1is` | Needed for translations shared across address-space identities. |
| Entire ASID, broadcast | `tlbi aside1is` | Explicitly does not flush global entries. |
| All EL1 translations, broadcast | `tlbi vmalle1is` | Used for the broadest invalidation request. |
| Entire ASID or all translations, local | Local helper's non-`is` forms | Used by activation paths where the collision is local to that CPU. |

The VA-specific ASID helper's source comment notes that matching global VA entries are also affected, whereas an ASID-only flush excludes globals. This distinction matters for nested shared regions. [VA/ASID helper](../../../xnu/osfmk/arm64/tlb.h#L188), [ASID-only helper](../../../xnu/osfmk/arm64/tlb.h#L286), [local helpers](../../../xnu/osfmk/arm64/tlb.h#L323).

TLBI's ordinary VA operands use 4 KiB units even when the selected mapping granule is 16 KiB. `tlbi_addr()` shifts by 12, the hardware ASID is placed in the high 16 bits, and loops advance by `pmap_page_size / 4096`. The 16 KiB branch rounds start/end to suitable boundaries. The source itself contains a caution about the expected exclusive-end contract; callers should pass correctly aligned ranges rather than rely on that rounding to repair arbitrary input. [Operand encoding](../../../xnu/osfmk/arm64/tlb.h#L35), [range iteration](../../../xnu/osfmk/arm64/tlb.h#L128), [architecture masks](../../../xnu/osfmk/arm64/proc_reg.h#L2444).

`flush_mmu_tlb_region_asid_async()` chooses among individual-entry loops, range-TLBI instructions when `__ARM_RANGE_TLBI__` is enabled, and full-ASID/full-system flushing above a threshold. It computes page count using the pmap's geometry. A nested pmap uses all-ASID invalidation; a sufficiently large kernel/nested request becomes a full flush. The `last_level_only` argument is passed into the range/entry helpers. [SPTM backend's explicit-flush selector](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10265), [legacy selector](../../../xnu/osfmk/arm/pmap/pmap.c#L10526).

[pmap.c, lines 10276–10288](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10276-L10288)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10276-L10288 -->
```c
	if (npages > ARM64_FULL_TLB_FLUSH_THRESHOLD) {
		boolean_t       flush_all = FALSE;

		if ((asid == 0) || (pmap->type == PMAP_TYPE_NESTED)) {
			flush_all = TRUE;
		}
		if (flush_all) {
			flush_mmu_tlb_async();
		} else {
			flush_mmu_tlb_asid_async((uint64_t)asid << TLBI_ASID_SHIFT, false);
		}
		return;
	}
```

With `__ARM_KERNEL_PROTECT__`, one pmap has distinct EL0 and EL1 ASIDs. An ASID-specific invalidation must cover both. Kernel mappings may be accessed while another pmap's identity is active, so targeting kernel ASID zero expands to all ASIDs rather than flushing only tag zero. These rules are implemented inside the low-level helpers, not left to every pmap caller. [Kernel-protection contract](../../../xnu/osfmk/arm64/tlb.h#L38), [paired ASID implementation](../../../xnu/osfmk/arm64/tlb.h#L290).

## Break-before-make and table lifetime

Replacing the physical output address of a valid mapping is not treated as an arbitrary overwrite. SPTM reports a physical-address conflict; XNU removes the old translation and retries the enter. The comment explicitly identifies that removal as the required break-before-make sequence. Legacy enter similarly identifies a different PA, gains exclusive pmap ownership, and removes the previous mapping before committing the new one. [SPTM conflict handling](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L6799), [legacy replacement path](../../../xnu/osfmk/arm/pmap/pmap.c#L6300).

Table removal adds another constraint. Once an intermediate TTE is cleared, stale hardware translation state must not continue referring to freed table storage. Meanwhile, software walkers or PV consumers may still have pointers to that storage. Legacy table deletion performs its translation maintenance within its locking/free sequence. SPTM calls the monitor to unlink the table and then drains XNU epochs; if temporary pins remain, the page is queued for delayed freeing. The monitor operation's hardware contract and XNU's reader-lifetime protocol are complementary. [Legacy TTE deallocation](../../../xnu/osfmk/arm/pmap/pmap.c#L4049), [SPTM table unlink/drain](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L3610), [full removal sequence](pmap-mapping-lifecycle.md#why-removing-the-last-pte-does-not-immediately-free-its-table).

An epoch drain is not itself a TLB flush. It observes software generations on CPUs. Conversely, issuing TLBI does not establish that every thread has stopped reading a PTD. Keeping these two observations separate makes the double-drain SPTM table-removal sequence easier to follow.

## Activating a pmap and reusing an ASID

Legacy `pmap_switch_internal()` tracks each CPU's last software identity associated with a hardware ASID. A mismatch requests the appropriate local invalidation before that ASID is reused. It also tracks nested shared-region state because globals can survive an ASID-only flush. Switching shared regions can therefore require local global invalidation, while geometry/commpage changes require additional handling. [Legacy switch](../../../xnu/osfmk/arm/pmap/pmap.c#L4613).

Changing translation geometry is more than installing a new root address. The legacy mixed-page-size path handles TCR changes and overlapping commpage granularities by temporarily clearing the user root as necessary, performing the required invalidation/synchronization, then installing the destination's root and geometry. `pmap_switch_user_ttb()` records per-CPU nested-region/page-shift state and constructs the root physical address plus ASID. A kernel-only switch installs the designated invalid user root. [Geometry/collision decisions](../../../xnu/osfmk/arm/pmap/pmap.c#L4670), [root installation](../../../xnu/osfmk/arm/pmap/pmap.c#L7920).

The visible ordinary TTBR0 helper completes prior work, writes TTBR0, and synchronizes execution. Under kernel protection it selects the EL1 member of the ASID pair:

[machine_routines_asm.s, lines 304–313](../../../xnu/osfmk/arm64/machine_routines_asm.s#L304-L313)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/machine_routines_asm.s#L304-L313 -->
```asm
LEXT(set_mmu_ttb)
	ARM64_PROLOG
#if __ARM_KERNEL_PROTECT__
	/* All EL1-mode ASIDs are odd. */
	orr		x0, x0, #(1 << TTBR_ASID_SHIFT)
#endif /* __ARM_KERNEL_PROTECT__ */
	dsb		ish
	msr		TTBR0_EL1, x0
	isb		sy
	ret
```

SPTM activation is a different interface: `pmap_switch_internal()` validates the ASID, updates replacement bookkeeping, and calls `sptm_switch_root(pmap->ttep, ...)`. An MTE security-override branch adds the appropriate root flag. Development/debug code observes return bits indicating an ASID-TLBI flush or speculation-context restriction. The root-switch instruction sequence and reuse enforcement inside the monitor cannot be reconstructed from those flags alone. [SPTM switch](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L4354).

[pmap.c, lines 4373–4394](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L4373-L4394)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L4373-L4394 -->
```c
	__unused sptm_return_t sptm_return;
#if HAS_MTE
	if (ml_thread_get_sec_override(thread)) {
		assert(pmap != kernel_pmap);
		sptm_return = sptm_switch_root(pmap->ttep, SPTM_ROOT_PT_FLAG_NO_TAG_FAULT, SPTM_ROOT_PT_FLAG_NO_TAG_FAULT);
#else
#pragma unused(thread)
	if (0) {
#endif
	} else {
		sptm_return = sptm_switch_root(pmap->ttep, 0, 0);
	}

#if DEVELOPMENT || DEBUG
	if (__improbable(sptm_return & SPTM_SWITCH_ASID_TLBI_FLUSH)) {
		os_atomic_inc(&pmap_asid_flushes, relaxed);
	}

	if (__improbable(sptm_return & SPTM_SWITCH_RCTX_FLUSH)) {
		os_atomic_inc(&pmap_speculation_restrictions, relaxed);
	}
#endif /* DEVELOPMENT || DEBUG */
```

Even switching between threads with the same pmap has a synchronization requirement. `machine_switch_pmap_and_extended_context()` issues `dsb ish` on that path because a thread can be preempted between issuing cache/TLB maintenance and its synchronizing DSB. Completion must occur on the processing element that issued the maintenance; moving the thread and eventually issuing a barrier elsewhere would not supply that guarantee. The function separately arranges context synchronization for the incoming execution. [Context-switch boundary](../../../xnu/osfmk/arm64/pcb.c#L437).

[pcb.c, lines 466–478](../../../xnu/osfmk/arm64/pcb.c#L466-L478)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/pcb.c#L466-L478 -->
```c
		/*
		 * If the thread is preempted while performing cache or TLB maintenance,
		 * it may be migrated to a different CPU between the completion of the relevant
		 * maintenance instruction and the synchronizing DSB.   ARM requires that the
		 * synchronizing DSB must be issued *on the PE that issued the maintenance instruction*
		 * in order to guarantee completion of the instruction and visibility of its effects.
		 * Issue DSB here to enforce that guarantee.  We only do this for the case in which
		 * the pmap isn't changing, as we expect pmap_switch() to issue DSB when it updates
		 * TTBR0.  Note also that cache maintenance may be performed in userspace, so we
		 * cannot further limit this operation e.g. by setting a per-thread flag to indicate
		 * a pending kernel TLB or cache maintenance instruction.
		 */
		__builtin_arm_dsb(DSB_ISH);
```

These runtime root switches should be distinguished from the user-return trampoline's kernel-mapping/ASID transitions. Both concern active translation state, but they occur at different points and under different configuration branches. See [ARM64 exception return](../platform/arm64-exception-return.md).

## SPTM normally owns PTE maintenance, but XNU still has explicit flush paths

Ordinary SPTM enter/remove/protect paths request changes through `sptm_map_page()`, `sptm_unmap_region()`, `sptm_update_region()`, and disjoint-update interfaces. XNU consumes their results and uses the operation contracts; it does not store protected PTEs directly in those paths. This is why the visible SPTM code cannot be explained by inserting the legacy store/DSB/TLBI sequence after every call. [Map helper](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L6356), [range removal](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L3810), [range protection](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L5584).

Some physical-page and batch operations explicitly request deferred invalidation. Their options distinguish three situations: the caller requested no flush, a supplied flush-range will cover matching aliases later, or the monitor should flush this update now. An alias outside the pending `(pmap, VA range)` cannot be left to that range flush; the code clears defer-TLBI for that alias so its update receives its own maintenance. Disconnecting mappings forcibly removes the no-flush option where necessary. [Physical-protect options](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L4930), [per-alias flush decision](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L5180).

The range reference/modify-clear path accumulates contiguous and disjoint operations while bounding preemption-disabled work. At the end it submits pending monitor operations; if the range needs a flush, it orders PTE writes, issues a leaf-only range invalidation, and completes it. The exact end-of-batch sequence is visible:

[pmap.c, lines 7902–7914](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7902-L7914)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7902-L7914 -->
```c
	pmap_multipage_op_submit(&flush_range);
	assert((flush_range.pending_disjoint_entries == 0) && (flush_range.pending_region_entries == 0));
	if (flush_range.ptfr_flush_needed) {
		/* Sync the PTE writes before potential TLB/Cache flushes. */
		FLUSH_PTE_STRONG();
		pmap_get_pt_ops(pmap)->flush_tlb_region_async(
			flush_range.ptfr_start,
			flush_range.ptfr_end - flush_range.ptfr_start,
			flush_range.ptfr_pmap,
			true);
		sync_tlb_flush();
	}
	return va;
```

The older generic `pmap_flush()` interface is a stub on this ARM implementation. Where a legacy flush argument reaches physical protect, the wrapper clears `PMAP_OPTIONS_NOFLUSH` rather than pretending that this stub will finish the deferred work. Readers should follow the specific batch/flush-range object being used instead of assuming every option named “no flush” has the same caller contract. [Physical-protect wrapper](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L5480), [pmap_flush stub](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L11636).

## Physical addresses, aperture aliases, and translation queries

`pmap_paddr_t` identifies physical storage; a C pointer used by XNU must normally be a mapped kernel virtual address. Table walkers therefore convert a table descriptor's physical output address through `phystokv()` before dereferencing it. The aperture is also used for cache operations and physical copying. It is not a per-process mapping returned to user space. [SPTM table walk](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7214).

The legacy `phystokv()` first searches `ptov_table` ranges, then falls back to `pa - gPhysBase + gVirtBase` after validating the physical range. Consequently, one universal constant offset is not sufficient to describe every legacy aperture segment. The SPTM version calls `sptm_phystokv()` and returns zero on failure. Its `phystokv_range()` conservatively limits the returned contiguous span to the remainder of a VM page. [Legacy aperture conversion](../../../xnu/osfmk/arm64/arm_vm_init.c#L383), [SPTM conversion](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1384).

[arm_init_sptm.c, lines 1383–1391](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1383-L1391)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1383-L1391 -->
```c
vm_map_address_t
phystokv(pmap_paddr_t pa)
{
	sptm_papt_t va;
	if (sptm_phystokv(pa, &va) != LIBSPTM_SUCCESS) {
		return 0;
	}
	return (vm_map_address_t)va;
}
```

`pmap_find_pa_nofault()` can use hardware translation for the kernel or currently active user pmap. A successful translation query is not proof that an ordinary load is permitted in the current context: the source calls out PAN as a case where translation can succeed while a privileged access is disallowed. The fallback `pmap_vtophys()` walks another pmap's tables in software. None of these helpers supplies a VM object/page lifetime reference. [Translation query](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7110), [software walk](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7214).

## Cache type changes and instruction visibility

PTE cacheability/shareability bits are constructed by `wimg_to_pte()` from VM WIMG attributes and the physical address. The same nominal `VM_WIMG_IO` request can select a different memory attribute for DRAM than for device space, and IO mappings are marked execute-never. `pmap_cache_attributes()` obtains managed-page overrides from physical attributes and consults IO ranges for unmanaged addresses. [Attribute conversion](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L6500), [attribute lookup](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10320).

Changing memory type must account for aliases, including the physical aperture that is absent from ordinary PV lists. SPTM's cache-update batch therefore starts a physical-page group with a PAPT header containing its aperture PTE template, then gathers CPU aliases from PV metadata. The templates change shareability and memory-attribute fields and request deferred TLBI. An epoch protects accumulated operations across physical pages even when their individual PVH locks have already been released. [PAPT header/alias collection](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10595), [batch epoch and lock handling](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L10870).

If the monitor returns `SPTM_UPDATE_DELAYED_TLBI`, the batch records a second pass. After ordering PTE writes, it invalidates aliases for the affected physical pages and synchronizes. A further pass performs forced data-cache cleaning when the requested RT memory type transition requires it, with DSB completion and bounded intervals before honoring pending preemption. `pmap_set_cache_attributes_internal()` wraps a single page into the same batch machinery. This is much more than changing `pp_attr_table`. [Flush/clean passes](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L11023), [single-page wrapper](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L11150).

Instruction visibility is another path. In the legacy backend `pmap_sync_page_data_phys()` calls `cache_sync_page()`, which converts the PA to its aperture VA and calls `InvalidatePoU_IcacheRegion()`. That assembly first calls `CleanPoU_DcacheRegion()`, then performs the applicable instruction-cache invalidation and barriers. On Apple ARM64 the clean-to-PoU routine has a “Fully Coherent” branch that omits the explicit `dc cvau` loop; non-Apple targets execute that loop. Both finish the helper with a DSB. [Legacy wrapper](../../../xnu/osfmk/arm/pmap/pmap.c#L7223), [cache_sync_page](../../../xnu/osfmk/arm/caches.c#L436), [instruction-cache operation](../../../xnu/osfmk/arm64/caches_asm.s#L61), [conditional data-cache clean](../../../xnu/osfmk/arm64/caches_asm.s#L255).

[caches_asm.s, lines 71–81](../../../xnu/osfmk/arm64/caches_asm.s#L71-L81)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/caches_asm.s#L71-L81 -->
```asm
	lsr		x1, x1, #MMU_I_CLINE					// Set cache line counter
L_ipui_loop:
	ic		ivau, x0							// Invalidate icache line
	add		x0, x0, #1<<MMU_I_CLINE				// Get next cache aligned addr
	subs	x1, x1, #1							// Decrementer cache line counter
	b.pl	L_ipui_loop							// Loop in counter not null
	dsb		sy
	isb		sy
#else
	bl		EXT(InvalidatePoU_Icache)
#endif
```

The SPTM `pmap_sync_page_data_phys()` wrapper is deliberately empty. Its comment states that the monitor automatically invalidates when retyping to executable-capable frame types. That statement supports the interface dependency, not an assertion about the external monitor's exact cache instructions. The separate `pmap_sync_page_attributes_phys()` still calls `flush_dcache()` for a physical page, and `pmap_attribute_cache_sync()` still has an explicit cache-sync route. [SPTM cache wrappers](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7531).

[pmap.c, lines 7546–7560](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7546-L7560)

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L7546-L7560 -->
```c
/*
 * pmap_sync_page_data_phys(ppnum_t pp)
 *
 * Invalidates all of the instruction cache on a physical page and
 * pushes any dirty data from the data cache for the same physical page.
 * Not required on SPTM systems, because the SPTM automatically performs
 * the invalidate operation when retyping to one of the types that allow
 * for executable permissions.
 */
void
pmap_sync_page_data_phys(
	__unused ppnum_t pp)
{
	return;
}
```

## Reading and verification boundaries

For a concrete exercise, follow one legacy `pmap_enter_pte()` replacing a valid same-PA PTE: identify the store, PTE barrier, VA/ASID helper, and final DSB/ISB. Then follow an SPTM reference-bit-clear range and find where monitor-deferred work becomes an explicit XNU range flush. Finally follow a context switch with the same pmap; it shows why maintenance completion belongs to a CPU execution boundary as well as a mapping operation.

| Sources inspected | Depth and limits |
| --- | --- |
| `arm64/tlb.h`, `proc_reg.h`, both range-flush selectors | Operand construction, scope, leaf/all-level distinction, thresholds, kernel-protection pairing, and completion helpers read directly. No hardware timing or architectural conformance test was performed. |
| Legacy enter/switch and TTBR helper; SPTM switch interface; `pcb.c` | Selected replacement/activation paths traced. SPTM's root-switch implementation is external. |
| SPTM physical-protect and reference-clear batching, cache-update batching | Deferred-TLBI contracts, alias selection, submission, completion, and PAPT handling inspected. Not every optional memory attribute/device policy is covered. |
| Aperture helpers, C/assembly cache routines | Physical/virtual boundaries and selected instruction/data visibility paths read directly; board-specific coherency and external monitor maintenance remain limits. |

These are source-based ordering traces, not a proof that every configuration and racing caller is correct. Configuration names and visible instruction variants are retained because collapsing them into one generic “flush the cache” operation would hide the behavior a reader needs to understand.
