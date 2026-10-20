# BSD syscalls: Virtual memory

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 65: msync

`int msync(caddr_ut addr, size_ut len, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L119) · **Condition:** `always` · **Audit event:** `AUE_MSYNC`.

Synchronize mapped memory according to the requested flags.

**Implementation:** [msync](../../../xnu/bsd/kern/kern_mman.c#L961). `msync_nocancel` sanitizes the range and calls `mach_vm_msync`; the ordinary wrapper first tests cancellation. This operation is distinct from descriptor fsync.

## 73: munmap

`int munmap(caddr_ut addr, size_ut len) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L131) · **Condition:** `always` · **Audit event:** `AUE_MUNMAP`.

Remove a process virtual-address range.

**Implementation:** [munmap](../../../xnu/bsd/kern/kern_mman.c#L1091). `munmap_sanitize` checks/normalizes the range before `mach_vm_deallocate_kernel` removes it from the current map; error conversion is handled at the BSD boundary.

## 74: mprotect

`int mprotect(caddr_ut addr, size_ut len, int prot) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L132) · **Condition:** `always` · **Audit event:** `AUE_MPROTECT`.

Change requested protections on a virtual range.

**Implementation:** [mprotect](../../../xnu/bsd/kern/kern_mman.c#L1163). Sanitizes range/protection, applies MAC/code-signing checks and invokes `mach_vm_protect`; maximum protection and map/pmap policy can reject the change.

## 75: madvise

`int madvise(caddr_ut addr, size_ut len, int behav);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L133) · **Condition:** `always` · **Audit event:** `AUE_MADVISE`.

Apply a virtual-memory behavior/advice request to a range.

**Implementation:** [madvise](../../../xnu/bsd/kern/kern_mman.c#L1387). `madvise_sanitize` validates the behavior/range, then `mach_vm_behavior_set` selects the VM operation; advice modes have different reclaim/read-ahead semantics.

## 78: mincore

`int mincore(caddr_ut addr, size_ut len, user_addr_t vec);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L136) · **Condition:** `always` · **Audit event:** `AUE_MINCORE`.

Report per-page residency/status information for a virtual range.

**Implementation:** [mincore](../../../xnu/bsd/kern/kern_mman.c#L1507). Sanitizes the range, queries batches with `vm_map_page_range_info_internal`, translates page-state bits and copies the result vector out.

## 85: swapon

`int swapon(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L143) · **Condition:** `always` · **Audit event:** `AUE_SWAPON`.

Preserve a historical swap-enable entry point.

**Implementation:** [swapon](../../../xnu/bsd/vm/vm_unix.c#L1190). The body returns `ENOTSUP`; actual compressor/swap lifecycle is not configured through this legacy syscall here.

## 197: mmap

`user_addr_t mmap(caddr_ut addr, size_ut len, int prot, int flags, int fd, off_t pos) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L293) · **Condition:** `always` · **Audit event:** `AUE_MMAP`.

Create a process virtual mapping from anonymous memory or a supported descriptor.

**Implementation:** [mmap](../../../xnu/bsd/kern/kern_mman.c#L279). Sanitizes address/size/protection/flags, resolves file or shared-memory backing and authorization, then enters Mach VM mapping with translated inheritance/copy/protection options; the returned address is copied through the syscall result ABI.

## 203: mlock

`int mlock(caddr_ut addr, size_ut len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L299) · **Condition:** `always` · **Audit event:** `AUE_MLOCK`.

Wire a user virtual-address range into memory.

**Implementation:** [mlock](../../../xnu/bsd/kern/kern_mman.c#L1671). Calls `vm_map_wire_kernel` for the current map with user-wiring semantics and translated protection; accounting, faults and resource-limit failures remain VM responsibilities.

## 204: munlock

`int munlock(caddr_ut addr, size_ut len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L300) · **Condition:** `always` · **Audit event:** `AUE_MUNLOCK`.

Remove user wiring from a range.

**Implementation:** [munlock](../../../xnu/bsd/kern/kern_mman.c#L1698). Calls `vm_map_unwire` for the current map/range; releasing a wiring claim is not necessarily freeing the physical page.

## 250: minherit

`int minherit(caddr_ut addr, size_ut len, int inherit);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L364) · **Condition:** `always` · **Audit event:** `AUE_MINHERIT`.

Change a mapping's fork inheritance behavior.

**Implementation:** [minherit](../../../xnu/bsd/kern/kern_mman.c#L1323). Sanitizes the range and inheritance value and calls `mach_vm_inherit`; later task/map copying interprets the resulting entry policy.

## 294: shared_region_check_np

`int shared_region_check_np(uint64_t *start_address) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L445) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Query/establish the process's shared-region association and start address.

**Implementation:** [shared_region_check_np](../../../xnu/bsd/vm/vm_unix.c#L1240). Uses `vm_shared_region_get` and shared-region validation/removal paths, considers task address width and mapping state, then returns the shared-region address through user output.

## 296: vm_pressure_monitor

`int vm_pressure_monitor(int wait_for_pressure, int nsecs_monitored, uint32_t *pages_reclaimed);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L447) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Query or wait for virtual-memory pressure information.

**Implementation:** [vm_pressure_monitor](../../../xnu/bsd/vm/vm_unix.c#L3181). Calls `mach_vm_pressure_monitor` with the requested wait/duration policy and copies pressure/reclaim information to the supplied output pointers.

## 324: mlockall

`int mlockall(int how);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L495) · **Condition:** `always` · **Audit event:** `AUE_MLOCKALL`.

Preserve declared whole-address-space wiring entry points without a local implementation.

**Implementation:** [mlockall](../../../xnu/bsd/kern/kern_mman.c#L1721). Each handler immediately returns `ENOSYS`; these numbers do not provide functioning whole-map lock/unlock operations in this checkout.

## 325: munlockall

`int munlockall(int how);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L496) · **Condition:** `always` · **Audit event:** `AUE_MUNLOCKALL`.

Preserve declared whole-address-space wiring entry points without a local implementation.

**Implementation:** [munlockall](../../../xnu/bsd/kern/kern_mman.c#L1727). Each handler immediately returns `ENOSYS`; these numbers do not provide functioning whole-map lock/unlock operations in this checkout.

## 405: msync_nocancel

`int msync_nocancel(caddr_ut addr, size_ut len, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L606) · **Condition:** `always` · **Audit event:** `AUE_MSYNC`.

Synchronize mapped memory according to the requested flags.

**Implementation:** [msync_nocancel](../../../xnu/bsd/kern/kern_mman.c#L1002). `msync_nocancel` sanitizes the range and calls `mach_vm_msync`; the ordinary wrapper first tests cancellation. This operation is distinct from descriptor fsync.

## 439: kas_info

`int kas_info(int selector, void *value, size_t *size);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L665) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Query selected kernel address-space layout information under privilege and configuration gates.

**Implementation:** [kas_info](../../../xnu/bsd/vm/vm_unix.c#L3218). The selector dispatch checks `CONFIG_KAS_INFO`, credentials/MAC and user-width/size inputs before copying slide or segment information; unsupported selectors/configurations fail rather than exposing arbitrary kernel memory.

## 440: memorystatus_control

`int memorystatus_control(uint32_t command, int32_t pid, uint32_t flags, user_addr_t buffer, size_t buffersize);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L667) · **Condition:** `(CONFIG_MEMORYSTATUS)` · **Audit event:** `AUE_NULL`.

Query or change process memory-status, limits, priority and related jetsam/freezer policy.

**Implementation:** [memorystatus_control](../../../xnu/bsd/kern/kern_memorystatus.c#L9227). Checks credentials/entitlements/MAC and dispatches the command to `memorystatus_cmd_*` helpers; list/snapshot queries, limit updates and process actions have different payload/ownership contracts.

## 453: memorystatus_get_level

`int memorystatus_get_level(user_addr_t level);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L695) · **Condition:** `(CONFIG_MEMORYSTATUS)` · **Audit event:** `AUE_NULL`.

Read the current memorystatus level.

**Implementation:** [memorystatus_get_level](../../../xnu/bsd/kern/kern_memorystatus.c#L894). Copies the maintained level value to the supplied user address; it does not initiate pressure collection or freeze a process.

## 489: mremap_encrypted

`int mremap_encrypted(caddr_ut addr, size_ut len, uint32_t cryptid, uint32_t cputype, uint32_t cpusubtype);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L753) · **Condition:** `(CONFIG_CODE_DECRYPTION)` · **Audit event:** `AUE_MPROTECT`.

Install encrypted-image mapping/decryption handling for a virtual range.

**Implementation:** [mremap_encrypted](../../../xnu/bsd/kern/kern_mman.c#L1751). Sanitizes the range, resolves the mapped vnode/offset identity and selects registered decryption/pager handling; cryptographic provider internals are outside this local frontend.

## 534: memorystatus_available_memory

`uint64_t memorystatus_available_memory(void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L846) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Estimate memory available to the current process under memorystatus policy.

**Implementation:** [memorystatus_available_memory](../../../xnu/bsd/kern/kern_memorystatus.c#L9788). Returns `memorystatus_available_memory_internal` through the 64-bit syscall result path, incorporating local limits/availability policy rather than raw free-page count alone.

## 536: shared_region_map_and_slide_2_np

`int shared_region_map_and_slide_2_np(uint32_t files_count, const struct shared_file_np *files, uint32_t mappings_count, const shared_file_mapping_slide_np_ut *mappings_u) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L848) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Map a collection of shared-cache files and slide/fixup metadata into the shared region.

**Implementation:** [shared_region_map_and_slide_2_np](../../../xnu/bsd/vm/vm_unix.c#L2178). Imports bounded file/mapping arrays through `shared_region_copyin`, validates descriptor-backed mappings, and enters the shared-region map/slide machinery; dyld's external cache production is outside this body.

## 550: map_with_linking_np

`int map_with_linking_np(void *regions, uint32_t region_count, void *link_info, uint32_t link_info_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L866) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Map file-backed regions with kernel-assisted linking metadata.

**Implementation:** [map_with_linking_np](../../../xnu/bsd/vm/vm_unix.c#L2372). Imports region/linking information, resolves vnode-backed descriptors and UBC objects, applies mmap policy and enters the VM map/linking path; the syscall consumes metadata rather than performing arbitrary userspace linking.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
