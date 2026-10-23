# Mach messages: notify

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/notify.defs](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 64: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L76).

### 65: mach_notify_port_deleted

**Interface contract:**

> MACH_NOTIFY_PORT_DELETED: 0101

**Mechanism:** The IPC notification wrapper sends the registered name on a send-once destination if that destination remains active. If it has died, the wrapper releases the send-once right instead. The message reports a namespace/right event to the registered receiver; it is not dispatched through an ordinary kernel kobject routine. See [port lifecycle](../../subsystems/ipc/ports-and-rights-lifecycle.md). [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L116).

**Declarations:** [`mach_notify_port_deleted`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L79) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_notify_port_deleted(
  notify : mach_port_move_send_once_t;
  name : mach_port_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:119](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L119). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 66: mach_notify_send_possible

**Interface contract:**

> MACH_NOTIFY_SEND_POSSIBLE: 0102

**Mechanism:** The IPC notification wrapper sends the registered name on a send-once destination if that destination remains active. If it has died, the wrapper releases the send-once right instead. The message reports a namespace/right event to the registered receiver; it is not dispatched through an ordinary kernel kobject routine. See [port lifecycle](../../subsystems/ipc/ports-and-rights-lifecycle.md). [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L105).

**Declarations:** [`mach_notify_send_possible`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L88) (`sender64`).
**Reserved instead in:** `server64`, `server32`, `client64`, `client32`, `libsyscall64`, `local64`.

**Fields after preprocessing (`sender64`):**

```text
simpleroutine mach_notify_send_possible(
  notify : mach_port_move_send_once_t;
  name : mach_port_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:108](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L108). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 67: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L98).

### 68: reserved

`skip` in all listed profiles. [Source slot](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L100).

### 69: mach_notify_port_destroyed

**Interface contract:**

> MACH_NOTIFY_PORT_DESTROYED: 0105

**Mechanism:** The wrapper sends the receive right itself in the port-destroyed notification, allowing a registered backup receiver to take ownership. This differs from reporting a numeric name whose port has irreversibly died. The destination and transferred receive capability are owned by the notification transport. [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L127).

**Declarations:** [`mach_notify_port_destroyed`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L103) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_notify_port_destroyed(
  notify : mach_port_move_send_once_t;
  rights : mach_port_move_receive_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:129](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L129). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 70: mach_notify_no_senders

**Interface contract:**

> MACH_NOTIFY_NO_SENDERS: 0106

**Mechanism:** The ordinary-port path removes the registered send-once request under the port lock and sends its make-send count if the destination is active, otherwise releases that right. Kernel kobjects use a separate direct `pol_kobject_no_senders` callback with a retained port; they do not all receive this MIG message. [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L133).

**Declarations:** [`mach_notify_no_senders`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L111) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_notify_no_senders(
  notify : mach_port_move_send_once_t;
  mscount : mach_port_mscount_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:164](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L164). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 71: mach_notify_send_once

**Interface contract:**

> MACH_NOTIFY_SEND_ONCE: 0107

**Mechanism:** When a send-once right is disposed, the helper clears reply context and chooses among dead-port release, an in-kernel kobject notification, full-kernel-port release, or an ordinary one-way notification after unlocking. Only the last branch sends this message to a user receiver. [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L185).

**Declarations:** [`mach_notify_send_once`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L119) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_notify_send_once(
  notify : mach_port_move_send_once_t
  );
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:198](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L198). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 72: mach_notify_dead_name

**Interface contract:**

> MACH_NOTIFY_DEAD_NAME: 0110

**Mechanism:** The IPC notification wrapper sends the registered name on a send-once destination if that destination remains active. If it has died, the wrapper releases the send-once right instead. The message reports a namespace/right event to the registered receiver; it is not dispatched through an ordinary kernel kobject routine. See [port lifecycle](../../subsystems/ipc/ports-and-rights-lifecycle.md). [Local path](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L94).

**Declarations:** [`mach_notify_dead_name`](../../../platydoc-data/xnu/osfmk/mach/notify.defs#L127) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine mach_notify_dead_name(
  notify : mach_port_move_send_once_t;
  name : mach_port_name_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/ipc/ipc_notify.c:97](../../../platydoc-data/xnu/osfmk/ipc/ipc_notify.c#L97). These may be senders, wrappers or declarations; they do not establish a local receiver.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
