# Mach messages: fairplayd_notification

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/fairplayd_notification.defs](../../../xnu/osfmk/mach/fairplayd_notification.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 41471: fairplayd_arcade_request

**Interface contract:**

> Notification from the kernel requesting a new arcade service port from fairplayd. Instead of replying with a port, the new port passed to the arcade_provider port sent here via arcade_set_upcall_port().

**Mechanism:** The refresh path marks refresh-in-progress, releases an old upcall port, obtains the host fairplayd endpoint and sends the registration capability. Only a successful send reaches its interruptible deadline wait for registration; an invalid endpoint or failed send clears refresh-in-progress without that wait. Concurrent refresh callers instead sleep on the in-progress flag without this explicit deadline. The external daemon must register an upcall through the separate kernel receiver. [Local path](../../../xnu/osfmk/kern/arcade.c#L182-L257).

**Declarations:** [`fairplayd_arcade_request`](../../../xnu/osfmk/mach/fairplayd_notification.defs#L48) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine fairplayd_arcade_request(
              fairplayd_port : mach_port_t;
              arcade_reg_port : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/arcade.c:223](../../../xnu/osfmk/kern/arcade.c#L223). These may be senders, wrappers or declarations; they do not establish a local receiver.
