# Mach messages: telemetry_notification

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/telemetry_notification.defs](../../../xnu/osfmk/mach/telemetry_notification.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 5100: telemetry_notification

Send telemetry notification data to the registered external receiver.

**Mechanism:** The local notification helper obtains the host telemetry service port, sends notice flags and releases the right. It returns silently when the endpoint is unavailable and does not propagate the message result. AST sampling and kernel collection are separate from this service notification; see [AST flavors](../../subsystems/runtime/ast-flavors.md). [Local path](../../../xnu/osfmk/kern/telemetry.c#L309).

**Declarations:** [`telemetry_notification`](../../../xnu/osfmk/mach/telemetry_notification.defs#L18) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine telemetry_notification(
 RequestPort telemetry_port : mach_port_t;
 in flags : uint32_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/telemetry.c:317](../../../xnu/osfmk/kern/telemetry.c#L317). These may be senders, wrappers or declarations; they do not establish a local receiver.
