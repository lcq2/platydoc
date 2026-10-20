# Platform services, power, and shared interfaces

[Platform overview](README.md) · [Boot path](boot.md) · [CPU power lifecycle](cpu-power-lifecycle.md)

## Platform Expert connects early data to later drivers

ARM `PE_init_platform(FALSE, args)` copies boot display/device-tree information into `PE_state`, initializes the flattened-tree reader, and identifies the machine. Its later `TRUE` call initializes platform interrupts. `PE_slide_devicetree()` adjusts the stored pointer and reinitializes the reader after a mapping slide. This is why an early device-tree pointer cannot simply be cached across all boot phases without understanding the mapping transition. [`pexpert/arm/pe_init.c`](../../../xnu/pexpert/arm/pe_init.c#L427).

`SecureDTInit()` stores the root, size, and end after checking overflow. Lookup traverses the flattened structure; property access validates headers, lengths, and region bounds before returning a pointer and size into the tree. It does not create a separately owned property buffer. Consumers must interpret the property's actual representation and validate its expected size. For example, ARM initialization reads `/chosen` DRAM properties separately from the kernel-managed memory range. [`device_tree.c`, initialization](../../../xnu/pexpert/gen/device_tree.c#L236), [`property access`](../../../xnu/pexpert/gen/device_tree.c#L598), [`DRAM inputs`](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1006).

The early flattened tree becomes input to the I/O Kit root nub, but it is not interchangeable with the full runtime I/O Registry. `InitIOKit()` constructs `IOPlatformExpertDevice` from that data; service matching and registry lifecycle proceed through I/O Kit. Consult [drivers](../drivers/README.md) for those objects rather than extending the raw device-tree reader into a model of all runtime device discovery. [`IOStartIOKit.cpp`](../../../xnu/iokit/Kernel/IOStartIOKit.cpp#L134).

Several `PE_*` CPU functions are implemented in `IOCPU.cpp`, not `pexpert/`. `PE_cpu_start_internal()` casts the platform CPU identifier to an `IOCPU` and calls `startCPU()`; signal, initialization, and quiesce wrappers call the corresponding methods. The machine layer prepares CPU state, while the platform CPU implementation performs hardware-specific operations. Nearby public wrappers such as `PE_cpu_start_from_kext()` and `PE_cpu_halt()` deliberately panic as unimplemented: follow the actual caller, not only an attractive API name. [`IOCPU.cpp`](../../../xnu/iokit/Kernel/IOCPU.cpp#L90), [`cpu_start()`](../../../xnu/osfmk/arm64/cpu.c#L898).

## Sleep and resume cross the same machine boundaries

Power-management policy belongs primarily to [I/O Kit power management](../drivers/README.md). The machine path sees its result as CPU quiescing, saved state, hardware sleep, and restoration. ARM64 `cpu_sleep()` records the active thread and architecture-specific reset handler, marks `SleepState`, stops configured counter/timer facilities, cleans caches, and calls platform quiesce/down logic. Whether this is system sleep or taking a CPU offline affects the path. [`cpu.c`](../../../xnu/osfmk/arm64/cpu.c#L315).

`ml_arm_sleep()` coordinates the last stage. The boot CPU waits for other CPUs' sleep tokens, captures `wake_abstime`, and sets its own token. `WITH_CLASSIC_S2R` adds a firmware-visible suspend signature; other hardware follows its configured reset route. Conditional hibernation can write an image and request poweroff. The remaining path drains serial output and enters architecture sleep preparation. This code runs in a constrained execution context, not as an arbitrary sleepable worker callback. [`cpu.c`](../../../xnu/osfmk/arm64/cpu.c#L1024).

```mermaid
flowchart LR
    PM[Driver power policy] --> Quiesce[CPU quiesce / cpu_sleep]
    Quiesce --> Last[ml_arm_sleep: all CPUs ready]
    Last --> Image[Optional hibernate_write_image]
    Last --> HW[Hardware sleep]
    Image --> HW
    HW --> Entry[Reset / monitor warm entry]
    Entry --> Init[arm_init_cpu: state, clocks, interrupts]
    Init --> Runtime[secondary_cpu_main / scheduler resume]
```

The diagram shows the XNU-side boundaries; firmware and monitor restore implementation are not present here. `arm_init_cpu()` clears sleep state, restores the thread association, initializes machine/timebase/interrupt facilities, resets timer deadlines, and re-enters common CPU startup. Hibernation branches restore timing information from the image header. `cpu_timebase_init()` rebases the hardware counter on system wake so `mach_absolute_time()` excludes sleep even if the underlying counter continued or reset. Continuous-time offsets are handled separately. [`legacy resume`](../../../xnu/osfmk/arm/arm_init.c#L700), [`SPTM resume`](../../../xnu/osfmk/arm64/sptm/arm_init_sptm.c#L1155), [`timebase rebasing`](../../../xnu/osfmk/arm64/cpu.c#L980).

x86 `acpi_sleep_kernel()` saves low-level state through `acpi_sleep_cpu()` and invokes the supplied platform callback. On return it rebases TSC conversion, restores syscall entry and configured machine-check/cache/VMX state, and marks CPUs for restart. Its ACPI/VMX path should not be read as an ARM register sequence with different names. [`acpi.c`](../../../xnu/osfmk/i386/acpi.c#L182), [`post-sleep restoration`](../../../xnu/osfmk/i386/acpi.c#L245).

## Hibernation joins VM, storage, and restricted restore code

`hibernate_alloc_page_lists()` allocates general, wired, and machine-specific page-list objects with failure cleanup. `hibernate_setup()` creates the physical-address map, optionally synchronizes/flushes compressor-backed memory while holding the decompressor lock, and calls `hibernate_processor_setup()`. On ARM that marks the boot CPU as hibernating. VM queue-lock handling explicitly identifies the single-threaded interval between shutdown and post-resume initialization. [`hibernate.c`](../../../xnu/osfmk/kern/hibernate.c#L51), [`hibernate_arm64.c`](../../../xnu/osfmk/arm64/hibernate_arm64.c#L293).

Image writing belongs to `IOHibernateIO.cpp`; its shutdown-context contract forbids ordinary blocking/preemption and relies on polled I/O. Architecture restore code supplies temporary mappings and physical-page copying. ARM64's `pal_hib_resume_tramp()` derives temporary mapping layout from the image metadata, while `hibernate_restore_phys_page()` uses the restore mapping helper to copy data to its physical destination. This survey does not establish image-format/security correctness or reproduce the external boot stage that loads the image. [`IOHibernateIO.cpp`, lifecycle contract](../../../xnu/iokit/Kernel/IOHibernateIO.cpp#L38), [`hibernate_write_image()`](../../../xnu/iokit/Kernel/IOHibernateIO.cpp#L1691), [`restore mapping/copy`](../../../xnu/osfmk/arm64/hibernate_restore.c#L58), [`resume trampoline`](../../../xnu/osfmk/arm64/hibernate_restore.c#L305).

## Commpage publishes selected kernel information to userspace

At boot, `vm_commpage_init()` invokes architecture population and `vm_commpage_text_init()` populates text routines. ARM `commpage_populate()` obtains mappings from `pmap_create_commpages()` and writes version, capabilities, CPU topology, page-size, timebase, and other fields through kernel aliases. User data mappings are read-only; the text mapping has separately chosen execute permissions. At exec, ARM `vm_commpage_enter()` inserts these mappings through pmap, whereas x86 follows memory-entry/VM-map setup. [`vm_shared_region.c`](../../../xnu/osfmk/vm/vm_shared_region.c#L3673), [`ARM population`](../../../xnu/osfmk/arm/commpage/commpage.c#L99), [`SPTM mapping attributes`](../../../xnu/osfmk/arm64/sptm/pmap/pmap.c#L1854).

Publication has synchronization rules. `commpage_set_timestamp()` clears the timestamp marker, executes a barrier, writes the related time fields, executes another barrier, and publishes the final timestamp. Readers must use the matching protocol; independently reading a few fields is not a general consistency guarantee. Commpage preemption-free text also interacts with the [AST return path](execution.md). [`commpage.c`](../../../xnu/osfmk/arm/commpage/commpage.c#L303).

## Virtualization interfaces are several different boundaries

`hv_support_kext.c` supplies task/thread target associations, callback registration, and trap-table dispatch. Missing or out-of-range handlers return `KERN_INVALID_ARGUMENT`; registered handlers validate their target objects. The callbacks connect scheduling and task/thread destruction to a virtualization provider. This is interface glue, not a complete hypervisor implementation. x86 additionally contains VMX CPU support, including per-CPU VMXON regions and entering/leaving VMX operation. [`hv_support_kext.c`](../../../xnu/osfmk/kern/hv_support_kext.c#L43), [`trap dispatch`](../../../xnu/osfmk/kern/hv_support_kext.c#L224), [`vmx_cpu.c`](../../../xnu/osfmk/i386/vmx/vmx_cpu.c#L167).

ARM64 `arm64_hypercall.c`, under `APPLEVIRTUALPLATFORM`, instead shows XNU acting as a guest: it issues `hvc #0`, checks host feature support, obtains boot/time metadata, and offers virtual-CPU kick/wait operations. The host implementation is not included. SPTM calls used for protected mappings form yet another boundary; do not infer that guest hypercalls and protected page-table operations share a provider or protocol. [`arm64_hypercall.c`](../../../xnu/osfmk/arm64/arm64_hypercall.c#L58), [`guest operations`](../../../xnu/osfmk/arm64/arm64_hypercall.c#L237), [`hypercall IDs`](../../../xnu/osfmk/arm64/hv_hvc.h#L30).

For the detailed power path, continue with [system sleep policy and orchestration](../drivers/system-sleep-and-wake.md), [hibernation image creation](hibernation-image-creation.md), [physical and VM restore](hibernation-restore.md), and [x86 sleep/resume](x86-sleep-and-resume.md). The [ARM64 CPU lifecycle](cpu-power-lifecycle.md) covers CPU offline/idle/system-suspend coordination.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
