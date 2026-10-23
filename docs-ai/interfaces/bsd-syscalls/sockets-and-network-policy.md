# BSD syscalls: Sockets and network policy

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 27: recvmsg

`int recvmsg(int s, struct msghdr *msg, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L73) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_RECVMSG`.

Receive socket data, source address and ancillary information.

**Implementation:** [recvmsg](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2359). Imports msghdr/iovecs, uses `recvit`, then copies updated message fields out; dequeue/control-right conversion and final user copyout are separate ownership stages. Ordinary recvmsg tests cancellation.

## 28: sendmsg

`int sendmsg(int s, caddr_t msg, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L74) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SENDMSG`.

Send iovec data and ancillary control information through a socket.

**Implementation:** [sendmsg](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1489). Imports the caller's msghdr/iovec ABI into a `uio`, obtains the socket and invokes `sendit`; control data may carry references. The ordinary wrapper tests cancellation.

## 29: recvfrom

`int recvfrom(int s, void *buf, size_t len, int flags, struct sockaddr *from, int *fromlenaddr) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L75) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_RECVFROM`.

Receive socket bytes and optionally copy the source address out.

**Implementation:** [recvfrom](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2295). The common body builds a user `uio` and calls `recvit`, then releases transfer state; ordinary recvfrom adds a cancellation test before the receive path.

## 30: accept

`int accept(int s, caddr_t name, socklen_t *anamelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L76) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_ACCEPT`.

Remove a completed connection from a listener and create a new descriptor.

**Implementation:** [accept](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L725). The common body checks the listener, waits/scans its accept queue, allocates accepted-socket file state and copies peer address data out; the ordinary entry first tests cancellation.

## 31: getpeername

`int getpeername(int fdes, caddr_t asa, socklen_t *alen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L77) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_GETPEERNAME`.

Read the peer or local socket address.

**Implementation:** [getpeername](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L3212). Pins/locks the socket, asks the socket-filter/protocol name path for a sockaddr, copies the size-limited address and length out, then releases address storage and the file reference.

## 32: getsockname

`int getsockname(int fdes, caddr_t asa, socklen_t *alen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L78) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_GETSOCKNAME`.

Read the peer or local socket address.

**Implementation:** [getsockname](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L3140). Pins/locks the socket, asks the socket-filter/protocol name path for a sockaddr, copies the size-limited address and length out, then releases address storage and the file reference.

## 97: socket

`int socket(int domain, int type, int protocol);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L156) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SOCKET`.

Create a protocol socket descriptor, with delegated process identity in the delegated form.

**Implementation:** [socket](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L252). `socket_common` selects domain/type/protocol, applies policy and allocates/publishes fileproc/socket state. The ordinary entry uses the caller PID; delegation has additional identity/authorization semantics.

## 98: connect

`int connect(int s, caddr_t name, socklen_t namelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L157) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_CONNECT`.

Connect a socket to a protocol peer.

**Implementation:** [connect](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L756). The common body imports the sockaddr and calls `connectit`, coordinating socket state and blocking/nonblocking completion; the ordinary wrapper tests cancellation.

## 104: bind

`int bind(int s, caddr_t name, socklen_t namelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L168) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_BIND`.

Associate a socket with a local protocol address.

**Implementation:** [bind](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L346). Pins the socket descriptor, imports the sockaddr, applies MAC checks and invokes `sobindlock`, then releases address and fileproc ownership.

## 105: setsockopt

`int setsockopt(int s, int level, int name, caddr_t val, socklen_t valsize);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L169) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SETSOCKOPT`.

Set a socket/protocol option.

**Implementation:** [setsockopt](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L3020). Validates option length and descriptor access, applies MAC checks and calls `sosetoptlock` with a user sockopt descriptor; SOL_SOCKET and protocol levels have separate option handlers.

## 106: listen

`int listen(int s, int backlog) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L170) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_LISTEN`.

Put a socket into listening mode with an accept-backlog request.

**Implementation:** [listen](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L407). Pins the socket, applies MAC listen checks and calls `solisten`; the protocol and socket layer manage listener state and queue limits.

## 118: getsockopt

`int getsockopt(int s, int level, int name, caddr_t val, socklen_t *avalsize);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L193) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_GETSOCKOPT`.

Read a socket/protocol option.

**Implementation:** [getsockopt](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L3073). Imports the requested size, applies MAC policy and calls `sogetoptlock`, then copies the resulting size and any option bytes out. This catalog scopes the multiplexor rather than all protocol options.

## 133: sendto

`int sendto(int s, caddr_t buf, size_t len, int flags, caddr_t to, socklen_t tolen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L212) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SENDTO`.

Send bytes to an optional destination through a socket.

**Implementation:** [sendto](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1414). The common body builds a user `uio`, pins the socket and calls `sendit`, which handles address/control/policy and protocol send ownership; ordinary sendto tests cancellation.

## 134: shutdown

`int shutdown(int s, int how);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L213) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SHUTDOWN`.

Disable the selected send/receive direction of a socket.

**Implementation:** [shutdown](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2982). Pins the socket and calls `soshutdown`; half-close changes socket/protocol state while the descriptor and opposite direction may remain live.

## 135: socketpair

`int socketpair(int domain, int type, int protocol, int *rsv) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L214) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SOCKETPAIR`.

Create two connected local socket endpoints and return their descriptors.

**Implementation:** [socketpair](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1209). Creates both sockets/fileprocs, connects them with `soconnect2`, copies descriptor numbers out and publishes reserved slots; failures close/free partial endpoints.

## 337: sendfile

`int sendfile(int fd, int s, off_t offset, off_t *nbytes, struct sf_hdtr *hdtr, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L515) · **Condition:** `(SENDFILE)` · **Audit event:** `AUE_SENDFILE`.

Transfer file data to a socket, optionally surrounding it with header/trailer vectors.

**Implementation:** [sendfile](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L3722). Pins a regular-file vnode and socket, imports the caller ABI, handles header/trailer writes and streams file-backed data through the socket path while tracking partial bytes and references.

## 401: recvmsg_nocancel

`int recvmsg_nocancel(int s, struct msghdr *msg, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L596) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_RECVMSG`.

Receive socket data, source address and ancillary information.

**Implementation:** [recvmsg_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2367). Imports msghdr/iovecs, uses `recvit`, then copies updated message fields out; dequeue/control-right conversion and final user copyout are separate ownership stages. Ordinary recvmsg tests cancellation.

## 402: sendmsg_nocancel

`int sendmsg_nocancel(int s, caddr_t msg, int flags) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L597) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SENDMSG`.

Send iovec data and ancillary control information through a socket.

**Implementation:** [sendmsg_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1497). Imports the caller's msghdr/iovec ABI into a `uio`, obtains the socket and invokes `sendit`; control data may carry references. The ordinary wrapper tests cancellation.

## 403: recvfrom_nocancel

`int recvfrom_nocancel(int s, void *buf, size_t len, int flags, struct sockaddr *from, int *fromlenaddr) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L598) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_RECVFROM`.

Receive socket bytes and optionally copy the source address out.

**Implementation:** [recvfrom_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2303). The common body builds a user `uio` and calls `recvit`, then releases transfer state; ordinary recvfrom adds a cancellation test before the receive path.

## 404: accept_nocancel

`int accept_nocancel(int s, caddr_t name, socklen_t *anamelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L599) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_ACCEPT`.

Remove a completed connection from a listener and create a new descriptor.

**Implementation:** [accept_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L454). The common body checks the listener, waits/scans its accept queue, allocates accepted-socket file state and copies peer address data out; the ordinary entry first tests cancellation.

## 409: connect_nocancel

`int connect_nocancel(int s, caddr_t name, socklen_t namelen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L611) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_CONNECT`.

Connect a socket to a protocol peer.

**Implementation:** [connect_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L764). The common body imports the sockaddr and calls `connectit`, coordinating socket state and blocking/nonblocking completion; the ordinary wrapper tests cancellation.

## 413: sendto_nocancel

`int sendto_nocancel(int s, caddr_t buf, size_t len, int flags, caddr_t to, socklen_t tolen) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L619) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SENDTO`.

Send bytes to an optional destination through a socket.

**Implementation:** [sendto_nocancel](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1421). The common body builds a user `uio`, pins the socket and calls `sendit`, which handles address/control/policy and protocol send ownership; ordinary sendto tests cancellation.

## 447: connectx

`int connectx(int socket, const sa_endpoints_t *endpoints, sae_associd_t associd, unsigned int flags, const struct iovec *iov, unsigned int iovcnt, size_t *len, sae_connid_t *connid);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L678) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_CONNECT`.

Connect using extended endpoint/association and optional initial-data arguments.

**Implementation:** [connectx](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1000). The wrapper tests cancellation then enters `connectx_nocancel`, which imports endpoints/iovecs and selects the protocol's extended connect operation with its association/connection IDs.

## 448: disconnectx

`int disconnectx(int s, sae_associd_t aid, sae_connid_t cid);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L679) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_NULL`.

Disconnect a selected extended socket connection.

**Implementation:** [disconnectx](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1158). Tests cancellation and calls `disconnectx_nocancel`, which resolves the socket and delegates the specified association/connection to protocol disconnect handling.

## 449: peeloff

`int peeloff(int s, sae_associd_t aid);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L680) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_NULL`.

Retain the declared peeloff interface as a local no-op.

**Implementation:** [peeloff](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1146). The body performs an unofficial cancellation-point test and returns zero without splitting a socket association or allocating a new descriptor.

## 450: socket_delegate

`int socket_delegate(int domain, int type, int protocol, pid_t epid);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L681) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_SOCKET`.

Create a protocol socket descriptor, with delegated process identity in the delegated form.

**Implementation:** [socket_delegate](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L261). `socket_common` selects domain/type/protocol, applies policy and allocates/publishes fileproc/socket state. The ordinary entry uses the caller PID; delegation has additional identity/authorization semantics.

## 460: necp_match_policy

`int necp_match_policy(uint8_t *parameters, size_t parameters_size, struct necp_aggregate_result *returned_result);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L711) · **Condition:** `(NECP)` · **Audit event:** `AUE_NECP`.

Evaluate application policy for supplied client parameters without creating a full client object.

**Implementation:** [necp_match_policy](../../../platydoc-data/xnu/bsd/net/necp_client.c#L12537). Copies the parameter buffer, calls `necp_application_find_policy_match_internal`, copies the result structure out and frees the temporary data.

## 480: recvmsg_x

`user_ssize_t recvmsg_x(int s, struct msghdr_x *msgp, u_int cnt, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L735) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_NULL`.

Receive an array of extended message records, including optimized datagram lists.

**Implementation:** [recvmsg_x](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2666). Pins the socket and selects its batch or per-record path. In the optimized branch, `soreceive_m_list` dequeues the packet/address/control lists before individual message-header and iovec imports. Later import/copy failures free remaining lists at cleanup; this path shows no requeue rollback. See [receive-before-import ordering](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2754) and [list cleanup](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L2938).

## 481: sendmsg_x

`user_ssize_t sendmsg_x(int s, struct msghdr_x *msgp, u_int cnt, int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L736) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_NULL`.

Submit an array of extended message records for batched sending.

**Implementation:** [sendmsg_x](../../../platydoc-data/xnu/bsd/kern/uipc_syscalls.c#L1880). Uses `sendit_x`/`sosend_list` where supported or imports individual records into `uio` operations, tracking completed records and freeing imported state on partial failure.

## 490: netagent_trigger

`int netagent_trigger(uuid_t agent_uuid, size_t agent_uuidlen);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L758) · **Condition:** `(NETWORKING)` · **Audit event:** `AUE_NETAGENT`.

Trigger a registered network agent by UUID.

**Implementation:** [netagent_trigger](../../../platydoc-data/xnu/bsd/net/network_agent.c#L3152). Imports/validates UUID and length, finds/locks the agent under registry protection and calls `netagent_send_trigger`; the userspace agent's response/work is external.

## 501: necp_open

`int necp_open(int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L785) · **Condition:** `(NECP)` · **Audit event:** `AUE_NECP`.

Create a descriptor for NECP client registration and observation.

**Implementation:** [necp_open](../../../platydoc-data/xnu/bsd/net/necp_client.c#L8098). Checks privilege/MAC and flags, allocates typed fd/client-list state, initializes locks/knote structures and publishes the descriptor; client/flow operations use it later.

## 502: necp_client_action

`int necp_client_action(int necp_fd, uint32_t action, uuid_t client_id, size_t client_id_len, uint8_t *buffer, size_t buffer_size);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L786) · **Condition:** `(NECP)` · **Audit event:** `AUE_NECP`.

Manage NECP clients, flow registrations, results, agents and nexus requests.

**Implementation:** [necp_client_action](../../../platydoc-data/xnu/bsd/net/necp_client.c#L12395). Looks up a typed NECP fd, checks action-specific MAC policy and dispatches add/claim/remove/copy/flow/agent/request helpers; buffers and IDs have action-specific formats/lifetimes.

## 522: necp_session_open

`int necp_session_open(int flags);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L826) · **Condition:** `(NECP)` · **Audit event:** `AUE_NECP`.

Create a privileged NECP policy-management session descriptor.

**Implementation:** [necp_session_open](../../../platydoc-data/xnu/bsd/net/necp.c#L1034). Checks caller identity/privilege, allocates fileproc/session state through `necp_create_session` and publishes the fd; this is distinct from a client-observer descriptor.

## 523: necp_session_action

`int necp_session_action(int necp_fd, uint32_t action, uint8_t *in_buffer, size_t in_buffer_length, uint8_t *out_buffer, size_t out_buffer_length);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L827) · **Condition:** `(NECP)` · **Audit event:** `AUE_NECP`.

Manage policies in a NECP session.

**Implementation:** [necp_session_action](../../../platydoc-data/xnu/bsd/net/necp.c#L1724). Pins the session and holds its lock while dispatching add/get/delete/list/apply operations and related controls; applying policies updates evaluation state beyond merely copying a rule buffer.

## 525: net_qos_guideline

`int net_qos_guideline(struct net_qos_param *param, uint32_t param_len);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L833) · **Condition:** `always` · **Audit event:** `AUE_NET`.

Query network QoS guidance for the supplied request context.

**Implementation:** [net_qos_guideline](../../../platydoc-data/xnu/bsd/netinet/in_tclass.c#L1959). Imports the parameter structure and inspects selected primary-interface properties such as expensive/constrained status to produce guidance; it does not reserve bandwidth or directly schedule a packet.

## 546: tracker_action

`int tracker_action(int action, char *buffer, size_t buffer_size);`

**Declaration:** [syscalls.master](../../../platydoc-data/xnu/bsd/kern/syscalls.master#L859) · **Condition:** `(SOCKETS)` · **Audit event:** `AUE_TRACKERACTION`.

Manage/query the privileged network tracker registry through an action selector.

**Implementation:** [tracker_action](../../../platydoc-data/xnu/bsd/kern/tracker.c#L956). Checks the required entitlement and dispatches tracker addition/dump operations with bounded user data; this is a registry/control interface rather than transport send/receive.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
