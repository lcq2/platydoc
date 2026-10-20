# Mach messages: prof

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/prof.defs](../../../xnu/osfmk/mach/prof.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 2450: samples

Deliver a batch of program-counter profiling samples to the external profiling receiver.

**Mechanism:** This profiling-output protocol declares one-way delivery to an external profile-server destination. The local source inventory resolves no same-symbol receiver/body, and the subsystem is not registered in `mig_e`. The payload contract is retained without asserting an active modern kernel producer or reconstructing the collector.

**Declarations:** [`samples`](../../../xnu/osfmk/mach/prof.defs#L126) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine samples(
   reply_port : mach_port_t;
   samples : sample_array_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 2451: notices

Deliver profiling notices to the external profiling receiver.

**Mechanism:** This profiling-output protocol declares one-way delivery to an external profile-server destination. The local source inventory resolves no same-symbol receiver/body, and the subsystem is not registered in `mig_e`. The payload contract is retained without asserting an active modern kernel producer or reconstructing the collector.

**Declarations:** [`notices`](../../../xnu/osfmk/mach/prof.defs#L130) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine notices(
   reply_port : mach_port_t;
   samples : sample_array_t;
 msgoption options : mach_msg_options_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
