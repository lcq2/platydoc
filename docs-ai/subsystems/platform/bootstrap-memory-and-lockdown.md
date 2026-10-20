# ARM64 bootstrap memory, ownership and lockdown

[Platform overview](README.md) · [Boot to PID 1](boot.md) · [ARM64 pmap](../vm/pmap-arm64.md) · [Kernel allocation](../vm/kernel-allocation.md) · [SPTM](../security/sptm.md)

Before the kernel can allocate an ordinary object, it needs page tables, physical-page descriptors, maps and zones. Those facilities themselves require memory. ARM64 startup breaks that dependency cycle using image-resident storage, physical allocation cursors and an early mapping allocator. Later, it replaces temporary CPU stacks, releases selected image/boot memory and makes protected state immutable. This chapter follows those ownership changes, rather than repeating the complete boot-to-PID-1 sequence.

The two local ARM64 boot implementations are selected separately: the `config_pmap_ppl` source set includes `start.s`, `arm_init.c` and `arm_vm_init.c`; the `config_sptm` set includes `start_sptm.s` and `arm_init_sptm.c`. Common VM bootstrap follows both. “Legacy” below means the non-SPTM implementation, with further PPL/integrity guards identified where relevant. It does not mean that every branch in that file is active in one product. [Build selection](../../../xnu/osfmk/conf/files.arm64#L10-L36).

## 1. Boot arguments describe supplied memory; they do not allocate it

The bootloader supplies the ordinary `boot_args`. The record describes the initial address/size inputs; it is not recovered from a running VM map. [boot.h:50–65](../../../xnu/pexpert/pexpert/arm64/boot.h#L50-L65):

<!-- source-excerpt: ../../../xnu/pexpert/pexpert/arm64/boot.h#L50-L65 -->
```c
typedef struct boot_args {
	uint16_t                Revision;                       /* Revision of boot_args structure */
	uint16_t                Version;                        /* Version of boot_args structure */
	uint64_t                virtBase;                       /* Virtual base of memory */
	uint64_t                physBase;                       /* Physical base of memory */
	uint64_t                memSize;                        /* Size of memory */
	uint64_t                topOfKernelData;        /* Highest physical address used in kernel data area */
	Boot_Video              Video;                          /* Video Information */
	uint32_t                machineType;            /* Machine Type */
	void                    *deviceTreeP;           /* Base of flattened device tree */
	uint32_t                deviceTreeLength;       /* Length of flattened tree */
	char                    CommandLine[BOOT_LINE_LENGTH];  /* Passed in command line */
	uint64_t                bootFlags;              /* Additional flags specified by the bootloader */
	uint64_t                memSizeActual;          /* Actual size of memory */
} boot_args;

```

| Quantity | Domain and use |
|---|---|
| `virtBase`, `physBase` | The initial kernel virtual/physical relationship. Early affine conversion is valid only within that bootstrap mapping contract. |
| `memSize` | Managed physical span supplied to the architecture initialization path, subject to page alignment and configured overrides. |
| `memSizeActual` | Total memory reporting input, which may differ from the managed span. |
| `topOfKernelData` | Physical boundary after boot/kernel data in the legacy path. It is not a virtual allocation result. |
| `deviceTreeP`, `deviceTreeLength` | Borrowed boot description, used to discover memory-map entries, kernel-collection ranges and other platform inputs. |
| `SPTMArgs->first_avail_phys` | SPTM's later physical consumption boundary; overrides the temptation to start at the older `topOfKernelData`. |
| `SPTMArgs->physmap_base/end`, root-table address | Monitor-established physical-aperture VA range and translation-root PA adopted by XNU. |

The SPTM `arm_init()` copies both argument records into late-read-only storage. It explicitly uses the monitor's first available physical address because SPTM and other components have consumed pages after the bootloader's boundary. A copied record preserves the values; it does not transfer ownership of every referenced region into the allocator. [Argument adoption](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L767-L781), [physical aperture/root adoption](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1830-L1860).

Image segments add another set of intervals. `arm_vm_init()` discovers Mach-O ranges for text, constant data, bootstrap data, link information and prelinked images. `arm_vm_prot_init()` expands the low image boundary for kernel-collection headers and selected device-tree/trust-cache data. The TrustCache entry is a physical-address/length record with size and placement checks. SPTM also imports auxiliary-collection boundaries; the legacy path constructs/protects local mappings. These ranges prevent “everything before the free cursor” from being treated as one homogeneous disposable buffer. [Legacy segment/protection setup](../../../xnu/osfmk/arm64/arm_vm_init.c#L1269-L1395), [SPTM segment boundaries](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1507-L1607).

Bootloader allocation, firmware carveout policy and monitor-internal image validation are not supplied by these consumers. Where XNU checks supplied relationships, the chapter explains those checks; it does not reconstruct how the prior stage selected the addresses.

## 2. First translations and stacks precede ordinary kernel allocation

### Legacy/PPL-selected cold entry

`start_first_cpu()` masks interrupts, keeps the boot-argument PA in `x20`, loads initial virtual/physical bases into `x22/x23`, and uses `x25` for the bootstrap-table storage. It computes virtual stack addresses from the initial base relationship, installs the exception stack in SP_EL1 and the interrupt stack in SP_EL0, and prepares `lr` as the virtual address of `arm_init()`. These are temporary CPU stacks, not ordinary thread stacks allocated by `kmem_alloc()`. [Register and stack preparation](../../../xnu/osfmk/arm64/start.s#L468-L523).

It then creates a V=P identity mapping for the running transition and a kernel-virtual mapping of the image/memory span. The macro allocates additional L2 tables as required while advancing VA/PA cursors and the free table pointer. The earlier “four pages” explanatory comment is not a universal allocation count: the later implementation explicitly reserves two L1 roots and a variable number of L2 pages, bounded by the bootstrap storage configuration. The code also adjusts its bases to avoid mapping memory before the kernel-cache header. [Mapping macro](../../../xnu/osfmk/arm64/start.s#L427-L459), [base adjustment and variable tables](../../../xnu/osfmk/arm64/start.s#L574-L624), [image-resident table buffer](../../../xnu/osfmk/arm64/arm_vm_init.c#L79-L87).

`common_start` programs the translation regime and table bases, cache attributes and vector address, then enables translation/caches through SCTLR and continues at the prepared virtual C entry. Warm/secondary paths have different inputs and can select an already-established `cpu_ttep`; they must not be described as rebuilding the cold VM state. [Translation setup](../../../xnu/osfmk/arm64/start.s#L645-L725), [vectors/SCTLR and C argument](../../../xnu/osfmk/arm64/start.s#L726-L814).

### SPTM cold entry

The SPTM entry receives a reason in `x0`, ordinary boot arguments in `x1` and monitor arguments in `x2`. Cold startup installs the supplied image's temporary stack addresses, preserves the argument pointers in `x26/x27`, rebases/signs absolute addresses and initializes static branches. It sets XNU vectors before issuing `SPTM_FUNCTIONID_FIXUPS_COMPLETE`. The local comments identify the initial executable region and monitor transition; the source does not contain the monitor's page-table construction or protected-register enforcement. [Entry contract](../../../xnu/osfmk/arm64/sptm/start_sptm.s#L35-L70), [cold setup and handoff](../../../xnu/osfmk/arm64/sptm/start_sptm.s#L121-L176).

Do not transplant the legacy TTBR-writing sequence into this route. SPTM `arm_vm_init()` adopts the monitor root via `libsptm_state.root_table_paddr`; it does not construct that root with the legacy `alloc_ptpage(TRUE)` sequence. [Adopted root](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1852-L1860).

```mermaid
flowchart TB
    B["Boot arguments and image storage"] -->|"PPL-selected entry"| L["Identity and kernel-VA bootstrap tables<br/>temporary CPU stacks"]
    B -->|"SPTM-selected entry"| S["Monitor-established mappings<br/>fixups-complete handoff"]
    L -->|"construct root<br/>and aperture"| LV["Legacy arm_vm_init"]
    S -->|"adopt root<br/>and aperture"| SV["SPTM arm_vm_init"]
    LV -->|"publish PA / VA bounds"| V["Common VM bootstrap"]
    SV -->|"publish PA / VA bounds"| V
    V -->|"normal kernel thread and allocators exist"| F["Finalize mappings and stacks<br/>release selected storage and lock down"]
```

## 3. Early table allocation is a physical cursor or image reservation

The legacy `alloc_ptpage(map_static)` returns a **virtual address**. Integrity configurations can satisfy static tables from `ropagetable_begin..ropagetable_end`, an image-resident area that will become read-only. Otherwise it converts `avail_start` to a physical-aperture pointer and increments the **physical cursor** by `ARM_PGBYTES`. It neither asks a zone for an object nor removes a `vm_page` from the free queue. Without the relevant integrity configuration, the static request is forced to the dynamic cursor route. [Legacy allocator](../../../xnu/osfmk/arm64/arm_vm_init.c#L449-L486).

The SPTM helper with the same general role returns a **physical address**, accepts a table level, and calls `sptm_retype(..., XNU_PAGE_TABLE, ...)`. The level is part of the frame-conversion request. The similarly named functions are therefore not interchangeable APIs. [SPTM allocator](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1698-L1744).

The SPTM dynamic branch and frame-type publication are visible in [arm_init_sptm.c:1728–1740](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1728-L1740):

<!-- source-excerpt: ../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1728-L1740 -->
```c
	} else {
		/* This is a RW allocation. Simply grab a page from [avail_start] */
		paddr = avail_start;
		avail_start += ARM_PGBYTES;
	}

	/* Retype the page to XNU_PAGE_TABLE, with the desired level */
	sptm_retype_params_t retype_params;
	retype_params.level = level;
	sptm_retype(paddr, XNU_DEFAULT, XNU_PAGE_TABLE, retype_params);

	return paddr;
}
```

`ARM_PGBYTES` is the hardware table-page granule in these helpers. Later VM ownership uses `PAGE_SIZE`, the software page size. Both `arm_vm_init()` implementations round the final free physical start **up** to a software-page boundary and the managed end **down** so VM never claims a partial page. An assumed “4 KiB everywhere” calculation would be wrong for the 16 KiB configurations and for test configurations with differing software/hardware sizes. [SPTM managed-end calculation](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1785-L1800), [SPTM final cursor](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L2166-L2176), [legacy final cursor](../../../xnu/osfmk/arm64/arm_vm_init.c#L2383-L2394).

### The permanent root and physical aperture change address assumptions

Legacy initialization builds `invalid_tte` and the later `cpu_tte`, establishes segment protections and dynamic VA table coverage, constructs the physical aperture, switches TTBR1 to `cpu_ttep`, installs an invalid TTBR0 and flushes translations. Only then does it set `kva_active` and recompute table pointers through `phystokv()`. [Root construction](../../../xnu/osfmk/arm64/arm_vm_init.c#L1936-L1964), [switch and pointer repair](../../../xnu/osfmk/arm64/arm_vm_init.c#L2124-L2180).

The PPL physical-aperture builder records `ptov_table_entry` intervals rather than assuming one affine VA/PA relationship forever. It maps reusable/ownership-changing regions at page granularity, slides bootstrap segments and ordinary memory into their aperture locations, adjusts an unlocked device-tree pointer, and publishes the conversion table. A later `gVirtBase/gPhysBase` subtraction on an arbitrary aperture pointer can therefore describe the wrong physical address. [Interval construction](../../../xnu/osfmk/arm64/arm_vm_init.c#L1516-L1543), [PPL aperture construction](../../../xnu/osfmk/arm64/arm_vm_init.c#L1553-L1629).

SPTM supplies its initial aperture range and root; XNU continues local bookkeeping and allocates additional table pages through monitor interfaces. Some image regions undergo a later `sptm_slide_region()` handoff during finalization. The implementation of that slide is external. Both source files retain a TODO concerning reclamation of bootstrap table memory; leaving the bootstrap root does not establish that every page once used for tables was freed. [SPTM adoption/TODO](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1830-L1860), [legacy TODO](../../../xnu/osfmk/arm64/arm_vm_init.c#L1936-L1941).

## 4. Pmap stealing breaks the map/zone/page-descriptor dependency cycle

After architecture initialization, `kernel_bootstrap()` calls `vm_mem_bootstrap()`. The sequence matters: resident-page bootstrap runs before zone bootstrap; special VM objects precede map initialization; `kmem_init()` then adopts the remaining VA range and advances KMEM/ZALLOC startup. [Common bootstrap](../../../xnu/osfmk/kern/startup.c#L521-L548), [VM order](../../../xnu/osfmk/vm/vm_init.c#L106-L141).

`vm_page_bootstrap()` initializes locks and page queues, advances the `PMAP_STEAL` startup phase and allocates resident hash/lock bookkeeping through `pmap_steal_memory()`. The `vm_map_steal_memory()` startup callback reserves enough storage for early kernel/submaps and their entries/nodes before those zones can expand dynamically. With MTE it also creates cell metadata before the canonical page array. This is a deliberate bootstrapping reserve, not an ordinary late allocation of every map entry. [Resident bootstrap](../../../xnu/osfmk/vm/vm_resident.c#L2120-L2181), [early phase](../../../xnu/osfmk/vm/vm_resident.c#L2240-L2251), [hash allocations](../../../xnu/osfmk/vm/vm_resident.c#L2294-L2323), [early maps](../../../xnu/osfmk/vm/vm_map.c#L1892-L1955).

`pmap_steal_memory_internal()` maintains a VA cursor independent of `avail_start`/`first_avail`:

1. Obtain the available kernel VA interval from pmap on first use; align the request and advance `virtual_space_start`.
2. For pages of the new VA span that still need backing, obtain physical frames with `pmap_next_page_hi()` and install writable kernel translations with `pmap_enter()`.
3. Account them as stolen/wired and return the VA. The API has fatal early-allocation failure paths rather than a general rollback transaction.

Word-aligned subpage allocations can share already-backed pages. The `map_addr = round_page(addr)` start is significant: this is not one physical page unconditionally allocated per call. `pmap_steal_freeable_memory()` changes the lifetime hint; on the ARM implementations inspected, `pmap_next_page_hi()` delegates to `pmap_next_page()` and ignores that hint. It does not by itself free the returned storage. [Steal allocator](../../../xnu/osfmk/vm/vm_resident.c#L2406-L2553), [wrappers](../../../xnu/osfmk/vm/vm_resident.c#L2557-L2578), [SPTM physical cursor](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L2520-L2547).

| Stage | Allocation identity | Later ownership |
|---|---|---|
| Image static storage | Linker-reserved bytes/table or stack symbol | Retained or explicitly jettisoned according to the segment's role. |
| `alloc_ptpage` | Hardware-granule frame from the early PA cursor, or image table reserve | Translation-table state; page-table protection/frame type follows the selected backend. |
| `pmap_steal_memory` | VA range backed by frames removed from the remaining physical cursor | Early bookkeeping/zone storage, accounted as unavailable to ordinary allocation. |
| `pmap_startup` | `vm_page` descriptors for the remaining physical span | Free/replacement queues and normal VM-page APIs become usable. |
| `kmem_init` and later allocators | VM-map ranges, objects and page ownership | Ordinary kernel allocation and teardown contracts. |

These stages overlap in initialization, but they must not be collapsed into a claim that `kalloc` was already available to build all its own prerequisites.

## 5. Canonical page descriptors make the remaining frames allocatable

`pmap_startup()` estimates descriptor count from the remaining physical span and `PAGE_SIZE + sizeof(struct vm_page)`, then steals storage for the `vm_pages` array itself. On ARM with a linear array, the span matters even when retired-page holes exist. The implementation notes that this estimate does not fully include page-table memory needed to map the array. It initializes descriptors while `pmap_next_page()` supplies frames, records `vm_pages_first_pnum`, and publishes free pages through startup release rules. [Array sizing](../../../xnu/osfmk/vm/vm_resident.c#L2602-L2672), [descriptor initialization/release](../../../xnu/osfmk/vm/vm_resident.c#L2735-L2796).

For SPTM, first use of the physical cursor initializes RAM ranges and optional MTE bookkeeping boundaries; subsequent calls advance `first_avail` by software pages and decrement available capacity until `avail_end`. It does not walk a running process map. [Physical allocator](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L2530-L2547), [MTE range adjustment](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L2410-L2496).

The initial wire count includes memory withheld from general VM even if no ordinary object performed `vm_page_wire()` on it. It is computed from total memory and free pools with feature-specific deductions, including MTE tag storage. Later releases must repair this accounting. The code also realigns and returns the unconsumed kernel VA range to `vm_mem_bootstrap()` for `kmem_init()`. [Initial wire accounting](../../../xnu/osfmk/vm/vm_resident.c#L2356-L2382), [remaining VA publication](../../../xnu/osfmk/vm/vm_resident.c#L2818-L2830).

MTE storage is not indiscriminately put on the ordinary free queue. Startup separates active tag backing, inactive claimable storage and recursive/unmanaged storage; some special-object insertion waits until KMEM initialization. See [MTE tag storage](../vm/mte-tag-storage-and-page-lifecycle.md#3-boot-creates-metadata-before-publishing-usable-backing).

## 6. Replacing CPU boot stacks must precede releasing their segment

By `machine_lockdown()`, execution is on a normal kernel thread bound to the boot CPU, so the temporary CPU exception/interrupt stacks can be replaced while they are not active. `cpu_stack_alloc()` allocates new permanent, zeroed, guarded stacks through `kmem_alloc()` and publishes their tops/pointers into `BootCpuData`. Each allocation has a guard page on either side; it is not merely a new pointer into BOOTDATA. [Allocation and published fields](../../../xnu/osfmk/arm64/cpu.c#L767-L787), [bootstrap-thread execution](../../../xnu/osfmk/kern/startup.c#L704-L764).

`arm64_replace_bootstack()` requires that kernel-thread context. It loads the new exception-stack top, masks asynchronous exceptions, selects SP_EL1, writes the new stack pointer, returns to SP_EL0 and restores DAIF. It does **not** copy an active boot call stack. Updating SP_EL1 must also precede lockdown of sensitive instructions on the relevant integrity configurations. [Contract and assembly](../../../xnu/osfmk/arm64/machine_routines_asm.s#L1736-L1766).

The critical assembly sequence is [machine_routines_asm.s:1747–1766](../../../xnu/osfmk/arm64/machine_routines_asm.s#L1747-L1766):

<!-- source-excerpt: ../../../xnu/osfmk/arm64/machine_routines_asm.s#L1747-L1766 -->
```asm
LEXT(arm64_replace_bootstack)
	ARM64_STACK_PROLOG
	PUSH_FRAME
	// Set the exception stack pointer
	ldr		x0, [x0, CPU_EXCEPSTACK_TOP]
	mrs		x4, DAIF					// Load current DAIF; use x4 as pinst may trash x1-x3
	msr		DAIFSet, #(DAIFSC_STANDARD_DISABLE)		// Disable all asynchronous exceptions
	// Set SP_EL1 to exception stack
#if defined(KERNEL_INTEGRITY_KTRR) || defined(KERNEL_INTEGRITY_CTRR) || defined(KERNEL_INTEGRITY_PV_CTRR)
	mov		x1, lr
	bl		EXT(pinst_spsel_1)
	mov		lr, x1
#else
	msr		SPSel, #1
#endif
	mov		sp, x0
	msr		SPSel, #0
	msr		DAIF, x4					// Restore interrupt state
	POP_FRAME
	ARM64_STACK_EPILOG EXT(arm64_replace_bootstack)
```

Legacy finalization replaces the stacks before freeing the BOOTDATA backing through its aperture address and clearing obsolete image aliases. SPTM finalization replaces them before asking the monitor to slide BOOTDATA, which would remove the old stack mapping. Freeing the physical pages is a later step in both explanations. [Legacy order](../../../xnu/osfmk/arm64/arm_vm_init.c#L1683-L1713), [SPTM order](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1637-L1650).

## 7. Static release disconnects aliases and may delay free-list publication

`ml_static_mfree(vaddr, size)` takes a virtual range and visits complete software pages. It converts each address through `kvtophys()` and then `phystokv()` to find the current physical-aperture alias. For a present translation it disconnects the page's other pmap mappings, restores an allocator-compatible physical-aperture/frame state, and creates canonical VM bookkeeping. It adjusts initial/current wired and kernel-cache counts afterward. [Release body](../../../xnu/osfmk/arm64/machine_routines.c#L2154-L2229).

`ml_static_protect()` is backend-specific. The SPTM branch retypes nondefault frames to `XNU_DEFAULT`. The legacy branch updates local permissions, rejects W+X or post-lockdown executable injection, and cannot arbitrarily change part of a block or contiguous-hint group whose permissions differ. A caller must not summarize the SPTM branch as directly editing the same PTEs as legacy. [Protection/retype split](../../../xnu/osfmk/arm64/machine_routines.c#L1953-L2052).

There is a further lifetime boundary: **a descriptor can exist before the frame is on a free queue**. Until aperture sliding has completed, `ml_static_mfree()` creates the descriptor and puts it on `ml_static_mfree_pre_slide_list`. Reusing that page too soon could leave pmap users with pointers to an aperture alias that subsequently moves. After `arm_vm_prot_finalize()` returns, `machine_lockdown()` calls `ml_release_deferred_pages()` to release that entire list; future static frees can publish immediately. [Deferred-list rationale and release](../../../xnu/osfmk/arm64/machine_routines.c#L2110-L2148), [caller order](../../../xnu/osfmk/arm64/machine_routines.c#L559-L573).

The publication choice appears in [machine_routines.c:2199–2206](../../../xnu/osfmk/arm64/machine_routines.c#L2199-L2206):

<!-- source-excerpt: ../../../xnu/osfmk/arm64/machine_routines.c#L2199-L2206 -->
```c
			if (__probable(!ml_static_mfree_queue_up)) {
				vm_page_create_canonical(ppn);
			} else {
				vm_page_t m = vm_page_create(ppn, true, Z_WAITOK);

				vm_page_list_push(&ml_static_mfree_pre_slide_list, m);
			}

```

```mermaid
sequenceDiagram
    participant J as Bootstrap-data owner
    participant M as ml_static_mfree
    participant P as Pmap or monitor
    participant V as VM page bookkeeping
    participant L as machine_lockdown
    J->>M: Release an eligible static range
    M->>P: Resolve current PA and aperture alias
    M->>P: Disconnect aliases and restore usable frame state
    M->>V: Create descriptor on deferred list
    L->>P: Complete arm_vm_prot_finalize
    L->>V: Release deferred descriptors to free queues
    Note over V: Allocators may now receive these physical pages
```

The diagram describes a pre-finalization release. After deferred mode is disabled, the same API publishes through `vm_page_create_canonical()` directly. It is not a promise that every supplied byte is released: below-aperture requests can return early, only complete pages are visited, absent translations are skipped, and protection failure is fatal rather than silently returning unsafe memory to VM. [Checks and failure policy](../../../xnu/osfmk/arm64/machine_routines.c#L2165-L2195).

## 8. Finalization and lockdown are related but separate operations

The bootstrap thread first loads the static trust-cache interfaces, runs `STARTUP_SUB_LOCKDOWN` callbacks, and jettisons kext bootstrap data with `OSKextRemoveKextBootstrap()`. That must precede `machine_lockdown()` because it can release or relocate static mappings. General IOKit matching is unlocked afterward through `PE_lockdown_iokit()`, and BSD startup follows. The startup phase named LOCKDOWN is therefore not itself the final hardware/monitor lock call. [Common ordering](../../../xnu/osfmk/kern/startup.c#L863-L923), [module teardown companion](../drivers/kext-loading-and-unloading.md).

| Operation | Legacy/PPL-selected path | SPTM-selected path |
|---|---|---|
| Selected early storage | Release pre-image/eligible prelink gaps, replace stacks and release BOOTDATA. | Slide selected KLDDATA, BOOTDATA, linkedit and prelink-info regions; release physical-slide storage, eligible gap and BOOTDATA. |
| Obsolete aliases | Under `XNU_MONITOR`, clear old image aliases for jettisoned bootstrap/link regions. | Request `sptm_slide_region()`; its internal mapping manipulation is not supplied. |
| Permissions | Tighten selected segments; make static page-table-containing DATA_CONST read-only last; barrier and TLB flush. | Prepare protected state locally, then use the monitor lockdown interface. |
| Final integrity | Configuration-selected region locking and optional PPL lockdown. | Prepare commpages and call `sptm_lockdown_xnu()` with preemption explicitly disabled. |

[Legacy finalization](../../../xnu/osfmk/arm64/arm_vm_init.c#L1654-L1755), [SPTM finalization](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1626-L1695), [machine integrity dispatch](../../../xnu/osfmk/arm64/machine_routines.c#L575-L623).

Linkedit is not unconditionally discarded/slid: `keepsyms`, configured DTrace symbol retention and the KASAN dynamic denylist alter the decision. Likewise, integrity macros determine which static tables/instructions can become immutable. The final non-SPTM permission update deliberately leaves DATA_CONST until other changes are complete because that region can contain the very tables needed to make those changes. [SPTM symbol retention](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1651-L1673), [legacy last protection](../../../xnu/osfmk/arm64/arm_vm_init.c#L1727-L1755).

`machine_lockdown()` performs finalization, releases deferred pages, dispatches the configured integrity operations, invokes the applicable platform HMAC invalidation callback and finally sets `lockdown_done`. The local SPTM call documents a potentially long retyping operation and disables preemption around it. Its comment about monitor-controlled register locks is an interface explanation; absent monitor code cannot establish the exact protected-register sequence. [Machine completion](../../../xnu/osfmk/arm64/machine_routines.c#L559-L650).

## 9. Reading a later physical page back through boot

Consider a page formerly backing a jettisoned bootstrap-data segment. This is an illustrative ownership trace, with addresses omitted because they depend on the selected image/platform:

1. The supplied image/boot intervals keep it outside the ordinary physical cursor. Its initial inability to move is reflected in initial wired accounting, even without an ordinary VM-object wire call.
2. A bootstrap consumer finishes using the data and calls the static-release path. The page can retain a usable physical-aperture translation after original aliases are disconnected.
3. The release path prepares permissions/frame type and creates a descriptor. If aperture finalization is incomplete, the descriptor waits on the deferred list.
4. Finalization finishes, deferred release puts it into an appropriate VM free queue, and an ordinary allocation can obtain it.
5. The new allocation can insert the page into a different VM object/map while the physical-aperture alias continues to exist for kernel access.

This is why “still mapped,” “has a canonical descriptor,” “counts as wired” and “available to allocation” answer different questions. The same distinction explains active MTE backing: its physical pages are represented by VM but deliberately owned/wired for tags. [Static release](../../../xnu/osfmk/arm64/machine_routines.c#L2154-L2229), [MTE companion](../vm/mte-tag-storage-and-page-lifecycle.md).

## 10. Configuration, evidence and limits

| Branch or evidence | What was established |
|---|---|
| `config_pmap_ppl` / `config_sptm` | Separate source selection and materially different early root/aperture ownership. [Selection](../../../xnu/osfmk/conf/files.arm64#L10-L36). |
| `ARM_PGBYTES` versus `PAGE_SIZE` | Early table allocation and VM ownership alignment use different named units; no universal granule is assumed. [Alignment](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1785-L1800). |
| `XNU_MONITOR`, KTRR/CTRR variants, `CONFIG_KERNEL_INTEGRITY` | Control static table allocation, obsolete-alias removal and final protection/locking. Their branches are described separately. [Finalization](../../../xnu/osfmk/arm64/arm_vm_init.c#L1695-L1755), [integrity dispatch](../../../xnu/osfmk/arm64/machine_routines.c#L575-L623). |
| `HAS_MTE`, runtime MTE and memory overrides | Tag storage must remain represented; capacity capping uses a special RAM-range policy. [Range logic](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L2410-L2494). |
| `KASAN`, symbol-retention options | Change memory reservations, early entry and release/slide choices; no single allocator geometry covers all sanitizer builds. [Retention](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1651-L1673), [memory geometry](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1783-L1838). |
| Assertions and panic branches | Source checks establish alignment, available static-table bounds and protection requirements. They were inspected, not triggered by booting a kernel. [Table bounds](../../../xnu/osfmk/arm64/arm_vm_init.c#L460-L484), [release failure](../../../xnu/osfmk/arm64/machine_routines.c#L2184-L2195). |
| `CONFIG_XNUPOST` | The generic post-test dispatcher runs after machine lockdown; its presence is not a dedicated proof of these ownership transitions. [Dispatch](../../../xnu/osfmk/kern/startup.c#L894-L903). |

This chapter follows selected local cold-boot paths, common VM bootstrap, static-page release and final integrity handoffs. It does not claim a new hardware boot test, exhaustive SoC register coverage, complete page-table reclamation, firmware allocation knowledge or monitor-internal verification. Normal exception/context switching and hibernation restoration use related structures but have separate lifetimes in their existing chapters.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
