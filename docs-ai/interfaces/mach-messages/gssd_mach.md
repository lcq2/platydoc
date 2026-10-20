# Mach messages: gssd_mach

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/gssd/gssd_mach.defs](../../../xnu/osfmk/gssd/gssd_mach.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 999: mach_gss_init_sec_context

Request a GSS initiator security-context step from the external GSS daemon.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_init_sec_context`](../../../xnu/osfmk/gssd/gssd_mach.defs#L57) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
Routine mach_gss_init_sec_context(
 server : mach_port_t;
 in mech : gssd_mechtype;
 in intoken : gssd_byte_buffer;
 in uid : uint32_t;
 in princ_namestr : gssd_string;
 in svc_namestr : gssd_string;
 in flags : uint32_t;
 in gssd_flags : uint32_t;
 inout context : gssd_ctx;
 inout cred_handle : gssd_cred;
 ServerAuditToken atoken : audit_token_t;
 out ret_flags : uint32_t;
 out key : gssd_byte_buffer, dealloc;
 out outtoken : gssd_byte_buffer, dealloc;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1000: mach_gss_accept_sec_context

Request a GSS acceptor security-context step from the external GSS daemon.

**Mechanism:** The NFS server obtains the gssd host port, packages its incoming GSS token as `vm_map_copy` and sends context/credential handles. It retries server death only for a new context and within a fixed retry bound, then validates returned lucid-context size, imports the context/token data and releases resources. Cryptographic negotiation and credential-service policy are implemented by external gssd. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_accept_sec_context`](../../../xnu/osfmk/gssd/gssd_mach.defs#L76) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_accept_sec_context(
 server : mach_port_t;
 in intoken : gssd_byte_buffer;
 in svc_namestr : gssd_string;
 in gssd_flags : uint32_t;
 inout context : gssd_ctx;
 inout cred_handle : gssd_cred;
 ServerAuditToken atoken : audit_token_t;
 out flags : uint32_t;
 out uid : uint32_t;
 out gids : gssd_gid_list;
 out key : gssd_byte_buffer, dealloc;
 out outtoken : gssd_byte_buffer, dealloc;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/nfs/nfs_gss.c:1155](../../../xnu/bsd/nfs/nfs_gss.c#L1155). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 1001: mach_gss_log_error

Forward a GSS error and descriptive context for daemon-side logging.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_log_error`](../../../xnu/osfmk/gssd/gssd_mach.defs#L93) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_gss_log_error(
 server : mach_port_t;
 in mnt : gssd_string;
 in uid : uint32_t;
 in source : gssd_string;
 in major_stat : uint32_t;
 in minor_stat : uint32_t;
 ServerAuditToken atoken : audit_token_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1002: mach_gss_init_sec_context_v2

Request the version-2 initiator exchange with the extra identity/context fields in this declaration.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_init_sec_context_v2`](../../../xnu/osfmk/gssd/gssd_mach.defs#L103) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_init_sec_context_v2(
 server : mach_port_t;
 in mech : gssd_mechtype;
 in intoken : gssd_byte_buffer;
 in uid : uint32_t;
 in clnt_nt : gssd_nametype;
 in clnt_princ : gssd_byte_buffer;
 in svc_nt : gssd_nametype;
 in svc_princ : gssd_byte_buffer;
 in flags : uint32_t;
 inout gssd_flags : uint32_t;
 inout context : gssd_ctx;
 inout cred_handle : gssd_cred;
 ServerAuditToken atoken : audit_token_t;
 out ret_flags : uint32_t;
 out key : gssd_byte_buffer, dealloc;
 out outtoken : gssd_byte_buffer, dealloc;
 out displayname : gssd_dstring;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1003: mach_gss_accept_sec_context_v2

Request the version-2 acceptor exchange with its declared identity and credential fields.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_accept_sec_context_v2`](../../../xnu/osfmk/gssd/gssd_mach.defs#L125) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_accept_sec_context_v2(
 server : mach_port_t;
 in intoken : gssd_byte_buffer;
 in svc_nt : gssd_nametype;
 in svc_princ : gssd_byte_buffer;
 inout gssd_flags : uint32_t;
 inout context : gssd_ctx;
 inout cred_handle : gssd_cred;
 ServerAuditToken atoken : audit_token_t;
 out flags : uint32_t;
 out uid : uint32_t;
 out gids : gssd_gid_list;
 out key : gssd_byte_buffer, dealloc;
 out outtoken : gssd_byte_buffer, dealloc;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1004: mach_gss_init_sec_context_v3

Request the version-3 initiator exchange, including its additional credential/identity representation.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_init_sec_context_v3`](../../../xnu/osfmk/gssd/gssd_mach.defs#L143) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_init_sec_context_v3(
 server : mach_port_t;
 in mech : gssd_mechtype;
 in intoken : gssd_byte_buffer;
 in uid : uint32_t;
 in clnt_nt : gssd_nametype;
 in clnt_princ : gssd_byte_buffer;
 in svc_nt : gssd_nametype;
 in svc_princ : gssd_byte_buffer;
 in flags : uint32_t;
 in etypes : gssd_etype_list;
 inout gssd_flags : uint32_t;
 inout context : gssd_ctx;
 inout cred_handle : gssd_cred;
 ServerAuditToken atoken : audit_token_t;
 out ret_flags : uint32_t;
 out key : gssd_byte_buffer, dealloc;
 out outtoken : gssd_byte_buffer, dealloc;
 out displayname : gssd_dstring;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1005: mach_gss_hold_cred

Ask the GSS daemon to retain the identified credential.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_hold_cred`](../../../xnu/osfmk/gssd/gssd_mach.defs#L166) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_hold_cred(
 server : mach_port_t;
 in mech : gssd_mechtype;
 in nt : gssd_nametype;
 in princ : gssd_byte_buffer;
 ServerAuditToken atoken : audit_token_t;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1006: mach_gss_unhold_cred

Release the daemon-side hold on the identified credential.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_unhold_cred`](../../../xnu/osfmk/gssd/gssd_mach.defs#L176) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_unhold_cred(
 server : mach_port_t;
 in mech : gssd_mechtype;
 in nt : gssd_nametype;
 in princ : gssd_byte_buffer;
 ServerAuditToken atoken : audit_token_t;
 out major_stat : uint32_t;
 out minor_stat : uint32_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1007: mach_gss_lookup

Resolve a credential/principal description through the GSS daemon.

**Mechanism:** The declaration carries a service-side GSS/credential operation using the tokens, handles, identity fields and outputs shown below. No same-symbol local receiver or direct sender was resolved. These handles belong to the external gssd protocol; the available NFS accept-context sender is evidence for that service boundary, not an implementation of every versioned operation. [Local path](../../../xnu/bsd/nfs/nfs_gss.c#L1122).

**Declarations:** [`mach_gss_lookup`](../../../xnu/osfmk/gssd/gssd_mach.defs#L186) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_gss_lookup(
 server : mach_port_t;
 in uid : uint32_t;
 in asid : int32_t;
 ServerAuditToken atoken : audit_token_t;
 out gssd_session_port : mach_port_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
