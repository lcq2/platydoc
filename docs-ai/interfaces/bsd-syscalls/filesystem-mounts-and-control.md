# BSD syscalls: Filesystem mounts and control

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 18: getfsstat

`int getfsstat(user_addr_t buf, int bufsize, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L63) · **Condition:** `always` · **Audit event:** `AUE_GETFSSTAT`.

Enumerate mounted filesystem statistics, optionally with MAC label output.

**Implementation:** [getfsstat](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L4027). Use `vfs_iterate` and size-limited output callbacks; the legacy entry delegates to `__mac_getfsstat`, while the 64-bit entry selects its own record layout.

## 36: sync

`int sync(void);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L90) · **Condition:** `always` · **Audit event:** `AUE_SYNC`.

Request synchronization of mounted filesystems and report dirty-buffer accounting internally.

**Implementation:** [sync](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3459). `vfs_iterate` visits eligible mounts for sync work; VM/buffer statistics are consulted separately. It is not a per-fd completion token or a universal hardware durability guarantee.

## 95: fsync

`int fsync(int fd);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L153) · **Condition:** `always` · **Audit event:** `AUE_FSYNC`.

Synchronize an open file; fdatasync selects the data-focused common mode.

**Implementation:** [fsync](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L8917). All reach `fsync_common`, which performs file/vnode synchronization. Ordinary fsync and fdatasync test cancellation; fsync_nocancel directly enters the common operation.

## 155: nfssvc

`int nfssvc(int flag, caddr_t argp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L241) · **Condition:** `(NFSSERVER)` · **Audit event:** `AUE_NFS_SVC`.

Operate the in-kernel NFS server using an operation flag set.

**Implementation:** [nfssvc](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L589). Privilege/MAC checks precede socket installation, server-worker entry, export management or statistics helpers such as `nfssvc_addsock`, `nfssvc_nfsd` and `nfssvc_export`; peer/server protocol work lives in the NFS implementation.

## 157: statfs

`int statfs(char *path, struct statfs *buf);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L247) · **Condition:** `always` · **Audit event:** `AUE_STATFS`.

Read filesystem statistics by path or open descriptor using the legacy ABI.

**Implementation:** [statfs](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3753). Resolve a vnode and call `statfs_internal`, which updates/collects mount information and copies the selected filesystem-stat structure.

## 158: fstatfs

`int fstatfs(int fd, struct statfs *buf);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L248) · **Condition:** `always` · **Audit event:** `AUE_FSTATFS`.

Read filesystem statistics by path or open descriptor using the legacy ABI.

**Implementation:** [fstatfs](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3782). Resolve a vnode and call `statfs_internal`, which updates/collects mount information and copies the selected filesystem-stat structure.

## 159: unmount

`int unmount(user_addr_t path, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L249) · **Condition:** `always` · **Audit event:** `AUE_UNMOUNT`.

Unmount a filesystem selected by path or descriptor.

**Implementation:** [unmount](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L2824). Resolve and retain the mount, apply mount/MAC checks and call `safedounmount`; busy/drain and failed-unmount state belong to the common VFS teardown path.

## 161: getfh

`int getfh(char *fname, fhandle_t *fhp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L253) · **Condition:** `(NFSSERVER)` · **Audit event:** `AUE_NFS_GETFH`.

Obtain an exported filesystem handle for a pathname.

**Implementation:** [getfh](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L285). Resolves the vnode and export context under NFS export protection, translates to an NFS filehandle and copies the bounded result out; requires appropriate privilege/server support.

## 164: funmount

`int funmount(int fd, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L260) · **Condition:** `always` · **Audit event:** `AUE_FUNMOUNT`.

Unmount a filesystem selected by path or descriptor.

**Implementation:** [funmount](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L2876). Resolve and retain the mount, apply mount/MAC checks and call `safedounmount`; busy/drain and failed-unmount state belong to the common VFS teardown path.

## 165: quotactl

`int quotactl(const char *path, int cmd, int uid, caddr_t arg);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L261) · **Condition:** `always` · **Audit event:** `AUE_QUOTACTL`.

Manage or query filesystem quota state.

**Implementation:** [quotactl](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3609), [quotactl](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3716). Under `QUOTA`, the handler imports command-specific data and invokes `VFS_QUOTACTL` while holding a mount reference; without it the alternate body returns `EOPNOTSUPP`. Commands include quota-file/control and per-ID usage/limit operations.

## 167: mount

`int mount(char *type, char *path, int flags, caddr_t data);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L263) · **Condition:** `always` · **Audit event:** `AUE_MOUNT`.

Mount or update a filesystem, with optional MAC-label input in the extended entry.

**Implementation:** [mount](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L396). `mount` forwards to `__mac_mount`; the latter imports type/options, resolves the mount point and enters `mount_common`/filesystem mount dispatch, coordinating authorization and publication.

## 187: fdatasync

`int fdatasync(int fd);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L283) · **Condition:** `always` · **Audit event:** `AUE_FDATASYNC`.

Synchronize an open file; fdatasync selects the data-focused common mode.

**Implementation:** [fdatasync](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L8943). All reach `fsync_common`, which performs file/vnode synchronization. Ordinary fsync and fdatasync test cancellation; fsync_nocancel directly enters the common operation.

## 242: fsctl

`int fsctl(const char *path, u_long cmd, caddr_t data, u_int options);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L350) · **Condition:** `always` · **Audit event:** `AUE_FSCTL`.

Issue filesystem-specific control commands by path or descriptor.

**Implementation:** [fsctl](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13701). Resolve/pin the vnode, apply mount-control MAC checks and call `fsctl_internal`. It rejects character/block vnodes with `ENOTTY`, decodes common commands and forwards permitted filesystem-specific controls through `VNOP_IOCTL`. Output copyout occurs after the operation and can fail independently. This catalog scopes the multiplexor, not every filesystem-private command. See [type rejection](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13398) and [filesystem dispatch/output](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13679).

## 245: ffsctl

`int ffsctl(int fd, u_long cmd, caddr_t data, u_int options);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L353) · **Condition:** `always` · **Audit event:** `AUE_FFSCTL`.

Issue filesystem-specific control commands by path or descriptor.

**Implementation:** [ffsctl](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13760). Resolve/pin the vnode, apply mount-control MAC checks and call `fsctl_internal`. It rejects character/block vnodes with `ENOTTY`, decodes common commands and forwards permitted filesystem-specific controls through `VNOP_IOCTL`. Output copyout occurs after the operation and can fail independently. This catalog scopes the multiplexor, not every filesystem-private command. See [type rejection](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13398) and [filesystem dispatch/output](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L13679).

## 248: fhopen

`int fhopen(const struct fhandle *u_fhp, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L358) · **Condition:** `(NFSSERVER)` · **Audit event:** `AUE_FHOPEN`.

Open an exported object using a filehandle.

**Implementation:** [fhopen](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L425). Imports the handle, resolves it with `nfsrv_fhtovp` under export protection, then validates vnode/open rights and constructs descriptor state.

## 345: statfs64

`int statfs64(char *path, struct statfs64 *buf);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L526) · **Condition:** `always` · **Audit event:** `AUE_STATFS64`.

Read filesystem statistics using the 64-bit statfs layout.

**Implementation:** [statfs64](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3845). Pin the vnode/mount, apply mount-stat authorization, call `vfs_update_vfsstat`/`vfs_get_statfs64`, and copy the assembled record out.

## 346: fstatfs64

`int fstatfs64(int fd, struct statfs64 *buf);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L527) · **Condition:** `always` · **Audit event:** `AUE_FSTATFS64`.

Read filesystem statistics using the 64-bit statfs layout.

**Implementation:** [fstatfs64](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L3906). Pin the vnode/mount, apply mount-stat authorization, call `vfs_update_vfsstat`/`vfs_get_statfs64`, and copy the assembled record out.

## 347: getfsstat64

`int getfsstat64(user_addr_t buf, int bufsize, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L528) · **Condition:** `always` · **Audit event:** `AUE_GETFSSTAT64`.

Enumerate mounted filesystem statistics, optionally with MAC label output.

**Implementation:** [getfsstat64](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L4201). Use `vfs_iterate` and size-limited output callbacks; the legacy entry delegates to `__mac_getfsstat`, while the 64-bit entry selects its own record layout.

## 408: fsync_nocancel

`int fsync_nocancel(int fd) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L609) · **Condition:** `always` · **Audit event:** `AUE_FSYNC`.

Synchronize an open file; fdatasync selects the data-focused common mode.

**Implementation:** [fsync_nocancel](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L8932). All reach `fsync_common`, which performs file/vnode synchronization. Ordinary fsync and fdatasync test cancellation; fsync_nocancel directly enters the common operation.

## 424: __mac_mount

`int __mac_mount(char *type, char *path, int flags, caddr_t data, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L638) · **Condition:** `always` · **Audit event:** `AUE_MAC_MOUNT`.

Mount or update a filesystem, with optional MAC-label input in the extended entry.

**Implementation:** [__mac_mount](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L939). `mount` forwards to `__mac_mount`; the latter imports type/options, resolves the mount point and enters `mount_common`/filesystem mount dispatch, coordinating authorization and publication.

## 425: __mac_get_mount

`int __mac_get_mount(char *path, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L640) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_MOUNT`.

Read a mount's externalized MAC label by pathname.

**Implementation:** [__mac_get_mount](../../../platydoc-data/xnu/security/mac_base.c#L1644). Resolve/retain the mount, invoke `mac_mount_label_get`, and drop the mount reference after output handling.

## 426: __mac_getfsstat

`int __mac_getfsstat(user_addr_t buf, int bufsize, user_addr_t mac, int macsize, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L644) · **Condition:** `always` · **Audit event:** `AUE_MAC_GETFSSTAT`.

Enumerate mounted filesystem statistics, optionally with MAC label output.

**Implementation:** [__mac_getfsstat](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L4059). Use `vfs_iterate` and size-limited output callbacks; the legacy entry delegates to `__mac_getfsstat`, while the 64-bit entry selects its own record layout.

## 455: vfs_purge

`int vfs_purge(void);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L700) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Request privileged purge of filesystem caches/file-backed pager resources.

**Implementation:** [vfs_purge](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L14783). Iterates VFS purge callbacks and calls `vm_purge_filebacked_pagers`; it is broader than closing descriptors and does not imply every referenced vnode can be destroyed.

## 518: fs_snapshot

`int fs_snapshot(uint32_t op, int dirfd, user_addr_t name1, user_addr_t name2, user_addr_t data, uint32_t flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L821) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Manage filesystem snapshots through a directory fd and operation selector.

**Implementation:** [fs_snapshot](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L15441). Checks snapshot authorization, resolves mount/root objects and dispatches create/delete/rename/mount/revert-related helpers. Actual snapshot storage is a filesystem operation, not reconstructed APFS code.

## 526: fmount

`int fmount(const char *type, int fd, int flags, void *data);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L834) · **Condition:** `always` · **Audit event:** `AUE_FMOUNT`.

Mount using an already-open mount-point descriptor.

**Implementation:** [fmount](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L409). Imports the filesystem type, obtains the vnode and parent/path context, then calls `mount_common`; supported update cases can use the shared MAC mount path.

## 537: pivot_root

`int pivot_root(const char *new_rootfs_path_before, const char *old_rootfs_path_after);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L849) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Switch the root filesystem under the supported platform/authorization configuration.

**Implementation:** [pivot_root](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L4719), [pivot_root](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L4811). Under `XNU_TARGET_OS_OSX`, the handler validates privileged inputs and calls `vfs_switch_root` after vnode/ioctl checks; the alternate definition invokes `nosys`. It is not enabled uniformly merely because a master number exists.

## 549: graftdmg

`int graftdmg(int dmg_fd, const char *mountdir, uint32_t graft_type, graftdmg_args_un *gda);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L865) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Graft an authenticated disk-image/cryptex filesystem at a mount location.

**Implementation:** [graftdmg](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L743). Imports the type-specific argument union, pins source/target vnodes, checks entitlements/MAC and calls the secure-boot graft helper, then sends policy notifications and releases lookup state.

## 555: ungraftdmg

`int ungraftdmg(const char *mountdir, uint64_t flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L871) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Remove a grafted image association.

**Implementation:** [ungraftdmg](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L850). Checks entitlement/MAC policy, resolves the target, issues the filesystem ungraft ioctl and performs notification/reference cleanup.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
