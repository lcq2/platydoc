# libkern objects, executable runtime, and supporting libraries

[Subsystem overview](README.md) · [Kernel allocation](../vm/kernel-allocation.md) · [Service matching](registry-and-service-lifecycle.md)

For the detailed lifetime trace, read [object runtime and collections](object-runtime-and-collections.md): construction versus initialization, tagged collection references, copy depth, iterator invalidation, and metaclass registration and unload pins.

## OSObject ownership underlies IOKit

`OSObject` provides reference counting, dynamic class identification, serialization, and explicit initialization/free hooks. `retain` and `release` delegate to tagged operations. The reference-count update is atomic, with separate accounting for collection-held references; final release marks the object as being freed before calling its virtual `free`. Overflow is handled specially rather than allowed to wrap into an accidental free. This protects reference-count transitions, not the object's arbitrary mutable fields. [`taggedTryRetain`](../../../xnu/libkern/c++/OSObject.cpp#L108), [`taggedRelease`](../../../xnu/libkern/c++/OSObject.cpp#L166).

Subclass cleanup normally releases acquired resources in `free` and calls the superclass implementation. The base removes the instance from metaclass accounting and deletes the object. `init` is an explicit success/failure step; allocation, initialization, attachment, and publication remain separate operations. Traces in `IOService::probeCandidates` and `newUserClient` demonstrate why every failed step needs its own release or detach path. [`OSObject::free`](../../../xnu/libkern/c++/OSObject.cpp#L399), [`newUserClient` cleanup](../../../xnu/iokit/Kernel/IOService.cpp#L8205).

The tree includes both raw pointers with manual retains and `OSSharedPtr`/`OSPtr` ownership wrappers. `OSRetain` takes another reference; `OSNoRetain` adopts an already-owned reference. Conversion helpers preserve that distinction, including move-like conversions that detach the old wrapper. A returned `getObject` pointer and an owned `with...` result must not be treated interchangeably. [`OSSharedPtr` ownership aliases and conversion helpers](../../../xnu/libkern/libkern/c++/OSSharedPtr.h#L60).

Allocation is also part of this runtime. `OSObject::operator new` uses a zeroed kernel heap allocation with libkern accounting. The typed path uses `kalloc_type_impl_external` when the object fits its registered type view, with a fallback for subclass layouts that do not use the expected class macros. IOKit's `IOMalloc` wrappers similarly delegate to kernel heaps; `IOMallocType` builds a typed allocation view. These are front ends to the [VM allocation subsystem](../vm/kernel-allocation.md), not independent physical-memory allocators. [`operator new`](../../../xnu/libkern/c++/OSObject.cpp#L295), [`IOMalloc_internal`](../../../xnu/iokit/Kernel/IOLib.cpp#L280), [`IOMallocType`](../../../xnu/iokit/IOKit/IOLib.h#L384).

The [allocator interface trace](../vm/allocator-interfaces.md) follows those macros, typed/external fallbacks, optional tracking headers and matching frees. The [type-isolation chapter](../vm/typed-allocation.md) explains how compiler metadata reaches startup zone/heap assignment; a class name or separate accounting tag alone does not establish exclusive storage.

## Collections own objects but do not supply universal synchronization

`OSArray::setObject` grows storage, updates the collection stamp, and retains the inserted object. Removal moves the owned reference into a temporary, shifts later entries, and lets the removed reference be released. The collection therefore keeps an element alive even when the inserter drops its own reference. Other containers support different indexing and ordering, but their ownership contracts must still be followed. [`OSArray::setObject`](../../../xnu/libkern/c++/OSArray.cpp#L247), [`removeObject`](../../../xnu/libkern/c++/OSArray.cpp#L340).

`OSCollectionIterator::isValid` compares the collection's update stamp with the stamp captured for iteration. `getNextObject` returns null if that validity check fails. This catches structural modification; it is not a lock that makes concurrent mutation safe. The registry, catalogue, workloop, and individual drivers provide their own surrounding lock domains. [`isValid`](../../../xnu/libkern/c++/OSCollectionIterator.cpp#L100), [`getNextObject`](../../../xnu/libkern/c++/OSCollectionIterator.cpp#L316).

`OSSymbol` supplies shared symbols for class names and dictionary keys. Its current pool uses a specialized symbol lookup path, and `withCString` first checks for an existing symbol. Read-only kernel strings can receive a permanent/no-copy optimization under relevant integrity configurations. Do not assume every apparent string allocation creates a fresh private byte array. [`OSSymbol::withCString`](../../../xnu/libkern/c++/OSSymbol.cpp#L438).

## Metaclasses connect a name to an allocatable class

IOKit class macros create metaclass information used for runtime casts, superclass traversal, instance accounting, and named allocation. `OSMetaClass::allocClassWithName` takes a class reference, calls its allocator, and releases the class reference. This is exactly the bridge from an `IOClass` personality string to the candidate object used by service matching. [`allocClassWithName`](../../../xnu/libkern/c++/OSMetaClass.cpp#L1285), [`probeCandidates`](../../../xnu/iokit/Kernel/IOService.cpp#L3851).

Class registration is coordinated with executable initialization. `preModLoad` holds the stalled-class lock and creates a list for classes whose constructors run during this load. `postModLoad` checks that registration succeeded, handles class dictionaries, associates classes with their `OSKext`, and rejects conflicts. The lock spans the registration interval; this is not an unconstrained global dictionary insertion performed by arbitrary constructors. [`preModLoad`](../../../xnu/libkern/c++/OSMetaClass.cpp#L780), [`postModLoad`](../../../xnu/libkern/c++/OSMetaClass.cpp#L818).

## Bootstrap and kext start are different levels

`InitIOKit` establishes IOLib, invokes `OSlibkernInit`, initializes object-port support, constructs the platform expert device, and attaches it as the root nub. `OSlibkernInit` initializes the metaclass base and runs `OSRuntimeInitializeCPP(NULL)` for the kernel. The post-constructor initialization function initializes registry, service, catalogue, OSKext, user-client and memory-descriptor machinery. `StartIOKitMatching` later asks the root nub to begin matching. Keep these distinct when following boot. [`InitIOKit`](../../../xnu/iokit/Kernel/IOStartIOKit.cpp#L131), [`OSlibkernInit`](../../../xnu/libkern/c++/OSRuntime.cpp#L137), [`iokit_post_constructor_init`](../../../xnu/iokit/Kernel/IOStartIOKit.cpp#L91), [`StartIOKitMatching`](../../../xnu/iokit/Kernel/IOStartIOKit.cpp#L178).

`OSRuntimeInitializeCPP` chooses the correct Mach-O header and constructor/finalizer sections, including a distinct built-in-kext case. It brackets constructor invocation with `preModLoad` and `postModLoad`; failures trigger appropriate finalizers or C++ runtime cleanup. This runtime setup makes a kext's classes available, but it is different from starting each service instance that those classes may later create. [`OSRuntimeInitializeCPP`](../../../xnu/libkern/c++/OSRuntime.cpp#L439).

`OSKext::start` checks executable state and load policy, validates mapping, starts dependencies when allowed, initializes the kext's C++ runtime, and calls its module start function. `OSKext::unload` checks unload eligibility and class instances before stopping and tearing down executable state. A detached service with surviving object instances can still prevent unloading its code: instance lifetime must outlast every virtual call into that executable. [`OSKext::start`](../../../xnu/libkern/c++/OSKext.cpp#L8389), [`OSKext::unload`](../../../xnu/libkern/c++/OSKext.cpp#L8645).

## Linking and kernel collections are configuration-dependent

`OSKext.cpp` contains both legacy/runtime-linking machinery and kernel-collection paths. `loadExecutable` contains a `CONFIG_KXLD` branch that calls the in-tree linker. `loadFileSetKexts` and `loadKCFileSet` are separate entry points for collection loading. The existence of the linker source does not mean each target dynamically links arbitrary kext files at runtime. Policy and compiled configuration determine which operations are available. [`loadExecutable`](../../../xnu/libkern/c++/OSKext.cpp#L7178), [`loadFileSetKexts`](../../../xnu/libkern/c++/OSKext.cpp#L13203), [`loadKCFileSet`](../../../xnu/libkern/c++/OSKext.cpp#L13514).

At the inspected KXLD entry boundary, `kxld_link_file` initializes the context and dependency objects, allocates the linked image, relocates it using symbol and vtable dictionaries, and exports the linked object and `kmod_info` address. Lower-level object, symbol, section, relocation and vtable modules implement those transformations. This was an entry-path survey; architecture-specific relocation validity and every C++ compatibility rule were not audited. [`kxld_link_file`](../../../xnu/libkern/kxld/kxld.c#L363), [`kxld_object.c`](../../../xnu/libkern/kxld/kxld_object.c), [`kxld_reloc.c`](../../../xnu/libkern/kxld/kxld_reloc.c), [`kxld_vtable.c`](../../../xnu/libkern/kxld/kxld_vtable.c).

## Useful supporting areas

| Area | Why it appears in a driver trace | Reading boundary |
| --- | --- | --- |
| [`IOLocks.cpp`](../../../xnu/iokit/Kernel/IOLocks.cpp) | Sleep/wakeup and recursive-lock adapters used by gates and driver locks | Follow into kernel lock primitives when wait semantics matter. |
| [`IOSharedDataQueue.cpp`](../../../xnu/iokit/Kernel/IOSharedDataQueue.cpp#L219) | Shared memory plus Mach notification for event delivery | `enqueue` validates indices, writes data, publishes the tail with release ordering, and notifies on an empty-to-nonempty observation. Do not infer arbitrary multi-producer support. |
| [`OSSerialize.cpp`](../../../xnu/libkern/c++/OSSerialize.cpp), [`OSSerializeBinary.cpp`](../../../xnu/libkern/c++/OSSerializeBinary.cpp), [`OSUnserializeXML.cpp`](../../../xnu/libkern/c++/OSUnserializeXML.cpp) | Property transport and object-graph encoding | Surveyed as supporting code, not a parser/security audit. |
| [`libkern/os`](../../../xnu/libkern/os) | Atomic/refcount utilities, logging, tracing and event logs | Used throughout XNU, not confined to IOKit. |
| [`bounded_ptr.h`](../../../xnu/libkern/libkern/c++/bounded_ptr.h), [`safe_allocation.h`](../../../xnu/libkern/libkern/c++/safe_allocation.h) | C++ allocation and bounds-oriented utility types | Separate from `OSObject` retain counting. |
| [`compression.c`](../../../xnu/libkern/compression/compression.c), [`register_crypto.c`](../../../xnu/libkern/crypto/register_crypto.c) | Registration of compression and cryptographic function interfaces | These boundaries install function tables; they are not evidence that all providers or algorithms live in these files. |

For a practical source-reading exercise, follow a personality's `IOClass` through named allocation, `init`, a collection insertion, `attach`, `start`, and failure cleanup. That one path connects class registration, object ownership, registry references, and executable lifetime without requiring the reader to begin inside the linker.
