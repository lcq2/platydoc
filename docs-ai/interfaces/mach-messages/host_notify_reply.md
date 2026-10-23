# Mach messages: host_notify_reply

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/host_notify_reply.defs](../../../platydoc-data/xnu/osfmk/mach/host_notify_reply.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 950: host_calendar_changed

Notify a registered receiver that calendar time changed.

**Mechanism:** The local host-notify helper constructs the generated request type for `HOST_NOTIFY_CALENDAR_CHANGE`, detaches eligible live registrations under the notify/port locks, then sends after releasing the list lock. It fills `msgh_id` from the reply-ID table and moves each registered send-once right. Delivery consumes the registration; calendar subscribers must register again as required. [Local path](../../../platydoc-data/xnu/osfmk/kern/host_notify.c#L203).

**Declarations:** [`host_calendar_changed`](../../../platydoc-data/xnu/osfmk/mach/host_notify_reply.defs#L37) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine host_calendar_changed(
  notify_port : mach_port_move_send_once_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 951: host_calendar_set

Notify a registered receiver of a calendar-time set operation.

**Mechanism:** The local host-notify helper constructs the generated request type for `HOST_NOTIFY_CALENDAR_SET`, detaches eligible live registrations under the notify/port locks, then sends after releasing the list lock. It fills `msgh_id` from the reply-ID table and moves each registered send-once right. Delivery consumes the registration; calendar subscribers must register again as required. [Local path](../../../platydoc-data/xnu/osfmk/kern/host_notify.c#L211).

**Declarations:** [`host_calendar_set`](../../../platydoc-data/xnu/osfmk/mach/host_notify_reply.defs#L40) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine host_calendar_set(
  notify_port : mach_port_move_send_once_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
