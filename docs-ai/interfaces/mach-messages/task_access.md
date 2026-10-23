# Mach messages: task_access

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/task_access.defs](../../../platydoc-data/xnu/osfmk/mach/task_access.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 27000: check_task_access

**Interface contract:**

> Verify task_for_pid access for the given pid Access granted by return value (success/failure)

**Mechanism:** This older declaration omits the explicit requested flavor. Current visible task-port acquisition uses `check_task_access_with_flavor`; no same-symbol local receiver was resolved. Policy and authentication must be supplied by the external task-access service, not inferred from the argument list.

**Declarations:** [`check_task_access`](../../../platydoc-data/xnu/osfmk/mach/task_access.defs#L45) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine check_task_access(
  task_access_port : mach_port_t;
  calling_pid : int32_t;
  calling_gid : uint32_t;
  target_pid : int32_t;
  ServerAuditToken caller_cred : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 27001: find_code_signature

**Interface contract:**

> Search for a code signature for unsigned executables

**Mechanism:** Exec can ask the task-access service to locate/attach signing information for the new PID through a synchronous wrapper. The source contains this call boundary and subsequent exec signing policy, not the daemon's signature search/database. See [executable signature policy](../../subsystems/security/executable-signature-policy.md). [Local path](../../../platydoc-data/xnu/bsd/kern/kern_exec.c#L8477).

**Declarations:** [`find_code_signature`](../../../platydoc-data/xnu/osfmk/mach/task_access.defs#L55) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine find_code_signature(
  task_access_port : mach_port_t;
  new_pid : int32_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/kern/kern_exec.c:8480](../../../platydoc-data/xnu/bsd/kern/kern_exec.c#L8480). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 27002: check_task_access_with_flavor

Ask the external task-access policy service whether a caller may obtain the requested task-port flavor.

**Mechanism:** The task-port acquisition path invokes the taskgated upcall with calling PID/GID, target PID and requested task-port flavor. The source shows the privileged access decision boundary; the external daemon implements its policy. Local process/credential checks and subsequent task-right conversion still surround that request. [Local path](../../../platydoc-data/xnu/bsd/kern/kern_proc.c#L5845).

**Declarations:** [`check_task_access_with_flavor`](../../../platydoc-data/xnu/osfmk/mach/task_access.defs#L59) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine check_task_access_with_flavor(
  task_access_port : mach_port_t;
  calling_pid : int32_t;
  calling_gid : uint32_t;
  target_pid : int32_t;
  flavor : mach_task_flavor_t;
  ServerAuditToken caller_cred : audit_token_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [bsd/kern/kern_proc.c:5848](../../../platydoc-data/xnu/bsd/kern/kern_proc.c#L5848). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
