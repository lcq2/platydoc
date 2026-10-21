# Policy and protocol extensions

[Back to networking](README.md)

Networking policy is applied at several levels: process/socket identity, address/route selection, stream content, IP packets, and interface traffic. These hooks can deny, redirect, transform, retain, or reinject traffic. The simple TCP path in the previous page is a representative allowed path, not an assertion that every socket reaches TCP/IP unchanged.

## NECP: decisions associated with a socket or flow

NECP policy sessions stage owned rule TLVs, then compile ordered socket/IP policies on APPLY. Application evaluation, socket lookup and packet output use related maps with different available inputs. [`necp_socket_find_policy_match()`](../../../xnu/bsd/net/necp.c#L10595-L10998) updates `inp_policyresult`, including generation/hash, terminal decision and accumulated filter/diversion/route-rule results. Outgoing mbuf tags carry selected IDs into IP policy checks; IP output consumes the returned pass/drop/tunnel decision. The [policy-evaluation companion](necp-policy-evaluation.md) traces admission, TLV ownership, compilation/order, map rebuilding, accumulative matching, cache reuse and result consumers, including allocation and copyout failure boundaries.

Persistent NECP clients are separately owned by a client fd. Their UUIDs name path requests; flow-registration UUIDs name concrete socket/nexus registrations below them. A provider assignment can supply a nexus instance/port/key before a later policy change makes the flow nonviable. The [client and flow-registration companion](necp-clients-and-flow-registration.md) follows creation, result evaluation, agent callbacks and asynchronous assignments, observer/readiness semantics, copyout partial progress, claim/remove and close. The remaining signed-query, statistics/cache and specialized multipath/offload interfaces are explicitly bounded there. [`necp_socket_should_use_flow_divert()`](../../../xnu/bsd/net/necp.c#L13581) remains a compact example of consuming the stored decision rather than rerunning the whole compiler.

## Content filters retain and reinject data

The [kernel control socket guide](kernel-control-sockets-and-network-statistics.md) explains the registered-controller transport, callback synchronization and receive enqueue contract used by control providers. Content filters add their own byte-offset and reinjection protocol on top of that transport.

Socket filters (`sflt_*`) and the configured content-filter system (`cfil_*`) are separate interfaces. In [`sosend()`](../../../xnu/bsd/kern/uipc_socket.c#L2390), socket filters run before the content-filter call and protocol send. An `EJUSTRETURN` result is treated as consumed data rather than a normal caller-owned error buffer.

[`cfil_sock_data_out()`](../../../xnu/bsd/net/content_filter.c#L5342) selects a socket's or datagram flow's `cfil_info`. Each provider has independent incoming/outgoing pass and peek offsets and retained-data queues. A peek copies bytes to the provider; a whole-record pass moves the original toward later providers and final injection. [`cfil_service_inject_queue()`](../../../xnu/bsd/net/content_filter.c#L4447) removes permitted originals before invoking protocol send or receive append, so a returned error is not a promise that the same mbuf can be retried.

The [socket content-filter companion](socket-content-filtering.md) follows provider admission, NECP selector matching, flow IDs, numeric offset examples, event/action parsing, datagram ancillary and saved-destination state, locks, backpressure, shutdown, provider disconnect and GC. It records the supplied implementation's retry/accounting limits explicitly. Userspace verdict policy remains an external boundary; [Skywalk netif filters](skywalk-netif-filters-and-reinjection.md) use a separate interface-packet/channel path.

## PF and IPsec operate at packet boundaries

[`pf_af_hook()`](../../../xnu/bsd/net/pf_ioctl.c#L4613), called from IP paths, takes PF perimeter/state protection when appropriate, handles packet-list separation/relinking, and dispatches to IPv4 or IPv6 filtering. It can replace or consume the packet through `mbuf **`. [PF rule publication and state](pf-rules-states-and-packet-ownership.md) follows staged rules, retained rule/key/state relationships, UDP and TCP exchanges, sequence/ACK/window checks, selected loose/proxy branches, NAT/checksum rewriting and purge. [BPF capture and filter lifetime](bpf-capture-and-filter-lifecycle.md) separately follows classic filter programs, listeners and capture buffers.

IPv4 output selects IPsec policy and calls the relevant transform path when configured. [`ipsec4_output()`](../../../xnu/bsd/netinet6/ipsec.c#L3670) walks the policy's `ipsecrequest` chain and constructs security-association lookup inputs; separate routines implement IPv6 transport/tunnel processing. [IPsec policy, associations and transforms](ipsec-policy-associations-and-transforms.md) follows those objects into control publication, association selection/retirement, selected ESP processing, IPv6 stages, ordered request chains and cleanup. Parser, key-management and provider boundaries remain explicit. The directory name `netinet6` does not mean `ipsec.c` is IPv6-only.

[IPsec interface lifecycle](ipsec-interface-lifecycle.md) continues into virtual-interface setup, mbuf/netif/kernel-pipe paths, interface-selected transforms, inbound delivery and disconnect draining. Hook order varies with output mode, injection, bypass flags, configuration, and redirection. Do not extrapolate the BSD IP hook sequence to every Skywalk provider path; inspect that path's actual integration points.

## Flow diversion changes the transport route

[`flow_divert_data_out()`](../../../xnu/bsd/netinet/flow_divert.c#L4214) uses `socket.so_fd_pcb`, validates diverted/PCB state, establishes an implicit connection when needed, checks interface-related restrictions, and sends application data through `flow_divert_send_app_data()`. It has its own tunnel/provider state and accounting. The UDP send path can select diversion based on NECP before ordinary UDP output, while TCP's user-request path also checks diversion state. This is more than changing the IP route of an already constructed packet.

The [flow-diversion companion](flow-diversion-and-provider-lifetime.md) follows provider admission, token/HMAC parsing, PCB/group ownership, CONNECT results, two layers of backpressure, receive buffers, conditional retry/fallback, half-close, detach and provider loss. It includes a numeric stream-credit example and separate datagram behavior. A socket marked diverted does not establish that every byte has reached a provider or network peer; the provider's user-space implementation remains external.

## MPTCP adds a connection above TCP subflows

[`mptses`](../../../xnu/bsd/netinet/mptcp_var.h#L62) links the multipath PCB, MPTCP control block, option list, and subflow list. Individual subflows still use TCP machinery. [`mptcp_usr_send()`](../../../xnu/bsd/netinet/mptcp_usrreq.c#L1052) assigns data-sequence information, appends to the multipath socket send buffer with `SB_NOCOMPRESS`, and invokes `mptcp_output()`. Connection-level data numbering is therefore separate from each subflow's TCP sequence numbering.

The lock relationship is observable in `tcp_lock()`: a subflow redirects to the parent multipath socket's lock. [`mptcp_subflow_add()`](../../../xnu/bsd/netinet/mptcp_subr.c#L2513) connects the session to those TCP sockets. [MPTCP sessions and subflows](mptcp-sessions-and-subflows.md) continues this introduction through admission, publication, path selection, two sequence spaces, reinjection, receive reassembly, fallback and teardown. Its worked exchange and source limits distinguish selected local mechanisms from a complete peer or product configuration.

All these facilities are conditional on build/runtime state (`NECP`, `CONTENT_FILTER`, `FLOW_DIVERT`, `IPSEC`, `MPTCP`, and related options). Source presence describes available implementation, not the configuration of an unspecified Apple product.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
