# Mach messages: doubleagent_mig

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/doubleagent_mig.defs](../../../platydoc-data/xnu/osfmk/mach/doubleagent_mig.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 6300: doubleagent_lookup_xattr

Request lookup of a mediated extended attribute from the external service.

**Mechanism:** The caller opens the AppleDouble backing file with a shared lock, creates a fileport, drops its vnode iocount and asks the daemon for offset/length. It maps transport failure to EIO, reacquires a vnode reference on success and performs the actual `VNOP_READ` locally. The daemon parses metadata; file bytes and uio accounting remain on the kernel path. [Local path](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1653).

**Declarations:** [`doubleagent_lookup_xattr`](../../../platydoc-data/xnu/osfmk/mach/doubleagent_mig.defs#L53) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine doubleagent_lookup_xattr(
    server : mach_port_t;
    in file_port : mach_port_move_send_t;
    in file_size : int64_t;
    in name : xattrname;
    out err : int;
    out value_offset : uint64_t;
    out value_length : uint64_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_xattr.c:1690](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1690). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6301: doubleagent_allocate_xattr

Request allocation/storage for a mediated extended attribute.

**Mechanism:** Opens/creates the backing file with an exclusive lock, exports a fileport and asks the daemon to allocate metadata for the name/length/options. After successful response and vnode reacquisition, the kernel adjusts the uio offset and writes bytes locally. A daemon allocation can precede a later local write failure; this is not a single rollback transaction. [Local path](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1936).

**Declarations:** [`doubleagent_allocate_xattr`](../../../platydoc-data/xnu/osfmk/mach/doubleagent_mig.defs#L63) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine doubleagent_allocate_xattr(
    server : mach_port_t;
    in file_port : mach_port_move_send_t;
    in file_size : int64_t;
    in name : xattrname;
    in size : uint64_t;
    in options : uint32_t;
    out err : int;
    out value_offset : uint64_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_xattr.c:1957](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1957). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6302: doubleagent_list_xattrs

Request the names of mediated extended attributes.

**Mechanism:** Exports the backing file capability and receives a fixed-format result containing names. On successful RPC/error status, reacquires the vnode, checks caller uio capacity and copies names; local copy errors remain possible after the daemon completed. The daemon's AppleDouble parsing is external. [Local path](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1766).

**Declarations:** [`doubleagent_list_xattrs`](../../../platydoc-data/xnu/osfmk/mach/doubleagent_mig.defs#L74) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine doubleagent_list_xattrs(
    server : mach_port_t;
    in file_port : mach_port_move_send_t;
    in file_size : int64_t;
    out err : int;
    out result : listxattrs_result_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_xattr.c:1787](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L1787). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6303: doubleagent_remove_xattr

Request removal of a mediated extended attribute.

**Mechanism:** Sends the backing file capability/name under the caller's exclusive-file operation and receives status plus an empty-file indication. After successful response and vnode reacquisition, the kernel removes the backing file when empty or closes it otherwise. The RPC result and later local cleanup are separate operations. [Local path](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L2041).

**Declarations:** [`doubleagent_remove_xattr`](../../../platydoc-data/xnu/osfmk/mach/doubleagent_mig.defs#L82) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine doubleagent_remove_xattr(
    server : mach_port_t;
    in file_port : mach_port_move_send_t;
    in file_size : int64_t;
    in name : xattrname;
    out err : int;
    out is_empty : boolean_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_xattr.c:2061](../../../platydoc-data/xnu/bsd/vfs/vfs_xattr.c#L2061). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
