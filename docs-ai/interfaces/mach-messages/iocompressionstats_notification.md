# Mach messages: iocompressionstats_notification

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/iocompressionstats_notification.defs](../../../platydoc-data/xnu/osfmk/mach/iocompressionstats_notification.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 5600: iocompressionstats_notification

Send the declared I/O compression statistics to an external notification receiver.

**Mechanism:** The VFS statistics sender obtains the host compression-statistics service port, sends notice value zero and releases the right; unavailable endpoints cause an early return. The message prompts userspace processing of collected statistics rather than carrying a complete compressed buffer or performing file compression. [Local path](../../../platydoc-data/xnu/bsd/vfs/vfs_io_compression_stats.c#L416).

**Declarations:** [`iocompressionstats_notification`](../../../platydoc-data/xnu/osfmk/mach/iocompressionstats_notification.defs#L18) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine iocompressionstats_notification(
 RequestPort iocompressionstats_port : mach_port_t;
 in flags : uint32_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_io_compression_stats.c:424](../../../platydoc-data/xnu/bsd/vfs/vfs_io_compression_stats.c#L424). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
