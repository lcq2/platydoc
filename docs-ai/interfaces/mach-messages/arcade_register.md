# Mach messages: arcade_register

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/arcade_register.defs](../../../xnu/osfmk/mach/arcade_register.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 51471: arcade_register_new_upcall

Register or replace the protected-feature upcall port after the local entitlement and ownership checks.

**Mechanism:** Requires a valid registration object and the arcade service entitlement. While a refresh is in progress, replaces the saved upcall send right under `arcade_upcall_mutex`, consumes the new right and wakes the waiting refresh. Outside that interval it fails, so possession of the registration port alone does not allow arbitrary-time endpoint replacement. [Local path](../../../xnu/osfmk/kern/arcade.c#L148).

**Declarations:** [`arcade_register_new_upcall`](../../../xnu/osfmk/mach/arcade_register.defs#L42) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine arcade_register_new_upcall(
     arcade_register : arcade_register_t;
     arcade_upcall : mach_port_t);
```

**Local body:** [`arcade_register_new_upcall`](../../../xnu/osfmk/kern/arcade.c#L148).
Calls visible in this body include `os_log`, `IOCurrentTaskHasEntitlement`, `lck_mtx_lock`, `IP_VALID`, `ipc_port_release_send`, `lck_mtx_unlock`, `thread_wakeup`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
