# BSD syscalls: Skywalk

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 503: __nexus_open

`int __nexus_open(struct nxctl_init *init, uint32_t init_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L792) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Create a Skywalk nexus-controller descriptor.

**Implementation:** [__nexus_open](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L83). Validates/copies initialization, creates a guard identity and reserved fd, calls `nxctl_create`, copies result state out and then publishes the controller fileproc; failed construction unwinds the reservation.

## 504: __nexus_register

`int __nexus_register(int ctl, struct nxprov_reg *reg, uint32_t reg_len, uuid_t *prov_uuid, uint32_t prov_uuid_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L793) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Register a provider owned by a nexus controller.

**Implementation:** [__nexus_register](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L171). Imports provider parameters, obtains the controller descriptor and lock, calls `nxprov_create`, and copies the provider UUID out. On an error after creation, cleanup drops the descriptor, calls `nxprov_close`, then releases the extra provider reference. The close result replaces the original error, including a UUID copyout error, and can be zero. See [cleanup ordering](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L232).

## 505: __nexus_deregister

`int __nexus_deregister(int ctl, uuid_t prov_uuid, uint32_t prov_uuid_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L794) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Remove a controller-owned provider registration.

**Implementation:** [__nexus_deregister](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L248). Imports/checks the provider UUID, pins and locks the controller, calls `nxprov_destroy` and releases the reference; dependent object teardown follows provider lifecycle rules.

## 506: __nexus_create

`int __nexus_create(int ctl, uuid_t prov_uuid, uint32_t prov_uuid_len, uuid_t *nx_uuid, uint32_t nx_uuid_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L795) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Allocate a nexus instance from a registered provider.

**Implementation:** [__nexus_create](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L294). Imports the provider UUID, pins/locks the controller and calls `nx_create`, then copies the new nexus UUID out. Cleanup drops the descriptor and extra caller reference; it does not undo successful instance creation on UUID copyout failure. Provider/global-list references retain the published instance. See [publication references](../../../xnu/bsd/skywalk/nexus/nexus.c#L1956) and [syscall cleanup](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L342).

## 507: __nexus_destroy

`int __nexus_destroy(int ctl, uuid_t nx_uuid, uint32_t nx_uuid_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L796) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Destroy a nexus instance through its controller.

**Implementation:** [__nexus_destroy](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L361). Imports/checks the UUID, pins/locks the controller and invokes `nx_destroy`; instance closure and final reference release can be distinct.

## 508: __nexus_get_opt

`int __nexus_get_opt(int ctl, uint32_t opt, void *aoptval, uint32_t *aoptlen);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L797) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Query controller/provider/instance configuration selected by a nexus option.

**Implementation:** [__nexus_get_opt](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L407). Builds a user sockopt, pins/locks the controller and calls `nxctl_get_opt`, then copies the returned output length and releases the descriptor reference.

## 509: __nexus_set_opt

`int __nexus_set_opt(int ctl, uint32_t opt, const void *aoptval, uint32_t optlen);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L798) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_NEXUS`.

Apply a nexus bind/unbind/configuration/control option.

**Implementation:** [__nexus_set_opt](../../../xnu/bsd/skywalk/nexus/nexus_syscalls.c#L470). Pins/locks the controller and sends the user sockopt to `nxctl_set_opt`; the option handler interprets the specific UUID/port/configuration payload.

## 510: __channel_open

`int __channel_open(struct ch_init *init, uint32_t init_len);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L799) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_CHANNEL`.

Create a guarded Skywalk channel descriptor bound to a nexus/port/ring selection.

**Implementation:** [__channel_open](../../../xnu/bsd/skywalk/channel/channel_syscalls.c#L137). Imports and validates initialization/key data, reserves a guarded fd and calls `ch_open`; result copyout precedes final fd publication, with teardown on failure.

## 511: __channel_get_info

`int __channel_get_info(int c, struct ch_info *cinfo, uint32_t cinfolen);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L800) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_CHANNEL`.

Read a channel's exported identity/layout information.

**Implementation:** [__channel_get_info](../../../xnu/bsd/skywalk/channel/channel_syscalls.c#L286). Pins a typed channel fd, validates output sizing and copies `ch_info` under the channel lock, then drops the descriptor reference.

## 512: __channel_sync

`int __channel_sync(int c, int mode, int flags);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L801) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_CHANNEL`.

Synchronize user and kernel ownership across selected channel rings.

**Implementation:** [__channel_sync](../../../xnu/bsd/skywalk/channel/channel_syscalls.c#L356). Pins/locks the channel, checks active/admissible state, enters sync protection and ring serialization, runs validation/prologue/provider-sync/finalize routines and records partial progress/errors.

## 513: __channel_get_opt

`int __channel_get_opt(int c, uint32_t opt, void *aoptval, uint32_t *aoptlen);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L802) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_CHANNEL`.

Read channel-specific options.

**Implementation:** [__channel_get_opt](../../../xnu/bsd/skywalk/channel/channel_syscalls.c#L670). Pins/locks the typed channel and dispatches `ch_get_opt` using a bounded user sockopt; output length is copied back separately.

## 514: __channel_set_opt

`int __channel_set_opt(int c, uint32_t opt, const void *aoptval, uint32_t optlen);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L803) · **Condition:** `(SKYWALK)` · **Audit event:** `AUE_CHANNEL`.

Change permitted channel options.

**Implementation:** [__channel_set_opt](../../../xnu/bsd/skywalk/channel/channel_syscalls.c#L734). Pins/locks the channel, rejects inactive/nonpermissive adapters and invokes `ch_set_opt`; option handling is distinct from submitting packets through sync.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
