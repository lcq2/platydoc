# Coverage audit: VM and driver runtime

**Current source-documentation pass.** [Writing protected object fields](../structures/read-only-object-updates.md) follows concrete `proc` and `task` setters through RO macros, source/destination checks and ARM64 physical-alias writes. The [key-structures overview](../structures/README.md) connects regular and RO zone allocations to separate reference and SMR protocols. Legacy ARM/PPL, SPTM and disabled-enforcement paths retain distinct contracts. See the [structure-study record](first-release-expansion.md#25-key-structures-proc-task-and-protected-updates); other structure families and complete field/configuration/interleaving coverage remain separate.

**Previous executable-pages and UPL pass (historical scope).** [Executable pages and UPL I/O](../subsystems/vm/executable-pages-and-upl-io.md) follows direction-dependent admission, the SPTM/non-macOS copy predicates, temporary kernel backing, changed data offsets and lifetime through UPL completion. It connects executable policy to the existing gather and DMA explanations; external monitor/device enforcement remains bounded. See the [parallel-batch record](first-release-expansion.md#23-exec-stacks-executable-io-and-scheduler-placement).

**Previous executable-memory and packet-policy pass (historical scope).** [Executable-memory policy](../subsystems/vm/executable-memory-policy.md) now connects MAP_JIT admission, common/mobile and macOS protection branches, monitor association, ARM64 fault policy and SPTM frame classification, with 16 KiB worked examples. This does not establish external entitlement grants, monitor policy or the user-space JIT switching implementation. See the [two-batch record](first-release-expansion.md#22-executable-memory-synchronization-packet-policy-and-build-selection).

**Previous argument/identity pass (historical scope).** The [argument/identity expansion](first-release-expansion.md#21-arguments-identity-integrity-instrumentation-and-packet-state) adds VM API argument sanitization and a complete IOKit external-method call through caller/connection/memory ownership, dispatch, output and async cleanup. Existing mapping/DMA/service chapters remain prerequisites; unavailable concrete providers remain bounded.

The [earlier prioritized pass](first-release-expansion.md#19-prioritized-review-ip-control-power-policy-and-instrumentation) implements the selected historical D4 policy mechanisms in a dedicated companion. Battery/thermal/clamshell/AOT combinations, external powerd and concrete display/storage/platform providers remain bounded; the existing sleep-transition chapters retain their role.

**Earlier follow-up status (historical scope).** Later work implements [copy-overwrite and mixed page sizes](../subsystems/vm/copy-overwrite-and-remap.md), [MTE tag-storage lifetime](../subsystems/vm/mte-tag-storage-and-page-lifecycle.md), and [ARM64 bootstrap memory/lockdown](../subsystems/platform/bootstrap-memory-and-lockdown.md). The latter two now connect MTE's boot/CPU prerequisites to process policy, checked mappings and aliases, allocator retagging, copy/compressor preservation and hard/soft/deferred faults; see the [mitigation expansion record](first-release-expansion.md#14-mte-mitigation-from-boot-policy-to-allocation-and-fault). The [first-release record](first-release-expansion.md) links the compressor, shared-region, deferred/purgeable/phantom, loading, serialization and NVRAM companions. [Symbol interning](../subsystems/drivers/symbol-interning.md) now explains pool publication, string backing and SMR destruction, with a separate [hash-table algorithm companion](../cross-cutting/smr-hash-tables.md). [Power assertions and idle policy](../subsystems/drivers/power-assertions-and-idle-policy.md) now covers asynchronous assertion records, DriverKit exclusion, preventer sets, idle decisions and aggressiveness propagation. Deeper KXLD relocation remains a candidate. The dispositions below preserve the historical baseline; remaining candidates must be reconciled against these explanations before adding chapters.

The [IOKit and worked-operation follow-up](first-release-expansion.md#17-iokit-queue-and-service-protocols-and-worked-operations) expands the existing queue, service-matching and notification chapters with cursor/reset/publication protocols, deferral/rematch variants and callback lifetime. New [file-mapping](../cross-cutting/mapped-file-to-arm64-fault.md) and [DMA](../cross-cutting/user-buffer-to-dma-completion.md) operations carry numeric examples and ownership through their VM/driver boundaries. These address the selected queue/service variants and cross-subsystem teaching gaps; exhaustive tests/interleavings, other power-policy combinations and KXLD relocation remain separate work.

[Complete audit](../coverage-audit.md) · [Guide index](../README.md)

The [VM/IPC complex-flow batch](first-release-expansion.md#18-vm-fault-upl-and-complex-ipc-state-transitions) implements historical V7 in [fault resolution](../subsystems/vm/fault-resolution.md#resilient-mappings-recover-selected-missing-contents-without-changing-the-file), alongside deeper top-object/copy-version retry rules. [Objects and pages](../subsystems/vm/objects-and-pages.md) now follows delayed-copy preservation and collapse/bypass through resident/compressed backing. [UPL gathering and completion](../subsystems/vm/upl-gather-and-completion.md) expands IOPL, partial ranges and vector lifetime. Remaining limits include the documented fast-gather/error-prefix unwind question, other configuration/alias/interleaving combinations and full transpose/provider behavior. The disposition tables below remain historical.

This audit covers the **42 Markdown files at the audit baseline** under `subsystems/vm` and `subsystems/drivers`: 21 in each directory, including their indexes. It evaluates the guides after the allocator, pmap, IOKit, sleep and signature expansions. It proposes work; it does not itself implement the proposed chapters or claim that the source has been exhaustively verified.

Two requested follow-ups were completed alongside the audit: [pmap translation walkthroughs](../subsystems/vm/pmap-translation-walkthroughs.md) and [DMA segment generation](../subsystems/drivers/dma-segment-walkthrough.md). Their addition does not change the historical 42-page disposition table below.

Every chapter's structure, reading role and stated limits were considered. Candidate mechanisms were checked against selected implementation bodies, configuration selections and available test sources. A reference to a function, a small interface table, or a paragraph acknowledging a subsystem was not counted as an implementation trace. Conversely, a concise introduction was not marked deficient when its linked companion already supplies the depth.

Priorities describe documentation benefit:

- **P1 — foundational:** closes a substantial gap in a common cross-subsystem route.
- **P2 — useful:** explains a distinct implemented mechanism that current chapters only mention or bound.
- **P3 — specialized:** valuable for a narrower failure mode, build configuration or implementation investigation.

The highest-value next work is the shared-region/transforming-pager path, VM copy-overwrite and mixed-page-size transfers, compressor segment/swapfile lifecycle, executable-module lifecycle, and serialized-object parsing. Another general allocation or IOKit lifecycle overview would mostly repeat existing material.

## Current strengths and what should be preserved

The VM guides already trace map intervals and range locks, fast/slow faults and relookup, object/page lifetimes, wiring and UPL ownership, and architecture-specific pmap insertion, disconnection and TLB completion. Their treatment is substantially deeper than a directory survey. [Map/fault entry guide](../subsystems/vm/maps-and-faults.md), [objects/pages](../subsystems/vm/objects-and-pages.md), [ARM mapping lifecycle](../subsystems/vm/pmap-mapping-lifecycle.md), [x86 pmap](../subsystems/vm/pmap-x86.md).

Allocator coverage is especially mature: fixed and variable type metadata, shared initial-allocation policy, finite zone assignment, heap routing, guard-object geometry, physical population, RO mutation, SMR zones, per-CPU/permanent storage and callback-backed object caches have their own mechanisms and ownership boundaries. MTE-specific physical-page management remains a separate gap; it should not trigger a rewrite of the allocation hierarchy. [Allocator route](../subsystems/vm/kernel-allocation.md), [typed isolation](../subsystems/vm/typed-allocation.md), [zone machinery](../subsystems/vm/zone-allocator.md), [special zones](../subsystems/vm/read-only-and-special-zones.md).

Driver coverage now includes actual service matching and termination, notification replay/removal, arbitration, object export/no-senders, DriverKit class and queue routing, actions, CPU memory maps, DMA preparation, interrupt sharing, workloop/timer delivery, PM acknowledgments, device transitions, system sleep and reporting. Hardware-controller and external DriverKit-runtime boundaries are usually explicit. Those are strengths to retain, not unfinished subjects to relabel as new work. [Driver reading routes](../subsystems/drivers/README.md).

The recent file-cache and signature guides also reduce adjacent gaps. A proposed transforming-pager chapter should link the existing page-validation explanation and focus on transformed backing, reuse and cleanup. It should not rederive ordinary UBC read ownership or the entire signing policy. [File-data cache](../subsystems/vfs/file-data-cache-and-read-path.md), [page validation](../subsystems/security/page-signature-validation.md).

## Disposition of every VM chapter

“Retain” means no immediate expansion is justified by this audit. “Add neighbor” preserves the current reading role and adds a separate mechanism guide. “Deepen” identifies a bounded section that can grow without changing the chapter's purpose. Candidate IDs refer to the proposals below.

| Current chapter | Disposition | Reason |
|---|---|---|
| [README](../subsystems/vm/README.md) | Retain; update navigation after approved work | Already distinguishes maps, objects, pages, pmaps and allocator layers; new mechanisms need routes rather than more overview prose. |
| [Allocator interfaces](../subsystems/vm/allocator-interfaces.md) | Retain | Concrete IOKit/BSD wrappers, C++ operators, constrained allocations and protection categories are covered; full executable loading belongs to D1. |
| [Fault resolution](../subsystems/vm/fault-resolution.md) | Deepen, V7; add neighbor V6 | Ordinary fault, COW, zero-fill, compressor fallback and pmap retry are deep. Resilient recovery and physical tag-storage ownership are explicitly bounded. |
| [Kalloc heaps and routing](../subsystems/vm/kalloc-heaps-and-routing.md) | Retain | Size classes, runtime routing, free/realloc and encoded arrays already have mechanism-level explanations. |
| [Kernel allocation](../subsystems/vm/kernel-allocation.md) | Retain | Useful entry guide to the detailed allocation family; expanding it would duplicate those chapters. |
| [Kernel virtual allocation](../subsystems/vm/kernel-virtual-allocation.md) | Retain; add neighbor V6 | Guard slots, placement, population, freeing and growth are deep. Tagged physical-page supply is a distinct lower-layer mechanism. |
| [Mapping walkthroughs](../subsystems/vm/mapping-walkthroughs.md) | Retain; later link V1/V2 | Existing end-to-end traces work as entry routes. Specialized transfers and shared-cache transformations should have dedicated destinations. |
| [Maps and faults](../subsystems/vm/maps-and-faults.md) | Retain | Intentionally concise navigation, backed by detailed maps/fault/pmap chapters. |
| [Memorystatus and freezer](../subsystems/vm/memorystatus-and-freezer.md) | Retain; add neighbors V3/V4/V5 | Candidate reservation, process references, task/map freezing and completion are already detailed. A deferred-ring drain or purge call is not an explanation of those mechanisms. |
| [Objects and pages](../subsystems/vm/objects-and-pages.md) | Add neighbors V5/V6 | Current allocation/reference/shadow/reaper coverage is useful. Purgeable transitions and tag-storage state need separate ownership models. |
| [Pagers and UPL](../subsystems/vm/pagers-and-upl.md) | Add neighbor V1 | Vnode/device pager and UPL paths are developed; shared-region/dyld pagers are not traced through setup, transformation, cache reuse and destruction. |
| [ARM64 pmap](../subsystems/vm/pmap-arm64.md) | Retain; link V1/V6 | Geometry, root identity and reverse maps are deep. Do not repeat them in shared-region or MTE chapters. |
| [Pmap mapping lifecycle](../subsystems/vm/pmap-mapping-lifecycle.md) | Retain; link V6 | Enter/protect/remove/disconnect, table lifetime and backend synchronization are already substantial. |
| [Pmap TLB and cache](../subsystems/vm/pmap-tlb-and-cache.md) | Retain | Distinguishes publication, flush completion, reuse, root switching and cache maintenance. Remaining architecture branches are specialized, not the next foundational gap. |
| [x86 pmap](../subsystems/vm/pmap-x86.md) | Retain | Four-level tables, PVs, PCIDs and distributed invalidation are covered; complete EPT/hypervisor behavior is a separately scoped project. |
| [Read-only and special zones](../subsystems/vm/read-only-and-special-zones.md) | Retain; link D3 as consumer | RO backends, SMR, per-CPU, permanent/exhaustible allocation and zcache already have their distinct lifetime rules. |
| [Reclaim and pressure](../subsystems/vm/reclaim-and-pressure.md) | Add neighbors V3/V4/V5 | Scanner/worker handoff and one compressor-slot/swap-I/O path are substantive. Segment relocation, swapfile drain, deferred rings and purgeable tokens are still missing mechanisms. |
| [Typed allocation](../subsystems/vm/typed-allocation.md) | Retain | Classification, fixed/variable grouping, startup assignment, runtime sharing and actual isolation limits are deep. |
| [Virtual address maps](../subsystems/vm/virtual-address-maps.md) | Add neighbor V2; link V7 | Remap integration is explained, but adjustment/overwrite algorithms and recovery flags are lighter than ordinary map mutation. |
| [Wiring and memory entries](../subsystems/vm/wiring-and-memory-entries.md) | Add neighbor V2/V5 | Three-stage wiring and transfer ownership are deep. Copy-overwrite is explicitly navigation-level; purgeable/ledger variants remain bounded. |
| [Zone allocator](../subsystems/vm/zone-allocator.md) | Retain | Geometry, bitmaps, CPU magazines, depot/recirculation, expansion and VA-retaining reclamation are developed. |

## Disposition of every driver chapter

| Current chapter | Disposition | Reason |
|---|---|---|
| [README](../subsystems/drivers/README.md) | Retain; update navigation after approved work | Strong route map; executable-image lifecycle and serialization need separate destinations. |
| [Bootstrap and BSD integration](../subsystems/drivers/bootstrap-and-bsd-integration.md) | Retain; add neighbor D1 | Constructor startup, device-tree import, matching and root-device handoff are detailed. Later executable loading is a distinct route. |
| [Device power state machine](../subsystems/drivers/device-power-state-machine.md) | Retain; add neighbor D4 | State order, child/parent dependencies, callouts, acknowledgments and stop are already covered; root assertion policy should not be inserted into each device step. |
| [DMA preparation and mapping](../subsystems/drivers/dma-preparation-and-mapping.md) | Retain | Backing preparation, bounce storage, mapper ownership, cursor generation and error cleanup are developed. Concrete IOMMU hardware remains outside the generic implementation. |
| [DriverKit dispatch and actions](../subsystems/drivers/driverkit-dispatch-and-actions.md) | Retain; link D2 | Queue selection, class metadata, action/reference lifecycle and kernel dispatch sources are detailed. Missing generated/user-runtime implementations are an availability boundary. |
| [Interrupt routing and command queues](../subsystems/drivers/interrupt-routing-and-command-queues.md) | Retain | Provider indexing, shared controllers, filters and queue/pool ownership are concrete. Hardware-family interrupt programming is a provider boundary. |
| [Libkern and kext runtime](../subsystems/drivers/libkern-and-kext-runtime.md) | Add neighbors D1/D2/D3/D5 | Its runtime and linking paragraphs remain a survey despite deep companions for ordinary object ownership. |
| [Memory and DMA](../subsystems/drivers/memory-and-dma.md) | Retain | Short introduction is supported by two detailed chapters and should stay navigable. |
| [Memory descriptors and CPU mappings](../subsystems/drivers/memory-descriptors-and-cpu-mappings.md) | Retain; link V5 | Buffer/sub/multi/interleaved composition, memory references and map/redirect destruction are deep; purgeability is an explicitly bounded VM interface. |
| [Object runtime and collections](../subsystems/drivers/object-runtime-and-collections.md) | Add neighbors D2/D3 | Reference/tag accounting, collection ownership, metaclass registration and instance counts are developed. Wire parsing and symbol-pool concurrency are explicitly omitted. |
| [Registry and service lifecycle](../subsystems/drivers/registry-and-service-lifecycle.md) | Retain | Deliberate entry guide with detailed registry, matching and notification companions. |
| [Registry planes and properties](../subsystems/drivers/registry-planes-and-properties.md) | Retain; link D2/D3 | Graph references, property locking, snapshots and traversal are deep. Property transport and intern-pool lifetime are adjacent mechanisms. |
| [Reporting and performance control](../subsystems/drivers/reporting-and-performance-control.md) | Retain | Reporter update/configuration locks, sample output and work-context identity have substantive traces; external performance policy is clearly bounded. |
| [Service matching and termination](../subsystems/drivers/service-matching-and-termination.md) | Retain; link D1 | Candidate/probe/start and three termination phases are explained. Executable availability and unload remain a separate object/code lifetime. |
| [Service notifications and arbitration](../subsystems/drivers/service-notifications-and-arbitration.md) | Retain | Replay, callback removal, self-callback exception, interest snapshots and owner-transfer rules are already deep. |
| [Shared data queues and notifications](../subsystems/drivers/shared-data-queues-and-notifications.md) | Retain | Both classic/circular queue publication and async-result messages are developed. Serializer graphs are not the same transport. |
| [System sleep and wake](../subsystems/drivers/system-sleep-and-wake.md) | Add neighbor D4 | Request/capability/notification/CPU handoff is deep; the full assertion and aggressiveness implementations are expressly outside it. |
| [User-client and DriverKit lifetime](../subsystems/drivers/user-client-and-driverkit-lifetime.md) | Retain; link D2 | Port export, shutdown, mapping survival and RPC descriptor ownership are deep. It calls the unserializer without explaining the decoded graph's construction and rollback. |
| [User clients and DriverKit](../subsystems/drivers/user-clients-and-driverkit.md) | Retain | Useful concise entry route into the detailed transport/lifetime/action chapters. |
| [Workloop and power protocols](../subsystems/drivers/workloop-and-power-protocols.md) | Retain | Gate/wakeup, membership, timer and callback/ack races have detailed source-backed treatment. |
| [Workloops and power](../subsystems/drivers/workloops-and-power.md) | Retain | Keep as introduction to execution, interrupt, device-PM and system-sleep guides. |

## VM expansion candidates

### V1 — P1: shared regions and transforming pagers

**Gap and current homes.** [Pagers and UPL](../subsystems/vm/pagers-and-upl.md) develops vnode/device backing, while [mapping walkthroughs](../subsystems/vm/mapping-walkthroughs.md) and [ARM pmap](../subsystems/vm/pmap-arm64.md) explain submaps/nesting. None connects shared-region selection, installation, sliding/fixups, pager reuse and lifetime. The [signature page](../subsystems/security/page-signature-validation.md) now explains validation provenance across transformation; that is not the entire transformation lifecycle.

**Source evidence.** `vm_shared_region_lookup` compares root, CPU/subtype, page-size and other identity inputs, drops the lock to create a candidate, then repeats lookup before publication. `vm_shared_region_deallocate` has persistence and delayed-destruction references. `dyld_pager_data_request` gathers absent destination pages, faults source backing, preserves busy/paging ownership across an unlocked copy/fixup interval, and cleans it up. Those are substantial missing protocols. [Lookup](../../xnu/osfmk/vm/vm_shared_region.c#L365-L445), [deallocation](../../xnu/osfmk/vm/vm_shared_region.c#L535-L608), [mapping setup](../../xnu/osfmk/vm/vm_shared_region.c#L1481), [enter](../../xnu/osfmk/vm/vm_shared_region.c#L2462), [dyld request](../../xnu/osfmk/vm/vm_dyld_pager.c#L963-L1035), [transformation](../../xnu/osfmk/vm/vm_dyld_pager.c#L1135-L1212).

**Proposed work.** Add `vm/shared-regions-and-transforming-pagers.md`. Answer: what makes two tasks reuse a region; who owns its map and pmap; how mapping/slide serialization works; which bytes and offsets identify a pager; how source and destination pages differ; how errors release UPLs and source fault state; and when cached regions/pagers survive their last mapping. Compare shared-region and dyld pagers without pretending their fixup formats are identical.

**Availability, dependencies and benefit.** Bodies are local, including [shared-region pager setup](../../xnu/osfmk/vm/vm_shared_region_pager.c#L1249), [dyld pager setup](../../xnu/osfmk/vm/vm_dyld_pager.c#L1591) and the [original shared-region note](../../xnu/doc/vm/shared_region.md). Userspace dyld/cache construction and external decryption providers remain boundaries. This builds on existing objects, UPLs, nesting and signing, and connects ordinary program launch to the VM architecture rather than adding another generic fault example.

### V2 — P1: copy-overwrite and mixed-page-size transfer

**Gap and current homes.** [Wiring and memory entries](../subsystems/vm/wiring-and-memory-entries.md) correctly covers the two `vm_map_copy` forms, selection, copyout consumption and discard. It explicitly leaves copy-overwrite at navigation depth. [Virtual address maps](../subsystems/vm/virtual-address-maps.md) explains remap extraction/installation but summarizes the transformation between source and target page geometries.

**Source evidence.** `vm_map_copy_overwrite_can_page_copy` rechecks page identity, `vo_copy` and `vo_copy_version` before allowing a physical copy. `vm_map_copy_overwrite_should_transfer_object` has policy that can reject replacing a destination with a source object, including the small-view/large-object tradeoff and malloc-backed destination restrictions. `vm_map_copy_adjust_to_target` has its own sanitizer and source/target granularity state. These are decisions beyond “copy uses COW.” [Page-copy revalidation](../../xnu/osfmk/vm/vm_map.c#L9379-L9422), [object-transfer decision](../../xnu/osfmk/vm/vm_map.c#L9541-L9630), [overwrite entry](../../xnu/osfmk/vm/vm_map.c#L10092), [target adjustment](../../xnu/osfmk/vm/vm_map.c#L16495).

**Proposed work.** Add `vm/copy-overwrite-and-remap.md`, retaining the current transfer introduction. Explain aligned entry substitution versus page/byte copying; destination preparation and submap traversal; protection changes during unlocked copying; partial progress and copy consumption on failure; mixed-granule trim/overmap decisions; and legacy versus return-data-address remap outputs. Include an existing-destination overwrite example and a 4 KiB/16 KiB geometry example with explicit prerequisites.

**Availability, dependencies and benefit.** Implementation and [copy tests](../../xnu/tests/vm/vm_copy_overwrite.c), [unaligned protection-race test](../../xnu/tests/vm/vm_unaligned_copy_protection_race.c), [map-switch race test](../../xnu/tests/vm/vm_unaligned_copy_switch_race.c) and [remap configurator](../../xnu/tests/vm/configurator_vm_remap.c) are local. Test presence is evidence of useful cases, not evidence they pass in this environment. This chapter depends on range locking, COW and IPC OOL ownership already documented, and clarifies what a receive overwrite or cross-map transfer actually preserves.

### V3 — P1: compressor segment movement and swapfile lifecycle

**Gap and current home.** [Reclaim and pressure](../subsystems/vm/reclaim-and-pressure.md) already explains object slots, repeated-value pages, `C_KEEP`/`C_DONT_BLOCK`, swap reservation and asynchronous completion. Its compaction description is short, and it expressly excludes swapfile creation, GC and trimming. Repeating the put/get overview would not close the gap.

**Source evidence.** `c_seg_minor_compaction_and_unlock` starts with segment busy ownership, can release the segment lock while rearranging contents, and distinguishes empty-segment freeing from packing. Major coalescing and state queues are separate operations. `vm_swap_reclaim` chooses a ready swapfile under `vm_swap_data_lock`, clears `SWAP_READY`, sets reclaim state, coordinates delayed trims and waits for outstanding I/O before proceeding. [Minor compaction](../../xnu/osfmk/vm/vm_compressor.c#L2253), [coalescing](../../xnu/osfmk/vm/vm_compressor.c#L2475), [state changes](../../xnu/osfmk/vm/vm_compressor.c#L1779), [swapfile reclamation](../../xnu/osfmk/vm/vm_compressor_backing_store.c#L2165-L2237), [delayed trim](../../xnu/osfmk/vm/vm_compressor_backing_store.c#L2046).

**Proposed work.** Add `vm/compressor-segments-and-swapfiles.md`. Track slot locators when bytes/segments move; segment lock versus busy ownership; minor versus major compaction; queue eligibility and swap-in races; swapfile admission/creation/reclamation; slot trim versus reuse; failed I/O; and the distinction between original page count, compressed occupancy and actual storage space.

**Availability, dependencies and benefit.** Core mechanisms and [swapfile creation](../../xnu/osfmk/vm/vm_compressor_backing_store.c#L1565) are present. Compressor, ordinary swap and freezer swap are separately selected by the [VM configuration predicates](../../xnu/osfmk/vm/vm_pageout.h#L227). [Compressor tests](../../xnu/tests/vm/vm_compressor.c#L22) include target/development-restricted configuration and introspection checks; they are not comprehensive compaction-race tests. Storage/filesystem behavior remains external to the compressor algorithm. The chapter would complete the backing-storage part of faults, reclamation and freezing without redoing process-selection policy.

### V4 — P2: deferred-reclamation ring and task lifetime

**Gap and current homes.** [Memorystatus/freezer](../subsystems/vm/memorystatus-and-freezer.md) mentions draining deferred reclamation before freeze, while [map removal](../subsystems/vm/virtual-address-maps.md) explains immediate removal. Neither explains the shared user/kernel ring that postpones those operations.

**Source evidence.** `reclaim_chunk` reads head/tail/busy through copy I/O, validates their relationship, publishes a busy range, fences and rereads tail before processing. It distinguishes cancellation, guard failures, deallocation and `VM_BEHAVIOR_REUSABLE`; that last behavior does not immediately remove the virtual range. `vm_deferred_reclamation_task_drain` retains metadata under the task lock, then obtains separate reclamation ownership outside it. [Ring protocol](../../xnu/osfmk/vm/vm_reclaim.c#L987-L1080), [entry actions and completion](../../xnu/osfmk/vm/vm_reclaim.c#L1160-L1240), [task drain/fork](../../xnu/osfmk/vm/vm_reclaim.c#L1840-L1899).

**Proposed work.** Add `vm/deferred-reclamation.md`: allocation/mapping of the ring; producer cancellation versus kernel busy reservation; copy faults and partial publication; metadata lock versus owner protocol; accounting and working-set sampling; suspend/freezer/pressure drains; fork/resize/teardown; and why reported reclaimed bytes are not necessarily immediately freed physical memory.

**Availability, dependencies and benefit.** The file is selected by [CONFIG_DEFERRED_RECLAIM](../../xnu/osfmk/conf/files#L312); the [option](../../xnu/config/MASTER#L373) and both [ARM64](../../xnu/config/MASTER.arm64#L69) and [x86 VM feature groups](../../xnu/config/MASTER.x86_64#L64) are visible. [Tests](../../xnu/tests/vm/vm_reclaim.c#L54) include enabled/disabled registration, entry actions and suspension paths. Production userspace allocator decisions are not reconstructed from the kernel ring alone. This connects map removal, task lifetime and pressure without conflating deferred free with pageout.

### V5 — P2: purgeable objects, aging tokens and owner accounting

**Gap and current homes.** [Objects/pages](../subsystems/vm/objects-and-pages.md), [reclaim](../subsystems/vm/reclaim-and-pressure.md), [memory entries](../subsystems/vm/wiring-and-memory-entries.md) and [driver CPU mappings](../subsystems/drivers/memory-descriptors-and-cpu-mappings.md) mention purgeability or its API boundary. They do not develop the state machine that allows contents to disappear while object identity remains.

**Source evidence.** `vm_object_purgable_control` requires the object lock, rejects denied/kernel-only transitions where applicable, and asserts that purgeable objects do not use delayed copies. `vm_purgeable_object_purge_one` combines page-queue locking, token ripeness, queue/group selection and object try-locking. The object-selection helper can skip locked candidates and consider owner importance. [Control](../../xnu/osfmk/vm/vm_object.c#L6156-L6204), [selection](../../xnu/osfmk/vm/vm_purgeable.c#L672-L733), [purge-one](../../xnu/osfmk/vm/vm_purgeable.c#L884-L971), [actual purge](../../xnu/osfmk/vm/vm_object.c#L5959).

**Proposed work.** Add `vm/purgeable-memory.md`. Explain NONVOLATILE/VOLATILE/EMPTY transitions, returned previous state, FIFO/LIFO groups and tokens, lock acquisition/skips, compressed backing, ownership/disowning and ledger effects. Compare purgeable memory with reusable pages, deferred deallocation and ordinary clean-file reclaim. Trace one named-memory-entry or IOKit caller into the common VM protocol.

**Availability, dependencies and benefit.** Bodies and [footprint tests](../../xnu/tests/vm_phys_footprint.c#L416), including [ownership cases](../../xnu/tests/vm_phys_footprint.c#L534), are local. App cache reconstruction policy and concrete external driver ownership choices are not. This is a useful bridge between memory APIs, reclaim decisions and the footprint charged to a task; it should build on existing object lifetime rather than replace it.

### V6 — P2: MTE tag-storage pages and reclamation

**Gap and current homes.** [Objects/pages](../subsystems/vm/objects-and-pages.md), [kernel virtual allocation](../subsystems/vm/kernel-virtual-allocation.md) and [fault resolution](../subsystems/vm/fault-resolution.md) identify MTE-dependent paths but do not explain how physical tag storage is supplied or reclaimed. Existing typed-allocation isolation is a different mechanism.

**Source evidence.** `mteinfo_tag_storage_activate_locked` drops the free-page lock, retypes tag-storage pages, wires them under object/page-queue locks, then reacquires the free lock and recomputes how many covered pages became taggable. Deactivation has a cross-CPU barrier, and `mteinfo_page_list_fix_tagging` batches pmap tagging/untagging while managing per-CPU suspension state. [Activation](../../xnu/osfmk/vm/vm_mteinfo.c#L1690-L1774), [deactivation barrier](../../xnu/osfmk/vm/vm_mteinfo.c#L1913-L1966), [allocation-list adjustment](../../xnu/osfmk/vm/vm_mteinfo.c#L2992-L3026).

**Proposed work.** Add `vm/mte-tag-storage-and-page-lifecycle.md`. Define tag-storage cells, covered physical pages, state lists/buckets and tagged versus regular allocation classes; explain reserve/refill/reclaim workers, activation publication, temporary inability to deactivate, wiring and compressor interactions. Trace a tagged page becoming an ordinary allocation and the lifetime of its former tag backing.

**Availability, dependencies and benefit.** This is guarded by [HAS_MTE](../../xnu/osfmk/vm/vm_mteinfo.c#L53), with local [cell/list policy tests](../../xnu/tests/vm/vm_mteinfo.c#L523), [reclamation tests](../../xnu/tests/vm/vm_mte_reclamation.c) and [compression tests](../../xnu/tests/arm_mte_compress.c). Architectural policy, exception handling and monitor enforcement should remain linked to the platform/security guides; hardware and external SPTM internals cannot be inferred from VM calls. Benefit: explains otherwise opaque memory-class branches throughout allocation, pageout and I/O.

### V7 — P3: resilient mapping and fault recovery

**Gap and current homes.** [Fault resolution](../subsystems/vm/fault-resolution.md) explicitly surveys resilient media rather than tracing it. [Mapping walkthroughs](../subsystems/vm/mapping-walkthroughs.md) describes ordinary file-backed behavior; its normal error model should not silently stand in for a resilient mapping.

**Source evidence.** BSD rejects selected resilient/signing flag combinations and historically strips `MAP_RESILIENT_MEDIA` from shared mappings. The fault retry preserves the failed object/offset and rechecks that the map still names them with resilience enabled before injecting a zero-filled top-object page; otherwise it releases the extra reference and restarts. [Flag handling](../../xnu/bsd/kern/kern_mman.c#L426-L465), [retry identity check](../../xnu/osfmk/vm/vm_fault.c#L5124-L5170).

**Proposed work.** Deepen `fault-resolution.md` with a bounded resilient-recovery section and a small flag/API link from `virtual-address-maps.md`. Answer which failures trigger recovery, how failed backing remains referenced across retry, why private top-object recovery matters, how signing resilience differs from media resilience, and what a concurrent remap/protection change does to the retry.

**Availability, dependencies and benefit.** [Media and COW tests](../../xnu/tests/vm/mmap_resilient_media.c#L57) are present, including a [separate COW scenario](../../xnu/tests/vm/mmap_resilient_media.c#L251). Fault injection is configuration-sensitive; test presence does not establish every media failure is recoverable. This is a specialized completion of the existing fault chapter, dependent on its ordinary retry/COW explanation and the signature-policy guide.

## Driver expansion candidates

### D1 — P1: executable-module load, dependencies, kernel collections and unload

**Gap and current homes.** [Libkern/kext runtime](../subsystems/drivers/libkern-and-kext-runtime.md) summarizes start/unload and kernel collections in a few paragraphs. [Object runtime](../subsystems/drivers/object-runtime-and-collections.md) develops metaclass registration and instance accounting, and [bootstrap](../subsystems/drivers/bootstrap-and-bsd-integration.md) develops initialization, but neither supplies the later module transaction.

**Source evidence.** `OSKext::load` has exclusion/loadability and already-loaded gates plus configuration-sensitive MAC entry. `resolveDependencies` detects graph loops and tracks dependency state. `unload` separately tests enablement, retains, loaded/module kind and class removal, then marks unloading before calling code that may belong to the module. Fileset/KC entry points are distinct from runtime linking. [Load](../../xnu/libkern/c++/OSKext.cpp#L6483-L6545), [dependencies](../../xnu/libkern/c++/OSKext.cpp#L9487-L9545), [unload](../../xnu/libkern/c++/OSKext.cpp#L8645-L8732), [fileset loading](../../xnu/libkern/c++/OSKext.cpp#L13203), [KC loading](../../xnu/libkern/c++/OSKext.cpp#L13514).

**Proposed work.** Add `drivers/kext-loading-and-unloading.md`: executable discovery/availability, dependency graph references, load/start/matching differences, C++ initialization failure, module start/stop errors, autounload eligibility, pending callback/resource requests, personality publication and executable/account teardown. Show why service detach, last object destruction and code unload are different events.

**Availability, dependencies and benefit.** XNU-side bodies are local. Kernel-collection production, external daemon policy, complete authorization providers and actual extension binaries remain outside this source trace. Runtime linking must be gated by [CONFIG_KXLD](../../xnu/config/MASTER#L541), not assumed for every target. The chapter connects existing service and metaclass lifetimes to the code they call. D5 can follow later; linker relocation internals need not block this lifecycle explanation.

### D2 — P1: serialized object graphs and parser ownership

**Gap and current homes.** [Object runtime](../subsystems/drivers/object-runtime-and-collections.md) describes serializer identity but excludes binary format/parser validation. [Registry properties](../subsystems/drivers/registry-planes-and-properties.md) covers in-kernel ownership, and [DriverKit lifetime](../subsystems/drivers/user-client-and-driverkit-lifetime.md) describes OOL copy conversion; neither traces construction and cleanup of the decoded graph.

**Source evidence.** `OSUnserializeBinary` validates transport alignment/signature, tracks a separate object table and collection stack, handles backward object references and string/symbol/data representations, installs children into retaining containers, and releases the temporary object table on both success and failure. Actual users include matching requests and DriverKit OOL object import. [Parser setup](../../xnu/libkern/c++/OSSerializeBinary.cpp#L347-L422), [reference/value decoding](../../xnu/libkern/c++/OSSerializeBinary.cpp#L448-L514), [construction and release](../../xnu/libkern/c++/OSSerializeBinary.cpp#L520-L636), [matching caller](../../xnu/iokit/Kernel/IOUserClient.cpp#L2666), [DriverKit caller](../../xnu/iokit/Kernel/IOUserServer.cpp#L3969).

**Proposed work.** Add `drivers/serialization-and-property-transport.md`. Explain XML versus binary/indexed dispatch; key/type/length encoding; object identity and permitted reference graphs; collection depth and growth limits; dictionary-key conversion; ownership of newly created versus referenced objects; error cleanup; and parsing versus later method/property authorization. Include one serialized graph with shared children and one malformed-input cleanup trace. This is documentation of checks and contracts, not an assertion of parser security.

**Availability, dependencies and benefit.** Binary bodies, [XML grammar](../../xnu/libkern/c++/OSUnserializeXML.y#L35) and the checked-in [generated shared XML implementation](../../xnu/libkern/libkern/c++/OSUnserializeXMLSharedImplementation.h) are available. That differs from absent DriverKit IIG-generated/runtime bodies. No focused comprehensive parser test suite was identified in this bounded audit; do not imply one was run. Benefit: connects reference-counted collections to actual external byte transport and closes a trust-boundary gap without repeating Mach descriptor ownership.

### D3 — P2: symbol interning, no-copy storage and SMR destruction

**Gap and current homes.** [Libkern/kext runtime](../subsystems/drivers/libkern-and-kext-runtime.md) gives `OSSymbol` a short survey. [Object runtime](../subsystems/drivers/object-runtime-and-collections.md) explains ordinary objects, and [special zones](../subsystems/vm/read-only-and-special-zones.md) explains generic SMR allocation; neither develops this heavily used concrete intern pool.

**Source evidence.** `OSSymbolPool::findSymbol` distinguishes SMR lookup from the huge-string locked route and copies a potentially faulting key before the SMR access. `withCString` races lookup against insertion and has a restricted permanent/no-copy optimization. `free` removes hash identity and uses SMR release; `smr_free` releases string storage and class accounting at reuse time, deliberately avoiding ordinary tracking cleanup. [Lookup](../../xnu/libkern/c++/OSSymbol.cpp#L199-L240), [creation](../../xnu/libkern/c++/OSSymbol.cpp#L438-L492), [destruction](../../xnu/libkern/c++/OSSymbol.cpp#L618-L668).

**Proposed work.** Add a substantial `OSSymbol` section to `object-runtime-and-collections.md`, or a focused `drivers/symbol-interning.md` if it becomes long. Explain successful try-retain during lookup, duplicate-insertion ownership, huge-string exceptions, pool growth/shrink, no-copy backing lifetime, permanent symbols and grace-period-delayed cleanup. Keep mutable `OSString`/`OSData` ownership contrasts narrow.

**Availability, dependencies and benefit.** Implementation and a [sysctl-driven symbol test](../../xnu/tests/iokit/ossymbol.c#L27) are local. Integrity configuration controls the permanent optimization; it is not a universal string rule. This is a useful worked consumer of the already documented SMR/zone mechanisms and clarifies dictionary keys, class names and registry identities.

### D4 — P2: power assertions, preventers and aggressiveness propagation

**Gap and current homes.** [System sleep](../subsystems/drivers/system-sleep-and-wake.md) explicitly bounds full assertion policy, while [device PM](../subsystems/drivers/device-power-state-machine.md) follows requested/current states and parent limits. Those routes do not explain the retained assertions and asynchronously propagated policy inputs that keep the system awake or modify idling.

**Source evidence.** Assertion creation/release/level changes are separate operations. `PMAssertionsTracker::tabulate` aggregates active kernel bits, combines user bits and calls policy evaluation only when the result changes. `setAggressiveness` coalesces queued requests under a separate lock, preserves special quick-spindown handling, and labels even its synchronous option as not truly synchronous. [Assertion APIs](../../xnu/iokit/Kernel/IOPMrootDomain.cpp#L11010-L11097), [aggregation](../../xnu/iokit/Kernel/IOPMrootDomain.cpp#L11886-L11925), [aggressiveness queue](../../xnu/iokit/Kernel/IOPMrootDomain.cpp#L2313-L2380), [preventer updates](../../xnu/iokit/Kernel/IOPMrootDomain.cpp#L3516).

**Proposed work.** Add `drivers/power-assertions-and-idle-policy.md`. Trace assertion IDs, owner/string lifetimes, request-to-gate publication, level/release cleanup, kernel/user aggregate changes and their effect on idle/demand sleep. Compare assertions with service preventer sets, wake-preventing state and aggressiveness broadcasts; explain joining/removing a recipient and coalesced update completion.

**Availability, dependencies and benefit.** Root-domain machinery is local. Userspace powerd policy, battery/thermal controllers and product-specific decisions are not derived from the generic tracker. No assertion-policy workload was run or identified as sufficient to validate the full matrix. This extends existing PM mechanisms upstream, rather than repeating callback acknowledgments or CPU sleep/resume.

### D5 — P3: KXLD relocation and C++ compatibility

**Gap and current home.** [Libkern/kext runtime](../subsystems/drivers/libkern-and-kext-runtime.md) explicitly calls its linker treatment an entry-path survey. D1 would explain image lifetime but still not show how symbols, sections, relocations and vtables become a linked executable.

**Source evidence.** `kxld_link_file` initializes dependency/context objects, obtains an output allocation, relocates using symbol/vtable dictionaries, exports the linked image and frees the allocation on failure. Mach-O object ingestion and vtable patching are local implementations, not unavailable provider calls. [Link transaction](../../xnu/libkern/kxld/kxld.c#L363-L438), [object ingestion](../../xnu/libkern/kxld/kxld_object.c#L215), [relocation](../../xnu/libkern/kxld/kxld_kext.c#L413), [vtable patching](../../xnu/libkern/kxld/kxld_vtable.c#L483).

**Proposed work.** Add `drivers/kxld-linking.md` after D1. Trace one supported target from Mach-O sections/symbols through undefined-symbol resolution, relocation, superclass/vtable compatibility, output image ownership and rollback. Enumerate architecture/build branches actually inspected rather than claiming all relocation encodings were audited.

**Availability, dependencies and benefit.** [Kernel source selection](../../xnu/libkern/conf/files#L117-L134) is conditional on `config_kxld`. The [separate library Makefile](../../xnu/libkern/kxld/Makefile#L1-L3) is not the regular kernel build. Local [array](../../xnu/libkern/kxld/tests/kxld_array_test.c) and [dictionary](../../xnu/libkern/kxld/tests/kxld_dict_test.c) tests exist, but the [load script](../../xnu/libkern/kxld/tests/loadtest.py#L29-L60) uses legacy i386/kext tooling and must not be presented as a modern target test recipe. This is valuable for linker investigations, lower priority than module lifecycle on configurations that do not runtime-link extensions.

## Recommended sequence and boundaries

Start with V1/V2 and D1/D2. They close missing paths between already strong chapters and produce useful traces for a reader following a program, cross-map operation or driver request. V3 then completes the backing-store lifetime behind reclamation. V4/V5 can be developed together because the important comparison is deferred removal, reusable contents and purgeable-object state; their APIs and ownership protocols must still remain separate.

V6 should coordinate with the platform/security audit so VM tag-storage state is not confused with process MTE policy or external monitor enforcement. D3 is a compact concrete SMR consumer. D4 follows the existing PM guides. V7 and D5 are bounded specialist work.

This audit does **not** recommend expanding another general pmap, zone/type-isolation, workloop, notification, DMA or device-PM chapter merely because some optional branches remain. Nor does it count external IOMMU/hardware drivers, missing DriverKit user-runtime code, complete userspace dyld behavior, monitor internals or filesystem-specific persistence as locally documentable implementations.

Other acknowledged limits—B+tree balancing, every object-collapse case, contiguous physical-page search, all sanitizer policies, every queue/reset variant and every collection class—remain possible later work. They are not prioritized here ahead of the twelve concrete gaps. A follow-up expansion should first check whether a neighboring subsystem guide has gained that material.

## Audit verification and limits

The disposition tables enumerate all Markdown files in the two owned subsystem directories, including short introductions and indexes. The candidate evidence was checked in the cited source bodies; build selectors and tests were inspected selectively to distinguish available implementation from assumed product behavior. No kernel, kext, parser, hardware transfer, pressure workload or test binary was executed.

The checked-in tests provide reading cases and possible future validation routes, not current passing results. External SDKs, entitlements, development kernels, architecture support and legacy tooling can affect whether they can run. This audit is complete as a chapter inventory and prioritized gap assessment, not as an exhaustive source or concurrency audit.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
