# BSD syscalls: Filesystem namespace

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 9: link

`int link(user_addr_t path, user_addr_t link);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L54) · **Condition:** `always` · **Audit event:** `AUE_LINK`.

Create a hard link, with the *at form accepting directory descriptors and lookup flags.

**Implementation:** [link](../../../xnu/bsd/vfs/vfs_syscalls.c#L6201). `linkat_internal` resolves source/destination, checks authorization and same-filesystem constraints, then performs the vnode link operation and releases lookup references.

## 10: unlink

`int unlink(user_addr_t path) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L55) · **Condition:** `always` · **Audit event:** `AUE_UNLINK`.

Remove a pathname through the shared unlink implementation.

**Implementation:** [unlink](../../../xnu/bsd/vfs/vfs_syscalls.c#L6751). `unlinkat_internal` selects the operation's compatibility flags, resolves parent/target state and performs authorized vnode removal; name removal is distinct from final vnode/open-file destruction.

## 12: sys_chdir

`int sys_chdir(user_addr_t path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L57) · **Condition:** `always` · **Audit event:** `AUE_CHDIR`.

Set the current-directory context for the process or current pthread, respectively.

**Implementation:** [sys_chdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L4587). `common_chdir` resolves/checks a directory and selects process-wide or per-thread state according to the entry's mode; it replaces references rather than just storing the user pathname.

## 13: sys_fchdir

`int sys_fchdir(int fd);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L58) · **Condition:** `always` · **Audit event:** `AUE_FCHDIR`.

Set process or per-thread current-directory context from an open descriptor.

**Implementation:** [sys_fchdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L4479). The shared `fchdir` helper obtains and checks the descriptor's directory vnode and updates the selected directory context with reference ownership.

## 14: mknod

`int mknod(user_addr_t path, int mode, int dev);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L59) · **Condition:** `always` · **Audit event:** `AUE_MKNOD`.

Create a filesystem node, including eligible special-device nodes.

**Implementation:** [mknod](../../../xnu/bsd/vfs/vfs_syscalls.c#L5693). Builds vnode attributes from mode/device inputs and calls `mknodat_internal` using current-directory or directory-fd lookup semantics.

## 56: revoke

`int revoke(char *path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L110) · **Condition:** `always` · **Audit event:** `AUE_REVOKE`.

Invalidate access through eligible character/block-device vnodes and aliases.

**Implementation:** [revoke](../../../xnu/bsd/vfs/vfs_syscalls.c#L11260). Resolves the vnode, checks type/mount/ownership/MAC restrictions, and invokes `VNOP_REVOKE`; it does not implement generic regular-file descriptor revocation.

## 57: symlink

`int symlink(char *path, char *link);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L111) · **Condition:** `always` · **Audit event:** `AUE_SYMLINK`.

Create a symbolic link containing the supplied target string.

**Implementation:** [symlink](../../../xnu/bsd/vfs/vfs_syscalls.c#L6389). `symlinkat_internal` imports the link content and resolves/creates the destination under the selected directory context, then dispatches the vnode creation operation.

## 58: readlink

`int readlink(char *path, char *buf, int count);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L112) · **Condition:** `always` · **Audit event:** `AUE_READLINK`.

Read a symlink's stored target bytes without following its final component.

**Implementation:** [readlink](../../../xnu/bsd/vfs/vfs_syscalls.c#L7845). `readlinkat_internal` uses the requested lookup base and a user buffer/uio, then calls the vnode readlink operation; returned bytes need not include a terminating NUL.

## 61: chroot

`int chroot(user_addr_t path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L115) · **Condition:** `always` · **Audit event:** `AUE_CHROOT`.

Change the process's root-directory lookup context.

**Implementation:** [chroot](../../../xnu/bsd/vfs/vfs_syscalls.c#L4622). Requires the local privilege/entitlement checks, resolves the directory through `change_dir`, applies MAC policy and replaces root/cwd-related vnode state; it is not a separate filesystem namespace implementation.

## 128: rename

`int rename(char *from, char *to) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L206) · **Condition:** `always` · **Audit event:** `AUE_RENAME`.

Rename filesystem names; *at variants supply directory descriptors and the extended variant supplies operation flags.

**Implementation:** [rename](../../../xnu/bsd/vfs/vfs_syscalls.c#L10347). `renameat_internal` coordinates both lookups, compound-operation/retry paths, authorization and the filesystem rename operation. Extended swap/exclusive semantics are flag-selected branches, not separate syscalls.

## 132: mkfifo

`int mkfifo(user_addr_t path, int mode);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L210) · **Condition:** `always` · **Audit event:** `AUE_MKFIFO`.

Create a named pipe node, with optional directory-fd or extended security attributes.

**Implementation:** [mkfifo](../../../xnu/bsd/vfs/vfs_syscalls.c#L5829). Builds vnode creation attributes and uses `mkfifo1`; the extended form first imports/frees filesec storage. Opening the resulting FIFO later constructs its data-transfer state.

## 136: mkdir

`int mkdir(user_addr_t path, int mode);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L220) · **Condition:** `always` · **Audit event:** `AUE_MKDIR`.

Create a directory, with optional directory-relative lookup or extended security attributes.

**Implementation:** [mkdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L10547). Builds creation attributes and calls `mkdir1at`; the extended form imports/frees filesec data. Namespace publication occurs in the filesystem operation, not at argument copyin.

## 137: rmdir

`int rmdir(char *path) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L221) · **Condition:** `always` · **Audit event:** `AUE_RMDIR`.

Remove an empty directory by pathname.

**Implementation:** [rmdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L10895). `rmdirat_internal` coordinates directory lookup/authorization and vnode removal, including the normal lookup cleanup.

## 205: undelete

`int undelete(user_addr_t path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L301) · **Condition:** `always` · **Audit event:** `AUE_UNDELETE`.

Retain a historical undelete syscall number without an implementation.

**Implementation:** [undelete](../../../xnu/bsd/vfs/vfs_syscalls.c#L6408). The local handler immediately returns `ENOTSUP`; no name restoration or filesystem operation occurs.

## 223: exchangedata

`int exchangedata(const char *path1, const char *path2, u_long options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L331) · **Condition:** `always` · **Audit event:** `AUE_EXCHANGEDATA`.

Exchange data between eligible regular files.

**Implementation:** [exchangedata](../../../xnu/bsd/vfs/vfs_syscalls.c#L11510). Resolves both vnodes, authorizes the exchange, handles lease/event bookkeeping and dispatches the filesystem exchange operation; its storage implementation is external for absent filesystems.

## 226: delete

`int delete(user_addr_t path) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L334) · **Condition:** `always` · **Audit event:** `AUE_DELETE`.

Remove a pathname through the shared unlink implementation.

**Implementation:** [delete](../../../xnu/bsd/vfs/vfs_syscalls.c#L6741). `unlinkat_internal` selects the operation's compatibility flags, resolves parent/target state and performs authorized vnode removal; name removal is distinct from final vnode/open-file destruction.

## 227: copyfile

`int copyfile(char *from, char *to, int mode, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L335) · **Condition:** `always` · **Audit event:** `AUE_COPYFILE`.

Request the filesystem-level copyfile operation between names.

**Implementation:** [copyfile](../../../xnu/bsd/vfs/vfs_syscalls.c#L9026). Resolves source/destination, checks MAC/authorization and leases, and invokes `VNOP_COPYFILE`; this syscall is not the entire userspace copyfile library's fallback implementation.

## 291: mkfifo_extended

`int mkfifo_extended(user_addr_t path, uid_t uid, gid_t gid, int mode, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L438) · **Condition:** `always` · **Audit event:** `AUE_MKFIFO_EXTENDED`.

Create a named pipe node, with optional directory-fd or extended security attributes.

**Implementation:** [mkfifo_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L5791). Builds vnode creation attributes and uses `mkfifo1`; the extended form first imports/frees filesec storage. Opening the resulting FIFO later constructs its data-transfer state.

## 292: mkdir_extended

`int mkdir_extended(user_addr_t path, uid_t uid, gid_t gid, int mode, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L439) · **Condition:** `always` · **Audit event:** `AUE_MKDIR_EXTENDED`.

Create a directory, with optional directory-relative lookup or extended security attributes.

**Implementation:** [mkdir_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L10517). Builds creation attributes and calls `mkdir1at`; the extended form imports/frees filesec data. Namespace publication occurs in the filesystem operation, not at argument copyin.

## 348: __pthread_chdir

`int __pthread_chdir(user_addr_t path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L529) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Set the current-directory context for the process or current pthread, respectively.

**Implementation:** [__pthread_chdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L4610). `common_chdir` resolves/checks a directory and selects process-wide or per-thread state according to the entry's mode; it replaces references rather than just storing the user pathname.

## 349: __pthread_fchdir

`int __pthread_fchdir(int fd);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L530) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Set process or per-thread current-directory context from an open descriptor.

**Implementation:** [__pthread_fchdir](../../../xnu/bsd/vfs/vfs_syscalls.c#L4485). The shared `fchdir` helper obtains and checks the descriptor's directory vnode and updates the selected directory context with reference ownership.

## 462: clonefileat

`int clonefileat(int src_dirfd, user_addr_t src, int dst_dirfd, user_addr_t dst, uint32_t flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L716) · **Condition:** `always` · **Audit event:** `AUE_CLONEFILEAT`.

Clone a source pathname into a destination directory/name.

**Implementation:** [clonefileat](../../../xnu/bsd/vfs/vfs_syscalls.c#L9399). Resolves source identity, then `clonefile_internal` validates and dispatches cloning to the filesystem. Copy-on-write extent behavior depends on that filesystem implementation.

## 465: renameat

`int renameat(int fromfd, char *from, int tofd, char *to) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L719) · **Condition:** `always` · **Audit event:** `AUE_RENAMEAT`.

Rename filesystem names; *at variants supply directory descriptors and the extended variant supplies operation flags.

**Implementation:** [renameat](../../../xnu/bsd/vfs/vfs_syscalls.c#L10369). `renameat_internal` coordinates both lookups, compound-operation/retry paths, authorization and the filesystem rename operation. Extended swap/exclusive semantics are flag-selected branches, not separate syscalls.

## 471: linkat

`int linkat(int fd1, user_addr_t path, int fd2, user_addr_t link, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L725) · **Condition:** `always` · **Audit event:** `AUE_LINKAT`.

Create a hard link, with the *at form accepting directory descriptors and lookup flags.

**Implementation:** [linkat](../../../xnu/bsd/vfs/vfs_syscalls.c#L6208). `linkat_internal` resolves source/destination, checks authorization and same-filesystem constraints, then performs the vnode link operation and releases lookup references.

## 472: unlinkat

`int unlinkat(int fd, user_addr_t path, int flag) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L726) · **Condition:** `always` · **Audit event:** `AUE_UNLINKAT`.

Remove a directory-relative name or, with the directory flag, a directory.

**Implementation:** [unlinkat](../../../xnu/bsd/vfs/vfs_syscalls.c#L6758). Selects `rmdirat_internal` for directory removal or `unlinkat_internal` otherwise, retaining the caller's directory-fd/flag semantics.

## 473: readlinkat

`int readlinkat(int fd, user_addr_t path, user_addr_t buf, size_t bufsize);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L727) · **Condition:** `always` · **Audit event:** `AUE_READLINKAT`.

Read a symlink's stored target bytes without following its final component.

**Implementation:** [readlinkat](../../../xnu/bsd/vfs/vfs_syscalls.c#L7856). `readlinkat_internal` uses the requested lookup base and a user buffer/uio, then calls the vnode readlink operation; returned bytes need not include a terminating NUL.

## 474: symlinkat

`int symlinkat(user_addr_t *path1, int fd, user_addr_t path2);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L728) · **Condition:** `always` · **Audit event:** `AUE_SYMLINKAT`.

Create a symbolic link containing the supplied target string.

**Implementation:** [symlinkat](../../../xnu/bsd/vfs/vfs_syscalls.c#L6396). `symlinkat_internal` imports the link content and resolves/creates the destination under the selected directory context, then dispatches the vnode creation operation.

## 475: mkdirat

`int mkdirat(int fd, user_addr_t path, int mode);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L729) · **Condition:** `always` · **Audit event:** `AUE_MKDIRAT`.

Create a directory, with optional directory-relative lookup or extended security attributes.

**Implementation:** [mkdirat](../../../xnu/bsd/vfs/vfs_syscalls.c#L10559). Builds creation attributes and calls `mkdir1at`; the extended form imports/frees filesec data. Namespace publication occurs in the filesystem operation, not at argument copyin.

## 488: renameatx_np

`int renameatx_np(int fromfd, char *from, int tofd, char *to, u_int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L751) · **Condition:** `always` · **Audit event:** `AUE_RENAMEAT`.

Rename filesystem names; *at variants supply directory descriptors and the extended variant supplies operation flags.

**Implementation:** [renameatx_np](../../../xnu/bsd/vfs/vfs_syscalls.c#L10354). `renameat_internal` coordinates both lookups, compound-operation/retry paths, authorization and the filesystem rename operation. Extended swap/exclusive semantics are flag-selected branches, not separate syscalls.

## 517: fclonefileat

`int fclonefileat(int src_fd, int dst_dirfd, user_addr_t dst, uint32_t flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L820) · **Condition:** `always` · **Audit event:** `AUE_FCLONEFILEAT`.

Clone an open source file into a destination directory/name.

**Implementation:** [fclonefileat](../../../xnu/bsd/vfs/vfs_syscalls.c#L9445). Pins the source fileproc/vnode, calls `clonefile_internal`, and drops both references on completion; filesystem cloning remains behind the VNOP boundary.

## 551: freadlink

`int freadlink(int fd, user_addr_t buf, user_size_t bufsize);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L867) · **Condition:** `always` · **Audit event:** `AUE_FREADLINK`.

Read symlink content through an existing descriptor.

**Implementation:** [freadlink](../../../xnu/bsd/vfs/vfs_syscalls.c#L7817). Takes a vnode reference from the descriptor, passes that vnode to `readlinkat_internal`, and drops it after the read.

## 553: mkfifoat

`int mkfifoat(int fd, user_addr_t path, int mode);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L869) · **Condition:** `always` · **Audit event:** `AUE_MKFIFOAT`.

Create a named pipe node, with optional directory-fd or extended security attributes.

**Implementation:** [mkfifoat](../../../xnu/bsd/vfs/vfs_syscalls.c#L5840). Builds vnode creation attributes and uses `mkfifo1`; the extended form first imports/frees filesec storage. Opening the resulting FIFO later constructs its data-transfer state.

## 554: mknodat

`int mknodat(int fd, user_addr_t path, int mode, int dev);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L870) · **Condition:** `always` · **Audit event:** `AUE_MKNODAT`.

Create a filesystem node, including eligible special-device nodes.

**Implementation:** [mknodat](../../../xnu/bsd/vfs/vfs_syscalls.c#L5705). Builds vnode attributes from mode/device inputs and calls `mknodat_internal` using current-directory or directory-fd lookup semantics.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
