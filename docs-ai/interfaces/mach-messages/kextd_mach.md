# Mach messages: kextd_mach

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/kextd/kextd_mach.defs](../../../platydoc-data/xnu/osfmk/kextd/kextd_mach.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 77000: kextd_ping

**Interface contract:**

> Ping kextd, launchd starts it if it's not running.

**Mechanism:** `OSKext::pingIOKitDaemon` is gated by `NO_KEXTD` and the daemon-active state, obtains the host kextd endpoint, sends the ping, logs failures and releases the port on exit. The request prompts the external daemon; its loading/policy work is not the body of this kernel wrapper. [Local path](../../../platydoc-data/xnu/libkern/c++/OSKext.cpp#L1554).

**Declarations:** [`kextd_ping`](../../../platydoc-data/xnu/osfmk/kextd/kextd_mach.defs#L42) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine kextd_ping(
 server : mach_port_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [libkern/c++/OSKext.cpp:1575](../../../platydoc-data/xnu/libkern/c++/OSKext.cpp#L1575). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
