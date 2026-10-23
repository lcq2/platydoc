# Mach messages: lockd_mach

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/lockd/lockd_mach.defs](../../../platydoc-data/xnu/osfmk/lockd/lockd_mach.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 1023: lockd_request

Forward an NFS record-lock operation and its file/owner/range parameters to the lock daemon.

**Mechanism:** This is a lock-daemon protocol declaration with a separately addressed server port. No same-symbol local receiver or direct sender was resolved in the indexed implementation. The declared NFS-lock request/control fields document the boundary, but actual userspace lock-service scheduling, persistence and completion cannot be reconstructed from this declaration.

**Declarations:** [`lockd_request`](../../../platydoc-data/xnu/osfmk/lockd/lockd_mach.defs#L51) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine lockd_request(
 server : mach_port_t;
 vers : uint32_t;
 flags : uint32_t;
 xid : uint64_t;
 flk_start : int64_t;
 flk_len : int64_t;
 flk_pid : int32_t;
 flk_type : int32_t;
 flk_whence : int32_t;
 sock_address : sock_storage;
 cred : xcred;
 fh_len : uint32_t;
 fh : nfs_handle
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1024: lockd_ping

**Interface contract:**

> Ping lockd, have launchd start it if its not running

**Mechanism:** This is a lock-daemon protocol declaration with a separately addressed server port. No same-symbol local receiver or direct sender was resolved in the indexed implementation. The declared NFS-lock request/control fields document the boundary, but actual userspace lock-service scheduling, persistence and completion cannot be reconstructed from this declaration.

**Declarations:** [`lockd_ping`](../../../platydoc-data/xnu/osfmk/lockd/lockd_mach.defs#L68) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine lockd_ping(
 server : mach_port_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1025: lockd_shutdown

Request lock-daemon shutdown/cleanup for the supplied peer state.

**Mechanism:** This is a lock-daemon protocol declaration with a separately addressed server port. No same-symbol local receiver or direct sender was resolved in the indexed implementation. The declared NFS-lock request/control fields document the boundary, but actual userspace lock-service scheduling, persistence and completion cannot be reconstructed from this declaration.

**Declarations:** [`lockd_shutdown`](../../../platydoc-data/xnu/osfmk/lockd/lockd_mach.defs#L73) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine lockd_shutdown(
 server : mach_port_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
