# Mach messages: audit_triggers

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/audit_triggers.defs](../../../xnu/osfmk/mach/audit_triggers.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 123: audit_triggers

Send an audit-control trigger to the registered audit daemon.

**Mechanism:** The audit wrapper obtains the host audit-control port, sends the declared payload and releases the right. It explicitly discards the RPC result and returns zero after that send attempt; endpoint acquisition failure follows a separate return path. Audit daemon processing is external, so wrapper success is not proof that the daemon completed the request. [Local path](../../../xnu/bsd/security/audit/audit_bsd.c#L459).

**Declarations:** [`audit_triggers`](../../../xnu/osfmk/mach/audit_triggers.defs#L50) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine audit_triggers(
  audit_port : mach_port_t;
 in flags : int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/security/audit/audit_bsd.c:467](../../../xnu/bsd/security/audit/audit_bsd.c#L467). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 124: audit_analytics

Send the declared audit analytics data to its registered receiver.

**Mechanism:** The audit wrapper obtains the host audit-control port, sends the declared payload and releases the right. It explicitly discards the RPC result and returns zero after that send attempt; endpoint acquisition failure follows a separate return path. Audit daemon processing is external, so wrapper success is not proof that the daemon completed the request. [Local path](../../../xnu/bsd/security/audit/audit_bsd.c#L476).

**Declarations:** [`audit_analytics`](../../../xnu/osfmk/mach/audit_triggers.defs#L54) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine audit_analytics(
   audit_port : mach_port_t;
 in caller_id : string_t;
 in caller_name : string_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/security/audit/audit_bsd.c:484](../../../xnu/bsd/security/audit/audit_bsd.c#L484). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
