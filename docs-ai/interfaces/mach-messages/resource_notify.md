# Mach messages: resource_notify

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/resource_notify.defs](../../../xnu/osfmk/mach/resource_notify.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 827800: cpu_usage_violation

Notify an external resource-policy receiver of CPU-time usage exceeding a threshold.

**Mechanism:** The shared sender is passed this generated `send_*` function as a function pointer. It snapshots the BSD process identity and ledger balance/refill/limit/period, timestamps the event and obtains the host resource-notify port. It sets the current thread’s honor-queue-limit option before the send, clears that bit afterward and releases the port; this is a set/clear pair, not restoration of a saved previous option value. The resource daemon's handling is external. [Local path](../../../xnu/osfmk/kern/task_policy.c#L3958).

**Declarations:** [`cpu_usage_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L58) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
SimpleRoutine cpu_usage_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    killed_proc_path : posix_path_t;
    timestamp : mach_timespec_t;
    observed_cpu_nsecs : int64_t;
    observation_nsecs : int64_t;
    cpu_nsecs_allowed : int64_t;
    limit_window_nsecs : int64_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 827801: cpu_wakes_violation

Notify an external resource-policy receiver of excessive wakeups during the observed interval.

**Mechanism:** The shared sender is passed this generated `send_*` function as a function pointer. It snapshots the BSD process identity and ledger balance/refill/limit/period, timestamps the event and obtains the host resource-notify port. It sets the current thread’s honor-queue-limit option before the send, clears that bit afterward and releases the port; this is a set/clear pair, not restoration of a saved previous option value. The resource daemon's handling is external. [Local path](../../../xnu/osfmk/kern/task_policy.c#L3958).

**Declarations:** [`cpu_wakes_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L78) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
SimpleRoutine cpu_wakes_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    killed_proc_path : posix_path_t;
    timestamp : mach_timespec_t;
    observed_cpu_wakes : int64_t;
    observation_nsecs : int64_t;
    cpu_wakes_allowed : int64_t;
    limit_window_nsecs : int64_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 827802: disk_writes_violation

Report excessive dirty-byte/disk-write activity and its observation window.

**Mechanism:** The shared sender is passed this generated `send_*` function as a function pointer. It snapshots the BSD process identity and ledger balance/refill/limit/period, timestamps the event and obtains the host resource-notify port. It sets the current thread’s honor-queue-limit option before the send, clears that bit afterward and releases the port; this is a set/clear pair, not restoration of a saved previous option value. The resource daemon's handling is external. [Local path](../../../xnu/osfmk/kern/task_policy.c#L3958).

**Declarations:** [`disk_writes_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L98) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
SimpleRoutine disk_writes_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    killed_proc_path : posix_path_t;
    timestamp : mach_timespec_t;
    observed_bytes_dirtied : int64_t;
    observation_nsecs : int64_t;
    bytes_dirtied_allowed : int64_t;
    limit_window_nsecs : int64_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 827803: port_space_violation

Report excessive Mach port-space consumption, including the declared fatal-action capability.

**Mechanism:** The common fatal-port sender requires the current task, forms process identity/time/current-size/limit information and prefers the task resource-notify port, falling back to the host service when no task port is set. It sends the fatal capability and flags through the supplied generated function pointer while honoring queue limits, then releases the endpoint. Notification policy is separate from resource allocation and eventual termination. [Local path](../../../xnu/osfmk/kern/task_policy.c#L4027).

**Declarations:** [`port_space_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L118) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
SimpleRoutine port_space_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    timestamp : mach_timespec_t;
    observed_ports : int64_t;
    ports_allowed : int64_t;
    fatal_port : mach_port_copy_send_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 827804: file_descriptors_violation

Report excessive file-descriptor consumption and the declared fatal-action capability.

**Mechanism:** The common fatal-port sender requires the current task, forms process identity/time/current-size/limit information and prefers the task resource-notify port, falling back to the host service when no task port is set. It sends the fatal capability and flags through the supplied generated function pointer while honoring queue limits, then releases the endpoint. Notification policy is separate from resource allocation and eventual termination. [Local path](../../../xnu/osfmk/kern/task_policy.c#L4027).

**Declarations:** [`file_descriptors_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L138) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
SimpleRoutine file_descriptors_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    timestamp : mach_timespec_t;
    observed_filedesc : int64_t;
    filedesc_allowed : int64_t;
    fatal_port : mach_port_copy_send_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 827805: kqworkloops_violation

Report excessive kqueue workloop consumption to the resource-policy receiver.

**Mechanism:** The common fatal-port sender requires the current task, forms process identity/time/current-size/limit information and prefers the task resource-notify port, falling back to the host service when no task port is set. It sends the fatal capability and flags through the supplied generated function pointer while honoring queue limits, then releases the endpoint. Notification policy is separate from resource allocation and eventual termination. [Local path](../../../xnu/osfmk/kern/task_policy.c#L4027).

**Declarations:** [`kqworkloops_violation`](../../../xnu/osfmk/mach/resource_notify.defs#L159) (`sender64`).
**Reserved instead in:** `server64`, `server32`, `client64`, `client32`, `libsyscall64`, `local64`.

**Fields after preprocessing (`sender64`):**

```text
SimpleRoutine kqworkloops_violation(
    receiver : mach_port_t;
    procname : proc_name_t;
    pid : int;
    timestamp : mach_timespec_t;
    observed_kqworkloops : int64_t;
    kqworkloops_allowed : int64_t;
    fatal_port : mach_port_copy_send_t;
    flags : resource_notify_flags_t
);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
