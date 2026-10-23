# Sockets and buffering

[Back to networking](README.md)

Continue with [socket lifetime and I/O ownership](socket-lifecycle-and-io.md) for send consumption, receive/ancillary handling, queue serialization, wait-all, and close, and [TCP connections and timers](tcp-connections-and-timers.md) for listener/accept behavior.

## From descriptor to protocol

[`socket_common()`](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L270) allocates a fileproc, sets its operations to `socketops`, creates a socket, stores the socket as file data, and publishes the descriptor only after successful initialization. The descriptor/fileglob lifetime is described in [process descriptors](../processes/descriptors-ipc.md). A socket is not the same object as its fd, and kernel-created sockets need not have a user fd.

[`socketops`](../../../platydoc-data/xnu/bsd/kern/sys_socket.c#L100) connects ordinary file operations to networking. `soo_read()` calls `so_proto->pr_usrreqs->pru_soreceive`; `soo_write()` calls `pru_sosend`. The explicit `sendmsg`/`sendto` family instead prepares addresses, ancillary data, and a `uio` before [`sendit()`](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1322) invokes that same protocol send interface. Thus `write()` on a socket reaches networking through file operations without first becoming a `sendmsg` syscall.

Three registration objects establish this dispatch:

| Object | Relevant fields | Selection |
| --- | --- | --- |
| [`domain`](../../../platydoc-data/xnu/bsd/sys/domain.h#L133) | `dom_family`, `dom_protosw`, `dom_mtx`, initialization and rights-handling callbacks | Address family, such as local, IPv4, or IPv6 |
| [`protosw`](../../../platydoc-data/xnu/bsd/sys/protosw.h#L255) | `pr_type`, `pr_protocol`, `pr_flags`, `pr_input`, `pr_usrreqs`, locking callbacks | Socket type/protocol within a family |
| [`pr_usrreqs`](../../../platydoc-data/xnu/bsd/sys/protosw.h#L507) | Attach, bind, connect, listen, accept, send, receive, shutdown, detach | Endpoint operations invoked by the socket layer |

[`socreate_internal()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L471) uses `pffindproto()` or `pffindtype()`, validates the match, allocates a socket, and invokes `pru_attach`. The TCP table in [`tcp_usrreq.c`](../../../platydoc-data/xnu/bsd/netinet/tcp_usrreq.c#L1412) selects generic `sosend`/`soreceive` for buffer management but TCP-specific `tcp_usr_send`, connect, attach, and receive-notification routines. Protocol layering is therefore partly direct calls and partly callback dispatch; TCP output is not simply a generic repeated invocation of `pr_output` at every layer.

## Socket state and buffers

[`struct socket`](../../../platydoc-data/xnu/bsd/sys/socketvar.h#L131) stores type/family/protocol, `so_state`, options, `so_error`, protocol/PCB pointers, ownership/policy state, and reference/upcall counts. Listening sockets maintain `so_incomp` and `so_comp` queues, with accepted candidates linking back through `so_head`. A completed connection waiting for `accept()` already has a socket; the syscall gives userspace a descriptor for it. The queue/lifetime design is visible in `sonewconn_internal()` and `sofreelastref()`.

The embedded `so_snd` and `so_rcv` are `sockbuf` objects. Important fields are:

- `sb_mb`, `sb_mbtail`, and `sb_lastrecord`: mbuf chains and record boundaries.
- `sb_cc` versus `sb_mbcnt`: buffered bytes versus allocated mbuf/storage accounting.
- `sb_hiwat`, `sb_mbmax`, and `sb_lowat`: capacity and readiness/wait thresholds.
- `sb_sel`, wait counts, `SB_SEL`, `SB_KNOTE`, and upcall fields: notification state.
- `SB_LOCK`: serialized use of the data queue during operations that may drop the socket mutex.

Limits on byte occupancy and memory occupancy are separate. TCP's send buffer also retains data after a packet has been passed toward the interface, because retransmission and acknowledgment processing still need it. UDP records preserve message boundaries; TCP exposes a byte stream even though its buffer uses mbufs internally.

## Send and receive contracts

[`sosend()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L2045) acquires a socket use reference/lock, updates owner and policy information, checks flags and length, and applies `sosendcheck()`/sockbuf serialization. The ordinary userspace path allocates mbufs and uses `uiomove()` to copy data from the `uio`, dropping/reacquiring the socket mutex around relevant copy/allocation work. The buffer serialization and socket reference must survive those unlocks.

Before protocol delivery it invokes socket filters and, when configured, content-filter processing. A filter returning `EJUSTRETURN` can mean it consumed the data. Otherwise `pru_send` takes the chain; `sosend()` clears its local `top`/`control` pointers at the consumption boundary. Error cleanup frees only data still owned locally. Understanding that boundary is more useful than assuming a nonzero C error always leaves ownership with the caller.

[`soreceive()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L3202) locks/references the socket, serializes receive-buffer access, checks connection/error/EOF conditions, and waits through `sbwait()` when appropriate. Its normal data-copy path moves buffered bytes to the userspace `uio`; `MSG_PEEK`, record boundaries, control/address data, and kernel mbuf-return callers have different handling. It invokes `pru_rcvd` where needed after consuming data, allowing TCP to react to newly available receive space. A short read can occur without connection closure.

`sendit()` reports bytes consumed from the `uio`, with interrupted/would-block errors suppressed after partial progress. `EPIPE` can generate `SIGPIPE` unless disabled for the socket or the call. None of these returns prove that the remote application has consumed data. TCP acknowledgment and application-level receipt are later, distinct events.

## Lock selection is protocol-dependent

[`socket_lock()` and `socket_unlock()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L7237) call `pr_lock`/`pr_unlock` when present; otherwise they use the domain mutex. Their `refcount` argument controls a socket use-reference increment/decrement in addition to locking. `socket_getlock()` exposes the appropriate mutex for sleep/assertion paths.

For an ordinary TCP connection, [`tcp_lock()`](../../../platydoc-data/xnu/bsd/netinet/tcp_subr.c#L3523) selects `inpcb.inpcb_mtx`. MPTCP subflow sockets redirect locking to the multipath socket and retry if their relationship changes while waiting. There is therefore no universal standalone `so_lock` field to grab for every protocol. The PCB table's `ipi_lock`, a particular PCB/socket lock, sockbuf serialization, and interface locks protect different state.

## Readiness and final teardown

[`soo_select()`](../../../platydoc-data/xnu/bsd/kern/sys_socket.c#L297) checks `soreadable()`/`sowriteable()` under socket locking or records interest in a sockbuf's `selinfo`. [`sorwakeup()` and `sowwakeup()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket2.c#L2671) lead to `sowakeup()`, which wakes select and sleeping buffer users, delivers configured `SIGIO`, invokes `KNOTE`, and handles optional kernel upcalls. Upcalls can execute with the socket unlocked; `so_upcallusecount` prevents close from tearing the object down during one. Knotes then use the [shared kevent/workqueue machinery](../processes/events-threads.md).

The last fileglob close reaches `soo_close()` and `soclose()`. [`soclose_locked()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L1114) coordinates upcalls/content filters, listener queues, disconnect/linger behavior, and protocol detach. [`sofreelastref()`](../../../platydoc-data/xnu/bsd/kern/uipc_socket.c#L991) tests `SS_NOFDREF` and `SOF_PCBCLEARING` before final decommissioning and protects completed accept-queue entries. Removing the last fd and freeing all protocol/socket state are separate events; TCP may have protocol work remaining after userspace closes its handle.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
