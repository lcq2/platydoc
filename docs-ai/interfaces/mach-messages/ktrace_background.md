# Mach messages: ktrace_background

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/ktrace_background.defs](../../../xnu/osfmk/mach/ktrace_background.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 670: ktrace_background_available

Notify a registered tracing client that background tracing is available.

**Mechanism:** The wrapper obtains the host background-tracing notification port and sends `send_ktrace_background_available`, releasing the right afterward and returning the send result. Missing/invalid endpoints produce failure. The receiving daemon's decision to start tracing is outside this tree. [Local path](../../../xnu/osfmk/kern/ktrace_background_notify.c#L43).

**Declarations:** [`ktrace_background_available`](../../../xnu/osfmk/mach/ktrace_background.defs#L46) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine ktrace_background_available(
              ktrace_background_port : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/ktrace_background_notify.c:53](../../../xnu/osfmk/kern/ktrace_background_notify.c#L53). These may be senders, wrappers or declarations; they do not establish a local receiver.
