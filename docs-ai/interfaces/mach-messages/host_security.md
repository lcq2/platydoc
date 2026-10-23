# Mach messages: host_security

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/host_security.defs](../../../platydoc-data/xnu/osfmk/mach/host_security.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 600: host_security_create_task_token

**Interface contract:**

> Obsolete interfaces, removed from kernel.

**Mechanism:** The interface file explicitly labels these operations obsolete and removed from the kernel. This declaration preserves the message shape, but this checkout supplies no corresponding routine body; it does not establish a working token-changing or clock-control service. The catalog registration boundary must be considered separately from successful preprocessing. [host_security_create_task_token](../../../platydoc-data/xnu/osfmk/mach/host_security.defs#L81).

**Declarations:** [`host_security_create_task_token`](../../../platydoc-data/xnu/osfmk/mach/host_security.defs#L81) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_security_create_task_token(
  host_security : host_security_t;
  parent_task : task_t;
  sec_token : security_token_t;
  audit_token : audit_token_t;
  host : host_t;
  ledgers : ledger_array_t;
  inherit_memory : boolean_t;
 out child_task : task_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 601: host_security_set_task_token

Request assignment of security/audit identity tokens to a task through the historical host-security capability.

**Mechanism:** The interface file explicitly labels these operations obsolete and removed from the kernel. This declaration preserves the message shape, but this checkout supplies no corresponding routine body; it does not establish a working token-changing or clock-control service. The catalog registration boundary must be considered separately from successful preprocessing. [host_security_set_task_token](../../../platydoc-data/xnu/osfmk/mach/host_security.defs#L91).

**Declarations:** [`host_security_set_task_token`](../../../platydoc-data/xnu/osfmk/mach/host_security.defs#L91) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine host_security_set_task_token(
  host_security : host_security_t;
  target_task : task_t;
  sec_token : security_token_t;
  audit_token : audit_token_t;
  host : host_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
