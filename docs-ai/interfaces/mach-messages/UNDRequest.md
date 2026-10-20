# Mach messages: UNDRequest

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/UserNotification/UNDRequest.defs](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 6000: UNDExecute_rpc

**Interface contract:**

> Execution information

**Mechanism:** `KUNCExecute` obtains a referenced notification-server port, sends the execution path and UID/GID, releases the port and returns the RPC status. An unavailable endpoint returns `MACH_SEND_INVALID_DEST`. The user notification daemon's execution and authorization implementation is not present. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L208).

**Declarations:** [`UNDExecute_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L44) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDExecute_rpc(
    server: UNDServerRef;
   in executionPath: UNDPath;
   in uid: int;
   in gid: int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/UserNotification/KUNCUserNotifications.c:217](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L217). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6001: UNDDisplayNoticeFromBundle_rpc

**Interface contract:**

> Bundle notice and bundle alert

**Mechanism:** This is a daemon request declaration, not a local kobject service. Its bundle/notification parameters and output contract are shown below, but no same-symbol implementation or direct local sender was resolved. The daemon receiver and its UI/cancellation behavior are unavailable in this checkout.

**Declarations:** [`UNDDisplayNoticeFromBundle_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L52) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDDisplayNoticeFromBundle_rpc(
    server: UNDServerRef;
   in reply: UNDReplyRef;
   in bundlePath: UNDPath;
   in fileName: UNDPath;
   in fileExtension: UNDPath;
   in messageKey: UNDKey);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 6002: UNDDisplayAlertFromBundle_rpc

Ask the notification daemon to display an alert using resources in the specified bundle.

**Mechanism:** This is a daemon request declaration, not a local kobject service. Its bundle/notification parameters and output contract are shown below, but no same-symbol implementation or direct local sender was resolved. The daemon receiver and its UI/cancellation behavior are unavailable in this checkout.

**Declarations:** [`UNDDisplayAlertFromBundle_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L60) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDDisplayAlertFromBundle_rpc(
    server: UNDServerRef;
   in reply: UNDReplyRef;
   in bundlePath: UNDPath;
   in fileName: UNDKey;
   in fileExtension: UNDKey;
   in messageKey: UNDKey);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 6003: UNDDisplayCustomFromBundle_rpc

Ask the notification daemon to display the bundle's custom notification content.

**Mechanism:** The bundle wrapper validates idle reply-object state under its lock, sets in-progress/callback fields and creates a send right to the reply kobject before requesting the daemon operation. The exported reply capability is the callback path for completion. A later RPC or endpoint failure occurs after those state changes; the wrapper shown does not roll them back. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L294).

**Declarations:** [`UNDDisplayCustomFromBundle_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L68) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDDisplayCustomFromBundle_rpc(
    server: UNDServerRef;
   in reply: UNDReplyRef;
   in bundlePath: UNDPath;
   in fileName: UNDKey;
   in fileExtension: UNDKey;
   in messageKey: UNDKey;
   in tokenKey: UNDPath);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/UserNotification/KUNCUserNotifications.c:324](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L324). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6004: reserved

`skip` in all listed profiles. [Source slot](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L77).

### 6005: UNDCancelNotification_rpc

**Interface contract:**

> was UNDDisplayCustomFromDictionary_rpc

**Mechanism:** This is a daemon request declaration, not a local kobject service. Its bundle/notification parameters and output contract are shown below, but no same-symbol implementation or direct local sender was resolved. The daemon receiver and its UI/cancellation behavior are unavailable in this checkout.

**Declarations:** [`UNDCancelNotification_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L79) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDCancelNotification_rpc(
    server: UNDServerRef;
   in userLandNotificationKey: int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 6006: UNDDisplayNoticeSimple_rpc

**Interface contract:**

> Just pops up a notice with a single OK button and the label and message specified below. As such, there is no acknowledgement from the server.

**Mechanism:** The local notice wrapper forwards timeout, flags and bounded UI/path strings to the referenced notification daemon and releases that endpoint afterward. There is no response-button output in this notice form. UI presentation and daemon policy are external; the wrapper reports invalid destination when no server port exists. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L225).

**Declarations:** [`UNDDisplayNoticeSimple_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L87) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine UNDDisplayNoticeSimple_rpc(
    server: UNDServerRef;
                        in rpctimeout: int;
                        in flags: unsigned;
                        in iconPath:UNDLabel;
                        in soundPath:UNDLabel;
                        in localizationPath:UNDLabel;
   in header: UNDLabel;
   in message: UNDMessage;
                        in defaultButtonTitle:UNDLabel);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/UserNotification/KUNCUserNotifications.c:240](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L240). These may be senders, wrappers or declarations; they do not establish a local receiver.

### 6007: UNDDisplayAlertSimple_rpc

**Interface contract:**

> A synchronous routine to display an alert. This will wait for the result to come back. As this can take an exceedingly long time to complete (and will block the calling thread for the duration) great care should be exercised before using this method.

**Mechanism:** The local alert wrapper forwards timeout, flags, presentation strings and button titles to the referenced daemon and supplies a response-flags output. Releases the daemon port after the RPC. The checkout exposes the request/reply contract, not the actual dialog implementation. [Local path](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L256).

**Declarations:** [`UNDDisplayAlertSimple_rpc`](../../../xnu/osfmk/UserNotification/UNDRequest.defs#L104) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine UNDDisplayAlertSimple_rpc(
    server: UNDServerRef;
                        in rpctimeout: int;
                        in flags: unsigned;
                        in iconPath:UNDLabel;
                        in soundPath:UNDLabel;
                        in localizationPath:UNDLabel;
   in header: UNDLabel;
   in message: UNDMessage;
                        in defaultButtonTitle:UNDLabel;
                        in alternateButtonTitle:UNDLabel;
                        in otherButtonTitle:UNDLabel;
   out response: unsigned);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/UserNotification/KUNCUserNotifications.c:274](../../../xnu/osfmk/UserNotification/KUNCUserNotifications.c#L274). These may be senders, wrappers or declarations; they do not establish a local receiver.
