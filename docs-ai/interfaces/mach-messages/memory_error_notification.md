# Mach messages: memory_error_notification

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/memory_error_notification.defs](../../../xnu/osfmk/mach/memory_error_notification.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 5900: memory_error_notification

Send the declared generic memory-error record to the registered external receiver.

**Mechanism:** This older notification slot is retained in the interface. The current local event sender switches between MCC and LLC payload routines instead, so no same-symbol local call or receiver was resolved. Do not infer another hardware-error pipeline from the historical declaration. [Local path](../../../xnu/osfmk/kern/memory_error_logging.c#L100).

**Declarations:** [`memory_error_notification`](../../../xnu/osfmk/mach/memory_error_notification.defs#L21) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine memory_error_notification(
 RequestPort memory_error_port : mach_port_t;
 in event : ecc_event_t;
 ServerAuditToken atoken : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 5901: mcc_memory_error_notification

Send memory-controller error information to the registered receiver.

**Mechanism:** The deferred event-notification path obtains the host memory-error endpoint and dispatches the MCC, guarded by `XNU_LOG_MCC` event payload through this message, then releases the send right. Missing endpoints are logged. The receiver's logging/diagnostic response and hardware-specific policy are not implemented by the MIG declaration. [Local path](../../../xnu/osfmk/kern/memory_error_logging.c#L90).

**Declarations:** [`mcc_memory_error_notification`](../../../xnu/osfmk/mach/memory_error_notification.defs#L26) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mcc_memory_error_notification(
 RequestPort memory_error_port : mach_port_t;
 in event : mcc_ecc_event_t;
 ServerAuditToken atoken : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/memory_error_logging.c:105](../../../xnu/osfmk/kern/memory_error_logging.c#L105). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 5902: llc_memory_error_notification

Send last-level-cache memory-error information to the registered receiver.

**Mechanism:** The deferred event-notification path obtains the host memory-error endpoint and dispatches the LLC event payload through this message, then releases the send right. Missing endpoints are logged. The receiver's logging/diagnostic response and hardware-specific policy are not implemented by the MIG declaration. [Local path](../../../xnu/osfmk/kern/memory_error_logging.c#L90).

**Declarations:** [`llc_memory_error_notification`](../../../xnu/osfmk/mach/memory_error_notification.defs#L31) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine llc_memory_error_notification(
 RequestPort memory_error_port : mach_port_t;
 in event : llc_event_t;
 ServerAuditToken atoken : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/memory_error_logging.c:109](../../../xnu/osfmk/kern/memory_error_logging.c#L109). These may be senders, wrappers or declarations; they do not establish a local receiver.
