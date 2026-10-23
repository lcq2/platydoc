# Source map

[Guide index](README.md) · [Architecture](architecture.md)

Kernel directory names and source paths on this page are relative to Platydoc's read-only `platydoc-data/xnu/` input. The project-root `docs-ai/`, `docs-ai-html/` and `.docs-cache/` directories belong to the documentation project and are not part of this source inventory.

## Top-level directories

This inventory counts files, not compiled translation units. Source/header/interface counts include `.c`, `.h`, `.cpp`, `.s`, `.S`, `.defs`, `.m`, and `.mm`. Conditional implementations and bundled external headers are included; the counts do not measure how much was reviewed.

| Directory | All files | Source/header/interface files | Role and guide |
| --- | ---: | ---: | --- |
| [bsd](../platydoc-data/xnu/bsd/) | 1,708 | 1,267 | POSIX processes, VFS, networking, security integration; [processes](subsystems/processes/README.md), [VFS](subsystems/vfs/README.md), [networking](subsystems/networking/README.md) |
| [osfmk](../platydoc-data/xnu/osfmk/) | 1,502 | 1,188 | Mach runtime, IPC, VM, machine code; [runtime](subsystems/runtime/README.md), [IPC](subsystems/ipc/README.md), [VM](subsystems/vm/README.md), [platform](subsystems/platform/README.md) |
| [iokit](../platydoc-data/xnu/iokit/) | 304 | 258 | C++ driver framework and user-driver interfaces; [drivers](subsystems/drivers/README.md) |
| [libkern](../platydoc-data/xnu/libkern/) | 304 | 264 | Kernel C/C++ support, object containers, extension loading, compression and library interfaces; [drivers](subsystems/drivers/README.md) |
| [pexpert](../platydoc-data/xnu/pexpert/) | 72 | 57 | Platform discovery, boot configuration, hardware callbacks; [platform](subsystems/platform/README.md) |
| [security](../platydoc-data/xnu/security/) | 39 | 30 | MAC framework and operation-specific hooks; [security](subsystems/security/README.md) |
| [san](../platydoc-data/xnu/san/) | 60 | 36 | Memory/undefined-behavior/coverage instrumentation; [observability](development/observability.md) |
| [libsyscall](../platydoc-data/xnu/libsyscall/) | 257 | 232 | User-side syscall and Mach interface support; [processes](subsystems/processes/README.md) |
| [libsa](../platydoc-data/xnu/libsa/) | 14 | 4 | Isolated bootstrap support, including startup extension discovery; [bootstrap.cpp](../platydoc-data/xnu/libsa/bootstrap.cpp) |
| [libkdd](../platydoc-data/xnu/libkdd/) | 18 | 12 | User-space decoding of kernel chunked data; [observability](development/observability.md) |
| [config](../platydoc-data/xnu/config/) | 79 | 0 | Kernel feature, architecture, platform, and export configurations |
| [makedefs](../platydoc-data/xnu/makedefs/) | 8 | 0 | Shared build machinery |
| [SETUP](../platydoc-data/xnu/SETUP/) | 25 | 13 | Build-time configuration and source-processing utilities |
| [EXTERNAL_HEADERS](../platydoc-data/xnu/EXTERNAL_HEADERS/) | 148 | 139 | Headers from separately built projects; presence of a header does not imply an in-tree implementation |
| [tests](../platydoc-data/xnu/tests/) | 1,298 | 1,086 | User-space regression tests, subsystem tests, and unit-test harnesses |
| [tools](../platydoc-data/xnu/tools/) | 239 | 55 | Debugger macros, trace tools, performance tools, formal models, and developer utilities |
| [doc](../platydoc-data/xnu/doc/) | 34 | 0 | Existing technical documentation; linked from the relevant new guides |

These source/header/interface files total about 2.47 million lines, including tests, comments, headers, and external definitions. The documentation follows representative core implementations and interfaces; it is not a line-by-line review of that total.

## Inside `osfmk`

| Area | How to orient yourself |
| --- | --- |
| [kern](../platydoc-data/xnu/osfmk/kern/) | Start with `task.h`, `thread.h`, `processor.h`; then `task.c`, `thread.c`, `sched_prim.c`. Also contains allocators, locks, wait queues, timers, exceptions, accounting, stackshot, and Exclaves integration. The directory name is much broader than scheduling. |
| [ipc](../platydoc-data/xnu/osfmk/ipc/) | Begin with `ipc_space.h`, `ipc_entry.h`, `ipc_port.h`, and `ipc_kmsg.h`; follow `mach_msg.c`, `ipc_kmsg.c`, and `ipc_mqueue.c`. |
| [vm](../platydoc-data/xnu/osfmk/vm/) | Public/internal/XNU-facing headers have distinct audiences. Start with map/object/page definitions, then `vm_fault.c`, `vm_map.c`, `vm_resident.c`, and `vm_pageout.c`. |
| [mach](../platydoc-data/xnu/osfmk/mach/) | User-visible types and MIG interface definitions. These define contracts; implementation usually lives elsewhere. |
| [arm64](../platydoc-data/xnu/osfmk/arm64/), [arm](../platydoc-data/xnu/osfmk/arm/), [x86_64](../platydoc-data/xnu/osfmk/x86_64/), [i386](../platydoc-data/xnu/osfmk/i386/), [machine](../platydoc-data/xnu/osfmk/machine/) | Entry/exit, context switching, pmap, CPU features, timers, and machine abstractions. Do not infer supported execution modes from historical directory names alone. |
| [device](../platydoc-data/xnu/osfmk/device/) | IOKit/Mach device interface glue, including `device.defs` and `iokit_rpc.c`. |
| [bank](../platydoc-data/xnu/osfmk/bank/), [voucher](../platydoc-data/xnu/osfmk/voucher/) | Voucher attributes for accounting relationships and pthread priority. Follow these from the IPC/runtime guides rather than treating them as a separate scheduler. |
| [atm](../platydoc-data/xnu/osfmk/atm/) | Activity tracing compatibility code. `atm_types.h` explicitly marks its contents deprecated; do not assume it is the primary modern tracing interface. |
| [corpses](../platydoc-data/xnu/osfmk/corpses/) | Task corpse/crash information, linked to task lifecycle and exception delivery. |
| [kperf](../platydoc-data/xnu/osfmk/kperf/), [kdp](../platydoc-data/xnu/osfmk/kdp/) | Performance sampling and debugger/core-dump infrastructure. |
| [gssd](../platydoc-data/xnu/osfmk/gssd/), [lockd](../platydoc-data/xnu/osfmk/lockd/), [kextd](../platydoc-data/xnu/osfmk/kextd/), [UserNotification](../platydoc-data/xnu/osfmk/UserNotification/) | Kernel-to-user-service interfaces. The `.defs` file is often the best starting point; the corresponding service need not be implemented here. |
| [tests](../platydoc-data/xnu/osfmk/tests/), [conf](../platydoc-data/xnu/osfmk/conf/) | In-kernel tests and build-selection rules. |

## Inside `bsd`

| Area | How to orient yourself |
| --- | --- |
| [sys](../platydoc-data/xnu/bsd/sys/) | Process, credential, descriptor, vnode, socket, and event structures and interfaces. `*_internal.h` often carries the implementation state that a public header hides. |
| [kern](../platydoc-data/xnu/bsd/kern/) | Process lifecycle, descriptors, signals, events, sockets, memory policy, credentials, code-signing integration, sysctl, tracing, TTYs, and multiple IPC mechanisms. |
| [vfs](../platydoc-data/xnu/bsd/vfs/), [vm](../platydoc-data/xnu/bsd/vm/) | Filesystem-independent operations and the vnode-pager bridge. `bsd/vm` is a boundary with Mach VM, not the whole VM implementation. |
| [miscfs](../platydoc-data/xnu/bsd/miscfs/), [nfs](../platydoc-data/xnu/bsd/nfs/) | In-tree filesystem implementations and special vnode operations. The generic VFS is not an APFS implementation. |
| [net](../platydoc-data/xnu/bsd/net/), [netinet](../platydoc-data/xnu/bsd/netinet/), [netinet6](../platydoc-data/xnu/bsd/netinet6/), [netkey](../platydoc-data/xnu/bsd/netkey/) | Interfaces/routing/policy, IPv4/TCP/UDP, IPv6, and key-management code. |
| [skywalk](../platydoc-data/xnu/bsd/skywalk/) | Channels, packet pools, nexuses, flow switching, and network-interface integration. Read alongside traditional sockets and mbufs. |
| [pthread](../platydoc-data/xnu/bsd/pthread/) | Workqueue code and callback shims for pthread implementation supplied separately. |
| [dev](../platydoc-data/xnu/bsd/dev/) | Architecture syscall entry, device/TTY support, and DTrace. Some architecture code also lives under `bsd/arm` and `bsd/i386`. |
| [security](../platydoc-data/xnu/bsd/security/), [bsm](../platydoc-data/xnu/bsd/bsm/) | Audit implementation and audit data/interface support, alongside framework hooks in top-level `security`. |
| [man](../platydoc-data/xnu/bsd/man/), [tests](../platydoc-data/xnu/bsd/tests/), [conf](../platydoc-data/xnu/bsd/conf/) | API documentation, in-kernel tests, and build metadata. |

## Generated interfaces and external boundaries

Searching only for a C definition can miss the most useful source. BSD syscall tables come from [syscalls.master](../platydoc-data/xnu/bsd/kern/syscalls.master) and [makesyscalls.sh](../platydoc-data/xnu/bsd/kern/makesyscalls.sh). Mach RPC stubs come from `.defs` files and build rules. DriverKit includes `.iig` interface descriptions, for example [IOUserServer.iig](../platydoc-data/xnu/iokit/DriverKit/IOUserServer.iig). Generated outputs can live under a build directory and be absent from this source-only checkout.

An interface header, callback table, or stub can mark a real implementation boundary. Examples include `pthread_functions` in [pthread_shims.c](../platydoc-data/xnu/bsd/pthread/pthread_shims.c), crypto/trust headers in [EXTERNAL_HEADERS](../platydoc-data/xnu/EXTERNAL_HEADERS/), registered MAC policies in [mac_policy.h](../platydoc-data/xnu/security/mac_policy.h), and providers discovered through [IOService.cpp](../platydoc-data/xnu/iokit/Kernel/IOService.cpp). Follow both the declaration and the registration/call site before concluding that an operation is implemented here.

## Search by question

| Question | First stops |
| --- | --- |
| Why did this thread stop running? | `sched_prim.c`, selected `sched_*` policy, `waitq.c`, `turnstile.c`, thread state |
| Why does an address fault? | Architecture fault handler, `vm_fault.c`, map entry, object/page, pmap |
| What does a PID identify during exec? | `kern_exec.c`, `kern_fork.c`, `kern_proc.c`, `proc_ro` |
| Where does a Mach port name lead? | IPC space entry, right type, `ipc_port`, queue or kernel object |
| What does a descriptor point at? | `filedesc`, `fileproc`, `fileglob`, `fileops`, vnode/socket/pipe |
| Why is file access denied? | Name lookup context, vnode authorization, credentials, MAC hook, mount flags |
| How does a packet reach a socket? | Interface input, protocol dispatch, IP/TCP/UDP input, socket buffer wakeup |
| Why did a driver attach? | Catalogue personality, matching dictionary, provider relation, `probe`, `start` |
| What initializes this global? | `STARTUP` registration, explicit boot call, `conf/files*`, selected configuration |
| How can I inspect it? | [Observability guide](development/observability.md), `tools/lldbmacros`, corresponding tests |

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
