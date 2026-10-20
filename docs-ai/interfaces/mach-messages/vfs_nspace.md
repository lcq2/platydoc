# Mach messages: vfs_nspace

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/vfs_nspace.defs](../../../xnu/osfmk/mach/vfs_nspace.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 867800: nspace_handle

Send a namespace/filesystem mediation request to the registered external service.

**Mechanism:** This deprecated declaration sends a PID and path and returns `handler_error`; unlike the later resolver routines, it has no request-ID or operation-mask argument. The current local VFS path uses the audited file, directory or reparent variants instead, and no matching receiver is present. The external namespace/file-coordination service performs resolution; the modern local request wait/cancel protocol should not be read back into this older contract. [Declaration](../../../xnu/osfmk/mach/vfs_nspace.defs#L45-L51); [current sender](../../../xnu/bsd/vfs/vfs_syscalls.c#L12934).

**Declarations:** [`nspace_handle`](../../../xnu/osfmk/mach/vfs_nspace.defs#L46) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine nspace_handle(
        nspace_handler_port : mach_port_t;
        pid : uint32_t;
     in path : vfs_path_t;
    out handler_error : int
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 867801: nspace_resolve_cancel

Cancel a pending namespace-resolution request in the external service.

**Mechanism:** The cancellation helper obtains the host filecoordinationd port and sends the request ID; send failure is logged but not fatal. The source explicitly treats cancellation as advisory. Removing local request state therefore does not prove the external resolver has stopped its work. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12199).

**Declarations:** [`nspace_resolve_cancel`](../../../xnu/osfmk/mach/vfs_nspace.defs#L53) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine nspace_resolve_cancel(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_syscalls.c:12208](../../../xnu/bsd/vfs/vfs_syscalls.c#L12208). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 867802: nspace_resolve_path

**Interface contract:**

> nspace_resolve_path should not be moved even after it's not used, it's going to mess up the calls numbering in mig.

**Mechanism:** This retained resolver declaration exposes the request identifier and path/operation contract shown below. The current local VFS path uses the audited file, directory or reparent variants instead; no same-symbol receiver is present. The external namespace/file-coordination service performs resolution, while the local request wait/cancel protocol is a separate mechanism. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12934).

**Declarations:** [`nspace_resolve_path`](../../../xnu/osfmk/mach/vfs_nspace.defs#L62) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine nspace_resolve_path(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        pid : uint32_t;
        op : uint32_t;
     in path : nspace_path_t;
    out resolve_error : int
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 867803: vfs_resolve_file

**Interface contract:**

> vfs_resolve_file is deprecated in favor of vfs_resolve_file_with_audit_token.

**Mechanism:** This retained resolver declaration exposes the request identifier and path/operation contract shown below. The current local VFS path uses the audited file, directory or reparent variants instead; no same-symbol receiver is present. The external namespace/file-coordination service performs resolution, while the local request wait/cancel protocol is a separate mechanism. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12934).

**Declarations:** [`vfs_resolve_file`](../../../xnu/osfmk/mach/vfs_nspace.defs#L74) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vfs_resolve_file(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        pid : uint32_t;
        op : uint32_t;
        offset : int64_t;
        size : int64_t;
     in path : nspace_path_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 867804: vfs_resolve_dir

**Interface contract:**

> vfs_resolve_dir is deprecated in favor of vfs_resolve_dir_with_audit_token.

**Mechanism:** This retained resolver declaration exposes the request identifier and path/operation contract shown below. The current local VFS path uses the audited file, directory or reparent variants instead; no same-symbol receiver is present. The external namespace/file-coordination service performs resolution, while the local request wait/cancel protocol is a separate mechanism. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12934).

**Declarations:** [`vfs_resolve_dir`](../../../xnu/osfmk/mach/vfs_nspace.defs#L87) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vfs_resolve_dir(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        pid : uint32_t;
        op : uint32_t;
     in file_name : nspace_name_t;
     in path : nspace_path_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 867805: vfs_resolve_file_with_audit_token

Request mediated file resolution with explicit audit identity.

**Mechanism:** The namespace resolver constructs a tracked request and sends file path plus offset/size with an operation/event mask and audit token. If the send fails it removes the request and returns the mapped timeout error; after a successful send it waits through the separate resolver-request protocol. A send acknowledgement alone is not file materialization completion. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L13009).

**Declarations:** [`vfs_resolve_file_with_audit_token`](../../../xnu/osfmk/mach/vfs_nspace.defs#L96) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vfs_resolve_file_with_audit_token(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        op : uint32_t;
        offset : int64_t;
        size : int64_t;
     in path : nspace_path_t;
     in req_atoken : audit_token_t;
ServerAuditToken atoken : audit_token_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_syscalls.c:13009](../../../xnu/bsd/vfs/vfs_syscalls.c#L13009). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 867806: vfs_resolve_dir_with_audit_token

Request mediated directory resolution with explicit audit identity.

**Mechanism:** The namespace resolver constructs a tracked request and sends directory path plus an optional bounded lookup name with an operation/event mask and audit token. If the send fails it removes the request and returns the mapped timeout error; after a successful send it waits through the separate resolver-request protocol. A send acknowledgement alone is not file materialization completion. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12993).

**Declarations:** [`vfs_resolve_dir_with_audit_token`](../../../xnu/osfmk/mach/vfs_nspace.defs#L107) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vfs_resolve_dir_with_audit_token(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        op : uint32_t;
     in file_name : nspace_name_t;
     in path : nspace_path_t;
     in req_atoken : audit_token_t;
ServerAuditToken atoken : audit_token_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_syscalls.c:12993](../../../xnu/bsd/vfs/vfs_syscalls.c#L12993). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 867807: vfs_resolve_reparent_with_audit_token

Request mediated reparent resolution with explicit audit identity.

**Mechanism:** The namespace resolver constructs a tracked request and sends source and destination-directory paths for rename with an operation/event mask and audit token. If the send fails it removes the request and returns the mapped timeout error; after a successful send it waits through the separate resolver-request protocol. A send acknowledgement alone is not file materialization completion. [Local path](../../../xnu/bsd/vfs/vfs_syscalls.c#L12957).

**Declarations:** [`vfs_resolve_reparent_with_audit_token`](../../../xnu/osfmk/mach/vfs_nspace.defs#L117) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine vfs_resolve_reparent_with_audit_token(
        nspace_handler_port : mach_port_t;
        req_id : uint32_t;
        op : uint32_t;
     in path : nspace_path_t;
     in dest_path : nspace_path_t;
     in req_atoken : audit_token_t;
ServerAuditToken atoken : audit_token_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/vfs/vfs_syscalls.c:12957](../../../xnu/bsd/vfs/vfs_syscalls.c#L12957). These may be senders, wrappers or declarations; they do not establish a local receiver.
