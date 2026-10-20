# Mach messages: netname

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[libsyscall/mach/servers/netname.defs](../../../xnu/libsyscall/mach/servers/netname.defs#L1). Not listed as a separate subsystem in this checkout's `mig_e` table. Local bodies, generated interfaces and compatibility aliases are distinguished below; a declaration alone does not establish an active kernel message endpoint.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 1040: netname_check_in

Register a name and port with the historical name server, using a signature port for ownership.

**Mechanism:** This library-supplied historical name-service protocol addresses an external server and uses bounded name strings plus the declared port capabilities. Its server prefix is `_`; no matching receiver body is supplied. It is not the kernel IPC-space name table and is not registered in `mig_e`, so server lookup/registration policy is outside this checkout. [Local path](../../../xnu/libsyscall/mach/servers/netname.defs#L53).

**Declarations:** [`netname_check_in`](../../../xnu/libsyscall/mach/servers/netname.defs#L60) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine netname_check_in(server_port : mach_port_t;
   port_name : netname_name_t;
   signature : mach_port_t;
   port_id : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1041: netname_look_up

Request the port registered for a name on the indicated host.

**Mechanism:** This library-supplied historical name-service protocol addresses an external server and uses bounded name strings plus the declared port capabilities. Its server prefix is `_`; no matching receiver body is supplied. It is not the kernel IPC-space name table and is not registered in `mig_e`, so server lookup/registration policy is outside this checkout. [Local path](../../../xnu/libsyscall/mach/servers/netname.defs#L53).

**Declarations:** [`netname_look_up`](../../../xnu/libsyscall/mach/servers/netname.defs#L65) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine netname_look_up(server_port : mach_port_t;
   host_name : netname_name_t;
   port_name : netname_name_t;
      out port_id : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1042: netname_check_out

Remove a name-server registration using its signature capability.

**Mechanism:** This library-supplied historical name-service protocol addresses an external server and uses bounded name strings plus the declared port capabilities. Its server prefix is `_`; no matching receiver body is supplied. It is not the kernel IPC-space name table and is not registered in `mig_e`, so server lookup/registration policy is outside this checkout. [Local path](../../../xnu/libsyscall/mach/servers/netname.defs#L53).

**Declarations:** [`netname_check_out`](../../../xnu/libsyscall/mach/servers/netname.defs#L70) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine netname_check_out(server_port : mach_port_t;
   port_name : netname_name_t;
   signature : mach_port_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 1043: netname_version

Request the name server's version string.

**Mechanism:** This library-supplied historical name-service protocol addresses an external server and uses bounded name strings plus the declared port capabilities. Its server prefix is `_`; no matching receiver body is supplied. It is not the kernel IPC-space name table and is not registered in `mig_e`, so server lookup/registration policy is outside this checkout. [Local path](../../../xnu/libsyscall/mach/servers/netname.defs#L53).

**Declarations:** [`netname_version`](../../../xnu/libsyscall/mach/servers/netname.defs#L74) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine netname_version(server_port : mach_port_t;
      out version : netname_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
