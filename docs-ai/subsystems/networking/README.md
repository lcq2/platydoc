# Networking

[Guide index](../../README.md) · [Architecture](../../architecture.md)

XNU networking contains both a conventional BSD socket stack and Skywalk's channel/nexus infrastructure. They share interfaces, policy, packet scheduling, and compatibility paths, but their userspace interfaces and packet ownership models differ. Start with one concrete packet path before following the many protocol and policy extensions.

This chapter describes the supplied `xnu-12377.121.6` snapshot. It was developed by reading declarations and selected implementation paths; no kernel was built or run. Build options, provider registration, interface capabilities, socket type, and runtime policy determine which branches are active.

## Reading route

1. [Sockets and buffering](sockets.md): fd-to-socket dispatch, protocol registration, lifetime, locking, and readiness.
2. [TCP, IP, interfaces, and mbufs](tcp-ip-interfaces.md): a send and receive path, packet ownership, routing, loopback, and protocol variants.
3. [Policy and protocol extensions](policy-extensions.md): NECP, content filters, PF, IPsec, flow diversion, and MPTCP.
4. [Skywalk channels and flowswitch](skywalk.md): shared rings, packet pools, validation, a concrete transmit path, and host-stack interaction.

Continue with the mechanism guides when the overview raises a lifetime or synchronization question:

| Guide | Concrete questions answered |
| --- | --- |
| [Socket lifetime, buffering, and I/O ownership](socket-lifecycle-and-io.md) | Which reference/lock survives user copy? Who owns data after a failed send? How do receive, ancillary rights, wait-all, upcalls, and close interact? |
| [TCP connections, timers, and close](tcp-connections-and-timers.md) | When are listener children allocated/promoted/accepted? Which ACK/FIN transitions matter? What keeps timer work alive, and how do retransmit, persist, keepalive, and delayed ACK differ? |
| [Packets, routes, and interfaces](packets-routes-and-interfaces.md) | How do shared mbuf storage, route invalidation, protocol callbacks, I/O references, and asynchronous interface detach fit together? |
| [Skywalk channel, pool, and flow lifecycles](skywalk-lifecycles.md) | How do alloc/free rings differ from TX/RX, how is outstanding packet ownership validated, and what survives channel or flow deletion? |

```mermaid
flowchart TB
    S[Socket fd: read/write/send/recv] --> SO[Socket and sockbufs]
    SO --> T[TCP / UDP / other protocol]
    T --> IP[IPv4 / IPv6 and routing]
    IP --> D[DLIL and interface protocols]
    D --> I[ifnet / queues / driver callbacks]
    C[Channel fd and shared rings] --> F[Skywalk flowswitch]
    F --> N[Skywalk netif and device provider]
    N --> I
    F -->|host receive fallback| D
    P[Policy and filtering] -.-> SO
    P -.-> IP
    P -.-> F
    SO --> E[Select / kqueue / workqueue notification]
    C --> E
```

The diagram shows architectural relationships, not a mandatory sequence through every box. A direct netif channel, a UNIX-domain socket, and a TCP socket exercise different paths. The flowswitch TX path examined here copies user-pool packets into device-pool packets; “shared rings” does not establish end-to-end zero-copy behavior.

## Main state and ownership boundaries

| Object | Main job | Source |
| --- | --- | --- |
| `socket`, `sockbuf` | Endpoint state, accept queues, send/receive buffers, readiness | [`socketvar.h`](../../../xnu/bsd/sys/socketvar.h) |
| `domain`, `protosw`, `pr_usrreqs` | Address-family registration and protocol operations | [`domain.h`](../../../xnu/bsd/sys/domain.h), [`protosw.h`](../../../xnu/bsd/sys/protosw.h) |
| `inpcb`, `tcpcb` | Internet addresses/ports/routing and TCP connection state | [`in_pcb.h`](../../../xnu/bsd/netinet/in_pcb.h), [`tcp_var.h`](../../../xnu/bsd/netinet/tcp_var.h) |
| `mbuf` | BSD packet fragments, packet lists, metadata, external storage | [`mbuf.h`](../../../xnu/bsd/sys/mbuf.h) |
| `ifnet`, `if_proto`, `rtentry` | Interface lifetime, family/media callbacks, routes | [`if_var_private.h`](../../../xnu/bsd/net/if_var_private.h), [`route_private.h`](../../../xnu/bsd/net/route_private.h) |
| `kern_channel`, `nexus_adapter`, `kern_nexus` | Skywalk endpoint, ring implementation, provider instance | [`channel_var.h`](../../../xnu/bsd/skywalk/channel/channel_var.h), [`nexus_adapter.h`](../../../xnu/bsd/skywalk/nexus/nexus_adapter.h), [`nexus_var.h`](../../../xnu/bsd/skywalk/nexus/nexus_var.h) |
| `__kern_packet`, `kern_pbufpool` | Skywalk metadata/buffers and allocation ownership | [`packet_var.h`](../../../xnu/bsd/skywalk/packet/packet_var.h), [`pbufpool_var.h`](../../../xnu/bsd/skywalk/packet/pbufpool_var.h) |

Networking enters through [BSD process descriptors](../processes/descriptors-ipc.md), blocks/wakes [Mach threads](../runtime/README.md), consults [credentials and MAC policy](../security/README.md), and connects to [driver infrastructure](../drivers/README.md) through interface/provider callbacks. Socket readiness is part of [BSD kevent machinery](../processes/events-threads.md), not a separate scheduling system.

## Sources inspected and limits

“Detailed” means selected bodies and their immediate ownership/locking relationships were read; it does not imply a complete protocol or concurrency audit.

| Area | Inspection performed | Limits |
| --- | --- | --- |
| [`uipc_syscalls.c`](../../../xnu/bsd/kern/uipc_syscalls.c), [`sys_socket.c`](../../../xnu/bsd/kern/sys_socket.c), [`uipc_socket.c`](../../../xnu/bsd/kern/uipc_socket.c), [`uipc_socket2.c`](../../../xnu/bsd/kern/uipc_socket2.c) | Detailed creation, accept/connect, send consumption/waits, receive copy/peek/control/wait-all, buffer locks, upcalls and close/ref gates | Every option, batched syscall variant, ancillary type, UNIX-domain rights collector, and protocol-specific race was not traced |
| TCP sources and headers | Detailed attach/connect/listen, selected handshake/ACK/FIN branches, accept promotion/dequeue, timer scheduler references, retransmit/persist/keepalive/delayed-ACK handlers and close deferral | Full state-machine/concurrency audit, congestion-control algorithms, SACK/RACK details, and attacks remain outside coverage |
| IPv4, DLIL, interface/routing sources | Detailed selected input/output ownership, protocol callbacks, route cache/gateway/final-release locks, interface object/I/O references, attach serialization and final detach | All fragmentation/reassembly, multicast, neighbor resolution, route mutation, and driver-specific paths remain outside coverage |
| [`uipc_mbuf.c`](../../../xnu/bsd/kern/uipc_mbuf.c) and mbuf declarations | Detailed chain model, copy/external-buffer sharing, pullup consumption, one-chain/list frees and external final release | Cache implementation and every checksum/tag/completion convention were not covered |
| Skywalk channel/ring, flowswitch, netif, packet-pool sources | Detailed open/bind/close, TX/RX and alloc/free synchronization, outstanding-allocation hash/purge, partial allocation, flow installation/rollback/delete/linger, representative TX copy/queue and RX fallback | Complete metadata validation, namespace/route preparation, RX aggregation, arena protection/cache internals, and hardware providers were not audited |
| UDP, IPv6, NECP, content filter, PF, IPsec, flow divert, MPTCP | Selected representative bodies plus navigation survey | These pages identify integration points; they are not complete subsystem specifications |

For source navigation, distinguish three callback families: socket protocol operations (`protosw`), protocols attached to an interface (`if_proto`), and Skywalk provider operations. They connect at specific points and should not be treated as one interchangeable dispatch table.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
