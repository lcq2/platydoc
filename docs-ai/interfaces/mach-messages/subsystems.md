# MIG subsystem and source inventory

[Message dispatch guide](README.md) · [All kernel entry interfaces](../README.md)

This table covers every non-test `.defs` file containing a subsystem declaration. Counts combine the explicit profiles; overlapping numeric ranges are not summed into a global ABI. For example, `vm_map`/`vm32_map` share compatibility numbering, and unrelated external receivers can use the same IDs.

| Definition and routine catalog | Base IDs | Slots across profiles | With a routine in at least one profile | Always skipped | Registration category |
| --- | --- | ---: | ---: | ---: | --- |
| [netname](netname.md) | 1040 | 4 | 4 | 0 | Declaration/compatibility; not separately registered |
| [UNDReply](UNDReply.md) | 6200 | 2 | 2 | 0 | Kernel kobject registration (guarded) |
| [UNDRequest](UNDRequest.md) | 6000 | 8 | 7 | 1 | Service/callback boundary |
| [device](device.md) | 2800 | 91 | 90 | 1 | Kernel kobject registration (guarded) |
| [gssd_mach](gssd_mach.md) | 999 | 9 | 9 | 0 | Service/callback boundary |
| [kextd_mach](kextd_mach.md) | 77000 | 1 | 1 | 0 | Service/callback boundary |
| [lockd_mach](lockd_mach.md) | 1023 | 3 | 3 | 0 | Service/callback boundary |
| [arcade_register](arcade_register.md) | 51471 | 1 | 1 | 0 | Kernel kobject registration (guarded) |
| [arcade_upcall](arcade_upcall.md) | 61471 | 1 | 1 | 0 | Service/callback boundary |
| [audit_triggers](audit_triggers.md) | 123 | 2 | 2 | 0 | Service/callback boundary |
| [clock](clock.md) | 1000 | 3 | 3 | 0 | Kernel kobject registration (guarded) |
| [clock_priv](clock_priv.md) | 1200 | 2 | 2 | 0 | Declaration/compatibility; not separately registered |
| [clock_reply](clock_reply.md) | 3125107 | 1 | 1 | 0 | Service/callback boundary |
| [coalition_notification](coalition_notification.md) | 5300 | 1 | 1 | 0 | Service/callback boundary |
| [doubleagent_mig](doubleagent_mig.md) | 6300 | 4 | 4 | 0 | Service/callback boundary |
| [exc](exc.md) | 2401 | 3 | 3 | 0 | Kernel kobject registration (guarded) |
| [fairplayd_notification](fairplayd_notification.md) | 41471 | 1 | 1 | 0 | Service/callback boundary |
| [host_notify_reply](host_notify_reply.md) | 950 | 2 | 2 | 0 | Service/callback boundary |
| [host_priv](host_priv.md) | 400 | 26 | 23 | 3 | Kernel kobject registration (guarded) |
| [host_security](host_security.md) | 600 | 2 | 2 | 0 | Declaration/compatibility; not separately registered |
| [iocompressionstats_notification](iocompressionstats_notification.md) | 5600 | 1 | 1 | 0 | Service/callback boundary |
| [ktrace_background](ktrace_background.md) | 670 | 1 | 1 | 0 | Service/callback boundary |
| [ledger](ledger.md) | 5000 | 0 | 0 | 0 | Declaration/compatibility; not separately registered |
| [mach_eventlink](mach_eventlink.md) | 716200 | 4 | 4 | 0 | Kernel kobject registration (guarded) |
| [mach_exc](mach_exc.md) | 2405 | 6 | 6 | 0 | Kernel kobject registration (guarded) |
| [mach_host](mach_host.md) | 200 | 36 | 32 | 4 | Kernel kobject registration (guarded) |
| [mach_port](mach_port.md) | 3200 | 43 | 43 | 0 | Kernel kobject registration (guarded) |
| [mach_test_upcall](mach_test_upcall.md) | 125 | 2 | 2 | 0 | Service/callback boundary |
| [mach_vm](mach_vm.md) | 4800 | 30 | 29 | 1 | Kernel kobject registration (guarded) |
| [mach_voucher](mach_voucher.md) | 5400 | 5 | 5 | 0 | Kernel kobject registration (guarded) |
| [mach_voucher_attr_control](mach_voucher_attr_control.md) | 5600 | 2 | 2 | 0 | Declaration/compatibility; not separately registered |
| [memory_entry](memory_entry.md) | 4900 | 4 | 4 | 0 | Kernel kobject registration (guarded) |
| [memory_error_notification](memory_error_notification.md) | 5900 | 3 | 3 | 0 | Service/callback boundary |
| [notify](notify.md) | 64 | 9 | 6 | 3 | Service/callback boundary |
| [processor](processor.md) | 3000 | 6 | 6 | 0 | Kernel kobject registration (guarded) |
| [processor_set](processor_set.md) | 4000 | 11 | 11 | 0 | Kernel kobject registration (guarded) |
| [prof](prof.md) | 2450 | 2 | 2 | 0 | Declaration/compatibility; not separately registered |
| [resource_notify](resource_notify.md) | 827800 | 6 | 6 | 0 | Service/callback boundary |
| [restartable](restartable.md) | 8000 | 2 | 2 | 0 | Kernel kobject registration (guarded) |
| [semaphore](semaphore.md) | 617200 | 7 | 7 | 0 | Declaration/compatibility; not separately registered |
| [sysdiagnose_notification](sysdiagnose_notification.md) | 31337 | 2 | 2 | 0 | Service/callback boundary |
| [task](task.md) | 3400 | 66 | 65 | 1 | Kernel kobject registration (guarded) |
| [task_access](task_access.md) | 27000 | 3 | 3 | 0 | Service/callback boundary |
| [telemetry_notification](telemetry_notification.md) | 5100 | 1 | 1 | 0 | Service/callback boundary |
| [thread_act](thread_act.md) | 3600 | 34 | 34 | 0 | Kernel kobject registration (guarded) |
| [upl](upl.md) | 2050 | 4 | 4 | 0 | Declaration/compatibility; not separately registered |
| [vfs_nspace](vfs_nspace.md) | 867800 | 8 | 8 | 0 | Service/callback boundary |
| [vm32_map](vm32_map.md) | 3800 | 34 | 29 | 5 | Kernel kobject registration (guarded) |
| [vm_map](vm_map.md) | 3800 | 34 | 30 | 4 | Declaration/compatibility; not separately registered |

## Include wrappers

These files are accounted for separately; they do not create an additional independent routine catalog.

- [libsyscall/mach/clock.defs](../../../xnu/libsyscall/mach/clock.defs#L1): includes `mach/clock.defs`.
- [libsyscall/mach/clock_priv.defs](../../../xnu/libsyscall/mach/clock_priv.defs#L1): includes `mach/clock_priv.defs`.
- [libsyscall/mach/clock_reply.defs](../../../xnu/libsyscall/mach/clock_reply.defs#L1): includes `mach/clock_reply.defs`.
- [libsyscall/mach/exc.defs](../../../xnu/libsyscall/mach/exc.defs#L1): includes `mach/exc.defs`.
- [libsyscall/mach/host_priv.defs](../../../xnu/libsyscall/mach/host_priv.defs#L1): includes `mach/host_priv.defs`.
- [libsyscall/mach/host_security.defs](../../../xnu/libsyscall/mach/host_security.defs#L1): includes `mach/host_security.defs`.
- [libsyscall/mach/ledger.defs](../../../xnu/libsyscall/mach/ledger.defs#L1): includes `mach/ledger.defs`.
- [libsyscall/mach/mach_eventlink.defs](../../../xnu/libsyscall/mach/mach_eventlink.defs#L1): includes `mach/mach_eventlink.defs`.
- [libsyscall/mach/mach_host.defs](../../../xnu/libsyscall/mach/mach_host.defs#L1): includes `mach/mach_host.defs`.
- [libsyscall/mach/mach_port.defs](../../../xnu/libsyscall/mach/mach_port.defs#L1): includes `mach/mach_port.defs`.
- [libsyscall/mach/mach_vm.defs](../../../xnu/libsyscall/mach/mach_vm.defs#L1): includes `mach/mach_vm.defs`.
- [libsyscall/mach/mach_voucher.defs](../../../xnu/libsyscall/mach/mach_voucher.defs#L1): includes `mach/mach_voucher.defs`.
- [libsyscall/mach/memory_entry.defs](../../../xnu/libsyscall/mach/memory_entry.defs#L1): includes `mach/memory_entry.defs`.
- [libsyscall/mach/notify.defs](../../../xnu/libsyscall/mach/notify.defs#L1): includes `mach/notify.defs`.
- [libsyscall/mach/processor.defs](../../../xnu/libsyscall/mach/processor.defs#L1): includes `mach/processor.defs`.
- [libsyscall/mach/processor_set.defs](../../../xnu/libsyscall/mach/processor_set.defs#L1): includes `mach/processor_set.defs`.
- [libsyscall/mach/restartable.defs](../../../xnu/libsyscall/mach/restartable.defs#L1): includes `mach/restartable.defs`.
- [libsyscall/mach/task.defs](../../../xnu/libsyscall/mach/task.defs#L1): includes `mach/task.defs`.
- [libsyscall/mach/thread_act.defs](../../../xnu/libsyscall/mach/thread_act.defs#L1): includes `mach/thread_act.defs`.
- [libsyscall/mach/vm_map.defs](../../../xnu/libsyscall/mach/vm_map.defs#L1): includes `mach/mach_vm.defs`, `mach/vm_map.defs`.
- [osfmk/mach/mach_notify.defs](../../../xnu/osfmk/mach/mach_notify.defs#L1): includes `mach/notify.defs`.

## Supporting type definitions

These files are accounted for separately; they do not create an additional independent routine catalog.

- [osfmk/UserNotification/UNDTypes.defs](../../../xnu/osfmk/UserNotification/UNDTypes.defs#L1): includes `mach/std_types.defs`.
- [osfmk/device/device_types.defs](../../../xnu/osfmk/device/device_types.defs#L1): includes `mach/std_types.defs`, `mach/mach_types.defs`.
- [osfmk/mach/clock_types.defs](../../../xnu/osfmk/mach/clock_types.defs#L1): includes `mach/std_types.defs`.
- [osfmk/mach/mach_types.defs](../../../xnu/osfmk/mach/mach_types.defs#L1): includes `mach/std_types.defs`.
- [osfmk/mach/machine/machine_types.defs](../../../xnu/osfmk/mach/machine/machine_types.defs#L1).
- [osfmk/mach/std_types.defs](../../../xnu/osfmk/mach/std_types.defs#L1): includes `mach/machine/machine_types.defs`.
- [osfmk/mach_debug/mach_debug_types.defs](../../../xnu/osfmk/mach_debug/mach_debug_types.defs#L1): includes `mach/std_types.defs`.

## Test interfaces

Test-specific exception servers and replacement declarations are not production kernel entry surfaces.

- [tests/excserver.defs](../../../xnu/tests/excserver.defs#L1)
- [tests/excserver_backtrace.defs](../../../xnu/tests/excserver_backtrace.defs#L1)
- [tests/excserver_protect.defs](../../../xnu/tests/excserver_protect.defs#L1)
- [tests/mach_exc.defs](../../../xnu/tests/mach_exc.defs#L1)
- [tests/notifyserver.defs](../../../xnu/tests/notifyserver.defs#L1)
- [tests/rnserver.defs](../../../xnu/tests/rnserver.defs#L1)
- [tests/vm/vm_parameter_validation_replacement_host_priv.defs](../../../xnu/tests/vm/vm_parameter_validation_replacement_host_priv.defs#L1)
- [tests/vm/vm_parameter_validation_replacement_mach_host.defs](../../../xnu/tests/vm/vm_parameter_validation_replacement_mach_host.defs#L1)

## Reconciliation

- **49** subsystem-bearing definition files.
- **541** raw routine declaration sites; every site appears in at least one profile.
- **510** per-file ID slots with a routine in at least one profile, plus **23** always-skipped per-file slots.
- **510** routine slots with authored mechanism or explicit implementation-boundary explanations.
- Counts include historical, external and overlapping compatibility interfaces. They are not the number of callable kernel RPCs.
