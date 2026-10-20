# Mach messages: arcade_upcall

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/arcade_upcall.defs](../../../xnu/osfmk/mach/arcade_upcall.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 61471: arcade_upcall

Issue the registered protected-feature request to its external service.

**Mechanism:** The local bridge sends a `vm_map_copy` path buffer, its length and file offset to the registered validation service and receives `should_kill`. The AST path obtains/refreshes that service and interprets the RPC outcome. Validation internals run in the external service; this declaration does not expose its policy implementation. [Local path](../../../xnu/osfmk/kern/arcade.c#L261).

**Declarations:** [`arcade_upcall`](../../../xnu/osfmk/mach/arcade_upcall.defs#L43) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine arcade_upcall(
           arcade_upcall : mach_port_t;
           path : pointer_t;
           offset : uint64_t;
 out should_kill : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/arcade.c:267](../../../xnu/osfmk/kern/arcade.c#L267). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
