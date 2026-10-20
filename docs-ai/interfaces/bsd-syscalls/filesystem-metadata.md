# BSD syscalls: Filesystem metadata

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 15: chmod

`int chmod(user_addr_t path, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L60) · **Condition:** `always` · **Audit event:** `AUE_CHMOD`.

Change permission mode for a pathname, optionally relative to a directory fd.

**Implementation:** [chmod](../../../xnu/bsd/vfs/vfs_syscalls.c#L8291). `fchmodat_internal` applies lookup flags and invokes the shared authorization/setattr path; directory-relative selection is not an alternate credential model.

## 16: chown

`int chown(user_addr_t path, int uid, int gid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L61) · **Condition:** `always` · **Audit event:** `AUE_CHOWN`.

Change owner/group of a pathname, optionally relative to a directory fd.

**Implementation:** [chown](../../../xnu/bsd/vfs/vfs_syscalls.c#L8501). `fchownat_internal` resolves with the wrapper's follow and directory-base rules, then applies vnode ownership authorization and attributes.

## 33: access

`int access(user_addr_t path, int flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L87) · **Condition:** `always` · **Audit event:** `AUE_ACCESS`.

Test requested pathname access using access-check credential semantics, optionally relative to a directory fd.

**Implementation:** [access](../../../xnu/bsd/vfs/vfs_syscalls.c#L7348). `faccessat_internal` performs the requested lookup/flag handling and permission test; it is not a reservation guaranteeing that a later open will still succeed.

## 34: chflags

`int chflags(char *path, int flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L88) · **Condition:** `always` · **Audit event:** `AUE_CHFLAGS`.

Change filesystem flags by pathname or descriptor.

**Implementation:** [chflags](../../../xnu/bsd/vfs/vfs_syscalls.c#L7942). Resolve/pin the vnode, handle applicable lease breaking, and call `chflags1`; allowed flags and ownership checks are enforced in the common attribute path.

## 35: fchflags

`int fchflags(int fd, int flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L89) · **Condition:** `always` · **Audit event:** `AUE_FCHFLAGS`.

Change filesystem flags by pathname or descriptor.

**Implementation:** [fchflags](../../../xnu/bsd/vfs/vfs_syscalls.c#L7981). Resolve/pin the vnode, handle applicable lease breaking, and call `chflags1`; allowed flags and ownership checks are enforced in the common attribute path.

## 60: umask

`int umask(int newmask);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L114) · **Condition:** `always` · **Audit event:** `AUE_UMASK`.

Replace the process creation mask and, for the extended form, associated security mask state.

**Implementation:** [umask](../../../xnu/bsd/vfs/vfs_syscalls.c#L11246). Both enter `umask1`, which updates the creation policy used by later vnode creation; existing file permissions are not changed.

## 123: fchown

`int fchown(int fd, int uid, int gid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L201) · **Condition:** `always` · **Audit event:** `AUE_FCHOWN`.

Change ownership of an open file.

**Implementation:** [fchown](../../../xnu/bsd/vfs/vfs_syscalls.c#L8530). Pins the descriptor vnode, calls `vn_chown_internal`, then releases the vnode and descriptor references.

## 124: fchmod

`int fchmod(int fd, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L202) · **Condition:** `always` · **Audit event:** `AUE_FCHMOD`.

Change permission mode through an open descriptor.

**Implementation:** [fchmod](../../../xnu/bsd/vfs/vfs_syscalls.c#L8382). Builds a vnode-attribute request and passes it to `fchmod1`, which resolves the descriptor vnode and performs the authorized change.

## 138: utimes

`int utimes(char *path, struct timeval *tptr);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L222) · **Condition:** `always` · **Audit event:** `AUE_UTIMES`.

Set file timestamps by pathname or descriptor.

**Implementation:** [utimes](../../../xnu/bsd/vfs/vfs_syscalls.c#L8651). `getutimes` imports/converts the supplied time values, then `setutimes` performs the vnode update after lookup and lease handling.

## 139: futimes

`int futimes(int fd, struct timeval *tptr);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L223) · **Condition:** `always` · **Audit event:** `AUE_FUTIMES`.

Set file timestamps by pathname or descriptor.

**Implementation:** [futimes](../../../xnu/bsd/vfs/vfs_syscalls.c#L8704). `getutimes` imports/converts the supplied time values, then `setutimes` performs the vnode update after lookup and lease handling.

## 188: stat

`int stat(user_addr_t path, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L284) · **Condition:** `always` · **Audit event:** `AUE_STAT`.

Read status for a pathname while following its final symlink, using the declared legacy/64-bit and optional filesec ABI.

**Implementation:** [stat](../../../xnu/bsd/vfs/vfs_syscalls.c#L7591). `fstatat_internal` resolves the vnode and marshals status/security output according to flags supplied by each wrapper; size/ABI variants share lookup and attribute collection rather than a different filesystem operation.

## 189: sys_fstat

`int sys_fstat(int fd, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L285) · **Condition:** `always` · **Audit event:** `AUE_FSTAT`.

Read status from an open descriptor using its declared status/filesec ABI.

**Implementation:** [sys_fstat](../../../xnu/bsd/kern/kern_descrip.c#L5844). The shared `fstat` helper references the fileproc and invokes the file type's stat operation; wrappers select layout and extended-security arguments.

## 190: lstat

`int lstat(user_addr_t path, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L286) · **Condition:** `always` · **Audit event:** `AUE_LSTAT`.

Read status for the final pathname component itself, including a symlink, using the declared ABI.

**Implementation:** [lstat](../../../xnu/bsd/vfs/vfs_syscalls.c#L7656). `fstatat_internal` receives no-follow semantics and the wrapper's legacy/64-bit/filesec options, then collects and copies out vnode attributes.

## 191: pathconf

`int pathconf(char *path, int name);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L287) · **Condition:** `always` · **Audit event:** `AUE_PATHCONF`.

Query a path-associated implementation limit.

**Implementation:** [pathconf](../../../xnu/bsd/vfs/vfs_syscalls.c#L7734). Resolves a vnode and invokes `vn_pathconf`, then releases pathname and vnode references; the requested name selects the queried limit.

## 192: sys_fpathconf

`int sys_fpathconf(int fd, int name);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L288) · **Condition:** `always` · **Audit event:** `AUE_FPATHCONF`.

Query an implementation limit through a descriptor.

**Implementation:** [sys_fpathconf](../../../xnu/bsd/kern/kern_descrip.c#L5913). Looks up the fileproc, obtains its vnode where applicable, and calls `vn_pathconf` with the selected name before dropping references.

## 196: getdirentries

`int getdirentries(int fd, char *buf, u_int count, long *basep);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L292) · **Condition:** `always` · **Audit event:** `AUE_GETDIRENTRIES`.

Read directory records and return the enumeration base offset using the declared record ABI.

**Implementation:** [getdirentries](../../../xnu/bsd/vfs/vfs_syscalls.c#L11145). `getdirentries_common` drives directory reading and shared offset handling; wrappers choose legacy/64-bit layout and copy the resulting base offset out separately.

## 200: truncate

`int truncate(char *path, off_t length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L296) · **Condition:** `always` · **Audit event:** `AUE_TRUNCATE`.

Change a named file's length.

**Implementation:** [truncate](../../../xnu/bsd/vfs/vfs_syscalls.c#L8809). Validates the requested length, resolves the vnode and invokes `truncate_internal`; shrinking/growing cache and filesystem state is delegated to the vnode/UBC path.

## 201: ftruncate

`int ftruncate(int fd, off_t length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L297) · **Condition:** `always` · **Audit event:** `AUE_FTRUNCATE`.

Change the length of an open file or POSIX shared-memory object.

**Implementation:** [ftruncate](../../../xnu/bsd/vfs/vfs_syscalls.c#L8841). Dispatches POSIX shared memory to `pshm_truncate`; eligible vnode descriptors pass validation and `truncate_internal`, with fileproc/vnode references held across the operation.

## 217: fsgetpath_ext

`user_ssize_t fsgetpath_ext(user_addr_t buf, size_t bufsize, user_addr_t fsid, uint64_t objid, uint32_t options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L325) · **Condition:** `always` · **Audit event:** `AUE_FSGETPATH_EXTENDED`.

Resolve filesystem/object identity to a pathname, with extended options where declared.

**Implementation:** [fsgetpath_ext](../../../xnu/bsd/vfs/vfs_syscalls.c#L14471). `fsgetpath_extended` performs identity lookup and path construction through `fsgetpath_internal`, then copies the result to the supplied buffer subject to access and size checks.

## 220: getattrlist

`int getattrlist(const char *path, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, u_long options) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L328) · **Condition:** `always` · **Audit event:** `AUE_GETATTRLIST`.

Read a requested bitmap of filesystem attributes into a packed user buffer.

**Implementation:** [getattrlist](../../../xnu/bsd/vfs/vfs_attrlist.c#L3627). Imports `attrlist`, resolves through `getattrlistat_internal`, and assembles the selected attributes using the user ABI, options and directory base.

## 221: setattrlist

`int setattrlist(const char *path, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, u_long options) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L329) · **Condition:** `always` · **Audit event:** `AUE_SETATTRLIST`.

Set a bitmap-selected packed set of filesystem attributes by path, directory-relative path or descriptor.

**Implementation:** [setattrlist](../../../xnu/bsd/vfs/vfs_attrlist.c#L4931). Each entry resolves/pins its vnode, handles lease interaction and calls `setattrlist_internal`, which validates bitmap/layout and performs the attribute update.

## 222: getdirentriesattr

`int getdirentriesattr(int fd, struct attrlist *alist, void *buffer, size_t buffersize, u_long *count, u_long *basep, u_long *newstate, u_long options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L330) · **Condition:** `always` · **Audit event:** `AUE_GETDIRENTRIESATTR`.

Enumerate directory entries with requested attributes through the older packed interface.

**Implementation:** [getdirentriesattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L11326). Imports attrlist/count inputs, holds the directory fileglob offset lock, drives the directory-attribute vnode operation and copies updated enumeration/output counts back.

## 225: searchfs

`int searchfs(const char *path, struct fssearchblock *searchblock, uint32_t *nummatches, uint32_t scriptcode, uint32_t options, struct searchstate *state);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L333) · **Condition:** `always` · **Audit event:** `AUE_SEARCHFS`.

Search a filesystem using packed attribute predicates and continuation state.

**Implementation:** [searchfs](../../../xnu/bsd/vfs/vfs_syscalls.c#L11690), [searchfs](../../../xnu/bsd/vfs/vfs_syscalls.c#L11979). Under `CONFIG_SEARCHFS`, the handler imports search parameters, resolves the filesystem root and invokes `VNOP_SEARCHFS` with a user `uio`; without it the alternate body returns `ENOTSUP`. Matching indexes inside absent filesystems are not implemented here.

## 228: fgetattrlist

`int fgetattrlist(int fd, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, u_long options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L336) · **Condition:** `always` · **Audit event:** `AUE_FGETATTRLIST`.

Read packed filesystem attributes from an open vnode descriptor.

**Implementation:** [fgetattrlist](../../../xnu/bsd/vfs/vfs_attrlist.c#L3521). Obtains a typed fileproc and vnode reference, imports the requested bitmap and invokes `getattrlist_internal`, then releases both references.

## 229: fsetattrlist

`int fsetattrlist(int fd, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, u_long options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L337) · **Condition:** `always` · **Audit event:** `AUE_FSETATTRLIST`.

Set a bitmap-selected packed set of filesystem attributes by path, directory-relative path or descriptor.

**Implementation:** [fsetattrlist](../../../xnu/bsd/vfs/vfs_attrlist.c#L5037). Each entry resolves/pins its vnode, handles lease interaction and calls `setattrlist_internal`, which validates bitmap/layout and performs the attribute update.

## 234: getxattr

`user_ssize_t getxattr(user_addr_t path, user_addr_t attrname, user_addr_t value, size_t size, uint32_t position, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L342) · **Condition:** `always` · **Audit event:** `AUE_GETXATTR`.

Read an extended attribute by path or descriptor, or query its size.

**Implementation:** [getxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L13827). Resolve/pin the vnode, copy and validate the attribute name including protected-name rules, and call `vn_getxattr` with a user `uio` when a data buffer is supplied.

## 235: fgetxattr

`user_ssize_t fgetxattr(int fd, user_addr_t attrname, user_addr_t value, size_t size, uint32_t position, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L343) · **Condition:** `always` · **Audit event:** `AUE_FGETXATTR`.

Read an extended attribute by path or descriptor, or query its size.

**Implementation:** [fgetxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L13920). Resolve/pin the vnode, copy and validate the attribute name including protected-name rules, and call `vn_getxattr` with a user `uio` when a data buffer is supplied.

## 236: setxattr

`int setxattr(user_addr_t path, user_addr_t attrname, user_addr_t value, size_t size, uint32_t position, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L344) · **Condition:** `always` · **Audit event:** `AUE_SETXATTR`.

Create or replace an extended attribute by path or descriptor.

**Implementation:** [setxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L13986). Validate name/options/protected-attribute permissions, build a user `uio`, handle applicable leases and call `vn_setxattr`; successful changes can generate filesystem events.

## 237: fsetxattr

`int fsetxattr(int fd, user_addr_t attrname, user_addr_t value, size_t size, uint32_t position, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L345) · **Condition:** `always` · **Audit event:** `AUE_FSETXATTR`.

Create or replace an extended attribute by path or descriptor.

**Implementation:** [fsetxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L14073). Validate name/options/protected-attribute permissions, build a user `uio`, handle applicable leases and call `vn_setxattr`; successful changes can generate filesystem events.

## 238: removexattr

`int removexattr(user_addr_t path, user_addr_t attrname, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L346) · **Condition:** `always` · **Audit event:** `AUE_REMOVEXATTR`.

Remove a named extended attribute.

**Implementation:** [removexattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L14143). Resolve/pin the vnode, validate the name/options and call `vn_removexattr`, with lease and filesystem-event handling around a successful mutation.

## 239: fremovexattr

`int fremovexattr(int fd, user_addr_t attrname, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L347) · **Condition:** `always` · **Audit event:** `AUE_FREMOVEXATTR`.

Remove a named extended attribute.

**Implementation:** [fremovexattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L14205). Resolve/pin the vnode, validate the name/options and call `vn_removexattr`, with lease and filesystem-event handling around a successful mutation.

## 240: listxattr

`user_ssize_t listxattr(user_addr_t path, user_addr_t namebuf, size_t bufsize, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L348) · **Condition:** `always` · **Audit event:** `AUE_LISTXATTR`.

List a file's extended-attribute names or query required size.

**Implementation:** [listxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L14258). Build the appropriate user `uio` after path/fd lookup and call `vn_listxattr`; residual/output sizing controls the returned byte count.

## 241: flistxattr

`user_ssize_t flistxattr(int fd, user_addr_t namebuf, size_t bufsize, int options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L349) · **Condition:** `always` · **Audit event:** `AUE_FLISTXATTR`.

List a file's extended-attribute names or query required size.

**Implementation:** [flistxattr](../../../xnu/bsd/vfs/vfs_syscalls.c#L14310). Build the appropriate user `uio` after path/fd lookup and call `vn_listxattr`; residual/output sizing controls the returned byte count.

## 278: umask_extended

`int umask_extended(int newmask, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L425) · **Condition:** `always` · **Audit event:** `AUE_UMASK_EXTENDED`.

Replace the process creation mask and, for the extended form, associated security mask state.

**Implementation:** [umask_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L11240). Both enter `umask1`, which updates the creation policy used by later vnode creation; existing file permissions are not changed.

## 279: stat_extended

`int stat_extended(user_addr_t path, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L426) · **Condition:** `always` · **Audit event:** `AUE_STAT_EXTENDED`.

Read status for a pathname while following its final symlink, using the declared legacy/64-bit and optional filesec ABI.

**Implementation:** [stat_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L7578). `fstatat_internal` resolves the vnode and marshals status/security output according to flags supplied by each wrapper; size/ABI variants share lookup and attribute collection rather than a different filesystem operation.

## 280: lstat_extended

`int lstat_extended(user_addr_t path, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L427) · **Condition:** `always` · **Audit event:** `AUE_LSTAT_EXTENDED`.

Read status for the final pathname component itself, including a symlink, using the declared ABI.

**Implementation:** [lstat_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L7645). `fstatat_internal` receives no-follow semantics and the wrapper's legacy/64-bit/filesec options, then collects and copies out vnode attributes.

## 281: sys_fstat_extended

`int sys_fstat_extended(int fd, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L428) · **Condition:** `always` · **Audit event:** `AUE_FSTAT_EXTENDED`.

Read status from an open descriptor using its declared status/filesec ABI.

**Implementation:** [sys_fstat_extended](../../../xnu/bsd/kern/kern_descrip.c#L5825). The shared `fstat` helper references the fileproc and invokes the file type's stat operation; wrappers select layout and extended-security arguments.

## 282: chmod_extended

`int chmod_extended(user_addr_t path, uid_t uid, gid_t gid, int mode, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L429) · **Condition:** `always` · **Audit event:** `AUE_CHMOD_EXTENDED`.

Change permissions and extended file-security attributes by path or descriptor.

**Implementation:** [chmod_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L8250). `chmod_extended_init` imports filesec state, then `chmodat` or `fchmod1` performs the change; copied security storage is freed on completion.

## 283: fchmod_extended

`int fchmod_extended(int fd, uid_t uid, gid_t gid, int mode, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L430) · **Condition:** `always` · **Audit event:** `AUE_FCHMOD_EXTENDED`.

Change permissions and extended file-security attributes by path or descriptor.

**Implementation:** [fchmod_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L8358). `chmod_extended_init` imports filesec state, then `chmodat` or `fchmod1` performs the change; copied security storage is freed on completion.

## 284: access_extended

`int access_extended(user_addr_t entries, size_t size, user_addr_t results, uid_t uid) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L431) · **Condition:** `always` · **Audit event:** `AUE_ACCESS_EXTENDED`.

Perform a batch of extended pathname access tests.

**Implementation:** [access_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L7006). Imports the descriptor/path test buffer, derives real-identity credentials, resolves each selected name and uses `access1`, reporting per-test results under the packed interface contract.

## 338: stat64

`int stat64(user_addr_t path, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L519) · **Condition:** `always` · **Audit event:** `AUE_STAT64`.

Read status for a pathname while following its final symlink, using the declared legacy/64-bit and optional filesec ABI.

**Implementation:** [stat64](../../../xnu/bsd/vfs/vfs_syscalls.c#L7598). `fstatat_internal` resolves the vnode and marshals status/security output according to flags supplied by each wrapper; size/ABI variants share lookup and attribute collection rather than a different filesystem operation.

## 339: sys_fstat64

`int sys_fstat64(int fd, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L520) · **Condition:** `always` · **Audit event:** `AUE_FSTAT64`.

Read status from an open descriptor using its declared status/filesec ABI.

**Implementation:** [sys_fstat64](../../../xnu/bsd/kern/kern_descrip.c#L5887). The shared `fstat` helper references the fileproc and invokes the file type's stat operation; wrappers select layout and extended-security arguments.

## 340: lstat64

`int lstat64(user_addr_t path, user_addr_t ub);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L521) · **Condition:** `always` · **Audit event:** `AUE_LSTAT64`.

Read status for the final pathname component itself, including a symlink, using the declared ABI.

**Implementation:** [lstat64](../../../xnu/bsd/vfs/vfs_syscalls.c#L7663). `fstatat_internal` receives no-follow semantics and the wrapper's legacy/64-bit/filesec options, then collects and copies out vnode attributes.

## 341: stat64_extended

`int stat64_extended(user_addr_t path, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L522) · **Condition:** `always` · **Audit event:** `AUE_STAT64_EXTENDED`.

Read status for a pathname while following its final symlink, using the declared legacy/64-bit and optional filesec ABI.

**Implementation:** [stat64_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L7621). `fstatat_internal` resolves the vnode and marshals status/security output according to flags supplied by each wrapper; size/ABI variants share lookup and attribute collection rather than a different filesystem operation.

## 342: lstat64_extended

`int lstat64_extended(user_addr_t path, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L523) · **Condition:** `always` · **Audit event:** `AUE_LSTAT64_EXTENDED`.

Read status for the final pathname component itself, including a symlink, using the declared ABI.

**Implementation:** [lstat64_extended](../../../xnu/bsd/vfs/vfs_syscalls.c#L7687). `fstatat_internal` receives no-follow semantics and the wrapper's legacy/64-bit/filesec options, then collects and copies out vnode attributes.

## 343: sys_fstat64_extended

`int sys_fstat64_extended(int fd, user_addr_t ub, user_addr_t xsecurity, user_addr_t xsecurity_size) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L524) · **Condition:** `always` · **Audit event:** `AUE_FSTAT64_EXTENDED`.

Read status from an open descriptor using its declared status/filesec ABI.

**Implementation:** [sys_fstat64_extended](../../../xnu/bsd/kern/kern_descrip.c#L5867). The shared `fstat` helper references the fileproc and invokes the file type's stat operation; wrappers select layout and extended-security arguments.

## 344: getdirentries64

`user_ssize_t getdirentries64(int fd, void *buf, user_size_t bufsize, off_t *position) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L525) · **Condition:** `always` · **Audit event:** `AUE_GETDIRENTRIES64`.

Read directory records and return the enumeration base offset using the declared record ABI.

**Implementation:** [getdirentries64](../../../xnu/bsd/vfs/vfs_syscalls.c#L11169). `getdirentries_common` drives directory reading and shared offset handling; wrappers choose legacy/64-bit layout and copy the resulting base offset out separately.

## 364: lchown

`int lchown(user_addr_t path, uid_t owner, gid_t group) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L545) · **Condition:** `always` · **Audit event:** `AUE_LCHOWN`.

Change ownership of the final pathname component without following a symlink.

**Implementation:** [lchown](../../../xnu/bsd/vfs/vfs_syscalls.c#L8508). Uses `fchownat_internal` with no-follow semantics rather than changing the referenced symlink target.

## 427: fsgetpath

`user_ssize_t fsgetpath(user_addr_t buf, size_t bufsize, user_addr_t fsid, uint64_t objid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L645) · **Condition:** `always` · **Audit event:** `AUE_FSGETPATH`.

Resolve filesystem/object identity to a pathname, with extended options where declared.

**Implementation:** [fsgetpath](../../../xnu/bsd/vfs/vfs_syscalls.c#L14464). `fsgetpath_extended` performs identity lookup and path construction through `fsgetpath_internal`, then copies the result to the supplied buffer subject to access and size checks.

## 461: getattrlistbulk

`int getattrlistbulk(int dirfd, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, uint64_t options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L715) · **Condition:** `always` · **Audit event:** `AUE_GETATTRLISTBULK`.

Read packed attributes for multiple directory entries while advancing directory enumeration state.

**Implementation:** [getattrlistbulk](../../../xnu/bsd/vfs/vfs_attrlist.c#L4254). Pins a directory fileproc/vnode, imports the attribute selection and uses the bulk directory-attribute path; output capacity and returned entry count bound progress.

## 466: faccessat

`int faccessat(int fd, user_addr_t path, int amode, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L720) · **Condition:** `always` · **Audit event:** `AUE_FACCESSAT`.

Test requested pathname access using access-check credential semantics, optionally relative to a directory fd.

**Implementation:** [faccessat](../../../xnu/bsd/vfs/vfs_syscalls.c#L7355). `faccessat_internal` performs the requested lookup/flag handling and permission test; it is not a reservation guaranteeing that a later open will still succeed.

## 467: fchmodat

`int fchmodat(int fd, user_addr_t path, int mode, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L721) · **Condition:** `always` · **Audit event:** `AUE_FCHMODAT`.

Change permission mode for a pathname, optionally relative to a directory fd.

**Implementation:** [fchmodat](../../../xnu/bsd/vfs/vfs_syscalls.c#L8298). `fchmodat_internal` applies lookup flags and invokes the shared authorization/setattr path; directory-relative selection is not an alternate credential model.

## 468: fchownat

`int fchownat(int fd, user_addr_t path, uid_t uid,gid_t gid, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L722) · **Condition:** `always` · **Audit event:** `AUE_FCHOWNAT`.

Change owner/group of a pathname, optionally relative to a directory fd.

**Implementation:** [fchownat](../../../xnu/bsd/vfs/vfs_syscalls.c#L8515). `fchownat_internal` resolves with the wrapper's follow and directory-base rules, then applies vnode ownership authorization and attributes.

## 469: fstatat

`int fstatat(int fd, user_addr_t path, user_addr_t ub, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L723) · **Condition:** `always` · **Audit event:** `AUE_FSTATAT`.

Read status relative to a directory descriptor with explicit lookup flags.

**Implementation:** [fstatat](../../../xnu/bsd/vfs/vfs_syscalls.c#L7695). `fstatat_internal` carries the directory base, follow/no-follow flags and status ABI into common pathname and attribute handling.

## 470: fstatat64

`int fstatat64(int fd, user_addr_t path, user_addr_t ub, int flag);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L724) · **Condition:** `always` · **Audit event:** `AUE_FSTATAT`.

Read status relative to a directory descriptor with explicit lookup flags.

**Implementation:** [fstatat64](../../../xnu/bsd/vfs/vfs_syscalls.c#L7706). `fstatat_internal` carries the directory base, follow/no-follow flags and status ABI into common pathname and attribute handling.

## 476: getattrlistat

`int getattrlistat(int fd, const char *path, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, u_long options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L730) · **Condition:** `always` · **Audit event:** `AUE_GETATTRLISTAT`.

Read a requested bitmap of filesystem attributes into a packed user buffer.

**Implementation:** [getattrlistat](../../../xnu/bsd/vfs/vfs_attrlist.c#L3650). Imports `attrlist`, resolves through `getattrlistat_internal`, and assembles the selected attributes using the user ABI, options and directory base.

## 524: setattrlistat

`int setattrlistat(int fd, const char *path, struct attrlist *alist, void *attributeBuffer, size_t bufferSize, uint32_t options);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L832) · **Condition:** `always` · **Audit event:** `AUE_SETATTRLISTAT`.

Set a bitmap-selected packed set of filesystem attributes by path, directory-relative path or descriptor.

**Implementation:** [setattrlistat](../../../xnu/bsd/vfs/vfs_attrlist.c#L4980). Each entry resolves/pins its vnode, handles lease interaction and calls `setattrlist_internal`, which validates bitmap/layout and performs the attribute update.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
