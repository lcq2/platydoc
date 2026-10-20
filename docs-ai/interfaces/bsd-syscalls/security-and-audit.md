# BSD syscalls: Security and audit

[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)

This page is generated from `syscalls.master` and authored `descriptions.json`. The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. Descriptions identify selected local mechanisms; they do not claim every branch was audited.

## 169: csops

`int csops(pid_t pid, uint32_t ops, user_addr_t useraddr, user_size_t usersize);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L265) · **Condition:** `always` · **Audit event:** `AUE_CSOPS`.

Inspect or change process code-signing state using an operation selector; the audit-token variant additionally binds the request to a process identity.

**Implementation:** [csops](../../../xnu/bsd/kern/kern_proc.c#L3652). Both reach `csops_internal`, which resolves the target process, applies operation-specific authorization, and switches among status, identity/blob retrieval, and flag-changing requests. The audit-token form rejects a null token before entering that helper. These are process signing operations, distinct from installing a vnode signature with `fcntl`.

## 170: csops_audittoken

`int csops_audittoken(pid_t pid, uint32_t ops, user_addr_t useraddr, user_size_t usersize, user_addr_t uaudittoken);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L266) · **Condition:** `always` · **Audit event:** `AUE_CSOPS`.

Inspect or change process code-signing state using an operation selector; the audit-token variant additionally binds the request to a process identity.

**Implementation:** [csops_audittoken](../../../xnu/bsd/kern/kern_proc.c#L3659). Both reach `csops_internal`, which resolves the target process, applies operation-specific authorization, and switches among status, identity/blob retrieval, and flag-changing requests. The audit-token form rejects a null token before entering that helper. These are process signing operations, distinct from installing a vnode signature with `fcntl`.

## 350: audit

`int audit(void *record, int length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L531) · **Condition:** `always` · **Audit event:** `AUE_AUDIT`.

Submit a userspace BSM audit record for inclusion with a kernel audit record.

**Implementation:** [audit](../../../xnu/bsd/security/audit/audit_syscalls.c#L147), [audit](../../../xnu/bsd/security/audit/audit_syscalls.c#L1259). The handler checks privilege or the audit-user entitlement, bounds and imports the record, validates it, and normally splices in an identity token. It attaches the resulting buffer to `kaudit_record.k_udata` with `AR_COMMIT_USER` and user trail/pipe selection flags; the audit completion path owns it afterward. Without `CONFIG_AUDIT`, the alternate body returns `ENOSYS`.

## 351: auditon

`int auditon(int cmd, void *data, int length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L532) · **Condition:** `always` · **Audit event:** `AUE_AUDITON`.

Read or modify selected audit subsystem controls.

**Implementation:** [auditon](../../../xnu/bsd/security/audit/audit_syscalls.c#L367), [auditon](../../../xnu/bsd/security/audit/audit_syscalls.c#L1267). The command switch handles policy, queue limits, event/class mappings, audit condition and process/session-related requests using command-specific privilege, MAC and size checks, with `audit_mtx` protecting shared settings. This is a control-command family, not an arbitrary kernel-memory interface. The non-audit build returns `ENOSYS`.

## 353: getauid

`int getauid(au_id_t *auid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L534) · **Condition:** `always` · **Audit event:** `AUE_GETAUID`.

Read the calling process's audit user ID.

**Implementation:** [getauid](../../../xnu/bsd/security/audit/audit_syscalls.c#L994), [getauid](../../../xnu/bsd/security/audit/audit_syscalls.c#L1275). After the MAC check, the handler reads `cr_audit.as_aia_p->ai_auid` from the cached process credential and copies the scalar to userspace. The alternate `!CONFIG_AUDIT` body returns `ENOSYS`.

## 354: setauid

`int setauid(au_id_t *auid);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L535) · **Condition:** `always` · **Audit event:** `AUE_SETAUID`.

Change the process's audit user ID while preserving the other current session information.

**Implementation:** [setauid](../../../xnu/bsd/security/audit/audit_syscalls.c#L1017), [setauid](../../../xnu/bsd/security/audit/audit_syscalls.c#L1283). The handler imports the ID, performs MAC and superuser checks, copies the credential's session data and selection mask, requests a new session ID when necessary, and publishes through `audit_session_setaia`. Without `CONFIG_AUDIT` it returns `ENOSYS`.

## 357: getaudit_addr

`int getaudit_addr(struct auditinfo_addr *auditinfo_addr, int length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L538) · **Condition:** `always` · **Audit event:** `AUE_GETAUDIT_ADDR`.

Retrieve the calling process's extended audit identity and address/session information.

**Implementation:** [getaudit_addr](../../../xnu/bsd/security/audit/audit_syscalls.c#L1077), [getaudit_addr](../../../xnu/bsd/security/audit/audit_syscalls.c#L1291). The handler checks MAC policy and delegates sized export to `getaudit_addr_internal`, using the process credential's audit session and selection mask. The non-audit alternate returns `ENOSYS`.

## 358: setaudit_addr

`int setaudit_addr(struct auditinfo_addr *auditinfo_addr, int length);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L539) · **Condition:** `always` · **Audit event:** `AUE_SETAUDIT_ADDR`.

Install extended audit identity, terminal address, mask and session information.

**Implementation:** [setaudit_addr](../../../xnu/bsd/security/audit/audit_syscalls.c#L1097), [setaudit_addr](../../../xnu/bsd/security/audit/audit_syscalls.c#L1299). The handler zero-initializes and imports a bounded structure, validates address family and session ID, checks MAC and superuser authority, then calls `audit_session_setaia`. If assigning a new session ID, it obtains the newly published credential and copies the assigned information back. Without `CONFIG_AUDIT` it returns `ENOSYS`.

## 359: auditctl

`int auditctl(char *path);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L540) · **Condition:** `always` · **Audit event:** `AUE_AUDITCTL`.

Replace the vnode used as the audit trail destination.

**Implementation:** [auditctl](../../../xnu/bsd/security/audit/audit_syscalls.c#L1170), [auditctl](../../../xnu/bsd/security/audit/audit_syscalls.c#L1307). The handler requires superuser authority and, in external-control mode, the reserved entitlement; a null path is rejected. It opens and checks a regular vnode, applies MAC policy, retains the credential and hands the destination to `audit_rotate_vnode`, balancing its vnode iocount afterward. The non-audit alternate returns `ENOSYS`.

## 381: __mac_syscall

`int __mac_syscall(char *policy, int call, user_addr_t arg);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L563) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_SYSCALL`.

Invoke an operation implemented by a named MAC policy.

**Implementation:** [__mac_syscall](../../../xnu/security/mac_base.c#L1564). After importing the policy name and applying `mac_proc_check_mac_syscall`, the handler searches static registrations and then the dynamically protected registry. It calls the matching `mpo_policy_syscall`; dynamic traversal is paired with `mac_policy_list_unbusy`. An absent matching callback yields `ENOPOLICY`; the policy owns its operation ABI.

## 382: __mac_get_file

`int __mac_get_file(char *path_p, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L564) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_FILE`.

Export selected MAC labels from a pathname, with the file form following the final symbolic link and the link form not following it.

**Implementation:** [__mac_get_file](../../../xnu/security/mac_base.c#L1393). `mac_get_filelink` imports the requested label elements through `mac_do_get`, resolves the vnode with `namei`, copies its label into temporary storage, externalizes it and drops the vnode iocount and label. The callback implementations determine which label elements exist.

## 383: __mac_set_file

`int __mac_set_file(char *path_p, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L565) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_SET_FILE`.

Set MAC label elements on a pathname, following or not following the final symbolic link according to the variant.

**Implementation:** [__mac_set_file](../../../xnu/security/mac_base.c#L1518). `mac_set_filelink` requires vnode labeling, allocates and internalizes a temporary label, resolves the vnode with the appropriate `FOLLOW`/`NOFOLLOW` flag, and invokes `vn_setlabel`. Each failure path releases the temporary label and any acquired vnode iocount.

## 384: __mac_get_link

`int __mac_get_link(char *path_p, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L566) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_LINK`.

Export selected MAC labels from a pathname, with the file form following the final symbolic link and the link form not following it.

**Implementation:** [__mac_get_link](../../../xnu/security/mac_base.c#L1400). `mac_get_filelink` imports the requested label elements through `mac_do_get`, resolves the vnode with `namei`, copies its label into temporary storage, externalizes it and drops the vnode iocount and label. The callback implementations determine which label elements exist.

## 385: __mac_set_link

`int __mac_set_link(char *path_p, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L567) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_SET_LINK`.

Set MAC label elements on a pathname, following or not following the final symbolic link according to the variant.

**Implementation:** [__mac_set_link](../../../xnu/security/mac_base.c#L1525). `mac_set_filelink` requires vnode labeling, allocates and internalizes a temporary label, resolves the vnode with the appropriate `FOLLOW`/`NOFOLLOW` flag, and invokes `vn_setlabel`. Each failure path releases the temporary label and any acquired vnode iocount.

## 386: __mac_get_proc

`int __mac_get_proc(struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L568) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_PROC`.

Export selected MAC label elements from the current credential.

**Implementation:** [__mac_get_proc](../../../xnu/security/mac_base.c#L1265). `mac_do_get` handles the userspace label request and output buffer; its callback obtains `mac_cred_label(kauth_cred_get())` and calls `mac_cred_label_externalize`.

## 387: __mac_set_proc

`int __mac_set_proc(struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L569) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_SET_PROC`.

Request a MAC credential-label update for the calling process.

**Implementation:** [__mac_set_proc](../../../xnu/security/mac_base.c#L1278). `mac_do_set` imports the text; the callback allocates and internalizes a credential label, checks `mac_cred_check_label_update`, and calls `kauth_proc_label_update`. Temporary label storage is freed on both success and failure.

## 388: __mac_get_fd

`int __mac_get_fd(int fd, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L570) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_FD`.

Export MAC label elements from a vnode-backed descriptor.

**Implementation:** [__mac_get_fd](../../../xnu/security/mac_base.c#L1303). The handler retains the `fileproc`, applies `mac_file_check_get`, obtains a vnode iocount, copies and externalizes its label, then balances both references. Despite a nearby historical comment, the switch implements only `DTYPE_VNODE`; socket and other descriptor kinds return `ENOSYS`.

## 389: __mac_set_fd

`int __mac_set_fd(int fd, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L571) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_SET_FD`.

Set MAC label elements on a vnode-backed descriptor.

**Implementation:** [__mac_set_fd](../../../xnu/security/mac_base.c#L1407). After `fp_lookup` and `mac_file_check_set`, the vnode branch requires labeling, internalizes a temporary label and calls `vn_setlabel` while holding a vnode iocount. Other descriptor kinds return `ENOSYS`; `fp_drop` and label cleanup balance ownership.

## 390: __mac_get_pid

`int __mac_get_pid(pid_t pid, struct mac *mac_p);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L572) · **Condition:** `(CONFIG_MACF)` · **Audit event:** `AUE_MAC_GET_PID`.

Export selected credential-label elements for a process ID.

**Implementation:** [__mac_get_pid](../../../xnu/security/mac_base.c#L1242). The `mac_do_get` callback obtains a referenced credential with `kauth_cred_proc_ref_for_pid`, returns `ESRCH` if absent, externalizes its label, and releases the credential. This reads credential labels, not arbitrary per-thread policy state.

## 428: audit_session_self

`mach_port_name_t audit_session_self(void);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L646) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Obtain a Mach send-right name representing the calling process's audit session.

**Implementation:** [audit_session_self](../../../xnu/bsd/security/audit/audit_session.c#L1223), [audit_session_self](../../../xnu/bsd/security/audit/audit_session.c#L2044). The handler references the current credential, rejects the default session, initializes the port's inherited selection mask when needed, calls `audit_session_mksend`, and copies the send right into the task IPC space. Credential cleanup is paired on exit; the non-audit body returns `ENOSYS`.

## 429: audit_session_join

`int audit_session_join(mach_port_name_t port);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L647) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Join the audit session represented by a supplied Mach send-right name.

**Implementation:** [audit_session_join](../../../xnu/bsd/security/audit/audit_session.c#L1475), [audit_session_join](../../../xnu/bsd/security/audit/audit_session.c#L2053). The handler imports an `IKOT_AU_SESSIONPORT` send right through `ipc_typed_port_copyin_send` and delegates credential/session changes to `audit_session_join_internal`. Failed import returns `EINVAL` and the default session ID; the non-audit body returns `ENOSYS`.

## 432: audit_session_port

`int audit_session_port(au_asid_t asid, user_addr_t portnamep);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L650) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Obtain a Mach send-right name for a requested audit session ID.

**Implementation:** [audit_session_port](../../../xnu/bsd/security/audit/audit_session.c#L1294), [audit_session_port](../../../xnu/bsd/security/audit/audit_session.c#L2062). The caller's own session requires no additional privilege; another session requires `PRIV_AUDIT_SESSION_PORT`. The handler references the session, creates/copies out its port and writes the name to userspace, dropping session/credential references and deallocating an already installed name if final copyout fails. Without audit support it returns `ENOSYS`.

## 483: csrctl

`int csrctl(uint32_t op, user_addr_t useraddr, user_addr_t usersize) NO_SYSCALL_STUB;`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L743) · **Condition:** `(CONFIG_CSR)` · **Audit event:** `AUE_NULL`.

Query whether requested SIP/CSR permissions are allowed or retrieve the active CSR configuration.

**Implementation:** [csrctl](../../../xnu/bsd/kern/kern_csr.c#L390). The dispatcher recognizes only `CSR_SYSCALL_CHECK` and `CSR_SYSCALL_GET_ACTIVE_CONFIG`, forwarding to helpers that validate the supplied buffer and call the CSR policy functions. Unknown operations return `ENOSYS`; this entry does not provide a general configuration setter.

## 500: getentropy

`int getentropy(void *buffer, size_t size);`

**Declaration:** [syscalls.master](../../../xnu/bsd/kern/syscalls.master#L783) · **Condition:** `always` · **Audit event:** `AUE_NULL`.

Fill a userspace buffer with at most 256 bytes from the kernel random subsystem.

**Implementation:** [getentropy](../../../xnu/bsd/dev/random/randomdev.c#L243). The handler rejects larger requests, fills a fixed stack buffer through `read_random`, and copies exactly the requested count out. The random generator's internal construction is beyond this syscall wrapper.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
