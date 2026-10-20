# BSD syscalls: Processes credentials and policy

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 1: exit

`void exit(int rval) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L46) · **Condition:** `always` · **Audit event:** `AUE_EXIT`.

Terminate the current process with an exit status.

**Implementation:** [exit](../../../xnu/bsd/kern/kern_exit.c#L1606). Calls `exit1` with an encoded wait status, then follows thread exception-return/block termination paths; descriptor/task teardown and parent wake/reap are distinct later stages.

## 2: fork

`int fork(void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L47) · **Condition:** `always` · **Audit event:** `AUE_FORK`.

Create a child process/task derived from the caller.

**Implementation:** [fork](../../../xnu/bsd/kern/kern_fork.c#L572). `fork1` allocates/clones process/thread state, arranges map/task and return-register state, completes transition/signal coordination and releases the child for execution; failures unwind partial construction.

## 7: wait4

`int wait4(int pid, user_addr_t status, int options, user_addr_t rusage) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L52) · **Condition:** `always` · **Audit event:** `AUE_WAIT4`.

Wait for selected child state and optionally return status/resource usage.

**Implementation:** [wait4](../../../xnu/bsd/kern/kern_exit.c#L3036). The nocancel body scans children under process-list coordination, waits/retries and copies results before eligible reaping. Ordinary wait4 first performs the cancellation test.

## 20: getpid

`int getpid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L65) · **Condition:** `always` · **Audit event:** `AUE_GETPID`.

Return the calling process ID.

**Implementation:** [getpid](../../../xnu/bsd/kern/kern_prot.c#L158). Reads `proc_getpid(p)` into the syscall result slot; no process lookup or new reference is needed for the current process argument.

## 23: setuid

`int setuid(uid_t uid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L68) · **Condition:** `always` · **Audit event:** `AUE_SETUID`.

Change real/effective/saved user identity according to the selected API.

**Implementation:** [setuid](../../../xnu/bsd/kern/kern_prot.c#L703). Use `kauth_cred_proc_update` with privilege/MAC checks and `kauth_cred_model_setresuid`; credential publication and process-count accounting replace immutable credential state rather than editing a shared credential in place.

## 24: getuid

`int getuid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L69) · **Condition:** `always` · **Audit event:** `AUE_GETUID`.

Read the caller's real/effective user/group ID as selected by the entry.

**Implementation:** [getuid](../../../xnu/bsd/kern/kern_prot.c#L289). The four wrappers call `kauth_getruid`, `kauth_getuid`, `kauth_getrgid` or `kauth_getgid`, respectively, and return a scalar identity from the active credential.

## 25: geteuid

`int geteuid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L70) · **Condition:** `always` · **Audit event:** `AUE_GETEUID`.

Read the caller's real/effective user/group ID as selected by the entry.

**Implementation:** [geteuid](../../../xnu/bsd/kern/kern_prot.c#L306). The four wrappers call `kauth_getruid`, `kauth_getuid`, `kauth_getrgid` or `kauth_getgid`, respectively, and return a scalar identity from the active credential.

## 26: ptrace

`int ptrace(int req, pid_t pid, caddr_t addr, int data);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L71) · **Condition:** `always` · **Audit event:** `AUE_PTRACE`.

Control permitted process tracing/debugging operations.

**Implementation:** [ptrace](../../../xnu/bsd/kern/mach_process.c#L118). Dispatches request-specific attach/detach, signal and state operations after process/credential/platform checks; some requests terminate or alter execution state. It is not a generic unchecked task-memory accessor.

## 38: sys_crossarch_trap

`int sys_crossarch_trap(uint32_t name) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L92) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Retain a cross-architecture namespace entry point.

**Implementation:** [sys_crossarch_trap](../../../xnu/bsd/kern/kern_crossarch.c#L35). The body checks the namespace against `CROSSARCH_MAX_VALID_NAMESPACE`, returning `EINVAL` if invalid and `ENOTSUP` otherwise; it performs no cross-architecture execution in this source.

## 39: getppid

`int getppid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L93) · **Condition:** `always` · **Audit event:** `AUE_GETPPID`.

Return the calling process's recorded parent ID.

**Implementation:** [getppid](../../../xnu/bsd/kern/kern_prot.c#L177). Reads the proc parent-ID field into the result slot; it does not acquire a capability to the parent task.

## 43: getegid

`int getegid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L97) · **Condition:** `always` · **Audit event:** `AUE_GETEGID`.

Read the caller's real/effective user/group ID as selected by the entry.

**Implementation:** [getegid](../../../xnu/bsd/kern/kern_prot.c#L384). The four wrappers call `kauth_getruid`, `kauth_getuid`, `kauth_getrgid` or `kauth_getgid`, respectively, and return a scalar identity from the active credential.

## 47: getgid

`int getgid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L101) · **Condition:** `always` · **Audit event:** `AUE_GETGID`.

Read the caller's real/effective user/group ID as selected by the entry.

**Implementation:** [getgid](../../../xnu/bsd/kern/kern_prot.c#L361). The four wrappers call `kauth_getruid`, `kauth_getuid`, `kauth_getrgid` or `kauth_getgid`, respectively, and return a scalar identity from the active credential.

## 49: getlogin

`int getlogin(char *namebuf, u_int namelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L103) · **Condition:** `always` · **Audit event:** `AUE_GETLOGIN`.

Read the session login name.

**Implementation:** [getlogin](../../../xnu/bsd/kern/kern_prot.c#L1566). Obtains the process group/session, copies the name under the session lock into kernel storage, releases the group and copies the bounded string to userspace.

## 50: setlogin

`int setlogin(char *namebuf) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L104) · **Condition:** `always` · **Audit event:** `AUE_SETLOGIN`.

Change the session login name under privilege checks.

**Implementation:** [setlogin](../../../xnu/bsd/kern/kern_prot.c#L1619). Checks `proc_suser`, imports the bounded name and calls `setlogin_internal`; the affected object is session state, not the username fields of every credential.

## 55: reboot

`int reboot(int opt, char *msg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L109) · **Condition:** `always` · **Audit event:** `AUE_REBOOT`.

Request reboot, halt or other shutdown behavior selected by flags.

**Implementation:** [reboot](../../../xnu/bsd/kern/kern_xxx.c#L106). Checks privilege/MAC policy, imports an optional bounded message, marks shutdown state and calls `reboot_kernel`; hardware/platform shutdown behavior is beyond this frontend.

## 59: execve

`int execve(char *fname, char **argp, char **envp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L113) · **Condition:** `always` · **Audit event:** `AUE_EXECVE`.

Replace the current executable image, optionally with MAC execution-label input.

**Implementation:** [execve](../../../xnu/bsd/kern/kern_exec.c#L5984). `execve` forwards to `__mac_execve`, which imports arguments/environment, coordinates replacement proc/task state and invokes image activation; failures before and after the transition's commitment point have different cleanup rules.

## 66: vfork

`int vfork(void) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L121) · **Condition:** `(CONFIG_VFORK)` · **Audit event:** `AUE_VFORK`.

Declare a conditional historical vfork entry point.

**Implementation:** [Declaration only; local handler absent](../../../xnu/bsd/kern/syscalls.master#L121). `CONFIG_VFORK` selects this master declaration, but no local handler definition is present in this checkout. Comments describing legacy vfork-related execution are not an implementation; the disabled alternative is `nosys`.

## 79: getgroups

`int getgroups(u_int gidsetsize, gid_t *gidset);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L137) · **Condition:** `always` · **Audit event:** `AUE_GETGROUPS`.

Read the caller's supplementary group list or its required count.

**Implementation:** [getgroups](../../../xnu/bsd/kern/kern_prot.c#L422). Retains the active credential, accesses `posix_cred_get` group state, checks supplied capacity and copies the array out before releasing the credential.

## 80: setgroups

`int setgroups(u_int gidsetsize, gid_t *gidset);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L138) · **Condition:** `always` · **Audit event:** `AUE_SETGROUPS`.

Replace supplementary groups, with initgroups also supplying the membership identity context.

**Implementation:** [setgroups](../../../xnu/bsd/kern/kern_prot.c#L1464). `setgroups1` imports and validates the group array and publishes updated credential state; the two wrappers select the corresponding identity/group semantics.

## 81: getpgrp

`int getpgrp(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L139) · **Condition:** `always` · **Audit event:** `AUE_GETPGRP`.

Return the calling process's process-group ID.

**Implementation:** [getpgrp](../../../xnu/bsd/kern/kern_prot.c#L196). Reads the process group identifier from the current proc state into the scalar result.

## 82: setpgid

`int setpgid(int pid, int pgid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L140) · **Condition:** `always` · **Audit event:** `AUE_SETPGRP`.

Change a process's process-group membership.

**Implementation:** [setpgid](../../../xnu/bsd/kern/kern_prot.c#L574). Validates caller/child/session and exec restrictions, obtains group references and invokes `enterpgrp`; membership updates are coordinated with proc/group lifetime protection.

## 96: setpriority

`int setpriority(int which, id_t who, int prio) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L154) · **Condition:** `always` · **Audit event:** `AUE_SETPRIORITY`.

Change or query selected process/group/user scheduling policy values.

**Implementation:** [setpriority](../../../xnu/bsd/kern/kern_resource.c#L471). The selector dispatch finds and references target processes/groups, applies `donice` or specialized background/role handlers, and checks permissions; supported selectors extend beyond a single nice integer.

## 100: getpriority

`int getpriority(int which, id_t who);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L163) · **Condition:** `always` · **Audit event:** `AUE_GETPRIORITY`.

Change or query selected process/group/user scheduling policy values.

**Implementation:** [getpriority](../../../xnu/bsd/kern/kern_resource.c#L199). The selector dispatch finds and references target processes/groups, applies `donice` or specialized background/role handlers, and checks permissions; supported selectors extend beyond a single nice integer.

## 117: getrusage

`int getrusage(int who, struct rusage *rusage);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L191) · **Condition:** `always` · **Audit event:** `AUE_GETRUSAGE`.

Read process/children/thread resource usage according to the selector.

**Implementation:** [getrusage](../../../xnu/bsd/kern/kern_resource.c#L1802). Collects accounting through `calcru` and protected proc/thread state, converts to the caller's 32/64-bit rusage ABI and copies it out.

## 126: setreuid

`int setreuid(uid_t ruid, uid_t euid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L204) · **Condition:** `always` · **Audit event:** `AUE_SETREUID`.

Change real/effective/saved user identity according to the selected API.

**Implementation:** [setreuid](../../../xnu/bsd/kern/kern_prot.c#L855). Use `kauth_cred_proc_update` with privilege/MAC checks and `kauth_cred_model_setresuid`; credential publication and process-count accounting replace immutable credential state rather than editing a shared credential in place.

## 127: setregid

`int setregid(gid_t rgid, gid_t egid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L205) · **Condition:** `always` · **Audit event:** `AUE_SETREGID`.

Change real/effective/saved group identity according to the selected API.

**Implementation:** [setregid](../../../xnu/bsd/kern/kern_prot.c#L1094). Use `kauth_cred_proc_update`, operation-specific permission/MAC checks and `kauth_cred_model_setresgid`; invalid identity transitions fail before publication.

## 147: setsid

`int setsid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L231) · **Condition:** `always` · **Audit event:** `AUE_SETSID`.

Create a new session/process group for an eligible caller.

**Implementation:** [setsid](../../../xnu/bsd/kern/kern_prot.c#L526). `setsid_internal` validates session/group restrictions and establishes the new group/session relationship; the wrapper returns the process ID on success.

## 151: getpgid

`int getpgid(pid_t pid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L235) · **Condition:** `always` · **Audit event:** `AUE_GETPGID`.

Return a selected process's process-group ID.

**Implementation:** [getpgid](../../../xnu/bsd/kern/kern_prot.c#L220). Uses the current process for PID zero or obtains a referenced process with `proc_find`, reads its group identity and releases the lookup reference.

## 152: setprivexec

`int setprivexec(int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L236) · **Condition:** `always` · **Audit event:** `AUE_SETPRIVEXEC`.

Set the proc's legacy privileged-debugger execution flag and return its previous value.

**Implementation:** [setprivexec](../../../xnu/bsd/kern/kern_prot.c#L137). Audits the input, returns `p_debugger`, then stores whether the supplied flag is nonzero. The body is a direct proc-field operation, not a general privilege grant engine.

## 173: waitid

`int waitid(idtype_t idtype, id_t id, siginfo_t *infop, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L269) · **Condition:** `always` · **Audit event:** `AUE_WAITID`.

Wait for selected child events and return structured siginfo.

**Implementation:** [waitid](../../../xnu/bsd/kern/kern_exit.c#L3298). The shared body filters children/events using idtype/options, coordinates wait ownership and copies siginfo; options can observe state without consuming it. The ordinary wrapper tests cancellation.

## 181: setgid

`int setgid(gid_t gid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L277) · **Condition:** `always` · **Audit event:** `AUE_SETGID`.

Change real/effective/saved group identity according to the selected API.

**Implementation:** [setgid](../../../xnu/bsd/kern/kern_prot.c#L959). Use `kauth_cred_proc_update`, operation-specific permission/MAC checks and `kauth_cred_model_setresgid`; invalid identity transitions fail before publication.

## 182: setegid

`int setegid(gid_t egid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L278) · **Condition:** `always` · **Audit event:** `AUE_SETEGID`.

Change real/effective/saved group identity according to the selected API.

**Implementation:** [setegid](../../../xnu/bsd/kern/kern_prot.c#L1025). Use `kauth_cred_proc_update`, operation-specific permission/MAC checks and `kauth_cred_model_setresgid`; invalid identity transitions fail before publication.

## 183: seteuid

`int seteuid(uid_t euid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L279) · **Condition:** `always` · **Audit event:** `AUE_SETEUID`.

Change real/effective/saved user identity according to the selected API.

**Implementation:** [seteuid](../../../xnu/bsd/kern/kern_prot.c#L792). Use `kauth_cred_proc_update` with privilege/MAC checks and `kauth_cred_model_setresuid`; credential publication and process-count accounting replace immutable credential state rather than editing a shared credential in place.

## 194: getrlimit

`int getrlimit(u_int which, struct rlimit *rlp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L290) · **Condition:** `always` · **Audit event:** `AUE_GETRLIMIT`.

Read a process resource limit pair.

**Implementation:** [getrlimit](../../../xnu/bsd/kern/kern_resource.c#L1716). Uses `proc_limitget` for the selected resource and copies the current/maximum limits out.

## 195: setrlimit

`int setrlimit(u_int which, struct rlimit *rlp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L291) · **Condition:** `always` · **Audit event:** `AUE_SETRLIMIT`.

Change a process resource limit pair.

**Implementation:** [setrlimit](../../../xnu/bsd/kern/kern_resource.c#L1395). Copies user limits into kernel storage and calls `dosetrlimit`, which enforces privilege/resource constraints and updates associated process limits.

## 243: initgroups

`int initgroups(u_int gidsetsize, gid_t *gidset, int gmuid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L351) · **Condition:** `always` · **Audit event:** `AUE_INITGROUPS`.

Replace supplementary groups, with initgroups also supplying the membership identity context.

**Implementation:** [initgroups](../../../xnu/bsd/kern/kern_prot.c#L1432). `setgroups1` imports and validates the group array and publishes updated credential state; the two wrappers select the corresponding identity/group semantics.

## 244: posix_spawn

`int posix_spawn(pid_t *pid, const char *path, const struct _posix_spawn_args_desc *adesc, char **argv, char **envp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L352) · **Condition:** `always` · **Audit event:** `AUE_POSIX_SPAWN`.

Create or replace a process image with spawn attributes and file actions.

**Implementation:** [posix_spawn](../../../xnu/bsd/kern/kern_exec.c#L4333). Imports packed attributes/actions, builds the child/replacement process state, applies descriptor/identity actions and image activation, then either publishes success or unwinds construction. It is not just fork followed by an uncoordinated userspace exec.

## 285: sys_settid

`int sys_settid(uid_t uid, gid_t gid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L432) · **Condition:** `always` · **Audit event:** `AUE_SETTID`.

Set a thread-specific effective identity override.

**Implementation:** [sys_settid](../../../xnu/bsd/kern/kern_prot.c#L1236). Passes the requested UID/GID to `kern_settid`, which manages the thread credential override; it is distinct from changing the process credential.

## 286: gettid

`int gettid(uid_t *uidp, gid_t *gidp) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L433) · **Condition:** `always` · **Audit event:** `AUE_GETTID`.

Read thread-credential identity into UID/GID outputs.

**Implementation:** [gettid](../../../xnu/bsd/kern/kern_prot.c#L325). Examines `current_thread_ro` and copies real UID/GID from the applicable credential context; this historical syscall is not the numeric thread-ID query provided by thread_selfid.

## 287: setsgroups

`int setsgroups(int setlen, user_addr_t guidset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L434) · **Condition:** `always` · **Audit event:** `AUE_SETSGROUPS`.

Retain historical supplementary-group entry points without implementation.

**Implementation:** [setsgroups](../../../xnu/bsd/kern/kern_prot.c#L1478). These local handlers immediately return `ENOTSUP`; they do not read or change group arrays.

## 288: getsgroups

`int getsgroups(user_addr_t setlen, user_addr_t guidset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L435) · **Condition:** `always` · **Audit event:** `AUE_GETSGROUPS`.

Retain historical supplementary-group entry points without implementation.

**Implementation:** [getsgroups](../../../xnu/bsd/kern/kern_prot.c#L463). These local handlers immediately return `ENOTSUP`; they do not read or change group arrays.

## 289: setwgroups

`int setwgroups(int setlen, user_addr_t guidset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L436) · **Condition:** `always` · **Audit event:** `AUE_SETWGROUPS`.

Retain historical supplementary-group entry points without implementation.

**Implementation:** [setwgroups](../../../xnu/bsd/kern/kern_prot.c#L1491). These local handlers immediately return `ENOTSUP`; they do not read or change group arrays.

## 290: getwgroups

`int getwgroups(user_addr_t setlen, user_addr_t guidset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L437) · **Condition:** `always` · **Audit event:** `AUE_GETWGROUPS`.

Retain historical supplementary-group entry points without implementation.

**Implementation:** [getwgroups](../../../xnu/bsd/kern/kern_prot.c#L476). These local handlers immediately return `ENOTSUP`; they do not read or change group arrays.

## 293: identitysvc

`int identitysvc(int opcode, user_addr_t message) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L441) · **Condition:** `(CONFIG_EXT_RESOLVER)` · **Audit event:** `AUE_IDENTITYSVC`.

Serve kernel identity/group resolver work through a privileged userspace service.

**Implementation:** [identitysvc](../../../xnu/bsd/kern/kern_credential.c#L509). Checks entitlement/authorization and dispatches resolver registration, work delivery, completion and cache-related operations under the resolver lock; the directory-service implementation itself is external.

## 310: getsid

`int getsid(pid_t pid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L477) · **Condition:** `always` · **Audit event:** `AUE_GETSID`.

Return a selected process's session ID.

**Implementation:** [getsid](../../../xnu/bsd/kern/kern_prot.c#L260). Uses `proc_sessionid`, looking up and releasing another process when a noncurrent PID is requested.

## 311: sys_settid_with_pid

`int sys_settid_with_pid(pid_t pid, int assume) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L478) · **Condition:** `always` · **Audit event:** `AUE_SETTIDWITHPID`.

Set thread identity using another process's credential context.

**Implementation:** [sys_settid_with_pid](../../../xnu/bsd/kern/kern_prot.c#L1256). Obtains a referenced credential by PID, extracts the relevant identity, calls `kern_settid` and releases the temporary credential; PID lookup/policy can fail.

## 322: iopolicysys

`int iopolicysys(int cmd, void *arg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L493) · **Condition:** `always` · **Audit event:** `AUE_IOPOLICYSYS`.

Query or change process/thread I/O policies through a typed operation buffer.

**Implementation:** [iopolicysys](../../../xnu/bsd/kern/kern_resource.c#L2097). Imports the policy request, applies MAC checks and selects disk or VFS policy helpers, including materialization/atime/permission-related policy types; each selector has its own supported scope.

## 323: process_policy

`int process_policy(int scope, int action, int policy, int policy_subtype, user_addr_t attrp, pid_t target_pid, uint64_t target_threadid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L494) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Apply or query selected process/thread resource and lifecycle policies.

**Implementation:** [process_policy](../../../xnu/bsd/kern/process_policy.c#L108). Looks up and authorizes the target, then dispatches low-resource, CPU-use, application-lifecycle/type and related policy handlers; cleanup releases target credentials/process references.

## 327: issetugid

`int issetugid(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L498) · **Condition:** `always` · **Audit event:** `AUE_ISSETUGID`.

Report whether process execution has acquired the set-ID/security-tainted state.

**Implementation:** [issetugid](../../../xnu/bsd/kern/kern_prot.c#L667). Returns `proc_issetugid(p)`; it reports maintained process history/state rather than comparing only current UID and EUID.

## 336: proc_info

`int proc_info(int32_t callnum,int32_t pid,uint32_t flavor, uint64_t arg,user_addr_t buffer,int32_t buffersize) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L513) · **Condition:** `always` · **Audit event:** `AUE_PROCINFO`.

Query/control process information through call/flavor selectors, optionally enforcing extended identity.

**Implementation:** [proc_info](../../../xnu/bsd/kern/proc_info.c#L287). `proc_info_internal` routes PID, fd, region, list and other operation families, checks access and copies flavor-specific data. Extended identity helps reject stale PID selection; this catalog does not enumerate every proc flavor layout.

## 380: __mac_execve

`int __mac_execve(char *fname, char **argp, char **envp, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L561) · **Condition:** `always` · **Audit event:** `AUE_MAC_EXECVE`.

Replace the current executable image, optionally with MAC execution-label input.

**Implementation:** [__mac_execve](../../../xnu/bsd/kern/kern_exec.c#L6027). `execve` forwards to `__mac_execve`, which imports arguments/environment, coordinates replacement proc/task state and invokes image activation; failures before and after the transition's commitment point have different cleanup rules.

## 400: wait4_nocancel

`int wait4_nocancel(int pid, user_addr_t status, int options, user_addr_t rusage) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L594) · **Condition:** `always` · **Audit event:** `AUE_WAIT4`.

Wait for selected child state and optionally return status/resource usage.

**Implementation:** [wait4_nocancel](../../../xnu/bsd/kern/kern_exit.c#L3043). The nocancel body scans children under process-list coordination, waits/retries and copies results before eligible reaping. Ordinary wait4 first performs the cancellation test.

## 416: waitid_nocancel

`int waitid_nocancel(idtype_t idtype, id_t id, siginfo_t *infop, int options) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L625) · **Condition:** `always` · **Audit event:** `AUE_WAITID`.

Wait for selected child events and return structured siginfo.

**Implementation:** [waitid_nocancel](../../../xnu/bsd/kern/kern_exit.c#L3305). The shared body filters children/events using idtype/options, coordinates wait ownership and copies siginfo; options can observe state without consuming it. The ordinary wrapper tests cancellation.

## 433: pid_suspend

`int pid_suspend(int pid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L651) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Suspend or resume a selected process task under process-access policy.

**Implementation:** [pid_suspend](../../../xnu/bsd/kern/kern_proc.c#L6360). Checks POSIX/MAC/entitlement and possible task-access-port authorization, references the task, then invokes pid-suspend/resume machinery; socket resumption is separately coordinated.

## 434: pid_resume

`int pid_resume(int pid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L652) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Suspend or resume a selected process task under process-access policy.

**Implementation:** [pid_resume](../../../xnu/bsd/kern/kern_proc.c#L6587). Checks POSIX/MAC/entitlement and possible task-access-port authorization, references the task, then invokes pid-suspend/resume machinery; socket resumption is separately coordinated.

## 435: pid_hibernate

`int pid_hibernate(int pid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L654) · **Condition:** `(CONFIG_EMBEDDED)` · **Audit event:** `AUE_NULL`.

Request eligible process memory reclamation/freezing behavior.

**Implementation:** [pid_hibernate](../../../xnu/bsd/kern/kern_proc.c#L6697). Applies process-access/MAC checks and selects configured anonymous-pageout or memorystatus freeze/inactivity machinery; it is not whole-system hibernation image creation.

## 436: pid_shutdown_sockets

`int pid_shutdown_sockets(int pid, int level);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L659) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_NULL`.

Shut down sockets associated with selected process ownership under authorization.

**Implementation:** [pid_shutdown_sockets](../../../xnu/bsd/kern/kern_proc.c#L6868). Validates target identity/access and iterates the relevant processes/socket shutdown machinery; it does not simply kill the process or close every fd.

## 445: usrctl

`int usrctl(uint32_t flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L675) · **Condition:** `always` · **Audit event:** `AUE_USRCTL`.

Execute privileged userspace-reboot/logout control operations.

**Implementation:** [usrctl](../../../xnu/bsd/kern/kern_xxx.c#L282). Dispatches the requested command to `usrctl_full` or `usrctl_logout`; each path coordinates its own process/service shutdown protocol rather than executing a machine reset directly.

## 446: proc_rlimit_control

`int proc_rlimit_control(pid_t pid, int flavor, void *arg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L676) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Control extended process resource monitors beyond setrlimit's array.

**Implementation:** [proc_rlimit_control](../../../xnu/bsd/kern/kern_resource.c#L3509). Authorizes the target and dispatches selected monitor operations, including task CPU-usage monitoring; the payload/control ABI is selector-specific.

## 452: proc_uuid_policy

`int proc_uuid_policy(uint32_t operation, uuid_t uuid, size_t uuidlen, uint32_t flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L690) · **Condition:** `(CONFIG_PROC_UUID_POLICY)` · **Audit event:** `AUE_NULL`.

Manage policy entries associated with executable UUIDs.

**Implementation:** [proc_uuid_policy](../../../xnu/bsd/kern/proc_uuid_policy.c#L365). Checks privilege and command inputs, copies the UUID and invokes `proc_uuid_policy_kernel`; policies are stored/queried by UUID rather than attached solely to the calling fd.

## 454: system_override

`int system_override(uint64_t timeout, uint64_t flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L699) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Apply a bounded privileged override of selected system resource behavior.

**Implementation:** [system_override](../../../xnu/bsd/kern/kern_overrides.c#L97). Checks privilege and serializes begin/abort/end operations under the override mutex; the syscall can wait for its requested duration and then withdraw the override.

## 456: sfi_ctl

`int sfi_ctl(uint32_t operation, uint32_t sfi_class, uint64_t time, uint64_t *out_time) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L701) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Set/query system forced-idle windows or class off-times.

**Implementation:** [sfi_ctl](../../../xnu/bsd/kern/kern_sfi.c#L65). Privilege checks precede window/class selector dispatch to SFI setters/getters; query results are copied out and cancel operations remove scheduled constraints.

## 457: sfi_pidctl

`int sfi_pidctl(uint32_t operation, pid_t pid, uint32_t sfi_flags, uint32_t *out_sfi_flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L702) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Set/query a process's managed forced-idle policy.

**Implementation:** [sfi_pidctl](../../../xnu/bsd/kern/kern_sfi.c#L188). Finds/iterates authorized target processes, applies `proc_apply_sfi_managed` or queries task policy, and releases target references.

## 458: coalition

`int coalition(uint32_t operation, uint64_t *cid, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L704) · **Condition:** `(CONFIG_COALITIONS)` · **Audit event:** `AUE_NULL`.

Create, request termination of or reap a coalition.

**Implementation:** [coalition](../../../xnu/bsd/kern/sys_coalition.c#L224). Validates operation/type and privileged-coalition policy, then dispatches `coalition_create_syscall`, reap or terminate helpers; requesting termination and releasing all members are different stages.

## 459: coalition_info

`int coalition_info(uint32_t flavor, uint64_t *cid, void *buffer, size_t *bufsize) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L705) · **Condition:** `(CONFIG_COALITIONS)` · **Audit event:** `AUE_NULL`.

Read or update selected coalition information.

**Implementation:** [coalition_info](../../../xnu/bsd/kern/sys_coalition.c#L398). Copies the coalition ID, obtains a referenced coalition and dispatches resource usage, name, efficiency, PID-list or debug operations; releases the reference after output handling.

## 494: persona

`int persona(uint32_t operation, uint32_t flags, struct kpersona_info *info, uid_t *id, size_t *idlen, char *path) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L774) · **Condition:** `(CONFIG_PERSONAS)` · **Audit event:** `AUE_PERSONA`.

Create, remove, query or find persona identities through an operation selector.

**Implementation:** [persona](../../../xnu/bsd/kern/sys_persona.c#L468). Dispatches to `kpersona_*_syscall` helpers that validate/import identity data and manage persona object/reference lifetime. `CONFIG_PERSONAS` controls whether this declaration is selected.

## 532: coalition_ledger

`int coalition_ledger(uint32_t operation, uint64_t *cid, void *buffer, size_t *bufsize) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L841) · **Condition:** `(CONFIG_COALITIONS)` · **Audit event:** `AUE_NULL`.

Control selected coalition ledger limits.

**Implementation:** [coalition_ledger](../../../xnu/bsd/kern/sys_coalition.c#L477). Requires privilege, imports the coalition identity and dispatches ledger operations such as the logical-write limit, then drops the coalition reference.

## 538: task_inspect_for_pid

`int task_inspect_for_pid(mach_port_name_t target_tport, int pid, mach_port_name_t *t);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L850) · **Condition:** `always` · **Audit event:** `AUE_TASKINSPECTFORPID`.

Obtain a restricted inspect/read task capability for an authorized PID.

**Implementation:** [task_inspect_for_pid](../../../xnu/bsd/kern/kern_proc.c#L6122). Convert the supplied target task port, find and identify the process, check POSIX/MAC/task-access policy and create/copy out the requested task-port flavor. Neither entry promises a task-control right.

## 539: task_read_for_pid

`int task_read_for_pid(mach_port_name_t target_tport, int pid, mach_port_name_t *t);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L851) · **Condition:** `always` · **Audit event:** `AUE_TASKREADFORPID`.

Obtain a restricted inspect/read task capability for an authorized PID.

**Implementation:** [task_read_for_pid](../../../xnu/bsd/kern/kern_proc.c#L6244). Convert the supplied target task port, find and identify the process, check POSIX/MAC/task-access policy and create/copy out the requested task-port flavor. Neither entry promises a task-control right.

## 545: proc_info_extended_id

`int proc_info_extended_id(int32_t callnum, int32_t pid, uint32_t flavor, uint32_t flags, uint64_t ext_id, uint64_t arg, user_addr_t buffer, int32_t buffersize) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L857) · **Condition:** `always` · **Audit event:** `AUE_PROCINFO`.

Query/control process information through call/flavor selectors, optionally enforcing extended identity.

**Implementation:** [proc_info_extended_id](../../../xnu/bsd/kern/proc_info.c#L293). `proc_info_internal` routes PID, fd, region, list and other operation families, checks access and copies flavor-specific data. Extended identity helps reject stale PID selection; this catalog does not enumerate every proc flavor layout.

## 556: sys_coalition_policy_set

`int sys_coalition_policy_set(uint64_t cid, uint32_t flavor, uint32_t value);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L873) · **Condition:** `(CONFIG_COALITIONS)` · **Audit event:** `AUE_NULL`.

Set or query coalition policy such as suppression.

**Implementation:** [sys_coalition_policy_set](../../../xnu/bsd/kern/sys_coalition.c#L582). Checks the entitlement and coalition type, finds a referenced coalition and invokes the flavor-specific policy set/get helper before releasing it.

## 557: sys_coalition_policy_get

`int sys_coalition_policy_get(uint64_t cid, uint32_t flavor);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L874) · **Condition:** `(CONFIG_COALITIONS)` · **Audit event:** `AUE_NULL`.

Set or query coalition policy such as suppression.

**Implementation:** [sys_coalition_policy_get](../../../xnu/bsd/kern/sys_coalition.c#L619). Checks the entitlement and coalition type, finds a referenced coalition and invokes the flavor-specific policy set/get helper before releasing it.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
