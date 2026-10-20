# Mach messages: clock_priv

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/clock_priv.defs](../../../xnu/osfmk/mach/clock_priv.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 1200: clock_set_time

**Interface contract:**

> Obsolete interfaces, removed from kernel.

**Mechanism:** The interface file explicitly labels these operations obsolete and removed from the kernel. This declaration preserves the message shape, but this checkout supplies no corresponding routine body; it does not establish a working token-changing or clock-control service. The catalog registration boundary must be considered separately from successful preprocessing. [clock_set_time](../../../xnu/osfmk/mach/clock_priv.defs#L51).

**Declarations:** [`clock_set_time`](../../../xnu/osfmk/mach/clock_priv.defs#L51) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine clock_set_time(
  clock_ctrl : clock_ctrl_t;
  new_time : mach_timespec_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1201: clock_set_attributes

Request a privileged update of the selected clock attribute flavor.

**Mechanism:** The interface file explicitly labels these operations obsolete and removed from the kernel. This declaration preserves the message shape, but this checkout supplies no corresponding routine body; it does not establish a working token-changing or clock-control service. The catalog registration boundary must be considered separately from successful preprocessing. [clock_set_attributes](../../../xnu/osfmk/mach/clock_priv.defs#L55).

**Declarations:** [`clock_set_attributes`](../../../xnu/osfmk/mach/clock_priv.defs#L55) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine clock_set_attributes(
  clock_ctrl : clock_ctrl_t;
 in flavor : clock_flavor_t;
 in clock_attr : clock_attr_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
