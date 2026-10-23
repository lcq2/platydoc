# BSD syscalls: Files and descriptors

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 3: read

`user_ssize_t read(int fd, user_addr_t cbuf, user_size_t nbyte);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L48) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read bytes from an open descriptor into a user buffer.

**Implementation:** [read](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L390). `read_internal` constructs a user `uio`, obtains a referenced fileproc and dispatches file operations; the ordinary entry first calls `__pthread_testcancel`, whereas the nocancel entry enters the I/O path directly.

## 4: write

`user_ssize_t write(int fd, user_addr_t cbuf, user_size_t nbyte);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L49) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Write user bytes through an open descriptor.

**Implementation:** [write](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L716). `write_internal` validates access/guard state, builds the `uio` and dispatches the file's write operation; the ordinary entry first tests cancellation.

## 5: open

`int open(user_addr_t path, int flags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L50) · **Condition:** `always` · **Audit event:** `AUE_OPEN_RWTC`.

Resolve a pathname and create an open-file descriptor.

**Implementation:** [open](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5434). `openat_internal` performs the common lookup/open path using the current directory; `open` adds a cancellation test. The deeper `open1` path handles vnode access, fileglob/fileproc allocation and publication.

## 6: sys_close

`int sys_close(int fd);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L51) · **Condition:** `always` · **Audit event:** `AUE_CLOSE`.

Close a descriptor and release its open-file ownership.

**Implementation:** [sys_close](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L5590). Both call `close_nocancel` with the current credential; the ordinary wrapper tests cancellation. Descriptor removal, drain and final file-operation close are distinct stages underneath.

## 41: sys_dup

`int sys_dup(u_int fd);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L95) · **Condition:** `always` · **Audit event:** `AUE_DUP`.

Allocate another descriptor referring to the same open-file description.

**Implementation:** [sys_dup](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L2467). Under fd-table protection, checks guard restrictions, reserves a slot with `fdalloc`, and calls `finishdup` to retain the fileglob and publish a new fileproc.

## 42: pipe

`int pipe(void);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L96) · **Condition:** `always` · **Audit event:** `AUE_PIPE`.

Allocate a connected anonymous pipe pair and return both descriptors.

**Implementation:** [pipe](../../../platydoc-data/xnu/bsd/kern/sys_pipe.c#L392). Allocates pipepair storage and two fileprocs, associates endpoint data and labels, then releases reserved fd slots into the table; failed construction closes/frees the partially built endpoints.

## 54: ioctl

`int ioctl(int fd, u_long com, caddr_t data) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L108) · **Condition:** `always` · **Audit event:** `AUE_IOCTL`.

Issue a control request to the object represented by a descriptor.

**Implementation:** [ioctl](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L844). Decodes IOC direction/size, imports a bounded command buffer, looks up the fileproc and applies MAC checks, handles generic descriptor controls, then uses file-operation ioctl dispatch; device-specific command semantics live behind that callback.

## 89: sys_getdtablesize

`int sys_getdtablesize(void);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L147) · **Condition:** `always` · **Audit event:** `AUE_GETDTABLESIZE`.

Return the process's current descriptor limit.

**Implementation:** [sys_getdtablesize](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L2386). Reads the effective nofile limit through `proc_limitgetcur_nofile`; it is a limit query, not a count of open descriptors.

## 90: sys_dup2

`int sys_dup2(u_int from, u_int to);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L148) · **Condition:** `always` · **Audit event:** `AUE_DUP2`.

Replace a specified descriptor with a duplicate of another.

**Implementation:** [sys_dup2](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L2521). `dup2` handles source/target identity, reservations, guarded close and target replacement; it can restart while a target slot is reserved before `finishdup` publishes the duplicate.

## 92: sys_fcntl

`int sys_fcntl(int fd, int cmd, long arg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L150) · **Condition:** `always` · **Audit event:** `AUE_FCNTL`.

Apply descriptor/open-file control commands.

**Implementation:** [sys_fcntl](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L2638). The common switch handles descriptor flags/duplication, file flags, offsets, advisory locks, leases, preallocation, signatures and other command families, dispatching to file/VNOP or UBC helpers as appropriate. The ordinary entry tests cancellation; this catalog does not enumerate every command ABI.

## 120: readv

`user_ssize_t readv(int fd, struct iovec *iovp, u_int iovcnt);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L198) · **Condition:** `always` · **Audit event:** `AUE_READV`.

Scatter a read across user iovecs.

**Implementation:** [readv](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L488). `readv_uio` imports and validates the vector into a `uio`, then follows descriptor read dispatch; the ordinary entry adds a cancellation test.

## 121: writev

`user_ssize_t writev(int fd, struct iovec *iovp, u_int iovcnt);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L199) · **Condition:** `always` · **Audit event:** `AUE_WRITEV`.

Gather user iovecs into a descriptor write.

**Implementation:** [writev](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L807). `writev_uio` imports vector storage and dispatches the resulting `uio`; the ordinary wrapper tests cancellation before the common operation.

## 131: sys_flock

`int sys_flock(int fd, int how);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L209) · **Condition:** `always` · **Audit event:** `AUE_FLOCK`.

Acquire or release whole-file advisory locking on an open file.

**Implementation:** [sys_flock](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L5993). Obtains the vnode/fileproc, translates operation flags and invokes `VNOP_ADVLOCK` with flock ownership; retains the references across the lock operation and drops them afterward.

## 153: pread

`user_ssize_t pread(int fd, user_addr_t buf, user_size_t nbyte, off_t offset);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L237) · **Condition:** `always` · **Audit event:** `AUE_PREAD`.

Read at an explicit file offset without using the shared descriptor offset as the request position.

**Implementation:** [pread](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L417). Both reach `read_internal` with the positional-I/O flag and supplied offset; only the ordinary wrapper performs its initial cancellation test.

## 154: pwrite

`user_ssize_t pwrite(int fd, user_addr_t buf, user_size_t nbyte, off_t offset);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L238) · **Condition:** `always` · **Audit event:** `AUE_PWRITE`.

Write at an explicit offset.

**Implementation:** [pwrite](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L749). Both reach `write_internal` with positional-I/O state; the common file operation performs the transfer and reports partial progress. The ordinary wrapper tests cancellation.

## 199: lseek

`off_t lseek(int fd, off_t offset, int whence);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L295) · **Condition:** `always` · **Audit event:** `AUE_LSEEK`.

Query or change an open file's shared offset, including supported data/hole queries.

**Implementation:** [lseek](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L6798). Gets the fileglob/vnode, rejects unsuitable objects, applies offset authorization and computes the requested origin; filesystem ioctl handling supports selected seek modes before publishing the offset.

## 216: open_dprotected_np

`int open_dprotected_np(user_addr_t path, int flags, int class, int dpflags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L324) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Open with explicit data-protection class/flags, optionally relative to a directory descriptor.

**Implementation:** [open_dprotected_np](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5378). `openat_dprotected_internal` carries protection attributes into the common open machinery; actual content-protection behavior remains filesystem-dependent.

## 218: openat_dprotected_np

`int openat_dprotected_np(int fd, user_addr_t path, int flags, int class, int dpflags, int mode, int authfd) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L326) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Open with explicit data-protection class/flags, optionally relative to a directory descriptor.

**Implementation:** [openat_dprotected_np](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5367). `openat_dprotected_internal` carries protection attributes into the common open machinery; actual content-protection behavior remains filesystem-dependent.

## 277: open_extended

`int open_extended(user_addr_t path, int flags, uid_t uid, gid_t gid, int mode, user_addr_t xsecurity) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L424) · **Condition:** `always` · **Audit event:** `AUE_OPEN_EXTENDED_RWTC`.

Open a pathname with extended file-security creation attributes.

**Implementation:** [open_extended](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5256). Copies the filesec using `kauth_copyinfilesec`, builds vnode attributes, calls `open1`, then releases copied security storage on return.

## 396: read_nocancel

`user_ssize_t read_nocancel(int fd, user_addr_t cbuf, user_size_t nbyte) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L590) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Read bytes from an open descriptor into a user buffer.

**Implementation:** [read_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L373). `read_internal` constructs a user `uio`, obtains a referenced fileproc and dispatches file operations; the ordinary entry first calls `__pthread_testcancel`, whereas the nocancel entry enters the I/O path directly.

## 397: write_nocancel

`user_ssize_t write_nocancel(int fd, user_addr_t cbuf, user_size_t nbyte) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L591) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Write user bytes through an open descriptor.

**Implementation:** [write_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L701). `write_internal` validates access/guard state, builds the `uio` and dispatches the file's write operation; the ordinary entry first tests cancellation.

## 398: open_nocancel

`int open_nocancel(user_addr_t path, int flags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L592) · **Condition:** `always` · **Audit event:** `AUE_OPEN_RWTC`.

Resolve a pathname and create an open-file descriptor.

**Implementation:** [open_nocancel](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5441). `openat_internal` performs the common lookup/open path using the current directory; `open` adds a cancellation test. The deeper `open1` path handles vnode access, fileglob/fileproc allocation and publication.

## 399: sys_close_nocancel

`int sys_close_nocancel(int fd) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L593) · **Condition:** `always` · **Audit event:** `AUE_CLOSE`.

Close a descriptor and release its open-file ownership.

**Implementation:** [sys_close_nocancel](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L5599). Both call `close_nocancel` with the current credential; the ordinary wrapper tests cancellation. Descriptor removal, drain and final file-operation close are distinct stages underneath.

## 406: sys_fcntl_nocancel

`int sys_fcntl_nocancel(int fd, int cmd, long arg) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L607) · **Condition:** `always` · **Audit event:** `AUE_FCNTL`.

Apply descriptor/open-file control commands.

**Implementation:** [sys_fcntl_nocancel](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L2845). The common switch handles descriptor flags/duplication, file flags, offsets, advisory locks, leases, preallocation, signatures and other command families, dispatching to file/VNOP or UBC helpers as appropriate. The ordinary entry tests cancellation; this catalog does not enumerate every command ABI.

## 411: readv_nocancel

`user_ssize_t readv_nocancel(int fd, struct iovec *iovp, u_int iovcnt) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L616) · **Condition:** `always` · **Audit event:** `AUE_READV`.

Scatter a read across user iovecs.

**Implementation:** [readv_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L479). `readv_uio` imports and validates the vector into a `uio`, then follows descriptor read dispatch; the ordinary entry adds a cancellation test.

## 412: writev_nocancel

`user_ssize_t writev_nocancel(int fd, struct iovec *iovp, u_int iovcnt) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L617) · **Condition:** `always` · **Audit event:** `AUE_WRITEV`.

Gather user iovecs into a descriptor write.

**Implementation:** [writev_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L798). `writev_uio` imports vector storage and dispatches the resulting `uio`; the ordinary wrapper tests cancellation before the common operation.

## 414: pread_nocancel

`user_ssize_t pread_nocancel(int fd, user_addr_t buf, user_size_t nbyte, off_t offset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L623) · **Condition:** `always` · **Audit event:** `AUE_PREAD`.

Read at an explicit file offset without using the shared descriptor offset as the request position.

**Implementation:** [pread_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L397). Both reach `read_internal` with the positional-I/O flag and supplied offset; only the ordinary wrapper performs its initial cancellation test.

## 415: pwrite_nocancel

`user_ssize_t pwrite_nocancel(int fd, user_addr_t buf, user_size_t nbyte, off_t offset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L624) · **Condition:** `always` · **Audit event:** `AUE_PWRITE`.

Write at an explicit offset.

**Implementation:** [pwrite_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L723). Both reach `write_internal` with positional-I/O state; the common file operation performs the transfer and reports partial progress. The ordinary wrapper tests cancellation.

## 430: sys_fileport_makeport

`int sys_fileport_makeport(int fd, user_addr_t portnamep);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L648) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Export a sendable open-file description as a Mach fileport.

**Implementation:** [sys_fileport_makeport](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L6066). Checks guard/sendability, retains the fileglob, allocates a fileport and copies a send right into the task's IPC space; copyout failures unwind the acquired ownership.

## 431: sys_fileport_makefd

`int sys_fileport_makefd(mach_port_name_t port);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L649) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Create a descriptor from a Mach fileport.

**Implementation:** [sys_fileport_makefd](../../../platydoc-data/xnu/bsd/kern/kern_descrip.c#L6221). Copies in a typed fileport send right, calls `fileport_makefd` to reserve/publish descriptor state, then releases the temporary port right.

## 441: guarded_open_np

`int guarded_open_np(user_addr_t path, const guardid_t *guard, u_int guardflags, int flags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L671) · **Condition:** `always` · **Audit event:** `AUE_OPEN_RWTC`.

Create an open descriptor with caller-specified guard identity/restrictions, optionally data protection.

**Implementation:** [guarded_open_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L265). Copies the guard value, builds vnode/open attributes and calls `open1` with guard state; later operations must satisfy the guard contract, not merely possess the numeric fd.

## 442: guarded_close_np

`int guarded_close_np(int fd, const guardid_t *guard);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L672) · **Condition:** `always` · **Audit event:** `AUE_CLOSE`.

Close a descriptor only under the matching guard contract.

**Implementation:** [guarded_close_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L423). Copies the guard, uses `fp_lookup_guarded` under fd protection, then calls `fp_close_and_unlock`; guard mismatch is distinct from ordinary lookup failure.

## 444: change_fdguard_np

`int change_fdguard_np(int fd, const guardid_t *guard, u_int guardflags, const guardid_t *nguard, u_int nguardflags, int *fdflagsp);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L674) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Install, replace or remove a descriptor's guard identity and flags.

**Implementation:** [change_fdguard_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L507). Copies guard inputs, prepares a guarded fileproc, validates/replaces protected fd state under the descriptor lock, and reports the old/new state through the requested output.

## 463: openat

`int openat(int fd, user_addr_t path, int flags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L717) · **Condition:** `always` · **Audit event:** `AUE_OPENAT_RWTC`.

Open a pathname relative to a directory descriptor or the current directory.

**Implementation:** [openat](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5457). `openat_internal` receives `fd`, flags and mode and resolves the pathname with that starting context; the ordinary entry tests cancellation.

## 464: openat_nocancel

`int openat_nocancel(int fd, user_addr_t path, int flags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L718) · **Condition:** `always` · **Audit event:** `AUE_OPENAT_RWTC`.

Open a pathname relative to a directory descriptor or the current directory.

**Implementation:** [openat_nocancel](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5449). `openat_internal` receives `fd`, flags and mode and resolves the pathname with that starting context; the ordinary entry tests cancellation.

## 479: openbyid_np

`int openbyid_np(user_addr_t fsid, user_addr_t objid, int oflags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L733) · **Condition:** `always` · **Audit event:** `AUE_OPENBYID_RWT`.

Open a filesystem object selected by filesystem/object identity.

**Implementation:** [openbyid_np](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L5502). Checks permission to open by ID, resolves a path through `fsgetpath_internal`, then uses `openat_internal`; identity resolution does not bypass the ordinary open operation.

## 484: guarded_open_dprotected_np

`int guarded_open_dprotected_np(user_addr_t path, const guardid_t *guard, u_int guardflags, int flags, int dpclass, int dpflags, int mode) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L747) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Create an open descriptor with caller-specified guard identity/restrictions, optionally data protection.

**Implementation:** [guarded_open_dprotected_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L318). Copies the guard value, builds vnode/open attributes and calls `open1` with guard state; later operations must satisfy the guard contract, not merely possess the numeric fd.

## 485: guarded_write_np

`user_ssize_t guarded_write_np(int fd, const guardid_t *guard, user_addr_t cbuf, user_size_t nbyte);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L748) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Write through a descriptor while supplying its guard identity.

**Implementation:** [guarded_write_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L690). Copies the guard and calls `write_internal` with it, sharing ordinary transfer machinery while preserving guard checks.

## 486: guarded_pwrite_np

`user_ssize_t guarded_pwrite_np(int fd, const guardid_t *guard, user_addr_t buf, user_size_t nbyte, off_t offset);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L749) · **Condition:** `always` · **Audit event:** `AUE_PWRITE`.

Perform a positional write with a descriptor guard identity.

**Implementation:** [guarded_pwrite_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L711). Copies the guard and passes it with offset/positional flags to `write_internal`.

## 487: guarded_writev_np

`user_ssize_t guarded_writev_np(int fd, const guardid_t *guard, struct iovec *iovp, int iovcnt);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L750) · **Condition:** `always` · **Audit event:** `AUE_WRITEV`.

Perform a gather-write with a descriptor guard identity.

**Implementation:** [guarded_writev_np](../../../platydoc-data/xnu/bsd/kern/kern_guarded.c#L737). Copies the guard and invokes `writev_uio`; iovec import and file-operation dispatch remain the common vector-I/O path.

## 540: sys_preadv

`user_ssize_t sys_preadv(int fd, struct iovec *iovp, int iovcnt, off_t offset);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L852) · **Condition:** `always` · **Audit event:** `AUE_PREADV`.

Perform positional scatter-read I/O.

**Implementation:** [sys_preadv](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L505). `readv_uio` receives the explicit offset and positional flag, separating this request from ordinary shared-offset reads; the non-nocancel wrapper tests cancellation.

## 541: sys_pwritev

`user_ssize_t sys_pwritev(int fd, struct iovec *iovp, int iovcnt, off_t offset);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L853) · **Condition:** `always` · **Audit event:** `AUE_PWRITEV`.

Perform positional gather-write I/O.

**Implementation:** [sys_pwritev](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L824). `writev_uio` receives the supplied offset and positional flag; it shares descriptor validation and transfer machinery with vector writes. The ordinary wrapper tests cancellation.

## 542: sys_preadv_nocancel

`user_ssize_t sys_preadv_nocancel(int fd, struct iovec *iovp, int iovcnt, off_t offset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L854) · **Condition:** `always` · **Audit event:** `AUE_PREADV`.

Perform positional scatter-read I/O.

**Implementation:** [sys_preadv_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L495). `readv_uio` receives the explicit offset and positional flag, separating this request from ordinary shared-offset reads; the non-nocancel wrapper tests cancellation.

## 543: sys_pwritev_nocancel

`user_ssize_t sys_pwritev_nocancel(int fd, struct iovec *iovp, int iovcnt, off_t offset) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L855) · **Condition:** `always` · **Audit event:** `AUE_PWRITEV`.

Perform positional gather-write I/O.

**Implementation:** [sys_pwritev_nocancel](../../../platydoc-data/xnu/bsd/kern/sys_generic.c#L814). `writev_uio` receives the supplied offset and positional flag; it shares descriptor validation and transfer machinery with vector writes. The ordinary wrapper tests cancellation.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
