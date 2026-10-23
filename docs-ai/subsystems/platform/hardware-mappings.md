# Hardware mappings and pmap backends

[Platform overview](README.md) · [VM subsystem](../vm/README.md)

This page connects machine execution to VM. For the full implementation, continue with [ARM64 table geometry and metadata](../vm/pmap-arm64.md), [mapping and table lifetimes](../vm/pmap-mapping-lifecycle.md), [TLB/cache operations and activation](../vm/pmap-tlb-and-cache.md), and [x86_64 pmap](../vm/pmap-x86.md). The [mapping walkthroughs](../vm/mapping-walkthroughs.md) trace the higher-level VM policy that supplies these operations.

## Separate VM policy from installed translations

A `vm_map` describes virtual ranges, protections, and backing objects. Its `pmap` supplies the hardware translation layer. Resolving a fault may fetch or create a VM page before installing a PTE; removing a mapping must also account for cached translations and metadata that identifies other mappings of that physical page. The machine exception path's `arm_fast_fault()`/`vm_fault()` split makes this boundary visible. [`sleh.c`](../../../platydoc-data/xnu/osfmk/arm64/sleh.c#L1951), [`VM pmap interface`](../../../platydoc-data/xnu/osfmk/vm/pmap.h).

`osfmk/arm/pmap.h` selects the SPTM header under `CONFIG_SPTM`, otherwise the legacy ARM header. Build configuration selects matching source implementations. A symbol search for `pmap_enter_options_addr()` therefore finds several implementations and prototypes; its effective body depends on the build. [`arm/pmap.h`](../../../platydoc-data/xnu/osfmk/arm/pmap.h#L42), [`files.arm64`](../../../platydoc-data/xnu/osfmk/conf/files.arm64#L10).

| Backend | Core representation | Commit/activation boundary |
|---|---|---|
| Legacy ARM/PPL | `tte` virtual root, `ttep` physical root, page-table geometry, ledger, old RW lock, references and address-space identity | Wrapper selects PPL entry or direct internal implementation according to `XNU_MONITOR`. |
| ARM64 SPTM | Root virtual/physical pointers, geometry, ledger, reference count, nested-region metadata, ASID/VMID | XNU prepares metadata and uses monitor operations such as `sptm_map_page()` and `sptm_switch_root()`. |
| x86_64 | `pm_pml4`, `pm_cr3`, user shadow roots, PCIDs/coherency vector, EPT root, RW lock and ledger | Page-table updates plus CR3/PCID activation and cross-CPU invalidation machinery. |

Definitions and dispatch: [`legacy pmap`](../../../platydoc-data/xnu/osfmk/arm/pmap/pmap.h#L334), [`SPTM pmap`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.h#L307), [`x86 pmap`](../../../platydoc-data/xnu/osfmk/i386/pmap.h#L583), [`legacy enter wrapper`](../../../platydoc-data/xnu/osfmk/arm/pmap/pmap.c#L6673), [`SPTM activation`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L4354).

ARM `pmap.min/max` describe bounds supported by the paging hierarchy, not all higher-level address-space partition policy. ASIDs identify address spaces for translation caching; the SPTM structure reserves zero for the kernel and also uses zero for nested pmaps that are never directly activated. The union includes a VMID for stage-2 contexts, but the inspected public SPTM creation path passes `is_stage2 = false`; the field alone does not establish a complete stage-2 implementation. [`SPTM pmap.h`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.h#L314), [creation and scope](../vm/pmap-arm64.md).

## Follow one SPTM mapping installation

`pmap_enter_options_addr()` calls `pmap_enter_options_internal()`. The internal path validates alignment, range, and mapping constraints, constructs a PTE, and coordinates physical-page metadata through a locked PV-head entry. Reverse mappings let operations starting from a physical page find affected PTEs. The code retries when allocation drops protection, a conflicting physical mapping must be removed, a table must be expanded, or a prior flush remains pending. [`pmap.c`, wrapper](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L7009), [`internal setup`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L6625), [`retry cases`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L6768).

`pmap_enter_pte()` is the critical boundary. Its caller must have preemption disabled because monitor results are returned through per-CPU storage. It determines the required frame type, handles retyping constraints, enters a pmap epoch, calls `sptm_map_page()`, and reads the prior PTE and resulting PTE pointer from the monitor output. Wiring metadata is updated before leaving the epoch. Failure unwinds temporary frame-type changes; flush-pending results ask the caller to retry. These are source-visible XNU contracts, not an inspection of the monitor's internal validation. [`pmap_enter_pte()`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L6328).

The epoch prevents concurrent table removal or unnesting from invalidating assumptions during the operation. PV-head protection prevents a competing mapping installation on the same physical page while retyping is prepared. Long reverse-map operations can permit preemption, invalidating cached per-CPU pointers; the code explicitly detects or retries around that transition. A single global “pmap lock” is therefore an inadequate description of this backend. [`pmap_enter_pte()`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L6390), [`PV allocation retry`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L6730).

Removal has a complementary lifetime problem. `pmap_remove_range_options()` pins the leaf table while it removes translations through `sptm_unmap_region()` and later removes reverse-map entries. Otherwise another remover could free a page-table descriptor while a reverse-map consumer still needs it. It batches monitor requests with preemption disabled, then copies the physical-page indices it needs before performing work that can permit migration. The wrapper splits ranges at leaf-table boundaries. [`pmap_remove_range_options()`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L3797), [`pmap_remove_options()`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L4182).

## PPL is a different implementation boundary

Legacy ARM `pmap_enter_options_addr()` invokes `pmap_enter_options_ppl()` when `XNU_MONITOR` is enabled, forcing the inner call to avoid blocking allocation. Resource shortage can be handled outside the protected call by allocating a page for PPL, then retrying; an externally requested `PMAP_OPTIONS_NOWAIT` limits that behavior. Other builds call the internal function directly. Ledger flushing is also performed outside the protected call. [`legacy pmap.c`](../../../platydoc-data/xnu/osfmk/arm/pmap/pmap.c#L6673).

The PPL interface macros generate protected-entry variants, while internal routines use explicit pmap lock/preemption contracts and reverse-map metadata. The SPTM backend retains several historical filenames/macros, so a file named `pmap_ppl_interface.c` under `sptm/` does not establish that it executes the legacy PPL transition. Inspect the selected macro definitions and actual calls. [`legacy interface description`](../../../platydoc-data/xnu/osfmk/arm/pmap/pmap_ppl_interface.c#L30), [`legacy lock helpers`](../../../platydoc-data/xnu/osfmk/arm/pmap/pmap_internal.h#L226), [`SPTM internal macro`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap_internal.h#L59).

## TLB completion is part of correctness

Changing page-table memory is not enough to make every CPU stop using an old translation. ARM's `flush_mmu_tlb_region_asid_async()` selects whole-ASID/global, range, or individual-entry invalidation according to size, hardware support, and nested-map status. The synchronous wrapper follows it with `sync_tlb_flush()`. SPTM update operations can also defer invalidation for batching, and mapping retries account for pending flushes. Follow the completion point before concluding that physical memory or a table may be reused. [`ARM flush selection`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L10265), [`deferred-update flags`](../../../platydoc-data/xnu/osfmk/arm64/sptm/pmap/pmap.c#L5107).

On x86, `pmap_flush_tlbs()` scans running CPUs for matching active/task CR3s or shared mappings, invalidates PCID coherency state, and marks or signals affected CPUs. Some CPUs may flush lazily at an idle/kernel boundary; active users of the relevant map need explicit signaling. The function waits for required completion and has timeout handling. EPT mappings use a distinct `invept` path. [`x86 pmap.c`](../../../platydoc-data/xnu/osfmk/x86_64/pmap.c#L2924).

x86 `pmap_enter_options()` uses a shared pmap lock while locating tables, releases it to expand missing tables, and then retries. Its per-PTE/physical-page synchronization and TLB decisions sit below the common mapping API. Activation calls `set_dirbase()` with interrupts disabled; PCID support can preserve valid cached translations rather than forcing a full flush every switch. [`pmap_x86_common.c`](../../../platydoc-data/xnu/osfmk/i386/pmap_x86_common.c#L653), [`pmap_switch()`](../../../platydoc-data/xnu/osfmk/x86_64/pmap.c#L2715), [`PCID activation`](../../../platydoc-data/xnu/osfmk/x86_64/pmap_pcid.c#L329).

## Physical addresses, aperture addresses, and I/O mappings

Do not dereference a physical address as though it were a kernel pointer. Legacy `phystokv()` first searches the physical-to-virtual aperture table, then uses a checked base-offset fallback. SPTM `phystokv()` asks `sptm_phystokv()` and returns zero on failure. Neither API is a general replacement for translating arbitrary task virtual addresses. [`legacy arm_vm_init.c`](../../../platydoc-data/xnu/osfmk/arm64/arm_vm_init.c#L383), [`SPTM arm_init_sptm.c`](../../../platydoc-data/xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1384).

`io_map()` illustrates a separate physical/virtual boundary: before KMEM startup it reserves kernel virtual space and uses bootstrap mapping routines; later it allocates a kernel-map range and installs mappings with device/cache attributes. It reserves address space for the supplied physical range rather than allocating new device memory. Also distinguish software `PAGE_SIZE` from hardware translation granules; ARM VM initialization explicitly rounds managed memory to software-page boundaries. [`io_map.c`](../../../platydoc-data/xnu/osfmk/arm/io_map.c#L70), [`SPTM VM initialization`](../../../platydoc-data/xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1785).

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
