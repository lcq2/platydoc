# Policy and protocol extensions

[Back to networking](README.md)

Networking policy is applied at several levels: process/socket identity, address/route selection, stream content, IP packets, and interface traffic. These hooks can deny, redirect, transform, retain, or reinject traffic. The simple TCP path in the previous page is a representative allowed path, not an assertion that every socket reaches TCP/IP unchanged.

## NECP: decisions associated with a socket or flow

[`necp_socket_find_policy_match()`](../../../xnu/bsd/net/necp.c#L10595) evaluates policy using socket/PCB information and optional address/interface overrides, updates `inp_policyresult`, and handles special bypass/drop cases. The stored result includes policy/generation identifiers and outputs such as filter-control units, diversion units, and route rules. `sosend()` updates socket policy; TCP input calls `necp_socket_is_allowed_to_send_recv()` before accepting relevant traffic; IP output can call `necp_ip_output_find_policy_match()` for packet/route-level decisions. The same policy result can therefore influence several stages without those stages being identical checks.

[`necp_socket_should_use_flow_divert()`](../../../xnu/bsd/net/necp.c#L13581) is a compact example of consuming that result: it tests the socket's skip flag and diversion result/aggregate unit. [`necp_client.c`](../../../xnu/bsd/net/necp_client.c) implements the much larger client-action interface and flow-related control work. That control plane was surveyed, not traced end to end; the selected matching/consumer paths do not establish every rule's precedence or all policy-cache invalidation behavior.

## Content filters retain and reinject data

Socket filters (`sflt_*`) and the configured content-filter system (`cfil_*`) are separate interfaces. In [`sosend()`](../../../xnu/bsd/kern/uipc_socket.c#L2390), socket filters run before the content-filter call and protocol send. An `EJUSTRETURN` result is treated as consumed data rather than a normal caller-owned error buffer.

[`cfil_sock_data_out()`](../../../xnu/bsd/net/content_filter.c#L5342) handles datagram flow tracking or a socket's `cfil_info`, validates policy/filter state, requires appropriate socket/buffer locking, and passes data to `cfil_data_common()`. Filter state can hold pending data instead of immediately transmitting it. [`cfil_service_inject_queue()`](../../../xnu/bsd/net/content_filter.c#L4447) removes permitted data from injection queues and calls `sosend_reinject()` on output; receive reinjection uses skip-filter markers and the appropriate receive-buffer machinery. This introduces queue lifetime, backpressure, and close coordination. Content-filter userspace/provider behavior is outside the inspected kernel path.

## PF and IPsec operate at packet boundaries

[`pf_af_hook()`](../../../xnu/bsd/net/pf_ioctl.c#L4613), called from IP paths, takes PF perimeter/state protection when appropriate, handles packet-list separation/relinking, and dispatches to IPv4 or IPv6 filtering. It can replace or consume the packet through `mbuf **`. PF state/rule evaluation lives in [`pf.c`](../../../xnu/bsd/net/pf.c); that algorithm was not audited here. PF is also distinct from BPF capture/filtering in [`bpf.c`](../../../xnu/bsd/net/bpf.c).

IPv4 output selects IPsec policy and calls the relevant transform path when configured. [`ipsec4_output()`](../../../xnu/bsd/netinet6/ipsec.c#L3670) walks the policy's `ipsecrequest` chain and constructs security-association lookup inputs; separate routines implement IPv6 transport/tunnel processing. Security policy, security association, and transformed packet ownership are separate objects. [`key.c`](../../../xnu/bsd/netkey/key.c) and ESP/AH implementation files are the next reading targets, not covered cryptographic audits. The directory name `netinet6` does not mean `ipsec.c` is IPv6-only.

Hook order varies with output mode, injection, bypass flags, configuration, and redirection. Do not extrapolate the BSD IP hook sequence to every Skywalk provider path; inspect that path's actual integration points.

## Flow diversion changes the transport route

[`flow_divert_data_out()`](../../../xnu/bsd/netinet/flow_divert.c#L4214) uses `socket.so_fd_pcb`, validates diverted/PCB state, establishes an implicit connection when needed, checks interface-related restrictions, and sends application data through `flow_divert_send_app_data()`. It has its own tunnel/provider state and accounting. The UDP send path can select diversion based on NECP before ordinary UDP output, while TCP's user-request path also checks diversion state. This is more than changing the IP route of an already constructed packet.

The file's control messages, tunnel lifecycle, and provider reconnection logic are larger than the selected send path and remain a navigation target. Do not interpret a socket marked diverted as evidence that every byte has already reached a provider or network peer.

## MPTCP adds a connection above TCP subflows

[`mptses`](../../../xnu/bsd/netinet/mptcp_var.h#L62) links the multipath PCB, MPTCP control block, option list, and subflow list. Individual subflows still use TCP machinery. [`mptcp_usr_send()`](../../../xnu/bsd/netinet/mptcp_usrreq.c#L1052) assigns data-sequence information, appends to the multipath socket send buffer with `SB_NOCOMPRESS`, and invokes `mptcp_output()`. Connection-level data numbering is therefore separate from each subflow's TCP sequence numbering.

The lock relationship is observable in `tcp_lock()`: a subflow redirects to the parent multipath socket's lock. [`mptcp_subflow_add()`](../../../xnu/bsd/netinet/mptcp_subr.c#L2513) and output/scheduling/reassembly files are the next reading route. This chapter inspected the session structure and user-send/locking boundaries, not path selection, loss recovery, or all MPTCP options.

All these facilities are conditional on build/runtime state (`NECP`, `CONTENT_FILTER`, `FLOW_DIVERT`, `IPSEC`, `MPTCP`, and related options). Source presence describes available implementation, not the configuration of an unspecified Apple product.
