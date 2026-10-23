# Filesystem registration, boot mounts, small filesystems, and NFS

[VFS index](README.md) · [Dispatch model](vnodes-mounts-and-dispatch.md) · [I/O paths](io-and-cache.md)

Continue with the detailed [namespace mutation](namespace-mutations.md), [devfs/specfs/FIFO](device-nodes-and-fifos.md), [bindfs/nullfs](stacked-filesystems.md), and [NFS server request](nfs-server-requests.md) chapters for current implementation paths, references, locks and cleanup.

## Filesystem type registration and operation vectors

[`vfsinit`](../../../platydoc-data/xnu/bsd/vfs/vfs_init.c#L311) initializes vnode infrastructure, filesystem events and the name cache; builds vnode operation vectors; then initializes statically configured filesystem types from [`vfsconf`](../../../platydoc-data/xnu/bsd/vfs/vfs_conf.c). Conditional entries include devfs, nullfs, bindfs, mockfs and routefs. Compilation guards matter: an entry in source is not proof that a running product enabled it.

Filesystem-wide operations such as mount, unmount and root lookup are in `struct vfsops`; [`VFS_MOUNT`](../../../platydoc-data/xnu/bsd/vfs/kpi_vfs.c#L201) and [`VFS_ROOT`](../../../platydoc-data/xnu/bsd/vfs/kpi_vfs.c#L268) dispatch through `mnt_op`. Per-object operations instead use `vnode->v_op`. [`vfs_opv_init`](../../../platydoc-data/xnu/bsd/vfs/vfs_init.c#L158) fills vectors by each operation descriptor's assigned offset, then fills missing entries with the filesystem's default method. The operation descriptions in [`vnode_if.c`](../../../platydoc-data/xnu/bsd/vfs/vnode_if.c) identify argument layout and relevant vnode/context fields; [`vnode_if.src`](../../../platydoc-data/xnu/bsd/vfs/vnode_if.src) is the interface specification.

Dynamic filesystems register with [`vfs_fsadd`](../../../platydoc-data/xnu/bsd/vfs/kpi_vfs.c#L963), supplying type name, `vfsops`, operation descriptors and flags. The function validates thread-safety declarations, assigns type information and constructs dispatch vectors. This is an integration boundary for filesystem implementations supplied outside the XNU tree, including APFS. Generic VFS cannot explain those implementations' internal on-disk structures, allocation or transaction logic.

## Boot and ordinary mounts

[`vfs_mountroot`](../../../platydoc-data/xnu/bsd/vfs/vfs_subr.c#L1203) supports a special `mountroot` callback path, otherwise creates a block-device vnode for `rootdev`, iterates root-capable registered filesystems, and invokes their root-mount callback or `VFS_MOUNT`. On success it records the device/mount, initializes I/O attributes and starts/probes the filesystem. [`bsd_init`](../../../platydoc-data/xnu/bsd/kern/bsd_init.c#L895) then obtains the filesystem root with `VFS_ROOT`, establishes `rootvnode` and later mounts devfs. [`IOFindBSDRoot`](../../../platydoc-data/xnu/bsd/kern/bsd_init.c#L1141) connects BSD root-device selection with IOKit; image/root-volume policy has additional configuration-dependent paths.

Ordinary [`mount_common`](../../../platydoc-data/xnu/bsd/vfs/vfs_syscalls.c#L1154) distinguishes updates from new mounts, manages lifecycle state and authorization, associates `mnt_vnodecovered`, calls `VFS_MOUNT`, then installs the directory's `v_mountedhere` relationship and publishes the mount. During lookup this relationship leads to `VFS_ROOT`; during unmount it must be detached while crossings and active operations are synchronized. A mounted filesystem is not just another child directory vnode.

## Included filesystems and operation layers

These implementations were surveyed at their key entry points; they are useful small examples, not substitutes for the missing production disk-filesystem implementations.

| Implementation | Role and useful source route |
|---|---|
| **devfs** | Device namespace. [`devfs_make_node`](../../../platydoc-data/xnu/bsd/miscfs/devfs/devfs_tree.c#L1542) registers nodes; [`devfs_mount`](../../../platydoc-data/xnu/bsd/miscfs/devfs/devfs_vfsops.c#L172) creates mount-specific state; [`devfs_lookup`](../../../platydoc-data/xnu/bsd/miscfs/devfs/devfs_vnops.c#L334) searches the internal tree under `DEVFS_LOCK` and obtains vnodes. |
| **specfs operations** | Character/block-device behavior. [`spec_read`](../../../platydoc-data/xnu/bsd/miscfs/specfs/spec_vnops.c#L523) reaches character `d_read` or block I/O paths; [`spec_strategy`](../../../platydoc-data/xnu/bsd/miscfs/specfs/spec_vnops.c#L2569) reaches block `d_strategy`. Devfs special-node vectors wrap/use these methods. Namespace creation and device implementation are separate. |
| **fifofs operations** | Named FIFO behavior attached to filesystem vnodes. [`fifo_open`](../../../platydoc-data/xnu/bsd/miscfs/fifofs/fifo_vnops.c#L152) creates connected local stream sockets and tracks readers/writers. Data flows through local IPC rather than disk blocks. |
| **deadfs operations** | Replacement behavior after reclaim. [`dead_vnops.c`](../../../platydoc-data/xnu/bsd/miscfs/deadfs/dead_vnops.c) supplies operations for handles whose former filesystem object is gone. |
| **nullfs / bindfs** | Layered readonly views in this checkout. [`null_lookup`](../../../platydoc-data/xnu/bsd/miscfs/nullfs/null_vnops.c#L560) and [`bind_lookup`](../../../platydoc-data/xnu/bsd/miscfs/bindfs/bind_vnops.c#L185) reject create/delete/rename, acquire a lower-vnode iocount, dispatch lower lookup and wrap the result. Nullfs also handles special nodes and a patched context. |
| **mockfs** | Small boot/testing-oriented filesystem. [`mockfs_read`, `mockfs_pagein`, `mockfs_blockmap`, `mockfs_strategy`](../../../platydoc-data/xnu/bsd/miscfs/mockfs/mockfs_vnops.c#L208) expose a particularly readable clustered-I/O route over backing storage. Memory-backed mode has different constraints. |
| **routefs** | Special kernel-mounted routing view. [`routefs_mount`](../../../platydoc-data/xnu/bsd/miscfs/routefs/routefs_ops.c#L83) retains a supplied root vnode/path and records its vid; mount checks restrict how it is instantiated. |

The `bsd/miscfs/union` directory contains a header/build material rather than a complete standalone union vnode implementation. Generic union-mount traversal is separately guarded in `vfs_lookup.c`. Do not infer a full filesystem merely from a directory name.

## NFS server request path

The available NFS server is conditional on [`CONFIG_NFS_SERVER`](../../../platydoc-data/xnu/bsd/nfs/nfs_conf.h#L32). [`nfssvc`](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L589) exposes socket registration, worker entry, export configuration and statistics. `NFSSVC_ADDSOCK` retains a supplied socket so its userspace descriptor can be closed without destroying server ownership; `NFSSVC_NFSD` enters the server worker. Privilege and MAC checks protect the relevant operations.

[`nfssvc_nfsd`](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L904) takes work from server socket queues, obtains RPC records, consults the duplicate-request cache, and dispatches through [`nfsrv_procs`](../../../platydoc-data/xnu/bsd/nfs/nfs_serv.c#L5201). Socket state uses `ns_rwlock`; worker/queue state uses `nfsd_mutex`; export lookup and procedure execution use the export rwlock. [`nfs_upcall.c`](../../../platydoc-data/xnu/bsd/nfs/nfs_upcall.c) also provides worker-mediated socket receive upcalls. These upcalls are distinct from GSS's Mach upcalls to userspace.

[`nfsrv_read`](../../../platydoc-data/xnu/bsd/nfs/nfs_serv.c#L914) demonstrates the VFS bridge: decode file handle/offset/count, resolve the handle using `nfsrv_fhtovp`, check export credentials and access, obtain attributes, build a kernel-space `uio` over reply mbufs, call `VNOP_READ`, then encode the reply and drop the vnode iocount. The server does not need a process file descriptor to read an exported vnode. The inspected handlers explicitly distinguish NFS versions 2 and 3; this is not documentation of an absent NFSv4 client.

[`nfsrv_fhtovp`](../../../platydoc-data/xnu/bsd/nfs/nfs_subs.c#L2296) validates handle format, finds an export, selects client-specific export options and checks security flavor before filesystem handle translation. A remote handle is not a trusted kernel vnode pointer. Name-based remote lookup takes a related route through [`nfsrv_lookup`](../../../platydoc-data/xnu/bsd/nfs/nfs_serv.c#L662) and `nfsrv_namei`.

## lockd, gssd, and missing client code

[`fhopen`](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L425) is explicitly provided for `rpc.lockd` to turn an NFS file handle into an open descriptor. It requires superuser credentials, validates flags/handle length, resolves the vnode under export synchronization, and performs open setup. It is a daemon interface, not the full lock daemon implementation.

For RPCSEC_GSS setup, [`nfs_gss_svc_gssd_upcall`](../../../platydoc-data/xnu/bsd/nfs/nfs_gss.c#L1124) obtains the host's gssd port and calls `mach_gss_accept_sec_context`, exchanging tokens/context information and receiving identity/security state. The message interface is in [`gssd_mach.defs`](../../../platydoc-data/xnu/osfmk/gssd/gssd_mach.defs). The gssd daemon implementation and a complete protocol/cryptographic audit are outside this chapter.

The tree lacks the NFS client's vnode/mount implementation. It does include [`nfs_register_hooks`](../../../platydoc-data/xnu/bsd/nfs/nfs_syscalls.c#L175) for buffer invalidation callbacks and wrappers such as `nfs_vinvalbuf`, which VFS cleanup can call. These are evidence of an external integration boundary; generic comments mentioning NFS clients must not be mistaken for an implementation available here.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
