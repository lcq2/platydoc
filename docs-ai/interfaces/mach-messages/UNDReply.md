# Mach messages: UNDReply

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/UserNotification/UNDReply.defs](../../../xnu/osfmk/UserNotification/UNDReply.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 6200: UNDAlertCompletedWithResult_rpc

Deliver an alert's completion result and response dictionary back to the kernel notification object.

**Mechanism:** Requires a nonnull reply object with a notification in progress. Under `KERNEL_CF`, raw XML can be decoded into a dictionary; otherwise the callback receives the raw data pointer. Invokes the stored callback, then locks the reply object and clears its in-progress state and notification key. Callback execution precedes that state reset. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L103).

**Declarations:** [`UNDAlertCompletedWithResult_rpc`](../../../xnu/osfmk/UserNotification/UNDReply.defs#L38) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDAlertCompletedWithResult_rpc(
    reply: UNDReplyRef;
   in result: int;
   in data: xmlData);
```

**Local body:** [`UNDAlertCompletedWithResult_rpc`](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L103).
Calls visible in this body include `IOCFUnserialize`, `CFShow`, `CFRelease`, `UNDReply_lock`, `UNDReply_unlock`.

### 6201: UNDNotificationCreated_rpc

Associate the notification daemon's newly created notification identifier with the kernel request.

**Mechanism:** Locks the reply object and accepts the daemon notification key only if the object is not in progress and its old key equals −1; otherwise it returns invalid argument. These are the actual current checks, despite the adjacent comment suggesting an intermediate notification while processing is underway. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L161).

**Declarations:** [`UNDNotificationCreated_rpc`](../../../xnu/osfmk/UserNotification/UNDReply.defs#L43) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDNotificationCreated_rpc(
    reply: UNDReplyRef;
   in userLandNotificationKey: int);
```

**Local body:** [`UNDNotificationCreated_rpc`](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L161).
Calls visible in this body include `UNDReply_lock`, `UNDReply_unlock`.

[Implementation excerpt](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L161-L177):
<!-- source-excerpt: ../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L161-L177 -->
```c
UNDNotificationCreated_rpc(
	UNDReplyRef     reply,
	int             userLandNotificationKey)
{
	if (reply == UND_REPLY_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	UNDReply_lock(reply);
	if (reply->inprogress || reply->userLandNotificationKey != -1) {
		UNDReply_unlock(reply);
		return KERN_INVALID_ARGUMENT;
	}
	reply->userLandNotificationKey = userLandNotificationKey;
	UNDReply_unlock(reply);
	return KERN_SUCCESS;
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
