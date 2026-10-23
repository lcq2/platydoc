# Mach messages: sysdiagnose_notification

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/sysdiagnose_notification.defs](../../../platydoc-data/xnu/osfmk/mach/sysdiagnose_notification.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 31337: sysdiagnose_notification

Request diagnostics through the registered external notification service.

**Mechanism:** This older message declares the keycode notification without the audited form. The visible local sender uses `sysdiagnose_notification_with_audit_token` instead; no same-symbol receiver is supplied. The two protocol slots are retained separately rather than treated as two kernel diagnostic implementations. [Local path](../../../platydoc-data/xnu/osfmk/kern/sysdiagnose.c#L58).

**Declarations:** [`sysdiagnose_notification`](../../../platydoc-data/xnu/osfmk/mach/sysdiagnose_notification.defs#L45) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine sysdiagnose_notification(
              sysdiagnose_port : mach_port_t;
              flags : uint32_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 31338: sysdiagnose_notification_with_audit_token

Request diagnostics with the explicit audit-token form of the interface.

**Mechanism:** `sysdiagnose_notify_user` looks up the host sysdiagnose port, records a kdebug event, sends the keycode via the audited notification form and releases the right. The declared audit-token trailer supports receiver-side sender identity; collecting diagnostics is the external service's work. [Local path](../../../platydoc-data/xnu/osfmk/kern/sysdiagnose.c#L45).

**Declarations:** [`sysdiagnose_notification_with_audit_token`](../../../platydoc-data/xnu/osfmk/mach/sysdiagnose_notification.defs#L49) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine sysdiagnose_notification_with_audit_token(
              sysdiagnose_port : mach_port_t;
              flags : uint32_t;
              ServerAuditToken atoken : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/sysdiagnose.c:58](../../../platydoc-data/xnu/osfmk/kern/sysdiagnose.c#L58). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
