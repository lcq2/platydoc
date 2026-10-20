# BSD syscalls: Time and accounting

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 51: acct

`int acct(char *path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L105) · **Condition:** `always` · **Audit event:** `AUE_ACCT`.

Enable, replace or disable process accounting output to a file.

**Implementation:** [acct](../../../xnu/bsd/kern/kern_acct.c#L153). Checks privilege/MAC, opens the accounting vnode, serializes accounting subsystem state and arranges `acctwatch`; file ownership and later accounting writes outlive this syscall.

## 83: setitimer

`int setitimer(u_int which, struct itimerval *itv, struct itimerval *oitv);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L141) · **Condition:** `always` · **Audit event:** `AUE_SETITIMER`.

Set a process interval timer and optionally return its previous state.

**Implementation:** [setitimer](../../../xnu/bsd/kern/kern_time.c#L387). Imports/validates the selected timer, coordinates proc timing state and programs thread-call deadlines for real time or task virtual timers for execution-time modes.

## 86: getitimer

`int getitimer(u_int which, struct itimerval *itv);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L144) · **Condition:** `always` · **Audit event:** `AUE_GETITIMER`.

Read the current process interval-timer state.

**Implementation:** [getitimer](../../../xnu/bsd/kern/kern_time.c#L314). Copies protected timer state, computes remaining real time against the current uptime when needed, converts the user ABI and copies it out.

## 116: gettimeofday

`int gettimeofday(struct timeval *tp, struct timezone *tzp, uint64_t *mach_absolute_time) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L190) · **Condition:** `always` · **Audit event:** `AUE_GETTIMEOFDAY`.

Read calendar time and supported optional time-related outputs.

**Implementation:** [gettimeofday](../../../xnu/bsd/kern/kern_time.c#L118). Uses `clock_gettimeofday_and_absolute_time`, converts 32/64-bit timeval layout and copies requested time/timezone-related data; it does not advance timer state.

## 122: settimeofday

`int settimeofday(struct timeval *tv, struct timezone *tzp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L200) · **Condition:** `always` · **Audit event:** `AUE_SETTIMEOFDAY`.

Set calendar time and optional timezone state under policy checks.

**Implementation:** [settimeofday](../../../xnu/bsd/kern/kern_time.c#L171). Checks entitlement/privilege/MAC, imports/converts time values, calls `setthetime` and updates protected timezone state where requested.

## 140: adjtime

`int adjtime(struct timeval *delta, struct timeval *olddelta);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L224) · **Condition:** `always` · **Audit event:** `AUE_ADJTIME`.

Request gradual clock adjustment and optionally read the previous adjustment.

**Implementation:** [adjtime](../../../xnu/bsd/kern/kern_ntptime.c#L710). Checks time-setting authorization, converts the timeval request, calls `kern_adjtime` and copies the old adjustment out; it is distinct from directly replacing calendar time.

## 186: thread_selfcounts

`int thread_selfcounts(uint32_t kind, user_addr_t buf, user_size_t size);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L282) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read selected current-thread time/cycle/instruction/energy counters, optionally by performance level.

**Implementation:** [thread_selfcounts](../../../xnu/bsd/kern/sys_recount.c#L175), [thread_selfcounts](../../../xnu/bsd/kern/sys_recount.c#L275). Under `CONFIG_PERVASIVE_CPI`, the switch invokes `_selfcounts` or `_selfcounts_perf_level`; unsupported kinds and the alternate no-support definition return `ENOTSUP`.

## 373: ledger

`int ledger(int cmd, caddr_t arg1, caddr_t arg2, caddr_t arg3);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L554) · **Condition:** `always` · **Audit event:** `AUE_LEDGER`.

Query selected task ledger information, entries or template metadata.

**Implementation:** [ledger](../../../xnu/bsd/kern/sys_generic.c#L2254). Imports the selector/target, checks process/MAC access, uses `ledger_info`, `ledger_get_task_entry_info_multiple` or `ledger_template_info`, and copies size-limited results out while releasing process/buffer ownership.

## 482: thread_selfusage

`uint64_t thread_selfusage(void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L741) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read the current thread's execution runtime.

**Implementation:** [thread_selfusage](../../../xnu/bsd/kern/kern_resource.c#L3606). Returns `thread_get_runtime_self` through the syscall result ABI; it is a runtime aggregate, not a thread port or wall-clock timestamp.

## 527: ntp_adjtime

`int ntp_adjtime(struct timex *tp);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L835) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read/change NTP clock-discipline parameters and return discipline status.

**Implementation:** [ntp_adjtime](../../../xnu/bsd/kern/kern_ntptime.c#L296). Imports the timex ABI, checks authorization for modifications, updates discipline state under `NTP_LOCK` and returns the selected output/status through the declared interface.

## 528: ntp_gettime

`int ntp_gettime(struct ntptimeval *ntvp);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L836) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read NTP calendar/error/state information.

**Implementation:** [ntp_gettime](../../../xnu/bsd/kern/kern_ntptime.c#L258). Calls `ntp_gettime1` under the NTP lock, converts the caller's structure layout and copies it out.

## 531: __mach_bridge_remote_time

`uint64_t __mach_bridge_remote_time(uint64_t local_timestamp);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L839) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Convert a local timestamp through the platform's remote-time bridge.

**Implementation:** [__mach_bridge_remote_time](../../../xnu/bsd/kern/kern_time.c#L959). Returns `mach_bridge_remote_time(local_timestamp)` in the 64-bit syscall result; synchronization/provider details live behind that kernel time helper.
