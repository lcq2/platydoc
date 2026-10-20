# Mach messages: mach_voucher_attr_control

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_voucher_attr_control.defs](../../../xnu/osfmk/mach/mach_voucher_attr_control.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 5600: mach_voucher_attr_control_get_values

**Interface contract:**

> Extract the given voucher-control's value-handle from the supplied voucher

**Mechanism:** Validates a nonnull control and voucher, takes the key index from the control and retrieves zero handles for an unused value or exactly one cached handle for a present value in the current `ivace_lookup_values` body. Zero requested output capacity returns success immediately. This is control-capability access to internal attribute values; the separate subsystem is not registered in `mig_e`. [`Implementation`](../../../xnu/osfmk/ipc/ipc_voucher.c#L2036).

**Declarations:** [`mach_voucher_attr_control_get_values`](../../../xnu/osfmk/mach/mach_voucher_attr_control.defs#L45) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_voucher_attr_control_get_values(
  control : ipc_voucher_attr_control_t;
  voucher : ipc_voucher_t;
 out value_handles : mach_voucher_attr_value_handle_array_t, CountInOut);
```

**Local body:** [`mach_voucher_attr_control_get_values`](../../../xnu/osfmk/ipc/ipc_voucher.c#L2036).
Calls visible in this body include `os_ref_get_count_raw`, `iv_lookup`, `ivace_lookup_values`.
This body/reference does not override the kernel-server slot's reserved or declaration-only status.

### 5601: mach_voucher_attr_control_create_mach_voucher

**Interface contract:**

> Create a new voucher with the control's privilege (to directly assign value-handles)

**Mechanism:** This historical declaration is skipped by the kernel-server profile and its subsystem is absent from `mig_e`; no same-symbol receiver is resolved. A distinct local helper, `ipc_voucher_attr_control_create_mach_voucher`, rejects a null control and passes its privilege plus kernel-form recipes to `ipc_create_mach_voucher_internal`. That helper does not establish a callable receiver for the `mach_` declaration. [Local kernel helper](../../../xnu/osfmk/ipc/ipc_voucher.c#L1595), [reserved server slots](../../../xnu/osfmk/mach/mach_voucher_attr_control.defs#L40).

**Declarations:** [`mach_voucher_attr_control_create_mach_voucher`](../../../xnu/osfmk/mach/mach_voucher_attr_control.defs#L51) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine mach_voucher_attr_control_create_mach_voucher(
  control : ipc_voucher_attr_control_t;
  recipes : mach_voucher_attr_raw_recipe_array_t;
 out voucher : ipc_voucher_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
