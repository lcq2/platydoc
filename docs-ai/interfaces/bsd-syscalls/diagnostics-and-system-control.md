# BSD syscalls: Diagnostics and system control

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 67: oslog_coproc_reg

`int oslog_coproc_reg(const char *uuid, const char *file_path, size_t file_path_len) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L125) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Register a coprocessor firmware UUID and harvest-file path with kernel logging.

**Implementation:** [oslog_coproc_reg](../../../xnu/bsd/kern/sys_generic.c#L2570). The caller must be a DriverKit task and hold the coprocessor-logging entitlement. The handler bounds and imports the path and UUID, calls `os_log_coprocessor_register_with_type` with the filesystem-table harvest type, and releases its temporary allocation.

## 68: oslog_coproc

`int oslog_coproc(void *buff, uint64_t buff_len, uint32_t type, const char *uuid, uint64_t timestamp, uint32_t offset, uint32_t stream_log) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L126) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Submit a coprocessor log payload with UUID, timestamp, format offset and streaming selection.

**Implementation:** [oslog_coproc](../../../xnu/bsd/kern/sys_generic.c#L2501). The handler requires a DriverKit task plus entitlement, checks the full record size with overflow detection, imports payload and UUID, calls `os_log_coprocessor`, and frees the payload on success or failure.

## 142: gethostuuid

`int gethostuuid(unsigned char *uuid_buf, const struct timespec *timeoutp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L226) · **Condition:** `always` · **Audit event:** `AUE_SYSCTL`.

Retrieve the platform UUID, allowing the platform lookup to wait for the supplied timeout.

**Implementation:** [gethostuuid](../../../xnu/bsd/kern/sys_generic.c#L2193). The handler applies the entitlement/platform/MAC branch, converts the process-width `timespec`, calls `IOBSDGetPlatformUUID`, then copies the UUID out. An unsuccessful IOKit lookup becomes `EWOULDBLOCK`; the entitlement is not an unconditional requirement on every configuration.

## 177: kdebug_typefilter

`int kdebug_typefilter(void** addr, size_t* size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L273) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Map the kernel tracing type-filter bitmap read-only into the calling address space.

**Implementation:** [kdebug_typefilter](../../../xnu/bsd/kern/kdebug.c#L1164). The handler maps `kdbg_typefilter_memory_entry` with `mach_vm_map_kernel`, read-only protections and shared inheritance, copies out the resulting pointer using the map's address width, and deallocates the mapping if that copyout fails. In this body the size pointer is checked for null but not written.

## 178: kdebug_trace_string

`uint64_t kdebug_trace_string(uint32_t debugid, uint64_t str_id, const char *str) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L274) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Associate, update or terminate a string identifier in the kernel debug trace stream.

**Implementation:** [kdebug_trace_string](../../../xnu/bsd/kern/kdebug.c#L1435). Tracing and event/process filters can make the call return without recording. Otherwise it validates the debug ID and string ID, imports a bounded string (allowing truncation), and calls `kernel_debug_string_internal`; a null string with a valid existing ID takes the termination path.

## 179: kdebug_trace64

`int kdebug_trace64(uint32_t code, uint64_t arg1, uint64_t arg2, uint64_t arg3, uint64_t arg4) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L275) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Emit a kernel debug trace event with four user-supplied arguments.

**Implementation:** [kdebug_trace64](../../../xnu/bsd/kern/kdebug.c#L1211). The narrow wrapper builds the 64-bit argument structure and delegates. `kdebug_trace64` returns immediately when tracing is disabled; otherwise it rejects kernel-only event IDs and calls `kernel_debug_internal`, supplying the current thread ID rather than a user-selected fifth argument.

## 180: kdebug_trace

`int kdebug_trace(uint32_t code, u_long arg1, u_long arg2, u_long arg3, u_long arg4) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L276) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Emit a kernel debug trace event with four user-supplied arguments.

**Implementation:** [kdebug_trace](../../../xnu/bsd/kern/kdebug.c#L1192). The narrow wrapper builds the 64-bit argument structure and delegates. `kdebug_trace64` returns immediately when tracing is disabled; otherwise it rejects kernel-only event IDs and calls `kernel_debug_internal`, supplying the current thread ID rather than a user-selected fifth argument.

## 185: sys_panic_with_data

`int sys_panic_with_data(uuid_t uuid, void *addr, uint32_t len, uint32_t flags, const char *msg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L281) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Request a kernel panic carrying a bounded userspace message and auxiliary data.

**Implementation:** [sys_panic_with_data](../../../xnu/bsd/kern/kern_xxx.c#L163). The handler requires the extended-panic-log entitlement, imports or substitutes message/data/UUID fields and derives debugger options from supported flags. Allocation or copy failures converge on the final `panic_with_data` call rather than an ordinary successful return.

## 202: sysctl

`int sysctl(int *name, u_int namelen, void *old, size_t *oldlenp, void *new, size_t newlen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L298) · **Condition:** `always` · **Audit event:** `AUE_SYSCTL`.

Read or write an individual registered system-control node, addressed by numeric OID or name.

**Implementation:** [sysctl](../../../xnu/bsd/kern/kern_newsysctl.c#L2025). The numeric form imports the OID array; the named form allocates and terminates an imported name. Both construct a `sysctl_req` with userspace copy functions and call `userland_sysctl`, which resolves the node and enforces its access policy. They export the resulting old length, including the `ENOMEM` size-reporting case. Individual OID handlers are a separate interface surface.

## 274: sys_sysctlbyname

`int sys_sysctlbyname(const char *name, size_t namelen, void *old, size_t *oldlenp, void *new, size_t newlen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L421) · **Condition:** `always` · **Audit event:** `AUE_SYSCTL`.

Read or write an individual registered system-control node, addressed by numeric OID or name.

**Implementation:** [sys_sysctlbyname](../../../xnu/bsd/kern/kern_newsysctl.c#L2108). The numeric form imports the OID array; the named form allocates and terminates an imported name. Both construct a `sysctl_req` with userspace copy functions and call `userland_sysctl`, which resolves the node and enforces its access policy. They export the resulting old length, including the `ENOMEM` size-reporting case. Individual OID handlers are a separate interface surface.

## 451: telemetry

`int telemetry(uint64_t cmd, uint64_t deadline, uint64_t interval, uint64_t leeway, uint64_t arg4, uint64_t arg5) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L688) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Select telemetry setup/read operations or set the current thread's voucher name.

**Implementation:** [telemetry](../../../xnu/bsd/kern/sys_generic.c#L2369). Under `CONFIG_TELEMETRY`, the command switch reaches PMI, page-in and memory-usage helpers; the timer-event command returns `ENOTSUP`. The voucher-name command calls `thread_set_voucher_name` independently of that guard. Unknown or unavailable commands return `EINVAL`.

## 477: proc_trace_log

`int proc_trace_log(pid_t pid, uint64_t uniqueid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L731) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Request delivery of a particular process's trace-memory data.

**Implementation:** [proc_trace_log](../../../xnu/bsd/kern/kern_proc.c#L5171). The handler checks `PRIV_PROC_TRACE_INSPECT`, finds and references the PID, verifies the supplied unique ID to reject PID reuse, calls `task_send_trace_memory`, and releases the process reference. Missing/mismatched identity yields `ENOENT`.

## 491: stack_snapshot_with_config

`int stack_snapshot_with_config(int stackshot_config_version, user_addr_t stackshot_config, size_t stackshot_config_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L762) · **Condition:** `always` · **Audit event:** `AUE_STACKSNAPSHOT`.

Collect or retrieve a stackshot using the versioned stackshot configuration ABI.

**Implementation:** [stack_snapshot_with_config](../../../xnu/bsd/kern/stackshot.c#L522). The wrapper checks superuser authority and the configured entitlement/reporting policy, validates the version and exact structure size, imports the configuration and calls `kern_stack_snapshot_internal`. It translates Mach results through `stackshot_kern_return_to_bsd_error` and may report the authorization/outcome stage.

## 492: microstackshot

`int microstackshot(user_addr_t tracebuf, uint32_t tracebuf_size, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L764) · **Condition:** `(CONFIG_TELEMETRY)` · **Audit event:** `AUE_STACKSNAPSHOT`.

Control or retrieve the telemetry microstackshot stream.

**Implementation:** [microstackshot](../../../xnu/bsd/kern/stackshot.c#L594). The `CONFIG_TELEMETRY` handler requires superuser authority, calls `stack_microstackshot` with the userspace buffer and flags, and translates the Mach result to a BSD error. The helper controls enabled modes, collection and output size.

## 493: grab_pgo_data

`user_ssize_t grab_pgo_data (user_addr_t uuid, int flags, user_addr_t buffer, user_ssize_t size);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L769) · **Condition:** `(PGO)` · **Audit event:** `AUE_NULL`.

Retrieve compiler profiling data for the kernel or a selected kext, or reset profiling counters.

**Implementation:** [grab_pgo_data](../../../xnu/bsd/pgo/profile_runtime.c#L111). The handler checks superuser and MAC authority, validates flags and sizes, rejects hibernation-profile requests, and supports size queries. A UUID selects `OSKextGrabPgoData`; the kernel-data branch uses `write_buffer` under `PROFILE` and otherwise returns `ENOSYS`. Reset requests call `pgo_reset_counters`; temporary buffers are freed on exit.

## 533: log_data

`int log_data(unsigned int tag, unsigned int flags, void *buffer, unsigned int size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L845) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Submit a bounded DriverKit message to the kernel logging path.

**Implementation:** [log_data](../../../xnu/bsd/kern/sys_generic.c#L2417). The handler requires a driver task, validates the version tag and log type, caps the message size, imports it into allocated storage and forces a terminating null byte. `os_log_driverKit` emits the message and may update the error result; cleanup always frees the temporary buffer.

## 535: objc_bp_assist_cfg_np

`int objc_bp_assist_cfg_np(uint64_t adr, uint64_t ctl);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L847) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Expose the Objective-C breakpoint-assist configuration syscall slot.

**Implementation:** [objc_bp_assist_cfg_np](../../../xnu/bsd/dev/arm/stubs.c#L99), [objc_bp_assist_cfg_np](../../../xnu/bsd/dev/i386/stubs.c#L121). Both local ARM and x86 handler bodies are stubs returning literal `KERN_FAILURE`; neither applies a configuration. The declaration therefore does not establish an implemented breakpoint-assistance facility in this checkout.

## 547: debug_syscall_reject

`int debug_syscall_reject(uint64_t packed_selectors) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L863) · **Condition:** `always` · **Audit event:** `AUE_DEBUG_SYSCALL_REJECT`.

Configure the current thread's debugging syscall-rejection mask.

**Implementation:** [debug_syscall_reject](../../../xnu/bsd/kern/kern_debug.c#L320), [debug_syscall_reject](../../../xnu/bsd/kern/kern_debug.c#L478). The compatibility entry packages the older selector word for `sys_debug_syscall_reject_config`. The configured body starts with deny-all, applies packed allow/deny mask selectors under `syscall_rejection_mtx`, allocates per-uthread masks and handles once-only state. Missing masks can be ignored in the configured ignore mode. Without `CONFIG_DEBUG_SYSCALL_REJECTION`, both alternate bodies return `ENOTSUP`.

## 548: sys_debug_syscall_reject_config

`int sys_debug_syscall_reject_config(uint64_t packed_selectors1, uint64_t packed_selectors2, uint64_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L864) · **Condition:** `always` · **Audit event:** `AUE_DEBUG_SYSCALL_REJECT_CONFIG`.

Configure the current thread's debugging syscall-rejection mask.

**Implementation:** [sys_debug_syscall_reject_config](../../../xnu/bsd/kern/kern_debug.c#L222), [sys_debug_syscall_reject_config](../../../xnu/bsd/kern/kern_debug.c#L471). The compatibility entry packages the older selector word for `sys_debug_syscall_reject_config`. The configured body starts with deny-all, applies packed allow/deny mask selectors under `syscall_rejection_mtx`, allocates per-uthread masks and handles once-only state. Missing masks can be ignored in the configured ignore mode. Without `CONFIG_DEBUG_SYSCALL_REJECTION`, both alternate bodies return `ENOTSUP`.

## 552: sys_record_system_event

`int sys_record_system_event(uint32_t type, uint32_t subsystem, const char *event, const char *payload) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L868) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Record an entitled system event with a bounded event name and payload.

**Implementation:** [sys_record_system_event](../../../xnu/bsd/kern/sys_record_event.c#L29). The handler checks `SYSTEM_EVENT_ENTITLEMENT`, imports both null-terminated strings into fixed buffers, and calls `record_system_event_no_varargs`, narrowing the type and subsystem to their byte fields. Import errors return before the logging call.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
