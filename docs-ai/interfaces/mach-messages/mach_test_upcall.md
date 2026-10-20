# Mach messages: mach_test_upcall

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_test_upcall.defs](../../../xnu/osfmk/mach/mach_test_upcall.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 125: mach_test_sync_upcall

Send a test synchronous upcall to the supplied receiver.

**Mechanism:** Under `DEVELOPMENT || DEBUG`, `task_test_sync_upcall` requires the current task and a valid caller-supplied send port, invokes this synchronous request/reply operation, releases the supplied send right and returns `KERN_SUCCESS` without propagating the upcall result. Other builds return `KERN_NOT_SUPPORTED`. The wrapper does not look up a configured service port; receiver behavior is external to the declaration. [Local path](../../../xnu/osfmk/kern/task.c#L10223-L10243).

**Declarations:** [`mach_test_sync_upcall`](../../../xnu/osfmk/mach/mach_test_upcall.defs#L37) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_test_sync_upcall(
  port : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/task.c:10234](../../../xnu/osfmk/kern/task.c#L10234). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 126: mach_test_async_upcall

Send a test one-way upcall to the supplied receiver.

**Mechanism:** Under `DEVELOPMENT || DEBUG`, `task_test_async_upcall_propagation` requires the current task, a valid caller-supplied port and bounded QoS/I/O-tier values. It propagates those attributes to the port, sets send-importance on the current thread around this one-way upcall, then clears it and releases the send right. Attribute-propagation failure returns early; the upcall result itself is not propagated. Other builds return `KERN_NOT_SUPPORTED`; no configured service endpoint is looked up. [Local path](../../../xnu/osfmk/kern/task.c#L10245-L10290).

**Declarations:** [`mach_test_async_upcall`](../../../xnu/osfmk/mach/mach_test_upcall.defs#L40) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_test_async_upcall(
  port : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/task.c:10278](../../../xnu/osfmk/kern/task.c#L10278). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
